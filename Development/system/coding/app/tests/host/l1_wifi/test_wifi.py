"""VT-14: L1 expectations from Wi-Fi service and selection design.

SNTP cases carry the VT that the time synchronization design traces them to.
"""

import pytest

WIFI = "Development/system/design/WIFI/interfaces-and-behavior.md#"
SERVICE = WIFI + "service-boundary"
ENTRY = WIFI + "supported-networks"
CACHE = WIFI + "failure-boundaries-and-bounded-results"
TIME_DESIGN = "Development/system/design/COMMUNICATION/time-synchronization.md#"
TIME = TIME_DESIGN + "clock-mapping-and-native-behavior"
TIME_INTERFACE = TIME_DESIGN + "ownership-and-proposed-interfaces"
TIME_FLOW = TIME_DESIGN + "flow-and-scheduling"
TIME_TRACE = TIME_DESIGN + "limitations-and-verification"
STOP_BOUND = "Development/system/design/COMMUNICATION/parameters.md (P23 cleanup: each stop bounded to 1 s)"
DRIVER = "https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/wifi/esp32/src/esp_wifi_drv.c#L487-L528"
DHCP = "https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/dhcpv4/dhcpv4.c#L1997-L2023"
WIFI_VT = "VT-14"
# time-synchronization.md, verification table: successful exchange and native units.
TIME_SUCCESS_VT = "VT-07, VT-08"
# time-synchronization.md, verification table: DNS failure, blocked UDP, rejected response; Start race.
TIME_FAILURE_VT = "VT-08, VT-09"
# time-synchronization.md, verification table: cleanup fault.
TIME_CLEANUP_VT = "VT-08, VT-09, VT-11"
CASES = []


def add(scenario, operation, argument, expected, basis, description, vt=WIFI_VT):
    CASES.append(
        pytest.param(
            scenario,
            operation,
            argument,
            expected,
            basis,
            description,
            vt,
            id=scenario,
        )
    )


for name, password, valid in (
    ("open", "", True),
    ("passphrase-7", "p" * 7, False),
    ("passphrase-8", "p" * 8, True),
    ("passphrase-63", "p" * 63, True),
    ("hex-key-64", "0123456789ABCDEF" * 4, True),
    ("nonhex-key-64", "g" * 64, False),
    ("null", "null", False),
    ("empty-name", "empty-name", False),
    ("unterminated-name", "unterminated-name", False),
    ("unterminated-password", "unterminated-password", False),
):
    add(
        "wifi-input-" + name,
        "validity",
        password,
        int(valid),
        SERVICE,
        "Accept only a terminated nonempty SSID and empty password, 8–63 passphrase bytes or 64 hex digits; leave input unchanged.",
    )
for security, name, count in (
    (0, "open", 1),
    (1, "wpa2-psk", 1),
    (2, "wpa1", 0),
    (3, "wpa2-sha256", 0),
    (4, "wpa3-sae", 0),
    (5, "enterprise", 0),
    (6, "wep", 0),
):
    add(
        "wifi-security-" + name,
        "security",
        str(security),
        count,
        ENTRY,
        "List open and WPA2-PSK only; exclude unsupported security types.",
    )
for scenario, operation, basis, description in (
    (
        "wifi-retained-dhcp-address-cannot-complete-new-join",
        "retained-address",
        SERVICE,
        "The different selected network stays pending until its own address arrives, even if the old DHCP lease survives disconnection. Substitute fidelity: ESP32 disconnect and DHCP stop in REBINDING ("
        + DRIVER
        + "; "
        + DHCP
        + ").",
    ),
    (
        "wifi-disconnect-request-failure-retry",
        "disconnect-request-failure",
        SERVICE,
        "A failed disconnect request leaves the join cancelled and permits a later confirmed disconnect followed by a new join. Substitute fidelity: "
        + DRIVER
        + ".",
    ),
    (
        "wifi-strongest-distinct-cache",
        "strongest",
        CACHE,
        "Keep the strongest 16 distinct SSIDs; a stronger duplicate updates its entry and a weaker duplicate cannot replace it.",
    ),
    (
        "wifi-late-scan-and-rearm",
        "cancelled-scan",
        SERVICE,
        "Reject late results after cancellation; block rearm until SCAN_DONE; the new scan contains only its own result. Driver callbacks are untagged substitutes; production L1 rejects them.",
    ),
    (
        "wifi-late-join-and-disconnect-rearm",
        "disconnect-before-rearm",
        SERVICE,
        "Reject old connect and address events during cancellation; no rearm before DISCONNECT_RESULT. Untagged driver callbacks exercise production L1.",
    ),
    (
        "wifi-scan-cancel-1-second-confirmation",
        "scan-cancel-confirmed",
        SERVICE,
        "Accept SCAN_DONE at the one-second cancel budget and permit the next scan.",
    ),
    (
        "wifi-disconnect-1-second-confirmation",
        "disconnect-confirmed",
        SERVICE,
        "Accept terminal disconnect confirmation at one second before permitting the next connect. The connecting-station substitute reports connect failure, following "
        + DRIVER
        + ".",
    ),
    (
        "wifi-old-link-cleared-before-join",
        "old-link",
        SERVICE,
        "Disconnect the existing station before accepting a new join; an old address cannot complete it.",
    ),
    (
        "wifi-one-associated-hotspot-client",
        "hotspot-client-limit",
        "Development/system/design/WIFI/parameters.md",
        "Request one associated AP client through the vendor adapter; association enforcement remains a target check.",
    ),
    (
        "wifi-deleted-record",
        "deleted-record",
        SERVICE,
        "A zero-length deleted settings record returns -ENOENT without modifying the caller buffer; the settings callback is substituted.",
    ),
):
    add(scenario, operation, "", None, basis, description)

for state in ("idle", "connected", "connecting"):
    add(
        "wifi-join-from-" + state,
        "join-from-state",
        state,
        None,
        SERVICE,
        "Join the selected network from "
        + state
        + "; disconnect existing work first and succeed only with the new address. Substitute fidelity: connected disconnect reports nonzero USER_REQUEST; idle/connecting disconnect reports connect failure ("
        + DRIVER
        + ").",
    )


for failure in ("enable", "get-configuration", "set-configuration", "dhcp"):
    add(
        "wifi-hotspot-immediate-rollback-" + failure,
        "hotspot-rollback",
        failure,
        None,
        SERVICE,
        "A partially failed AP/DHCP start or vendor configuration immediately stops DHCP and disables the AP before returning the original error; no L2 cleanup or clock advance is needed.",
    )

for boundary in ("before-ipv4", "online", "requested"):
    add(
        "wifi-disconnect-address-boundary-" + boundary,
        "disconnect-at-address-boundary",
        boundary,
        None,
        SERVICE,
        "A disconnect before IPv4 terminates the pending join immediately, ignores late IPv4 and permits a new attempt; established link loss and requested cancellation do not publish a join failure.",
    )


for name, response, expected, description, vt in (
    (
        "synchronized-stratum-1",
        "0 1 250",
        "1 1",
        "A response with leap indicator 0 and stratum 1 is parsed and normalized.",
        TIME_SUCCESS_VT,
    ),
    (
        "leap-warning-stratum-15",
        "2 15 250",
        "1 1",
        "A leap warning (indicator 2) from stratum 15 is still synchronized and is parsed and normalized.",
        TIME_SUCCESS_VT,
    ),
    (
        "leap-indicator-3",
        "3 2 250",
        "0 0",
        "Leap indicator 3 (alarm, clock not synchronized) fails the exchange on receipt without parsing.",
        TIME_FAILURE_VT,
    ),
    (
        "stratum-0",
        "0 0 250",
        "0 0",
        "Stratum 0 (kiss-o'-death or unspecified) fails the exchange on receipt without parsing.",
        TIME_FAILURE_VT,
    ),
    (
        "stratum-16",
        "0 16 250",
        "0 0",
        "Stratum 16 (reserved) fails the exchange on receipt without parsing.",
        TIME_FAILURE_VT,
    ),
    (
        "before-check",
        "0 2 0",
        "0 1",
        "A response the query parses before the server state check cannot succeed.",
        TIME_FAILURE_VT,
    ),
):
    add(
        "wifi-time-response-" + name,
        "time-response",
        response,
        expected,
        TIME,
        description
        + " The SNTP parser substitute checks no header field; the query uses a zero receive timeout.",
        vt,
    )


@pytest.mark.parametrize(
    "scenario,operation,argument,expected,basis,description,vt", CASES
)
def test_wifi_service(
    scenario,
    operation,
    argument,
    expected,
    basis,
    description,
    vt,
    service,
    record_property,
):
    for name, value in (
        ("scenario", scenario),
        ("vt_id", vt),
        ("basis", basis),
        ("expected", description),
    ):
        record_property(name, value)
    output = service("wifi", operation, argument)
    if expected is not None:
        assert output.split() == str(expected).split()


AT_MOST = "<="
DIFFERENT_FROM = "!="
TERMINAL_WITHOUT_SAMPLE = {"wait_terminal_failure": "1", "sample_untouched": "1"}
QUIESCENT_AFTERWARDS = {"final_cancel": "0", "restart": "0"}
CANCEL_FAILS_WITHIN_STOP_BOUND = {
    "running_cancel_failed": "1",
    "cancel_milliseconds": (AT_MOST, 1000),
    "start_while_cancelling": "EBUSY",
}
NATIVE_SECONDS = "1793836800"

TIME_CASES = [
    (
        "wifi-time-start-while-pending-busy",
        "time-start-busy",
        "",
        {"first_start": "0", "second_start": "EBUSY"},
        TIME_INTERFACE,
        "Start accepts at most one pending operation; a second Start while it is pending returns busy.",
        TIME_FAILURE_VT,
    ),
    (
        "wifi-time-cancel-inactive-idempotent",
        "time-cancel-inactive",
        "",
        {"first_cancel": "0", "second_cancel": "0", "cancel_milliseconds": "0"},
        TIME_INTERFACE,
        "Cancel without an operation is idempotent: it returns success twice without waiting.",
        TIME_FAILURE_VT,
    ),
    (
        "wifi-time-cancel-before-worker",
        "time-cancel-before-worker",
        "",
        {
            "start": "0",
            "cancel": "0",
            "cancel_milliseconds": (AT_MOST, 1000),
            **TERMINAL_WITHOUT_SAMPLE,
            "lookups": "0",
            "sockets_opened": "0",
            "requests": "0",
            "after_worker_wait_terminal_failure": "1",
            "after_worker_sample_untouched": "1",
            "restart": "0",
        },
        TIME_INTERFACE + "; " + STOP_BOUND,
        "Cancel of an accepted operation before its worker ran confirms quiescence within the stop bound and publishes one terminal result without a sample; "
        "the worker that runs afterwards neither resolves, opens a socket nor sends, and a new Start is accepted.",
        TIME_FAILURE_VT,
    ),
    (
        "wifi-time-cancel-during-lookup-fails-within-stop-bound",
        "time-cancel-during-lookup",
        "pending",
        {
            "start": "0",
            **CANCEL_FAILS_WITHIN_STOP_BOUND,
            "lookup_cancellations": "1",
            "sockets_opened": "0",
            "requests": "0",
            **TERMINAL_WITHOUT_SAMPLE,
            **QUIESCENT_AFTERWARDS,
        },
        TIME_INTERFACE + "; " + TIME_FLOW + "; " + STOP_BOUND,
        "While the worker cannot release within the 1 s stop bound, Cancel returns failure by the bound instead of acknowledging release and Start stays busy; "
        "the worker then cancels the DNS query, sends nothing and publishes a terminal result without a sample, after which Cancel confirms and Start is accepted. "
        "Cancel and the worker interleave at one worker unlock; the single-threaded substitute cannot show a worker that releases within the bound.",
        TIME_CLEANUP_VT,
    ),
    (
        "wifi-time-late-lookup-answer-during-cancellation",
        "time-cancel-during-lookup",
        "late-answer",
        {
            "start": "0",
            **CANCEL_FAILS_WITHIN_STOP_BOUND,
            "sockets_opened": "0",
            "requests": "0",
            **TERMINAL_WITHOUT_SAMPLE,
            **QUIESCENT_AFTERWARDS,
        },
        TIME_INTERFACE + "; " + STOP_BOUND,
        "A DNS answer that arrives after cancellation invalidated the operation cannot start the exchange or publish a sample.",
        TIME_CLEANUP_VT,
    ),
    (
        "wifi-time-late-response-during-cancellation",
        "time-cancel-during-exchange",
        "",
        {
            "start": "0",
            **CANCEL_FAILS_WITHIN_STOP_BOUND,
            "requests": "1",
            "responses_parsed": "1",
            "sockets_closed": "1",
            **TERMINAL_WITHOUT_SAMPLE,
            **QUIESCENT_AFTERWARDS,
        },
        TIME_INTERFACE + "; " + STOP_BOUND,
        "An SNTP response received after cancellation invalidated the operation cannot publish a sample; the socket is closed once and no request is resent.",
        TIME_CLEANUP_VT,
    ),
    (
        "wifi-time-single-request-native-units",
        "time-single-request",
        "350 " + NATIVE_SECONDS + " 999999 50000",
        {
            "start": "0",
            "lookup_name": "pool.ntp.org",
            "server_address": "192.0.2.123",
            "server_port": "123",
            "requests": "1",
            "wait": "0",
            "utc_seconds": NATIVE_SECONDS,
            "utc_fraction_nanoseconds": "999999000",
            "receive_monotonic_microseconds": "350000",
            "uncertainty_microseconds": "50000",
            "repeated_wait_same": "1",
            "requests_after_waits": "1",
        },
        TIME_INTERFACE + "; " + TIME + "; " + TIME_DESIGN + "parameters (P25-SERVER)",
        "The hostname is resolved to IPv4 and exactly one UDP/123 request is sent; the pinned microsecond fraction 999,999 becomes 999,999,000 ns, "
        "the receive time is the kernel monotonic time at reception and the uncertainty stays in microseconds; waiting again returns the same result without a new request.",
        TIME_SUCCESS_VT,
    ),
    (
        "wifi-time-single-request-zero-fraction",
        "time-single-request",
        "120 " + NATIVE_SECONDS + " 0 100000",
        {
            "requests": "1",
            "wait": "0",
            "utc_seconds": NATIVE_SECONDS,
            "utc_fraction_nanoseconds": "0",
            "receive_monotonic_microseconds": "120000",
            "uncertainty_microseconds": "100000",
            "requests_after_waits": "1",
        },
        TIME_INTERFACE + "; " + TIME,
        "A zero microsecond fraction normalizes to 0 ns and the Zephyr uncertainty estimate is passed on unchanged in microseconds.",
        TIME_SUCCESS_VT,
    ),
    (
        "wifi-time-no-response-no-resend",
        "time-single-request",
        "none 0 0 0",
        {
            "start": "0",
            "requests": "1",
            **TERMINAL_WITHOUT_SAMPLE,
            "repeated_wait_same": "1",
            "requests_after_waits": "1",
        },
        TIME_INTERFACE + "; " + TIME_FLOW,
        "Without a response the operation ends with a terminal result without a sample after exactly one request; neither the worker nor waiting resends.",
        TIME_FAILURE_VT,
    ),
    (
        "wifi-time-apply-advances-with-carry",
        "time-apply",
        NATIVE_SECONDS + " 900000000 1000000 2350 50000 ok",
        {
            "apply": "0",
            "clock_set_calls": "1",
            "clock_is_realtime": "1",
            "clock_seconds": "1793836802",
            "clock_nanoseconds": "250000000",
            "anchor_seconds": "1793836802",
            "anchor_fraction_nanoseconds": "250000000",
            "anchor_monotonic_microseconds": "2350000",
            "anchor_uncertainty_microseconds": "50000",
        },
        TIME_INTERFACE + "; " + TIME,
        "The sample received at 1 s is advanced by the 1.35 s elapsed monotonic time with subsecond carry (0.9 s + 0.35 s) before Zephyr real time is set; "
        "the anchor pairs the applied UTC with the monotonic time of application.",
        TIME_SUCCESS_VT,
    ),
    (
        "wifi-time-apply-carry-to-whole-second",
        "time-apply",
        NATIVE_SECONDS + " 900000000 1000000 1100 50000 ok",
        {
            "apply": "0",
            "clock_seconds": "1793836801",
            "clock_nanoseconds": "0",
            "anchor_seconds": "1793836801",
            "anchor_fraction_nanoseconds": "0",
            "anchor_monotonic_microseconds": "1100000",
        },
        TIME_INTERFACE + "; " + TIME,
        "A fraction that reaches exactly one second after advancing carries into the seconds and leaves 0 ns.",
        TIME_SUCCESS_VT,
    ),
    (
        "wifi-time-apply-clock-set-failure-no-anchor",
        "time-apply",
        NATIVE_SECONDS + " 900000000 1000000 2350 50000 EIO",
        {
            "apply": (DIFFERENT_FROM, "0"),
            "clock_set_calls": "1",
            "anchor_untouched": "1",
        },
        TIME_INTERFACE + "; " + TIME_FLOW,
        "When setting Zephyr real time fails, apply fails and publishes no anchor.",
        TIME_FAILURE_VT,
    ),
]


def matches(actual, expected):
    if isinstance(expected, tuple):
        comparison, value = expected
        if comparison == AT_MOST:
            return actual is not None and int(actual) <= value
        return actual is not None and actual != value
    return actual == expected


@pytest.mark.parametrize(
    "scenario,operation,argument,expected,basis,description,vt",
    [pytest.param(*case, id=case[0]) for case in TIME_CASES],
)
def test_time_synchronization(
    scenario,
    operation,
    argument,
    expected,
    basis,
    description,
    vt,
    service,
    record_property,
):
    for name, value in (
        ("scenario", scenario),
        ("vt_id", vt),
        ("basis", basis),
        ("expected", description),
    ):
        record_property(name, value)
    output = service("wifi", operation, argument)
    actual = dict(token.split("=", 1) for token in output.split())
    mismatches = {
        key: (actual.get(key), value)
        for key, value in expected.items()
        if not matches(actual.get(key), value)
    }
    assert not mismatches, output
