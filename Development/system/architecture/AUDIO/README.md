# Audio architecture

The first audio step carries microphone audio to the DAC line output without a listening filter,
volume control or BPM analysis. It fixes the transport that those later steps build on. The
[decision record](../../planning/mvp-decisions-2026-11-10.md#first-audio-path) defines its scope,
sample rate, block size and pool sizes [1].

| View | Editable source | Preview |
| --- | --- | --- |
| First audio path | [audio-path.puml](audio-path.puml) | [SVG](rendered/audio_path.svg) |

## Responsibilities

| Component | Responsible for | Not responsible for |
| --- | --- | --- |
| L0 Zephyr I2S driver | Clocking and DMA on `i2s0` (microphone RX) and `i2s1` (DAC TX); queues of completed RX blocks and pending TX blocks | Processing; recovery after its error state |
| `L1_I2S` | Configuration of both links, the RX and TX block pools in internal RAM, priming TX with silence, start and stop, lending received blocks and accepting filled TX blocks; driver errors as typed outcomes | Sample processing, retries, fault policy, indication |
| `L2_AUDIO` audio thread | The block loop: take the left slot, run the processing step, write the result into both TX slots; return every block it borrowed before the next block; report started, stopped and faults | Mode, session or volume state; driver calls other than through `L1_I2S` |
| `L2_CONTROL` | Start and Stop commands to `L2_AUDIO`; the error indication for reported faults per the [feedback catalogue](../../design/FEEDBACK/catalogue.md) | Audio data |

The processing step only copies in this step. The listening filter (`L1_FILTER`), volume and the
analysis fan-out to the BPM worker shown in the [threads view](../system/README.md) join this loop
later without changing the transport boundary.

## Data path and block ownership

Every block has exactly one holder at a time: the driver (DMA or queue), `L1_I2S`, or the audio
thread. `L2_AUDIO` holds at most one received and one TX block per iteration, and no block leaves
the audio thread. Both pools are fixed at build time in internal, DMA-capable RAM; this step uses
no PSRAM [1].

The pinned driver only supports two-slot frames, so RX blocks contain a filled left slot and an
unused right slot, and TX blocks must carry both slots [2]. The microphone's L/R pin is tied to
ground, which selects the left slot. The bring-up firmware read the microphone from that slot
without errors over 30 s on 14 August 2026 [3]. The DAC path from these blocks to the line output
has not been verified physically yet: the bring-up's loopback test was not run [3].

## Clocking

Both links use the same sample rate, slot width and word size. The pinned driver clocks both
controllers from the same default clock source and derives their dividers from these settings,
so the microphone and the DAC run at the same rate on their separate pins and the path needs no
rate adaptation [2]. A different word size on one link would change its master-clock multiple and
could make the rates differ slightly [2]. This is a source reading; a long-running check of the TX
queue level is part of the verification below.

## Stream faults

When the audio thread falls behind, the driver stops the stream: an empty TX queue sets its error
state and stops TX, and RX enters the error state when no free pool block is left [2]. The stream
stays stopped until it is configured and started again [2]. The bring-up session showed this on
hardware: a blocking full-screen display redraw, estimated in the protocol at about 120 ms,
overran RX, and audio stopped permanently [3]. The pool sizes therefore bound how late the audio thread may be, and `L2_AUDIO`
treats a driver error as a fault it reports to `L2_CONTROL`. Start and Stop order and fault
handling belong to the detailed design.

## Expected verification

| Scenario | Basis | Expected result |
| --- | --- | --- |
| Power-on, then wait without Start | REQ-01, VT-01 | No sound on either DAC channel; no TX stream before Start |
| Start with the chestpiece on the chest | REQ-02 | Heart sounds audible on both channels within 2 s of Start |
| Tap the chestpiece during listening | REQ-05, VT-02 | Tap heard together with the touch, no echo or lag |
| Microphone or DAC link fails to start | VT-01 | Silent output and the catalogue error for the failed link |
| Audio thread delayed beyond the pool reserve | VT-02 | Stream stops, fault reported, output silent; no silent hang |
| Listening for at least 10 minutes | VT-02 | No stream fault; TX queue level stays constant, so the two links do not drift |
| Copy step with a known input block | VT-03 | Both TX slots equal the received left slot |

## Sources

[1] Nico, *First audio path: internal RAM, 16 kHz, 64-frame blocks, five RX and five TX blocks,
left microphone slot*, personal communication, T3 Code and homelab whiteboard, 10 November 2026.
Project decision, not a measurement.
[Source register](../../../../thesis-material/quellen.md#nico_audio_path_decision_20261110).

[2] The Zephyr Project, *ESP32 I2S driver and its Kconfig*, source revision
`357467a011cd2557a1a3f0b4be83d817c4addc9b`,
[i2s_esp32.c](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/i2s/i2s_esp32.c)
and
[Kconfig.esp32](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/i2s/Kconfig.esp32),
accessed 10 November 2026. Source reading, not a target measurement.
[Source register](../../../../thesis-material/quellen.md#zephyr_esp32_i2s_driver_357467a).

[3] Nico F., *Hardware Test Protocol — ESP32-S3 Bring-up*, session of 14 August 2026, bring-up
firmware commit `2cd6d4c818be92f0bf1e1181ef0b4cd7de7ceb14`, Zephyr
`357467a011cd2557a1a3f0b4be83d817c4addc9b`: tests T05, T07 and T09 in
[TEST-PROTOCOL.md](../../../../preThesis/06-bringup-zephyr/TEST-PROTOCOL.md), wiring in
[HARDWARE.md](../../../../preThesis/06-bringup-zephyr/HARDWARE.md). Own measurement on archived
pre-thesis firmware.
[Source register](../../../../thesis-material/quellen.md#nico_bringup_hardware_protocol_20260814).

The INMP441 datasheet describes the L/R pin and slot format; its download was not available when
this page was written, so the slot assignment above rests on the bring-up evidence [3], not on the
datasheet.
