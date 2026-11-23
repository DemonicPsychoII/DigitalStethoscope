# BPM filter evaluation: summary

Generated 2026-11-23T02:06 by `src/bpm_evaluate.py --reference reference`.

Reference: `C:\Users\nicop\Desktop\heart-filter-study\reference` (independent beat reference, other agent). Metrics are on windows the reference marks `reliable` unless a column says "all windows".

Windows: 255 (8 s, ending at each full second 10-60 s, 5 recordings), 226 marked reliable. Windows overlap by 7 s: about 7 independent windows per recording, 35 in total.

Ranking metric: mean absolute error (MAE) of the raw per-window estimate on reliable windows, validity ignored; ties broken by the share within tolerance max(5 BPM, 10 %). Gross error: more than 20 % off.

## Answer

Best combination: **elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check]**, MAE 0.3 BPM, 100 % within tolerance, 0 gross errors, 100 % valid.
Final estimator [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] chosen as the stage-3 configuration with the lowest mean MAE over the top 10 filters and the 3 baselines (then fewest gross errors), then run over all filters (stage 4).
Design candidate BPM 25-150 Hz Butterworth 2+2 with the default estimator: MAE 0.7 BPM, 100 % within tolerance; with the best estimator variant: MAE 0.3 BPM, 100 % within tolerance.
Candidates statistically indistinguishable from the best (moving-block bootstrap, 8-window blocks, 95 % interval of the MAE difference includes 0, among the top 150 rows): **147**.

Cheapest candidate within noise of the best: **decimated_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check]**, 5 multiplies per sample, MAE 0.3 BPM.

Bootstrap 95 % interval of MAE(candidate) - MAE(best) in BPM for the baselines (interval above 0 = worse than the best beyond noise):

| baseline | MAE | interval |
| --- | --- | --- |
| Raw (no filter) | 1.32 | +0.43 ... +1.93 |
| Raw (no filter) [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.42 | +0.02 ... +0.18 |
| design BPM 25-150 Hz Butterworth 2+2 | 0.70 | +0.12 ... +0.79 |
| design BPM 25-150 Hz Butterworth 2+2 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.30 | -0.05 ... +0.02 |
| design Murmur 40-800 Hz Butterworth 2+2 | 0.54 | +0.13 ... +0.30 |
| design Murmur 40-800 Hz Butterworth 2+2 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.30 | -0.04 ... +0.03 |

Quality threshold (normalised autocorrelation peak) versus valid share and accuracy on valid windows (reliable windows):

| candidate | threshold | valid share | MAE valid | within tolerance valid | gross errors valid |
| --- | --- | --- | --- | --- | --- |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.2 | 100 % | 0.3 | 100 % | 0 |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 100 % | 0.3 | 100 % | 0 |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.4 | 100 % | 0.3 | 100 % | 0 |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 100 % | 0.3 | 100 % | 0 |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.6 | 99 % | 0.3 | 100 % | 0 |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.7 | 97 % | 0.3 | 100 % | 0 |
| (quality range 0.56-0.95, median 0.87) | | | | | |
| design BPM 25-150 Hz Butterworth 2+2 | 0.2 | 100 % | 0.7 | 100 % | 1 |
| design BPM 25-150 Hz Butterworth 2+2 | 0.3 | 100 % | 0.7 | 100 % | 1 |
| design BPM 25-150 Hz Butterworth 2+2 | 0.4 | 99 % | 0.7 | 100 % | 1 |
| design BPM 25-150 Hz Butterworth 2+2 | 0.5 | 94 % | 0.6 | 100 % | 1 |
| design BPM 25-150 Hz Butterworth 2+2 | 0.6 | 84 % | 0.6 | 99 % | 1 |
| design BPM 25-150 Hz Butterworth 2+2 | 0.7 | 69 % | 0.5 | 99 % | 1 |
| (quality range 0.36-0.94, median 0.80) | | | | | |
| Raw (no filter) | 0.2 | 100 % | 1.3 | 99 % | 3 |
| Raw (no filter) | 0.3 | 99 % | 1.3 | 99 % | 3 |
| Raw (no filter) | 0.4 | 92 % | 1.3 | 99 % | 3 |
| Raw (no filter) | 0.5 | 81 % | 0.7 | 99 % | 1 |
| Raw (no filter) | 0.6 | 66 % | 0.7 | 99 % | 1 |
| Raw (no filter) | 0.7 | 50 % | 0.4 | 100 % | 0 |
| (quality range 0.30-0.88, median 0.70) | | | | | |
## Findings in plain words

1. **The estimator matters more than the filter.** The default estimator (highest autocorrelation peak) picks the sub-harmonic (half rate, the peak at two cycles) in a few windows; the half-lag check plus a smoother envelope (two cascaded one-pole low-passes at 5 Hz) leaves no gross error on the reliable windows for 1258 of 1310 filters; the exceptions all have a high-pass at 60 Hz (worst: elliptic_hp4_60_lp4_100, MAE 2.86 BPM). Design BPM filter: MAE 0.70 -> 0.30 BPM; Raw: 1.32 -> 0.42 BPM.
2. **With the final estimator the BPM filter choice is within noise on reliable windows.** Median MAE over all filters 0.31 BPM, 10th-90th percentile 0.30-0.37 BPM; 147 of the top 150 rows are inside the bootstrap noise of the best. The best filters, the design filters and even Raw meet the project targets (MAE <= 5 BPM, >= 90 % valid, each window within max(5 BPM, 10 %)) on these recordings.
3. **What does separate filters is the artefact windows** (movement in rest-1 at 39-40 s, start of elevated-1), which the reference marks unreliable. On all windows Raw has MAE 4.22 BPM, the design BPM filter 0.69, the design Murmur filter 0.35, the best 0.35 (median over filters 0.72). A high-pass of about 25-40 Hz, preferably steeper (order 3-4 at 30 Hz), rejects the low-frequency movement energy; the low-pass edge (60 Hz to none) hardly matters. This rests on two artefact events, so it is a plausible mechanism, not a proven ranking.
4. Robust: Raw fails on artefact windows; a steep high-pass at 60 Hz or above causes half-rate errors (it removes most of the low-frequency S1 energy); square and Shannon-energy rectification are worse than absolute value; comb peak choice as implemented is harmful; holding 8 s of filtered audio instead of the envelope buys nothing (`results/bpm_window_representation.md`). Within noise: family (Butterworth, Bessel, Chebyshev I/II, elliptic), orders, low-pass edge, input limiters, envelope rate 50-200 Hz.
5. Caveats: one person, five recordings, 35 roughly independent windows; the reference marks beats on a 25-150 Hz Hilbert envelope, so it is not fully independent of 25-150 Hz analysis filters; the quality threshold 0.3 was set from a noise argument (about 4 standard deviations of the normalised autocorrelation of a non-periodic envelope with about 200 independent samples in 8 s), not tuned, and no window fell below it with the final estimator, so the validity rule is untested here.

## Top 20 filters with the final estimator [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check]

| candidate [estimator variant] | MAE | median AE | bias | within tolerance | gross errors | valid | MAE valid | MAE all windows | within tolerance all windows | filter multiplies per sample | est. CPU of one core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp2_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp4_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 20 | 0.79 % |
| butterworth_hp3_30_lp2_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 13 | 0.60 % |
| butterworth_hp3_30_lp3_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 16 | 0.68 % |
| butterworth_hp3_30_lp4_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 18 | 0.73 % |
| butterworth_hp3_30_lp1_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 11 | 0.55 % |
| butterworth_hp3_30_lp3_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 16 | 0.68 % |
| butterworth_hp3_30_lp4_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 18 | 0.73 % |
| butterworth_hp3_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 13 | 0.60 % |
| elliptic_hp4_30_lp2_150 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| butterworth_hp3_30_lp1_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 11 | 0.55 % |
| butterworth_hp3_30_lp3_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 16 | 0.68 % |
| butterworth_hp3_30_lp2_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 13 | 0.60 % |
| butterworth_hp3_30_lp4_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 18 | 0.73 % |
| butterworth_hp3_30_lp1_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 11 | 0.55 % |
| butterworth_hp4_30_lp2_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| butterworth_hp4_30_lp3_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 18 | 0.73 % |
| butterworth_hp4_30_lp1_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 13 | 0.60 % |
| butterworth_hp4_30_lp4_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 20 | 0.79 % |

## Top 10 filters with the final estimator ranked on all windows, including the windows the reference marks unreliable (artefacts, movement, fast rate change)

| candidate [estimator variant] | MAE | median AE | bias | within tolerance | gross errors | valid | MAE valid | MAE all windows | within tolerance all windows | filter multiplies per sample | est. CPU of one core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elliptic_hp4_30_lp2_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp4_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 20 | 0.79 % |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp2_150 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| butterworth_hp4_30_lp2_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| butterworth_hp4_30_lp1_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 13 | 0.60 % |
| butterworth_hp4_30_lp3_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 18 | 0.73 % |
| butterworth_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| butterworth_hp4_30_lp4_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 20 | 0.79 % |
| butterworth_hp4_30_lp1_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 13 | 0.60 % |

## Top 10 over all rows (any estimator variant)

| candidate [estimator variant] | MAE | median AE | bias | within tolerance | gross errors | valid | MAE valid | MAE all windows | within tolerance all windows | filter multiplies per sample | est. CPU of one core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.6 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp2_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.6 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp2_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 15 | 0.65 % |
| elliptic_hp4_30_lp4_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.6 | 100 % | 20 | 0.79 % |
| elliptic_hp4_30_lp4_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.3 | 100 % | 20 | 0.79 % |
| butterworth_hp3_30_lp2_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 13 | 0.60 % |
| butterworth_hp3_30_lp3_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 16 | 0.68 % |
| butterworth_hp3_30_lp4_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 18 | 0.73 % |
| butterworth_hp3_30_lp1_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.1 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 11 | 0.55 % |

## Baselines

| candidate [estimator variant] | MAE | median AE | bias | within tolerance | gross errors | valid | MAE valid | MAE all windows | within tolerance all windows | filter multiplies per sample | est. CPU of one core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Raw (no filter) | 1.3 | 0.4 | -0.4 | 99 % | 3 | 99 % | 1.3 | 4.2 | 94 % | 0 | 0.23 % |
| Raw (no filter) [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.4 | 0.3 | 0.0 | 100 % | 0 | 100 % | 0.4 | 4.2 | 94 % | 0 | 0.25 % |
| design BPM 25-150 Hz Butterworth 2+2 | 0.7 | 0.3 | -0.0 | 100 % | 1 | 100 % | 0.7 | 0.8 | 100 % | 10 | 0.49 % |
| design BPM 25-150 Hz Butterworth 2+2 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.7 | 100 % | 10 | 0.52 % |
| design Murmur 40-800 Hz Butterworth 2+2 | 0.5 | 0.3 | 0.2 | 100 % | 0 | 100 % | 0.5 | 0.7 | 100 % | 10 | 0.49 % |
| design Murmur 40-800 Hz Butterworth 2+2 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 10 | 0.52 % |

## Listening filters as analysis filters

| candidate [estimator variant] | MAE | median AE | bias | within tolerance | gross errors | valid | MAE valid | MAE all windows | within tolerance all windows | filter multiplies per sample | est. CPU of one core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| butterworth_hp2_40_lp2_1500 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 10 | 0.52 % |
| design Murmur 40-800 Hz Butterworth 2+2 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 10 | 0.52 % |
| butterworth_hp2_40_lp2_400 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 10 | 0.52 % |
| butterworth_hp2_20_lp2_800 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.7 | 100 % | 10 | 0.52 % |
| butterworth_hp2_100_lp2_800 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 2.4 | 97 % | 10 | 0.52 % |
| butterworth_hp2_60_lp2_800 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 0.0 | 100 % | 0 | 100 % | 0.3 | 0.4 | 100 % | 10 | 0.52 % |
| Raw (no filter) [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.4 | 0.3 | 0.0 | 100 % | 0 | 100 % | 0.4 | 4.2 | 94 % | 0 | 0.25 % |
| butterworth_hp2_40_lp2_400 | 0.5 | 0.3 | 0.2 | 100 % | 0 | 100 % | 0.5 | 0.7 | 100 % | 10 | 0.49 % |
| design Murmur 40-800 Hz Butterworth 2+2 | 0.5 | 0.3 | 0.2 | 100 % | 0 | 100 % | 0.5 | 0.7 | 100 % | 10 | 0.49 % |
| butterworth_hp2_40_lp2_1500 | 0.5 | 0.3 | 0.2 | 100 % | 0 | 100 % | 0.5 | 0.7 | 100 % | 10 | 0.49 % |
| butterworth_hp2_60_lp2_800 | 0.5 | 0.3 | 0.2 | 100 % | 0 | 100 % | 0.5 | 0.7 | 100 % | 10 | 0.49 % |
| butterworth_hp2_100_lp2_800 | 0.6 | 0.3 | 0.2 | 100 % | 0 | 100 % | 0.6 | 1.6 | 99 % | 10 | 0.49 % |
| butterworth_hp2_20_lp2_800 | 0.7 | 0.3 | -0.0 | 100 % | 1 | 100 % | 0.7 | 1.1 | 99 % | 10 | 0.49 % |
| Raw (no filter) | 1.3 | 0.4 | -0.4 | 99 % | 3 | 99 % | 1.3 | 4.2 | 94 % | 0 | 0.23 % |

## Per-recording MAE (reliable windows) of the top 10 and the baselines

| candidate | rest-1 | rest-2 | elevated-1 | elevated-2 | elevated-3 | spread (max-min) |
| --- | --- | --- | --- | --- | --- | --- |
| elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.4 | 0.1 | 0.3 | 0.5 | 0.2 | 0.3 |
| elliptic_hp4_30_lp2_200 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.4 | 0.1 | 0.3 | 0.5 | 0.2 | 0.3 |
| elliptic_hp4_30_lp4_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.4 | 0.1 | 0.3 | 0.5 | 0.2 | 0.3 |
| butterworth_hp3_30_lp2_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.3 |
| butterworth_hp3_30_lp3_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.3 |
| butterworth_hp3_30_lp4_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.3 |
| butterworth_hp3_30_lp1_600 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.3 |
| butterworth_hp3_30_lp3_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.3 |
| butterworth_hp3_30_lp4_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.3 |
| butterworth_hp3_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.3 |
| Raw (no filter) | 2.2 | 1.5 | 2.7 | 0.4 | 0.3 | 2.3 |
| Raw (no filter) [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.8 | 0.3 | 0.5 | 0.4 | 0.3 | 0.5 |
| design BPM 25-150 Hz Butterworth 2+2 | 1.2 | 1.2 | 0.7 | 0.3 | 0.2 | 1.0 |
| design BPM 25-150 Hz Butterworth 2+2 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.3 | 0.2 | 0.3 |
| design Murmur 40-800 Hz Butterworth 2+2 | 1.1 | 0.3 | 0.7 | 0.4 | 0.3 | 0.9 |
| design Murmur 40-800 Hz Butterworth 2+2 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.5 | 0.1 | 0.3 | 0.4 | 0.2 | 0.4 |

## Leave-one-recording-out, filter sweep with the default estimator (clean: nothing tuned on the held-out recording)

| held out | chosen on the other four | MAE on the four | MAE held out | within tolerance held out | best possible held out | design BPM filter held out |
| --- | --- | --- | --- | --- | --- | --- |
| rest-1 | chebyshev2_hp4_20_lp2_100 | 0.3 | 1.3 | 100 % | 0.9 | 1.2 |
| rest-2 | elliptic_hp4_30_lp4_100 | 0.5 | 0.2 | 100 % | 0.2 | 1.2 |
| elevated-1 | chebyshev1_hp4_30_lp4_100 | 0.4 | 0.6 | 100 % | 0.4 | 0.7 |
| elevated-2 | elliptic_hp4_30_lp4_100 | 0.5 | 0.4 | 100 % | 0.3 | 0.3 |
| elevated-3 | elliptic_hp4_40_lp2_300 | 0.5 | 2.1 | 98 % | 0.2 | 0.2 |

Mean held-out MAE: 0.9 BPM; design BPM filter: 0.7 BPM.

## Leave-one-recording-out, filter sweep with the final estimator (the estimator itself was chosen on all five)

| held out | chosen on the other four | MAE on the four | MAE held out | within tolerance held out | best possible held out | design BPM filter held out |
| --- | --- | --- | --- | --- | --- | --- |
| rest-1 | fir257_hp_100_lp_800 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.5 | 100 % | 0.4 | 0.5 |
| rest-2 | elliptic_hp2_30_lp2_150 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.1 | 100 % | 0.1 | 0.1 |
| elevated-1 | butterworth_hp2_25_lp1_80 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.3 | 100 % | 0.3 | 0.3 |
| elevated-2 | elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.2 | 0.5 | 100 % | 0.3 | 0.3 |
| elevated-3 | elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.2 | 100 % | 0.2 | 0.2 |

Mean held-out MAE: 0.3 BPM; design BPM filter: 0.3 BPM.

## Leave-one-recording-out over all rows (estimator variants were staged on all five recordings, so this is optimistic)

| held out | chosen on the other four | MAE on the four | MAE held out | within tolerance held out | best possible held out | design BPM filter held out |
| --- | --- | --- | --- | --- | --- | --- |
| rest-1 | fir257_hp_100_lp_800 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.5 | 100 % | 0.4 | 0.5 |
| rest-2 | elliptic_hp2_30_lp2_150 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.1 | 100 % | 0.1 | 0.1 |
| elevated-1 | butterworth_hp2_25_lp1_80 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check] | 0.3 | 0.3 | 100 % | 0.3 | 0.3 |
| elevated-2 | elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0] | 0.2 | 0.5 | 100 % | 0.3 | 0.3 |
| elevated-3 | elliptic_hp4_30_lp2_300 [envelope_lowpass=two_pole,envelope_lowpass_hz=5.0] | 0.3 | 0.2 | 100 % | 0.2 | 0.2 |

Mean held-out MAE: 0.3 BPM; design BPM filter: 0.3 BPM.

## Estimator variants (stage 2): change of MAE versus the default over the top 10 filters and the 3 baselines

| variant | mean MAE change (BPM) | median MAE change (BPM) | gross errors summed over these filters |
| --- | --- | --- | --- |
| envelope_lowpass=two_pole | -0.14 | -0.08 | 1 |
| envelope_lowpass_hz=5.0 | -0.10 | -0.11 | 4 |
| envelope_lowpass_hz=8.0 | -0.09 | -0.05 | 2 |
| peak_choice=first_above | -0.06 | +0.00 | 0 |
| compression=clip_mean3 | -0.05 | -0.11 | 5 |
| peak_choice=half_check | -0.04 | +0.00 | 1 |
| compression=log | -0.03 | -0.12 | 9 |
| envelope_lowpass=boxcar | -0.01 | -0.01 | 4 |
| default | +0.00 | +0.00 | 4 |
| envelope_rate_hz=200 | +0.02 | +0.00 | 5 |
| envelope_lowpass_hz=20.0 | +0.07 | +0.07 | 4 |
| envelope_rate_hz=50 | +0.10 | +0.01 | 10 |
| rectification=shannon | +0.29 | +0.32 | 14 |
| rectification=square | +0.52 | +0.48 | 21 |
| peak_choice=comb | +3.38 | +3.48 | 227 |

## Estimator configurations of stage 3 over the same filters

| estimator | mean MAE | worst filter MAE | gross errors summed | MAE of the design BPM filter | MAE of Raw |
| --- | --- | --- | --- | --- | --- |
| default | 0.56 | 1.32 | 4 | 0.70 | 1.32 |
| peak_choice=half_check | 0.52 | 0.97 | 1 | 0.51 | 0.97 |
| envelope_lowpass=two_pole | 0.43 | 0.60 | 1 | 0.60 | 0.53 |
| envelope_lowpass_hz=5.0 | 0.46 | 1.30 | 4 | 0.57 | 1.30 |
| envelope_lowpass_hz=8.0 | 0.47 | 0.77 | 2 | 0.64 | 0.77 |
| peak_choice=first_above | 0.51 | 0.67 | 0 | 0.51 | 0.67 |
| envelope_lowpass=two_pole,envelope_lowpass_hz=5.0 | 0.50 | 1.89 | 13 | 1.40 | 1.89 |
| envelope_lowpass=two_pole,envelope_lowpass_hz=8.0 | 0.43 | 1.24 | 4 | 0.54 | 1.24 |
| envelope_lowpass=two_pole,peak_choice=first_above | 0.42 | 0.53 | 0 | 0.42 | 0.53 |
| envelope_lowpass_hz=5.0,peak_choice=first_above | 0.39 | 0.52 | 0 | 0.39 | 0.52 |
| envelope_lowpass_hz=8.0,peak_choice=first_above | 0.45 | 0.59 | 0 | 0.45 | 0.59 |
| envelope_lowpass=two_pole,peak_choice=half_check | 0.41 | 0.53 | 0 | 0.42 | 0.53 |
| envelope_lowpass_hz=5.0,peak_choice=half_check | 0.39 | 0.52 | 0 | 0.39 | 0.52 |
| envelope_lowpass_hz=8.0,peak_choice=half_check | 0.45 | 0.60 | 0 | 0.45 | 0.60 |
| envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check | 0.31 | 0.42 | 0 | 0.30 | 0.42 |
| envelope_lowpass=two_pole,envelope_lowpass_hz=8.0,peak_choice=half_check | 0.36 | 0.46 | 0 | 0.35 | 0.46 |

Input limiter before the filter (stage 2, default estimator, top 10 filters and baselines):

| candidate | MAE | within tolerance | gross errors |
| --- | --- | --- | --- |
| chebyshev1_hp4_30_lp4_100__hardlimit0p25 | 0.5 | 100 % | 0 |
| chebyshev1_hp4_30_lp4_100__softlimit0p25 | 0.5 | 100 % | 0 |
| elliptic_hp4_30_lp4_100__hardlimit0p5 | 0.5 | 100 % | 0 |
| chebyshev1_hp4_30_lp4_100__hardlimit0p5 | 0.5 | 100 % | 0 |
| chebyshev1_hp4_30_lp2_300__hardlimit0p5 | 0.5 | 100 % | 0 |
| chebyshev1_hp4_30_lp2_200__hardlimit0p5 | 0.5 | 100 % | 0 |
| chebyshev1_hp4_30_lp2_300__hardlimit0p25 | 0.5 | 100 % | 0 |
| elliptic_hp4_30_lp2_300__hardlimit0p5 | 0.5 | 100 % | 0 |
| elliptic_hp4_30_lp4_100__hardlimit0p25 | 0.5 | 100 % | 0 |
| elliptic_hp4_30_lp2_200__hardlimit0p5 | 0.5 | 100 % | 0 |
| chebyshev1_hp4_30_lp2_200__hardlimit0p25 | 0.5 | 100 % | 0 |
| elliptic_hp4_30_lp4_100__softlimit0p25 | 0.5 | 100 % | 0 |

## Best per family

| family | estimator | best candidate | MAE | within tolerance | gross errors | multiplies per sample |
| --- | --- | --- | --- | --- | --- | --- |
| raw | default | raw | 1.3 | 99 % | 3 | 0 |
| butterworth | default | butterworth_hp2_30_lp2_60 | 0.5 | 100 % | 0 | 10 |
| bessel | default | bessel_hp2_40_lp4_100 | 0.5 | 100 % | 0 | 15 |
| chebyshev1 | default | chebyshev1_hp4_30_lp4_100 | 0.5 | 100 % | 0 | 20 |
| chebyshev2 | default | chebyshev2_hp4_30_lp4_100 | 0.5 | 100 % | 0 | 20 |
| elliptic | default | elliptic_hp4_30_lp4_100 | 0.5 | 100 % | 0 | 20 |
| fir | default | fir257_hp_100_lp_800 | 0.6 | 100 % | 0 | 257 |
| decimated | default | decimated_hp4_30_lp2_80 | 0.5 | 100 % | 0 | 5 |
| raw | final | raw | 0.4 | 100 % | 0 | 0 |
| butterworth | final | butterworth_hp3_30_lp2_600 | 0.3 | 100 % | 0 | 13 |
| bessel | final | bessel_hp4_40_lp2_300 | 0.3 | 100 % | 0 | 15 |
| chebyshev1 | final | chebyshev1_hp2_40_lp4_100 | 0.3 | 100 % | 0 | 15 |
| chebyshev2 | final | chebyshev2_hp2_25_lp4_200 | 0.3 | 100 % | 0 | 15 |
| elliptic | final | elliptic_hp4_30_lp2_300 | 0.3 | 100 % | 0 | 15 |
| fir | final | fir257_hp_100_lp_800 | 0.3 | 100 % | 0 | 257 |
| decimated | final | decimated_hp4_30_lp4_300 | 0.3 | 100 % | 0 | 6 |

## Final best candidate: realisation

- Filter: `elliptic_hp4_30_lp2_300`: elliptic (0.5 dB / 40 dB): order-4 high-pass at 30 Hz then order-2 low-pass at 300 Hz.
- Estimator: `envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check` (see `src/hfs/bpm_estimator.py`).
- Filter cost: 15 multiplies per sample, 24 state bytes, 60 coefficient bytes.
- Estimator: window 3200 bytes (PSRAM), total estimator RAM 8096 bytes, 240199 multiplies per update.
- Estimated CPU share of one 240 MHz core: 0.65 % (ESTIMATE, not measured: 4 cycles per filter multiply including loads and the dependency chain of a biquad, 2 cycles per autocorrelation multiply-accumulate, 60 cycles per logf; autocorrelation burst about 2.0 ms per update on the BPM worker thread).

Second-order sections (float32; b0 b1 b2 a0 a1 a2):

```
{0.931433797f, -1.86285889f, 0.931433797f, 1f, -1.97611129f, 0.976417542f},
{1f, -1.99995387f, 1f, 1f, -1.99685585f, 0.996986389f},
{0.0137708215f, -0.00919216592f, 0.0137708215f, 1f, -1.82697201f, 0.846408784f},
```

## Staging and pruning

1. Filter sweep with the default estimator: 1310 filters. Butterworth 2+2 over every high-pass edge (none, 10-80 Hz) x every low-pass edge (60-800 Hz, none) with LP >= 1.5 x HP; Butterworth full order cross 1-4 x 1-4 on HP 15-60 Hz x LP 80-600 Hz; Bessel, Chebyshev I (0.5 dB), Chebyshev II (40 dB, edge moved to the -3 dB point) and elliptic (0.5/40 dB) with orders 1+1, 2+2, 4+4, 2+4, 4+2 on HP 15-60 Hz x LP 100-300 Hz; FIR (Hamming window) 65/129/257 taps; decimated design (64-tap anti-alias FIR, decimation to 1 kHz, Butterworth there).
   Pruned: edge pairs closer than 1.5:1 (pass band too narrow for heart sounds), 3rd-order other families, other families at 10 Hz and LP > 300 Hz (Butterworth covers those edges).
2. Estimator variants (one change at a time) and input limiters on the top 10 filters plus the baselines.
3. Joint confirmation: the improving variants and their pairwise combinations (16 configurations) on the same filters.

FIR note: at 16 kHz a Hamming-window FIR resolves about 3.3 x 16000 / N Hz of transition width (about 800 Hz at 65 taps, 200 Hz at 257 taps), so a 25 Hz high-pass edge is not realisable with these lengths; the FIR rows behave like low-pass filters with a weak, wide high-pass, at N multiplies per sample.
