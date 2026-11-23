"""Assembles page/read.md (version 3) from the previous read (page/read.v2.md) and the text parts in this folder."""
import re
from pathlib import Path

STUDY = Path(__file__).resolve().parents[2]
PARTS = STUDY / "page" / "parts"
old = (STUDY / "page" / "read.v2.md").read_text(encoding="utf-8")


def part(name):
    return (PARTS / name).read_text(encoding="utf-8").rstrip() + "\n"


def section(title):
    start = re.search(r"^## " + re.escape(title) + r"\n", old, re.M)
    assert start, title
    following = re.search(r"^## ", old[start.end():], re.M)
    return old[start.start(): start.end() + following.start() if following else len(old)]


def replace_once(text, before, after):
    assert before in text, before[:70]
    return text.replace(before, after, 1)


question = section("The question")
recorded = replace_once(section("What was recorded"), "## What was recorded", "## The own recordings")
simulated = replace_once(
    section("How the device was simulated"),
    " At lower volume settings the simulation limits the signal before the volume step, while the design does so after it; this does not affect any number here.",
    " In the first version the simulation limited the signal before the volume step at lower volume settings, while the design does so after it; this is corrected in this version and does not change any number here (at full volume the output is identical value for value).",
)
reference = section("What the heart rate was compared with")
reference = replace_once(reference, "## What the heart rate was compared with", "## What the heart rate was compared with in the own recordings")
reference = replace_once(
    reference,
    "There was no independent heart-rate sensor: no ECG, watch or pulse oximeter. The reference was derived from the recordings themselves. It is weaker than an ECG.",
    "For Nico's recordings there was no independent heart-rate sensor: no ECG, watch or pulse oximeter. The reference was derived from the recordings themselves. It is weaker than an ECG. In this version the method was checked against an ECG on public recordings (see the results against an ECG below).",
)
heart_rate = section("Results: heart rate")
heart_rate = replace_once(heart_rate, "## Results: heart rate", "## Results: heart rate on the own recordings")
heart_rate = replace_once(
    heart_rate,
    "For the filters that first reduce the data rate, the share of invalid windows in the result files is wrong because of an error in how overloaded values are counted; their mean errors are not affected.",
    "For the filters that first reduce the data rate, the share of invalid windows in the result files of the first version was wrong because of an error in how overloaded values were counted (31 windows wrongly marked invalid); the error is corrected in the code of this version, the tables of this section were not recomputed, and their mean errors are not affected.",
)
heart_rate = replace_once(
    heart_rate,
    "The project requires the result",
    "This section is the first part of the study, on Nico's five recordings, unchanged in its numbers. The next section tests the same filters and the same counting method against an ECG.\n\nThe project requires the result",
)
listening = section("Results: listening")
listening = replace_once(
    listening,
    "## Results: listening\n",
    "## Results: listening\n\nThe first three subsections are the first part of the study, on Nico's five recordings. The fourth tests the same candidates on public recordings with murmurs.\n",
)
listening = replace_once(
    listening,
    'The \\"25–150 Hz (BPM position)\\" entry is the BPM filter as originally planned; the recommended 40–150 Hz version was not part of the listening samples.',
    'The \\"25–150 Hz (BPM position)\\" entry is the BPM filter as originally planned. The recommended 40–150 Hz filter is not in this figure; it was added to the listening samples in this version (largest safe boost +0.358 dB).',
)
decibel_box = listening[listening.index('::term{name="decibel (dB)"}'): listening.index("### Why a filter can make overload worse")]
listening = listening.replace(decibel_box, "")
listening = listening[: listening.index("### Listen and compare")] + part("40-listening-public.md") + "\n"

new = "\n".join([
    part("00-summary.md"), question.rstrip() + "\n", recorded.rstrip() + "\n", part("10-chain-measurement.md"),
    part("20-public-data.md"), simulated.rstrip() + "\n", reference.rstrip() + "\n", heart_rate.rstrip() + "\n",
    part("30-bpm-public.md"), part("35-window-methods.md"), listening.rstrip() + "\n", part("45-listen.md"),
    part("50-comparison.md"), part("60-tail.md"),
])
(STUDY / "page" / "read.md").write_text(new, encoding="utf-8")
print(len(new), "characters written")
