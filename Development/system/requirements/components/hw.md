# HW — Hardware integration

**Status: local review draft.** “Source-backed” identifies origin, not formal approval. Acceptance with open parameters remains conditional. Interface names are proposed contracts, not existing APIs.

## HW-001

The hardware integration shall retain the ESP32-S3 N16R8, INMP441 I2S0 input, PCM5102A I2S1 output and the maintained carrier pin map.

- **Derivation:** UC-01,UC-02 → SR-01,SR-11; sources S01,S03,S07.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-12.
- **Acceptance:** Inspect schematic/carrier/overlay and continuity evidence; record revisions and differences before energizing.

## HW-002

The audio output assembly shall connect the PCM5102A line output to an external headphone amplifier and load each DAC output by at least 1 kΩ rather than directly driving headphones.

- **Derivation:** UC-02 → SR-02,SR-11; sources S01,S03.
- **Status:** Source-backed; amplifier open.
- **Parameters:** P16.
- **Verification:** VT-12.
- **Acceptance:** Approved amplifier/gain, load measurement and output-level evidence; digital gain is not a substitute.

## HW-003

The hardware integration shall give display, touch and SD separate chip selects on shared SPI2 and preserve ADC1 volume input, reserved PSRAM pins and noncompeting GPIO38/48 use.

- **Derivation:** UC-04,UC-09 → SR-11; sources S03,S07.
- **Status:** Source-backed.
- **Parameters:** —.
- **Verification:** VT-12,VT-13.
- **Acceptance:** Overlay/schematic inspection plus simultaneous bus trace; verify speed-switch contact truth table and carrier revision.

## HW-004

The hardware documentation shall identify chestpiece coupling, microphone low-frequency limitations, supply and DAC straps, and distinguish acoustic acquisition from fixture bypass.

- **Derivation:** UC-02,UC-04 → SR-02,SR-08; sources S01,S03,S05.
- **Status:** Derived scope reconciliation.
- **Parameters:** —.
- **Verification:** VT-12,VT-10.
- **Acceptance:** Documentation and audible-path target evidence; do not claim restored sub-band response or acoustic-chain characterization excluded by S05.

Created by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
