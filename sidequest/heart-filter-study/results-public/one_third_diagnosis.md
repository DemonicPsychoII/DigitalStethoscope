# Why the run-1 final method reports one third of the heart rate (run 2, EPHNOGRAM)

Script: `src/bpm_improved_method_diagnosis.py` (numbers in `one_third_diagnosis_numbers.json`). Method under test:
run-1 final method (two smoothing steps at 5 Hz, half-rate check), Butterworth 2+2 40-150 Hz, rest level, microphone
only. Three records from three subjects with many one-third windows: ECGPCG0064 (S006, bicycle stress test, window
ending at 900 s, ECG 146 BPM, device 49 BPM), ECGPCG0032 (S015, pedalling a stationary bicycle, 760 s, 118 vs 39 BPM),
ECGPCG0052 (S017, treadmill stress test, 760 s, 144 vs 48 BPM). "Resample only" = the same sound resampled to 16 kHz
and scaled, without the chain model (microphone response, noise floor, limiter).

## Answer in short

1. **The sound is clean and strongly periodic; the self-similarity curve has almost equal peaks at T, 2T, 3T, 4T**
   (figure 1: 0.93-0.95 at S006 900 s). Picking "the highest peak" among near-equal peaks is a coin toss decided by
   a few per cent. Over all one-third windows of the three records, r(3T) exceeded r(T) by a median of only 5-12 %
   (median r(T) / r(3T) = 0.67/0.72, 0.67/0.73, 0.74/0.81).
2. **The per-shift normalisation removes the natural preference for short shifts and so lets 3T win.** The estimator
   divides the sum at shift L by the energies of the two overlapping parts, which undoes the (N - L)/N fall-off of the
   plain autocorrelation. On the very windows where the estimator chose 3T, the plain (biased) autocorrelation
   r(3T) > r(T) holds in only 32 %, 21 % and 38 % (S006, S015, S017); in the remaining 62-79 % it would prefer T. At
   146 BPM the fall-off is 0.95 at T and 0.85 at 3T, a 12 % handicap for 3T, the same size as the observed lead of 3T.
3. **The half-rate check cannot help**: 3T / 2 = 1.5T is a trough, not a peak. One-third is only possible when 3T fits
   below the 2 s search limit (30 BPM), i.e. at an ECG rate of 90 BPM or more, which is why the error grows with heart
   rate and appears in exercise records. Raising the lower search limit to 40 BPM would block it only below 120 BPM.

## Is it the sound or the model?

The sound. With the sound only resampled (no chain model), the same three records show r(3T) > r(T) in 56 %, 85 % and
59 % of the one-third windows (figure 1, yellow and blue curves are nearly identical), and even in 16 %, 45 % and 9 % of
the windows that the modelled chain got right. The chain model lowers all peaks a little (noise floor) but does not
create the 3T peak.

## Is there a spectral line at one third of the heart rate?

Weakly. Figure 2 (Welch spectrum of 32 s of envelope) shows a small bump at one third of the heart rate for S006 and
S017, about 1.5-2 orders of magnitude below the heart-rate line. In 8 s windows the power within 4 % of one third of
the heart rate was 5-14x the median background in one-third windows, versus 3-10x in correct windows, and 4-8 % of the
heart-rate line. So there is a faint 3-beat repetition in the sound (a slight beat-to-beat pattern locked to every
third beat, plausibly breathing or pedal/stride rhythm locking to the heart beat during exercise; the database has no
breathing or cadence channel, so this is **not established**). It is too weak to be the cause on its own; it only tips
the balance between near-equal peaks after the normalisation has removed the short-shift preference.

## The 5 Hz smoothing

It makes things worse but is not the root cause. With the one-step 12 Hz envelope on the same one-third windows,
r(3T) > r(T) held in 58 %, 62 % and 68 % instead of 100 %: the heavier smoothing turns S1+S2 into one smooth bump per
beat, the envelope becomes nearly sinusoidal and all multiples of T look alike. This matches run 2, where the
half-rate check with the 12 Hz envelope had lower error (23.1 BPM) than the final method (26.6 BPM).

## The other gross errors (final method, 40-150 Hz, rest level, ECG-reliable windows)

- **Half rate** (7,259 windows): concentrated at 70-110 BPM (12-13 % of windows there; 1-2.5 % above 130 BPM) and in
  the rate bands typical of rest and walking; there 2T is the highest peak and the half check's 0.8 fraction is not met.
- **"Other"** errors are not a constant step or pedal cadence: their estimates follow the heart rate. Ratios
  estimate / ECG cluster at 0.25 (shift 4T: 1,430 treadmill, 500 pedalling, 370 bicycle-test windows), 0.37-0.45
  (about 2.5T), 0.55-0.71 (1.5T, probably a beat aligned with the next beat's second sound; not verified) and, when lying on the bed, above 2.2
  (estimates at 185-195 BPM: the search edge at 200 BPM picks the S1-S2 spacing when the beat is weak). Most "other"
  errors are therefore further multiples of the true spacing (4T), the same mechanism as one third.

## Consequences for the method

- Choose the **shortest** lag whose peak is nearly as high as the highest: a sub-multiple check over L/2, L/3, L/4
  (catches T when r(T) >= ~0.85 r(3T)), or the existing `first_above`.
- Or restore a mild preference for short shifts (weight the normalised value by the overlap (N - L)/N before choosing).
- A harmonic sum r(L)+r(2L)+r(3L) does not separate T from 3T on such a periodic envelope (all terms are near equal,
  and 6T, 9T lie outside the 4 s of computed shifts), so it cannot fix this error; see `improved_method.md`.

Figures: `figures/one_third_envelope_and_correlation.png` (envelope with ECG beats and self-similarity with T, 2T, 3T
marked, modelled device and resample only), `figures/one_third_envelope_spectrum.png` (envelope spectrum with the heart
rate, one third and two thirds marked).
