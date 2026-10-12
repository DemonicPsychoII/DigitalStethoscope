# INP — Physical and touch input adapters

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## INP-001

Input adapters shall emit typed, timestamped control events only after a button or SP3T position has become stable, with one event for each accepted transition.

- **Derivation:** UC-02,UC-03 → SR-03; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** P10.
- **Verification:** VT-04.
- **Acceptance:** Bounce/contact-sequence injection yields one press or transition; report invalid zero/multiple contacts without replacing last valid selection.

## INP-002

GPIO/touch interrupt handlers shall only acknowledge and signal deferred work; they shall not process audio, access SD, redraw display or perform network I/O.

- **Derivation:** UC-02 → SR-03; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-04,VT-02.
- **Acceptance:** Call-path inspection and interrupt timing trace under bounce/load.

## INP-003

The potentiometer adapter shall use calibrated ADC1 values, clamp the normalized volume request to 0–100%, and retain a defined safe value when acquisition fails.

- **Derivation:** UC-02,UC-09 → SR-03; sources S03,S07.
- **Status:** Derived.
- **Parameters:** P10,P16.
- **Verification:** VT-04.
- **Acceptance:** Sweep endpoints/out-of-range/read errors; UI/controller receive bounded values; failure policy and smoothing parameters recorded.

## INP-004

When the control queue is full, input adapters shall preserve the latest stable switch/pot state for reconciliation and shall explicitly report an unaccepted action rather than silently replaying a stale button action.

- **Derivation:** UC-02,UC-08 → SR-03,SR-09; sources S03,S04.
- **Status:** Source-backed + derived overflow policy.
- **Parameters:** P11.
- **Verification:** VT-04,VT-09.
- **Acceptance:** Queue saturation recovers effective stable settings; no duplicate capture; rejected actions visible.

## INP-005

The button adapter shall emit a distinct long-press event once the button has been held stably for at least the configured long-press time, and shall then suppress the ordinary press for that actuation.

- **Derivation:** UC-10 → SR-12; sources S05; [12 October decisions](../../planning/mvp-decisions-2026-10-12.md).
- **Status:** Owner decision 12 October; time proposed.
- **Parameters:** P10,P21.
- **Verification:** VT-04,VT-14.
- **Acceptance:** Press durations just below/above the threshold, bounce at release and queue saturation produce exactly one press or one long-press event, never both.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
