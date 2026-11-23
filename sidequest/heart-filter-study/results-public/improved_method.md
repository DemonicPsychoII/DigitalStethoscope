# Improved peak choice and validity rule (run 2 follow-up, EPHNOGRAM + own recordings)

Full tables: `improved_method_tables.md` (generated). Per-row numbers with intervals: `improved_method.csv`; paired
differences: `improved_method_paired.csv`; selection grid on development subjects: `improved_method_selection.csv`;
choice: `improved_method_choice.json`; own recordings: `improved_method_own_recordings.csv`; bit-identity proof:
`improved_method_identity_check.json`. Diagnosis: `one_third_diagnosis.md`.

All EPHNOGRAM numbers are on ECG-reliable windows. Intervals are 95 % subject-bootstrap intervals (2,000 resamples,
seed 20261123, within the subjects of each half). Tolerance max(5 BPM, 10 %). Gross error = more than 20 % off.

## The improved method (new options in `src/hfs/bpm_estimator.py`; existing options unchanged)

`EstimatorConfiguration(envelope_lowpass="two_pole", envelope_lowpass_hz=5.0, peak_choice="submultiple",
lag_weighting="overlap", submultiple_fraction=0.6, submultiple_largest_divisor=4, quality_threshold=0.3,
minimum_rival_margin=0.15, agreement_fraction=0.1)`

1. Envelope, window, mean removal and normalised autocorrelation exactly as in the run-1 final method.
2. **Overlap weighting**: multiply r(L) by (N - L) / N (N = 800 window samples). This restores the mild preference
   for short shifts that the per-shift normalisation removes (diagnosis).
3. **Sub-multiple check**: take the highest peak L of the weighted curve; for divisor 4, 3, 2 in that order, look for
   a peak within 10 % of L / divisor; take the first one whose weighted value is at least 0.6 x the highest.
4. **Validity** (all must hold): rate 30-200 BPM; clipping share as before; r(chosen) >= 0.3; **margin** r(chosen)
   minus the highest peak that is neither a multiple nor a sub-multiple (1/2-1/4) of the chosen lag >= 0.15;
   **agreement**: the estimate is within 10 % of at least one of the previous two estimates.

Cost against the run-1 final method: the autocorrelation (about 0.24 million multiply-adds per update) is unchanged.
Added per update: at most 402 multiplies for the weighting (the weight can be computed as (N - L) / N on the fly, or
held as a 402-entry float32 table = 1.6 KB), one weighted copy of the correlation (1.6 KB, or none if weighted in
place after the quality value is read), the peak list (at most 402 entries; run 1 already has one), three short scans
of the peak list, one scan for the rival peak, and two floats of history. Less than 1 % more work, fixed-size arrays, no
dynamic allocation, float32 throughout. The new choice is the numba function `_choose_lag` and is written in loops
that translate directly to C.

## Honest selection

- Subject split (fixed seed 20261123, stratified so both halves contain stress tests): development S001, S003, S004,
  S006, S007, S011, S013, S014, S015, S016, S017; test S002, S005, S008, S009, S010, S012, S018, S019, S020, S021, S022
  (test subject S022 has no ECG-reliable window, so 10 test subjects count).
- Chosen on development subjects only, 40-150 Hz, rest and overload levels pooled, by mean error: 2 envelopes x 2
  weightings x 26 peak choices (highest, half check, first-above 0.6-0.95, sub-multiple 0.5-0.9 with divisors up to 3
  or 4, harmonic sum). Then the validity rule: quality 0.3-0.6 x margin off/0-0.15 x agreement off/10 %/15 %, choosing the
  lowest share of gross errors among valid windows that loses at most 5 points of valid share against the quality
  threshold alone. (A first attempt required >= 80 % valid; no rule reached that on development data, so it fell back to
  a 49 %-valid rule; I replaced it with the 5-point rule before looking at the test half.)
- Development, 40-150 Hz, both levels pooled: run-1 final method 21.56 BPM; overlap + sub-multiple 0.6 up to 4:
  8.84 BPM (best); first-above 0.65 with overlap: 9.27; sub-multiple without overlap: 9.59; harmonic sum: 11.02 with
  overlap, 28.79 without.
- Test numbers were computed once with the chosen settings; nothing was changed after seeing them.

## Results, 40-150 Hz, overall

| half | level | method | MAE (interval) | median | within tolerance | gross: half / third / double / other | valid | MAE of valid | gross among valid | subjects / windows |
|---|---|---|---|---|---|---|---|---|---|---|
| development | rest | run-1 final | 24.87 (20.47-28.36) | 1.22 | 63.7 % | 3185 / 7244 / 427 / 4935 | 75.5 % | 21.36 | 26.6 % | 11 / 44908 |
| development | rest | improved | 11.51 (8.36-16.09) | 0.63 | 81.4 % | 1799 / 848 / 908 / 4136 | 69.4 % | 3.43 | 3.6 % | 11 / 44908 |
| development | overload | run-1 final | 18.25 (14.18-21.17) | 0.55 | 76.2 % | 1710 / 5913 / 233 / 2536 | 88.3 % | 15.97 | 20.0 % | 11 / 44908 |
| development | overload | improved | 6.18 (3.74-9.68) | 0.36 | 91.9 % | 774 / 122 / 656 / 1751 | 83.6 % | 2.63 | 2.5 % | 11 / 44908 |
| **test** | rest | run-1 final | 28.39 (20.98-36.17) | 2.98 | 57.5 % | 4070 / 6781 / 151 / 6015 | 71.8 % | 22.76 | 29.4 % | 10 / 42899 |
| **test** | rest | improved | 13.14 (7.14-19.70) | 0.95 | 75.8 % | 2600 / 1351 / 253 / 4679 | 65.4 % | 3.81 | 5.8 % | 10 / 42899 |
| **test** | overload | run-1 final | 22.16 (16.49-27.64) | 1.25 | 69.0 % | 3290 / 6024 / 89 / 3105 | 75.2 % | 19.44 | 24.9 % | 10 / 42899 |
| **test** | overload | improved | 7.20 (4.53-10.10) | 0.55 | 87.7 % | 1672 / 492 / 149 / 1984 | 70.3 % | 2.87 | 3.3 % | 10 / 42899 |

Paired difference improved minus run-1 final (same filter, same windows), test half: rest -15.25 BPM (-21.14 to -9.37),
overload -14.95 (-20.05 to -9.78); development half: rest -13.36 (-16.14 to -9.19), overload -12.07 (-14.92 to -7.83).
The improvement holds on every filter in both halves (-11.9 to -18.8 BPM, all intervals below zero; table at the end
of `improved_method_tables.md`). One-third errors drop by 80-98 %; half-rate errors by 36-55 %; "other" errors by 16-36 %.

The validity rule removes most wrong numbers from the display: among windows shown as valid, gross errors fall from
29.4 % to 5.8 % (test, rest level) and from 24.9 % to 3.3 % (test, overload). It shows fewer windows (65-70 % instead of
72-75 %).

## By activity group (40-150 Hz, test subjects; development in the tables)

| level | activity | method | MAE | within tolerance | valid | MAE of valid | gross among valid | target met | subjects / windows |
|---|---|---|---|---|---|---|---|---|---|
| rest | seated rest | run-1 final | 3.80 | 85.1 % | 95.6 % | 3.34 | 1.7 % | yes | 4 / 1818 |
| rest | seated rest | improved | 3.74 | 85.1 % | 86.6 % | 2.73 | 0.6 % | **no** (valid share) | 4 / 1818 |
| rest | lying | run-1 final | 5.38 | 87.9 % | 87.3 % | 3.37 | 3.8 % | no | 3 / 5845 |
| rest | lying | improved | **8.05** | 86.9 % | 78.2 % | 2.05 | 1.4 % | no | 3 / 5845 |
| rest | walking | run-1 final | 26.33 | 52.1 % | 70.4 % | 19.55 | 35.7 % | no | 8 / 13442 |
| rest | walking | improved | 16.31 | 67.3 % | 62.6 % | 7.71 | 14.5 % | no | 8 / 13442 |
| rest | stress tests | run-1 final | 41.14 | 44.9 % | 66.7 % | 38.64 | 42.5 % | no | 6 / 17998 |
| rest | stress tests | improved | 15.16 | 73.4 % | 61.2 % | 2.49 | 2.9 % | no | 6 / 17998 |
| rest | steady pedalling | run-1 final | 22.40 | 76.5 % | 65.4 % | 11.71 | 14.0 % | no | 2 / 3796 |
| rest | steady pedalling | improved | 4.67 | 95.6 % | 65.0 % | 0.39 | 0.0 % | no | 2 / 3796 |
| overload | seated rest | run-1 final | 3.68 | 86.3 % | 96.3 % | 3.13 | 1.2 % | yes | 4 / 1818 |
| overload | seated rest | improved | 3.62 | 86.2 % | 87.6 % | 2.59 | 0.6 % | no | 4 / 1818 |
| overload | lying | run-1 final | 4.72 | 89.1 % | 68.1 % | 1.95 | 1.2 % | no | 3 / 5845 |
| overload | lying | improved | 6.48 | 88.6 % | 62.2 % | 1.45 | 0.4 % | no | 3 / 5845 |
| overload | walking | run-1 final | 18.88 | 66.6 % | 78.1 % | 15.26 | 25.7 % | no | 8 / 13442 |
| overload | walking | improved | 9.77 | 81.7 % | 71.2 % | 5.44 | 7.4 % | no | 8 / 13442 |
| overload | stress tests | run-1 final | 31.64 | 61.1 % | 81.9 % | 30.27 | 35.2 % | no | 6 / 17998 |
| overload | stress tests | improved | 5.64 | 91.1 % | 78.1 % | 1.76 | 2.0 % | no | 6 / 17998 |
| overload | steady pedalling | run-1 final | 24.49 | 75.1 % | 34.4 % | 5.80 | 7.7 % | no | 2 / 3796 |
| overload | steady pedalling | improved | 8.35 | 92.6 % | 34.3 % | 0.33 | 0.0 % | no | 2 / 3796 |

Groups: seated rest = 30 s records and "sitting on armchair"; lying = "laying on bed"; walking = constant-speed walk and
the walk/sit-stand protocol; stress tests = Bruce treadmill and bicycle stress tests; steady pedalling = "pedaling a
stationary bicycle" (constant load, not a stress test, kept separate).

**Where the improved method is worse:** lying (test rest 5.38 -> 8.05 BPM; development 16.94 -> 20.53; all subjects
11.6 -> 14.8) and below 70 BPM (test 4.33 -> 8.72). Seated rest is unchanged on test subjects (3.80 -> 3.74) but worse on
development subjects (1.61 -> 3.74) and on all subjects (2.7 -> 3.7). At slow rates the 0.6 fraction lets a sub-multiple
peak (most likely the S1-to-S2 spacing at about L/2 or L/3) win; the "other" errors rise (test lying 279 -> 404).
**Acceptance target** (valid share >= 90 % and MAE of valid <= 5 BPM): met only for seated rest, and only with the run-1
rule; the improved validity rule shows 86.6-87.6 % of seated-rest windows on test subjects (93 % on development), so
the target fails there by the valid share, although its valid windows are more accurate. Walking (development,
overload) is the only other group that meets it (90.5 %, 3.29 BPM). No group meets it on test subjects with the
improved rule. On test subjects, stress tests and steady pedalling reach a low error on valid windows (0.3-2.5 BPM) and walking 5.4-7.7 BPM, but they show only 34-78 % of windows.

## By ECG rate band (40-150 Hz, test subjects, rest level)

| band | run-1 final MAE | improved MAE | improved within tolerance | improved valid | improved gross among valid | subjects / windows |
|---|---|---|---|---|---|---|
| below 70 | 4.33 | **8.72** | 87.0 % | 76.7 % | 0.65 % | 7 / 3824 |
| 70-90 | 15.41 | 13.04 | 66.4 % | 69.8 % | 16.0 % | 9 / 7399 |
| 90-110 | 25.72 | 14.57 | 72.0 % | 61.7 % | 5.9 % | 8 / 13366 |
| 110-130 | 34.84 | 17.22 | 71.9 % | 53.9 % | 3.7 % | 8 / 11669 |
| 130-150 | 37.81 | 6.08 | 93.0 % | 77.1 % | 1.7 % | 7 / 3479 |
| 150-170 | 53.64 | 2.23 | 98.1 % | 93.0 % | 0.26 % | 7 / 1681 |
| above 170 | 77.75 | 8.90 | 93.0 % | 79.8 % | 0.0 % | 6 / 1481 |

The remaining problem zone is 70-130 BPM (walking), where half-rate and "other" errors remain and 16 % of the windows
shown as valid at 70-90 BPM are still grossly wrong.

## Own recordings (five recordings, 255 windows, 226 reliable)

| filter | method | MAE reliable | MAE all | within tolerance (all) | gross (all) | valid (all) |
|---|---|---|---|---|---|---|
| 40-150 Hz | run-1 final (baseline reproduced) | 0.301 | 0.354 | 100 % | 0 | 99.6 % |
| 40-150 Hz | improved | 0.301 | 0.354 | 100 % | 0 | 97.6 % |
| 25-150 Hz | run-1 final | 0.296 | 0.691 | 99.6 % | 1 | 100 % |
| 25-150 Hz | improved | 0.296 | 0.358 | 100 % | 0 | 97.3 % |
| 60-150 Hz | run-1 final / improved | 0.307 / 0.307 | 0.365 / 0.365 | 100 % / 100 % | 0 / 0 | 99.2 % / 97.3 % |
| 80-150 Hz | run-1 final / improved | 0.304 / 0.305 | 0.365 / 0.521 | 100 % / 99.6 % | 0 / 1 | 98.4 % / 96.1 % |
| 4+4 60-150 Hz | run-1 final / improved | 1.165 / 0.323 | 3.487 / 2.741 | 96.1 % / 96.9 % | 10 / 8 | 99.6 % / 94.5 % |
| no filter | run-1 final / improved | 0.422 / 0.422 | 4.217 / 2.839 | 93.7 % / 95.7 % | 16 / 11 | 98.0 % / 93.7 % |

On the own recordings the improved method gives the same error at 30-150, 40-150, 50-150, 60-150 and 40-400 Hz
(30-150 Hz: 0.354 vs 0.353 BPM on all windows) and is better without a filter, at 25-150 Hz and 4+4 60-150 Hz. It is
slightly worse at 80-150 Hz on all windows (0.521 vs 0.365 BPM, 1 gross error vs 0; reliable windows 0.305 vs 0.304). The only cost is 2-4 points fewer windows shown as valid (the
agreement and margin rules; 97.6 % at 40-150 Hz, so the >= 90 % target is still met there).

**Existing options unchanged:** all 31 distinct run-1 configurations in `cache/bpm/` were re-run on recording rest-1
with the extended module (40-150 Hz where cached, else 25-150 Hz) and give bit-identical estimate, valid flag, quality,
margin and reason (`improved_method_identity_check.json`). Configuration keys (and so all cache keys) of existing
configurations are unchanged because the new fields default to "off".

## Filter ranking

Unchanged by the improved method. At rest level the ranking by MAE stays 4+4 60-150 < 60-150 ~ 80-150 < 50-150 <
40-150 < 40-400 < 30-150 < 25-150 < no filter, in both halves; at overload level 40-150 and 50-150 stay best. The
lower-edge differences shrink: test rest 25 / 40 / 60 Hz = 15.9 / 13.1 / 11.5 BPM improved (32.1 / 28.4 / 25.6 run-1);
test overload 8.0 / 7.2 / 7.6 (24.1 / 22.2 / 21.6). On the own recordings 4+4 60-150 Hz is clearly worse (2.74 BPM on
all windows, 8 gross errors) and 40-150 Hz has no gross error, so the recommendation **40-150 Hz** stands.

## Implementation check of this study

The EPHNOGRAM numbers come from per-second correlations cached as float16 (`cache/bpm-improved/`) and a numba batch
version of the new peak choice (`bpm_improved_method_common.choose_batch`, which calls the module's `_choose_lag`).
Against the cached run-2 estimates of the run-1 methods it differs in 2 of 1,800 windows of a long record (near-tie
peaks flipped by float16 rounding) and in none of the 30 s records; all methods go through the same path, so comparisons
are paired. The own-recording numbers use the real streaming `BPMEstimator`.

## Limits

- Tuned on one public database: one sensor and one recording setup, a model of our capture chain instead of our device,
  22 young male subjects (11 for development, 10 scorable for test). Intervals are wide (test rest MAE 7.1-19.7 BPM);
  activity groups have 2-8 test subjects (steady pedalling: 2), so group numbers are indicative only.
- The 0.6 fraction trades slow-rate accuracy for exercise accuracy; on lying and below 70 BPM the method is worse. A
  rate-dependent fraction or a second check at slow rates could recover this but was not tested (follow-up).
- The faint one-third-rate component in the envelope is real but its source (breathing, stride or pedal rhythm) is not
  established; the database has no breathing or cadence channel.
- The validity rule is causal but uses the last two estimates; in `public_evaluation_common.estimate_record`, which
  shares one estimator object across configurations, the agreement history would mix configurations, so do not use the
  new agreement option through that function (the study uses its own batch path).
- The acceptance target (>= 90 % valid with <= 5 BPM) is not met during exercise on this database with either method.

## Rerun

```
.venv/Scripts/python.exe -I src/bpm_improved_method_compute.py --workers 6      # correlations, about 8 min
.venv/Scripts/python.exe -I src/bpm_improved_method_diagnosis.py               # one-third diagnosis, about 2 min
.venv/Scripts/python.exe -I src/bpm_improved_method_select.py                  # development-half selection
.venv/Scripts/python.exe -I src/bpm_improved_method_own.py                     # identity proof and own recordings
.venv/Scripts/python.exe -I src/bpm_improved_method_report.py                  # both halves, all filters
.venv/Scripts/python.exe -I src/bpm_improved_method_figures.py                 # page figures (refuses to overwrite)
```
