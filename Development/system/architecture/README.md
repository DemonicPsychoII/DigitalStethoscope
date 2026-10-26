# Architecture

Decisions in force for each topic: [current baseline](../planning/README.md#current-baseline).

Open the [local viewer](review.html) for the proposed thesis-product views.
PlantUML sources are editable; the SVG previews are generated. These views do
not establish that the evaluation firmware implements the proposed contracts.

| View | Source |
|---|---|
| Architecture | [architecture-choice.puml](architecture-choice.puml) |
| System context | [system-context.puml](system-context.puml) |
| System components | [system-components.puml](system-components.puml) |
| Electrical interfaces | [electrical-interfaces.puml](electrical-interfaces.puml) |
| Software components | [software-components.puml](software-components.puml) |
| Threads | [runtime-ownership.puml](runtime-ownership.puml) |
| Listening | [listening-workflow.puml](listening-workflow.puml) |
| Wi-Fi states | [wifi-state.puml](wifi-state.puml) |
| Wi-Fi setup flow | [wifi-flow.puml](wifi-flow.puml) |
| Wi-Fi recovery flow | [wifi-recovery.puml](wifi-recovery.puml) |
| Current Wi-Fi snapshot | [wifi-workflows.html](wifi-workflows.html) |
| MVP session / alarms | [mvp-session-state.puml](mvp-session-state.puml) |
| BPM measurement | [measurement-workflow.puml](measurement-workflow.puml) |
| Wi-Fi setup sequence | [patient-assignment-workflow.puml](patient-assignment-workflow.puml) |

`patient-assignment-workflow.puml` keeps its file name for existing links; it shows Wi-Fi setup.
The evaluation implementation view is listed in the [view notes](VIEW-NOTES.md#current-evaluation-implementation).

[View notes](VIEW-NOTES.md) record review boundaries, I2S presentation-name mapping,
provenance, runtime assumptions and the separate evaluation implementation view.
The [overlay](../coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay) is the
wiring baseline; the device ends at the DAC line output and the headphone amplifier is outside the project scope (14 October).

For behavior and open choices, use [detailed design](../design/interfaces-and-behavior.md),
[design parameters](../design/parameters.md) and [implementation readiness](../planning/implementation-readiness.md).
Original board [snapshots](sources/manifest.json) are immutable provenance.

## Render

From this directory, render offline with PlantUML 1.2026.2 (no Graphviz or remote includes).
Component views use Smetana; the evaluation implementation uses bundled ELK
because Smetana fails on its labelled flat edges. Activity views use the activity renderer:

```sh
java -jar /path/to/plantuml.jar -charset UTF-8 -failfast2 -tsvg -o rendered "*.puml"
```

The viewer loads regenerated SVGs directly; only the flowcharts have zoom controls.
Rerender after each `.puml` edit: the documentation check compares the source embedded
in each SVG with its `.puml` file and fails on a stale render.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.
