# Architecture

PlantUML sources define each diagram; committed SVG previews are generated from them.

| Area | Responsibilities and views |
| --- | --- |
| [System](system/README.md) | Boundaries, hardware, layers, runtime ownership, audio, measurement and feedback ground rules. |
| [AUDIO](AUDIO/README.md) | Microphone-to-DAC transport, block ownership, clocking and stream faults. |
| [WIFI](WIFI/README.md) | General station/provisioning model and radio operation boundary. |
| [COMMUNICATION](COMMUNICATION/README.md) | Wi-Fi setup workflow, composition, recovery and listening-priority boundary; [time synchronization](COMMUNICATION/time-ownership.md) and [secure transport](COMMUNICATION/secure-transport.md) to the server. |
| [FHIR and server communication](COMMUNICATION/server-communication.md) | Registration, examination-context, serialization and delivery responsibilities. |
| [PORTAL](PORTAL/README.md) | Browser, HTTP and typed controller-request boundary. |

The device ends at the DAC line output; the headphone amplifier is external.

## Render

From a diagram folder, render offline using PlantUML 1.2026.9 (no remote includes or Graphviz). Component views use Smetana.

```sh
java -jar /path/to/plantuml.jar -charset UTF-8 -failfast2 -tsvg -o ../rendered "puml/*.puml"
```
