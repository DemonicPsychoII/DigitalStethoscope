# Architecture view boundaries and provenance

These notes qualify the [presentation viewer](review.html); the diagrams describe
a proposed thesis product, except for the separate evaluation implementation view.

| View | Source | Review boundary |
|---|---|---|
| Architecture | [architecture-choice.puml](architecture-choice.puml) | Chosen layers, RTOS workers and events; task isolation is optional protection. A/B firmware is an update/rollback concept, not a selected feature. |
| System context | [system-context.puml](system-context.puml) | Device as a black box; the device initiates FHIR requests and receives status/readback responses. Test tooling is outside the normal-use view. |
| System components | [system-components.puml](system-components.puml) | Hardware and external connections; ESP32 remains a black box. Networking is Wi-Fi plus HTTPS. |
| Electrical interfaces | [electrical-interfaces.puml](electrical-interfaces.puml) | Connection types and chip roles; pin assignments and speeds remain in the maintained overlay and hardware requirements. |
| Software components | [software-components.puml](software-components.puml) | Individual components in Application, Services and Zephyr/adapters. DSP belongs inside Services; MON observes across layers. |
| Threads | [runtime-ownership.puml](runtime-ownership.puml) | Proposed workers and data/communication methods. Touch belongs to Input; original-rate blocks reach BPM before listening filter/gain. |
| Listening | [listening-workflow.puml](listening-workflow.puml) | Selected filter or Raw bypass, volume, playback and optional bounded capture/replay. Lung is Raw; Heart can also select Raw. |
| BPM measurement | [measurement-workflow.puml](measurement-workflow.puml) | Save measurement settings, acquire until configured time elapses, aggregate, then deliver a valid result when listening is stopped. |

## Hardware naming

The electrical presentation labels the two audio paths **I2S1** and **I2S2**.
These are presentation names, not register/devicetree identifiers:

| Presentation | Role | Maintained Zephyr overlay |
|---|---|---|
| I2S1 | INMP441 microphone input | `i2s0` / alias `i2s-mic` |
| I2S2 | PCM5102A DAC output | `i2s1` / alias `i2s-dac` |

The [overlay](../coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay)
remains the wiring baseline. DAC line output needs a suitable headphone amplifier.
The diagram simplification does not approve amplifier gain, output limits or wiring.

## Scope and provenance

The [source manifest](sources/manifest.json) preserves four original board timestamps
and SHA-256 hashes. Snapshots are provenance, not editable diagram baselines.
The reviewed views reconcile S01-S04; presentation simplifications and the A/B
explanation come from the subsequent review rather than additions to the old boards.

- DSP algorithms are pure C within Services so the same code can run in host tests.
- Queues carry bounded events or buffer handles. BPM collects successive original-rate
  blocks into its own analysis window; it never waits for an entire replay clip.
- During replay, BPM continues receiving original-rate microphone audio.
- The thread methods shown are a proposed design. Queue sizes, priorities and exact
  wake-up mechanisms remain implementation choices subject to measured timing.
- Measurement/session timing remains configurable. The 8 s window, 1 s update and
  30 s session in the parameter register are candidates, not approved thresholds.
- FHIR is device-initiated PUT/readback; the server responds rather than polling or
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

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
