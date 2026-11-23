# Council review, round 2: "Which filters should the digital stethoscope use?"

You are one of three independent reviewers of round 2. **Read-only: do not edit, create, commit, push, publish or post anything, and do not start subagents.** You may run read-only commands and Python one-liners (Python: `C:/Users/nicop/Desktop/heart-filter-study/.venv/Scripts/python.exe`; scratch files only in a temp directory outside the study folder). Time budget: about 15 minutes. No history is available to you; everything is here.

## What to review

The revised report source `C:/Users/nicop/Desktop/heart-filter-study/page/read.md` (Markdown with `::directives`; built page `page/site/index.html`; figures `page/figures/*.png` with a description each in `page/figures/*.txt`). It is a plain-language scientific read for the project owner about choosing the listening filter and the heart-rate (BPM) filter of a digital stethoscope from a simulation with five own recordings.

Evidence in the study folder `C:/Users/nicop/Desktop/heart-filter-study/`: `BRIEF.md`, `STATE.md` (section "Council" records round 1), `FINDINGS.md`, `reference/SUMMARY.md`, `reference/*.json`, `results/SUMMARY.md`, `results/bpm_filter_grid.csv` (final counting method = rows with `estimator == "envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check"`, first draft = `"default"`), `results/bpm_per_window.csv`, `results/bpm_listening_filters_as_analysis.csv`, `listening/SUMMARY.md`, `listening/metrics_summary.csv`, `listening/metrics.csv`, `page/tables/*.csv`, code in `src/`. Firmware and design documents (read-only): `C:/Users/nicop/.t3/worktrees/DigitalStethoscope/feature-audio-chain-swe-2447cecce9041295/` (`AGENTS.md` section "Thesis sources"; `Development/system/design/system/parameters.md`; `Development/system/requirements/system-requirements.md`).

## Round 1 (three reviewers, each 6/10) and how each finding was handled

Round 2 checks **the changed text and figures and the open findings only**. Verify that each fix below is actually present and correct, and look for errors introduced by the rewrite. Do not raise again what was declined with a reason.

Fixed in the text (`read.md`):
1. "A fixed boost of 6 dB" clips (safe value 5.975 dB) → now "just under 6 dB", setting "5.9 dB", and the exact value is given.
2. "Reference good to ±1.5 BPM" was not demonstrated → removed everywhere; the text now reports the observed agreement (at most 1.8 BPM on clean windows), the actual rule for clean windows (no detected disturbance, no uncertain beat, method spread below 3 BPM), and that errors in disturbed windows are differences from an uncertain value.
3. "Adding one check" → both changes of the final counting method are named (smoother loudness curve: two smoothing steps at 5 Hz; half-rate check), with 0.70 → 0.51 → 0.30 BPM; heading scoped to clean signal; design item 2 lists both.
4. "1,258 of 1,310 … between 0.3 and 0.4" → "0.29 to 0.44 BPM"; the 52 exceptions report a third of the rate in part of one recording.
5. "Overload on every beat" → "about one beat in three (42 of 129 and 45 of 127 beats)", "overload on many beats"; overload is at the lower limit.
6. "The same order of steps" → scoped to full volume, with the difference at lower volume stated.
7. Validity rule statement → scoped: never triggered on clean windows with the recommended filter; with no filter flagged 5 of 16 gross errors, missed all 8 during movement; wrong invalid share for rate-reduced filters disclosed.
8. "From 30 Hz upward no gross error" and "design and upper edge do not matter" → scoped to the gentle Butterworth type with upper edge 150 Hz (30–80 Hz) and to clean windows; other designs' gross errors in disturbed windows disclosed.
9. "25 vs 40 Hz rests on two disturbances" → "a single 8-second window at the start of one recording, where the reference itself is uncertain"; recommendation labelled a precaution.
10. Reference not independent (same 25–150 Hz range; third method learns from the first two; disturbance detection by 3–20 Hz energy with thresholds set on these recordings; single-method gap fills) → stated in the reference section and in the limitations.
11. "Below 20 Hz cannot be heard [3]" → removed; ISO 226 described as covering 20 Hz–12.5 kHz.
12. Listening numbers: gentle/steep named for every value; upper-edge statement scoped to a 40 Hz lower edge with the 100 Hz case given; "under 2.4 % above 1 kHz" scoped (average per candidate; 8.2 % in one recording); the expected gain of the provisional 100–800 Hz candidate stated with all three estimates.
13. Plain language: order (gentle/steep), FIR, 32-bit numbers, 24 bit, kHz, ms, A-weighting, "after-ring" (was "Ringing"), mean error defined; dB box moved before first use in the listening results; "high-pass/low-pass" and "gain" replaced or explained; audio player rows now use the table's plain names.
14. Sourcing: REQ-06 is a session requirement whose tolerance the study borrows for windows ("whichever is larger" marked as this study's reading); EC13 "reported"; cost estimate sourcing scoped; access dates added where recorded in the project; source [12] cited inline; source [13] for the 22 November measurement; LUFS unit.
15. Limitations added: half-rate check may double the rate at other chest positions; two chest positions (not one); 35 non-overlapping windows; counting method not checked on held-out data.

Fixed in figures (`src/page_figures.py`): heart-sound arrows in `beat_closeup` now from the reference beat marks (second sound at 150 ms / 246 ms after the first), labels separated, "cut off at full scale"; ±1.5 BPM band removed from `bpm_highpass_effect`; "cannot be heard" removed from `where_the_energy_is`; "simulated device estimate" in `bpm_tracks`; "overload on many beats" / "overload only at the start"; vocabulary aligned with the text ("counting method", "clean windows", "values", "rate-reduced", "studied here", "boost"); `shortlist_responses` lines distinguishable.

Declined, with reason (do not raise again):
- Fixing the code bug in the invalid-window share for rate-reduced filters and changing the simulation's volume/limit order: neither affects any published number; both are disclosed on the page and logged as follow-ups.
- Adding the recommended 40–150 Hz filter to the listening samples: outside this round; stated on the page that the BPM-position sample is the originally planned 25–150 Hz filter.
- Renaming internal file names such as `bpm_estimator_vs_filter.png`: not visible to the reader.

## Output format (final message)

- **Score: N/10** for the read as it now stands (10 = publish as is; 9 = only optional polish left).
- **Blocking findings** (must fix before publishing): numbered, each with a quote of the location, what is wrong, the evidence (file and value), and the proposed fix. Include any round-1 fix that is missing, wrong, or introduced a new error.
- **Non-blocking findings**: numbered, brief.
- **Round-1 fixes verified** (short list).
Be specific and terse. No praise padding. Additions beyond the brief's scope are follow-ups, not blocking.
