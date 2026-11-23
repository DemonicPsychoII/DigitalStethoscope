---
title: Which filters should the digital stethoscope use?
subtitle: A simulation study of the listening filter and the heart-rate filter, on five own heart recordings and two public collections (TICKET-189)
authors: Nico Friedrich, Technische Hochschule Augsburg. Analysis, code, figures and text were produced with AI assistance (Claude Fable 5.2 as lead, Claude Opus 5.5 for all code) and checked by independent AI reviewers; see Appendix A.
date: 23 November 2026
status: Version 4 (editorial revision of version 3, same results); listening judgement pending
watermark: Published by Claude-Fable-5.2 on behalf of Nico running in T3 Code through Claude Code.
---

::summary{title="Abstract"}
The digital stethoscope needs two filters: one for listening and one for counting the heart rate. Both were studied by simulating the device on five recordings of one person, on 29 hours of public heart sounds with an ECG, and on public recordings of 874 patients with and without heart murmurs. For counting, a gentle **40–150 Hz** filter is recommended: against the ECG it is 4.4 beats per minute (BPM) better than the planned 25–150 Hz filter with the original counting method (2.8 BPM with the improved one, not tested on its own); on Nico's recordings the two are equal once the counting method is improved. The original method was 0.30 BPM off on undisturbed stretches of Nico's recordings but 26.6 BPM off against the ECG: above about 90 BPM it often reports a third of the true rate. An improved method halves the error on people it was not tuned on (28.4 to 13.1 BPM) but doubles it below 70 BPM. For listening, a **100–800 Hz** filter separates murmur from no murmur better than the planned 40–800 Hz filter (score 0.70 against 0.62) and allowed a boost of 5.9 dB on Nico's recordings only; the modelled public recordings leave no room for it. The choice by ear is pending; nothing ran on the device.
::end

## 1 Introduction

The stethoscope picks up heart sounds with a microphone, processes them in a small computer (an ESP32-S3) and plays them into the earpieces. It also counts the heart rate. Two filters are still open in the design (parameter P08 [1]):

- the **listening filter** for the switch position "Murmur" (next to "Raw", which plays the microphone signal unchanged), and
- the **BPM filter**, which prepares the signal for counting the heart rate and can also be listened to in the switch position "BPM".

::term{name="filter"}
A filter lets one range of pitches through and weakens the rest. Pitch is measured in hertz (Hz): the number of vibrations per second. A filter described as "40–800 Hz" keeps sound between 40 and 800 vibrations per second. The lower limit is called the lower edge, the upper limit the upper edge. 1 kHz (kilohertz) is 1,000 Hz.
::end

::term{name="decibel (dB)"}
A measure for ratios. +6 dB means twice as large, +20 dB ten times as large, 0 dB no change, negative values smaller. A "boost of 6 dB" doubles every sound value; "a dip of 13 dB" means a pitch arrives at less than a quarter of its strength.
::end

The filters decide what the listener hears and whether the displayed heart rate can be trusted. A listening filter that is too wide wastes loudness on pitches the ear hardly hears; one that is too narrow removes the murmurs a doctor listens for. A BPM filter that lets movement through produces wrong heart rates. Nico set the goals on 23 November 2026 (project decisions):

1. Listening: the loudest result that is not distorted and does not carry too much other sound, judged by ear.
2. Heart rate: the filter that gives the most accurate count on the device, using the last 8 seconds of signal, updated once per second.
3. Try all filter variants worth trying, as close to the real device as possible.

This paper answers the questions by simulation, with two kinds of data. Nico's own recordings were made through the real chest-piece, tube and microphone, but they come from one person, contain no heart murmur and have no independent heart-rate reference. Two public collections add what they lack: heart sounds with an ECG at rest and during exercise, and heart sounds with labelled murmurs. The public recordings come from other sensors and other people, are much brighter than what our chain delivered on Nico's chest, and were only passed through a model of our device input. They test the filters and the counting method more widely; they do not show how our device sounds on those people.

Section 2 describes the device and what is known about its sound path, Section 3 the data, Section 4 the methods. Section 5 gives the results, Section 6 what they mean for the design, Section 7 the limitations and Section 8 the conclusion and next steps.

## 2 Device and audio chain

### 2.1 The signal path in the device

Sound reaches the microphone (INMP441 [2]) through the chest-piece and a tube. The firmware handles it at 16,000 values per second in blocks of 64 values (4 thousandths of a second, written 4 ms) [4]. From there the design has two paths (Figure 1). The listening path applies the filter selected by the switch, then the volume, then the output limit, and plays the result through a digital-to-analogue converter [11] into the earpieces. The heart-rate path always uses the BPM filter and takes its signal before the volume control, whatever the listener selects [1]. It is planned to cover 30 to 200 BPM [1].

::figure{src="page/figures/signal_chain.png" alt="Block diagram of the listening path and the heart-rate path" caption="Figure 1. The two paths in the device, as designed. The heart-rate path always uses the BPM filter and takes its signal before the volume control, whatever the listener selects [1]." width="wide"}

The volume and output-limit code exists in the firmware; it can only make the sound smaller, never larger [5]. The filter and the heart-rate code are still empty.

### 2.2 The chain measurement of 22 November 2026

One day before the heart recordings, the sound path of the device was measured on a table, without a patient (own measurement [13]). This section says what that measurement was, what came out, and what this study took from it and what it did not. It rests on a condensed record of the setup, its results and two independent reviews of it [14].

**What was measured, and how.** A headphone played a test tone that glides from low to high pitch (20 Hz to 8 kHz, four glides of 5 seconds, at two loudness settings). The device recorded it with a small capture program that stores the microphone signal unchanged, 16,000 values per second. From the recording, the computer works out how strongly each pitch arrives. Three arrangements were measured, each re-seated four times (Figure 2).

::figure{src="page/figures/run2_chain_measurement_setups.png" alt="Three arrangements side by side: ear cup over the bare microphone; ear cup over the membrane side of the chest-piece with tube and microphone; the same with the bell side" caption="Figure 2. The three arrangements of 22 November 2026. A: the microphone alone under the ear cup. B: the membrane side of the chest-piece under the ear cup, with the sound travelling through the tube to the microphone. C: the same with the bell side. Dividing B by A and C by A was meant to leave the chest-piece and tube alone, because headphone and microphone are in both and cancel. Dividing C by B compares bell and membrane directly and does not need A." width="wide"}

There was no calibrated measuring microphone and the sound reached the chest-piece through air, not through a body. The measurement can therefore only compare arrangements with each other; it cannot say how the chest-piece behaves on a chest.

**What came out.** Both reviews checked the calculation and found it correct: they recomputed the result files (agreement within 0.0005 dB) and recovered a known test system within 0.1 dB; the two loudness settings agree within 0.2 to 0.4 dB, so the chain behaved the same at both levels [14]. These results hold:

- **The tube leaves a fingerprint.** Both sides of the chest-piece show the same row of peaks at about 261, 572, 940, 1,313 and 1,705 Hz (within ±2 Hz of each other). This fits a tube of about 44 to 45 cm that favours certain pitches, like an organ pipe; the tube length is inferred, not measured [14].
- **Bell against membrane (C ÷ B):** in air, the two sides are nearly the same below 1 kHz. The membrane is 9 to 10 dB stronger around 1.7 to 2.5 kHz, the bell 3.5 to 13 dB stronger above 4.5 kHz.
- Both sides fall off steeply above about 5 kHz. This is the hardware, not the calculation.

And these do not hold (Figure 3):

- **Chest-piece alone (B ÷ A, C ÷ A) below about 400 Hz.** Arrangement A had a weakness of its own: a dip of about 13 dB at 220 Hz, caused by the ear cushion resting on the edge of the circuit board; it disappears when the cup is lifted. Dividing by A adds about 10 to 13 dB to the peak at about 250 Hz in both results.
- **Membrane side above about 5.5 kHz:** sound reached the microphone through the air 0.5 to 1 ms before the sound through the tube.
- The later seatings (after a pause of 68 minutes) were about 2 dB lower overall and up to 6 dB lower below 315 Hz, and A was not measured again at the end, so slow drift cannot be ruled out.
- The distortion figures are upper limits only, set by the background noise.

::figure{src="page/figures/run2_chain_measurement_valid_ranges.png" alt="Bands over a pitch axis from 20 Hz to 8 kHz showing where each measured quantity is usable" caption="Figure 3. Where the measurement of 22 November can be used, according to the two reviews [14], and where the heart sounds of Nico's recordings have most of their energy. The two do not overlap for the chest-piece-alone results: these are unusable exactly where the heart sounds are." width="wide"}

**What this study took from it.**

- **The capture program.** The heart recordings of 23 November were made with the capture firmware written for that measurement. Without it there would be no raw microphone recordings to simulate on.
- **The microphone model.** The measurement's description of the microphone from its datasheet [2][15] is the microphone step in this study's model of the device input for the public recordings (Section 4.2). Two of its values are still unchecked against the datasheet page and stay marked as such.
- **The limits of validity.** The reviews' finding that the chest-piece-alone results are unusable below about 400 Hz decided how the chest-piece is treated here.
- **The decision not to apply a chest-piece correction.** Nico's recordings already contain the real chest-piece, tube and microphone, so nothing must be added. For the public recordings a correction was considered and rejected: the only quantity that is reliable at the low pitches of the heart sounds, bell against membrane, describes the difference between the two sides of our chest-piece. It says nothing about the difference between our chest-piece and the unknown sensors of the public recordings, and those recordings were not made through our bell. This is a decision of this study.
- **No cross-check for the heart sounds.** Nico's recordings contain almost no energy above 150 Hz (0.06 % between 150 and 800 Hz). The measurement cannot explain this: where it is usable, above 400 Hz, the path through chest-piece and tube was stronger in air than the bare microphone at most pitches (membrane side, at the louder setting: by 1 to 11 dB between 400 Hz and 1 kHz and by up to about 20 dB near 2.5 kHz; from the result files of the session [13]), which neither supports nor contradicts the missing energy on a chest, where the chest-piece is loaded differently.

**What it did not take, and why.**

- No curve of the chest-piece or the tube enters any number in this paper. Below 400 Hz, where the heart sounds are, the measured curves are not valid.
- The tube's row of peaks (261 Hz and upward) was not built into the model for the public recordings. It lies above most heart-sound energy, and the public sensors have their own unknown tubes and housings.
- The distortion figures were not used, since they are upper limits only.

**What the planned second session would change.** A second session is planned but not done [14]: arrangement A rebuilt without its own dip and measured before and after each block, a sealed tube, checks for sound leaking past the chest-piece, a recording of silence, a test tone from 10 Hz, and corrected calculation details. If it yields a valid chest-piece and tube curve down to low pitches, the model of the device input could use a measured curve instead of the tone-balance matching used here. It would still be a comparison between arrangements, measured in air: how the chest-piece behaves on skin would remain open, and relating the overload at the microphone to a sound pressure would need a calibrated measuring microphone in addition.

## 3 Data

### 3.1 Nico's recordings

Five recordings of 60 seconds each were made on Nico's chest on 23 November 2026 (two chest positions) through the real chest-piece (membrane side), tube and microphone, with the capture firmware of the chain measurement, which stores the raw microphone signal (own measurement [12]; 16,000 values per second, each stored as a 24-bit number, which allows about 16.8 million steps; the firmware revision is not stored in the recording files). The first 2 seconds of each recording contain the start-up of the microphone and were discarded. Table 1 and Figure 4 give an overview.

| Recording | State | Heart rate range over 8-second windows (BPM) | Values at full scale | Energy below 20 Hz (%) | Clean windows of 51 |
|---|---:|---:|---:|---:|---:|
| Resting 1 | resting | 73–82 | 26 | 60.2 | 42 |
| Resting 2 | resting | 79–87 | 0 | 51.7 | 43 |
| After exercise 1 | after exercise | 86–129 | 16 | 48.6 | 39 |
| After exercise 2 | after exercise, overload on many beats | 119–144 | 473 | 32.0 | 51 |
| After exercise 3 | after exercise, overload in the first half | 116–149 | 457 | 38.2 | 51 |

*Table 1. Nico's five recordings. "Values at full scale" counts values at either limit of the number range of the microphone path. "Clean windows" are 8-second windows in which the reference heart rate is trustworthy (Section 4.5).*

::figure{src="page/figures/recordings_overview.png" alt="Five recordings over 60 seconds with their loudness and reference heart rate" caption="Figure 4. Nico's five recordings. After exercise the heart beats so strongly that the signal reaches the limit of the number range of the microphone path (full scale) on many beats. The heart-rate line follows the rate beat to beat, so it moves more than the 8-second ranges in Table 1." width="wide"}

::term{name="full scale and overload"}
A digital device stores each sound value as a number within a fixed range. Its limits, upward and downward, are called full scale. A sound that would need a number outside this range is cut off flat at the limit. This is overload (also called clipping), and it is heard as distortion.
::end

::figure{src="page/figures/beat_closeup.png" alt="Close-up of heart beats at rest and after exercise, with values cut off at the lower limit" caption="Figure 5. A heartbeat is heard as two sounds, a first and a second one (visible in these recordings as two bursts per beat). After exercise (right) some beats reach full scale (here at the lower limit) and are cut off there: the microphone path itself is overloaded, before any filter. No filter can repair this." width="wide"}

::callout{kind="finding"}
After exercise the real chain of chest-piece, tube and microphone overloads on about one beat in three (42 of 129 and 45 of 127 beats; 473 and 457 values at full scale in the two overloaded recordings; in the third recording after exercise only during the first 30 seconds; Figure 5). The device will see the same. Between 32 % and 60 % of the recorded energy lies below 20 Hz, the lowest pitch for which the standard hearing curves are defined [3]. This very low part uses up the number range (Figure 6).
::end

::figure{src="page/figures/where_the_energy_is.png" alt="Spectrum of the five recordings from 5 Hz to 8 kHz" caption="Figure 6. Where the energy of Nico's recordings sits. Most of it is at very low pitch; above about 1 kHz almost nothing is left." width="wide"}

### 3.2 Public collections

Two open collections of heart recordings from the research archive PhysioNet add what Nico's recordings lack (Table 2). Both were downloaded on 23 November 2026, and every file was checked against the checksum list of its source (a checksum is a fingerprint of a file that shows it arrived unchanged). In this paper they are called the ECG collection and the murmur collection.

| | ECG collection (EPHNOGRAM [16]) | Murmur collection (CirCor DigiScope [17], described in [18]) |
|---|---|---|
| What it adds | An independent heart-rate reference, at rest and during exercise | Murmurs, labelled by a specialist, with the parts of each beat marked |
| People | 24 healthy men, 23 to 29 years (as stated by the source) | 942 patients in the published part, mostly children; of the 874 used, 178 with a murmur between the heart sounds, 695 without, and 1 with a murmur only after the second heart sound |
| Recordings used | 66 of 69 (about 29 hours): 8 of 30 seconds at rest, the others of 30 minutes while sitting, lying, walking, on a treadmill or on a bicycle | 2,888 recordings of 874 patients, 58,156 fully marked heartbeats |
| Sensor | A stethoscope converted to digital, held by a chest strap during exercise | An electronic stethoscope in a screening clinic |
| Values per second | 8,000 | 4,000 |
| Reference | ECG, recorded at the same time | Murmur present or absent, loudness grade, pitch, and the start and end of each heart sound |
| Licence | Open Data Commons Attribution | Open Data Commons Attribution |

*Table 2. The two public collections as used. Counts are from the downloaded files; the source page of the murmur collection describes 1,568 patients, of which 942 are published.*

::term{name="ECG"}
An electrocardiogram records the electrical signal of the heart through electrodes on the skin. Each heartbeat shows as a sharp spike. Counting the spikes gives the heart rate independently of any sound.
::end

::term{name="heart murmur"}
An extra, noise-like sound between the two normal heart sounds, caused by turbulent blood flow. Some murmurs are harmless, some point to a heart defect. Doctors grade their loudness from I (very soft) upward; in the murmur collection the grades are I, II and "III or more".
::end

Three recordings of the ECG collection were left out: two are exact copies of other recordings filed under a different person, and one is marked by its authors as having no sound. This leaves 22 of the 24 people (the two copies were the only recordings filed under their two names), and one of the 22 has no window with a reliable ECG, so most numbers rest on 21 people. From the murmur collection, the 68 patients whose label is "unknown" were left out, and one recording with unreadable markings. Murmurs after the second heart sound are too rare in the collection to judge (5 patients, 4 of whom also have a murmur between the heart sounds; described but not tested).

## 4 Methods

### 4.1 Simulating the device

The simulation follows the firmware and the design documents step by step [1][4]: the same 16,000 values per second, the same blocks of 64 values, the same order of steps, and the firmware's own volume and output-limit code [5], copied so that it produces the same numbers bit for bit. All results in this paper use full volume (100 %).

Where the firmware is not written yet (the filter and the heart-rate code), the simulation uses what the device would realistically use. These are choices of this study, not measurements on the device:

- Filters are computed with numbers with a decimal point, stored in 32 bits, in small standard building blocks. How sharply a filter cuts off at its edges is called its order: a 2nd-order edge is called **gentle** here, a 4th-order edge **steep**. A filter with two gentle edges needs 10 multiplications per sound value.
- The heart rate is counted as the system design drafts it [1] (Section 4.4).

### 4.2 A model of the device input for the public recordings

The public recordings were made with other sensors. To test our filters on them as the device would see them, each recording was passed through a model of our device's input, built from what is known:

1. Convert to the device's 16,000 values per second.
2. Apply the microphone's behaviour from its datasheet [2][15]: it weakens very low pitches (to about 0.7 times at 60 Hz by the datasheet; two further values of the model are not yet checked against the datasheet).
3. Set the loudness so that the heart sounds are as strong as in Nico's recordings. Two settings: **rest level** (as strong as in his three recordings without lasting overload) and **overload level** (raised until one beat in three reaches full scale, as in his two overloaded recordings).
4. Add background noise where the public recording is quieter between the beats than our real chain was.
5. Cut off at full scale, as the real microphone path does.

After that, the simulation of the device is the same as for Nico's recordings. No correction for our chest-piece is applied (Section 2.2). As a variant, the tone balance of the public recordings was shifted towards that of Nico's recordings ("matched"); this stands in for all differences at once, sensor, chest-piece, tube and person, and cannot tell them apart.

Nico's recordings are the real chain on a real chest, so they are the yardstick for how close the model comes (Figure 7, Table 3).

::figure{src="page/figures/run2_public_vs_own_spectrum.png" alt="Strength against pitch for the own recordings and the two modelled public collections" caption="Figure 7. Tone balance of Nico's recordings and of the public recordings after the model of our device input. Each curve is drawn relative to its own strongest range, so only the shape counts." width="wide"}

| Measure | Nico's recordings | ECG collection | Murmur collection |
|---|---:|---:|---:|
| Heart-sound level at rest (dB below full scale) | 9.6 | 9.7 | 9.7 |
| Energy below 20 Hz (%) | 52 | 17 | 2.5 |
| Energy from 20 to 150 Hz (%) | 48 | 80 | 43 |
| Energy from 150 to 800 Hz (%) | 0.06 | 2.1 | 40 |
| Sound between the beats, relative to the heart sounds (dB) | −21 | −14 | −11 |

*Table 3. How close the modelled public recordings come to Nico's recordings at rest level, without the matching variant (medians over recordings; computed on 20 recordings of the ECG collection and 200 of the murmur collection).*

- **Loudness fits**: the heart-sound level at rest agrees within 0.1 dB, and at the overload level 34 % of all beats taken together reach full scale, as in Nico's recordings (the typical single recording reaches less: 23 % in the ECG collection and 20 % in the murmur collection). This was set on purpose, so it is not a test.
- **Tone balance does not fit.** The public recordings are much brighter: relative to Nico's recordings they carry 10 to 18 dB more between 100 Hz and 1 kHz (ECG collection) and 12 to 39 dB more (murmur collection). They carry far less below 20 Hz. The matching variant brings the ECG collection to within about 6 dB; the murmur collection stays 14 to 33 dB too bright above 200 Hz, because the correction was limited to 12 dB.
- **They are noisier between the beats** by 7 to 10 dB.
- **Overload works differently.** In Nico's overloaded recordings the cut-off beats ride on a slow swing below 20 Hz that uses up 0.2 to 0.4 of the number range; when the slow part is removed from the stored recordings afterwards, only 3 of 129 and 5 of 127 beats still reach full scale instead of 42 and 45 (own analysis; the recordings were already cut off when stored, so how far the true peaks went beyond full scale is unknown). The public recordings lack this slow part, so in the model the heart sounds themselves must be raised until they are cut off.

::callout{kind="limitation"}
The public recordings test the filters on other people, with murmurs and against an ECG. They do not show how our chain sounds on those people. Whether the difference in tone balance comes from the sensors, from our chest-piece and tube, or from the people (children in the murmur collection, one adult man in ours) cannot be separated with the data at hand.
::end

### 4.3 Filters

On Nico's recordings about 1,300 filters were tried for counting: five classic filter designs (Butterworth, Bessel, two kinds of Chebyshev, elliptic), a different kind of filter that works on a fixed number of past values (called FIR) and a version that first reduces the data rate; gentle to steep edges; lower edges from none to 100 Hz; upper edges from 60 Hz to none. On the ECG collection a smaller set was run: the lower edges of Table 8, upper edges from 100 to 800 Hz, a steep 60–150 Hz filter, the other designs with the same edges, and the 100–800 Hz gentle listening candidate.

For listening, nine candidates were prepared (Table 9): no filter, six listening filters and the two BPM filters. Filters are named by their band and steepness throughout, for example "40–150 Hz gentle". Four of them have a role:

- **25–150 Hz gentle**: the BPM filter as planned in the design [1];
- **40–150 Hz gentle**: the BPM filter recommended here;
- **40–800 Hz gentle**: the listening filter as planned in the design [1];
- **100–800 Hz gentle**: the first listening candidate of this study.

### 4.4 Counting the heart rate

The counting follows the draft in the system design [1]: filter, turn the signal into a slow loudness curve (100 values per second), keep the last 8 seconds (800 values, 3.2 kilobytes), and once per second search this curve for its repeat pattern.

::term{name="repeat pattern search (autocorrelation)"}
The loudness curve is compared with a shifted copy of itself. If shifting by 0.75 seconds makes the two copies match best, the heart beats every 0.75 seconds, which is 80 beats per minute. The method uses the whole 8 seconds, not single beats.
::end

Three versions of the method appear in this paper:

- The **first-draft method** simply takes the strongest repeat pattern (the highest peak of the search).
- The **original counting method** adds two changes: a smoother loudness curve (smoothed twice, slower than before) and a half-rate check (if there is a nearly equally strong pattern at half the spacing, take that). It was tuned on Nico's recordings, and all results on the roughly 1,300 filters use it. Two in-between variants are reported where they explain a result: the half-rate check alone, and an "8 Hz variant" (a less strongly smoothed curve, two steps at 8 Hz, plus the check).
- The **improved counting method** was built after the ECG collection showed that the original method often reports a third of the true rate (Section 5.1.3). It changes the choice of the peak in two ways: longer shifts count slightly less (in proportion to how much of the 8 seconds still overlaps), and after finding the highest peak the method looks at a quarter, a third and half of that shift and takes the shortest one whose peak is at least 0.6 times as high. A wrong number is also shown less often as valid: the estimate must stand clear of rival peaks and agree within 10 % with one of the two previous estimates. To keep this honest, the people of the ECG collection were split in two halves before anything was tuned: all settings were chosen on 11 people and then tested once on the other 10.

Labels inside some figures differ from the text: "final method" or "method of the first part" is the original counting method, "own recordings" are Nico's recordings, "public recordings" the public collections, "Raw" is no filter, and "design candidate" is a filter as planned in the design.

All three versions only use the past (the device cannot look ahead). The cost of the original method was estimated, not measured: about half a percent of one processor core and about 8 kilobytes of memory. The filter part of this estimate uses the published speed of the processor's filter routine [6]; the larger part (loudness curve and pattern search) uses assumed costs per operation without a source. The extra cost of the improved method is below 1 % of the counting work and about 2 to 3 kilobytes of memory (estimate). A measurement on the device is still needed.

Because the count works on a stored stretch of 8 seconds, it does not have to be done in real time. Nico asked for this to be explored (23 November 2026). The planned design keeps only the loudness curve in memory (800 values); keeping the sound itself as well is possible and costs extra memory (Table 12). The counting path could then work on the whole stored stretch at once and look "ahead" inside it, which a filter that handles each value as it arrives cannot. Listening is not affected: the sound for the ear must stay in real time. Two ideas were tried, on the same 8-second windows:

- **Filtering forwards and backwards.** Running a filter over the stored stretch once forwards and once backwards cancels the small delay that a filter gives to different pitches, and makes its edges twice as steep.
- **The method of Springer, Tarassenko and Clifford [20].** A widely used research method for marking the heart sounds. Its openly published program code [21] was read for this study (the article itself is not freely available and was not read; the code was not run). Before it marks anything, the code prepares the sound and estimates the heart rate: a filter from 25 to 400 Hz run forwards and backwards, removal of loud clicks, a loudness curve taken from the *logarithm* of the signal (which makes loud and soft beats more alike), and a repeat-pattern search that, unlike the one of the original method, lets longer shifts count less, but only looks between 0.5 and 2 seconds, so that it cannot report more than 120 BPM. Its second half, a statistical model that marks each heart sound, was not implemented: it needs trained values this study does not have.

### 4.5 Reference heart rates

**Nico's recordings: a reference derived from the sound.**

::callout{kind="limitation"}
For Nico's recordings there was no independent heart-rate sensor: no ECG, watch or pulse oximeter. The reference was derived from the recordings themselves. It is weaker than an ECG. The method was checked against an ECG on the ECG collection (Section 5.1.2).
::end

The reference was computed afterwards, with methods that may look at the whole recording at once, which the device cannot. Three different methods marked every heartbeat: one follows the loudness peaks, one follows changes in the sound's pitch content, one searches for the average beat shape. A beat counts as certain if at least two methods agree within 0.06 seconds; five beats are marked as uncertain, two of them kept from a single method to fill a gap. For each 8-second window the reference rate is the average rate of the whole beats inside it.

- 226 of 255 windows are called **clean windows**: they contain no detected disturbance, no uncertain or missing beat, and the three methods differ by no more than 3 BPM. In these windows the methods actually differ by at most 1.8 BPM. This is a measure of how well the methods agree, not a proof of accuracy.
- The other 29 windows have an uncertain reference. 25 of them contain a detected disturbance (a movement, a rubbing noise or the unsteady start of a recording); 4 contain no detected disturbance but one uncertain beat near the end of a recording. They are kept and reported separately ("all windows" means all 255), because a real examination has such moments too. Errors there are differences from an uncertain value. For short, they are called **disturbed windows**.
- A check on the average beat shape shows two sounds per cycle in every recording, so the reference did not count half or double the rate.

The reference has three weaknesses beyond the missing sensor. All three methods listen to the same sound: a beat that cannot be heard, or a noise that sounds like a beat, can mislead all three together, and the third method learns its beat shape from beats the first two agree on. The beat marks are placed using the 25–150 Hz range, the same range as the planned BPM filter, so the reference is not fully independent of the filters being tested. And disturbances are detected partly by strong energy between 3 and 20 Hz, with limits set by looking at these five recordings, so it is partly built in that filters letting those low pitches through do worse in disturbed windows.

**ECG collection: the ECG.** The ECG heart rate was computed by two different spike-finding methods; an 8-second window counts as a **reliable window** where both find the same beats and the beat spacing is plausible (87,807 of 103,927 windows, 22 people; one of them has no reliable window).

### 4.6 Error measures for the heart rate

"Mean error" always means the average size of the difference from the reference, so that too-high and too-low values cannot cancel. A "gross error" means more than 20 % off, for example half or a third of the true rate, or a rate far too high during a movement.

The project requires the result of each heart session of at least 15 seconds to be within ±5 BPM or ±10 % of a reference device (requirement REQ-06 [7]). This study borrows that tolerance for single 8-second windows and reads it as "whichever is larger"; that reading is this study's. "Within tolerance" refers to it. The same numbers are reported for the standard for ECG heart-rate meters, ANSI/AAMI EC13, which does not apply to stethoscopes and is cited from the project's source register without inspection of the full text [8]. The project's provisional acceptance target is a mean error of at most 5 BPM with at least 90 % of windows valid; the project defines it for clean test signals [22].

### 4.7 Listening measures

**Room for a boost.** For each candidate the largest fixed boost was computed that never overloads the output on any of Nico's five recordings at full volume ("largest safe boost").

**Estimated loudness.** How loud a sound seems depends on pitch: hearing is much less sensitive to low tones [3]. Three standard estimates of loudness were computed, none of which replaces listening: a curve of equal loudness (ISO 226 [3]), "A-weighting", the correction for pitch that sound level meters apply (IEC 61672-1 [9]), and the loudness measure of broadcasting (ITU-R BS.1770-4 [10]). Also computed: how strong the sound between the beats is compared with the heart sounds, and the "after-ring", how long the filter keeps sounding after a short click (until it has faded to one hundredth); a long after-ring can blur the two heart sounds. The after-ring measure was defined by this study.

**Murmur measures.** What "audible" and "distinguishable" mean in numbers was fixed before any result existed (decision of this study on 23 November 2026, following the project's notes on comparing filters [19]), with one exception named below. All measures are taken at the device output, for every filter on the same marked stretches of each beat, with one value per patient:

- **Murmur level (main measure):** how strong the stretch between the two heart sounds is at the output, weighted for the ear's sensitivity (A-weighting [9]), each candidate at its largest safe boost; given as the difference to no filter.
- **Murmur against heart sounds:** the energy of that stretch divided by the energy of the two heart sounds.
- **Murmur against the quiet part:** the average power of that stretch divided by the average power of the quiet stretch after the second heart sound (average, because the two stretches differ in length).
- **Telling murmur from no murmur:** how well the last two measures separate the patients with a murmur from those without, as a score: the chance that a patient with a murmur gets a higher value than a patient without one. It runs from 0 to 1; 0.5 is no better than chance, 1 is perfect. Figure 22 calls this score by its technical name, area under the curve. Fixed in advance was the score built on the heart-sound measure; using the quiet-part measure as a second score was added afterwards and is exploratory, although it gives the higher scores. For patients with a murmur only recordings from places on the chest where the specialist had heard the murmur were used; for patients without a murmur, all their recordings. The scores therefore describe how well a known murmur stands out, not how well an unknown patient would be screened.

### 4.8 Statistics

- **Nico's recordings.** Consecutive 8-second windows share 7 seconds, so only 35 of the 255 windows do not overlap. Whether a filter can be told apart from the best-ranked one was judged by re-drawing blocks of 8 consecutive windows (95 % range of the difference in mean error).
- **ECG collection.** Unless stated otherwise, numbers are for the rest level and for reliable windows. The ranges in brackets are 95 % ranges obtained by re-drawing people, not windows, because the windows of one person are not independent.
- **Murmur collection.** Each candidate was compared with no filter patient by patient (a paired test, with a correction for having run 48 tests at once). With this many patients even tiny differences pass such a test, so the size in dB is what counts. The tests fixed in advance compared each candidate with no filter, not the candidates with each other.

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
- **Other filter designs and the upper edge.** Other designs with the same edges were 2 to 7 BPM worse than the planned gentle design (Butterworth 26.6 BPM; Bessel 28.5, Chebyshev 29.1, elliptic 29.1, the FIR candidate 34.0), and the upper edge made no difference (26.6 to 27.2 BPM for upper edges from 100 to 800 Hz, lower edge 40 Hz). At rest level the 100–800 Hz gentle filter was as good an input for counting as 40–150 Hz (26.8 BPM); at the overload level it was 6.1 BPM worse (26.3 against 20.2 BPM, range 3.8 to 8.4). That it is a poor input on Nico's recordings came from their low-pitched disturbances, which the ECG collection lacks; the overload level shows that the ECG collection does not clear it as an input for counting either.
- **The counting method matters far more than the filter.** Changing the filter moves the result on the ECG collection by a few BPM; changing the choice of the peak moves it by 15 BPM. The order of the counting variants is even reversed here: the half-rate check alone (23.1 BPM) beats the original method (26.6 BPM).

::callout{kind="finding"}
**Recommended BPM filter: 40–150 Hz gentle.** The evidence for it over the planned 25–150 Hz gentle filter comes from the ECG collection (better by 4.4 BPM with the original counting method and by 2.8 BPM with the improved one on the test half, a difference of two means that was not tested on its own); on Nico's recordings the two are equal once the counting method is improved. The ECG collection would favour a lower edge of 50 to 60 Hz, but a steep 60 Hz edge failed on Nico's recordings, the only ones made with our own chain, so 40 Hz remains the cautious choice, and 50 Hz is worth testing on the device. **The original counting method has to be replaced:** it must not take the highest peak of a fairly compared repeat-pattern search. The improved method is the new starting point; it still needs a repair for slow heart rates.
::end

::callout{kind="limitation"}
The ECG collection was recorded with a sensor strapped to the chest of young men while they walked, ran and cycled; four in five windows are from exercise. A stethoscope is held on a patient at rest. The numbers during exercise therefore say more about the counting method's weak spots than about everyday use, and they come from another sensor passed through a model of our device input. The improved method was tuned on half of the same collection; it has not seen any other data except Nico's five recordings.
::end

### 5.2 Listening

#### 5.2.1 A filter can make overload worse

Removing the very low part should free number range, which could then be used to make the rest louder. For clean recordings this works: on the clean resting recording the planned 40–800 Hz gentle filter would allow the sound to be made three times as large (9.6 dB). But the device needs one fixed setting for all cases, and the overloaded recordings spoil it.

::figure{src="page/figures/overshoot_explained.png" alt="A quarter of a second of signal before and after two filters" caption="Figure 18. The moment that limits the planned listening filter: a movement of the chest-piece in the first resting recording (39.9 s). Top: the microphone signal, which touches full scale (6 values). Middle: after the 40–800 Hz gentle filter it swings to 1.03 times full scale, so the output cuts it off. Bottom: with a 100 Hz lower edge it reaches only 0.45 times full scale." width="wide"}

A filter does not only make things smaller. When it removes the slow part of a signal that sits close to full scale, the fast part that remains swings around zero and can reach further than the original did (Figure 18). Two events set the limit in Nico's recordings: the movement shown in Figure 18, and the cut-off beats after exercise. Leaving the movement out, the planned filter would have +0.208 dB of room instead of −0.236 dB, limited by the overloaded beats, so the finding does not depend on that one movement.

::figure{src="page/figures/headroom_gain.png" alt="Largest safe fixed boost against the lower band edge" caption="Figure 19. The largest safe boost on Nico's five recordings against the lower edge of the filter. Below 0 dB the filtered sound overloads sooner than the unfiltered one." width="wide"}

::callout{kind="finding"}
With a lower edge of 40 Hz or less, the filter output overloads sooner than no filter at full volume (107 of 109 such candidates). The planned 40–800 Hz gentle filter has −0.236 dB of room. Room for a boost appears from about 50 Hz and grows quickly (Figure 19): 3.465 dB at 80 Hz, 5.975 dB at 100 Hz (so a setting of 5.9 dB is safe and 6.0 dB is not) and 8.363 dB at 150 Hz (gentle edges, upper edge 800 Hz). For this gentle filter the upper edge hardly changes this up to a lower edge of 100 Hz and changes it by about 2 dB at 150 Hz; for the steep filter the upper edge already matters at 100 Hz (about 3 dB).
::end

#### 5.2.2 Louder, but thinner

Table 9 and Figure 20 give the listening measures of Section 4.7 for the candidates, Figure 21 which pitches each candidate lets through.

::figure{src="page/figures/shortlist_tradeoff.png" alt="Safe boost, estimated loudness and sound between beats for the eight candidates measured on Nico's recordings" caption="Figure 20. The eight candidates whose loudness was measured on Nico's recordings: largest safe boost, estimated loudness against no filter at that boost, and how strong the sound between the beats is compared with the heart sounds (lower is cleaner). The ninth candidate, the recommended BPM filter 40–150 Hz gentle, is not shown: it was not part of the measured set; its largest safe boost is +0.358 dB, and its loudness was not measured." width="wide"}

| Filter | Largest safe boost (dB) | Loudness vs no filter, hearing-curve estimate (dB) | Loudness vs no filter, A-weighted (dB) | Sound between beats vs heart sounds (dB) | After-ring (ms) | Multiplications per sound value |
|---|---:|---:|---:|---:|---:|---:|
| No filter | −0.010 | 0.0 | 0.0 | −14.9 | 2.2 | 0 |
| 40–800 Hz gentle (planned listening filter) | −0.236 | −1.5 | −1.7 | −14.3 | 16.8 | 10 |
| 100–800 Hz gentle (first listening candidate) | +5.975 | +1.5 | +1.1 | −11.8 | 9.8 | 10 |
| 100–800 Hz steep | +7.200 | +2.5 | +2.0 | −11.1 | 17.1 | 20 |
| 150–800 Hz steep | +9.760 | +3.4 | +2.8 | −9.9 | 12.2 | 20 |
| 60–800 Hz very steep (elliptic) | +3.840 | +1.1 | +0.8 | −13.1 | 42.7 | 20 |
| Above 80 Hz only | +3.460 | +0.5 | +0.4 | −12.7 | 9.0 | 5 |
| 25–150 Hz gentle (planned BPM filter) | −1.843 | −3.9 | −3.9 | −17.8 | 37.3 | 10 |
| 40–150 Hz gentle (recommended BPM filter) | +0.358 | not measured | not measured | not measured | not measured | 10 |

*Table 9. The nine listening candidates on Nico's recordings. The largest safe boost is given as computed, to 0.001 dB; a setting on the device must be rounded down (for example 5.9 dB, not 6.0 dB; Figure 20 shows values rounded down). It is slightly negative even for no filter, because the rule allows no output value at the limit and the recordings themselves contain such values. Loudness is compared with no filter, each at its own largest safe boost. The 40–150 Hz gentle filter was not part of the measured set; only its boost was determined.*

- By the first two estimates, the planned 40–800 Hz gentle filter ends up slightly **quieter** than no filter (about −1.5 dB), the 100–800 Hz gentle filter with its boost 1.1 to 1.5 dB louder, the 100–800 Hz steep filter 2.0 to 2.5 dB louder, and the 150–800 Hz steep filter about 3 dB louder. These are small gains for a boost of 6 to 10 dB, because the boost mostly replaces low tones that the filter removed.
- The third estimate (broadcast loudness) disagrees: it counts low tones more and rates every filtered version quieter than no filter (the 100–800 Hz gentle filter by 6.5 LU, the unit for differences in this loudness measure). The estimates do not settle the question.
- Raising the lower edge makes the sound between the beats relatively stronger (from −14.9 dB for no filter to −11.8 dB for the 100–800 Hz gentle filter and −9.9 dB for the 150–800 Hz steep filter): the heart sounds lose more than the background does.
- With the lower edge at 40 Hz (gentle filter) the upper edge matters little: between upper edges of 200 Hz and none the hearing-curve estimate changes by 1.2 dB and the A-weighted estimate by 1.3 dB. With a lower edge of 100 Hz the upper edge matters more (up to about 2.9 dB by the hearing-curve estimate). Averaged over the recordings, less than 2.4 % of the energy of any candidate lies above 1 kHz; in a single recording it reaches 8.2 %.

::figure{src="page/figures/shortlist_responses.png" alt="Which pitches each of the nine candidates lets through" caption="Figure 21. Which pitches each of the nine candidates lets through (0 dB = unchanged, −20 dB = one tenth)." width="wide"}

#### 5.2.3 Murmurs (murmur collection)

Nico's recordings contain no murmur. The murmur collection does: 178 patients with a murmur between the first and the second heart sound, and 695 without one. Table 10 gives the murmur measures of Section 4.7.

| Candidate (boost used in the simulation) | Murmur level vs no filter (dB) | Murmur against quiet part vs no filter (dB) | Telling murmur from no murmur (heart-sound measure, fixed in advance) | Telling murmur from no murmur (quiet-part measure, exploratory) |
|---|---:|---:|---:|---:|
| No filter (−0.010 dB) | 0 | 0 | 0.53 | 0.79 |
| 40–800 Hz gentle (planned listening filter, −0.236 dB) | −1.9 | +1.6 | 0.62 | 0.86 |
| **100–800 Hz gentle (first listening candidate, +5.975 dB)** | **+4.1** | **+3.0** | **0.70** | **0.90** |
| 100–800 Hz steep (+7.200 dB) | +5.5 | +3.4 | 0.72 | 0.90 |
| 150–800 Hz steep (+9.760 dB) | +7.7 | +3.2 | 0.70 | 0.88 |
| 60–800 Hz very steep (+3.840 dB) | +2.2 | +3.1 | 0.71 | 0.91 |
| Above 80 Hz only (+3.460 dB) | +3.4 | +2.6 | 0.68 | 0.89 |
| 25–150 Hz gentle (planned BPM filter, −1.843 dB) | −14.4 | −0.2 | 0.51 | 0.80 |
| 40–150 Hz gentle (recommended BPM filter, +0.358 dB) | −12.3 | +0.7 | 0.57 | 0.85 |

*Table 10. Murmur measures on the murmur collection at rest level (178 patients with a murmur, 695 without). The boosts are the largest safe boosts on Nico's recordings (Table 9), as used in the simulation; a setting on the device would be rounded down (5.9 dB for the 100–800 Hz gentle filter). Differences are typical paired differences over the 178 patients; for the 100–800 Hz gentle filter the 95 % ranges are +3.9 to +4.3 dB (murmur level), +2.6 to +3.4 dB (quiet part) and +0.13 to +0.21 for the gain in the first score.*

::figure{src="page/figures/run2_murmur_separation.png" alt="Score for telling murmur from no murmur, per candidate, with ranges" caption="Figure 22. How well two simple measures tell patients with a murmur from patients without, after each candidate filter (0.5 = chance, 1 = perfect; bars: 95 % ranges). Candidates printed in grey were added for this comparison; they are not among the listening samples." width="wide"}

::figure{src="page/figures/run2_murmur_spectrum.png" alt="Strength against pitch of the stretch between the heart sounds, with and without murmur" caption="Figure 23. Where the murmur energy lies in the murmur collection (after the model of our device input, before any filter): the stretch between the two heart sounds for patients without a murmur and with soft, medium and loud murmurs. Murmurs add energy from about 60 Hz upward. The recordings contain nothing above 2 kHz." width="wide"}

- **Of the six listening filters, the planned 40–800 Hz gentle filter gave the lowest murmur level and the lowest score on the heart-sound measure** (Table 10, Figure 22): the murmur comes out 1.9 dB quieter than without a filter, and it separates murmur from no murmur less well than every candidate with a higher lower edge. (Among the candidates added for this comparison, 40–400 Hz is weaker still: 5.2 dB quieter.)
- **Candidates with a lower edge of 80 to 150 Hz, together with the 60–800 Hz very steep filter, form the top group.** The murmur stands out better against the quiet part (+2.6 to +3.4 dB), and the scores for telling murmur from no murmur are highest (0.68 to 0.72 and 0.88 to 0.91). These two results hardly depend on the boost (for the 100–800 Hz gentle filter the first score is 0.696 without a boost and 0.701 with it). With their boost the murmur is also 2 to 8 dB stronger than without a filter. Differences inside this group are small: for example the 100–800 Hz steep filter scores 0.016 higher than the gentle one on the heart-sound measure (0.010 to 0.021 when the same patients are re-drawn for both; a check by one of the reviewers of version 3). Whether differences this small matter for listening is unknown.
- **The gain in murmur level is the boost, not the filter.** Without a boost every candidate with an upper edge at 800 Hz makes the murmur 1.6 to 2.0 dB quieter, mostly through that upper edge; "above 80 Hz only" costs 0.06 dB. The boost is possible only because a higher lower edge frees room, which is what Section 5.2.1 found on Nico's recordings.
- **The upper edge costs murmur level.** With the lower edge at 100 Hz (gentle, each at its own largest safe boost), the murmur level against no filter is +2.9 dB with an upper edge of 600 Hz, +4.1 dB with 800 Hz, +4.7 dB with 1 kHz, +5.7 dB with 2 kHz and +5.8 dB without an upper edge. The scores for telling murmur from no murmur do not change with it beyond their ranges (0.69 to 0.71). On Nico's recordings the upper edge hardly mattered, because they contain almost nothing above 150 Hz. Murmurs add energy from about 60 Hz upward (Figure 23).
- **Soft and low-pitched murmurs are harder, and the two measures disagree on how hard.** After the 100–800 Hz gentle filter, the measure against the heart sounds separates loud murmurs (grade III or more) with a score of 0.94 and high-pitched ones with 0.97, but soft ones (grade I) only with 0.61, and low-pitched ones not at all (0.50; across all candidates 0.44 to 0.51, every range including chance). The measure against the quiet part does better there: 0.86 for soft and 0.82 for low-pitched murmurs.
- **The two BPM filters are poor choices by the murmur level** (12 to 14 dB quieter than no filter), although the murmur still stands apart from the quiet part in them (scores 0.80 and 0.85). Whether they are unusable is for listening to decide.
- One result is unexplained: the unweighted ratio of murmur to heart sounds falls for every filter (by 0.6 to 2.6 dB) although the score built on it rises.

The broad pattern was the same at the overload level, with the matched tone balance, and in two random halves of the patients. Details change: with the matched tone balance the 100–800 Hz gentle filter and "above 80 Hz only" swap places in murmur level (+3.1 against +3.3 dB instead of +4.1 against +3.4 dB).

::callout{kind="limitation"}
All filters were measured on the same marked stretches of each beat. A filter delays the sound slightly (the 100–800 Hz steep filter by up to 6 ms at 100 Hz, the 60–800 Hz very steep filter by about 3.5), which moves a little heart-sound energy into the stretch counted as murmur and can flatter the steep filters in the measure against the heart sounds.

These are energy measures on other people's recordings, made with another sensor on children, far brighter than what our chain delivered on Nico's chest, and with nothing above 2 kHz. They show which filters keep murmur energy and let it stand out; they do not show what a listener hears through our earpieces. The boosts were found safe on Nico's five recordings only. The modelled recordings of the murmur collection are more peaky: at rest level almost every one (3,141 of 3,162) already touches full scale at the device input, so the output of the listening candidates overloads on 90 to 99 % of them even without any boost (99 % with no filter, 98 % with the 40–800 Hz gentle filter, 97 % with the 100–800 Hz gentle filter, all at 0 dB) and, for the five listening candidates with a boost above zero, on 99.7 to 99.9 % with their boosts. Only the two narrow BPM filters stay mostly clear (the 40–150 Hz gentle filter overloads on 8 % with its boost). A setting that stays clear of overload on 99 % of these recordings would be a cut, not a boost: −4.2 dB for 40–800 Hz gentle, −4.5 dB for 100–800 Hz gentle and −5.6 dB for 100–800 Hz steep. On these recordings a higher lower edge frees no room. These figures depend on how the loudness of the public recordings was set and are not a measurement of the device, but they show that "safe on five recordings" is not "safe", and that the gain in murmur level in Table 10 rests on a boost the murmur collection does not support.
::end

#### 5.2.4 Listen and compare

Use headphones: in Nico's recordings almost all energy lies below 150 Hz, which small loudspeakers of phones and laptops reproduce poorly (general experience, no source checked). Each player holds the same stretch of sound through the nine candidates of Table 9. Tap a row to switch while it plays. "Hide names" gives a blind comparison. The loudness on a computer is not the loudness of the device; compare the candidates with each other. A 20-millisecond fade at the start and end of each sample is not part of the device.

**Nico's recordings** (10 seconds each, through the real chest-piece, tube and microphone):

::audio-compare{excerpt="resting" variants="madeup,device,matched" title="At rest" note="Clean recording, about 80 beats per minute."}

::audio-compare{excerpt="elevated-clean" variants="madeup,device,matched" title="After exercise, no overload" note="About 100 beats per minute."}

::audio-compare{excerpt="elevated-overload" variants="madeup,device,matched" title="After exercise, repeated overload on the beats" note="The microphone path is overloaded on many beats here. Listen for which candidates make the distortion more or less noticeable."}

::audio-compare{excerpt="movement-artefact" variants="madeup,device,matched" title="At rest, with a movement" note="Contains a movement of the chest-piece: the case for \"too much other sound\"."}

**Murmur collection** (8 seconds each, passed through the model of our device input at rest level and then through the same simulated device; offered with the fixed boosts and at equal loudness only, without the version "as the device plays it today"). The samples are from children of about 1.1 m height and were chosen by a fixed rule before listening: the clearest example of its group, at the place on the chest where the murmur is heard best. These are not recordings made with our device: they are brighter than ours and contain nothing above 2 kHz. With the fixed boosts, some candidates overload the output on the two murmur samples (values cut off at full scale, out of 128,000 per sample, loud / soft murmur: 100–800 Hz gentle 71 / 46, 100–800 Hz steep 292 / 193, 150–800 Hz steep 804 / 693, above 80 Hz only 7 / 9, 60–800 Hz very steep 0 / 10; none in the sample without a murmur and none in the "same loudness" versions). This is the overload warning of Section 5.2.3 made audible. Each murmur sample starts with the filter switched on at its first value, so the first fraction of a second can sound different from the rest.

::audio-compare{excerpt="murmur-loud" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. On this public recording some boosted candidates overload the output (see the note above)." title="Loud murmur (grade III or more)" note="A harsh, high-pitched murmur that fills the whole stretch between the first and the second heart sound. Listen for which candidates keep the murmur clear; harshness in the boosted candidates can come from the overload described above and not from the filter (compare with the same-loudness versions)."}

::audio-compare{excerpt="murmur-soft" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. On this public recording some boosted candidates overload the output (see the note above)." title="Soft murmur (grade I)" note="The clearest grade I example in the collection, so easier to hear than a typical soft murmur."}

::audio-compare{excerpt="no-murmur-child" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico's five recordings. No candidate overloads the output on this sample (the highest peak stays 0.2 dB below full scale)." title="No murmur, child of similar size" note="For comparison: the same place on the chest as the loud murmur, without a murmur."}

::callout{kind="open"}
**The listening filter is not decided.** It is Nico's judgement by ear. A reasonable first candidate to check is 100–800 Hz gentle with a fixed boost of 5.9 dB: on Nico's recordings it is 1.1 to 1.5 dB louder than no filter by two of the three estimates and 6.5 LU quieter by the third, and on the murmur collection it is in the top group for telling murmur from no murmur, with or without the boost. The 4.1 dB by which the murmur comes out stronger than without a filter there is the boost itself, and with that boost the output overloads on 99.8 % of the modelled recordings of the murmur collection. The filter weakens sound at 50 Hz to about a quarter (−12.3 dB; with the boost, about half, −6.4 dB). Compare it against "40–800 Hz gentle" and "above 80 Hz only" for whether it sounds too thin. If the planned 40–800 Hz gentle filter sounds best, it cannot be boosted. The boost of 5.9 dB is safe on Nico's five recordings only.
::end

### 5.3 Counting on the whole stored 8 seconds

Table 11 and Figure 24 compare the whole-window variants of Section 4.4 with the original counting method.

::figure{src="page/figures/run2_window_methods_error.png" alt="Mean heart-rate error of fifteen counting variants on Nico's recordings and on the ECG collection at two loudness levels" caption="Figure 24. Counting on the whole stored 8 seconds against the original counting method (amber, dashed line), on Nico's recordings and on the ECG collection (every fourth window; lines: 95 % ranges over people)." width="wide"}

| Variant | Nico's recordings, clean / all windows (BPM) | ECG collection, change against the original method (BPM, rest level) | The same at overload level |
|---|---:|---:|---:|
| Original method: filter while recording, 40–150 Hz gentle | 0.30 / 0.35 | 0 (mean error 26.9) | 0 (mean error 20.2) |
| Same filter, forwards and backwards over the stored stretch | 0.33 / 0.39 | −3.6 (−4.5 to −2.7) | −1.2 (−2.1 to −0.5) |
| Same filter applied twice while recording (no look-ahead) | 0.32 / 0.38 | −3.5 (−4.5 to −2.6) | −1.0 (−1.9 to −0.2) |
| Springer's preparation as published (limit 120 BPM) | 21.0 / 19.2 | worse (+7.1) | worse (+4.4) |
| Springer's preparation, range widened to 200 BPM | 0.38 / 0.44 | −1.2 (−3.7 to +1.4) | −5.3 (−8.0 to −2.2) |
| Springer's preparation, range widened to 200 BPM, with half-rate check | 0.38 / 0.44 | −6.2 (−8.4 to −3.7) | −9.7 (−11.9 to −7.1) |
| Springer's three loudness curves combined, with half-rate check | 0.63 / 0.69 | −7.4 (−9.4 to −5.1) | −8.8 (−10.9 to −6.3) |

*Table 11. Whole-window variants against the original counting method. Nico's recordings: 226 clean and 255 windows. ECG collection: 21 people, 21,956 reliable windows (every fourth second), ranges are 95 % ranges over people. A negative change is an improvement.*

- **On Nico's recordings nothing beats the original method.** On all 255 windows the mean error was 0.35 BPM for the original method, 0.39 for forwards-and-backwards filtering, 0.44 for the widened Springer preparation with the half-rate check and 0.69 for the three combined loudness curves; differences of a tenth of a BPM cannot be told apart on five recordings. The Springer code as published fails there (19 BPM mean error), because two recordings are faster than its limit of 120 BPM.
- **On the ECG collection, filtering forwards and backwards helps by 3.6 BPM, but hardly because it looks ahead.** Applying the same filter twice while recording, without any look-ahead, recovers nearly all of that gain (3.5 BPM). Compared directly on the same windows, the difference forwards-and-backwards minus twice-forwards was −0.07 BPM at rest level (a range that includes zero: −0.38 to +0.24) and −0.25 BPM at overload level (−0.49 to −0.02; paired check by one of the reviewers of version 3 on the stored results). So nearly all of the benefit is the steeper filter, and the small remainder gives little reason to store the sound for filtering alone.
- **The handling of the ends of the stored stretch does not matter**; cutting off the first and last quarter or half second makes the result worse, because it shortens the stretch.
- **Springer's preparation helps more, mainly with the half-rate check and only at higher heart rates.** Widening its search from 120 to 200 BPM reduced its own mean error by 8.3 BPM at rest level and by 9.7 BPM at overload level. Against the original method, the widened version without the half-rate check is 1.2 BPM better at rest level (range for the difference −3.7 to +1.4, which includes zero) and 5.3 BPM better at overload level (−8.0 to −2.2). With the half-rate check added it improves the result on the ECG collection by 6 to 10 BPM, mostly above 110 BPM, where it removes many of the one-third errors of Section 5.1.3; below 70 BPM it is 7 to 11 BPM worse at rest level and 4 to 10 BPM worse at overload level. Its logarithmic loudness curve is one likely ingredient: a quick extra test (run after the first results, at rest level only) of forwards-and-backwards filtering at 1,000 values per second gave −3.7 BPM on its own and −6.1 BPM with the logarithmic curve, so the curve added about 2.4 BPM there.
- **All of these gains are smaller than that of the improved counting method** (about 15 BPM on the test half, without look-ahead; Section 5.1.4). The two were not combined, and the two comparisons use different sets of people and windows (all 21 people and every fourth window here, the 10 test people and every window there), so the sizes can only be compared roughly.
- **Storing less is enough.** Reducing the stored stretch from 16,000 to 1,000 values per second before the analysis gives the same error and needs 73 kilobytes instead of about 1 MB (Table 12).

Table 12 estimates what the variants would cost on the device (the same assumed costs per operation as in Section 4.4, not a measurement; the extra time for reaching the external memory is unknown and not included).

| Variant | Time per update (ms) | Share of one processor core at one update per second (%) | Memory |
|---|---:|---:|---:|
| Original method | 2.0 | 0.5 | 7 kB |
| Same filter applied twice while recording | 2.0 | 0.8 | 7 kB |
| Forwards and backwards, stored at 16,000 values per second | 49 | 4.9 | about 1 MB |
| Forwards and backwards, stored at 1,000 values per second | 5.0 | 0.6 | 73 kB |
| Logarithmic loudness curve, 1,000 values per second | 20 | 2.1 | 136 kB |
| Springer's preparation and heart rate | 37 | 3.8 | 254 kB (223 kB of it in the fast internal memory) |

*Table 12. Estimated cost per variant on the ESP32-S3 (the count of Section 4.4 for the memory of the original method came to about 8 kB; this count gives 7 kB). By processor time, all would fit at one update per second; whether the larger variants also fit in memory is open (the internal memory is shared with the rest of the firmware, and the cost of using the slower external memory was not measured). The audio path keeps priority, and the work can be spread over many 4 ms blocks. If the counting may use a tenth of one core, the original method could update about 48 times per second, forwards-and-backwards filtering at 1,000 values per second about 20 times, the logarithmic curve about 5 times and the other whole-window variants 2 to 3 times.*

::callout{kind="finding"}
**By the estimated processor time, counting in non-real time is possible on the device; whether the larger variants fit in memory beside the firmware is open.** **Filtering forwards and backwards brings almost no gain of its own:** a steeper filter gives nearly the same improvement while recording, at almost no cost. Springer's preparation with a search up to 200 BPM and the half-rate check helped more (6 to 10 BPM), but it was only tried with look-ahead, it is worse at slow heart rates, and it helps less than the improved counting method. Whether its logarithmic loudness curve also works without look-ahead, and together with the improved counting method, was not tested. The published Springer code cannot be copied into the firmware as it is: its 120 BPM limit does not fit the planned range of 30 to 200 BPM [1], and its files carry a licence (GNU General Public License, version 3 or later, according to the file headers) that would bind the firmware.
::end

### 5.4 Do the two data sources agree?

Table 13 answers the main questions with each data source.

| Question | Nico's recordings | Public collections | Verdict |
|---|---|---|---|
| Is a BPM filter needed at all? | Yes: without a filter 16 gross errors in 255 windows | Yes: no filter is 6.9 BPM worse than 40–150 Hz gentle (33.5 against 26.6 BPM) | Agree |
| 40–150 Hz or the planned 25–150 Hz? | 40 Hz as a precaution; rested on one window, and equal once the counting method is improved | 40 Hz better by 4.4 BPM (3.3 to 5.5) against an ECG; by 2.8 BPM with the improved counting method (test half, not tested on its own) | Public collections decide |
| Best lower edge? | 30 to 80 Hz equal; steep 60 Hz worst | At rest level the error falls up to 80 Hz; steep 60 Hz best | Differ |
| Does the filter design or the upper edge matter? | Not measurably on clean windows | Upper edge: no. Other designs 2 to 7 BPM worse than the planned one; the planned one applied twice 3.5 BPM better | Differ slightly |
| Is the original counting method good? | 0.30 BPM, no gross error | Good sitting still (2.7 BPM), fails during exercise (26.6 BPM overall) | Differ |
| Ranking of the counting variants | original method > 8 Hz variant > half-rate check alone | half-rate check alone > 8 Hz variant > original method | Reversed |
| Was the sound-derived reference sound? | Could not be checked | 99.7 % within 2 BPM of the ECG where it called a window clean | Confirmed |
| Planned listening filter 40–800 Hz gentle | No room for a boost; slightly quieter than no filter | Of the six listening filters, the lowest murmur level and the lowest score on the heart-sound measure | Agree |
| First listening candidate 100–800 Hz gentle | Louder by two of three estimates, with its boost | In the top group for telling murmurs apart and for letting them stand out, with or without the boost | Agree |
| Order of candidates by estimated loudness | By A-weighting and by the hearing curve | Same order (agreement 0.98 on a scale from −1 to 1) | Agree |
| Order by broadcast loudness | Every filter quieter than no filter | Reversed (−0.93): boosted filters louder | Differ |
| Does the upper edge matter for listening? | Hardly | Yes: a higher upper edge keeps more murmur level | Differ |
| Is there room for a fixed boost? | Yes with a lower edge of 50 Hz or more (5.9 dB at 100 Hz), on the five recordings | No: the seven candidates other than the two BPM filters (no filter and the six listening filters) overload on 90 to 99 % of the 3,162 modelled recordings of the murmur collection even without a boost (100–800 Hz gentle on 97 %, and on 99.8 % with its boost) | Differ |

*Table 13. The main questions answered with each data source.*

Why they differ, where they do:

- **Heart rates and regularity.** The ECG collection contains far more windows above 90 BPM (about three quarters) with very regular beats, which is exactly where the original counting method picks a wrong multiple. On Nico's recordings the original counting method gave no estimate at one third of the rate with the 40–150 Hz gentle filter, but it did with other filters (1 window with the planned 25–150 Hz gentle filter, 2 with the steep 60–150 Hz filter, 4 without a filter). The ECG collection showed how often the same error occurs with the 40–150 Hz gentle filter at high heart rates.
- **Tone balance.** The public recordings carry much more sound above 100 Hz and much less below 20 Hz than Nico's recordings. A higher or steeper lower edge therefore still leaves plenty of heart sound in the public recordings, while in Nico's recordings it cuts into the little there is. The same explains why the broadcast loudness measure, which gives low tones more weight than the other two estimates, reverses its order, and why the upper edge matters in the public recordings and not in Nico's.
- **Disturbances.** The gross errors on Nico's recordings came from a movement and an unsteady start, both strong below 20 Hz. The public recordings contain little below 20 Hz, so they do not test this; they test regular beats at high rates and exercise noise instead.
- **Peaks.** The public recordings are more peaky than Nico's (their loudest moments stand further above their average), so a loudness setting that matches the heart sounds makes them overload sooner.

## 6 Discussion

### 6.1 What the results mean

::callout{kind="finding"}
**The recommended filters hold; the method around them changes.** The ECG collection supports the BPM filter 40–150 Hz gentle over the planned 25–150 Hz gentle with the original counting method and, by a smaller untested margin, with the improved one, while Nico's recordings no longer separate the two once the counting method is improved; Nico's recordings are what speaks against a steep 60 Hz edge. Both data sources support a listening filter with a lower edge near 100 Hz over the planned 40–800 Hz gentle; the fixed boost that goes with it is supported by Nico's recordings only. What the public collections change is the counting method (its choice of the peak must be replaced), the confidence in fixed boosts (they need a safety margin or a limiter, not a value found on five recordings), and the upper edge of the listening filter (800 Hz costs murmur level; 1 to 2 kHz is worth a listen).
::end

For the heart rate, the filter is the smaller question. On clean signal almost every filter does equally well; disturbances and, on the ECG collection, a higher lower edge separate them by a few BPM. The choice of the peak in the repeat-pattern search moves the result by 15 BPM. The filter and the counting method therefore have to be fixed together, and the counting method is where the larger differences were found.

For listening, the numbers narrow the choice but cannot make it. A lower edge near 100 Hz frees room for a boost on Nico's recordings and lets murmurs stand out better in the murmur collection, at the price of relatively more sound between the beats and possibly a thinner sound. Whether that trade sounds right is for Nico's ear (Section 5.2.4).

### 6.2 Recommendations for the design

1. **BPM filter (P08):** 40–150 Hz, a 2nd-order lower edge and a 2nd-order upper edge (Butterworth; the design documents call these high-pass and low-pass), 10 multiplications per sound value. Against the planned 25–150 Hz it is supported by the ECG collection (by 4.4 BPM with the original counting method, by an untested 2.8 BPM with the improved one); on Nico's recordings the two are equal once the counting method is improved. A lower edge of 50 Hz, or the same filter applied twice, is worth testing on the device; a steep lower edge at 60 Hz is not recommended, because it failed on the recordings made with our own chain.
2. **Counting method:** keep the loudness curve and the repeat-pattern search, but replace the choice of the peak. Starting point: the improved counting method (let longer shifts count less, then take the shortest of a quarter, a third and half of the best shift whose peak is nearly as high, and show a number only if it stands clear of rivals and agrees with the previous estimates). Open: a repair for slow heart rates, and a test of the logarithmic loudness curve without look-ahead.
3. **Real time is not required for counting, and so far not needed.** By the estimated processor time, the stored 8 seconds could be processed as a whole; whether the larger variants fit in memory beside the firmware is open. Filtering forwards and backwards brought almost no gain of its own (0.07 to 0.25 BPM over the same filter applied twice while recording); the loudness curve of the Springer method brought more, but only with look-ahead tested, and less than the improved counting method, which works while recording.
4. **Listening filter (P08):** open until Nico has listened. Both data sources favour testing a lower edge near 100 Hz instead of the planned 40–800 Hz. Nico's five recordings allowed a boost of 5.9 dB with it. On the modelled recordings of the murmur collection the filter improved the score for telling murmur from no murmur without any boost (0.53 to 0.70), and 99.8 % of the recordings reached the output limit at the tested boost. The upper edge should become part of a later listening test (800 Hz, 1 kHz, 2 kHz), because 800 Hz costs murmur level in the murmur collection; the samples in Section 5.2.4 do not yet contain these variants. A fixed boost per switch position is a new design element; the firmware today can only make the sound smaller, never larger [5]. The boost needs a safety margin or a limiter: the room for it was found on five recordings, and the modelled recordings of the murmur collection, as their loudness was set here, leave no such room.
5. **Overload at the microphone** cannot be filtered away. In Nico's recordings it is driven by a slow swing below 20 Hz under the heart sounds. This points to the mechanical side (pressure, chest-piece, tube) or to the microphone's own low limit as the place to act, not the filters.
6. **The analysis keeps its own filter**, independent of the listening switch, as designed. The murmur collection points the same way from the other side: the BPM filters make a murmur 12 to 14 dB quieter.

## 7 Limitations

- **Nico's recordings:** one person, five recordings, one session, membrane side only, two chest positions. No murmurs, no other bodies, no clothing noise, no talking. In the movement of the first resting recording the raw signal contains straight ramps of about 35 ms, which may be the microphone recovering from overload or values lost during capture; this was not investigated.
- **Public recordings are not our device.** Other sensors, other people (young men during exercise; children in the murmur collection), passed through a model of our device input that fits the loudness but not the tone balance. Nothing above 2 kHz in the murmur collection and nothing above 4 kHz in the ECG collection. No correction for our chest-piece and tube, because no valid measurement of them exists where the heart sounds are.
- **The microphone model** comes from the datasheet; two of its values are not yet checked against the datasheet page, and the assumption that both of its low-pitch limits are simple first-order ones is the measurement project's.
- **Loudness of the public recordings in the model** was set to match Nico's recordings. Everything that depends on absolute loudness there (overload counts, safe boosts, the better heart-rate results at the overload level) describes the model, not the device.
- **Heart-rate reference.** For Nico's recordings it comes from the same sound (checked against an ECG on the ECG collection and found reliable where it claimed to be). For the ECG collection it is an ECG read by two methods that share their last step, so their close agreement shows that they find the same beats, not that each beat time is exact.
- **Windows overlap.** Consecutive 8-second windows share 7 seconds. In Nico's recordings only 35 windows do not overlap. For the ECG collection the ranges were computed by re-drawing people, which accounts for this; they rest on 21 people (10 in the test half).
- **The counting methods were tuned on the data they were tested on.** The original method was tuned on Nico's recordings, the improved method on half of the ECG collection. The improved method has been tested on the other half and on Nico's recordings, not on any third source.
- **The rule for invalid windows is not validated** (Section 5.1.1).
- **Murmur measures are energy measures.** They do not know what a murmur sounds like. One of the measures fixed in advance behaved in an unexplained way (it fell for every filter).
- **Loudness of the 40–150 Hz gentle filter was not measured** on Nico's recordings; only its largest safe boost is known (Table 9).
- Heart rates covered: 73 to 149 BPM in Nico's recordings, below 60 to about 200 BPM in the ECG collection.
- Processor load and memory are estimates. Nothing ran on the device. The loudness figures are estimates for an assumed listening level; the earpiece and the ear are not in the simulation. The digital-to-analogue converter [11] and the earpieces are treated as ideal.
- The half-rate check, and in the improved method the check for a third and a quarter, could wrongly raise the rate where the second heart sound is as loud as the first and falls halfway between two beats. At slow rates in the ECG collection this happens.
- The audio players use a compressed, lossless sound format (FLAC) that was tested in one desktop browser (Chrome) only, not on a phone.

## 8 Conclusion and next steps

A gentle 40–150 Hz filter is the recommended BPM filter, and 100–800 Hz gentle with a boost of 5.9 dB is the first listening candidate to judge by ear. Neither recommendation is final: the first depends on a counting method whose original form fails at high heart rates and whose improved form is worse than the original at slow ones (below 70 BPM: 8.7 instead of 4.3 BPM), the second on a boost that only Nico's five recordings support. On the ECG collection, the way the heart rate is counted matters more than the filter in front of it.

Next steps:

1. Nico listens to the samples, including the murmur samples, and chooses the listening filter and its boost. A second set of samples with upper edges of 800 Hz, 1 kHz and 2 kHz should follow.
2. Repair the improved counting method for slow heart rates, try the logarithmic loudness curve without look-ahead, and test both on a third data source.
3. Record more sessions with our own chain and a pulse oximeter or ECG at the same time (as REQ-06 requires [7]), on several people, with other chest positions, movement and poor contact.
4. Do the planned second chain measurement, so that the chest-piece and tube can enter the model with a valid curve.
5. Decide how to deal with overload at the microphone at high heart rates, and how much margin a fixed boost gets.
6. Write the filter and the counting method into the firmware and measure processor time and memory on the device.
7. Test the rule for invalid windows with deliberately bad signals (REQ-08 [7]).

## References

::sources
[1] DigitalStethoscope project, system design: `Development/system/design/system/parameters.md` (P01, P05, P06, P08), `interfaces-and-behavior.md` (section "DSP and measurement design") and `shared-filter-signal-flow.puml`; filter roles decided on 13 November 2026 (`Development/system/planning/mvp-decisions-2026-11-13-delivery-and-filters.md`). Project documents and project decisions, repository state of commit b1c7fbb.
[2] TDK InvenSense, *INMP441 Omnidirectional Microphone with Bottom Port and I²S Digital Output*, DS-INMP441-00, revision 1.0, 2014. [Datasheet](https://www.farnell.com/datasheets/1824785.pdf), accessed 11 November 2026 according to the project's AUDIO design; not re-opened for this study.
[3] ISO 226:2003, *Acoustics — Normal equal-loudness-level contours*, International Organization for Standardization. Covers 20 Hz to 12.5 kHz. The falling sensitivity toward low tones is taken from this standard's contours as implemented in the study's script (60-phon contour, extended below 20 Hz by the script); the full text was not inspected for this study (unverified).
[4] DigitalStethoscope project, AUDIO design: `Development/system/design/AUDIO/interfaces-and-behavior.md` (sample rate 16,000 Hz, blocks of 64 values, sample format, volume as linear gain 0–100 % with saturation). Project document, commit b1c7fbb.
[5] DigitalStethoscope firmware, `Development/system/coding/app/L2_application/L2_AUDIO/audio_processing.c`, function `audio_applyVolume`, commit b1c7fbb.
[6] Espressif Systems, *ESP-DSP Library Benchmarks*, ESP32-S3 column, row `dsps_biquad_f32` (17,552 processor cycles per 1,024 values). [Benchmarks](https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html). Value taken from the project's thesis material (`thesis-material/03-grundlagen-technisch/04-dsp-filter.md`, register entry `esp_dsp_benchmarks`, access date not recorded there); one reviewer re-opened the page on 23 November 2026 and found the same value. The processor speed of 240 MHz and the costs assumed for the other operations are assumptions of this study; the cost assumed for the larger calculations of the whole-window variants is taken from the same thesis material, where it is marked as still to be checked.
[7] DigitalStethoscope project, `Development/system/requirements/system-requirements.md`, REQ-06 and REQ-08. Project requirements.
[8] ANSI/AAMI EC13:2002, *Cardiac monitors, heart rate meters, and alarms*, Association for the Advancement of Medical Instrumentation. Cited from the project's source register (entry `ec13`); full text paywalled and not inspected.
[9] IEC 61672-1:2013, *Electroacoustics — Sound level meters — Part 1: Specifications* (A-weighting). Full text not inspected for this study; the weighting was implemented from its published formula and re-derived for 16,000 values per second.
[10] ITU-R BS.1770-4 (2015), *Algorithms to measure audio programme loudness and true-peak audio level*, International Telecommunication Union. Implemented from the recommendation's filter definition, re-derived for 16,000 values per second; a full-scale 997 Hz tone reads −2.97 LUFS instead of −3.01 LUFS (LUFS is the unit of this loudness measure).
[11] Texas Instruments, *PCM510xA 2.1 VRMS Audio Stereo DAC*, SLAS859C, 2015. [Datasheet](https://www.ti.com/lit/ds/symlink/pcm5102a.pdf), accessed 11 November 2026 according to the project's AUDIO design; not re-opened for this study.
[12] Own measurements and simulation of this study, 23 November 2026: recordings, scripts and result tables in `C:/Users/nicop/Desktop/heart-filter-study/` (`STATE.md`, `FINDINGS.md`; Nico's recordings: `reference/`, `results/`, `listening/`; public collections and whole-window counting: `calibration/`, `reference-public/`, `results-public/`, `results-window/`, `listening-public/`). All numbers in this paper without another source come from there.
[13] Own measurement, audio chain session of 22 November 2026: `C:/Users/nicop/audio-chain-measurements/2026-11-22/` (`notes.md`, `analysis/`, `photos/`); capture firmware built from commit b1c7fbb with the untracked chain-measurement files; method and code described in `Development/system/testing/AUDIO/chain-measurement/README.md` of the project repository (untracked at the time of this study).
[14] *Chain measurement of 22 November 2026: setup, results and the two independent reviews*, `chain-measurement-reviews.md` in the study folder, condensed on 23 November 2026 from the measurement thread and from two read-only reviews (by Claude Fable and by Gemini Neon, both 23 November 2026). The full review texts were not inspected for this study; this condensed record was.
[15] DigitalStethoscope project, `Development/system/testing/AUDIO/chain-measurement/microphone_model.py`: microphone model from the datasheet [2] (weakening of low pitches with half power at 60 Hz, a second limit of 3.7 Hz at 48,000 values per second scaled to the device's rate, usable range up to 0.423 times the number of values per second). According to that file, the 60 Hz value is checked against the project's datasheet record; the 3.7 Hz value and the usable range are not yet, and the simple (first-order) form of both limits is the project's assumption.
[16] A. Kazemnejad, P. Gordany, R. Sameni, *EPHNOGRAM: A Simultaneous Electrocardiogram and Phonocardiogram Database* (version 1.0.0), PhysioNet, 2021. [doi:10.13026/tjtq-5911](https://doi.org/10.13026/tjtq-5911), accessed 23 November 2026. Open Data Commons Attribution License v1.0 (the version number is stated on the dataset page; the licence file in the download carries none). 69 recordings downloaded and verified against the source's SHA-256 list; 66 used. Details on people, device and activities are from the dataset page and its spreadsheet. The source asks users to also cite its database article (A. Kazemnejad, P. Gordany, R. Sameni, "An open-access simultaneous electrocardiogram and phonocardiogram database," bioRxiv, 2021, doi:10.1101/2021.05.17.444563; title as listed on the dataset page, place of publication and DOI as found by one of the reviewers of version 3), the toolbox used by its authors (R. Sameni, *The Open-Source Electrophysiological Toolbox (OSET)*, version 3.14, https://github.com/alphanumericslab/OSET; not used in this study), and: T. Pollard et al., "PhysioNet as a global platform for biomedical research," *Nature Health*, 2026, doi:10.1038/s44360-026-00096-z (cited as given on the dataset page; not inspected).
[17] J. Oliveira, F. Renna, P. Costa, M. Nogueira, A. C. Oliveira, A. Elola, C. Ferreira, A. Jorge, A. Bahrami Rad, M. Reyna, R. Sameni, G. Clifford, M. Coimbra, *The CirCor DigiScope Phonocardiogram Dataset* (version 1.0.3), PhysioNet, 2022. [doi:10.13026/tshs-mw03](https://doi.org/10.13026/tshs-mw03), accessed 23 November 2026. Open Data Commons Attribution License v1.0. 10,434 files downloaded and verified against the source's SHA-256 list. Collected in two screening campaigns in Northeast Brazil in 2014 and 2015; murmurs described by one specialist; the marks of the heart sounds come from three computer methods checked and corrected by a person (all according to the dataset page).
[18] J. Oliveira et al., "The CirCor DigiScope Dataset: From Murmur Detection to Murmur Classification," *IEEE Journal of Biomedical and Health Informatics*, vol. 26, no. 6, pp. 2524–2535, 2022, doi:10.1109/JBHI.2021.3137048. The article describing [17]; volume, pages and year as found in the publisher's record by one of the reviewers of version 3 on 23 November 2026; full text not inspected.
[19] DigitalStethoscope project, thesis material `thesis-material/08-evaluation/03-filtervergleich-statistik.md` (units A002, A003, A004, A009, A010, A017, A018, A019, U050: possible measures for murmurs, equal conditions for all filters, one common marking of the beats, paired tests with a correction for several tests). Project notes; the literature they cite was not re-opened for this study. The exact measures used here were fixed by this study before the analysis (recorded in `STATE.md`, decision R2-6).
[20] D. B. Springer, L. Tarassenko, G. D. Clifford, "Logistic Regression-HSMM-Based Heart Sound Segmentation," *IEEE Transactions on Biomedical Engineering*, vol. 63, no. 4, pp. 822–832, 2016, doi:10.1109/TBME.2015.2475278. Bibliographic data checked against the dblp index on 23 November 2026; the article is not freely available and was not read.
[21] D. Springer, *Logistic Regression-HSMM-based Heart Sound Segmentation* (program code, version 1.0), PhysioNet, 2019, doi:10.13026/vnt9-kf93 (year and DOI from the project page, as found by one of the reviewers of version 3). [Project page](https://physionet.org/content/hss/1.0/), files downloaded 23 November 2026 and checked against the project's checksum list. The steps described in this paper were read from the files `getHeartRateSchmidt.m`, `schmidt_spike_removal.m`, `Homomorphic_Envelope_with_Hilbert.m` and `default_Springer_HSMM_options.m`, and for the three combined loudness curves also from `getSpringerPCGFeatures.m`, `Hilbert_Envelope.m` and `get_PSD_feature_Springer_HMM.m` (file and line in `sources/springer-method-notes.md` of the study folder). Licence GNU General Public License version 3 or later according to the file headers; the project page lists GPL version 3 (seen by one of the reviewers; this study's own download of the licence file failed).
[22] DigitalStethoscope project, evaluation guide `preThesis/06-bringup-zephyr/EVAL-GUIDE.md`, row E04: provisional target of a mean error of at most 5 BPM with at least 90 % valid windows, defined there for clean test signals. Project document.
::end

## Appendix A: How this paper was produced and checked

**Authorship.** Nico Friedrich set the questions and goals, made the recordings and the chain measurement, and decides the open points. The analysis was planned, led and written up by an AI assistant (Claude Fable 5.2); all code was written by a second AI model (Claude Opus 5.5) and reviewed by the lead. Nico has not yet reviewed the text in detail.

**Versions.** Versions 1 and 2 (23 November 2026) covered Nico's five recordings. Version 3 added the two public collections, the account of the chain measurement and counting on the whole stored 8 seconds. Version 4, this one, is an editorial revision of version 3: paper structure, numbered figures and tables, one name per filter, method and data set. It contains no new analysis and no changed number. Two results of the earlier versions were replaced along the way and are reported here in their current form: the original counting method was called "final" until the ECG collection showed its one-third errors, and the 40 Hz lower edge rested on a single window of Nico's recordings until the ECG collection supported it.

**Review of versions 1 and 2.** Three rounds by three independent AI reviewers (one model each from three providers: GPT Astra, Claude Fable, Gemini Neon), with final scores of 8, 9 and 9 out of 10.

**Review of version 3.** Checked in the same way on 23 November 2026: the reviewers compared the numbers with the result files (each checked several dozen to about a hundred), the method, the sources and the plainness of the language. Scores out of 10 in the first round: 8, 7 and 6. The reviewers found, among other things, that the first draft overstated three conclusions (that non-real-time counting brings no gain, that both data sources support the 40 Hz lower edge, and that the murmur collection confirms the boost), mixed numbers from the tuning and the test half, and described one figure wrongly. All findings marked as blocking were corrected in the text and figures. A second round with new reviewer sessions confirmed these corrections against the result files and scored 8, 8 and 8; what it still found were places where a correction had not been carried through everywhere, and small errors of scope (for example which candidates a statement covers). These were corrected as well. In a third and last round two reviewers again scored 8 and wrote that the text would be at 9 once two or three remaining sentences were replaced (a caveat missing in one design point, in the note at the listening samples and in one table cell, and a statement that held at one loudness level only); these sentences were replaced as they proposed, and the result was not reviewed again. The third reviewer (GPT Astra) could not take part in the last round because its provider's usage limit was reached, so it gave no score there. The target of 9 from every reviewer was therefore not formally reached.

**Check of version 4.** The new text was compared with version 3 in two ways. A script compared every number: version 3 contains 1,706 numbers (477 different ones), all of which occur in version 4, and version 4 adds none except a software version number in Appendix B; Table 9 was recomputed from the result file and 31 further key numbers were found in the result files. One independent AI reviewer (Claude Sonnet 5.5) then compared the two texts section by section for changed meanings, lost limitations, changed numbers and broken figures, players and references. It found no changed number and no number attached to the wrong filter, method or data set. It found five places where newly written sentences (in the abstract and in Sections 5.1.5, 6.1 and 8) had lost a qualifier or were stronger than version 3, and two items that were not referenced in the text; all were corrected as it proposed, and the corrections were not reviewed again. There was no full three-reviewer round for this version. The reviewer did not check numbers against the result files and did not open the page in a browser; the published page was checked separately by the lead (figures, players, phone width).

## Appendix B: Reproducibility and file paths

Everything lives in the study folder `C:/Users/nicop/Desktop/heart-filter-study/` [12]; `STATE.md` there records every decision, delegated task and check, `FINDINGS.md` every finding with its evidence. Table B1 lists the scripts and result folders. Scripts run with `.venv/Scripts/python.exe` (Python 3.12 with numpy, scipy, soundfile, matplotlib) and cache intermediate results.

| What | Script | Results |
|---|---|---|
| Device simulation, filters, counting methods | `src/hfs/` | (library) |
| Reference heart rates, Nico's recordings | `src/reference_beats.py` | `reference/` |
| Heart rate, Nico's recordings | `src/bpm_evaluate.py`, `src/bpm_report.py` | `results/` (`bpm_filter_grid.csv`, `bpm_per_window.csv`, `SUMMARY.md`) |
| Listening measures and samples, Nico's recordings | `src/listening_metrics.py`, `src/listening_samples.py` | `listening/` (`metrics_summary.csv`, `shortlist.json`, `samples/`) |
| Download and checksums of the public collections | `src/public_download_ephnogram.py`, `src/public_download_circor.py` | `public-data/` (`MANIFEST.json`) |
| Model of the device input and its calibration | `src/hfs/chain_model.py`, `src/chain_model_calibrate.py` | `calibration/` |
| ECG reference | `src/ecg_reference.py` | `reference-public/ephnogram/` |
| Heart rate against the ECG; one-third diagnosis; improved counting method | `src/bpm_evaluate_public.py`, `src/bpm_improved_method_*.py` | `results-public/` |
| Counting on the whole stored 8 seconds | `src/bpm_window_methods.py`, `src/hfs/window_bpm.py` | `results-window/`; notes on the Springer code in `sources/springer-method-notes.md` |
| Murmur measures | `src/listening_public.py` | `listening-public/` |
| Figures | `src/page_figures.py`, `src/page_figures_public_model.py`, `src/page_figures_chain_measurement.py`, `src/bpm_public_figures.py`, `src/bpm_window_figures.py`, `src/bpm_improved_method_figures.py` | `page/figures/` (each figure with a `.txt` description) |
| This page | `src/build_page.py` | text in `page/parts4/*.md`, joined into `page/read.md`; site in `page/site/` |

*Table B1. Scripts and result folders.*

Two errors in the simulation code were found by reviewers of version 2 and corrected for version 3; neither changes a number in this paper. The share of overloaded values was counted wrongly for the filters that first reduce the data rate (Section 5.1.1). And at volume settings below 100 % the simulation limited the signal before the volume step, while the design does so after it; at full volume, which all results use, the output is identical value for value.

The chain measurement of 22 November 2026 is in `C:/Users/nicop/audio-chain-measurements/2026-11-22/` [13]. The recordings of the public collections are not redistributed here; their sources and versions are given in [16] and [17].

## Appendix C: Terms in plain words

::glossary
