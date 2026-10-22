# Verification and acceptance evidence

**All procedures are planned, not executed product tests.** Acceptance is defined by the
[system requirements](../requirements/system-requirements.md): each requirement names the test Nico runs on the
device and its pass criterion. The developer checks below are internal: they help find defects before the
acceptance tests and verify the [design constraints](../design/interfaces-and-behavior.md#design-constraints),
but they are not requirements.

## Acceptance tests

Run every requirement as written in the [requirement table](../requirements/system-requirements.md). Record each run with
the evidence template below.

## Developer checks (internal)

| ID | Check | Level / method | Exercise and evidence |
|---|---|---|---|
| VT-01 | Startup | Host fault injection + target | Power-on with missing microphone/DAC; silent initialization and a restart-required muted Error per current catalogue. Physical tests only with owner authorization. |
| VT-02 | Audio timing and resources | Target instrumented load/soak | Critical CPU time and block waits per audio block, queue/memory watermarks, drift. Latency is judged by ear (REQ-05); no two-channel measurement setup is available. |
| VT-03 | Listening DSP | Host production core + target listening | Raw identity before gain, impulse/sweep response, extremes and saturation, transition artifacts. |
| VT-04 | Control and input | Host model/adapter injection + target | Every allowed/rejected transition; bounce, queue saturation, Busy, LED patterns and snapshot consistency. |
| VT-06 | BPM sessions | Host recordings/reference + target | Supported range, S1/S2 and harmonics, silence/noise/clipping/gaps, aggregation, cancel/finalize races. Recordings, reference and resampling decided during the Wi-Fi/FHIR phase. |
| VT-07 | FHIR delivery | Host serializer / mock server + authorized local HAPI | Profile/code/unit/`effectiveDateTime`, `device` reference, `subject` only when the server has linked a patient (16 October); conditional create; up to 3 retries within 10 s with no duplicate; `201`/`200` receipt, no readback (15 October); invalid BPM sends only the error report. |
| VT-08 | TLS and network failures | Mock TLS/socket transport + authorized target/server | Wrong CA/name/expired cert/unset time, server failures, partial responses, bounded waits; no active network jobs during listening; retained station association tested separately; secrets redacted. |
| VT-09 | Fault containment | Host injection + target | Wi-Fi-only failures preserve audio; other faults halt per catalogue. Verify counted code/context, that with several errors only the highest-priority error is shown (equal priority: first latched), short-press acknowledgement without retry, and restart-required microphone/DAC faults. Start during setup safely tears down; Start during analysis/sending stays Busy. |
| VT-10 | Filter study on host | Host, identical recordings | Same input through each listening filter and the analysis filter into BPM detection; hash-identical inputs and configurations recorded. |
| VT-11 | Evidence and privacy | Inspection | Identity/setup/reference/results/anomalies recorded; logs free of secrets and patient data. |
| VT-12 | Electrical interfaces | Inspection + owner-authorized bench | Carrier pin map, grounds/supplies/straps, 24-bit I2S alignment, DAC line output. |
| VT-14 | Wi-Fi and portal | Host controller/NET model + authorized DevKit/phone | Scan-before-AP initial entry; open hotspot/QR; open and protected joins; address before save; all operation retry budgets; boot manual vs reconnect automatic recovery; explicit/implicit rescan and scan-finished; polling; both Cancel levels; paused inactivity timer; save failure retains connection/old settings; 10 s result closure; Start teardown and late callbacks; retained association audio interference; offline fallback; restart persistence; no secrets in logs. See 19 October decisions. |
| VT-15 | Persistent Device registration (later FHIR phase) | Authorized DevKit and lab HAPI | First registration stores server id; subsequent restarts reuse it; one Device; missing-server-id recovery separately validated. Not a Wi-Fi/portal completion gate. |

VT-05 (replay) and VT-13 (shared SPI) were removed with the optional features on 14 October 2026.

## Evidence record template

Use one record per requirement/configuration combination, including negative cases. A passing lap-like
functional demonstration under one configuration does not establish acceptance for other configurations.

| Field | Required entry |
|---|---|
| Case identity | Test ID/case, REQ IDs, report revision |
| Device identity | Board/carrier revision, device identifier, microphone/DAC and wiring revision |
| Software | Commit plus dirty state, build/profile ID, source snapshot/configuration hashes |
| Parameters | Filters/coefficient version, window/update/session length, coverage rules, gain |
| Setup | Fixture hash/license, signal/reference device, instrumentation, input level, sample format/rate, environment |
| Preconditions | Capability/readiness, calibration, patient/test provenance, clock/trust/server configuration (no secrets) |
| Steps | Repeatable actions, fault injection, cancellation timing and load conditions |
| Expected | Agreed threshold and defined statistic for each linked requirement |
| Actual | Measured values, raw evidence/log paths, invalid fraction, counters, observed outcomes |
| Verdict | Pass / Fail / Blocked / Not run, with deviations and limitations |
| Review | Executor, date, independent reviewer, anomalies/disposition, retest after corrections |

## Acceptance sequence

1. Review scope/use cases and parameters with Nico; resolve implementation-blocking questions.
2. Verify pure core and control contracts on host using production modules and meaningful negative cases.
3. Integrate target hardware incrementally, record physical readiness and timing before optimizing cores.
4. Run authorized system workflows, load/fault tests and FHIR readback; retain configuration.
5. Evaluate filter variants on identical approved material and reference; report outcome even if no
   filter wins. Optional exploratory hearing study is separate and does not replace functional checks.
6. After review-driven arithmetic, interface or configuration changes, rerun affected tests.
7. Run the acceptance test of every system requirement on the finished device. Formal acceptance requires reviewed results; this draft supplies no acceptance claim.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

The [14 October decisions](../planning/mvp-decisions-2026-10-14.md) and the [implementation timeline](../planning/mvp-implementation-timeline.md) define the remaining evidence.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.

## Wi-Fi workflow host evidence — 19 October 2026

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

Recorded by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
