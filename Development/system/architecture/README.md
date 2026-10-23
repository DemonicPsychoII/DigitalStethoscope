# Architecture

Current Wi-Fi/portal and feedback behaviour follows the [19 October resolutions](../planning/mvp-decisions-2026-10-19.md); earlier dated notes remain history.

Open the [local viewer](system/review.html) for the proposed thesis-product views.
PlantUML sources are editable; the SVG previews are generated. These views do
not establish that the evaluation firmware implements the proposed contracts.

| Area | Diagrams and editable sources |
|---|---|
| [System](system/README.md) | Shared system views, workflows and evaluation implementation. |
| [WIFI](WIFI/README.md) | Wi-Fi states, setup, recovery and the current page snapshot. |
| [PORTAL](PORTAL/README.md) | Links to portal content currently mixed into the Wi-Fi views. |

[View notes](system/VIEW-NOTES.md) record review boundaries, I2S presentation-name mapping,
provenance, runtime assumptions and the separate evaluation implementation view.
The [overlay](../coding/bringup-zephyr/boards/esp32s3_devkitc_procpu.overlay) is the
wiring baseline; the device ends at the DAC line output and the headphone amplifier is outside the project scope (14 October).

For behavior and open choices, use [detailed design](../design/interfaces-and-behavior.md),
[design parameters](../design/parameters.md) and [implementation readiness](../planning/implementation-readiness.md).
Original board [snapshots](system/sources/manifest.json) are immutable provenance.

## Render

From the folder containing the sources (`system/`, `WIFI/`, or another diagram folder), render offline with PlantUML 1.2026.2 (no Graphviz or remote includes).
Component views use Smetana; the evaluation implementation uses bundled ELK
because Smetana fails on its labelled flat edges. Activity views use the activity renderer:

```sh
java -jar /path/to/plantuml.jar -charset UTF-8 -failfast2 -tsvg -o rendered "*.puml"
```

The viewer loads regenerated SVGs directly; only the flowcharts have zoom controls.

Updated by Claude-Opus-5.5 on behalf of Nico running in T3 Code through Claude Code.

## Feedback preparation (2026-10-07)

Display, touch, SD-card storage and capture / slower replay are optional beyond the MVP.
Grey elements carry an explicit `optional` stereotype; mixed core/extension boxes
name optional responsibilities in their labels. Existing evaluation capabilities
remain visible without implying MVP scope. Component views use component syntax;
listening and measurement use activity syntax (`start`, actions, decisions, `stop`).
PlantUML infers the diagram family from these declarations; `@startuml` names
the output and is not a diagram-type declaration.

See [framework and transport evaluation](../planning/framework-and-transport-evaluation.md)
for ESP32-S3 drivers, external C/C++ library integration and HTTP/HTTPS effort.

Session baseline follows [11 October owner decisions](../planning/mvp-decisions-2026-10-11.md): Busy blocks Start, failed sends abort, context changes are rejected. Current halt/clear rules follow the 19 October catalogue adoption. Numeric targets remain proposals. [Component timeline](../planning/mvp-implementation-timeline.md) puts Wi-Fi/FHIR before carrier-dependent audio.

[12 October decisions](../planning/mvp-decisions-2026-10-12.md) add the hotspot portal and patient assignment to the MVP. The patient-assignment view is a sequence diagram; the session state view gains the Portal state and the context view the phone browser.

[15 October decisions](../planning/mvp-decisions-2026-10-15.md) remove patient selection from the device. The sequence view (file name kept for links) now shows current Wi-Fi setup; Device registration and delivery are later FHIR work.

Historically, [16 October decisions](../planning/mvp-decisions-2026-10-16.md) replaced the Device Alarm with a single error type that a short press clears once the cause is gone, and let the device pass on a patient that the server has linked. The current catalogue supersedes those indication and clear rules. The session state view shows the Muted state.

[13 October decisions](../planning/mvp-decisions-2026-10-13.md) fix the firmware layer structure. The software components view shows the [`coding/app/`](../coding/app/README.md) modules: L2 orchestrates (CONTROL, AUDIO, COMMUNICATION, SHELL), L1 holds hardware adapters and pure C libraries, and L0 is Zephyr. The threads view names the module behind each worker.
