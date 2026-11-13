# Audio block size and pool sizes confirmed — 13 November 2026

Nico decided on 13 November 2026 in T3 Code (conversation link not recorded), reviewing the
diagram audit of the audio architecture and design, which block size and pool sizes the project
goes with. This is a project decision, not a measurement. It builds on the
[first audio path decision of 10 November](mvp-decisions-2026-11-10.md#first-audio-path) and the
[audio thread decisions of 11 November](mvp-decisions-2026-11-11.md).

The audit found that the shared system design on `integration` (commit `994ce24`) still specified
128-frame blocks of 8 ms (P01), at most 4 ms of execution per block (P02) and four RX and four TX
blocks (P11), while the audio design branch specified 64-frame blocks, at most 3 ms and five plus
five blocks.

## Decision

1. **64-frame blocks and five plus five blocks.** The audio path uses 64-frame blocks of 4 ms at
   16 kHz and pools of five RX and five TX blocks. The processing budget stays at most 3 ms per
   block. Statements of 128-frame or 8 ms blocks, a 4 ms execution budget or four plus four blocks
   no longer describe the design.

## Applied in

- [AUDIO architecture](../architecture/AUDIO/README.md) and
  [AUDIO design](../design/AUDIO/interfaces-and-behavior.md)
- Parameters P01, P02 and P11 in the [system parameters](../design/system/parameters.md); the
  `AudioBlock` frame count and the memory accounting in the
  [system design](../design/system/interfaces-and-behavior.md#ownership-memory-and-queues)
- D10 in the [decision register](implementation-readiness.md#decision-register) and the
  integration notes of the [thesis material](../../../thesis-material/README.md)
