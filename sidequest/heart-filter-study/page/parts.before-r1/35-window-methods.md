### Does the heart rate have to be counted in real time?

No. The count uses the last 8 seconds, which sit in the device's memory. The counting path could therefore work on the whole stored stretch at once and look "ahead" inside it, which a filter that handles each value as it arrives cannot. Nico asked for this to be explored during this version (23 November 2026). Listening is not affected: the sound for the ear must stay in real time.

Two ideas were tried, on the same 8-second windows as before:

- **Filtering forwards and backwards.** Running a filter over the stored stretch once forwards and once backwards cancels the small delay that a filter gives to different pitches, and makes its edges twice as steep.
- **The method of Springer, Tarassenko and Clifford [20].** A widely used research method for marking the heart sounds. Its openly published program code [21] was read for this study (the article itself is not freely available and was not read; the code was not run). Before it marks anything, the code prepares the sound and estimates the heart rate: a filter from 25 to 400 Hz run forwards and backwards, removal of loud clicks, a loudness curve taken from the *logarithm* of the signal (which makes loud and soft beats more alike), and the same repeat-pattern search as here, but only between 0.5 and 2 seconds, so that it cannot report more than 120 BPM. Its second half, a statistical model that marks each heart sound, was not implemented: it needs trained values this study does not have.

::figure{src="page/figures/run2_window_methods_error.png" alt="Mean heart-rate error of fourteen counting variants on the own recordings and on the public recordings at two loudness levels" caption="Counting on the whole stored 8 seconds against the method of the first part (amber, dashed line), on Nico's recordings and on the public recordings with ECG (every fourth window; lines: 95 % ranges over people). Every variant here uses the half-rate check unless it says \"as published\"." width="wide"}

| Variant | Own recordings, clean / all windows (BPM) | Public with ECG, change against the first part's method (BPM, rest level) | The same at overload level |
|---|---:|---:|---:|
| Method of the first part: filter while recording, 40–150 Hz | 0.30 / 0.35 | 0 (mean error 26.9) | 0 (mean error 20.2) |
| Same filter, forwards and backwards over the stored stretch | 0.32 / 0.38 | −3.6 (−4.6 to −2.7) | −1.2 (−2.1 to −0.5) |
| Same filter applied twice while recording (no look-ahead) | 0.32 / 0.38 | −3.5 (−4.5 to −2.6) | −1.0 (−1.9 to −0.2) |
| Springer's preparation as published (limit 120 BPM) | 21.0 / 19.2 | worse (+7.1) | worse (+4.4) |
| Springer's preparation, range widened to 200 BPM, with half-rate check | 0.38 / 0.44 | −6.2 (−8.4 to −3.7) | −9.7 (−11.9 to −7.1) |
| Springer's three loudness curves combined, with half-rate check | 0.63 / 0.69 | −7.4 (−9.4 to −5.1) | −8.8 (−10.9 to −6.3) |

*Whole-window variants against the method of the first part. Own recordings: 226 clean and 255 windows. Public recordings: 21 people, 21,956 windows with a reliable ECG rate (every fourth second), ranges are 95 % ranges over people, corrected for the number of variants compared. A negative change is an improvement.*

- **On Nico's recordings nothing beats the method of the first part.** All sensible variants lie within about 0.1 BPM of each other, which these five recordings cannot tell apart. The Springer code as published fails there (19 BPM mean error), because two recordings are faster than its limit of 120 BPM.
- **On the public recordings, filtering forwards and backwards helps by 3.6 BPM, but not because it looks ahead.** Applying the same filter twice while recording, without any look-ahead, gives the same gain (3.5 BPM). The benefit is the steeper filter, not the cancelled delay.
- **The handling of the ends of the stored stretch does not matter**; cutting off the first and last quarter or half second makes the result worse, because it shortens the stretch.
- **Springer's logarithmic loudness curve is the most promising ingredient.** With the search widened to 200 BPM and the half-rate check added, it improves the public result by 6 to 10 BPM, mostly above 110 BPM, where it removes many of the one-third errors described above; below 70 BPM it is 7 to 11 BPM worse. A quick extra test of the logarithmic curve alone (run after the first results, at rest level only) gave −6.1 BPM.
- **Storing less is enough.** Reducing the stored stretch from 16,000 to 1,000 values per second before the analysis gives the same error and needs 31 kilobytes instead of 512.

What it would cost on the device (an estimate with the same assumed costs per operation as in the first part, not a measurement; the extra time for reaching the external memory is unknown and not included):

| Variant | Time per update (ms) | Share of one processor core at one update per second (%) | Memory |
|---|---:|---:|---:|
| Method of the first part | 2.0 | 0.5 | 7 kB |
| Same filter applied twice while recording | 2.0 | 0.8 | 7 kB |
| Forwards and backwards, stored at 16,000 values per second | 49 | 4.9 | about 1 MB |
| Forwards and backwards, stored at 1,000 values per second | 5.0 | 0.6 | 63 kB |
| Logarithmic loudness curve, 1,000 values per second | 20 | 2.1 | 136 kB |
| Springer's preparation and heart rate | 37 | 3.8 | 254 kB |

*Estimated cost per variant on the ESP32-S3. All would fit at one update per second; the audio path keeps priority, and the work can be spread over many 4 ms blocks.*

::callout{kind="finding"}
**Counting in non-real time is possible on the device but is not what brings the gain.** A steeper filter gives the same improvement while recording, at almost no cost. If more accuracy is wanted, the lead to follow is the logarithmic loudness curve with a search up to 200 BPM; whether it also works without look-ahead was not tested. The published Springer code cannot be copied into the firmware as it is: its 120 BPM limit does not fit the planned range of 30 to 200 BPM [1], and its files carry a licence (GNU General Public License, version 3 or later, according to the file headers) that would bind the firmware.
::end
