# Run 2: whole-window (non-causal) BPM counting against the causal 40-150 Hz method

The question: the 8 s window sits in memory, so the analysis could work on the whole window at once, without
being causal. Does that beat run 1's causal method (2+2 Butterworth 40-150 Hz, two 5 Hz one-pole low-passes,
autocorrelation with the half-rate check), and what would it cost on the ESP32-S3?

## Answer

- **Own five recordings (255 windows, 226 reliable): no.** The causal method is 0.30 / 0.35 BPM (reliable / all
  windows), with 0 gross errors. The best whole-window methods tie it: zero-phase 2+2 25-150 Hz without edge
  handling, and zero-phase 2+2 25-400 Hz, both 0.30 / 0.35. None is better. These are the recordings run 1 tuned
  its method on, so a tie is the expected result.
- **EPHNOGRAM, 66 records, 21 people, 21,956 windows with a reliable ECG rate: yes, by a few BPM. But the filter's
  phase is not what helps.**
  - At the rest level the causal baseline is 26.88 BPM. Whole-window 2+2 forward-backward filtering at 40-150 Hz
    gives 23.28 BPM. The difference is -3.60 BPM, 95 % range [-4.55, -2.72] from resampling people, Holm-adjusted
    p 0.013. It is better for 18 of 21 people.
  - Running the same 2+2 sections twice in a row while recording gets almost all of that gain: 23.35 BPM,
    -3.53 [-4.46, -2.57]. That method is causal, needs no stored raw window and costs 7.9 instead of 5.2 ms per
    second.
  - The gain therefore comes from the steeper magnitude response, the 2+2 response squared. It does not come from
    zero phase.
  - At the overload level the gains are smaller: whole-window -1.23 [-2.13, -0.45], causal twice
    -0.98 [-1.86, -0.17].
- **Largest gain on public data: the Springer-type log envelope, not the zero-phase filter.**
  - Springer heart rate with the half-rate check: -6.18 BPM at rest and -9.71 at overload.
  - Springer's three envelopes combined with the half-rate check: -7.43 at rest and -8.80 at overload. All are
    Holm p 0.013.
  - Both lose below 90 BPM. In the band below 70 BPM: +7.2 and +10.8 BPM worse.
  - Both win strongly above 110 BPM. In the band 130-150 BPM: -20 and -22 BPM. They mostly remove the one-third-rate
    errors of the causal method.
  - A diagnostic added after these results replaces only the envelope of the 1 kHz zero-phase method with
    Springer's homomorphic envelope. That gives -6.06 [-7.42, -4.48] at rest. This points to the logarithmic
    envelope as the main ingredient. Spike removal alone gave -4.07, compared with -3.67 for the same method
    without it.
  - On the own recordings these variants are slightly worse: 0.43 / 0.48 BPM, and 0.79 BPM with 2 gross errors
    when spike removal is added. The diagnostic was only run at the rest level and is outside the Holm family.
- **Cost (estimate):**
  - Whole-window filtering of the raw 16 kHz window: about 49 ms of processor time per update and 1 MB of PSRAM.
  - The same on a 1 kHz window reduced at capture time: 6.0 ms per second in total and 73 kB, with the same error
    (23.21 BPM).
  - Springer heart rate: about 38 ms per second (two FFTs of 8,192 points, two of 16,384).
  - Every method fits within 10 % of one core at one update per second. The largest, zero-phase at 16 kHz, needs
    123 blocks of 4 ms (0.5 s) when spread at 10 %.

So for the owner's question: **non-causal processing of the window is not needed for the filter gain.** A steeper
causal filter (the same 2+2 sections twice) gives the same improvement on public data at almost no cost. What
buys more on public data is the log-domain envelope of Springer's code, together with a search range that reaches
200 BPM. That envelope uses a Hilbert transform and zero-phase smoothing in the reference code. Whether a causal
log envelope does as well was not tested. It also costs accuracy at resting heart rates, and on the own recordings.

## Data and windows

- **Own:** 5 recordings, windows of 8 s ending at every full second 10-60 s after the 2 s discard, the same
  time base as `src/bpm_evaluate.py`. 255 windows, 226 reliable. Metrics are exactly run 1's
  (`bpm_evaluate.metric_block`).
- **Baselines reproduced exactly** (`check_baselines` stops the script otherwise):
  - 40-150 Hz: 0.30 / 0.35 BPM, 255 of 255 within tolerance.
  - 25-150 Hz: 0.30 / 0.69 BPM, 1 gross error.
  - Raw: 0.42 / 4.22 BPM, 16 gross errors.
- **Public:** EPHNOGRAM through `hfs.chain_model`, using the same capture-chain call and seeds as
  `src/bpm_evaluate_public.py`.
  - 66 records: 68 usable, minus the duplicates ECGPCG0001 and ECGPCG0002. 22 subjects, of which 21 have reliable
    windows.
  - Windows end every 4th second from 12 s on (12, 16, 20, ... s after the record start). This subset was chosen
    because the whole-window methods are slow to simulate. The 4-second step is the only thinning.
  - Reference: `reference-public/ephnogram/`. 25,994 windows, 21,956 of them reliable.
  - Both level conditions were run, "rest" and "overload" (`spectrum_variant="microphone_only"`).
  - Intervals: cluster bootstrap over subjects, 2,000 resamples, seed 20261123, of the paired mean-absolute-error
    difference to `causal_40_150`. Holm correction over the 25 methods compared with the baseline. The smallest attainable p is 1/2000, which becomes 0.013 after Holm.

## Own recordings (selected rows; all 127 rows in `own_recordings.csv`)

| Method | Reliable MAE | All MAE | Within tolerance | Gross |
| --- | ---: | ---: | ---: | ---: |
| causal 40-150 (baseline) | 0.30 | 0.35 | 255/255 | 0 |
| causal 40-150 sections twice | 0.32 | 0.38 | 255/255 | 0 |
| zero-phase 2+2 40-150, reflect padding, zero-phase envelope | 0.33 | 0.39 | 255/255 | 0 |
| zero-phase 2+2 40-150, no edge handling | 0.32 | 0.38 | 255/255 | 0 |
| zero-phase 2+2 25-150, no edge handling | 0.30 | 0.35 | 255/255 | 0 |
| zero-phase 1+1 40-150, edges matched to -3 dB | 0.31 | 0.63 | 254/255 | 1 (half rate) |
| two forward passes 2+2 (same magnitude as zero-phase, doubled delay) | 0.33 | 0.39 | 255/255 | 0 |
| forward pass streamed, backward pass on the window | 0.32 | 0.39 | 255/255 | 0 |
| 1 kHz window, zero-phase 2+2 40-150 | 0.33 | 0.39 | 255/255 | 0 |
| 2 kHz window, zero-phase 2+2 40-150 | 0.33 | 0.39 | 255/255 | 0 |
| stored 800 envelope values, unchanged (identity check) | 0.30 | 0.35 | 255/255 | 0 |
| stored values smoothed forward and backward at 5 Hz | 0.26 | 0.66 | 254/255 | 1 (third) |
| stored values with 20 % taper | 0.68 | 0.68 | 254/255 | 1 (third) |
| Springer heart rate as published (0.5-2 s) | 20.97 | 19.19 | 186/255 | 69 (all half rate) |
| Springer heart rate, 0.3-2 s | 0.38 | 0.44 | 255/255 | 0 |
| Springer heart rate, half-rate check | 0.38 | 0.44 | 255/255 | 0 |
| Springer three envelopes combined, 50 Hz, half-rate check | 0.63 | 0.69 | 255/255 | 0 |
| 1 kHz zero-phase + homomorphic envelope (diagnostic) | 0.43 | 0.48 | 255/255 | 0 |

Per recording, all windows: the baseline is 0.59 / 0.12 / 0.46 / 0.39 / 0.20 BPM for rest-1, rest-2,
elevated-1, elevated-2 and elevated-3. Zero-phase 2+2 40-150 is 0.74 / 0.15 / 0.42 / 0.43 / 0.22. Springer as
published fails only on elevated-2 and elevated-3 (49.1 and 42.7 BPM), whose heart rate is 116-149 BPM, above its
120 BPM limit. It also fails twice in elevated-1.

## Public data (reliable windows; full table with per band and per subject rows in `public_ephnogram.csv`)

| Method | Rest MAE | Difference to baseline [95 %] | Overload MAE | Difference [95 %] |
| --- | ---: | ---: | ---: | ---: |
| causal 40-150 (baseline) | 26.88 | | 20.22 | |
| causal 40-150 sections twice | 23.35 | -3.53 [-4.46, -2.57] | 19.24 | -0.98 [-1.86, -0.17] |
| zero-phase 2+2 40-150, reflect | 23.28 | -3.60 [-4.55, -2.72] | 18.99 | -1.23 [-2.13, -0.45] |
| zero-phase 2+2 40-150, causal envelope | 23.46 | -3.42 [-4.33, -2.54] | 18.96 | -1.26 [-2.18, -0.49] |
| two forward passes 2+2 | 23.44 | -3.43 [-4.32, -2.58] | 19.16 | -1.06 [-1.86, -0.36] |
| streamed forward, backward on window | 23.28 | -3.59 [-4.56, -2.69] | 19.01 | -1.22 [-2.14, -0.44] |
| 1 kHz window zero-phase 2+2 | 23.21 | -3.67 [-4.63, -2.77] | 19.01 | -1.21 [-2.14, -0.44] |
| 2 kHz window zero-phase 2+2 | 23.17 | -3.70 [-4.64, -2.82] | 19.04 | -1.19 [-2.09, -0.42] |
| zero-phase 1+1 40-150 matched edges | 29.57 | +2.69 [+2.03, +3.32] | 21.52 | +1.30 [+0.83, +1.74] |
| zero-phase 2+2 25-150 | 29.06 | +2.19 [+1.44, +2.89] | 21.12 | +0.90 [+0.38, +1.40] |
| zero-phase 2+2 25-400 (Springer's band) | 28.93 | +2.06 [+1.54, +2.59] | 21.71 | +1.48 [+1.07, +1.91] |
| stored values, 20 % taper | 25.97 | -0.91 [-1.50, -0.33] | 19.16 | -1.06 [-1.72, -0.37] |
| stored values smoothed again at 5 Hz | 31.00 | +4.13 [+2.83, +5.45] | 24.91 | +4.68 [+3.76, +5.67] |
| Springer heart rate as published | 34.01 | +7.14 [+4.70, +9.36] | 24.63 | +4.41 [+1.27, +7.47] |
| Springer heart rate, 0.3-2 s | 25.68 | -1.19 [-3.69, +1.39], Holm p 0.50 | 14.89 | -5.33 [-8.05, -2.17] |
| Springer heart rate, half-rate check | 20.70 | -6.18 [-8.41, -3.67] | 10.52 | -9.71 [-11.90, -7.10] |
| Springer three envelopes, half-rate check | 19.45 | -7.43 [-9.39, -5.09] | 11.42 | -8.80 [-10.91, -6.26] |
| 1 kHz zero-phase + homomorphic envelope (diagnostic, rest only) | 20.81 | -6.06 [-7.42, -4.48] | not run | |

Every difference in this table has a Holm-adjusted p of at most 0.048. Two rows are exceptions: Springer 0.3-2 s at
rest (0.50), and the diagnostic, which is outside the correction. Not significant elsewhere: a single forward pass
on the window (rest 0.50, overload 1.0), and discarding 0.25 s or 0.5 s at overload (1.0). Within tolerance
at rest: the baseline reaches 60.4 %, zero-phase 2+2 67.1 %, and Springer combined 69.4 %.

**By ECG heart-rate band (rest, reliable windows; numbers of windows and people are in the CSV):**

- **Zero-phase 2+2 40-150.** The differences are -0.28 (<70), -3.13 (70-90), -5.46 (90-110), -2.96 (110-130),
  -2.04 (130-150), -3.42 (150-170) and -5.33 (>170) BPM. The intervals for 130 BPM and above include 0.
- **Springer three envelopes with the half-rate check.** The differences are +10.8 (<70, worse), +1.9 (70-90),
  -6.0 (90-110), -12.5 (110-130), -22.0 (130-150), -28.8 (150-170) and -27.6 (>170) BPM.
- **Main error type of the causal method on public data:** the one-third rate, 3,602 of 21,956 windows at rest.
  The steeper filter barely changes that (3,375). The Springer envelopes halve it (1,641).

The public errors are much larger than on the own recordings, and the rest level is worse than overload. The chain
model's rest level apparently leaves the heart sounds close to the modelled noise floor. This applies to every
method, the baseline included, and is a property of the chain model, not of the methods. It was not investigated
further.

## Window edges

- **Own recordings, zero-phase 2+2 40-150:**
  - No handling: 0.32 / 0.38 BPM.
  - Odd-reflection padding as in `filtfilt`: 0.33 / 0.39.
  - Discarding 0.25 s at each end: 0.36 / 0.40. Discarding 0.5 s: 0.44 / 0.48.
- **For 1+1 filters**, discarding adds the gross error that 1+1 already has, or keeps it.
- **Public, rest:**
  - No handling: -3.66 BPM against the baseline.
  - Reflection: -3.60.
  - Discard 0.25 s: -2.95. Discard 0.5 s: -2.14.
- **At overload:** reflection -1.23, discard 0.25 s -0.24 (not significant), discard 0.5 s +0.41 (not significant).
- **Discarding** shortens the usable window from 8 s to 7.5 s or 7 s, and accuracy drops with it. Edge transients
  of a 40 Hz high-pass last only tens of milliseconds, so they do not matter. Odd-reflection padding (15 samples at
  each end for 2+2) costs nothing measurable, and neither does leaving it out. **Recommendation:** no discard;
  padding optional.

## Rate reduction

- **At capture time**, the raw signal can be reduced with run 1's 64-tap anti-alias FIR to 1 or 2 kHz (8,000 or
  16,000 stored values) before the whole-window band-pass. This gives the same error as 16 kHz in every case:
  - own data: 0.33 / 0.39 at both rates;
  - public rest: 23.21 and 23.17 against 23.28 at 16 kHz;
  - public overload: 19.01 and 19.04 against 18.99.
- **Memory:** 31 kB (1 kHz) instead of 512 kB of PSRAM for the window, plus the same again as working buffer.
  1 kHz is enough for a 40-150 Hz analysis.

## Counting stage alone on the stored 800 envelope values

- **Unchanged** stored values reproduce the baseline exactly (0.30 / 0.35), which checks the code path.
- **Zero-phase smoothing at 5 Hz** of the stored values:
  - own data: 0.26 on reliable windows (best of all), but 0.66 on all windows with one one-third-rate error;
  - public: +4.1 / +4.7 BPM worse.
- **A 20 % taper:**
  - own data: 0.68 / 0.68, worse;
  - public: -0.91 at rest and -1.06 at overload, better.

This is the cheapest possible change, and it is inconsistent between the data sources.

## Device budget (estimate, not measured; `device_budget.csv`)

Cost assumptions are those of run 1: 4 cycles per filter multiplication, 2 per correlation multiplication, 60 per
logarithm. Also assumed: exponential and square root cost the same as a logarithm, and the ESP-DSP figure
`dsps_fft2r_fc32` of 97,847 cycles per 1,024 complex points is scaled by N log2 N. The FFT figure comes from
`thesis-material/03-grundlagen-technisch/04-dsp-filter.md:26`; the thesis material marks it as still to be checked
against the original table. The PSRAM access penalty is unknown and not measured, and is not included.

| Method | ms per update | Core share at 1 update/s | Max updates/s at 10 % / 50 % | 4 ms blocks at 10 % | PSRAM | Internal RAM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| causal 40-150 (baseline) | 2.0 | 0.52 % | 48 / 248 | 6 | 0 | 7.2 kB |
| causal 40-150 sections twice | 2.0 | 0.79 % | 47 / 247 | 6 | 0 | 7.2 kB |
| stored values, taper or zero-phase smoothing | 2.0 | 0.52 % | 48 / 245 | 6 | 0 | 7.2 kB |
| zero-phase 2+2, 16 kHz window | 49.0 | 4.89 % | 2.0 / 10.2 | 123 | 1,000 kB | 10.4 kB |
| streamed forward, backward pass on 16 kHz window | 27.6 | 3.03 % | 3.5 / 18.0 | 71 | 500 kB | 10.4 kB |
| zero-phase 2+2, 1 kHz window | 5.0 | 0.60 % | 20 / 101 | 13 | 62.5 kB | 10.4 kB |
| zero-phase 2+2, 2 kHz window | 7.9 | 1.00 % | 12 / 63 | 21 | 125 kB | 10.4 kB |
| 1 kHz + homomorphic envelope | 20.2 | 2.13 % | 4.9 / 24.7 | 52 | 31 kB | 105 kB |
| Springer heart rate (any search variant) | 37.2 | 3.83 % | 2.7 / 13.4 | 95 | 31 kB | 223 kB |
| Springer three envelopes combined | 42.7 | 4.37 % | 2.3 / 11.7 | 108 | 31 kB | 127 kB |

"ms per update" is the once-per-second analysis. The core share also includes the continuous work while recording:
the causal filter and envelope, or the anti-alias filter. Cross-check: with the ESP-DSP biquad figure of 17,552
cycles per 1,024 values instead of 4 cycles per multiplication, the 16 kHz zero-phase update drops from 49 to
42 ms (column `per_update_milliseconds_with_esp_dsp_biquad_figure`).

Spreading the work: the filter passes, the envelope and the direct autocorrelation are sequential loops with
carried state. They can be cut into chunks per 4 ms block, so every method finishes within 1 s at 10 % of a core.
An FFT can only be split between its stages, which is possible but not free. The Springer methods need 128-223 kB
of FFT buffers. Those fit in internal RAM only with care; otherwise they go to PSRAM, at an unknown penalty.

## Springer method

What the PhysioNet code does, with file and line references, is in `sources/springer-method-notes.md`. The source
files are in `sources/springer-hss-1.0/`; all 12 match the published SHA-256 sums.

- **Licence:** GPL-3.0-or-later according to the file headers. `LICENSE.txt` itself could not be downloaded.
- **What it does:**
  - 2+2 Butterworth 25-400 Hz, run forward and backward;
  - Schmidt spike removal;
  - homomorphic envelope: exp of the 8 Hz first-order forward-backward low-passed log of the Hilbert magnitude;
  - autocorrelation (`xcorr` 'coeff') at the 1 kHz feature rate;
  - highest value in 0.5-2 s, so the result is at most 120 BPM.
- **Not verified:** the paywalled article, the licence file, and the MATLAB built-in details (`resample`,
  `filtfilt` padding, `spectrogram` window).
- **Not implemented:** the wavelet feature and the hidden semi-Markov segmentation.
- **Cost of the segmentation (rough estimate, not implemented, Viterbi code not read):** a 4-state duration-dependent
  Viterbi over 400 feature samples at 50 Hz, with durations up to about 100 samples. That is of the order of 10^5 to
  10^6 operations per window, on top of the features. It also needs trained emission and duration parameters, which
  this study does not have.

## What is inconclusive or missing

- **Own recordings:** with 5 recordings, every whole-window method is within about 0.05 BPM of the baseline on
  reliable windows. These data cannot separate the methods.
- **Diagnostics:** the homomorphic-envelope and spike-removal diagnostics were added after seeing the public rest
  results, are outside the Holm family, and were run only at rest.
- **Not tested:** a causal log envelope, which would separate "logarithm" from "Hilbert and zero-phase smoothing".
- **Chain model:** the public results rest on the modelled capture chain. Its rest level gives errors around
  20-27 BPM for every method, so absolute values do not transfer to the device. Only the paired differences are
  the evidence.
- **Reference:** windows with an unreliable ECG reference are reported under "all windows" only.
- **Not done:** the wavelet feature and the HSMM segmentation.
