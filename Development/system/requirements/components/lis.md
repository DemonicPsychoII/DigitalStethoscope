# LIS — Listening DSP and output

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## LIS-001

Listening DSP shall provide Raw, Murmur and BPM-emphasis filter paths, applying no band filter in Raw and selecting listening coefficients independently of analysis coefficients.

- **Derivation:** UC-02,UC-04 → SR-02,SR-08; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** P08.
- **Verification:** VT-03,VT-10.
- **Acceptance:** Impulse/sweep/known waveform checks against specified coefficient response; Raw unity before gain; identical input in comparisons.

## LIS-002

Listening DSP shall smooth accepted filter and gain transitions and saturate output before integer conversion, including extreme input and volume settings.

- **Derivation:** UC-02 → SR-02; sources S03,S07.
- **Status:** Source-backed; smoothing open.
- **Parameters:** P09,P16.
- **Verification:** VT-03.
- **Acceptance:** Finite/bounded output; no overflow/wrap; crossfade/ramp response and clipping count match approved specification.

## LIS-003

Changes to listening filter, gain or replay speed shall not alter the sample clock or data supplied to the BPM analysis path.

- **Derivation:** UC-02,UC-05 → SR-02,SR-05; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-06.
- **Acceptance:** Replay/volume/filter changes leave estimator input sample count/values invariant for the same microphone stream.

## LIS-004

The live 1× signal path shall achieve end-to-end latency below the approved live target, including transport buffering, filtering and DAC/analog delay.

- **Derivation:** UC-02 → SR-02; sources S03,S06.
- **Status:** Source-backed target.
- **Parameters:** P03.
- **Verification:** VT-02.
- **Acceptance:** Electrical/acoustic latency measurement with fixture and timestamped setup; report worst/percentiles; <10 ms is stretch, not required baseline.

## LIS-005

The core filtering, gain, estimator and replay algorithms shall be callable as pure C without Zephyr headers, hardware access, network I/O or heap allocation in the per-block processing path.

- **Derivation:** UC-04 → SR-08; sources S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-03,VT-10.
- **Acceptance:** Host compilation of production core and dependency review; same coefficient/config IDs as target.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
