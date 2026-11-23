"""Figures and small tables for the plain-language report page.

Usage: python src/page_figures.py [--only shortlist_responses,shortlist_tradeoff]
Writes page/figures/<name>.png with a caption fact file <name>.txt, and page/tables/<name>.csv.
--only regenerates just the named figures and leaves every other figure and table untouched.
BPM estimates come from the evaluation cache (cache/bpm); missing entries are computed with the library.
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
import numpy
import soundfile
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpm_evaluate
from hfs import device_chain, filters
from hfs.bpm_estimator import EstimatorConfiguration
from hfs.recordings import (RECORDING_NAMES, RECORDINGS_DIRECTORY, SAMPLE_MAXIMUM, SAMPLE_MINIMUM, SAMPLE_RATE_HZ,
                            STUDY_DIRECTORY, load_recording)

FIGURES_DIRECTORY = STUDY_DIRECTORY / "page" / "figures"
TABLES_DIRECTORY = STUDY_DIRECTORY / "page" / "tables"
REFERENCE_DIRECTORY = STUDY_DIRECTORY / "reference"
LISTENING_DIRECTORY = STUDY_DIRECTORY / "listening"
WELCH_SEGMENT_SAMPLES = 16384
FULL_SCALE = 8388608.0

BACKGROUND = "#0b0f10"
TEXT = "#f2f6f6"
SECONDARY = "#96a3a4"
GRID = "#192021"
SPINE = "#252d2f"
MINT, AMBER, BLUE, PINK = "#7ad8c8", "#f2c14e", "#7aa7ff", "#f59ac6"
VIOLET, ORANGE, LIME, SKY, RED = "#b49cff", "#ffa570", "#a6d96b", "#6cc3ff", "#f08a7c"
SERIES_COLOURS = [MINT, AMBER, BLUE, PINK, VIOLET, ORANGE, LIME, SKY]
BOX_FACE = "#141b1d"

FIRST_DRAFT_ESTIMATOR = EstimatorConfiguration()
FINAL_ESTIMATOR = EstimatorConfiguration(envelope_lowpass="two_pole", envelope_lowpass_hz=5.0, peak_choice="half_check")
FINAL_ESTIMATOR_KEY = "envelope_lowpass=two_pole,envelope_lowpass_hz=5.0,peak_choice=half_check"
assert FINAL_ESTIMATOR.key() == FINAL_ESTIMATOR_KEY

RECORDING_TITLES = {"rest-1": "Resting 1", "rest-2": "Resting 2", "elevated-1": "After exercise 1 (overload only at the start)",
                    "elevated-2": "After exercise 2 (overload on many beats)",
                    "elevated-3": "After exercise 3 (overload in the first half)"}
RECORDING_SHORT = {"rest-1": "Resting 1", "rest-2": "Resting 2", "elevated-1": "After exercise 1",
                   "elevated-2": "After exercise 2", "elevated-3": "After exercise 3"}

SPEC_RAW = bpm_evaluate.specification("raw", None, None)
SPEC_DESIGN_BPM = bpm_evaluate.specification("butterworth", 25, 150)
SPEC_RECOMMENDED = bpm_evaluate.specification("butterworth", 40, 150)

BPM_SUMMARY_ROWS = [
    ("No filter (Raw)", SPEC_RAW),
    ("25–150 Hz gentle (design candidate BPM)", SPEC_DESIGN_BPM),
    ("30–150 Hz gentle", bpm_evaluate.specification("butterworth", 30, 150)),
    ("40–150 Hz gentle (recommended)", SPEC_RECOMMENDED),
    ("40–800 Hz gentle (design candidate Murmur)", bpm_evaluate.specification("butterworth", 40, 800)),
    ("100–800 Hz gentle (louder listening candidate)", bpm_evaluate.specification("butterworth", 100, 800)),
    ("30–300 Hz elliptic, steep lower edge (best-ranked)", bpm_evaluate.specification("elliptic", 30, 300, 4, 2)),
]

SHORTLIST_LABELS = {
    "raw": "No filter (Raw)",
    "butterworth_hp2_40_lp2_800": "40–800 Hz, gentle (design candidate)",
    "butterworth_hp2_100_lp2_800": "100–800 Hz, gentle",
    "butterworth_hp4_100_lp4_800": "100–800 Hz, steep",
    "butterworth_hp4_150_lp4_800": "150–800 Hz, steep",
    "elliptic_hp4_60_lp4_800": "60–800 Hz, very steep (elliptic)",
    "butterworth_hp2_80_lp0_none": "Above 80 Hz only",
    "butterworth_hp2_25_lp2_150": "25–150 Hz (BPM position)",
    "butterworth_hp2_40_lp2_150": "40–150 Hz (recommended BPM filter)",
}
SHORTLIST_FIGURE_LABELS = {**SHORTLIST_LABELS,
                           "butterworth_hp2_25_lp2_150": "25–150 Hz (BPM position, as originally planned)"}

FAMILY_NAMES = {"butterworth": "Butterworth", "bessel": "Bessel", "chebyshev1": "Chebyshev I",
                "chebyshev2": "Chebyshev II", "elliptic": "elliptic", "fir": "FIR", "decimated": "rate-reduced"}


# ---------------------------------------------------------------- style and helpers

def apply_style():
    pyplot.rcParams.update({
        "figure.facecolor": BACKGROUND, "axes.facecolor": BACKGROUND, "savefig.facecolor": BACKGROUND,
        "text.color": TEXT, "axes.labelcolor": TEXT, "axes.edgecolor": SPINE, "axes.titlecolor": TEXT,
        "xtick.color": SECONDARY, "ytick.color": SECONDARY, "xtick.labelcolor": SECONDARY, "ytick.labelcolor": SECONDARY,
        "grid.color": GRID, "grid.linewidth": 1.0, "axes.grid": True, "axes.axisbelow": True,
        "font.size": 13, "axes.titlesize": 14, "axes.labelsize": 13, "xtick.labelsize": 12, "ytick.labelsize": 12,
        "legend.fontsize": 12, "legend.facecolor": BACKGROUND, "legend.edgecolor": SPINE, "legend.labelcolor": TEXT,
        "figure.titlesize": 16, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
    })


def save_figure(figure, name, caption):
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURES_DIRECTORY / f"{name}.png", dpi=200, bbox_inches="tight", pad_inches=0.15)
    pyplot.close(figure)
    (FIGURES_DIRECTORY / f"{name}.txt").write_text(caption.strip() + "\n", encoding="utf-8")
    print(f"figure {name}")


def write_table(name, header, rows):
    TABLES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with open(TABLES_DIRECTORY / f"{name}.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"table {name}")


def signed(value):
    rounded = round(value, 1)
    return "0.0" if rounded == 0 else f"{rounded:+.1f}"


def rounded_down(value, decimals=1):
    scale = 10 ** decimals
    # The epsilon absorbs binary representation error such as 0.29 * 100 = 28.999..., so exact values are not lowered.
    rounded = math.floor(value * scale + 1e-9) / scale
    return f"{0:.{decimals}f}" if rounded == 0 else f"{rounded:+.{decimals}f}"


def hertz_label(value, _=None):
    return f"{value / 1000:g} kHz" if value >= 1000 else f"{value:g} Hz"


def hertz_axis(axis, minimum_hz, maximum_hz, ticks=(5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 8000)):
    axis.set_xscale("log")
    axis.set_xlim(minimum_hz, maximum_hz)
    axis.xaxis.set_major_locator(FixedLocator([value for value in ticks if minimum_hz <= value <= maximum_hz]))
    axis.xaxis.set_major_formatter(FuncFormatter(hertz_label))
    axis.xaxis.set_minor_formatter(NullFormatter())
    axis.xaxis.set_minor_locator(NullLocator())


def full_file_full_scale(name):
    left_aligned, _ = soundfile.read(RECORDINGS_DIRECTORY / name / "capture.wav", dtype="int32")
    samples = (left_aligned >> 8).astype(numpy.int32)
    return samples


def load_reference(name):
    return json.loads((REFERENCE_DIRECTORY / f"{name}.json").read_text())


def recording_full_scale(name):
    return load_recording(name).astype(numpy.float64) / FULL_SCALE


def window_reference(name):
    windows = load_reference(name)["windows"]
    return (numpy.array([window["end_time_s"] for window in windows], float),
            numpy.array([window["reference_bpm"] if window["reference_bpm"] is not None else numpy.nan for window in windows], float),
            numpy.array([bool(window.get("reliable", True)) for window in windows]))


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# ---------------------------------------------------------------- BPM evaluation access

_BPM_LOADED = {}
_BPM_REFERENCE = bpm_evaluate.load_reference(REFERENCE_DIRECTORY)


def bpm_estimates(spec, configuration):
    """Per recording list of [end_time, bpm, valid, quality, margin, reason], from the evaluation cache."""
    identifier = bpm_evaluate.candidate_identifier(spec)
    key = (identifier, configuration)
    if key not in _BPM_LOADED:
        loaded, _ = bpm_evaluate.run_items([(identifier, spec, [configuration])], workers=4)
        _BPM_LOADED.update(loaded)
    return _BPM_LOADED[key]


def bpm_arrays(spec, configuration):
    return bpm_evaluate.aligned_arrays(bpm_estimates(spec, configuration), _BPM_REFERENCE)


def bpm_metrics(spec, configuration):
    return bpm_evaluate.compute_metrics(bpm_arrays(spec, configuration))


def multiplies(spec):
    return filters.cost(bpm_evaluate.build_candidate(spec))["multiplies_per_sample"]


# ---------------------------------------------------------------- 1 signal chain

def figure_signal_chain():
    figure = pyplot.figure(figsize=(10, 7.5))
    axis = figure.add_axes([0, 0, 1, 1])
    axis.set_xlim(0, 100)
    axis.set_ylim(0, 75)
    axis.axis("off")

    def box(x, y, width, height, text, accent=False, size=13):
        colour = AMBER if accent else SPINE
        patch = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.4,rounding_size=1.6",
                               facecolor="#1d1a10" if accent else BOX_FACE, edgecolor=colour, linewidth=2.6 if accent else 1.6)
        axis.add_patch(patch)
        axis.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=size, color=TEXT, linespacing=1.25)
        return (x, y, width, height)

    def arrow(start, end, colour=SECONDARY, style="-|>", connection="arc3"):
        axis.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=20, color=colour, linewidth=2.0,
                                       connectionstyle=connection, shrinkA=2, shrinkB=2))

    axis.text(50, 72.2, "How the sound travels through the stethoscope", ha="center", va="center", fontsize=16,
              color=TEXT, weight="bold")
    # source row
    chest = box(14, 59, 26, 8, "Chest-piece and tube")
    microphone = box(52, 59, 34, 8, "Microphone\n16,000 values per second, 24 bit")
    arrow((chest[0] + chest[2] + 0.6, 63), (microphone[0] - 0.6, 63))
    split_x = microphone[0] + microphone[2] / 2

    # listening row
    axis.text(2.5, 52.5, "Listening", fontsize=15, color=MINT, weight="bold", va="center")
    listening_y, listening_height, width = 37, 11, 20.5
    xs = [2.5, 27.0, 51.5, 76.0]
    labels = ["Switch:\nRaw / Murmur /\nBPM filter", "Volume\n(0–100 %)", "Output limit\n(24 bit)", "Converter and\nearpieces"]
    listening_boxes = [box(x, listening_y, width, listening_height, label, accent=index == 0) for index, (x, label) in enumerate(zip(xs, labels))]
    for left, right in zip(listening_boxes[:-1], listening_boxes[1:]):
        arrow((left[0] + left[2] + 0.6, listening_y + listening_height / 2), (right[0] - 0.6, listening_y + listening_height / 2))

    # heart-rate row
    axis.text(2.5, 29.0, "Heart-rate measurement", fontsize=15, color=BLUE, weight="bold", va="center")
    rate_y, rate_height, rate_width = 11, 13, 16.2
    rate_xs = [2.5 + index * 19.6 for index in range(5)]
    rate_labels = ["BPM filter\n(always on)", "Loudness\ncurve, 100\nvalues per\nsecond", "Last 8 s\nkept in\nmemory",
                   "Repeat\npattern\nsearch, once\nper second", "Beats per\nminute"]
    rate_boxes = [box(x, rate_y, rate_width, rate_height, label, accent=index == 0, size=12.5)
                  for index, (x, label) in enumerate(zip(rate_xs, rate_labels))]
    for left, right in zip(rate_boxes[:-1], rate_boxes[1:]):
        arrow((left[0] + left[2] + 0.5, rate_y + rate_height / 2), (right[0] - 0.5, rate_y + rate_height / 2))

    # split from the microphone: a trunk down the left side feeding both rows
    trunk_x = 1.0
    axis.plot([split_x, split_x], [59 - 0.6, 56], color=SECONDARY, linewidth=2.0)
    axis.plot([split_x, trunk_x], [56, 56], color=SECONDARY, linewidth=2.0)
    axis.plot([trunk_x, trunk_x], [56, rate_y + rate_height / 2], color=SECONDARY, linewidth=2.0, solid_capstyle="round")
    arrow((trunk_x, listening_y + listening_height / 2), (listening_boxes[0][0] - 0.6, listening_y + listening_height / 2))
    arrow((trunk_x, rate_y + rate_height / 2), (rate_boxes[0][0] - 0.6, rate_y + rate_height / 2))

    legend_patch = Patch(facecolor="#1d1a10", edgecolor=AMBER, linewidth=2.6, label="studied here")
    axis.legend(handles=[legend_patch], loc="lower right", bbox_to_anchor=(0.985, 0.005), frameon=False, fontsize=13)
    figure.savefig(FIGURES_DIRECTORY / "signal_chain.svg", bbox_inches="tight", pad_inches=0.15)
    save_figure(figure, "signal_chain",
                "Block diagram of the device's audio chain: the microphone (16,000 values per second, 24 bit) feeds a "
                "listening path (filter switch Raw / Murmur / BPM filter, volume 0–100 %, 24-bit output limit, converter and "
                "earpieces) and a heart-rate path (BPM filter always on, loudness curve at 100 values per second, last 8 s "
                "kept, repeat-pattern search once per second, beats per minute). The two amber boxes are the filters "
                "studied here.")


# ---------------------------------------------------------------- 2 recordings overview

def figure_recordings_overview(recording_facts):
    figure, axes = pyplot.subplots(5, 1, figsize=(10, 13), sharex=True)
    bin_seconds = 0.02
    for axis, name in zip(axes, RECORDING_NAMES):
        samples = full_file_full_scale(name)
        values = samples / FULL_SCALE
        bin_samples = int(bin_seconds * SAMPLE_RATE_HZ)
        bin_count = values.size // bin_samples
        reshaped = values[:bin_count * bin_samples].reshape(bin_count, bin_samples)
        times = (numpy.arange(bin_count) + 0.5) * bin_seconds
        axis.fill_between(times, reshaped.min(axis=1), reshaped.max(axis=1), color=MINT, linewidth=0, alpha=0.9)
        axis.axvspan(0, 2.0, color="#2a3133", alpha=0.7, linewidth=0)
        axis.text(1.0, 0.0, "start-up, discarded", ha="center", va="center", fontsize=9.5, color=TEXT, rotation=90)
        for level in (-1, 1):
            axis.axhline(level, color=SECONDARY, linestyle="--", linewidth=1.2)
        axis.text(2.4, 1.04, "full scale", va="bottom", ha="left", fontsize=10.5, color=SECONDARY)
        clipped = numpy.flatnonzero((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM))
        clipped = clipped[clipped >= int(2.0 * SAMPLE_RATE_HZ)]
        if clipped.size:
            axis.scatter(clipped / SAMPLE_RATE_HZ, numpy.sign(values[clipped]) * 1.0, s=9, color=RED, zorder=4, linewidths=0)
        axis.set_ylim(-1.35, 1.35)
        axis.set_yticks([-1, 0, 1])
        axis.set_ylabel("level\n(full scale)", fontsize=11.5)
        axis.set_title(f"{RECORDING_TITLES[name]} — {recording_facts[name]['clipped']} values at full scale",
                       loc="left", fontsize=13.5)
        twin = axis.twinx()
        reference = load_reference(name)
        track_times = numpy.array([entry["time_s"] for entry in reference["rate_track"]], float)
        track_bpm = numpy.array([entry["bpm"] for entry in reference["rate_track"]], float)
        twin.plot(track_times, track_bpm, color=AMBER, linewidth=2.2)
        low, high = numpy.nanmin(track_bpm), numpy.nanmax(track_bpm)
        margin = max(6.0, 0.25 * (high - low))
        twin.set_ylim(low - 3 * margin, high + margin)
        twin.set_ylabel("heart rate\n(BPM)", color=AMBER, fontsize=11.5)
        twin.tick_params(axis="y", colors=AMBER, labelcolor=AMBER, labelsize=11)
        twin.grid(False)
        twin.spines["right"].set_visible(True)
        twin.spines["right"].set_color(SPINE)
    axes[-1].set_xlim(0, 60)
    axes[-1].set_xlabel("time since start of recording (s)")
    handles = [Patch(color=MINT, label="microphone signal (smallest and largest value per 20 ms)"),
               Line2D([], [], color=RED, marker="o", linestyle="", markersize=5, label="value at full scale (overload)"),
               Line2D([], [], color=AMBER, linewidth=2.2, label="reference heart rate, beat to beat over about 2 s (right axis)")]
    figure.legend(handles=handles, loc="lower center", ncol=1, frameon=False, bbox_to_anchor=(0.5, -0.045), fontsize=12)
    figure.suptitle("The five recordings: waveform, overload and heart rate", x=0.02, ha="left", fontsize=16)
    figure.tight_layout(rect=(0, 0.02, 1, 0.98))
    counts = ", ".join(f"{RECORDING_SHORT[name]} {recording_facts[name]['clipped']}" for name in RECORDING_NAMES)
    ranges = ", ".join(f"{RECORDING_SHORT[name]} {recording_facts[name]['rate_low']:.0f}–{recording_facts[name]['rate_high']:.0f}"
                       for name in RECORDING_NAMES)
    save_figure(figure, "recordings_overview",
                f"Each panel shows one 60 s recording as the smallest and largest microphone value per 20 ms in units of full "
                f"scale (dashed lines at ±1); the first 2 s (start-up) are discarded from all analysis, red dots mark values "
                f"at full scale and the amber line is the reference heart rate, once per second the mean of the beat-to-beat "
                f"intervals that overlap the 2 s around that second (right axis). "
                f"Values at full scale after the start-up: {counts}. Heart rate range over the 8 s reference windows (BPM): {ranges}.")


# ---------------------------------------------------------------- 3 beat close-up

def heart_sound_envelope(name):
    """Zero-phase 25-400 Hz envelope, smoothed with a zero-phase 20 Hz low-pass."""
    values = recording_full_scale(name)
    sections = signal.butter(2, [25, 400], "bandpass", fs=SAMPLE_RATE_HZ, output="sos")
    envelope = numpy.abs(signal.hilbert(signal.sosfiltfilt(sections, values)))
    return signal.sosfiltfilt(signal.butter(2, 20, fs=SAMPLE_RATE_HZ, output="sos"), envelope)


def recording_index(time_s):
    return int(round((time_s - 2.0) * SAMPLE_RATE_HZ))


def heart_sound_positions(name, start_s, duration_s):
    """First reference beat mark in the excerpt (first heart sound) and the second heart sound after it: the largest
    envelope peak strictly between 0.20 and 0.55 of the interval to the next beat mark, kept only if it is at least
    3 times the median envelope in the 0.6-0.9 part of the cycle. Returns (first_s, second_s or None, ratio or None)."""
    beats = numpy.array(load_reference(name)["beat_times_s"])
    inside = numpy.flatnonzero((beats > start_s + 0.15) & (beats < start_s + duration_s - 0.6))
    first = float(beats[inside[0]])
    interval = float(beats[inside[0] + 1]) - first
    envelope = heart_sound_envelope(name)
    search_start = recording_index(first + 0.20 * interval) + 1
    search = envelope[search_start:recording_index(first + 0.55 * interval)]
    background = numpy.median(envelope[recording_index(first + 0.6 * interval):recording_index(first + 0.9 * interval)])
    peaks, _ = signal.find_peaks(search)
    if not peaks.size:
        return first, None, None
    peak = int(peaks[numpy.argmax(search[peaks])])
    ratio = float(search[peak] / background)
    if ratio < 3.0:
        return first, None, ratio
    return first, 2.0 + (search_start + peak) / SAMPLE_RATE_HZ, ratio


def beats_with_full_scale(name):
    """Count of reference beats with at least one full-scale sample (each full-scale sample after the start-up is
    assigned to the nearest reference beat mark), the beat count, and the time of the last full-scale sample."""
    samples = load_recording(name)
    beats = numpy.array(load_reference(name)["beat_times_s"])
    clipped_times = 2.0 + numpy.flatnonzero((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM)) / SAMPLE_RATE_HZ
    following = numpy.clip(numpy.searchsorted(beats, clipped_times), 1, beats.size - 1)
    nearest = numpy.where(clipped_times - beats[following - 1] <= beats[following] - clipped_times, following - 1, following)
    return numpy.unique(nearest).size, beats.size, float(clipped_times.max())


def figure_beat_closeup():
    figure, axes = pyplot.subplots(1, 2, figsize=(10.5, 4.8), sharey=True)
    excerpts = [("rest-2", 20.0, "Resting 2 (no overload)"), ("elevated-2", 20.0, "After exercise 2 (overload)")]
    facts = []
    lower_counts = []
    for axis, (name, start_s, title) in zip(axes, excerpts):
        values = recording_full_scale(name)
        start_index = int(round((start_s - 2.0) * SAMPLE_RATE_HZ))
        stop_index = start_index + int(2.5 * SAMPLE_RATE_HZ)
        excerpt = values[start_index:stop_index]
        times = numpy.arange(excerpt.size) / SAMPLE_RATE_HZ
        axis.plot(times, excerpt, color=MINT, linewidth=0.7)
        for level in (-1, 1):
            axis.axhline(level, color=SECONDARY, linestyle="--", linewidth=1.2)
        clipped = numpy.flatnonzero(numpy.abs(excerpt) >= SAMPLE_MAXIMUM / FULL_SCALE)
        if clipped.size:
            axis.scatter(times[clipped], numpy.sign(excerpt[clipped]), s=6, color=RED, zorder=4, linewidths=0)
        s1_time, s2_time, s2_ratio = heart_sound_positions(name, start_s, 2.5)
        labels = [(s1_time, "first heart sound", -0.05, 1.36, "right")]
        if s2_time is not None:
            labels.append((s2_time, "second heart sound", 0.05, 1.66, "left"))
        for time_s, label, offset_s, height, alignment in labels:
            axis.annotate(label, xy=(time_s - start_s, 1.08), xytext=(time_s - start_s + offset_s, height), ha=alignment,
                          va="bottom", fontsize=11.5, color=AMBER,
                          arrowprops=dict(arrowstyle="-|>", color=AMBER, linewidth=1.5, shrinkA=2, shrinkB=0))
        axis.set_title(title, loc="left")
        axis.set_xlim(0, 2.5)
        axis.set_xlabel(f"time (s) from {start_s:.0f} s")
        facts.append((name, int(clipped.size), float(numpy.abs(excerpt).max()), s1_time, s2_time, s2_ratio))
        lower_counts.append(int(numpy.count_nonzero(excerpt[clipped] < 0)))
    axes[0].set_ylim(-1.3, 1.9)
    axes[0].set_yticks([-1, -0.5, 0, 0.5, 1])
    axes[0].set_ylabel("level (full scale)")
    axes[1].text(2.47, -1.12, "dashed: full scale   red: value cut off at full scale", ha="right", va="top", fontsize=10.5, color=SECONDARY)
    figure.suptitle("Heart sounds up close: a normal beat and an overloaded beat", x=0.02, ha="left")
    figure.tight_layout()
    rest, overload = facts
    overload_lower = lower_counts[1]

    def labelled(fact, place):
        _, _, _, s1_time, s2_time, s2_ratio = fact
        if s2_time is None:
            return (f"{place}: first heart sound at {s1_time:.3f} s; no second heart sound labelled (no envelope peak "
                    f"at least 3 times the background)")
        return (f"{place}: first heart sound at {s1_time:.3f} s, second heart sound at {s2_time:.3f} s "
                f"({1000 * (s2_time - s1_time):.0f} ms later, {s2_ratio:.1f} times the background)")

    full_scale_beats = {name: beats_with_full_scale(name) for name in ("elevated-2", "elevated-3")}
    save_figure(figure, "beat_closeup",
                f"Raw microphone signal in units of full scale over 2.5 s: left Resting 2 from 20 s, right After exercise 2 "
                f"from 20 s. The first heart sound is the reference beat mark; the second heart sound is the largest peak of "
                f"a zero-phase 25–400 Hz envelope strictly between 0.20 and 0.55 of the interval to the next beat mark, "
                f"labelled only if it is at least 3 times the median envelope in the 0.6–0.9 part of the cycle. "
                f"{labelled(rest, 'Resting 2')}; {labelled(overload, 'After exercise 2')} (times from the start of the file). "
                f"The resting excerpt peaks at {rest[2]:.2f} of full scale with {rest[1]} values at full scale; the "
                f"overloaded excerpt has {overload[1]} values cut off at full scale ({overload_lower} of them at the lower limit −1.0). "
                f"Beats with at least one value at "
                f"full scale (each full-scale value assigned to the nearest reference beat): After exercise 2 "
                f"{full_scale_beats['elevated-2'][0]} of {full_scale_beats['elevated-2'][1]} beats, After exercise 3 "
                f"{full_scale_beats['elevated-3'][0]} of {full_scale_beats['elevated-3'][1]} beats; the last full-scale "
                f"value in After exercise 3 is at {full_scale_beats['elevated-3'][2]:.3f} s.")


# ---------------------------------------------------------------- 4 spectrum

def figure_where_the_energy_is(recording_facts):
    figure, axis = pyplot.subplots(figsize=(10, 5.8))
    densities = []
    for colour, name in zip(SERIES_COLOURS, RECORDING_NAMES):
        frequencies, density = signal.welch(recording_full_scale(name), fs=SAMPLE_RATE_HZ, nperseg=WELCH_SEGMENT_SAMPLES)
        densities.append(density)
        keep = (frequencies >= 5) & (frequencies <= 8000)
        axis.plot(frequencies[keep], 10 * numpy.log10(density[keep]), color=colour, linewidth=1.0, alpha=0.75,
                  label=RECORDING_SHORT[name])
    mean_density = numpy.mean(densities, axis=0)
    keep = (frequencies >= 5) & (frequencies <= 8000)
    axis.plot(frequencies[keep], 10 * numpy.log10(mean_density[keep]), color=TEXT, linewidth=3.0, label="mean of the five")
    hertz_axis(axis, 5, 8000)
    axis.axvspan(5, 20, color="#2a3133", alpha=0.75, linewidth=0, zorder=0)
    low_y = 10 * numpy.log10(mean_density[keep]).min()
    high_y = 10 * numpy.log10(numpy.max(densities, axis=0)[keep]).max()
    axis.set_ylim(low_y - 5, high_y + 18)
    axis.text(10, high_y + 14, "below 20 Hz", ha="center", va="top", fontsize=11.5, color=TEXT)
    for edge in (25, 40, 150, 800):
        axis.axvline(edge, color=AMBER, linestyle=":", linewidth=1.6)
        label_y = high_y + 7 if edge == 40 else high_y + 14
        axis.text(edge * 1.04, label_y, hertz_label(edge), color=AMBER, fontsize=11, va="top", ha="left")
    shares = [recording_facts[name]["below_20_percent"] for name in RECORDING_NAMES]
    axis.text(0.98, 0.70, f"energy below 20 Hz:\n{min(shares):.0f}–{max(shares):.0f} % of the total\n(range over the recordings)",
              transform=axis.transAxes, ha="right", va="top", fontsize=12.5, color=TEXT,
              bbox=dict(boxstyle="round,pad=0.4", facecolor=BOX_FACE, edgecolor=SPINE))
    axis.set_xlabel("frequency")
    axis.set_ylabel("level (dB relative to full scale per Hz)")
    axis.legend(loc="upper center", ncol=3, frameon=False, fontsize=11.5, bbox_to_anchor=(0.5, -0.16))
    axis.set_title("Where the energy of the heart sounds is: averaged spectrum", loc="left", fontsize=15)
    figure.tight_layout()
    above_150 = mean_density[frequencies > 150].sum() / mean_density[frequencies >= 20].sum()
    save_figure(figure, "where_the_energy_is",
                f"Averaged power spectrum (Welch, {WELCH_SEGMENT_SAMPLES}-sample Hann segments, {SAMPLE_RATE_HZ / WELCH_SEGMENT_SAMPLES:.2f} Hz "
                f"resolution) of each raw recording after the start-up (thin lines) and their mean (thick), in dB relative "
                f"to full scale per Hz, 5 Hz–8 kHz; dotted lines mark the design band edges 25, 40, 150 and 800 Hz. "
                f"Energy below 20 Hz: {min(shares):.1f}–{max(shares):.1f} % of the total per recording; of the "
                f"energy above 20 Hz, {100 * above_150:.1f} % lies above 150 Hz (mean spectrum).")


# ---------------------------------------------------------------- 5 BPM tracks

def figure_bpm_tracks():
    figure, axes = pyplot.subplots(5, 1, figsize=(10, 14.5), sharex=True)
    series = [("No filter (Raw)", SPEC_RAW, FINAL_ESTIMATOR, RED, "-", 1.8),
              ("25–150 Hz (design candidate)", SPEC_DESIGN_BPM, FINAL_ESTIMATOR, BLUE, "-", 1.8),
              ("40–150 Hz (recommended)", SPEC_RECOMMENDED, FINAL_ESTIMATOR, MINT, "-", 2.4),
              ("25–150 Hz with the first-draft counting method", SPEC_DESIGN_BPM, FIRST_DRAFT_ESTIMATOR, AMBER, ":", 1.6)]
    worst = {}
    for axis, name in zip(axes, RECORDING_NAMES):
        end_times, reference_bpm, reliable = window_reference(name)
        axis.plot(end_times, reference_bpm, color="#d8dede", linewidth=4.0, alpha=0.55, zorder=1)
        axis.scatter(end_times[~reliable], reference_bpm[~reliable], s=38, facecolors="none", edgecolors=TEXT,
                     linewidths=1.4, zorder=5)
        lows, highs = [numpy.nanmin(reference_bpm)], [numpy.nanmax(reference_bpm)]
        for label, spec, configuration, colour, style, width in series:
            rows = bpm_estimates(spec, configuration)[name]
            times = numpy.array([row[0] for row in rows], float)
            estimates = numpy.array([row[1] for row in rows], float)
            axis.plot(times, estimates, color=colour, linestyle=style, linewidth=width, zorder=3)
            lows.append(numpy.nanmin(estimates))
            highs.append(numpy.nanmax(estimates))
            lookup = dict(zip(end_times, reference_bpm))
            errors = [abs(estimate - lookup[time]) for time, estimate in zip(times, estimates) if time in lookup]
            worst[(name, label)] = max(errors)
        span = max(highs) - min(lows)
        axis.set_ylim(min(lows) - 0.08 * span - 2, max(highs) + 0.08 * span + 2)
        axis.set_ylabel("BPM")
        axis.set_title(RECORDING_TITLES[name], loc="left", fontsize=13.5)
    axes[-1].set_xlim(9, 61)
    axes[-1].set_xlabel("end of the 8 s window (s since start of recording)")
    handles = [Line2D([], [], color="#d8dede", alpha=0.55, linewidth=4, label="reference heart rate"),
               Line2D([], [], color=TEXT, marker="o", markerfacecolor="none", linestyle="", label="window not clean (reference)")]
    handles += [Line2D([], [], color=colour, linestyle=style, linewidth=width, label=label + ("" if configuration is FIRST_DRAFT_ESTIMATOR else ", final counting method"))
                for label, _, configuration, colour, style, width in series]
    figure.legend(handles=handles, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.005), fontsize=12)
    figure.suptitle("Simulated device estimate of the heart rate compared with the reference", x=0.02, ha="left")
    figure.tight_layout(rect=(0, 0.06, 1, 0.985))
    raw_worst = max(worst[(name, series[0][0])] for name in RECORDING_NAMES)
    raw_worst_name = max(RECORDING_NAMES, key=lambda name: worst[(name, series[0][0])])
    recommended_worst = max(worst[(name, series[2][0])] for name in RECORDING_NAMES)
    draft_worst = max(worst[(name, series[3][0])] for name in RECORDING_NAMES)
    draft_worst_name = max(RECORDING_NAMES, key=lambda name: worst[(name, series[3][0])])
    save_figure(figure, "bpm_tracks",
                f"Per recording: reference heart rate per 8 s window (thick grey, hollow circles where the reference marks the "
                f"window as not clean) and the simulated device estimate per window, plotted at the window's end time, for no filter, "
                f"25–150 Hz and 40–150 Hz (final counting method) and 25–150 Hz with the first-draft counting method (dotted). "
                f"Largest single error: no filter {raw_worst:.1f} BPM ({RECORDING_SHORT[raw_worst_name]}), 40–150 Hz "
                f"{recommended_worst:.1f} BPM, 25–150 Hz with the first-draft counting method {draft_worst:.1f} BPM ({RECORDING_SHORT[draft_worst_name]}).")


# ---------------------------------------------------------------- 6 high-pass effect

def edge_label(value):
    return "none" if value is None else f"{value:g} Hz"


def figure_bpm_highpass_effect():
    highpass_edges = [None, 10, 15, 20, 25, 30, 40, 50, 60, 80]
    lowpass_edges = [60, 80, 100, 120, 150, 200, 250, 300, 400, 600, 800, None]
    left = [bpm_metrics(bpm_evaluate.specification("butterworth", edge, 150) if edge else
                        bpm_evaluate.specification("butterworth", None, 150), FINAL_ESTIMATOR) for edge in highpass_edges]
    right = [bpm_metrics(bpm_evaluate.specification("butterworth", 40, edge), FINAL_ESTIMATOR) for edge in lowpass_edges]
    maximum = max(max(row["all_mae_bpm"] for row in left + right), 1.6)
    figure, axes = pyplot.subplots(1, 2, figsize=(11, 5.6), sharey=True, gridspec_kw={"width_ratios": [10, 12]})
    for axis, rows, edges, title, xlabel in (
            (axes[0], left, highpass_edges, "Lower band edge (upper edge 150 Hz)", "lower band edge"),
            (axes[1], right, lowpass_edges, "Upper band edge (lower edge 40 Hz)", "upper band edge")):
        positions = numpy.arange(len(edges))
        axis.plot(positions, [row["all_mae_bpm"] for row in rows], color=AMBER, marker="o", linewidth=2.4, markersize=7,
                  label="all windows, including movement\nand start-up disturbances")
        axis.plot(positions, [row["reliable_mae_bpm"] for row in rows], color=MINT, marker="s", linewidth=2.4, markersize=7,
                  label="clean windows only")
        axis.set_xticks(positions)
        axis.set_xticklabels([edge_label(edge) for edge in edges], rotation=45, ha="right")
        axis.set_title(title, loc="left", fontsize=13.5)
        axis.set_xlabel(xlabel)
        axis.grid(axis="x", visible=False)
        axis.set_xlim(-0.5, len(edges) - 0.5)
    axes[0].set_ylim(0, maximum * 1.1)
    axes[0].set_ylabel("mean error (BPM)")
    axes[1].legend(loc="upper right", frameon=False)
    figure.suptitle("Heart-rate error: the lower band edge matters, the upper edge does not", x=0.02, ha="left")
    figure.tight_layout()
    none_row, row_40 = left[0], left[highpass_edges.index(40)]
    right_all = [row["all_mae_bpm"] for row in right]
    right_clean = [row["reliable_mae_bpm"] for row in right]
    best_index = int(numpy.argmin([row["all_mae_bpm"] for row in left]))
    save_figure(figure, "bpm_highpass_effect",
                f"Mean absolute heart-rate error (BPM) of the final counting method with a gentle (2nd-order) Butterworth band "
                f"filter, on clean windows only and on all 255 windows; left: lower edge varied at upper edge 150 Hz, right: "
                f"upper edge varied at lower edge 40 Hz. "
                f"All windows: {none_row['all_mae_bpm']:.2f} BPM without a lower edge, {row_40['all_mae_bpm']:.2f} BPM at 40 Hz "
                f"(lowest {left[best_index]['all_mae_bpm']:.2f} BPM at {edge_label(highpass_edges[best_index])}); clean windows "
                f"{min(row['reliable_mae_bpm'] for row in left):.2f}–{max(row['reliable_mae_bpm'] for row in left):.2f} BPM over all lower edges; "
                f"over all upper edges from 60 Hz to none the error changes by at most {max(right_all) - min(right_all):.3f} BPM (all windows, "
                f"{min(right_all):.2f} BPM) and {max(right_clean) - min(right_clean):.3f} BPM (clean, {min(right_clean):.2f} BPM).")


# ---------------------------------------------------------------- 7 estimator against filter

def figure_bpm_estimator_vs_filter():
    combinations = []
    for filter_label, spec in (("No filter", SPEC_RAW), ("25–150 Hz design", SPEC_DESIGN_BPM), ("40–150 Hz recommended", SPEC_RECOMMENDED)):
        for estimator_label, configuration in (("first-draft counting method", FIRST_DRAFT_ESTIMATOR), ("final counting method", FINAL_ESTIMATOR)):
            combinations.append((f"{filter_label},\n{estimator_label}", bpm_metrics(spec, configuration)))
    figure, axis = pyplot.subplots(figsize=(10, 6.6))
    positions = numpy.arange(len(combinations))[::-1] * 1.0
    height = 0.36
    maximum = max(metrics["all_mae_bpm"] for _, metrics in combinations)
    for offset, key, gross_key, colour, label in ((height / 2, "all_mae_bpm", "all_gross_error_count", AMBER, "all windows"),
                                                  (-height / 2, "reliable_mae_bpm", "reliable_gross_error_count", MINT, "clean windows")):
        values = [metrics[key] for _, metrics in combinations]
        axis.barh(positions + offset, values, height=height * 0.92, color=colour, label=label)
        for position, value, (_, metrics) in zip(positions, values, combinations):
            count = metrics[gross_key]
            axis.text(value + maximum * 0.012, position + offset, f"{value:.2f}  ({count} gross error{'s' if count != 1 else ''})",
                      va="center", ha="left", fontsize=11.5, color=TEXT)
    axis.set_yticks(positions)
    axis.set_yticklabels([label for label, _ in combinations], fontsize=12)
    axis.tick_params(axis="y", labelcolor=TEXT)
    axis.set_xlim(0, maximum * 1.45)
    axis.set_xlabel("mean error (BPM)")
    axis.grid(axis="y", visible=False)
    axis.legend(loc="lower right", frameon=False)
    axis.set_title("On clean windows the counting method matters at least as much as the filter\n(gross error: more than 20 % off)", loc="left", fontsize=15)
    figure.tight_layout()
    lookup = {label.replace("\n", " "): metrics for label, metrics in combinations}
    save_figure(figure, "bpm_estimator_vs_filter",
                f"Mean absolute heart-rate error (BPM) on all 255 windows and on the 226 clean windows for three filters, each with "
                f"the first-draft counting method (highest repeat peak) and the final counting method (half-rate check, smoother loudness "
                f"curve); numbers in brackets are gross errors (more than 20 % off). 25–150 Hz: "
                f"{lookup['25–150 Hz design, first-draft counting method']['all_mae_bpm']:.2f} → {lookup['25–150 Hz design, final counting method']['all_mae_bpm']:.2f} BPM on all windows, "
                f"{lookup['25–150 Hz design, first-draft counting method']['reliable_mae_bpm']:.2f} → {lookup['25–150 Hz design, final counting method']['reliable_mae_bpm']:.2f} BPM clean; "
                f"no filter: {lookup['No filter, first-draft counting method']['reliable_mae_bpm']:.2f} → {lookup['No filter, final counting method']['reliable_mae_bpm']:.2f} BPM clean, "
                f"but {lookup['No filter, final counting method']['all_mae_bpm']:.2f} BPM on all windows with the final counting method "
                f"({lookup['No filter, final counting method']['all_gross_error_count']} gross errors).")


# ---------------------------------------------------------------- 8 filter families

def figure_bpm_filter_families(grid_rows):
    final = [row for row in grid_rows if row["estimator"] == FINAL_ESTIMATOR_KEY and row["family"] in FAMILY_NAMES]
    families = list(FAMILY_NAMES)
    generator = numpy.random.default_rng(3)
    figure, axis = pyplot.subplots(figsize=(10.5, 5.8))
    facts = []
    for index, family in enumerate(families):
        rows = [row for row in final if row["family"] == family]
        for offset, key, colour in ((-0.18, "reliable_mae_bpm", MINT), (0.18, "all_mae_bpm", AMBER)):
            values = numpy.array([float(row[key]) for row in rows])
            jitter = generator.uniform(-0.12, 0.12, values.size)
            axis.scatter(index + offset + jitter, values, s=11, color=colour, alpha=0.6, linewidths=0)
            axis.plot([index + offset - 0.15, index + offset + 0.15], [numpy.median(values)] * 2, color=TEXT, linewidth=2.2)
        facts.append((FAMILY_NAMES[family], len(rows), numpy.median([float(row["reliable_mae_bpm"]) for row in rows]),
                      numpy.median([float(row["all_mae_bpm"]) for row in rows])))
    axis.set_xticks(range(len(families)))
    axis.set_xticklabels([f"{FAMILY_NAMES[family]}\n({fact[1]})" for family, fact in zip(families, facts)], fontsize=12)
    axis.tick_params(axis="x", labelcolor=TEXT)
    axis.set_ylim(0, None)
    axis.set_ylabel("mean error (BPM)")
    axis.grid(axis="x", visible=False)
    handles = [Line2D([], [], color=MINT, marker="o", linestyle="", label="clean windows"),
               Line2D([], [], color=AMBER, marker="o", linestyle="", label="all windows"),
               Line2D([], [], color=TEXT, linewidth=2.2, label="median of the design")]
    axis.legend(handles=handles, loc="upper left", frameon=False, ncol=3)
    axis.set_title("Every filter type works on clean windows; FIR filters fail on disturbed\nones (final counting method, number of filters per type in brackets)",
                   loc="left", fontsize=15)
    axis.set_ylim(0, max(float(row["all_mae_bpm"]) for row in final) * 1.12)
    figure.tight_layout()
    medians_clean = [fact[2] for fact in facts]
    medians_all = [fact[3] for fact in facts]
    by_name = {fact[0]: fact for fact in facts}
    others_all = [fact[3] for fact in facts if fact[0] != "FIR"]
    fir_rows = [row for row in final if row["family"] == "fir"]
    fir_bad = sum(float(row["all_mae_bpm"]) > 1.0 for row in fir_rows)
    save_figure(figure, "bpm_filter_families",
                f"One dot per tested filter ({len(final)} in total) with the final counting method: mean absolute heart-rate error "
                f"on clean windows and on all windows, grouped by filter type; bars are the medians. Medians per type: "
                f"{min(medians_clean):.2f}–{max(medians_clean):.2f} BPM on clean windows and {min(medians_all):.2f}–{max(medians_all):.2f} BPM "
                f"on all windows. On all windows FIR filters have a median of {by_name['FIR'][3]:.2f} BPM ({fir_bad} of {len(fir_rows)} above 1 BPM) "
                f"against {min(others_all):.2f}–{max(others_all):.2f} BPM for the other types; largest single value "
                f"{max(float(row['all_mae_bpm']) for row in final):.2f} BPM.")


# ---------------------------------------------------------------- 9 headroom

def figure_headroom_gain(listening_rows):
    figure, axis = pyplot.subplots(figsize=(10, 5.6))
    facts = {}
    for order, colour, label in ((2, MINT, "gentle (2nd order per edge)"), (4, AMBER, "steep (4th order per edge)")):
        rows = [row for row in listening_rows if row["family"] == "butterworth" and row["lowpass_hz"] == "800"
                and row["highpass_hz"] and int(row["highpass_order"]) == order and int(row["lowpass_order"]) == order
                and 10 <= float(row["highpass_hz"]) <= 150]
        rows.sort(key=lambda row: float(row["highpass_hz"]))
        edges = [float(row["highpass_hz"]) for row in rows]
        gains = [float(row["safe_gain_all_recordings_zero_saturation_db"]) for row in rows]
        axis.plot(edges, gains, color=colour, marker="o", linewidth=2.4, markersize=6, label=label)
        facts[order] = dict(zip(edges, gains))
    raw = next(row for row in listening_rows if row["identifier"] == "raw")
    raw_gain = float(raw["safe_gain_all_recordings_zero_saturation_db"])
    hertz_axis(axis, 9, 165, ticks=(10, 20, 30, 40, 50, 60, 80, 100, 150))
    low = min(min(values.values()) for values in facts.values())
    high = max(max(values.values()) for values in facts.values())
    axis.set_ylim(low - 1.5, high + 1.5)
    axis.axhspan(low - 1.5, 0, color="#2b1a18", linewidth=0, zorder=0)
    axis.axhline(raw_gain, color=TEXT, linewidth=1.8, linestyle="--")
    axis.text(9.6, raw_gain + 0.3, "No filter (Raw)", color=TEXT, fontsize=12, va="bottom")
    axis.text(9.6, low - 1.2, "filter output overloads sooner than Raw", color=RED, fontsize=12, va="bottom")
    axis.set_xlabel("lower band edge (upper edge 800 Hz)")
    axis.set_ylabel("largest safe fixed boost (dB)")
    axis.legend(loc="upper left", frameon=False)
    axis.set_title("How much louder the output can be made without overload\n(all five recordings)", loc="left", fontsize=15)
    figure.tight_layout()
    save_figure(figure, "headroom_gain",
                f"Largest fixed boost (dB) after the filter that produces no value at the 24-bit output limit on any of the five "
                f"recordings, against the lower band edge, for Butterworth filters with an upper edge at 800 Hz (device "
                f"arithmetic, volume 100 %); dashed line: no filter ({rounded_down(raw_gain, 2)} dB). Boosts rounded down. Gentle filter: {rounded_down(facts[2][40])} dB at 40 Hz, "
                f"{rounded_down(facts[2][100])} dB at 100 Hz, {rounded_down(facts[2][150])} dB at 150 Hz; steep filter: {rounded_down(facts[4][40])}, "
                f"{rounded_down(facts[4][100])} and {rounded_down(facts[4][150])} dB. Edges at or below 40 Hz give no headroom.")


# ---------------------------------------------------------------- 10 overshoot

def figure_overshoot_explained():
    settle = SAMPLE_RATE_HZ
    gentle_filter = filters.design_filter("butterworth", 40, 800, 2, 2)
    high_filter = filters.design_filter("butterworth", 100, 800, 2, 2)
    gentle_peaks = {}
    for candidate_name in RECORDING_NAMES:
        output = device_chain.apply_filter_blockwise(gentle_filter, load_recording(candidate_name))
        gentle_peaks[candidate_name] = float(numpy.abs(output[settle:]).max())
    name = max(RECORDING_NAMES, key=lambda candidate_name: gentle_peaks[candidate_name])
    samples = load_recording(name)
    raw = samples.astype(numpy.float64) / FULL_SCALE
    gentle = device_chain.apply_filter_blockwise(gentle_filter, samples).astype(numpy.float64)
    high = device_chain.apply_filter_blockwise(high_filter, samples).astype(numpy.float64)
    peak_index = settle + int(numpy.argmax(numpy.abs(gentle[settle:])))
    start = peak_index - int(0.10 * SAMPLE_RATE_HZ)
    stop = start + int(0.25 * SAMPLE_RATE_HZ)
    times = numpy.arange(stop - start) / SAMPLE_RATE_HZ * 1000
    start_time_s = 2.0 + start / SAMPLE_RATE_HZ
    figure, axes = pyplot.subplots(3, 1, figsize=(10, 10.5), sharex=True, sharey=True)
    panels = [(raw, f"(a) Microphone signal, {RECORDING_SHORT[name]}", MINT), (gentle, "(b) After the 40–800 Hz filter, before the output limit", AMBER),
              (high, "(c) After the 100–800 Hz filter", BLUE)]
    peaks = []
    for axis, (values, title, colour) in zip(axes, panels):
        excerpt = values[start:stop]
        axis.plot(times, excerpt, color=colour, linewidth=1.3)
        for level in (-1, 1):
            axis.axhline(level, color=SECONDARY, linestyle="--", linewidth=1.2)
        axis.set_title(title, loc="left", fontsize=13.5)
        axis.set_ylabel("level (full scale)")
        peaks.append(float(numpy.abs(excerpt).max()))
    axes[0].text(times[0], 1.03, "full scale", ha="left", va="bottom", fontsize=11, color=SECONDARY)
    clipped = numpy.abs(raw[start:stop]) >= SAMPLE_MAXIMUM / FULL_SCALE
    axes[0].scatter(times[clipped], numpy.sign(raw[start:stop][clipped]), s=7, color=RED, zorder=4, linewidths=0)
    excerpt = gentle[start:stop]
    over = numpy.abs(excerpt) > 1.0
    axes[1].fill_between(times, numpy.clip(excerpt, 1.0, None), 1.0, where=excerpt > 1.0, color=RED, linewidth=0, alpha=0.9)
    axes[1].fill_between(times, numpy.clip(excerpt, None, -1.0), -1.0, where=excerpt < -1.0, color=RED, linewidth=0, alpha=0.9)
    axes[1].text(0.99, 0.95, f"peak {peaks[1]:.2f} × full scale:\nthe red part is cut off by the output limit",
                 transform=axes[1].transAxes, ha="right", va="top", fontsize=12, color=RED)
    room_db = -20 * numpy.log10(peaks[2])
    axes[2].text(0.99, 0.95, f"peak {peaks[2]:.2f} × full scale:\n{room_db:.1f} dB of room left", transform=axes[2].transAxes,
                 ha="right", va="top", fontsize=12, color=BLUE)
    axes[0].text(0.99, 0.95, f"{int(clipped.sum())} values at full scale", transform=axes[0].transAxes, ha="right", va="top",
                 fontsize=12, color=RED)
    axes[1].scatter(times[over], excerpt[over], s=14, color=RED, zorder=5, linewidths=0)
    axes[0].set_ylim(-1.35, 1.9)
    axes[-1].set_xlabel(f"time (ms) from {start_time_s:.2f} s in {RECORDING_SHORT[name]}")
    figure.suptitle("Why a filter can overload the output although its input does not exceed full scale", x=0.02, ha="left")
    figure.tight_layout()
    whole_high_peak = float(numpy.abs(high[settle:]).max())
    over_count = int(numpy.count_nonzero(numpy.abs(gentle[settle:]) > SAMPLE_MAXIMUM / FULL_SCALE))
    save_figure(figure, "overshoot_explained",
                f"The same 0.25 s of {RECORDING_SHORT[name]} (from {start_time_s:.2f} s), chosen automatically as the moment where the "
                f"40–800 Hz output exceeds full scale most over all five recordings (after the first second), in units of full scale: (a) raw microphone signal, (b) after the "
                f"gentle 40–800 Hz filter in device arithmetic before the output limit, (c) after the gentle 100–800 Hz filter. "
                f"The 40–800 Hz output reaches {peaks[1]:.2f} × full scale here ({over_count} values above full scale in the whole recording) "
                f"although the input is limited to 1.0; the 100–800 Hz output peaks at {peaks[2]:.2f} × full scale here "
                f"({room_db:.1f} dB of room) and at {whole_high_peak:.2f} × full scale over the whole recording. Largest 40–800 Hz output "
                f"per recording (× full scale): " + ", ".join(f"{RECORDING_SHORT[key]} {value:.3f}" for key, value in gentle_peaks.items()) + ".")


# ---------------------------------------------------------------- 11 / 12 shortlist

def shortlist_candidates():
    document = json.loads((LISTENING_DIRECTORY / "shortlist.json").read_text())
    entries = []
    for entry in document["candidates"]:
        if entry["family"] == "raw":
            candidate = filters.raw_candidate()
        else:
            candidate = filters.design_filter(entry["family"], entry.get("highpass_hz"), entry.get("lowpass_hz"),
                                              entry.get("highpass_order", 2), entry.get("lowpass_order", 2))
        assert candidate.identifier == entry["identifier"], (candidate.identifier, entry["identifier"])
        entries.append((entry["identifier"], SHORTLIST_FIGURE_LABELS[entry["identifier"]], candidate))
    return entries


def figure_shortlist_responses():
    frequencies = numpy.geomspace(10, 7999, 1500)
    figure, axis = pyplot.subplots(figsize=(10.5, 6.2))
    facts = []
    candidates = shortlist_candidates()
    colours = SERIES_COLOURS + [TEXT]
    assert len(candidates) <= len(colours), len(candidates)
    for colour, (identifier, label, candidate) in zip(colours, candidates):
        magnitude = 20 * numpy.log10(numpy.maximum(numpy.abs(filters.frequency_response(candidate, frequencies)), 1e-12))
        style = {"raw": "--", "butterworth_hp2_25_lp2_150": "-.", "butterworth_hp2_40_lp2_150": ":"}.get(identifier, "-")
        line_width = 2.8 if style == ":" else 2.2
        axis.plot(frequencies, magnitude, color=colour, linewidth=line_width, linestyle=style, label=label)
        facts.append((label, float(numpy.interp(numpy.log(50), numpy.log(frequencies), magnitude))))
    hertz_axis(axis, 10, 8000, ticks=(10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 8000))
    axis.set_ylim(-40, 3)
    axis.set_xlabel("pitch")
    axis.set_ylabel("response (dB)")
    axis.legend(loc="upper center", ncol=2, frameon=False, fontsize=11.5, bbox_to_anchor=(0.5, -0.15))
    axis.set_title("Which pitches each candidate filter lets through", loc="left", fontsize=15)
    figure.tight_layout()
    at_50 = "; ".join(f"{label}: {value:.1f} dB" for label, value in facts if label != "No filter (Raw)")
    save_figure(figure, "shortlist_responses",
                f"Magnitude response (dB) of the nine candidate listening filters, computed from the single-precision "
                f"coefficients the device holds, 10 Hz–8 kHz; gentle = 2nd order per edge, steep = 4th order. "
                f"Response at 50 Hz, where much of the first heart sound lies: {at_50}.")


def shortlist_metrics(listening_rows):
    by_identifier = {row["identifier"]: row for row in listening_rows}
    raw = by_identifier["raw"]
    rows = []
    for identifier, label, candidate in shortlist_candidates():
        row = by_identifier.get(identifier)
        if row is None:
            continue
        rows.append({
            "label": label, "table_label": SHORTLIST_LABELS[identifier], "identifier": identifier,
            "safe_gain": float(row["safe_gain_all_recordings_zero_saturation_db"]),
            "iso226": float(row["iso226_60phon_level_at_safe_gain_db_mean"]) - float(raw["iso226_60phon_level_at_safe_gain_db_mean"]),
            "a_weighted": float(row["a_weighted_level_at_safe_gain_db_mean"]) - float(raw["a_weighted_level_at_safe_gain_db_mean"]),
            "between": float(row["between_to_heart_a_weighted_db_mean"]),
            "ringing": float(row["ringing_to_minus40db_ms"]),
            "multiplies": int(float(row["multiplies_per_sample"])),
        })
    return rows


def figure_shortlist_tradeoff(listening_rows):
    rows = shortlist_metrics(listening_rows)
    figure, axes = pyplot.subplots(1, 3, figsize=(13, 6.4), sharey=True, gridspec_kw={"width_ratios": [1, 1.25, 1]})
    positions = numpy.arange(len(rows))[::-1]

    def value_labels(axis, ys, values, span, label_format=signed):
        for y, value in zip(ys, values):
            axis.text(value + (span * 0.02 if value >= 0 else -span * 0.02), y, label_format(value), va="center",
                      ha="left" if value >= 0 else "right", fontsize=10.5, color=TEXT)

    values = [row["safe_gain"] for row in rows]
    axes[0].barh(positions, values, color=[RED if value < 0 else MINT for value in values], height=0.65)
    span = max(values) - min(values)
    value_labels(axes[0], positions, values, span, rounded_down)
    axes[0].set_xlim(min(values) - 0.35 * span, max(values) + 0.35 * span)
    axes[0].set_title("(a) Safe fixed boost\n(dB)", loc="left", fontsize=13)

    height = 0.36
    iso_values = [row["iso226"] for row in rows]
    a_values = [row["a_weighted"] for row in rows]
    axes[1].barh(positions + height / 2, iso_values, height=height * 0.92, color=AMBER, label="hearing-curve estimate")
    axes[1].barh(positions - height / 2, a_values, height=height * 0.92, color=BLUE, label="A-weighted")
    span = max(iso_values + a_values) - min(iso_values + a_values)
    value_labels(axes[1], positions + height / 2, iso_values, span)
    value_labels(axes[1], positions - height / 2, a_values, span)
    axes[1].set_xlim(min(iso_values + a_values) - 0.35 * span, max(iso_values + a_values) + 0.35 * span)
    axes[1].set_title("(b) Loudness at that boost\nvs Raw (dB)", loc="left", fontsize=13)
    figure.legend(handles=axes[1].get_legend_handles_labels()[0], labels=axes[1].get_legend_handles_labels()[1],
                  loc="lower center", bbox_to_anchor=(0.62, 0.035), ncol=2, frameon=False, fontsize=12)

    between = [row["between"] for row in rows]
    axes[2].barh(positions, between, color=VIOLET, height=0.65)
    span = max(between) - min(between)
    for y, value in zip(positions, between):
        axes[2].text(value - abs(min(between)) * 0.02, y, f"{value:.1f}", va="center", ha="right", fontsize=10.5, color=TEXT)
    axes[2].set_xlim(min(between) * 1.25, 0)
    axes[2].set_title("(c) Sound between beats\nvs heart sounds (dB, lower = cleaner)", loc="left", fontsize=13)
    for axis in axes:
        axis.axvline(0, color=SECONDARY, linewidth=1.2)
        axis.grid(axis="y", visible=False)
    axes[0].set_yticks(positions)
    axes[0].set_yticklabels([row["label"] for row in rows], fontsize=12)
    axes[0].tick_params(axis="y", labelcolor=TEXT)
    figure.suptitle("The eight candidates measured on Nico's recordings: how loud, how clean", x=0.02, ha="left")
    figure.text(0.02, 0.0, "Not shown: 40–150 Hz (recommended BPM filter), added to the listening samples later; "
                "largest safe boost +0.358 dB, loudness not measured.", ha="left", va="bottom", fontsize=10.5, color=SECONDARY)
    figure.tight_layout(rect=(0, 0.09, 1, 1))
    lookup = {row["identifier"]: row for row in rows}
    loudest = max(rows, key=lambda row: row["iso226"])
    save_figure(figure, "shortlist_tradeoff",
                f"For the eight candidates measured on Nico's recordings: (a) largest fixed boost without output overload on all five recordings "
                f"(rounded down), "
                f"(b) mean level at that boost relative to no filter, by a 60-phon equal-loudness weighting (ISO 226 proxy) and by "
                f"A-weighting, (c) A-weighted level between beats relative to the heart sounds (mean over recordings). "
                f"100–800 Hz gentle: {rounded_down(lookup['butterworth_hp2_100_lp2_800']['safe_gain'])} dB boost, "
                f"{lookup['butterworth_hp2_100_lp2_800']['iso226']:+.1f} dB (hearing curve) / {lookup['butterworth_hp2_100_lp2_800']['a_weighted']:+.1f} dB (A) vs Raw; "
                f"40–800 Hz design: {rounded_down(lookup['butterworth_hp2_40_lp2_800']['safe_gain'])} dB, {lookup['butterworth_hp2_40_lp2_800']['iso226']:+.1f} / "
                f"{lookup['butterworth_hp2_40_lp2_800']['a_weighted']:+.1f} dB; loudest by the hearing curve: {loudest['label']} ({loudest['iso226']:+.1f} dB); "
                f"between-beat ratio from {min(between):.1f} dB to {max(between):.1f} dB (Raw {lookup['raw']['between']:.1f} dB).")
    return rows


# ---------------------------------------------------------------- tables

def recording_facts_compute():
    facts = {}
    for name in RECORDING_NAMES:
        samples = load_recording(name)
        values = samples.astype(numpy.float64) / FULL_SCALE
        frequencies, density = signal.welch(values, fs=SAMPLE_RATE_HZ, nperseg=WELCH_SEGMENT_SAMPLES)
        _, reference_bpm, reliable = window_reference(name)
        facts[name] = {"clipped": int(numpy.count_nonzero((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM))),
                       "below_20_percent": 100.0 * density[frequencies < 20.0].sum() / density.sum(),
                       "rate_low": float(numpy.nanmin(reference_bpm)), "rate_high": float(numpy.nanmax(reference_bpm)),
                       "clean_windows": int(reliable.sum()), "windows": int(reliable.size)}
    return facts


def table_recordings(facts):
    states = {"rest-1": "resting", "rest-2": "resting", "elevated-1": "after exercise", "elevated-2": "after exercise, overload on many beats",
              "elevated-3": "after exercise, overload in the first half"}
    rows = [[RECORDING_SHORT[name], states[name], f"{facts[name]['rate_low']:.0f}–{facts[name]['rate_high']:.0f}",
             facts[name]["clipped"], f"{facts[name]['below_20_percent']:.1f}", facts[name]["clean_windows"]] for name in RECORDING_NAMES]
    write_table("recordings", ["Recording", "State", "Heart rate range (BPM)", "Samples at full scale", "Energy below 20 Hz (%)",
                               f"Clean windows of {facts[RECORDING_NAMES[0]]['windows']}"], rows)


def table_bpm_summary():
    header = ["Filter", "Mean error, clean windows (BPM)", "Mean error, all windows (BPM)", "Within tolerance, all windows (%)",
              "Gross errors, all windows", "Multiplications per sample"]
    results = {}
    for table_name, configuration in (("bpm_summary", FINAL_ESTIMATOR), ("bpm_summary_first_draft_estimator", FIRST_DRAFT_ESTIMATOR)):
        rows = []
        for label, spec in BPM_SUMMARY_ROWS:
            metrics = bpm_metrics(spec, configuration)
            results[(table_name, label)] = metrics
            rows.append([label, f"{metrics['reliable_mae_bpm']:.2f}", f"{metrics['all_mae_bpm']:.2f}",
                         f"{100 * metrics['all_within_tolerance_share']:.1f}", metrics["all_gross_error_count"], multiplies(spec)])
        write_table(table_name, header, rows)
    return results


def table_bpm_per_recording():
    rows = []
    for label, spec in (("40–150 Hz gentle (recommended)", SPEC_RECOMMENDED), ("25–150 Hz gentle (design candidate BPM)", SPEC_DESIGN_BPM)):
        arrays = bpm_arrays(spec, FINAL_ESTIMATOR)
        for name in RECORDING_NAMES:
            data = arrays[name]
            error = numpy.abs(data["estimate"] - data["reference"])
            rows.append([label, RECORDING_SHORT[name], f"{error[data['reliable']].mean():.2f}", f"{error.mean():.2f}",
                         f"{error.max():.2f}", int(data["reliable"].sum()), int(error.size)])
    write_table("bpm_per_recording", ["Filter", "Recording", "Mean error, clean windows (BPM)", "Mean error, all windows (BPM)",
                                      "Largest single error (BPM)", "Clean windows", "All windows"], rows)


def table_listening_shortlist(shortlist_rows):
    rows = [[row["table_label"], rounded_down(row["safe_gain"]), signed(row["iso226"]), signed(row["a_weighted"]), f"{row['between']:.1f}",
             f"{row['ringing']:.1f}", row["multiplies"]] for row in shortlist_rows]
    write_table("listening_shortlist", ["Filter", "Safe fixed boost (dB)", "Loudness vs Raw, hearing-curve estimate (dB)",
                                        "Loudness vs Raw, A-weighted (dB)", "Sound between beats vs heart sounds (dB)", "Ringing (ms)",
                                        "Multiplications per sample"], rows)


def main():
    apply_style()
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    grid_rows = read_csv(STUDY_DIRECTORY / "results" / "bpm_filter_grid.csv")
    listening_rows = read_csv(LISTENING_DIRECTORY / "metrics_summary.csv")
    facts = recording_facts_compute()
    figure_signal_chain()
    figure_recordings_overview(facts)
    figure_beat_closeup()
    figure_where_the_energy_is(facts)
    figure_bpm_tracks()
    figure_bpm_highpass_effect()
    figure_bpm_estimator_vs_filter()
    figure_bpm_filter_families(grid_rows)
    figure_headroom_gain(listening_rows)
    figure_overshoot_explained()
    figure_shortlist_responses()
    shortlist_rows = figure_shortlist_tradeoff(listening_rows)
    summary = table_bpm_summary()
    table_bpm_per_recording()
    table_listening_shortlist(shortlist_rows)
    table_recordings(facts)
    grid_lookup = {(row["identifier"], row["estimator"]): row for row in grid_rows}
    for (table_name, label), metrics in summary.items():
        spec = dict(BPM_SUMMARY_ROWS)[label]
        estimator = FINAL_ESTIMATOR_KEY if table_name == "bpm_summary" else "default"
        row = grid_lookup.get((bpm_evaluate.candidate_identifier(spec), estimator))
        if row and abs(float(row["all_mae_bpm"]) - metrics["all_mae_bpm"]) > 1e-3:
            print(f"mismatch with the grid CSV: {table_name} {label}: {row['all_mae_bpm']} vs {metrics['all_mae_bpm']:.4f}")


SELECTABLE_FIGURES = {
    "shortlist_responses": lambda: figure_shortlist_responses(),
    "shortlist_tradeoff": lambda: figure_shortlist_tradeoff(read_csv(LISTENING_DIRECTORY / "metrics_summary.csv")),
}


def regenerate_selected_figures(names):
    unknown = [name for name in names if name not in SELECTABLE_FIGURES]
    if unknown:
        raise SystemExit(f"unknown figure(s) {', '.join(unknown)}; choose from {', '.join(SELECTABLE_FIGURES)}")
    apply_style()
    for name in names:
        SELECTABLE_FIGURES[name]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Figures and tables for the report page.")
    parser.add_argument("--only", help="comma-separated figure names to regenerate: " + ", ".join(SELECTABLE_FIGURES))
    arguments = parser.parse_args()
    if arguments.only:
        regenerate_selected_figures([name.strip() for name in arguments.only.split(",") if name.strip()])
    else:
        main()
