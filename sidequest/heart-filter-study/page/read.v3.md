---
title: Which filters should the digital stethoscope use?
subtitle: A simulation with five own heart recordings and two public collections (heart sounds with ECG, heart sounds with murmurs), for listening and for counting the heart rate (TICKET-189)
date: 23 November 2026
status: Second version, with public data; listening judgement pending
watermark: Published by Claude-Fable-5.2 on behalf of Nico running in T3 Code through Claude Code.
---

::summary
**What is new in this version.** The first version rested on five recordings of one person. This one adds two public collections: 29 hours of heart sounds from 22 young men with an ECG as an independent heart-rate reference, at rest and during exercise, and recordings of 874 patients, mostly children, with and without heart murmurs. They were passed through a model of our device's input. It also explains how the table measurement of 22 November fed into the study, and explores counting the heart rate on the stored 8 seconds as a whole.

**Heart rate: the filter recommendation holds, the counting method does not.** The recommended **40–150 Hz** filter beats the planned 25–150 Hz filter and no filter on the public recordings, now against an ECG, with the counting method of the first version and, by a smaller margin that was not tested on its own, with the improved one. But the counting method of the first version fails there during exercise: sitting still it is 2.7 beats per minute (BPM) off on average, over all recordings 26.6 BPM, because above about 90 BPM it often reports a third of the true rate. The cause was found (it picks the wrong one of several equally good repeat patterns) and an improved choice was built and tested on people it was not tuned on: it halves the error (28.4 to 13.1 BPM) and leaves the error on Nico's recordings unchanged (it shows 97.6 % of their windows as valid instead of 99.6 %), but below 70 BPM its error doubles (4.3 to 8.7 BPM), and it is still far from the target during exercise. By the estimated processor time, the heart rate could be counted once per second on the stored 8 seconds as a whole; whether the larger methods fit beside the running firmware needs a check on the device. Filtering forwards and backwards brings almost no gain of its own; a loudness curve from a published research method helped more, but was only tried with look-ahead and helps less than the improved choice of the repeat pattern.

**Listening: the first candidate is confirmed for murmurs.** Of the six filters prepared for listening in the first version, the planned 40–800 Hz filter gave the lowest murmur level and the lowest score for telling murmur from no murmur. Filters with a lower edge of 80 to 150 Hz let simple measures tell murmur from no murmur better (score 0.70 for 100–800 Hz against 0.62 for the planned filter and 0.53 without a filter; 0.5 is chance) and let the murmur stand out more against the quiet part of the beat (+3.0 against +1.6 dB; dB is a measure for ratios, explained below: +6 dB is twice as large). The first candidate named in the first version, **100–800 Hz with a boost of 5.9 dB**, is in that top group. Its gain in murmur loudness (4.1 dB) is the boost, and the room for that boost was found only on Nico's five recordings; on the public recordings, as their loudness was set here, there is no such room. The choice by ear is still Nico's; murmur samples are now among the listening samples.

**How far this carries.** The public recordings come from other sensors and other people, are much brighter than what our chain delivered on Nico's chest, and were only passed through a model of our device input. They test the filters and the counting method more widely; they do not show how our device sounds on those people.
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

## The own recordings

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

## How the first measurement setup fed into this study

One day before the heart recordings, on 22 November 2026, the sound path of the device was measured on a table, without a patient (own measurement [13]). This section says what that measurement was, what came out, and what this study took from it and what it did not. It rests on a condensed record of the setup, its results and two independent reviews of it [14].

### What was measured, and how

A headphone played a test tone that glides from low to high pitch (20 Hz to 8 kHz, four glides of 5 seconds, at two loudness settings). The device recorded it with the same small capture program that later recorded the heart sounds: it stores the microphone signal unchanged, 16,000 values per second. From the recording, the computer works out how strongly each pitch arrives. Three arrangements were measured, each re-seated four times:

::figure{src="page/figures/run2_chain_measurement_setups.png" alt="Three arrangements side by side: ear cup over the bare microphone; ear cup over the membrane side of the chest-piece with tube and microphone; the same with the bell side" caption="The three arrangements of 22 November 2026. A: the microphone alone under the ear cup. B: the membrane side of the chest-piece under the ear cup, with the sound travelling through the tube to the microphone. C: the same with the bell side. Dividing B by A and C by A was meant to leave the chest-piece and tube alone, because headphone and microphone are in both and cancel. Dividing C by B compares bell and membrane directly and does not need A." width="wide"}

There was no calibrated measuring microphone and the sound reached the chest-piece through air, not through a body. The measurement can therefore only compare arrangements with each other; it cannot say how the chest-piece behaves on a chest.

### What came out

::term{name="decibel (dB)"}
A measure for ratios. +6 dB means twice as large, +20 dB ten times as large, 0 dB no change, negative values smaller. A "boost of 6 dB" doubles every sound value; "a dip of 13 dB" means a pitch arrives at less than a quarter of its strength.
::end

Both reviews checked the calculation and found it correct: they recomputed the result files (agreement within 0.0005 dB) and recovered a known test system within 0.1 dB; the two loudness settings agree within 0.2 to 0.4 dB, so the chain behaved the same at both levels [14]. These results hold:

- **The tube leaves a fingerprint.** Both sides of the chest-piece show the same row of peaks at about 261, 572, 940, 1,313 and 1,705 Hz (within ±2 Hz of each other). This fits a tube of about 44 to 45 cm that favours certain pitches, like an organ pipe; the tube length is inferred, not measured [14].
- **Bell against membrane (C ÷ B):** in air, the two sides are nearly the same below 1 kHz. The membrane is 9 to 10 dB stronger around 1.7 to 2.5 kHz, the bell 3.5 to 13 dB stronger above 4.5 kHz.
- Both sides fall off steeply above about 5 kHz. This is the hardware, not the calculation.

And these do not hold:

- **Chest-piece alone (B ÷ A, C ÷ A) below about 400 Hz.** Arrangement A had a weakness of its own: a dip of about 13 dB at 220 Hz, caused by the ear cushion resting on the edge of the circuit board; it disappears when the cup is lifted. Dividing by A adds about 10 to 13 dB to the peak at about 250 Hz in both results.
- **Membrane side above about 5.5 kHz:** sound reached the microphone through the air 0.5 to 1 thousandths of a second before the sound through the tube.
- The later seatings (after a pause of 68 minutes) were about 2 dB lower overall and up to 6 dB lower below 315 Hz, and A was not measured again at the end, so slow drift cannot be ruled out.
- The distortion figures are upper limits only, set by the background noise.

::figure{src="page/figures/run2_chain_measurement_valid_ranges.png" alt="Bands over a pitch axis from 20 Hz to 8 kHz showing where each measured quantity is usable" caption="Where the measurement of 22 November can be used, according to the two reviews [14], and where the heart sounds of the own recordings have most of their energy. The two do not overlap for the chest-piece-alone results: these are unusable exactly where the heart sounds are." width="wide"}

### What this study took from it

- **The capture program.** The heart recordings of 23 November were made with the capture firmware written for that measurement. Without it there would be no raw microphone recordings to simulate on.
- **The microphone model.** The measurement's description of the microphone from its datasheet [2][15] is the microphone step in this study's model of the device chain for the public recordings (below). Two of its values are still unchecked against the datasheet page and stay marked as such.
- **The limits of validity.** The reviews' finding that the chest-piece-alone results are unusable below about 400 Hz decided how the chest-piece is treated here.
- **The decision not to apply a chest-piece correction.** Nico's own recordings already contain the real chest-piece, tube and microphone, so nothing must be added. For the public recordings (see below) a correction was considered and rejected: the only quantity that is reliable at the low pitches of the heart sounds, bell against membrane, describes the difference between the two sides of our chest-piece. It says nothing about the difference between our chest-piece and the unknown sensors of the public recordings, and those recordings were not made through our bell. This is a decision of this study.
- **No cross-check for the heart sounds.** The own recordings contain almost no energy above 150 Hz (0.06 % between 150 and 800 Hz). The measurement cannot explain this: where it is usable, above 400 Hz, the path through chest-piece and tube was stronger in air than the bare microphone at most pitches (membrane side, at the louder setting: by 1 to 11 dB between 400 Hz and 1 kHz and by up to about 20 dB near 2.5 kHz; from the result files of the session [13]), which neither supports nor contradicts the missing energy on a chest, where the chest-piece is loaded differently.

### What it did not take, and why

- No curve of the chest-piece or the tube enters any number on this page. Below 400 Hz, where the heart sounds are, the measured curves are not valid.
- The tube's row of peaks (261 Hz and upward) was not built into the model for the public recordings. It lies above most heart-sound energy, and the public sensors have their own unknown tubes and housings.
- The distortion figures were not used, since they are upper limits only.

### What the planned second session would change

A second session is planned but not done [14]: arrangement A rebuilt without its own dip and measured before and after each block, a sealed tube, checks for sound leaking past the chest-piece, a recording of silence, a test tone from 10 Hz, and corrected calculation details. If it yields a valid chest-piece and tube curve down to low pitches, the model of the device chain could use a measured curve instead of the tone-balance matching used here. It would still be a comparison between arrangements, measured in air: how the chest-piece behaves on skin would remain open, and relating the overload at the microphone to a sound pressure would need a calibrated measuring microphone in addition.

## A second source: public recordings

The first version of this study had only Nico's five recordings: one person, no heart murmurs, and a heart-rate reference taken from the same sound. This version adds two open collections of heart recordings from the research archive PhysioNet. Both were downloaded on 23 November 2026, and every file was checked against the checksum list of its source (a checksum is a fingerprint of a file that shows it arrived unchanged).

| | Heart sounds with ECG (EPHNOGRAM [16]) | Heart sounds with murmur labels (CirCor DigiScope [17], described in [18]) |
|---|---|---|
| What it adds | An independent heart-rate reference, at rest and during exercise | Murmurs, labelled by a specialist, with the parts of each beat marked |
| People | 24 healthy men, 23 to 29 years (as stated by the source) | 942 patients in the published part, mostly children; of the 874 used, 178 with a murmur between the heart sounds, 695 without, and 1 with a murmur only after the second heart sound |
| Recordings used | 66 of 69 (about 29 hours): 8 of 30 seconds at rest, the others of 30 minutes while sitting, lying, walking, on a treadmill or on a bicycle | 2,888 recordings of 874 patients, 58,156 fully marked heartbeats |
| Sensor | A stethoscope converted to digital, held by a chest strap during exercise | An electronic stethoscope in a screening clinic |
| Values per second | 8,000 | 4,000 |
| Reference | ECG, recorded at the same time | Murmur present or absent, loudness grade, pitch, and the start and end of each heart sound |
| Licence | Open Data Commons Attribution | Open Data Commons Attribution |

*The two public collections as used. Counts are from the downloaded files; the source page of the murmur collection describes 1,568 patients, of which 942 are published.*

::term{name="ECG"}
An electrocardiogram records the electrical signal of the heart through electrodes on the skin. Each heartbeat shows as a sharp spike. Counting the spikes gives the heart rate independently of any sound.
::end

::term{name="heart murmur"}
An extra, noise-like sound between the two normal heart sounds, caused by turbulent blood flow. Some murmurs are harmless, some point to a heart defect. Doctors grade their loudness from I (very soft) upward; in this collection the grades are I, II and "III or more".
::end

Three recordings of the first collection were left out: two are exact copies of other recordings filed under a different person, and one is marked by its authors as having no sound. This leaves 22 of the 24 people (the two copies were the only recordings filed under their two names), and one of the 22 has no window with a reliable ECG, so most numbers rest on 21 people. From the murmur collection, the 68 patients whose label is "unknown" were left out, and one recording with unreadable markings.

### Putting public recordings through our device

The public recordings were made with other sensors. To test our filters on them as the device would see them, each recording was passed through a model of our device's input, built from what is known:

1. Convert to the device's 16,000 values per second.
2. Apply the microphone's behaviour from its datasheet [2][15]: it weakens very low pitches (to about 0.7 times at 60 Hz by the datasheet; two further values of the model are not yet checked against the datasheet).
3. Set the loudness so that the heart sounds are as strong as in Nico's recordings. Two settings: **rest level** (as strong as in his three recordings without lasting overload) and **overload level** (raised until one beat in three reaches full scale, as in his two overloaded recordings).
4. Add background noise where the public recording is quieter between the beats than our real chain was.
5. Cut off at full scale, as the real microphone path does.

After that, the simulation of the device is the same as for Nico's recordings. No correction for our chest-piece is applied (see the previous section). As a variant, the tone balance of the public recordings was shifted towards that of Nico's recordings ("matched"); this stands in for all differences at once, sensor, chest-piece, tube and person, and cannot tell them apart.

### How close the modelled public recordings come to our real chain

Nico's recordings are the real chain on a real chest, so they are the yardstick.

::figure{src="page/figures/run2_public_vs_own_spectrum.png" alt="Strength against pitch for the own recordings and the two modelled public collections" caption="Tone balance of Nico's recordings and of the public recordings after the model of our device input. Each curve is drawn relative to its own strongest range, so only the shape counts." width="wide"}

| Measure | Own recordings | Public, with ECG | Public, murmur data |
|---|---:|---:|---:|
| Heart-sound level at rest (dB below full scale) | 9.6 | 9.7 | 9.7 |
| Energy below 20 Hz (%) | 52 | 17 | 2.5 |
| Energy from 20 to 150 Hz (%) | 48 | 80 | 43 |
| Energy from 150 to 800 Hz (%) | 0.06 | 2.1 | 40 |
| Sound between the beats, relative to the heart sounds (dB) | −21 | −14 | −11 |

*How close the modelled public recordings come to the own recordings at rest level, without the matching variant (medians over recordings; computed on 20 recordings of the collection with ECG and 200 of the murmur collection).*

- **Loudness fits**: the heart-sound level at rest agrees within 0.1 dB, and at the overload level 34 % of all beats taken together reach full scale, as in Nico's recordings (the typical single recording reaches less: 23 % in the collection with ECG and 20 % in the murmur collection). This was set on purpose, so it is not a test.
- **Tone balance does not fit.** The public recordings are much brighter: relative to Nico's recordings they carry 10 to 18 dB more between 100 Hz and 1 kHz (with ECG) and 12 to 39 dB more (murmur data). They carry far less below 20 Hz. The matching variant brings the recordings with ECG to within about 6 dB; the murmur data stay 14 to 33 dB too bright above 200 Hz, because the correction was limited to 12 dB.
- **They are noisier between the beats** by 7 to 10 dB.
- **Overload works differently.** In Nico's overloaded recordings the cut-off beats ride on a slow swing below 20 Hz that uses up 0.2 to 0.4 of the number range; when the slow part is removed from the stored recordings afterwards, only 3 of 129 and 5 of 127 beats still reach full scale instead of 42 and 45 (own analysis for this version; the recordings were already cut off when stored, so how far the true peaks went beyond full scale is unknown). The public recordings lack this slow part, so in the model the heart sounds themselves must be raised until they are cut off.

::callout{kind="limitation"}
The public recordings test the filters on other people, with murmurs and against an ECG. They do not show how our chain sounds on those people. Whether the difference in tone balance comes from the sensors, from our chest-piece and tube, or from the people (children in the murmur collection, one adult man in ours) cannot be separated with the data at hand.
::end

## How the device was simulated

The simulation follows the firmware and the design documents step by step [1][4]: the same 16,000 values per second, the same blocks of 64 values (4 thousandths of a second, written 4 ms), the same order of steps at full volume, and the firmware's own volume and output-limit code [5], copied so that it produces the same numbers bit for bit. All results on this page use full volume (100 %). In the first version the simulation limited the signal before the volume step at lower volume settings, while the design does so after it; this is corrected in this version and does not change any number here (at full volume the output is identical value for value).

::figure{src="page/figures/signal_chain.png" alt="Block diagram of the listening path and the heart-rate path" caption="The two paths in the device, as designed. The heart-rate path always uses the BPM filter and takes its signal before the volume control, whatever the listener selects [1]." width="wide"}

Where the firmware is not written yet (the filter and the heart-rate code are still empty), the simulation uses what the device would realistically use. These are choices of this study, not measurements on the device:

- Filters are computed with numbers with a decimal point, stored in 32 bits (a choice of this study for the device; the firmware's filter is not written yet), in small standard building blocks. How sharply a filter cuts off at its edges is called its order: a 2nd-order edge is gentle, a 4th-order edge is steep. A filter with two gentle edges needs 10 multiplications per sound value.
- The heart-rate method follows the draft in the system design [1]: filter, turn the signal into a slow loudness curve (100 values per second), keep the last 8 seconds (800 values, 3.2 kilobytes), and once per second search this curve for its repeat pattern.

::term{name="repeat pattern search (autocorrelation)"}
The loudness curve is compared with a shifted copy of itself. If shifting by 0.75 seconds makes the two copies match best, the heart beats every 0.75 seconds, which is 80 beats per minute. The method uses the whole 8 seconds, not single beats.
::end

The method only uses the past (the device cannot look ahead). Its cost was estimated, not measured: about half a percent of one processor core and about 8 kilobytes of memory. The filter part of this estimate uses the published speed of the processor's filter routine [6]; the larger part (loudness curve and pattern search) uses assumed costs per operation without a source. A measurement on the device is still needed.

## What the heart rate was compared with in the own recordings

::callout{kind="limitation"}
For Nico's recordings there was no independent heart-rate sensor: no ECG, watch or pulse oximeter. The reference was derived from the recordings themselves. It is weaker than an ECG. In this version the method was checked against an ECG on public recordings (see the results against an ECG below).
::end

The reference was computed afterwards, with methods that may look at the whole recording at once, which the device cannot. Three different methods marked every heartbeat: one follows the loudness peaks, one follows changes in the sound's pitch content, one searches for the average beat shape. A beat counts as certain if at least two methods agree within 0.06 seconds; five beats are marked as uncertain, two of them kept from a single method to fill a gap. For each 8-second window the reference rate is the average rate of the whole beats inside it.

- 226 of 255 windows are called **clean windows**: they contain no detected disturbance, no uncertain or missing beat, and the three methods differ by no more than 3 BPM. In these windows the methods actually differ by at most 1.8 BPM. This is a measure of how well the methods agree, not a proof of accuracy.
- The other 29 windows are **windows with an uncertain reference**. 25 of them contain a detected disturbance (a movement, a rubbing noise or the unsteady start of a recording); 4 contain no detected disturbance but one uncertain beat near the end of a recording. They are kept and reported separately ("all windows" below means all 255), because a real examination has such moments too. Errors there are differences from an uncertain value. For short, the text calls them disturbed windows.
- A check on the average beat shape shows two sounds per cycle in every recording, so the reference did not count half or double the rate.

The reference has three weaknesses beyond the missing sensor. All three methods listen to the same sound: a beat that cannot be heard, or a noise that sounds like a beat, can mislead all three together, and the third method learns its beat shape from beats the first two agree on. The beat marks are placed using the 25–150 Hz range, the same range as the planned BPM filter, so the reference is not fully independent of the filters being tested. And disturbances are detected partly by strong energy between 3 and 20 Hz, with limits set by looking at these five recordings, so it is partly built in that filters letting those low pitches through do worse in disturbed windows.

## Results: heart rate on the own recordings

This section is the first part of the study, on Nico's five recordings, unchanged in its numbers. The next section tests the same filters and the same counting method against an ECG.

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
The difference between 25 Hz and 40 Hz rests on a single 8-second window at the start of one recording, where the reference itself is uncertain. This error at 25 Hz occurred with the final counting method (and with its slower smoothing alone); it disappeared with the half-rate check alone and with two smoothing steps at 8 Hz plus the check. The first-draft method had one gross error at 25 Hz and none at 40 Hz, in a different window. The two disturbances that cause gross errors (that start and a movement in one resting recording) explain why no filter and lower edges of 10 to 20 Hz do worse; they do not prove that 40 Hz is better than 25 Hz. The rule that should mark bad windows as invalid is not validated: with the recommended filter it was never triggered on clean windows but rejected one window during the movement whose estimate was only 0.3 BPM off, and with no filter it flagged 5 of the 16 gross errors and missed all 8 during the movement. For the filters that first reduce the data rate, the share of invalid windows in the result files of the first version was wrong because of an error in how overloaded values were counted (31 windows wrongly marked invalid); the error is corrected in the code of this version, the tables of this section were not recomputed, and their mean errors are not affected.
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
- The acceptance target is still met only when sitting still (and there only with the validity rule of the first part; the new rule shows 87 to 88 % of the windows on the test half). On the test half no exercise situation meets it with either method.

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

- **The direction of the first part's recommendation is confirmed, now with an independent reference.** The recommended 40–150 Hz filter is better than the planned 25–150 Hz filter by 4.4 BPM (3.3 to 5.5) at rest level and by 1.8 BPM (1.0 to 2.6) at overload level, and it is better than no filter by 6.9 BPM. Of the lower edges in the table, no filter and 10 Hz are the worst (33.5 and 33.7 BPM). In the first part this step rested on a single window.
- **But 40 Hz is not the best lower edge on the public recordings.** At rest level the error keeps falling up to 80 Hz, and a steep filter from 60 to 150 Hz does best. That same steep 60 Hz filter was the worst in the first part, where it produced errors on clean windows of Nico's recordings. At overload level the curve is flat between 40 and 60 Hz.
- **With the improved counting method the order stays the same and the gaps shrink** (test half, rest level: no filter 16.8 BPM, 25–150 Hz 15.9, 40–150 Hz 13.1, 60–150 Hz 11.5).
- **On Nico's recordings the improved counting method removes the difference between 25 and 40 Hz.** With it, the planned 25–150 Hz filter has no gross error either (0.30 BPM on clean windows, 0.36 on all, against 0.30 and 0.35 for 40–150 Hz). The single window that separated the two in the first part was a product of the first part's counting method. What Nico's recordings still speak against is the steep 60–150 Hz filter (with the improved method still 8 gross errors and 2.7 BPM on all windows; all 8 lie in the disturbed windows, on clean windows it reaches 0.32 BPM).
- **The ranking of the first part does not carry over** filter by filter (the two orders are unrelated on reliable windows). This was to be expected: in the first part almost all filters lay within 0.29 to 0.44 BPM of each other, which is no ranking at all.
- **Other filter designs and the upper edge.** Other designs with the same edges were 2 to 7 BPM worse than the planned gentle design (Butterworth 26.6 BPM; Bessel 28.5, Chebyshev 29.1, elliptic 29.1, the FIR candidate 34.0), and the upper edge made no difference (26.6 to 27.2 BPM for upper edges from 100 to 800 Hz, lower edge 40 Hz). At rest level the listening candidate 100–800 Hz was as good an input for counting as 40–150 Hz (26.8 BPM); at the overload level it was 6.1 BPM worse (26.3 against 20.2 BPM, range 3.8 to 8.4). The first part's finding that it is a poor input came from the low-pitched disturbances in Nico's recordings, which the public recordings lack; the overload level shows that the public recordings do not clear it as an input for counting either.
- **The counting method matters far more than the filter.** Changing the filter moves the public result by a few BPM; changing the choice of the peak moves it by 15 BPM. The order of the counting variants of the first part is even reversed here: the half-rate check alone (23.1 BPM) beats the first part's final method (26.6 BPM).

::callout{kind="finding"}
**Recommended BPM filter: still 40–150 Hz, gentle edges.** The evidence for it over the planned 25–150 Hz filter now comes from the public recordings (better by 4.4 BPM with the first part's counting method and by 2.8 BPM with the improved one on the test half, a difference of two means that was not tested on its own); on Nico's recordings the two are equal once the counting method is improved. The public recordings would favour a lower edge of 50 to 60 Hz, but a steep 60 Hz edge failed on Nico's recordings, the only ones made with our own chain, so 40 Hz remains the cautious choice, and 50 Hz is worth testing on the device. **The counting method of the first part has to be replaced:** it must not take the highest peak of a fairly compared repeat-pattern search. The improved method of this version is the new starting point; it still needs a repair for slow heart rates.
::end

::callout{kind="limitation"}
The public recordings were made with a sensor strapped to the chest of young men while they walked, ran and cycled; four in five windows are from exercise. A stethoscope is held on a patient at rest. The numbers during exercise therefore say more about the counting method's weak spots than about everyday use, and they come from another sensor passed through a model of our device input. The improved method was tuned on half of the same collection; it has not seen any other data except Nico's five recordings.
::end

### Does the heart rate have to be counted in real time?

No. The count uses the last 8 seconds. The planned design keeps only their loudness curve in memory (800 values); keeping the sound itself as well is possible and costs the extra memory shown in the table below. The counting path could therefore work on the whole stored stretch at once and look "ahead" inside it, which a filter that handles each value as it arrives cannot. Nico asked for this to be explored during this version (23 November 2026). Listening is not affected: the sound for the ear must stay in real time.

Two ideas were tried, on the same 8-second windows as before:

- **Filtering forwards and backwards.** Running a filter over the stored stretch once forwards and once backwards cancels the small delay that a filter gives to different pitches, and makes its edges twice as steep.
- **The method of Springer, Tarassenko and Clifford [20].** A widely used research method for marking the heart sounds. Its openly published program code [21] was read for this study (the article itself is not freely available and was not read; the code was not run). Before it marks anything, the code prepares the sound and estimates the heart rate: a filter from 25 to 400 Hz run forwards and backwards, removal of loud clicks, a loudness curve taken from the *logarithm* of the signal (which makes loud and soft beats more alike), and a repeat-pattern search that, unlike the one of the first part, lets longer shifts count less, but only looks between 0.5 and 2 seconds, so that it cannot report more than 120 BPM. Its second half, a statistical model that marks each heart sound, was not implemented: it needs trained values this study does not have.

::figure{src="page/figures/run2_window_methods_error.png" alt="Mean heart-rate error of fifteen counting variants on the own recordings and on the public recordings at two loudness levels" caption="Counting on the whole stored 8 seconds against the method of the first part (amber, dashed line), on Nico's recordings and on the public recordings with ECG (every fourth window; lines: 95 % ranges over people). " width="wide"}

| Variant | Own recordings, clean / all windows (BPM) | Public with ECG, change against the first part's method (BPM, rest level) | The same at overload level |
|---|---:|---:|---:|
| Method of the first part: filter while recording, 40–150 Hz | 0.30 / 0.35 | 0 (mean error 26.9) | 0 (mean error 20.2) |
| Same filter, forwards and backwards over the stored stretch | 0.33 / 0.39 | −3.6 (−4.5 to −2.7) | −1.2 (−2.1 to −0.5) |
| Same filter applied twice while recording (no look-ahead) | 0.32 / 0.38 | −3.5 (−4.5 to −2.6) | −1.0 (−1.9 to −0.2) |
| Springer's preparation as published (limit 120 BPM) | 21.0 / 19.2 | worse (+7.1) | worse (+4.4) |
| Springer's preparation, range widened to 200 BPM | 0.38 / 0.44 | −1.2 (−3.7 to +1.4) | −5.3 (−8.0 to −2.2) |
| Springer's preparation, range widened to 200 BPM, with half-rate check | 0.38 / 0.44 | −6.2 (−8.4 to −3.7) | −9.7 (−11.9 to −7.1) |
| Springer's three loudness curves combined, with half-rate check | 0.63 / 0.69 | −7.4 (−9.4 to −5.1) | −8.8 (−10.9 to −6.3) |

*Whole-window variants against the method of the first part. Own recordings: 226 clean and 255 windows. Public recordings: 21 people, 21,956 windows with a reliable ECG rate (every fourth second), ranges are 95 % ranges over people. A negative change is an improvement.*

- **On Nico's recordings nothing beats the method of the first part.** On all 255 windows the mean error was 0.35 BPM for the method of the first part, 0.39 for forwards-and-backwards filtering, 0.44 for the widened Springer preparation with the half-rate check and 0.69 for the three combined loudness curves; differences of a tenth of a BPM cannot be told apart on five recordings. The Springer code as published fails there (19 BPM mean error), because two recordings are faster than its limit of 120 BPM.
- **On the public recordings, filtering forwards and backwards helps by 3.6 BPM, but hardly because it looks ahead.** Applying the same filter twice while recording, without any look-ahead, recovers nearly all of that gain (3.5 BPM). Compared directly on the same windows, the difference forwards-and-backwards minus twice-forwards was −0.07 BPM at rest level (a range that includes zero: −0.38 to +0.24) and −0.25 BPM at overload level (−0.49 to −0.02; paired check by one of the reviewers of this read on the stored results). So nearly all of the benefit is the steeper filter, and the small remainder gives little reason to store the sound for filtering alone.
- **The handling of the ends of the stored stretch does not matter**; cutting off the first and last quarter or half second makes the result worse, because it shortens the stretch.
- **Springer's preparation helps more, mainly with the half-rate check and only at higher heart rates.** Widening its search from 120 to 200 BPM reduced its own mean error by 8.3 BPM at rest level and by 9.7 BPM at overload level. Against the method of the first part, the widened version without the half-rate check is 1.2 BPM better at rest level (range for the difference −3.7 to +1.4, which includes zero) and 5.3 BPM better at overload level (−8.0 to −2.2). With the half-rate check added it improves the public result by 6 to 10 BPM, mostly above 110 BPM, where it removes many of the one-third errors described above; below 70 BPM it is 7 to 11 BPM worse at rest level and 4 to 10 BPM worse at overload level. Its logarithmic loudness curve is one likely ingredient: a quick extra test (run after the first results, at rest level only) of forwards-and-backwards filtering at 1,000 values per second gave −3.7 BPM on its own and −6.1 BPM with the logarithmic curve, so the curve added about 2.4 BPM there.
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

*Estimated cost per variant on the ESP32-S3 (the first part's own count of the memory of its method came to about 8 kB; this count gives 7 kB). By processor time, all would fit at one update per second; whether the larger variants also fit in memory is open (the internal memory is shared with the rest of the firmware, and the cost of using the slower external memory was not measured). The audio path keeps priority, and the work can be spread over many 4 ms blocks. If the counting may use a tenth of one core, the method of the first part could update about 48 times per second, forwards-and-backwards filtering at 1,000 values per second about 20 times, the logarithmic curve about 5 times and the other whole-window variants 2 to 3 times.*

::callout{kind="finding"}
**By the estimated processor time, counting in non-real time is possible on the device; whether the larger variants fit in memory beside the firmware is open.** **Filtering forwards and backwards brings almost no gain of its own:** a steeper filter gives nearly the same improvement while recording, at almost no cost. Springer's preparation with a search up to 200 BPM and the half-rate check helped more (6 to 10 BPM), but it was only tried with look-ahead, it is worse at slow heart rates, and it helps less than the improved choice of the peak. Whether its logarithmic loudness curve also works without look-ahead, and together with the improved choice, was not tested. The published Springer code cannot be copied into the firmware as it is: its 120 BPM limit does not fit the planned range of 30 to 200 BPM [1], and its files carry a licence (GNU General Public License, version 3 or later, according to the file headers) that would bind the firmware.
::end

## Results: listening

The first three subsections are the first part of the study, on Nico's five recordings. The fourth tests the same candidates on public recordings with murmurs.

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

::figure{src="page/figures/shortlist_tradeoff.png" alt="Safe boost, estimated loudness and sound between beats for eight candidates" caption="The eight candidates prepared for listening: safe boost, estimated loudness against Raw at that boost, and how strong the sound between the beats is compared with the heart sounds (lower is cleaner). The \"25–150 Hz (BPM position)\" entry is the BPM filter as originally planned. The recommended 40–150 Hz filter is not in this figure; it was added to the listening samples in this version (largest safe boost +0.358 dB)." width="wide"}

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

### Do the candidates keep murmurs audible? (public murmur data)

Nico's recordings contain no murmur. The murmur collection [17] does: 178 patients with a murmur between the first and the second heart sound, and 695 without one. Murmurs after the second heart sound are too rare in the collection to judge (5 patients, 4 of whom also have a murmur between the heart sounds; described but not tested).

What "audible" and "distinguishable" mean in numbers was fixed before any result existed (decision of this study on 23 November 2026, following the project's notes on comparing filters [19]), with one exception named below. All measures are taken at the device output, for every filter on the same marked stretches of each beat, with one value per patient:

- **Murmur level (main measure):** how strong the stretch between the two heart sounds is at the output, weighted for the ear's sensitivity (A-weighting [9]), each candidate at its fixed boost from the first part of this study; given as the difference to no filter.
- **Murmur against heart sounds:** the energy of that stretch divided by the energy of the two heart sounds.
- **Murmur against the quiet part:** the average power of that stretch divided by the average power of the quiet stretch after the second heart sound (average, because the two stretches differ in length).
- **Telling murmur from no murmur:** how well the last two measures separate the patients with a murmur from those without, as a score: the chance that a patient with a murmur gets a higher value than a patient without one. It runs from 0 to 1; 0.5 is no better than chance, 1 is perfect. The figure calls this score by its technical name, area under the curve. Fixed in advance was the score built on the heart-sound measure; using the quiet-part measure as a second score was added afterwards and is exploratory, although it gives the higher scores. For patients with a murmur only recordings from places on the chest where the specialist had heard the murmur were used; for patients without a murmur, all their recordings. The scores therefore describe how well a known murmur stands out, not how well an unknown patient would be screened.

Each candidate was compared with no filter patient by patient (a paired test, with a correction for having run 48 tests at once). With this many patients even tiny differences pass such a test, so the size in dB is what counts.

| Candidate (boost used in the simulation) | Murmur level vs no filter (dB) | Murmur against quiet part vs no filter (dB) | Telling murmur from no murmur (heart-sound measure, fixed in advance) | Telling murmur from no murmur (quiet-part measure, exploratory) |
|---|---:|---:|---:|---:|
| No filter (Raw, −0.010 dB) | 0 | 0 | 0.53 | 0.79 |
| 40–800 Hz, gentle (design candidate, −0.236 dB) | −1.9 | +1.6 | 0.62 | 0.86 |
| **100–800 Hz, gentle (+5.975 dB)** | **+4.1** | **+3.0** | **0.70** | **0.90** |
| 100–800 Hz, steep (+7.200 dB) | +5.5 | +3.4 | 0.72 | 0.90 |
| 150–800 Hz, steep (+9.760 dB) | +7.7 | +3.2 | 0.70 | 0.88 |
| 60–800 Hz, very steep (+3.840 dB) | +2.2 | +3.1 | 0.71 | 0.91 |
| Above 80 Hz only (+3.460 dB) | +3.4 | +2.6 | 0.68 | 0.89 |
| 25–150 Hz (BPM filter as first planned, −1.843 dB) | −14.4 | −0.2 | 0.51 | 0.80 |
| 40–150 Hz (recommended BPM filter, +0.358 dB) | −12.3 | +0.7 | 0.57 | 0.85 |

*Murmur measures on the public murmur data at rest level (178 patients with a murmur, 695 without). The boosts are the largest safe values from the first part, as used in the simulation; a setting on the device would be rounded down (5.9 dB for the gentle 100–800 Hz filter). Differences are typical paired differences over the 178 patients; for the gentle 100–800 Hz filter the 95 % ranges are +3.9 to +4.3 dB (murmur level), +2.6 to +3.4 dB (quiet part) and +0.13 to +0.21 for the gain in the first score.*

::figure{src="page/figures/run2_murmur_separation.png" alt="Score for telling murmur from no murmur, per candidate, with ranges" caption="How well two simple measures tell patients with a murmur from patients without, after each candidate filter (0.5 = chance, 1 = perfect; bars: 95 % ranges). Candidates printed in grey were added for this comparison; they are not among the listening samples." width="wide"}

::figure{src="page/figures/run2_murmur_spectrum.png" alt="Strength against pitch of the stretch between the heart sounds, with and without murmur" caption="Where the murmur energy lies in the public recordings (after the model of our device input, before any filter): the stretch between the two heart sounds for patients without a murmur and with soft, medium and loud murmurs. Murmurs add energy from about 60 Hz upward. The recordings contain nothing above 2 kHz." width="wide"}

- **Of the six filters prepared for listening in the first part, the planned 40–800 Hz filter gave the lowest murmur level and the lowest score on the heart-sound measure**: the murmur comes out 1.9 dB quieter than without a filter, and it separates murmur from no murmur less well than every candidate with a higher lower edge. (Among the candidates added for this comparison, 40–400 Hz is weaker still: 5.2 dB quieter.)
- **Candidates with a lower edge of 80 to 150 Hz, together with the very steep 60–800 Hz filter, form the top group.** The murmur stands out better against the quiet part (+2.6 to +3.4 dB), and the scores for telling murmur from no murmur are highest (0.68 to 0.72 and 0.88 to 0.91). These two results hardly depend on the boost (for the gentle 100–800 Hz filter the first score is 0.696 without a boost and 0.701 with it). With their boost the murmur is also 2 to 8 dB stronger than without a filter. The tests fixed in advance compared each candidate with no filter, not the candidates with each other. Differences inside this group are small: for example the steep 100–800 Hz filter scores 0.016 higher than the gentle one on the heart-sound measure (0.010 to 0.021 when the same patients are re-drawn for both; a check by one of the reviewers of this read). Whether differences this small matter for listening is unknown.
- **The gain in murmur level is the boost, not the filter.** Without a boost every candidate with an upper edge at 800 Hz makes the murmur 1.6 to 2.0 dB quieter, mostly through that upper edge; "above 80 Hz only" costs 0.06 dB. The boost is possible only because a higher lower edge frees room, which is what the first part found on Nico's recordings.
- **The upper edge costs murmur level.** With the lower edge at 100 Hz (gentle, each at its own safe boost), the murmur level against no filter is +2.9 dB with an upper edge of 600 Hz, +4.1 dB with 800 Hz, +4.7 dB with 1 kHz, +5.7 dB with 2 kHz and +5.8 dB without an upper edge. The scores for telling murmur from no murmur do not change with it beyond their ranges (0.69 to 0.71). On Nico's recordings the upper edge hardly mattered, because they contain almost nothing above 150 Hz.
- **Soft and low-pitched murmurs are harder, and the two measures disagree on how hard.** After the gentle 100–800 Hz filter, the measure against the heart sounds separates loud murmurs (grade III or more) with a score of 0.94 and high-pitched ones with 0.97, but soft ones (grade I) only with 0.61, and low-pitched ones not at all (0.50; across all candidates 0.44 to 0.51, every range including chance). The measure against the quiet part does better there: 0.86 for soft and 0.82 for low-pitched murmurs.
- **The two BPM filters are poor choices by the murmur level** (12 to 14 dB quieter than no filter), although the murmur still stands apart from the quiet part in them (scores 0.80 and 0.85). Whether they are unusable is for listening to decide.
- One result is unexplained: the unweighted ratio of murmur to heart sounds falls for every filter (by 0.6 to 2.6 dB) although the score built on it rises.

The broad pattern was the same at the overload level, with the matched tone balance, and in two random halves of the patients. Details change: with the matched tone balance the gentle 100–800 Hz filter and "above 80 Hz only" swap places in murmur level (+3.1 against +3.3 dB instead of +4.1 against +3.4 dB).

::callout{kind="limitation"}
All filters were measured on the same marked stretches of each beat. A filter delays the sound slightly (the steep 100–800 Hz filter by up to 6 thousandths of a second at 100 Hz, the very steep 60–800 Hz filter by about 3.5), which moves a little heart-sound energy into the stretch counted as murmur and can flatter the steep filters in the measure against the heart sounds.

These are energy measures on other people's recordings, made with another sensor on children, far brighter than what our chain delivered on Nico's chest, and with nothing above 2 kHz. They show which filters keep murmur energy and let it stand out; they do not show what a listener hears through our earpieces. The boosts were found safe on Nico's five recordings only. The modelled public recordings are more peaky: at rest level almost every one (3,141 of 3,162) already touches full scale at the device input, so the output of the listening candidates overloads on 90 to 99 % of them even without any boost (99 % with no filter, 98 % with the planned 40–800 Hz filter, 97 % with the gentle 100–800 Hz filter, all at 0 dB) and, for the five listening candidates with a boost above zero, on 99.7 to 99.9 % with their boosts. Only the two narrow BPM filters stay mostly clear (the recommended 40–150 Hz filter overloads on 8 % with its boost). A setting that stays clear of overload on 99 % of these recordings would be a cut, not a boost: −4.2 dB for 40–800 Hz, −4.5 dB for the gentle and −5.6 dB for the steep 100–800 Hz filter. On these recordings a higher lower edge frees no room. These figures depend on how the loudness of the public data was set and are not a measurement of the device, but they show that "safe on five recordings" is not "safe", and that the gain in murmur level in the table rests on a boost the public recordings do not support.
::end

### Listen and compare

Use headphones: in Nico's recordings almost all energy lies below 150 Hz, which small loudspeakers of phones and laptops reproduce poorly (general experience, no source checked). Each player holds the same stretch of sound through nine candidates: the eight of the first version and, new in this version, the recommended BPM filter 40–150 Hz. Tap a row to switch while it plays. "Hide names" gives a blind comparison. The loudness on a computer is not the loudness of the device; compare the candidates with each other. A 20-millisecond fade at the start and end of each sample is not part of the device.

**Nico's recordings** (10 seconds each, through the real chest-piece, tube and microphone):

::audio-compare{excerpt="resting" variants="madeup,device,matched" title="At rest" note="Clean recording, about 80 beats per minute."}

::audio-compare{excerpt="elevated-clean" variants="madeup,device,matched" title="After exercise, no overload" note="About 100 beats per minute."}

::audio-compare{excerpt="elevated-overload" variants="madeup,device,matched" title="After exercise, repeated overload on the beats" note="The microphone path is overloaded on many beats here. Listen for which candidates make the distortion more or less noticeable."}

::audio-compare{excerpt="movement-artefact" variants="madeup,device,matched" title="At rest, with a movement" note="Contains a movement of the chest-piece: the case for \"too much other sound\"."}

**Public recordings with murmurs** (8 seconds each, from the murmur collection [17], passed through the model of our device input at rest level and then through the same simulated device; offered with the fixed boosts and at equal loudness only, without the version "as the device plays it today"). They are from children of about 1.1 m height and were chosen by a fixed rule before listening: the clearest example of its group, at the place on the chest where the murmur is heard best. These are not recordings made with our device: they are brighter than ours and contain nothing above 2 kHz. With the fixed boosts, some candidates overload the output on the two murmur samples (values cut off at full scale, out of 128,000 per sample, loud / soft murmur: 100–800 Hz gentle 71 / 46, 100–800 Hz steep 292 / 193, 150–800 Hz steep 804 / 693, above 80 Hz only 7 / 9, 60–800 Hz very steep 0 / 10; none in the sample without a murmur and none in the "same loudness" versions). This is the overload warning from the murmur results made audible. Each murmur sample starts with the filter switched on at its first value, so the first fraction of a second can sound different from the rest.

::audio-compare{excerpt="murmur-loud" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. On this public recording some boosted candidates overload the output (see the note above)." title="Loud murmur (grade III or more)" note="A harsh, high-pitched murmur that fills the whole stretch between the first and the second heart sound. Listen for which candidates keep the murmur clear; harshness in the boosted candidates can come from the overload described above and not from the filter (compare with the same-loudness versions)."}

::audio-compare{excerpt="murmur-soft" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. On this public recording some boosted candidates overload the output (see the note above)." title="Soft murmur (grade I)" note="The clearest grade I example in the collection, so easier to hear than a typical soft murmur."}

::audio-compare{excerpt="no-murmur-child" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. No candidate overloads the output on this sample (the highest peak stays 0.2 dB below full scale)." title="No murmur, child of similar size" note="For comparison: the same place on the chest as the loud murmur, without a murmur."}

::callout{kind="open"}
**The listening filter is not decided.** It is Nico's judgement by ear. A reasonable first candidate to check is still "100–800 Hz, gentle" with a fixed boost of 5.9 dB: on Nico's recordings it is 1.1 to 1.5 dB louder than Raw by two of the three estimates and 6.5 LU quieter by the third, and on the public murmur recordings it is in the top group for telling murmur from no murmur, with or without the boost. The 4.1 dB by which the murmur comes out stronger than Raw there is the boost itself, and with that boost the output overloads on 99.8 % of the modelled public recordings. The filter weakens sound at 50 Hz to about a quarter (−12.3 dB; with the boost, about half, −6.4 dB). Compare it against "40–800 Hz" and "above 80 Hz only" for whether it sounds too thin. If the planned 40–800 Hz filter sounds best, it cannot be boosted. The boost of 5.9 dB is safe on Nico's five recordings only.
::end

## Do the two data sources agree?

| Question | Own recordings (first part) | Public recordings (this version) | Verdict |
|---|---|---|---|
| Is a BPM filter needed at all? | Yes: without a filter 16 gross errors in 255 windows | Yes: no filter is 6.9 BPM worse than the recommended filter (33.5 against 26.6 BPM) | Agree |
| 40–150 Hz or the planned 25–150 Hz? | 40 Hz as a precaution; rested on one window, and equal once the counting method is improved | 40 Hz better by 4.4 BPM (3.3 to 5.5) against an ECG; by 2.8 BPM with the improved counting method (test half, not tested on its own) | Public recordings decide |
| Best lower edge? | 30 to 80 Hz equal; steep 60 Hz worst | At rest level the error falls up to 80 Hz; steep 60 Hz best | Differ |
| Does the filter design or the upper edge matter? | Not measurably on clean windows | Upper edge: no. Other designs 2 to 7 BPM worse than the planned one; the planned one applied twice 3.5 BPM better | Differ slightly |
| Is the counting method of the first part good? | 0.30 BPM, no gross error | Good sitting still (2.7 BPM), fails during exercise (26.6 BPM overall) | Differ |
| Ranking of the counting variants | final method > 8 Hz variant > half-rate check alone | half-rate check alone > 8 Hz variant > final method | Reversed |
| Was the sound-derived reference sound? | Could not be checked | 99.7 % within 2 BPM of the ECG where it called a window clean | Confirmed |
| Planned listening filter 40–800 Hz | No room for a boost; slightly quieter than no filter | Of the six filters prepared for listening, the lowest murmur level and the lowest score on the heart-sound measure | Agree |
| First listening candidate 100–800 Hz | Louder by two of three estimates, with its boost | In the top group for telling murmurs apart and for letting them stand out, with or without the boost | Agree |
| Order of candidates by estimated loudness | By A-weighting and by the hearing curve | Same order (agreement 0.98 on a scale from −1 to 1) | Agree |
| Order by broadcast loudness | Every filter quieter than no filter | Reversed (−0.93): boosted filters louder | Differ |
| Does the upper edge matter for listening? | Hardly | Yes: a higher upper edge keeps more murmur level | Differ |
| Is there room for a fixed boost? | Yes with a lower edge of 50 Hz or more (5.9 dB at 100 Hz), on the five recordings | No: the seven prepared candidates other than the two BPM filters (no filter and the six listening filters) overload on 90 to 99 % of the 3,162 modelled public recordings even without a boost (the gentle 100–800 Hz filter on 97 %, and on 99.8 % with its boost) | Differ |

*The main questions answered with each data source.*

Why they differ, where they do:

- **Heart rates and regularity.** The public recordings contain far more windows above 90 BPM (about three quarters) with very regular beats, which is exactly where the first part's counting method picks a wrong multiple. On Nico's recordings the first part's counting method gave no estimate at one third of the rate with the recommended 40–150 Hz filter, but it did with other filters (1 window with the planned 25–150 Hz filter, 2 with the steep 60–150 Hz filter, 4 without a filter). The public recordings showed how often the same error occurs with the recommended filter at high heart rates.
- **Tone balance.** The public recordings carry much more sound above 100 Hz and much less below 20 Hz than Nico's recordings. A higher or steeper lower edge therefore still leaves plenty of heart sound in the public recordings, while in Nico's recordings it cuts into the little there is. The same explains why the broadcast loudness measure, which gives low tones more weight than the other two estimates, reverses its order, and why the upper edge matters in the public recordings and not in Nico's.
- **Disturbances.** The gross errors of the first part came from a movement and an unsteady start, both strong below 20 Hz. The public recordings contain little below 20 Hz, so they do not test this; they test regular beats at high rates and exercise noise instead.
- **Peaks.** The public recordings are more peaky than Nico's (their loudest moments stand further above their average), so a loudness setting that matches the heart sounds makes them overload sooner.

::callout{kind="finding"}
**The recommended filters hold; the method around them changes.** The public recordings support the BPM filter 40–150 Hz over the planned 25–150 Hz with the first part's counting method and, by a smaller untested margin, with the improved one, while Nico's recordings no longer separate the two once the counting method is improved; Nico's recordings are what speaks against a steep 60 Hz edge. Both data sources support a listening filter with a lower edge near 100 Hz over the planned 40–800 Hz; the fixed boost that goes with it is supported by Nico's recordings only. What the public recordings change is the counting method (its choice of the peak must be replaced), the confidence in fixed boosts (they need a safety margin or a limiter, not a value found on five recordings), and the upper edge of the listening filter (800 Hz costs murmur level; 1 to 2 kHz is worth a listen).
::end

## What it means for the design

1. **BPM filter (P08):** 40–150 Hz, a 2nd-order lower edge and a 2nd-order upper edge (Butterworth; the design documents call these high-pass and low-pass), 10 multiplications per sound value. Against the planned 25–150 Hz it is supported by the public recordings (by 4.4 BPM with the first part's counting method, by an untested 2.8 BPM with the improved one); on Nico's recordings the two are equal once the counting method is improved. A lower edge of 50 Hz, or the same filter applied twice, is worth testing on the device; a steep lower edge at 60 Hz is not recommended, because it failed on the recordings made with our own chain.
2. **Counting method:** keep the loudness curve and the repeat-pattern search, but replace the choice of the peak. Starting point: let longer shifts count less, then take the shortest of a quarter, a third and half of the best shift whose peak is nearly as high (improved method of this version), and show a number only if it stands clear of rivals and agrees with the previous estimates. Open: a repair for slow heart rates, and a test of the logarithmic loudness curve without look-ahead.
3. **Real time is not required for counting, and so far not needed.** By the estimated processor time, the stored 8 seconds could be processed as a whole; whether the larger variants fit in memory beside the firmware is open. Filtering forwards and backwards brought almost no gain of its own (0.07 to 0.25 BPM over the same filter applied twice while recording); the loudness curve of the Springer method brought more, but only with look-ahead tested, and less than the improved choice of the peak, which works while recording.
4. **Listening filter (P08):** open until Nico has listened. Both data sources favour testing a lower edge near 100 Hz instead of the planned 40–800 Hz. Nico's five recordings allowed a boost of 5.9 dB with it. On the modelled public recordings the filter improved the score for telling murmur from no murmur without any boost (0.53 to 0.70), and 99.8 % of the recordings reached the output limit at the tested boost. The upper edge should become part of a later listening test (800 Hz, 1 kHz, 2 kHz), because 800 Hz costs murmur level in the public recordings; the samples on this page do not yet contain these variants. A fixed boost per switch position is a new design element; the firmware today can only make the sound smaller, never larger [5]. The boost needs a safety margin or a limiter: the room for it was found on five recordings, and the modelled public recordings, as their loudness was set here, leave no such room.
5. **Overload at the microphone** cannot be filtered away. In Nico's recordings it is driven by a slow swing below 20 Hz under the heart sounds. This points to the mechanical side (pressure, chest-piece, tube) or to the microphone's own low limit as the place to act, not the filters.
6. **The analysis keeps its own filter**, independent of the listening switch, as designed. The murmur data point the same way from the other side: the BPM filters make a murmur 12 to 14 dB quieter.

## Limitations

- **Own recordings:** one person, five recordings, one session, membrane side only, two chest positions. No murmurs, no other bodies, no clothing noise, no talking. In the movement of the first resting recording the raw signal contains straight ramps of about 35 thousandths of a second, which may be the microphone recovering from overload or values lost during capture; this was not investigated.
- **Public recordings are not our device.** Other sensors, other people (young men during exercise; children in the murmur collection), passed through a model of our device input that fits the loudness but not the tone balance. Nothing above 2 kHz in the murmur collection and nothing above 4 kHz in the collection with ECG. No correction for our chest-piece and tube, because no valid measurement of them exists where the heart sounds are.
- **The microphone model** comes from the datasheet; two of its values are not yet checked against the datasheet page, and the assumption that both of its low-pitch limits are simple first-order ones is the measurement project's.
- **Loudness of the public recordings in the model** was set to match Nico's recordings. Everything that depends on absolute loudness there (overload counts, safe boosts, the better heart-rate results at the overload level) describes the model, not the device.
- **Heart-rate reference.** For Nico's recordings it comes from the same sound (now checked against an ECG on public recordings and found reliable where it claimed to be). For the public recordings it is an ECG read by two methods that share their last step, so their close agreement shows that they find the same beats, not that each beat time is exact.
- **Windows overlap.** Consecutive 8-second windows share 7 seconds. In Nico's recordings only 35 windows do not overlap. For the public recordings the ranges were computed by re-drawing people, which accounts for this; they rest on 21 people (10 in the test half).
- **The counting methods were tuned on the data they were tested on in the first part**, and the improved method on half of one public collection. It has been tested on the other half and on Nico's recordings, not on any third source.
- **Murmur measures are energy measures.** They do not know what a murmur sounds like. One of the measures fixed in advance behaved in an unexplained way (it fell for every filter).
- Heart rates covered: 73 to 149 BPM in the own recordings, below 60 to about 200 BPM in the public ones.
- Processor load and memory are estimates. Nothing ran on the device. The loudness figures are estimates for an assumed listening level; the earpiece and the ear are not in the simulation. The digital-to-analogue converter [11] and the earpieces are treated as ideal.
- The half-rate check, and now the check for a third and a quarter, could wrongly raise the rate where the second heart sound is as loud as the first and falls halfway between two beats. At slow rates in the public recordings this happens.

## Next steps

1. Nico listens to the samples, including the murmur samples, and chooses the listening filter and its boost. A second set of samples with upper edges of 800 Hz, 1 kHz and 2 kHz should follow.
2. Repair the improved counting method for slow heart rates, try the logarithmic loudness curve without look-ahead, and test both on a third data source.
3. Record more sessions with our own chain and a pulse oximeter or ECG at the same time (as REQ-06 requires [7]), on several people, with other chest positions, movement and poor contact.
4. Do the planned second table measurement, so that the chest-piece and tube can enter the model with a valid curve.
5. Decide how to deal with overload at the microphone at high heart rates, and how much margin a fixed boost gets.
6. Write the filter and the counting method into the firmware and measure processor time and memory on the device.
7. Test the rule for invalid windows with deliberately bad signals (REQ-08 [7]).

## How this read was checked

The first version of this read was checked in three rounds by three independent reviewers (one model each from three providers: GPT Astra, Claude Fable, Gemini Neon), with final scores of 8, 9 and 9 out of 10.

This second version was checked in the same way on 23 November 2026: the reviewers compared the numbers with the result files (each checked several dozen to about a hundred), the method, the sources and the plainness of the language. Scores out of 10 in the first round: 8, 7 and 6. The reviewers found, among other things, that the first draft overstated three conclusions (that non-real-time counting brings no gain, that both data sources support the 40 Hz lower edge, and that the public murmur data confirm the boost), mixed numbers from the tuning and the test half, and described one figure wrongly. All findings marked as blocking were corrected in the text and figures. A second round with new reviewer sessions confirmed these corrections against the result files and scored 8, 8 and 8; what it still found were places where a correction had not been carried through everywhere, and small errors of scope (for example which candidates a statement covers). These were corrected as well. In a third and last round two reviewers again scored 8 and wrote that the page would be at 9 once two or three remaining sentences were replaced (a caveat missing in one design point, in the note at the listening samples and in one table cell, and a statement that held at one loudness level only); these sentences were replaced as they proposed, and the result was not reviewed again. The third reviewer (GPT Astra) could not take part in the last round because its provider's usage limit was reached, so it gave no score there. The target of 9 from every reviewer was therefore not formally reached.

Known open points:

- The table of the eight listening candidates and two figures of the first part do not yet show the ninth candidate (40–150 Hz), which is in the listening samples.
- The listening samples do not yet contain variants with a higher upper edge (1 kHz, 2 kHz).
- The audio players use a compressed, lossless sound format (FLAC) that was tested in one desktop browser (Chrome) only, not on a phone.
- The improved counting method is weaker at slow heart rates; this is not repaired.

::glossary

## Sources

::sources
[1] DigitalStethoscope project, system design: `Development/system/design/system/parameters.md` (P01, P05, P06, P08), `interfaces-and-behavior.md` (section "DSP and measurement design") and `shared-filter-signal-flow.puml`; filter roles decided on 13 November 2026 (`Development/system/planning/mvp-decisions-2026-11-13-delivery-and-filters.md`). Project documents and project decisions, repository state of commit b1c7fbb.
[2] TDK InvenSense, *INMP441 Omnidirectional Microphone with Bottom Port and I²S Digital Output*, DS-INMP441-00, revision 1.0, 2014. [Datasheet](https://www.farnell.com/datasheets/1824785.pdf), accessed 11 November 2026 according to the project's AUDIO design; not re-opened for this study.
[3] ISO 226:2003, *Acoustics — Normal equal-loudness-level contours*, International Organization for Standardization. Covers 20 Hz to 12.5 kHz. The falling sensitivity toward low tones is taken from this standard's contours as implemented in the study's script (60-phon contour, extended below 20 Hz by the script); the full text was not inspected for this study (unverified).
[4] DigitalStethoscope project, AUDIO design: `Development/system/design/AUDIO/interfaces-and-behavior.md` (sample rate 16,000 Hz, blocks of 64 values, sample format, volume as linear gain 0–100 % with saturation). Project document, commit b1c7fbb.
[5] DigitalStethoscope firmware, `Development/system/coding/app/L2_application/L2_AUDIO/audio_processing.c`, function `audio_applyVolume`, commit b1c7fbb.
[6] Espressif Systems, *ESP-DSP Library Benchmarks*, ESP32-S3 column, row `dsps_biquad_f32` (17,552 processor cycles per 1,024 values). [Benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html). Value taken from the project's thesis material (`thesis-material/03-grundlagen-technisch/04-dsp-filter.md`, register entry `esp_dsp_benchmarks`, access date not recorded there); one council reviewer re-opened the page on 23 November 2026 and found the same value. The processor speed of 240 MHz and the costs assumed for the other operations are assumptions of this study; the cost assumed for the larger calculations of the whole-window variants is taken from the same thesis material, where it is marked as still to be checked.
[7] DigitalStethoscope project, `Development/system/requirements/system-requirements.md`, REQ-06 and REQ-08. Project requirements.
[8] ANSI/AAMI EC13:2002, *Cardiac monitors, heart rate meters, and alarms*, Association for the Advancement of Medical Instrumentation. Cited from the project's source register (entry `ec13`); full text paywalled and not inspected.
[9] IEC 61672-1:2013, *Electroacoustics — Sound level meters — Part 1: Specifications* (A-weighting). Full text not inspected for this study; the weighting was implemented from its published formula and re-derived for 16,000 values per second.
[10] ITU-R BS.1770-4 (2015), *Algorithms to measure audio programme loudness and true-peak audio level*, International Telecommunication Union. Implemented from the recommendation's filter definition, re-derived for 16,000 values per second; a full-scale 997 Hz tone reads −2.97 LUFS instead of −3.01 LUFS (LUFS is the unit of this loudness measure).
[11] Texas Instruments, *PCM510xA 2.1 VRMS Audio Stereo DAC*, SLAS859C, 2015. [Datasheet](https://www.ti.com/lit/ds/symlink/pcm5102a.pdf), accessed 11 November 2026 according to the project's AUDIO design; not re-opened for this study.
[12] Own measurements and simulation of this study, 23 November 2026: recordings, scripts and result tables in `C:/Users/nicop/Desktop/heart-filter-study/` (`STATE.md`, `FINDINGS.md`; first part: `reference/`, `results/`, `listening/`; this version: `calibration/`, `reference-public/`, `results-public/`, `results-window/`, `listening-public/`). All numbers on this page without another source come from there.
[13] Own measurement, audio chain session of 22 November 2026: `C:/Users/nicop/audio-chain-measurements/2026-11-22/` (`notes.md`, `analysis/`, `photos/`); capture firmware built from commit b1c7fbb with the untracked chain-measurement files; method and code described in `Development/system/testing/AUDIO/chain-measurement/README.md` of the project repository (untracked at the time of this study).
[14] *Chain measurement of 22 November 2026: setup, results and the two independent reviews*, `chain-measurement-reviews.md` in the study folder, condensed on 23 November 2026 from the measurement thread and from two read-only reviews (by Claude Fable and by Gemini Neon, both 23 November 2026). The full review texts were not inspected for this study; this condensed record was.
[15] DigitalStethoscope project, `Development/system/testing/AUDIO/chain-measurement/microphone_model.py`: microphone model from the datasheet [2] (weakening of low pitches with half power at 60 Hz, a second limit of 3.7 Hz at 48,000 values per second scaled to the device's rate, usable range up to 0.423 times the number of values per second). According to that file, the 60 Hz value is checked against the project's datasheet record; the 3.7 Hz value and the usable range are not yet, and the simple (first-order) form of both limits is the project's assumption.
[16] A. Kazemnejad, P. Gordany, R. Sameni, *EPHNOGRAM: A Simultaneous Electrocardiogram and Phonocardiogram Database* (version 1.0.0), PhysioNet, 2021. [doi:10.13026/tjtq-5911](https://doi.org/10.13026/tjtq-5911), accessed 23 November 2026. Open Data Commons Attribution License v1.0 (the version number is stated on the dataset page; the licence file in the download carries none). 69 recordings downloaded and verified against the source's SHA-256 list; 66 used. Details on people, device and activities are from the dataset page and its spreadsheet. The source asks users to also cite its database article (A. Kazemnejad, P. Gordany, R. Sameni, "An open-access simultaneous electrocardiogram and phonocardiogram database," bioRxiv, 2021, doi:10.1101/2021.05.17.444563; title as listed on the dataset page, place of publication and DOI as found by one of the reviewers of this read), the toolbox used by its authors (R. Sameni, *The Open-Source Electrophysiological Toolbox (OSET)*, version 3.14, https://github.com/alphanumericslab/OSET; not used in this study), and: T. Pollard et al., "PhysioNet as a global platform for biomedical research," *Nature Health*, 2026, doi:10.1038/s44360-026-00096-z (cited as given on the dataset page; not inspected).
[17] J. Oliveira, F. Renna, P. Costa, M. Nogueira, A. C. Oliveira, A. Elola, C. Ferreira, A. Jorge, A. Bahrami Rad, M. Reyna, R. Sameni, G. Clifford, M. Coimbra, *The CirCor DigiScope Phonocardiogram Dataset* (version 1.0.3), PhysioNet, 2022. [doi:10.13026/tshs-mw03](https://doi.org/10.13026/tshs-mw03), accessed 23 November 2026. Open Data Commons Attribution License v1.0. 10,434 files downloaded and verified against the source's SHA-256 list. Collected in two screening campaigns in Northeast Brazil in 2014 and 2015; murmurs described by one specialist; the marks of the heart sounds come from three computer methods checked and corrected by a person (all according to the dataset page).
[18] J. Oliveira et al., "The CirCor DigiScope Dataset: From Murmur Detection to Murmur Classification," *IEEE Journal of Biomedical and Health Informatics*, vol. 26, no. 6, pp. 2524–2535, 2022, doi:10.1109/JBHI.2021.3137048. The article describing [17]; volume, pages and year as found in the publisher's record by one of the reviewers of this read on 23 November 2026; full text not inspected.
[19] DigitalStethoscope project, thesis material `thesis-material/08-evaluation/03-filtervergleich-statistik.md` (units A002, A003, A004, A009, A010, A017, A018, A019, U050: possible measures for murmurs, equal conditions for all filters, one common marking of the beats, paired tests with a correction for several tests). Project notes; the literature they cite was not re-opened for this study. The exact measures used here were fixed by this study before the analysis (recorded in `STATE.md`, decision R2-6).
[20] D. B. Springer, L. Tarassenko, G. D. Clifford, "Logistic Regression-HSMM-Based Heart Sound Segmentation," *IEEE Transactions on Biomedical Engineering*, vol. 63, no. 4, pp. 822–832, 2016, doi:10.1109/TBME.2015.2475278. Bibliographic data checked against the dblp index on 23 November 2026; the article is not freely available and was not read.
[21] D. Springer, *Logistic Regression-HSMM-based Heart Sound Segmentation* (program code, version 1.0), PhysioNet, 2019, doi:10.13026/vnt9-kf93 (year and DOI from the project page, as found by one of the reviewers of this read). [Project page](https://physionet.org/content/hss/1.0/), files downloaded 23 November 2026 and checked against the project's checksum list. The steps described on this page were read from the files `getHeartRateSchmidt.m`, `schmidt_spike_removal.m`, `Homomorphic_Envelope_with_Hilbert.m` and `default_Springer_HSMM_options.m`, and for the three combined loudness curves also from `getSpringerPCGFeatures.m`, `Hilbert_Envelope.m` and `get_PSD_feature_Springer_HMM.m` (file and line in `sources/springer-method-notes.md` of the study folder). Licence GNU General Public License version 3 or later according to the file headers; the project page lists GPL version 3 (seen by one of the reviewers; this study's own download of the licence file failed).
[22] DigitalStethoscope project, evaluation guide `preThesis/06-bringup-zephyr/EVAL-GUIDE.md`, row E04: provisional target of a mean error of at most 5 BPM with at least 90 % valid windows, defined there for clean test signals. Project document.
::end
