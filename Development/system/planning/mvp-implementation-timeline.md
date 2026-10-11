# MVP component implementation timeline

Baseline proposal: one implementer (Nico), 4 focused hours per weekday from 16 October, 96 h including 8 h correction reserve. Dates are planning targets, not availability commitments. [Decisions and acceptance proposals](mvp-decisions-2026-10-11.md) define scope and evidence. Existing TICKET-143 (18 November) and TICKET-133 (3 December) deadlines are preserved. Review/admin and writing remain outside this change.

Tasks are direct children of TICKET-98 so the existing Jira timeline can display their dates and dependency links. TICKET-143 remains the implementation umbrella; do not double-count its aggregate estimate. No task is marked implemented by creating this plan.

| ID | Component task | Effort | Start → due | Functional blockers | Jira |
|---|---|---|---|---|---|
| BASE | Pin Zephyr and establish MVP contracts | 4 h | 2026-10-16 → 2026-10-16 | — | [TICKET-166](https://nfrie.atlassian.net/browse/TICKET-166) |
| WIFI | Implement Wi-Fi configuration and clock mapping | 8 h | 2026-10-19 → 2026-10-20 | BASE | [TICKET-167](https://nfrie.atlassian.net/browse/TICKET-167) |
| FHIR | Implement HTTPS/FHIR delivery and invalid-result reporting | 8 h | 2026-10-21 → 2026-10-22 | WIFI | [TICKET-168](https://nfrie.atlassian.net/browse/TICKET-168) |
| NETTEST | Verify one device-originated FHIR integration run | 4 h | 2026-10-23 → 2026-10-23 | FHIR | [TICKET-169](https://nfrie.atlassian.net/browse/TICKET-169) |
| CTL | Implement session controller and alarm states | 8 h | 2026-10-26 → 2026-10-27 | BASE | [TICKET-170](https://nfrie.atlassian.net/browse/TICKET-170) |
| BOARD | Verify latest evaluation carrier and component wiring | 4 h | 2026-10-28 → 2026-10-28 | Carrier and equipment availability | [TICKET-171](https://nfrie.atlassian.net/browse/TICKET-171) |
| AUDIO | Implement and verify microphone-to-output audio path | 12 h | 2026-10-29 → 2026-11-02 | BOARD | [TICKET-172](https://nfrie.atlassian.net/browse/TICKET-172) |
| DSP | Implement independent listening and analysis filters | 8 h | 2026-11-03 → 2026-11-04 | AUDIO | [TICKET-173](https://nfrie.atlassian.net/browse/TICKET-173) |
| BPM | Implement streaming BPM and reference validation | 12 h | 2026-11-05 → 2026-11-09 | DSP | [TICKET-174](https://nfrie.atlassian.net/browse/TICKET-174) |
| INTEGRATE | Integrate completed sessions with FHIR and error reporting | 8 h | 2026-11-10 → 2026-11-11 | BPM, NETTEST, CTL | [TICKET-175](https://nfrie.atlassian.net/browse/TICKET-175) |
| VERIFY | Verify MVP timing, resources and fault containment | 12 h | 2026-11-12 → 2026-11-16 | INTEGRATE | [TICKET-176](https://nfrie.atlassian.net/browse/TICKET-176) |
| BUFFER | Resolve integration findings and freeze MVP evidence | 8 h | 2026-11-17 → 2026-11-18 | VERIFY | [TICKET-177](https://nfrie.atlassian.net/browse/TICKET-177) |

Carrier arrival around 25 October and access to a latency fixture are external prerequisites, not demonstrated facts. BASE rechecks newest stable Zephyr. NETTEST uses an explicit diagnostic harness and synthetic Patient; INTEGRATE repeats the run with real microphone BPM. Saved raw audio/replay/captive portal are optional follow-ups.

## BASE — Pin Zephyr and establish MVP contracts

**Inputs:** Newest stable Zephyr release; current application structure and evaluation baseline.

**Output and acceptance evidence:** Pin release tag/SHA and SDK; build ESP32-S3 baseline; define frozen result, error event and network lease contracts. No physical peripheral qualification implied.

## WIFI — Implement Wi-Fi configuration and clock mapping

**Inputs:** ESP32-S3 DevKit, lab AP and private deployment configuration. Carrier PCB not required.

**Output and acceptance evidence:** Serial/shell provisioning for MVP; no captive portal required. DHCP/DNS, finite connection timeout, SNTP on configured lab network before measurement; freeze UTC/monotonic anchor. Unset time forbids patient send; unconfigured Wi-Fi causes no send error; configured connection failure leaves offline listening available.

## FHIR — Implement HTTPS/FHIR delivery and invalid-result reporting

**Inputs:** Frozen result/error contracts, endpoint https://nglegion:8443/fhir, ca.pem, synthetic Patient/stetho-test-01.

**Output and acceptance evidence:** Stable-ID PUT plus matching GET; CA, hostname and clock verification. One attempt then terminal failed/unverified indication and no retry queue. Invalid BPM has no numeric value; agree and validate missing-value error representation with server. Production fixture provenance guard remains intact.

## NETTEST — Verify one device-originated FHIR integration run

**Inputs:** Flashed DevKit, configured lab network/server and diagnostic test payload; owner executes device operations.

**Output and acceptance evidence:** Record hash/config, device request/status, ID/patient/value/unit/time matching readback and validator output. Explicit diagnostic harness sends only synthetic-patient fixtures; do not bypass production source guards. Wrong CA/name, unset clock, missing Patient, lost response and failed readback tested. This proves transport, not acoustic measurement accuracy; repeat with actual microphone session at INTEGRATE.

## CTL — Implement session controller and alarm states

**Inputs:** Confirmed Start/Stop/session decisions and network completion events.

**Output and acceptance evidence:** Start blocked with busy indication during analysis/sending. Reject mode/patient/context changes in session without mutation; normal fault. Separate acknowledgement click clears normal Wi-Fi latch only manually; no implicit Start. DA mutes and latches until full restart, no button recovery. Stop <15 s cancels; Lung no BPM/FHIR. Host race/state matrix passes.

## BOARD — Verify latest evaluation carrier and component wiring

**Inputs:** Latest Altium evaluation PCB, fitted carrier and current pin map; carrier expected around 25 October, not confirmed.

**Output and acceptance evidence:** Record exact PCB revision/export hash, GPIO/I2S mappings and amplifier identity/gain/load. Check power and output limits before headphone tests. Carrier arrival and test fixture access are blocking prerequisites; driver readiness is not physical operation.

## AUDIO — Implement and verify microphone-to-output audio path

**Inputs:** INMP441, PCM5102A and verified headphone amplifier/carrier.

**Output and acceptance evidence:** Signed 24-bit normalization, bounded internal DMA pools, DAC output, volume and controls. Record physical input/output proof and timing. No replay or full-session audio storage in MVP. DA injection and full-restart recovery verified.

## DSP — Implement independent listening and analysis filters

**Inputs:** Original-rate blocks and candidate Raw/Murmur/BPM bands.

**Output and acceptance evidence:** Listening filter/gain changes cannot change analysis input. Measure response, smoothing/clipping and delays. Raw, 40–800 Hz Murmur and 25–150 Hz analysis are evaluation candidates, not proven optimal bands; document INMP441 low-frequency constraint.

## BPM — Implement streaming BPM and reference validation

**Inputs:** Selected PCG corpus with independent reference, proposed acceptance table.

**Output and acceptance evidence:** 8 s window/1 s update/30 s recommended session; Stop >=15 s finalizes if quality/coverage pass. Whole-cycle estimator, gap/clipping/harmonic guards, median and union-based coverage. Report MAE/bias/tolerance pass fraction and invalid-session fraction on held-out subjects. No raw-session capture required.

## INTEGRATE — Integrate completed sessions with FHIR and error reporting

**Inputs:** Verified streaming result and network/controller contracts.

**Output and acceptance evidence:** Real microphone Heart session produces one frozen result with measured interval/time; stop, analysis and send block Start. Readback matches; invalid BPM generates only agreed error report. Failed sends abort, Lung/offline/cancel and DA paths verified. Remove rolling-estimate 2.5 s age gate from completed-result eligibility; retain provenance/time guards.

## VERIFY — Verify MVP timing, resources and fault containment

**Inputs:** Integrated current image plus latency fixture/equipment access.

**Output and acceptance evidence:** 30 min load soak; no audio deadline misses/drops, <=4 ms critical execution per 8 ms block, <30 ms end-to-end target (<10 ms stretch), <=100 ms input effect, <=500 ms status, >=25% measured stack/internal-heap headroom. Separate electrical vs acoustic measurement and detection vs mute latency; no physical-latency pass until fixture exists.

## BUFFER — Resolve integration findings and freeze MVP evidence

**Inputs:** Logged findings and reproducible evidence.

**Output and acceptance evidence:** Re-test fixes, reconcile requirements/diagrams, record remaining limitations. Eight-hour contingency, not optional-feature allocation; flag slippage rather than compressing physical verification. Implementation target 18 November; refinement/validation milestones remain 25 November/2–3 December.

## Progress and replanning

Log actual time and update remaining estimate at each work block. If remaining effort exceeds the baseline, a blocker remains open at the scheduled start, or a task misses its due date, recalculate successor dates and compare the finish with 18 November/3 December. Preserve the baseline in this document; explain scope/evidence changes in Jira. Independent work may move earlier when the carrier is delayed; one owner cannot execute overlapping allocations. No extra optional features before required evidence closes.
