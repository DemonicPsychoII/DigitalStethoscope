"""Page figures for the improved counting method, in the style of src/page_figures.py.

Usage: python -I src/bpm_improved_method_figures.py [--force]
Writes page/figures/run2_bpm_by_activity.png, run2_bpm_one_third_explained.png and
run2_bpm_estimate_vs_ecg_improved.png, each with a .txt of the plotted numbers. Existing figures are overwritten only with --force.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
import numpy

import bpm_improved_method_common as improved
import bpm_improved_method_diagnosis as diagnosis
import bpm_improved_method_own as own
import bpm_improved_method_report as report
import page_figures as style
import public_evaluation_common as common
from hfs import ephnogram

EXAMPLE_RECORD = "ECGPCG0064"
EXAMPLE_END_SECONDS = 900
GROUP_TITLES = {"seated rest": "sitting\nstill", "lying": "lying\ndown", "walking": "walking",
                "stress tests": "stress\ntests", "pedalling": "steady\npedalling"}


FORCE = "--force" in sys.argv[1:]


def save(figure, name, caption):
    if not FORCE and (style.FIGURES_DIRECTORY / f"{name}.png").exists():
        raise SystemExit(f"{name}.png exists; remove it by hand to regenerate")
    style.save_figure(figure, name, caption)


def figure_by_activity():
    _, merged = report.measure_filter(common.RECOMMENDED)
    methods = {"final": ("counting method of the first part", style.RED), "improved": ("improved counting method", style.MINT)}
    figure, axes = pyplot.subplots(1, 2, figsize=(15, 6.2))
    positions = numpy.arange(len(improved.ACTIVITY_GROUPS))
    width = 0.38
    lines = ["Public recordings (EPHNOGRAM), sound passed through a model of the device, rest level, filter 40-150 Hz, "
             "only windows where the ECG rate is clean. All 21 subjects with clean ECG; the improved method was chosen on 11 of "
             "them, the numbers of the other 10 alone are in results-public/improved_method.md. Stress tests = treadmill and bicycle stress tests; steady pedalling = stationary bicycle at constant effort.",
             "group | method | mean difference to ECG (BPM) | share within 5 BPM or 10 % | subjects | windows"]
    for offset, (method_name, (label, colour)) in zip((-width / 2, width / 2), methods.items()):
        measures = merged[(method_name, "rest")]
        means, shares, subject_counts = [], [], []
        for group in improved.ACTIVITY_GROUPS:
            mask = measures["group"] == group
            means.append(measures["absolute"][mask].mean())
            shares.append(measures["within"][mask].mean() * 100)
            subject_counts.append(len(numpy.unique(measures["subject"][mask])))
            lines.append(f"{group} | {label} | {means[-1]:.2f} | {shares[-1]:.1f} % | {subject_counts[-1]} | {int(mask.sum())}")
        axes[0].bar(positions + offset, means, width, color=colour, label=label)
        axes[1].bar(positions + offset, shares, width, color=colour, label=label)
        for position, mean, share in zip(positions + offset, means, shares):
            axes[0].text(position, mean + 0.6, f"{mean:.1f}", ha="center", fontsize=10, color=style.TEXT)
            axes[1].text(position, share + 1.0, f"{share:.0f}", ha="center", fontsize=10, color=style.TEXT)
    labels = [f"{GROUP_TITLES[group]}\n({count} people)" for group, count in zip(improved.ACTIVITY_GROUPS, subject_counts)]
    for axis in axes:
        axis.set_xticks(positions)
        axis.set_xticklabels(labels, fontsize=10.5)
    axes[0].set_ylabel("mean difference to ECG (BPM)")
    axes[0].set_title("How far off, on average", loc="left")
    axes[1].set_ylabel("share of windows within 5 BPM or 10 % (%)")
    axes[1].set_ylim(0, 108)
    axes[1].set_title("How often close enough", loc="left")
    axes[0].legend(loc="upper left", frameon=False)
    figure.suptitle("Heart rate from the sound, by activity: counting method of the first part and improved method", x=0.02, ha="left")
    figure.text(0.02, 0.01, "All people, including the 11 on whom the improved method was tuned.", fontsize=10,
                color=style.SECONDARY)
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    save(figure, "run2_bpm_by_activity", "\n".join(lines))


def figure_one_third_explained():
    envelope = diagnosis.envelopes_for(EXAMPLE_RECORD, "rest", common.FINAL_METHOD)
    reference = common.load_reference(EXAMPLE_RECORD)
    heart_rate = reference[EXAMPLE_END_SECONDS]["reference_bpm"]
    beat_spacing = 60.0 / heart_rate
    window = diagnosis.window_at(envelope, EXAMPLE_END_SECONDS)
    correlation = diagnosis.normalised(window)
    lags = numpy.arange(correlation.shape[0])
    weighted = correlation * (diagnosis.WINDOW_LENGTH - lags) / diagnosis.WINDOW_LENGTH
    beat_times = numpy.array(json.loads((common.REFERENCE_DIRECTORY / f"{EXAMPLE_RECORD}.json").read_text())["beat_times_s"])
    figure, axes = pyplot.subplots(1, 2, figsize=(14, 5.4), gridspec_kw={"width_ratios": [1.1, 1]})
    time_axis = numpy.arange(diagnosis.WINDOW_LENGTH) / diagnosis.ENVELOPE_RATE_HZ - 8
    axes[0].plot(time_axis, window / window.max(), color=style.SKY, linewidth=1.3)
    for beat_time in beat_times[(beat_times >= EXAMPLE_END_SECONDS - 8) & (beat_times <= EXAMPLE_END_SECONDS)]:
        axes[0].axvline(beat_time - EXAMPLE_END_SECONDS, color=style.RED, linewidth=0.9, alpha=0.6)
    axes[0].set_xlabel("time (seconds before the estimate)")
    axes[0].set_ylabel("loudness of the heart sound (scaled)")
    axes[0].set_title(f"8 seconds of sound: {heart_rate:.0f} beats per minute by ECG (red lines)", loc="left", fontsize=12.5)
    shift = lags / diagnosis.ENVELOPE_RATE_HZ
    search = (shift >= 0.3) & (shift <= 2.0)
    axes[1].plot(shift[search], correlation[search], color=style.RED, linewidth=2, label="method of the first part: compared as is")
    axes[1].plot(shift[search], weighted[search], color=style.MINT, linewidth=2,
                 label="improved: longer shifts count slightly less")
    lines = [f"Record {EXAMPLE_RECORD}, subject S006, bicycle stress test, 8 s window ending at {EXAMPLE_END_SECONDS} s, "
             f"ECG {heart_rate:.1f} BPM, filter 40-150 Hz, rest level.", "beats apart | shift (s) | first-part similarity | improved similarity"]
    for multiple in (1, 2, 3, 4):
        lag = multiple * beat_spacing * diagnosis.ENVELOPE_RATE_HZ
        if lag / diagnosis.ENVELOPE_RATE_HZ > 2.0:
            continue
        low, high = int(lag * 0.9), int(numpy.ceil(lag * 1.1))
        peak = low + int(numpy.argmax(correlation[low:high + 1]))
        axes[1].annotate(f"{multiple} beat{'s' if multiple > 1 else ''}\napart", (shift[peak], correlation[peak]),
                         textcoords="offset points", xytext=(0, 10), ha="center", fontsize=10.5, color=style.TEXT)
        lines.append(f"{multiple} | {shift[peak]:.2f} | {correlation[peak]:.3f} | {weighted[peak]:.3f}")
    old_choice = int(numpy.argmax(numpy.where(search, correlation, -9)))
    axes[1].scatter([shift[old_choice]], [correlation[old_choice]], s=120, facecolors="none", edgecolors=style.RED, linewidths=2.5)
    axes[1].set_ylim(-0.55, 1.15)
    axes[1].set_xlabel("shift (seconds)")
    axes[1].set_ylabel("how alike the sound is to itself shifted")
    axes[1].set_title("All whole-beat shifts look almost equally alike", loc="left", fontsize=12.5)
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), frameon=False, fontsize=10.5)
    figure.text(0.02, -0.1, f"The method of the first part took the highest peak (red circle, 3 beats apart: "
                f"{60 / shift[old_choice]:.0f} BPM, one third of the true rate), because the peaks differ by only a few per cent. "
                "The improved method lets longer shifts count slightly less, then checks a quarter, a third and half of the best "
                "shift and takes the shortest of these whose peak is at least 60 % as high.",
                fontsize=11, color=style.SECONDARY, wrap=True)
    lines.append(f"choice of the method of the first part: {shift[old_choice]:.2f} s = {60 / shift[old_choice]:.1f} BPM")
    figure.suptitle("Why the device reported one third of the heart rate", x=0.02, ha="left")
    figure.tight_layout()
    save(figure, "run2_bpm_one_third_explained", "\n".join(lines))


def figure_estimate_vs_ecg_improved():
    methods = own.chosen_configurations()
    info = ephnogram.record_info(EXAMPLE_RECORD)
    record = improved.RecordData(info, "rest")
    reference = common.load_reference(EXAMPLE_RECORD)
    figure, axis = pyplot.subplots(figsize=(12, 5.4))
    correlations, end_times, clipped = record.load(common.RECOMMENDED, improved.envelope_name(methods["improved"]))
    times = end_times.astype(int)
    keep = times >= common.FIRST_SCORED_END_TIME_SECONDS
    ecg = numpy.array([reference[time]["reference_bpm"] if time in reference and reference[time].get("reliable") else numpy.nan
                       for time in times], float)
    axis.plot(times[keep] / 60, ecg[keep], color=style.TEXT, linewidth=2.0, label="ECG heart rate (clean windows)")
    lines = [f"Record {EXAMPLE_RECORD}, subject {info.subject_id}, {info.scenario}; rest level, filter 40-150 Hz "
             "(same record as run2_bpm_estimate_vs_ecg.png). Subject S006 belongs to the half on which the improved method was chosen."]
    for method_name, colour, label in (("final", style.RED, "device, counting method of the first part"),
                                       ("improved", style.MINT, "device, improved counting method")):
        output = improved.estimates_from_correlations(correlations, clipped, methods[method_name])
        values = output[:, 0]
        valid = output[:, 1] > 0.5
        axis.scatter(times[keep] / 60, values[keep], s=4, color=colour, alpha=0.75, label=label, linewidths=0)
        clean = keep & numpy.isfinite(ecg)
        error = numpy.abs(values[clean] - ecg[clean])
        shown = clean & valid
        lines.append(f"{label}: mean difference {error.mean():.2f} BPM over {clean.sum()} clean windows, "
                     f"{numpy.count_nonzero(error > 0.2 * ecg[clean])} more than 20 % off; shown as valid {shown.sum()} windows, "
                     f"of which {numpy.count_nonzero(numpy.abs(values[shown] - ecg[shown]) > 0.2 * ecg[shown])} more than 20 % off")
    axis.set_xlabel("time in the record (minutes)")
    axis.set_ylabel("heart rate (BPM)")
    axis.set_ylim(30, 210)
    axis.legend(loc="upper left", frameon=False, markerscale=3)
    axis.set_title("One exercise record over time: ECG against the device, counting method of the first part and improved\n"
                   "counting, one person, bicycle stress test (a person from the half used for tuning)",
                   loc="left", fontsize=14)
    figure.tight_layout()
    save(figure, "run2_bpm_estimate_vs_ecg_improved", "\n".join(lines))


def main():
    style.apply_style()
    figure_one_third_explained()
    figure_estimate_vs_ecg_improved()
    figure_by_activity()


if __name__ == "__main__":
    main()
