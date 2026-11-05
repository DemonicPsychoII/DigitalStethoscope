# Server profiles

Each deployment file `<deployment>.toml` describes one server deployment: the HTTPS FHIR base URL, the server keep-alive and the public server certificate. It is the only input of the device's server profile image ([server profile design](../../design/STORAGE/server-profile.md)). A server change is a reviewed change of its file.

This repository is public, so it holds test deployments only: no production endpoint, no private key, keystore, password or other credential. A real deployment keeps its file with that deployment and uses the same tool.

| Deployment | Server | Owner |
| --- | --- | --- |
| [`lab-hapi`](lab-hapi.toml) | Local HAPI FHIR test server on `nglegion`, home network 192.168.2.0/24, `https://192.168.2.40:8443/fhir`, or iPhone hotspot 172.20.10.0/28. Server configuration and certificate source: `ntmedlinkkis` repository (`certs/cert.conf`, `docker-compose.yml`). | Nico |

## Use

From the repository root, with the pinned toolchain environment:

```powershell
.ci-workspace/.venv/Scripts/python.exe Development/system/coding/tools/server-profile/server_profile.py check Development/system/coding/server-profiles/lab-hapi.toml
Development/system/coding/tools/flash-server-profile.ps1 <COM port number> Development/system/coding/server-profiles/lab-hapi.toml
```

`check` validates the file and the certificate. The flash command builds the image against the firmware build's partition table and writes only the server profile partition; the firmware and the saved Wi-Fi network stay unchanged.

A lab deployment names its server by the IPv4 address of the day. The `lab-hapi` certificate covers the home address and every iPhone hotspot client address, 172.20.10.2 to 172.20.10.14, so on these networks only `base_url` changes before the image is flashed again. On any other address, reissue the server certificate with that address in its Subject Alternative Names and update the file.

Created by Claude-Opus-5.5 on behalf of Nico running in claude code.
