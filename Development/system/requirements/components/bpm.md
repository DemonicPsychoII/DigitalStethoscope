# BPM — Heart-rate analysis and session aggregation

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## BPM-001

BPM analysis shall operate on original-rate audio through its own configured filter, independent of audible filter, volume and replay speed.

- **Derivation:** UC-05 → SR-05; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** P08.
- **Verification:** VT-06.
- **Acceptance:** Identical estimator input/result timeline across listening-condition changes.

## BPM-002

The estimator shall evaluate whole cardiac-cycle periodicity over the agreed window/range rather than treating adjacent high-amplitude S1/S2 peaks as separate beats.

- **Derivation:** UC-05 → SR-05; sources S03.
- **Status:** Source-backed; estimator parameters open.
- **Parameters:** P05,P06.
- **Verification:** VT-06.
- **Acceptance:** Synthetic and annotated double-sound, variable-amplitude and harmonic-ambiguity cases; no systematic 2×/0.5× error.

## BPM-003

The estimator shall mark windows invalid for discontinuity, insufficient samples, clipping or inadequate periodicity, expose the reason and never substitute the previous valid BPM as a new estimate.

- **Derivation:** UC-05,UC-08 → SR-05,SR-09; sources S03,S04.
- **Status:** Source-backed; thresholds open.
- **Parameters:** P07.
- **Verification:** VT-06,VT-09.
- **Acceptance:** Gap, silence, noise, clipping and stale-estimate injection; invalid flag/reason/time asserted.

## BPM-004

On session completion, BPM analysis shall aggregate accepted windows using a declared rule, count overlapping windows once in temporal coverage, and freeze result validity, value, interval, source, patient, point and analysis settings.

- **Derivation:** UC-05 → SR-05; sources S03.
- **Status:** Source-backed; aggregation design derived.
- **Parameters:** P05,P07,P18.
- **Verification:** VT-06.
- **Acceptance:** Reference aggregation cases; coverage uses union of accepted intervals; missing coverage returns invalid result.

## BPM-005

For the approved corpus and reference, valid heart-rate results shall meet the agreed error criterion over the supported BPM range, with invalid fraction and failure cases reported separately.

- **Derivation:** UC-05 → SR-05; sources S03,S06.
- **Status:** Open acceptance target.
- **Parameters:** P06,P07.
- **Verification:** VT-06.
- **Acceptance:** Per-case error, bias/MAE and coverage by rate/noise strata; agree reference and statistic before scoring.

## BPM-006

Session cancellation or context change shall discard incomplete aggregation and prevent finalization or sending for that cancelled session ID.

- **Derivation:** UC-05,UC-08 → SR-05,SR-09; sources S03.
- **Status:** Derived.
- **Parameters:** —.
- **Verification:** VT-06,VT-09.
- **Acceptance:** Cancel races including late finalizer completion; no old result accepted as a new session.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
