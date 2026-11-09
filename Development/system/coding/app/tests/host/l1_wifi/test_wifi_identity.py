"""VT-15: L1 physical device identity from the factory station MAC."""

import pytest

IDENTITY = (
    "Development/system/design/WIFI/interfaces-and-behavior.md#physical-device-identity"
)
BINDING = "Development/system/design/COMMUNICATION/server-communication.md#physical-identity-and-server-binding"
FACTORY_MAC = "modules/hal/espressif/components/esp_hw_support/mac_addr.c, esp_efuse_mac_get_default and generate_mac (ESP_MAC_WIFI_STA is the base MAC)"

# Output: <result> <identifier or -> <untouched beyond size> <terminated> <factory MAC reads>
CASES = [
    ("typical", "7CDFA10B2C3D 20", "OK stetho-7CDFA10B2C3D 1 1 1", BINDING),
    ("uppercase-hex", "f4cdef0a1b2c 20", "OK stetho-F4CDEF0A1B2C 1 1 1", BINDING),
    ("leading-zero-digits", "000102030405 20", "OK stetho-000102030405 1 1 1", BINDING),
    ("first-byte-first", "0C0B0A090807 20", "OK stetho-0C0B0A090807 1 1 1", BINDING),
    (
        "locally-administered-unicast",
        "02AABBCCDDEE 20",
        "OK stetho-02AABBCCDDEE 1 1 1",
        IDENTITY,
    ),
    ("larger-buffer", "7CDFA10B2C3D 64", "OK stetho-7CDFA10B2C3D 1 1 1", IDENTITY),
    ("size-one-short", "7CDFA10B2C3D 19", "EINVAL - 1 1 0", IDENTITY),
    ("size-zero", "7CDFA10B2C3D 0", "EINVAL - 1 1 0", IDENTITY),
    ("null-output", "7CDFA10B2C3D 20 null", "EINVAL - 1 0 0", IDENTITY),
    ("read-error", "7CDFA10B2C3D 20 read-error", "EIO - 1 1 1", FACTORY_MAC),
    ("all-zero", "000000000000 20", "ENODATA - 1 1 1", BINDING),
    ("all-ones", "FFFFFFFFFFFF 20", "ENODATA - 1 1 1", IDENTITY),
    ("multicast", "017CDFA10B2C 20", "ENODATA - 1 1 1", IDENTITY),
    ("multicast-odd-first-byte", "AB0000000001 20", "ENODATA - 1 1 1", IDENTITY),
]


@pytest.mark.parametrize(
    "scenario,argument,expected,basis",
    [pytest.param(*case, id=case[0]) for case in CASES],
)
def test_device_identifier(
    scenario, argument, expected, basis, service, record_property
):
    for name, value in (
        ("scenario", "wifi-device-identifier-" + scenario),
        ("vt_id", "VT-15"),
        ("basis", basis),
        ("expected", expected),
    ):
        record_property(name, value)
    output = service("wifi", "device-identifier", argument)
    assert output.split() == expected.split()


# Output: <wifi_startHotspot result> <hotspot name or - if never enabled> <factory MAC reads>
HOTSPOT_CASES = [
    ("same-mac-as-identifier", "ok", "0 Stetho-7CDFA10B2C3D 1"),
    ("no-hotspot-without-identity", "read-error", "-5 - 1"),
]


@pytest.mark.parametrize(
    "scenario,argument,expected",
    [pytest.param(*case, id=case[0]) for case in HOTSPOT_CASES],
)
def test_hotspot_name_uses_identifier(
    scenario, argument, expected, service, record_property
):
    for name, value in (
        ("scenario", "wifi-hotspot-name-" + scenario),
        ("vt_id", "VT-15"),
        ("basis", BINDING),
        ("expected", expected),
    ):
        record_property(name, value)
    output = service("wifi", "hotspot-name", argument)
    assert output.split() == expected.split()
