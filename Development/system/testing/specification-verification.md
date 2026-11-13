# Application verification cases

This AI-generated system verification catalogue derives cases from the agreed requirements and design. It belongs to the Tests stage; developer case-list review and device sign-off remain separate. It links the system acceptance checks to the component checks needed during development. The [development process](../process/README.md) defines test generation and review; [verification operations](ci/OPERATIONS.md) defines execution and infrastructure.

## Current state and target

The catalogue defines the target cases. The [Wi-Fi/portal L2 batch](../coding/app/tests/host/README.md) covers the communication design with production L2 and controlled L1 services. The [host integration batch](../coding/app/tests/host/integration/README.md) also connects real L2 and L1 services at the Zephyr API boundary. At this head one strict expected failure records a known
implementation defect: a DNS answer without an IPv4 record ends a delivery terminally instead of being retried ([GitHub #131](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/131) / [TICKET-220](https://nfrie.atlassian.net/browse/TICKET-220)). Other cases still need a test or procedure reference, as listed below. Recorded results apply to their identified source and configuration. Full device acceptance remains pending.

## System acceptance

[REQ-01–REQ-15](../requirements/system-requirements.md) define the finished-device tests and pass criteria. Each requirement is exercised on the identified device and firmware build, with an outcome and evidence. Component evidence supports these complete system runs.

The [draft P22 procedure](system/P22-final-legibility.md) is deferred pending resolution of the conflict between P22 and the 19 October owner decision not to plan MVP visibility checks. It does not add a required MVP acceptance step. If adopted later, it uses the [executed-run format](manual/README.md). It records three separate observations: every pattern is visible at 1 m; the error state is visible at 4 m; and the specific catalogue error code and its priority are identifiable at 1 m. Record the operator, device and firmware, injected code/pattern, distance, ambient illuminance, viewing angle, each observation and its own outcome at 100–1500 lx inside a 30° viewing cone. Identification at 1 m is not evidence of visibility at 4 m. This is outside automated MVP verification; applicability and primary IEC clauses remain unverified working assumptions.

## Component and integration cases

The VT cases below define the required component and integration checks. The identified design and implementation are checked against these cases. Their identifiers remain stable
as procedures and tests are added in the generated test stage.

| ID | Check | Level / method | Exercise and evidence |
|---|---|---|---|
| VT-01 | Startup | Host fault injection + target | Power-on with missing microphone/DAC; silent initialization and a restart-required muted Error per current catalogue. Physical tests only with owner authorization. |
| VT-02 | Audio timing and resources | Target instrumented load/soak | Critical CPU time and block waits per audio block, queue/memory watermarks, drift. Latency is judged by ear (REQ-05); no two-channel measurement setup is available. |
| VT-03 | Listening DSP | Host production core + target listening | Raw identity before gain, impulse/sweep response, extremes and saturation, transition artifacts. |
| VT-04 | Control and input | Host model/adapter injection + target | Every allowed/rejected transition; bounce, queue saturation, Busy, LED patterns and snapshot consistency. |
| VT-06 | BPM sessions | Host recordings/reference + target | Supported range, S1/S2 and harmonics, silence/noise/clipping/gaps, aggregation, cancel/finalize races. Recordings, reference and resampling decided during the Wi-Fi/FHIR phase. |
| VT-07 | FHIR delivery | Host serializer / mock server + authorized local HAPI | Profile/code/unit/`effectiveDateTime`, `device` reference, `subject` equals the reference supplied with a synthetic server-requested examination, otherwise omitted; the device never selects or adds a patient ID. Server-request protocol and its integration fixture remain open; conditional create; first write committed but receipt lost, then retry: exactly one Observation and identical conditional-create identity in every captured attempt; up to 3 retries within 10 s; `201`/`200` receipt confirms delivery without readback; invalid BPM sends only the error report. |
| VT-08 | TLS and network failures | Mock TLS/socket transport + authorized target/server | Wrong CA/name/expired cert/unset time, server failures, partial responses, bounded waits; no active network jobs during listening; retained station association tested separately; secrets redacted. |
| VT-09 | Fault containment | Host injection + target | Wi-Fi-only failures preserve audio; other faults halt per catalogue. Verify counted code/context, that with several errors only the highest-priority error is shown (equal priority: first latched), short-press acknowledgement without retry, and restart-required microphone/DAC faults. Start during setup safely tears down; Start during analysis stays Busy; Start during sending cancels the delivery (DELIVERY_FAILURE, or SERVER_CONNECTION_FAILURE before the UTC end is frozen), releases the network and starts listening. |
| VT-10 | Filter study on host | Host, identical recordings | Same input through each listening filter and the analysis filter into BPM detection; hash-identical inputs and configurations recorded. |
| VT-11 | Evidence and privacy | Inspection | Identity/setup/reference/results/anomalies recorded; logs free of secrets and patient data. |
| VT-12 | Electrical interfaces | Inspection + owner-authorized bench | Carrier pin map, grounds/supplies/straps, 24-bit I2S alignment, DAC line output. |
| VT-14 | Wi-Fi and portal | Host controller/NET model + authorized DevKit/phone | Setup, recovery, cancellation and persistence per REQ-11/REQ-12 and the case groups below. |
| VT-15 | Persistent Device registration (later FHIR phase) | Authorized DevKit and lab HAPI | First registration stores server id; subsequent restarts reuse it; one Device; missing-server-id recovery separately validated. Not a Wi-Fi/portal completion gate. |

VT-14 case groups:

- Entry with no saved credentials at boot, and separately a 2 s hold in Idle with saved credentials: both must open the hotspot and portal. Initial scan before hotspot setup; open hotspot and QR (quick response) code; open and protected joins; address before save.
- Retry budgets; manual boot recovery and automatic reconnect; explicit and implicit rescan; scan-finished state and polling.
- Both Cancel levels; paused inactivity timer; failed save retains the connection and old settings; result closes after 10 s.
- Start teardown and late callbacks; retained association during audio; offline fallback; restart persistence; private logs.

VT-07 and VT-08 are partly covered, on the host only:

- **Host unit evidence:** the [L1_FHIR host suite](../coding/app/tests/host/l1_fhir/test_fhir.py) checks the Device and Observation serializers, both conditional-create conditions and the validation of registration responses. This includes malformed and partial responses and two responses captured from the lab HAPI server.
- **HTTP reader evidence:** the [HTTP reader suite](../coding/app/tests/host/l1_wifi_http/test_wifi_http.py) runs in static CI against a vendored copy of the pinned Zephyr `http_parser`. A test checks that copy against the pin.
- **Host-simulation evidence:** the [delivery scenarios](../coding/app/tests/host/test_delivery.py) cover the L2 workflow under P13 in simulated time. They check the identical retry after a lost receipt or a server error, the four-attempt limit, the 2 s gap measured after the cancellation released the attempt, the 1 s receipt cancel, the 3 s setup budget, fewer attempts when a gap would use up the remaining budget, release by the global deadline, terminal certificate failures, retried malformed or oversized receipts, keep-alive replacement without using an attempt, `WIFI_CLEANUP_FAILURE` instead of a retry, and no request after the deadline. The P25 cases check one SNTP exchange before every TLS setup and none on a reused connection, the 12.5 h mapping limit, a stale anchor replaced by the delivery-setup clock, the 100 ms uncertainty budget and no time or transport work while listening. The DNS case for #131 is a strict expected failure.
- **Time synchronization (L1):** the [L1_WIFI time cases](../coding/app/tests/host/l1_wifi/test_wifi.py) check response rejection, one request without resend, busy Start, idempotent and bounded Cancel, late DNS answers or responses after Cancel, native units and clock application with carry.
- **Secure transport (L2):** the [delivery scenarios](../coding/app/tests/host/test_delivery.py) also cover Idle preparation: cancellation at the P26 10 s attempt budget, the 60 s gap after a failure or an interrupting Start, one `SERVER_CONNECTION_FAILURE` per episode, certificate validity checked before the handshake and the device keep-alive. The TLS worker (`wifi_secure_connection.c`) is not built on the host; its handshake, write, read and cancellation paths remain target evidence.
- **Server profile:** the [server profile tool cases](../coding/app/tests/host/server_profile_tool/test_server_profile.py) check the deployment-file, URL and certificate rules, the image layout and CRC, the partition check and the commands. The [STORAGE reader cases](../coding/app/tests/host/l1_storage/test_storage.py) check valid, erased and corrupted images against the design layout.
- **Open design question:** whether a response that completes in the read crossing the deadline counts as a receipt ([GitHub #130](https://github.com/DemonicPsychoII/DigitalStethoscope/issues/130) / [TICKET-219](https://nfrie.atlassian.net/browse/TICKET-219)). No case asserts either behavior.
- **Still open for VT-07 (TICKET-181, TICKET-209), on the target:**
  - The P13 budgets measured on the board.
  - The server-requested examination.
  - Runs against the authorized local HAPI.
  - Before acceptance, freeze the clock reference, synchronization evidence and allowed measurement-end timestamp skew. Use REQ-06 for value accuracy; the delivery deadline does not define timestamp accuracy.
- **Still open for VT-08 (TICKET-180), on the target:** TLS, socket and timeout fault cases in the mbedTLS exchange worker.

VT-09 and VT-11 are partly covered, on the host only, for time synchronization and the server profile. The L1 time cases check rejected responses, bounded cancellation and late results; the STORAGE reader rejects corrupted images; the server profile tool rejects private keys and other PEM labels (VT-11). Fault containment across the other components and the evidence and privacy procedure still need to be added.

VT-15 is partly covered, on the host only:

- **Host unit evidence:** the [L1_WIFI identity tests](../coding/app/tests/host/l1_wifi/test_wifi_identity.py) check the physical identifier derived from the factory MAC. The L1_FHIR suite checks the encoding and decoding of the registration record.
- **Host-simulation evidence:** the [registration scenarios](../coding/app/tests/host/test_registration.py) cover reuse of a stored record, conditional registration, save failure, the recovery gap, and that interrupted attempts and missing prerequisites do not count toward the failure limit.
- **Still open, on the authorized DevKit with the lab HAPI server:**
  - Reuse across three restarts.
  - Exactly one Device on the server.
  - Recovery from a missing server id.

VT-05 (replay) and VT-13 (shared SPI) were removed in the [scope decision](../planning/mvp-decisions-2026-10-14.md#scope).

## Retired cases

- VT-05: Retired — replay was removed by the scope decision above.
- VT-13: Retired — shared SPI (Serial Peripheral Interface) was removed by the scope decision above.

## Not yet covered

The [documentation check](ci/validate_docs.py) requires each VT ID to occur in a test or procedure file, or in the gap list below. Retired cases use the separate list above. It checks references only. The case list and recorded results show how much of each case is covered. Remove a gap entry when a test or procedure is added.

- VT-01: Not yet covered — startup fault procedures need to be added.
- VT-02: Not yet covered — target timing and resource procedures need to be added.
- VT-03: Not yet covered — application DSP (digital signal processing) cases need to be added. Before final REQ-03 acceptance, the filter study (TICKET-189 / design decision D06) must freeze the listening coefficients, tone frequencies and expected pass/attenuated classifications in the run configuration. No approved study result or quantitative attenuation threshold exists in this baseline; that filter demonstration remains blocked. REQ-03 is an audible selector/filter demonstration, not a filter-superiority claim.
- VT-04: Not yet covered — control and input cases need to be added.
- VT-06: Not yet covered — BPM (beats per minute) session cases need to be added. Freeze signal-validity criteria and reference selection before recording or excluding sessions; REQ-06 acceptance is blocked until then (TICKET-208).
- VT-10: Not yet covered — filter comparison procedure needs to be added.
- VT-12: Not yet covered — electrical inspection procedure needs to be added.

VT-14 host cases are in [the communication batch](../coding/app/tests/host/test_communication.py). Target-only radio, phone/QR/page, restart persistence, retained-station audio and private-log checks are covered by the [Wi-Fi procedure](WIFI/VT-14-target.md) and [portal procedure](PORTAL/VT-14-target.md). Both procedures are unexecuted; target results remain pending (TICKET-182).

## Case execution

Each case becomes an automated test, a manual procedure, or both, depending on what can be observed in its execution environment. Unit, L2 and integration coverage is identified using the levels in [verification operations](ci/OPERATIONS.md#test-levels).

Manual procedures use the single [manual-test format](../process/README.md#manual-component-and-final-system-tests) and [validated executed-run record](manual/README.md). Case-specific setup includes the relevant parameters, signal/reference source, configuration and equipment. The device/software field and step notes retain these details or link their evidence. Sensitive credentials and patient data do not belong in the record.

## Recorded evidence

<details>
<summary>Wi-Fi workflow host evidence — 19 October 2026</summary>

Historical source: local implementation based on `10fde50`, recorded in the service-contract and stacked workflow work for PR #50 (`feature/implement-wifi-service`). The tests described below are absent from this end state. These results identify that earlier source, not current application coverage. No target firmware revision or hardware measurement is claimed.

- `python -m pytest -q Development/system/coding/app/tests/host`: 17 passed using
  Zig 0.16.0 as a C11 host compiler through `CC`. The production communication
  source is compiled with deterministic kernel and L1 substitutes. Cases cover
  control bursts, stale acknowledgement, exact retry/result deadlines, Start
  during scan/result display, cancellation and teardown failures, scan timeout,
  two failed saves, scan-before-AP, one-time recovery, inactivity, retained station,
  setup holds, partial startup failure and offline release after init failure.
- ESP32-S3 application build: passed with the pinned Zephyr workspace. This builds
  the service placeholders and orchestration, not a functioning radio or HTTP server.
- Agent-gate tests: 90 passed. Build-tooling tests: 57 passed, including selection of
  the workflow host tests for application changes. Documentation links, changed
  PlantUML renders, Python lint and C formatting: passed. The Wi-Fi page was checked
  in desktop and phone-width previews; no console errors were reported.
- Full static verification stops at missing Windows `actionlint`; later workflow
  and shell checks were not run. The combined bring-up/application host run had
  4 failures and 69 fixture errors in the existing bring-up suite because a usable
  `gcc` executable was unavailable; its 15 then-existing communication cases passed.
  The final 17-case communication suite was run separately and passed.
- Target cancellation latency, atomic flash behaviour, radio/audio interference,
  HTTP request handling, visibility and the CONTROL integration remain unverified.

</details>

<details>
<summary>Earlier documentation review</summary>

The 6 October 2026 review-package validation is a historical record at
`Development/system/testing/evidence/2026-10-06-draft-validation.md`. Its recorded
commands and paths describe that earlier checkout. Links to evidence and test files
are added in the generated test stage.

</details>
