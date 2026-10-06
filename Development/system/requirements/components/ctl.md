# CTL — Application controller

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

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

On mode/source/patient/point changes during acquisition, the controller shall cancel the affected incomplete session and tag subsequent commands with a new generation so late completions cannot change current state.

- **Derivation:** UC-03,UC-05,UC-08 → SR-04,SR-05,SR-09; sources S03.
- **Status:** Derived.
- **Parameters:** —.
- **Verification:** VT-04,VT-09.
- **Acceptance:** Race cancellation with block/result completion; no mixed context, stale replay or new-result relabelling.

## CTL-004

On entry to Lung, the controller shall cancel clip/measurement activity, invalidate current BPM, force Raw live 1× and reject capture/replay/measurement/send requests until Heart is selected.

- **Derivation:** UC-07 → SR-07; sources S03,S05.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-04,VT-06,VT-07.
- **Acceptance:** Every guarded request rejected in Lung; volume remains available; old completed results not sent in Lung.

## CTL-005

The controller shall grant network work only in Idle with no active capture, replay or measurement; a listening-start request shall wait for network cancellation/completion acknowledgement before audio resumes.

- **Derivation:** UC-06,UC-08 → SR-06,SR-09; sources S04.
- **Status:** Source-backed + derived lease contract.
- **Parameters:** P13,P19.
- **Verification:** VT-08.
- **Acceptance:** Race start/stop/send/time sync/connect; traces show no exclusive states overlap; failed cancellation does not grant audio permission.

## CTL-006

The controller shall expose distinct start/stop listening, capture/cancel clip, start/cancel measurement and retry commands, and shall map the physical button to capture from Live and cancel from Capture/Replay.

- **Derivation:** UC-01,UC-03,UC-05 → SR-01,SR-04,SR-05; sources S02,S03.
- **Status:** Proposed workflow.
- **Parameters:** P20.
- **Verification:** VT-04,VT-05.
- **Acceptance:** Transition table covers each event/state and rejection reason; review D02/P20 before implementation.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
