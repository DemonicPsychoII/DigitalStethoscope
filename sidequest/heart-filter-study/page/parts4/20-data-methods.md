
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
