# Capture-chain model: calibration and how close it comes to the own recordings

Generated 2026-11-23T09:56+01:00 by `src/chain_model_calibrate.py` (481 s). Model: `src/hfs/chain_model.py`. Own recordings: Nico, 23 Nov 2026, capture firmware, raw INMP441 at 16 kHz, first 2 s discarded (`src/hfs/recordings.py`); reference beat times `reference/<name>.json`.

## Calibration

| Dataset | Recordings | Source rate | Level measure | Overload share by | Gain rest, microphone only | Gain overload, microphone only | Gain rest, matched | Gain overload, matched |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EPHNOGRAM | 20 | 8000 Hz | median_beat_peak | beats | 2.302 | 5.298 | 3.045 | 6.437 |
| CirCor | 200 | 4000 Hz | median_beat_peak | beats | 2.278 | 4.47 | 3.843 | 6.973 |

Gains are in the unit of the dataset's samples to full scale (EPHNOGRAM in mV as stored, CirCor in WAV full scale). The overload gain divided by the rest gain says how much louder the public data must be played into the model to clip as often as elevated-2 and elevated-3.

Targets (own recordings): rest level -9.6 dB re full scale (median per-beat peak of the 20-400 Hz band; median over rest-1, rest-2, elevated-1); overload: 87 of 256 beats (34.0 %) in elevated-2 and elevated-3 have a sample at the 24-bit limit; share of samples at the limit 0.050 %.

Spectrum correction of the matched variant (dB, third-octave centre frequency):

| Band | EPHNOGRAM | CirCor |
| --- | --- | --- |
| 20 Hz | +3.7 | +12.0 |
| 25 Hz | +3.3 | +12.0 |
| 31.5 Hz | +2.6 | +12.0 |
| 40 Hz | +0.8 | +10.4 |
| 50 Hz | -2.4 | +5.7 |
| 63 Hz | -5.7 | -0.7 |
| 80 Hz | -8.8 | -6.8 |
| 100 Hz | -11.1 | -10.8 |
| 125 Hz | -12.0 | -12.0 |
| 160 Hz | -12.0 | -12.0 |
| 200 Hz | -12.0 | -12.0 |
| 250 Hz | -12.0 | -12.0 |
| 315 Hz | -12.0 | -12.0 |
| 400 Hz | -12.0 | -12.0 |
| 500 Hz | -12.0 | -12.0 |
| 630 Hz | -12.0 | -12.0 |
| 800 Hz | -12.0 | -12.0 |
| 1 kHz | -12.0 | -12.0 |

## How close (medians over recordings)

Own: rest condition compared with rest-1, rest-2, elevated-1; overload with elevated-2, elevated-3.

| Measure | Condition | Own | EPHNOGRAM microphone only | EPHNOGRAM matched to own recordings | CirCor microphone only | CirCor matched to own recordings |
| --- | --- | --- | --- | --- | --- | --- |
| heart-sound level (median beat peak, 20-400 Hz), dB re full scale | rest | -9.65 | -9.69 | -9.61 | -9.74 | -9.59 |
| heart-sound level (median beat peak, 20-400 Hz), dB re full scale | overload | -3.17 | -2.42 | -3.14 | -3.96 | -4.42 |
| overall level (RMS of the whole signal), dB re full scale | rest | -19.71 | -22.85 | -21.37 | -21.33 | -20.39 |
| overall level (RMS of the whole signal), dB re full scale | overload | -13.68 | -16.29 | -15.03 | -17.34 | -15.84 |
| crest factor (peak over RMS), dB | rest | 18.08 | 18.30 | 16.86 | 21.33 | 20.30 |
| crest factor (peak over RMS), dB | overload | 13.75 | 15.73 | 14.34 | 17.34 | 15.84 |
| energy below 20 Hz, % | rest | 51.74 | 17.41 | 27.64 | 2.48 | 2.78 |
| energy below 20 Hz, % | overload | 35.12 | 18.36 | 30.30 | 1.11 | 2.05 |
| energy 20-150 Hz, % | rest | 48.18 | 80.39 | 72.09 | 43.09 | 82.99 |
| energy 20-150 Hz, % | overload | 64.79 | 78.24 | 69.37 | 38.04 | 83.82 |
| energy 150-800 Hz, % | rest | 0.06 | 2.11 | 0.17 | 39.60 | 7.07 |
| energy 150-800 Hz, % | overload | 0.08 | 3.20 | 0.23 | 45.03 | 8.02 |
| energy above 800 Hz, % | rest | 0.00 | 0.02 | 0.01 | 7.23 | 2.49 |
| energy above 800 Hz, % | overload | 0.00 | 0.04 | 0.01 | 8.66 | 2.89 |
| samples at full scale, % | rest | 0.00 | 0.00 | 0.00 | 0.10 | 0.04 |
| samples at full scale, % | overload | 0.05 | 0.11 | 0.29 | 0.44 | 0.31 |
| beats with a sample at full scale, %, median over recordings | rest | 1.04 | 0.00 | 0.00 | 2.61 | 0.00 |
| beats with a sample at full scale, %, median over recordings | overload | 34.00 | 23.06 | 31.55 | 20.00 | 11.11 |
| beats with a sample at full scale, %, all beats pooled (the calibrated quantity) | rest | 1.19 | 3.44 | 4.46 | 9.18 | 11.53 |
| beats with a sample at full scale, %, all beats pooled (the calibrated quantity) | overload | 33.98 | 34.05 | 34.00 | 34.03 | 33.88 |
| floor between beats relative to heart sounds (10th / 90th percentile of 100 ms power, 20-400 Hz), dB | rest | -21.17 | -13.78 | -16.36 | -11.10 | -14.62 |
| floor between beats relative to heart sounds (10th / 90th percentile of 100 ms power, 20-400 Hz), dB | overload | -26.23 | -16.65 | -17.50 | -14.05 | -15.56 |

Spectral shape per third-octave band, modelled minus own median (dB, rest condition; each spectrum relative to its 20 Hz-1 kHz band sum, so overall level does not enter):

| Band | EPHNOGRAM before matching | EPHNOGRAM after matching | CirCor before matching | CirCor after matching |
| --- | --- | --- | --- | --- |
| 20 Hz | -1.9 | +0.2 | -6.0 | -6.0 |
| 25 Hz | -1.2 | +0.8 | -6.1 | -3.9 |
| 31.5 Hz | -1.2 | +0.2 | -6.4 | -1.7 |
| 40 Hz | -2.3 | -1.2 | -7.6 | +1.4 |
| 50 Hz | +0.3 | -0.9 | -5.2 | +2.3 |
| 63 Hz | +4.8 | -0.7 | -0.6 | +2.6 |
| 80 Hz | +6.5 | -1.0 | +5.6 | +2.9 |
| 100 Hz | +12.5 | +2.9 | +12.5 | +5.5 |
| 125 Hz | +12.9 | +3.0 | +15.8 | +7.7 |
| 160 Hz | +10.4 | -0.3 | +16.2 | +8.0 |
| 200 Hz | +13.6 | +3.1 | +22.2 | +14.2 |
| 250 Hz | +12.4 | +1.4 | +23.5 | +15.8 |
| 315 Hz | +16.3 | +5.4 | +28.2 | +20.9 |
| 400 Hz | +17.9 | +5.9 | +30.8 | +23.6 |
| 500 Hz | +17.0 | +5.6 | +33.1 | +26.1 |
| 630 Hz | +16.5 | +4.8 | +37.7 | +30.8 |
| 800 Hz | +15.2 | +3.5 | +39.0 | +32.6 |
| 1 kHz | +13.1 | +2.4 | +38.8 | +32.9 |

Figures: `figures/long_term_spectra.png`, `figures/band_difference.png`, `figures/time_domain.png`.


## Modelling choices and their sources

- Resampling: `scipy.signal.resample_poly` (polyphase, Kaiser window beta 5.0, cutoff at the lower Nyquist frequency).
  The public data carry nothing above their own Nyquist frequency: CirCor (4 kHz) nothing above 2 kHz, EPHNOGRAM
  (8 kHz) nothing above 4 kHz; the model then fills that region with the own recordings' floor only (rates: dataset
  headers, read by `hfs.circor` / `hfs.ephnogram`).
- INMP441: numbers from `Development/system/testing/AUDIO/chain-measurement/microphone_model.py` (DigitalStethoscope
  repository; datasheet record `tdk_inmp441_datasheet_2014`, DS-INMP441-00 rev. 1.0). Acoustic high-pass 60 Hz
  (checked in the record); digital high-pass 3.7 Hz at 48 kHz scaled to 1.23 Hz at 16 kHz and pass band
  0.423 x fS are NOT yet checked against the datasheet page (unverified, as marked in that file); first order for both
  corners and the scaling with fS are project assumptions of that file. Applied as causal first-order sections
  (a first-order high-pass is minimum phase); the 17.2-sample group delay is omitted so that dataset segmentations stay
  aligned. Phase is not what the model is trusted for.
- Chest-piece: none applied (lead decision R2-4 in `STATE.md`). The public sensors stay inside the signal.
- Spectrum match (variant): smooth third-octave correction 20 Hz-1 kHz, limit +-12 dB, three-point smoothing, linear
  interpolation over octaves inside, tapering to 0 dB within one octave outside; zero-phase linear-phase FIR,
  8191 taps (Blackman window, `firwin2`). It moves the dataset's median long-term spectral shape onto the own median
  shape. It stands for chest-piece, tube and sensor differences together AND for differences between persons (one
  adult man, own recordings, against the dataset's subjects); an empirical match, not a physical model (project decision).
- Level measure: median over beats of the largest absolute value of the zero-phase 4th-order Butterworth 20-400 Hz
  band. Chosen because it measures the heart sounds themselves (beat by beat, robust to a few loud beats and to
  between-beat noise) on the band where heart-sound energy lies, and it is computable the same way on own data
  (reference beats) and on public data (CirCor S1 starts, EPHNOGRAM ECG R peaks); below 20 Hz is excluded because the
  public sensors deliver little there (project decision). One gain per dataset and condition (median over recordings),
  so differences between recordings stay; `per_recording_normalisation=True` switches to one gain per recording.
- Overload: the gain at which the same share of beats as in elevated-2/elevated-3 contains a sample at a 24-bit limit
  (quantile of the per-beat gains to reach a limit). Beat segments run from midpoint to midpoint between beat times.
- Noise floor: per third-octave band 20 Hz-6.3 kHz, the 10th percentile of 250 ms frame power (hop 62.5 ms),
  median over the five own recordings (own measurement, 23 Nov 2026). This floor contains room and body sound and the
  chest-piece's pick-up, not only microphone noise. Added: Gaussian noise (seeded) shaped so that the floor reaches the
  target where the modelled floor lies below it; nothing is subtracted. The INMP441 datasheet signal-to-noise ratio /
  equivalent input noise is NOT recorded in `thesis-material/quellen.md` (the `tdk_inmp441_datasheet_2014` record
  lists only frequency response, group delay and interface data), so no comparison with a datasheet noise figure is
  made here (unverified).
- Hard limit: the own recordings reach exactly -8388608 (lower 24-bit limit; 473 samples in elevated-2, 457 in
  elevated-3) in flat runs of up to 33 samples, while the positive peaks stay below +8388607 (largest 8313073 in
  elevated-2); rest-1 hits both limits only during its movement artefact (own measurement 23 Nov 2026, `load_recording`).
  At the clipped samples the part below 20 Hz (4th-order zero-phase split at 20 Hz) contributes a median of
  -0.37 full scale (elevated-2) and -0.19 (elevated-3), the part from 20 Hz upward -0.64 and -0.81; with the part below
  20 Hz removed only 3 of 129 and 5 of 127 beats would reach the limit instead of 42 and 45 (own measurement,
  23 Nov 2026). So the overload is a heart-sound peak riding on a negative slow excursion, and it is one-sided because
  of that excursion, not because the positive limit differs. The model clips symmetrically at -8388608 / +8388607 and
  rounds to integers: clipping lands on whichever polarity reaches the limit.

## Where the model cannot reach the real chain

- Content below about 20 Hz: the own recordings carry a large share of their energy there (see table); the public
  sensors deliver much less (their own sensors' low-frequency roll-off is unknown; the cause on the own side, chest
  motion or pressure in chest-piece and tube, is not measured). In elevated-2/-3 a negative slow excursion adds
  0.2-0.4 full scale under the heart sound at the clipped samples (see above). In the model the overload gain must
  push the heart sounds themselves to full scale, so clipping hits both polarities rather than only the lower limit,
  and the gain is higher than the real loudness difference between rest and elevated recordings.
- The spectrum match is limited to +-12 dB and to 20 Hz-1 kHz; where the correction hits the limit, the shape stays off
  (see the band table).
- No content above 2 kHz (CirCor) or 4 kHz (EPHNOGRAM): the region is filled with floor noise only.
- Floor: the public recordings' own noise (their sensors, rooms, children crying in CirCor) remains; where it lies above
  the own floor nothing is removed.
- The 17.2-sample microphone delay and the microphone phase are not modelled.

## Known problems

- The overload gain matches the pooled share of beats (all beats of all recordings together). Per recording the
  share scatters widely, so the median over recordings lies below the target (see the two rows in the table).
- At the rest gain the public data clip more often than the own rest recordings (pooled 3-12 % of beats against
  1.2 %): their beat-to-beat and recording-to-recording level spread is wider than the own three rest recordings'.
- The EPHNOGRAM selection takes records whose ECG reference file exists in `reference-public/ephnogram/` at run time;
  while that folder still grows, a rerun may pick other records (the selection used is in `selection.json`).
- The EPHNOGRAM beat times are ECG R peaks, the own ones S1 energy centroids and the CirCor ones S1 onsets; the
  midpoint-to-midpoint beat segments still contain S1 and S2 in all three cases at the heart rates seen.
- Matching hits the +-12 dB limit from 125 Hz upward for both datasets; CirCor stays 15-33 dB above the own shape
  from 200 Hz to 1 kHz even after matching.
