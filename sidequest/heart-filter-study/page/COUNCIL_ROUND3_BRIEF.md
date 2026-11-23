# Council review, round 3 (final): "Which filters should the digital stethoscope use?"

You are one of three independent reviewers of round 3. **Read-only: do not edit, create, commit, push, publish or post anything, and do not start subagents.** You may run read-only commands and Python one-liners (Python: `C:/Users/nicop/Desktop/heart-filter-study/.venv/Scripts/python.exe`; scratch files only in a temp directory outside the study folder). Time budget: about 12 minutes. No history is available to you; everything is here.

## What to review

The revised report source `C:/Users/nicop/Desktop/heart-filter-study/page/read.md` (Markdown with `::directives`; built page `page/site/index.html` with `page/site/assets/page.js` for the audio players; figures `page/figures/*.png`, each described in `page/figures/*.txt`). It is a plain-language scientific read for the project owner about choosing the listening filter and the heart-rate (BPM) filter of a digital stethoscope from a simulation with five own recordings.

Evidence in `C:/Users/nicop/Desktop/heart-filter-study/`: `BRIEF.md`, `STATE.md` (section "Council"), `FINDINGS.md`, `reference/SUMMARY.md`, `reference/*.json`, `results/SUMMARY.md`, `results/bpm_filter_grid.csv` (final counting method = rows with `estimator == "envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check"`, first draft = `"default"`), `results/bpm_per_window.csv`, `results/bpm_listening_filters_as_analysis.csv`, `listening/SUMMARY.md`, `listening/metrics_summary.csv`, `listening/metrics.csv`, `page/tables/*.csv`, code in `src/`. Project documents (read-only): `C:/Users/nicop/.t3/worktrees/DigitalStethoscope/feature-audio-chain-swe-2447cecce9041295/` (`AGENTS.md` section "Thesis sources"; `Development/system/design/system/parameters.md`; `Development/system/requirements/system-requirements.md`).

## History

Round 1: 6 / 6 / 6. Round 2: 8 / 8 / 9 (one reviewer had no blocking finding). Round 1 handling is listed in `page/COUNCIL_ROUND2_BRIEF.md`; do not re-review it.

Round 3 checks **only the round-2 findings below and the text changed for them**, plus any error those changes introduced. Do not raise again what was declined with a reason.

Round-2 blocking findings and their fixes (verify each is present and correct in `read.md`):
1. Mean device error was compared with the *maximum* disagreement of the reference methods → now reported separately: reference methods differ by 0.30 BPM on average, half of the clean windows below 0.16, at most 1.79 BPM; the device's average difference is of the same size; its largest difference on a clean window with the recommended filter is 3.7 BPM; absolute accuracy unknown.
2. "Filters differ only when the signal is disturbed" → qualified with the group of unsuitable filters (steep lower edge at 60 Hz) in the summary and the figure caption; "147 of the 150" now says all use the final counting method.
3. "Neither change helps without a filter" concealed a trade-off, and the 40 Hz precaution is conditional on the counting method → now stated: without a filter, clean windows improve 1.32 → 0.42 BPM while the 29 other windows worsen 26.7 → 33.8 BPM; with the half-rate check alone the planned 25–150 Hz filter is within tolerance in all 255 windows (0.51 BPM clean); the slower smoothing produced the single window outside tolerance; two smoothing steps at 8 Hz give 0.35 BPM clean with 255 of 255; the recommendation callout says filter and counting method must be fixed together.
4. "The other 29 windows contain a movement, a rubbing noise or the unsteady start" → now "windows with an uncertain reference": 25 with a detected disturbance, 4 with only an uncertain beat; the clean-window rule says "no uncertain or missing beat" and "no more than 3 BPM".
5. Safe-boost values were rounded above the safe value → the table column "Largest safe fixed boost (dB)" now gives exact values (−0.236, 5.975, 7.200, 9.760, 3.840, 3.460, −1.843) with the note that a setting must be rounded down; the finding callout gives 3.465 / 5.975 / 8.363 dB; figures and audio players show boosts rounded down.

Round-2 non-blocking findings applied: −12.3 dB at 50 Hz for the filter alone and −6.4 dB with the boost; upper-edge sentences scoped to the gentle filter (1.2 dB hearing curve, 1.3 dB A-weighted at 40 Hz; steep filter about 3 dB at 100 Hz); "values cut off at the lower limit"; full scale defined as either limit of the number range; gross-error wording; validity-rule false alarm (one window with the recommended filter); "probably because" for the 60 Hz failures; REQ-06 as sessions of at least 15 s; "one session"; heading "at least as much as the filter"; heart-rate range column labelled as 8-second windows; LU/LUFS named; audio player rows show "boost", "peak … below full scale", "values cut off", and one explanatory small-print line; figure vocabulary ("values", "design", "candidate", boosts rounded down).

Declined, with reason (do not raise again):
- Code fixes for the invalid-window share of rate-reduced filters and for the simulation's volume/limit order at less than full volume: neither affects a published number; both are disclosed on the page.
- Adding the recommended 40–150 Hz filter to the listening samples; renaming internal file names; replacing the axis label "frequency" in figures.
- Choosing a different counting method (for example 8 Hz smoothing) as the recommendation: the page states the trade-off and leaves the final choice to be made together with more recordings.

## Output format (final message)

- **Score: N/10** for the read as it now stands (10 = publish as is; 9 = only optional polish left).
- **Blocking findings** (must fix before publishing): numbered, each with a quote of the location, what is wrong, evidence (file and value), and the proposed fix. Only a missing or wrong round-2 fix, or an error introduced by the changes, can be blocking.
- **Non-blocking findings**: numbered, brief.
- **Round-2 fixes verified** (short list).
Be specific and terse. No praise padding.
