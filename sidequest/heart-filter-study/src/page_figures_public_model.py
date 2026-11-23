"""Page figures and table for run 2: public heart-sound recordings after the capture-chain model against the own
recordings.

Usage: .venv/Scripts/python.exe -I src/page_figures_public_model.py
Writes page/figures/run2_public_vs_own_spectrum.{png,txt}, page/figures/run2_public_vs_own_waveform.{png,txt} and
page/tables/run2_how_close.md. Spectra are recomputed on a fixed smaller sample from calibration/selection.json
(the first 10 EPHNOGRAM records and the first 60 CirCor recordings); the table comes from calibration/how_close.csv.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
import numpy
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import page_figures
from hfs import chain_model, circor, ephnogram, recordings
from page_figures import BLUE, MINT, ORANGE, RED, SECONDARY

STUDY_DIRECTORY = Path(__file__).resolve().parents[1]
CALIBRATION_DIRECTORY = STUDY_DIRECTORY / "calibration"
FIGURES_DIRECTORY = STUDY_DIRECTORY / "page" / "figures"
TABLES_DIRECTORY = STUDY_DIRECTORY / "page" / "tables"
EPHNOGRAM_SAMPLE_COUNT = 10
CIRCOR_SAMPLE_COUNT = 60
EXCERPT_SECONDS = 60.0
SPECTRUM_LOWEST_HZ = 10.0
SPECTRUM_HIGHEST_HZ = 4000.0
PITCH_TICKS = (10, 20, 50, 100, 200, 500, 1000, 2000, 4000)
HEART_SOUND_RANGE_HZ = (20.0, 150.0)
WAVEFORM_SECONDS = 3.0
OWN_WAVEFORM_RECORDING = "rest-2"
OWN_WAVEFORM_START_SECONDS = 10.0
PUBLIC_WAVEFORM_START_SECONDS = 5.0
DATASET_COLOURS = {"ephnogram": BLUE, "circor": ORANGE}
DATASET_LABELS = {"ephnogram": "Public data with ECG", "circor": "Public murmur data"}
SECOND = chain_model.TARGET_SAMPLE_RATE_HZ


def selection():
    return json.loads((CALIBRATION_DIRECTORY / "selection.json").read_text(encoding="utf-8"))


def ephnogram_sample(entries):
    samples = []
    for entry in entries:
        record = ephnogram.load_record(entry["name"])
        rate = float(record.sample_rate_hz)
        first = int(entry["excerpt_start_seconds"] * rate)
        excerpt = numpy.asarray(record.pcg[first:first + int(EXCERPT_SECONDS * rate)], dtype=numpy.float64)
        samples.append({"name": entry["name"], "group": entry["group"], "samples": excerpt, "sample_rate_hz": rate})
    return samples


def circor_sample(entries):
    samples = []
    for entry in entries:
        recording = circor.load_recording(entry["name"])
        samples.append({"name": entry["name"], "group": entry["group"],
                        "samples": numpy.asarray(recording.samples, dtype=numpy.float64),
                        "sample_rate_hz": float(recording.sample_rate_hz)})
    return samples


def band_levels_db(samples_int24, band_centres_hz):
    full_scale = numpy.asarray(samples_int24, dtype=numpy.float64) / chain_model.FULL_SCALE
    powers = chain_model.band_power_spectrum(full_scale - full_scale.mean(), SECOND, band_centres_hz)
    levels = 10.0 * numpy.log10(numpy.maximum(powers, 1e-30))
    return levels - levels.max()


def median_shape(levels):
    """Median over recordings of the per-recording normalised levels, shifted again so its own maximum is 0 dB;
    returns the shift too, so a range drawn around it can be moved by the same amount."""
    median = numpy.median(levels, axis=0)
    return median - median.max(), -median.max()


def modelled(items, calibration, condition, variant, index):
    return chain_model.model_through_capture_chain(items[index]["samples"], items[index]["sample_rate_hz"],
                                                   level_condition=condition, spectrum_variant=variant,
                                                   calibration=calibration, seed=index)


def pitch_axis(axis):
    page_figures.hertz_axis(axis, SPECTRUM_LOWEST_HZ, SPECTRUM_HIGHEST_HZ, ticks=PITCH_TICKS)
    axis.set_xlabel("Pitch")


def number_list(values):
    return ", ".join(f"{value:.1f}" for value in values)


def figure_spectrum(band_centres_hz, own_levels, public_shapes, sample_sizes):
    own_median, own_shift = median_shape(own_levels)
    own_lowest = own_levels.min(axis=0) + own_shift
    own_highest = own_levels.max(axis=0) + own_shift
    figure, axis = pyplot.subplots(figsize=(11, 6.4))
    axis.axvspan(*HEART_SOUND_RANGE_HZ, color=SECONDARY, alpha=0.13, linewidth=0)
    axis.text(numpy.sqrt(HEART_SOUND_RANGE_HZ[0] * HEART_SOUND_RANGE_HZ[1]), -77,
              "most heart-sound energy\nof the own recordings", ha="center", va="bottom", fontsize=11, color=SECONDARY)
    axis.fill_between(band_centres_hz, own_lowest, own_highest, color=MINT, alpha=0.22, linewidth=0)
    axis.plot(band_centres_hz, own_median, color=MINT, linewidth=2.8)
    for dataset in ("ephnogram", "circor"):
        axis.plot(band_centres_hz, public_shapes[dataset]["microphone_only"], color=DATASET_COLOURS[dataset], linewidth=2.2)
        axis.plot(band_centres_hz, public_shapes[dataset]["matched_to_own_recordings"], color=DATASET_COLOURS[dataset],
                  linewidth=1.3, linestyle=(0, (4, 3)))
    pitch_axis(axis)
    axis.set_ylim(-80, 3)
    axis.set_ylabel("Strength relative to each signal's\nstrongest range (dB)")
    axis.set_title("The public recordings are brighter than our own", loc="left", fontsize=16)
    handles = [Line2D([], [], color=MINT, linewidth=2.8, label="Own recordings (real device chain)"),
               Patch(color=MINT, alpha=0.22, label="Own recordings, range of the five"),
               Line2D([], [], color=BLUE, linewidth=2.2, label="Public data with ECG, modelled"),
               Line2D([], [], color=ORANGE, linewidth=2.2, label="Public murmur data, modelled"),
               Line2D([], [], color=BLUE, linewidth=1.3, linestyle=(0, (4, 3)),
                      label="Public data with ECG, after matching the tone balance"),
               Line2D([], [], color=ORANGE, linewidth=1.3, linestyle=(0, (4, 3)),
                      label="Public murmur data, after matching the tone balance")]
    axis.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False, fontsize=11.5)
    caption = f"""
Run 2: long-term third-octave band levels, 10 Hz to 4 kHz, each curve relative to its own strongest band (0 dB).
Own recordings: the five recordings ({', '.join(recordings.RECORDING_NAMES)}), first 2 s discarded; each normalised
to its strongest band, median over the five, then shifted so the median's strongest band is 0 dB; the band is the
lowest to highest of the five, shifted by the same amount.
Public data: capture-chain model (src/hfs/chain_model.py, calibration/chain_model_<dataset>.json), rest level,
seed = index as in src/chain_model_calibrate.py; same normalisation, median over recordings.
Sample: the first {sample_sizes['ephnogram']} EPHNOGRAM records (60 s excerpts) and the first {sample_sizes['circor']}
CirCor recordings of calibration/selection.json (the calibration itself used 20 and 200).
Band power: Welch, Hann, 16384 samples, half overlap (chain_model.band_power_spectrum).
Shaded: {HEART_SOUND_RANGE_HZ[0]:g}-{HEART_SOUND_RANGE_HZ[1]:g} Hz (own recordings: 48 % of energy at rest per
calibration/how_close.csv; 52 % lies below 20 Hz).
EPHNOGRAM is sampled at 8 kHz, so it carries nothing above 4 kHz; CirCor at 4 kHz carries nothing above 2 kHz,
where the model adds only the own recordings' floor noise.

Band centres (Hz): {', '.join(f'{centre:.4g}' for centre in band_centres_hz)}
Own median (dB): {number_list(own_median)}
Own lowest of five (dB): {number_list(own_lowest)}
Own highest of five (dB): {number_list(own_highest)}
EPHNOGRAM modelled (dB): {number_list(public_shapes['ephnogram']['microphone_only'])}
EPHNOGRAM after matching (dB): {number_list(public_shapes['ephnogram']['matched_to_own_recordings'])}
CirCor modelled (dB): {number_list(public_shapes['circor']['microphone_only'])}
CirCor after matching (dB): {number_list(public_shapes['circor']['matched_to_own_recordings'])}
"""
    page_figures.save_figure(figure, "run2_public_vs_own_spectrum", caption)


def figure_waveform(rows):
    figure, axes = pyplot.subplots(len(rows), 1, figsize=(11, 7.2), sharex=True, sharey=True)
    for axis, (title, values, colour) in zip(axes, rows):
        time_axis = numpy.arange(len(values)) / SECOND
        axis.plot(time_axis, values / chain_model.FULL_SCALE, color=colour, linewidth=0.7)
        for limit in (-1.0, 1.0):
            axis.axhline(limit, color=RED, linewidth=0.9, linestyle=(0, (2, 2)))
        axis.set_ylim(-1.08, 1.08)
        axis.set_yticks([-1, -0.5, 0, 0.5, 1])
        axis.set_xlim(0, WAVEFORM_SECONDS)
        axis.set_ylabel("share of\nfull scale")
        axis.set_title(title, loc="left", fontsize=13.5)
    axes[-1].set_xlabel("Time (seconds)")
    axes[0].set_title("dashed red: full scale", loc="right", fontsize=10.5, color=SECONDARY)
    figure.suptitle("Three seconds at the resting level: own recording and modelled public data", x=0.01, ha="left",
                    fontsize=16)
    figure.tight_layout()
    return figure


def percent_text(value):
    if value < 0.05:
        return "below 0.1 %"
    return f"{value:.1f} %" if value < 10 else f"{value:.0f} %"


def decibel_text(value):
    return f"{value:.1f} dB"


def write_how_close_table():
    rows = {}
    with open(CALIBRATION_DIRECTORY / "how_close.csv", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[(row["measure"], row["condition"])] = row
    columns = ["own", "ephnogram microphone_only", "circor microphone_only",
               "ephnogram matched_to_own_recordings", "circor matched_to_own_recordings"]
    pooled = "beats with a sample at full scale, %, all beats pooled (the calibrated quantity)"
    lines_spec = [
        ("Heart-sound level at rest (loudness of the beats, below full scale)",
         "heart-sound level (median beat peak, 20-400 Hz), dB re full scale", "rest", decibel_text),
        ("Share of energy below 20 Hz (rest)", "energy below 20 Hz, %", "rest", percent_text),
        ("Share of energy 20-150 Hz (rest)", "energy 20-150 Hz, %", "rest", percent_text),
        ("Share of energy 150-800 Hz (rest)", "energy 150-800 Hz, %", "rest", percent_text),
        ("Share of energy above 800 Hz (rest)", "energy above 800 Hz, %", "rest", percent_text),
        ("Sound between beats relative to the heart sounds (rest; lower is quieter)",
         "floor between beats relative to heart sounds (10th / 90th percentile of 100 ms power, 20-400 Hz), dB", "rest",
         decibel_text),
        ("Share of beats reaching full scale, resting level", pooled, "rest", percent_text),
        ("Share of beats reaching full scale, overload level", pooled, "overload", percent_text),
    ]
    lines = ["| | Own recordings | Public data with ECG (modelled) | Public murmur data (modelled) "
             "| Public data with ECG, after matching | Public murmur data, after matching |",
             "| --- | --- | --- | --- | --- | --- |"]
    for label, measure, condition, formatter in lines_spec:
        row = rows[(measure, condition)]
        lines.append(f"| {label} | " + " | ".join(formatter(float(row[column])) for column in columns) + " |")
    lines += ["",
              "Source: `calibration/how_close.csv` (written by `src/chain_model_calibrate.py`; medians over 20 EPHNOGRAM "
              "and 200 CirCor recordings, own: rest-1, rest-2, elevated-1 at rest, elevated-2, elevated-3 at overload; "
              "beat shares pool all beats; the overload level of the model was set to reach the own 34 % of beats)."]
    TABLES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    path = TABLES_DIRECTORY / "run2_how_close.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"table {path.name}")


def main():
    page_figures.apply_style()
    band_centres_hz = chain_model.third_octave_centres_hz(SPECTRUM_LOWEST_HZ, SPECTRUM_HIGHEST_HZ)
    chosen = selection()
    items = {"ephnogram": ephnogram_sample(chosen["ephnogram"][:EPHNOGRAM_SAMPLE_COUNT]),
             "circor": circor_sample(chosen["circor"][:CIRCOR_SAMPLE_COUNT])}
    calibrations = {dataset: chain_model.load_calibration(dataset) for dataset in items}

    own_levels = numpy.array([band_levels_db(recordings.load_recording(name), band_centres_hz)
                              for name in recordings.RECORDING_NAMES])
    public_shapes = {}
    for dataset, dataset_items in items.items():
        public_shapes[dataset] = {}
        for variant in chain_model.SPECTRUM_VARIANTS:
            levels = numpy.array([band_levels_db(modelled(dataset_items, calibrations[dataset], "rest", variant, index),
                                                 band_centres_hz) for index in range(len(dataset_items))])
            public_shapes[dataset][variant] = median_shape(levels)[0]
        print(dataset, "spectra done")
    figure_spectrum(band_centres_hz, own_levels, public_shapes, {dataset: len(value) for dataset, value in items.items()})

    ephnogram_index = next(index for index, item in enumerate(items["ephnogram"]) if item["group"].startswith("Rest"))
    circor_index = next(index for index, item in enumerate(items["circor"]) if item["group"].startswith("Absent"))
    own = recordings.load_recording(OWN_WAVEFORM_RECORDING)
    own_first = int(OWN_WAVEFORM_START_SECONDS * SECOND)
    public_first = int(PUBLIC_WAVEFORM_START_SECONDS * SECOND)
    length = int(WAVEFORM_SECONDS * SECOND)
    ephnogram_item, circor_item = items["ephnogram"][ephnogram_index], items["circor"][circor_index]
    rows = [("Own recording, resting (real device chain)", own[own_first:own_first + length], MINT),
            (f"Public data with ECG, modelled at the resting level (adult {ephnogram_item['group'].split(':')[1].strip().replace('laying', 'lying')})",
             modelled(items["ephnogram"], calibrations["ephnogram"], "rest", "microphone_only", ephnogram_index)
             [public_first:public_first + length], BLUE),
            ("Public murmur data, modelled at the resting level (child without a murmur)",
             modelled(items["circor"], calibrations["circor"], "rest", "microphone_only", circor_index)
             [public_first:public_first + length], ORANGE)]
    figure = figure_waveform(rows)
    peaks = [float(numpy.abs(values).max() / chain_model.FULL_SCALE) for _, values, _ in rows]
    caption = f"""
Run 2: 3 s of capture-chain output at the resting level, same time and value scale, value as share of 24-bit full
scale (dashed red: the limits).
Own: {OWN_WAVEFORM_RECORDING}, {OWN_WAVEFORM_START_SECONDS + recordings.DISCARDED_SECONDS:g}-{OWN_WAVEFORM_START_SECONDS + recordings.DISCARDED_SECONDS + WAVEFORM_SECONDS:g} s from file start (raw INMP441, 16 kHz), as in calibration/figures/time_domain.png.
Public data with ECG: EPHNOGRAM {ephnogram_item['name']} ({ephnogram_item['group']}), 60 s excerpt from
{chosen['ephnogram'][ephnogram_index]['excerpt_start_seconds']:g} s, model output {PUBLIC_WAVEFORM_START_SECONDS:g}-{PUBLIC_WAVEFORM_START_SECONDS + WAVEFORM_SECONDS:g} s, microphone only, rest level, seed {ephnogram_index}.
Public murmur data: CirCor {circor_item['name']} (murmur {circor_item['group']}), model output {PUBLIC_WAVEFORM_START_SECONDS:g}-{PUBLIC_WAVEFORM_START_SECONDS + WAVEFORM_SECONDS:g} s,
microphone only, rest level, seed {circor_index}.
Largest absolute value in the shown 3 s (share of full scale): own {peaks[0]:.3f}, EPHNOGRAM {peaks[1]:.3f}, CirCor {peaks[2]:.3f}.
"""
    page_figures.save_figure(figure, "run2_public_vs_own_waveform", caption)
    write_how_close_table()


if __name__ == "__main__":
    main()
