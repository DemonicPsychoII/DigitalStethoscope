# Public murmur excerpts (CirCor DigiScope 1.0.3, chain-modelled)

Each `capture.wav` is 8 s of a CirCor recording passed through the capture-chain model (`hfs.chain_model.model_through_capture_chain`, `level_condition="rest"`, `spectrum_variant="microphone_only"`, CirCor calibration, seed = CRC-32 of the file stem): 24-bit mono 16 kHz, the same format as `recordings/<name>/capture.wav`, so the device chain takes it unchanged. Not filtered. The source is sampled at 4 kHz, so there is nothing above 2 kHz.

Selection rule (fixed before listening): consecutive complete annotated heart cycles for at least 8 s, the patient's most audible location, no modelled sample at the 24-bit limit in the excerpt; murmurs: the recording with the largest systole-to-diastole power ratio (50-800 Hz) in its group; no murmur: same age category and location as the loud murmur, among the 40 closest in height, the median ratio.

| Label | Patient | Recording | Location | Time range in the source (s) | Age category, sex, height | Labels | Systole/diastole 50-800 Hz (dB) |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| `murmur-loud` | 84949 | 84949_TV | TV | 1.231-9.231 | Child, Female, 112.0 cm | systolic murmur grade III/VI, timing Holosystolic, shape Plateau, pitch High, quality Harsh; heard at AV+MV+PV+TV, most audible at TV | +22.4 |
| `murmur-soft` | 50099 | 50099_PV | PV | 0.560-8.560 | Child, Male, 114.0 cm | systolic murmur grade I/VI, timing Holosystolic, shape Diamond, pitch High, quality Harsh; heard at MV+PV+TV, most audible at PV | +15.2 |
| `no-murmur-child` | 50788 | 50788_TV | TV | 15.640-23.640 | Child, Female, 111.0 cm | murmur Absent | +0.4 |

Optional fourth (diastolic murmur, not written): patient 50277, 50277_PV, 0.980-8.980 s, diastolic grade III/IV, timing Early-diastolic, pitch Medium, quality Blowing; systolic grade III/VI. 4 diastolic-murmur recording(s) with 8 s of clean annotation exist in total (`excerpts.json`).

## Source and licence

CirCor DigiScope Phonocardiogram Dataset, version 1.0.3, PhysioNet, DOI 10.13026/tshs-mw03, https://physionet.org/content/circor-heart-sound/1.0.3/ (accessed 2026-11-23). Licence: Open Data Commons Attribution License v1.0 (`public-data/circor-1.0.3/LICENSE.txt`); attribution required when these excerpts are shared. Dataset paper: J. Oliveira et al., "The CirCor DigiScope Dataset: From Murmur Detection to Murmur Classification", 2022, arXiv:2108.00813 (journal pages not verified here).

Written by `src/listening_public.py excerpts`.
