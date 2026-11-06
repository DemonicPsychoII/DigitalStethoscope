"""Hardware regression run of the app firmware against a local HAPI FHIR test server.

Each scenario prepares the server profile partition and the FHIR container, resets the
board through RTS and checks the serial log for required lines in order and for forbidden
lines within a time limit. The settings partition with the saved Wi-Fi network is never
touched. See README.md in this directory for the setup.
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
from dataclasses import dataclass
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

CRASH_PATTERNS = [
    r"FATAL",
    r"Guru Meditation",
    r"Backtrace:",
    r"ASSERTION FAIL",
    r"Stack overflow",
    r"heap corruption",
    r"rst:0x[0-9a-f]+ \((?!POWERON|RTC_SW_SYS_RESET)",
]
# A first preparation right after the join can miss its budget; the 60 s retry must then verify.
FIRST_ATTEMPT_WARNINGS = [
    r"Connect rejected",
    r"TLS setup failed",
    r"time synchronization failed",
    r"SERVER_CONNECTION_FAILURE",
]
ESCAPE_SEQUENCE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


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
        return self.output_directory / f"{scenario}.log"


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
    server = tomllib.loads(LAB_DEPLOYMENT.read_text(encoding="utf-8"))["server"]
    if not isinstance(server.get("certificate"), str) or not isinstance(
        server.get("keep_alive_seconds"), int
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


def capture(
    context: Context,
    scenario: str,
    seconds: float,
    required: Sequence[str],
    forbidden: Sequence[str],
    warnings: Sequence[str] = (),
    quiet_seconds: float = 0,
    on_line: Callable[[str], None] | None = None,
) -> list[str]:
    """Reset the board and read its console until every required pattern matched in order, then for quiet_seconds more."""
    pending_patterns = list(required)
    failures: list[str] = []
    quiet_until: float | None = None
    with (
        serial.Serial(context.port, BAUD_RATE, timeout=0.2) as connection,
        open(context.log(scenario), "w", encoding="utf-8") as log,
    ):
        connection.dtr = False
        connection.rts = True
        time.sleep(0.2)
        connection.rts = False
        start = time.monotonic()
        buffer = b""
        while time.monotonic() - start < seconds and (
            pending_patterns
            or (quiet_until is not None and time.monotonic() < quiet_until)
        ):
            buffer += connection.read(4096)
            *lines, buffer = buffer.split(b"\n")
            for raw_line in lines:
                elapsed = time.monotonic() - start
                line = ESCAPE_SEQUENCE.sub("", raw_line.decode("utf-8", "replace"))
                line = line.replace("uart:~$ ", "").rstrip()
                message = line[line.find("<") :] if "<" in line else line
                log.write(f"[{elapsed:7.2f}] {line}\n")
                log.flush()
                for pattern in forbidden:
                    if re.search(pattern, line):
                        failures.append(f"forbidden at {elapsed:.1f} s: {message}")
                for pattern in warnings:
                    if re.search(pattern, line):
                        print(f"    WARN {elapsed:6.1f} s  {message}", flush=True)
                if pending_patterns and re.search(pending_patterns[0], line):
                    print(
                        f"    {elapsed:6.1f} s  {pending_patterns.pop(0)}", flush=True
                    )
                    if not pending_patterns:
                        quiet_until = time.monotonic() + quiet_seconds
                if on_line:
                    on_line(line)
    failures += [
        f"missing within {seconds} s: {pattern}" for pattern in pending_patterns
    ]
    return failures


def scenario_no_profile(context: Context) -> list[str]:
    """Erased server profile: secure transport unavailable, Wi-Fi joins, no SNTP or TLS attempt for 70 s."""
    run_tool("erase-flash.ps1", context, "-ServerProfile")
    # SNTP runs only inside a TLS connection setup, so without a profile neither may start.
    return capture(
        context,
        "no-profile",
        150,
        [r"Secure transport unavailable: no server profile image", r"Wi-Fi connected"],
        CRASH_PATTERNS
        + [r"Time synchronized", r"Server connection", r"WIFI_CLEANUP_FAILURE"],
        quiet_seconds=70,
    )


def scenario_foreign_certificate(context: Context) -> list[str]:
    """Profile pins another certificate for the same address: the device refuses the server."""
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
    return capture(
        context,
        "foreign-certificate",
        150,
        [
            r"Wi-Fi connected",
            r"Server verification failed \(flags 0x8\)",
            r"SERVER_CONNECTION_FAILURE \(-13\)",
        ],
        CRASH_PATTERNS + [r"Server connection verified", r"WIFI_CLEANUP_FAILURE"],
    )


def scenario_server_down_then_up(context: Context) -> list[str]:
    """Server stopped at boot: failure and the 60 s retry, then verified once the server is back."""
    run_tool("flash-server-profile.ps1", context, deployment_file(context, "lab-hapi"))
    set_server_running(context, False)
    is_server_started = threading.Event()

    def start_server_after_failure(line: str) -> None:
        if not is_server_started.is_set() and "SERVER_CONNECTION_FAILURE" in line:
            is_server_started.set()
            # Started in the background so the console keeps being read while the server boots.
            threading.Thread(
                target=set_server_running, args=(context, True), daemon=True
            ).start()

    return capture(
        context,
        "server-down-then-up",
        240,
        [
            r"Wi-Fi connected",
            r"Time synchronized",
            r"SERVER_CONNECTION_FAILURE \(-?\d+\); retry in 60 s",
            r"Server connection verified",
        ],
        CRASH_PATTERNS + [r"WIFI_CLEANUP_FAILURE", r"Server verification failed"],
        on_line=start_server_after_failure,
    )


def scenario_valid_profile(context: Context) -> list[str]:
    """Lab profile: stored Wi-Fi join, SNTP and a verified TLS connection to the pinned server."""
    run_tool("flash-server-profile.ps1", context, deployment_file(context, "lab-hapi"))
    set_server_running(context, True)
    return capture(
        context,
        "valid-profile",
        120,
        [
            rf"Server {re.escape(context.base_url)} configured",
            r"Connecting to \"",
            r"Wi-Fi connected",
            r"Time synchronized: 20\d\d-",
            r"Server connection verified",
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


SCENARIOS: dict[str, Callable[[Context], list[str]]] = {
    "no-profile": scenario_no_profile,
    "foreign-certificate": scenario_foreign_certificate,
    "server-down-then-up": scenario_server_down_then_up,
    "valid-profile": scenario_valid_profile,
}


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
    # The lab profile goes last, so the board is left in its normal configuration.
    names = arguments.scenario or list(SCENARIOS)
    results: dict[str, list[str]] = {}
    try:
        for name in names:
            print(f"\n== {name}: {SCENARIOS[name].__doc__}", flush=True)
            results[name] = SCENARIOS[name](context)
            for failure in results[name]:
                print(f"    FAIL {failure}", flush=True)
    finally:
        set_server_running(context, True)
        if names[-1] != "valid-profile":
            run_tool(
                "flash-server-profile.ps1",
                context,
                deployment_file(context, "lab-hapi"),
            )
    print("\nSummary")
    for name, failures in results.items():
        print(f"  {'FAIL' if failures else 'PASS'}  {name}")
    sys.exit(1 if any(results.values()) else 0)


if __name__ == "__main__":
    main()
