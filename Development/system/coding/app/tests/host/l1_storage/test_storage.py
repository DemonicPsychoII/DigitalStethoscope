"""VT-08/VT-09: L1 server profile image reader from the flash layout and server profile design.

Images are built from the version 1 field table of the design, not with the host
tool: server_profile.py imports the third-party cryptography package.
"""

import struct
import zlib

import pytest

LAYOUT = "Development/system/design/STORAGE/interfaces-and-behavior.md#flash-layout"
PROFILE = "Development/system/design/STORAGE/server-profile.md#"
DEVICE = PROFILE + "device-behavior"
LIMITS = PROFILE + "parameters (P28-LIMITS, P28-IMAGE, P28-PARTITION)"
INTERFACE = "Development/system/coding/app/L1_services/L1_STORAGE/storage.h (storage_readServerProfile contract)"
# server-profile.md, verification allocation: valid deployment file read by the firmware reader.
VALID_VT = "VT-08"
# server-profile.md, verification allocation: missing or corrupted image at boot.
INVALID_VT = "VT-08, VT-09"

BASE_URL = b"https://192.0.2.40:8443/fhir"
KEEP_ALIVE_SECONDS = 600
BASE_URL_MAXIMUM_LENGTH = 256
CERTIFICATE_MAXIMUM_LENGTH = 8192
MAXIMUM_IMAGE_SIZE = 8465


def certificate(length):
    """PEM-shaped text of exactly length bytes; the reader leaves its content uninterpreted."""
    begin = b"-----BEGIN CERTIFICATE-----\n"
    end = b"\n-----END CERTIFICATE-----\n"
    return begin + b"A" * (length - len(begin) - len(end)) + end


CERTIFICATE = certificate(1399)


def image(
    base_url=BASE_URL,
    keep_alive=KEEP_ALIVE_SECONDS,
    certificate_text=CERTIFICATE,
    magic=b"STPV",
    version=1,
):
    body = (
        magic
        + bytes([version])
        + struct.pack("<H", len(base_url))
        + base_url
        + struct.pack("<I", keep_alive)
        + struct.pack("<H", len(certificate_text))
        + certificate_text
    )
    return body + struct.pack("<I", zlib.crc32(body))


def flipped(data, offset):
    corrupted = bytearray(data)
    corrupted[offset] ^= 0x01
    return bytes(corrupted)


def accepted(
    base_url=BASE_URL, keep_alive=KEEP_ALIVE_SECONDS, certificate_text=CERTIFICATE
):
    return {
        "result": "0",
        "base_url": base_url.hex(),
        "base_url_terminated": "1",
        "keep_alive": str(keep_alive),
        "certificate": certificate_text.hex(),
        "certificate_length": str(len(certificate_text)),
        "certificate_terminated": "1",
    }


INVALID = {"result": "EBADMSG", "cleared": "1"}
VALID = image()
CRC_OFFSET = len(VALID) - 4

CASES = [
    (
        "valid",
        VALID,
        None,
        accepted(),
        LAYOUT + "; " + DEVICE,
        "A version 1 image with a correct CRC-32 is accepted; base URL, keep-alive and certificate are returned as terminated text with the certificate length.",
        VALID_VT,
    ),
    (
        "valid-maximum-lengths",
        image(
            base_url=b"https://" + b"h" * (BASE_URL_MAXIMUM_LENGTH - 8),
            certificate_text=certificate(CERTIFICATE_MAXIMUM_LENGTH),
        ),
        None,
        accepted(
            base_url=b"https://" + b"h" * (BASE_URL_MAXIMUM_LENGTH - 8),
            certificate_text=certificate(CERTIFICATE_MAXIMUM_LENGTH),
        ),
        LAYOUT + "; " + LIMITS,
        "A 256-byte base URL and an 8,192-byte certificate (the 8,465-byte largest image) are accepted.",
        VALID_VT,
    ),
    (
        "keep-alive-below-minimum-left-to-communication",
        image(keep_alive=5),
        None,
        accepted(keep_alive=5),
        LAYOUT,
        "The reader checks only the structure: a CRC-valid image with a 5-second keep-alive is returned; COMMUNICATION rejects it.",
        VALID_VT,
    ),
    (
        "content-left-to-wifi",
        image(
            base_url=b"http://not-a-canonical-url",
            certificate_text=b"not a certificate",
        ),
        None,
        accepted(
            base_url=b"http://not-a-canonical-url",
            certificate_text=b"not a certificate",
        ),
        LAYOUT + "; " + INTERFACE,
        "Endpoint and certificate are returned as text without content checks; WIFI rejects an unusable URL or certificate.",
        VALID_VT,
    ),
    (
        "erased-missing",
        None,
        None,
        {"result": "ENOENT", "cleared": "1"},
        DEVICE + "; " + INTERFACE,
        "An erased partition is a missing image (server-profile.md and storage.h; the flash layout section calls erased flash invalid) and the output is cleared.",
        INVALID_VT,
    ),
    (
        "unknown-magic",
        image(magic=b"STPW"),
        None,
        INVALID,
        LAYOUT + "; " + DEVICE,
        "An unknown magic makes the image invalid and clears the output.",
        INVALID_VT,
    ),
    (
        "version-0",
        image(version=0),
        None,
        INVALID,
        LAYOUT + "; " + DEVICE,
        "Format version 0 is unknown; the image is invalid and the output is cleared.",
        INVALID_VT,
    ),
    (
        "version-2",
        image(version=2),
        None,
        INVALID,
        LAYOUT + "; " + DEVICE,
        "Format version 2 is unknown to this firmware; the image is invalid and the output is cleared.",
        INVALID_VT,
    ),
    (
        "base-url-length-257",
        image(base_url=b"https://" + b"h" * (BASE_URL_MAXIMUM_LENGTH - 7)),
        None,
        INVALID,
        LAYOUT + "; " + LIMITS,
        "A 257-byte base URL with a correct CRC-32 is an out-of-range length; the image is invalid and the output is cleared.",
        INVALID_VT,
    ),
    (
        "certificate-length-8193",
        image(certificate_text=certificate(CERTIFICATE_MAXIMUM_LENGTH + 1)),
        None,
        INVALID,
        LAYOUT + "; " + LIMITS,
        "An 8,193-byte certificate with a correct CRC-32 is an out-of-range length; the image is invalid and the output is cleared.",
        INVALID_VT,
    ),
    (
        "crc-flipped",
        flipped(VALID, CRC_OFFSET),
        None,
        INVALID,
        LAYOUT + "; " + DEVICE,
        "A flipped CRC-32 bit is a CRC mismatch; the image is invalid and the output is cleared.",
        INVALID_VT,
    ),
    (
        "payload-flipped",
        flipped(VALID, 4 + 1 + 2 + 3),
        None,
        INVALID,
        LAYOUT + "; " + DEVICE,
        "A flipped base URL bit under the original CRC-32 is a CRC mismatch; the image is invalid and the output is cleared.",
        INVALID_VT,
    ),
    (
        "missing-crc",
        VALID[:CRC_OFFSET],
        None,
        INVALID,
        LAYOUT + "; " + DEVICE,
        "An image whose CRC-32 field is still erased is a CRC mismatch; the image is invalid and the output is cleared.",
        INVALID_VT,
    ),
    (
        "flash-read-error-first-field",
        VALID,
        0,
        {"result": "EIO", "cleared": "1"},
        INTERFACE,
        "A flash driver error while reading the magic is returned unchanged and the output is cleared.",
        INVALID_VT,
    ),
    (
        "flash-read-error-crc",
        VALID,
        CRC_OFFSET,
        {"result": "EIO", "cleared": "1"},
        INTERFACE,
        "A flash driver error while reading the CRC-32 is returned unchanged and the output is cleared, although every earlier field was read.",
        INVALID_VT,
    ),
    (
        "null-destination",
        "null",
        None,
        {"result": "EINVAL"},
        INTERFACE,
        "A NULL destination returns -EINVAL.",
        INVALID_VT,
    ),
]


# P28-PARTITION states the largest image size; the field table above must produce it.
assert len(CASES[1][1]) == MAXIMUM_IMAGE_SIZE


@pytest.mark.parametrize(
    "name,data,error_offset,expected,basis,description,vt",
    [pytest.param(*case, id=case[0]) for case in CASES],
)
def test_server_profile_reader(
    name,
    data,
    error_offset,
    expected,
    basis,
    description,
    vt,
    service,
    record_property,
    tmp_path,
):
    for property_name, value in (
        ("scenario", "storage-server-profile-" + name),
        ("vt_id", vt),
        ("basis", basis),
        ("expected", description),
    ):
        record_property(property_name, value)
    if data is None:
        argument = "erased"
    elif data == "null":
        argument = "null"
    else:
        path = tmp_path / "server-profile.bin"
        path.write_bytes(data)
        argument = str(path)
    if error_offset is not None:
        argument += f" {error_offset}"
    output = service("storage", "server-profile", argument)
    actual = dict(token.split("=", 1) for token in output.split())
    mismatches = {
        key: (actual.get(key), value)
        for key, value in expected.items()
        if actual.get(key) != value
    }
    assert not mismatches, output
