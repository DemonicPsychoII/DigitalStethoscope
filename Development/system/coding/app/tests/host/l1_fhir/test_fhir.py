"""VT-07/VT-08: L1_FHIR bounded serialization from the server-communication design."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess

import pytest

import host_build

HERE = Path(__file__).resolve().parent
DESIGN = "Development/system/design/COMMUNICATION/server-communication.md#"
REGISTRATION = DESIGN + "registration-flow-and-recovery"
IDENTITY = DESIGN + "physical-identity-and-server-binding"
BUFFERS = DESIGN + "parameters-and-outstanding-evidence"
JSON_ESCAPING = "https://www.rfc-editor.org/rfc/rfc8259#section-7"

IDENTIFIER = "stetho-A1B2C3D4E5F6"
DEVICE_BODY = (
    '{"resourceType":"Device","identifier":[{"system":"urn:stethoscope:device",'
    '"value":"stetho-A1B2C3D4E5F6"}],"status":"active"}'
)
CONDITION = "identifier=urn%3Astethoscope%3Adevice|stetho-A1B2C3D4E5F6"


@pytest.fixture(scope="module")
def harness(host_build_directory):
    target = host_build.build(
        host_build_directory("unit", "fhir"), "fhir", [HERE / "fhir_harness.c"]
    ).path

    def run(operation, value, capacity, *extra):
        arguments = [str(target), operation, value, str(capacity)]
        arguments += [str(item) for item in extra]
        completed = subprocess.run(
            arguments, capture_output=True, text=True, timeout=10
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        return completed.stdout.split()

    return run


def evidence(record_property, scenario, basis, expected):
    record_property("scenario", scenario)
    record_property("vt_id", "VT-07, VT-08")
    record_property("basis", basis)
    record_property("expected", expected)


def check(fields, result, text):
    name, length, output, canary_is_intact, is_terminated = fields
    assert name == result
    assert canary_is_intact == "1", "wrote beyond the given capacity"
    assert is_terminated == "1", "output is not NUL-terminated inside the capacity"
    if result == "OK":
        assert bytes.fromhex(output).decode("latin-1") == text
        assert int(length) == len(text.encode("latin-1"))
    else:
        assert output == "-", "failure left partial output"
        assert length == "0"


SUCCESS_CASES = [
    pytest.param("device", 2048, DEVICE_BODY, id="fhir-device-body-exact"),
    pytest.param(
        "device", len(DEVICE_BODY) + 1, DEVICE_BODY, id="fhir-device-body-exact-fit"
    ),
    pytest.param("condition", 128, CONDITION, id="fhir-device-condition-exact"),
    pytest.param(
        "condition", len(CONDITION) + 1, CONDITION, id="fhir-device-condition-exact-fit"
    ),
]


@pytest.mark.parametrize("operation, capacity, expected", SUCCESS_CASES)
def test_registration_output(harness, record_property, operation, capacity, expected):
    evidence(
        record_property, f"{operation} capacity {capacity}", REGISTRATION, expected
    )
    check(harness(operation, IDENTIFIER, capacity), "OK", expected)


def test_registration_is_deterministic(harness, record_property):
    evidence(record_property, "same identity twice", REGISTRATION, "identical bytes")
    for operation, capacity in (("device", 2048), ("condition", 128)):
        first = harness(operation, IDENTIFIER, capacity)
        assert first[0] == "OK"
        assert harness(operation, IDENTIFIER, capacity) == first


def test_condition_size_constant(harness, record_property):
    evidence(
        record_property,
        "condition size constant",
        REGISTRATION,
        str(len(CONDITION) + 1),
    )
    assert harness("condition-size", "-", 0)[0] == str(len(CONDITION) + 1)


OVERFLOW_CASES = [
    pytest.param("device", len(DEVICE_BODY), id="fhir-device-body-one-short"),
    pytest.param("device", 1, id="fhir-device-body-terminator-only"),
    pytest.param("device", 0, id="fhir-device-body-zero-capacity"),
    pytest.param("condition", len(CONDITION), id="fhir-device-condition-one-short"),
    pytest.param("condition", 0, id="fhir-device-condition-zero-capacity"),
]


@pytest.mark.parametrize("operation, capacity", OVERFLOW_CASES)
def test_overflow_never_truncates(harness, record_property, operation, capacity):
    evidence(
        record_property,
        f"{operation} capacity {capacity}",
        BUFFERS,
        "ENOSPC, empty, no write beyond capacity",
    )
    check(harness(operation, IDENTIFIER, capacity), "ENOSPC", "")


INVALID_IDENTIFIERS = [
    pytest.param("stetho-a1b2c3d4e5f6", id="lowercase-hex"),
    pytest.param("stetho-A1B2C3D4E5", id="short"),
    pytest.param("stetho-A1B2C3D4E5F6A", id="long"),
    pytest.param("Stetho-A1B2C3D4E5F6", id="hotspot-prefix"),
    pytest.param("stetho_A1B2C3D4E5F6", id="wrong-separator"),
    pytest.param("stetho-A1B2C3D4E5G6", id="non-hex"),
    pytest.param("stetho-D4E5F6", id="hotspot-suffix-only"),
    pytest.param("", id="empty"),
    pytest.param("<null>", id="null"),
]


@pytest.mark.parametrize("operation", ["device", "condition"])
@pytest.mark.parametrize("identifier", INVALID_IDENTIFIERS)
def test_malformed_identity_is_rejected(
    harness, record_property, operation, identifier
):
    evidence(
        record_property,
        f"{operation} identity {identifier!r}",
        IDENTITY,
        "EINVAL, empty output",
    )
    check(harness(operation, identifier, 2048), "EINVAL", "")


@pytest.mark.parametrize("operation", ["device", "condition"])
@pytest.mark.parametrize("option", ["null-output", "null-length"])
def test_null_outputs_are_rejected(harness, record_property, operation, option):
    evidence(record_property, f"{operation} {option}", REGISTRATION, "EINVAL")
    capacity = 0 if option == "null-output" else 2048
    fields = harness(operation, IDENTIFIER, capacity, option)
    assert fields[0] == "EINVAL"
    assert fields[3] == "1"


ESCAPE_CASES = [
    pytest.param(b"plain", '"plain"', id="plain"),
    pytest.param(b"", '""', id="empty"),
    pytest.param(b'a"b\\c', '"a\\"b\\\\c"', id="quote-and-backslash"),
    pytest.param(b"\b\f\n\r\t", '"\\b\\f\\n\\r\\t"', id="short-escapes"),
    pytest.param(b"\x01\x1f", '"\\u0001\\u001f"', id="other-control-characters"),
    pytest.param(b"/\x7f", '"/\x7f"', id="solidus-and-delete-unescaped"),
    pytest.param(
        "Ärztin".encode(),
        '"' + "Ärztin".encode().decode("latin-1") + '"',
        id="utf8-unchanged",
    ),
]


@pytest.mark.parametrize("raw, expected", ESCAPE_CASES)
def test_json_string_escaping(harness, record_property, raw, expected):
    evidence(record_property, f"escape {raw!r}", JSON_ESCAPING, expected)
    fields = harness("escape", raw.hex() or "-", 64)
    name, length, output, canary_is_intact, is_terminated = fields
    assert (name, canary_is_intact, is_terminated) == ("OK", "1", "1")
    actual = bytes.fromhex(output).decode("latin-1")
    assert actual.lower() == expected.lower(), (
        "hex digits of \\u escapes may use either case"
    )
    assert int(length) == len(actual)


def test_json_string_overflow_inside_escape(harness, record_property):
    evidence(record_property, "escape overflow mid-sequence", BUFFERS, "ENOSPC, empty")
    raw = b"\x01"
    for capacity in range(1, len('"\\u0001"') + 1):
        check(harness("escape", raw.hex(), capacity), "ENOSPC", "")


OBSERVATION = DESIGN + "observation-construction-and-delivery"
DELIVERY = "Development/system/design/system/interfaces-and-behavior.md#delivery-clock-and-configuration"
HEART_RATE = 0
POOR_SIGNAL = 1
SERVER_ID = "device-42"
END_SECONDS = 1792756800  # 2026-10-23T12:00:00Z, the design example
END_TEXT = "2026-10-23T12:00:00.000Z"


def build(
    harness,
    operation,
    capacity=2048,
    option="",
    server_id=SERVER_ID,
    seconds=END_SECONDS,
    milliseconds=0,
    patient="<null>",
    kind=HEART_RATE,
    scaled=725,
    places=1,
):
    fields = [seconds, milliseconds, patient, kind, scaled, places]
    if option:
        fields.append(option)
    return harness(operation, server_id, capacity, *fields)


def parse(fields):
    assert fields[0] == "OK", fields
    assert fields[3:] == ["1", "1"], "wrote beyond capacity or left output unterminated"
    raw = bytes.fromhex(fields[2]).decode("utf-8")
    assert int(fields[1]) == len(raw.encode("utf-8"))
    return raw, json.loads(raw)


def expected_observation(
    server_id=SERVER_ID, end_text=END_TEXT, patient=None, value=None
):
    resource = {
        "resourceType": "Observation",
        "identifier": [
            {
                "system": "urn:stethoscope:measurement",
                "value": f"{server_id}:{end_text}",
            }
        ],
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                    }
                ]
            }
        ],
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        "effectiveDateTime": end_text,
        "device": {"reference": f"Device/{server_id}"},
    }
    if patient is not None:
        resource["subject"] = {"reference": patient}
    if value is None:
        resource["dataAbsentReason"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                    "code": "error",
                }
            ]
        }
    else:
        resource["valueQuantity"] = {
            "value": value,
            "unit": "/min",
            "system": "http://unitsofmeasure.org",
            "code": "/min",
        }
    return resource


def test_observation_heart_rate_without_subject(harness, record_property):
    evidence(
        record_property,
        "valid BPM, standalone",
        OBSERVATION,
        "fields per design table, no subject, no meta",
    )
    raw, resource = parse(build(harness, "observation"))
    assert resource == expected_observation(value=72.5)
    assert '"value":72.5,' in raw
    assert not any(character.isspace() for character in raw), (
        "no whitespace in the serialized bytes"
    )


def test_observation_with_escaped_subject(harness, record_property):
    evidence(
        record_property,
        "supplied patient reference",
        OBSERVATION,
        "subject.reference exact, escaped",
    )
    patient = 'Patient/a"b\\c'
    _, resource = parse(build(harness, "observation", patient=patient))
    assert resource == expected_observation(patient=patient, value=72.5)


def test_observation_poor_signal(harness, record_property):
    evidence(
        record_property,
        "poor signal",
        OBSERVATION,
        "dataAbsentReason error, no valueQuantity",
    )
    raw, resource = parse(
        build(harness, "observation", kind=POOR_SIGNAL, scaled=0, places=0)
    )
    assert resource == expected_observation(value=None)
    assert "valueQuantity" not in raw


@pytest.mark.parametrize(
    "scaled, places, text",
    [
        pytest.param(72, 0, "72", id="integer"),
        pytest.param(725, 1, "72.5", id="one-place"),
        pytest.param(7250, 2, "72.50", id="trailing-zero-kept"),
        pytest.param(5, 2, "0.05", id="leading-zeros"),
        pytest.param(4294967295, 9, "4.294967295", id="largest-scaled-nine-places"),
        pytest.param(4294967295, 0, "4294967295", id="largest-integer"),
    ],
)
def test_observation_declared_precision(harness, record_property, scaled, places, text):
    evidence(record_property, f"value {scaled} places {places}", OBSERVATION, text)
    raw, _ = parse(build(harness, "observation", scaled=scaled, places=places))
    assert f'"value":{text},' in raw


@pytest.mark.parametrize(
    "seconds, milliseconds",
    [
        pytest.param(0, 0, id="epoch"),
        pytest.param(951782400, 1, id="leap-day-2000"),
        pytest.param(4107456000, 500, id="no-leap-day-2100"),
        pytest.param(END_SECONDS, 999, id="design-example"),
        pytest.param(253402300799, 999, id="year-9999-end"),
    ],
)
def test_observation_time_format(harness, record_property, seconds, milliseconds):
    text = (
        datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    ).strftime("%Y-%m-%dT%H:%M:%S") + f".{milliseconds:03d}Z"
    evidence(record_property, f"UTC {seconds}.{milliseconds:03d}", DELIVERY, text)
    _, resource = parse(
        build(harness, "observation", seconds=seconds, milliseconds=milliseconds)
    )
    assert resource["effectiveDateTime"] == text
    assert resource["identifier"][0]["value"] == f"{SERVER_ID}:{text}"


def test_observation_is_deterministic(harness, record_property):
    evidence(
        record_property,
        "same frozen result twice",
        OBSERVATION,
        "identical bytes for retries",
    )
    first = build(harness, "observation", patient="Patient/7")
    assert first[0] == "OK"
    assert build(harness, "observation", patient="Patient/7") == first


def test_observation_condition_design_example(harness, record_property):
    expected = "identifier=urn%3Astethoscope%3Ameasurement|device-42%3A2026-10-23T12%3A00%3A00.000Z"
    evidence(record_property, "condition example", DELIVERY, expected)
    check(
        build(harness, "observation-condition", capacity=len(expected) + 1),
        "OK",
        expected,
    )
    check(build(harness, "observation-condition", capacity=len(expected)), "ENOSPC", "")


def test_observation_condition_ignores_content(harness, record_property):
    evidence(
        record_property,
        "condition from identity only",
        DELIVERY,
        "same condition for any subject or value",
    )
    first = build(harness, "observation-condition")
    assert first[0] == "OK"
    assert (
        build(
            harness,
            "observation-condition",
            patient="Patient/9",
            kind=POOR_SIGNAL,
            scaled=0,
        )
        == first
    )


def test_observation_condition_longest_id_fits_size(harness, record_property):
    evidence(
        record_property,
        "longest id condition",
        BUFFERS,
        "fits FHIR_OBSERVATION_CONDITION_SIZE exactly",
    )
    size = int(harness("condition-size", "-", 0)[1])
    server_id = "A." + "b-" * 31
    assert len(server_id) == 64
    fields = build(
        harness,
        "observation-condition",
        capacity=size,
        server_id=server_id,
        seconds=253402300799,
        milliseconds=999,
    )
    assert fields[0] == "OK"
    assert int(fields[1]) == size - 1


def test_observation_exact_fit_and_one_short(harness, record_property):
    evidence(
        record_property,
        "body capacity boundary",
        BUFFERS,
        "exact fit OK, one byte short ENOSPC and empty",
    )
    raw, _ = parse(build(harness, "observation", patient="Patient/7"))
    size = len(raw.encode("utf-8"))
    parse(build(harness, "observation", capacity=size + 1, patient="Patient/7"))
    for capacity in (size, 1, 0):
        check(
            build(harness, "observation", capacity=capacity, patient="Patient/7"),
            "ENOSPC",
            "",
        )


INVALID_IDENTITIES = [
    pytest.param({"server_id": ""}, id="empty-id"),
    pytest.param({"server_id": "<null>"}, id="null-id"),
    pytest.param({"server_id": "a" * 65}, id="overlong-id"),
    pytest.param({"server_id": "Device/42"}, id="id-with-slash"),
    pytest.param({"server_id": "device_42"}, id="id-with-underscore"),
    pytest.param({"milliseconds": 1000}, id="milliseconds-1000"),
    pytest.param({"seconds": 253402300800}, id="after-year-9999"),
]
INVALID_CONTENT = [
    pytest.param({"patient": ""}, id="empty-patient"),
    pytest.param({"kind": 7}, id="unknown-kind"),
    pytest.param({"scaled": 0}, id="zero-bpm"),
    pytest.param({"places": 10}, id="ten-places"),
]


@pytest.mark.parametrize("operation", ["observation", "observation-condition"])
@pytest.mark.parametrize("fields", INVALID_IDENTITIES)
def test_observation_invalid_identity(harness, record_property, operation, fields):
    evidence(record_property, f"{operation} {fields}", DELIVERY, "EINVAL, empty output")
    check(build(harness, operation, **fields), "EINVAL", "")


@pytest.mark.parametrize("fields", INVALID_CONTENT)
def test_observation_invalid_content(harness, record_property, fields):
    evidence(
        record_property, f"observation {fields}", OBSERVATION, "EINVAL, empty output"
    )
    check(build(harness, "observation", **fields), "EINVAL", "")


@pytest.mark.parametrize("operation", ["observation", "observation-condition"])
@pytest.mark.parametrize("option", ["null-output", "null-length", "null-observation"])
def test_observation_null_arguments(harness, record_property, operation, option):
    evidence(record_property, f"{operation} {option}", OBSERVATION, "EINVAL")
    capacity = 0 if option == "null-output" else 2048
    fields = build(harness, operation, capacity=capacity, option=option)
    assert fields[0] == "EINVAL"
    assert fields[3] == "1"


RESPONSE = DESIGN + "registration-flow-and-recovery"
BINDING = DESIGN + "physical-identity-and-server-binding"
P13 = "Development/system/design/system/parameters.md (P13 outcome policy)"
BASE = "https://nglegion:8443/fhir"
LOCATION = BASE + "/Device/1/_history/1"
OUR_IDENTIFIER = {"system": "urn:stethoscope:device", "value": IDENTIFIER}

# Captured from the lab server (HAPI FHIR 8.12.0, R4) on 8 November 2026 for a test
# identity; the same Location and body came back for the 201 and the 200 response.
PROFILE_BASE = "https://172.20.10.7:8443/fhir"
HAPI_IDENTIFIER = "stetho-000000000001"
HAPI_LOCATION = "https://192.168.2.40:8443/fhir/Device/7501/_history/1"
HAPI_BODY = (
    '{\n  "resourceType": "Device",\n  "id": "7501",\n  "meta": {\n'
    '    "versionId": "1",\n    "lastUpdated": "2026-11-08T21:11:17.105+00:00"\n  },\n'
    '  "identifier": [ {\n    "system": "urn:stethoscope:device",\n'
    '    "value": "stetho-000000000001"\n  } ],\n  "status": "active"\n}'
)


def device_body(identifier=None, resource_id="1", **extra):
    """Synthetic HAPI-like representation; not a captured server response."""
    resource = {"resourceType": "Device"}
    if resource_id is not None:
        resource["id"] = resource_id
    resource["meta"] = {
        "versionId": "1",
        "lastUpdated": "2026-11-08T12:00:00.000+00:00",
        "source": "#Ab12",
    }
    resource["text"] = {
        "status": "generated",
        "div": '<div xmlns="http://www.w3.org/1999/xhtml"><b>Device</b> ä\n</div>',
    }
    resource["identifier"] = [OUR_IDENTIFIER] if identifier is None else identifier
    if resource["identifier"] == "omit":
        del resource["identifier"]
    resource["status"] = "active"
    resource.update(extra)
    return json.dumps(resource)


def register(
    harness,
    status=201,
    location=LOCATION,
    body=None,
    base=BASE,
    identifier=IDENTIFIER,
    capacity=65,
    option="",
):
    if body is None:
        body = device_body()
    body_hex = body.encode("utf-8").hex() if body != "" else "-"
    fields = [status, location if location is not None else "<null>", body_hex, base]
    if option:
        fields.append(option)
    return harness("registration", identifier, capacity, *fields)


def expect_registration(fields, result, cause, server_id=""):
    name, cause_name, _, _, output, canary_is_intact, is_terminated = fields
    assert (name, cause_name) == (result, cause)
    assert canary_is_intact == "1", "wrote beyond the given capacity"
    assert is_terminated == "1"
    actual = "" if output == "-" else bytes.fromhex(output).decode("ascii")
    assert actual == server_id


VALID_RESPONSES = [
    pytest.param({}, "1", id="created-location-and-body"),
    pytest.param({"status": 200, "location": None}, "1", id="existing-match-body-only"),
    pytest.param({"body": ""}, "1", id="location-only"),
    pytest.param({"location": BASE + "/Device/1"}, "1", id="location-without-history"),
    pytest.param(
        {"location": "HTTPS://NGLEGION:8443/fhir/Device/1/_history/7"},
        "1",
        id="scheme-and-host-case-insensitive",
    ),
    pytest.param(
        {"location": "https://other:8443/fhir/Device/1"}, "1", id="other-host"
    ),
    pytest.param(
        {"location": "https://nglegion:443/fhir/Device/1"}, "1", id="other-port"
    ),
    pytest.param(
        {"location": "https://nglegion/fhir/Device/1"}, "1", id="port-omitted"
    ),
    pytest.param(
        {"location": "https://other/Device/1", "base": "https://nglegion:8443"},
        "1",
        id="base-without-path",
    ),
    pytest.param(
        {
            "location": HAPI_LOCATION,
            "body": HAPI_BODY,
            "base": PROFILE_BASE,
            "identifier": HAPI_IDENTIFIER,
        },
        "7501",
        id="captured-hapi-201",
    ),
    pytest.param(
        {
            "status": 200,
            "location": HAPI_LOCATION,
            "body": HAPI_BODY,
            "base": PROFILE_BASE,
            "identifier": HAPI_IDENTIFIER,
        },
        "7501",
        id="captured-hapi-200",
    ),
    pytest.param(
        {"body": json.dumps(json.loads(device_body()), indent=2)},
        "1",
        id="pretty-printed-body",
    ),
    pytest.param(
        {"body": device_body(identifier="omit")},
        "1",
        id="representation-without-identifiers",
    ),
    pytest.param(
        {
            "body": device_body(
                identifier=[
                    {"use": "official", "system": "urn:other", "value": "x"},
                    {
                        "type": {"text": "serial"},
                        "value": IDENTIFIER,
                        "system": OUR_IDENTIFIER["system"],
                    },
                ]
            )
        },
        "1",
        id="identifier-among-others",
    ),
    pytest.param(
        {
            "location": BASE + "/Device/" + "A." + "b-" * 31,
            "body": device_body(resource_id="A." + "b-" * 31),
        },
        "A." + "b-" * 31,
        id="longest-id",
    ),
    pytest.param(
        {
            "body": device_body(
                extension=[[[[[[[[{"a": [1, -2.5e3, True, False, None]}]]]]]]]]
            )
        },
        "1",
        id="nested-skipped-member",
    ),
    pytest.param(
        {"location": None, "body": device_body(resource_id=None)[:-1] + ',"id":"9"}'},
        "9",
        id="id-member-last",
    ),
]


@pytest.mark.parametrize("fields, server_id", VALID_RESPONSES)
def test_registration_response_valid(harness, record_property, fields, server_id):
    evidence(record_property, f"registration {fields}", RESPONSE, f"OK, id {server_id}")
    expect_registration(register(harness, **fields), "OK", "NONE", server_id)


STATUSES = [
    pytest.param(412, "MULTIPLE_MATCHES", id="412-multiple-matches"),
    pytest.param(501, "UNSUPPORTED", id="501-unsupported"),
    pytest.param(500, "SERVER_ERROR", id="500"),
    pytest.param(503, "SERVER_ERROR", id="503"),
    pytest.param(599, "SERVER_ERROR", id="599"),
    pytest.param(400, "REJECTED", id="400"),
    pytest.param(401, "REJECTED", id="401-authentication"),
    pytest.param(403, "REJECTED", id="403"),
    pytest.param(404, "REJECTED", id="404"),
    pytest.param(422, "REJECTED", id="422"),
    pytest.param(429, "REJECTED", id="429"),
    pytest.param(204, "REJECTED", id="204"),
    pytest.param(202, "REJECTED", id="202"),
    pytest.param(302, "REJECTED", id="302"),
    pytest.param(100, "REJECTED", id="100"),
]


@pytest.mark.parametrize("status, cause", STATUSES)
def test_registration_status_classes(harness, record_property, status, cause):
    evidence(record_property, f"status {status}", P13, cause)
    expect_registration(register(harness, status=status), "EBADMSG", cause)


LONG_ID = "a" * 65
INVALID_RESPONSES = [
    pytest.param({"location": None, "body": ""}, id="no-location-no-body"),
    pytest.param({"location": "http://nglegion:8443/fhir/Device/1"}, id="plain-http"),
    pytest.param({"location": "https:///fhir/Device/1"}, id="empty-authority"),
    pytest.param(
        {"location": "https:nglegion:8443/fhir/Device/1"}, id="authority-missing"
    ),
    pytest.param(
        {"location": "https://nglegion?/fhir/Device/1"}, id="query-in-authority"
    ),
    pytest.param(
        {"location": "https://nglegion#/fhir/Device/1"}, id="fragment-in-authority"
    ),
    pytest.param(
        {"location": "https://other/fhir/Device/1", "base": "https://nglegion:8443"},
        id="path-added-to-empty-base-path",
    ),
    pytest.param(
        {"location": "https://nglegion:8443/fhir2/Device/1"}, id="other-base-path"
    ),
    pytest.param(
        {"location": "https://nglegion:8443/FHIR/Device/1"}, id="path-case-differs"
    ),
    pytest.param(
        {"location": "https://nglegion:8443/Device/1"}, id="base-path-missing"
    ),
    pytest.param({"location": BASE + "/Patient/1"}, id="other-resource-type"),
    pytest.param({"location": "Device/1/_history/1"}, id="relative-location"),
    pytest.param({"location": BASE + "/Device/1/"}, id="trailing-slash"),
    pytest.param({"location": BASE + "/Device/"}, id="empty-id"),
    pytest.param({"location": BASE + "/Device/1/_history/"}, id="empty-version"),
    pytest.param({"location": BASE + "/Device/1/_history/1/x"}, id="after-version"),
    pytest.param({"location": BASE + "/Device/1/_versions/1"}, id="other-suffix"),
    pytest.param({"location": BASE + "/Device/1?x=1"}, id="query"),
    pytest.param({"location": BASE + "/Device/1_2"}, id="id-underscore"),
    pytest.param({"location": BASE + "/Device/" + LONG_ID}, id="id-65"),
    pytest.param({"location": BASE + "/Device/2"}, id="ids-disagree"),
    pytest.param(
        {"body": device_body(resourceType="OperationOutcome")}, id="other-resource-body"
    ),
    pytest.param(
        {"body": device_body()[:-1] + ',"resourceType":"Device"}'},
        id="duplicate-resource-type",
    ),
    pytest.param({"body": device_body()[:-1] + ',"id":"1"}'}, id="duplicate-id"),
    pytest.param(
        {"body": device_body()[:-1] + ',"identifier":[]}'}, id="duplicate-identifier"
    ),
    pytest.param(
        {"body": json.dumps({"id": "1", "status": "active"})},
        id="missing-resource-type",
    ),
    pytest.param({"body": "[]"}, id="array-body"),
    pytest.param({"body": "<html>error</html>"}, id="html-body"),
    pytest.param({"body": device_body() + "x"}, id="trailing-content"),
    pytest.param({"body": device_body() + "{}"}, id="second-object"),
    pytest.param({"body": device_body()[:-1]}, id="unterminated-object"),
    pytest.param({"body": device_body()[:40]}, id="truncated-body"),
    pytest.param({"body": '{"resourceType":"Dev'}, id="unterminated-string"),
    pytest.param(
        {"body": '{"resourceType":"\\u0044evice","id":"1"}'}, id="escaped-resource-type"
    ),
    pytest.param({"body": '{"resourceType":"Device","id":"\\u0031"}'}, id="escaped-id"),
    pytest.param({"body": '{"resourceType":"Device","id":1}'}, id="numeric-id"),
    pytest.param({"body": device_body(resource_id="1/2")}, id="invalid-body-id"),
    pytest.param(
        {"body": device_body(resource_id=LONG_ID), "location": None},
        id="overlong-body-id",
    ),
    pytest.param({"body": device_body(identifier=[])}, id="identifiers-without-ours"),
    pytest.param(
        {
            "body": device_body(
                identifier=[{"system": "urn:other", "value": IDENTIFIER}]
            )
        },
        id="our-value-other-system",
    ),
    pytest.param(
        {
            "body": device_body(
                identifier=[
                    {"system": OUR_IDENTIFIER["system"], "value": "stetho-000000000000"}
                ]
            )
        },
        id="other-device-identifier",
    ),
    pytest.param(
        {"body": device_body(identifier={"value": IDENTIFIER})},
        id="identifier-not-array",
    ),
    pytest.param(
        {"body": '{"resourceType":"Device","id":"1","x":"a\tb"}'},
        id="raw-control-character",
    ),
    pytest.param(
        {"body": '{"resourceType":"Device","id":"1","x":"\\q"}'}, id="invalid-escape"
    ),
    pytest.param(
        {"body": '{"resourceType":"Device","id":"1","x":"\\u12G4"}'},
        id="invalid-unicode-escape",
    ),
    pytest.param(
        {"body": '{"resourceType":"Device","id":"1","x":tru}'}, id="broken-literal"
    ),
    pytest.param(
        {"body": '{"resourceType":"Device","id":"1","x":[1,]}'}, id="trailing-comma"
    ),
    pytest.param(
        {"body": '{"resourceType":"Device","id":"1","x":}'}, id="missing-value"
    ),
    pytest.param({"body": '{"resourceType":"Device" "id":"1"}'}, id="missing-comma"),
    pytest.param(
        {"body": '{"resourceType":"Device","id":"1","x":' + "[" * 40 + "]" * 40 + "}"},
        id="nesting-too-deep",
    ),
    pytest.param({"body": " "}, id="whitespace-body"),
]


@pytest.mark.parametrize("fields", INVALID_RESPONSES)
def test_registration_response_invalid(harness, record_property, fields):
    evidence(
        record_property,
        f"registration {fields}",
        RESPONSE,
        "EBADMSG INVALID_REPRESENTATION, empty id",
    )
    expect_registration(
        register(harness, **fields), "EBADMSG", "INVALID_REPRESENTATION"
    )


@pytest.mark.parametrize(
    "fields, option",
    [
        pytest.param({}, "null-response", id="null-response"),
        pytest.param({}, "null-output", id="null-output"),
        pytest.param({}, "null-cause", id="null-cause"),
        pytest.param({"base": "<null>"}, "", id="null-base"),
        pytest.param({"base": ""}, "", id="empty-base"),
        pytest.param(
            {"identifier": "stetho-a1b2c3d4e5f6"}, "", id="malformed-identity"
        ),
        pytest.param({"capacity": 64}, "", id="capacity-64"),
    ],
)
def test_registration_invalid_arguments(harness, record_property, fields, option):
    evidence(
        record_property,
        f"registration {option or fields}",
        BINDING,
        "EINVAL, cause unwritten",
    )
    capacity = fields.pop("capacity", 0 if option == "null-output" else 65)
    result = register(harness, capacity=capacity, option=option, **fields)
    assert result[0] == "EINVAL"
    if option != "null-cause":
        assert result[1] == "UNWRITTEN"
    assert result[5] == "1"
    if option != "null-output":
        assert result[4] == "-", "stale output after an argument error"


RECORD_DESIGN = DESIGN + "registration-record"
RECORD_SIZE = 343
RECORD_BASE = "https://172.20.10.7:8443/fhir"
RECORD_ID = "7501"


def record_evidence(record_property, scenario, expected):
    record_property("scenario", scenario)
    record_property("vt_id", "VT-15")
    record_property("basis", RECORD_DESIGN)
    record_property("expected", expected)


def field(text, size):
    data = text.encode("ascii")
    assert len(data) < size
    return data + bytes(size - len(data))


def record_bytes(
    base=RECORD_BASE, identifier=IDENTIFIER, server_id=RECORD_ID, version=1
):
    """Version-1 layout from the design, built independently of the C code."""
    return (
        bytes([version])
        + field(base, 257)
        + field(identifier, 20)
        + field(server_id, 65)
    )


def encode(
    harness,
    base=RECORD_BASE,
    identifier=IDENTIFIER,
    server_id=RECORD_ID,
    capacity=RECORD_SIZE,
    option="",
):
    extra = [identifier, server_id] + ([option] if option else [])
    return harness("record-encode", base, capacity, *extra)


def decode(
    harness, data, base=RECORD_BASE, identifier=IDENTIFIER, capacity=65, option=""
):
    extra = [data.hex() if data else "-", base] + ([option] if option else [])
    return harness("record-decode", identifier, capacity, *extra)


def test_record_size_is_343(record_property):
    record_evidence(record_property, "record layout", "1 + 257 + 20 + 65 = 343 bytes")
    assert len(record_bytes()) == RECORD_SIZE


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({}, id="typical"),
        pytest.param({"base": "https://h"}, id="short-base"),
        pytest.param({"base": "https://" + "h" * 248}, id="base-256"),
        pytest.param({"server_id": "A." + "b-" * 31}, id="server-id-64"),
        pytest.param({"server_id": "x"}, id="server-id-1"),
    ],
)
def test_record_encode_layout(harness, record_property, fields):
    record_evidence(
        record_property, f"encode {fields}", "exact version-1 bytes, zero padding"
    )
    name, data, canary = encode(harness, **fields)
    assert (name, canary) == ("OK", "1")
    assert bytes.fromhex(data) == record_bytes(**fields)


def test_record_encode_zero_fills_larger_buffer(harness, record_property):
    record_evidence(
        record_property, "encode into 400 bytes", "record, then zeros up to capacity"
    )
    name, data, canary = encode(harness, capacity=400)
    assert (name, canary) == ("OK", "1")
    assert bytes.fromhex(data) == record_bytes() + bytes(400 - RECORD_SIZE)


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({"base": ""}, id="empty-base"),
        pytest.param({"base": "https://" + "h" * 249}, id="base-257"),
        pytest.param({"base": "<null>"}, id="null-base"),
        pytest.param({"identifier": "stetho-a1b2c3d4e5f6"}, id="lowercase-identity"),
        pytest.param({"identifier": "stetho-A1B2C3D4E5F"}, id="short-identity"),
        pytest.param({"identifier": "<null>"}, id="null-identity"),
        pytest.param({"server_id": ""}, id="empty-server-id"),
        pytest.param({"server_id": "a" * 65}, id="server-id-65"),
        pytest.param({"server_id": "a_b"}, id="server-id-underscore"),
        pytest.param({"server_id": "<null>"}, id="null-server-id"),
        pytest.param({"capacity": RECORD_SIZE - 1}, id="capacity-342"),
        pytest.param({"capacity": 0}, id="capacity-0"),
        pytest.param({"option": "null-output"}, id="null-output"),
    ],
)
def test_record_encode_rejects(harness, record_property, fields):
    record_evidence(
        record_property,
        f"encode {fields}",
        "EINVAL, zero-filled, nothing beyond capacity",
    )
    capacity = fields.get("capacity", RECORD_SIZE)
    name, data, canary = encode(harness, **fields)
    assert (name, canary) == ("EINVAL", "1")
    if fields.get("option") != "null-output" and capacity > 0:
        assert bytes.fromhex(data) == bytes(capacity)


@pytest.mark.parametrize(
    "server_id",
    [
        pytest.param(RECORD_ID, id="typical"),
        pytest.param("A." + "b-" * 31, id="server-id-64"),
    ],
)
def test_record_decode_valid(harness, record_property, server_id):
    record_evidence(record_property, f"decode id {server_id}", "OK with the stored id")
    fields = decode(harness, record_bytes(server_id=server_id))
    check(fields, "OK", server_id)


def test_record_round_trip(harness, record_property):
    record_evidence(record_property, "encode then decode", "OK with the same id")
    name, data, _ = encode(harness)
    assert name == "OK"
    fields = decode(harness, bytes.fromhex(data))
    check(fields, "OK", RECORD_ID)


def corrupt(offset, value):
    data = bytearray(record_bytes())
    data[offset] = value
    return bytes(data)


def unterminated(offset, size):
    data = bytearray(record_bytes())
    data[offset : offset + size] = b"h" * size
    return bytes(data)


BASE_FIELD, IDENTITY_FIELD, SERVER_FIELD = 1, 1 + 257, 1 + 257 + 20


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(record_bytes()[:-1], id="size-342"),
        pytest.param(record_bytes() + b"\0", id="size-344"),
        pytest.param(b"", id="size-0"),
        pytest.param(record_bytes(version=0), id="version-0"),
        pytest.param(record_bytes(version=2), id="version-2"),
        pytest.param(bytes([0xFF]) * RECORD_SIZE, id="erased-flash"),
        pytest.param(bytes(RECORD_SIZE), id="all-zero"),
        pytest.param(bytes([1]) + bytes(RECORD_SIZE - 1), id="version-only"),
        pytest.param(unterminated(BASE_FIELD, 257), id="base-without-terminator"),
        pytest.param(corrupt(BASE_FIELD + 200, ord("x")), id="base-nonzero-padding"),
        pytest.param(corrupt(BASE_FIELD + 256, 0xFF), id="base-padding-erased"),
        pytest.param(record_bytes(base=""), id="base-empty"),
        pytest.param(
            corrupt(IDENTITY_FIELD + 19, ord("x")), id="identity-without-terminator"
        ),
        pytest.param(
            record_bytes(identifier="stetho-a1b2c3d4e5f6"), id="identity-malformed"
        ),
        pytest.param(record_bytes(identifier=""), id="identity-empty"),
        pytest.param(unterminated(SERVER_FIELD, 65), id="server-id-without-terminator"),
        pytest.param(
            corrupt(SERVER_FIELD + 30, ord("x")), id="server-id-nonzero-padding"
        ),
        pytest.param(record_bytes(server_id=""), id="server-id-empty"),
        pytest.param(record_bytes(server_id="a_b"), id="server-id-invalid"),
    ],
)
def test_record_decode_malformed(harness, record_property, data):
    record_evidence(record_property, "decode malformed record", "EBADMSG, empty id")
    fields = decode(harness, data)
    check(fields, "EBADMSG", "")
    assert fields[2] == "-", "stale output after a malformed record"


@pytest.mark.parametrize(
    "data, base",
    [
        pytest.param(
            record_bytes(base="https://192.168.2.40:8443/fhir"),
            RECORD_BASE,
            id="other-base",
        ),
        pytest.param(record_bytes(), RECORD_BASE + "2", id="base-prefix-only"),
        pytest.param(record_bytes(), RECORD_BASE.upper(), id="base-case-differs"),
        pytest.param(
            record_bytes(identifier="stetho-0000000000AA"),
            RECORD_BASE,
            id="other-identity",
        ),
    ],
)
def test_record_decode_other_binding(harness, record_property, data, base):
    record_evidence(
        record_property, "decode record of another binding", "ESTALE, empty id"
    )
    fields = decode(harness, data, base=base)
    check(fields, "ESTALE", "")
    assert fields[2] == "-"


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({"option": "null-record"}, id="null-record"),
        pytest.param({"option": "null-output", "capacity": 0}, id="null-output"),
        pytest.param({"base": "<null>"}, id="null-base"),
        pytest.param({"base": ""}, id="empty-base"),
        pytest.param(
            {"identifier": "stetho-a1b2c3d4e5f6"}, id="malformed-expected-identity"
        ),
        pytest.param({"identifier": "<null>"}, id="null-expected-identity"),
        pytest.param({"capacity": 64}, id="capacity-64"),
    ],
)
def test_record_decode_invalid_arguments(harness, record_property, fields):
    record_evidence(record_property, f"decode {fields}", "EINVAL, empty id")
    fields = decode(harness, record_bytes(), **fields)
    assert fields[0] == "EINVAL"
    assert fields[3] == "1", "wrote beyond the given capacity"
    assert fields[2] == "-"
