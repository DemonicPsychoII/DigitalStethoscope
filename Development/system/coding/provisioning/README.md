# Server deployments

Each file `<deployment>.toml` describes one server deployment: the HTTPS FHIR base URL, the server keep-alive and the public server certificate. It is the only input of the device's provisioning image ([provisioning design](../../design/STORAGE/provisioning.md)). A server change is a reviewed change of its file.

This repository is public, so it holds test deployments only: no production endpoint, no private key, keystore, password or other credential. A real deployment keeps its file with that deployment and uses the same tool.

| Deployment | Server | Owner |
| --- | --- | --- |
| [`lab-hapi`](lab-hapi.toml) | Local HAPI FHIR test server on `nglegion`, home network 192.168.2.0/24, `https://192.168.2.40:8443/fhir`. Server configuration and certificate source: `ntmedlinkkis` repository, commit `4dd534b` (`certs/cert.conf`, `docker-compose.yml`). | Nico |

## Use

From the repository root, with the pinned toolchain environment:

```powershell
.ci-workspace/.venv/Scripts/python.exe Development/system/coding/tools/provisioning/provisioning.py check Development/system/coding/provisioning/lab-hapi.toml
Development/system/coding/tools/flash-provisioning.ps1 <COM port number> Development/system/coding/provisioning/lab-hapi.toml
```

`check` validates the file and the certificate. The flash command builds the image against the firmware build's partition table and writes only the provisioning partition; the firmware and the saved Wi-Fi network stay unchanged.

A lab deployment names its server by the IPv4 address of the day. If the address changes, reissue the server certificate with the new address in its Subject Alternative Names, update the file and flash the image again.

Created by Claude-Opus-5.5 on behalf of Nico running in claude code.
