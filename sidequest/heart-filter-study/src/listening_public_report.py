"""Figures for the page and listening-public/SUMMARY.md of run 2 (murmurs in public data).

Usage: python -I src/listening_public_report.py --force
Redraws only run2_murmur_separation and run2_murmur_spectrum from the cached results in listening-public/, without
recomputing any statistics.
"""
import sys
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).resolve().parent
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

import numpy  # noqa: E402

import listening_public_analysis as analysis  # noqa: E402
import listening_public_compute as compute  # noqa: E402
import page_figures as style  # noqa: E402
from hfs import circor  # noqa: E402

pyplot = style.pyplot
FIGURES_DIRECTORY = style.FIGURES_DIRECTORY
PRIMARY = analysis.PRIMARY_CONDITION
LABELS = analysis.SHORT_LABELS
SHORTLIST = compute.SHORTLIST_IDENTIFIERS
CONDITION_TITLES = {"rest_microphone_only": "resting level, microphone model only (primary)",
                    "overload_microphone_only": "overload level, microphone model only",
                    "rest_matched_to_own_recordings": "resting level, spectrum matched to the own recordings"}
CONDITION_SHORT = {"rest_microphone_only": "rest, microphone only", "overload_microphone_only": "overload, microphone only",
                   "rest_matched_to_own_recordings": "rest, matched spectrum"}
SEPARATION_LABELS = {
    "butterworth_hp2_25_lp2_150": "25–150 Hz (BPM filter as first planned)",
    "butterworth_hp2_40_lp2_1000": "40 Hz–1 kHz gentle",
    "butterworth_hp2_100_lp2_1000": "100 Hz–1 kHz gentle",
    "butterworth_hp2_100_lp2_2000": "100 Hz–2 kHz gentle",
}
GRADE_COLOURS = {"I/VI": style.AMBER, "II/VI": style.ORANGE, "III/VI": style.RED}


def save_figure(figure, name: str, caption: str) -> None:
    path = FIGURES_DIRECTORY / f"{name}.png"
    if path.exists() and not (FIGURES_DIRECTORY / f".{name}.run2").exists() and "--force" not in sys.argv[1:]:
        raise FileExistsError(f"{path} exists and was not written by this script")
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.15)
    pyplot.close(figure)
    (FIGURES_DIRECTORY / f"{name}.txt").write_text(caption.strip() + "\n", encoding="utf-8")
    (FIGURES_DIRECTORY / f".{name}.run2").write_text("written by src/listening_public_report.py\n", encoding="utf-8")
    print(f"figure {name}")


def find_test(tests, condition, gain_setting, candidate, metric, family_label=None, group="systolic"):
    for record in tests:
        if (record["condition"] == condition and record["gain_setting"] == gain_setting and record["candidate"] == candidate
                and record["metric"] == metric and record["murmur_group"] == group
                and (family_label is None or record["family_label"] == family_label)):
            return record
    return None


def find_area(areas, condition, gain_setting, candidate, metric="murmur_to_heart_sound_db", subgroup="all systolic murmurs"):
    for record in areas:
        if (record["condition"] == condition and record["gain_setting"] == gain_setting and record["candidate"] == candidate
                and record["metric"] == metric and record["subgroup"] == subgroup):
            return record
    return None


def ordered_candidates(tests) -> list[str]:
    present = {record["candidate"] for record in tests if record["condition"] == PRIMARY}
    return [identifier for identifier in compute.CANDIDATE_IDENTIFIERS if identifier in present]


def interval_figure(name, title, subtitle, axis_label, series, caption, reference_line=0.0, labels=None,
                    highlighted=SHORTLIST):
    """series: list of (legend label, colour, {candidate: (estimate, low, high)})."""
    labels = labels or LABELS
    candidates = [identifier for identifier in compute.CANDIDATE_IDENTIFIERS
                  if any(identifier in values for _, _, values in series)]
    figure, axis = pyplot.subplots(figsize=(11, 0.48 * len(candidates) + 2.2))
    positions = numpy.arange(len(candidates))[::-1]
    offset = 0.18 if len(series) > 1 else 0.0
    for series_index, (label, colour, values) in enumerate(series):
        shift = offset * (1 - 2 * series_index) if len(series) > 1 else 0.0
        for position, identifier in zip(positions, candidates):
            if identifier not in values:
                continue
            estimate, low, high = values[identifier]
            axis.errorbar(estimate, position + shift, xerr=[[estimate - low], [high - estimate]], fmt="o", color=colour,
                          markersize=6, capsize=3, linewidth=1.6, label=label if position == positions[0] or identifier == candidates[0] else None)
    if reference_line is not None:
        axis.axvline(reference_line, color=style.SECONDARY, linewidth=1.2)
    axis.set_yticks(positions)
    axis.set_yticklabels([labels[identifier] for identifier in candidates])
    axis.tick_params(axis="y", labelcolor=style.TEXT)
    axis.grid(axis="y", visible=False)
    for position, identifier in zip(positions, candidates):
        if identifier in highlighted:
            continue
        axis.get_yticklabels()[list(positions).index(position)].set_color(style.SECONDARY)
    axis.set_xlabel(axis_label)
    if len(series) > 1:
        handles, labels = axis.get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        axis.legend(unique.values(), unique.keys(), loc="upper center", bbox_to_anchor=(0.4, -0.1), ncol=2, frameon=False)
    figure.suptitle(title, x=0.02, ha="left")
    axis.set_title(subtitle, loc="left", fontsize=12, color=style.SECONDARY)
    figure.tight_layout()
    save_figure(figure, name, caption)


def numbers_text(series, labels=None) -> str:
    labels = labels or LABELS
    lines = []
    for label, _, values in series:
        lines.append(f"{label}:")
        for identifier in compute.CANDIDATE_IDENTIFIERS:
            if identifier in values:
                estimate, low, high = values[identifier]
                lines.append(f"  {labels[identifier]}: {estimate:+.2f} ({low:+.2f} to {high:+.2f})")
    return "\n".join(lines)


def figure_murmur_level(tests, patients):
    series = []
    for label, colour, gain_setting in (("each filter at its fixed boost from run 1", style.MINT, "fixed"),
                                        ("all filters without boost (0 dB)", style.BLUE, "zero")):
        values = {}
        for identifier in ordered_candidates(tests):
            record = find_test(tests, PRIMARY, gain_setting, identifier, "murmur_level_a_weighted_db",
                               f"{PRIMARY}, {gain_setting} gain")
            if record and "hodges_lehmann_db" in record:
                values[identifier] = (record["hodges_lehmann_db"], record["interval_low_db"], record["interval_high_db"])
        series.append((label, colour, values))
    caption = (f"How loud the murmur part of the heart cycle (systole) is after each filter, compared with no filter, for "
               f"{patients} patients with a systolic murmur in the public CirCor data (children and young adults, modelled "
               f"through the device's microphone and output chain at resting level). A-weighted level difference in dB; "
               f"dot = typical paired difference (Hodges-Lehmann estimate), bar = 95 % bootstrap interval. Grey labels are "
               f"extra filters outside the shortlist. Energy proxy, not a listening test.\n\n" + numbers_text(series))
    interval_figure("run2_murmur_level_vs_raw", "How loud is the murmur after each filter?",
                    "Difference to no filter, A-weighted, in dB (right = louder than no filter)",
                    "Murmur level compared with no filter (dB)", series, caption)


def figure_murmur_to_heart(tests, patients):
    values = {}
    for identifier in ordered_candidates(tests):
        record = find_test(tests, PRIMARY, "fixed", identifier, "murmur_to_heart_sound_db", f"{PRIMARY}, fixed gain")
        if record and "hodges_lehmann_db" in record:
            values[identifier] = (record["hodges_lehmann_db"], record["interval_low_db"], record["interval_high_db"])
    series = [("murmur energy over heart-sound energy", style.AMBER, values)]
    caption = (f"Change of the murmur's share relative to the heart sounds (energy in systole over energy in S1 plus S2 of "
               f"the same beat), each filter compared with no filter, {patients} patients with a systolic murmur, resting "
               f"level. Right = the murmur stands out more against the heart sounds. A fixed boost does not change this "
               f"ratio; dot = Hodges-Lehmann estimate, bar = 95 % bootstrap interval.\n\n" + numbers_text(series))
    interval_figure("run2_murmur_to_heart_sound", "Does the murmur stand out more against the heart sounds?",
                    "Change of murmur energy over heart-sound energy compared with no filter, in dB",
                    "Change compared with no filter (dB)", series, caption)


def figure_separation(areas):
    series = []
    for label, colour, metric in (("murmur over heart sounds", style.MINT, "murmur_to_heart_sound_db"),
                                  ("murmur over the quiet part of the beat", style.VIOLET, "murmur_to_quiet_phase_db")):
        values = {}
        for identifier in compute.CANDIDATE_IDENTIFIERS:
            record = find_area(areas, PRIMARY, "fixed", identifier, metric)
            if record:
                values[identifier] = (record["area_under_curve"], record["interval_low"], record["interval_high"])
        series.append((label, colour, values))
    first = next(iter(series[0][2]), None)
    counts = find_area(areas, PRIMARY, "fixed", "raw") or {}
    labels = dict(LABELS, **SEPARATION_LABELS)
    caption = (f"How well a simple energy measure in the stretch between the two heart sounds tells patients with a "
               f"murmur there ({counts.get('present_patients', '?')}) from patients without a murmur "
               f"({counts.get('absent_patients', '?')}) after each filter: score for telling murmur from no murmur (area "
               f"under the curve), 0.5 = chance, 1 = perfect separation; bar = 95 % patient bootstrap interval (2,000 "
               f"resamples). This measures an energy proxy, not what a listener hears.\n\n" + numbers_text(series, labels))
    if first is None:
        return
    interval_figure("run2_murmur_separation", "Can a simple measure tell murmur from no murmur after each filter?",
                    "Score for telling murmur from no murmur (area under the curve): 0.5 = chance, 1 = perfect", "Score",
                    series, caption, reference_line=0.5, labels=labels,
                    highlighted=set(SHORTLIST) | {"butterworth_hp2_40_lp2_150"})


def figure_spectrum(caches, rows):
    cache = caches.get(PRIMARY)
    if not cache:
        return
    classes = {}
    for row in rows:
        if row["condition"] == PRIMARY and row["candidate"] == "raw" and row["gain_setting"] == "fixed":
            if row["murmur_class"] == "systolic" and row["systolic_grade"] in GRADE_COLOURS:
                classes[row["patient"]] = row["systolic_grade"]
            elif row["murmur_class"] == "absent":
                classes[row["patient"]] = "absent"
    patients = {patient.patient_identifier: patient for patient in circor.list_patients()}
    spectra = {}
    for patient_identifier, group in classes.items():
        stems = [recording.file_stem for recording in analysis.runner.analysed_recordings(patients[patient_identifier])]
        values = [cache[stem]["raw_spectrum"][0] for stem in stems if stem in cache]
        if values:
            spectra.setdefault(group, []).append(numpy.nanmedian(numpy.array(values), axis=0))
    edges = compute.SPECTRUM_BAND_EDGES_HZ
    centres = numpy.sqrt(edges[:-1] * edges[1:])
    figure, axis = pyplot.subplots(figsize=(11, 6))
    lines = []
    for group, colour, label in (("absent", style.BLUE, "no murmur"), ("I/VI", style.AMBER, "soft murmur (grade I/VI)"),
                                 ("II/VI", style.ORANGE, "medium murmur (grade II/VI)"),
                                 ("III/VI", style.RED, "loud murmur (grade III/VI)")):
        if group not in spectra:
            continue
        median = numpy.nanmedian(numpy.array(spectra[group]), axis=0)
        level = 10.0 * numpy.log10(numpy.where(median > 0, median, numpy.nan))
        visible = (centres >= 40.0) & (centres <= 2000.0) & numpy.isfinite(level)
        axis.plot(centres[visible], level[visible], color=colour, linewidth=2.2, label=f"{label}, {len(spectra[group])} patients")
        lines.append((label, len(spectra[group]), centres[visible], level[visible]))
    for edge in (40, 60, 80, 100, 150, 400, 800, 1000):
        axis.axvline(edge, color=style.SPINE, linewidth=1.0, linestyle="--")
    style.hertz_axis(axis, 40, 2000, ticks=(40, 60, 100, 150, 250, 400, 800, 2000))
    axis.set_xlabel("Pitch")
    axis.set_ylabel("Strength between the two heart sounds (dB)")
    axis.legend(loc="lower left", frameon=False)
    figure.suptitle("Where the murmur energy lies", x=0.02, ha="left")
    axis.set_title("Typical strength at each pitch in the stretch between the two heart sounds, after the model of our "
                   "device input,\nbefore any filter; dashed lines: filter edges of the candidates. The public recordings "
                   "contain nothing above 2 kHz;\nbelow 40 Hz these short stretches cannot show the pitch reliably.",
                   loc="left", fontsize=12, color=style.SECONDARY)
    figure.tight_layout()
    text_lines = ["Median over patients of the median over their recordings of the systole power spectrum (Hann window per "
                  "systole, 1/12-octave bands), no filter, resting level, microphone model only. dB relative to full "
                  "scale per frequency bin, shown from 40 Hz to 2 kHz. Dashed lines at 40, 60, 80, 100, 150, 400, 800 and 1000 Hz (candidate edges). "
                  "CirCor is sampled at 4 kHz: no content above 2 kHz."]
    for label, count, frequencies, levels in lines:
        text_lines.append(f"{label} ({count} patients):")
        text_lines.append("  " + "; ".join(f"{frequency:.0f} Hz {level:.1f} dB" for frequency, level in
                                           zip(frequencies[::4], levels[::4])))
    save_figure(figure, "run2_murmur_spectrum", "\n".join(text_lines))


def figure_run1_vs_public(run1_rows, correlations):
    rows = {row["candidate"]: row for row in run1_rows if row["condition"] == PRIMARY and row["candidate"] in SHORTLIST}
    if not rows:
        return
    panels = [("a_weighted_vs_raw_db", "(a) A-weighted level\nvs no filter (dB)"),
              ("iso226_vs_raw_db", "(b) Hearing-curve level\nvs no filter (dB)"),
              ("k_loudness_vs_raw_db", "(c) Loudness (K-weighted)\nvs no filter (dB)"),
              ("between_to_heart_a_weighted_db", "(d) Sound between beats vs\nheart sounds (dB, lower = cleaner)")]
    figure, axes = pyplot.subplots(1, 4, figsize=(15, 6.2), sharey=True)
    candidates = [identifier for identifier in SHORTLIST if identifier in rows]
    positions = numpy.arange(len(candidates))[::-1]
    height = 0.36
    text = ["Run 1 (five own recordings of one healthy adult) next to the public data (CirCor, modelled, resting level), "
            "each shortlist candidate at its fixed boost from run 1. Spearman rank correlation of the candidate order:"]
    for axis, (name, title) in zip(axes, panels):
        own = [rows[identifier][f"run1_{name}"] for identifier in candidates]
        public = [rows[identifier][name] for identifier in candidates]
        axis.barh(positions + height / 2, own, height=height * 0.92, color=style.AMBER, label="own recordings (run 1)")
        axis.barh(positions - height / 2, public, height=height * 0.92, color=style.MINT, label="public data (children)")
        axis.axvline(0, color=style.SECONDARY, linewidth=1.2)
        axis.grid(axis="y", visible=False)
        correlation = correlations.get(PRIMARY, {}).get(name)
        axis.set_title(title + (f"\nrank agreement {correlation:+.2f} (1 = same order)" if correlation is not None else ""),
                       loc="left", fontsize=12)
        text.append(f"{title.replace(chr(10), ' ')}: rank correlation {correlation:+.2f}" if correlation is not None else title)
        for identifier, own_value, public_value in zip(candidates, own, public):
            text.append(f"  {LABELS[identifier]}: own {own_value:+.2f}, public {public_value:+.2f}")
    axes[0].set_yticks(positions)
    axes[0].set_yticklabels([LABELS[identifier] for identifier in candidates])
    axes[0].tick_params(axis="y", labelcolor=style.TEXT)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.55, 0.0))
    figure.suptitle("Own recordings and public data: do the filters rank the same?", x=0.02, ha="left")
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    save_figure(figure, "run2_listening_run1_vs_public", "\n".join(text))


# ---------------------------------------------------------------- summary

def signed(value, decimals=1):
    return f"{value:+.{decimals}f}"


def p_text(value):
    return "<0.001" if value < 0.001 else f"{value:.3f}"


def population_lines(rows) -> list[str]:
    primary = [row for row in rows if row["condition"] == PRIMARY and row["candidate"] == "raw" and row["gain_setting"] == "fixed"]
    lines = []
    counts = {}
    for row in primary:
        counts[row["murmur_class"]] = counts.get(row["murmur_class"], 0) + 1
    lines.append("| Group | Patients analysed |\n| --- | ---: |")
    for key, value in sorted(counts.items()):
        lines.append(f"| {key} | {value} |")
    systolic = [row for row in primary if row["murmur_class"] == "systolic"]
    lines.append("")
    lines.append("| Systolic murmur grade | Patients | | Pitch | Patients | | Age category (all analysed) | Patients |")
    lines.append("| --- | ---: | --- | --- | ---: | --- | --- | ---: |")
    grades = [(grade, sum(row["systolic_grade"] == grade for row in systolic)) for grade in analysis.GRADES]
    pitches = [(pitch, sum(row["systolic_pitch"] == pitch for row in systolic)) for pitch in analysis.PITCHES]
    ages = {}
    for row in primary:
        ages[row["age_category"] or "not stated"] = ages.get(row["age_category"] or "not stated", 0) + 1
    age_items = sorted(ages.items())
    for index in range(max(len(grades), len(pitches), len(age_items))):
        grade = grades[index] if index < len(grades) else ("", "")
        pitch = pitches[index] if index < len(pitches) else ("", "")
        age = age_items[index] if index < len(age_items) else ("", "")
        lines.append(f"| {grade[0]} | {grade[1]} | | {pitch[0]} | {pitch[1]} | | {age[0]} | {age[1]} |")
    recordings = sum(row["recordings"] for row in primary)
    cycles = sum(row["cycles"] for row in primary)
    lines.append("")
    lines.append(f"{len(primary)} patients, {recordings} recordings, {cycles} complete annotated heart cycles in the primary "
                 f"analysis (murmur-present patients: only recordings at a location where the murmur is heard).")
    return lines


def test_table(tests, condition, gain_setting, family_label, candidates, metrics=tuple(analysis.METRICS)) -> list[str]:
    lines = ["| Candidate | Metric | Patients | Raw median (dB) | Hodges-Lehmann difference (dB) | 95 % interval (dB) | "
             "Patients above Raw | Holm p |", "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |"]
    for identifier in candidates:
        for metric in metrics:
            record = find_test(tests, condition, gain_setting, identifier, metric, family_label)
            if not record or "hodges_lehmann_db" not in record:
                continue
            lines.append(f"| {LABELS[identifier]} | {metric_short(metric)} | {record['patients']} | "
                         f"{record['raw_median_db']:.1f} | {signed(record['hodges_lehmann_db'], 2)} | "
                         f"{signed(record['interval_low_db'], 2)} to {signed(record['interval_high_db'], 2)} | "
                         f"{100 * record['share_of_patients_higher_than_raw']:.0f} % | "
                         f"{p_text(record.get('holm_p', record['wilcoxon_p']))} |")
    return lines


def metric_short(metric):
    return {"murmur_level_a_weighted_db": "murmur level (A)", "murmur_to_heart_sound_db": "murmur / S1+S2",
            "murmur_to_quiet_phase_db": "murmur / diastole", "murmur_to_heart_sound_a_weighted_db": "murmur / S1+S2 (A)",
            "murmur_to_quiet_phase_a_weighted_db": "murmur / diastole (A)"}[metric]


def area_table(areas, condition, gain_setting, metric, subgroups, candidates) -> list[str]:
    header = "| Candidate | " + " | ".join(subgroups) + " |"
    lines = [header, "| --- | " + " | ".join("---" for _ in subgroups) + " |"]
    for identifier in candidates:
        cells = []
        for subgroup in subgroups:
            record = find_area(areas, condition, gain_setting, identifier, metric, subgroup)
            if record is None:
                cells.append("")
                continue
            cell = f"{record['area_under_curve']:.3f} ({record['interval_low']:.3f}–{record['interval_high']:.3f})"
            if identifier != "raw":
                cell += (f"; vs Raw {signed(record['difference_to_raw'], 3)} "
                         f"({signed(record['difference_interval_low'], 3)} to {signed(record['difference_interval_high'], 3)})")
            cells.append(cell)
        lines.append(f"| {LABELS[identifier]} | " + " | ".join(cells) + " |")
    return lines


def write_summary(rows, tests, areas, clipping, run1_rows, correlations, family_sizes, caches, gains, delays, halves):
    lines = ["# Run 2: murmurs in public data (CirCor DigiScope 1.0.3)", "",
             "Generated by `src/listening_public.py analyse`. Tables: `murmur_metrics_per_patient.csv`, `murmur_tests.csv`, "
             "`murmur_auc.csv`, `clipping_public.csv`, `run1_metrics_on_public.csv`.", "",
             "**These are energy proxies at the device output; they do not replace listening.** CirCor was recorded at "
             "4 kHz with an electronic stethoscope on children and young adults; the recordings carry nothing above 2 kHz, "
             "and the capture chain (INMP441 microphone) is modelled, not measured. Nothing was tuned on this data, so no "
             "training split is needed; two disjoint random halves of the patients (seed 7) show the stability.", ""]
    interpretation = analysis.OUTPUT_DIRECTORY / "interpretation.md"
    if interpretation.exists():
        lines += ["## Reading of the results", "", interpretation.read_text(encoding="utf-8").strip(), ""]
    condition_counts = {condition: len(cache) for condition, cache in caches.items()}
    lines.append("Conditions computed (recordings in cache): " + ", ".join(
        f"{CONDITION_TITLES[condition]}: {count}" for condition, count in condition_counts.items()) + ".")
    lines.append("")
    lines.append("## Population")
    lines.append("")
    lines += population_lines(rows)
    lines.append("")
    lines.append("## Primary and secondary results (shortlist, resting level, microphone model, fixed run-1 gain)")
    lines.append("")
    size = family_sizes.get((PRIMARY, "fixed"), 0)
    lines.append(f"Two-sided Wilcoxon signed-rank test against Raw over patients with a systolic murmur, Hodges-Lehmann "
                 f"estimate of the paired difference, 95 % bootstrap interval (2,000 resamples of patients), Holm correction "
                 f"over the family of all {size} tests (all non-Raw candidates × primary, secondary 1, secondary 2). "
                 f"Raw at -0.010 dB. Murmur phase = systole, quiet phase = diastole.")
    lines.append("")
    lines += test_table(tests, PRIMARY, "fixed", f"{PRIMARY}, fixed gain", SHORTLIST[1:] + ["butterworth_hp2_40_lp2_150"])
    lines.append("")
    lines.append("Extra candidates (not on the shortlist), same family:")
    lines.append("")
    extra = [identifier for identifier in compute.CANDIDATE_IDENTIFIERS
             if identifier not in SHORTLIST and identifier != "butterworth_hp2_40_lp2_150"]
    lines += test_table(tests, PRIMARY, "fixed", f"{PRIMARY}, fixed gain", extra)
    lines.append("")
    lines.append("## Filter shape alone (all filters at 0 dB gain)")
    lines.append("")
    lines.append(f"Same tests with every filter at 0 dB, Holm over its own family of "
                 f"{family_sizes.get((PRIMARY, 'zero'), 0)} tests. The ratios (secondaries 1 and 2) do not depend on a "
                 f"fixed gain except through clipping, so they are nearly identical to the table above.")
    lines.append("")
    lines += test_table(tests, PRIMARY, "zero", f"{PRIMARY}, zero gain", SHORTLIST[1:] + ["butterworth_hp2_40_lp2_150"],
                        metrics=("murmur_level_a_weighted_db",))
    lines.append("")
    lines.append("## Exploratory (not part of the pre-specified family)")
    lines.append("")
    lines.append("Secondaries 1 and 2 with A-weighting (uncorrected p in the last column):")
    lines.append("")
    lines += test_table(tests, PRIMARY, "fixed", f"{PRIMARY}, fixed gain", SHORTLIST[1:],
                        metrics=tuple(analysis.EXPLORATORY_METRICS))
    lines.append("")
    diastolic = [record for record in tests if record["condition"] == PRIMARY and record["gain_setting"] == "fixed"
                 and record["murmur_group"] == "diastolic" and record["metric"] in analysis.METRICS
                 and record["family_label"] == f"{PRIMARY}, fixed gain"]
    diastolic_patients = diastolic[0]["patients"] if diastolic else 0
    lines.append(f"Diastolic murmurs: {diastolic_patients} patient(s) (some also have a systolic murmur); descriptive only "
                 f"(murmur phase = diastole, quiet phase = systole). "
                 f"Median differences to Raw: " + "; ".join(
                     f"{LABELS[record['candidate']]} {metric_short(record['metric'])} {signed(record['median_difference_db'], 1)} dB"
                     for record in diastolic if record["candidate"] in SHORTLIST) + ".")
    lines.append("")
    lines.append("## Separation of murmur-present from murmur-absent patients (area under the ROC curve)")
    lines.append("")
    lines.append("Secondary 1 (systole energy over S1 + S2) and secondary 2 (systole power over diastole power) as a score; "
                 "area = probability that a patient with a systolic murmur scores higher than one without (0.5 = chance, "
                 "1 = perfect). Interval: 2,000 patient bootstrap resamples, stratified by group, seed fixed; the "
                 "difference to Raw uses the same resamples (paired). Sub-analyses by grade and pitch: 1,000 resamples, "
                 "each subgroup against all murmur-absent patients.")
    lines.append("")
    for metric in ("murmur_to_heart_sound_db", "murmur_to_quiet_phase_db"):
        lines.append(f"**{metric_short(metric)}**, fixed gain:")
        lines.append("")
        lines += area_table(areas, PRIMARY, "fixed", metric, ["all systolic murmurs"], compute.CANDIDATE_IDENTIFIERS)
        lines.append("")
    subgroups = [f"systolic_grade={grade}" for grade in analysis.GRADES] + [f"systolic_pitch={pitch}" for pitch in analysis.PITCHES]
    lines.append("By grade and pitch (secondary 1, fixed gain; area only):")
    lines.append("")
    header = "| Candidate | " + " | ".join(subgroup.split("=")[1] for subgroup in subgroups) + " |"
    lines.append(header)
    lines.append("| --- | " + " | ".join("---:" for _ in subgroups) + " |")
    counts_row = []
    for subgroup in subgroups:
        record = find_area(areas, PRIMARY, "fixed", "raw", "murmur_to_heart_sound_db", subgroup)
        counts_row.append(str(record["present_patients"]) if record else "")
    lines.append("| patients with murmur | " + " | ".join(counts_row) + " |")
    for identifier in compute.CANDIDATE_IDENTIFIERS:
        cells = []
        for subgroup in subgroups:
            record = find_area(areas, PRIMARY, "fixed", identifier, "murmur_to_heart_sound_db", subgroup)
            cells.append(f"{record['area_under_curve']:.3f}" if record else "")
        lines.append(f"| {LABELS[identifier]} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Stability: two disjoint random halves of the patients")
    lines.append("")
    lines.append("| Candidate | Metric | Half A: HL (95 % interval) | Half B: HL (95 % interval) | Area half A | Area half B |")
    lines.append("| --- | --- | --- | --- | ---: | ---: |")
    for identifier in SHORTLIST[1:]:
        for metric in analysis.METRICS:
            cells = []
            for half in ("half A", "half B"):
                record = find_test(tests, PRIMARY, "fixed", identifier, metric, f"{PRIMARY}, fixed gain, {half}")
                cells.append(f"{signed(record['hodges_lehmann_db'], 2)} ({signed(record['interval_low_db'], 2)} to "
                             f"{signed(record['interval_high_db'], 2)})" if record and "hodges_lehmann_db" in record else "")
            area_cells = []
            for half in ("half A", "half B"):
                record = find_area(areas, PRIMARY, "fixed", identifier, "murmur_to_heart_sound_db",
                                   f"all systolic murmurs, {half}")
                area_cells.append(f"{record['area_under_curve']:.3f}" if record and metric == "murmur_to_heart_sound_db" else "")
            lines.append(f"| {LABELS[identifier]} | {metric_short(metric)} | {cells[0]} | {cells[1]} | {area_cells[0]} | {area_cells[1]} |")
    lines.append("")
    lines.append("## Sensitivity analyses (shortlist)")
    lines.append("")
    for condition in caches:
        if condition == PRIMARY:
            continue
        lines.append(f"**{CONDITION_TITLES[condition]}** (Holm over its own family of "
                     f"{family_sizes.get((condition, 'fixed'), 0)} tests):")
        lines.append("")
        lines += test_table(tests, condition, "fixed", f"{condition}, fixed gain", SHORTLIST[1:])
        lines.append("")
        lines += area_table(areas, condition, "fixed", "murmur_to_heart_sound_db", ["all systolic murmurs"], SHORTLIST)
        lines.append("")
    missing = [CONDITION_TITLES[condition] for condition in compute.CONDITIONS if condition not in caches]
    if missing:
        lines.append("Not computed: " + "; ".join(missing) + ".")
        lines.append("")
    lines.append("## Clipping on public data")
    lines.append("")
    lines.append("Output samples at the 24-bit limit after the device chain (first 0.5 s of each recording excluded as filter "
                 "start-up), and the largest fixed gain that no recording (100 %) or 99 % of the recordings would clip at.")
    lines.append("")
    lines.append("| Condition | Candidate | Run-1 safe gain (dB) | Recordings clipping at that gain | Patients clipping | "
                 "Safe for 99 % (dB) | Safe for 100 % (dB) | Recordings with input at the limit |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for record in clipping:
        if record["candidate"] not in SHORTLIST and record["candidate"] != "butterworth_hp2_40_lp2_150":
            continue
        lines.append(f"| {CONDITION_SHORT[record['condition']]} | {LABELS[record['candidate']]} | "
                     f"{signed(record['run1_safe_gain_db'], 2)} | "
                     f"{record['recordings_with_output_at_limit_at_run1_gain_percent']:.1f} % | "
                     f"{record['patients_with_output_at_limit_at_run1_gain_percent']:.1f} % | "
                     f"{signed(record['safe_gain_for_99_percent_of_recordings_db'], 2)} | "
                     f"{signed(record['safe_gain_for_100_percent_of_recordings_db'], 2)} | "
                     f"{record['recordings_with_input_at_limit']} |")
    lines.append("")
    lines.append("## Run-1 metrics repeated on public data")
    lines.append("")
    lines.append("Each candidate at its fixed run-1 gain, mean over recordings (murmur-present and -absent patients; "
                 "between-beat ratio: diastole of murmur-absent patients over S1 + S2). Run 1 value / public value. "
                 "K-weighted loudness on public data is computed at the fixed gain including any clipping.")
    lines.append("")
    for condition in caches:
        condition_rows = {row["candidate"]: row for row in run1_rows if row["condition"] == condition}
        if not condition_rows:
            continue
        lines.append(f"**{CONDITION_TITLES[condition]}**")
        lines.append("")
        lines.append("| Candidate | A-weighted vs Raw | ISO 226 60 phon vs Raw | K-weighted vs Raw | Between / heart (A) |")
        lines.append("| --- | --- | --- | --- | --- |")
        for identifier in SHORTLIST:
            row = condition_rows.get(identifier)
            if row is None:
                continue
            cells = []
            for name in analysis.RUN1_METRICS:
                cells.append(f"{signed(row[f'run1_{name}'])} / {signed(row[name])}")
            lines.append(f"| {LABELS[identifier]} | " + " | ".join(cells) + " |")
        correlation = correlations.get(condition, {})
        lines.append("| Spearman rank correlation (8 candidates) | " + " | ".join(
            f"{correlation[name]:+.2f}" if name in correlation else "" for name in analysis.RUN1_METRICS) + " |")
        lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append("- Same windows for all filters (A018): the dataset's segmentation, not shifted by the filters' group delay. "
                 "Group delay at 100 Hz / 200 Hz: " + "; ".join(
                     f"{LABELS[identifier]} {values[0]:.1f} / {values[1]:.1f} ms" for identifier, values in delays.items()
                     if identifier in SHORTLIST[1:]) + ". Steep and elliptic designs move part of S1/S2 energy into the "
                 "following phase; this biases secondary 1 upward for them.")
    delay_info = compute.load_delays()
    lines.append(f"- Chain-model delay measured by cross-correlation (median of 12 recordings): " + ", ".join(
        f"{condition} {1e3 * value:+.2f} ms" for condition, value in delay_info.items()) + "; segment times corrected by it.")
    lines.append("- CirCor segmentations are semi-automatic; the murmur labels are per patient and location, not per beat.")
    lines.append("- The fixed gains are safe for the five own recordings of one adult; the public signals are scaled by the "
                 "chain model's calibration to the own resting (or overload) level, so clipping on public data depends "
                 "on that calibration.")
    lines.append("- Hundreds of patients make tiny differences significant; read the size in dB, not the p value.")
    (analysis.OUTPUT_DIRECTORY / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("summary written")



def write_everything(rows, tests, areas, clipping, run1_rows, correlations, family_sizes, caches, gains, delays, halves):
    style.apply_style()
    systolic_patients = len({row["patient"] for row in rows if row["condition"] == PRIMARY and row["murmur_class"] == "systolic"})
    if compute.chain_model_available():
        figure_murmur_level(tests, systolic_patients)
        figure_murmur_to_heart(tests, systolic_patients)
        figure_separation(areas)
        figure_spectrum(caches, rows)
        figure_run1_vs_public(run1_rows, correlations)
    else:
        print("chain model not available: figures not written (stand-in numbers are for development only)")
    write_summary(rows, tests, areas, clipping, run1_rows, correlations, family_sizes, caches, gains, delays, halves)


def redraw_page_figures() -> None:
    import csv
    style.apply_style()
    with open(compute.OUTPUT_DIRECTORY / "murmur_auc.csv", newline="", encoding="utf-8") as handle:
        areas = list(csv.DictReader(handle))
    for record in areas:
        for field in ("area_under_curve", "interval_low", "interval_high"):
            record[field] = float(record[field])
    with open(compute.OUTPUT_DIRECTORY / "murmur_metrics_per_patient.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    figure_separation(areas)
    figure_spectrum({PRIMARY: analysis.load_condition(PRIMARY)}, rows)


if __name__ == "__main__":
    redraw_page_figures()
