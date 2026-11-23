"""Text revisions after council run 2 round 2 (Claude Fable). Each replacement must match exactly once."""
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
    ("Filtering forwards and backwards brings no gain of its own;", "Filtering forwards and backwards brings almost no gain of its own;"),
    ("on the public recordings, now against an ECG and with either counting method.",
     "on the public recordings, now against an ECG, with the counting method of the first version and, by a smaller margin that was not tested on its own, with the improved one."),
])

revise("10-chain-measurement.md", [
    ("(membrane side, at the louder setting: by a few dB at 400 Hz to 1 kHz and by up to about 20 dB near 2.5 kHz)",
     "(membrane side, at the louder setting: by 1 to 11 dB between 400 Hz and 1 kHz and by up to about 20 dB near 2.5 kHz; from the result files of the session [13])"),
])

revise("20-public-data.md", [
    ("(single recordings differ: typically 11 to 32 %)",
     "(the typical single recording reaches less: 23 % in the collection with ECG and 20 % in the murmur collection)"),
])

revise("30-bpm-public.md", [
    ("No filter and a lower edge of 10 Hz are the worst choices (33.5 and 33.7 BPM).",
     "Of the lower edges in the table, no filter and 10 Hz are the worst (33.5 and 33.7 BPM)."),
    ("What Nico's recordings still rule out is the steep 60–150 Hz filter (8 gross errors, 2.7 BPM on all windows, also with the improved method).",
     "What Nico's recordings still speak against is the steep 60–150 Hz filter (8 gross errors, 2.7 BPM on all windows, also with the improved method; all 8 lie in the disturbed windows, on clean windows it reaches 0.32 BPM)."),
])

revise("35-window-methods.md", [
    ("forwards-and-backwards was better than twice-forwards by 0.07 BPM at rest level (a range that includes zero: −0.38 to +0.24) and by 0.25 BPM at overload level (−0.49 to −0.02;",
     "the difference forwards-and-backwards minus twice-forwards was −0.07 BPM at rest level (a range that includes zero: −0.38 to +0.24) and −0.25 BPM at overload level (−0.49 to −0.02;"),
    ("- **Springer's preparation helps more, but only with the half-rate check and only at higher heart rates.** Widening its search to 200 BPM alone changes little at rest level (−1.2 BPM, a range that includes zero).",
     "- **Springer's preparation helps more, mainly with the half-rate check and only at higher heart rates.** Widening its search to 200 BPM alone changes little at rest level (−1.2 BPM, a range that includes zero) but improves the overload level by 5.3 BPM (−8.1 to −2.2)."),
    ("below 70 BPM it is 7 to 11 BPM worse.",
     "below 70 BPM it is 7 to 11 BPM worse at rest level and 4 to 10 BPM worse at overload level."),
    ("gives the same error and needs 31 kilobytes instead of 512.",
     "gives the same error and needs 73 kilobytes instead of about 1 MB (see the table below)."),
])

revise("40-listening-public.md", [
    ("and on 99.7 to 99.9 % with their boosts.",
     "and, for the five candidates with a boost above zero, on 99.7 to 99.9 % with their boosts."),
])

revise("50-comparison.md", [
    ("| Yes: no filter is the worst choice (33.5 against 26.6 BPM) | Agree |",
     "| Yes: no filter is 6.9 BPM worse than the recommended filter (33.5 against 26.6 BPM) | Agree |"),
    ("No: the eight prepared listening candidates other than the BPM filter overload on 90 to 99 %",
     "No: the seven prepared listening candidates other than the BPM filter overload on 90 to 99 %"),
    ("The public recordings support the BPM filter 40–150 Hz over the planned 25–150 Hz with either counting method,",
     "The public recordings support the BPM filter 40–150 Hz over the planned 25–150 Hz with the first part's counting method and, by a smaller untested margin, with the improved one,"),
    ("Nico's recordings are what rules out a steep 60 Hz edge.",
     "Nico's recordings are what speaks against a steep 60 Hz edge."),
])

revise("60-tail.md", [
    ("Filtering forwards and backwards brought no gain of its own;",
     "Filtering forwards and backwards brought almost no gain of its own (0.1 to 0.3 BPM over the same filter applied twice while recording);"),
    ("it is supported by the public recordings with either counting method;",
     "it is supported by the public recordings (by 4.4 BPM with the first part's counting method, by an untested 2.8 BPM with the improved one);"),
])
print("revisions applied")
