# AUD — Audio source and block transport

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## AUD-001

The audio source adapter shall convert INMP441 left-channel signed 24-bit data in 32-bit stereo slots into normalized signed mono blocks at 16 kHz, retaining source, sample index, sequence and valid-frame count.

- **Derivation:** UC-02,UC-04 → SR-02,SR-08; sources S03,S07.
- **Status:** Source-backed.
- **Parameters:** P01.
- **Verification:** VT-02,VT-10.
- **Acceptance:** Known positive/negative extrema and channel pattern; no sign/alignment error; monotonically indexed 128-frame blocks.

## AUD-002

Audio transport shall allocate I2S DMA buffers and descriptors in suitable internal memory, prime TX with silence, and duplicate mono output to both DAC channels.

- **Derivation:** UC-01,UC-02 → SR-01,SR-02; sources S03,S07.
- **Status:** Source-backed.
- **Parameters:** P11,P15.
- **Verification:** VT-01,VT-02.
- **Acceptance:** Map/runtime memory inspection and digital I2S trace; no PSRAM DMA block; stereo channels equal.

## AUD-003

The complete audio critical path shall meet each 8 ms block deadline and the planned ≤4 ms execution budget, without network, filesystem or display waits.

- **Derivation:** UC-02 → SR-02; sources S03,S04.
- **Status:** Source-backed target.
- **Parameters:** P01,P02.
- **Verification:** VT-02.
- **Acceptance:** Instrument RX-ready to TX-submit CPU time plus blocking/scheduling delays; worst observed under defined load and soak, misses counted; margins not inferred from averages.

## AUD-004

Audio fan-out shall continue listening if analysis cannot accept a block and shall mark the analysis discontinuity so the BPM window is reset or invalidated.

- **Derivation:** UC-02,UC-05 → SR-02,SR-05; sources S03,S04.
- **Status:** Source-backed.
- **Parameters:** P11.
- **Verification:** VT-06,VT-09.
- **Acceptance:** Stall BPM/overflow analysis queue; listening progresses; no accepted estimate spans an unreported gap.

## AUD-005

On microphone/DAC transport failure, the audio worker shall output silence or stop TX, cancel active acquisition and report a fault; restarting shall require explicit bounded recovery.

- **Derivation:** UC-02,UC-08 → SR-02,SR-09; sources S03.
- **Status:** Source-backed + proposed response bound.
- **Parameters:** P12.
- **Verification:** VT-09.
- **Acceptance:** Injected RX/TX failure produces mute within the agreed bound after detection; detection time measured separately.

## AUD-006

Source changes shall occur at a block boundary, flush old source buffers and reset source-dependent DSP/analysis state before publishing blocks with the new generation.

- **Derivation:** UC-02,UC-04 → SR-02,SR-08; sources S03.
- **Status:** Derived.
- **Parameters:** —.
- **Verification:** VT-10,VT-09.
- **Acceptance:** Alternate microphone/fixture mid-window; no mixed-source result or wrong provenance.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
