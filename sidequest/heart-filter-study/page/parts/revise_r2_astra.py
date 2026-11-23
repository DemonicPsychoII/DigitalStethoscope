"""Text revisions after council run 2 round 2 (GPT Astra). Each replacement must match exactly once."""
from pathlib import Path

PARTS = Path(__file__).resolve().parent


def revise(name, pairs):
    path = PARTS / name
    text = path.read_text(encoding="utf-8")
    for before, after in pairs:
        assert text.count(before) == 1, (name, before[:70], text.count(before))
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")


revise("00-summary.md", [
    ("Counting on the stored 8 seconds in non-real time is possible on the device.",
     "By the estimated processor time, the heart rate could be counted once per second on the stored 8 seconds as a whole; whether the larger methods fit beside the running firmware needs a check on the device."),
    ("Of the six listening filters prepared in the first version, the planned 40–800 Hz filter is the weakest for murmurs.",
     "Of the six filters prepared for listening in the first version, the planned 40–800 Hz filter gave the lowest murmur level and the lowest score for telling murmur from no murmur."),
])

revise("10-chain-measurement.md", [
    ("the only reliable quantity, bell against membrane, describes the difference between the two sides of our chest-piece.",
     "the only quantity that is reliable at the low pitches of the heart sounds, bell against membrane, describes the difference between the two sides of our chest-piece."),
])

revise("35-window-methods.md", [
    ("All sensible variants lie within about 0.1 BPM of each other, which these five recordings cannot tell apart.",
     "On all 255 windows the mean error was 0.35 BPM for the method of the first part, 0.39 for forwards-and-backwards filtering, 0.44 for the widened Springer preparation with the half-rate check and 0.69 for the three combined loudness curves; differences of a tenth of a BPM cannot be told apart on five recordings."),
    ("Widening its search to 200 BPM alone changes little at rest level (−1.2 BPM, a range that includes zero) but improves the overload level by 5.3 BPM (−8.1 to −2.2).",
     "Widening its search from 120 to 200 BPM reduced its own mean error by 8.3 BPM at rest level and by 9.7 BPM at overload level. Against the method of the first part, the widened version without the half-rate check is 1.2 BPM better at rest level (range for the difference −3.7 to +1.4, which includes zero) and 5.3 BPM better at overload level (−8.1 to −2.2)."),
    ("**Counting in non-real time looks possible on the device by processor time.",
     "**By the estimated processor time, counting in non-real time is possible on the device; whether the larger variants fit in memory beside the firmware is open.**"),
    (" Filtering forwards and backwards brings almost no gain of its own:** a steeper filter",
     " **Filtering forwards and backwards brings almost no gain of its own:** a steeper filter"),
])

revise("40-listening-public.md", [
    ("as a score from 0.5 (no better than chance) to 1 (perfect).",
     "as a score: the chance that a patient with a murmur gets a higher value than a patient without one. It runs from 0 to 1; 0.5 is no better than chance, 1 is perfect."),
    ("| Candidate (boost) |", "| Candidate (boost used in the simulation) |"),
    ("| No filter (Raw) | 0 | 0 | 0.53 | 0.79 |", "| No filter (Raw, −0.010 dB) | 0 | 0 | 0.53 | 0.79 |"),
    ("| 40–800 Hz, gentle (design candidate, −0.2 dB) |", "| 40–800 Hz, gentle (design candidate, −0.236 dB) |"),
    ("| **100–800 Hz, gentle (+5.9 dB)** |", "| **100–800 Hz, gentle (+5.975 dB)** |"),
    ("| 100–800 Hz, steep (+7.2 dB) |", "| 100–800 Hz, steep (+7.200 dB) |"),
    ("| 150–800 Hz, steep (+9.7 dB) |", "| 150–800 Hz, steep (+9.760 dB) |"),
    ("| 60–800 Hz, very steep (+3.8 dB) |", "| 60–800 Hz, very steep (+3.840 dB) |"),
    ("| Above 80 Hz only (+3.4 dB) | +3.4 | +2.6 | 0.68 | 0.90 |", "| Above 80 Hz only (+3.460 dB) | +3.4 | +2.6 | 0.68 | 0.89 |"),
    ("| 25–150 Hz (BPM filter as first planned, −1.8 dB) |", "| 25–150 Hz (BPM filter as first planned, −1.843 dB) |"),
    ("| 40–150 Hz (recommended BPM filter, +0.3 dB) |", "| 40–150 Hz (recommended BPM filter, +0.358 dB) |"),
    ("*Murmur measures on the public murmur data at rest level (178 patients with a murmur, 695 without).",
     "*Murmur measures on the public murmur data at rest level (178 patients with a murmur, 695 without). The boosts are the largest safe values from the first part, as used in the simulation; a setting on the device would be rounded down (5.9 dB for the gentle 100–800 Hz filter)."),
    ("- **Of the six listening filters prepared in the first part, the planned 40–800 Hz filter is the weakest for murmurs**: the murmur comes out 1.9 dB quieter than without a filter, and it separates murmur from no murmur less well than every candidate with a higher lower edge.",
     "- **Of the six filters prepared for listening in the first part, the planned 40–800 Hz filter gave the lowest murmur level and the lowest score on the heart-sound measure**: the murmur comes out 1.9 dB quieter than without a filter, and it separates murmur from no murmur less well than every candidate with a higher lower edge."),
    ("and low-pitched ones not at all (0.50, for every filter).",
     "and low-pitched ones not at all (0.50; across all candidates 0.44 to 0.51, every range including chance)."),
    ("and the scores for telling murmur from no murmur are highest (0.68 to 0.72 and 0.88 to 0.91). These two results do not depend on the boost.",
     "and the scores for telling murmur from no murmur are highest (0.68 to 0.72 and 0.88 to 0.91). These two results hardly depend on the boost (for the gentle 100–800 Hz filter the first score is 0.696 without a boost and 0.701 with it)."),
])

revise("50-comparison.md", [
    ("Nico's five recordings did not trigger it. This is a weakness of the method that five recordings could not reveal, not a difference between the people.",
     "On Nico's recordings the first part's counting method gave no estimate at one third of the rate with the recommended 40–150 Hz filter, but it did with other filters (1 window with the planned 25–150 Hz filter, 2 with the steep 60–150 Hz filter, 4 without a filter). The public recordings showed how often the same error occurs with the recommended filter at high heart rates."),
    ("| Weakest of the six prepared listening filters for murmurs (only the BPM filter 25–150 Hz is weaker by murmur level) | Agree |",
     "| Of the six filters prepared for listening, the lowest murmur level and the lowest score on the heart-sound measure | Agree |"),
])

revise("60-tail.md", [
    ("Both data sources point to a lower edge near 100 Hz with a fixed boost instead of the planned 40–800 Hz.",
     "Both data sources favour testing a lower edge near 100 Hz instead of the planned 40–800 Hz. Nico's five recordings allowed a boost of 5.9 dB with it. On the modelled public recordings the filter improved the score for telling murmur from no murmur without any boost (0.53 to 0.70), and 99.8 % of the recordings reached the output limit at the tested boost."),
    ("\"An open-access simultaneous electrocardiogram and phonocardiogram database,\" 2021; title as listed on the dataset page, place of publication not verified here)",
     "\"An open-access simultaneous electrocardiogram and phonocardiogram database,\" bioRxiv, 2021, doi:10.1101/2021.05.17.444563; title as listed on the dataset page, place of publication and DOI as found by one of the reviewers of this read)"),
])
print("revisions applied")
