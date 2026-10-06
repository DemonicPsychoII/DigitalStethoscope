# REC — Volatile clip capture and replay

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## REC-001

Clip capture shall store original-rate unfiltered samples before listening gain in a preallocated bounded volatile buffer with clip/source/configuration metadata and explicit capacity.

- **Derivation:** UC-03 → SR-04; sources S03.
- **Status:** Proposal; recording policy open.
- **Parameters:** P04.
- **Verification:** VT-05.
- **Acceptance:** Known waveform capture independent of listening settings; max frames and raw conversion verified; no patient SD write.

## REC-002

On capture capacity completion, replay shall process the completed clip through the selected listening filter at 1×, 0.75× or 0.5× while new microphone samples remain available to analysis.

- **Derivation:** UC-03 → SR-04; sources S03.
- **Status:** Source-backed workflow.
- **Parameters:** P04,P14.
- **Verification:** VT-05,VT-06.
- **Acceptance:** Replay does not feed slowed samples to BPM; at end controller returns Live 1×.

## REC-003

Slow replay shall use a bounded pitch-preserving method and shall produce an output duration corresponding to clip_duration/speed without an ever-growing live backlog.

- **Derivation:** UC-03 → SR-04; sources S03,S06.
- **Status:** Source-backed; acceptance open.
- **Parameters:** P14.
- **Verification:** VT-05.
- **Acceptance:** Duration and pitch/artifact corpus evaluated for each speed; bounds approved before pass/fail.

## REC-004

Cancellation, stop or source/mode change shall release clip/replay ownership, clear incomplete clip validity and prevent any cancelled generation from restarting playback.

- **Derivation:** UC-03,UC-08 → SR-04,SR-09; sources S03.
- **Status:** Derived.
- **Parameters:** —.
- **Verification:** VT-05,VT-09.
- **Acceptance:** Cancel at first/last block and during overlap-add; bounded resources; stale handle rejected.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
