| | Own recordings | Public data with ECG (modelled) | Public murmur data (modelled) | Public data with ECG, after matching | Public murmur data, after matching |
| --- | --- | --- | --- | --- | --- |
| Heart-sound level at rest (loudness of the beats, below full scale) | -9.6 dB | -9.7 dB | -9.7 dB | -9.6 dB | -9.6 dB |
| Share of energy below 20 Hz (rest) | 52 % | 17 % | 2.5 % | 28 % | 2.8 % |
| Share of energy 20-150 Hz (rest) | 48 % | 80 % | 43 % | 72 % | 83 % |
| Share of energy 150-800 Hz (rest) | 0.1 % | 2.1 % | 40 % | 0.2 % | 7.1 % |
| Share of energy above 800 Hz (rest) | below 0.1 % | below 0.1 % | 7.2 % | below 0.1 % | 2.5 % |
| Sound between beats relative to the heart sounds (rest; lower is quieter) | -21.2 dB | -13.8 dB | -11.1 dB | -16.4 dB | -14.6 dB |
| Share of beats reaching full scale, resting level | 1.2 % | 3.4 % | 9.2 % | 4.5 % | 12 % |
| Share of beats reaching full scale, overload level | 34 % | 34 % | 34 % | 34 % | 34 % |

Source: `calibration/how_close.csv` (written by `src/chain_model_calibrate.py`; medians over 20 EPHNOGRAM and 200 CirCor recordings, own: rest-1, rest-2, elevated-1 at rest, elevated-2, elevated-3 at overload; beat shares pool all beats; the overload level of the model was set to reach the own 34 % of beats).
