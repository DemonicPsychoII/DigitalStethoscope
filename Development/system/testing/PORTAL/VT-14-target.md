# VT-14-PORTAL — phone page, navigation and closure

**Test ID:** VT-14-PORTAL (VT-14).
**Basis:** REQ-11/REQ-12 in [system requirements](../../requirements/system-requirements.md),
[page entry](../../design/PORTAL/interfaces-and-behavior.md#page-entry-and-network-selection),
[requests and published state](../../design/PORTAL/interfaces-and-behavior.md#requests-and-published-state),
[navigation and exit](../../design/PORTAL/interfaces-and-behavior.md#form-navigation-and-setup-exit)
and P21/P23/P24 in [Wi-Fi parameters](../../design/WIFI/parameters.md),
basis revision `13ac2d5a27854c67ed7fa819510559212ee2c143`.

## Device and software

Device, firmware/build full SHA (secure hash algorithm), test-source SHA, phone/operating system,
browser/version, network and QR (quick response) display setup: **________**

## Preconditions

- Owner-authorized target run; device in Idle, controlled open and protected networks in range.
- Phone camera and browser, device portal URL QR code and manual hotspot-join controls available.
  If no QR display or carrier is implemented, mark that step Blocked.
- Timestamped browser/network evidence and radio/settings logs; no patient or production secrets.
- Start from fresh setup for each independent navigation/timeout step. Use the
  [Wi-Fi procedure](../WIFI/VT-14-target.md) for radio/persistence evidence.

## Execution

1. Enter setup, manually join the open hotspot and scan the enclosure/setup-card QR.
   **Pass:** The QR opens exactly http://192.168.4.1/ on HTTP port 80 and the page renders on the phone.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
2. Leave and manually rejoin the hotspot, then reopen the page.
   **Pass:** The page remains usable and shows the completed network list.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
3. Select a controlled open network.
   **Pass:** The form hides the password field.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
4. Select a controlled WPA2-PSK network.
   **Pass:** The form requires valid credentials before the submitted network can join.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
5. Before Connect, use each available form Back/Cancel control in a fresh run.
   **Pass:** The page returns to selection without a Connect or setup Cancel request and setup stays open.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
6. Choose setup Cancel and capture status and service shutdown.
   **Pass:** Closing precedes teardown with the 2 s notice and no added 10 s result delay.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
7. Repeat setup Cancel with an established station.
   **Pass:** The station remains associated after setup closes.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
8. Start a join and attempt cancellation during connecting, saving and result display in separate runs.
   **Pass:** Cancellation is unavailable or ignored from Connect through automatic closure.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
9. Join a controlled network and capture the result.
   **Pass:** Its station IPv4 address is visible throughout the 10 s result display.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
10. Observe the end of success or save-warning display in separate runs.
   **Pass:** Closing precedes portal/DHCP/AP teardown while the established station remains.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
11. Join with a wrong password.
   **Pass:** The cause remains available while the AP stays open and the refreshed list permits another selection.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
12. Request Rescan and capture callbacks and page updates.
   **Pass:** Only the completed scan replaces the list, with page and hotspot still open.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
13. Exhaust four Rescan attempts with the page open.
   **Pass:** SCAN_FAILURE and Closing precede closure and a new Idle hold is needed to retry.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
14. Leave the page polling without user action.
   **Pass:** Setup closes after five minutes plus the notice and polling does not extend inactivity.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
15. Near expiry, select a network or type a password in separate runs.
   **Pass:** Selection or input restarts the full five-minute inactivity interval.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
16. Request Rescan near expiry, then repeat with a join crossing the old deadline.
   **Pass:** Each operation pauses inactivity until it finishes.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
17. Capture browser requests while repeatedly selecting and typing.
   **Pass:** Activity is sent at most once per second.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
18. Capture consecutive idle status polls.
   **Pass:** Status polling uses the one-second interval.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
19. Press Start during selection, scan, join, service startup and result display in separate runs.
   **Pass:** Normal audio release follows confirmed teardown with Closing and no added Start notice delay.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
20. Using controlled memory instrumentation, consume a queued Connect request.
   **Pass:** The consumed queue slot and caller password are wiped after use; mark Blocked if instrumentation is unavailable.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
21. Stop the server with unread Connect credentials and a partial form.
   **Pass:** Queue and form password buffers are erased; mark Blocked if instrumentation is unavailable.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
22. Use two HTTP connections from the associated phone; begin a fragmented form on the first and submit on the second.
   **Pass:** The second submission returns 409 and cannot alter ownership or mix form fragments.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
23. Submit malformed URL encoding and oversized or invalid credential data.
   **Pass:** Each malformed submission returns HTTP 400.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
24. After a failed join, submit Rescan while AP/server remain open; try Connect during the rescan and again after completed selection. Also submit requests outside selection in separate runs.
   **Pass:** Post-failure Rescan returns HTTP 202; Connect returns HTTP 409 until the completed list permits selection, then HTTP 202. Other requests outside selection return HTTP 409.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
25. Pause the consumer, fill the four-entry request queue and send another request.
   **Pass:** The next request returns HTTP 503 without changing published state.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
26. Leave an HTTP connection idle with socket instrumentation.
   **Pass:** The five-second HTTP client inactivity policy closes the idle connection.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
27. Publish controlled SSIDs with HTML tags, quotes, ampersands and control/malformed bytes; inspect list, form and status.
   **Pass:** Names render safely as text and JSON parses without script execution or broken navigation.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**
28. Inspect browser, server and serial logs and shared evidence using synthetic credentials.
   **Pass:** No plaintext credential or patient data appears; redact any exposure and record the failure.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: **—**

## Completion

Overall result: [ ] Pass / [ ] Fail / [ ] Blocked / [ ] Not run.
Sign-off (name, date, signature reference): **________**

Created by GPT-6.1-Sol on behalf of Nico running in codex.
