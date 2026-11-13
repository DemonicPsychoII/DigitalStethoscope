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
2. **Listening starts at the started event.** The system enters Listening when `L2_AUDIO` reports
   that the stream has started, not when the Start command is sent.
3. **Non-audio halting faults during listening are deferred.** When one of the restart-required
   errors that are not audio errors (`SESSION_CONTEXT_CHANGE`, `CONTROL_INPUT_FAILURE`, `HEART_RATE_WORKER_STALL` and `SETTINGS_SAVE_FAILURE`) occurs while listening, its indication is muted and listening continues; the error
   is shown, and its halt and clear rule applies, after the operator stops the examination
   manually.
4. **An audio fault halts the device.** In Fault, `L2_AUDIO` cannot be started again; every input,
   including Start, is blocked until restart.
5. **An audio fault drops both links at once.** On any audio fault, including a failed start, both
   links are dropped at once with no 8 ms wait, as the 10 November decision says. The normal Stop
   keeps its STOP, 8 ms wait and DROP sequence. Nico: "yes to dropping both".

## Applied in

- [AUDIO architecture](../architecture/AUDIO/README.md) and
  [AUDIO design](../design/AUDIO/interfaces-and-behavior.md)
- Parameters P01, P02 and P11 in the [system parameters](../design/system/parameters.md); the
  `AudioBlock` frame count and the memory accounting in the
  [system design](../design/system/interfaces-and-behavior.md#ownership-memory-and-queues)
- D10 in the [decision register](implementation-readiness.md#decision-register) and the
  integration notes of the [thesis material](../../../thesis-material/README.md)
- Decision 2 in the [MVP session state view](../architecture/system/mvp-session-state.puml):
  Listening is entered when AUDIO reports started
- Decision 3 in the system session and workflow views and P12: applied by
  [#162](https://github.com/DemonicPsychoII/DigitalStethoscope/pull/162)
