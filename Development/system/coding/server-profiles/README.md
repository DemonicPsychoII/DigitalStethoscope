# Server profiles

Each deployment file `<deployment>.toml` describes one server deployment: the HTTPS FHIR base URL, the server keep-alive and the public server certificate. It is the only input to the device's server profile image ([server profile design](../../design/STORAGE/server-profile.md)).

The deployment files are test deployments: they contain no production endpoint and no private key, keystore, password or other credential. A real deployment keeps its file with that deployment and uses the same tool.

| Deployment | Server |
| --- | --- |
| [`lab-hapi`](lab-hapi.toml) | Local HAPI FHIR test server. |

## Use

Run the commands from the repository root after [`setup-toolchain.ps1`](../tools/setup-toolchain.ps1) has provisioned the pinned toolchain. The first line resolves the pinned workspace:

```powershell
$workspace = (python Development/system/coding/tools/toolchain/toolchain_environment.py --format locations | ConvertFrom-Json).workspace
& "$workspace\.venv\Scripts\python.exe" Development/system/coding/tools/server-profile/server_profile.py check Development/system/coding/server-profiles/lab-hapi.toml
Development/system/coding/tools/flash-server-profile.ps1 <COM port number> Development/system/coding/server-profiles/lab-hapi.toml
```

`check` validates the file and the certificate. The flash command builds the image against the firmware build's partition table and writes only the server profile partition; the firmware and the saved Wi-Fi network stay unchanged.

A lab deployment identifies its server by IPv4 address. The `lab-hapi` certificate includes Subject Alternative Names for the lab addresses, so switching between those addresses only requires updating `base_url` and reflashing the server profile image. For any other address, reissue the server certificate with that address in its Subject Alternative Names and update the deployment file.
