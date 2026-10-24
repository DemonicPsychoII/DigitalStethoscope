"""VT-14: L1 expectations from Wi-Fi service and selection design."""

import pytest

WIFI = "Development/system/design/WIFI/interfaces-and-behavior.md#"
SERVICE = WIFI + "service-boundary"
ENTRY = WIFI + "entry-scan-and-recovery"
DRIVER = "https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/wifi/esp32/src/esp_wifi_drv.c#L487-L528"
DHCP = "https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/dhcpv4/dhcpv4.c#L1997-L2023"
CASES = []


def add(scenario, operation, argument, expected, basis, description):
    CASES.append(
        pytest.param(
            scenario, operation, argument, expected, basis, description, id=scenario
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
        ENTRY,
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


@pytest.mark.parametrize(
    "scenario,operation,argument,expected,basis,description", CASES
)
def test_wifi_service(
    scenario,
    operation,
    argument,
    expected,
    basis,
    description,
    service,
    record_property,
):
    for name, value in (
        ("scenario", scenario),
        ("vt_id", "VT-14"),
        ("basis", basis),
        ("expected", description),
    ):
        record_property(name, value)
    output = service("wifi", operation, argument)
    if expected is not None:
        assert int(output) == expected
