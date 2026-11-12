# Status light pin, placeholder volume, catalogue order and first audio path — 10 November 2026

Nico decided on 10 November 2026 in T3 Code (conversation link not recorded) how the first fitted
evaluation carrier is used and how the feedback catalogue is ordered. These are project decisions,
not measurements.

Board state reported by Nico: the evaluation PCB from the `DigitalStethoscope_Eval` Altium project
(commit `a8f23a2`, production package of 13 October 2026) is assembled with J3 (INMP441 microphone),
J4 (PCM5102A DAC socket), J6 (illuminated button) and J8 (Raw/Murmur/BPM switch). J7 (volume
potentiometer) is not fitted, and the SD card is not used. The DevKitC-1 revision was not known
when the decision was made.

Bench observation on 10 November 2026 (Nico, local build of the TICKET-187 changes on commit
`5705ac4`, which is `integration` `50de562` plus a CI-only change): the status light lit on GPIO48, so the fitted DevKit is v1.0.
The DevKit was not yet soldered to the carrier, so carrier inputs such as J8 were not connected.

## Decision

1. **Status light on GPIO48.** The RGB status light is driven on GPIO48, its position on DevKitC-1
   v1.0, whichever revision is fitted. The carrier's SD card chip select on GPIO48 is not used.
   GPIO38 is not driven, so it stays the BPM contact of the filter switch. If the light stays dark,
   the DevKit is v1.1 and the pin is revisited. This replaces the earlier precondition to confirm
   the DevKit revision before enabling the RGB LED driver.
2. **Fixed volume until J7 is fitted.** Until the potentiometer is fitted, the audio path uses a
   fixed volume of 100 % as a placeholder that the potentiometer replaces. REQ-04 and the volume
   part of TICKET-187 stay unverified until then.
3. **Catalogue rows grouped by subject, blink codes kept.** Within each colour, statuses come first
   and errors are grouped by subject in workflow order, for example all `DELIVERY_*` rows together.
   Every code keeps its blink count, so blink counts no longer rise down the table. The enum in
   `feedback.h` and the status light table follow the same order. This replaces the sort rule
   "colour, then number of blinks" (option B of the comparison on the Pages board
   `stethoscope-feedback-grouping`).

## Applied in

- [Feedback catalogue](../design/FEEDBACK/catalogue.md) and the
  [electrical interface baseline](../spec/product-scope.md#electrical-interface-baseline)
- [Architecture view notes](../architecture/system/VIEW-NOTES.md) and the application board overlay
  in [`coding/app/boards/`](../coding/app/README.md)

## First audio path

Nico decided on 10 November 2026 in T3 Code (conversation link not recorded), working on the
whiteboard board "Audio Path Architecture" (homelab whiteboard, board id `audio-path-architecture`),
how the first audio step from microphone to DAC is built. These are project decisions, not
measurements. The derived sizes follow from the decisions and the pinned Zephyr ESP32 I2S driver
[zephyr_esp32_i2s_driver_357467a](../../../thesis-material/quellen.md#zephyr_esp32_i2s_driver_357467a).

4. **Internal RAM and a copy step first.** The first step moves audio from the microphone to the
   DAC through DMA blocks in internal RAM. Its processing step only copies; the listening filter,
   volume and BPM fan-out come later. No PSRAM buffers are used in this step. The two 10 s
   history buffers drawn on the board are dropped; the BPM analysis window is sized in TICKET-192.
5. **16 kHz, 64-frame blocks.** The sample rate stays 16 kHz. A transport block holds 64 frames,
   4 ms, instead of 128 frames. 48 kHz with 240-frame blocks was considered and not chosen.
6. **Five RX and five TX blocks.** Each direction has a pool of five blocks, so the audio thread
   has three blocks (12 ms) for processing and lateness together before the stream stops. Four
   TX blocks in flight give a transport delay of 16 ms: the first RX block fills and is processed
   while the primed blocks play, so neither adds delay. This is below the P03 target of 30 ms.
7. **Microphone on the left slot, copied to both DAC channels.** The INMP441 L/R pin is tied to
   ground, as on the bring-up wiring, so the microphone sends on the left slot. The audio path
   takes the left slot and writes the same sample to both DAC slots.
8. **Start and Stop order.** Start fills the TX queue with silence, then starts RX, then TX. Stop
   lets the block in DMA finish, then discards both queues; faults discard both queues at once.
   Corrected after reading the driver source ([Stop sequence](../design/AUDIO/interfaces-and-behavior.md#stop-sequence)).

Both I2S controllers use the same word size and sample rate. Nico asked on 10 November 2026 whether
one clock can drive both links; the pinned driver clocks both controllers from the same default
clock source and derives their dividers from these settings, so they run at the same rate on their
separate pins without rate adaptation. This is a source reading, not a measurement.

Applied in the [AUDIO architecture](../architecture/AUDIO/README.md), the
[AUDIO design](../design/AUDIO/interfaces-and-behavior.md) and parameters P01, P02 and P11 in the
[system parameters](../design/system/parameters.md).
