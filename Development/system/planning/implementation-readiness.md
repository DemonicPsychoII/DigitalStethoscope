# Review decisions and implementation readiness

**Status: review package complete; implementation baseline not yet approved.** This is the boundary
requested: use cases, component allocation, interfaces, detailed behavior and planned verification
exist. Open scientific/hardware/parameter decisions are visible rather than silently fixed in code.
A complete specification draft is not the same as permission to implement unagreed behavior.

## Decision register

All rows are open unless stated otherwise. Nico can edit the proposed resolution directly.

| ID | Decision / conflict | Proposed draft treatment | Blocks |
|---|---|---|---|
| D01 | S04 network outside live vs S03 stress with simultaneous encrypted sending | Follow saved S04; Idle lease, test accidental overlap and radio interference. Mechanism needs review. | NET/CTL handoff and target timing |
| D02 | Startup Idle vs ready/live; button for clip vs BPM-session start | Proposed silent Idle then explicit Start; button captures/cancels clip, touch/shell independently start measurement. | Controller/UI state API approval |
| D03 | Raw int32 capture vs bring-up filtered int16; clip length, replay speed changes | Proposed 5 s raw int32 mono, documented valid-bit alignment, filters reprocess raw clip; agree conversion/duration/continuity. | REC/storage format and memory |
| D04 | S02 3 s window/15–30 s vs bring-up 8 s rolling estimate | Candidate 8 s window/1 s update/30 s session; whole-cycle estimator; median accepted estimates with overlap-aware coverage. Warm-up/weighting open. | BPM session and estimator acceptance |
| D05 | Supported range, error, reference and quality | Candidate 30–200 BPM; max(5 BPM,10% reference), quality ≥0.6/coverage ≥80%; choose corpus/reference/statistic before implementation acceptance. | BPM validation; not diagnostic claim |
| D06 | Murmur/BPM bands and smooth changes | Bring-up 40–800/25–150 Hz and 20 ms are candidates; derive literature response and transient criteria. | DSP coefficient baseline / scientific evaluation |
| D07 | External amplifier/headphone output | Confirm model/gain/safe output level and ≥1 kΩ DAC load; 250 Ω headphones from S01/S03. | Hardware output and volume limits |
| D08 | FHIR server/patient/profile/auth/point/time | R4 HAPI candidate; effectivePeriod for aggregate; stable-ID PUT/readback; approve point coding, precision and trusted-clock assumptions. | NET serialization/deployment |
| D09 | S03 acoustic characterization vs current S05 exclusion | Scope draft follows S05: datasheets/literature plus functional audio only. No measured transfer-chain claim; retain older intention as superseded proposal pending confirmation. | Thesis scope reconciliation |
| D10 | Timing/resource/queue/response margins and soak length | Keep 8 ms/≤4 ms board targets; review P10–P15 capacities/thresholds; candidate 30 min soak. Measure first; priority alone insufficient. | Scheduling and acceptance budgets |
| D11 | Thesis folder/skeleton migration | Separate `coding/thesis-zephyr/` proposed. S04 says old skeleton replaced via PR #15, but this local tree still has it; do not migrate/delete in drafting task. | Implementation placement |
| D12 | MON watchdog and risk-control scope | Class B/SOUP is recorded intent; develop hazards, detection/mute timing and watchdog obligations before claiming safety controls implemented. | Supervision design / standards argument |
| D13 | SD/host fixture formats, maximum size and clock normalization | Candidate mono PCM WAV 16/32-bit 16 kHz, explicit sign/alignment and no hidden resampling; prefetch buffer sizing open. | Fixture adapter API |
| D14 | Continuous BPM vs explicit session | Draft allows independent estimator updates while listening and explicit bounded session aggregation; only completed sessions eligible for send. Confirm heart/listening behavior. | BPM/controller interaction |

## Risks and proposed controls (not a completed ISO 14971 analysis)

| Failure / potential consequence | Proposed controls | Linked requirements / evidence |
|---|---|---|
| Excessive output/transient or incorrect amplifier load | Zero-gain startup, smooth transitions, saturation, approved amplifier/output level | HW-002, LIS-002; VT-03/VT-12 |
| Misleading BPM from S1/S2, noise, stale/missing audio | Whole-cycle estimator, validity/coverage/gap gating, explicit invalid display | BPM-002..006, UI-005; VT-06/VT-09 |
| Wrong patient/test source/time transmitted | Frozen provenance/context, worker-side guards, validated clock/profile | CTL-003, NET-002/003/007; VT-07/VT-08 |
| Duplicate observation after uncertain network response | Stable identity/payload and explicit retry/readback | NET-004/006; VT-07 |
| Audio stalls due to UI/storage/TLS or memory pressure | Bounded independent workers, internal DMA, prefetch, network lease, monitored deadlines | AUD-002..004, STO-002, CTL-005, MON-001/003; VT-02/VT-08/VT-13 |
| Driver initialized but peripheral absent/wrong | Separate readiness/transfer/physical evidence; essential faults mute | MON-002, AUD-005; VT-01/VT-12 |

## Work packages to reach implementation

Estimate with Nico before execution; actual effort and deviations recorded afterward. The estimates
below are proposed remaining review/design effort, not measured effort or a replacement of S05's
320 h thesis budget. Include review corrections and re-verification, as the SW-Basis example teaches.

| Package | Inputs → output / exit condition | Candidate effort |
|---|---|---|
| WP-01 Scope and workflow agreement | sources/use cases/D02,D09,D14 → reviewed product boundary and operator transitions | 3–5 h |
| WP-02 Parameter and evaluation agreement | P04–P09/P14,D04–D06 → corpus/reference, metrics and signed-off candidate parameters | 5–8 h |
| WP-03 Hardware/configuration closure | D07,D08,D13 → amplifier/wiring and private server/time setup plan | 3–5 h; procurement/bench calendar separate |
| WP-04 Architecture/interface review | diagrams/contracts/D01,D03,D10–D12 → ownership, queue and response budgets agreed | 4–6 h |
| WP-05 Verification and risk review | requirements/traceability/tests → acceptance cases and limitations reviewed | 3–5 h |
| WP-06 Corrections and baseline freeze | review findings → consistent requirements/diagrams/test plan; rerender/recheck | 2–4 h |
| Review/meeting buffer | planning + review + documentation overhead not already covered | 4 h |
| Total remaining preparation candidate | no implementation coding included | 24–37 h |

## Implementation sequence after review

1. Create the agreed thesis structure, pure-C contracts and host fixtures; preserve evaluation firmware.
2. Implement controller guards/snapshots and audio source/output; measure block/latency budgets on
   authorized hardware before placing work on two cores.
3. Implement independent analysis and bounded raw capture/replay; verify cancellation and source
   provenance before integrating UI and storage contention.
4. Integrate input/UI/fixture adapters with bounded shared-bus operations; repeat timing/fault tests.
5. Add frozen result/FHIR delivery and exclusive Idle lease; verify semantics, TLS/readback and retries.
6. Evaluate filters/reference metrics; review changes and repeat affected verification.

## Readiness checklist for baseline approval

- [ ] Nico agrees scope/use cases, operator actions and all implementation-blocking D rows.
- [ ] Each P row has an approved value or explicitly deferred dependency with no invented pass criterion.
- [ ] Hardware amplifier and unconfirmed carrier wiring have an authorized verification plan.
- [ ] Interfaces, ownership, failure outcomes and timing/resource budgets reviewed.
- [ ] Every component requirement has an agreed verification case and reproducible evidence format.
- [ ] Classification/SOUP/risk claims are separated from demonstrated compliance and device safety.
- [ ] Estimate includes familiarization, meetings, documentation, reviews and correction/test iterations.
- [ ] Specification, diagrams, detailed design and traceability agree after review edits.

This package documents an unapproved implementation baseline. No board/server changes,
firmware changes, flashing, serial access or device-network operations are included.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
