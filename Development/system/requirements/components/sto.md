# STO — Fixture storage and prefetch

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## STO-001

Fixture storage shall validate supported sample format/rate, frame length and provenance before selection and reject malformed or unsupported files without silently resampling.

- **Derivation:** UC-04 → SR-08,SR-11; sources S03.
- **Status:** Source-backed; file formats proposed.
- **Parameters:** P17.
- **Verification:** VT-10.
- **Acceptance:** Known good, unsupported rate, truncated header/data and oversized fixtures tested; supported formats agreed.

## STO-002

SD/host fixture acquisition shall prefetch into bounded processor-owned buffers outside the audio worker, using chunked serialized SPI operations.

- **Derivation:** UC-04 → SR-08,SR-11; sources S03.
- **Status:** Source-backed.
- **Parameters:** P11.
- **Verification:** VT-13,VT-02.
- **Acceptance:** Audio worker performs no filesystem read; worst display/touch/SD contention measured; prefetch pressure bounded.

## STO-003

Mount failure, EOF, read error or fixture starvation shall produce a defined fixture stop/error outcome without formatting the card or interrupting available microphone listening.

- **Derivation:** UC-04,UC-08 → SR-08,SR-09; sources S03,S07.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-10,VT-09.
- **Acceptance:** No implicit format/write and no fabricated samples; explicit source restoration event required after fixture fault.

## STO-004

Fixture metadata shall retain content hash, license/reference, sample representation and evaluation configuration, and the storage service shall not persist microphone clips or patient audio.

- **Derivation:** UC-04,UC-09 → SR-08,SR-10; sources S03,S05.
- **Status:** Derived.
- **Parameters:** —.
- **Verification:** VT-10,VT-11.
- **Acceptance:** Hash/config evidence matches source; SD write trace absent for capture/replay.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
