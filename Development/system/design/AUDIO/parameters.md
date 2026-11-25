# Audio parameters

These parameters define the timing, processing and measurement values of `L2_AUDIO` with `L1_I2S`, `L1_FILTER` and `L1_BPM`. The block pool, queue and block-wait capacities are [P11](../cross-module.md#parameters), and the fault response is [P12](../FEEDBACK/parameters.md).

| ID | Parameter | Value | Basis | Owners |
|---|---|---|---|---|
| P01 | Sample rate / block | 16,000 Hz / 64 frames; 4 ms | [AUDIO stream configuration](interfaces-and-behavior.md#stream-configuration) | L2_AUDIO, L1_I2S |
| P02 | Execution budget | ≤3 ms critical-path execution per block (read, process, send; 75 % of the period); deadline 4 ms | 75 % of the 4 ms block period | L2_AUDIO, L1_FILTER, MONITOR |
| P03 | Live latency | <30 ms | [REQ-05](../../requirements/system-requirements.md#req-05) | L2_AUDIO, L1_FILTER |
| P05 | BPM session duration | Stop <15 s cancels the session without a result; a manual Stop ≥15 s finalizes the session | [REQ-06](../../requirements/system-requirements.md#req-06), [REQ-07](../../requirements/system-requirements.md#req-07) | L2_AUDIO, L1_BPM |
| P06 | BPM error | Acceptance ±5 BPM or ±10 % against a pulse oximeter or smartwatch reference | [REQ-06](../../requirements/system-requirements.md#req-06) | L2_AUDIO, L1_BPM |
| P07 | BPM validity / coverage | Coverage is the union of accepted window intervals clipped to the session bounds; overlaps count once. A finalized session is either valid with a BPM value or invalid without a numeric value | [REQ-06](../../requirements/system-requirements.md#req-06), [REQ-08](../../requirements/system-requirements.md#req-08) | L2_AUDIO, L1_BPM |
| P08 | Filter assignment | The Raw position applies no band filter; the Murmur and BPM positions each apply their own band filter. BPM analysis always applies the BPM filter, and the BPM listening position applies the same coefficients | [REQ-03](../../requirements/system-requirements.md#req-03) | L2_AUDIO, L1_FILTER, L1_BPM |
| P09 | Transition smoothing | A change of the listening filter or of the volume is applied as a smooth transition | – | L2_AUDIO, L1_FILTER |
| P17 | Test recording format | Host-side mono PCM WAV | – | L2_AUDIO, L1_BPM |
| P20 | Startup mode | Idle at zero gain; explicit Start listening | [REQ-01](../../requirements/system-requirements.md#req-01) | L2_CONTROL, L2_AUDIO |
