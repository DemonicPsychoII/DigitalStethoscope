# MVP decisions and evaluation proposals — 11 October 2026

Nico's answers in T3 thread `58a691a9-4492-46b4-b65e-39cde5d8e3fc` supersede older workflow proposals. This records decisions and planned evidence, not firmware behavior or completed hardware validation. Numeric values below are proposals requested by Nico, not approved thresholds or medical claims.

## Confirmed scope and behavior

- Saved audio, replay, display/touch, SD and speed presets are optional. MVP BPM uses bounded streaming analysis state, not full-session capture. Post-Stop aggregation operates on retained estimates/coverage; deferred processing of raw session audio is an optional follow-up.
- Start during analysis or sending is rejected as Busy with an activity indication; it does not cancel work or queue another session. Proposed indication: pulsing activity LED. Stop before 15 s cancels; ordinary Start/Stop and separate error acknowledgement remain distinct actions.
- Failed sends are indicated and aborted. No automatic/manual retry queue or retained sendable failed payload in MVP. Retain redacted outcome metadata for evidence. A timeout after server commit is Unverified; aborting locally cannot retract a server write.
- Wi-Fi error indication clears manually only. Acknowledgement clears the indication, not the underlying network condition, does not retry, and does not start audio. A new failed operation can latch it again. Unconfigured Wi-Fi produces no send attempt/error; configured Wi-Fi failure permits offline listening.
- Mode, patient and session identity/context are fixed during the session. Reject attempted changes with a normal fault and retain the original context; do not mutate or implicitly cancel/relabel the session. Freeze context through finalization/delivery. Volume/listening-filter adjustment remains separate from session identity and analysis settings.
- Invalid BPM produces no numeric BPM transmission and should send an error message to the server. This is a separate outcome path, never BPM=0 or the previous valid value. Lung still sends nothing. Error reporting waits until audio is stopped and requires configured network/trust/time/context; failed reporting also aborts without retry.
- **Device Alarm (DA):** dangerous fault or failed essential device functionality, including essential audio failure. Mute and latch; recovery requires complete device restart and startup checks. A button acknowledgement cannot restore operation. **Normal alarm/fault:** reduced functionality, such as BPM or Wi-Fi failure, while listening still works. Detection limits remain software-observable; bench tests establish physical operation.
- Use the newest Altium evaluation PCB and newest stable Zephyr release for evaluation. Freeze exact PCB export/revision and release SHA in evidence. No function is demonstrated on this current board/image yet. Historical bring-up results do not establish current-board acceptance.
- Hardware is present; carrier PCB was approximately two weeks away on 11 October (planning assumption: around 25 October, not a committed delivery date). No measurement equipment/second microphone is currently available. Arrange a latency fixture rather than marking subjective listening as measured latency.
- Nico implements and verifies; others review. Wi-Fi/FHIR is the first phase because it can run on the DevKit before the carrier. Device-originated FHIR integration evidence belongs in that phase; a later microphone-session run closes end-to-end evidence.
- Existing HTTPS/lab CA, software-only startup checks, Lung, fixed identity and cancellation decisions stand. No review-slot action or thesis prose drafting is requested.

## Proposed BPM acceptance table

Published BPM values alone are not reference-labelled audio and do not validate this estimator. Select a corpus before tuning; record version/license, file hashes, subject split and reference extraction. PhysioNet Challenge 2016 is a candidate, but only records with independently usable beat timing/synchronous ECG qualify for accuracy tests. Normal/abnormal labels alone do not supply BPM ground truth. Synthetic signals verify mechanics and boundaries only.

| Criterion | Proposed test | Proposed pass condition |
|---|---|---|
| Supported range | Synthetic whole-cycle fixtures at 30, 40, 60, 80, 100, 120, 150, 180, 200 BPM; real referenced records stratified by available rates | Engineering scope 30–200 BPM; results outside range invalid. Do not claim corpus coverage where data are absent. |
| Session error | Same retained sample interval for estimator and independent reference; held-out subjects; report MAE, bias, max error and distribution | MAE ≤5 BPM and ≥95% of valid session results within max(5 BPM, 10% reference); invalid runs reported separately. Engineering target, not standards compliance. |
| Result availability | Predeclared clean held-out sessions, all attempted sessions in denominator | ≥95% valid completed sessions; aspiration is a BPM on every usable run. Poor signals intentionally yield no BPM. Report count and rate by condition. |
| Poor signal / gaps | Silence, clipping, noise, missing blocks and insufficient periodicity fixtures | No numeric result on declared unusable fixtures; missing blocks reset/invalidate affected windows, never reuse old BPM. Score definition/threshold calibrated on development split only. |
| Harmonic errors | S1/S2 fixtures and annotated examples with varied sound amplitudes | No accepted doubled/halved estimate on declared fixtures; all real-data harmonic failures reported and count toward error criterion. Range alone cannot catch them. |
| Session duration | Stop at 14.999/15/30 s and long sessions | <15 s cancels; ≥15 s may finalize if all validity rules pass. Recommend 30 s acquisition, without changing manual Stop semantics. |
| Window / aggregation | Compare 3/5/8 s windows with 1 s update on identical recordings | Start with 8 s, median of valid estimates, ≥3 valid windows and ≥80% union of valid sample intervals within actual session; overlap counted once. Final value describes the frozen acquisition interval. |
| Filter independence | Identical source with Raw/Murmur/BPM listening selections and volume changes | Analysis is unchanged by listening settings; evaluate analysis Raw vs 25–150 Hz candidate. Listening Raw and 40–800 Hz Murmur are candidates. Measure response within INMP441 usable band; no assumed optimality. |

For an 8 s window at 30 BPM there are four cardiac cycles; a 3 s window contains 1.5. This is a reason to evaluate longer windows, not evidence of accuracy. Streaming envelope storage at 100 Hz × 8 s × 4 bytes is 3,200 bytes; account separately for raw block pools, filter state and estimator workspace. Optional 30 s raw int32/16 kHz mono storage would cost 1,920,000 bytes and is excluded from the MVP budget.

## Latency research and proposed budgets

[Lester & Boley, AES 2007](https://boseperformer.com/images/7/7b/AES_Latency.pdf) studied live musical monitoring: acceptable delay depended on instrument and monitor, spanning approximately 42 ms to below 1.4 ms. [Jack, Stockman & McPherson, 2016](https://instrumentslab.org/data/andrew/jack_am2016.pdf) found worse subjective instrument ratings for 20 ms and 10 ms with jitter than zero delay; fixed 10 ms did not differ significantly in ratings. Neither is a stethoscope perception study. There is no established universal imperceptible upper limit here, and these sources do not justify 80 ms. Older R09 research's universal 10–15 ms wording should be read with this qualification.

| Budget | Proposal | Evidence / pass method |
|---|---|---|
| End-to-end listening | <30 ms baseline; <10 ms stretch; stable delay | Input/output transient captured on a common clock, including microphone, buffers, DSP, DAC and amplifier. Report median/p95/max, jitter and fixture uncertainty per filter; distinguish electrical transport from acoustic path. Baseline is an engineering compromise, not proven imperceptibility. |
| Processing | ≤4 ms critical execution for each 128-frame/16 kHz (8 ms) block | Target traces, worst observed load and zero deadline misses; measure scheduling/queue waits separately. |
| Controls / indication | ≤100 ms effective control response; ≤500 ms visible status | Timestamp event through applied state/output; include debounce. Busy and acknowledgement do not accidentally accept Start. |
| Resources | ≥25% measured free stack/internal-heap headroom | Linker map plus watermarks during TLS, BPM and 30 min soak; separate DMA SRAM from PSRAM. Also record allocation-failure paths and minimum largest-free-block; total free heap alone is insufficient. |
| Networking | Proposed 10 s connect/TLS and 10 s request/readback phase limits, bounded terminal completion | Timeout injection and target logs; one active delivery, Start blocked. Application network jobs excluded from listening/measurement; measure remaining radio interference. |
| Fault response | Mute within one 8 ms block after detected DA; restart-only recovery | Inject detectable faults, measure detection and mute separately. No claim of detection of all analog/acoustic faults. |

Latest stable listed by [Zephyr release documentation](https://docs.zephyrproject.org/latest/releases/index.html) on 11 October is 4.4.0; 4.5 is planned for October but is not yet listed stable. Recheck the newest stable tag when BASE begins and freeze it; preserve current CI pin until a separately verified migration. Release support and successful builds are not physical-driver qualification.

## Error-report transport proposal

The server contract for invalid BPM is not supplied yet. Proposed interoperable representation: a missing-value R4 Observation carrying the frozen patient/measurement interval and `dataAbsentReason`, without `valueQuantity`. Verify status, coding, profile and server acceptance before selecting it; an explicit error endpoint is an alternative if the lab backend requires it. [FHIR R4 Observation](https://hl7.org/fhir/R4/observation.html) allows absent-value reasons only when value is absent. [OperationOutcome](https://hl7.org/fhir/R4/operationoutcome.html) represents operation diagnostics and is not automatically a client fault-ingestion endpoint. Do not invent or post to such an endpoint. This contract check belongs in FHIR, not a claim of existing backend support.

## Implementation timeline

See [component timeline](mvp-implementation-timeline.md). Existing Jira deadlines were re-read on 11 October: preparation 14 October, implementation 18 November, refinement 25 November, verification 2 December and validated milestone 3 December. Dates below are a provisional single-person schedule at 4 focused hours per weekday, 96 h total including 8 h correction reserve; holidays, meetings and actual availability are not modelled. Remaining capacity through 3 December is for refinement/verification, not a reason to add optional scope. Update remaining estimates and successor dates as soon as evidence changes; Jira links express real blockers, calendar sequencing also reflects one implementer.
