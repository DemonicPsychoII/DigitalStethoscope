# Audio thread, processing budget, sample alignment and stream faults — 11 November 2026

Nico decided on 11 November 2026 in T3 Code (conversation link not recorded), walking through the
AUDIO architecture and design of the first audio path, how the audio thread works and how it handles
faults. These are project decisions, not measurements. They build on the
[first audio path decision of 10 November](mvp-decisions-2026-11-10.md#first-audio-path).

## Decision

1. **Ownership and control.** `L1_I2S` owns the I2S block pools and the driver calls; `L2_AUDIO`
   borrows one RX and one TX block per iteration. RX and TX keep separate pools, and the audio thread
   copies between them. `L2_CONTROL` sends Start and Stop through a message queue; `L2_AUDIO`
   reports started, stopped and faults through a message queue.
2. **One deterministic processing path.** One audio thread reads a block, processes it and sends it.
   The thread runs at the highest application thread priority. Processing in an interrupt callback
   and separate RX and TX threads were considered and not chosen.
3. **Processing budget of 3 ms.** One iteration, from the received block to the queued TX block, may
   take at most 3 ms of the 4 ms block period (P02). This replaces the 2 ms proposal.
4. **Four primed TX blocks.** TX starts with four silent blocks. The thread then has 12 ms for
   processing and lateness together, so with the 3 ms budget it may start a block up to 9 ms
   late, and the transport delay is a constant 16 ms.
5. **Left-aligned samples.** The mono working sample keeps the 24-bit microphone value left-aligned
   in 32 bits with the low 8 bits cleared.
6. **Stream faults need a restart.** When a stream fails, `L2_AUDIO` stops both links and reports
   the failed link; `L2_CONTROL` shows `MICROPHONE_FAILURE` or `AUDIO_OUTPUT_FAILURE`, which require
   a device restart as in the feedback catalogue. No automatic stream restart.
7. **20 ms block waits.** The thread waits at most 20 ms (five block periods) for an RX block or a
   free TX block before it reports a microphone or output failure.
8. **Monitoring.** `L2_AUDIO` records the longest iteration time, the pools' highest use, processed
   blocks and stream faults, and the TX queue level over time.

## Applied in

- [AUDIO design](../design/AUDIO/interfaces-and-behavior.md)
- Parameters P02 and P11 in the [system parameters](../design/system/parameters.md) and the
  `AudioBlock` contract in the [system design](../design/system/interfaces-and-behavior.md)
