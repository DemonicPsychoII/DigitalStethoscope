"""Text revisions after council run 2 round 3 (Gemini Neon) and the final review paragraph."""
from pathlib import Path

PARTS = Path(__file__).resolve().parent


def revise(name, pairs):
    path = PARTS / name
    text = path.read_text(encoding="utf-8")
    for before, after in pairs:
        assert text.count(before) == 1, (name, before[:70], text.count(before))
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")


revise("50-comparison.md", [
    ("the seven prepared candidates other than the BPM filter (no filter and the six listening filters)",
     "the seven prepared candidates other than the two BPM filters (no filter and the six listening filters)"),
    ("| Error falls up to 80 Hz; steep 60 Hz best |", "| At rest level the error falls up to 80 Hz; steep 60 Hz best |"),
])

revise("40-listening-public.md", [
    ("for the five candidates with a boost above zero,", "for the five listening candidates with a boost above zero,"),
])

revise("35-window-methods.md", [
    ("*Estimated cost per variant on the ESP32-S3.",
     "*Estimated cost per variant on the ESP32-S3 (the first part's own count of the memory of its method came to about 8 kB; this count gives 7 kB)."),
])

revise("60-tail.md", [
    ("These were corrected as well. COUNCIL_ROUND3_PLACEHOLDER",
     "These were corrected as well. In a third and last round two reviewers again scored 8 and wrote that the page would be at 9 once two or three remaining sentences were replaced (a caveat missing in one design point, in the note at the listening samples and in one table cell, and a statement that held at one loudness level only); these sentences were replaced as they proposed, and the result was not reviewed again. The third reviewer (GPT Astra) could not take part in the last round because its provider's usage limit was reached, so it gave no score there. The target of 9 from every reviewer was therefore not formally reached."),
])
print("revisions applied")
