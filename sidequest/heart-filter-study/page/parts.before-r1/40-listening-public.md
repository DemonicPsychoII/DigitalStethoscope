### Do the candidates keep murmurs audible? (public murmur data)

Nico's recordings contain no murmur. The murmur collection [17] does: 178 patients with a murmur between the first and the second heart sound, and 695 without one. Murmurs after the second heart sound are too rare in the collection to judge (5 patients, 4 of them analysed).

What "audible" and "distinguishable" mean in numbers was fixed before any result existed (decision of this study on 23 November 2026, following the project's notes on comparing filters [19]). All measures are taken at the device output, for every filter on the same marked stretches of each beat, with one value per patient:

- **Murmur level (main measure):** how strong the stretch between the two heart sounds is at the output, weighted for the ear's sensitivity (A-weighting [9]), each candidate at its fixed boost from the first part of this study; given as the difference to no filter.
- **Murmur against heart sounds:** the energy of that stretch divided by the energy of the two heart sounds.
- **Murmur against the quiet part:** the energy of that stretch divided by the energy of the quiet stretch after the second heart sound.
- **Telling murmur from no murmur:** how well the last two measures separate the patients with a murmur from those without, as a score from 0.5 (no better than chance) to 1 (perfect).

Each candidate was compared with no filter patient by patient (a paired test, with a correction for having run 48 tests at once). With this many patients even tiny differences pass such a test, so the size in dB is what counts.

| Candidate (boost) | Murmur level vs no filter (dB) | Murmur against quiet part vs no filter (dB) | Telling murmur from no murmur (heart-sound measure) | Telling murmur from no murmur (quiet-part measure) |
|---|---:|---:|---:|---:|
| No filter (Raw) | 0 | 0 | 0.53 | 0.79 |
| 40–800 Hz, gentle (design candidate, −0.2 dB) | −1.9 | +1.6 | 0.62 | 0.86 |
| **100–800 Hz, gentle (+5.9 dB)** | **+4.1** | **+3.0** | **0.70** | **0.90** |
| 100–800 Hz, steep (+7.2 dB) | +5.5 | +3.4 | 0.72 | 0.90 |
| 150–800 Hz, steep (+9.7 dB) | +7.7 | +3.2 | 0.70 | 0.88 |
| 60–800 Hz, very steep (+3.8 dB) | +2.2 | +3.1 | 0.71 | 0.91 |
| Above 80 Hz only (+3.4 dB) | +3.4 | +2.6 | 0.68 | 0.90 |
| 25–150 Hz (BPM filter as first planned, −1.8 dB) | −14.4 | −0.2 | 0.51 | 0.80 |
| 40–150 Hz (recommended BPM filter, +0.3 dB) | −12.3 | +0.7 | 0.57 | 0.85 |

*Murmur measures on the public murmur data at rest level (178 patients with a murmur, 695 without). Differences are typical paired differences over the 178 patients; for the gentle 100–800 Hz filter the 95 % ranges are +3.9 to +4.3 dB (murmur level), +2.6 to +3.4 dB (quiet part) and +0.13 to +0.21 for the gain in the first score.*

::figure{src="page/figures/run2_murmur_separation.png" alt="Score for telling murmur from no murmur, per candidate, with ranges" caption="How well two simple measures tell patients with a murmur from patients without, after each candidate filter (0.5 = chance, 1 = perfect; bars: 95 % ranges). Candidates printed in grey were added for this comparison and are not among the listening samples." width="wide"}

::figure{src="page/figures/run2_murmur_spectrum.png" alt="Strength against pitch of the stretch between the heart sounds, with and without murmur" caption="Where the murmur energy lies in the public recordings (after the model of our device input, before any filter): the stretch between the two heart sounds for patients without a murmur and with soft, medium and loud murmurs. Murmurs add energy from about 60 Hz upward. The recordings contain nothing above 2 kHz." width="wide"}

- **The planned 40–800 Hz filter is the weakest listening candidate for murmurs**: the murmur comes out 1.9 dB quieter than without a filter, and it separates murmur from no murmur less well than every candidate with a higher lower edge.
- **Candidates with a lower edge of 80 to 150 Hz form the top group.** With their boost the murmur is 3 to 8 dB stronger than without a filter, and it stands out better against the quiet part (+2.6 to +3.4 dB). Their scores overlap within their ranges; the data do not rank them against each other.
- **The gain in murmur level is the boost, not the filter.** Without a boost every candidate with an upper edge at 800 Hz makes the murmur 1.6 to 2.0 dB quieter, mostly through that upper edge; "above 80 Hz only" costs 0.06 dB. The boost is possible only because a higher lower edge frees room, which is what the first part found on Nico's recordings.
- **The upper edge costs murmur level.** With the lower edge at 100 Hz (gentle, each at its own safe boost), the murmur level against no filter is +2.9 dB with an upper edge of 600 Hz, +4.1 dB with 800 Hz, +4.7 dB with 1 kHz, +5.7 dB with 2 kHz and +5.8 dB without an upper edge. The scores for telling murmur from no murmur do not change with it beyond their ranges (0.69 to 0.71). On Nico's recordings the upper edge hardly mattered, because they contain almost nothing above 150 Hz.
- **Soft and low-pitched murmurs stay hard.** Loud murmurs (grade III or more) are separated with a score of 0.94 after the gentle 100–800 Hz filter, soft ones (grade I) only with 0.61; high-pitched murmurs reach 0.97, low-pitched ones stay at chance for every filter.
- **The two BPM filters are unusable for listening to murmurs** (12 to 14 dB quieter).
- One result is unexplained: the unweighted ratio of murmur to heart sounds falls for every filter (by 0.6 to 2.6 dB) although the score built on it rises.

The same order came out at the overload level, with the matched tone balance, and in two random halves of the patients.

::callout{kind="limitation"}
These are energy measures on other people's recordings, made with another sensor on children, far brighter than what our chain delivered on Nico's chest, and with nothing above 2 kHz. They show which filters keep murmur energy and let it stand out; they do not show what a listener hears through our earpieces. The boosts were found safe on Nico's five recordings only: on the modelled public recordings, which are more peaky, almost every recording already touches full scale at the device input at rest level, and every boosted candidate overloads on 97 to 100 % of them. That figure depends on how the loudness of the public data was set and is not a measurement of the device, but it shows that "safe on five recordings" is not "safe".
::end
