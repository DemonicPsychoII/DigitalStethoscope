"""Check a deployment file and build its provisioning image.

The deployment file and the commands follow design/STORAGE/provisioning.md;
the image is format version 1 of design/STORAGE/interfaces-and-behavior.md#flash-layout:
magic "STPV", version, base URL length and base URL, server keep-alive seconds,
certificate length and PEM certificate, IEEE CRC-32 over all preceding bytes,
all little-endian.
"""

from __future__ import annotations

import argparse
import ipaddress
import re
import struct
import subprocess
import sys
import tomllib
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm

MAGIC = b"STPV"
VERSION = 1
FILE_FORMAT = 1
BASE_URL_MAX_LENGTH = 256
CERTIFICATE_MAX_LENGTH = 8192
KEEP_ALIVE_MINIMUM_SECONDS = 6
KEEP_ALIVE_MAXIMUM_SECONDS = 0xFFFFFFFF
DEFAULT_HTTPS_PORT = 443

DEPLOYMENT_NAME = re.compile(r"[a-z0-9-]+")
DNS_LABEL = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?")
PEM_BEGIN = re.compile(r"-----BEGIN ([^-\n]*)-----")
PEM_CERTIFICATE = re.compile(
    r"-----BEGIN CERTIFICATE-----\n[A-Za-z0-9+/=\n]+-----END CERTIFICATE-----\n"
)
PARTITION = re.compile(
    r"\bprovisioning_partition:\s*(?:\w+:\s*)*partition@[0-9a-fA-F]+\s*\{[^}]*?"
    r"\breg\s*=\s*<\s*(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s*>",
    re.DOTALL,
)

TOP_LEVEL_KEYS = {"format", "description", "server"}
SERVER_KEYS = {"base_url", "keep_alive_seconds", "certificate"}


class DeploymentError(Exception):
    """A violated rule, named together with the key it applies to."""

    def __init__(self, key: str, rule: str) -> None:
        super().__init__(f"{key}: {rule}")


@dataclass(frozen=True)
class Deployment:
    name: str
    base_url: str
    keep_alive_seconds: int
    certificate_text: bytes
    certificate: x509.Certificate


def canonical_base_url(text: str) -> tuple[str, str]:
    """Return the canonical base URL and its host, or raise DeploymentError."""
    key = "server.base_url"
    if not text.isascii() or any(character.isspace() for character in text):
        raise DeploymentError(key, "must be ASCII without spaces")
    parts = urlsplit(text)
    if parts.scheme.lower() != "https":
        raise DeploymentError(key, "scheme must be https")
    if "@" in parts.netloc:
        raise DeploymentError(key, "userinfo is not allowed")
    if "?" in text or "#" in text:
        raise DeploymentError(key, "query and fragment are not allowed")
    if "[" in parts.netloc:
        raise DeploymentError(key, "IPv6 literals are not allowed; the device uses IPv4 only")
    host = (parts.hostname or "").lower()
    try:
        port = parts.port
    except ValueError:
        raise DeploymentError(key, "port must be a number from 1 to 65535") from None
    if port == 0:
        raise DeploymentError(key, "port must be a number from 1 to 65535")
    if not is_ipv4_address(host) and not is_dns_name(host):
        raise DeploymentError(key, "host must be a DNS name or an IPv4 address")
    path = parts.path.rstrip("/")
    url = f"https://{host}:{port or DEFAULT_HTTPS_PORT}{path}"
    if len(url) > BASE_URL_MAX_LENGTH:
        raise DeploymentError(key, f"canonical URL is longer than {BASE_URL_MAX_LENGTH} bytes")
    return url, host


def is_ipv4_address(host: str) -> bool:
    try:
        ipaddress.IPv4Address(host)
    except ValueError:
        return False
    return True


def is_dns_name(host: str) -> bool:
    labels = host.split(".")
    return (
        0 < len(host) <= 253
        and all(DNS_LABEL.fullmatch(label) for label in labels)
        and not labels[-1].isdigit()
    )


def certificate_text(text: str) -> bytes:
    """Return the certificate with LF line endings and one final newline."""
    key = "server.certificate"
    normalized = text.replace("\r\n", "\n").strip() + "\n"
    for label in PEM_BEGIN.findall(normalized):
        if label != "CERTIFICATE":
            raise DeploymentError(key, f"PEM label {label!r} is not allowed; only public CERTIFICATE data")
    if not normalized.isascii() or PEM_CERTIFICATE.fullmatch(normalized) is None:
        raise DeploymentError(key, "must be exactly one PEM CERTIFICATE block")
    if len(normalized) > CERTIFICATE_MAX_LENGTH:
        raise DeploymentError(key, f"longer than {CERTIFICATE_MAX_LENGTH} bytes")
    return normalized.encode("ascii")


def check_certificate(pem: bytes, host: str, now: datetime) -> x509.Certificate:
    """Apply certificate rules 1 to 4 of the design."""
    key = "server.certificate"
    try:
        certificate = x509.load_pem_x509_certificate(pem)
    except ValueError:
        raise DeploymentError(key, "rule 1: not a parsable X.509 certificate") from None
    try:
        certificate.verify_directly_issued_by(certificate)
    except (ValueError, TypeError, InvalidSignature, UnsupportedAlgorithm):
        raise DeploymentError(
            key, "rule 2: must be self-issued and verify with its own public key"
        ) from None
    try:
        names = certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except x509.ExtensionNotFound:
        raise DeploymentError(key, "rule 3: no Subject Alternative Name extension") from None
    if is_ipv4_address(host):
        matches = ipaddress.IPv4Address(host) in names.get_values_for_type(x509.IPAddress)
        entry_type = "IP address"
    else:
        matches = any(
            "*" not in name and name.lower() == host
            for name in names.get_values_for_type(x509.DNSName)
        )
        entry_type = "DNS"
    if not matches:
        raise DeploymentError(
            key, f"rule 3: no {entry_type} Subject Alternative Name equals host {host!r}"
        )
    if not certificate.not_valid_before_utc <= now <= certificate.not_valid_after_utc:
        raise DeploymentError(
            key,
            "rule 4: not valid on this PC's date "
            f"(valid {certificate.not_valid_before_utc:%Y-%m-%d} to {certificate.not_valid_after_utc:%Y-%m-%d})",
        )
    return certificate


def load_deployment(path: Path, now: datetime) -> Deployment:
    if path.suffix != ".toml" or DEPLOYMENT_NAME.fullmatch(path.stem) is None:
        raise DeploymentError("file name", "must be <deployment>.toml with lowercase letters, digits and hyphens")
    try:
        with path.open("rb") as file:
            document = tomllib.load(file)
    except OSError as error:
        raise DeploymentError("file", f"cannot be read ({error.strerror})") from None
    except tomllib.TOMLDecodeError as error:
        raise DeploymentError("file", f"not valid TOML v1.0.0 ({error})") from None

    for key in sorted(document.keys() - TOP_LEVEL_KEYS):
        raise DeploymentError(key, "unknown key or table")
    file_format = document.get("format")
    if type(file_format) is not int or file_format != FILE_FORMAT:
        raise DeploymentError("format", f"required integer {FILE_FORMAT}")
    if "description" in document and not isinstance(document["description"], str):
        raise DeploymentError("description", "must be a string")
    server = document.get("server")
    if not isinstance(server, dict):
        raise DeploymentError("server", "required table")
    for key in sorted(server.keys() - SERVER_KEYS):
        raise DeploymentError(f"server.{key}", "unknown key or table")
    for key in sorted(SERVER_KEYS - server.keys()):
        raise DeploymentError(f"server.{key}", "required key is missing")

    if not isinstance(server["base_url"], str):
        raise DeploymentError("server.base_url", "must be a string")
    base_url, host = canonical_base_url(server["base_url"])
    keep_alive_seconds = server["keep_alive_seconds"]
    if (
        type(keep_alive_seconds) is not int
        or not KEEP_ALIVE_MINIMUM_SECONDS <= keep_alive_seconds <= KEEP_ALIVE_MAXIMUM_SECONDS
    ):
        raise DeploymentError(
            "server.keep_alive_seconds",
            f"must be an integer from {KEEP_ALIVE_MINIMUM_SECONDS} to {KEEP_ALIVE_MAXIMUM_SECONDS}",
        )
    if not isinstance(server["certificate"], str):
        raise DeploymentError("server.certificate", "must be a string")
    pem = certificate_text(server["certificate"])
    certificate = check_certificate(pem, host, now)
    return Deployment(path.stem, base_url, keep_alive_seconds, pem, certificate)


def build_image(deployment: Deployment) -> bytes:
    url = deployment.base_url.encode("ascii")
    body = (
        MAGIC
        + struct.pack("<BH", VERSION, len(url))
        + url
        + struct.pack("<IH", deployment.keep_alive_seconds, len(deployment.certificate_text))
        + deployment.certificate_text
    )
    return body + struct.pack("<I", zlib.crc32(body))


def provisioning_partition(build_directory: Path) -> tuple[int, int]:
    """Start and size of the provisioning partition from the build's final devicetree."""
    devicetree = build_directory / "zephyr" / "zephyr.dts"
    try:
        text = devicetree.read_text(encoding="utf-8")
    except OSError as error:
        raise DeploymentError("--build-dir", f"cannot read {devicetree} ({error.strerror})") from None
    match = PARTITION.search(text)
    if match is None:
        raise DeploymentError("--build-dir", f"no provisioning_partition node in {devicetree}")
    return int(match.group(1), 16), int(match.group(2), 16)


def check(path: Path) -> Deployment:
    deployment = load_deployment(path, datetime.now(timezone.utc))
    certificate = deployment.certificate
    names = certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    alternative_names = [f"DNS:{name}" for name in names.get_values_for_type(x509.DNSName)]
    alternative_names += [f"IP:{address}" for address in names.get_values_for_type(x509.IPAddress)]
    print(f"Deployment:                {deployment.name}")
    print(f"Base URL:                  {deployment.base_url}")
    print(f"Server keep-alive:         {deployment.keep_alive_seconds} s")
    print(f"Certificate subject:       {certificate.subject.rfc4514_string()}")
    print(f"Subject Alternative Names: {', '.join(alternative_names)}")
    print(f"Certificate expiry:        {certificate.not_valid_after_utc:%Y-%m-%d %H:%M:%S} UTC")
    print(f"Image size:                {len(build_image(deployment))} bytes")
    return deployment


def build(path: Path, build_directory: Path) -> tuple[Path, int]:
    deployment = check(path)
    image = build_image(deployment)
    start, size = provisioning_partition(build_directory)
    if len(image) > size:
        raise DeploymentError("--build-dir", f"image of {len(image)} bytes exceeds the partition of {size} bytes")
    output = build_directory / "provisioning" / f"{deployment.name}.bin"
    output.parent.mkdir(exist_ok=True)
    output.write_bytes(image)
    print(f"Image:                     {output}")
    print(f"Partition:                 start 0x{start:x}, size 0x{size:x}")
    return output, start


def flash(path: Path, build_directory: Path, port: str) -> int:
    """Build the image, then write only it at the partition start; esptool verifies the written data."""
    output, start = build(path, build_directory)
    command = [sys.executable, "-m", "esptool", "--chip", "esp32s3", "--port", port, "write-flash", f"0x{start:x}", str(output)]
    return subprocess.run(command, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    check_command = commands.add_parser("check", help="Validate a deployment file and its certificate.")
    check_command.add_argument("file", type=Path)
    build_command = commands.add_parser("build", help="Check, then write <build>/provisioning/<deployment>.bin.")
    build_command.add_argument("file", type=Path)
    build_command.add_argument("--build-dir", type=Path, required=True, help="Firmware build with the partition table.")
    flash_command = commands.add_parser("flash", help="Build, then write the image; used by flash-provisioning.ps1.")
    flash_command.add_argument("file", type=Path)
    flash_command.add_argument("--build-dir", type=Path, required=True)
    flash_command.add_argument("--port", required=True, help="Serial port, for example COM4.")
    arguments = parser.parse_args()

    try:
        if arguments.command == "check":
            check(arguments.file)
            result = 0
        elif arguments.command == "build":
            build(arguments.file, arguments.build_dir)
            result = 0
        else:
            result = flash(arguments.file, arguments.build_dir, arguments.port)
    except DeploymentError as error:
        print(f"error: {error}", file=sys.stderr)
        result = 1
    return result


if __name__ == "__main__":
    sys.exit(main())
