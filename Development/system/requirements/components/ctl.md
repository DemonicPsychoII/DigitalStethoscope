# CTL — Application controller

Current owner decisions and numeric proposals: [11 October MVP decisions](../../planning/mvp-decisions-2026-10-11.md). Older source snapshots and evaluation behavior remain historical evidence.

**Status: current owner behavior decisions with proposed numeric acceptance.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## CTL-001

The controller shall be the sole writer of mode, source, point, patient context, filter/speed settings and workflow state; other components shall request changes by events and read consistent snapshots.

- **Derivation:** UC-01,UC-02,UC-09 → SR-01,SR-03; sources S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-04.
- **Acceptance:** Host concurrency/state tests and dependency review; no shell/UI direct mutable mode writes.

## CTL-002

The controller shall apply the last accepted stable filter/speed transition from physical, touch or shell input and shall not let unchanged physical contacts overwrite a later accepted command.

- **Derivation:** UC-02 → SR-03; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** P10.
- **Verification:** VT-04.
- **Acceptance:** Interleave events including equal timestamps; serialized arrival order breaks ties; observe effective setting and snapshot.

## CTL-003

During acquisition, finalization and delivery, the controller shall reject mode/source/patient/point changes with a normal fault and preserve frozen session context. A new session receives a new generation so late completions cannot change current state.

- **Derivation:** UC-03,UC-05,UC-08 → SR-04,SR-05,SR-09; sources S03.
- **Status:** Derived.
- **Parameters:** —.
- **Verification:** VT-04,VT-09.
- **Acceptance:** Race rejected changes and cancellation with completion; context remains unchanged, no mixed identity or new-result relabelling.

## CTL-004

Accept entry to Lung only outside a session; reject an in-session mode change without mutation. On accepted entry invalidate current BPM, force Raw live 1× and reject capture/replay/measurement/send requests until Heart is selected.

- **Derivation:** UC-07 → SR-07; sources S03,S05.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-04,VT-06,VT-07.
- **Acceptance:** Every guarded request rejected in Lung; volume remains available; old completed results not sent in Lung.

## CTL-005

The controller shall grant network work only in Idle with no active capture, replay or measurement; a Start request during analysis or sending shall be rejected as Busy with visible activity, without cancellation or a queued start. Audio resumes only on a fresh Start after the lease is released.

- **Derivation:** UC-06,UC-08 → SR-06,SR-09; sources S04.
- **Status:** Source-backed + derived lease contract.
- **Parameters:** P13,P19.
- **Verification:** VT-08.
- **Acceptance:** Race start/stop/send/time sync/connect; traces show no exclusive states overlap; failed cancellation does not grant audio permission.

## CTL-006

The MVP controller shall expose ordinary Start/Stop and separate normal-error acknowledgement. Stop before 15 seconds cancels measurement. During analysis/sending Start is Busy; Device Alarm recovery requires full restart. Capture/replay commands are optional extensions; retry is excluded from MVP.

- **Derivation:** UC-01,UC-03,UC-05 → SR-01,SR-04,SR-05; sources S02,S03.
- **Status:** Proposed workflow.
- **Parameters:** P20.
- **Verification:** VT-04,VT-05.
- **Acceptance:** Transition table covers each event/state and rejection reason; review D02/P20 before implementation.

## CTL-007

The controller shall accept the hotspot long press only in Idle, hold a Portal state with an exclusive network lease until confirmation, cancel or timeout, reject Start and session commands while in Portal, and own the local patient assignment: set only from a matching server readback, frozen into each session, and cleared on failed assignment.

- **Derivation:** UC-05,UC-10 → SR-03,SR-12; sources S05; [12 October decisions](../../planning/mvp-decisions-2026-10-12.md).
- **Status:** Owner decision 12 October; timeout and assignment lifetime proposed.
- **Parameters:** P19,P21.
- **Verification:** VT-04,VT-14.
- **Acceptance:** Long press in every state; Start during Portal; timeout/cancel leaves assignment unchanged; failed readback leaves the device unassigned; a session keeps its frozen patient after reassignment.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
