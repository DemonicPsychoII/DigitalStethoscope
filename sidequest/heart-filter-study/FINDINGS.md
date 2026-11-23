# FINDINGS: heart filter study (TICKET-189)

Each finding with evidence and confidence. Updated as results arrive.

## F1 Reference heart rate (no ECG)

- Three offline, non-causal methods agree within 1.8 BPM on every window marked reliable
  (226 of 255 windows). Evidence: `reference/SUMMARY.md`, `reference/<name>.json`, figures in
  `reference/figures/`. Lead check: marks sit on the first heart sound in elevated-1 and elevated-2;
  median cycle profile shows two sounds per cycle, so the period is the full cycle, not half or double.
- Rate ranges per 8 s window: rest-1 73-82, rest-2 80-87, elevated-1 86-129, elevated-2 119-144,
  elevated-3 116-149 BPM.
- Confidence: medium. All methods use the same sound; no independent sensor. elevated-1 has no
  reliable reference for windows ending 10-17 s (steepest fall).

## F2 Listening: headroom and loudness (evidence `listening/SUMMARY.md`, `listening/metrics_summary.csv`)

- Input overload (samples at the 24-bit limit after 2 s): rest-1 26, rest-2 0, elevated-1 16,
  elevated-2 473, elevated-3 457. 32-60 % of the Raw energy lies below 20 Hz. Confidence: high (counted).
- One fixed gain safe for all five recordings (low-pass 800 Hz, Butterworth 2+2), by high-pass edge:
  10 Hz -3.0 dB, 20 Hz -2.8, 30 Hz -1.7, 40 Hz -0.2, 50 Hz +0.7, 60 Hz +1.4, 80 Hz +3.5,
  100 Hz +6.0, 150 Hz +8.4 dB. So the design candidate 40-800 Hz has no room for a boost, and
  high-pass edges at or below 40 Hz clip more than Raw at full volume, because filtering the
  flat-topped overloaded beats makes them overshoot. Limiting recordings: elevated-2 and the
  rest-1 movement artefact. Confidence: high for these recordings; the gain depends on the worst case recorded.
- Loudness over Raw at the safe gain (ISO 226 60-phon proxy / A-weighted): design 40-800 -1.5 / -1.7 dB;
  100-800 2+2 +1.5 / +1.1; 100-800 4+4 +2.5 / +2.0; 150-800 4+4 +3.4 / +2.8. By BS.1770-4 K-weighting no
  filter is louder than Raw. Confidence: low as a statement about heard loudness (proxies; earpiece unknown).
- Other sound: between-beat level relative to heart sounds (A-weighted): Raw -14.9 dB, design -14.3,
  100-800 -11.8, 150-800 4+4 -9.9, BPM 25-150 -17.8. Raising the high-pass makes the gaps relatively
  louder; the low-pass edge matters little (at most 1.2 dB; under 2.4 % of energy above 1 kHz).
- Shortlist of 8 with samples in `listening/samples/`; the subjective choice is Nico's and pending.

## F3 BPM filter (evidence `results/SUMMARY.md`, `results/bpm_filter_grid.csv`; 255 windows, 226 clean)

- With the final estimator, every sensible band-pass reaches 0.29-0.31 BPM mean error on clean
  windows, 100 % within tolerance max(5 BPM, 10 %), 0 gross errors. 147 of the top 150 rows are within
  bootstrap noise of the best. Family, order, upper edge, input limiter, envelope rate: no measurable
  effect. Confidence: high that differences are not measurable here; the error figure itself is below
  the reference's own accuracy (about +-1.5 BPM).
- What separates filters is disturbances (all 255 windows, Butterworth 2+2, upper edge 150 Hz, final
  estimator): Raw 4.22 BPM (16 gross errors), 10 Hz 2.46 (10), 20 Hz 0.74 (1), 25 Hz design 0.69 (1),
  30 Hz 0.35 (0), 40 Hz 0.35 (0), 50-80 Hz 0.36 (0). Rests on two events (rest-1 movement at 40 s,
  elevated-1 start). Confidence: medium for "a lower edge of 30 Hz or more protects", low for the exact edge.
- The estimator step matters more: design 25-150 Hz with the first-draft estimator (highest peak) 0.70 BPM
  and 1 gross error on clean windows; Raw 1.32 BPM, 3 gross errors; with the half-lag check 0.30 and 0.42, 0.
- Listening filters as analysis input (final estimator): 40-800 Hz 0.30 clean / 0.35 all; 100-800 Hz 0.30 / 2.4.
- Leave-one-recording-out: picking the filter on four recordings does not beat the design filter on the fifth.
- Cost (estimate, not measured): filter 10 multiplications per sample, estimator RAM 8.1 kB, window 3.2 kB,
  about 0.5 % of one 240 MHz core, autocorrelation about 2 ms once per second.
- Validity rule (quality below 0.3 = invalid) never triggered on clean windows and did not flag Raw's
  wrong estimates during movement: untested.

## F4 Corrections after council (supersede earlier wording above)

- The lower-edge step 25 -> 40 Hz rests on ONE window (elevated-1, ending 11 s; reference uncertain there) and
  appears only with the final counting method (two smoothing steps at 5 Hz + half-rate check). With the
  half-rate check alone (0.51 BPM clean) or with two steps at 8 Hz (0.35 BPM clean) the planned 25-150 Hz
  filter is within tolerance in 255/255 windows. Filter and counting method must be fixed together.
  Confidence in "40 Hz is better than 25 Hz": low; it is a precaution.
- "Design and upper edge do not matter" holds on clean windows only; in the 29 other windows several designs
  and edge combinations show gross errors. 52 filters with a steep 60 Hz lower edge fail on clean windows
  (a third of the rate in part of elevated-3).
- Reference: method spread on clean windows mean 0.30, median 0.16, max 1.79 BPM. The device's mean
  difference (0.30) is of the same size. Absolute accuracy unknown. The earlier "+-1.5 BPM" is withdrawn.
- Overload after exercise is on about one beat in three (42/129, 45/127), at the lower limit.
- Safe boost for 100-800 Hz gentle is 5.975 dB: a setting of 6.0 dB clips 3 values; use 5.9 dB.
- 29 non-clean windows = 25 with a detected disturbance + 4 with only an uncertain beat.

## F5 Result as published (version 2, https://homelab-server.tail15fafc.ts.net:8092/p/heart-filter-study/)

- BPM filter recommendation (precaution, to be fixed together with the counting method): Butterworth,
  2nd-order lower edge 40 Hz + 2nd-order upper edge 150 Hz; 0.30 BPM mean difference on 226 clean windows,
  0.35 BPM on all 255, 255/255 within tolerance, 0 gross errors, 10 multiplications per value.
  Planned 25-150 Hz: 0.30 / 0.69 BPM, 254/255, 1 gross error (with the final counting method).
  No filter: 0.42 / 4.22 BPM, 239/255, 16 gross errors.
- Counting method: absolute value, two smoothing steps at 5 Hz, 100 values per second, 8 s (800 values,
  3.2 kB), autocorrelation once per second, half-rate check. Estimated about 0.5 % of one core, 8.1 kB.
- Listening filter: open (Nico's ear). Planned 40-800 Hz has -0.236 dB room; 100-800 Hz gentle allows
  5.975 dB (set 5.9 dB), 1.1-1.5 dB louder than Raw by two estimates, 6.5 LU quieter by the third.
- Council: 6/6/6, 8/8/9, 8/9/9 (Astra/Fable/Neon); all blocking findings corrected.

---

# Run 2: public data

## R2-F1 CirCor DigiScope v1.0.3 as downloaded (evidence `public-data/circor-1.0.3/MANIFEST.json`, `public-data-summary/circor.md`)

- 10,434 of 10,434 files match the source's SHA-256 list. The openly published part is the training set:
  942 patients, 3,163 recordings (the dataset page's 1,568 / 5,272 include the held-back part). 4,000 values
  per second, 16 bit. Confidence: high (counted from the files).
- Murmur: 179 present (178 systolic: grade I 104, II 28, III 46; pitch low 87, medium 49, high 42; 5 diastolic),
  695 absent, 68 unknown. Ages: 6 neonates, 126 infants, 664 children, 72 adolescents, 74 without age (70 pregnant).
  Median heart rate from the segmentation: child 103, infant 136 BPM.
- Usable for the murmur test (at least 5 complete annotated cycles): 179 murmur patients (495 recordings at a
  location where the murmur is heard), 695 murmur-free patients in the result files (the dataset summary counts 694 with at least 5 complete cycles; 2,380 recordings).

## R2-F2 EPHNOGRAM v1.0.0 as downloaded, ECG reference (evidence `public-data/ephnogram-1.0.0/MANIFEST.json`, `reference-public/ephnogram/SUMMARY.md`)

- All 69 records downloaded (WFDB, 8.02 GB), every file matches the source's SHA-256 list. 24 subjects, 8,000 values
  per second, 8 x 30 s and 61 x 30 min. Two record pairs are sample-identical under different subject labels
  (0001 = 0031, 0002 = 0069); 0001 and 0002 are excluded, 67 distinct records remain. Confidence: high.
- Activities per the spreadsheet: sitting, lying, walking 3.7 km/h, walk and sit-stand protocol, treadmill stress
  test (Bruce protocol), stationary bicycle, bicycle stress test. The signal's physical scale is unverified.
- ECG reference: two offline R-peak detectors (band-pass/derivative type; wavelet + template type). 89,653 of
  105,971 8-second windows are reliable (84.6 %). Reliable windows by ECG heart rate: <70: 8,783 (16 subjects);
  70-90: 14,150 (20); 90-110: 32,301 (16); 110-130: 21,341 (14); 130-150: 7,350 (13); 150-170: 3,733 (13);
  >170: 1,995 (11). Rates up to about 199 BPM. Confidence: high for the rate; the two detectors share the final
  peak refinement, so their near-zero difference (max 0.76 BPM on reliable windows) is agreement on which beats
  exist, not an independent timing check. Lead check pending: figures.

## R2-F3 Chain model and how close it comes to Nico's recordings (evidence `calibration/SUMMARY.md`, `calibration/how_close.csv`)

- Model: resample to 16 kHz -> INMP441 datasheet response (unverified fields stay marked) -> one gain per dataset
  and level condition -> missing noise floor added -> hard limit at 24 bit. No chest-piece correction (decision R2-4).
- Level: heart-sound level at rest matches within 0.1 dB (-9.65 own, -9.69 EPHNOGRAM, -9.74 CirCor, dB re full scale).
  Overload condition: 34 % of beats reach full scale, as in elevated-2/-3 (calibrated quantity).
- Spectrum: NOT close. Relative to the own median, modelled EPHNOGRAM has +10 to +18 dB and CirCor +12 to +39 dB
  from 100 Hz to 1 kHz; energy below 20 Hz is 52 % own, 17 % EPHNOGRAM, 2.5 % CirCor; energy 150-800 Hz is 0.06 % own,
  2.1 % EPHNOGRAM, 39.6 % CirCor. The matched variant brings EPHNOGRAM within about 6 dB (20 Hz-1 kHz) but CirCor stays
  14-33 dB off above 200 Hz (correction limited to +-12 dB).
- Own finding on the overload mechanism: in elevated-2/-3 the cut-off beats ride on a slow negative swing below 20 Hz
  (0.2-0.4 of full scale); without the part below 20 Hz only 3 of 129 and 5 of 127 beats would reach the limit
  (instead of 42 and 45). The public data lack this slow part, so the model's overload hits both polarities.
- Confidence: high for the numbers; the cause of the spectral difference (sensor, chest-piece and tube, person, age) is
  not separable.

## R2-F4 BPM on public data against ECG (evidence `results-public/SUMMARY.md`, `results-public/bpm_public_grid.csv`, `bpm_public_by_scenario.csv`; 66 records, 22 subjects, 87,807 ECG-reliable windows, about 29 h)

- Run-1 recommendation (40-150 Hz gentle, final counting method), rest level: mean error 26.6 BPM (95 % interval over
  subjects 22.3-30.7), median 1.8 BPM, 61 % within tolerance; overload level 20.2 BPM. Most windows are right; 37 % are
  gross errors: 14,054 at one third of the rate, 7,259 at half, 10,969 other. No combination meets the acceptance
  target (mean error <= 5 BPM with >= 90 % valid) overall. Confidence: high that the method fails on this exercise sound.
- By activity: seated rest 2.7 BPM, 91 % within tolerance, acceptance target met (9 subjects, 3,709 windows); lying
  10.8-11.8 BPM; walking, treadmill, bicycle 21-54 BPM. By ECG rate: <70: 7.0; 70-90: 18.0; 90-110: 25.8; 110-130: 29.7;
  130-150: 33.3; 150-170: 52.1; >170: 81.9 BPM.
- Filter: 40-150 Hz beats the planned 25-150 Hz by 4.4 BPM (3.3-5.5) at rest level and 1.8 BPM (1.0-2.6) at overload
  level; no filter is worst (33.5). Error keeps falling up to a lower edge of 80 Hz (23.3); the steep 60-150 Hz filter,
  run 1's worst, is best here (22.0 final method; 18.6 with the half-rate check only). Rankings do not carry over
  (Spearman -0.24 / -0.08 on reliable windows; run 1's candidates were near ties).
- Counting method: half-rate check only (23.1 BPM) beats the final method (26.6) on public data: run 1's order of the
  last three methods is reversed.
- Run 1's sound-derived reference, validated against ECG (67 one-minute excerpts, 17 subjects): on the 1,278 windows
  it calls reliable, 99.7 % are within 2 BPM of ECG (mean difference 0.16, largest 11.2 BPM); it flags 1,024 of 1,027
  disagreeing windows as unreliable; it also rejects 42.7 % of windows that would have agreed. Confidence: high that
  run 1's reference was sound where it claimed to be.
- Limits: sensor strapped to the chest during exercise; 81 % of windows are exercise; the modelled sound has far less
  energy below 20 Hz than the own recordings, so run 1's movement and start-up disturbances are not reproduced.

## R2-F5 Listening filters and murmurs on CirCor (evidence `listening-public/SUMMARY.md`, `murmur_tests.csv`, `murmur_auc.csv`, `clipping_public.csv`; 178 patients with a systolic murmur, 695 without; metrics fixed before the analysis, decision R2-6)

- Primary (A-weighted level of the murmur phase at the output, difference to no filter, each at its run-1 boost):
  40-800 Hz design -1.87 dB (-2.09 to -1.69); 100-800 Hz gentle +4.10 (+3.89 to +4.29); 100-800 steep +5.49; 150-800
  steep +7.69; 60-800 elliptic +2.15; above 80 Hz +3.40; 25-150 Hz -14.38; 40-150 Hz -12.26. All Holm p < 0.001
  (family of 48). At 0 dB boost every band-pass costs 1.6-2.0 dB (the 800 Hz upper edge); the gains are the boost.
- Secondary: murmur over S1+S2 (unweighted) falls for every filter (-0.6 to -2.6 dB; unexplained, A-weighted version
  falls only 0.1-0.6 dB); murmur over diastole rises +1.6 (design) to +3.4 dB (100-800 steep).
- Distinguishing murmur from no murmur (area under the curve, murmur over S1+S2 / murmur over diastole): no filter
  0.53 / 0.79; design 0.62 / 0.86; 100-800 gentle 0.70 (+0.17, +0.13 to +0.21) / 0.90; 100-800 steep 0.72 / 0.90;
  BPM position 0.51. Grade III/VI 0.94, grade I/VI 0.61; high pitch 0.97; low-pitched murmurs at chance for every filter.
  Lower edges 80-150 Hz overlap within their intervals.
- Run 1's provisional pick (100-800 Hz gentle, +5.9 dB) is in the top group: confirmed for murmurs, not separated
  from its steeper siblings. The 40-800 Hz design is weaker on every murmur measure. BPM filters are unusable for murmurs.
- Clipping: at the modelled resting level 3,141 of 3,162 modelled CirCor recordings already touch the 24-bit limit at
  the input (CirCor is more peaky: crest factor 22 dB against 18 dB), and every boosted candidate clips on 97-100 %
  of recordings; a gain safe for 99 % would be -4 to -6 dB. This depends on the level calibration and is not a device
  measurement; effect on the metrics at most 0.1 dB. Run 1's safe boosts are safe for the five own recordings only.
- Run 1 vs public rank agreement over the shortlist: A-weighted +0.98, hearing-curve +0.98, broadcast loudness -0.93
  (order reverses: public data have little energy below 60 Hz), sound between beats +0.38.
- Sensitivity (overload level; spectrum matched): same ranking. Two random halves of patients: same signs.
- Confidence: high for the direction (lower edge 80-100 Hz helps murmurs stand out), low as a statement about what a
  listener hears: energy measures, children, another sensor, nothing above 2 kHz, far brighter than our chain.

## R2-F6 Non-real-time (whole-window) BPM processing (evidence `results-window/SUMMARY.md`, `own_recordings.csv`, `public_ephnogram.csv`, `device_budget.csv`, `sources/springer-method-notes.md`)

- Springer/Tarassenko/Clifford 2016 reference code, read from the source files (not run): 25-400 Hz Butterworth 2nd-order
  each, forward-backward; spike removal (500 ms frames, 3 x median peak); homomorphic envelope (8 Hz 1st-order
  forward-backward low-pass of the logarithm of the Hilbert magnitude); autocorrelation, highest value between 0.5 and
  2 s lag (so at most 120 BPM). Article not read (closed access). Code licence GPL-3.0-or-later per file headers.
- Own recordings (255 windows, baselines reproduce run 1 exactly): causal 40-150 Hz 0.30 / 0.35 BPM (reliable / all);
  zero-phase 2+2 40-150 Hz 0.33 / 0.39; Springer as published 20.97 / 19.19 (69 gross errors: halves rates above 120);
  Springer with range 30-200 BPM 0.38 / 0.44. Nothing beats the causal baseline; differences of 0.05 BPM cannot be separated here.
- Public data with ECG (21 subjects, 21,956 reliable windows, every 4th second), paired difference to the causal baseline
  (26.9 BPM rest level, 20.2 overload level), 95 % range over subjects, Holm-corrected: zero-phase 2+2 40-150 Hz -3.6
  (-4.6 to -2.7) / -1.2; the same sections run twice causally -3.5 (-4.5 to -2.6) / -1.0: the gain is steepness, not
  missing phase delay. Springer heart rate + half-rate check -6.2 (-8.4 to -3.7) / -9.7 (-11.9 to -7.1); Springer
  envelopes combined -7.4 / -8.8; they win above 110 BPM (20-29 BPM better from 130 BPM) and lose below 70 BPM (7-11 BPM
  worse). A zero-phase 1 kHz filter with the logarithmic envelope alone gives -6.1 (exploratory, rest only): the
  logarithmic envelope is the likely ingredient.
- Window edges: no handling = padding; discarding 0.25-0.5 s per end is worse. Reducing to 1 or 2 kHz before storing
  gives the same error with 31 kB instead of 512 kB.
- Device estimate (not measured; memory-access penalty unknown): baseline 2.0 ms per update, 0.52 % of a core, 7.2 kB;
  sections twice 0.79 %; zero-phase at 16 kHz 49 ms, 4.9 %, about 1 MB; zero-phase at 1 kHz 5 ms, 0.60 %, 62.5 kB;
  logarithmic envelope at 1 kHz 20 ms, 2.1 %; Springer heart rate 37 ms, 3.8 %, 31 + 223 kB. All fit at one update per second.
- Answer: non-real-time filtering is not needed for its gain. The lead for more accuracy is the logarithmic envelope with
  a range to 200 BPM and the half-rate check; a causal version was not tested. Confidence: medium (public numbers depend
  on the chain model; all methods are far from the acceptance target during exercise).

## R2-F7 Why one third of the rate, and an improved counting method (evidence `results-public/one_third_diagnosis.md`, `improved_method.md`, `improved_method_tables.md`, `improved_method_own_recordings.csv`)

- Cause: the heart sound is cleanly periodic, so the repeat-pattern curve has nearly equal peaks at 1, 2, 3, 4 beat
  spacings (0.93 / 0.92 / 0.94 / 0.92 in one example at 146 BPM). The curve is normalised separately at each shift,
  which removes the natural preference for short shifts; three spacings then wins by 5-12 %. Same result with the sound
  only resampled (no chain model): it is the method on this sound, not the model. Only possible from about 90 BPM
  (three spacings must fit into the 2 s search range). The 5 Hz smoothing makes it worse. Confidence: high.
- Improved method (chosen on 11 development subjects, tested once on 10 others): weight the curve by the overlap
  (800 - shift)/800, then take the shortest of 1/4, 1/3, 1/2 of the best shift whose peak is at least 0.6 of the
  highest; validity adds a margin (0.15) and agreement within 10 % with one of the last two estimates. Cost: under 1 %
  more work, 1.6-3.2 kB.
- Test subjects, 40-150 Hz: rest level 28.4 -> 13.1 BPM (95 % 7.1-19.7), overload level 22.2 -> 7.2 (4.5-10.1); paired
  gain about 15 BPM; one-third errors fall 80-98 %. Stress tests 41.1 -> 15.2, steady pedalling 22.4 -> 4.7, walking
  26.3 -> 16.3, above 130 BPM 38-78 -> 2-9. Worse: lying 5.4 -> 8.1, below 70 BPM 4.3 -> 8.7, sitting 2.7 -> 3.7.
  Wrong numbers shown as valid: 29 % -> 6 % (rest level), 25 % -> 3 % (overload), with 65-70 % of windows shown.
- Acceptance target (<= 5 BPM with >= 90 % valid): met only at seated rest with the run-1 rule; no exercise group with
  either method.
- Own recordings: at 40-150 Hz identical error (0.30 / 0.35, 255/255 within tolerance, 0 gross), valid share 97.6 %.
- Filter recommendation unchanged (same ranking, smaller gaps). Confidence: medium; tuned on one database, 22 young men.


## R2-F8 Result as published (version 3, https://homelab-server.tail15fafc.ts.net:8092/p/heart-filter-study/v/3/)

- Corrections to the findings above after the council (they supersede earlier wording): R2-F4 "no filter is worst" -> no filter
  is 6.9 BPM worse than 40-150 Hz; a 10 Hz edge, the FIR candidate and the steep 150-800 Hz filter are as bad or worse.
  R2-F5 "BPM filters are unusable for murmurs" -> poor by murmur level (12-14 dB quieter), separation against the quiet
  part still 0.80-0.85; the separation gain of 100-800 Hz does not need the boost (0.696 without, 0.701 with); the
  quiet-part separation score is exploratory; low-pitched murmurs 0.44-0.51 on the heart-sound measure, 0.82 on the
  quiet-part measure. R2-F6 "the gain is steepness, not phase" -> almost: forwards-backwards minus twice-forwards is
  -0.07 BPM (-0.38 to +0.24) at rest level and -0.25 (-0.49 to -0.02) at overload level. R2-F7: on Nico's recordings
  the improved method makes 25-150 Hz equal to 40-150 Hz (0.30/0.36 vs 0.30/0.35, no gross error), so the evidence for
  40 Hz over 25 Hz is the public data alone; 100-800 Hz as counting input is equal at rest level but 6.1 BPM worse at
  overload level.
- Recommendations: BPM filter 40-150 Hz gentle (kept); counting method: improved peak choice as new starting point,
  slow-rate weakness open; listening: 100-800 Hz gentle first candidate (boost 5.9 dB supported by own recordings only),
  decision by ear pending. Council: 8/7/6, 8/8/8, no score/8/8 (Astra/Fable/Neon).


---

# Run 3: editorial pass (no new findings)

Version 4 (https://homelab-server.tail15fafc.ts.net:8092/p/heart-filter-study/v/4/) restructures version 3 as a paper. No new
analysis and no changed number: every number of version 3 is in version 4 (check and review recorded in `STATE.md`, "Run 3").
Terms used from version 4 on: "Nico's recordings", "ECG collection" (EPHNOGRAM), "murmur collection" (CirCor); "first-draft",
"original" (earlier "final" / "method of the first part") and "improved" counting method; filters by band and steepness.


## Late corrections (version 5, 13:56): supersede earlier wording

- Upper edge of the BPM filter on public data: a small effect, not none (lower edge 40 Hz: 100 Hz is 0.6 BPM worse than 150 Hz at
  rest level; 800 Hz is 1.1 BPM worse at overload level). Evidence `results-public/bpm_public_grid.csv`.
- The 3.5 BPM gain of "the filter applied twice" is for the recommended 40-150 Hz filter at rest level, not the planned 25-150 Hz.
- The murmur separation score on the heart-sound measure rises for every candidate except 25-150 Hz (0.531 -> 0.508).
- Council, final: 8/7/6, 8/8/8, 8/8/8 (Astra/Fable/Neon); Astra's round 3 arrived late and is included in version 5.
