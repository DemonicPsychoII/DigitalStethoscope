# Audio interfaces and behavior

`L1_I2S` owns both I2S links and their block pools; `L2_AUDIO` owns the block loop and reports to
`L2_CONTROL`. The [AUDIO architecture](../../architecture/AUDIO/README.md) defines these
responsibilities and the [decision record](../../planning/mvp-decisions-2026-11-10.md#first-audio-path)
the chosen values. This page covers the first audio step: microphone to DAC with a copy step.

## Stream configuration

Both links use the same settings, so both controllers derive the same clock dividers from the same
default clock source [1].

| Setting | Value | Reason |
| --- | --- | --- |
| Links | `i2s0` RX from the INMP441, `i2s1` TX to the PCM5102A | [Electrical interface baseline](../../spec/product-scope.md#electrical-interface-baseline) |
| Format | Zephyr `I2S_FMT_DATA_FORMAT_I2S`, the ESP32-S3 drives bit and frame clock on both links | The microphone and the DAC both take their clocks from the ESP32-S3, as configured in the bring-up firmware [2] |
| Channels, word size | 2 channels, 32-bit words | The driver accepts only two channels [1]; equal word sizes keep the dividers equal [1] |
| Sample rate | 16,000 Hz (P01) | Decision of 10 November 2026 |
| Block | 64 frames × 2 slots × 4 bytes = 512 bytes, 4 ms | P01; below the 4092-byte DMA descriptor limit, so one descriptor per block [1] |
| RX pool | 5 blocks; `CONFIG_I2S_ESP32_RX_BLOCK_COUNT` = 3 | 3 completed blocks waiting, 1 in DMA, 1 lent to the audio thread |
| TX pool | 5 blocks; `CONFIG_I2S_ESP32_TX_BLOCK_COUNT` = 4 | 4 blocks primed before TX starts (1 in DMA and 3 queued afterwards), 1 being filled |
| Memory | Both pools in internal DMA-capable RAM, defined at build time | No PSRAM in this step |

## Service boundary

Proposed `L1_I2S` interface. Names avoid Zephyr's `i2s_read`, `i2s_write` and `i2s_configure`.
Every operation returns an `i2s_result`: `I2S_RESULT_OK`, `I2S_RESULT_MICROPHONE_FAILURE` or
`I2S_RESULT_OUTPUT_FAILURE`. The two failure values identify the failed link and map to the catalogue
codes `MICROPHONE_FAILURE` and `AUDIO_OUTPUT_FAILURE`. `L1_I2S` logs the driver error code; it does
not retry.

| Interface | Inputs | Outputs and ownership |
| --- | --- | --- |
| `i2s_initialize()` | One call at boot | Checks that both devices are ready and configures both links. No stream runs afterwards. |
| `i2s_start()` | Called while stopped | Configures both links again, primes 4 silent TX blocks, starts RX, then TX. On failure it stops both links and returns the failed link. |
| `i2s_stop()` | Any time, also after a failure | Discards both queues at once and returns every pool block; no further sound. Repeated calls are harmless. |
| `i2s_receiveBlock(receivedFrames)` | Pointer for the result | Waits at most the receive wait (P11) for the next completed RX block and lends it to the caller. A timeout or driver error is a microphone failure. |
| `i2s_releaseReceivedBlock(receivedFrames)` | A lent RX block | Returns it to the RX pool. |
| `i2s_allocateTransmitBlock(transmitFrames)` | Pointer for the result | Waits at most the TX-block wait (P11) for a free TX block. A timeout is an output failure. |
| `i2s_transmitBlock(transmitFrames)` | A filled TX block | Queues it for the DAC; ownership passes to the driver. On failure `L1_I2S` returns the block to the pool and reports an output failure. |

## Block loop

`L2_AUDIO` runs one audio thread with one deterministic processing path: read, process, send
([decision of 11 November](../../planning/mvp-decisions-2026-11-11.md)). It runs at the highest application thread priority; the
numeric priority is an implementation choice measured under VT-02. It waits for commands while
stopped and runs the loop below while started. Each iteration, from the received block to the
queued TX block, finishes within the processing budget of 3 ms (P02); the wait for the next block
is not part of it. No lock is held across a block wait.

1. `i2s_receiveBlock`.
2. For each of the 64 frames, take the left slot (even index) into a 64-entry mono working buffer,
   using the [sample format](#sample-format).
3. `i2s_releaseReceivedBlock`.
4. Processing step: copy. The listening filter and volume replace this step later; until the
   potentiometer is fitted, the volume is a fixed 100 %.
5. `i2s_allocateTransmitBlock`, then write each mono sample into both slots of its frame.
6. `i2s_transmitBlock`.
7. Check the command queue without waiting; Stop ends the loop.

The mono working buffer is 256 bytes owned by the audio thread. Each iteration returns the received
block before it requests a TX block, so the thread never holds more than one block of each pool.

## Start, Stop and faults

| Event | Behavior | Result |
| --- | --- | --- |
| Boot | `i2s_initialize`; no stream is started | Ready: stopped. Failure: reported to `L2_CONTROL` |
| Start command while stopped | `i2s_start`, then the block loop | `started` event, or the start failure |
| Stop command | Leave the loop, `i2s_stop` | `stopped` event; output silent |
| Any non-OK result in the loop | `i2s_stop`; the thread waits for commands | Fault event with the failed link; `L2_CONTROL` shows the catalogue error, which requires a restart |

A stream fault includes a deadline miss. If the thread falls more than three blocks behind, the
driver stops the stream itself [1]. The bring-up session showed that such a stream stays stopped
until it is configured and started again [2]. A stream fault stays a restart-required error under
the catalogue ([decision of 11 November](../../planning/mvp-decisions-2026-11-11.md)): a Start after a fault needs a device
restart.

## Sample format

The bring-up firmware treated the 24-bit microphone sample as the top 24 bits of the 32-bit left
slot: it shifted the slot right by 8 bits, or scaled the whole slot by 2³¹, and its microphone test
passed [2]. Nothing in this evidence defines the 8 low bits after the sample, so the loop clears
them. The INMP441 datasheet would state the slot format; its download was not available, so the
format rests on the bring-up evidence, not on the datasheet.

Two alignments of the mono working sample are possible:

- **Left-aligned, low 8 bits cleared.** The sample keeps the full 32-bit scale of the DAC slot and
  passes through without shifting.
- **Signed 24-bit, right-aligned.** This matches the current `AudioBlock` wording "signed 24-bit
  normalized into int32", but needs an 8-bit shift into the TX slot.

The mono working sample is left-aligned with its low 8 bits cleared
([decision of 11 November](../../planning/mvp-decisions-2026-11-11.md)), so the copy step writes the DAC slot unchanged.

The PCM5102A receives 32-bit words. The bring-up's DAC test only showed that the link accepts
blocks, and its loopback test was not run [2], so audible output from these words is not verified
yet.

## Timing and sizing

| Quantity | Derivation | Value |
| --- | --- | --- |
| Block period | 64 frames ÷ 16,000 Hz | 4 ms |
| RX reserve | 3 waiting blocks × 4 ms | The thread may be up to 12 ms late before RX overruns |
| TX reserve | 3 queued blocks behind the one in DMA × 4 ms | The thread may be up to 12 ms late before TX runs empty |
| Transport delay | 1 RX block + 4 TX blocks, × 4 ms | About 20 ms plus processing, below the P03 target of 30 ms |
| Processing budget | Three quarters of the block period (P02) | At most 3 ms per block |
| Block waits | 5 block periods (P11) | 20 ms; a normal block arrives within 4 ms |
| Internal RAM | 2 pools × 5 × 512 bytes, plus the 256-byte mono buffer | 5,376 bytes, plus thread stack and driver descriptors |

The transport delay and the reserves are derived from the driver behavior [1], not measured. P03
remains judged by ear under REQ-05.

## Monitoring

`L2_AUDIO` counts processed blocks and stream faults, records the longest iteration time, the
pools' highest use and the TX queue level over time ([decision of 11 November](../../planning/mvp-decisions-2026-11-11.md)). These
values feed VT-02. The iteration time and pool use make a deadline miss visible before it becomes a
stream fault; a TX queue level that drifts over a long run would show that the two links do not
run at the same rate.

## Expected verification

| Scenario | Basis | Expected result |
| --- | --- | --- |
| Boot with both links ready | VT-01, REQ-01 | Stopped; no TX stream and no sound before Start |
| Boot with one device missing | VT-01 | Failure for the missing link; `L2_CONTROL` shows `MICROPHONE_FAILURE` or `AUDIO_OUTPUT_FAILURE` |
| Start, then Stop | REQ-01, REQ-02, VT-04 | `started` after priming and RX before TX; `stopped`, all pool blocks returned, output silent |
| Heart sounds after Start | REQ-02 | Audible on both channels within 2 s |
| Copy step with a known RX block | VT-03 | Both TX slots of every frame equal the left RX slot with its low 8 bits cleared; the right RX slot is ignored |
| Receive wait expires | VT-01 | Microphone failure; stream stopped; catalogue error |
| Thread delayed more than 12 ms | VT-02 | Driver stops the stream; fault reported; no hang and no repeated stale audio |
| 10 min of listening under load | VT-02 | No fault; longest iteration time ≤ 3 ms; pool use never reaches 5 blocks; constant TX queue level (no drift) |
| Tap on the chestpiece | REQ-05 | No noticeable delay |

## Sources

[1] The Zephyr Project, *ESP32 I2S driver and its Kconfig*, source revision
`357467a011cd2557a1a3f0b4be83d817c4addc9b`,
[i2s_esp32.c](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/i2s/i2s_esp32.c)
and
[Kconfig.esp32](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/i2s/Kconfig.esp32),
accessed 10 November 2026. Source reading, not a target measurement.
[Source register](../../../../thesis-material/quellen.md#zephyr_esp32_i2s_driver_357467a).

[2] Nico F., *Hardware Test Protocol — ESP32-S3 Bring-up*, session of 14 August 2026, bring-up
firmware commit `2cd6d4c818be92f0bf1e1181ef0b4cd7de7ceb14`, Zephyr
`357467a011cd2557a1a3f0b4be83d817c4addc9b`: tests T05, T07, T08 and T09 in
[TEST-PROTOCOL.md](../../../../preThesis/06-bringup-zephyr/TEST-PROTOCOL.md), wiring in
[HARDWARE.md](../../../../preThesis/06-bringup-zephyr/HARDWARE.md), sample handling in
[audio_loopback.c](../../../../preThesis/06-bringup-zephyr/src/audio_loopback.c). Own measurement
and code on archived pre-thesis firmware.
[Source register](../../../../thesis-material/quellen.md#nico_bringup_hardware_protocol_20260814).
