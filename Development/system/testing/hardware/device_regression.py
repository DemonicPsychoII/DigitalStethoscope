"""Hardware regression run of the app firmware against a local HAPI FHIR test server.

Each scenario prepares the server profile partition and the FHIR container, resets the
board through RTS and checks the serial log for required lines in order, forbidden lines,
unexpected resets and the timing of server connection attempts. The settings partition
with the saved Wi-Fi network is never touched. See README.md in this directory.
"""

import argparse
import datetime
import ipaddress
import re
import ssl
import subprocess
import sys
import threading
import time
import tomllib
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import serial
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

REPOSITORY = Path(__file__).resolve().parents[4]
TOOLS = REPOSITORY / "Development/system/coding/tools"
LAB_DEPLOYMENT = REPOSITORY / "Development/system/coding/server-profiles/lab-hapi.toml"
BAUD_RATE = 115200
SERVER_START_TIMEOUT_SECONDS = 180
DOCKER_COMMAND_TIMEOUT_SECONDS = 60

# P26-ATTEMPT and P26-RETRY in design/COMMUNICATION/secure-transport.md.
PREPARATION_LIMIT_SECONDS = 10
RETRY_GAP_SECONDS = 60
# P23: a failed SNTP exchange is logged only after its cancellation, which has its own stop bound.
CLEANUP_LIMIT_SECONDS = 1
# Log timestamps have millisecond resolution; logging and scheduling add a little more.
TIMING_TOLERANCE_SECONDS = 0.5

CRASH_PATTERNS = [
    r"FATAL",
    r"Guru Meditation",
    r"Backtrace:",
    r"ASSERTION FAIL",
    r"Stack overflow",
    r"heap corruption",
]
# A first preparation right after the join can miss its budget; the 60 s retry must then verify.
FIRST_ATTEMPT_WARNINGS = [
    r"Connect rejected",
    r"TLS setup failed",
    r"time synchronization failed",
    r"SERVER_CONNECTION_FAILURE",
]
ESCAPE_SEQUENCE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
BOOT_BANNER = re.compile(r"^rst:0x[0-9a-f]+ ")
DEVICE_TIMESTAMP = re.compile(r"\[(\d+):(\d\d):(\d\d)\.(\d{3}),\d{3}\]")
TIME_SYNCHRONIZED = "Time synchronized"
ATTEMPT_FAILED = re.compile(
    r"Server connection: (TLS setup failed|time synchronization failed|certificate not valid)"
)
ATTEMPT_SUCCEEDED = "Server connection verified"


@dataclass
class Context:
    port: str
    server_address: str
    server_container: str
    output_directory: Path

    @property
    def port_number(self) -> int:
        return int(self.port.upper().removeprefix("COM"))

    @property
    def base_url(self) -> str:
        return f"https://{self.server_address}:8443/fhir"

    def log(self, scenario: str) -> Path:
        path = self.output_directory / f"{scenario}.log"
        repetition = 1
        while path.exists():
            repetition += 1
            path = self.output_directory / f"{scenario}-{repetition}.log"
        return path


@dataclass
class LogEvent:
    device_seconds: float
    message: str


@dataclass
class Capture:
    failures: list[str] = field(default_factory=list)
    events: list[LogEvent] = field(default_factory=list)


def run(command: Sequence[str | Path]) -> None:
    print("  $", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], check=True)


def run_tool(script: str, context: Context, *arguments: str | Path) -> None:
    run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            TOOLS / script,
            str(context.port_number),
            *arguments,
        ]
    )


def lab_server() -> dict[str, object]:
    server = tomllib.loads(LAB_DEPLOYMENT.read_text(encoding="utf-8")).get("server")
    if (
        not isinstance(server, dict)
        or not isinstance(server.get("certificate"), str)
        or not isinstance(server.get("keep_alive_seconds"), int)
    ):
        raise SystemExit(f"{LAB_DEPLOYMENT} has no certificate or keep-alive")
    return server


def deployment_file(
    context: Context, name: str, certificate: str | None = None
) -> Path:
    """Write a deployment file into the run directory from lab-hapi with this run's address."""
    server = lab_server()
    path = context.output_directory / "deployments" / f"{name}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'format = 1\ndescription = "Hardware regression run: {name}"\n\n[server]\n'
        f'base_url = "{context.base_url}"\n'
        f"keep_alive_seconds = {server['keep_alive_seconds']}\n"
        f'certificate = """\n{(certificate or str(server["certificate"])).strip()}\n"""\n',
        encoding="utf-8",
    )
    return path


def flash_lab_profile(context: Context) -> None:
    run_tool("flash-server-profile.ps1", context, deployment_file(context, "lab-hapi"))


def foreign_certificate(server_address: str) -> str:
    """A valid self-signed certificate for the server address that the server does not hold."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, server_address)])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=30))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.IPAddress(ipaddress.IPv4Address(server_address))]
            ),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    return certificate.public_bytes(serialization.Encoding.PEM).decode("ascii")


def set_server_running(context: Context, running: bool) -> None:
    """Start or stop the FHIR container; a start returns once metadata answers over the pinned certificate."""
    subprocess.run(
        ["docker", "start" if running else "stop", context.server_container],
        check=True,
        capture_output=True,
        timeout=DOCKER_COMMAND_TIMEOUT_SECONDS,
    )
    if not running:
        return
    trust = ssl.create_default_context(cadata=str(lab_server()["certificate"]))
    deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"{context.base_url}/metadata", context=trust, timeout=5
            ) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(5)
    raise RuntimeError(
        f"FHIR server did not answer within {SERVER_START_TIMEOUT_SECONDS} s"
    )


def device_seconds(line: str) -> float | None:
    match = DEVICE_TIMESTAMP.search(line)
    if match is None:
        return None
    hours, minutes, seconds, milliseconds = (int(group) for group in match.groups())
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def capture(
    context: Context,
    scenario: str,
    seconds: float,
    required: Sequence[str],
    forbidden: Sequence[str],
    warnings: Sequence[str] = (),
    quiet_seconds: float = 0,
    on_line: Callable[[str], None] | None = None,
) -> Capture:
    """Reset the board and read its console until every required pattern matched in order
    within seconds, then for quiet_seconds more, which the overall limit does not shorten."""
    result = Capture()
    pending_patterns = list(required)
    quiet_until: float | None = None
    boot_count = 0
    with (
        serial.Serial(context.port, BAUD_RATE, timeout=0.2) as connection,
        open(context.log(scenario), "w", encoding="utf-8") as log,
    ):
        connection.dtr = False
        connection.rts = True
        time.sleep(0.2)
        # Opening the port can briefly reset the board; drop that partial boot while it is held in reset.
        connection.reset_input_buffer()
        connection.rts = False
        start = time.monotonic()
        buffer = b""
        while (pending_patterns and time.monotonic() - start < seconds) or (
            quiet_until is not None and time.monotonic() < quiet_until
        ):
            buffer += connection.read(4096)
            *lines, buffer = buffer.split(b"\n")
            for raw_line in lines:
                elapsed = time.monotonic() - start
                line = ESCAPE_SEQUENCE.sub("", raw_line.decode("utf-8", "replace"))
                line = line.replace("uart:~$ ", "").strip()
                message = line[line.find("<") :] if "<" in line else line
                log.write(f"[{elapsed:7.2f}] {line}\n")
                log.flush()
                if BOOT_BANNER.search(line):
                    boot_count += 1
                    if boot_count > 1:
                        result.failures.append(
                            f"unexpected reset at {elapsed:.1f} s: {line}"
                        )
                for pattern in forbidden:
                    if re.search(pattern, line):
                        result.failures.append(
                            f"forbidden at {elapsed:.1f} s: {message}"
                        )
                for pattern in warnings:
                    if re.search(pattern, line):
                        print(f"    WARN {elapsed:6.1f} s  {message}", flush=True)
                timestamp = device_seconds(line)
                if timestamp is not None:
                    result.events.append(LogEvent(timestamp, message))
                if pending_patterns and re.search(pending_patterns[0], line):
                    print(
                        f"    {elapsed:6.1f} s  {pending_patterns.pop(0)}", flush=True
                    )
                    if not pending_patterns:
                        quiet_until = time.monotonic() + quiet_seconds
                if on_line:
                    on_line(line)
    if boot_count == 0:
        result.failures.append("no boot banner after the reset")
    result.failures += [
        f"missing within {seconds} s: {pattern}" for pattern in pending_patterns
    ]
    return result


def check_attempt_timing(
    events: Sequence[LogEvent], maximum_failed_attempts: int | None = None
) -> list[str]:
    """Check P26 on the device clock: a failed attempt ends within 10 s of its SNTP result,
    and the next attempt's SNTP result follows 60 s to 70.5 s after that failure; a failed
    SNTP exchange may log up to 1 s later because its cancellation (P23) runs first.

    The log has no line for the start of an attempt, so its SNTP result is the earliest
    evidence of it; the 10 s bound is therefore checked from that line, not from the start.
    """
    failures: list[str] = []
    attempt_synchronized_at: float | None = None
    previous_failure_at: float | None = None
    failed_attempts = 0
    for event in events:
        is_failure = ATTEMPT_FAILED.search(event.message) is not None
        is_synchronization_failure = "time synchronization failed" in event.message
        starts_attempt = (
            TIME_SYNCHRONIZED in event.message or is_synchronization_failure
        )
        if starts_attempt and previous_failure_at is not None:
            gap = event.device_seconds - previous_failure_at
            latest_gap = (
                RETRY_GAP_SECONDS
                + PREPARATION_LIMIT_SECONDS
                + (CLEANUP_LIMIT_SECONDS if is_synchronization_failure else 0)
                + TIMING_TOLERANCE_SECONDS
            )
            if not RETRY_GAP_SECONDS <= gap <= latest_gap:
                failures.append(
                    f"next attempt {gap:.1f} s after the failure at {previous_failure_at:.1f} s,"
                    f" expected {RETRY_GAP_SECONDS} s to {latest_gap:.1f} s"
                )
            previous_failure_at = None
        if TIME_SYNCHRONIZED in event.message:
            attempt_synchronized_at = event.device_seconds
        if is_failure or ATTEMPT_SUCCEEDED in event.message:
            if attempt_synchronized_at is not None:
                duration = event.device_seconds - attempt_synchronized_at
                if duration > PREPARATION_LIMIT_SECONDS + TIMING_TOLERANCE_SECONDS:
                    failures.append(
                        f"attempt ended {duration:.1f} s after its SNTP result at"
                        f" {event.device_seconds:.1f} s, limit {PREPARATION_LIMIT_SECONDS} s"
                    )
            attempt_synchronized_at = None
        if is_failure:
            failed_attempts += 1
            previous_failure_at = event.device_seconds
    if (
        maximum_failed_attempts is not None
        and failed_attempts > maximum_failed_attempts
    ):
        failures.append(
            f"{failed_attempts} failed attempts, at most {maximum_failed_attempts} allowed"
        )
    return failures


def scenario_no_profile(context: Context) -> list[str]:
    """Erased server profile: secure transport unavailable, Wi-Fi joins, no SNTP result or server connection outcome for 70 s."""
    run_tool("erase-flash.ps1", context, "-ServerProfile")
    # SNTP runs only inside a TLS connection setup, so without a profile neither may start.
    return capture(
        context,
        "no-profile",
        80,
        [r"Secure transport unavailable: no server profile image", r"Wi-Fi connected"],
        CRASH_PATTERNS
        + [TIME_SYNCHRONIZED, r"Server connection", r"WIFI_CLEANUP_FAILURE"],
        quiet_seconds=70,
    ).failures


def scenario_foreign_certificate(context: Context) -> list[str]:
    """Profile pins another certificate for the same address: the first attempt and the retry both refuse the server."""
    set_server_running(context, True)
    run_tool(
        "flash-server-profile.ps1",
        context,
        deployment_file(
            context,
            "foreign-certificate",
            certificate=foreign_certificate(context.server_address),
        ),
    )
    result = capture(
        context,
        "foreign-certificate",
        150,
        [
            r"Wi-Fi connected",
            r"Server verification failed \(flags 0x8\)",
            r"SERVER_CONNECTION_FAILURE \(-13\)",
            r"Server verification failed \(flags 0x8\)",
            r"TLS setup failed \(-13, cause 6\)",
        ],
        CRASH_PATTERNS + [ATTEMPT_SUCCEEDED, r"WIFI_CLEANUP_FAILURE"],
    )
    return result.failures + check_attempt_timing(result.events)


def scenario_server_down_then_up(context: Context) -> list[str]:
    """Server stopped at boot: failure and the 60 s retry, then verified once the server is back."""
    flash_lab_profile(context)
    set_server_running(context, False)
    server_start_errors: list[str] = []

    def start_server() -> None:
        try:
            set_server_running(context, True)
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            server_start_errors.append(f"server start failed: {error}")

    # Started in the background so the console keeps being read while the server boots.
    server_starter = threading.Thread(target=start_server, daemon=True)

    def start_server_after_failure(line: str) -> None:
        if server_starter.ident is None and "SERVER_CONNECTION_FAILURE" in line:
            server_starter.start()

    try:
        result = capture(
            context,
            "server-down-then-up",
            240,
            [
                r"Wi-Fi connected",
                TIME_SYNCHRONIZED,
                r"SERVER_CONNECTION_FAILURE \(-?\d+\); retry in 60 s",
                ATTEMPT_SUCCEEDED,
            ],
            CRASH_PATTERNS + [r"WIFI_CLEANUP_FAILURE", r"Server verification failed"],
            on_line=start_server_after_failure,
        )
    except BaseException:
        if server_starter.ident is not None:
            server_starter.join()
        # The capture exception propagates; a start error recorded before it is reported here.
        for error in server_start_errors:
            print(f"    FAIL {error}", flush=True)
        raise
    if server_starter.ident is not None:
        server_starter.join()
    return result.failures + check_attempt_timing(result.events) + server_start_errors


def scenario_valid_profile(context: Context) -> list[str]:
    """Lab profile: stored Wi-Fi join, SNTP and a verified TLS connection to the pinned server within one retry."""
    flash_lab_profile(context)
    set_server_running(context, True)
    result = capture(
        context,
        "valid-profile",
        120,
        [
            rf"Server {re.escape(context.base_url)} configured",
            r"Connecting to \"",
            r"Wi-Fi connected",
            TIME_SYNCHRONIZED + r": 20\d\d-",
            ATTEMPT_SUCCEEDED,
        ],
        CRASH_PATTERNS
        + [
            r"Secure transport unavailable",
            r"WIFI_CLEANUP_FAILURE",
            r"Server verification failed",
        ],
        warnings=FIRST_ATTEMPT_WARNINGS,
        quiet_seconds=20,
    )
    return result.failures + check_attempt_timing(
        result.events, maximum_failed_attempts=1
    )


SCENARIOS: dict[str, Callable[[Context], list[str]]] = {
    "no-profile": scenario_no_profile,
    "foreign-certificate": scenario_foreign_certificate,
    "server-down-then-up": scenario_server_down_then_up,
    "valid-profile": scenario_valid_profile,
}


def restore(context: Context, is_lab_profile_flashed: bool) -> list[str]:
    """Leave the server running and the lab profile on the board; each step runs even if the other fails."""
    failures: list[str] = []
    try:
        set_server_running(context, True)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        failures.append(f"server start failed: {error}")
    if not is_lab_profile_flashed:
        try:
            flash_lab_profile(context)
        except (OSError, subprocess.SubprocessError) as error:
            failures.append(f"lab profile restore failed: {error}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default="COM4", help="Serial port of the board.")
    parser.add_argument(
        "--server-address",
        default="192.168.2.40",
        help="IPv4 address of the FHIR server; it must be in the lab certificate's Subject Alternative Names.",
    )
    parser.add_argument(
        "--server-container",
        default="fhir_tls",
        help="Docker container of the FHIR server.",
    )
    parser.add_argument(
        "--flash-firmware",
        action="store_true",
        help="Flash the release build in build-app before the scenarios.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        choices=list(SCENARIOS),
        help="Run only this scenario; repeatable. Default: all.",
    )
    arguments = parser.parse_args()
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    # Inputs are checked before anything touches the board.
    if re.fullmatch(r"COM\d+", arguments.port.upper()) is None:
        parser.error(f"--port must be a COM port such as COM4, not {arguments.port}")
    try:
        ipaddress.IPv4Address(arguments.server_address)
    except ValueError:
        parser.error(
            f"--server-address must be an IPv4 address, not {arguments.server_address}"
        )
    lab_server()
    context = Context(
        port=arguments.port,
        server_address=arguments.server_address,
        server_container=arguments.server_container,
        output_directory=REPOSITORY / "artifacts/hardware-regression" / stamp,
    )
    context.output_directory.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(
        ["git", "-C", str(REPOSITORY), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    print(f"Tree {commit}, port {context.port}, logs {context.output_directory}")
    if arguments.flash_firmware:
        run_tool("flash-firmware.ps1", context)
    names = arguments.scenario or list(SCENARIOS)
    results: list[tuple[str, list[str]]] = []
    is_lab_profile_flashed = False
    cleanup_failures: list[str] = []
    try:
        for name in names:
            # Cleared first: a scenario that fails before its own flash leaves the profile unknown.
            is_lab_profile_flashed = False
            print(f"\n== {name}: {SCENARIOS[name].__doc__}", flush=True)
            failures = SCENARIOS[name](context)
            # A list, so a repeated scenario keeps the result of every run.
            results.append((name, failures))
            is_lab_profile_flashed = name in ("server-down-then-up", "valid-profile")
            for failure in failures:
                print(f"    FAIL {failure}", flush=True)
    finally:
        cleanup_failures = restore(context, is_lab_profile_flashed)
        for failure in cleanup_failures:
            print(f"    CLEANUP FAIL {failure}", flush=True)
    print("\nSummary")
    for name, failures in results:
        print(f"  {'FAIL' if failures else 'PASS'}  {name}")
    sys.exit(1 if any(failures for _, failures in results) or cleanup_failures else 0)


if __name__ == "__main__":
    main()
