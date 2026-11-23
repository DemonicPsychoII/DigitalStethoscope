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
- **The decision not to apply a chest-piece correction.** Nico's own recordings already contain the real chest-piece, tube and microphone, so nothing must be added. For the public recordings (see below) a correction was considered and rejected: the only reliable quantity, bell against membrane, describes the difference between the two sides of our chest-piece. It says nothing about the difference between our chest-piece and the unknown sensors of the public recordings, and those recordings were not made through our bell. This is a decision of this study.
- **No cross-check for the heart sounds.** The own recordings contain almost no energy above 150 Hz (0.06 % between 150 and 800 Hz). The measurement cannot explain this: where it is usable, above 400 Hz, the path through chest-piece and tube was stronger in air than the bare microphone at most pitches (membrane side, at the louder setting: by a few dB at 400 Hz to 1 kHz and by up to about 20 dB near 2.5 kHz), which neither supports nor contradicts the missing energy on a chest, where the chest-piece is loaded differently.

### What it did not take, and why

- No curve of the chest-piece or the tube enters any number on this page. Below 400 Hz, where the heart sounds are, the measured curves are not valid.
- The tube's row of peaks (261 Hz and upward) was not built into the model for the public recordings. It lies above most heart-sound energy, and the public sensors have their own unknown tubes and housings.
- The distortion figures were not used, since they are upper limits only.

### What the planned second session would change

A second session is planned but not done [14]: arrangement A rebuilt without its own dip and measured before and after each block, a sealed tube, checks for sound leaking past the chest-piece, a recording of silence, a test tone from 10 Hz, and corrected calculation details. If it yields a valid chest-piece and tube curve down to low pitches, the model of the device chain could use a measured curve instead of the tone-balance matching used here. It would still be a comparison between arrangements, measured in air: how the chest-piece behaves on skin would remain open, and relating the overload at the microphone to a sound pressure would need a calibrated measuring microphone in addition.
