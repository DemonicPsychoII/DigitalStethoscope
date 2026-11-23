"""Text revisions after the late round-3 review by GPT Astra (run 2), applied to the version-4 text."""
from pathlib import Path

PARTS = Path(__file__).resolve().parent


def revise(name, pairs):
    path = PARTS / name
    text = path.read_text(encoding="utf-8")
    for before, after in pairs:
        assert text.count(before) == 1, (name, before[:70], text.count(before))
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")


revise("30-results-bpm.md", [
    ("and the upper edge made no difference (26.6 to 27.2 BPM for upper edges from 100 to 800 Hz, lower edge 40 Hz)",
     "and the upper edge had a small effect (lower edge 40 Hz: compared with 150 Hz, an upper edge of 100 Hz raised the mean error by 0.6 BPM at rest level, and an upper edge of 800 Hz raised it by 1.1 BPM at overload level)"),
])

revise("40-results-listening.md", [
    ("- One result is unexplained: the unweighted ratio of murmur to heart sounds falls for every filter (by 0.6 to 2.6 dB) although the score built on it rises.",
     "- One result is unexplained: the unweighted ratio of murmur to heart sounds falls for every filter (by 0.6 to 2.6 dB), although the score built on it rises for every candidate except the BPM filter as first planned (25–150 Hz), for which it falls from 0.53 to 0.51."),
    ("Upper edge: no. Other designs 2 to 7 BPM worse than the planned one; the planned one applied twice 3.5 BPM better",
     "The upper edge changed the mean error by up to about 1 BPM. Other designs 2 to 7 BPM worse than the gentle design; at rest level the recommended 40–150 Hz filter applied twice was 3.5 BPM better than applied once"),
])

revise("50-discussion-end.md", [
    ("The third reviewer (GPT Astra) could",
     "(Its review arrived later, on the same day, with a score of 8 and three further factual corrections: a small effect of the upper edge that the text had called none, one filter for which a murmur score fell, and a mislabelled filter in the comparison table. They are corrected in this version.) At the time of the last round, the third reviewer (GPT Astra) could"),
])
print("revisions applied")
