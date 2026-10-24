"""VT-14 workflow expectations from the Wi-Fi and portal design."""

import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
WIFI = "Development/system/design/WIFI/interfaces-and-behavior.md#"
PARAMETERS = "Development/system/design/WIFI/parameters.md"
# P21/P23: proposed target timings, used here as the design simulation baseline.
RETRY = 5_000
INACTIVITY = 300_000
RESULT = 10_000
NOTICE = 2_000
CHECK = 120_000
SCAN_TIMEOUT = 10_000
JOIN_TIMEOUT = 15_000
CASES = []


def case(name, anchor, expected, defect=None):
    def register(function):
        if defect is None:
            marks = []
        else:
            marks = [
                pytest.mark.xfail(
                    strict=True, raises=AssertionError, reason=f"{defect}; see PR"
                )
            ]
        CASES.append(
            pytest.param(function, name, anchor, expected, id=name, marks=marks)
        )
        return function

    return register


class Trace:
    def __init__(self, output):
        self.rows = [
            (int(trace), key, int(value))
            for trace, key, value in (line.split() for line in output.splitlines())
        ]

    def times(self, key):
        return [time for time, kind, _ in self.rows if kind == key]

    def values(self, key):
        return [value for _, kind, value in self.rows if kind == key]

    def count(self, key):
        return len(self.times(key))

    def last(self, key):
        values = self.values(key)
        assert values, f"Missing {key}: {self.rows}"
        return values[-1]

    def before(self, first, second):
        assert self.times(first) and self.times(second), self.rows
        assert self.rows.index(
            next(row for row in self.rows if row[1] == first)
        ) < self.rows.index(next(row for row in self.rows if row[1] == second)), (
            self.rows
        )


def event(time_milliseconds, kind, value=0):
    return f"event {time_milliseconds} {kind} {value}\n"


def plan(kind, results, delay=100):
    return "".join(f"{kind} {result} {delay}\n" for result in results)


@pytest.fixture(scope="session")
def executable(host_build_directory):
    if sys.platform == "win32":
        executable_name = "simulation.exe"
    else:
        executable_name = "simulation"
    target = host_build_directory("l2", "communication") / executable_name
    # shlex keeps compiler arguments (e.g. Zig's cc subcommand); quoted paths work.
    compiler = shlex.split(os.environ.get("CC", "gcc"))
    command = compiler + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-g"]
    if os.environ.get("STETHO_COVERAGE_DIRECTORY"):
        command += ["--coverage", "-O0"]
    if os.environ.get("STETHO_SANITIZERS", "").lower() == "true":
        command += ["-fsanitize=address,undefined", "-fno-sanitize-recover=all"]
    for directory in (
        HERE / "include",
        APP / "L2_application/L2_COMMUNICATION",
        APP / "L1_services/L1_WIFI",
        APP / "L1_services/L1_PORTAL",
        APP / "L1_services/L1_STORAGE",
    ):
        command += ["-I", str(directory)]
    command += [
        str(HERE / "simulation.c"),
        str(APP / "L2_application/L2_COMMUNICATION/communication.c"),
        "-o",
        str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode:
        pytest.fail(
            f"Host compile failed: {command}\n{result.stdout}\n{result.stderr}",
            pytrace=False,
        )
    try:
        version = subprocess.check_output(
            compiler + ["--version"], text=True, timeout=30
        ).splitlines()[0]
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=APP, text=True, timeout=30
        ).strip()
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"Host tool identity timed out: {error.cmd}", pytrace=False)
    return target, command, version, revision


@pytest.fixture
def simulate(executable, record_property):
    return create_simulation_runner(executable, record_property)


def create_simulation_runner(executable, record_property):
    target, command, version, revision = executable
    record_property("source_revision", revision)
    record_property("compiler_version", version)
    record_property("compiler_command", subprocess.list2cmdline(command))

    def run(script="", until=1000, stored=False):
        script = f"horizon {until}\nstored {int(stored)}\n" + script
        result = subprocess.run(
            [str(target)], input=script, capture_output=True, text=True, timeout=10
        )
        record_property("simulation_input", script)
        record_property("simulation_trace", result.stdout)
        record_property("production_log", result.stderr)
        if result.returncode:
            pytest.fail(
                f"Simulation failed ({result.returncode}):\n{result.stdout}\n{result.stderr}",
                pytrace=False,
            )
        trace = Trace(result.stdout)
        trace.production_log = result.stderr
        return trace

    return run


ENTRY = WIFI + "entry-scan-and-recovery"
JOIN = WIFI + "join-persistence-and-result-closure"
CANCEL = WIFI + "cancellation-and-inactivity"
START = WIFI + "listening-priority-and-safe-teardown"


@case(
    "boot-stored",
    ENTRY,
    "Join stored settings once; retain station without opening setup or rewriting settings.",
)
def boot_stored(simulation):
    trace = simulation(stored=True)
    assert trace.count("join") == 1 and trace.count("scan") == 0
    assert trace.last("connected") == 1 and trace.count("write") == 0
    assert trace.last("join_selected") == 0


@case(
    "boot-fourth-attempt",
    ENTRY,
    "Three failures are followed by the fourth successful join, each retry 5 s after failure.",
)
def boot_fourth(simulation):
    trace = simulation(plan("join", [-5, -5, -5, 0]), until=20_000, stored=True)
    assert trace.times("join") == [0, 100 + RETRY, 200 + 2 * RETRY, 300 + 3 * RETRY]
    assert trace.last("connected") == 1 and trace.count("scan") == 0


@case(
    "boot-exhaustion-manual-recovery",
    ENTRY,
    "Four failed boot joins stop; only the later Idle hold opens setup.",
)
def boot_exhaustion(simulation):
    trace = simulation(
        plan("join", [-5] * 4) + event(25_000, "snapshot") + event(30_000, "hold"),
        until=31_000,
        stored=True,
    )
    assert trace.count("join") == 4 and trace.times("scan") == [30_000]
    assert trace.last("page") == 1


@case(
    "boot-join-timeout",
    ENTRY,
    "Each pending join stops at the 15 s candidate limit; four attempts use 5 s retry gaps.",
)
def boot_timeout(simulation):
    trace = simulation(
        plan("join", [0] * 4, JOIN_TIMEOUT * 2), until=80_000, stored=True
    )
    assert trace.times("join") == [
        0,
        JOIN_TIMEOUT + RETRY,
        2 * (JOIN_TIMEOUT + RETRY),
        3 * (JOIN_TIMEOUT + RETRY),
    ]
    assert trace.times("disconnect") == [
        JOIN_TIMEOUT,
        2 * JOIN_TIMEOUT + RETRY,
        3 * JOIN_TIMEOUT + 2 * RETRY,
        4 * JOIN_TIMEOUT + 3 * RETRY,
    ]
    assert trace.count("scan") == 0


@case(
    "missing-settings-scan-before-ap",
    ENTRY,
    "Finish and publish the initial scan before AP, DHCP and page start.",
)
def missing_settings(simulation):
    trace = simulation()
    for first, second in (
        ("scan_result", "networks"),
        ("networks", "ap_start"),
        ("ap_start", "dhcp_start"),
        ("dhcp_start", "page_start"),
    ):
        trace.before(first, second)
    assert trace.last("page") == 1


@case(
    "invalid-stored-settings",
    JOIN,
    "Reject an invalid stored record; scan for setup without submitting it to Wi-Fi.",
)
def invalid_settings(simulation):
    trace = simulation(stored=2)
    assert trace.count("join") == 0 and trace.count("scan") == 1


@case(
    "settings-read-failure",
    JOIN,
    "A settings read failure opens setup without passing damaged settings to Wi-Fi.",
)
def read_failure(simulation):
    trace = simulation("read_error -5\n", stored=True)
    assert trace.count("join") == 0 and trace.last("page") == 1


@case(
    "idle-hold-entry",
    ENTRY,
    "A setup event after the 2 s Idle hold starts scanning while retaining the station.",
)
def hold_entry(simulation):
    trace = simulation(event(2000, "hold"), until=3000, stored=True)
    assert trace.times("scan") == [2000] and trace.last("connected") == 1


@case(
    "scan-fourth-attempt",
    ENTRY,
    "Four scan attempts maximum, 5 s between failures; open AP only after scan success.",
)
def scan_fourth(simulation):
    trace = simulation(plan("scan", [-5, -5, -5, 0]), until=20_000)
    assert trace.times("scan") == [0, 100 + RETRY, 200 + 2 * RETRY, 300 + 3 * RETRY]
    assert trace.values("scan_result") == [-5, -5, -5, 0]
    assert trace.count("ap_start") == 1
    successful_scan_result = next(
        row for row in reversed(trace.rows) if row[1] == "scan_result"
    )
    first_ap_start = next(row for row in trace.rows if row[1] == "ap_start")
    assert trace.rows.index(successful_scan_result) < trace.rows.index(first_ap_start)
    assert trace.count("networks") == 1 and trace.last("page") == 1


@case(
    "scan-exhaustion-manual-retry",
    ENTRY,
    "Four failed scans leave setup closed; a later hold can try setup again.",
)
def scan_exhaustion(simulation):
    trace = simulation(
        plan("scan", [-5] * 4) + event(25_000, "snapshot") + event(30_000, "hold"),
        until=31_000,
    )
    assert trace.times("scan")[-1] == 30_000 and trace.count("scan") == 5
    assert trace.times("ap_start") == [30_100]
    assert len(trace.times("closing")) == 1 and trace.times("closing")[0] < 30_000


@case(
    "scan-timeout-budget",
    ENTRY,
    "Cancel each scan at the 10 s candidate limit; stop after four timed out attempts.",
)
def scan_timeout(simulation):
    trace = simulation(plan("scan", [0] * 4, SCAN_TIMEOUT * 2), until=60_000)
    assert trace.times("scan") == [
        0,
        SCAN_TIMEOUT + RETRY,
        2 * (SCAN_TIMEOUT + RETRY),
        3 * (SCAN_TIMEOUT + RETRY),
    ]
    assert trace.count("scan_cancel") == 4 and trace.count("ap_start") == 0


@case(
    "explicit-rescan",
    ENTRY,
    "Keep AP and page open during rescan; publish no partial list.",
)
def explicit_rescan(simulation):
    trace = simulation(
        plan("scan", [0], 100)
        + plan("scan", [0], 1000)
        + event(1000, "rescan")
        + event(1500, "snapshot"),
        until=2500,
    )
    assert trace.times("networks") == [100, 2000]
    assert trace.count("ap_start") == 1 and trace.count("page_start") == 1
    assert trace.count("page_stop") == 0 and trace.last("page") == 1


@case(
    "failed-join-rescan",
    ENTRY,
    "One failed portal join shows its cause and refreshes the scan list with AP still open.",
)
def failed_join(simulation):
    trace = simulation(plan("join", [-13]) + event(1000, "connect", 1), until=3000)
    assert trace.count("join") == 1 and trace.values("join_failed") == [-13]
    assert trace.count("scan") == 2 and trace.count("networks") == 2
    assert trace.count("write") == 0 and trace.last("page") == 1


@case(
    "join-after-failed-join",
    ENTRY,
    "A new Connect after failure uses the refreshed selection and can complete successfully.",
)
def join_after_failure(simulation):
    trace = simulation(
        plan("join", [-13, 0]) + event(1000, "connect", 1) + event(3000, "connect", 1),
        until=15_000,
    )
    assert trace.count("join") == 2 and trace.count("success") == 1
    assert trace.last("connected") == 1 and trace.last("record_new") == 1


@case(
    "portal-open-join",
    JOIN,
    "An open-network request uses no password; selected address is available before one save.",
)
def portal_open(simulation):
    trace = simulation(event(1000, "connect"), until=2000)
    assert trace.values("join_protected") == [0] and trace.count("join") == 1
    assert trace.count("write") == 1 and trace.last("page_address") == 1
    trace.before("join_result", "address")
    trace.before("address", "write")


@case(
    "portal-protected-join",
    JOIN,
    "A protected-network request carries credentials and saves only after selected-network join.",
)
def portal_protected(simulation):
    trace = simulation(event(1000, "connect", 1), until=2000)
    assert trace.values("join_protected") == [1]
    assert trace.last("record_new") == 1 and trace.count("success") == 1


@case(
    "old-link-not-new-join",
    JOIN,
    "An old station does not complete a pending selected-network join or cause a save.",
)
def old_link(simulation):
    trace = simulation(
        plan("join", [0], 100)
        + plan("join", [0], 5000)
        + event(2000, "hold")
        + event(3000, "connect"),
        until=9000,
        stored=True,
    )
    assert trace.count("join") == 2 and trace.times("write") == [8000]
    assert trace.times("join_result") == [100, 8000]
    assert trace.count("disconnect_before_rearm") == 2
    assert trace.count("success") == 1 and trace.last("record_new") == 1


@case(
    "portal-join-timeout",
    JOIN,
    "A pending portal join is cancelled after 15 s, with no retry or save, then rescanned.",
)
def portal_join_timeout(simulation):
    trace = simulation(plan("join", [0], 30_000) + event(1000, "connect"), until=18_000)
    assert trace.times("disconnect") == [1000 + JOIN_TIMEOUT]
    assert trace.count("join") == 1 and trace.count("write") == 0
    assert trace.count("scan") == 2 and trace.count("join_failed") == 1


@case(
    "save-retry-success",
    JOIN,
    "A failed first save is retried once; success retains the connection and new settings.",
)
def save_retry(simulation):
    trace = simulation("write_failures 1\n" + event(1000, "connect"), until=12_000)
    assert trace.count("write") == 2 and trace.count("success") == 1
    assert trace.last("record_new") == 1 and trace.last("connected") == 1


@case(
    "save-exhaustion-retains-old",
    JOIN,
    "Two failed saves show a warning; connection and previous valid settings remain.",
)
def save_exhaustion(simulation):
    trace = simulation(
        "write_failures 2\n" + event(2000, "hold") + event(3000, "connect"),
        until=15_000,
        stored=True,
    )
    assert trace.count("write") == 2 and trace.count("save_failed") == 1
    assert trace.last("record_old") == 1 and trace.last("connected") == 1
    assert trace.last("page") == 0 and trace.count("disconnect") == 0


@case(
    "success-result-deadline",
    JOIN,
    "Keep the success result open through 9999 ms; close at 10 s and retain the station.",
)
def success_deadline(simulation):
    trace = simulation(event(1000, "connect") + event(11099, "snapshot"), until=12_000)
    assert trace.times("page_stop") == [1100 + RESULT]
    assert trace.values("page") == [1, 0] and trace.last("connected") == 1


@case(
    "save-warning-deadline",
    JOIN,
    "Show the save warning for 10 s, then close setup while retaining the unsaved station.",
)
def warning_deadline(simulation):
    trace = simulation(
        "write_failures 2\n" + event(1000, "connect") + event(11099, "snapshot"),
        until=12_000,
    )
    assert trace.times("page_stop") == [1100 + RESULT]
    assert trace.values("page") == [1, 0] and trace.last("connected") == 1


@case(
    "setup-cancel",
    CANCEL,
    "Setup Cancel sends a closing notice, then closes after the 2 s candidate notice, without 10 s delay.",
)
def setup_cancel(simulation):
    trace = simulation(event(1000, "cancel"), until=4000)
    assert trace.times("closing") == [1000] and trace.times("page_stop") == [
        1000 + NOTICE
    ]
    assert trace.last("hotspot") == 0 and trace.last("dhcp") == 0


@case(
    "cancel-retains-station",
    CANCEL,
    "Cancelling setup preserves an already established station.",
)
def cancel_retains(simulation):
    trace = simulation(
        event(2000, "hold") + event(3000, "cancel"), until=6000, stored=True
    )
    assert trace.last("connected") == 1 and trace.count("disconnect") == 0
    assert trace.last("page") == 0


@case(
    "cancel-during-join-ignored",
    CANCEL,
    "Cancel after Connect cannot abort join, save or automatic result closure.",
)
def cancel_join(simulation):
    trace = simulation(
        plan("join", [0], 2000) + event(1000, "connect") + event(1500, "cancel"),
        until=14_000,
    )
    assert trace.count("success") == 1 and trace.times("page_stop") == [3000 + RESULT]
    assert trace.count("disconnect") == 0


@case(
    "cancel-during-result-ignored",
    CANCEL,
    "Cancel during the result display does not shorten the 10 s display.",
)
def cancel_result(simulation):
    trace = simulation(event(1000, "connect") + event(2000, "cancel"), until=12_000)
    assert trace.times("page_stop") == [1100 + RESULT]
    assert all(
        time_milliseconds >= 1100 + RESULT
        for time_milliseconds in trace.times("closing")
    )


@case(
    "inactivity-boundary",
    CANCEL,
    "Without activity, selection remains until 5 min, then notice and teardown follow.",
)
def inactivity_boundary(simulation):
    trace = simulation(event(100 + INACTIVITY - 1, "snapshot"), until=INACTIVITY + 4000)
    # Event-check intervals may observe the deadline up to 200 ms later.
    assert 100 + INACTIVITY <= trace.times("closing")[0] <= 300 + INACTIVITY
    assert trace.times("page_stop")[0] - trace.times("closing")[0] == NOTICE
    assert trace.values("page") == [1, 0]


@case(
    "polls-do-not-reset-inactivity",
    CANCEL,
    "Status polls do not keep the page open beyond the inactivity deadline.",
)
def polls_no_reset(simulation):
    trace = simulation(
        "".join(
            event(time_milliseconds, "poll")
            for time_milliseconds in (1000, 100_000, 200_000, 299_000)
        ),
        until=304_000,
    )
    assert 300_100 <= trace.times("closing")[0] <= 300_300
    assert trace.last("page") == 0


@case(
    "activity-resets-inactivity",
    CANCEL,
    "Selection or input activity restarts the full 5 min inactivity budget.",
)
def activity_reset(simulation):
    trace = simulation(
        event(200_000, "activity") + event(400_000, "snapshot"), until=504_000
    )
    assert 200_000 + INACTIVITY <= trace.times("closing")[0] <= 200_200 + INACTIVITY
    assert trace.values("page") == [1, 0]


@case(
    "rescan-pauses-inactivity",
    CANCEL,
    "A rescan near expiry remains active; a new 5 min budget starts after it finishes.",
)
def rescan_pause(simulation):
    trace = simulation(
        plan("scan", [0], 100)
        + plan("scan", [0], 9000)
        + event(299_000, "rescan")
        + event(305_000, "snapshot"),
        until=611_000,
    )
    assert trace.times("networks") == [100, 308_000]
    assert 308_000 + INACTIVITY <= trace.times("closing")[0] <= 308_200 + INACTIVITY
    assert trace.values("page") == [1, 0]


@case(
    "join-pauses-inactivity",
    CANCEL,
    "A join crossing the inactivity deadline completes and receives the full result display.",
)
def join_pause(simulation):
    trace = simulation(
        plan("join", [0], 5000) + event(299_000, "connect"), until=316_000
    )
    assert trace.count("success") == 1 and trace.times("page_stop") == [
        304_000 + RESULT
    ]


@case(
    "link-loss-reconnect",
    ENTRY,
    "After link loss, reconnect in Idle with stored settings and no setup if successful.",
)
def reconnect(simulation):
    trace = simulation(event(1000, "drop"), until=CHECK + 1000, stored=True)
    assert trace.count("join") == 2 and trace.times("join")[1] >= CHECK
    assert trace.last("connected") == 1 and trace.count("scan") == 0


@case(
    "reconnect-fourth-attempt",
    ENTRY,
    "Reconnect can succeed on the fourth attempt, with 5 s between failures.",
)
def reconnect_fourth(simulation):
    trace = simulation(
        plan("join", [0, -5, -5, -5, 0]) + event(1000, "drop"),
        until=140_000,
        stored=True,
    )
    starts = trace.times("join")[1:]
    assert (
        len(starts) == 4
        and [second - first for first, second in zip(starts, starts[1:])]
        == [RETRY + 100] * 3
    )
    assert trace.last("connected") == 1 and trace.count("scan") == 0


@case(
    "reconnect-exhaustion-automatic-setup",
    ENTRY,
    "Four failed reconnects automatically open setup in Idle, without a hold.",
)
def reconnect_exhaustion(simulation):
    trace = simulation(
        plan("join", [0] + [-5] * 4) + event(1000, "drop"), until=140_000, stored=True
    )
    assert (
        trace.count("join") == 5
        and trace.count("scan") == 1
        and trace.last("page") == 1
    )


@case(
    "listening-defers-recovery",
    START,
    "Retain the station at Start; link loss and setup requests cause no jobs until Stop returns Idle.",
)
def listening_deferral(simulation):
    trace = simulation(
        event(1000, "start")
        + event(2000, "snapshot")
        + event(3000, "drop")
        + event(4000, "hold")
        + event(200_000, "snapshot")
        + event(210_000, "stop"),
        until=212_000,
        stored=True,
    )
    assert trace.values("connected")[0] == 1 and trace.values("ack")[0] == 0
    assert trace.times("join") == [0, 210_000] and trace.count("scan") == 0


@case(
    "measurement-defers-network",
    START,
    "During the shared listening/measurement exclusion event, no scan or reconnect runs; Idle resumes recovery.",
)
def measurement_deferral(simulation):
    trace = simulation(
        event(1000, "start")
        + event(2000, "drop")
        + event(35_000, "hold")
        + event(60_000, "stop"),
        until=62_000,
        stored=True,
    )
    assert trace.times("join") == [0, 60_000] and trace.count("scan") == 0


@case(
    "start-during-scan",
    START,
    "Start cancels the scan; acknowledge only after cancellation, without opening setup services.",
)
def start_scan(simulation):
    trace = simulation(
        plan("scan", [0], 5000) + event(1000, "start") + event(1500, "snapshot"),
        until=2000,
    )
    assert trace.count("scan_cancel") == 1 and trace.last("ack") == 0
    assert trace.count("ap_start") == 0 and trace.count("networks") == 0


@case(
    "start-during-join",
    START,
    "Start cancels the pending portal join and closes setup; do not save cancelled credentials.",
)
def start_join(simulation):
    trace = simulation(
        plan("join", [0], 5000)
        + event(1000, "connect")
        + event(2000, "start")
        + event(2500, "snapshot"),
        until=3000,
    )
    assert trace.count("disconnect") == 1 and trace.count("write") == 0
    assert trace.last("page") == 0 and trace.last("ack") == 0


@case(
    "start-during-result",
    START,
    "Start shortens result display, tears down setup, and keeps the established station.",
)
def start_result(simulation):
    trace = simulation(
        event(1000, "connect") + event(2000, "start") + event(2500, "snapshot"),
        until=3000,
    )
    assert trace.times("page_stop") == [2000] and trace.last("connected") == 1
    assert trace.last("ack") == 0 and trace.count("disconnect") == 0


@case(
    "cleanup-failure-blocks-ack",
    START,
    "Failed portal shutdown blocks release; retry cleanup and acknowledge only after success.",
)
def cleanup_failure(simulation):
    trace = simulation(
        "stop_failures 1\n"
        + event(1000, "start")
        + event(1050, "snapshot")
        + event(2000, "snapshot"),
        until=4500,
    )
    assert trace.count("page_stop_failed") == 1 and trace.count("page_stop") == 1
    assert trace.values("ack")[0] != 0 and trace.last("ack") == 0
    assert trace.values("page")[0] == 1 and trace.last("page") == 0


@case(
    "new-start-invalidates-ack",
    START,
    "A fresh Start invalidates the old release acknowledgement until the worker confirms again.",
)
def acknowledgement_invalidation(simulation):
    trace = simulation(
        event(1000, "start")
        + event(2000, "snapshot")
        + event(3000, "stop")
        + event(3000, "start")
        + event(3000, "snapshot")
        + event(4000, "snapshot"),
        until=4500,
        stored=True,
    )
    assert trace.values("ack")[:3] == [0, -11, 0]


@case(
    "wifi-init-offline",
    CANCEL,
    "Wi-Fi initialization failure leaves network work stopped and permits offline release for audio.",
)
def init_offline(simulation):
    trace = simulation("init_error -5\n" + event(1000, "start"), until=2000)
    assert (
        trace.count("join") == 0 and trace.count("scan") == 0 and trace.last("ack") == 0
    )


@case(
    "ap-start-failure-manual-retry",
    ENTRY,
    "Clean partial AP startup failure; stay offline until a later hold retries setup.",
)
def ap_failure(simulation):
    trace = simulation("start_failure 1\n" + event(2000, "hold"), until=3000)
    assert trace.count("ap_start") == 2 and trace.count("ap_stop") == 2
    assert trace.count("page_start") == 0 and trace.last("hotspot") == 0
    trace.before("closing", "ap_stop")


@case(
    "dhcp-start-failure-cleanup",
    CANCEL,
    "A DHCP startup failure closes the partial services and permits offline audio release.",
)
def dhcp_failure(simulation):
    trace = simulation("start_failure 2\n" + event(1000, "start"), until=2000)
    assert trace.count("dhcp_stop") == 1 and trace.count("ap_stop") == 1
    assert trace.count("page_start") == 0 and trace.last("ack") == 0
    trace.before("closing", "dhcp_stop")


@case(
    "portal-start-failure-cleanup",
    CANCEL,
    "A portal startup failure closes all partial services and permits offline audio release.",
)
def portal_failure(simulation):
    trace = simulation("start_failure 3\n" + event(1000, "start"), until=2000)
    assert (
        trace.count("page_stop") == 1
        and trace.count("dhcp_stop") == 1
        and trace.count("ap_stop") == 1
    )
    assert trace.last("ack") == 0 and trace.last("page") == 0
    trace.before("closing", "page_stop")


@case(
    "address-unavailable-no-save",
    WIFI + "specified-failures-and-interrupted-boot",
    "If the selected station address cannot be obtained, do not persist or publish a successful join.",
    defect="COMMUNICATION saves and reports success after wifi_getAddress fails",
)
def missing_address(simulation):
    trace = simulation("address_error 1\n" + event(1000, "connect"), until=2000)
    assert trace.count("write") == 0, (
        "Settings were saved without obtaining the selected station address"
    )
    assert trace.count("success") == 0
    assert trace.count("join_failed") == 1 and trace.count("scan") == 2


@case(
    "empty-scan-list",
    ENTRY,
    "A completed empty scan publishes an empty selection and opens setup for a later rescan.",
)
def empty_scan(simulation):
    trace = simulation("scan_count 0\n")
    assert trace.values("networks") == [0] and trace.last("page") == 1


@case(
    "full-scan-list",
    PARAMETERS,
    "Publish all 16 entries at the candidate scan-list capacity after scan completion.",
)
def full_scan(simulation):
    trace = simulation("scan_count 16\n")
    assert trace.values("networks") == [16] and trace.last("page") == 1


@case(
    "hold-during-setup-ignored",
    ENTRY,
    "A repeated setup hold while setup is active does not restart scan or reopen services.",
)
def hold_while_setup(simulation):
    trace = simulation(event(2000, "hold"), until=3000)
    assert trace.count("scan") == 1 and trace.count("page_start") == 1


@case(
    "start-during-atomic-save",
    START,
    "An atomic settings write finishes before teardown and release; Start does not leave a partial record.",
)
def start_save(simulation):
    trace = simulation(
        "write_delay 1000\n"
        + event(1000, "connect")
        + event(1500, "start")
        + event(1600, "snapshot")
        + event(2500, "snapshot"),
        until=3000,
    )
    assert trace.times("write_complete") == [2100]
    assert trace.values("ack")[0] != 0 and trace.last("ack") == 0
    assert trace.values("record_new")[0] == 0 and trace.last("record_new") == 1
    trace.before("write_complete", "page_stop")
    assert trace.last("connected") == 1


@case(
    "start-interrupts-reconnect",
    START,
    "Start cancels a pending reconnect; defer further attempts until Idle returns.",
)
def start_reconnect(simulation):
    trace = simulation(
        plan("join", [0], 100)
        + plan("join", [0], 5000)
        + event(1000, "drop")
        + event(121_000, "start")
        + event(125_000, "snapshot")
        + event(130_000, "stop"),
        until=132_000,
        stored=True,
    )
    assert trace.times("join") == [0, 120_100, 130_000]
    assert trace.times("disconnect") == [121_000]
    assert trace.values("join_pending")[0] == 0 and trace.last("connected") == 1


@case(
    "rescan-exhaustion-closes-setup",
    ENTRY,
    "Four failed rescan attempts publish no partial replacement, send a notice and close setup.",
)
def rescan_failure(simulation):
    trace = simulation(
        plan("scan", [0] + [-5] * 4) + event(1000, "rescan"), until=20_000
    )
    assert trace.count("scan") == 5 and trace.count("networks") == 1
    assert trace.times("closing") == [1000 + 4 * 100 + 3 * RETRY]
    assert trace.times("page_stop")[0] - trace.times("closing")[0] == NOTICE


@case(
    "result-close-publishes-closing",
    "Development/system/design/PORTAL/interfaces-and-behavior.md#form-navigation-and-setup-exit",
    "Publish Closing before stopping the portal server after the 10 s result display.",
)
def result_closing(simulation):
    trace = simulation(event(1000, "connect"), until=12_000)
    trace.before("closing", "page_stop")


@case(
    "start-close-publishes-closing",
    "Development/system/design/PORTAL/interfaces-and-behavior.md#form-navigation-and-setup-exit",
    "Publish Closing before stopping the portal server for Start, without adding a result-display delay.",
)
def start_closing(simulation):
    trace = simulation(event(1000, "start"), until=2000)
    trace.before("closing", "page_stop")
    assert trace.last("ack") == 0


FAILURES = WIFI + "specified-failures-and-interrupted-boot"
PORTAL_EXIT = "Development/system/design/PORTAL/interfaces-and-behavior.md#form-navigation-and-setup-exit"


@case(
    "unsolicited-link-cannot-complete-join",
    JOIN,
    "An unsolicited link while a selected join is pending cannot trigger a save; only the join wait result completes it. L1 substitute exposes the link without filtering it.",
)
def unsolicited_link(simulation):
    trace = simulation(
        plan("join", [0], 5000)
        + event(1000, "connect")
        + event(2000, "late_link")
        + event(4000, "snapshot"),
        until=7000,
    )
    assert trace.times("write") == [6000] and trace.times("join_result") == [6000]
    assert trace.values("record_new")[0] == 0 and trace.last("record_new") == 1


for final_start in (False, True):
    if final_start:
        final_command_name = "start"
    else:
        final_command_name = "stop"

    @case(
        "coalesced-start-stop-final-" + final_command_name,
        START,
        "Preserve the final requested mode when Start and Stop arrive together; a final Start tears down, a final Stop remains Idle. CONTROL events are substituted.",
    )
    def coalesced_commands(simulation, final_start=final_start):
        if final_start:
            kinds = ("stop", "start")
        else:
            kinds = ("start", "stop")
        trace = simulation(
            plan("scan", [0], 5000) + "".join(event(1000, kind) for kind in kinds),
            until=7000,
        )
        if final_start:
            expected_acknowledgment = 0
        else:
            expected_acknowledgment = -11
        assert trace.last("ack") == expected_acknowledgment
        assert trace.count("scan_cancel") == int(final_start)
        assert trace.last("page") == int(not final_start)


for stage, start_time, page_started in (
    ("ap", 500, False),
    ("dhcp", 1500, False),
    ("portal", 2500, True),
):

    @case(
        "start-during-" + stage + "-startup",
        START,
        "Start during a bounded service startup waits for that call and cleans every partially started service before release. One-second startup completion is substituted.",
    )
    def start_during_startup(
        simulation, start_time=start_time, page_started=page_started, stage=stage
    ):
        trace = simulation(
            "service_delay 1000\n"
            + event(start_time, "start")
            + event(start_time + 50, "snapshot"),
            until=5000,
        )
        assert trace.values("ack")[0] != 0 and trace.last("ack") == 0
        assert (
            trace.last("page") == 0
            and trace.last("dhcp") == 0
            and trace.last("hotspot") == 0
        )
        assert trace.count("page_start") == int(page_started)
        trace.before("closing", "ap_stop")
        if stage == "ap":
            assert trace.count("dhcp_start") == 0


@case(
    "start-during-closing-notice",
    PORTAL_EXIT,
    "Start interrupts the Cancel notice with no added delay and preserves Closing before teardown.",
)
def start_during_notice(simulation):
    trace = simulation(event(1000, "cancel") + event(1500, "start"), until=3000)
    assert trace.times("closing") == [1000] and trace.times("page_stop") == [1500]
    assert trace.last("ack") == 0


@case(
    "interrupted-boot-counts-issued-attempt",
    FAILURES,
    "An interrupted issued boot attempt consumes one of four; Stop resumes after the five-second gap, exhaustion remains manual boot recovery.",
)
def interrupted_boot_budget(simulation):
    trace = simulation(
        plan("join", [0], 9000)
        + plan("join", [-5] * 3)
        + event(1000, "start")
        + event(3000, "stop")
        + event(25000, "snapshot")
        + event(30000, "hold"),
        until=32000,
        stored=True,
    )
    assert trace.times("join") == [0, 8000, 13100, 18200]
    assert trace.times("scan") == [30000]
    assert (
        "JOIN_FAILURE" in trace.production_log
        and "RECONNECT_FAILURE" not in trace.production_log
    )


@case(
    "start-before-boot-attempt-consumes-none",
    FAILURES,
    "A Start observed before issuing the boot join consumes no attempt; Stop then permits all four after the retry gap.",
)
def boot_before_attempt(simulation):
    trace = simulation(
        plan("join", [-5] * 4) + event(0, "start") + event(1000, "stop"),
        until=25000,
        stored=True,
    )
    assert trace.times("join") == [6000, 11100, 16200, 21300]
    assert trace.count("scan") == 0


@case(
    "invalid-page-connect-rejected",
    WIFI + "service-boundary",
    "A malformed typed Connect never reaches the radio or storage; publish invalid input and rescan. The portal substitute injects a boundary fault that real HTTP rejects with 400.",
)
def invalid_page_connect(simulation):
    trace = simulation(event(1000, "connect", 2), until=3000)
    assert trace.count("join") == 0 and trace.count("write") == 0
    assert trace.values("join_failed") == [-22] and trace.count("scan") == 2


@case(
    "portal-start-independent-failure-manual-retry",
    FAILURES,
    "An HTTP-only start failure reports its cause, closes partial portal/DHCP/AP services, and waits for a new hold. L1 startup failure is substituted.",
)
def independent_portal_failure(simulation):
    trace = simulation(
        "start_failure 3\n" + event(1500, "snapshot") + event(2000, "hold"), until=4000
    )
    assert trace.times("page_start") == [100, 2100]
    assert (
        trace.count("page_stop") == 2
        and trace.count("ap_stop") == 2
        and trace.count("dhcp_stop") == 2
    )
    assert "HOTSPOT_START_FAILURE" in trace.production_log


@case(
    "rescan-exhaustion-retains-station-manual-retry",
    FAILURES,
    "Four failed open-page rescans show SCAN_FAILURE and Closing, close setup, retain the old station, and wait for a new hold.",
)
def rescan_exhaustion_station(simulation):
    trace = simulation(
        plan("scan", [0] + [-5] * 4 + [0])
        + event(1000, "hold")
        + event(2000, "rescan")
        + event(25000, "snapshot")
        + event(30000, "hold"),
        until=32000,
        stored=True,
    )
    assert trace.count("scan") == 6 and trace.count("networks") == 2
    assert trace.times("closing") == [17400] and trace.times("page_stop") == [19400]
    assert trace.values("connected")[0] == 1 and trace.last("connected") == 1
    assert (
        trace.times("page_start") == [1100, 30100]
        and "SCAN_FAILURE" in trace.production_log
    )


for service_name, setting, call_name, failure_name, setup_script, stored in (
    ("portal", "stop_failures", "page_stop", "page_stop_failed", "", False),
    ("dhcp", "dhcp_stop_failures", "dhcp_stop", "dhcp_stop_failed", "", False),
    ("ap", "ap_stop_failures", "ap_stop", "ap_stop_failed", "", False),
    (
        "scan",
        "scan_stop_failures",
        "scan_cancel",
        "scan_cancel_failed",
        plan("scan", [0], 20000),
        False,
    ),
    (
        "disconnect",
        "disconnect_failures",
        "disconnect",
        "disconnect_failed",
        plan("join", [0], 20000),
        True,
    ),
):
    for failure_count in (1, 2, 20):
        exhaust = failure_count == 20
        defect = None
        if service_name in {"scan", "disconnect"}:
            defect = "Implementation defect: initial cancellation bypasses cleanup backoff and is followed by three additional stop passes"

        if exhaust:
            cleanup_case_suffix = "-exhaustion-latch"
        elif failure_count == 2:
            cleanup_case_suffix = "-third-pass-success"
        else:
            cleanup_case_suffix = "-retry-success"

        @case(
            "cleanup-" + service_name + cleanup_case_suffix,
            FAILURES,
            "Each pending stop runs at most three times with one/two-second backoff and one second per stop. Success confirms release; exhaustion latches WIFI_CLEANUP_FAILURE, releases audio and prohibits later Wi-Fi work. L1 stop outcomes and timing are substituted.",
            defect=defect,
        )
        def cleanup_budget(
            simulation,
            setting=setting,
            call_name=call_name,
            failure_name=failure_name,
            setup_script=setup_script,
            stored=stored,
            exhaust=exhaust,
            service_name=service_name,
            failures=failure_count,
        ):
            trace = simulation(
                f"{setting} {failures}\n"
                + setup_script
                + event(1000, "start")
                + event(1500, "snapshot")
                + event(12000, "snapshot")
                + event(13000, "stop")
                + event(14000, "hold")
                + event(15000, "start"),
                until=18000,
                stored=stored,
            )
            attempts = trace.count(failure_name)
            if exhaust:
                expected_attempts = 3
            else:
                expected_attempts = failures
            assert attempts == expected_attempts
            if exhaust:
                assert "WIFI_CLEANUP_FAILURE" in trace.production_log
                if service_name == "scan":
                    expected_scan_count = 1
                elif stored:
                    expected_scan_count = 0
                else:
                    expected_scan_count = 1
                assert trace.count("scan") == expected_scan_count
                assert trace.count("join") == int(stored)
                assert trace.last("ack") == 0
                assert (
                    trace.times(failure_name)[1] - trace.times(failure_name)[0] == 2000
                )
                assert (
                    trace.times(failure_name)[2] - trace.times(failure_name)[1] == 3000
                )
            else:
                assert "WIFI_CLEANUP_FAILURE" not in trace.production_log
                stop_times = sorted(
                    set(trace.times(call_name) + trace.times(failure_name))
                )
                assert stop_times[1] - stop_times[0] == 2000
                if failures == 2:
                    assert stop_times[2] - stop_times[1] == 3000
                assert trace.values("ack")[0] != 0 and trace.values("ack")[1] == 0


@case(
    "control-release-wait-timeout",
    START,
    "The release API returns pending at its bounded timeout while teardown is unconfirmed. CONTROL is represented by a caller; its empty implementation cannot verify audio gating.",
)
def release_wait_timeout(simulation):
    trace = simulation(
        "stop_failures 1\n" + event(1000, "start") + event(1100, "release_wait", 250),
        until=5000,
    )
    assert trace.values("release_wait_result") == [-11]
    assert trace.values("release_wait_elapsed") == [250]
    assert trace.last("ack") == 0


@case(
    "save-warning-close-publishes-closing",
    PORTAL_EXIT,
    "Publish Closing before stopping the server after the ten-second save-warning display.",
)
def warning_closing(simulation):
    trace = simulation("write_failures 2\n" + event(1000, "connect"), until=13000)
    trace.before("closing", "page_stop")


@pytest.mark.parametrize("function,scenario,basis,expected", CASES)
def test_design_scenario(
    function, scenario, basis, expected, simulate, record_property
):
    record_property("scenario", scenario)
    record_property("vt_id", "VT-14")
    record_property("basis", basis)
    record_property("parameters", PARAMETERS)
    record_property("expected", expected)
    function(simulate)


@pytest.fixture(scope="session")
def memory_executable(executable, host_build_directory):
    _, previous_command, version, revision = executable
    if sys.platform == "win32":
        executable_name = "memory.exe"
    else:
        executable_name = "memory"
    target = host_build_directory("l2", "communication-memory") / executable_name
    command = previous_command.copy()
    source_index = command.index(str(HERE / "simulation.c"))
    command[source_index : source_index + 2] = [
        str(HERE / "communication_memory_harness.c")
    ]
    command[-1] = str(target)
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    return target, command, version, revision


MEMORY_CASES = [
    pytest.param(
        "stored-read-failure-erases-working-record",
        "read_error -5\n",
        True,
        2000,
        "stored_buffer_cleared",
        FAILURES,
        "An unreadable partially returned record is cleared from L2 working memory, never joined and preserves flash for diagnosis. Storage failure and clock are substituted; a white-box probe observes erasure.",
        marks=pytest.mark.xfail(
            strict=True,
            raises=AssertionError,
            reason="Implementation defect: a failed storage_read leaves its partially filled credential record in L2 working memory",
        ),
        id="stored-read-failure-erases-working-record",
    ),
    pytest.param(
        "invalid-record-erases-working-record",
        "",
        2,
        2000,
        "stored_buffer_cleared",
        FAILURES,
        "Clear an invalid stored record from working memory without a join or flash write. Storage and clock are substituted; a white-box probe observes erasure.",
        id="invalid-record-erases-working-record",
    ),
]


def test_coalesced_start_stop_resumes_boot(memory_executable, record_property):
    record_property("scenario", "coalesced-start-stop-resumes-boot-after-five-seconds")
    record_property("vt_id", "VT-14")
    record_property("basis", FAILURES)
    record_property(
        "expected",
        "An interrupted boot pending in Idle resumes after the five-second gap when Start and Stop both precede the worker's next check. A white-box harness seeds the pending-boot boundary; L1 and clock are substituted.",
    )
    target, command, version, revision = memory_executable
    record_property("source_revision", revision)
    record_property("compiler_version", version)
    record_property("compiler_command", subprocess.list2cmdline(command))
    result = subprocess.run(
        [str(target), "coalesced-boot-resume"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    trace = Trace(result.stdout)
    assert trace.times("join") == [RETRY]
    assert trace.last("connected") == 1 and trace.count("scan") == 0


for name, script in (
    ("success", event(1000, "connect", 1)),
    ("failure", plan("join", [-13]) + event(1000, "connect", 1)),
    (
        "start-interruption",
        plan("join", [0], 5000) + event(1000, "connect", 1) + event(1500, "start"),
    ),
):
    MEMORY_CASES.append(
        pytest.param(
            "consumed-password-erased-" + name,
            script,
            False,
            3000,
            "request_password_cleared",
            "Development/system/design/PORTAL/interfaces-and-behavior.md#requests-and-published-state",
            "L2 clears the consumed request password after join/save, failure or Start interruption. L1 and clock are substituted; a white-box probe observes the caller buffer.",
            id="consumed-password-erased-" + name,
        )
    )


@pytest.mark.parametrize(
    "scenario,script,stored,until,observation,basis,expected", MEMORY_CASES
)
def test_communication_memory(
    scenario,
    script,
    stored,
    until,
    observation,
    basis,
    expected,
    memory_executable,
    record_property,
):
    for name, value in (
        ("scenario", scenario),
        ("vt_id", "VT-14"),
        ("basis", basis),
        ("expected", expected),
    ):
        record_property(name, value)
    simulation = create_simulation_runner(memory_executable, record_property)
    trace = simulation(script, until=until, stored=stored)
    if observation == "stored_buffer_cleared":
        assert (
            trace.count("join") == 0
            and trace.count("write") == 0
            and trace.last("page") == 1
        )
        if stored is True:
            assert trace.last("record_old") == 1
    assert trace.last(observation) == 1
