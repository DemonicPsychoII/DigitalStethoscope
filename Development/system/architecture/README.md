# Architecture

Open the [local viewer](review.html) for eight proposed thesis-product views.
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
| BPM measurement | [measurement-workflow.puml](measurement-workflow.puml) |

[View notes](VIEW-NOTES.md) record review boundaries, I2S presentation-name mapping,
provenance, runtime assumptions and the separate evaluation implementation view.
The [overlay](../coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay) is the
wiring baseline; DAC line output requires a suitable headphone amplifier.

For behavior and open choices, use [detailed design](../design/interfaces-and-behavior.md),
[parameters](../requirements/parameters.md) and [implementation readiness](../planning/implementation-readiness.md).
Original board [snapshots](sources/manifest.json) are immutable provenance.

## Render

From this directory, render offline with Smetana (no Graphviz or remote includes):

```sh
java -jar /path/to/plantuml.jar -charset UTF-8 -failfast2 -tsvg -o rendered "*.puml"
```

The viewer loads regenerated SVGs directly; only the flowcharts have zoom controls.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
