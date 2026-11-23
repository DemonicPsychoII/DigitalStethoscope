# Heart filter study (TICKET-189), first simulation

Decided by Nico on 23 November 2026:

1. Data: 4 own recordings on Nico's chest through the real chest-piece, tube and INMP441 (2 resting, 2 at higher heart rate).
2. Listening (Murmur/Raw) filter: loudest audible without distortion or too much other sound, judged subjectively; prepare listening samples to judge.
3. BPM filter: highest accuracy of an on-ESP32-S3 BPM estimate over an 8 s rolling window held in PSRAM.
4. Try all filter variants (types, orders, band edges).
5. Simulation as close to the real device as possible; firmware and measurements are in the DigitalStethoscope repository.
6. Everything lives in this folder.

Work is done by a Fable subagent with a 5 h limit, started only when Nico says so.

## Recordings

`record_heart.py <name>` records raw from the capture firmware (COM4, 16 kHz, 24-bit) into `recordings/<name>/`;
`quick_check.py <wav>` prints level, clipping and a rough BPM per 8 s window.

### Recorded 23 November 2026 (Nico, membrane side, capture firmware, 60 s each, no reference heart rate)

| Recording | State | Overload (samples >= 0.99 FS) | Rough BPM (25-150 Hz envelope autocorrelation, 8 s windows) |
| --- | --- | --- | --- |
| rest-1 | resting, first spot | 117, only at 39.5-40.1 s (movement) | 73-86 |
| rest-2 | resting, re-placed lower | 0 | 80-87 |
| elevated-1 | after about 1 min exercise, lower spot | 57, only at 3.7 s | 128 falling to 88 |
| elevated-2 | after 1.5-2 min exercise, lower spot | 2795, on heartbeats throughout | 141 falling to 120 |
| elevated-3 | as elevated-2 with lighter pressure | 2352, on heartbeats in the first 30 s | 149 falling to 116 |

Finding: at high post-exercise heart rates the chest-piece + tube + INMP441 chain reaches digital full scale on every beat, even with lighter pressure; most energy lies below 150 Hz, a large part below 20 Hz. The real device will clip the same way. elevated-2 and elevated-3 are kept as realistic overload cases.

The rough BPM column is an unverified quick check, not a reference. There is no independent reference heart rate (no ECG, watch or oximeter).
