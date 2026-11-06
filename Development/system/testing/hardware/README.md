# Hardware regression run

[`device_regression.py`](device_regression.py) checks the app firmware on a connected board against a local HAPI FHIR test server. It is a developer regression aid for changes to Wi-Fi, SNTP, the server profile and TLS. It does not replace the owner-run target procedures such as [VT-14-WIFI](../WIFI/VT-14-target.md), and it records no test evidence.

Each scenario prepares the server profile partition and the FHIR container, resets the board through RTS and reads the serial console. A scenario fails on a missing required line, on a forbidden line, or on a crash or unexpected reset. The settings partition with the saved Wi-Fi network is never written.

| Scenario | Prepares | Passes when | Basis |
| --- | --- | --- | --- |
| `no-profile` | Erased server profile partition | "no server profile image", the stored network joins, and no SNTP or TLS attempt follows for 70 s | [Time synchronization](../../design/COMMUNICATION/time-synchronization.md#flow-and-scheduling), item 2: SNTP runs only inside a TLS connection setup |
| `foreign-certificate` | Profile that pins a different valid certificate for the server address | Verification fails with flags `0x8` (not trusted) and `SERVER_CONNECTION_FAILURE (-13)`, never "verified" | [Secure transport](../../design/COMMUNICATION/secure-transport.md): the device trusts only the provisioned certificate |
| `server-down-then-up` | Lab profile, server container stopped | `SERVER_CONNECTION_FAILURE` with the 60 s retry; once the server is started again, "Server connection verified" within 240 s | P26-ATTEMPT and P26-RETRY in [secure transport](../../design/COMMUNICATION/secure-transport.md#parameters) |
| `valid-profile` | Lab profile, server running | The stored network joins, the clock synchronizes, and the connection is verified within one retry | As above |

In `valid-profile`, a first attempt that fails and then recovers on the retry is printed as `WARN`: a rejected join, a TLS timeout, or an SNTP uncertainty above the P25 budget right after the join. A trust failure, a crash or no verification at all fails the scenario. The lab profile is flashed last, so the board ends in its normal configuration.

## Setup

1. **FHIR server.** Run the HAPI FHIR server of the [`lab-hapi`](../../coding/server-profiles/README.md) deployment in Docker on the test computer, with `SERVER_BASE_ADDRESS` set to `https://<server address>:8443/fhir`. Its address must be in the certificate's Subject Alternative Names. The runner starts and stops the container `fhir_tls`; `--server-container` names another one.
2. **Network.** The board and the server must be on the same network, and the test computer must accept inbound TCP 8443.
3. **Board.** Build the release firmware (`build-firmware.ps1`). The board needs a saved Wi-Fi network for that network. To save one, erase only the settings with `erase-flash.ps1 <port> -Settings`, then join the `Stetho-<MAC>` setup hotspot from a phone, open `http://192.168.4.1` and submit the network. Back up the settings partition first if the saved network should be restored later. Do not record passwords.
4. **Owner authorization.** The run flashes and resets the board. Run it only with the owner's authorization for that board.

## Use

From the repository root, with the pinned toolchain environment:

```powershell
.ci-workspace/.venv/Scripts/python.exe Development/system/testing/hardware/device_regression.py --port COM4 --server-address 192.168.2.40 --flash-firmware
.ci-workspace/.venv/Scripts/python.exe Development/system/testing/hardware/device_regression.py --port COM4 --scenario server-down-then-up
```

`--flash-firmware` writes the build in `build-app` first. Without `--scenario`, all four scenarios run in the order of the table, which takes about 10 minutes. The serial log and the deployment files of each run go to `artifacts/hardware-regression/<date-time>/`. The exit code is 0 only if every scenario passed.

Created by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
