"""Text revisions after council run 2 round 1 (GPT Astra). Each replacement must match exactly once."""
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
    ("it halves the error (28.4 to 13.1 BPM) and leaves the result on Nico's recordings unchanged,",
     "it halves the error (28.4 to 13.1 BPM) and leaves the error on Nico's recordings unchanged (it shows 97.6 % of their windows as valid instead of 99.6 %),"),
    ("The planned 40–800 Hz filter is the weakest listening candidate for murmurs.",
     "Of the eight candidates prepared for listening, the planned 40–800 Hz filter is the weakest listening filter for murmurs."),
])

revise("10-chain-measurement.md", [
    ("the path through chest-piece and tube was 2 to 14 dB stronger in air than the bare microphone (membrane side, at the louder setting), which neither supports nor contradicts",
     "the path through chest-piece and tube was stronger in air than the bare microphone at most pitches (membrane side, at the louder setting: by a few dB at 400 Hz to 1 kHz and by up to about 20 dB near 2.5 kHz), which neither supports nor contradicts"),
    ("the model of the device chain could use a measured curve instead of the tone-balance matching used here, and the overload at the microphone could be related to sound pressure. It would still be a measurement in air; how the chest-piece behaves on skin would remain open.",
     "the model of the device chain could use a measured curve instead of the tone-balance matching used here. It would still be a comparison between arrangements, measured in air: how the chest-piece behaves on skin would remain open, and relating the overload at the microphone to a sound pressure would need a calibrated measuring microphone in addition."),
])

revise("20-public-data.md", [
    ("without that slow part only 3 of 129 and 5 of 127 beats would reach full scale instead of 42 and 45 (own analysis for this version).",
     "when the slow part is removed from the stored recordings afterwards, only 3 of 129 and 5 of 127 beats still reach full scale instead of 42 and 45 (own analysis for this version; the recordings were already cut off when stored, so how far the true peaks went beyond full scale is unknown)."),
    ("*How close the modelled public recordings come to the own recordings at rest level, without the matching variant (medians over recordings).*",
     "*How close the modelled public recordings come to the own recordings at rest level, without the matching variant (medians over recordings; computed on 20 recordings of the collection with ECG and 200 of the murmur collection).*"),
    ("and at the overload level 34 % of all beats reach full scale, as in Nico's recordings.",
     "and at the overload level 34 % of all beats taken together reach full scale, as in Nico's recordings (single recordings differ: typically 11 to 32 %)."),
])

revise("30-bpm-public.md", [
    ("So the clean windows of the first part were trustworthy.",
     "This supports trust in the clean windows of the first part; it does not replace an independent reference for Nico's own recordings, which still does not exist."),
    ("with the public sound merely converted to 16,000 values per second, the third peak still wins in 56 to 85 % of the affected windows.",
     "with the public sound merely converted to 16,000 values per second, the peak at three beats is still higher than the peak at one beat in 56 to 85 % of the affected windows."),
    ("Nico's five recordings also reach 149 BPM and showed no such error. Why they were spared was not examined;",
     "Nico's five recordings also reach 149 BPM and showed no such error with the recommended filter (the 52 filters with a steep 60 Hz lower edge did show it, in one recording after exercise). Why the recommended filter was spared there was not examined;"),
    ("- A wrong number is shown as valid in 6 % of the shown windows instead of 29 %.",
     "- A grossly wrong number (more than 20 % off) is shown as valid in 6 % of the shown windows instead of 29 %; counting every number outside the tolerance, 7 % instead of 31 %."),
    ("- **On Nico's recordings it changes nothing** with the recommended filter: 0.30 BPM on clean windows, 0.35 BPM on all, 255 of 255 within tolerance, as before; 97.6 % of the windows are shown as valid.",
     "- **On Nico's recordings the error does not change** with the recommended filter: 0.30 BPM on clean windows, 0.35 BPM on all, 255 of 255 within tolerance, as before. Fewer windows are shown as valid: 97.6 % instead of 99.6 %."),
    ("at overload level, and no filter is worst.",
     "at overload level, and it is better than no filter by 6.9 BPM. No filter and a lower edge of 10 Hz are the worst choices (33.5 and 33.7 BPM)."),
])

revise("35-window-methods.md", [
    ("- **On the public recordings, filtering forwards and backwards helps by 3.6 BPM, but not because it looks ahead.** Applying the same filter twice while recording, without any look-ahead, gives the same gain (3.5 BPM). The benefit is the steeper filter, not the cancelled delay.",
     "- **On the public recordings, filtering forwards and backwards helps by 3.6 BPM, but hardly because it looks ahead.** Applying the same filter twice while recording, without any look-ahead, recovers nearly all of that gain (3.5 BPM). Compared directly on the same windows, forwards-and-backwards was better than twice-forwards by 0.07 BPM at rest level (a range that includes zero: −0.38 to +0.24) and by 0.25 BPM at overload level (−0.49 to −0.02; paired check by one of the reviewers of this read on the stored results). So nearly all of the benefit is the steeper filter, and the small remainder gives little reason to store the sound for filtering alone."),
    ("- **All of these gains are smaller than that of the improved choice of the peak** described above (about 15 BPM on the test half, without look-ahead). The two were not combined.",
     "- **All of these gains are smaller than that of the improved choice of the peak** described above (about 15 BPM on the test half, without look-ahead). The two were not combined, and the two comparisons use different sets of people and windows (all 21 people and every fourth window here, the 10 test people and every window there), so the sizes can only be compared roughly."),
    ("| Springer's preparation and heart rate | 37 | 3.8 | 254 kB |",
     "| Springer's preparation and heart rate | 37 | 3.8 | 254 kB (223 kB of it in the fast internal memory) |"),
    ("*Estimated cost per variant on the ESP32-S3. All would fit at one update per second; the audio path keeps priority,",
     "*Estimated cost per variant on the ESP32-S3. By processor time, all would fit at one update per second; whether the larger variants also fit in memory is open (the internal memory is shared with the rest of the firmware, and the cost of using the slower external memory was not measured). The audio path keeps priority,"),
    ("**Counting in non-real time is possible on the device. Filtering forwards and backwards brings no gain of its own:** a steeper filter gives the same improvement while recording, at almost no cost.",
     "**Counting in non-real time looks possible on the device by processor time. Filtering forwards and backwards brings almost no gain of its own:** a steeper filter gives nearly the same improvement while recording, at almost no cost."),
])

revise("40-listening-public.md", [
    ("What \"audible\" and \"distinguishable\" mean in numbers was fixed before any result existed (decision of this study on 23 November 2026, following the project's notes on comparing filters [19]).",
     "What \"audible\" and \"distinguishable\" mean in numbers was fixed before any result existed (decision of this study on 23 November 2026, following the project's notes on comparing filters [19]), with one exception named below."),
    ("- **Murmur against the quiet part:** the energy of that stretch divided by the energy of the quiet stretch after the second heart sound.",
     "- **Murmur against the quiet part:** the average power of that stretch divided by the average power of the quiet stretch after the second heart sound (average, because the two stretches differ in length)."),
    ("The figure calls this score by its technical name, area under the curve.",
     "The figure calls this score by its technical name, area under the curve. Fixed in advance was the score built on the heart-sound measure; using the quiet-part measure as a second score was added afterwards and is exploratory, although it gives the higher scores. For patients with a murmur only recordings from places on the chest where the specialist had heard the murmur were used; for patients without a murmur, all their recordings. The scores therefore describe how well a known murmur stands out, not how well an unknown patient would be screened."),
    ("| Telling murmur from no murmur (heart-sound measure) | Telling murmur from no murmur (quiet-part measure) |",
     "| Telling murmur from no murmur (heart-sound measure, fixed in advance) | Telling murmur from no murmur (quiet-part measure, exploratory) |"),
    ("- **The planned 40–800 Hz filter is the weakest listening candidate for murmurs**: the murmur comes out 1.9 dB quieter than without a filter, and it separates murmur from no murmur less well than every candidate with a higher lower edge.",
     "- **Of the listening candidates prepared in the first part, the planned 40–800 Hz filter is the weakest for murmurs**: the murmur comes out 1.9 dB quieter than without a filter, and it separates murmur from no murmur less well than every candidate with a higher lower edge. (Among the candidates added for this comparison, 40–400 Hz is weaker still: 5.2 dB quieter.)"),
    ("The scores of this group overlap within their ranges; the data do not rank its members against each other.",
     "The tests fixed in advance compared each candidate with no filter, not the candidates with each other. Differences inside this group are small: for example the steep 100–800 Hz filter scores 0.016 higher than the gentle one on the heart-sound measure (0.010 to 0.021 when the same patients are re-drawn for both; a check by one of the reviewers of this read). Whether differences this small matter for listening is unknown."),
    ("- **The two BPM filters are unusable for listening to murmurs** (12 to 14 dB quieter).",
     "- **The two BPM filters are poor choices by the murmur level** (12 to 14 dB quieter than no filter), although the murmur still stands apart from the quiet part in them (scores 0.80 and 0.85). Whether they are unusable is for listening to decide."),
    ("The same order came out at the overload level, with the matched tone balance, and in two random halves of the patients.",
     "The broad pattern was the same at the overload level, with the matched tone balance, and in two random halves of the patients. Details change: with the matched tone balance the gentle 100–800 Hz filter and \"above 80 Hz only\" swap places in murmur level (+3.1 against +3.3 dB instead of +4.1 against +3.4 dB)."),
])

revise("50-comparison.md", [
    ("| Planned listening filter 40–800 Hz | No room for a boost; slightly quieter than no filter | Weakest listening candidate for murmurs | Agree |",
     "| Planned listening filter 40–800 Hz | No room for a boost; slightly quieter than no filter | Weakest of the eight prepared listening candidates for murmurs | Agree |"),
    ("| No: overload on 97 to 100 % of the modelled public recordings even without a boost | Differ |",
     "| No: the eight prepared listening candidates other than the BPM filter overload on 90 to 99 % of the 3,162 modelled public recordings even without a boost (the gentle 100–800 Hz filter on 97 %, and on 99.8 % with its boost) | Differ |"),
    ("The same explains why the broadcast loudness measure, which counts low tones fully, reverses its order,",
     "The same explains why the broadcast loudness measure, which gives low tones more weight than the other two estimates, reverses its order,"),
])

revise("60-tail.md", [
    ("The upper edge should be part of the listening test (800 Hz, 1 kHz, 2 kHz), because 800 Hz costs murmur level in the public recordings.",
     "The upper edge should become part of a later listening test (800 Hz, 1 kHz, 2 kHz), because 800 Hz costs murmur level in the public recordings; the samples on this page do not yet contain these variants."),
    ("The murmur data confirm it from the other side: the BPM filters are unusable for listening to murmurs.",
     "The murmur data point the same way from the other side: the BPM filters make a murmur 12 to 14 dB quieter."),
    ("1. Nico listens to the samples, including the murmur samples, and chooses the listening filter, its upper edge and its boost.",
     "1. Nico listens to the samples, including the murmur samples, and chooses the listening filter and its boost. A second set of samples with upper edges of 800 Hz, 1 kHz and 2 kHz should follow."),
    ("Details on people, device and activities are from the dataset page and its spreadsheet. The source asks users to also cite:",
     "Details on people, device and activities are from the dataset page and its spreadsheet. The source asks users to also cite its database article (A. Kazemnejad, P. Gordany, R. Sameni, \"An open-access simultaneous electrocardiogram and phonocardiogram database,\" 2021; title as listed on the dataset page, place of publication not verified here), the toolbox used by its authors (R. Sameni, *The Open-Source Electrophysiological Toolbox (OSET)*, version 3.14, https://github.com/alphanumericslab/OSET; not used in this study), and:"),
    ("*IEEE Journal of Biomedical and Health Informatics*, 2021 (as dated by its DOI), doi:10.1109/JBHI.2021.3137048. The article describing [17]; cited as given on the dataset page, full text not inspected.",
     "*IEEE Journal of Biomedical and Health Informatics*, vol. 26, no. 6, pp. 2524–2535, 2022, doi:10.1109/JBHI.2021.3137048. The article describing [17]; volume, pages and year as found in the publisher's record by one of the reviewers of this read on 23 November 2026; full text not inspected."),
    ("[21] D. Springer, *Logistic Regression-HSMM-based Heart Sound Segmentation* (program code, version 1.0), PhysioNet. [Project page](https://physionet.org/content/hss/1.0/), files downloaded 23 November 2026",
     "[21] D. Springer, *Logistic Regression-HSMM-based Heart Sound Segmentation* (program code, version 1.0), PhysioNet, 2019, doi:10.13026/vnt9-kf93 (year and DOI from the project page, as found by one of the reviewers of this read). [Project page](https://physionet.org/content/hss/1.0/), files downloaded 23 November 2026"),
    ("Licence GNU General Public License version 3 or later according to the file headers; the licence page of the project could not be opened (unverified).",
     "Licence GNU General Public License version 3 or later according to the file headers; the project page lists GPL version 3 (seen by one of the reviewers; this study's own download of the licence file failed)."),
])
print("revisions applied")
