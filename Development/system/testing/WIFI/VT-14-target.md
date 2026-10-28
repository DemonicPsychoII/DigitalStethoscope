# VT-14-WIFI — radio, persistence and retained station

**Test ID:** VT-14-WIFI (VT-14).
**Basis:** REQ-11/REQ-12/REQ-13 in [system requirements](../../requirements/system-requirements.md);
[setup and recovery](../../design/COMMUNICATION/interfaces-and-behavior.md#wi-fi-setup-and-recovery),
[safe teardown](../../design/COMMUNICATION/interfaces-and-behavior.md#listening-priority-and-safe-teardown)
and P19/P21/P23/P24 in [parameters](../../design/WIFI/parameters.md),
basis revision `13ac2d5a27854c67ed7fa819510559212ee2c143`.

## Device and software

Device, board revision, firmware/build full SHA (secure hash algorithm), test-source SHA,
radio/access-point setup, phone and audio setup identity: **________**

## Preconditions

- Owner-authorized target run; compatible ESP32-S3 board, external audio path and headphones.
- Controlled open and protected Wi-Fi networks; no patient data or production credentials.
- Firmware identity and the test procedure revision available. Controlled network loss,
  save-failure injection and radio-event instrumentation must be identified in the setup.
  If unavailable, mark the affected step Blocked; do not infer a pass from simulation.
- Preserve the original settings before controlled fault tests. Do not record passwords.
- Serial logging, timestamped evidence capture and a phone ready for the
  [portal procedure](../PORTAL/VT-14-target.md).

## Execution

1. Start without a saved record and capture the scan and AP trace.
   **Pass:** The initial scan completes before the open hotspot starts.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
2. Join that hotspot from the phone.
   **Pass:** DHCP supplies the phone with an address.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
3. After a stored join, hold the setup button for 2 s in Idle.
   **Pass:** Setup opens while the existing station association remains until a new join is submitted.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
4. Submit the controlled open network from the portal.
   **Pass:** The open network joins with an empty password.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
5. Submit the controlled WPA2-PSK network with a wrong password.
   **Pass:** One failed portal join shows its cause and starts a rescan.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
6. Repeat with the correct password and timestamp the address event, storage and page result.
   **Pass:** Credentials are saved after the station received its IPv4 address, and the page shows that address.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
7. Restart after a successful saved join.
   **Pass:** The same stored network joins without portal input.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
8. Retain an old record, join another network and inject failure into both atomic save attempts.
   **Pass:** Exactly two failed save attempts produce a warning without replacing the old record.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
9. Observe that save-warning result for 10 s.
   **Pass:** Setup closes after the warning display while the new station remains associated.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
10. Remove the save-failure injection and restart.
   **Pass:** The previously valid stored record is used.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
11. Remove the joined network in Idle and restore it during retry.
   **Pass:** Reconnect succeeds within four attempts with 5 s between failed attempts.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
12. Repeat with the network absent for all four reconnect attempts.
   **Pass:** Reconnect exhaustion opens setup automatically in Idle.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
13. Remove the network during listening, then repeat during measurement.
   **Pass:** Active recovery is deferred until Idle and the Wi-Fi-only failure preserves audio.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
14. Compare the same heart/tone input offline and while listening with a retained station; record source, duration, gain, traffic and audio counters.
   **Pass:** The retained association causes no added audible interruption in this observational comparison.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
15. Repeat the comparison during measurement with controlled background traffic.
   **Pass:** No active setup, reconnect or delivery job runs during the audio operation.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
16. With timestamped driver instrumentation, request Start during a scan and then a join.
   **Pass:** Confirmed cancellation and portal/DHCP/AP shutdown precede normal release to audio.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
17. Deliver a delayed old callback during cancellation and before a newer request can be armed.
   **Pass:** No old result publishes a list, completes another join or saves settings.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
18. Make the stop fail for scan cancel, disconnect, HTTP, DHCP and AP in separate instrumented runs.
   **Pass:** One failed cleanup stop latches WIFI_CLEANUP_FAILURE without further stop tries, prohibits Wi-Fi work until restart and releases audio under the Wi-Fi-only exception.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
19. Inspect the serial command list and invoke `settings` without supplying a credential.
   **Pass:** The settings shell is unavailable and cannot print the stored password; record the effective CONFIG_SETTINGS_SHELL=n setting.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
20. Inspect startup and failure logs using synthetic credentials.
   **Pass:** Logs contain no plaintext Wi-Fi password, keys, tokens or patient data; redact any exposure and record the failed step.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
21. Remove or corrupt the stored wifi/network record, then restart in separate controlled runs.
   **Pass:** An unreadable, deleted or invalid record is never submitted for a join and initial setup opens.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
22. Inject an HTTP server startup failure while AP and DHCP start successfully.
   **Pass:** HOTSPOT_START_FAILURE records the HTTP cause and cleanup returns offline until a new setup hold.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
23. Attempt to associate a second phone while one is already on the setup hotspot.
   **Pass:** At most one hotspot client is associated; HTTP connections from the associated phone remain separate.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**

## Completion

Overall result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run.
Sign-off (name, date, signature reference): **________**

Created by GPT-6.1-Sol on behalf of Nico running in codex.
