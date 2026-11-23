"""Text revisions after council run 2 round 1 (Claude Fable). Each replacement must match exactly once."""
from pathlib import Path

PARTS = Path(__file__).resolve().parent


def revise(name, pairs):
    path = PARTS / name
    text = path.read_text(encoding="utf-8")
    for before, after in pairs:
        assert text.count(before) == 1, (name, before[:70], text.count(before))
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")


revise("10-chain-measurement.md", [
    ("- **A cross-check that fits.** The own recordings contain almost no energy above 150 Hz (0.06 % between 150 and 800 Hz), and the measurement shows no boost of the chest-piece in the range where it is usable. This fits together but is not proof: on a chest the chest-piece is loaded differently than in air.\n",
     "- **No cross-check for the heart sounds.** The own recordings contain almost no energy above 150 Hz (0.06 % between 150 and 800 Hz). The measurement cannot explain this: where it is usable, above 400 Hz, the path through chest-piece and tube was 2 to 14 dB stronger in air than the bare microphone (membrane side, at the louder setting), which neither supports nor contradicts the missing energy on a chest, where the chest-piece is loaded differently.\n"),
    ("Dividing by A turns this dip into a false peak of 10 to 13 dB at about 250 Hz in both results.",
     "Dividing by A adds about 10 to 13 dB to the peak at about 250 Hz in both results."),
])

revise("20-public-data.md", [
    ("it weakens very low pitches (half strength at 60 Hz by the datasheet; two further values of the model are not yet checked against the datasheet).",
     "it weakens very low pitches (to about 0.7 times at 60 Hz by the datasheet; two further values of the model are not yet checked against the datasheet)."),
])

revise("00-summary.md", [
    ("it halves the error (28.4 to 13.1 BPM) and leaves the result on Nico's recordings unchanged, but is slightly worse at slow heart rates and still far from the target during exercise. Counting on the stored 8 seconds in non-real time is possible but brings no gain of its own.",
     "it halves the error (28.4 to 13.1 BPM) and leaves the result on Nico's recordings unchanged, but below 70 BPM its error doubles (4.3 to 8.7 BPM), and it is still far from the target during exercise. Counting on the stored 8 seconds in non-real time is possible on the device. Filtering forwards and backwards brings no gain of its own; a loudness curve from a published research method helped more, but was only tried with look-ahead and helps less than the improved choice of the repeat pattern."),
    ("Filters with a lower edge of 80 to 150 Hz, played with the boost they make room for, make a murmur 3 to 8 dB stronger than without a filter (dB is a measure for ratios, explained below: +6 dB is twice as large) and let simple measures tell murmur from no murmur better. The first candidate named in the first version, **100–800 Hz with a boost of 5.9 dB**, is in that top group.",
     "Filters with a lower edge of 80 to 150 Hz let simple measures tell murmur from no murmur better (score 0.70 for 100–800 Hz against 0.62 for the planned filter and 0.53 without a filter; 0.5 is chance) and let the murmur stand out more against the quiet part of the beat (+3.0 against +1.6 dB; dB is a measure for ratios, explained below: +6 dB is twice as large). The first candidate named in the first version, **100–800 Hz with a boost of 5.9 dB**, is in that top group. Its gain in murmur loudness (4.1 dB) is the boost, and the room for that boost was found only on Nico's five recordings; on the public recordings, as their loudness was set here, there is no such room."),
])

revise("30-bpm-public.md", [
    ("*Heart rate from the sound against the ECG, by activity, rest level, all people. The improved method is explained below.*",
     "*Heart rate from the sound against the ECG, by activity, rest level, all people. The improved method is explained below; its columns include the 11 people it was tuned on, so they flatter it somewhat. The test on the other people follows below.*"),
    ("In 14,054 windows the device reported **one third** of the true rate, in 7,259 one half, and most of the others are a quarter.",
     "In 14,054 windows the device reported **one third** of the true rate and in 7,259 one half. Of the remaining gross errors at least 2,300 are a quarter of the rate (counted in three activities); the others cluster at about one and a half and two and a half beat spacings and, lying down, at the upper end of the search (near 200 BPM)."),
    ("- On the test half the improved method **halves the mean error** (by about 15 BPM at both loudness levels) and removes 80 to 98 % of the one-third errors. Above 130 BPM the mean error falls from 38–78 BPM to 2–9 BPM.",
     "- On the test half the improved method **halves the mean error** (by about 15 BPM at both loudness levels) and removes 80 % (rest level) and 92 % (overload level) of the one-third errors. Above 130 BPM the mean error falls from 38–78 BPM to 2–9 BPM."),
    ("- A wrong number is shown as valid in 6 % of the shown windows instead of 29 %. The price: only about two thirds of the windows are shown at all.",
     "- A wrong number is shown as valid in 6 % of the shown windows instead of 29 %. The price: 65 % of the windows are shown instead of 72 %."),
    ("- **It is slightly worse at rest**: sitting still 3.7 instead of 2.7 BPM, lying down 14.8 instead of 11.6 BPM, below 70 BPM 8.7 instead of 4.3 BPM (test half). At slow rates the rule sometimes prefers a shorter wrong shift. A rule that depends on the rate could repair this; it was not built.",
     "- **It is worse at slow heart rates, which is where a stethoscope is mostly used.** On the test half: below 70 BPM 8.7 instead of 4.3 BPM, lying down 8.1 instead of 5.4 BPM, sitting still unchanged (3.7 against 3.8 BPM). Over all people: sitting still 3.7 instead of 2.7 BPM, lying down 14.8 instead of 11.6 BPM. At slow rates the rule sometimes prefers a shorter wrong shift. A rule that depends on the rate could repair this; it was not built."),
    ("- The acceptance target is still met only when sitting still (and there only with the validity rule of the first part; the new rule shows 87 to 88 % of the windows). No exercise situation meets it with either method.",
     "- The acceptance target is still met only when sitting still (and there only with the validity rule of the first part; the new rule shows 87 to 88 % of the windows). On the test half no exercise situation meets it with either method."),
    ('caption="Heart rate from the sound against the ECG by activity, for the counting method of the first part (\\"run-1\\" in the figure) and the improved method, recommended 40–150 Hz filter, rest level, all people."',
     'caption="Heart rate from the sound against the ECG by activity, for the counting method of the first part (\\"run-1\\" in the figure) and the improved method, recommended 40–150 Hz filter, rest level, all people, including the 11 on whom the improved method was tuned."'),
    ("- **The counting method matters far more than the filter.**",
     "- **Other filter designs and the upper edge.** Other designs with the same edges were 2 to 7 BPM worse than the planned gentle design (Butterworth 26.6 BPM; Bessel 28.5, Chebyshev 29.1, elliptic 29.1, the FIR candidate 34.0), and the upper edge made no difference (26.6 to 27.2 BPM for upper edges from 100 to 800 Hz, lower edge 40 Hz). The listening candidate 100–800 Hz was as good an input for counting as 40–150 Hz here (26.8 BPM); the first part's finding that it is a poor input came from the low-pitched disturbances in Nico's recordings, which the public recordings lack.\n- **The counting method matters far more than the filter.**"),
])

revise("35-window-methods.md", [
    ('Every variant here uses the half-rate check unless it says \\"as published\\"." width="wide"}',
     'The bar \\"range widened to 200 BPM\\" is Springer\'s preparation without the half-rate check; with the check it reaches 20.7 and 10.5 BPM on the public recordings (not drawn; see the table)." width="wide"}'),
    ("| Same filter, forwards and backwards over the stored stretch | 0.32 / 0.38 |",
     "| Same filter, forwards and backwards over the stored stretch | 0.33 / 0.39 |"),
    ("| Springer's preparation, range widened to 200 BPM, with half-rate check | 0.38 / 0.44 |",
     "| Springer's preparation, range widened to 200 BPM | 0.38 / 0.44 | −1.2 (−3.7 to +1.4) | −5.3 |\n| Springer's preparation, range widened to 200 BPM, with half-rate check | 0.38 / 0.44 |"),
    ("ranges are 95 % ranges over people, corrected for the number of variants compared. A negative change is an improvement.*",
     "ranges are 95 % ranges over people. A negative change is an improvement.*"),
    ("- **Springer's logarithmic loudness curve is the most promising ingredient.** With the search widened to 200 BPM and the half-rate check added, it improves the public result by 6 to 10 BPM, mostly above 110 BPM, where it removes many of the one-third errors described above; below 70 BPM it is 7 to 11 BPM worse. A quick extra test of the logarithmic curve alone (run after the first results, at rest level only) gave −6.1 BPM.",
     "- **Springer's preparation helps more, but only with the half-rate check and only at higher heart rates.** Widening its search to 200 BPM alone changes little at rest level (−1.2 BPM, a range that includes zero). With the half-rate check added it improves the public result by 6 to 10 BPM, mostly above 110 BPM, where it removes many of the one-third errors described above; below 70 BPM it is 7 to 11 BPM worse. Its logarithmic loudness curve is one likely ingredient: a quick extra test (run after the first results, at rest level only) of forwards-and-backwards filtering at 1,000 values per second gave −3.7 BPM on its own and −6.1 BPM with the logarithmic curve, so the curve added about 2.4 BPM there.\n- **All of these gains are smaller than that of the improved choice of the peak** described above (about 15 BPM on the test half, without look-ahead). The two were not combined."),
    ("| Forwards and backwards, stored at 1,000 values per second | 5.0 | 0.6 | 63 kB |",
     "| Forwards and backwards, stored at 1,000 values per second | 5.0 | 0.6 | 73 kB |"),
    ("*Estimated cost per variant on the ESP32-S3. All would fit at one update per second; the audio path keeps priority, and the work can be spread over many 4 ms blocks.*",
     "*Estimated cost per variant on the ESP32-S3. All would fit at one update per second; the audio path keeps priority, and the work can be spread over many 4 ms blocks. If the counting may use a tenth of one core, the method of the first part could update about 48 times per second, forwards-and-backwards filtering at 1,000 values per second about 20 times, the logarithmic curve about 5 times and the other whole-window variants 2 to 3 times.*"),
    ("**Counting in non-real time is possible on the device but is not what brings the gain.** A steeper filter gives the same improvement while recording, at almost no cost. If more accuracy is wanted, the lead to follow is the logarithmic loudness curve with a search up to 200 BPM; whether it also works without look-ahead was not tested.",
     "**Counting in non-real time is possible on the device. Filtering forwards and backwards brings no gain of its own:** a steeper filter gives the same improvement while recording, at almost no cost. Springer's preparation with a search up to 200 BPM and the half-rate check helped more (6 to 10 BPM), but it was only tried with look-ahead, it is worse at slow heart rates, and it helps less than the improved choice of the peak. Whether its logarithmic loudness curve also works without look-ahead, and together with the improved choice, was not tested."),
])

revise("40-listening-public.md", [
    ("- **Telling murmur from no murmur:** how well the last two measures separate the patients with a murmur from those without, as a score from 0.5 (no better than chance) to 1 (perfect).",
     "- **Telling murmur from no murmur:** how well the last two measures separate the patients with a murmur from those without, as a score from 0.5 (no better than chance) to 1 (perfect). The figure calls this score by its technical name, area under the curve."),
    ("- **Candidates with a lower edge of 80 to 150 Hz form the top group.** With their boost the murmur is 3 to 8 dB stronger than without a filter, and it stands out better against the quiet part (+2.6 to +3.4 dB). Their scores overlap within their ranges; the data do not rank them against each other.",
     "- **Candidates with a lower edge of 80 to 150 Hz, together with the very steep 60–800 Hz filter, form the top group.** The murmur stands out better against the quiet part (+2.6 to +3.4 dB), and the scores for telling murmur from no murmur are highest (0.68 to 0.72 and 0.88 to 0.91). These two results do not depend on the boost. With their boost the murmur is also 2 to 8 dB stronger than without a filter. The scores of this group overlap within their ranges; the data do not rank its members against each other."),
    ("- **Soft and low-pitched murmurs stay hard.** Loud murmurs (grade III or more) are separated with a score of 0.94 after the gentle 100–800 Hz filter, soft ones (grade I) only with 0.61; high-pitched murmurs reach 0.97, low-pitched ones stay at chance for every filter.",
     "- **Soft and low-pitched murmurs are harder, and the two measures disagree on how hard.** After the gentle 100–800 Hz filter, the measure against the heart sounds separates loud murmurs (grade III or more) with a score of 0.94 and high-pitched ones with 0.97, but soft ones (grade I) only with 0.61, and low-pitched ones not at all (0.50, for every filter). The measure against the quiet part does better there: 0.86 for soft and 0.82 for low-pitched murmurs."),
    ("The boosts were found safe on Nico's five recordings only: on the modelled public recordings, which are more peaky, almost every recording already touches full scale at the device input at rest level, and every boosted candidate overloads on 97 to 100 % of them. That figure depends on how the loudness of the public data was set and is not a measurement of the device, but it shows that \"safe on five recordings\" is not \"safe\".",
     "The boosts were found safe on Nico's five recordings only. The modelled public recordings are more peaky: at rest level almost every one (3,141 of 3,162) already touches full scale at the device input, so the output overloads on 97 to 100 % of them even without any boost (99 % with no filter, 98 % with the planned 40–800 Hz filter, 97 % with the gentle 100–800 Hz filter, all at 0 dB). A setting that stays clear of overload on 99 % of these recordings would be a cut, not a boost: −4.2 dB for 40–800 Hz, −4.5 dB for the gentle and −5.6 dB for the steep 100–800 Hz filter. On these recordings a higher lower edge frees no room. These figures depend on how the loudness of the public data was set and are not a measurement of the device, but they show that \"safe on five recordings\" is not \"safe\", and that the gain in murmur level in the table rests on a boost the public recordings do not support."),
])

revise("45-listen.md", [
    ("Listen for which candidates keep the murmur clear without making it harsh.",
     "Listen for which candidates keep the murmur clear; harshness in the boosted candidates can come from the overload described above and not from the filter (compare with the same-loudness versions)."),
])

revise("50-comparison.md", [
    ("| Does the filter design or the upper edge matter? | Not measurably on clean windows | A steeper filter helps a little (about 3.5 BPM) | Differ slightly |",
     "| Does the filter design or the upper edge matter? | Not measurably on clean windows | Upper edge: no. Other designs 2 to 7 BPM worse than the planned one; the planned one applied twice 3.5 BPM better | Differ slightly |"),
    ("| First listening candidate 100–800 Hz with boost | Louder by two of three estimates | In the top group for murmur level and for telling murmurs apart | Agree |",
     "| First listening candidate 100–800 Hz | Louder by two of three estimates, with its boost | In the top group for telling murmurs apart and for letting them stand out, independent of the boost | Agree |"),
    ("| Are the fixed boosts safe? | Safe on the five recordings by construction | Overload on 97 to 100 % of the modelled public recordings | Differ |",
     "| Is there room for a fixed boost? | Yes with a lower edge of 50 Hz or more (5.9 dB at 100 Hz), on the five recordings | No: overload on 97 to 100 % of the modelled public recordings even without a boost | Differ |"),
    ("Both data sources support the BPM filter 40–150 Hz over the planned 25–150 Hz, and both support a listening filter with a lower edge near 100 Hz and a fixed boost over the planned 40–800 Hz.",
     "Both data sources support the BPM filter 40–150 Hz over the planned 25–150 Hz, and both support a listening filter with a lower edge near 100 Hz over the planned 40–800 Hz; the fixed boost that goes with it is supported by Nico's recordings only."),
])

revise("60-tail.md", [
    ("3. **Real time is not required for counting, and not needed.** The stored 8 seconds could be processed as a whole within the processor budget, but the gain came from the steeper filter, which works while recording.",
     "3. **Real time is not required for counting, and so far not needed.** The stored 8 seconds could be processed as a whole within the processor budget. Filtering forwards and backwards brought no gain of its own; the loudness curve of the Springer method brought more, but only with look-ahead tested, and less than the improved choice of the peak, which works while recording."),
    ("The boost needs a safety margin or a limiter: the values found on five recordings overloaded on almost all modelled public recordings.",
     "The boost needs a safety margin or a limiter: the room for it was found on five recordings, and the modelled public recordings, as their loudness was set here, leave no such room."),
])
print("revisions applied")
