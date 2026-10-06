# Planned verification and acceptance evidence

**All procedures are planned, not executed product tests.** The documentation checks performed for this draft are separate from the device verification below. Open parameters prevent final pass/fail claims until agreed. Each component requirement names its verification procedure; [traceability.csv](../requirements/traceability.csv) supplies the reverse mapping.

| ID | Procedure | Level / method | Required exercise and evidence |
|---|---|---|---|
| VT-01 | Startup and capabilities | Host fault injection + target | Power-on, missing mic/DAC/display/touch/SD; silent initialization, degraded controls and evidence levels. Record actual mute and readiness; power/physical test only with owner authorization. |
| VT-02 | Audio timing, latency and resource budget | Target instrumented load/soak | I2S known samples; critical CPU and scheduling/block wait times per 8 ms block; complete analog latency including DAC; queue/memory watermarks and drift. Candidate soak 30 min pending D10; averages alone insufficient. |
| VT-03 | Listening DSP and conversions | Host production core + target listening | Raw identity before gain, impulse/sweep coefficient response, extremes/sign conversion/saturation, transition artifacts. Repeat on changed arithmetic/coefficients. |
| VT-04 | Control, mode, input and UI | Host model/adapter injection + target | Every allowed/rejected transition; bounce, multiple/open contacts, physical/touch/shell races, queue saturation, equal timestamps, Lung guards, LED overlap and snapshot consistency. |
| VT-05 | Capture and replay | Host waveforms + target | Raw independence from listening filter/gain, capacity/end/cancel boundary, speeds/duration/pitch/artifacts, fresh-mic BPM during replay; no patient persistence. |
| VT-06 | BPM sessions and validity | Host corpus/reference + target | Supported range, S1/S2 and harmonics, silence/noise/clipping/gaps, invalid coverage, overlap-aware aggregation, frozen context and cancel/finalize races; error and invalid fraction stratified. |
| VT-07 | FHIR semantics and provenance | Host serializer / mock server + authorized local HAPI | Validate profile/code/unit/subject/measurement interval, stable-ID PUT/retry after commit timeout, readback content, one initial attempt, all invalid/test/Lung negative cases emit no patient request. |
| VT-08 | TLS, network failures and exclusion | Mock TLS/socket transport + authorized target/server | Wrong CA/name/expired cert/time, auth/server/partial response failures, bounded waits and cancellation; race live-start against connection/TLS/readback; no lease overlap; secrets redacted. |
| VT-09 | Fault containment and recovery | Host injection + target | Stall workers/queues, transport errors, source/mode/context changes, optional-device errors, stale generations; measured fault-detection and mute response separately; bounded explicit recovery. |
| VT-10 | Fixture portability and evaluation reproducibility | Host and target same PCM | Hash-identical inputs/configs across listening/analysis variants; good/bad formats, EOF/truncation, SD absence and source transition; retain license/reference; measure host-uploaded target fixture volatile-buffer use against the agreed bound and trace zero SD/SPI access; verify host-side fixture injection uses the same DSP path with zero target-SPI operations; no acoustic-path claim for bypassed fixture. |
| VT-11 | Evidence and privacy | Inspection + completed evaluation report | Check identity/setup/reference/actual results/reviewer/anomalies, separate readiness from physical proof, configuration provenance, secret-free logs and rerun evidence after changes. |
| VT-12 | Electrical/hardware interface checks | Inspection + owner-authorized bench | Carrier/overlay pin map, grounds/supplies/straps, 24-bit I2S alignment, amplifier DAC load/output level, reserved pins, speed switch and SD wiring confirmation. |
| VT-13 | Shared SPI scheduling | Target bus trace + fault injection | Concurrent partial display/touch/SD requests, operation chunk sizes, prefetch starvation/queue behavior, no filesystem wait in audio; transfer lower bound does not serve as measured bus WCET. |

## Evidence record template

Use one record per requirement/configuration combination, including negative cases. A passing lap-like
functional demonstration under one configuration does not establish acceptance for other configurations.

| Field | Required entry |
|---|---|
| Case identity | Test ID/case, requirement IDs, use-case IDs, report revision |
| Device identity | Board/carrier revision, device identifier, microphone/DAC/amplifier and wiring revision |
| Software | Commit plus dirty state, build/profile ID, source snapshot/configuration hashes |
| Parameters | Filters/coefficient version, window/update/session length, validity/coverage thresholds, replay speed, gain, mode/point |
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
4. Run authorized system workflows, shared-bus/load/fault tests and FHIR readback; retain configuration.
5. Evaluate filter variants on identical approved material and reference; report outcome even if no
   filter wins. Optional exploratory hearing study is separate and does not replace functional checks.
6. After review-driven arithmetic, interface or configuration changes, rerun affected tests and update
   traceability. Formal acceptance requires reviewed results; this draft supplies no acceptance claim.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
