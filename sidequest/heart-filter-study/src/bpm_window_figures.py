"""Page figures for the whole-window methods: page/figures/run2_window_methods_error.png and run2_window_methods_cost.png
(each with a .txt of the plotted numbers), in the style of src/page_figures.py.

Usage: python -I src/bpm_window_figures.py  (after bpm_window_methods.py, bpm_window_public.py compute and bpm_window_budget.py)
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy

import bpm_evaluate
import bpm_window_methods as own
import bpm_window_public as public
import bpm_window_public_report as public_report
import page_figures as style
from hfs.recordings import RECORDING_NAMES, STUDY_DIRECTORY

pyplot = style.pyplot
FIGURE_NAMES = ("run2_window_methods_error", "run2_window_methods_cost")
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20261123
BLOCK_LENGTH = 8

METHOD_LABELS = {
    "causal_40_150": "Filter while recording, 40–150 Hz (method of the first part)",
    "causal_25_150": "Filter while recording, 25–150 Hz",
    "causal_raw": "No filter",
    "causal_40_150_twice": "Filter while recording, 40–150 Hz applied twice (steeper)",
    "stored_envelope_nosmooth_taper20": "Method of the first part, soft edges on the stored loudness curve",
    "stored_envelope_smooth5hz_taper0": "Method of the first part, stored loudness curve smoothed again",
    "zero_phase_40_150_order2_reflect_zpenv": "Whole window filtered forwards and backwards, 40–150 Hz",
    "forward_twice_40_150_order2_reflect_causalenv": "Same filter steepness, both passes forwards (delay kept)",
    "streamed_forward_backward_window_40_150_order2_reflect_zpenv": "Forward pass while recording, backward pass on the window",
    "reduced_1k_zero_phase_40_150_order2_reflect_zpenv": "Forwards and backwards on 1,000 values per second",
    "springer_heart_rate": "Springer reference code as published (up to 120 BPM)",
    "springer_heart_rate_range_30_200": "Springer reference code, range widened to 200 BPM, without half-rate check",
    "springer_heart_rate_half_check": "Springer reference code, range widened to 200 BPM, with half-rate check",
    "springer_envelopes_combined_50hz_half_check": "Springer's three loudness curves combined",
    "reduced_1k_zero_phase_40_150_order2_reflect_homomorphic": "1,000 values per second, both directions, Springer's\nlogarithmic loudness curve (tried after first results)",
}
SHOWN_METHODS = list(METHOD_LABELS)


def check_names():
    for name in FIGURE_NAMES:
        caption = style.FIGURES_DIRECTORY / f"{name}.txt"
        if caption.exists() and "whole-window" not in caption.read_text(encoding="utf-8"):
            raise SystemExit(f"{caption} exists and was not written by this script; not overwriting")


def own_errors(method):
    reference = bpm_evaluate.load_reference(STUDY_DIRECTORY / "reference")
    estimates = {name: json.loads(own.own_cache_path(name, method).read_text())["rows"] for name in RECORDING_NAMES}
    arrays = bpm_evaluate.aligned_arrays(estimates, reference)
    return {name: numpy.abs(arrays[name]["estimate"] - arrays[name]["reference"]) for name in RECORDING_NAMES}


def own_interval(errors_by_recording):
    """Moving-block bootstrap over windows within each recording (as run 1), interval of the mean error."""
    generator = numpy.random.default_rng(BOOTSTRAP_SEED)
    means = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        total = 0.0
        count = 0
        for errors in errors_by_recording.values():
            starts = generator.integers(0, max(1, errors.size - BLOCK_LENGTH + 1), int(numpy.ceil(errors.size / BLOCK_LENGTH)))
            chosen = (starts[:, None] + numpy.arange(BLOCK_LENGTH)[None, :]).ravel()[:errors.size]
            total += errors[chosen].sum()
            count += errors.size
        means.append(total / count)
    return numpy.percentile(means, [2.5, 97.5])


def public_values(condition):
    windows, records = public_report.load_condition(condition)
    if not records:
        return {}, 0, 0, 0
    values = {}
    for method in SHOWN_METHODS:
        if method not in windows:
            continue
        arrays = public_report.arrays_of(windows[method])
        mask = arrays["reliable"]
        error = numpy.abs(numpy.nan_to_num(arrays["estimate"][mask], nan=0.0) - arrays["reference"][mask])
        subjects = arrays["subject"][mask]
        unique, index = numpy.unique(subjects, return_inverse=True)
        sums = numpy.bincount(index, weights=error, minlength=unique.size)
        counts = numpy.bincount(index, minlength=unique.size).astype(float)
        generator = numpy.random.default_rng(BOOTSTRAP_SEED)
        draws = generator.integers(0, unique.size, size=(BOOTSTRAP_RESAMPLES, unique.size))
        resampled = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
        values[method] = (float(error.mean()), *numpy.percentile(resampled, [2.5, 97.5]))
        window_count, subject_count = int(mask.sum()), int(unique.size)
    return values, len(records), window_count, subject_count


def figure_error():
    own_values = {}
    for method in SHOWN_METHODS:
        errors = own_errors(method)
        mean = float(numpy.concatenate(list(errors.values())).mean())
        low, high = own_interval(errors)
        own_values[method] = (mean, float(low), float(high))
    rest_values, record_count, window_count, subject_count = public_values("rest")
    overload_values, _, _, _ = public_values("overload")
    figure, axes = pyplot.subplots(1, 3, figsize=(20, 9.0), sharey=True)
    positions = numpy.arange(len(SHOWN_METHODS))[::-1]
    panels = ((axes[0], own_values, "Own recordings, all windows\n(5 recordings, 255 windows)", style.MINT),
              (axes[1], rest_values, f"Public recordings with ECG, rest level\n({subject_count} people, "
                                     f"{window_count:,} windows\nwith a reliable ECG rate)", style.BLUE),
              (axes[2], overload_values, f"Same public recordings,\noverload level ({subject_count} people)", style.SKY))
    for axis, values, title, colour in panels:
        baseline = values.get("causal_40_150")
        maximum = max((value[2] for value in values.values()), default=1.0)
        for position, method in zip(positions, SHOWN_METHODS):
            if method not in values:
                axis.text(0.02 * maximum, position, "not computed", va="center", color=style.SECONDARY, fontsize=11)
                continue
            mean, low, high = values[method]
            bar_colour = style.AMBER if method == "causal_40_150" else colour
            axis.barh(position, mean, height=0.62, color=bar_colour)
            axis.plot([low, high], [position, position], color=style.TEXT, linewidth=1.6)
            axis.text(high + maximum * 0.02, position, f"{mean:.2f}", va="center", ha="left", fontsize=11.5, color=style.TEXT)
        if baseline:
            axis.axvline(baseline[0], color=style.AMBER, linestyle="--", linewidth=1.2)
        axis.set_xlim(0, maximum * 1.25)
        axis.set_title(title, loc="left", fontsize=13)
        axis.set_xlabel("mean error (BPM), line: 95 % range")
        axis.grid(axis="y", visible=False)
    axes[0].set_yticks(positions)
    axes[0].set_yticklabels([METHOD_LABELS[method] for method in SHOWN_METHODS], fontsize=11.5)
    axes[0].tick_params(axis="y", labelcolor=style.TEXT)
    figure.suptitle("Does working on the whole stored 8 seconds count the heart rate better?\n"
                    "Dashed line and amber bar: the method of the first part", x=0.01, ha="left", fontsize=15)
    figure.tight_layout()
    lines = ["Plotted numbers (whole-window methods), mean absolute heart-rate error in BPM with 95 % bootstrap range.",
             "Own recordings: all 255 windows of 5 recordings; range from a moving-block bootstrap (8 windows) within each recording.",
             f"Public: EPHNOGRAM through the modelled capture chain (level: rest), windows ending every 4th second from 12 s, "
             f"{window_count} windows with a reliable ECG rate, {subject_count} people, {record_count} recordings; range from resampling people. "
             "Second public panel: the same windows at the overload level of the chain model."]
    for method in SHOWN_METHODS:
        own_text = "own {:.2f} [{:.2f}, {:.2f}]".format(*own_values[method])
        public_text = "public rest {:.2f} [{:.2f}, {:.2f}]".format(*rest_values[method]) if method in rest_values else "public rest not computed"
        overload_text = ("public overload {:.2f} [{:.2f}, {:.2f}]".format(*overload_values[method]) if method in overload_values
                         else "public overload not computed")
        lines.append(f"{METHOD_LABELS[method].replace(chr(10), ' ')} ({method}): {own_text}; {public_text}; {overload_text}")
    style.save_figure(figure, FIGURE_NAMES[0], "\n".join(lines))


def figure_cost():
    with open(own.RESULTS_DIRECTORY / "device_budget.csv", encoding="utf-8") as handle:
        budget = {row["method"]: row for row in csv.DictReader(handle)}
    shown = [method for method in SHOWN_METHODS if method in budget or method.startswith("springer_heart_rate")]
    shown = [method for method in shown if method in budget]
    figure, axes = pyplot.subplots(1, 2, figsize=(18, 7.4), sharey=True)
    positions = numpy.arange(len(shown))[::-1]
    time_values = [10.0 * float(budget[method]["core_share_percent_at_one_update_per_second"]) for method in shown]
    memory_values = [(float(budget[method]["psram_kilobytes"]) + float(budget[method]["internal_ram_kilobytes"])) for method in shown]
    for axis, values, label, unit in ((axes[0], time_values, "processor time per second\n(milliseconds, estimate)", "ms"),
                                      (axes[1], memory_values, "memory for the analysis\n(kilobytes, estimate)", "kB")):
        maximum = max(values)
        for position, method, value in zip(positions, shown, values):
            axis.barh(position, value, height=0.62, color=style.AMBER if method == "causal_40_150" else style.VIOLET)
            axis.text(value + maximum * 0.02, position, f"{value:,.1f} {unit}", va="center", ha="left", fontsize=11.5, color=style.TEXT)
        axis.axvline(values[shown.index("causal_40_150")], color=style.AMBER, linestyle="--", linewidth=1.2)
        axis.set_xlim(0, maximum * 1.3)
        axis.set_xlabel(label)
        axis.grid(axis="y", visible=False)
    axes[0].set_yticks(positions)
    axes[0].set_yticklabels([METHOD_LABELS[method] for method in shown], fontsize=11.5)
    axes[0].tick_params(axis="y", labelcolor=style.TEXT)
    axes[0].set_title("Filtering while recording\nplus one count per second", loc="left", fontsize=13)
    axes[1].set_title("Stored window\nplus working memory", loc="left", fontsize=13)
    figure.suptitle("What each counting method would cost on the stethoscope's processor (estimate, not measured)\n"
                    "Dashed line and amber bar: the method of the first part", x=0.01, ha="left", fontsize=15)
    figure.tight_layout()
    lines = ["Plotted numbers (whole-window methods): estimated processor time per second (continuous filtering while recording plus "
             "one update per second) and memory, "
             "from results-window/device_budget.csv; estimate, not measured on the ESP32-S3; slower external memory not included."]
    for method, time_value, memory_value in zip(shown, time_values, memory_values):
        row = budget[method]
        lines.append(f"{METHOD_LABELS[method].replace(chr(10), ' ')} ({method}): {time_value:.2f} ms of processor time per second "
                     f"({row['per_update_milliseconds']} ms of it in the once-per-second update), {memory_value:.1f} kB "
                     f"(external {row['psram_kilobytes']} kB, internal {row['internal_ram_kilobytes']} kB), "
                     f"share of one core at one update per second {row['core_share_percent_at_one_update_per_second']} %")
    style.save_figure(figure, FIGURE_NAMES[1], "\n".join(lines))


def main():
    check_names()
    style.apply_style()
    figure_error()
    figure_cost()


if __name__ == "__main__":
    main()
