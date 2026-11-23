### Does the heart rate have to be counted in real time?

No. The count uses the last 8 seconds, which sit in the device's memory. The counting path could therefore work on the whole stored stretch at once and look "ahead" inside it, which a filter that handles each value as it arrives cannot. Nico asked for this to be explored during this version (23 November 2026). Listening is not affected: the sound for the ear must stay in real time.

Two ideas were tried, on the same 8-second windows as before:

- **Filtering forwards and backwards.** Running a filter over the stored stretch once forwards and once backwards cancels the small delay that a filter gives to different pitches, and makes its edges twice as steep.
- **The method of Springer, Tarassenko and Clifford [20].** A widely used research method for marking the heart sounds. Its openly published program code [21] was read for this study (the article itself is not freely available and was not read; the code was not run). Before it marks anything, the code prepares the sound and estimates the heart rate: a filter from 25 to 400 Hz run forwards and backwards, removal of loud clicks, a loudness curve taken from the *logarithm* of the signal (which makes loud and soft beats more alike), and a repeat-pattern search that, unlike the one of the first part, lets longer shifts count less, but only looks between 0.5 and 2 seconds, so that it cannot report more than 120 BPM. Its second half, a statistical model that marks each heart sound, was not implemented: it needs trained values this study does not have.

::figure{src="page/figures/run2_window_methods_error.png" alt="Mean heart-rate error of fifteen counting variants on the own recordings and on the public recordings at two loudness levels" caption="Counting on the whole stored 8 seconds against the method of the first part (amber, dashed line), on Nico's recordings and on the public recordings with ECG (every fourth window; lines: 95 % ranges over people). " width="wide"}

| Variant | Own recordings, clean / all windows (BPM) | Public with ECG, change against the first part's method (BPM, rest level) | The same at overload level |
|---|---:|---:|---:|
| Method of the first part: filter while recording, 40–150 Hz | 0.30 / 0.35 | 0 (mean error 26.9) | 0 (mean error 20.2) |
| Same filter, forwards and backwards over the stored stretch | 0.33 / 0.39 | −3.6 (−4.6 to −2.7) | −1.2 (−2.1 to −0.5) |
| Same filter applied twice while recording (no look-ahead) | 0.32 / 0.38 | −3.5 (−4.5 to −2.6) | −1.0 (−1.9 to −0.2) |
| Springer's preparation as published (limit 120 BPM) | 21.0 / 19.2 | worse (+7.1) | worse (+4.4) |
| Springer's preparation, range widened to 200 BPM | 0.38 / 0.44 | −1.2 (−3.7 to +1.4) | −5.3 (−8.1 to −2.2) |
| Springer's preparation, range widened to 200 BPM, with half-rate check | 0.38 / 0.44 | −6.2 (−8.4 to −3.7) | −9.7 (−11.9 to −7.1) |
| Springer's three loudness curves combined, with half-rate check | 0.63 / 0.69 | −7.4 (−9.4 to −5.1) | −8.8 (−10.9 to −6.3) |

*Whole-window variants against the method of the first part. Own recordings: 226 clean and 255 windows. Public recordings: 21 people, 21,956 windows with a reliable ECG rate (every fourth second), ranges are 95 % ranges over people. A negative change is an improvement.*

- **On Nico's recordings nothing beats the method of the first part.** On all 255 windows the mean error was 0.35 BPM for the method of the first part, 0.39 for forwards-and-backwards filtering, 0.44 for the widened Springer preparation with the half-rate check and 0.69 for the three combined loudness curves; differences of a tenth of a BPM cannot be told apart on five recordings. The Springer code as published fails there (19 BPM mean error), because two recordings are faster than its limit of 120 BPM.
- **On the public recordings, filtering forwards and backwards helps by 3.6 BPM, but hardly because it looks ahead.** Applying the same filter twice while recording, without any look-ahead, recovers nearly all of that gain (3.5 BPM). Compared directly on the same windows, the difference forwards-and-backwards minus twice-forwards was −0.07 BPM at rest level (a range that includes zero: −0.38 to +0.24) and −0.25 BPM at overload level (−0.49 to −0.02; paired check by one of the reviewers of this read on the stored results). So nearly all of the benefit is the steeper filter, and the small remainder gives little reason to store the sound for filtering alone.
- **The handling of the ends of the stored stretch does not matter**; cutting off the first and last quarter or half second makes the result worse, because it shortens the stretch.
- **Springer's preparation helps more, mainly with the half-rate check and only at higher heart rates.** Widening its search from 120 to 200 BPM reduced its own mean error by 8.3 BPM at rest level and by 9.7 BPM at overload level. Against the method of the first part, the widened version without the half-rate check is 1.2 BPM better at rest level (range for the difference −3.7 to +1.4, which includes zero) and 5.3 BPM better at overload level (−8.1 to −2.2). With the half-rate check added it improves the public result by 6 to 10 BPM, mostly above 110 BPM, where it removes many of the one-third errors described above; below 70 BPM it is 7 to 11 BPM worse at rest level and 4 to 10 BPM worse at overload level. Its logarithmic loudness curve is one likely ingredient: a quick extra test (run after the first results, at rest level only) of forwards-and-backwards filtering at 1,000 values per second gave −3.7 BPM on its own and −6.1 BPM with the logarithmic curve, so the curve added about 2.4 BPM there.
- **All of these gains are smaller than that of the improved choice of the peak** described above (about 15 BPM on the test half, without look-ahead). The two were not combined, and the two comparisons use different sets of people and windows (all 21 people and every fourth window here, the 10 test people and every window there), so the sizes can only be compared roughly.
- **Storing less is enough.** Reducing the stored stretch from 16,000 to 1,000 values per second before the analysis gives the same error and needs 73 kilobytes instead of about 1 MB (see the table below).

What it would cost on the device (an estimate with the same assumed costs per operation as in the first part, not a measurement; the extra time for reaching the external memory is unknown and not included):

| Variant | Time per update (ms) | Share of one processor core at one update per second (%) | Memory |
|---|---:|---:|---:|
| Method of the first part | 2.0 | 0.5 | 7 kB |
| Same filter applied twice while recording | 2.0 | 0.8 | 7 kB |
| Forwards and backwards, stored at 16,000 values per second | 49 | 4.9 | about 1 MB |
| Forwards and backwards, stored at 1,000 values per second | 5.0 | 0.6 | 73 kB |
| Logarithmic loudness curve, 1,000 values per second | 20 | 2.1 | 136 kB |
| Springer's preparation and heart rate | 37 | 3.8 | 254 kB (223 kB of it in the fast internal memory) |

*Estimated cost per variant on the ESP32-S3. By processor time, all would fit at one update per second; whether the larger variants also fit in memory is open (the internal memory is shared with the rest of the firmware, and the cost of using the slower external memory was not measured). The audio path keeps priority, and the work can be spread over many 4 ms blocks. If the counting may use a tenth of one core, the method of the first part could update about 48 times per second, forwards-and-backwards filtering at 1,000 values per second about 20 times, the logarithmic curve about 5 times and the other whole-window variants 2 to 3 times.*

::callout{kind="finding"}
**By the estimated processor time, counting in non-real time is possible on the device; whether the larger variants fit in memory beside the firmware is open.** **Filtering forwards and backwards brings almost no gain of its own:** a steeper filter gives nearly the same improvement while recording, at almost no cost. Springer's preparation with a search up to 200 BPM and the half-rate check helped more (6 to 10 BPM), but it was only tried with look-ahead, it is worse at slow heart rates, and it helps less than the improved choice of the peak. Whether its logarithmic loudness curve also works without look-ahead, and together with the improved choice, was not tested. The published Springer code cannot be copied into the firmware as it is: its 120 BPM limit does not fit the planned range of 30 to 200 BPM [1], and its files carry a licence (GNU General Public License, version 3 or later, according to the file headers) that would bind the firmware.
::end
