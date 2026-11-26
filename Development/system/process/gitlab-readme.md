# Digital stethoscope

Firmware and development documents of a digital stethoscope on an ESP32-S3. The operator places the
chestpiece on a patient and listens to the heart sounds through headphones. The device measures the
heart rate and sends the result to a FHIR server in the local network.

## Documents and code

| Folder | Content |
|---|---|
| [Product specification](../spec/product-scope.md) | Purpose, product boundary, functions and terminology |
| [Requirements](../requirements/README.md) | Use-case flows and the system requirements with their tests |
| [Architecture](../architecture/README.md) | System architecture and the architecture of each module |
| [Design](../design/README.md) | Detailed design of each module and the cross-module design |
| [Code](../coding/app/README.md) | Firmware application, build and flash instructions |
| [Verification allocation](../testing/verification-allocation.md) | Scenarios that verify the design pages, with their requirements and expected results |
| [Reference code](../references/newtec-pulsoxy/README.md) | PulsOxy code of NewTec GmbH that the design refers to |

## Build

The firmware builds with the Zephyr toolchain that the scripts under
`Development/system/coding/tools/` set up. The [firmware README](../coding/app/README.md)
gives the commands for building, flashing and debugging.
