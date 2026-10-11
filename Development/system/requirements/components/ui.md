# UI — Display, LED and shell surface

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## UI-001

Display/UI shall render a consistent state snapshot including mode/source, effective filter/speed/volume, point, clip/measurement progress, BPM validity and delivery outcome without blocking input or audio.

- **Derivation:** UC-01,UC-02,UC-05,UC-06 → SR-01,SR-03,SR-10; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** P10.
- **Verification:** VT-04,VT-13.
- **Acceptance:** Slow/full redraw injection does not block controller/audio; displayed state generation is consistent.

## UI-002

The activity LED shall be on while capture, replay or measurement acquisition is active and off when none is active; overlapping activities shall not turn it off prematurely.

- **Derivation:** UC-03,UC-05,UC-08 → SR-03,SR-09; sources S03.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-04,VT-05.
- **Acceptance:** State/LED truth table across overlapping sessions and cancellation; separate delivery status on display.

## UI-003

Touch and shell controls shall validate values and submit the same typed events as physical controls rather than directly writing state; touch calibration and brightness shall remain separate from volume.

- **Derivation:** UC-02,UC-09 → SR-03; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-04.
- **Acceptance:** Out-of-bounds coordinates, invalid settings and calibration cases; equivalent event paths.

## UI-004

Display transfers shall be bounded/chunked on shared SPI and display/touch failure shall leave physical controls and microphone listening available with degraded status.

- **Derivation:** UC-04,UC-08 → SR-09,SR-11; sources S03.
- **Status:** Source-backed.
- **Parameters:** P10.
- **Verification:** VT-09,VT-13.
- **Acceptance:** Bus trace and injected absent display/touch; no full-frame wait in audio or input path.

## UI-005

The UI shall clearly label test sources, invalid/stale BPM and research-only output, and shall display a named point mapping rather than implying an index is an inferred anatomical location.

- **Derivation:** UC-04,UC-05,UC-09 → SR-08,SR-10; sources S03,S07.
- **Status:** Derived.
- **Parameters:** P18.
- **Verification:** VT-04,VT-11.
- **Acceptance:** Screens/shell snapshots for test/lung/invalid states and configured anatomical labels.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
