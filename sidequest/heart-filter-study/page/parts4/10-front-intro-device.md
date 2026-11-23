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
