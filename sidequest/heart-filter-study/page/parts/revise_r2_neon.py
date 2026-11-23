"""Text revisions after council run 2 round 2 (Gemini Neon). Each replacement must match exactly once."""
from pathlib import Path

PARTS = Path(__file__).resolve().parent


def revise(name, pairs):
    path = PARTS / name
    text = path.read_text(encoding="utf-8")
    for before, after in pairs:
        assert text.count(before) == 1, (name, before[:70], text.count(before))
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")


revise("45-listen.md", [
    ('::audio-compare{excerpt="no-murmur-child" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico\'s five recordings. On this public recording some boosted candidates overload the output (see the note above)."',
     '::audio-compare{excerpt="no-murmur-child" variants="madeup,matched" explain-madeup="Each candidate with the fixed boost found safe on Nico\'s five recordings. No candidate overloads the output on this sample (the highest peak stays 0.2 dB below full scale)."'),
])

revise("00-summary.md", [
    ("Of the eight candidates prepared for listening, the planned 40–800 Hz filter is the weakest listening filter for murmurs.",
     "Of the six listening filters prepared in the first version, the planned 40–800 Hz filter is the weakest for murmurs."),
])

revise("40-listening-public.md", [
    ("- **Of the listening candidates prepared in the first part, the planned 40–800 Hz filter is the weakest for murmurs**",
     "- **Of the six listening filters prepared in the first part, the planned 40–800 Hz filter is the weakest for murmurs**"),
])

revise("50-comparison.md", [
    ("| Weakest of the eight prepared listening candidates for murmurs | Agree |",
     "| Weakest of the six prepared listening filters for murmurs (only the BPM filter 25–150 Hz is weaker by murmur level) | Agree |"),
    ("No: the seven prepared listening candidates other than the BPM filter overload on 90 to 99 %",
     "No: the seven prepared candidates other than the BPM filter (no filter and the six listening filters) overload on 90 to 99 %"),
])

revise("20-public-data.md", [
    ("mostly children; 178 with a murmur between the heart sounds, 695 without |",
     "mostly children; of the 874 used, 178 with a murmur between the heart sounds, 695 without, and 1 with a murmur only after the second heart sound |"),
])

revise("35-window-methods.md", [
    ('alt="Mean heart-rate error of fourteen counting variants', 'alt="Mean heart-rate error of fifteen counting variants'),
    ("| Springer's preparation, range widened to 200 BPM | 0.38 / 0.44 | −1.2 (−3.7 to +1.4) | −5.3 |",
     "| Springer's preparation, range widened to 200 BPM | 0.38 / 0.44 | −1.2 (−3.7 to +1.4) | −5.3 (−8.1 to −2.2) |"),
])
print("revisions applied")
