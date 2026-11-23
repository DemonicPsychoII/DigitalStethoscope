"""Text revisions after council run 2 round 3 (Claude Fable)."""
from pathlib import Path

PARTS = Path(__file__).resolve().parent


def revise(name, pairs, expected_count=1):
    path = PARTS / name
    text = path.read_text(encoding="utf-8")
    for before, after in pairs:
        assert text.count(before) == expected_count, (name, before[:70], text.count(before))
        text = text.replace(before, after)
    path.write_text(text, encoding="utf-8")


revise("60-tail.md", [
    ("The stored 8 seconds could be processed as a whole within the processor budget.",
     "By the estimated processor time, the stored 8 seconds could be processed as a whole; whether the larger variants fit in memory beside the firmware is open."),
    ("(0.1 to 0.3 BPM over", "(0.07 to 0.25 BPM over"),
])

revise("45-listen.md", [
    ("and on the public murmur recordings it makes the murmur 4.1 dB stronger than Raw and is in the top group for telling murmur from no murmur.",
     "and on the public murmur recordings it is in the top group for telling murmur from no murmur, with or without the boost. The 4.1 dB by which the murmur comes out stronger than Raw there is the boost itself, and with that boost the output overloads on 99.8 % of the modelled public recordings."),
])

revise("30-bpm-public.md", [
    ("The listening candidate 100–800 Hz was as good an input for counting as 40–150 Hz here (26.8 BPM); the first part's finding that it is a poor input came from the low-pitched disturbances in Nico's recordings, which the public recordings lack.",
     "At rest level the listening candidate 100–800 Hz was as good an input for counting as 40–150 Hz (26.8 BPM); at the overload level it was 6.1 BPM worse (26.3 against 20.2 BPM, range 3.8 to 8.4). The first part's finding that it is a poor input came from the low-pitched disturbances in Nico's recordings, which the public recordings lack; the overload level shows that the public recordings do not clear it as an input for counting either."),
    ("(8 gross errors, 2.7 BPM on all windows, also with the improved method;",
     "(with the improved method still 8 gross errors and 2.7 BPM on all windows;"),
    ("the new rule shows 87 to 88 % of the windows", "the new rule shows 87 to 88 % of the windows on the test half"),
])

revise("35-window-methods.md", [
    ("The count uses the last 8 seconds, which sit in the device's memory.",
     "The count uses the last 8 seconds. The planned design keeps only their loudness curve in memory (800 values); keeping the sound itself as well is possible and costs the extra memory shown in the table below."),
    ("−3.6 (−4.6 to −2.7)", "−3.6 (−4.5 to −2.7)"),
])
revise("35-window-methods.md", [("−8.1 to −2.2", "−8.0 to −2.2")], expected_count=2)

revise("50-comparison.md", [
    ("by 2.8 BPM with the improved counting method", "by 2.8 BPM with the improved counting method (test half, not tested on its own)"),
    ("independent of the boost", "with or without the boost"),
])
print("revisions applied")
