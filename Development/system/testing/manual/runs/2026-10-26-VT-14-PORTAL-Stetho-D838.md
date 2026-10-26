# VT-14-PORTAL — phone page, navigation and closure

**Test ID:** VT-14-PORTAL (VT-14).
**Basis:** REQ-11/REQ-12 in [system requirements](../../../requirements/system-requirements.md),
[page entry](../../../design/PORTAL/interfaces-and-behavior.md#page-entry-and-network-selection),
[requests and published state](../../../design/PORTAL/interfaces-and-behavior.md#requests-and-published-state),
[navigation and exit](../../../design/PORTAL/interfaces-and-behavior.md#form-navigation-and-setup-exit)
and P21/P23/P24 in [Wi-Fi parameters](../../../design/WIFI/parameters.md),
basis revision `13ac2d5a27854c67ed7fa819510559212ee2c143`.

## Device and software

See the execution record below.

Procedure copied from the [tested-revision procedure](https://github.com/DemonicPsychoII/DigitalStethoscope/blob/e58aa0fad9f3c45f3587ebe902b969c9f1289473/Development/system/testing/PORTAL/VT-14-target.md); this signed copy retains its step wording rather than adopting a different revision retrospectively.

## Execution record

- Execution date: 2026-10-26. Executor: Nico.
- Device: Stetho-D838, the project's single device; board revision not supplied.
- Firmware/software identity reported by Nico: `e58aa0fad9f3c45f3587ebe902b969c9f1289473`; additional build configuration not supplied.
- Test-source/procedure revision used for this retrospective mapping: `e58aa0fad9f3c45f3587ebe902b969c9f1289473`; the procedure was not reported as followed step by step during execution.
- Phone: iPhone 16; iOS and browser/version not supplied. Network security type and network equipment not supplied.
- Evidence: Nico's first-hand execution report in the task conversation on 2026-10-26; no logs, screenshots or timing traces supplied. Initial flash used the erase flag.
- Only fully supported observable criteria are marked Pass. Partial observations remain in the relevant notes; all other checks are skipped / Not run. Reported execution outcome: successful for the checked flow; no overall procedure pass is claimed.
- Signature entered as Nico at Nico's explicit request: “Update the manual tests for me, check what's checked, skip the rest, sign with my Name `Nico`”.

## Reported manual execution — successful

- [x] Flash with erase flag; device boots and opens a visible setup hotspot.
- [x] iPhone 16 connects and opens the setup page with discovered networks.
- [x] Select a network, go Back, then select again.
- [x] Connect shows an attempt and success; the setup page displays the device IPv4 address.
- [x] After the reported 10 seconds, setup closes, the page cannot be refreshed and the hotspot is no longer visible.
- [x] Reset detects saved settings and reconnects successfully without portal input.

These reported checks passed. The full procedures remain partially executed; unchecked criteria are not inferred from the successful flow.

## Preconditions

- Owner-authorized target run; device in Idle, controlled open and protected networks in range.
- Phone camera and browser, device portal URL QR code and manual hotspot-join controls available.
  If no QR display or carrier is implemented, mark that step Blocked.
- Timestamped browser/network evidence and radio/settings logs; no patient or production secrets.
- Start from fresh setup for each independent navigation/timeout step. Use the
  [Wi-Fi procedure](../../WIFI/VT-14-target.md) for radio/persistence evidence.

## Execution

1. Enter setup, manually join the open hotspot and scan the enclosure/setup-card QR. Pass: The QR opens exactly http://192.168.4.1/ on HTTP port 80 and the page renders on the phone.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Manual hotspot connection and setup-page rendering passed on iPhone 16. QR entry and exact URL/port were not reported.
2. Leave and manually rejoin the hotspot, then reopen the page. Pass: The page remains usable and shows the completed network list.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: The setup page showed discovered networks. Leaving and rejoining the hotspot was not reported.
3. Select a controlled open network. Pass: The form hides the password field.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
4. Select a controlled WPA2-PSK network. Pass: The form requires valid credentials before the submitted network can join.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
5. Before Connect, use each available form Back/Cancel control in a fresh run. Pass: The page returns to selection without a Connect or setup Cancel request and setup stays open.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Select, Back and select again succeeded before Connect. Every available Back/Cancel control and absence of Connect/setup Cancel requests were not checked.
6. Choose setup Cancel and capture status and service shutdown. Pass: Closing precedes teardown with the 2 s notice and no added 10 s result delay.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
7. Repeat setup Cancel with an established station. Pass: The station remains associated after setup closes.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
8. Start a join and attempt cancellation during connecting, saving and result display in separate runs. Pass: Cancellation is unavailable or ignored from Connect through automatic closure.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
9. Join a controlled network and capture the result. Pass: Its station IPv4 address is visible throughout the 10 s result display.
   Result: [x] Pass / [ ] Fail / [ ] Blocked / [ ] Not run. Notes/evidence: Nico reported a connection attempt followed by success, with device IPv4 displayed on the setup page during the reported 10-second result period. No timestamped capture was supplied.
10. Observe the end of success or save-warning display in separate runs. Pass: Closing precedes portal/DHCP/AP teardown while the established station remains.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: After the reported 10-second success period, setup closed, the phone browser could no longer refresh the page and the hotspot was no longer visible. Closing-before-teardown ordering, DHCP shutdown, retained station association and the save-warning variant were not checked.
11. Join with a wrong password. Pass: The cause remains available while the AP stays open and the refreshed list permits another selection.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
12. Request Rescan and capture callbacks and page updates. Pass: Only the completed scan replaces the list, with page and hotspot still open.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
13. Exhaust four Rescan attempts with the page open. Pass: SCAN_FAILURE and Closing precede closure and a new Idle hold is needed to retry.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
14. Leave the page polling without user action. Pass: Setup closes after five minutes plus the notice and polling does not extend inactivity.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
15. Near expiry, select a network or type a password in separate runs. Pass: Selection or input restarts the full five-minute inactivity interval.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
16. Request Rescan near expiry, then repeat with a join crossing the old deadline. Pass: Each operation pauses inactivity until it finishes.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
17. Capture browser requests while repeatedly selecting and typing. Pass: Activity is sent at most once per second.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
18. Capture consecutive idle status polls. Pass: Status polling uses the one-second interval.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
19. Press Start during selection, scan, join, service startup and result display in separate runs. Pass: Normal audio release follows confirmed teardown with Closing and no added Start notice delay.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
20. Using controlled memory instrumentation, consume a queued Connect request. Pass: The consumed queue slot and caller password are wiped after use; mark Blocked if instrumentation is unavailable.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
21. Stop the server with unread Connect credentials and a partial form. Pass: Queue and form password buffers are erased; mark Blocked if instrumentation is unavailable.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
22. Use two HTTP connections from the associated phone; begin a fragmented form on the first and submit on the second. Pass: The second submission returns 409 and cannot alter ownership or mix form fragments.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
23. Submit malformed URL encoding and oversized or invalid credential data. Pass: Each malformed submission returns HTTP 400.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
24. After a failed join, submit Rescan while AP/server remain open; try Connect during the rescan and again after completed selection. Also submit requests outside selection in separate runs. Pass: Post-failure Rescan returns HTTP 202; Connect returns HTTP 409 until the completed list permits selection, then HTTP 202. Other requests outside selection return HTTP 409.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
25. Pause the consumer, fill the four-entry request queue and send another request. Pass: The next request returns HTTP 503 without changing published state.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
26. Leave an HTTP connection idle with socket instrumentation. Pass: The five-second HTTP client inactivity policy closes the idle connection.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
27. Publish controlled SSIDs with HTML tags, quotes, ampersands and control/malformed bytes; inspect list, form and status. Pass: Names render safely as text and JSON parses without script execution or broken navigation.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.
28. Inspect browser, server and serial logs and shared evidence using synthetic credentials. Pass: No plaintext credential or patient data appears; redact any exposure and record the failure.
   Result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Notes/evidence: Skipped at Nico's request; execution not reported.

## Completion

Overall result: [ ] Pass / [ ] Fail / [ ] Blocked / [x] Not run. Partial execution; remaining steps skipped.
Date: **2026-10-26**

Name (signature): **Nico**

Recorded by GPT-6.1-Sol on behalf of Nico running in codex.
