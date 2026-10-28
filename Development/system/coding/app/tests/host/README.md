# Wi-Fi and portal host verification

VT-14; REQ-11/REQ-12 with supporting REQ-13/REQ-14. Basis:
`07267b4ebef4cde952c296200bc428bc29d519c2` (`replay/11-project-records`).

## Run

From the repository root:

```powershell
$env:CC='<path-to>/zig.exe cc'
$env:STETHO_SANITIZERS='true'
python -m pytest -q -o junit_family=xunit1 --junitxml=artifacts/ci/application-host.xml Development/system/coding/app/tests/host
python Development/system/testing/ci/application_host_results.py artifacts/ci/application-host.xml
```

`CC` defaults to GCC; quote executable paths containing spaces inside `CC`.
C builds use `-Wall -Wextra -Werror`. `STETHO_SANITIZERS=true` requests
AddressSanitizer and UndefinedBehaviorSanitizer; effective support depends on the
compiler/platform and must be recorded with results. Node executes the production
page JavaScript with DOM, clock and fetch substitutes. Linux uses the pinned
Node 24.19.0 executable at `.ci-validation-tools/node`, installed by
`python Development/system/testing/ci/validation_tools.py` with an archive SHA-256
check and bounded extraction. Prepared images with older pins download the missing
tool. Neither PATH nor the Actions runner's bundled Node selects this runtime.
Missing or unusable runtimes fail CI with a diagnostic and never skip the check.
No browser dependencies are installed.

The pinned installer supports Linux x86-64. Outside CI, Windows explicitly skips
the page execution check unless `STETHO_NODE` names an absolute Node executable
path, for example `$env:STETHO_NODE='C:/Program Files/nodejs/node.exe'`.
This local override is ignored in CI. To obtain a complete local host report,
set that path before running pytest; the reporter rejects ordinary skipped cases.
Git records the tested source revision. The other L1 tests require only this
documented compiler and Git, with no additional host executables.

The `communication`, `wifi` and `portal` component suites share the existing
`Quality / Static Checks` host step. JUnit properties record VT-14, the design
anchor, expected result and compiler/source identity; each scenario has its own
result row. XFAIL records an implementation defect and a strict unexpected pass
fails verification. Classifications and the complete case list belong in the PR.

## Test basis

Expectations come from [Wi-Fi behavior](../../../../design/WIFI/interfaces-and-behavior.md),
[portal behavior](../../../../design/PORTAL/interfaces-and-behavior.md),
[P19/P21/P23/P24](../../../../design/WIFI/parameters.md),
[system behavior](../../../../design/system/interfaces-and-behavior.md),
[system parameters](../../../../design/system/parameters.md) and the public
WIFI, PORTAL, COMMUNICATION and STORAGE interfaces. Requirements and architecture
provide traceability; implementation is inspected only to connect the harness to
real functions, callbacks, resources and secret buffers.

## Harness boundaries

Production `communication.c` is a separate translation unit. Controlled kernel
waits advance a deterministic clock; events at the same timestamp arrive together.
Zero-time commands arrive before the worker starts. Each case gets a fresh process.
Service substitutes supply specified results and delays; storage failures preserve
the previous record and can return partially filled working data. A new join drops
the old station association. An unsolicited-link case exposes the link directly;
the substitute does not reject it for COMMUNICATION. Late-result rejection is
exercised through real L1 callbacks rather than a simulated generation identifier.

`communication_memory_harness.c` additionally includes COMMUNICATION with the
simulation so it can observe private working-record and consumed-password erasure
without changing firmware interfaces. Ordinary workflow cases retain the separate
translation-unit boundary.

The same white-box harness models a worker shutdown acknowledgement during a
CONTROL sleep. Release-wait cases cover the final polling interval, the deadline,
late acknowledgements and zero-time queries; they do not establish target scheduling.

`l1_harness.c` includes the unchanged production WIFI, PORTAL and STORAGE units so
it can inspect private form/queue erasure without adding firmware hooks. Small
Zephyr/ESP-IDF/HTTP/settings substitutes drive their actual handlers and wait APIs.
Driver events have no invented request identifier. Disconnect confirmation gates
rearm; cancelled scan results are injected before SCAN_DONE and the next scan.
The station substitute uses idle, connecting and connected states. Requested
disconnects report nonzero USER_REQUEST for a connected station and connect
failure before association, following the Zephyr Project's
[ESP32 Wi-Fi driver, revision 357467a011cd2557a1a3f0b4be83d817c4addc9b, lines 487–528](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/wifi/esp32/src/esp_wifi_drv.c#L487-L528)
(accessed 2026-10-24). Its retained-lease case follows the Zephyr Project's
[DHCPv4 client at the same revision, lines 1997–2023](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/subsys/net/lib/dhcpv4/dhcpv4.c#L1997-L2023)
(accessed 2026-10-24): stop removes an address in Bound/Renewing, but not Rebinding.
These sources define substitute fidelity; successful selected-network joins and
confirmed teardown remain design expectations. A failed-start case holds the
listener absent through the stop wait and checks that a later start is allowed;
the separate L2 startup-failure case checks HOTSPOT_START_FAILURE and a new manual hold.
The synthetic settings callback supplies a zero-length deleted record. Listener
readiness/closure and vendor AP configuration are observed through substitutes.
These checks cannot establish real driver ordering or physical socket closure.

The page test executes the served JavaScript, including hostile SSID rendering,
Activity throttling and poll scheduling. Its small DOM substitute observes markup,
not browser layout. JSON checks parse full 16-entry responses and verify names,
control-character handling and security flags. HTTP handler tests exercise decoding,
400/409/503 gating, fragment ownership and secret erasure with actual C code.

The release-wait timeout case uses COMMUNICATION's public API with a CONTROL caller
substitute. CONTROL has no implemented behavior in this basis, so actual audio
start prevention remains an integration gap. Physical button recognition, one
associated radio client, HTTP inactivity, flash atomicity, target scheduling,
malformed SSID display and the QR target need the [Wi-Fi](../../../../testing/WIFI/VT-14-target.md)
and [portal](../../../../testing/PORTAL/VT-14-target.md) procedures. The one-time P22
error-code identification check belongs to system acceptance.

The system design proposal for Busy admission during Delivery Pending belongs to
CONTROL and FHIR delivery. This VT-14 batch does not exercise
that boundary; CONTROL/FHIR implementation and executable acceptance cases
remain a coverage gap. Wi-Fi setup interruption by Start is a separate rule.

Created by GPT-6.1-Sol on behalf of Nico running in codex.

## Production integration and coverage

The [integration batch](integration/README.md) runs real L2 with real L1 services.
It is selected in the same host job and reported with the `integration` level in
JUnit. The existing deterministic L2 scenarios remain. No case is marked XFAIL at this head,
so no known defect is recorded as an expected failure; the address, Closing, cleanup
and stored-read record-erasure cases run as ordinary passing cases.

On a Linux host with matching GCC/gcov, set
`STETHO_COVERAGE_DIRECTORY=artifacts/ci/host-coverage` before running the complete
pytest batch, then run
`python Development/system/testing/ci/host_coverage.py artifacts/ci/host-coverage`.
Use a fresh coverage directory for each run. The report includes production C
line and branch coverage separately for unit, L2 and integration levels; harness,
substitute and header lines are excluded. CI runs coverage separately from sanitizers and
retains the report with the counters. An executed XFAIL still contributes counts
without becoming verified behavior. No numeric percentage is a pass threshold.
