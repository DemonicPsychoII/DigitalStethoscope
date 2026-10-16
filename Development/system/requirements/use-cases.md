# Use cases (MVP)

Abstract operator flows for the [system requirements](system-requirements.md), decided on 14 October 2026
([decisions](../planning/mvp-decisions-2026-10-14.md)). Detailed internal behavior is in the
[architecture workflows](../architecture/README.md) and [detailed design](../design/interfaces-and-behavior.md).
Sources are in [`use-cases/`](use-cases/); render them as described in the [architecture README](../architecture/README.md#render).

## F1 — Power up and listen

![F1 Power up and listen](use-cases/rendered/uc_01_listen.svg)

## F2 — Measure heart rate and deliver it

![F2 Measure heart rate and deliver it](use-cases/rendered/uc_02_measure_and_deliver.svg)

## F3 — Set up Wi-Fi and register the device

Changed on 15 October 2026 ([decisions](../planning/mvp-decisions-2026-10-15.md)): patient selection is no longer on the device.

![F3 Set up Wi-Fi and register the device](use-cases/rendered/uc_03_assign_patient.svg)

## F4 — Handle faults

![F4 Handle faults](use-cases/rendered/uc_04_faults.svg)

The earlier use cases UC-01…UC-10 were retired on 14 October 2026; their IDs are not reused.
Optional flows (replay, Lung, test recordings on the device) are removed for now.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
