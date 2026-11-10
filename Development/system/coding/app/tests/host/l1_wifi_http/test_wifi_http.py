"""VT-07/VT-08: bounded HTTP/1.1 response reader on Zephyr's http_parser."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

import host_build

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[6]
DESIGN = "Development/system/design/COMMUNICATION/server-communication.md#"
RECEIPT = DESIGN + "observation-construction-and-delivery"
BUFFERS = DESIGN + "parameters-and-outstanding-evidence"
HEADER_COUNT = (
    "; Development/system/coding/app/L1_services/L1_WIFI/wifi_http.h"
    " (WIFI_HTTP_HEADER_CAPACITY)"
)
FRAMING = "https://www.rfc-editor.org/rfc/rfc9112#section-7.1"
MESSAGE_LENGTH = "https://www.rfc-editor.org/rfc/rfc9112#section-6.3"
LOCATION_FIELD = "https://www.rfc-editor.org/rfc/rfc9110#section-10.2.2"
VT_ID = "VT-07, VT-08"
BODY_CAPACITY = 4096
LOCATION_SIZE = 512


# The static CI job has no Zephyr workspace, so the parser is vendored at the pinned revision.
# The files are stored flat because tracked "/zephyr/" paths count as a checked-in workspace.
VENDORED = REPOSITORY / "Development/system/coding/third_party/zephyr-http-parser"
TOOLCHAIN = REPOSITORY / "Development/system/coding/tools/toolchain/toolchain.json"
VENDORED_REVISION = "357467a011cd2557a1a3f0b4be83d817c4addc9b"
VENDORED_BLOBS = {
    "include/zephyr/net/http/method.h": "9bcad986dd4f6df2c0c0a93dac26b1c7c6bc0fa2",
    "include/zephyr/net/http/parser.h": "d7b754e5dac53988a3c8de00c1fc5dfeee89af59",
    "include/zephyr/net/http/parser_state.h": "2369c6b676f31916b46924c08034194b25bcf3b2",
    "include/zephyr/net/http/parser_url.h": "e795e18ab3a7a1b4a28b745f490e0a172035730b",
    "subsys/net/lib/http/http_parser.c": "a36bceef9b97e489605a72c1f7fd29a0fe563bf1",
    "subsys/net/lib/http/http_parser_url.c": "cb46029002f397770af42b158f4658b376b713d1",
}


@pytest.fixture(scope="module", autouse=True)
def traceability(request):
    """Map every case before the module fixtures build the harness, so a build failure keeps it."""
    for item in request.session.items:
        if getattr(item, "module", None) is request.module:
            item.user_properties.append(("vt_id", VT_ID))


def test_vendored_parser_matches_the_pinned_zephyr(record_property):
    for name, value in (
        ("scenario", "wifi-http-vendored-parser-pin"),
        (
            "basis",
            "Development/system/coding/tools/toolchain/toolchain.json (zephyr_revision)",
        ),
        ("expected", "vendored files equal the git blobs of the pinned revision"),
    ):
        record_property(name, value)
    pinned = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))["zephyr_revision"]
    assert pinned == VENDORED_REVISION, "re-vendor the parser for the new Zephyr pin"
    for path, blob in VENDORED_BLOBS.items():
        content = (VENDORED / Path(path).name).read_bytes()
        header = f"blob {len(content)}\0".encode()
        assert hashlib.sha1(header + content).hexdigest() == blob, path


@pytest.fixture(scope="module")
def reader(host_build_directory, tmp_path_factory):
    zephyr = tmp_path_factory.mktemp("zephyr")
    for path in VENDORED_BLOBS:
        (zephyr / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(VENDORED / Path(path).name, zephyr / path)
    target = host_build.build(
        host_build_directory("unit", "wifi-http"),
        "http",
        [
            HERE / "http_harness.c",
            zephyr / "subsys/net/lib/http/http_parser.c",
            zephyr / "subsys/net/lib/http/http_parser_url.c",
        ],
        [zephyr / "include"],
    ).path
    directory = tmp_path_factory.mktemp("responses")

    def run(data, piece_size=4096, option=""):
        path = directory / "response.http"
        path.write_bytes(data)
        arguments = [str(target), str(path), str(piece_size)] + (
            [option] if option else []
        )
        completed = subprocess.run(
            arguments, capture_output=True, text=True, timeout=30
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        fields = completed.stdout.split()
        (
            result,
            consumed,
            status,
            has_location,
            location,
            length,
            overflow,
            keeps,
            body,
        ) = fields
        return {
            "result": result,
            "consumed": int(consumed),
            "status": int(status),
            "has_location": has_location == "1",
            "location": ""
            if location == "-"
            else bytes.fromhex(location).decode("latin-1"),
            "body_length": int(length),
            "overflowed": overflow == "1",
            "keeps": keeps == "1",
            "body": b"" if body == "-" else bytes.fromhex(body),
        }

    run.target = target
    return run


def evidence(record_property, scenario, basis, expected):
    record_property("scenario", scenario)
    record_property("basis", basis)
    record_property("expected", expected)


def response(status_line, headers, body=b""):
    return (
        status_line + b"\r\n" + b"".join(h + b"\r\n" for h in headers) + b"\r\n" + body
    )


def chunked(*parts):
    return b"".join(b"%x\r\n" % len(p) + p + b"\r\n" for p in parts) + b"0\r\n\r\n"


def dechunk(data):
    """Reference decoder for the test inputs, independent of the C code."""
    body = data[data.index(b"\r\n\r\n") + 4 :]
    decoded = b""
    while True:
        size_line, body = body.split(b"\r\n", 1)
        size = int(size_line, 16)
        if size == 0:
            return decoded
        decoded += body[:size]
        body = body[size + 2 :]


# Captured from the lab server (HAPI FHIR 8.12.0, R4) on 8 November 2026 with curl --raw:
# GET /fhir/Device/7503 after its deletion, and an empty Device search.
HAPI_410_GONE = (
    b"HTTP/1.1 410 \r\n"
    b"X-Powered-By: HAPI FHIR 8.12.0 REST Server (FHIR Server; FHIR 4.0.1/R4)\r\n"
    b"X-Request-ID: Bu96lBc7X4714Sry\r\n"
    b"Location: https://192.168.2.40:8443/fhir/Device/7503/_history/2\r\n"
    b"Content-Type: application/fhir+json;charset=UTF-8\r\n"
    b"Transfer-Encoding: chunked\r\n"
    b"Date: Sun, 08 Nov 2026 23:44:28 GMT\r\n"
    b"\r\n"
    b"26\r\n"
    b"{\n"
    b'  "resourceType": "OperationOutcome"\r\n'
    b"28\r\n"
    b",\n"
    b'  "issue": [ {\n'
    b'    "severity": "error"\r\n'
    b"1a\r\n"
    b",\n"
    b'    "code": "processing"\r\n'
    b"4c\r\n"
    b",\n"
    b'    "diagnostics": "Resource was deleted at 2026-11-08T21:23:55.333+00:00"\r\n'
    b"8\r\n"
    b"\n"
    b"  } ]\n"
    b"}\r\n"
    b"0\r\n"
    b"\r\n"
)
HAPI_200_SEARCH = (
    b"HTTP/1.1 200 \r\n"
    b"X-Powered-By: HAPI FHIR 8.12.0 REST Server (FHIR Server; FHIR 4.0.1/R4)\r\n"
    b"X-Request-ID: zuc4I80cAOdwlJlo\r\n"
    b"Last-Modified: Sun, 08 Nov 2026 23:44:28 GMT\r\n"
    b"Content-Type: application/fhir+json;charset=UTF-8\r\n"
    b"Transfer-Encoding: chunked\r\n"
    b"Date: Sun, 08 Nov 2026 23:44:28 GMT\r\n"
    b"\r\n"
    b"1c\r\n"
    b"{\n"
    b'  "resourceType": "Bundle"\r\n'
    b"30\r\n"
    b",\n"
    b'  "id": "ac95ed2c-938c-4c99-ae45-6482764d07e4"\r\n'
    b"40\r\n"
    b",\n"
    b'  "meta": {\n'
    b'    "lastUpdated": "2026-11-08T23:44:28.948+00:00"\r\n'
    b"1b\r\n"
    b"\n"
    b"  },\n"
    b'  "type": "searchset"\r\n'
    b"e\r\n"
    b",\n"
    b'  "total": 0\r\n'
    b"26\r\n"
    b",\n"
    b'  "link": [ {\n'
    b'    "relation": "self"\r\n'
    b"70\r\n"
    b",\n"
    b'    "url": "https://192.168.2.40:8443/fhir/Device?identifier=urn%3Astethoscope%3Adevice%7Cstetho-000000000001"\r\n'
    b"8\r\n"
    b"\n"
    b"  } ]\n"
    b"}\r\n"
    b"0\r\n"
    b"\r\n"
)
HAPI_LOCATION = "https://192.168.2.40:8443/fhir/Device/7503/_history/2"
CREATED = b"HTTP/1.1 201 Created"
LOCATION = b"Location: https://h:8443/fhir/Device/1/_history/1"


@pytest.mark.parametrize("piece_size", [4096, 1, 7])
@pytest.mark.parametrize(
    "data, status, location",
    [
        pytest.param(HAPI_410_GONE, 410, HAPI_LOCATION, id="captured-410"),
        pytest.param(HAPI_200_SEARCH, 200, "", id="captured-200"),
    ],
)
def test_captured_hapi_responses(
    reader, record_property, data, status, location, piece_size
):
    evidence(
        record_property,
        f"captured HAPI {status}, pieces of {piece_size}",
        FRAMING,
        "complete, chunked framing removed, connection reusable",
    )
    fields = reader(data, piece_size)
    assert fields["result"] == "OK"
    assert fields["consumed"] == len(data)
    assert (fields["status"], fields["location"]) == (status, location)
    assert fields["has_location"] == bool(location)
    assert fields["body"] == dechunk(data)
    assert fields["body_length"] == len(dechunk(data))
    assert (fields["overflowed"], fields["keeps"]) == (False, True)


@pytest.mark.parametrize(
    "data, expected",
    [
        pytest.param(
            response(CREATED, [LOCATION, b"Content-Length: 5"], b"hello"),
            {"status": 201, "body": b"hello", "keeps": True},
            id="content-length",
        ),
        pytest.param(
            response(CREATED, [LOCATION, b"Content-Length: 0"]),
            {"status": 201, "body": b"", "keeps": True},
            id="empty-body",
        ),
        pytest.param(
            response(
                b"HTTP/1.1 201 ", [b"Transfer-Encoding: chunked"], chunked(b"a", b"bc")
            ),
            {"status": 201, "body": b"abc", "keeps": True},
            id="empty-reason-phrase",
        ),
        pytest.param(
            response(CREATED, [b"Connection: close", b"Content-Length: 2"], b"ok"),
            {"status": 201, "body": b"ok", "keeps": False},
            id="connection-close",
        ),
        pytest.param(
            response(b"HTTP/1.0 200 OK", [b"Content-Length: 2"], b"ok"),
            {"status": 200, "body": b"ok", "keeps": False},
            id="http-1-0",
        ),
        pytest.param(
            response(
                CREATED,
                [b"Transfer-Encoding: chunked"],
                b"3;name=value\r\nabc\r\n0\r\nTrailer: x\r\n\r\n",
            ),
            {"status": 201, "body": b"abc", "keeps": True},
            id="chunk-extension-and-trailer",
        ),
        pytest.param(
            response(
                b"HTTP/1.1 503 Service Unavailable", [b"Content-Length: 4"], b"busy"
            ),
            {"status": 503, "body": b"busy", "keeps": True},
            id="server-error-is-still-a-response",
        ),
    ],
)
def test_framings(reader, record_property, data, expected):
    evidence(
        record_property,
        f"framing {expected}",
        FRAMING,
        "complete with the decoded body",
    )
    for piece_size in (4096, 1):
        fields = reader(data, piece_size)
        assert fields["result"] == "OK"
        assert fields["consumed"] == len(data)
        assert fields["status"] == expected["status"]
        assert fields["body"] == expected["body"]
        assert fields["keeps"] == expected["keeps"]


def test_close_delimited_body_completes_at_close(reader, record_property):
    evidence(
        record_property,
        "body until close",
        FRAMING,
        "EAGAIN, then OK at close, no reuse",
    )
    data = response(b"HTTP/1.1 200 OK", [b"Connection: close"], b"until close")
    assert reader(data)["result"] == "EAGAIN"
    fields = reader(data, 4096, "finish")
    assert (fields["result"], fields["body"], fields["keeps"]) == (
        "OK",
        b"until close",
        False,
    )


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"HTTP/1.1 201 Created\r\nLocation: x", id="inside-headers"),
        pytest.param(
            response(CREATED, [b"Content-Length: 10"], b"short"),
            id="short-content-length",
        ),
        pytest.param(
            response(CREATED, [b"Transfer-Encoding: chunked"], b"5\r\nab"),
            id="inside-chunk",
        ),
        pytest.param(
            response(CREATED, [b"Transfer-Encoding: chunked"], b"2\r\nab\r\n"),
            id="final-chunk-missing",
        ),
        pytest.param(b"", id="nothing-received"),
        pytest.param(b"HTTP/1.1 200 OK\r\n", id="status-line-only"),
        pytest.param(
            b"HTTP/1.1 200 OK\r\nConnection: close\r\n",
            id="close-delimited-headers-unterminated",
        ),
    ],
)
def test_truncated_response_is_no_receipt(reader, record_property, data):
    evidence(
        record_property,
        "connection closed early",
        RECEIPT,
        "EAGAIN, then EBADMSG at close",
    )
    if data:
        assert reader(data)["result"] == "EAGAIN"
    assert reader(data, 4096, "finish")["result"] == "EBADMSG"


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"hello world\r\n\r\n", id="no-status-line"),
        pytest.param(b"HTTP/1.1 abc OK\r\n\r\n", id="status-not-numeric"),
        pytest.param(
            response(
                CREATED, [b"Transfer-Encoding: chunked"], b"zz\r\nab\r\n0\r\n\r\n"
            ),
            id="chunk-size-not-hex",
        ),
        pytest.param(
            response(CREATED, [b"Content-Length: abc"]), id="content-length-not-numeric"
        ),
        pytest.param(
            response(CREATED, [b"Content-Length: 1", b"Content-Length: 2"], b"ab"),
            id="content-length-twice",
        ),
        pytest.param(
            response(CREATED, [LOCATION, LOCATION, b"Content-Length: 0"]),
            id="location-twice",
        ),
        pytest.param(
            response(
                CREATED,
                [
                    LOCATION,
                    b"location: https://h:8443/fhir/Device/2",
                    b"Content-Length: 0",
                ],
            ),
            id="location-twice-other-case",
        ),
        pytest.param(
            response(CREATED, [b"Location:", LOCATION, b"Content-Length: 0"]),
            id="empty-location-then-location",
        ),
    ],
)
def test_malformed_response(reader, record_property, data):
    evidence(
        record_property,
        "malformed response",
        RECEIPT,
        "EBADMSG; malformed headers are no receipt",
    )
    for piece_size in (4096, 1):
        assert reader(data, piece_size)["result"] == "EBADMSG"


@pytest.mark.parametrize(
    "name",
    [b"Location", b"location", b"LOCATION", b"LoCaTiOn"],
)
def test_location_name_is_case_insensitive(reader, record_property, name):
    evidence(
        record_property,
        f"header name {name!r}",
        "https://www.rfc-editor.org/rfc/rfc9110#section-5.1",
        "Location kept",
    )
    data = response(
        CREATED, [name + b": https://h/fhir/Device/9", b"Content-Length: 0"]
    )
    fields = reader(data, 1)
    assert (fields["result"], fields["has_location"], fields["location"]) == (
        "OK",
        True,
        "https://h/fhir/Device/9",
    )


@pytest.mark.parametrize(
    "name",
    [b"Content-Location", b"Locations", b"X-Location", b"Locatio"],
)
def test_similar_header_names_are_not_location(reader, record_property, name):
    evidence(record_property, f"header name {name!r}", RECEIPT, "no Location")
    data = response(
        CREATED, [name + b": https://h/fhir/Device/9", b"Content-Length: 0"]
    )
    fields = reader(data, 1)
    assert (fields["result"], fields["has_location"], fields["location"]) == (
        "OK",
        False,
        "",
    )


@pytest.mark.parametrize("piece_size", [4096, 1])
def test_empty_header_value_before_location(reader, record_property, piece_size):
    evidence(
        record_property,
        f"empty header value, then Location, pieces of {piece_size}",
        RECEIPT,
        "the next name starts a new header; Location kept",
    )
    data = response(
        CREATED,
        [b"X-Empty:", b"Location: https://h/fhir/Device/9", b"Content-Length: 0"],
    )
    fields = reader(data, piece_size)
    assert (fields["result"], fields["location"]) == ("OK", "https://h/fhir/Device/9")


def test_content_location_before_location_like_hapi(reader, record_property):
    evidence(
        record_property, "Content-Location then Location", RECEIPT, "only Location kept"
    )
    data = response(
        CREATED,
        [
            b"Content-Location: https://h/fhir/Device/8/_history/1",
            b"Location: https://h/fhir/Device/9/_history/1",
            b"Content-Length: 0",
        ],
    )
    fields = reader(data, 3)
    assert (fields["result"], fields["location"]) == (
        "OK",
        "https://h/fhir/Device/9/_history/1",
    )


@pytest.mark.parametrize(
    "length, result",
    [
        pytest.param(LOCATION_SIZE - 1, "OK", id="location-511"),
        pytest.param(LOCATION_SIZE, "EMSGSIZE", id="location-512"),
        pytest.param(3000, "EMSGSIZE", id="location-3000"),
    ],
)
def test_location_bound_never_truncates(reader, record_property, length, result):
    evidence(record_property, f"Location of {length} bytes", BUFFERS, result)
    value = b"https://h/" + b"a" * (length - len(b"https://h/"))
    data = response(CREATED, [b"Location: " + value, b"Content-Length: 0"])
    for piece_size in (4096, 1):
        fields = reader(data, piece_size)
        assert fields["result"] == result
        if result == "OK":
            assert fields["location"] == value.decode()


def test_header_capacity(reader, record_property):
    evidence(
        record_property, "headers over 4096 bytes", BUFFERS, "EMSGSIZE, no receipt"
    )
    data = response(CREATED, [b"X-Filler: " + b"f" * 5000, b"Content-Length: 0"])
    assert reader(data)["result"] == "EMSGSIZE"
    many = [b"X-Small-%d: v" % index for index in range(400)]
    assert (
        reader(response(CREATED, many + [b"Content-Length: 0"]))["result"] == "EMSGSIZE"
    )
    within = response(CREATED, [b"X-Filler: " + b"f" * 3000, b"Content-Length: 0"])
    assert reader(within)["result"] == "OK"


@pytest.mark.parametrize(
    "length, overflowed",
    [
        pytest.param(BODY_CAPACITY, False, id="body-4096"),
        pytest.param(BODY_CAPACITY + 1, True, id="body-4097"),
        pytest.param(200000, True, id="body-200000"),
    ],
)
def test_body_bound_drains_without_truncation(
    reader, record_property, length, overflowed
):
    evidence(
        record_property,
        f"body of {length} bytes",
        BUFFERS + " and " + RECEIPT,
        "complete; oversized body unusable and connection closed",
    )
    body = bytes((index * 7) % 251 for index in range(length))
    for data in (
        response(CREATED, [b"Content-Length: %d" % length], body),
        response(
            CREATED, [b"Transfer-Encoding: chunked"], chunked(body[:1000], body[1000:])
        ),
    ):
        fields = reader(data, 1500)
        assert (fields["result"], fields["consumed"]) == ("OK", len(data))
        assert (fields["overflowed"], fields["keeps"]) == (overflowed, not overflowed)
        assert fields["body_length"] <= BODY_CAPACITY
        if not overflowed:
            assert fields["body"] == body


FIRST_RESPONSE = response(CREATED, [b"Content-Length: 2"], b"ok")
BEHIND_FIRST_RESPONSE = FIRST_RESPONSE + response(
    b"HTTP/1.1 500 Internal Server Error", [b"Content-Length: 0"]
)


def test_bytes_behind_the_message_in_the_same_piece_end_reuse(reader, record_property):
    evidence(
        record_property,
        "second response behind the first, in the same piece",
        RECEIPT,
        "first response only; the leftover bytes end reuse, so the connection is closed",
    )
    fields = reader(BEHIND_FIRST_RESPONSE, len(BEHIND_FIRST_RESPONSE))
    assert (fields["result"], fields["status"], fields["body"]) == ("OK", 201, b"ok")
    assert fields["consumed"] == len(FIRST_RESPONSE)
    assert fields["keeps"] is False


def test_message_end_stops_before_bytes_of_later_pieces(reader, record_property):
    evidence(
        record_property,
        "second response behind the first, pieces of 1",
        RECEIPT,
        "first response only, no byte behind it consumed; the reader saw no leftover "
        "bytes, so the complete keep-alive response leaves the connection reusable",
    )
    fields = reader(BEHIND_FIRST_RESPONSE, 1)
    assert (fields["result"], fields["status"], fields["body"]) == ("OK", 201, b"ok")
    assert fields["consumed"] == len(FIRST_RESPONSE)
    assert fields["keeps"] is True


def header_bytes_response(reason_phrase, aggregate):
    """Fill one header so the reason phrase, names and values total aggregate bytes."""
    counted = len(reason_phrase) + len(b"Content-Length") + len(b"0")
    counted += len(b"X-Filler")
    filler = b"f" * (aggregate - counted)
    return response(
        b"HTTP/1.1 201 " + reason_phrase,
        [b"X-Filler: " + filler, b"Content-Length: 0"],
    )


@pytest.mark.parametrize(
    "reason_phrase, aggregate, result",
    [
        pytest.param(b"Created", 4096, "OK", id="aggregate-4096"),
        pytest.param(b"Created", 4097, "EMSGSIZE", id="aggregate-4097"),
        pytest.param(b"", 4096, "OK", id="aggregate-4096-empty-reason-phrase"),
        pytest.param(b"", 4097, "EMSGSIZE", id="aggregate-4097-empty-reason-phrase"),
    ],
)
def test_header_capacity_boundary(
    reader, record_property, reason_phrase, aggregate, result
):
    evidence(
        record_property,
        f"reason phrase, header names and values of {aggregate} bytes",
        BUFFERS + HEADER_COUNT,
        f"{result}; reason phrase, names and values count, the status line prefix, "
        "separators and line ends do not",
    )
    data = header_bytes_response(reason_phrase, aggregate)
    for piece_size in (4096, 1):
        assert reader(data, piece_size)["result"] == result


def test_reason_phrase_counts_against_the_header_capacity(reader, record_property):
    evidence(
        record_property,
        "headers of 4089 bytes and a reason phrase of 8 bytes",
        BUFFERS + HEADER_COUNT,
        "EMSGSIZE",
    )
    data = header_bytes_response(b"Created", 4096).replace(
        b" 201 Created\r\n", b" 201 Created!\r\n"
    )
    for piece_size in (4096, 1):
        assert reader(data, piece_size)["result"] == "EMSGSIZE"


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param(
            [b"Transfer-Encoding: chunked", b"Content-Length: 3"],
            id="transfer-encoding-first",
        ),
        pytest.param(
            [b"Content-Length: 3", b"Transfer-Encoding: chunked"],
            id="content-length-first",
        ),
    ],
)
def test_transfer_encoding_with_content_length_is_malformed(
    reader, record_property, headers
):
    evidence(
        record_property,
        f"both framings {headers}",
        MESSAGE_LENGTH + " and " + RECEIPT,
        "EBADMSG; a response with both framings is handled as an error, no receipt",
    )
    data = response(CREATED, headers, chunked(b"a"))
    for piece_size in (4096, 1):
        assert reader(data, piece_size)["result"] == "EBADMSG"


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(
            response(CREATED, [b"Content-Length: %d" % 2**64], b"hello"),
            id="content-length-2-to-the-64",
        ),
        pytest.param(
            response(CREATED, [b"Content-Length: %d" % (2**64 + 5)], b"hello"),
            id="content-length-wraps-to-5",
        ),
        pytest.param(
            response(CREATED, [b"Content-Length: " + b"9" * 30], b"hello"),
            id="content-length-30-digits",
        ),
        pytest.param(
            response(
                CREATED,
                [b"Transfer-Encoding: chunked"],
                b"%x\r\na\r\n0\r\n\r\n" % 2**64,
            ),
            id="chunk-size-2-to-the-64",
        ),
        pytest.param(
            response(
                CREATED,
                [b"Transfer-Encoding: chunked"],
                b"%x\r\na\r\n0\r\n\r\n" % (2**64 + 1),
            ),
            id="chunk-size-wraps-to-1",
        ),
    ],
)
def test_lengths_beyond_64_bits_are_malformed(reader, record_property, data):
    evidence(
        record_property,
        "length beyond 64 bits",
        MESSAGE_LENGTH + " and " + FRAMING + " and " + RECEIPT,
        "EBADMSG; no length is wrapped into a smaller value, no receipt",
    )
    for piece_size in (4096, 1):
        assert reader(data, piece_size)["result"] == "EBADMSG"


@pytest.mark.parametrize("value", [b"", b" "], ids=["no-value", "space-only"])
def test_empty_location_keeps_no_address(reader, record_property, value):
    evidence(
        record_property,
        f"empty Location value {value!r}",
        LOCATION_FIELD + " and " + RECEIPT,
        "complete; the empty value is kept as empty, no address is invented",
    )
    data = response(CREATED, [b"Location:" + value, b"Content-Length: 0"])
    for piece_size in (4096, 1):
        fields = reader(data, piece_size)
        assert (fields["result"], fields["status"], fields["location"]) == (
            "OK",
            201,
            "",
        )


def test_read_after_complete_is_rejected(reader, record_property):
    evidence(
        record_property, "read after the end", RECEIPT, "EBADMSG, nothing consumed"
    )
    data = response(CREATED, [b"Content-Length: 0"])
    fields = reader(data, 4096, "read-after-complete")
    assert (fields["result"], fields["consumed"]) == ("EBADMSG", len(data))


REQUEST = DESIGN + "registration-flow-and-recovery"
OBSERVATION_REQUEST = (
    "Development/system/design/system/interfaces-and-behavior.md"
    "#delivery-clock-and-configuration"
)
DEVICE_CONDITION = "identifier=urn%3Astethoscope%3Adevice|stetho-A1B2C3D4E5F6"


def expected_head(resource, condition, body_length, host, port, base):
    return (
        f"POST {base}/{resource} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Content-Type: application/fhir+json\r\n"
        "Accept: application/fhir+json\r\n"
        "Prefer: return=representation\r\n"
        f"If-None-Exist: {condition}\r\n"
        f"Content-Length: {body_length}\r\n"
        "\r\n"
    )


@pytest.fixture(scope="module")
def request_head(reader):
    def run(
        resource="Device",
        condition=DEVICE_CONDITION,
        body_length=127,
        host="172.20.10.7",
        port=8443,
        base="/fhir",
        capacity=1024,
        option="",
    ):
        arguments = [reader.target, "request-head", resource, condition]
        arguments += [str(body_length), host, str(port), base, str(capacity)]
        arguments += [option] if option else []
        completed = subprocess.run(
            [str(item) for item in arguments],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        name, length, head, untouched, terminated = completed.stdout.split()
        assert untouched == "1", "wrote beyond the given capacity"
        assert terminated == "1", "head is not NUL-terminated inside the capacity"
        text = "" if head == "-" else bytes.fromhex(head).decode("latin-1")
        return name, int(length), text

    return run


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({}, id="device-registration"),
        pytest.param(
            {
                "resource": "Observation",
                "condition": "identifier=urn%3Astethoscope%3Ameasurement|"
                + "7501%3A2026-11-08T21%3A11%3A53.250Z",
                "body_length": 2048,
            },
            id="observation",
        ),
        pytest.param({"base": ""}, id="base-without-path"),
        pytest.param(
            {"port": 443, "host": "nglegion"}, id="default-port-still-written"
        ),
        pytest.param(
            {
                "resource": "Observation",
                "condition": "identifier=urn%3Astethoscope%3Ameasurement|"
                + "a" * 64
                + "%3A2026-11-08T21%3A11%3A53.250Z",
                "body_length": 2048,
                "host": "h" * 253,
                "base": "/" + "p" * 255,
                "port": 65535,
            },
            id="longest-fields-fit-1024",
        ),
    ],
)
def test_request_head_layout(request_head, record_property, fields):
    evidence(
        record_property,
        f"request head {fields}",
        OBSERVATION_REQUEST if fields.get("resource") == "Observation" else REQUEST,
        "exact request line and headers",
    )
    arguments = {
        "resource": "Device",
        "condition": DEVICE_CONDITION,
        "body_length": 127,
        "host": "172.20.10.7",
        "port": 8443,
        "base": "/fhir",
    }
    arguments.update(fields)
    head = expected_head(**arguments)
    assert request_head(**fields) == ("OK", len(head), head)


def test_request_head_exact_fit_and_one_short(request_head, record_property):
    evidence(
        record_property,
        "head capacity boundary",
        REQUEST,
        "OK at length + 1, ENOSPC at length",
    )
    head = expected_head("Device", DEVICE_CONDITION, 127, "172.20.10.7", 8443, "/fhir")
    assert request_head(capacity=len(head) + 1) == ("OK", len(head), head)
    assert request_head(capacity=len(head)) == ("ENOSPC", 0, "")
    assert request_head(capacity=0) == ("ENOSPC", 0, "")


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({"condition": ""}, id="unconditional-post"),
        pytest.param({"condition": "<null>"}, id="null-condition"),
        pytest.param({"condition": "a b"}, id="space-in-condition"),
        pytest.param({"condition": "a\r\nX-Injected: 1"}, id="header-injection"),
        pytest.param({"condition": "a\x7f"}, id="delete-in-condition"),
        pytest.param({"resource": ""}, id="empty-resource"),
        pytest.param({"resource": "/Device"}, id="absolute-resource"),
        pytest.param({"resource": "Device/1"}, id="resource-with-id"),
        pytest.param({"resource": "Device1"}, id="digit-in-resource"),
        pytest.param({"resource": "<null>"}, id="null-resource"),
        pytest.param({"host": ""}, id="empty-host"),
        pytest.param({"host": "a b"}, id="space-in-host"),
        pytest.param({"host": "<null>"}, id="null-host"),
        pytest.param({"port": 0}, id="port-0"),
        pytest.param({"base": "fhir"}, id="base-without-slash"),
        pytest.param({"base": "/fhir/"}, id="base-trailing-slash"),
        pytest.param({"base": "/"}, id="base-slash-only"),
        pytest.param({"base": "<null>"}, id="null-base"),
        pytest.param({"body_length": 0}, id="empty-body"),
        pytest.param({"option": "null-request"}, id="null-request"),
        pytest.param({"option": "null-output"}, id="null-output"),
        pytest.param({"option": "null-length"}, id="null-length"),
    ],
)
def test_request_head_rejects(request_head, record_property, fields):
    evidence(record_property, f"request head {fields}", REQUEST, "EINVAL, empty output")
    name, length, text = request_head(**fields)
    assert name == "EINVAL"
    assert text == ""
    if fields.get("option") != "null-length":
        assert length == 0
