# Thesis firmware — layer structure

Target structure for the thesis firmware on Zephyr (ESP32-S3). It replaces the
earlier empty skeleton (`L0HAL`, `L1RTE`, `L2MOD`, `L2MON`). The bring-up and
evaluation firmware in `../bringup-zephyr` stays as it is; code moves here when it
becomes thesis firmware.

Decision and alternatives: Excalidraw board "Software Architecture — Options and
Decision" on the home-lab whiteboard.

| Folder | Layer | Contents | May depend on |
|---|---|---|---|
| `L2_application/` | L2 Application | controller (mode state machine, single writer of mode state), UI, shell | L1, L0, `common` |
| `L1_services/` | L1 Services | audio pipeline, BPM analysis, storage, network/FHIR; owns the pre-send source check | L0, `dsp_core`, `common` |
| `L1_services/dsp_core/` | L1, pure C | filters, envelope, autocorrelation, WSOLA | `common` only |
| `L0_platform/` | L0 Platform | thin adapters over Zephyr drivers and devicetree | Zephyr, `common` |
| `MON/` | cross-cutting | runtime self-monitoring as risk control | all layers (read-only) |
| `common/` | — | shared types (`AudioBlock`, `ControlEvent`, `MeasurementResult`) | nothing |
| `tests/host/` | — | host unit tests, `dsp_core` with recorded WAV files | `dsp_core`, `common` |

## Building the skeleton

This directory is a standalone Zephyr application. `main.c` returns to the idle
thread; the component `.c` / `.h` files reserve places for implementation and
declare no APIs yet. `common/shared_types.h` reserves the shared data types.
The board overlay is intentionally empty, so no application peripherals are
configured. No audio processing, networking, storage, UI or monitoring is active.

With the repository's pinned Zephyr environment activated, build from the repository root:

```sh
west build --pristine=always -b esp32s3_devkitc/esp32s3/procpu Development/system/coding/app -d build-app
```

`python Development/system/testing/ci/run_ci.py build` also compiles this skeleton
to `build-ci-app`, before building and packaging the bring-up firmware. The skeleton
is not packaged or published as the bring-up firmware. The pure C DSP placeholders
will gain host tests in `tests/host` when their behavior is implemented.

## Layer rules

- Calls go downward only. Upward communication uses Zephyr message queues
  (`k_msgq`), because data flows mostly linearly from component to component.
- Start on one core. Move to both cores as soon as measurements show the audio
  path needs more compute (Zephyr ESP32-S3: AMP today, SMP still experimental).
- Zephyr provides drivers, DMA and interrupts. There is no project-owned HAL;
  Zephyr is SOUP in IEC 62304 terms.
- `dsp_core` includes no Zephyr headers, so the same code runs on the PC. Q2 needs
  every filter evaluated on identical recordings.
- The BPM path uses its own analysis filter. The filter switch selects only the
  listening filter.
- `MON` collects supervision that the risk analysis requires: watchdog, stack and
  heap watermarks, block deadline and buffer under-/overrun, and BPM quality gate.
  L1 enforces the rule that test sources are never sent as FHIR; MON observes and
  reports this rule.
- Software safety class: IEC 62304 class B, argued in the thesis.

## Reminder

Software and testing scope stay as specified. When time runs short, keep in mind
that a missed audio block lowers sound quality but is not a hazard: a working
system comes first, optimisation second.

Created by Claude-Opus-5.5 on behalf of Nico running in claude code.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
