# Thesis firmware — layer structure

This directory records the Zephyr/ESP32-S3 layer structure from the saved
architecture decision. Firmware placement/migration remains open under
[D11](../../planning/implementation-readiness.md#decision-register); the
[evaluation firmware](../bringup-zephyr/README.md) remains separate.

| Folder | Contents | May depend on |
|---|---|---|
| `L2_application/` | Controller (single writer of mode state), UI, shell | L1, L0, `common` |
| `L1_services/` | Audio, BPM, storage, network/FHIR; pre-send source check | L0, `dsp_core`, `common` |
| `L1_services/dsp_core/` | Pure C filters, envelope, autocorrelation, WSOLA | `common` |
| `L0_platform/` | Thin Zephyr driver/devicetree adapters | Zephyr, `common` |
| `MON/` | Runtime supervision | All layers, read-only |
| `common/` | Shared audio/event/result types | Nothing |
| `tests/host/` | DSP tests on recorded WAVs | `dsp_core`, `common` |

Calls go downward; upward notifications use events/message queues. Zephyr owns
drivers, DMA and interrupts. DSP includes no Zephyr headers. Listening and BPM
analysis filters are independent; Services enforce the test-source send prohibition,
while MON observes it. Start on one core and measure before adding another.

[Detailed design](../../design/interfaces-and-behavior.md) defines contracts and
ownership. [Product scope](../../spec/product-scope.md) and the
[risk/readiness register](../../planning/implementation-readiness.md) qualify
class B/SOUP intentions and monitoring controls; classification and hazards require
substantiation.

Updated by GPT-6.1-Sol on behalf of Nico running in T3 Code through Codex.
