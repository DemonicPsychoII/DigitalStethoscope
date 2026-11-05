# Architecture view boundaries

These notes qualify the [presentation viewer](review.html); the diagrams describe
the proposed thesis product.

| View | Source | Review boundary |
|---|---|---|
| Architecture | [architecture-choice.puml](architecture-choice.puml) | Layers: L2 orchestrates, L1 adapts hardware or holds pure C libraries, L0 is Zephyr, RTOS workers and events; task isolation is optional protection (TICKET-207). A/B firmware is an update/rollback concept, not a selected feature. |
| System context | [system-context.puml](system-context.puml) | Device as a black box; the device initiates FHIR requests and receives status responses as the receipt. Test tooling is outside the normal-use view. |
| System components | [system-components.puml](system-components.puml) | Hardware and external connections; ESP32 remains a black box. Networking is Wi-Fi plus HTTPS. |
| Electrical interfaces | [electrical-interfaces.puml](electrical-interfaces.puml) | Product connection types and chip roles; the electrical baseline below defines the planned application wiring. Optional interfaces are outside MVP acceptance. |
| Software components | [software-components.puml](software-components.puml) | Firmware modules: L2 orchestration, L1 hardware adapters and pure C libraries, L0 Zephyr. Libraries include no Zephyr headers; MONITOR observes across layers. |
| Threads | [runtime-ownership.puml](runtime-ownership.puml) | Proposed workers, the modules they run and data/communication methods. Touch belongs to Input; the BPM worker belongs to `L2_AUDIO`; original-rate blocks reach BPM before the volume control; BPM uses its own analysis filter, independent of the listening switch (S04 decision D5); the filter study decides the band. |
| Listening | [listening-workflow.puml](listening-workflow.puml) | Selected filter or Raw bypass, volume, playback and optional bounded capture/replay. Heart can select Raw; optional Lung mode is Raw listening only (TICKET-203). |
| BPM measurement | [measurement-workflow.puml](measurement-workflow.puml) | Freeze measurement settings and acquire until Stop; cancel without sending before 15 s, or finalize at or after 15 s subject to quality/coverage. Aggregate after listening stops, then deliver the result or validated error report. |

## Hardware naming

The electrical presentation labels the two audio paths **I2S1** and **I2S2**.
These are presentation names, not register/devicetree identifiers:

| Presentation | Role | Controller and planned signal assignment |
|---|---|---|
| I2S1 | INMP441 microphone input | `i2s0`: clock GPIO4, word select GPIO5, data input GPIO6 |
| I2S2 | PCM5102A DAC output | `i2s1`: clock GPIO40, word select GPIO41, data output GPIO42 |

The application electrical baseline also assigns the Start/Stop button to GPIO16,
the Raw/Murmur/BPM switch to GPIO18/21/38, the volume potentiometer to GPIO1
(ADC1 channel 0), and the button LED to GPIO17. Switch contacts and the button
connect to ground with pull-ups; the button LED is active high.
The GPIO38 switch assignment has an open board check against the RGB LED
([specification baseline](../../spec/product-scope.md#electrical-interface-baseline)); this view does not resolve it.
The [specification baseline](../../spec/product-scope.md#electrical-interface-baseline)
defines these project assignments and their limits. The application overlay still
needs these peripheral assignments; memory configuration alone does not establish
application wiring or physical verification. The device ends at the DAC line
output; the headphone amplifier is outside the project scope.

## Scope and source material

Four raw board snapshots retain their original timestamps and SHA-256 hashes. They are not editable diagram baselines.
Editable product views define the system. Raw board snapshots are immutable source material; they do not define a separate behavior baseline.

- DSP algorithms are pure C libraries in L1 (`L1_FILTER`, `L1_BPM`) so the same code can run in host tests.
- Queues carry bounded events or buffer handles. BPM collects successive original-rate
  blocks into its own analysis window; it never waits for an entire replay clip.
- During replay, BPM continues receiving original-rate microphone audio.
- The thread methods shown are a proposed design. Queue sizes, priorities and exact
  wake-up mechanisms remain implementation choices subject to measured timing.
- Measurement/session timing remains configurable. The 8 s window, 1 s update and
  30 s session are candidates (preThesis/02-entscheidungen/open-questions.md, D03–D06), not approved thresholds.
- FHIR result delivery is a device-initiated conditional create (`POST`) with up to 3 retries and a `201`/`200` receipt without readback. The [examination-request boundary](../COMMUNICATION/server-communication.md) is separate and its protocol remains unspecified; the delivery view does not rule it out. Network work waits until listening stops.
- Start on one core; measure before assigning work to a second core. AMP can run
  separate images concurrently on separate cores; SMP shares one OS across cores.
- Task isolation protects memory domains inside the runtime. A/B firmware instead
  stores two images and chooses one at boot for updates/rollback. See the
  [MCUboot image-slot and swap design](https://docs.mcuboot.com/design.html).
  A/B firmware is explanatory context, not an implementation requirement.

The later design stage specifies contracts, parameter candidates and open implementation choices within these architecture boundaries.

## Diagram notation

Display, touch, SD-card storage, capture / slower replay and Lung mode are optional beyond the MVP (TICKET-206, TICKET-202, TICKET-203).
Grey elements carry an explicit `optional` stereotype; mixed core/extension boxes
name optional responsibilities in their labels. Existing evaluation capabilities
remain visible without implying MVP scope. Component views use component syntax;
listening and measurement use activity syntax (`start`, actions, decisions, `stop`).
PlantUML infers the diagram family from these declarations; `@startuml` names
the output and is not a diagram-type declaration.
