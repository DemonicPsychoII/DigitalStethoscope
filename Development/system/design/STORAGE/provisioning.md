# Provisioning from a deployment file

## Basis

This Design-stage contract refines the [provisioning architecture](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/108) at `29f0e8f4b73e2491430c9f633d62e39026f2863e` and the [flash layout and image format](interfaces-and-behavior.md#flash-layout) at `fb2c979760f562bcb371a1c13cbb2ded7b3f0821`, which applies the design review of 2 November 2026 and the flash layout decision of 4 November 2026 [8]. It covers REQ-09, REQ-11 and REQ-13; verification uses VT-08, VT-09 and VT-11. No firmware, tool or generated tests change here.

Nico decided on 4 November 2026 that one TOML file per server deployment, with the certificate embedded as PEM text and versioned in the repository, is the only input, and that one flash command validates, builds and writes the image [1]. The image format of the design review stays unchanged; the deployment file is a host-side input only.

## Deployment file

Each server deployment has one file `Development/system/coding/provisioning/<deployment>.toml`. The name uses lowercase letters, digits and hyphens, for example `lab-hapi.toml`, and is the image name. The folder's README lists every deployment with its server and owner. A server change is a reviewed change of this file; no other input exists. The repository is public, so only test deployments are committed: no production endpoint and no credentials. A real deployment keeps its file with that deployment and uses the same tool.

The file follows TOML v1.0.0 [2]. The tool reads it with Python's standard `tomllib` module [3] in the pinned toolchain environment, so no extra dependency is needed for parsing. Format 1:

| Key | TOML type | Required | Rule |
| --- | --- | --- | --- |
| `format` | integer | yes | `1`. Any other value is rejected, so a newer file never reaches an older tool. |
| `description` | string | no | For people: server, network and purpose. Not written to the image. |
| `server.base_url` | string | yes | HTTPS FHIR base URL; canonical form below. |
| `server.keep_alive_seconds` | integer | yes | The server's idle connection timeout, 6 to 4,294,967,295 seconds; the device closes its connection 5 seconds earlier. |
| `server.certificate` | string | yes | Exactly one PEM `CERTIFICATE` block [4], normally written as a multi-line basic string [2]. At most 8,192 bytes after line endings are normalized to LF. |

Unknown keys or tables are errors, so a misspelt key never silently drops a value. The file holds public information only: a `PRIVATE KEY` label or any other PEM label than `CERTIFICATE` is rejected.

```toml
format = 1
description = "Local HAPI test server on nglegion, home network 192.168.2.0/24"

[server]
base_url = "https://192.168.2.40:8443/fhir"
keep_alive_seconds = 600
certificate = """
-----BEGIN CERTIFICATE-----
MIID...
-----END CERTIFICATE-----
"""
```

A lab deployment names the server host by its IPv4 address on the network of the day. Before each test the address is read again; if it changed, the server certificate is reissued with that address in its Subject Alternative Names, the file is updated and the image is flashed again. A host name avoids this only where the network's DNS resolves it, which the phone hotspot does not.

### Canonical base URL

The tool writes the canonical form into the image; registration binds to the same string. Scheme and host are lowercased [5]. The scheme must be `https`. A missing port becomes `:443`, because the server binding requires an explicit port (project rule of the design review). A trailing slash is removed; the remaining path is kept. Userinfo, query and fragment are rejected. The host is a DNS name or an IPv4 literal; IPv6 literals are rejected because the station resolves and connects over IPv4 only. The canonical URL has at most 256 bytes.

### Certificate checks

Before anything is written, the tool applies the device's certificate rules, so a mismatch fails on the developer PC. The device applies rules 1 and 3 at boot, enforces rules 2 and 5 through its handshake verification and applies rule 4 against its synchronized clock before each handshake, because boot has no valid clock yet:

1. The text is exactly one parsable X.509 certificate.
2. It is self-issued and its signature verifies with its own public key, because the device trusts it directly.
3. It has a Subject Alternative Name extension whose entry type follows the host: a DNS name host needs an equal DNS entry (case-insensitive, no wildcard); an IPv4 host needs an equal IP address entry, and a DNS entry spelling the address does not count. Common Name is never used [6].
4. It is valid on the developer PC's current date. The tool prints the expiry date.
5. Its key may sign TLS 1.3 server authentication: a Key Usage extension, if present, includes `digitalSignature` [9]; an Extended Key Usage extension, if present, includes `serverAuth` or `anyExtendedKeyUsage`. The device's TLS library rejects the handshake otherwise [10].

The checks use the `cryptography` package already present in the toolchain environment as an esptool dependency (own observation, 4 November 2026: version 50.0.2 in `.ci-workspace/.venv`). A pinned-dependency change of the toolchain must keep it available.

## Image built from the file

The image keeps format version 1 of the [flash layout](interfaces-and-behavior.md#flash-layout). Field sources:

| Image field | From the deployment file |
| --- | --- |
| Magic `STPV`, version `1` | Fixed by the tool. |
| Base URL length and base URL | Canonical `server.base_url`, ASCII. |
| Server keep-alive | `server.keep_alive_seconds`. |
| Certificate length and certificate | `server.certificate` with LF line endings and one final newline. |
| CRC-32 | Computed by the tool over all preceding bytes. |

The tool rejects an image larger than the provisioning area. It takes the area's start and size from the `provisioning_partition` node of the firmware build's final devicetree (`<build>/zephyr/zephyr.dts`), so no offset is written twice. A build without that node is rejected.

## Commands

| Command | Result |
| --- | --- |
| `provisioning.py check <file>` | Validates file and certificate; prints canonical URL, keep-alive, certificate subject, Subject Alternative Names, expiry and image size. Exit 0 or 1. |
| `provisioning.py build <file> --build-dir <build>` | Runs `check`, then writes `<build>/provisioning/<deployment>.bin`. |
| `flash-provisioning.ps1 <COM port> <file> [-BuildDir <build>]` | Runs `build`, then writes only that image at the partition offset with the pinned esptool [7], which verifies the written data. The firmware image and the settings partition stay unchanged. |

The tool lives in `Development/system/coding/tools/provisioning/`. Every rejection names the key and the violated rule, exits with status 1 and writes nothing to the device.

## Device behavior

Boot reads and validates the image once, as the [flash layout](interfaces-and-behavior.md#flash-layout) defines; WIFI then applies certificate rules 1 and 3. Every boot failure leaves secure transport unavailable with a configuration cause and keeps Wi-Fi setup and offline listening working. Validity is checked later, after the setup's time synchronization and before each handshake, as the [TLS design](../COMMUNICATION/secure-transport.md) defines:

| Image state | Boot result |
| --- | --- |
| Erased partition | Missing image; no secure connection attempt. |
| Unknown magic or version, bad length, CRC mismatch | Invalid image. |
| Unusable URL, unparsable certificate, no matching Subject Alternative Name | Invalid configuration; the log names the rule. |
| Valid image | Server provisioned; preparation follows the [TLS design](../COMMUNICATION/secure-transport.md). |

## Parameters

| ID | Value / meaning |
| --- | --- |
| P28-FILE | TOML v1.0.0 deployment file, format 1, at `Development/system/coding/provisioning/<deployment>.toml` |
| P28-LIMITS | Canonical base URL at most 256 bytes; certificate at most 8,192 bytes; keep-alive 6 to 4,294,967,295 seconds |
| P28-IMAGE | Image format version 1 of the flash layout; IEEE CRC-32 |
| P28-PARTITION | Provisioning area with the fixed start `0xF00000` and 192 KiB, independent of the settings size (project decision [8]); the image occupies at most 8,465 bytes from that start; the tool takes start and size from the `provisioning_partition` node of the build devicetree |

## Verification allocation

These scenarios allocate future verification; they do not add a generated test batch or claim execution.

| Scenario | Trace | Expected result |
| --- | --- | --- |
| Valid deployment file | REQ-09/REQ-11; VT-08 | `check` passes; the image bytes match the field table and the firmware reader accepts them. |
| Each violated file rule | REQ-11; VT-08 | Rejected with key and rule; no image written. |
| Certificate not self-issued, without matching Subject Alternative Name, or with a DNS entry for an IPv4 host | REQ-11; VT-08 | Rejected by the tool; an image forced onto a device yields an invalid configuration at boot (missing or wrong-type SAN) or a failed verification at the handshake (not self-issued). |
| Certificate whose Key Usage lacks `digitalSignature` or whose Extended Key Usage lacks `serverAuth` and `anyExtendedKeyUsage` | REQ-11; VT-08 | Rejected by the tool; an image forced onto a device is accepted at boot and fails verification at the handshake. |
| Certificate expired or not yet valid | REQ-11; VT-08 | Rejected by the tool on the PC's date; on the device a valid image is accepted at boot and the setup fails its validity check after time synchronization, without a handshake. |
| Private key or other PEM label in the file | VT-11 | Rejected; nothing written. |
| Image larger than the provisioning area, or build without the partition node | REQ-11; VT-08 | Rejected before writing. |
| Flash command on a device | REQ-11/REQ-12; VT-08 | Only the provisioning range changes; saved network and firmware remain. |
| Missing or corrupted image at boot | REQ-11/REQ-13; VT-08/VT-09 | Secure transport unavailable with a configuration cause; Wi-Fi and offline listening unaffected. |

## Sources

[1] Nico, *Provisioning deployment-file decisions*, personal communication, T3 Code, 4 November 2026, [conversation](t3-thread://v2/d5e44f69-2ecc-4a3e-917b-31a7b084c12b/b0a0170f-70da-43f5-89a6-38c67da80e40), accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#nico_provisioning_decisions_20261104). Project decisions, not measurements.

[2] Tom Preston-Werner, Pradyun Gedam et al., *TOML v1.0.0*, specification, 11 January 2021, <https://toml.io/en/v1.0.0>, accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#toml_v1_2021).

[3] Python Software Foundation, *tomllib — Parse TOML files*, Python 3.14 documentation, module added in version 3.11, <https://docs.python.org/3/library/tomllib.html>, accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#python_tomllib_314).

[4] Simon Josefsson and Sean Leonard, *Textual Encodings of PKIX, PKCS, and CMS Structures*, IETF RFC 7468, April 2015, sections 2 and 5, DOI [10.17487/RFC7468](https://doi.org/10.17487/RFC7468), accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#ietf_pem_7468_2015).

[5] Tim Berners-Lee, Roy T. Fielding and Larry Masinter, *Uniform Resource Identifier (URI): Generic Syntax*, IETF RFC 3986, STD 66, January 2005, section 6.2.2.1, DOI [10.17487/RFC3986](https://doi.org/10.17487/RFC3986), accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#ietf_uri_3986_2005).

[6] Peter Saint-Andre and Rich Salz, *Service Identity in TLS*, IETF RFC 9525, November 2023, sections 4 and 6, DOI [10.17487/RFC9525](https://doi.org/10.17487/RFC9525), accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#ietf_service_identity_9525_2023).

[7] Espressif Systems, *esptool: Basic Commands (ESP32-S3)*, esptool documentation, latest; online revision and publication year not stated, <https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/basic-commands.html>, accessed 4 November 2026. [Source register](../../../../thesis-material/quellen.md#espressif_esptool_basic_commands).

[8] Nico, *Flash layout decision*, personal communication, T3 Code, 4 November 2026. [Source register](../../../../thesis-material/quellen.md#nico_flash_layout_decision_20261104). Project decision, not a measurement.

[9] Eric Rescorla, *The Transport Layer Security (TLS) Protocol Version 1.3*, IETF RFC 8446, August 2018, section 4.4.2.2, DOI [10.17487/RFC8446](https://doi.org/10.17487/RFC8446), accessed 5 November 2026. [Source register](../../../../thesis-material/quellen.md#ietf_tls13_8446_2018).

[10] Mbed TLS contributors, *`mbedtls_ssl_check_cert_usage` in `library/ssl_tls.c`*, Zephyr Mbed TLS module, revision `098e120afb51877ed814bdc04443890ae12e0642`; publication year unverified, [source](https://github.com/zephyrproject-rtos/mbedtls/blob/098e120afb51877ed814bdc04443890ae12e0642/library/ssl_tls.c#L8639), accessed 5 November 2026. [Source register](../../../../thesis-material/quellen.md#mbedtls_cert_usage_098e120).
