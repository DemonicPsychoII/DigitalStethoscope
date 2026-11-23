
## 5 Results

### 5.1 Heart rate

#### 5.1.1 Nico's recordings

**On clean signal, the counting method matters at least as much as the filter.** The first-draft method sometimes reported half the true rate, because a pattern that repeats every beat also repeats every second beat. The two changes of the original counting method together removed these mistakes on clean windows (Figure 8). For the planned 25–150 Hz gentle filter the mean error on clean windows fell from 0.70 BPM to 0.51 BPM with the half-rate check alone and to 0.30 BPM with both changes. Without a filter the changes do not help overall: "no filter" stays at 4.2 BPM over all windows, because the improvement on clean windows (1.32 to 0.42 BPM) is offset by larger errors in the 29 disturbed windows (26.7 to 33.8 BPM).

The two changes also pull in different directions for the planned filter. With the half-rate check alone, the 25–150 Hz gentle filter stayed within tolerance in all 255 windows (0.51 BPM on clean windows). Adding the slower smoothing improved clean windows to 0.30 BPM but produced the single window outside the tolerance that is discussed below. The 8 Hz variant gave 0.35 BPM on clean windows with all 255 windows within tolerance.

::figure{src="page/figures/bpm_estimator_vs_filter.png" alt="Bar chart of mean error for three filters with the first-draft and the original counting method" caption="Figure 8. Mean error of the heart rate on Nico's recordings for three filters, with the first-draft and the original counting method (labelled \"final\" in the figure)." width="wide"}

**On clean signal, almost all filters are equally good.** With the original counting method, on clean windows:

- 1,258 of 1,310 filters differ from the reference by **0.29 to 0.44 BPM** on average, with no gross error;
- the 52 exceptions all have a steep lower edge at 60 Hz. With them the method reports a third of the true rate in part of the third recording after exercise, probably because they cut away much of the low heart sound (the cause was not examined). Lower edges this high and steep should be avoided for counting;
- of the 150 best-ranked filters, 147 cannot be told apart statistically from the best one;
- the filter design, the steepness (below that limit) and the upper edge make no measurable difference on clean windows (Figure 9).

For comparison, the reference's own three methods differ from each other by 0.30 BPM on average on the clean windows (median 0.16 BPM, at most 1.79 BPM). The device's average difference from the reference is of the same size; its largest difference on a clean window with the 40–150 Hz gentle filter is 3.7 BPM, larger than the reference methods' largest disagreement. This shows agreement with this reference; the absolute accuracy of the device remains unknown.

::figure{src="page/figures/bpm_filter_families.png" alt="Dot plot of mean error per filter design" caption="Figure 9. Mean error for every tested filter on Nico's recordings, grouped by filter design. On clean windows the designs do not differ, apart from the filters with a steep lower edge at 60 Hz (the higher dots). With disturbed windows included, the FIR filters are as poor as no filter: the short FIR filters that fit the device's time budget cannot cut off sharply at such low pitches, so movement gets through." width="wide"}

**Disturbances separate the filters, and the lower edge decides** (Figure 10, Table 4).

::figure{src="page/figures/bpm_highpass_effect.png" alt="Mean heart-rate error against the lower and the upper band edge" caption="Figure 10. Mean error on Nico's recordings against the lower edge (left, upper edge fixed at 150 Hz) and the upper edge (right, lower edge fixed at 40 Hz), for the planned gentle filter type (Butterworth, 2nd-order edges). On clean windows nothing changes. With disturbed windows included, a lower edge below about 30 Hz lets disturbances through." width="wide"}

| Filter | Mean error, clean windows (BPM) | Mean error, all windows (BPM) | Within tolerance, all windows (%) | Gross errors, all windows | Multiplications per sound value |
|---|---:|---:|---:|---:|---:|
| No filter | 0.42 | 4.22 | 93.7 | 16 | 0 |
| 25–150 Hz gentle (planned BPM filter) | 0.30 | 0.69 | 99.6 | 1 | 10 |
| 30–150 Hz gentle | 0.30 | 0.35 | 100.0 | 0 | 10 |
| **40–150 Hz gentle (recommended BPM filter)** | **0.30** | **0.35** | **100.0** | **0** | **10** |
| 40–800 Hz gentle (planned listening filter) | 0.30 | 0.35 | 100.0 | 0 | 10 |
| 100–800 Hz gentle (first listening candidate) | 0.30 | 2.45 | 97.3 | 7 | 10 |
| 30–300 Hz elliptic, steep lower edge (best-ranked) | 0.29 | 0.35 | 100.0 | 0 | 15 |

*Table 4. Heart-rate results on Nico's recordings with the original counting method. Clean windows: 226; all windows: 255.*

- **No filter** fails during movement and at an unsteady start: 16 gross errors, mean error 4.2 BPM over all windows.
- The **planned 25–150 Hz gentle** filter has one gross error (0.69 BPM over all windows): at the unsteady start of the first recording after exercise it reports 43 BPM where the reference, itself uncertain there, says 128 BPM. During the movement in the first resting recording it does as well as the 40 Hz filter.
- For this gentle filter type with the upper edge at 150 Hz, lower edges from **30 Hz to 80 Hz** have no gross error and 0.35 to 0.36 BPM over all windows.
- This does not hold for every filter. In disturbed windows some other designs with a 30 Hz lower edge, very gentle (1st-order) lower edges, and some combinations with a high lower edge and a wide band do show gross errors. The statement that design and upper edge make no difference is true for clean windows only.
- A listening filter with a high lower edge and a wide band is a poor input for counting: 100–800 Hz gentle gives 7 gross errors over all windows (2.45 BPM). The design rule that counting always uses its own filter [1] is therefore right.

Figure 11 shows the heart rate over time, Table 5 the results per recording.

::figure{src="page/figures/bpm_tracks.png" alt="Heart rate over time for five recordings: reference and device estimates" caption="Figure 11. Heart rate over time on Nico's recordings, simulated. Each point is the estimate from the previous 8 seconds. Hollow reference points mark disturbed windows." width="wide"}

| Filter | Recording | Mean error, clean windows (BPM) | Mean error, all windows (BPM) | Largest single error (BPM) | Clean windows | All windows |
|---|---:|---:|---:|---:|---:|---:|
| 40–150 Hz gentle | Resting 1 | 0.48 | 0.59 | 3.71 | 42 | 51 |
| 40–150 Hz gentle | Resting 2 | 0.12 | 0.12 | 0.47 | 43 | 51 |
| 40–150 Hz gentle | After exercise 1 | 0.32 | 0.46 | 2.83 | 39 | 51 |
| 40–150 Hz gentle | After exercise 2 | 0.39 | 0.39 | 0.98 | 51 | 51 |
| 40–150 Hz gentle | After exercise 3 | 0.20 | 0.20 | 0.66 | 51 | 51 |
| 25–150 Hz gentle | Resting 1 | 0.47 | 0.53 | 3.99 | 42 | 51 |
| 25–150 Hz gentle | Resting 2 | 0.14 | 0.14 | 0.50 | 43 | 51 |
| 25–150 Hz gentle | After exercise 1 | 0.34 | 2.24 | 85.22 | 39 | 51 |
| 25–150 Hz gentle | After exercise 2 | 0.35 | 0.35 | 0.87 | 51 | 51 |
| 25–150 Hz gentle | After exercise 3 | 0.20 | 0.20 | 0.66 | 51 | 51 |

*Table 5. Per recording, original counting method.*

::callout{kind="finding"}
**On Nico's recordings alone, 40–150 Hz gentle is a precaution, not a proven improvement.** With the original counting method, 30 Hz is the first lower edge of this filter type without a gross error, and 40 Hz keeps some distance from that limit. With a less strongly smoothed loudness curve the planned 25 Hz edge showed no such error either, so the filter and the counting method have to be fixed together. On clean windows no other design or upper edge did better, so the planned structure (Butterworth, 2nd-order edges) and the planned 150 Hz stay.
::end

::callout{kind="limitation"}
The difference between 25 Hz and 40 Hz rests on a single 8-second window at the start of one recording, where the reference itself is uncertain. This error at 25 Hz occurred with the original counting method (and with its slower smoothing alone); it disappeared with the half-rate check alone and with the 8 Hz variant. The first-draft method had one gross error at 25 Hz and none at 40 Hz, in a different window. The two disturbances that cause gross errors (that start and a movement in one resting recording) explain why no filter and lower edges of 10 to 20 Hz do worse; they do not prove that 40 Hz is better than 25 Hz.

The rule that should mark bad windows as invalid is not validated: with the 40–150 Hz gentle filter it was never triggered on clean windows but rejected one window during the movement whose estimate was only 0.3 BPM off, and with no filter it flagged 5 of the 16 gross errors and missed all 8 during the movement. For the filters that first reduce the data rate, the share of invalid windows in the result files is wrong because of an error in how overloaded values were counted (31 windows wrongly marked invalid); the error is corrected in the code (Appendix B), the tables of this section were not recomputed, and their mean errors are not affected.
::end

#### 5.1.2 The sound-derived reference, checked against an ECG

The reference for Nico's recordings came from the sound (Section 4.5). Applied to 67 one-minute excerpts of the ECG collection (17 people) and compared with the ECG (Figure 12):

- Where that method called a window clean (1,278 windows), it agreed with the ECG within 2 BPM in 99.7 % of them (mean difference 0.16 BPM, largest 11.2 BPM), at every heart rate up to above 170 BPM.
- Of 1,027 windows where it disagreed with the ECG, it had marked 1,024 as not clean.
- It is cautious: it also rejected 42.7 % of the windows in which it would have been right.

This supports trust in the clean windows of Nico's recordings; it does not replace an independent reference for them, which still does not exist.

::figure{src="page/figures/run2_sound_reference_vs_ecg.png" alt="Heart rate from the sound-derived reference against the ECG heart rate" caption="Figure 12. The sound-derived reference against the ECG, on 67 one-minute excerpts of the ECG collection." width="wide"}

#### 5.1.3 ECG collection: the original counting method fails during exercise

The ECG collection puts the counting to a harder and fairer test: 22 people instead of one, about 29 hours instead of 5 minutes, heart rates from below 60 to about 200 BPM, and a reference that does not come from the sound. The device simulation, the filters and the counting method are exactly those used on Nico's recordings.

| Situation (40–150 Hz gentle filter) | People | Mean error, original method (BPM) | Within tolerance (%) | Mean error, improved method (BPM) | Within tolerance (%) |
|---|---:|---:|---:|---:|---:|
| Sitting still | 9 | 2.7 | 91 | 3.7 | 90 |
| Lying down | 7 | 11.6 | 79 | 14.8 | 78 |
| Walking | 13 | 24.9 | 57 | 14.0 | 73 |
| Stress tests (treadmill, bicycle) | 12 | 38.7 | 47 | 14.9 | 74 |
| Steady pedalling | 7 | 20.9 | 74 | 4.7 | 93 |
| All together | 21 | 26.6 (22.3–30.7) | 61 | see Table 7 | |

*Table 6. Heart rate from the sound against the ECG, by activity, rest level, all people. The columns of the improved method include the 11 people it was tuned on, so they flatter it somewhat; Table 7 gives the test on the other people.*

With the 40–150 Hz gentle filter and the original counting method, the device simulation is right most of the time (the middle error is 1.8 BPM), but in 37 % of the windows it is grossly wrong, which drives the mean error to 26.6 BPM (Table 6). Sitting still, it meets the project's provisional acceptance target. Lying down, walking and above all in the stress tests it does not. The error grows with the heart rate: 7 BPM below 70 BPM, 26 BPM between 90 and 110, 52 BPM between 150 and 170.

Most gross errors are not random. In 14,054 windows the device reported **one third** of the true rate and in 7,259 one half (Figure 13). Of the remaining gross errors at least 2,300 are a quarter of the rate (counted in three activities); the others cluster at about one and a half and two and a half beat spacings and, lying down, at the upper end of the search (near 200 BPM).

::figure{src="page/figures/run2_bpm_estimate_vs_ecg.png" alt="Heart rate over 30 minutes of an exercise recording: ECG and device estimates" caption="Figure 13. One exercise recording over time. White: heart rate from the ECG. Dots: what the device simulation reported with the original counting method, without a filter and with the 40–150 Hz gentle filter. Between minute 10 and 19 many estimates lie on a second line at exactly one third of the true rate." width="wide"}

The cause was traced (own analysis, three recordings of three people; Figure 14):

- The sound in these windows is clean. A regular heartbeat repeats just as well after two, three or four beats as after one, so the repeat-pattern search finds almost equally high peaks there (0.93, 0.92, 0.94 and 0.92 in the example).
- The original method compares each shift fairly, which sounds right but removes the small natural advantage of the shortest shift. A peak that is a few percent higher then wins, and that is often the third. The half-rate check cannot repair this, because half of three beats is not a peak.
- It is not caused by the model of our device input: with the public sound merely converted to 16,000 values per second, the peak at three beats is still higher than the peak at one beat in 56 to 85 % of the affected windows.
- It can only happen above about 90 BPM, because three beats must fit into the 2 seconds that the search covers. That is why it grows with the heart rate. The stronger smoothing of the original method makes it more likely.

::figure{src="page/figures/run2_bpm_one_third_explained.png" alt="Left: loudness curve of 8 seconds of heart sound at 146 BPM. Right: how alike the curve is to itself when shifted, with almost equal peaks at one, two, three and four beats" caption="Figure 14. Left: 8 seconds of the loudness curve of a clean, regular heart sound at 146 BPM. Right: the repeat-pattern search. A regular heartbeat matches itself equally well when shifted by one, two, three or four beats. The original counting method took the highest peak, here the third (49 BPM)." width="wide"}

Nico's five recordings also reach 149 BPM and showed no such error with the 40–150 Hz gentle filter (the 52 filters with a steep 60 Hz lower edge did show it, in one recording after exercise). Why this filter was spared there was not examined; a possible reason is that their beats vary more from one to the next.

#### 5.1.4 The improved counting method

Table 7 gives the result of the improved counting method (Section 4.4) on the 10 people it was not tuned on.

| 40–150 Hz gentle filter, test half (10 people, 42,899 windows) | Mean error (BPM) | Within tolerance (%) | Windows shown as valid (%) | Mean error of the windows shown (BPM) | Grossly wrong among the windows shown (%) |
|---|---:|---:|---:|---:|---:|
| Original method, rest level | 28.4 (21.0–36.2) | 57.5 | 71.8 | 22.8 | 29.4 |
| Improved method, rest level | 13.1 (7.1–19.7) | 75.8 | 65.4 | 3.8 (2.0–6.7) | 5.8 |
| Original method, overload level | 22.2 (16.5–27.6) | 69.0 | 75.2 | 19.4 | 24.9 |
| Improved method, overload level | 7.2 (4.5–10.1) | 87.7 | 70.3 | 2.9 (1.5–4.6) | 3.3 |

*Table 7. The improved counting method on people it was not tuned on.*

- On the test half the improved method **halves the mean error** (by about 15 BPM at both loudness levels) and removes 80 % (rest level) and 92 % (overload level) of the one-third errors. Above 130 BPM the mean error falls from 38–78 BPM to 2–9 BPM.
- A grossly wrong number is shown as valid in 6 % of the shown windows instead of 29 %; counting every number outside the tolerance, 7 % instead of 31 %. The price: 65 % of the windows are shown instead of 72 %.
- **It is worse at slow heart rates, which is where a stethoscope is mostly used.** On the test half: below 70 BPM 8.7 instead of 4.3 BPM, lying down 8.1 instead of 5.4 BPM, sitting still unchanged (3.7 against 3.8 BPM). Over all people (Table 6, Figure 15): sitting still 3.7 instead of 2.7 BPM, lying down 14.8 instead of 11.6 BPM. At slow rates the rule sometimes prefers a shorter wrong shift. A rule that depends on the rate could repair this; it was not built.
- **On Nico's recordings the error does not change** with the 40–150 Hz gentle filter: 0.30 BPM on clean windows, 0.35 BPM on all, 255 of 255 within tolerance, as with the original method. Fewer windows are shown as valid: 97.6 % instead of 99.6 %.
- The acceptance target is still met only when sitting still (and there only with the validity rule of the original method; the new rule shows 87 to 88 % of the windows on the test half). On the test half no exercise situation meets it with either method.

Figure 16 shows the same exercise recording as Figure 13 with the improved counting method.

::figure{src="page/figures/run2_bpm_by_activity.png" alt="Mean error and share within tolerance by activity for the original and the improved counting method" caption="Figure 15. Heart rate from the sound against the ECG by activity, for the original and the improved counting method, 40–150 Hz gentle filter, rest level, all people, including the 11 on whom the improved method was tuned." width="wide"}

::figure{src="page/figures/run2_bpm_estimate_vs_ecg_improved.png" alt="The same exercise recording with the improved counting method" caption="Figure 16. The same exercise recording as in Figure 13 with the improved counting method. This person belongs to the half on which the method was tuned." width="wide"}

#### 5.1.5 What the ECG collection says about the filter

::figure{src="page/figures/run2_bpm_lower_edge.png" alt="Mean heart-rate error against the lower edge of the filter, Nico's recordings and the ECG collection" caption="Figure 17. Mean error against the lower edge of the filter (upper edge 150 Hz, gentle filter, original counting method): Nico's recordings and the ECG collection. Mind the different sizes of the errors." width="wide"}

| Lower edge (upper edge 150 Hz, gentle) | None | 10 Hz | 20 Hz | 25 Hz | 30 Hz | 40 Hz | 50 Hz | 60 Hz | 80 Hz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nico's recordings, clean windows (BPM) | 0.42 | 0.35 | 0.30 | 0.30 | 0.30 | 0.30 | 0.31 | 0.31 | 0.30 |
| Nico's recordings, all windows (BPM) | 4.22 | 2.46 | 0.74 | 0.69 | 0.35 | 0.35 | 0.36 | 0.36 | 0.36 |
| ECG collection, rest level (BPM) | 33.5 | 33.7 | 32.4 | 31.0 | 29.4 | 26.6 | 24.9 | 23.8 | 23.3 |
| ECG collection, overload level (BPM) | 25.8 | 25.1 | 23.1 | 22.0 | 21.1 | 20.2 | 19.9 | 20.2 | 21.1 |

*Table 8. Mean error against the lower edge, original counting method. Nico's recordings: 226 clean and 255 windows. ECG collection: 21 people, 87,807 windows.*

- **The direction of the recommendation from Nico's recordings (40 Hz better than 25 Hz) is confirmed, now with an independent reference, for the original counting method** (Figure 17, Table 8). The 40–150 Hz gentle filter is better than the planned 25–150 Hz gentle filter by 4.4 BPM (3.3 to 5.5) at rest level and by 1.8 BPM (1.0 to 2.6) at overload level, and it is better than no filter by 6.9 BPM. Of the lower edges in Table 8, no filter and 10 Hz are the worst (33.5 and 33.7 BPM). On Nico's recordings this step rested on a single window.
- **But 40 Hz is not the best lower edge on the ECG collection.** At rest level the error keeps falling up to 80 Hz, and a steep filter from 60 to 150 Hz does best. That same steep 60 Hz filter was the worst on Nico's recordings, where it produced errors on clean windows. At overload level the curve is flat between 40 and 60 Hz.
- **With the improved counting method the order stays the same and the gaps shrink** (test half, rest level: no filter 16.8 BPM, 25–150 Hz 15.9, 40–150 Hz 13.1, 60–150 Hz 11.5).
- **On Nico's recordings the improved counting method removes the difference between 25 and 40 Hz.** With it, the planned 25–150 Hz gentle filter has no gross error either (0.30 BPM on clean windows, 0.36 on all, against 0.30 and 0.35 for 40–150 Hz). The single window that separated the two was a product of the original counting method. What Nico's recordings still speak against is the steep 60–150 Hz filter (with the improved method still 8 gross errors and 2.7 BPM on all windows; all 8 lie in the disturbed windows, on clean windows it reaches 0.32 BPM).
- **The ranking on Nico's recordings does not carry over** filter by filter (the two orders are unrelated on reliable windows). This was to be expected: on Nico's recordings almost all filters lay within 0.29 to 0.44 BPM of each other, which is no ranking at all.
- **Other filter designs and the upper edge.** Other designs with the same edges were 2 to 7 BPM worse than the planned gentle design (Butterworth 26.6 BPM; Bessel 28.5, Chebyshev 29.1, elliptic 29.1, the FIR candidate 34.0), and the upper edge had a small effect (lower edge 40 Hz: compared with 150 Hz, an upper edge of 100 Hz raised the mean error by 0.6 BPM at rest level, and an upper edge of 800 Hz raised it by 1.1 BPM at overload level). At rest level the 100–800 Hz gentle filter was as good an input for counting as 40–150 Hz (26.8 BPM); at the overload level it was 6.1 BPM worse (26.3 against 20.2 BPM, range 3.8 to 8.4). That it is a poor input on Nico's recordings came from their low-pitched disturbances, which the ECG collection lacks; the overload level shows that the ECG collection does not clear it as an input for counting either.
- **The counting method matters far more than the filter.** Changing the filter moves the result on the ECG collection by a few BPM; changing the choice of the peak moves it by 15 BPM. The order of the counting variants is even reversed here: the half-rate check alone (23.1 BPM) beats the original method (26.6 BPM).

::callout{kind="finding"}
**Recommended BPM filter: 40–150 Hz gentle.** The evidence for it over the planned 25–150 Hz gentle filter comes from the ECG collection (better by 4.4 BPM with the original counting method and by 2.8 BPM with the improved one on the test half, a difference of two means that was not tested on its own); on Nico's recordings the two are equal once the counting method is improved. The ECG collection would favour a lower edge of 50 to 60 Hz, but a steep 60 Hz edge failed on Nico's recordings, the only ones made with our own chain, so 40 Hz remains the cautious choice, and 50 Hz is worth testing on the device. **The original counting method has to be replaced:** it must not take the highest peak of a fairly compared repeat-pattern search. The improved method is the new starting point; it still needs a repair for slow heart rates.
::end

::callout{kind="limitation"}
The ECG collection was recorded with a sensor strapped to the chest of young men while they walked, ran and cycled; four in five windows are from exercise. A stethoscope is held on a patient at rest. The numbers during exercise therefore say more about the counting method's weak spots than about everyday use, and they come from another sensor passed through a model of our device input. The improved method was tuned on half of the same collection; it has not seen any other data except Nico's five recordings.
::end
