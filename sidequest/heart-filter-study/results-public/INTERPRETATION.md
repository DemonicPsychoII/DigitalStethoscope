## Plain statements (written by the delegate after reading the tables above; numbers from this run)

Data: 66 distinct EPHNOGRAM records (69 listed, ECGPCG0001 and ECGPCG0002 excluded as copies of 0031 and 0069,
ECGPCG0063 excluded because the spreadsheet marks its sound disconnected), 22 subjects, 103,927 scored windows
(about 29 h), 87,807 of them with a reliable ECG reference. Every number below is on ECG-reliable windows
unless it says "all windows"; intervals are 95 % subject-bootstrap intervals.

1. **On public data no candidate meets the acceptance target overall.** Mean absolute error of the run-1
   recommendation (Butterworth 2+2, 40-150 Hz, final counting method) is 26.6 BPM (22.3-30.7) at the rest level
   and 20.2 BPM (16.6-23.6) at the overload level (21 subjects, 87,807 windows); 60.6 % / 72.7 % of windows are
   within max(5 BPM, 10 %). The median error is small (1.8 / 0.8 BPM): most windows are right, and a large share
   are gross errors (32,863 at rest level, 37 %), mostly at one third of the rate (14,054), half the rate
   (7,259) and other wrong periods (10,969). Run 1 found 0.30 BPM on 226 windows of one person.
2. **The error is an exercise problem and grows with heart rate.** Seated rest (9 subjects, 3,709 windows):
   2.7 BPM, 91 % within tolerance, 96 % valid, acceptance target met for no filter, 25-150 Hz and 40-150 Hz with
   the final method. Lying rest in the 30-min records: 10.8-11.8 BPM. Walking, treadmill and bicycle stress
   tests: 21-54 BPM. By ECG rate (40-150 Hz, final, rest level): below 70 BPM 7.0, 70-90 18.0, 90-110 25.8,
   110-130 29.7, 130-150 33.3, 150-170 52.1, above 170 81.9 BPM (11-20 subjects per band). The time plot
   (`page/figures/run2_bpm_estimate_vs_ecg.png`) shows the mechanism: during exercise the estimate splits
   between the true rate and a track at exactly one third of it; the half-rate check cannot catch a
   one-third choice. Footstep and pedalling noise add further wrong periods.
3. **Does 40-150 Hz hold? Partly.** It beats the planned 25-150 Hz at both levels: paired difference -4.4 BPM
   (-5.5 to -3.3) at rest level and -1.8 BPM (-2.6 to -1.0) at overload level, consistent with run 1's
   direction (higher lower edge is safer), but for a different reason (exercise noise and one-third errors,
   not a start-up disturbance). It also beats no filter. It is not the best: at rest level the error keeps
   falling with the lower edge up to 80 Hz (23.3 BPM) and the steep 4th-order 60-150 Hz filter is best
   (22.0 BPM with the final method, 18.6 BPM with the half-rate check only); at overload level the curve is
   flat from 40 to 60 Hz (19.9-20.2 BPM). Run 1 had the steep 60 Hz filter as its worst candidate.
4. **Counting method: the final method is not the best on public data.** With the half-rate check only, the
   recommended filter has 23.1 BPM at rest level and 16.3 at overload, 3.5 and 3.9 BPM better than the final
   method; the 8 Hz alternative lies in between (24.5 / 17.8). The final method has a higher valid share
   (73.6 % against 62.7 % at rest level) and the lowest median error, so it is more often exactly right and
   more often wrong by a large factor. The first draft is worst everywhere (29.9 / 22.7). Run 1's order
   (first draft 0.70 > half-rate check 0.51 > 8 Hz 0.35 > final 0.30 on 25-150 Hz) is reversed between the
   last three.
5. **Rankings do not carry over from run 1.** Spearman correlation of candidate rankings between run 1 and
   public data is weak on ECG-reliable windows (27 shared candidates, final method: rho -0.24 at rest level,
   -0.08 at overload level) and moderate on all windows (0.34 / 0.54: no filter and low lower edges are bad in
   both); the steep 60 Hz filter moves from rank 27 to 1 (rest level); run 1's spread between candidates was 0.29-0.44 BPM, below its
   own reference spread, so its ranks were close to ties and a low correlation is expected.
6. **The overload level helps on public data.** Raising the level until about one beat in three clips lowers
   the error for every filter (40-150 Hz final: 26.6 -> 20.2 BPM). A likely reason is that the model adds the
   own chain's noise floor in full-scale units, so a louder heart sound stands further above it; this is a
   statement about the model, not a measured property of the device.
7. **Run 1's sound-derived reference is accurate where it says it is reliable** (see
   `sound_reference_validation.md`; 67 one-minute excerpts, 17 subjects, rest level of the chain model): on the
   1,278 windows it marks reliable, 1,275 (99.8 %) are within max(5 BPM, 10 %) of ECG and 99.7 % within 2 BPM
   (mean 0.16 BPM, largest 11.2 BPM), in every rate band up to above 170 BPM. Of 1,027 windows where it
   disagrees with ECG, it marks 1,024 unreliable. It is conservative: it rejects 42.7 % of the windows that
   would have agreed. This supports run 1's numbers on its reliable windows; it does not make run 1's five
   recordings representative of exercise.

8. **Spectrum-matched variant (rest level, 5 candidates):** same picture. 40-150 Hz final 27.5 BPM (22.6-31.9),
   3.1 BPM (2.2-4.0) better than 25-150 Hz; no filter is not significantly worse than 25-150 Hz here (+1.3 BPM,
   -0.1 to 2.4); the listening filter 100-800 Hz with the half-rate check only is best of the five (20.7 BPM).
   Matching the spectrum to the own recordings does not rescue the exercise windows.

What is inconclusive or limited:

- The public sound is the EPHNOGRAM stethoscope's, shaped by a microphone model and a level calibration, not
  by our chest-piece; it has much less energy below 20 Hz than the own recordings (13 % against 52 % at rest
  level, `calibration/SUMMARY.md`), so run 1's start-up and movement disturbances are not reproduced, and the
  exercise noise of the public recordings may not match what our device would pick up.
- The subjects exercised with the sensor on the chest; the own recordings were taken after exercise, at rest.
  The device use case (listening at rest or after exercise) is closer to the seated-rest result.
- Exercise windows dominate the pooled numbers (about 80 % of reliable windows); pooled means therefore say
  more about exercise than about the intended use.
- Holm correction (family: all other candidate x counting-method rows of the same condition against one anchor,
  123 comparisons per family at rest and overload level, 19 for the matched variant): 28 rows at rest level and
  27 at overload level are better than the recommendation after correction; best at rest level is the steep
  4th-order 60-150 Hz filter with the half-rate check only (18.6 BPM, difference -8.0 BPM), at overload level
  2nd-order 50-150 Hz with the half-rate check only (16.0 BPM, -4.2 BPM). These are differences within a
  failing range (no row meets the target overall), so they say which way to improve, not which filter to ship.
- p-values use a normal approximation of the subject bootstrap; with 22 subjects, of whom 11-16 contribute to
  each high-rate band, band-level differences are much less certain than the pooled ones.
