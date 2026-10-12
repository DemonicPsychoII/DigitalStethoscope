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

## UI-006

The hotspot portal shall show the patient list with only name, birth date and patient ID plus the list load time, require explicit confirmation of one patient, and offer a Wi-Fi page that validates and stores credentials without displaying them again. The activity LED shall show a distinct pattern while the hotspot is open.

- **Derivation:** UC-10 → SR-12; sources S05; [12 October decisions](../../planning/mvp-decisions-2026-10-12.md).
- **Status:** Owner decision 12 October; LED pattern and list size proposed.
- **Parameters:** P21.
- **Verification:** VT-14.
- **Acceptance:** Page inspection for empty/full/failed list and stale load time; no assignment without confirmation; stored password never returned in any response; LED pattern distinguishable from activity.

## UI-007

The hotspot shall use WPA2 with a per-device passphrase kept outside source code, run only in Portal state, close after the configured timeout, accept a bounded number of clients and requests, and keep credentials and patient data out of logs.

- **Derivation:** UC-10 → SR-10,SR-12; sources S05,S06; [12 October decisions](../../planning/mvp-decisions-2026-10-12.md).
- **Status:** Derived security constraint; portal login and passphrase provisioning open.
- **Parameters:** P21.
- **Verification:** VT-14,VT-11.
- **Acceptance:** Open/WEP join refused; hotspot down outside Portal and after timeout; oversized/malformed requests rejected without crash; log inspection shows no credentials or patient fields.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
