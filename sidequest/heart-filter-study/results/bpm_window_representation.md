# Window representation: streaming envelope versus filtered audio held in PSRAM

Estimator: envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check; analysis filter: decimated design (64-tap anti-alias FIR, 1 kHz, Butterworth).
Streaming: causal envelope at 16 kHz -> 100 Hz ring buffer of 800 float32 (3.2 kB).
Audio window: 8000 float32 of filtered audio at 1 kHz (32 kB); at each update |x| -> forward-backward two-pole 5 Hz -> 100 Hz -> same autocorrelation.

| filter | representation | window bytes | MAE reliable | within tolerance reliable | gross errors reliable | MAE all windows | gross errors all windows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| decimated_hp2_25_lp2_150 | streaming envelope | 3200 | 0.30 | 100 % | 0 | 0.69 | 1 |
| decimated_hp2_25_lp2_150 | filtered audio at 1 kHz | 32000 | 0.29 | 100 % | 0 | 0.86 | 2 |
| decimated_hp4_30_lp2_300 | streaming envelope | 3200 | 0.29 | 100 % | 0 | 0.35 | 0 |
| decimated_hp4_30_lp2_300 | filtered audio at 1 kHz | 32000 | 0.26 | 100 % | 0 | 0.59 | 1 |
| decimated_hp2_40_lp2_300 | streaming envelope | 3200 | 0.30 | 100 % | 0 | 0.35 | 0 |
| decimated_hp2_40_lp2_300 | filtered audio at 1 kHz | 32000 | 0.28 | 100 % | 0 | 0.61 | 1 |
