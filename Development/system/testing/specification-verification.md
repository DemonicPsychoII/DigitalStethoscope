# Application verification cases

This is the application's case catalogue. It links the system acceptance checks to the component checks needed during development. The [development process](../process/README.md) defines test generation and review; [verification operations](ci/OPERATIONS.md) defines execution and infrastructure.

## Current state and target

The catalogue defines the target cases. The communication host batch will provide partial VT-14 coverage in its test PR. Other cases still need a test or procedure reference, as listed below. Recorded results apply to their identified source and configuration. Full device acceptance remains pending.

## System acceptance

[REQ-01–REQ-15](../requirements/system-requirements.md) define the finished-device tests and pass criteria. Each requirement is exercised on the identified device and firmware build, with an outcome and evidence. Component evidence supports these complete system runs.

## Component and integration cases

The VT cases below check the [design contracts](../design/interfaces-and-behavior.md#design-constraints). They define internal verification of the agreed design. Their identifiers remain stable as the procedures are expanded.

| ID | Check | Level / method | Exercise and evidence |
|---|---|---|---|
| VT-01 | Startup | Host fault injection + target | Power-on with missing microphone/DAC; silent initialization and a restart-required muted Error per current catalogue. Physical tests only with owner authorization. |
| VT-02 | Audio timing and resources | Target instrumented load/soak | Critical CPU time and block waits per audio block, queue/memory watermarks, drift. Latency is judged by ear (REQ-05); no two-channel measurement setup is available. |
| VT-03 | Listening DSP | Host production core + target listening | Raw identity before gain, impulse/sweep response, extremes and saturation, transition artifacts. |
| VT-04 | Control and input | Host model/adapter injection + target | Every allowed/rejected transition; bounce, queue saturation, Busy, LED patterns and snapshot consistency. |
| VT-06 | BPM sessions | Host recordings/reference + target | Supported range, S1/S2 and harmonics, silence/noise/clipping/gaps, aggregation, cancel/finalize races. Recordings, reference and resampling decided during the Wi-Fi/FHIR phase. |
| VT-07 | FHIR delivery | Host serializer / mock server + authorized local HAPI | Profile/code/unit/`effectiveDateTime`, `device` reference, `subject` only when the server has [linked a patient](../planning/mvp-decisions-2026-10-16.md#confirmed-decisions); conditional create; up to 3 retries within 10 s with no duplicate; [`201`/`200` receipt](../design/interfaces-and-behavior.md#delivery-clock-and-configuration); invalid BPM sends only the error report. |
| VT-08 | TLS and network failures | Mock TLS/socket transport + authorized target/server | Wrong CA/name/expired cert/unset time, server failures, partial responses, bounded waits; no active network jobs during listening; retained station association tested separately; secrets redacted. |
| VT-09 | Fault containment | Host injection + target | Wi-Fi-only failures preserve audio; other faults halt per catalogue. Verify counted code/context, that with several errors only the highest-priority error is shown (equal priority: first latched), short-press acknowledgement without retry, and restart-required microphone/DAC faults. Start during setup safely tears down; Start during analysis/sending stays Busy. |
| VT-10 | Filter study on host | Host, identical recordings | Same input through each listening filter and the analysis filter into BPM detection; hash-identical inputs and configurations recorded. |
| VT-11 | Evidence and privacy | Inspection | Identity/setup/reference/results/anomalies recorded; logs free of secrets and patient data. |
| VT-12 | Electrical interfaces | Inspection + owner-authorized bench | Carrier pin map, grounds/supplies/straps, 24-bit I2S alignment, DAC line output. |
| VT-14 | Wi-Fi and portal | Host controller/NET model + authorized DevKit/phone | Setup, recovery, cancellation and persistence per the [Wi-Fi design](../design/interfaces-and-behavior.md#wi-fi-setup-and-recovery--19-october). See the case groups below. |
| VT-15 | Persistent Device registration (later FHIR phase) | Authorized DevKit and lab HAPI | First registration stores server id; subsequent restarts reuse it; one Device; missing-server-id recovery separately validated. Not a Wi-Fi/portal completion gate. |

VT-14 case groups:

- Initial scan before hotspot setup; open hotspot and QR (quick response) code; open and protected joins; address before save.
- Retry budgets; manual boot recovery and automatic reconnect; explicit and implicit rescan; scan-finished state and polling.
- Both Cancel levels; paused inactivity timer; failed save retains the connection and old settings; result closes after 10 s.
- Start teardown and late callbacks; retained association during audio; offline fallback; restart persistence; private logs.

VT-05 (replay) and VT-13 (shared SPI) were removed in the [scope decision](../planning/mvp-decisions-2026-10-14.md#scope).

## Retired cases

- VT-05: Retired — replay was removed by the scope decision above.
- VT-13: Retired — shared SPI (Serial Peripheral Interface) was removed by the scope decision above.

## Explicit coverage gaps

The [documentation check](ci/validate_docs.py) requires each VT ID to occur in a test or procedure file, or in the gap list below. Retired cases use the separate list above. It checks references only. The case list and recorded results show how much of each case is covered. Remove a gap entry when a test or procedure is added.

- VT-01: Not yet covered — startup fault procedures need to be added.
- VT-02: Not yet covered — target timing and resource procedures need to be added.
- VT-03: Not yet covered — application DSP (digital signal processing) cases need to be added.
- VT-04: Not yet covered — control and input cases need to be added.
- VT-06: Not yet covered — BPM (beats per minute) session cases need to be added.
- VT-07: Not yet covered — application FHIR (Fast Healthcare Interoperability Resources) receipt cases need to be added.
- VT-08: Not yet covered — TLS (Transport Layer Security) and network fault cases need to be added.
- VT-09: Not yet covered — fault containment cases need to be added.
- VT-10: Not yet covered — filter comparison procedure needs to be added.
- VT-11: Not yet covered — evidence and privacy procedure needs to be added.
- VT-12: Not yet covered — electrical inspection procedure needs to be added.
- VT-15: Not yet covered — persistent registration procedure needs to be added.

- VT-14: Not yet covered — the communication batch and target procedures follow in the test PR.

Target radio, portal, persistence and audio-interference results remain pending.

## Case execution

Each case becomes an automated test, a manual procedure, or both, depending on what can be observed in its execution environment. Unit, L2 and integration coverage is identified using the levels in [verification operations](ci/OPERATIONS.md#test-levels).

Manual procedures use the single [manual-test format](../process/README.md#manual-component-and-final-system-tests). Case-specific setup includes the relevant parameters, signal/reference source, configuration and equipment. The device/software field and step notes retain these details or link their evidence. Sensitive credentials and patient data do not belong in the record.

## Recorded evidence

<details>
<summary>Wi-Fi workflow host evidence — 19 October 2026</summary>

Source: local implementation based on `10fde50`. This branch holds only the
service contracts; the workflow and the host tests are in the stacked PR #50
(`feature/implement-wifi-service`). No target firmware revision or
hardware measurement is claimed.

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

[6 October 2026 review-package validation](evidence/2026-10-06-draft-validation.md) records historical documentation checks.

</details>
