
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
- One result is unexplained: the unweighted ratio of murmur to heart sounds falls for every filter (by 0.6 to 2.6 dB), although the score built on it rises for every candidate except the BPM filter as first planned (25–150 Hz), for which it falls from 0.53 to 0.51.

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
| Does the filter design or the upper edge matter? | Not measurably on clean windows | The upper edge changed the mean error by up to about 1 BPM. Other designs 2 to 7 BPM worse than the gentle design; at rest level the recommended 40–150 Hz filter applied twice was 3.5 BPM better than applied once | Differ slightly |
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
