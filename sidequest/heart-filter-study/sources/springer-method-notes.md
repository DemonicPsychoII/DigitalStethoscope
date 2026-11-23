# Springer reference code: what it does (from the source files)

Source: PhysioNet project "Logistic Regression-HSMM-based Heart Sound Segmentation", version 1.0, D. B. Springer.
Files downloaded as text on 2026-11-23 into `sources/springer-hss-1.0/` (URLs, SHA-256 and the result of the
checksum comparison in `MANIFEST.json`; all 12 `.m` files match the project's published `SHA256SUMS.txt`). Read only,
never executed. File names below omit the added `.txt` suffix; line numbers are those of the downloaded files.

Article: D. B. Springer, L. Tarassenko, G. D. Clifford, "Logistic Regression-HSMM-Based Heart Sound Segmentation",
IEEE Transactions on Biomedical Engineering 63(4):822-832, 2016, doi 10.1109/TBME.2015.2475278. Closed access, not read.

## Licence

Every downloaded file has the header "Copyright (C) 2016 David Springer" with the GNU General Public License, version 3
or any later version (for example `getSpringerPCGFeatures.m` lines 23-37, `getHeartRateSchmidt.m` lines 29-43).
The separate `LICENSE.txt` (listed in `SHA256SUMS.txt`) could not be downloaded (HTTP 502, archive mirror 404) and the
project page returned HTTP 502, so the licence stated on PhysioNet itself is **not verified**.
Consequence for the firmware: a C port derived from this code would be a derivative work under GPL-3.0-or-later. The
study's Python port in `src/hfs/window_bpm.py` is for evaluation only. An independent implementation from the article
or from Schmidt et al. 2010 (not read here) would avoid that, but is not what was evaluated.

## Processing steps

| Step | What the code does | File:line |
| --- | --- | --- |
| Sample rate for features | `springer_options.audio_Fs = 1000` ("The sampling frequency at which to extract signal features") | `default_Springer_HSMM_options.m:29` |
| Feature rate | `springer_options.audio_segmentation_Fs = 50` ("Set to 50 in Springer paper") | `default_Springer_HSMM_options.m:32-33` |
| Wavelet feature on | `include_wavelet_feature = true` | `default_Springer_HSMM_options.m:44` |
| Low-pass | `butterworth_low_pass_filter(audio_data,2,400,Fs,false)`: `butter(2, 2*400/Fs, 'low')`, then `filtfilt` (forward-backward; the file notes the order is "effectively doubled") | `getSpringerPCGFeatures.m:56`, `getHeartRateSchmidt.m:59`, `butterworth_low_pass_filter.m:8-10, 51, 64` |
| High-pass | `butterworth_high_pass_filter(audio_data,2,25,Fs)`: `butter(2, 2*25/Fs, 'high')`, `filtfilt` | `getSpringerPCGFeatures.m:57`, `getHeartRateSchmidt.m:60`, `butterworth_high_pass_filter.m:51, 55` |
| Band-pass comment | "25-400Hz 4th order Butterworth band pass" (order 2 per edge, forward-backward) | `getSpringerPCGFeatures.m:55` |
| Spike removal | `schmidt_spike_removal(audio_data, Fs)`: 500 ms frames (`round(fs/2)`), trailing samples kept unchanged; while any frame maximum absolute amplitude exceeds 3 x the median of the frame maxima: take the frame with the largest maximum, the spike runs from the last sign change at or before the maximum (or frame start) to the first sign change after it (or frame end), set those samples to 0.0001, recompute | `schmidt_spike_removal.m:59-111` (rule in comments lines 9-20) |
| Homomorphic envelope | `exp(filtfilt(B_low, A_low, log(abs(hilbert(x)))))` with `butter(1, 2*8/Fs, 'low')` (8 Hz, 1st order, forward-backward); first sample replaced by the second | `Homomorphic_Envelope_with_Hilbert.m:66-76` (default 8 Hz at line 68) |
| Hilbert envelope | `abs(hilbert(x))`, no smoothing | `Hilbert_Envelope.m:45` |
| Power spectral density feature | `spectrogram(data, Fs/40, round(Fs/80), 1:1:round(Fs/2), Fs)`, mean power over the bins nearest 40 and 60 Hz | `get_PSD_feature_Springer_HMM.m:44, 54-59`, called with 40, 60 at `getSpringerPCGFeatures.m:79` |
| Wavelet feature | `wavedec` with `rbio3.9`, level 3, absolute detail coefficients at level 3, expanded to signal length | `getSpringerPCGFeatures.m:85-99`, `getDWT.m:49-66` |
| Feature resampling and normalisation | each envelope `resample(..., featuresFs, Fs)`, then `normalise_signal` (minus mean, divided by standard deviation); the PSD feature is resampled to the homomorphic feature's length | `getSpringerPCGFeatures.m:67-69, 74-75, 80-81, 98-99`; `normalise_signal.m:35-39` |
| Heart rate | on the homomorphic envelope at the audio rate (not the 50 Hz features): `y = env - mean(env)`, `xcorr(y, 'coeff')`, keep positive lags; highest value between `min_index = 0.5*Fs` and `max_index = 2*Fs` samples; `heartRate = 60/(true_index/Fs)`; no interpolation, no harmonic check | `getHeartRateSchmidt.m:65-79` |
| Systolic interval | highest autocorrelation value between `round(0.2*Fs)` and half the heart cycle; `(min_sys_duration+pos)/Fs` | `getHeartRateSchmidt.m:88-92` |
| Use of both | `getSpringerPCGFeatures` and `getHeartRateSchmidt` are both called on the same `audio_data, Fs`; heart rate and systolic interval feed the Viterbi decoding of the hidden semi-Markov model | `runSpringerSegmentationAlgorithm.m:50-56` |

Consequence of the search limits: the lag window 0.5-2 s means the code can only report 30-120 BPM.
Above 120 BPM the true cycle lies outside the window and the highest value in range is the next multiple of the cycle,
so the reported rate is about half the true rate.

## How the port in `src/hfs/window_bpm.py` applies it to an 8 s window

- The 8 s window at 16 kHz (128,000 samples) is reduced to 1 kHz (8,000 samples) with `scipy.signal.resample_poly(x, 1, 16)`
  (polyphase, Kaiser-windowed FIR). MATLAB's `resample` also uses a Kaiser-windowed polyphase FIR, but its exact
  design is not in the downloaded files: the resampling is equivalent in intent, not verified to be bit-identical.
  Where the reference code reads `Fs`, the port uses 1000 Hz (`default_Springer_HSMM_options.m:29`); whether the
  original pipeline resamples to 1 kHz before calling `getHeartRateSchmidt` is in `run_Example_Springer_Script.m`,
  which was not downloaded (not verified).
- `filtfilt` is reproduced with `scipy.signal.filtfilt(b, a, x, padtype="odd", padlen=3*(max(len(a),len(b))-1))`, the
  padding rule of MATLAB's `filtfilt` (from MATLAB documentation knowledge, not from these files: not verified here).
- `hilbert`, `xcorr(..., 'coeff')` (raw lag sums divided by the zero-lag value), the spike-removal loop and the
  0.5-2 s highest-value search are ported line by line. `log` of the Hilbert magnitude is floored at 1e-30 to avoid
  `-inf`; the original has no floor.
- Every window is processed on its own (whole-recording processing in the original); nothing carries between windows.
- The spectrogram window: MATLAB uses a Hamming window when an integer length is given (MATLAB documentation, not in
  these files); the port uses `numpy.hamming(25)` at 1 kHz, overlap 13, and evaluates only the 40-60 Hz bins needed.
- Wavelet feature: **not implemented** (no wavelet library in the environment, and the `rbio3.9` filter coefficients
  would have to come from a verified source).

Variants added by this study (not in the reference code): search range 0.3-2 s (30-200 BPM, the study's range);
run 1's half-rate check on the same autocorrelation; the combined method that averages the autocorrelations of the
homomorphic, Hilbert and PSD features (at 50 Hz as in the code, and at 100 Hz) before one peak search, with
parabolic interpolation of the chosen lag.

## Not verified

- Anything that is only in the paywalled article: the paper's reported accuracy, whether the paper uses exactly the
  PhysioNet code's parameters, training data, and the logistic-regression emission model.
- The licence file text and the project page licence (download failures above).
- `run_Example_Springer_Script.m` and the training and Viterbi files: not downloaded, not read; the hidden
  semi-Markov segmentation is not implemented.
- MATLAB behaviour used for the port (`resample` filter design, `filtfilt` padding, `spectrogram` default window and
  scaling) comes from general knowledge of MATLAB, not from the downloaded files.
