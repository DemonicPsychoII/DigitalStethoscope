# Architecture view boundaries and provenance

Decisions in force for each topic: [current baseline](../planning/README.md#current-baseline).

Earlier session decisions and numeric proposals: [11 October MVP decisions](../planning/mvp-decisions-2026-10-11.md). Older source snapshots and evaluation behavior remain historical evidence.

These notes qualify the [presentation viewer](review.html); the diagrams describe
a proposed thesis product, except for the separate evaluation implementation view.

| View | Source | Review boundary |
|---|---|---|
| Architecture | [architecture-choice.puml](architecture-choice.puml) | Chosen layers (13 October: L2 orchestrates, L1 adapts hardware or holds pure C libraries, L0 is Zephyr), RTOS workers and events; task isolation is optional protection. A/B firmware is an update/rollback concept, not a selected feature. |
| System context | [system-context.puml](system-context.puml) | Device as a black box; the device initiates FHIR requests and receives status responses as the receipt. Test tooling is outside the normal-use view. |
| System components | [system-components.puml](system-components.puml) | Hardware and external connections; ESP32 remains a black box. Networking is Wi-Fi plus HTTPS. |
| Electrical interfaces | [electrical-interfaces.puml](electrical-interfaces.puml) | Connection types and chip roles; pin assignments and speeds remain in the maintained overlay and hardware requirements. |
| Software components | [software-components.puml](software-components.puml) | Firmware modules per [13 October decisions](../planning/mvp-decisions-2026-10-13.md): L2 orchestration, L1 hardware adapters and pure C libraries, L0 Zephyr. Libraries include no Zephyr headers; MONITOR observes across layers. |
| Threads | [runtime-ownership.puml](runtime-ownership.puml) | Proposed workers, the modules they run and data/communication methods. Touch belongs to Input; the BPM worker belongs to `L2_AUDIO`; original-rate blocks reach BPM before the volume control; whether BPM uses its own filter or a listening filter is decided by the filter study (14 October). |
| Listening | [listening-workflow.puml](listening-workflow.puml) | Selected filter or Raw bypass, volume, playback and optional bounded capture/replay. Lung is Raw; Heart can also select Raw. |
| BPM measurement | [measurement-workflow.puml](measurement-workflow.puml) | Freeze measurement settings and acquire until Stop; cancel without sending before 15 s, or finalize at or after 15 s subject to quality/coverage. Aggregate after listening stops, then deliver the result or validated error report. |

## Hardware naming

The electrical presentation labels the two audio paths **I2S1** and **I2S2**.
These are presentation names, not register/devicetree identifiers:

| Presentation | Role | Maintained Zephyr overlay |
|---|---|---|
| I2S1 | INMP441 microphone input | `i2s0` / alias `i2s-mic` |
| I2S2 | PCM5102A DAC output | `i2s1` / alias `i2s-dac` |

The [overlay](../coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay)
remains the wiring baseline. The device ends at the DAC line output; the headphone
amplifier is outside the project scope (14 October).

## Scope and provenance

The [source manifest](sources/manifest.json) preserves four original board timestamps
and SHA-256 hashes. Snapshots are provenance, not editable diagram baselines.
The reviewed views reconcile S01-S04; presentation simplifications and the A/B
explanation come from the subsequent review rather than additions to the old boards.

- DSP algorithms are pure C libraries in L1 (`L1_FILTER`, `L1_BPM`) so the same code can run in host tests.
- Queues carry bounded events or buffer handles. BPM collects successive original-rate
  blocks into its own analysis window; it never waits for an entire replay clip.
- During replay, BPM continues receiving original-rate microphone audio.
- The thread methods shown are a proposed design. Queue sizes, priorities and exact
  wake-up mechanisms remain implementation choices subject to measured timing.
- Measurement/session timing remains configurable. The 8 s window, 1 s update and
  30 s session in the parameter register are candidates, not approved thresholds.
- FHIR is a device-initiated conditional create (`POST`) with up to 3 retries (14 October) and a `201`/`200` receipt without readback (15 October); the server responds rather than polling or
  commanding the device. Network work waits until listening stops.
- Start on one core; measure before assigning work to a second core. AMP can run
  separate images concurrently on separate cores; SMP shares one OS across cores.
- Task isolation protects memory domains inside the runtime. A/B firmware instead
  stores two images and chooses one at boot for updates/rollback. See the
  [MCUboot image-slot and swap design](https://docs.mcuboot.com/design.html).
  A/B firmware is explanatory context, not an implementation requirement of this PR.

Detailed contracts, proposals and open questions remain in
[design](../design/interfaces-and-behavior.md) and
[implementation readiness](../planning/implementation-readiness.md).
The separate three-region state render was removed; it repeated the workflows.
Its proposed lifecycle contracts remain documented in detailed design.

## Current evaluation implementation

[Evaluation firmware source](software-implementation.puml) and
[its preview](rendered/software_implementation.svg) describe actual bring-up modules
and execution contexts. They are a reference outside the presentation viewer.
The current control settings have multiple mutex-protected callers; BPM and replay
run in the audio module, rather than in all of the proposed separate workers.
This reference describes the evaluation implementation, not the proposed worker layout.

## Diagram conventions

Display, touch, SD-card storage and capture / slower replay are optional beyond the MVP.
Grey elements carry an explicit `optional` stereotype; mixed core/extension boxes
name optional responsibilities in their labels. Existing evaluation capabilities
remain visible without implying MVP scope. Component views use component syntax;
listening and measurement use activity syntax (`start`, actions, decisions, `stop`).
PlantUML infers the diagram family from these declarations; `@startuml` names
the output and is not a diagram-type declaration.

See [framework and transport evaluation](../planning/framework-and-transport-evaluation.md)
for ESP32-S3 drivers, external C/C++ library integration and HTTP/HTTPS effort.

## View history

How earlier decisions changed the views. The [current baseline](../planning/README.md#current-baseline)
names the decisions in force.

Session baseline follows [11 October owner decisions](../planning/mvp-decisions-2026-10-11.md): Busy blocks Start, failed sends abort, context changes are rejected. Current halt/clear rules follow the 19 October catalogue adoption. Numeric targets remain proposals. [Component timeline](../planning/mvp-implementation-timeline.md) puts Wi-Fi/FHIR before carrier-dependent audio.

[12 October decisions](../planning/mvp-decisions-2026-10-12.md) add the hotspot portal and patient assignment to the MVP. The patient-assignment view is a sequence diagram; the session state view gains the Portal state and the context view the phone browser.

[15 October decisions](../planning/mvp-decisions-2026-10-15.md) remove patient selection from the device. The sequence view (file name kept for links) now shows current Wi-Fi setup; Device registration and delivery are later FHIR work.

Historically, [16 October decisions](../planning/mvp-decisions-2026-10-16.md) replaced the Device Alarm with a single error type that a short press clears once the cause is gone, and let the device pass on a patient that the server has linked. The current catalogue supersedes those indication and clear rules. The session state view shows the Muted state.

[13 October decisions](../planning/mvp-decisions-2026-10-13.md) fix the firmware layer structure. The software components view shows the [`coding/app/`](../coding/app/README.md) modules: L2 orchestrates (CONTROL, AUDIO, COMMUNICATION, SHELL), L1 holds hardware adapters and pure C libraries, and L0 is Zephyr. The threads view names the module behind each worker.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
