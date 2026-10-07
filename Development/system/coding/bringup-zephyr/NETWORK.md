# Optional Wi-Fi and FHIR setup

No server, test Patient, credentials or CA has been chosen. There is no default
connection and no automatic send. Configuration and tokens live only in RAM;
shell command history is disabled. Credentials entered on the console can still
appear in terminal captures, so enter them outside evaluation logging.

When the test server is chosen, add a local, untracked configuration file:

```text
CONFIG_STETHO_CA_FILE="/absolute/path/to/public-root-ca.pem"
```

Build with `-DEXTRA_CONF_FILE="network.conf;/absolute/path/to/local-network.conf"`.
Only the **public root certificate** is embedded. The network profile accepts
TLS 1.2 ECDHE-RSA/ECDHE-ECDSA AES-128-GCM certificates/ciphersuites. Hostname,
certificate chain and dates are verified; no insecure fallback exists.

Connect explicitly using Zephyr's `wifi connect` command (see `wifi connect -h`
for SSID/security/key options). Then configure and synchronize the clock:

```text
stetho net configure fhir.example.test 443 /fhir test-patient
stetho net sync your-time-server.example.test
stetho net send
```

Alternatively `stetho net time UNIX_SECONDS` sets the current UTC time locally.
SNTP is unauthenticated, so use a trusted lab time source. Optional bearer token:
`stetho net token TOKEN`. Reset clears all runtime configuration.

Sending requires a running microphone source, heart mode, a valid recent BPM
result, current clock and configured CA/server/Patient. It freezes that result
and its measurement time into a FHIR R4 heart-rate Observation (LOINC 8867-4,
UCUM `/min`, vital-signs category). A low-priority worker issues a TLS PUT to a
boot/measurement-specific resource ID. Explicitly retrying the same measurement
uses the same ID; there is no automatic retransmission or retry storm. Server
must support client-assigned Observation IDs. HTTP 200/201 is transport acceptance;
use the host readback tool to prove stored content. Network loss or TLS failure
is reported without stopping audio. See the [evaluation protocol](EVAL-GUIDE.md#fhir-test-setup-and-readback) for negative tests.

Device-network operations require owner authorization. These instructions describe
the current evaluation firmware; the proposed thesis delivery contract is in
[detailed design](../../design/interfaces-and-behavior.md#delivery-clock-and-configuration).

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
