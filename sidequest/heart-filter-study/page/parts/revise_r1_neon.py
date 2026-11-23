"""Text revisions after council run 2 round 1 (Gemini Neon). Each replacement must match exactly once."""
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
    ("29 hours of heart sounds from 22 young men with an ECG as an independent heart-rate reference, at rest and during exercise, and recordings of 873 patients, mostly children, with and without heart murmurs.",
     "29 hours of heart sounds from 22 young men with an ECG as an independent heart-rate reference, at rest and during exercise, and recordings of 874 patients, mostly children, with and without heart murmurs."),
    ("The recommended **40–150 Hz** filter beats the planned 25–150 Hz filter and no filter on the public recordings too, now against an ECG.",
     "The recommended **40–150 Hz** filter beats the planned 25–150 Hz filter and no filter on the public recordings, now against an ECG and with either counting method."),
])

revise("20-public-data.md", [
    ("Three recordings of the first collection were left out: two are exact copies of other recordings filed under a different person, and one is marked by its authors as having no sound.",
     "Three recordings of the first collection were left out: two are exact copies of other recordings filed under a different person, and one is marked by its authors as having no sound. This leaves 22 of the 24 people (the two copies were the only recordings filed under their two names), and one of the 22 has no window with a reliable ECG, so most numbers rest on 21 people."),
    ("| Recordings used | 66 of 69 (about 29 hours): 8 of 30 seconds at rest, the others of 30 minutes while sitting, lying, walking, on a treadmill or on a bicycle | 2,888 recordings, 58,156 fully marked heartbeats |",
     "| Recordings used | 66 of 69 (about 29 hours): 8 of 30 seconds at rest, the others of 30 minutes while sitting, lying, walking, on a treadmill or on a bicycle | 2,888 recordings of 874 patients, 58,156 fully marked heartbeats |"),
    ("| Heart-sound level at rest (dB below full scale) | 9.7 | 9.7 | 9.7 |",
     "| Heart-sound level at rest (dB below full scale) | 9.6 | 9.7 | 9.7 |"),
])

revise("30-bpm-public.md", [
    ('caption="The same exercise recording as above with the improved counting method."',
     'caption="The same exercise recording as above with the improved counting method. This person belongs to the half on which the method was tuned."'),
    ("- **With the improved counting method the order stays the same and the gaps shrink** (test half, rest level: no filter 16.8 BPM, 25–150 Hz 15.9, 40–150 Hz 13.1, 60–150 Hz 11.5).",
     "- **With the improved counting method the order stays the same and the gaps shrink** (test half, rest level: no filter 16.8 BPM, 25–150 Hz 15.9, 40–150 Hz 13.1, 60–150 Hz 11.5).\n- **On Nico's recordings the improved counting method removes the difference between 25 and 40 Hz.** With it, the planned 25–150 Hz filter has no gross error either (0.30 BPM on clean windows, 0.36 on all, against 0.30 and 0.35 for 40–150 Hz). The single window that separated the two in the first part was a product of the first part's counting method. What Nico's recordings still rule out is the steep 60–150 Hz filter (8 gross errors, 2.7 BPM on all windows, also with the improved method)."),
    ("**Recommended BPM filter: still 40–150 Hz, gentle edges.** The public recordings confirm that it beats the planned 25–150 Hz filter and no filter. They would favour a lower edge of 50 to 60 Hz, but a steep 60 Hz edge failed on Nico's recordings, the only ones made with our own chain, so 40 Hz remains the cautious choice, and 50 Hz is worth testing on the device.",
     "**Recommended BPM filter: still 40–150 Hz, gentle edges.** The evidence for it over the planned 25–150 Hz filter now comes from the public recordings (better by 4.4 BPM with the first part's counting method and by 2.8 BPM with the improved one, test half); on Nico's recordings the two are equal once the counting method is improved. The public recordings would favour a lower edge of 50 to 60 Hz, but a steep 60 Hz edge failed on Nico's recordings, the only ones made with our own chain, so 40 Hz remains the cautious choice, and 50 Hz is worth testing on the device."),
])

revise("35-window-methods.md", [
    ("a loudness curve taken from the *logarithm* of the signal (which makes loud and soft beats more alike), and the same repeat-pattern search as here, but only between 0.5 and 2 seconds, so that it cannot report more than 120 BPM.",
     "a loudness curve taken from the *logarithm* of the signal (which makes loud and soft beats more alike), and a repeat-pattern search that, unlike the one of the first part, lets longer shifts count less, but only looks between 0.5 and 2 seconds, so that it cannot report more than 120 BPM."),
])

revise("40-listening-public.md", [
    ("Murmurs after the second heart sound are too rare in the collection to judge (5 patients, 4 of them analysed).",
     "Murmurs after the second heart sound are too rare in the collection to judge (5 patients, 4 of whom also have a murmur between the heart sounds; described but not tested)."),
    ("so the output overloads on 97 to 100 % of them even without any boost (99 % with no filter, 98 % with the planned 40–800 Hz filter, 97 % with the gentle 100–800 Hz filter, all at 0 dB).",
     "so the output of the listening candidates overloads on 90 to 99 % of them even without any boost (99 % with no filter, 98 % with the planned 40–800 Hz filter, 97 % with the gentle 100–800 Hz filter, all at 0 dB) and on 99.7 to 99.9 % with their boosts. Only the two narrow BPM filters stay mostly clear (the recommended 40–150 Hz filter overloads on 8 % with its boost)."),
    ("::callout{kind=\"limitation\"}\nThese are energy measures on other people's recordings,",
     "::callout{kind=\"limitation\"}\nAll filters were measured on the same marked stretches of each beat. A filter delays the sound slightly (the steep 100–800 Hz filter by up to 6 thousandths of a second at 100 Hz, the very steep 60–800 Hz filter by about 3.5), which moves a little heart-sound energy into the stretch counted as murmur and can flatter the steep filters in the measure against the heart sounds.\n\nThese are energy measures on other people's recordings,"),
    ('Candidates printed in grey were added for this comparison and are not among the listening samples." width="wide"}',
     'Candidates printed in grey were added for this comparison; they are not among the listening samples." width="wide"}'),
])

revise("45-listen.md", [
    ("(8 seconds each, from the murmur collection [17], passed through the model of our device input at rest level and then through the same simulated device).",
     "(8 seconds each, from the murmur collection [17], passed through the model of our device input at rest level and then through the same simulated device; offered with the fixed boosts and at equal loudness only, without the version \"as the device plays it today\")."),
])

revise("50-comparison.md", [
    ("| 40–150 Hz or the planned 25–150 Hz? | 40 Hz as a precaution; rested on one window | 40 Hz better by 4.4 BPM (3.3 to 5.5), against an ECG | Agree; now supported |",
     "| 40–150 Hz or the planned 25–150 Hz? | 40 Hz as a precaution; rested on one window, and equal once the counting method is improved | 40 Hz better by 4.4 BPM (3.3 to 5.5) against an ECG; by 2.8 BPM with the improved counting method | Public recordings decide |"),
    ("Both data sources support the BPM filter 40–150 Hz over the planned 25–150 Hz, and both support",
     "The public recordings support the BPM filter 40–150 Hz over the planned 25–150 Hz with either counting method, while Nico's recordings no longer separate the two once the counting method is improved; Nico's recordings are what rules out a steep 60 Hz edge. Both data sources support"),
])

revise("60-tail.md", [
    ("Supported by both data sources against the planned 25–150 Hz.",
     "Against the planned 25–150 Hz it is supported by the public recordings with either counting method; on Nico's recordings the two are equal once the counting method is improved."),
    ("The steps described on this page were read from the files `getHeartRateSchmidt.m`, `schmidt_spike_removal.m`, `Homomorphic_Envelope_with_Hilbert.m` and `default_Springer_HSMM_options.m`",
     "The steps described on this page were read from the files `getHeartRateSchmidt.m`, `schmidt_spike_removal.m`, `Homomorphic_Envelope_with_Hilbert.m` and `default_Springer_HSMM_options.m`, and for the three combined loudness curves also from `getSpringerPCGFeatures.m`, `Hilbert_Envelope.m` and `get_PSD_feature_Springer_HMM.m`"),
])
print("revisions applied")
