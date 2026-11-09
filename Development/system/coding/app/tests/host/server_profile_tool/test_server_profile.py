"""VT-08: server profile host tool, deployment file to flash image."""

import base64
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[6]
TOOL = REPOSITORY / "Development/system/coding/tools/server-profile/server_profile.py"
CERTIFICATES = HERE / "certificates"
PROFILE = "Development/system/design/STORAGE/server-profile.md#"
FILE_RULES = PROFILE + "deployment-file"
URL_RULES = PROFILE + "canonical-base-url"
CERTIFICATE_RULES = PROFILE + "certificate-checks"
IMAGE_RULES = PROFILE + "image-built-from-the-file"
COMMANDS = PROFILE + "commands"
LIMITS = PROFILE + "parameters"
ALLOCATION = PROFILE + "verification-allocation"
LAYOUT = "Development/system/design/STORAGE/interfaces-and-behavior.md#flash-layout"
VT_ID = "VT-08"
# The verification allocation traces secret material in the deployment file to evidence and privacy.
VT_ID_BY_TEST = {"test_other_pem_labels_are_rejected": "VT-11"}

DNS_HOST = "fhir.example.test"
IP_HOST = "192.0.2.10"
DNS_URL = f"https://{DNS_HOST}:8443/fhir"
IP_URL = f"https://{IP_HOST}:8443/fhir"
NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)
PARTITION_START = 0xF00000
PARTITION_SIZE = 0x30000
DEPLOYMENT_NAME = "lab-test"


@pytest.fixture(scope="module", autouse=True)
def traceability(request):
    """Map every case before the module fixtures load the tool, so a load failure keeps it."""
    for item in request.session.items:
        if getattr(item, "module", None) is request.module:
            item.user_properties.append(
                ("vt_id", VT_ID_BY_TEST.get(item.originalname, VT_ID))
            )


@pytest.fixture(scope="module")
def tool():
    specification = importlib.util.spec_from_file_location("server_profile", TOOL)
    module = importlib.util.module_from_spec(specification)
    # dataclasses look the defining module up by name while the class is created.
    sys.modules[specification.name] = module
    try:
        specification.loader.exec_module(module)
    except ModuleNotFoundError as error:
        pytest.fail(
            f"server_profile.py needs the {error.name!r} package, which the design takes "
            "from the toolchain environment; install it in the host test environment",
            pytrace=False,
        )
    yield module
    sys.modules.pop(specification.name, None)


def evidence(record_property, scenario, basis, expected):
    record_property("scenario", scenario)
    record_property("basis", basis)
    record_property("expected", expected)


def certificate_text(fixture):
    return (CERTIFICATES / f"{fixture}.pem").read_text(encoding="ascii")


def toml_string(text):
    """A TOML basic string; JSON string escapes are a subset of TOML's."""
    return json.dumps(text)


def deployment_file(
    directory,
    name=DEPLOYMENT_NAME,
    top_level_extra=(),
    server_extra=(),
    trailing_extra=(),
    **values,
):
    """Write a deployment file; each value is TOML text and None leaves the key out."""
    fields = {
        "format": "1",
        "description": None,
        "base_url": toml_string(DNS_URL),
        "keep_alive_seconds": "600",
        "certificate": toml_string(certificate_text("dns-host")),
    }
    fields.update(values)
    lines = [
        f"{key} = {fields[key]}"
        for key in ("format", "description")
        if fields[key] is not None
    ]
    lines += list(top_level_extra) + ["[server]"]
    lines += [
        f"{key} = {fields[key]}"
        for key in ("base_url", "keep_alive_seconds", "certificate")
        if fields[key] is not None
    ]
    lines += list(server_extra) + list(trailing_extra)
    path = directory / f"{name}.toml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def rejection(tool, function, *arguments):
    with pytest.raises(tool.DeploymentError) as raised:
        function(*arguments)
    return str(raised.value)


def crc32(data):
    """IEEE 802.3 CRC-32, reflected polynomial 0xEDB88320, written independently of zlib."""
    value = 0xFFFFFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xEDB88320 if value & 1 else 0)
    return value ^ 0xFFFFFFFF


def expected_image(base_url, keep_alive_seconds, certificate):
    url = base_url.encode("ascii")
    body = b"STPV" + bytes([1])
    body += len(url).to_bytes(2, "little") + url
    body += keep_alive_seconds.to_bytes(4, "little")
    body += len(certificate).to_bytes(2, "little") + certificate
    return body + crc32(body).to_bytes(4, "little")


def devicetree(build_directory, partition_size=PARTITION_SIZE, has_partition=True):
    """Shape of the generated <build>/zephyr/zephyr.dts, including its origin comments."""
    server_profile = (
        "\t\t\t\t\t/* node '/soc/flash-controller@60002000/flash@0/partitions/"
        "partition@f00000' defined in boards\\flash-layout.dtsi:50 */\n"
        "\t\t\t\t\tserver_profile_partition: partition@f00000 {\n"
        '\t\t\t\t\t\tcompatible = "zephyr,mapped-partition"; /* in boards\\flash-layout.dtsi:51 */\n'
        '\t\t\t\t\t\tlabel = "server-profile";\n'
        f"\t\t\t\t\t\treg = < 0xf00000 {partition_size:#x} >; /* in boards\\flash-layout.dtsi:53 */\n"
        "\t\t\t\t\t\tread-only;\n"
        "\t\t\t\t\t};\n"
    )
    text = (
        "/dts-v1/;\n\n/ {\n\tsoc {\n\t\tflash-controller@60002000 {\n"
        "\t\t\tflash@0 {\n\t\t\t\tpartitions {\n"
        "\t\t\t\t\tstorage_partition: partition@e80000 {\n"
        '\t\t\t\t\t\tcompatible = "zephyr,mapped-partition";\n'
        '\t\t\t\t\t\tlabel = "storage";\n'
        "\t\t\t\t\t\treg = < 0xe80000 0x30000 >;\n"
        "\t\t\t\t\t};\n\n"
        + (server_profile if has_partition else "")
        + "\t\t\t\t};\n\t\t\t};\n\t\t};\n\t};\n};\n"
    )
    path = build_directory / "zephyr" / "zephyr.dts"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return build_directory


def run_tool(*arguments, environment=None):
    return subprocess.run(
        [sys.executable, str(TOOL), *[str(argument) for argument in arguments]],
        capture_output=True,
        text=True,
        timeout=120,
        env=environment,
    )


def written_images(build_directory):
    return sorted((build_directory / "server-profile").glob("*.bin"))


def test_valid_deployment_file_in_the_design_form(tool, record_property, tmp_path):
    evidence(
        record_property,
        "valid deployment file with description and a multi-line certificate",
        FILE_RULES + " and " + ALLOCATION,
        "loaded: deployment name from the file name, canonical URL, keep-alive and "
        "the certificate with LF line endings",
    )
    certificate = certificate_text("dns-host")
    path = deployment_file(
        tmp_path,
        description=toml_string("Local HAPI test server"),
        certificate='"""\n' + certificate + '"""',
    )
    deployment = tool.load_deployment(path, NOW)
    assert (deployment.name, deployment.base_url, deployment.keep_alive_seconds) == (
        DEPLOYMENT_NAME,
        DNS_URL,
        600,
    )
    assert deployment.certificate_text == certificate.encode("ascii")


@pytest.mark.parametrize(
    "values, key, rule_word",
    [
        pytest.param({"format": "2"}, "format", "1", id="format-2"),
        pytest.param({"format": '"1"'}, "format", "1", id="format-string"),
        pytest.param({"format": "true"}, "format", "1", id="format-boolean"),
        pytest.param({"format": "1.0"}, "format", "1", id="format-float"),
        pytest.param({"format": None}, "format", "1", id="format-missing"),
        pytest.param(
            {"description": "5"}, "description", "string", id="description-integer"
        ),
        pytest.param(
            {"top_level_extra": ['owner = "lab"']}, "owner", "unknown", id="unknown-key"
        ),
        pytest.param(
            {"trailing_extra": ["[client]", 'name = "x"']},
            "client",
            "unknown",
            id="unknown-table",
        ),
        pytest.param(
            {"server_extra": ['base_uri = "https://h/fhir"']},
            "server.base_uri",
            "unknown",
            id="misspelt-server-key",
        ),
        pytest.param(
            {"base_url": None}, "server.base_url", "required", id="base-url-missing"
        ),
        pytest.param(
            {"keep_alive_seconds": None},
            "server.keep_alive_seconds",
            "required",
            id="keep-alive-missing",
        ),
        pytest.param(
            {"certificate": None},
            "server.certificate",
            "required",
            id="certificate-missing",
        ),
        pytest.param(
            {"base_url": "443"}, "server.base_url", "string", id="base-url-integer"
        ),
        pytest.param(
            {"certificate": "1"},
            "server.certificate",
            "string",
            id="certificate-integer",
        ),
        pytest.param(
            {"keep_alive_seconds": "5"},
            "server.keep_alive_seconds",
            "4294967295",
            id="keep-alive-5",
        ),
        pytest.param(
            {"keep_alive_seconds": "4294967296"},
            "server.keep_alive_seconds",
            "4294967295",
            id="keep-alive-4294967296",
        ),
        pytest.param(
            {"keep_alive_seconds": "-1"},
            "server.keep_alive_seconds",
            "4294967295",
            id="keep-alive-negative",
        ),
        pytest.param(
            {"keep_alive_seconds": "600.0"},
            "server.keep_alive_seconds",
            "integer",
            id="keep-alive-float",
        ),
        pytest.param(
            {"keep_alive_seconds": '"600"'},
            "server.keep_alive_seconds",
            "integer",
            id="keep-alive-string",
        ),
        pytest.param(
            {"keep_alive_seconds": "true"},
            "server.keep_alive_seconds",
            "integer",
            id="keep-alive-boolean",
        ),
    ],
)
def test_file_rule_violation_names_key_and_rule(
    tool, record_property, tmp_path, values, key, rule_word
):
    evidence(
        record_property,
        f"deployment file {values}",
        FILE_RULES,
        f"rejected naming {key} and its rule",
    )
    message = rejection(
        tool, tool.load_deployment, deployment_file(tmp_path, **values), NOW
    )
    assert key in message
    assert rule_word in message.removeprefix(key)


def test_server_must_be_a_table(tool, record_property, tmp_path):
    evidence(
        record_property, "server is a string", FILE_RULES, "rejected naming server"
    )
    path = tmp_path / f"{DEPLOYMENT_NAME}.toml"
    path.write_text('format = 1\nserver = "https://h/fhir"\n', encoding="utf-8")
    assert "server" in rejection(tool, tool.load_deployment, path, NOW)


def test_invalid_toml_is_rejected(tool, record_property, tmp_path):
    evidence(
        record_property, "file is not TOML", FILE_RULES, "rejected as not TOML v1.0.0"
    )
    path = tmp_path / f"{DEPLOYMENT_NAME}.toml"
    path.write_text("format = 1\n[server\n", encoding="utf-8")
    assert "TOML" in rejection(tool, tool.load_deployment, path, NOW)


@pytest.mark.parametrize("seconds", [6, 600, 4294967295])
def test_keep_alive_range_is_accepted(tool, record_property, tmp_path, seconds):
    evidence(
        record_property,
        f"keep-alive of {seconds} s",
        FILE_RULES + " and " + LIMITS,
        "accepted unchanged",
    )
    path = deployment_file(tmp_path, keep_alive_seconds=str(seconds))
    assert tool.load_deployment(path, NOW).keep_alive_seconds == seconds


@pytest.mark.parametrize(
    "file_name, is_accepted",
    [
        pytest.param("lab-hapi-2.toml", True, id="lowercase-digits-hyphens"),
        pytest.param("Lab-HAPI.toml", False, id="uppercase"),
        pytest.param("lab_hapi.toml", False, id="underscore"),
        pytest.param("lab-hapi.txt", False, id="not-toml-suffix"),
    ],
)
def test_deployment_file_name(tool, record_property, tmp_path, file_name, is_accepted):
    evidence(
        record_property,
        f"deployment file named {file_name}",
        FILE_RULES,
        "accepted" if is_accepted else "rejected naming the file name",
    )
    path = deployment_file(tmp_path).rename(tmp_path / file_name)
    if is_accepted:
        assert tool.load_deployment(path, NOW).name == Path(file_name).stem
    else:
        assert "name" in rejection(tool, tool.load_deployment, path, NOW)


@pytest.mark.parametrize(
    "text, canonical",
    [
        pytest.param(IP_URL, IP_URL, id="already-canonical"),
        pytest.param(
            "HTTPS://FHIR.Example.TEST:8443/fhir",
            DNS_URL,
            id="scheme-and-host-lowercased",
        ),
        pytest.param(
            "https://fhir.example.test:8443/FHIR/R4",
            "https://fhir.example.test:8443/FHIR/R4",
            id="path-case-kept",
        ),
        pytest.param(
            "https://fhir.example.test/fhir",
            "https://fhir.example.test:443/fhir",
            id="missing-port-becomes-443",
        ),
        pytest.param(DNS_URL + "/", DNS_URL, id="trailing-slash-removed"),
        pytest.param(
            "https://fhir.example.test:8443/",
            "https://fhir.example.test:8443",
            id="root-path",
        ),
        pytest.param(
            "https://fhir.example.test:8443",
            "https://fhir.example.test:8443",
            id="no-path",
        ),
    ],
)
def test_canonical_base_url(tool, record_property, text, canonical):
    evidence(record_property, f"base URL {text}", URL_RULES, f"canonical {canonical}")
    assert tool.canonical_base_url(text)[0] == canonical


@pytest.mark.parametrize(
    "text, rule_word",
    [
        pytest.param("http://fhir.example.test:8443/fhir", "https", id="http-scheme"),
        pytest.param(
            "https://user@fhir.example.test:8443/fhir", "userinfo", id="userinfo"
        ),
        pytest.param(
            "https://user:secret@fhir.example.test:8443/fhir",
            "userinfo",
            id="userinfo-with-password",
        ),
        pytest.param(DNS_URL + "?_format=json", "query", id="query"),
        pytest.param(DNS_URL + "?", "query", id="empty-query"),
        pytest.param(DNS_URL + "#top", "fragment", id="fragment"),
        pytest.param("https://[2001:db8::1]:8443/fhir", "IPv6", id="ipv6-literal"),
        pytest.param("https:///fhir", "host", id="no-host"),
        pytest.param("https://fhír.example.test/fhir", "ASCII", id="non-ascii-host"),
    ],
)
def test_base_url_rule_violation(tool, record_property, text, rule_word):
    evidence(
        record_property,
        f"base URL {text}",
        URL_RULES,
        "rejected naming server.base_url and its rule",
    )
    message = rejection(tool, tool.canonical_base_url, text)
    assert "server.base_url" in message
    assert rule_word in message


def long_url(prefix, length):
    return prefix + "/" + "p" * (length - len(prefix) - 1)


@pytest.mark.parametrize(
    "text, is_accepted",
    [
        pytest.param(long_url(DNS_URL[: -len("/fhir")], 256), True, id="canonical-256"),
        pytest.param(
            long_url(DNS_URL[: -len("/fhir")], 256) + "/",
            True,
            id="257-with-trailing-slash-is-256-canonical",
        ),
        pytest.param(
            long_url("https://fhir.example.test", 252),
            True,
            id="252-without-port-is-256-canonical",
        ),
        pytest.param(
            long_url(DNS_URL[: -len("/fhir")], 257), False, id="canonical-257"
        ),
        pytest.param(
            long_url("https://fhir.example.test", 253),
            False,
            id="253-without-port-is-257-canonical",
        ),
    ],
)
def test_canonical_base_url_length_boundary(tool, record_property, text, is_accepted):
    evidence(
        record_property,
        f"base URL of {len(text)} bytes before canonicalization",
        URL_RULES + " and " + LIMITS,
        "the canonical form counts: at most 256 bytes accepted, 257 rejected",
    )
    if is_accepted:
        assert len(tool.canonical_base_url(text)[0]) == 256
    else:
        message = rejection(tool, tool.canonical_base_url, text)
        assert "server.base_url" in message
        assert "256" in message


def test_certificate_line_endings_are_normalized(tool, record_property, tmp_path):
    evidence(
        record_property,
        "certificate with CRLF line endings, surrounding blank lines and no final newline",
        FILE_RULES + " and " + IMAGE_RULES,
        "accepted; LF line endings and exactly one final newline",
    )
    certificate = certificate_text("dns-host")
    written = "\r\n\r\n" + certificate.strip().replace("\n", "\r\n")
    path = deployment_file(tmp_path, certificate=toml_string(written))
    assert tool.load_deployment(path, NOW).certificate_text == certificate.encode()


def pem_block(label, content=b"public test data, not key material"):
    encoded = base64.b64encode(content).decode("ascii")
    return f"-----BEGIN {label}-----\n{encoded}\n-----END {label}-----\n"


@pytest.mark.parametrize(
    "label",
    [
        "PRIVATE KEY",
        "EC PRIVATE KEY",
        "RSA PRIVATE KEY",
        "ENCRYPTED PRIVATE KEY",
        "PUBLIC KEY",
    ],
)
@pytest.mark.parametrize(
    "has_certificate", [True, False], ids=["with-certificate", "alone"]
)
def test_other_pem_labels_are_rejected(
    tool, record_property, tmp_path, label, has_certificate
):
    evidence(
        record_property,
        f"PEM label {label}, {'after a certificate' if has_certificate else 'alone'}",
        FILE_RULES + " and " + ALLOCATION,
        "rejected naming server.certificate and the label",
    )
    text = (certificate_text("dns-host") if has_certificate else "") + pem_block(label)
    path = deployment_file(tmp_path, certificate=toml_string(text))
    message = rejection(tool, tool.load_deployment, path, NOW)
    assert "server.certificate" in message
    assert label in message


@pytest.mark.parametrize(
    "text, rule_word",
    [
        pytest.param(
            certificate_text("dns-host") + certificate_text("ip-host"),
            "one",
            id="two-certificates",
        ),
        pytest.param("not a certificate\n", "one", id="no-pem"),
        pytest.param(pem_block("CERTIFICATE"), "rule 1", id="not-x509"),
    ],
)
def test_certificate_must_be_one_x509_certificate(
    tool, record_property, tmp_path, text, rule_word
):
    evidence(
        record_property,
        "certificate text that is not exactly one X.509 certificate",
        FILE_RULES + " and " + CERTIFICATE_RULES + " (rule 1)",
        "rejected naming server.certificate and the rule",
    )
    path = deployment_file(tmp_path, certificate=toml_string(text))
    message = rejection(tool, tool.load_deployment, path, NOW)
    assert "server.certificate" in message
    assert rule_word in message


def test_certificate_length_boundary(tool, record_property, tmp_path):
    evidence(
        record_property,
        "certificate of 8192 bytes, the same with CRLF, and 8193 bytes",
        FILE_RULES + " and " + LIMITS,
        "8192 bytes after LF normalization accepted, 8193 rejected naming the limit",
    )
    maximum = certificate_text("maximum-length")
    assert len(maximum.encode("ascii")) == 8192
    for text in (maximum, maximum.replace("\n", "\r\n")):
        path = deployment_file(tmp_path, certificate=toml_string(text))
        assert tool.load_deployment(path, NOW).certificate_text == maximum.encode()
    header, first_line, rest = maximum.split("\n", 2)
    one_byte_longer = f"{header}\n{first_line[:32]}\n{first_line[32:]}\n{rest}"
    path = deployment_file(tmp_path, certificate=toml_string(one_byte_longer))
    message = rejection(tool, tool.load_deployment, path, NOW)
    assert "server.certificate" in message
    assert "8192" in message


@pytest.mark.parametrize(
    "fixture, base_url, rule",
    [
        pytest.param("dns-host", DNS_URL, None, id="dns-host"),
        pytest.param(
            "dns-host-mixed-case", DNS_URL, None, id="dns-name-case-insensitive"
        ),
        pytest.param(
            "dns-host",
            "https://FHIR.EXAMPLE.TEST:8443/fhir",
            None,
            id="host-case-insensitive",
        ),
        pytest.param("ip-host", IP_URL, None, id="ip-host-with-ip-entry"),
        pytest.param("no-usage-extensions", DNS_URL, None, id="no-usage-extensions"),
        pytest.param(
            "extended-key-usage-any", DNS_URL, None, id="any-extended-key-usage"
        ),
        pytest.param("issued-by-authority", DNS_URL, 2, id="not-self-issued"),
        pytest.param(
            "self-named-foreign-signature",
            DNS_URL,
            2,
            id="self-named-foreign-signature",
        ),
        pytest.param(
            "no-subject-alternative-name", DNS_URL, 3, id="no-subject-alternative-name"
        ),
        pytest.param("wrong-dns-name", DNS_URL, 3, id="wrong-dns-name"),
        pytest.param("wildcard-dns-name", DNS_URL, 3, id="wildcard-dns-name"),
        pytest.param(
            "dns-name-spelling-ip-host", IP_URL, 3, id="dns-entry-for-ip-host"
        ),
        pytest.param("dns-host", IP_URL, 3, id="dns-certificate-for-ip-host"),
        pytest.param(
            "ip-host",
            "https://fhir.example.test:8443/fhir",
            3,
            id="ip-entry-for-dns-host",
        ),
        pytest.param("expired", DNS_URL, 4, id="expired"),
        pytest.param("not-yet-valid", DNS_URL, 4, id="not-yet-valid"),
        pytest.param(
            "key-usage-without-digital-signature",
            DNS_URL,
            5,
            id="key-usage-without-digital-signature",
        ),
        pytest.param(
            "extended-key-usage-client-only",
            DNS_URL,
            5,
            id="extended-key-usage-client-only",
        ),
    ],
)
def test_certificate_rules(tool, record_property, tmp_path, fixture, base_url, rule):
    evidence(
        record_property,
        f"certificate {fixture} for {base_url}, date {NOW:%Y-%m-%d}",
        CERTIFICATE_RULES + " and " + ALLOCATION,
        "accepted"
        if rule is None
        else f"rejected naming server.certificate and rule {rule}",
    )
    path = deployment_file(
        tmp_path,
        base_url=toml_string(base_url),
        certificate=toml_string(certificate_text(fixture)),
    )
    if rule is None:
        assert tool.load_deployment(path, NOW).certificate_text == certificate_text(
            fixture
        ).encode("ascii")
    else:
        message = rejection(tool, tool.load_deployment, path, NOW)
        assert "server.certificate" in message
        assert f"rule {rule}" in message


@pytest.mark.parametrize(
    "fixture, date, is_accepted",
    [
        pytest.param(
            "expired",
            datetime(2000, 6, 1, tzinfo=timezone.utc),
            True,
            id="expired-cert-in-its-period",
        ),
        pytest.param(
            "dns-host",
            datetime(2019, 12, 31, tzinfo=timezone.utc),
            False,
            id="before-valid-period",
        ),
    ],
)
def test_validity_follows_the_given_date(
    tool, record_property, tmp_path, fixture, date, is_accepted
):
    evidence(
        record_property,
        f"certificate {fixture} on {date:%Y-%m-%d}",
        CERTIFICATE_RULES + " (rule 4)",
        "accepted" if is_accepted else "rejected naming rule 4",
    )
    path = deployment_file(tmp_path, certificate=toml_string(certificate_text(fixture)))
    if is_accepted:
        tool.load_deployment(path, date)
    else:
        assert "rule 4" in rejection(tool, tool.load_deployment, path, date)


def test_independent_crc_matches_the_ieee_check_value(record_property):
    evidence(
        record_property,
        "reference CRC-32 of the test oracle",
        LAYOUT,
        "CRC-32 of ASCII 123456789 is 0xCBF43926",
    )
    assert crc32(b"123456789") == 0xCBF43926


@pytest.mark.parametrize(
    "base_url, keep_alive_seconds, fixture",
    [
        pytest.param(DNS_URL, 600, "dns-host", id="lab-sized"),
        pytest.param(IP_URL, 6, "ip-host", id="minimum-keep-alive"),
    ],
)
def test_image_layout(
    tool, record_property, tmp_path, base_url, keep_alive_seconds, fixture
):
    evidence(
        record_property,
        f"image for {base_url}, keep-alive {keep_alive_seconds} s",
        IMAGE_RULES + " and " + LAYOUT,
        "STPV, version 1, little-endian lengths and keep-alive, LF certificate, "
        "IEEE CRC-32 over all preceding bytes",
    )
    path = deployment_file(
        tmp_path,
        base_url=toml_string(base_url),
        keep_alive_seconds=str(keep_alive_seconds),
        certificate=toml_string(certificate_text(fixture)),
    )
    image = tool.build_image(tool.load_deployment(path, NOW))
    assert image == expected_image(
        base_url, keep_alive_seconds, certificate_text(fixture).encode("ascii")
    )


def test_largest_image_is_8465_bytes(tool, record_property, tmp_path):
    evidence(
        record_property,
        "256-byte URL, 8192-byte certificate, keep-alive 4294967295 s",
        LAYOUT + " and " + LIMITS,
        "8465 bytes, every field at its documented offset",
    )
    base_url = long_url(DNS_URL[: -len("/fhir")], 256)
    certificate = certificate_text("maximum-length").encode("ascii")
    path = deployment_file(
        tmp_path,
        base_url=toml_string(base_url),
        keep_alive_seconds="4294967295",
        certificate=toml_string(certificate.decode()),
    )
    image = tool.build_image(tool.load_deployment(path, NOW))
    assert len(image) == 8465
    assert image[:5] == b"STPV\x01"
    assert image[5:7] == (256).to_bytes(2, "little")
    assert image[7:263] == base_url.encode("ascii")
    assert image[263:267] == b"\xff\xff\xff\xff"
    assert image[267:269] == (8192).to_bytes(2, "little")
    assert image[269:8461] == certificate
    assert image[8461:] == crc32(image[:8461]).to_bytes(4, "little")


def test_partition_from_the_build_devicetree(tool, record_property, tmp_path):
    evidence(
        record_property,
        "generated devicetree with storage and server profile partitions",
        IMAGE_RULES + " and " + LIMITS,
        "start 0xF00000 and size 192 KiB of server_profile_partition",
    )
    build_directory = devicetree(tmp_path)
    assert tool.server_profile_partition(build_directory) == (0xF00000, 192 * 1024)


@pytest.mark.parametrize(
    "has_devicetree", [True, False], ids=["no-node", "no-devicetree"]
)
def test_build_without_the_partition_is_rejected(
    tool, record_property, tmp_path, has_devicetree
):
    evidence(
        record_property,
        "build without server_profile_partition"
        if has_devicetree
        else "build without devicetree",
        IMAGE_RULES + " and " + ALLOCATION,
        "rejected naming --build-dir",
    )
    if has_devicetree:
        devicetree(tmp_path, has_partition=False)
    message = rejection(tool, tool.server_profile_partition, tmp_path)
    assert "--build-dir" in message


@pytest.mark.usefixtures("tool")
def test_check_command_prints_the_deployment(record_property, tmp_path):
    evidence(
        record_property,
        "server_profile.py check with a valid file",
        COMMANDS,
        "exit 0; prints canonical URL, keep-alive, subject, Subject Alternative Names, "
        "expiry and image size",
    )
    path = deployment_file(
        tmp_path, base_url=toml_string("HTTPS://FHIR.Example.TEST/fhir/")
    )
    completed = run_tool("check", path)
    assert completed.returncode == 0, completed.stderr
    image_size = len(
        expected_image(
            "https://fhir.example.test:443/fhir",
            600,
            certificate_text("dns-host").encode("ascii"),
        )
    )
    for text in (
        "https://fhir.example.test:443/fhir",
        "600 s",
        f"CN={DNS_HOST}",
        f"DNS:{DNS_HOST}",
        "9999-12-31",
        f"{image_size} bytes",
    ):
        assert text in completed.stdout


@pytest.mark.usefixtures("tool")
@pytest.mark.parametrize(
    "partition_size_change, is_accepted",
    [
        pytest.param(None, True, id="192-kib-partition"),
        pytest.param(0, True, id="partition-equals-image"),
        pytest.param(-1, False, id="partition-one-byte-short"),
    ],
)
def test_build_command_writes_the_image(
    record_property, tmp_path, partition_size_change, is_accepted
):
    evidence(
        record_property,
        "server_profile.py build, partition "
        + (
            "192 KiB"
            if partition_size_change is None
            else f"image size {partition_size_change:+d}"
        ),
        COMMANDS + " and " + IMAGE_RULES,
        "exit 0 and <build>/server-profile/<deployment>.bin holds the image"
        if is_accepted
        else "exit 1 naming --build-dir and the size; no image written",
    )
    image = expected_image(DNS_URL, 600, certificate_text("dns-host").encode("ascii"))
    partition_size = PARTITION_SIZE
    if partition_size_change is not None:
        partition_size = len(image) + partition_size_change
    build_directory = devicetree(tmp_path / "build", partition_size)
    completed = run_tool(
        "build", deployment_file(tmp_path), "--build-dir", build_directory
    )
    if is_accepted:
        assert completed.returncode == 0, completed.stderr
        output = build_directory / "server-profile" / f"{DEPLOYMENT_NAME}.bin"
        assert written_images(build_directory) == [output]
        assert output.read_bytes() == image
    else:
        assert completed.returncode == 1
        assert "--build-dir" in completed.stderr
        assert str(partition_size) in completed.stderr
        assert written_images(build_directory) == []


@pytest.mark.usefixtures("tool")
@pytest.mark.parametrize(
    "values, key, rule_word",
    [
        pytest.param({"format": "2"}, "format", "1", id="format-2"),
        pytest.param(
            {"server_extra": ["keep_alive = 600"]},
            "server.keep_alive",
            "unknown",
            id="misspelt-key",
        ),
        pytest.param(
            {"keep_alive_seconds": "5"},
            "server.keep_alive_seconds",
            "6",
            id="keep-alive-5",
        ),
        pytest.param(
            {"base_url": toml_string(DNS_URL + "?x=1")},
            "server.base_url",
            "query",
            id="query",
        ),
        pytest.param(
            {
                "certificate": toml_string(
                    certificate_text("dns-host") + pem_block("PRIVATE KEY")
                )
            },
            "server.certificate",
            "PRIVATE KEY",
            id="private-key-label",
        ),
        pytest.param(
            {"certificate": toml_string(certificate_text("wrong-dns-name"))},
            "server.certificate",
            "rule 3",
            id="wrong-dns-name",
        ),
        pytest.param(
            {"certificate": toml_string(certificate_text("expired"))},
            "server.certificate",
            "rule 4",
            id="expired-on-this-date",
        ),
    ],
)
def test_build_command_rejection_writes_nothing(
    record_property, tmp_path, values, key, rule_word
):
    evidence(
        record_property,
        f"server_profile.py build with {next(iter(values))} violated",
        COMMANDS + " and " + ALLOCATION,
        "exit 1; the message names the key and the rule; no image written",
    )
    build_directory = devicetree(tmp_path / "build")
    completed = run_tool(
        "build", deployment_file(tmp_path, **values), "--build-dir", build_directory
    )
    assert completed.returncode == 1
    assert key in completed.stderr
    assert rule_word in completed.stderr.split(key, 1)[1]
    assert written_images(build_directory) == []


@pytest.fixture
def recording_esptool(tmp_path):
    """Stand-in for esptool that records its arguments instead of writing flash."""
    package = tmp_path / "substitutes" / "esptool"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "__main__.py").write_text(
        "import json, os, sys\n"
        "with open(os.environ['STETHO_ESPTOOL_RECORD'], 'w', encoding='utf-8') as record:\n"
        "    json.dump(sys.argv[1:], record)\n",
        encoding="utf-8",
    )
    record = tmp_path / "esptool-arguments.json"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(package.parent), environment.get("PYTHONPATH")])
    )
    environment["STETHO_ESPTOOL_RECORD"] = str(record)
    return environment, record


@pytest.mark.usefixtures("tool")
@pytest.mark.parametrize("is_valid", [True, False], ids=["valid", "keep-alive-5"])
def test_flash_command(record_property, tmp_path, recording_esptool, is_valid):
    evidence(
        record_property,
        f"server_profile.py flash with a {'valid' if is_valid else 'rejected'} file",
        COMMANDS + " and " + LIMITS,
        "esptool writes only the image at 0xF00000"
        if is_valid
        else "exit 1 naming the key; esptool never runs, nothing written to the device",
    )
    environment, record = recording_esptool
    build_directory = devicetree(tmp_path / "build")
    path = deployment_file(tmp_path, keep_alive_seconds="600" if is_valid else "5")
    completed = run_tool(
        "flash",
        path,
        "--build-dir",
        build_directory,
        "--port",
        "COM9",
        environment=environment,
    )
    if is_valid:
        assert completed.returncode == 0, completed.stderr
        arguments = json.loads(record.read_text(encoding="utf-8"))
        output = build_directory / "server-profile" / f"{DEPLOYMENT_NAME}.bin"
        assert arguments[-3:] == ["write-flash", f"{PARTITION_START:#x}", str(output)]
        assert arguments[arguments.index("--port") + 1] == "COM9"
    else:
        assert completed.returncode == 1
        assert "server.keep_alive_seconds" in completed.stderr
        assert not record.exists()
        assert written_images(build_directory) == []
