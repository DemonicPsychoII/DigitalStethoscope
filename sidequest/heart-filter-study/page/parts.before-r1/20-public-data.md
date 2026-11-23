## A second source: public recordings

The first version of this study had only Nico's five recordings: one person, no heart murmurs, and a heart-rate reference taken from the same sound. This version adds two open collections of heart recordings from the research archive PhysioNet. Both were downloaded on 23 November 2026, and every file was checked against the checksum list of its source (a checksum is a fingerprint of a file that shows it arrived unchanged).

| | Heart sounds with ECG (EPHNOGRAM [16]) | Heart sounds with murmur labels (CirCor DigiScope [17], described in [18]) |
|---|---|---|
| What it adds | An independent heart-rate reference, at rest and during exercise | Murmurs, labelled by a specialist, with the parts of each beat marked |
| People | 24 healthy men, 23 to 29 years (as stated by the source) | 942 patients in the published part, mostly children; 178 with a murmur between the heart sounds, 695 without |
| Recordings used | 66 of 69 (about 29 hours): 8 of 30 seconds at rest, the others of 30 minutes while sitting, lying, walking, on a treadmill or on a bicycle | 2,888 recordings, 58,156 fully marked heartbeats |
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

Three recordings of the first collection were left out: two are exact copies of other recordings filed under a different person, and one is marked by its authors as having no sound. From the murmur collection, the 68 patients whose label is "unknown" were left out, and one recording with unreadable markings.

### Putting public recordings through our device

The public recordings were made with other sensors. To test our filters on them as the device would see them, each recording was passed through a model of our device's input, built from what is known:

1. Convert to the device's 16,000 values per second.
2. Apply the microphone's behaviour from its datasheet [2][15]: it weakens very low pitches (half strength at 60 Hz by the datasheet; two further values of the model are not yet checked against the datasheet).
3. Set the loudness so that the heart sounds are as strong as in Nico's recordings. Two settings: **rest level** (as strong as in his three recordings without lasting overload) and **overload level** (raised until one beat in three reaches full scale, as in his two overloaded recordings).
4. Add background noise where the public recording is quieter between the beats than our real chain was.
5. Cut off at full scale, as the real microphone path does.

After that, the simulation of the device is the same as for Nico's recordings. No correction for our chest-piece is applied (see the previous section). As a variant, the tone balance of the public recordings was shifted towards that of Nico's recordings ("matched"); this stands in for all differences at once, sensor, chest-piece, tube and person, and cannot tell them apart.

### How close the modelled public recordings come to our real chain

Nico's recordings are the real chain on a real chest, so they are the yardstick.

::figure{src="page/figures/run2_public_vs_own_spectrum.png" alt="Strength against pitch for the own recordings and the two modelled public collections" caption="Tone balance of Nico's recordings and of the public recordings after the model of our device input. Each curve is drawn relative to its own strongest range, so only the shape counts." width="wide"}

| Measure | Own recordings | Public, with ECG | Public, murmur data |
|---|---:|---:|---:|
| Heart-sound level at rest (dB below full scale) | 9.7 | 9.7 | 9.7 |
| Energy below 20 Hz (%) | 52 | 17 | 2.5 |
| Energy from 20 to 150 Hz (%) | 48 | 80 | 43 |
| Energy from 150 to 800 Hz (%) | 0.06 | 2.1 | 40 |
| Sound between the beats, relative to the heart sounds (dB) | −21 | −14 | −11 |

*How close the modelled public recordings come to the own recordings at rest level, without the matching variant (medians over recordings).*

- **Loudness fits**: the heart-sound level at rest agrees within 0.1 dB, and at the overload level 34 % of all beats reach full scale, as in Nico's recordings. This was set on purpose, so it is not a test.
- **Tone balance does not fit.** The public recordings are much brighter: relative to Nico's recordings they carry 10 to 18 dB more between 100 Hz and 1 kHz (with ECG) and 12 to 39 dB more (murmur data). They carry far less below 20 Hz. The matching variant brings the recordings with ECG to within about 6 dB; the murmur data stay 14 to 33 dB too bright above 200 Hz, because the correction was limited to 12 dB.
- **They are noisier between the beats** by 7 to 10 dB.
- **Overload works differently.** In Nico's overloaded recordings the cut-off beats ride on a slow swing below 20 Hz that uses up 0.2 to 0.4 of the number range; without that slow part only 3 of 129 and 5 of 127 beats would reach full scale instead of 42 and 45 (own analysis for this version). The public recordings lack this slow part, so in the model the heart sounds themselves must be raised until they are cut off.

::callout{kind="limitation"}
The public recordings test the filters on other people, with murmurs and against an ECG. They do not show how our chain sounds on those people. Whether the difference in tone balance comes from the sensors, from our chest-piece and tube, or from the people (children in the murmur collection, one adult man in ours) cannot be separated with the data at hand.
::end
