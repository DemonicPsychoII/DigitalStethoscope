"""Page figures for run 2 (EPHNOGRAM against ECG), in the style of src/page_figures.py.

Usage: python -I src/bpm_public_figures.py
Reads results-public/*.csv (written by bpm_public_report.py and sound_reference_validation.py), the estimate cache
and results/bpm_filter_grid.csv. Writes page/figures/run2_*.png with a .txt of the plotted numbers; existing
files of other names are not touched.
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import page_figures as style
import public_evaluation_common as common
from hfs import ephnogram

RESULTS_DIRECTORY = common.RESULTS_DIRECTORY
FIGURE_PREFIX = "run2_"
METHOD_TITLES = {"first_draft": "first draft", "half_check_only": "half-rate\ncheck only",
                 "final": "method of the\nfirst part\n(smoothing at 5 Hz\n+ half-rate check)",
                 "alternative_8hz": "alternative\n(smoothing at 8 Hz\n+ half-rate check)"}
FILTER_TITLES = {"raw": "no filter", common.PLANNED: "planned 25–150 Hz", common.RECOMMENDED: "recommended 40–150 Hz"}
FILTER_COLOURS = {"raw": style.RED, common.PLANNED: style.AMBER, common.RECOMMENDED: style.MINT}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def save(figure, name, caption):
    if not name.startswith(FIGURE_PREFIX):
        raise ValueError("run-2 figures must carry the run2_ prefix so that run-1 figures are never overwritten")
    style.save_figure(figure, name, caption)


def figure_error_by_heart_rate(band_rows):
    conditions = [condition for condition in ("rest", "overload") if any(row["condition"] == condition for row in band_rows)]
    labels = [label for _, _, label in common.HEART_RATE_BANDS]
    figure, axes = pyplot.subplots(1, len(conditions), figsize=(6.4 * len(conditions), 5.8), sharey=True, squeeze=False)
    caption_parts = []
    maximum = 0.0
    for axis, condition in zip(axes[0], conditions):
        positions = numpy.arange(len(labels))
        width = 0.26
        for offset, identifier in zip((-width, 0.0, width), FILTER_TITLES):
            values, lows, highs, subjects = [], [], [], []
            for label in labels:
                match = [row for row in band_rows if row["condition"] == condition and row["identifier"] == identifier
                         and row["estimator"] == "final" and row["band_bpm"] == label]
                row = match[0] if match else {}
                values.append(number(row.get("reliable_mae_bpm")))
                lows.append(number(row.get("reliable_mae_interval_low")))
                highs.append(number(row.get("reliable_mae_interval_high")))
                subjects.append(int(number(row.get("reliable_subject_count")) or 0) if row else 0)
            values, lows, highs = map(numpy.array, (values, lows, highs))
            errors = numpy.vstack([numpy.clip(values - lows, 0, None), numpy.clip(highs - values, 0, None)])
            axis.bar(positions + offset, values, width=width * 0.92, color=FILTER_COLOURS[identifier], label=FILTER_TITLES[identifier])
            axis.errorbar(positions + offset, values, yerr=numpy.nan_to_num(errors), fmt="none", ecolor=style.TEXT, elinewidth=1.2, capsize=3)
            maximum = max(maximum, numpy.nanmax(highs) if numpy.isfinite(highs).any() else 0)
            caption_parts.append(f"{condition} level, {FILTER_TITLES[identifier]}: " + "; ".join(
                f"{label} BPM {value:.2f} ({low:.2f}–{high:.2f})" for label, value, low, high in zip(labels, values, lows, highs)
                if numpy.isfinite(value)))
            if identifier == common.RECOMMENDED:
                band_subjects = subjects
        axis.set_xticks(positions)
        axis.set_xticklabels([f"{label.replace('below ', '<').replace('above ', '>')}\n({count})"
                              for label, count in zip(labels, band_subjects)], fontsize=10.5)
        axis.set_xlabel("heart rate by ECG (BPM); in brackets: number of people")
        axis.grid(axis="x", visible=False)
        axis.set_title("level as at rest" if condition == "rest" else "level raised until about one beat in three overloads",
                       loc="left", fontsize=13)
    axes[0][0].set_ylabel("average difference from ECG (BPM)")
    axes[0][0].set_ylim(0, max(maximum * 1.08, 1.0))
    axes[0][0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False)
    figure.suptitle("Public recordings: how far the device's heart rate is from ECG, by heart rate", x=0.02, ha="left")
    figure.tight_layout()
    save(figure, "run2_bpm_error_by_heart_rate",
         "Mean absolute difference between the device's heart rate (final counting method) and the ECG heart rate, on windows "
         "with a clean ECG, per ECG heart-rate band; bars are 95 % intervals from resampling people. Numbers below the bands: "
         "people with windows in that band. " + " | ".join(caption_parts))


def figure_lower_edge(comparison_rows):
    rows = [row for row in comparison_rows if row["estimator"] == "final"]
    edges = [row for row in rows if row["lower_edge_hz"] != "none"]
    raw = [row for row in rows if row["lower_edge_hz"] == "none"]
    figure, axes = pyplot.subplots(1, 2, figsize=(12, 5.6), sharey=False)
    series = [("run1", "own recordings (first part)", style.BLUE, "o"), ("rest", "public recordings, rest level", style.MINT, "s"),
              ("overload", "public recordings, overload level", style.AMBER, "D")]
    caption_parts = []
    for axis, metric, title in ((axes[0], "all", "every window"), (axes[1], "reliable", "windows with a clean reference")):
        for prefix, label, colour, marker in series:
            key = f"{prefix}_{metric}_mae_bpm"
            points = [(number(row["lower_edge_hz"]), number(row.get(key))) for row in edges if row.get(key) not in (None, "")]
            points = [point for point in points if numpy.isfinite(point[1])]
            if not points:
                continue
            axis.plot([point[0] for point in points], [point[1] for point in points], color=colour, marker=marker,
                      linewidth=2.2, markersize=7, label=label)
            raw_value = number(raw[0].get(key)) if raw and raw[0].get(key) not in (None, "") else float("nan")
            if numpy.isfinite(raw_value):
                axis.axhline(raw_value, color=colour, linestyle="--", linewidth=1.3, alpha=0.8)
            caption_parts.append(f"{title}, {label}: no filter {raw_value:.2f}; " + ", ".join(
                f"{edge:g} Hz {value:.2f}" for edge, value in points))
        style.hertz_axis(axis, 8, 100, ticks=(10, 20, 40, 80))
        axis.set_xlabel("lower band edge (upper edge 150 Hz)")
        axis.set_title(title, loc="left", fontsize=13)
        axis.set_ylim(bottom=0)
    axes[0].set_ylabel("average difference from reference (BPM)")
    handles, legend_labels = axes[1].get_legend_handles_labels()
    figure.legend(handles, legend_labels, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=3, frameon=False, fontsize=10.5)
    figure.text(0.02, -0.1, "Dashed lines: the same data without any filter. Reference: own recordings from the sound itself, "
                "public recordings from the ECG.", fontsize=11, color=style.SECONDARY)
    figure.suptitle("Lower edge of the filter: own recordings next to public recordings (counting method of the first part)", x=0.02, ha="left")
    figure.tight_layout()
    save(figure, "run2_bpm_lower_edge",
         "Mean absolute heart-rate difference (BPM) of the counting method of the first part with a gentle 2nd-order "
         "Butterworth band filter, upper edge 150 Hz, against the lower edge; own recordings of the first part against their "
         "sound-derived reference, public recordings against ECG. "
         + " | ".join(caption_parts))


def figure_counting_methods(comparison_rows):
    methods = list(common.ESTIMATOR_VARIANTS)
    figure, axes = pyplot.subplots(1, 2, figsize=(13, 5.8), sharey=True)
    sources = [("run1", "own recordings (first part)", style.BLUE), ("rest", "public, rest level", style.MINT),
               ("overload", "public, overload level", style.AMBER)]
    caption_parts = []
    maximum = 0.0
    for axis, identifier in zip(axes, (common.PLANNED, common.RECOMMENDED)):
        positions = numpy.arange(len(methods))
        width = 0.26
        for offset, (prefix, label, colour) in zip((-width, 0.0, width), sources):
            values = []
            for method in methods:
                match = [row for row in comparison_rows if row["identifier"] == identifier and row["estimator"] == method]
                values.append(number(match[0].get(f"{prefix}_reliable_mae_bpm")) if match else float("nan"))
            values = numpy.array(values)
            axis.bar(positions + offset, values, width=width * 0.92, color=colour, label=label)
            for position, value in zip(positions + offset, values):
                if numpy.isfinite(value):
                    axis.text(position, value, f"{value:.2f}", ha="center", va="bottom", fontsize=10, color=style.TEXT)
            maximum = max(maximum, numpy.nanmax(values) if numpy.isfinite(values).any() else 0)
            caption_parts.append(f"{FILTER_TITLES[identifier]}, {label}: " + ", ".join(
                f"{METHOD_TITLES[method].split(chr(10) + '(')[0].replace(chr(10), ' ')} {value:.2f}" for method, value in zip(methods, values) if numpy.isfinite(value)))
        axis.set_xticks(positions)
        axis.set_xticklabels([METHOD_TITLES[method] for method in methods], fontsize=10)
        axis.grid(axis="x", visible=False)
        axis.set_title(FILTER_TITLES[identifier], loc="left", fontsize=13)
    axes[0].set_ylabel("average difference on clean windows (BPM)")
    axes[0].set_ylim(0, maximum * 1.18 if maximum else 1)
    axes[1].legend(loc="upper right", frameon=False, fontsize=10.5)
    figure.suptitle("Four ways of counting beats, on the planned and the recommended filter", x=0.02, ha="left")
    figure.tight_layout()
    save(figure, "run2_bpm_counting_methods",
         "Mean absolute heart-rate difference (BPM) on windows with a clean reference for the four counting methods, own "
         "recordings of the first part against their sound-derived reference, public recordings against ECG. " + " | ".join(caption_parts))


def choose_exercise_record(grid_rows):
    """Good-sound exercise record spanning at least 50 BPM whose error (recommended filter, final method) is the
    median of such records: a typical record, not the best or the worst."""
    key = common.configuration_key(common.FINAL_METHOD)
    options = []
    for info in ephnogram.list_records():
        reference = common.load_reference(info.record_name)
        if reference is None or info.duration_seconds < 600 or "rest" in info.scenario.lower()                 or info.pcg_quality.strip().lower() != "good" or info.record_name in common.duplicate_records_excluded():
            continue
        estimates = common.cached_estimates(info.record_name, "rest", common.RECOMMENDED)
        if key not in estimates or not common.cache_path(info.record_name, "rest", "raw").exists():
            continue
        times = numpy.array([time for time, window in reference.items() if time >= common.FIRST_SCORED_END_TIME_SECONDS
                             and window.get("reliable") and window.get("reference_bpm") and time - 1 < len(estimates[key])])
        if times.size == 0:
            continue
        rates = numpy.array([reference[time]["reference_bpm"] for time in times])
        if numpy.percentile(rates, 95) - numpy.percentile(rates, 5) < 50:
            continue
        options.append((float(numpy.mean(numpy.abs(estimates[key][times - 1, 1] - rates))), info))
    if not options:
        return None
    options.sort(key=lambda item: item[0])
    return options[len(options) // 2][1], len(options)


def figure_estimate_vs_ecg(grid_rows):
    chosen = choose_exercise_record(grid_rows)
    if chosen is None:
        print("no exercise record with cached estimates yet")
        return
    info, option_count = chosen
    reference = common.load_reference(info.record_name)
    times = numpy.array(sorted(time for time in reference if time >= common.FIRST_SCORED_END_TIME_SECONDS))
    ecg = numpy.array([reference[time]["reference_bpm"] if reference[time].get("reliable") else numpy.nan for time in times], float)
    key = common.configuration_key(common.FINAL_METHOD)
    figure, axis = pyplot.subplots(figsize=(12, 5.4))
    axis.plot(times / 60, ecg, color=style.TEXT, linewidth=2.0, label="ECG heart rate (clean windows)")
    caption = [f"Record {info.record_name}, subject {info.subject_id}, {info.scenario}; rest level, counting method of the first part. "
               f"Chosen as the median-error record among {option_count} exercise records with good sound and at least 50 BPM "
               f"between their 5th and 95th percentile heart rate."]
    for identifier, colour, size in (("raw", style.RED, 5), (common.RECOMMENDED, style.MINT, 4)):
        estimates = common.cached_estimates(info.record_name, "rest", identifier)[key]
        values = estimates[times - 1, 1]
        axis.scatter(times / 60, values, s=size, color=colour, alpha=0.75, label=f"device, {FILTER_TITLES[identifier]}", linewidths=0)
        clean = numpy.isfinite(ecg)
        error = numpy.abs(values[clean] - ecg[clean])
        caption.append(f"{FILTER_TITLES[identifier]}: mean difference {error.mean():.2f} BPM over {clean.sum()} clean windows, "
                       f"{numpy.count_nonzero(error > 0.2 * ecg[clean])} more than 20 % off")
    axis.set_xlabel("time in the record (minutes)")
    axis.set_ylabel("heart rate (BPM)")
    axis.set_ylim(30, 210)
    axis.legend(loc="upper left", frameon=False, markerscale=3)
    activity = info.scenario.split(":")[-1].strip()
    axis.set_title(f"One exercise record over time: ECG against the device's estimate (one person, {activity})", loc="left",
                   fontsize=14)
    figure.tight_layout()
    save(figure, "run2_bpm_estimate_vs_ecg", " ".join(caption))


def figure_sound_reference(validation_rows):
    rows = [row for row in validation_rows if row["ecg_reliable"] == "True" and row["sound_reference_bpm"] not in ("", "None")]
    if not rows:
        print("no sound-reference validation rows yet")
        return
    figure, axes = pyplot.subplots(1, 2, figsize=(12.5, 5.8))
    caption = []
    for flag, colour, label in (("True", style.MINT, "marked trustworthy by the sound method"),
                                ("False", style.AMBER, "marked uncertain by the sound method")):
        subset = [row for row in rows if row["sound_reference_reliable"] == flag]
        ecg = numpy.array([number(row["ecg_bpm"]) for row in subset])
        sound = numpy.array([number(row["sound_reference_bpm"]) for row in subset])
        if not subset:
            continue
        axes[0].scatter(ecg, sound, s=6, color=colour, alpha=0.6, label=f"{label} ({len(subset)})", linewidths=0)
        axes[1].scatter(ecg, sound - ecg, s=6, color=colour, alpha=0.6, linewidths=0)
        difference = numpy.abs(sound - ecg)
        caption.append(f"{label}: {len(subset)} windows, mean difference {difference.mean():.2f} BPM, largest {difference.max():.1f} BPM, "
                       f"{100 * numpy.mean(difference <= 2):.1f} % within 2 BPM")
    limits = (40, 200)
    axes[0].plot(limits, limits, color=style.SECONDARY, linewidth=1.0)
    axes[0].set_xlim(*limits)
    axes[0].set_ylim(*limits)
    axes[0].set_xlabel("ECG heart rate (BPM)")
    axes[0].set_ylabel("heart rate from the sound alone (BPM)")
    axes[0].legend(loc="upper left", frameon=False, markerscale=3, fontsize=10.5)
    axes[1].axhline(0, color=style.SECONDARY, linewidth=1.0)
    axes[1].set_xlim(*limits)
    axes[1].set_ylim(-30, 30)
    axes[1].set_xlabel("ECG heart rate (BPM)")
    axes[1].set_ylabel("sound minus ECG (BPM)")
    figure.suptitle("Heart rate from the sound alone, as in the first part, checked against ECG on public recordings", x=0.02, ha="left")
    figure.tight_layout()
    subjects = len({row["subject_id"] for row in rows})
    excerpts = len({(row["record"], row["excerpt_start_s"]) for row in rows})
    save(figure, "run2_sound_reference_vs_ecg",
         f"Each point is one 8 s window with a clean ECG ({len(rows)} windows, {excerpts} one-minute excerpts, {subjects} people); "
         f"differences beyond ±30 BPM are outside the right panel. " + "; ".join(caption))


def main():
    style.apply_style()
    band_rows = read_csv(RESULTS_DIRECTORY / "bpm_public_by_band.csv")
    comparison_rows = read_csv(RESULTS_DIRECTORY / "bpm_public_run1_comparison.csv")
    grid_rows = read_csv(RESULTS_DIRECTORY / "bpm_public_grid.csv")
    figure_error_by_heart_rate(band_rows)
    figure_lower_edge(comparison_rows)
    figure_counting_methods(comparison_rows)
    figure_estimate_vs_ecg(grid_rows)
    validation_path = RESULTS_DIRECTORY / "sound_reference_validation.csv"
    if validation_path.exists():
        figure_sound_reference(read_csv(validation_path))


if __name__ == "__main__":
    main()
