# Review decisions and implementation readiness

**Status: review package complete; implementation baseline not yet approved.** This is the boundary
requested: use cases, component allocation, interfaces, detailed behavior and planned verification
exist. Open scientific/hardware/parameter decisions are visible rather than silently fixed in code.
A complete specification draft is not the same as permission to implement unagreed behavior.

## Decision register

The original register below is historical preparation context. [11 October owner decisions](mvp-decisions-2026-10-11.md) supersede D02/D03/D08/D12/D14 workflow and scope proposals; [13 October decisions](mvp-decisions-2026-10-13.md) settle the firmware layer layout; the [14 October decisions](mvp-decisions-2026-10-14.md) close D05, D07, D09, D11 and D13 as marked. Numeric criteria remain proposals; [the component timeline](mvp-implementation-timeline.md) replaces the old audio-first implementation sequence.

| ID | Decision / conflict | Proposed draft treatment | Blocks |
|---|---|---|---|
| D01 | S04 network outside live vs S03 stress with simultaneous encrypted sending | Follow saved S04; Idle lease, test accidental overlap and radio interference. Mechanism needs review. | NET/CTL handoff and target timing |
| D02 | Startup Idle vs ready/live; button for clip vs BPM-session start | **Decided:** silent Idle, explicit Start (REQ-01); clip/replay and touch removed from the MVP. | — |
| D03 | Raw int32 capture vs bring-up filtered int16; clip length, replay speed changes | **Removed:** capture/replay optional and out of the MVP (14 October). | — |
| D04 | S02 3 s window/15–30 s vs bring-up 8 s rolling estimate | Candidate 8 s window/1 s update/30 s session; whole-cycle estimator; median accepted estimates with overlap-aware coverage. Warm-up/weighting open. | BPM session and estimator acceptance |
| D05 | Supported range, error, reference and quality | **Decided 14 October:** ±5 BPM or ±10 % against pulse oximeter/smartwatch (REQ-06); no fixed quality threshold. Host recordings/reference decided during the Wi-Fi/FHIR phase. | BPM validation; not diagnostic claim |
| D06 | Murmur/BPM bands and smooth changes | Bring-up 40–800/25–150 Hz are candidates; chosen after the device works in the filter study (TICKET-189), which also feeds each listening filter into BPM detection. | DSP coefficient baseline / scientific evaluation |
| D07 | External amplifier/headphone output | **Closed 14 October:** the device ends at the DAC line output; the amplifier is outside the project scope. | — |
| D08 | FHIR server/patient/profile/auth/point/time | R4 HAPI candidate; `effectiveDateTime` = interval end and conditional create/readback (decided 12 October); approve point coding, precision and trusted-clock assumptions. Patient: decided 12 October via hotspot portal and `Device.patient` ([decisions](mvp-decisions-2026-10-12.md)). | NET serialization/deployment |
| D09 | S03 acoustic characterization vs current S05 exclusion | **Closed:** follows S05; no acoustic transfer-chain measurement. | — |
| D10 | Timing/resource/queue/response margins and soak length | Keep 8 ms/≤4 ms board targets; review P10–P15 capacities/thresholds; candidate 30 min soak. Measure first; priority alone insufficient. | Scheduling and acceptance budgets |
| D11 | Thesis folder/skeleton migration | **Decided 14 October:** new firmware lives in [`coding/app/`](../coding/app/README.md); the evaluation firmware stays separate. Layer layout per [13 October](mvp-decisions-2026-10-13.md): L0 = Zephyr, L1 = hardware adapters and pure C libraries, L2 = orchestration. | — |
| D12 | MON watchdog and risk-control scope | Class B/SOUP is recorded intent; develop hazards, detection/mute timing and watchdog obligations before claiming safety controls implemented. | Supervision design / standards argument |
| D13 | Host test-recording formats and resampling | **Decided 14 October:** chosen during the Wi-Fi/FHIR phase; on-device SD fixtures removed from the MVP. | Host BPM tests |
| D14 | Continuous BPM vs explicit session | Draft allows independent estimator updates while listening and explicit bounded session aggregation; only completed sessions eligible for send. Confirm heart/listening behavior. | BPM/controller interaction |

## Risks and proposed controls (not a completed ISO 14971 analysis)

| Failure / potential consequence | Proposed controls | Linked requirements / checks |
|---|---|---|
| Loud output or transient at startup or on changes | Silent startup, smooth transitions, saturation | REQ-01, REQ-04; VT-03 |
| Misleading BPM from S1/S2, noise, stale/missing audio | Whole-cycle estimator, coverage/gap rules, error instead of a number | REQ-06, REQ-08; VT-06/VT-09 |
| Wrong patient or time transmitted | Frozen session context, assignment readback and pre-send check, validated clock | REQ-09, REQ-12; VT-07/VT-14 |
| Wrong patient assigned without a device display, or assignment left from the previous patient | Explicit phone confirmation with name/birth date, readback before use, session freeze, pre-send server comparison, no assignment → no send; assignment lifetime open | REQ-12; VT-14 |
| Patient data or credentials exposed through the hotspot | WPA2 with per-device passphrase, Idle-only with timeout, minimal fields, write-only password, no logs | REQ-11, REQ-12; VT-14/VT-11 |
| Duplicate or lost result after a lost response | Conditional create with stable identifier, up to 3 retries, readback | REQ-10; VT-07 |
| Audio stalls due to TLS or memory pressure | Bounded workers, internal DMA, network lease, monitored deadlines | REQ-02, REQ-05; VT-02/VT-08 |
| Peripheral absent or failed | Startup checks; essential faults mute until restart | REQ-13; VT-01/VT-12 |

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

Follow the [component timeline](mvp-implementation-timeline.md): release/contracts → Wi-Fi/time → HTTPS/FHIR/error contract → device transport evidence → controller/alarm states → carrier checks → audio → independent DSP → streaming BPM/reference → complete-session FHIR → timing/fault verification. Saved raw audio/replay remains optional. Functional dependency links and one-person calendar sequencing are recorded separately; hardware/equipment prerequisites remain explicit.

## Readiness checklist for baseline approval

- [ ] Nico agrees scope/use cases, operator actions and all implementation-blocking D rows.
- [ ] Each P row has an approved value or explicitly deferred dependency with no invented pass criterion.
- [ ] Unconfirmed carrier wiring has an authorized verification plan.
- [ ] Interfaces, ownership, failure outcomes and timing/resource budgets reviewed.
- [ ] Every system requirement (REQ-01…REQ-14) has a test Nico can run and a pass criterion.
- [ ] Classification/SOUP/risk claims are separated from demonstrated compliance and device safety.
- [ ] Estimate includes familiarization, meetings, documentation, reviews and correction/test iterations.
- [ ] Specification, diagrams and detailed design agree after review edits.

This package documents an unapproved implementation baseline. No board/server changes,
firmware changes, flashing, serial access or device-network operations are included.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
