"""Fixture tooling: regenerate the public test certificates in certificates/.

Not imported by the tests. Run it with the toolchain environment, which provides
the `cryptography` package, from the repository root:

    .ci-workspace/.venv/Scripts/python.exe Development/system/coding/app/tests/host/server_profile_tool/generate_certificates.py

Every run creates new keys, so the certificates change; their properties do not.
Private keys exist only in memory and are never written.
"""

from datetime import datetime, timezone
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

DIRECTORY = Path(__file__).resolve().parent / "certificates"
DNS_HOST = "fhir.example.test"
IP_HOST = "192.0.2.10"
VALID_FROM = datetime(2020, 1, 1, tzinfo=timezone.utc)
VALID_UNTIL = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
EXPIRED_FROM = datetime(2000, 1, 1, tzinfo=timezone.utc)
EXPIRED_UNTIL = datetime(2001, 1, 1, tzinfo=timezone.utc)
FUTURE_FROM = datetime(9000, 1, 1, tzinfo=timezone.utc)
MAXIMUM_PEM_LENGTH = 8192
PADDING_EXTENSION = x509.ObjectIdentifier(
    "2.25.329800735698586629295641978511506172918"
)


def name(common_name):
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])


def server_key_usage():
    return x509.KeyUsage(
        digital_signature=True,
        content_commitment=False,
        key_encipherment=False,
        data_encipherment=False,
        key_agreement=False,
        key_cert_sign=False,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False,
    )


def encipherment_only_key_usage():
    return x509.KeyUsage(
        digital_signature=False,
        content_commitment=False,
        key_encipherment=True,
        data_encipherment=False,
        key_agreement=True,
        key_cert_sign=False,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False,
    )


def certificate(
    alternative_names=(x509.DNSName(DNS_HOST),),
    *,
    subject=DNS_HOST,
    valid_from=VALID_FROM,
    valid_until=VALID_UNTIL,
    key_usage=server_key_usage(),
    extended_key_usage=(ExtendedKeyUsageOID.SERVER_AUTH,),
    issuer=None,
    signing_key=None,
    key=None,
    padding=0,
):
    key = key or ec.generate_private_key(ec.SECP256R1())
    builder = (
        x509.CertificateBuilder()
        .subject_name(name(subject))
        .issuer_name(name(issuer or subject))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_until)
    )
    if alternative_names:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(list(alternative_names)), critical=False
        )
    if key_usage is not None:
        builder = builder.add_extension(key_usage, critical=True)
    if extended_key_usage is not None:
        builder = builder.add_extension(
            x509.ExtendedKeyUsage(list(extended_key_usage)), critical=False
        )
    if padding:
        # DER OCTET STRING with a two-byte length, so the size grows in single bytes.
        value = b"\x04\x82" + padding.to_bytes(2, "big") + b"\x00" * padding
        builder = builder.add_extension(
            x509.UnrecognizedExtension(PADDING_EXTENSION, value), critical=False
        )
    return builder.sign(signing_key or key, hashes.SHA256())


def pem(value):
    return value.public_bytes(serialization.Encoding.PEM)


def maximum_length_certificate():
    """RSA signatures have a fixed length, so padding alone sets the PEM length."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    padding = 256
    while True:
        text = pem(certificate(key=key, padding=padding))
        if len(text) == MAXIMUM_PEM_LENGTH:
            return text
        if len(text) > MAXIMUM_PEM_LENGTH:
            raise SystemExit(f"no padding yields {MAXIMUM_PEM_LENGTH} PEM bytes")
        padding += 1


def main():
    authority_key = ec.generate_private_key(ec.SECP256R1())
    foreign_key = ec.generate_private_key(ec.SECP256R1())
    fixtures = {
        "dns-host": certificate(),
        "dns-host-mixed-case": certificate((x509.DNSName("FHIR.Example.TEST"),)),
        "ip-host": certificate(
            (x509.IPAddress(ipaddress.IPv4Address(IP_HOST)),), subject=IP_HOST
        ),
        "no-subject-alternative-name": certificate(()),
        "wrong-dns-name": certificate((x509.DNSName("other.example.test"),)),
        "wildcard-dns-name": certificate((x509.DNSName("*.example.test"),)),
        "dns-name-spelling-ip-host": certificate(
            (x509.DNSName(IP_HOST),), subject=IP_HOST
        ),
        "expired": certificate(valid_from=EXPIRED_FROM, valid_until=EXPIRED_UNTIL),
        "not-yet-valid": certificate(valid_from=FUTURE_FROM),
        "issued-by-authority": certificate(
            issuer="Example Test Authority", signing_key=authority_key
        ),
        "self-named-foreign-signature": certificate(signing_key=foreign_key),
        "key-usage-without-digital-signature": certificate(
            key_usage=encipherment_only_key_usage()
        ),
        "extended-key-usage-client-only": certificate(
            extended_key_usage=(ExtendedKeyUsageOID.CLIENT_AUTH,)
        ),
        "extended-key-usage-any": certificate(
            extended_key_usage=(ExtendedKeyUsageOID.ANY_EXTENDED_KEY_USAGE,)
        ),
        "no-usage-extensions": certificate(key_usage=None, extended_key_usage=None),
    }
    DIRECTORY.mkdir(exist_ok=True)
    for fixture, value in fixtures.items():
        (DIRECTORY / f"{fixture}.pem").write_bytes(pem(value))
    (DIRECTORY / "maximum-length.pem").write_bytes(maximum_length_certificate())


if __name__ == "__main__":
    main()
