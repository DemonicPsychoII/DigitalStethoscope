# MON — Monitoring and evidence

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## MON-001

Monitoring shall count RX/TX stalls, dropped blocks, deadline misses, clipping, analysis gaps and queue saturation with interval/configuration identity.

- **Derivation:** UC-02,UC-08 → SR-02,SR-09,SR-10; sources S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-02,VT-09,VT-11.
- **Acceptance:** Each injected anomaly increments the relevant counter without blocking the audio worker.

## MON-002

Monitoring shall distinguish driver readiness, accepted transfer and physically verified operation and shall never promote evidence level solely because initialization succeeded.

- **Derivation:** UC-01,UC-08,UC-09 → SR-01,SR-09,SR-10; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-01,VT-11.
- **Acceptance:** Unconnected peripheral case remains readiness/transfer evidence until an explicit physical test record exists.

## MON-003

Monitoring shall report measured stack/heap watermarks and separate internal DMA/processing memory from PSRAM clip/fixture storage, with bounded diagnostic overhead.

- **Derivation:** UC-02,UC-09 → SR-02,SR-10; sources S03,S04.
- **Status:** Source-backed; resource margins proposed.
- **Parameters:** P15.
- **Verification:** VT-02,VT-11.
- **Acceptance:** Linker/map and load-run resource evidence; proposed margin reviewed; no reliance on nominal PSRAM alone.

## MON-004

Supervision shall detect stalled required workers and request a muted fault/recovery outcome under an agreed watchdog policy without falsely treating invalid BPM or an optional peripheral failure as whole-system failure.

- **Derivation:** UC-08 → SR-09; sources S03,S04.
- **Status:** Derived watchdog/recovery design.
- **Parameters:** P12.
- **Verification:** VT-09.
- **Acceptance:** Stall each worker independently; exercise bounded recovery attempts; watchdog timeouts remain D12 until reviewed.

## MON-005

Evaluation evidence shall record software/build/config IDs, source hash, carrier/device identity, parameters, setup, reference, actual results, reviewer and anomalies and require re-verification after relevant changes.

- **Derivation:** UC-04,UC-09 → SR-08,SR-10; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-11.
- **Acceptance:** Completed report can reproduce each comparison; reviewed integer/filter/config changes rerun affected tests.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
