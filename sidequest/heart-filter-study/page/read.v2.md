---
title: Which filters should the digital stethoscope use?
subtitle: A first simulation with five own heart recordings, for listening and for counting the heart rate (TICKET-189)
date: 23 November 2026
status: First simulation, listening judgement pending
watermark: Published by Claude-Fable-5.2 on behalf of Nico running in T3 Code through Claude Code.
---

::summary
**Heart rate.** Once the counting method is improved in two small ways (a smoother loudness curve and a check against reporting half the true rate), the choice of filter hardly matters on undisturbed signal: almost every filter differs from our reference by 0.3 to 0.4 beats per minute (BPM) on average. That is about as much as the reference's own three methods differ from each other (0.3 BPM on average, 1.8 BPM at most); the true accuracy is unknown. Apart from one group of unsuitable filters (a steep lower edge at 60 Hz), filters differ only where the signal is disturbed or the reference is uncertain. Recommended as a precaution: keep the planned simple filter but raise its lower edge from 25 Hz to **40 Hz (40–150 Hz)**. With it, no estimate in any of the 255 tested 8-second windows was outside the tolerance; without a filter 16 were grossly wrong. The step from 25 to 40 Hz rests on a single window.

**Listening.** The planned listening filter (40–800 Hz) cannot be made louder: it has no room left before the output overloads. Raising the lower edge to 100 Hz frees room to make the sound almost twice as large (a boost of just under **6 dB**; dB is explained in the listening results), at the price of a thinner sound and relatively more sound between the beats. Which of these is "loudest without distortion and without too much other sound" is a judgement by ear. Eight candidates are prepared below to listen to; that judgement is still open.

**How far this carries.** One person, five one-minute recordings, one session, no independent heart-rate sensor. The results choose a starting point; they do not prove accuracy.
::end

## The question

The stethoscope picks up heart sounds with a microphone, processes them in a small computer (an ESP32-S3) and plays them into the earpieces. It also counts the heart rate. Two filters are still open in the design (parameter P08 [1]):

- the **listening filter** for the switch position "Murmur" (next to "Raw", which plays the microphone signal unchanged), and
- the **BPM filter**, which prepares the signal for counting the heart rate and can also be listened to in the switch position "BPM".

::term{name="filter"}
A filter lets one range of pitches through and weakens the rest. Pitch is measured in hertz (Hz): the number of vibrations per second. A filter described as "40–800 Hz" keeps sound between 40 and 800 vibrations per second. The lower limit is called the lower edge, the upper limit the upper edge. 1 kHz (kilohertz) is 1,000 Hz.
::end

Nico set the goals on 23 November 2026 (project decisions):

1. Listening: the loudest result that is not distorted and does not carry too much other sound, judged by ear.
2. Heart rate: the filter that gives the most accurate count on the device, using the last 8 seconds of signal, updated once per second.
3. Try all filter variants worth trying, as close to the real device as possible.

## What was recorded

Five recordings of 60 seconds each were made on Nico's chest on 23 November 2026 (two chest positions) through the real chest-piece (membrane side), tube and microphone (INMP441 [2]), with the capture firmware of the chain measurement, which stores the raw microphone signal (own measurement [12]; 16,000 values per second, each stored as a 24-bit number, which allows about 16.8 million steps; the firmware revision is not stored in the recording files). The first 2 seconds of each recording contain the start-up of the microphone and were discarded.

| Recording | State | Heart rate range over 8-second windows (BPM) | Values at full scale | Energy below 20 Hz (%) | Clean windows of 51 |
|---|---:|---:|---:|---:|---:|
| Resting 1 | resting | 73–82 | 26 | 60.2 | 42 |
| Resting 2 | resting | 79–87 | 0 | 51.7 | 43 |
| After exercise 1 | after exercise | 86–129 | 16 | 48.6 | 39 |
| After exercise 2 | after exercise, overload on many beats | 119–144 | 473 | 32.0 | 51 |
| After exercise 3 | after exercise, overload in the first half | 116–149 | 457 | 38.2 | 51 |

*The five recordings. "Values at full scale" counts values at either limit of the number range of the microphone path. "Clean windows" are 8-second windows in which the reference heart rate is trustworthy (see below).*

::figure{src="page/figures/recordings_overview.png" alt="Five recordings over 60 seconds with their loudness and reference heart rate" caption="The five recordings. After exercise the heart beats so strongly that the signal reaches the limit of the number range of the microphone path (full scale) on many beats. The heart-rate line follows the rate beat to beat, so it moves more than the 8-second ranges in the table." width="wide"}

::term{name="full scale and overload"}
A digital device stores each sound value as a number within a fixed range. Its limits, upward and downward, are called full scale. A sound that would need a number outside this range is cut off flat at the limit. This is overload (also called clipping), and it is heard as distortion.
::end

::figure{src="page/figures/beat_closeup.png" alt="Close-up of heart beats at rest and after exercise, with values cut off at the lower limit" caption="A heartbeat is heard as two sounds, a first and a second one (visible in these recordings as two bursts per beat). After exercise (right) some beats reach full scale (here at the lower limit) and are cut off there: the microphone path itself is overloaded, before any filter. No filter can repair this." width="wide"}

::callout{kind="finding"}
After exercise the real chain of chest-piece, tube and microphone overloads on about one beat in three (42 of 129 and 45 of 127 beats; 473 and 457 values at full scale in the two overloaded recordings; in the third recording after exercise only during the first 30 seconds). The device will see the same. Between 32 % and 60 % of the recorded energy lies below 20 Hz, the lowest pitch for which the standard hearing curves are defined [3]. This very low part uses up the number range.
::end

::figure{src="page/figures/where_the_energy_is.png" alt="Spectrum of the five recordings from 5 Hz to 8 kHz" caption="Where the energy of the recordings sits. Most of it is at very low pitch; above about 1 kHz almost nothing is left." width="wide"}

## How the device was simulated

The simulation follows the firmware and the design documents step by step [1][4]: the same 16,000 values per second, the same blocks of 64 values (4 thousandths of a second, written 4 ms), the same order of steps at full volume, and the firmware's own volume and output-limit code [5], copied so that it produces the same numbers bit for bit. All results on this page use full volume (100 %). At lower volume settings the simulation limits the signal before the volume step, while the design does so after it; this does not affect any number here.

::figure{src="page/figures/signal_chain.png" alt="Block diagram of the listening path and the heart-rate path" caption="The two paths in the device, as designed. The heart-rate path always uses the BPM filter and takes its signal before the volume control, whatever the listener selects [1]." width="wide"}

Where the firmware is not written yet (the filter and the heart-rate code are still empty), the simulation uses what the device would realistically use. These are choices of this study, not measurements on the device:

- Filters are computed with numbers with a decimal point, stored in 32 bits (a choice of this study for the device; the firmware's filter is not written yet), in small standard building blocks. How sharply a filter cuts off at its edges is called its order: a 2nd-order edge is gentle, a 4th-order edge is steep. A filter with two gentle edges needs 10 multiplications per sound value.
- The heart-rate method follows the draft in the system design [1]: filter, turn the signal into a slow loudness curve (100 values per second), keep the last 8 seconds (800 values, 3.2 kilobytes), and once per second search this curve for its repeat pattern.

::term{name="repeat pattern search (autocorrelation)"}
The loudness curve is compared with a shifted copy of itself. If shifting by 0.75 seconds makes the two copies match best, the heart beats every 0.75 seconds, which is 80 beats per minute. The method uses the whole 8 seconds, not single beats.
::end

The method only uses the past (the device cannot look ahead). Its cost was estimated, not measured: about half a percent of one processor core and about 8 kilobytes of memory. The filter part of this estimate uses the published speed of the processor's filter routine [6]; the larger part (loudness curve and pattern search) uses assumed costs per operation without a source. A measurement on the device is still needed.

## What the heart rate was compared with

::callout{kind="limitation"}
There was no independent heart-rate sensor: no ECG, watch or pulse oximeter. The reference was derived from the recordings themselves. It is weaker than an ECG.
::end

The reference was computed afterwards, with methods that may look at the whole recording at once, which the device cannot. Three different methods marked every heartbeat: one follows the loudness peaks, one follows changes in the sound's pitch content, one searches for the average beat shape. A beat counts as certain if at least two methods agree within 0.06 seconds; five beats are marked as uncertain, two of them kept from a single method to fill a gap. For each 8-second window the reference rate is the average rate of the whole beats inside it.

- 226 of 255 windows are called **clean windows**: they contain no detected disturbance, no uncertain or missing beat, and the three methods differ by no more than 3 BPM. In these windows the methods actually differ by at most 1.8 BPM. This is a measure of how well the methods agree, not a proof of accuracy.
- The other 29 windows are **windows with an uncertain reference**. 25 of them contain a detected disturbance (a movement, a rubbing noise or the unsteady start of a recording); 4 contain no detected disturbance but one uncertain beat near the end of a recording. They are kept and reported separately ("all windows" below means all 255), because a real examination has such moments too. Errors there are differences from an uncertain value. For short, the text calls them disturbed windows.
- A check on the average beat shape shows two sounds per cycle in every recording, so the reference did not count half or double the rate.

The reference has three weaknesses beyond the missing sensor. All three methods listen to the same sound: a beat that cannot be heard, or a noise that sounds like a beat, can mislead all three together, and the third method learns its beat shape from beats the first two agree on. The beat marks are placed using the 25–150 Hz range, the same range as the planned BPM filter, so the reference is not fully independent of the filters being tested. And disturbances are detected partly by strong energy between 3 and 20 Hz, with limits set by looking at these five recordings, so it is partly built in that filters letting those low pitches through do worse in disturbed windows.

## Results: heart rate

The project requires the result of each heart session of at least 15 seconds to be within ±5 BPM or ±10 % of a reference device (requirement REQ-06 [7]). This study borrows that tolerance for single 8-second windows and reads it as "whichever is larger"; that reading is this study's. The same numbers are reported for the standard for ECG heart-rate meters, ANSI/AAMI EC13, which does not apply to stethoscopes and is cited from the project's source register without inspection of the full text [8]. "Mean error" always means the average size of the difference from the reference, so that too-high and too-low values cannot cancel. A "gross error" means more than 20 % off, for example half or a third of the true rate, or a rate far too high during a movement.

### On clean signal, the counting method matters at least as much as the filter

The first draft of the method simply took the strongest repeat pattern. It sometimes reported half the true rate, because a pattern that repeats every beat also repeats every second beat. Two changes together removed these mistakes on clean windows: a smoother loudness curve (smoothed twice, slower than before), and a check (if there is a nearly equally strong pattern at half the spacing, take that). For the planned 25–150 Hz filter the mean error on clean windows fell from 0.70 BPM to 0.51 BPM with the check alone and to 0.30 BPM with both. Without a filter the changes do not help overall: "no filter" stays at 4.2 BPM over all windows, because the improvement on clean windows (1.32 to 0.42 BPM) is offset by larger errors in the 29 other windows (26.7 to 33.8 BPM).

The two changes also pull in different directions for the planned filter. With the half-rate check alone, the planned 25–150 Hz filter stayed within the tolerance in all 255 windows (0.51 BPM on clean windows). Adding the slower smoothing improved clean windows to 0.30 BPM but produced the single window outside the tolerance that is discussed below. An in-between smoothing (two steps at 8 Hz) gave 0.35 BPM on clean windows with all 255 windows inside the tolerance.

::figure{src="page/figures/bpm_estimator_vs_filter.png" alt="Bar chart of mean error for three filters with the first-draft and the final counting method" caption="Mean error of the heart rate for three filters, with the first-draft and the final counting method." width="wide"}

### On clean signal, almost all filters are equally good

About 1,300 filters were tried: five classic filter designs (Butterworth, Bessel, two kinds of Chebyshev, elliptic), a different kind of filter that works on a fixed number of past values (called FIR) and a version that first reduces the data rate; gentle to steep edges; lower edges from none to 100 Hz; upper edges from 60 Hz to none. With the final counting method, on clean windows:

- 1,258 of 1,310 filters differ from the reference by **0.29 to 0.44 BPM** on average, with no gross error;
- the 52 exceptions all have a steep (4th-order) lower edge at 60 Hz. With them the method reports a third of the true rate in part of the third recording after exercise, probably because they cut away much of the low heart sound (the cause was not examined). Lower edges this high and steep should be avoided for counting;
- of the 150 best-ranked filters (all with the final counting method), 147 cannot be told apart statistically from the best one;
- the filter design, the steepness (below that limit) and the upper edge make no measurable difference on clean windows.

For comparison, the reference's own three methods differ from each other by 0.30 BPM on average on the clean windows (median 0.16 BPM, at most 1.79 BPM). The device's average difference from the reference is of the same size; its largest difference on a clean window with the recommended filter is 3.7 BPM, larger than the reference methods' largest disagreement. This shows agreement with this reference; the absolute accuracy of the device remains unknown.

::figure{src="page/figures/bpm_filter_families.png" alt="Dot plot of mean error per filter design" caption="Mean error for every tested filter, grouped by filter design. On clean windows the designs do not differ, apart from the filters with a steep lower edge at 60 Hz (the higher dots). With disturbed windows included, the FIR filters are as poor as no filter: the short FIR filters that fit the device's time budget cannot cut off sharply at such low pitches, so movement gets through." width="wide"}

### Disturbances separate the filters, and the lower edge decides

::figure{src="page/figures/bpm_highpass_effect.png" alt="Mean heart-rate error against the lower and the upper band edge" caption="Mean error against the lower edge (left, upper edge fixed at 150 Hz) and the upper edge (right, lower edge fixed at 40 Hz), for the planned gentle filter type (Butterworth, 2nd-order edges). On clean windows nothing changes. With disturbed windows included, a lower edge below about 30 Hz lets disturbances through." width="wide"}

| Filter | Mean error, clean windows (BPM) | Mean error, all windows (BPM) | Within tolerance, all windows (%) | Gross errors, all windows | Multiplications per sound value |
|---|---:|---:|---:|---:|---:|
| No filter (Raw) | 0.42 | 4.22 | 93.7 | 16 | 0 |
| 25–150 Hz gentle (design candidate BPM) | 0.30 | 0.69 | 99.6 | 1 | 10 |
| 30–150 Hz gentle | 0.30 | 0.35 | 100.0 | 0 | 10 |
| **40–150 Hz gentle (recommended)** | **0.30** | **0.35** | **100.0** | **0** | **10** |
| 40–800 Hz gentle (design candidate Murmur) | 0.30 | 0.35 | 100.0 | 0 | 10 |
| 100–800 Hz gentle (louder listening candidate) | 0.30 | 2.45 | 97.3 | 7 | 10 |
| 30–300 Hz elliptic, steep lower edge (best-ranked) | 0.29 | 0.35 | 100.0 | 0 | 15 |

*Heart-rate results with the final counting method. Clean windows: 226; all windows: 255. "Gentle" means 2nd-order edges, the simplest standard filter.*

- **No filter (Raw)** fails during movement and at an unsteady start: 16 gross errors, mean error 4.2 BPM over all windows.
- The **planned 25–150 Hz** filter has one gross error (0.69 BPM over all windows): at the unsteady start of the first recording after exercise it reports 43 BPM where the reference, itself uncertain there, says 128 BPM. During the movement in the first resting recording it does as well as the 40 Hz filter.
- For this gentle filter type with the upper edge at 150 Hz, lower edges from **30 Hz to 80 Hz** have no gross error and 0.35 to 0.36 BPM over all windows.
- This does not hold for every filter. In disturbed windows some other designs with a 30 Hz lower edge, very gentle (1st-order) lower edges, and some combinations with a high lower edge and a wide band do show gross errors. The statement that design and upper edge make no difference is true for clean windows only.
- A listening filter with a high lower edge and a wide band is a poor input for counting: 100–800 Hz gives 7 gross errors over all windows (2.45 BPM). The design rule that counting always uses its own filter [1] is therefore right.

::figure{src="page/figures/bpm_tracks.png" alt="Heart rate over time for five recordings: reference and device estimates" caption="Heart rate over time, simulated. Each point is the estimate from the previous 8 seconds. Hollow reference points mark disturbed windows." width="wide"}

::callout{kind="finding"}
**Recommended BPM filter, as a precaution: 40–150 Hz, 2nd-order edges (Butterworth), the structure already planned, with the lower edge raised from 25 to 40 Hz.** This holds for the final counting method: with it, 30 Hz is the first lower edge of this filter type without a gross error, and 40 Hz keeps some distance from that limit. With a less strongly smoothed loudness curve the planned 25 Hz edge showed no such error either, so the filter and the counting method have to be fixed together. On clean windows no other design or upper edge did better, so the planned structure and the planned 150 Hz stay.
::end

::callout{kind="limitation"}
The difference between 25 Hz and 40 Hz rests on a single 8-second window at the start of one recording, where the reference itself is uncertain. This error at 25 Hz occurred with the final counting method (and with its slower smoothing alone); it disappeared with the half-rate check alone and with two smoothing steps at 8 Hz plus the check. The first-draft method had one gross error at 25 Hz and none at 40 Hz, in a different window. The two disturbances that cause gross errors (that start and a movement in one resting recording) explain why no filter and lower edges of 10 to 20 Hz do worse; they do not prove that 40 Hz is better than 25 Hz. The rule that should mark bad windows as invalid is not validated: with the recommended filter it was never triggered on clean windows but rejected one window during the movement whose estimate was only 0.3 BPM off, and with no filter it flagged 5 of the 16 gross errors and missed all 8 during the movement. For the filters that first reduce the data rate, the share of invalid windows in the result files is wrong because of an error in how overloaded values are counted; their mean errors are not affected.
::end

| Filter | Recording | Mean error, clean windows (BPM) | Mean error, all windows (BPM) | Largest single error (BPM) | Clean windows | All windows |
|---|---:|---:|---:|---:|---:|---:|
| 40–150 Hz gentle (recommended) | Resting 1 | 0.48 | 0.59 | 3.71 | 42 | 51 |
| 40–150 Hz gentle (recommended) | Resting 2 | 0.12 | 0.12 | 0.47 | 43 | 51 |
| 40–150 Hz gentle (recommended) | After exercise 1 | 0.32 | 0.46 | 2.83 | 39 | 51 |
| 40–150 Hz gentle (recommended) | After exercise 2 | 0.39 | 0.39 | 0.98 | 51 | 51 |
| 40–150 Hz gentle (recommended) | After exercise 3 | 0.20 | 0.20 | 0.66 | 51 | 51 |
| 25–150 Hz gentle (design candidate BPM) | Resting 1 | 0.47 | 0.53 | 3.99 | 42 | 51 |
| 25–150 Hz gentle (design candidate BPM) | Resting 2 | 0.14 | 0.14 | 0.50 | 43 | 51 |
| 25–150 Hz gentle (design candidate BPM) | After exercise 1 | 0.34 | 2.24 | 85.22 | 39 | 51 |
| 25–150 Hz gentle (design candidate BPM) | After exercise 2 | 0.35 | 0.35 | 0.87 | 51 | 51 |
| 25–150 Hz gentle (design candidate BPM) | After exercise 3 | 0.20 | 0.20 | 0.66 | 51 | 51 |

*Per recording, final counting method.*

## Results: listening

::term{name="decibel (dB)"}
A measure for ratios. +6 dB means twice as large, +20 dB ten times as large, 0 dB no change, negative values smaller. A "boost of 6 dB" doubles every sound value.
::end

### Why a filter can make overload worse

Removing the very low part should free number range, which could then be used to make the rest louder. For clean recordings this works: on the clean resting recording the planned 40–800 Hz filter would allow the sound to be made three times as large (9.6 dB). But the device needs one fixed setting for all cases, and the overloaded recordings spoil it.

::figure{src="page/figures/overshoot_explained.png" alt="A quarter of a second of signal before and after two filters" caption="The moment that limits the planned filter: a movement of the chest-piece in the first resting recording (39.9 s). Top: the microphone signal, which touches full scale (6 values). Middle: after the planned 40–800 Hz filter it swings to 1.03 times full scale, so the output cuts it off. Bottom: with a 100 Hz lower edge it reaches only 0.45 times full scale." width="wide"}

A filter does not only make things smaller. When it removes the slow part of a signal that sits close to full scale, the fast part that remains swings around zero and can reach further than the original did. Two events set the limit in these recordings: the movement shown above, and the cut-off beats after exercise. Leaving the movement out, the planned filter would have +0.208 dB of room instead of −0.236 dB, limited by the overloaded beats, so the finding does not depend on that one movement.

::figure{src="page/figures/headroom_gain.png" alt="Largest safe fixed boost against the lower band edge" caption="The largest fixed boost that never overloads the output on any of the five recordings, against the lower edge of the filter. Below 0 dB the filtered sound overloads sooner than the unfiltered one." width="wide"}

::callout{kind="finding"}
With a lower edge of 40 Hz or less, the filter output overloads sooner than Raw at full volume (107 of 109 such candidates). The planned 40–800 Hz filter has −0.236 dB of room. Room for a boost appears from about 50 Hz and grows quickly: 3.465 dB at 80 Hz, 5.975 dB at 100 Hz (so a setting of 5.9 dB is safe and 6.0 dB is not) and 8.363 dB at 150 Hz (2nd-order edges, upper edge 800 Hz). For this gentle filter the upper edge hardly changes this up to a lower edge of 100 Hz and changes it by about 2 dB at 150 Hz; for the steep filter the upper edge already matters at 100 Hz (about 3 dB).
::end

### Louder, but thinner

How loud a sound seems depends on pitch: hearing is much less sensitive to low tones [3]. Three standard estimates of loudness were computed, none of which replaces listening: a curve of equal loudness (ISO 226 [3]), "A-weighting", the correction for pitch that sound level meters apply (IEC 61672-1 [9]), and the loudness measure of broadcasting (ITU-R BS.1770-4 [10]).

::figure{src="page/figures/shortlist_tradeoff.png" alt="Safe boost, estimated loudness and sound between beats for eight candidates" caption="The eight candidates prepared for listening: safe boost, estimated loudness against Raw at that boost, and how strong the sound between the beats is compared with the heart sounds (lower is cleaner). The \"25–150 Hz (BPM position)\" entry is the BPM filter as originally planned; the recommended 40–150 Hz version was not part of the listening samples." width="wide"}

| Filter | Largest safe fixed boost (dB) | Loudness vs Raw, hearing-curve estimate (dB) | Loudness vs Raw, A-weighted (dB) | Sound between beats vs heart sounds (dB) | After-ring (ms) | Multiplications per sound value |
|---|---:|---:|---:|---:|---:|---:|
| No filter (Raw) | -0.010 | 0.0 | 0.0 | -14.9 | 2.2 | 0 |
| 40–800 Hz, gentle (design candidate) | -0.236 | -1.5 | -1.7 | -14.3 | 16.8 | 10 |
| 100–800 Hz, gentle | +5.975 | +1.5 | +1.1 | -11.8 | 9.8 | 10 |
| 100–800 Hz, steep | +7.200 | +2.5 | +2.0 | -11.1 | 17.1 | 20 |
| 150–800 Hz, steep | +9.760 | +3.4 | +2.8 | -9.9 | 12.2 | 20 |
| 60–800 Hz, very steep (elliptic) | +3.840 | +1.1 | +0.8 | -13.1 | 42.7 | 20 |
| Above 80 Hz only | +3.460 | +0.5 | +0.4 | -12.7 | 9.0 | 5 |
| 25–150 Hz (BPM position) | -1.843 | -3.9 | -3.9 | -17.8 | 37.3 | 10 |

*The eight candidates. "Gentle" means 2nd-order edges, "steep" 4th-order. The largest safe boost is given as computed, to 0.001 dB; a setting on the device must be rounded down (for example 5.9 dB, not 6.0 dB; the bar chart above shows values rounded down). It is slightly negative even for Raw, because the rule allows no output value at the limit and the recordings themselves contain such values. Loudness is compared with Raw, each at its own largest safe boost. "After-ring" is how long the filter keeps sounding after a short click (until it has faded to one hundredth); a long after-ring can blur the two heart sounds. This measure was defined by this study.*

- By the first two estimates, the planned filter ends up slightly **quieter** than Raw (about −1.5 dB), the gentle 100–800 Hz filter with its boost 1.1 to 1.5 dB louder, the steep 100–800 Hz filter 2.0 to 2.5 dB louder, and the steep 150–800 Hz filter about 3 dB louder. These are small gains for a boost of 6 to 10 dB, because the boost mostly replaces low tones that the filter removed.
- The third estimate (broadcast loudness) disagrees: it counts low tones more and rates every filtered version quieter than Raw (the gentle 100–800 Hz filter by 6.5 LU, the unit for differences in this loudness measure). The estimates do not settle the question.
- Raising the lower edge makes the sound between the beats relatively stronger (from −14.9 dB for Raw to −11.8 dB for the gentle 100–800 Hz filter and −9.9 dB for the steep 150–800 Hz filter): the heart sounds lose more than the background does.
- With the lower edge at 40 Hz (gentle filter) the upper edge matters little: between upper edges of 200 Hz and none the hearing-curve estimate changes by 1.2 dB and the A-weighted estimate by 1.3 dB. With a lower edge of 100 Hz the upper edge matters more (up to about 2.9 dB by the hearing-curve estimate). Averaged over the recordings, less than 2.4 % of the energy of any candidate lies above 1 kHz; in a single recording it reaches 8.2 %.

::figure{src="page/figures/shortlist_responses.png" alt="Which pitches each of the eight candidates lets through" caption="Which pitches each candidate lets through (0 dB = unchanged, −20 dB = one tenth)." width="wide"}

### Listen and compare

Use headphones: in these recordings almost all energy lies below 150 Hz, which small loudspeakers of phones and laptops reproduce poorly (general experience, no source checked). Each player holds the same 10 seconds through all eight candidates. Tap a row to switch while it plays. "Hide names" gives a blind comparison. The loudness on a computer is not the loudness of the device; compare the candidates with each other. A 20-millisecond fade at the start and end of each sample is not part of the device.

::audio-compare{excerpt="resting" variants="madeup,device,matched" title="At rest" note="Clean recording, about 80 beats per minute."}

::audio-compare{excerpt="elevated-clean" variants="madeup,device,matched" title="After exercise, no overload" note="About 100 beats per minute."}

::audio-compare{excerpt="elevated-overload" variants="madeup,device,matched" title="After exercise, repeated overload on the beats" note="The microphone path is overloaded on many beats here. Listen for which candidates make the distortion more or less noticeable."}

::audio-compare{excerpt="movement-artefact" variants="madeup,device,matched" title="At rest, with a movement" note="Contains a movement of the chest-piece: the case for \"too much other sound\"."}

::callout{kind="open"}
**The listening filter is not decided.** It is Nico's judgement by ear. A reasonable first candidate to check is "100–800 Hz, gentle" with a fixed boost of 5.9 dB: by two of the three estimates it is 1.1 to 1.5 dB louder than Raw, by the third 6.5 LU quieter, and the filter weakens sound at 50 Hz to about a quarter (−12.3 dB; with the boost, about half, −6.4 dB). Compare it against "40–800 Hz" and "above 80 Hz only" for whether it sounds too thin. If the planned 40–800 Hz filter sounds best, it cannot be boosted.
::end

## What it means for the design

1. **BPM filter (P08):** 40–150 Hz, a 2nd-order lower edge and a 2nd-order upper edge (Butterworth; the design documents call these high-pass and low-pass), 10 multiplications per sound value. Recommendation of this study, to be confirmed with more recordings.
2. **Counting method:** loudness curve smoothed twice (at 5 Hz) and reduced to 100 values per second, 8 seconds in memory, repeat pattern search once per second, with the half-rate check. On clean signal these two changes matter at least as much as the filter.
3. **Listening filter (P08):** open until Nico has listened. A fixed boost per switch position is a new design element; the firmware today can only make the sound smaller, never larger [5]. The BPM switch position would then play the 40–150 Hz filter, which has not been prepared as a listening sample.
4. **Overload at the microphone** cannot be filtered away. It limits both the loudness and the sound quality at high heart rates. Lighter pressure did not prevent it in the third recording after exercise.
5. **The analysis keeps its own filter**, independent of the listening switch, as designed.

## Limitations

- In the movement of the first resting recording the raw signal contains straight ramps of about 35 thousandths of a second. This may be the microphone recovering from overload or values lost during capture; it was not investigated.
- One person, five recordings, one session, membrane side only, two chest positions. No murmurs, no other bodies, no clothing noise, no talking.
- No independent heart-rate reference. The reference comes from the same sound, partly from the same pitch range as the tested filters; its methods agree within 1.8 BPM on clean windows, and its true accuracy is unknown.
- Consecutive 8-second windows overlap by 7 seconds: only 35 windows that do not overlap fit into the five recordings, so the 255 windows carry much less information than their number suggests.
- The counting method was chosen on the same five recordings it was tested on; this was not checked on held-out data. For the filter choice alone, a check that left one recording out at a time showed that picking a filter on four recordings does not beat the planned filter on the fifth.
- The half-rate check could wrongly double the rate where the second heart sound is as loud as the first and falls halfway between two beats. This did not happen in these recordings but was not tested at other chest positions.
- Heart rates covered: 73 to 149 BPM. The planned range of 30 to 200 BPM [1] is not covered at either end.
- Processor load and memory are estimates. Nothing ran on the device.
- The loudness figures are estimates for an assumed listening level; the earpiece and the ear are not in the simulation. The digital-to-analogue converter [11] and the earpieces are treated as ideal.
- The separate measurement of the chest-piece and tube of 22 November 2026 [13] was not used. Two reviews of it found it unreliable below about 400 Hz (as stated in the brief of this study; the review texts were not inspected), and the recordings already contain the real chest-piece.

## Next steps

1. Nico listens to the samples and chooses the listening filter and its boost.
2. Record more sessions with a pulse oximeter or smartwatch at the same time (as REQ-06 requires [7]), including other chest positions, movement and poor contact, and repeat this comparison.
3. Decide how to deal with overload at the microphone at high heart rates.
4. Write the filter and the counting method into the firmware and measure processor time and memory on the device.
5. Test the rule for invalid windows with deliberately bad signals (REQ-08 [7]).

## How this read was checked

Three independent reviewers (one model each from three providers: GPT Astra, Claude Fable, Gemini Neon) checked the numbers against the result files, the method, the sources and the plainness of the language, in three rounds on 23 November 2026. Scores out of 10: round 1: 6, 6, 6; round 2: 8, 8, 9; round 3: 8, 9, 9. Every finding the reviewers marked as blocking was corrected; the two from the last round (an overstated sentence about the counting method and one table value) were corrected after that round and not reviewed again. Known open points:

- Two errors in the simulation code do not affect any number on this page and are not fixed: the share of invalid windows for the filters that first reduce the data rate, and the order of volume and output limit at less than full volume.
- The recommended 40–150 Hz filter is not among the listening samples; the "BPM position" sample is the originally planned 25–150 Hz filter.
- The audio players were tested in desktop browsers and in a sandboxed test frame, not on a real phone.

::glossary

## Sources

::sources
[1] DigitalStethoscope project, system design: `Development/system/design/system/parameters.md` (P01, P05, P06, P08), `interfaces-and-behavior.md` (section "DSP and measurement design") and `shared-filter-signal-flow.puml`; filter roles decided on 13 November 2026 (`Development/system/planning/mvp-decisions-2026-11-13-delivery-and-filters.md`). Project documents and project decisions, repository state of commit b1c7fbb.
[2] TDK InvenSense, *INMP441 Omnidirectional Microphone with Bottom Port and I²S Digital Output*, DS-INMP441-00, revision 1.0, 2014. [Datasheet](https://www.farnell.com/datasheets/1824785.pdf), accessed 11 November 2026 according to the project's AUDIO design; not re-opened for this study.
[3] ISO 226:2003, *Acoustics — Normal equal-loudness-level contours*, International Organization for Standardization. Covers 20 Hz to 12.5 kHz. The falling sensitivity toward low tones is taken from this standard's contours as implemented in the study's script (60-phon contour, extended below 20 Hz by the script); the full text was not inspected for this study (unverified).
[4] DigitalStethoscope project, AUDIO design: `Development/system/design/AUDIO/interfaces-and-behavior.md` (sample rate 16,000 Hz, blocks of 64 values, sample format, volume as linear gain 0–100 % with saturation). Project document, commit b1c7fbb.
[5] DigitalStethoscope firmware, `Development/system/coding/app/L2_application/L2_AUDIO/audio_processing.c`, function `audio_applyVolume`, commit b1c7fbb.
[6] Espressif Systems, *ESP-DSP Library Benchmarks*, ESP32-S3 column, row `dsps_biquad_f32` (17,552 processor cycles per 1,024 values). [Benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html). Value taken from the project's thesis material (`thesis-material/03-grundlagen-technisch/04-dsp-filter.md`, register entry `esp_dsp_benchmarks`, access date not recorded there); one council reviewer re-opened the page on 23 November 2026 and found the same value. The processor speed of 240 MHz and the costs assumed for the other operations are assumptions of this study.
[7] DigitalStethoscope project, `Development/system/requirements/system-requirements.md`, REQ-06 and REQ-08. Project requirements.
[8] ANSI/AAMI EC13:2002, *Cardiac monitors, heart rate meters, and alarms*, Association for the Advancement of Medical Instrumentation. Cited from the project's source register (entry `ec13`); full text paywalled and not inspected.
[9] IEC 61672-1:2013, *Electroacoustics — Sound level meters — Part 1: Specifications* (A-weighting). Full text not inspected for this study; the weighting was implemented from its published formula and re-derived for 16,000 values per second.
[10] ITU-R BS.1770-4 (2015), *Algorithms to measure audio programme loudness and true-peak audio level*, International Telecommunication Union. Implemented from the recommendation's filter definition, re-derived for 16,000 values per second; a full-scale 997 Hz tone reads −2.97 LUFS instead of −3.01 LUFS (LUFS is the unit of this loudness measure).
[11] Texas Instruments, *PCM510xA 2.1 VRMS Audio Stereo DAC*, SLAS859C, 2015. [Datasheet](https://www.ti.com/lit/ds/symlink/pcm5102a.pdf), accessed 11 November 2026 according to the project's AUDIO design; not re-opened for this study.
[12] Own measurements and simulation of this study, 23 November 2026: recordings, scripts and result tables in `C:/Users/nicop/Desktop/heart-filter-study/` (`STATE.md`, `FINDINGS.md`, `reference/`, `results/`, `listening/`). All numbers on this page without another source come from there.
[13] Own measurement, audio chain session of 22 November 2026: `C:/Users/nicop/audio-chain-measurements/2026-11-22/` (`notes.md`, `analysis/`); capture firmware built from commit b1c7fbb with the untracked chain-measurement files. Not used for any number on this page.
::end
