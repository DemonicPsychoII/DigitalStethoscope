# Audio architecture

The audio path carries microphone audio to the DAC line output over two I2S links.

| View | Editable source | Preview |
| --- | --- | --- |
| Audio path | [puml/audio-path.puml](puml/audio-path.puml) | [SVG](rendered/audio_path.svg) |

## Responsibilities

| Component | Responsible for | Not responsible for |
| --- | --- | --- |
| L0 Zephyr I2S driver | Clocking and DMA on the microphone receive link and the DAC transmit link; queues of completed RX blocks and pending TX blocks | Processing; recovery after its error state |
| `L1_I2S` | Configuration of both links, the RX and TX block pools in internal RAM, priming TX with silence, start and stop, lending received blocks and accepting filled TX blocks; driver errors as typed outcomes | Sample processing, retries, fault policy, indication |
| `L2_AUDIO` audio thread | The block loop: take the left slot, run the processing step, write the result into both TX slots; return every block it borrowed before the next block; report started, stopped and faults | Mode, session or volume state; driver calls other than through `L1_I2S` |
| `L2_CONTROL` | Start and Stop commands to `L2_AUDIO`; the error indication for reported faults | Audio data |

The processing step applies the selected listening filter (`L1_FILTER`) and the volume. The audio
thread hands copies of the original-rate blocks to the BPM worker shown in the
[threads view](../system/README.md). Listening filter, volume control and the analysis fan-out leave
the transport boundary unchanged.

## Data path and block ownership

- Every block has exactly one holder at a time: the driver (DMA or queue), `L1_I2S`, or the audio
  thread. `L2_AUDIO` holds at most one received block and one TX block per iteration. No transport
  block leaves the audio thread; BPM analysis receives copies.
- Both pools are fixed at build time in internal, DMA-capable RAM without PSRAM.
- The Zephyr ESP32 I2S driver supports only two-slot frames [1]. RX blocks therefore contain a
  filled left slot and an unused right slot, and TX blocks carry both slots.
- The microphone's L/R pin is tied to ground, which selects the left slot [2].

## Clocking

- Both links use the same sample rate, slot width and word size.
- Both I2S controllers share one clock source and identical stream settings, so the microphone and
  the DAC run at the same sample rate without rate adaptation [1].
- A different word size on one link would change its master-clock multiple and could make the
  rates differ slightly [1].

## Stream faults

- When the audio thread falls behind, the driver stops the stream: an empty TX queue sets its error
  state and stops TX, and RX enters the error state when no free pool block is left [1].
- The stream stays stopped until it is prepared and started again [1].
- The pool sizes therefore bound how late the audio thread may be, and `L2_AUDIO` treats a driver
  error as a fault it reports to `L2_CONTROL`.
- `L2_AUDIO` starts and stops the stream only on a command from `L2_CONTROL`. After a fault it
  starts no stream until the device restarts.

## Expected verification

| Scenario | Basis | Expected result |
| --- | --- | --- |
| Power-on, then wait without Start | [REQ-01](../../requirements/system-requirements.md#req-01), VT-01 | No sound on either DAC channel; no TX stream before Start |
| Start with the chestpiece on the chest | [REQ-02](../../requirements/system-requirements.md#req-02) | Heart sounds audible on both channels within 2 s of Start |
| Tap the chestpiece during listening | [REQ-05](../../requirements/system-requirements.md#req-05), VT-02 | Tap heard together with the touch, no echo or lag |
| Microphone or DAC link fails to start | VT-01 | Silent output and the error indication for the failed link |
| Audio thread delayed beyond the pool reserve | VT-02 | Stream stops, fault reported, output silent; no silent hang |
| Listening for at least 10 minutes | VT-02 | No stream fault; TX queue level stays constant, so the two links do not drift |
| Processing step with a known input block, Raw selected and full volume | VT-03 | Both TX slots carry the sample of the received left slot |

## Sources

[1] The Zephyr Project, *ESP32 I2S driver and its Kconfig*, source revision
`357467a011cd2557a1a3f0b4be83d817c4addc9b`,
[i2s_esp32.c](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/i2s/i2s_esp32.c)
and
[Kconfig.esp32](https://github.com/zephyrproject-rtos/zephyr/blob/357467a011cd2557a1a3f0b4be83d817c4addc9b/drivers/i2s/Kconfig.esp32),
accessed 10 November 2026.

[2] TDK InvenSense, *INMP441 Omnidirectional Microphone with Bottom Port and I²S Digital Output*,
document DS-INMP441-00, revision 1.0, 6 February 2014, section "I²S Data Interface" (24-bit words,
64 SCK per stereo frame, L/R pin selects the channel, data pin tri-stated after the LSB, p. 11) and
Figure 9 (mono output, left channel, p. 12),
[datasheet](https://www.farnell.com/datasheets/1824785.pdf), accessed 11 November 2026.
