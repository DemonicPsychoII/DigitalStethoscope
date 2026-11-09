# Hardware regression run

[`device_regression.py`](device_regression.py) checks the app firmware on a connected board against a local HAPI FHIR test server. It is a developer regression aid for changes to Wi-Fi, SNTP, the server profile and TLS. It does not replace the owner-run target procedures such as [VT-14-WIFI](../WIFI/VT-14-target.md), and it records no test evidence.

Each scenario prepares the server profile partition and the FHIR container, resets the board through RTS and reads the serial console. A scenario fails on a missing required line, on a forbidden line, on a crash, or on any boot after the one its own reset started. The settings partition with the saved Wi-Fi network is never written.

The scenarios that connect also check P26 on the device's log timestamps. A failed attempt must end within 10 s of its SNTP result, and the next attempt's SNTP result must follow 60 s to 70 s after that failure, with 0.5 s tolerance for logging. If that SNTP exchange fails, its failure is logged only after the cancellation, so its P23 stop bound of 1 s is added. The log has no line for the start of an attempt, so both bounds are measured from the SNTP result, the earliest evidence of the attempt. This is partial coverage: it does not prove that a whole attempt, SNTP included, stays within 10 s, nor that the next attempt starts no earlier than 60 s after the failure. P25's uncertainty budget is not checked numerically.

| Scenario | Prepares | Passes when | Basis |
| --- | --- | --- | --- |
| `no-profile` | Erased server profile partition | "no server profile image", the stored network joins, and no SNTP result or server connection outcome follows for 70 s after the join. The log has no line for the start of an exchange; any attempt would log an outcome within its 10 s budget and 1 s cleanup | [Time synchronization](../../design/COMMUNICATION/time-synchronization.md#flow-and-scheduling), item 2: SNTP runs only inside a TLS connection setup |
| `foreign-certificate` | Profile that pins a different valid certificate for the server address | The first attempt and the retry 60 s later both fail verification with flags `0x8` (not trusted), with `SERVER_CONNECTION_FAILURE (-13)`; never "verified" | [Secure transport](../../design/COMMUNICATION/secure-transport.md): the device trusts only the provisioned certificate |
| `server-down-then-up` | Lab profile, server container stopped | `SERVER_CONNECTION_FAILURE`, then retries 60 s after each failure; once the server is started again, "Server connection verified", all within 240 s of the board reset | P26-ATTEMPT and P26-RETRY in [secure transport](../../design/COMMUNICATION/secure-transport.md#parameters) |
| `valid-profile` | Lab profile, server running | The stored network joins, the clock synchronizes, and the connection is verified with at most one failed attempt before it | As above |

In `valid-profile`, a first attempt that fails and then recovers on the retry is printed as `WARN`: a rejected join, a TLS timeout, or an SNTP uncertainty above the P25 budget right after the join. A second failed attempt, a trust failure or a crash fails the scenario. After the run, also after an error, the runner starts the server and flashes the lab profile unless the last completed scenario left it on the board; a failed cleanup step fails the run. Docker commands time out after 60 s, and the wait for the server's metadata after `docker start` after 180 s.

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

`--flash-firmware` writes the build in `build-app` first. Without `--scenario`, all four scenarios run in the order of the table, which takes about 10 minutes. The serial log and the deployment files of each run go to `artifacts/hardware-regression/<date-time>/`; a repeated scenario keeps each log, as `<scenario>-2.log` and so on. The exit code is 0 only if every scenario run passed, including each repetition of a repeated `--scenario`, and the cleanup succeeded.

Created by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
