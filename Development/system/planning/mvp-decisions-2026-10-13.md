# Architecture decisions — firmware layer structure, 13 October 2026

Nico's answers in T3 thread `d5e44f69-2ecc-4a3e-917b-31a7b084c12b` settle the thesis
firmware layer structure in [`coding/app/`](../coding/app/README.md) and close the layout part of
D11 in the [decision register](implementation-readiness.md#decision-register). They replace the
capability-based service split in [detailed design](../design/interfaces-and-behavior.md#static-dependency-and-module-map)
(audio, input, storage, measurement and delivery services over separate L0 adapters). Earlier
workflow, FHIR and patient-assignment decisions are unchanged. The skeleton reserves files only; no
behavior is implemented.

## Confirmed decisions

- **L0 is Zephyr.** Zephyr drivers, DMA, interrupts and the devicetree board overlay form L0.
  The project adds no own driver or HAL layer; `L0_platform/` stays empty apart from its README.
- **L1 is the layer between the firmware and the driver calls.** It contains two kinds of module:
  - Thin hardware adapters over Zephyr driver APIs: `L1_I2S` (microphone RX and DAC TX in one
    module, because one owner must keep the block cadence of both ends), `L1_WIFI` (Wi-Fi, TLS,
    time) and `L1_PHYSICALINTERFACE` (buttons, switches, potentiometer and LEDs).
  - Pure C libraries without Zephyr headers: `L1_FILTER`, `L1_BPM` (envelope, autocorrelation,
    aggregation) and `L1_FHIR` (Observation serialization). They are stateless; each caller owns
    its own instance, so listening and BPM analysis filters stay independent.
- **L2 orchestrates.**
  - `L2_CONTROL` is the single writer of mode state and grants the exclusive network lease.
  - `L2_AUDIO` runs the audio path through `L1_I2S` and `L1_FILTER`. It executes `AudioCommand`s
    from CONTROL and never writes mode state.
  - `L2_COMMUNICATION` orchestrates delivery: `L1_FHIR` builds the message and `L1_WIFI` sends it.
    It is the only path to a send, acts only under the CONTROL lease, and enforces the
    test-source send prohibition. The hotspot portal handler belongs here.
  - `L2_SHELL` reads back data and sends commands only through CONTROL: typed control events in,
    `StateSnapshot` copies out. It never calls services directly.
- **Optional parts are not in the skeleton yet:** display/UI, touch, SD storage, an SPI service and
  capture/slower replay (WSOLA). Zephyr's SPI driver already serializes bus access, so no SPI
  service is planned; bus timing matters again once the display returns.
- **File template and naming.** Every `.c` / `.h` follows the project template (copyright banner,
  Doxygen group, fixed section blocks). Doxygen groups and include guards carry the layer prefix
  without underscore: `L1I2S` / `L1I2S_H`, `L2CONTROL` / `L2CONTROL_H`. Modules outside the
  layers use `MONITOR`, `COMMONTYPES` and `COMMONMAIN`.
- **Manual builds.** [`coding/tools/build-firmware.ps1`](../coding/tools/build-firmware.ps1) builds
  the app (default) or the bring-up firmware with the pinned toolchain. It never flashes.

## Proposed, pending confirmation

- **BPM worker.** BPM runs in its own worker thread owned by `L2_AUDIO`, fed by copies in a fixed
  analysis pool, so a stalled BPM worker cannot pin I2S RX buffers.
- **Alarm indication.** LEDs are mandatory, not part of the optional UI. `L1_PHYSICALINTERFACE`
  drives them; CONTROL decides what they show, including the latched Device Alarm.
- **Entry point.** `common/main.c` is reserved for startup. The built entry point remains the root
  `main.c` until startup is implemented; only one of them may define `main()`.

## Consequences

- The send-ban control moves from Services to `L2_COMMUNICATION`; MON still observes it. The
  [risk row](implementation-readiness.md#risks-and-proposed-controls-not-a-completed-iso-14971-analysis)
  "Wrong patient/test source/time transmitted" keeps its NET requirement trace; NET is now
  realized by `L2_COMMUNICATION` with `L1_FHIR` and `L1_WIFI`.
- Logical components in detailed design (INP, CTL, AUD, LIS, REC, BPM, STO, UI, NET, MON) and
  their requirement IDs stay valid. Detailed design maps them to the new modules.
- Host tests in `tests/host/` target the L1 libraries only.

Created by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
