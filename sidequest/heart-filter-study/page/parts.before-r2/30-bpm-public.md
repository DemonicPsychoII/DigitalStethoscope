## Results: heart rate against an ECG (public recordings)

The public recordings with ECG [16] put the heart-rate method to a harder and fairer test: 22 people instead of one, about 29 hours instead of 5 minutes, heart rates from below 60 to about 200 BPM, and a reference that does not come from the sound. The ECG heart rate was computed by two different spike-finding methods; an 8-second window counts as reliable where both find the same beats and the beat spacing is plausible (87,807 of 103,927 windows, 22 people; one of them has no reliable window). The device simulation, the filters and the counting method are exactly those of the first part. Unless stated otherwise, numbers are for the rest level and for reliable windows, and the ranges in brackets are 95 % ranges obtained by re-drawing people, not windows, because the windows of one person are not independent.

### The reference of the first part holds up

First a check of the first part itself. Its reference came from the sound. Applied to 67 one-minute excerpts of the public recordings (17 people) and compared with the ECG:

- Where that method called a window clean (1,278 windows), it agreed with the ECG within 2 BPM in 99.7 % of them (mean difference 0.16 BPM, largest 11.2 BPM), at every heart rate up to above 170 BPM.
- Of 1,027 windows where it disagreed with the ECG, it had marked 1,024 as not clean.
- It is cautious: it also rejected 42.7 % of the windows in which it would have been right.

This supports trust in the clean windows of the first part; it does not replace an independent reference for Nico's own recordings, which still does not exist. What the first part could not show is how the device behaves on other people and during exercise.

::figure{src="page/figures/run2_sound_reference_vs_ecg.png" alt="Heart rate from the sound-derived reference against the ECG heart rate" caption="The sound-derived reference of the first part against the ECG, on 67 one-minute excerpts of the public recordings." width="wide"}

### At rest the method works; during exercise it often reports a third of the rate

| Situation (recommended 40–150 Hz filter) | People | Mean error, method of the first part (BPM) | Within tolerance (%) | Mean error, improved method (BPM) | Within tolerance (%) |
|---|---:|---:|---:|---:|---:|
| Sitting still | 9 | 2.7 | 91 | 3.7 | 90 |
| Lying down | 7 | 11.6 | 79 | 14.8 | 78 |
| Walking | 13 | 24.9 | 57 | 14.0 | 73 |
| Stress tests (treadmill, bicycle) | 12 | 38.7 | 47 | 14.9 | 74 |
| Steady pedalling | 7 | 20.9 | 74 | 4.7 | 93 |
| All together | 21 | 26.6 (22.3–30.7) | 61 | see below | |

*Heart rate from the sound against the ECG, by activity, rest level, all people. The improved method is explained below; its columns include the 11 people it was tuned on, so they flatter it somewhat. The test on the other people follows below.*

With the filter and counting method recommended in the first part, the device simulation is right most of the time (the middle error is 1.8 BPM), but in 37 % of the windows it is grossly wrong, which drives the mean error to 26.6 BPM. Sitting still, it meets the project's provisional acceptance target (mean error of at most 5 BPM with at least 90 % of windows valid; the project defines it for clean test signals [22]). Lying down, walking and above all in the stress tests it does not. The error grows with the heart rate: 7 BPM below 70 BPM, 26 BPM between 90 and 110, 52 BPM between 150 and 170.

Most gross errors are not random. In 14,054 windows the device reported **one third** of the true rate and in 7,259 one half. Of the remaining gross errors at least 2,300 are a quarter of the rate (counted in three activities); the others cluster at about one and a half and two and a half beat spacings and, lying down, at the upper end of the search (near 200 BPM).

::figure{src="page/figures/run2_bpm_estimate_vs_ecg.png" alt="Heart rate over 30 minutes of an exercise recording: ECG and device estimates" caption="One exercise recording over time. White: heart rate from the ECG. Dots: what the device simulation reported with the method of the first part, without a filter and with the recommended 40–150 Hz filter. Between minute 10 and 19 many estimates lie on a second line at exactly one third of the true rate." width="wide"}

### Why one third, and how to prevent it

::figure{src="page/figures/run2_bpm_one_third_explained.png" alt="Left: loudness curve of 8 seconds of heart sound at 146 BPM. Right: how alike the curve is to itself when shifted, with almost equal peaks at one, two, three and four beats" caption="Left: 8 seconds of the loudness curve of a clean, regular heart sound at 146 BPM. Right: the repeat-pattern search. A regular heartbeat matches itself equally well when shifted by one, two, three or four beats. The method of the first part took the highest peak, here the third (49 BPM)." width="wide"}

The cause was traced for this version (own analysis, three recordings of three people):

- The sound in these windows is clean. A regular heartbeat repeats just as well after two, three or four beats as after one, so the repeat-pattern search finds almost equally high peaks there (0.93, 0.92, 0.94 and 0.92 in the example).
- The method of the first part compares each shift fairly, which sounds right but removes the small natural advantage of the shortest shift. A peak that is a few percent higher then wins, and that is often the third. The half-rate check cannot repair this, because half of three beats is not a peak.
- It is not caused by the model of our device input: with the public sound merely converted to 16,000 values per second, the peak at three beats is still higher than the peak at one beat in 56 to 85 % of the affected windows.
- It can only happen above about 90 BPM, because three beats must fit into the 2 seconds that the search covers. That is why it grows with the heart rate. The stronger smoothing chosen in the first part makes it more likely.

Nico's five recordings also reach 149 BPM and showed no such error with the recommended filter (the 52 filters with a steep 60 Hz lower edge did show it, in one recording after exercise). Why the recommended filter was spared there was not examined; a possible reason is that their beats vary more from one to the next.

An **improved counting method** was then built, with two changes to the choice of the peak: longer shifts count slightly less (in proportion to how much of the 8 seconds still overlaps), and after finding the highest peak the method looks at a quarter, a third and half of that shift and takes the shortest one whose peak is at least 0.6 times as high. A wrong number is also shown less often as valid: the estimate must stand clear of rival peaks and agree within 10 % with one of the two previous estimates. The extra cost is below 1 % of the counting work and about 2 to 3 kilobytes of memory (estimate).

To keep this honest, the people were split in two halves before anything was tuned: all settings were chosen on 11 people and then tested once on the other 10.

| 40–150 Hz filter, test half (10 people, 42,899 windows) | Mean error (BPM) | Within tolerance (%) | Windows shown as valid (%) | Mean error of the windows shown (BPM) | Grossly wrong among the windows shown (%) |
|---|---:|---:|---:|---:|---:|
| Method of the first part, rest level | 28.4 (21.0–36.2) | 57.5 | 71.8 | 22.8 | 29.4 |
| Improved method, rest level | 13.1 (7.1–19.7) | 75.8 | 65.4 | 3.8 (2.0–6.7) | 5.8 |
| Method of the first part, overload level | 22.2 (16.5–27.6) | 69.0 | 75.2 | 19.4 | 24.9 |
| Improved method, overload level | 7.2 (4.5–10.1) | 87.7 | 70.3 | 2.9 (1.5–4.6) | 3.3 |

*The improved counting method on people it was not tuned on.*

- On the test half the improved method **halves the mean error** (by about 15 BPM at both loudness levels) and removes 80 % (rest level) and 92 % (overload level) of the one-third errors. Above 130 BPM the mean error falls from 38–78 BPM to 2–9 BPM.
- A grossly wrong number (more than 20 % off) is shown as valid in 6 % of the shown windows instead of 29 %; counting every number outside the tolerance, 7 % instead of 31 %. The price: 65 % of the windows are shown instead of 72 %.
- **It is worse at slow heart rates, which is where a stethoscope is mostly used.** On the test half: below 70 BPM 8.7 instead of 4.3 BPM, lying down 8.1 instead of 5.4 BPM, sitting still unchanged (3.7 against 3.8 BPM). Over all people: sitting still 3.7 instead of 2.7 BPM, lying down 14.8 instead of 11.6 BPM. At slow rates the rule sometimes prefers a shorter wrong shift. A rule that depends on the rate could repair this; it was not built.
- **On Nico's recordings the error does not change** with the recommended filter: 0.30 BPM on clean windows, 0.35 BPM on all, 255 of 255 within tolerance, as before. Fewer windows are shown as valid: 97.6 % instead of 99.6 %.
- The acceptance target is still met only when sitting still (and there only with the validity rule of the first part; the new rule shows 87 to 88 % of the windows). On the test half no exercise situation meets it with either method.

::figure{src="page/figures/run2_bpm_by_activity.png" alt="Mean error and share within tolerance by activity for the method of the first part and the improved method" caption="Heart rate from the sound against the ECG by activity, for the counting method of the first part and the improved method, recommended 40–150 Hz filter, rest level, all people, including the 11 on whom the improved method was tuned." width="wide"}

::figure{src="page/figures/run2_bpm_estimate_vs_ecg_improved.png" alt="The same exercise recording with the improved counting method" caption="The same exercise recording as above with the improved counting method. This person belongs to the half on which the method was tuned." width="wide"}

### What the public recordings say about the filter

::figure{src="page/figures/run2_bpm_lower_edge.png" alt="Mean heart-rate error against the lower edge of the filter, own recordings and public recordings" caption="Mean error against the lower edge of the filter (upper edge 150 Hz, gentle filter, counting method of the first part): Nico's recordings and the public recordings. Mind the different sizes of the errors." width="wide"}

| Lower edge (upper edge 150 Hz, gentle) | None | 10 Hz | 20 Hz | 25 Hz | 30 Hz | 40 Hz | 50 Hz | 60 Hz | 80 Hz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Own recordings, clean windows (BPM) | 0.42 | 0.35 | 0.30 | 0.30 | 0.30 | 0.30 | 0.31 | 0.31 | 0.30 |
| Own recordings, all windows (BPM) | 4.22 | 2.46 | 0.74 | 0.69 | 0.35 | 0.35 | 0.36 | 0.36 | 0.36 |
| Public with ECG, rest level (BPM) | 33.5 | 33.7 | 32.4 | 31.0 | 29.4 | 26.6 | 24.9 | 23.8 | 23.3 |
| Public with ECG, overload level (BPM) | 25.8 | 25.1 | 23.1 | 22.0 | 21.1 | 20.2 | 19.9 | 20.2 | 21.1 |

*Mean error against the lower edge, counting method of the first part. Own recordings: 226 clean and 255 windows. Public: 21 people, 87,807 windows.*

- **The direction of the first part's recommendation is confirmed, now with an independent reference.** The recommended 40–150 Hz filter is better than the planned 25–150 Hz filter by 4.4 BPM (3.3 to 5.5) at rest level and by 1.8 BPM (1.0 to 2.6) at overload level, and it is better than no filter by 6.9 BPM. No filter and a lower edge of 10 Hz are the worst choices (33.5 and 33.7 BPM). In the first part this step rested on a single window.
- **But 40 Hz is not the best lower edge on the public recordings.** At rest level the error keeps falling up to 80 Hz, and a steep filter from 60 to 150 Hz does best. That same steep 60 Hz filter was the worst in the first part, where it produced errors on clean windows of Nico's recordings. At overload level the curve is flat between 40 and 60 Hz.
- **With the improved counting method the order stays the same and the gaps shrink** (test half, rest level: no filter 16.8 BPM, 25–150 Hz 15.9, 40–150 Hz 13.1, 60–150 Hz 11.5).
- **On Nico's recordings the improved counting method removes the difference between 25 and 40 Hz.** With it, the planned 25–150 Hz filter has no gross error either (0.30 BPM on clean windows, 0.36 on all, against 0.30 and 0.35 for 40–150 Hz). The single window that separated the two in the first part was a product of the first part's counting method. What Nico's recordings still rule out is the steep 60–150 Hz filter (8 gross errors, 2.7 BPM on all windows, also with the improved method).
- **The ranking of the first part does not carry over** filter by filter (the two orders are unrelated on reliable windows). This was to be expected: in the first part almost all filters lay within 0.29 to 0.44 BPM of each other, which is no ranking at all.
- **Other filter designs and the upper edge.** Other designs with the same edges were 2 to 7 BPM worse than the planned gentle design (Butterworth 26.6 BPM; Bessel 28.5, Chebyshev 29.1, elliptic 29.1, the FIR candidate 34.0), and the upper edge made no difference (26.6 to 27.2 BPM for upper edges from 100 to 800 Hz, lower edge 40 Hz). The listening candidate 100–800 Hz was as good an input for counting as 40–150 Hz here (26.8 BPM); the first part's finding that it is a poor input came from the low-pitched disturbances in Nico's recordings, which the public recordings lack.
- **The counting method matters far more than the filter.** Changing the filter moves the public result by a few BPM; changing the choice of the peak moves it by 15 BPM. The order of the counting variants of the first part is even reversed here: the half-rate check alone (23.1 BPM) beats the first part's final method (26.6 BPM).

::callout{kind="finding"}
**Recommended BPM filter: still 40–150 Hz, gentle edges.** The evidence for it over the planned 25–150 Hz filter now comes from the public recordings (better by 4.4 BPM with the first part's counting method and by 2.8 BPM with the improved one on the test half, a difference of two means that was not tested on its own); on Nico's recordings the two are equal once the counting method is improved. The public recordings would favour a lower edge of 50 to 60 Hz, but a steep 60 Hz edge failed on Nico's recordings, the only ones made with our own chain, so 40 Hz remains the cautious choice, and 50 Hz is worth testing on the device. **The counting method of the first part has to be replaced:** it must not take the highest peak of a fairly compared repeat-pattern search. The improved method of this version is the new starting point; it still needs a repair for slow heart rates.
::end

::callout{kind="limitation"}
The public recordings were made with a sensor strapped to the chest of young men while they walked, ran and cycled; four in five windows are from exercise. A stethoscope is held on a patient at rest. The numbers during exercise therefore say more about the counting method's weak spots than about everyday use, and they come from another sensor passed through a model of our device input. The improved method was tuned on half of the same collection; it has not seen any other data except Nico's five recordings.
::end
