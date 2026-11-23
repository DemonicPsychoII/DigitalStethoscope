"""Fit the capture-chain model for EPHNOGRAM and CirCor, and report how close the modelled data comes to the own
recordings. Writes calibration/chain_model_<dataset>.json, calibration/SUMMARY.md, calibration/how_close.csv and
calibration/figures/*.png.

Run: .venv/Scripts/python.exe -I src/chain_model_calibrate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import csv
import datetime
import json
import random
import time
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
import numpy
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
from scipy import signal

from hfs import chain_model, circor, ephnogram, recordings

STUDY_DIRECTORY = Path(__file__).resolve().parents[1]
CALIBRATION_DIRECTORY = STUDY_DIRECTORY / "calibration"
FIGURE_DIRECTORY = CALIBRATION_DIRECTORY / "figures"
EPHNOGRAM_REFERENCE_DIRECTORY = STUDY_DIRECTORY / "reference-public" / "ephnogram"
SAMPLING_SEED = 20261123
EPHNOGRAM_RECORD_LIMIT = 20
EPHNOGRAM_EXCERPT_SECONDS = 60.0
CIRCOR_RECORDING_COUNT = 200
CIRCOR_LOCATIONS = ("AV", "MV", "PV", "TV")
CIRCOR_MURMUR_LABELS = ("Present", "Absent", "Unknown")
ENERGY_BANDS_HZ = (("below 20 Hz", 0.0, 20.0), ("20-150 Hz", 20.0, 150.0), ("150-800 Hz", 150.0, 800.0),
                   ("above 800 Hz", 800.0, 8000.0))
BACKGROUND = "#0d1117"
TEXT = "#e6edf3"
GRID = "#30363d"
OWN_COLOUR = "#e6edf3"
EPHNOGRAM_COLOUR = "#58a6ff"
CIRCOR_COLOUR = "#f0883e"
DATASET_COLOURS = {"ephnogram": EPHNOGRAM_COLOUR, "circor": CIRCOR_COLOUR}
DATASET_TITLES = {"ephnogram": "EPHNOGRAM", "circor": "CirCor"}
VARIANT_TITLES = {"microphone_only": "microphone only", "matched_to_own_recordings": "matched to own recordings"}
CONDITION_OWN_RECORDINGS = {"rest": chain_model.REST_LEVEL_RECORDINGS, "overload": chain_model.OVERLOAD_RECORDINGS}


# Dataset samples ---------------------------------------------------------------------------------------------

def ephnogram_items(record_limit=EPHNOGRAM_RECORD_LIMIT):
    """Up to 20 records, one per subject first, spread over scenarios; a 60 s excerpt from each record's middle;
    beat times are the ECG R peaks of reference-public/ephnogram/<record>.json where that file exists."""
    available = [info for info in ephnogram.list_records() if info.available]
    with_reference = [info for info in available if (EPHNOGRAM_REFERENCE_DIRECTORY / f"{info.record_name}.json").exists()]
    pool = with_reference if len(with_reference) >= record_limit // 2 else available
    by_scenario = defaultdict(list)
    for info in sorted(pool, key=lambda info: info.record_name):
        by_scenario[info.scenario].append(info)
    chosen, used_subjects = [], set()
    for allow_repeat in (False, True):
        progress = True
        while len(chosen) < record_limit and progress:
            progress = False
            for scenario in sorted(by_scenario):
                for info in by_scenario[scenario]:
                    if info in chosen or (not allow_repeat and info.subject_id in used_subjects):
                        continue
                    chosen.append(info)
                    used_subjects.add(info.subject_id)
                    progress = True
                    break
                if len(chosen) >= record_limit:
                    break
    items = []
    for info in chosen:
        record = ephnogram.load_record(info.record_name)
        rate = float(record.sample_rate_hz)
        duration = len(record.pcg) / rate
        start_seconds = max(0.0, (duration - EPHNOGRAM_EXCERPT_SECONDS) / 2.0)
        first = int(start_seconds * rate)
        excerpt = numpy.asarray(record.pcg[first:first + int(EPHNOGRAM_EXCERPT_SECONDS * rate)], dtype=numpy.float64)
        beat_times = None
        reference_path = EPHNOGRAM_REFERENCE_DIRECTORY / f"{info.record_name}.json"
        if reference_path.exists():
            all_beats = numpy.asarray(json.loads(reference_path.read_text(encoding="utf-8"))["beat_times_s"])
            beat_times = all_beats[(all_beats >= start_seconds) & (all_beats < start_seconds + len(excerpt) / rate)] - start_seconds
        items.append({"name": info.record_name, "subject": info.subject_id, "group": info.scenario,
                      "samples": excerpt, "sample_rate_hz": rate, "beat_times_s": beat_times,
                      "excerpt_start_seconds": start_seconds})
    return items


def circor_items(recording_count=CIRCOR_RECORDING_COUNT):
    """200 recordings, fixed seed, spread evenly over murmur label (Present, Absent, Unknown) x location
    (AV, MV, PV, TV), at most one recording per patient; beat times are the starts of the S1 segments."""
    patients = {patient.patient_identifier: patient for patient in circor.list_patients()}
    strata = defaultdict(list)
    for info in circor.list_recordings():
        murmur = patients[info.patient_identifier].murmur
        if info.has_segmentation and info.location in CIRCOR_LOCATIONS and murmur in CIRCOR_MURMUR_LABELS:
            strata[(murmur, info.location)].append(info)
    generator = random.Random(SAMPLING_SEED)
    for key in sorted(strata):
        strata[key].sort(key=lambda info: info.file_stem)
        generator.shuffle(strata[key])
    chosen, used_patients = [], set()
    positions = {key: 0 for key in strata}
    while len(chosen) < recording_count and any(positions[key] < len(strata[key]) for key in strata):
        for key in sorted(strata):
            while positions[key] < len(strata[key]):
                info = strata[key][positions[key]]
                positions[key] += 1
                if info.patient_identifier not in used_patients:
                    chosen.append(info)
                    used_patients.add(info.patient_identifier)
                    break
            if len(chosen) >= recording_count:
                break
    items = []
    for info in chosen:
        recording = circor.load_recording(info.file_stem)
        segments = recording.segments
        beat_times = numpy.asarray(segments["start_seconds"][segments["state"] == circor.STATE_S1])
        items.append({"name": info.file_stem, "subject": info.patient_identifier,
                      "group": f"{patients[info.patient_identifier].murmur} {info.location}",
                      "samples": numpy.asarray(recording.samples, dtype=numpy.float64),
                      "sample_rate_hz": float(recording.sample_rate_hz), "beat_times_s": beat_times})
    return items


# Measures ----------------------------------------------------------------------------------------------------

def welch_spectrum(samples_full_scale):
    return signal.welch(samples_full_scale, fs=chain_model.TARGET_SAMPLE_RATE_HZ, nperseg=chain_model.WELCH_SEGMENT_SAMPLES)


def quiet_to_loud_db(samples_full_scale):
    """10th over 90th percentile of the 100 ms frame power of the 20-400 Hz band: floor between beats relative
    to the heart sounds."""
    band = chain_model.heart_sound_band(samples_full_scale)
    frame = chain_model.TARGET_SAMPLE_RATE_HZ // 10
    powers = numpy.mean(band[:len(band) // frame * frame].reshape(-1, frame) ** 2, axis=1)
    return float(10 * numpy.log10(numpy.percentile(powers, 10) / numpy.percentile(powers, 90)))


def measure(samples_int24, beat_times_s, time_offset_s=0.0):
    values = numpy.asarray(samples_int24)
    full_scale = values.astype(numpy.float64) / chain_model.FULL_SCALE
    centred = full_scale - full_scale.mean()
    frequencies, density = welch_spectrum(centred)
    total = density.sum()
    rms = float(numpy.sqrt(numpy.mean(centred ** 2)))
    result = {
        "band_shape_db": chain_model.band_shape_db(centred, chain_model.TARGET_SAMPLE_RATE_HZ),
        "welch_frequencies_hz": frequencies,
        "welch_density": density,
        "rms_dbfs": 20 * numpy.log10(rms),
        "crest_factor_db": 20 * numpy.log10(numpy.abs(centred).max() / rms),
        "share_of_samples_at_full_scale_percent": 100 * chain_model.share_of_samples_at_full_scale(values),
        "floor_relative_to_heart_sounds_db": quiet_to_loud_db(centred),
    }
    for label, low, high in ENERGY_BANDS_HZ:
        result[f"energy {label} percent"] = 100 * float(density[(frequencies >= low) & (frequencies < high)].sum() / total)
    if beat_times_s is not None and len(beat_times_s) >= 2:
        result["heart_sound_level_dbfs"] = 20 * numpy.log10(chain_model.heart_sound_level(
            centred, beat_times_s, time_offset_s, "median_beat_peak"))
        clipped, beats = chain_model.share_of_beats_at_full_scale(values, beat_times_s, time_offset_s=time_offset_s)
        result["share_of_beats_at_full_scale_percent"] = 100 * clipped / beats if beats else numpy.nan
        result["beats_at_full_scale"], result["beat_count"] = clipped, beats
    else:
        result["heart_sound_level_dbfs"] = 20 * numpy.log10(chain_model.heart_sound_level(
            centred, level_measure="envelope_95th_percentile"))
        result["share_of_beats_at_full_scale_percent"] = numpy.nan
        result["beats_at_full_scale"], result["beat_count"] = 0, 0
    return result


SCALAR_MEASURES = (
    ("heart_sound_level_dbfs", "heart-sound level (median beat peak, 20-400 Hz), dB re full scale"),
    ("rms_dbfs", "overall level (RMS of the whole signal), dB re full scale"),
    ("crest_factor_db", "crest factor (peak over RMS), dB"),
    ("energy below 20 Hz percent", "energy below 20 Hz, %"),
    ("energy 20-150 Hz percent", "energy 20-150 Hz, %"),
    ("energy 150-800 Hz percent", "energy 150-800 Hz, %"),
    ("energy above 800 Hz percent", "energy above 800 Hz, %"),
    ("share_of_samples_at_full_scale_percent", "samples at full scale, %"),
    ("share_of_beats_at_full_scale_percent", "beats with a sample at full scale, %, median over recordings"),
    ("pooled_share_of_beats_at_full_scale_percent", "beats with a sample at full scale, %, all beats pooled (the calibrated quantity)"),
    ("floor_relative_to_heart_sounds_db", "floor between beats relative to heart sounds (10th / 90th percentile of 100 ms power, 20-400 Hz), dB"),
)


def median_of(measures, key):
    if key == "pooled_share_of_beats_at_full_scale_percent":
        beats = sum(entry["beat_count"] for entry in measures)
        return 100 * sum(entry["beats_at_full_scale"] for entry in measures) / beats if beats else float("nan")
    values = numpy.array([entry[key] for entry in measures], dtype=float)
    values = values[numpy.isfinite(values)]
    return float(numpy.median(values)) if len(values) else float("nan")


# Figures -----------------------------------------------------------------------------------------------------

def style_axes(axes):
    axes.set_facecolor(BACKGROUND)
    axes.tick_params(colors=TEXT, which="both")
    for spine in axes.spines.values():
        spine.set_color(GRID)
    axes.grid(True, color=GRID, linewidth=0.6)
    axes.xaxis.label.set_color(TEXT)
    axes.yaxis.label.set_color(TEXT)
    axes.title.set_color(TEXT)


def frequency_label(value, _position=None):
    return f"{value / 1000:g} kHz" if value >= 1000 else f"{value:g} Hz"


NOMINAL_THIRD_OCTAVE_HZ = (20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000)


def nominal_band_label(centre_hz):
    """IEC 61260 nominal name of a base-10 third-octave band."""
    return frequency_label(min(NOMINAL_THIRD_OCTAVE_HZ, key=lambda nominal: abs(numpy.log(nominal / centre_hz))))


def frequency_axis(axes, lowest_hz, highest_hz):
    axes.set_xscale("log")
    ticks = [tick for tick in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000) if lowest_hz <= tick <= highest_hz]
    axes.xaxis.set_major_locator(FixedLocator(ticks))
    axes.xaxis.set_major_formatter(FuncFormatter(frequency_label))
    axes.xaxis.set_minor_locator(NullLocator())
    axes.set_xlim(lowest_hz, highest_hz)
    axes.set_xlabel("Frequency")


def new_figure(rows, columns, width, height):
    figure, axes = pyplot.subplots(rows, columns, figsize=(width, height), squeeze=False)
    figure.patch.set_facecolor(BACKGROUND)
    for single in axes.flat:
        style_axes(single)
    return figure, axes


def legend(axes):
    handle = axes.legend(facecolor=BACKGROUND, edgecolor=GRID, fontsize=8)
    for text in handle.get_texts():
        text.set_color(TEXT)


def save(figure, name):
    FIGURE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(FIGURE_DIRECTORY / name, dpi=130, facecolor=BACKGROUND)
    pyplot.close(figure)


def density_db(density):
    return 10 * numpy.log10(numpy.maximum(density, 1e-20))


def figure_long_term_spectra(own_measures, modelled):
    figure, axes = new_figure(2, 2, 13, 8.5)
    for row, condition in enumerate(chain_model.LEVEL_CONDITIONS):
        for column, variant in enumerate(chain_model.SPECTRUM_VARIANTS):
            panel = axes[row, column]
            for name, entry in own_measures.items():
                panel.plot(entry["welch_frequencies_hz"], density_db(entry["welch_density"]), color=OWN_COLOUR,
                           linewidth=0.5, alpha=0.35)
            group = [own_measures[name] for name in CONDITION_OWN_RECORDINGS[condition]]
            frequencies = group[0]["welch_frequencies_hz"]
            panel.plot(frequencies, density_db(numpy.median([entry["welch_density"] for entry in group], axis=0)),
                       color=OWN_COLOUR, linewidth=2.0, label=f"own, median of {', '.join(CONDITION_OWN_RECORDINGS[condition])}")
            for dataset, results in modelled.items():
                entries = results[(variant, condition)]
                panel.plot(frequencies, density_db(numpy.median([entry["welch_density"] for entry in entries], axis=0)),
                           color=DATASET_COLOURS[dataset], linewidth=1.6,
                           label=f"modelled {DATASET_TITLES[dataset]}, median of {len(entries)}")
            frequency_axis(panel, 5, 8000)
            panel.set_ylim(-150, -20)
            panel.set_ylabel("Power density (dB re full scale squared per Hz)")
            panel.set_title(f"{VARIANT_TITLES[variant]}, level condition {condition}")
            legend(panel)
    figure.suptitle("Long-term spectra (Welch, 1 s segments): own recordings (thin: each) against modelled public data",
                    color=TEXT)
    save(figure, "long_term_spectra.png")


def figure_band_difference(own_median_shape, modelled):
    figure, axes = new_figure(1, 1, 10, 5)
    panel = axes[0, 0]
    centres = chain_model.match_band_centres_hz()
    for dataset, results in modelled.items():
        for variant, style in (("microphone_only", "--"), ("matched_to_own_recordings", "-")):
            shapes = numpy.median([entry["band_shape_db"] for entry in results[(variant, "rest")]], axis=0)
            panel.plot(centres, shapes - own_median_shape, style, marker="o", markersize=3,
                       color=DATASET_COLOURS[dataset], label=f"{DATASET_TITLES[dataset]}, {VARIANT_TITLES[variant]}")
    panel.axhline(0, color=TEXT, linewidth=0.8)
    frequency_axis(panel, 18, 1100)
    panel.set_ylabel("Band level difference, modelled minus own (dB)")
    panel.set_title("Spectral shape, third-octave bands 20 Hz-1 kHz (each relative to its band sum), rest condition")
    legend(panel)
    save(figure, "band_difference.png")


def figure_time_domain(own_segments, modelled_segments):
    figure, axes = new_figure(3, 2, 13, 8)
    for column, condition in enumerate(chain_model.LEVEL_CONDITIONS):
        rows = [own_segments[condition]] + [modelled_segments[dataset][condition] for dataset in ("ephnogram", "circor")]
        colours = [OWN_COLOUR, EPHNOGRAM_COLOUR, CIRCOR_COLOUR]
        for row, ((title, values), colour) in enumerate(zip(rows, colours)):
            panel = axes[row, column]
            time_axis = numpy.arange(len(values)) / chain_model.TARGET_SAMPLE_RATE_HZ
            panel.plot(time_axis, values / chain_model.FULL_SCALE, color=colour, linewidth=0.6)
            for limit in (-1.0, 1.0):
                panel.axhline(limit, color="#f85149", linewidth=0.8, linestyle=":")
            panel.set_ylim(-1.1, 1.1)
            panel.set_xlim(0, time_axis[-1])
            panel.set_ylabel("Full scale")
            panel.set_title(title, fontsize=9)
            if row == 2:
                panel.set_xlabel("Time (s)")
    figure.suptitle("3 s of capture-chain output: own recording against modelled public data (microphone only); dotted: 24-bit limits",
                    color=TEXT)
    save(figure, "time_domain.png")


# Main --------------------------------------------------------------------------------------------------------

def write_summary(calibrations, own_measures, modelled, item_counts, table_rows, band_rows, elapsed_seconds):
    lines = ["# Capture-chain model: calibration and how close it comes to the own recordings", "",
             f"Generated {datetime.datetime.now().astimezone().isoformat(timespec='minutes')} by `src/chain_model_calibrate.py`"
             f" ({elapsed_seconds:.0f} s). Model: `src/hfs/chain_model.py`. Own recordings: Nico, 23 Nov 2026, capture firmware,"
             " raw INMP441 at 16 kHz, first 2 s discarded (`src/hfs/recordings.py`); reference beat times `reference/<name>.json`.", ""]
    lines += ["## Calibration", "",
              "| Dataset | Recordings | Source rate | Level measure | Overload share by | Gain rest, microphone only | Gain overload, microphone only | Gain rest, matched | Gain overload, matched |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for dataset, calibration in calibrations.items():
        gains = calibration.gain
        lines.append(f"| {DATASET_TITLES[dataset]} | {calibration.recording_count} | "
                     f"{', '.join(f'{rate:g} Hz' for rate in calibration.source_sample_rates_hz)} | {calibration.level_measure} | "
                     f"{calibration.overload_share_method} | {gains['microphone_only']['rest']:.4g} | {gains['microphone_only']['overload']:.4g} | "
                     f"{gains['matched_to_own_recordings']['rest']:.4g} | {gains['matched_to_own_recordings']['overload']:.4g} |")
    targets = next(iter(calibrations.values())).targets
    lines += ["", "Gains are in the unit of the dataset's samples to full scale (EPHNOGRAM in mV as stored, CirCor in WAV"
              " full scale). The overload gain divided by the rest gain says how much louder the public data must be played"
              " into the model to clip as often as elevated-2 and elevated-3.", "",
              f"Targets (own recordings): rest level {20 * numpy.log10(targets['rest_level_median_beat_peak']):.1f} dB re full scale"
              f" (median per-beat peak of the 20-400 Hz band; median over rest-1, rest-2, elevated-1); overload: "
              f"{int(targets['overload_beats_at_limit'])} of {int(targets['overload_beat_count'])} beats"
              f" ({100 * targets['overload_beat_share']:.1f} %) in elevated-2 and elevated-3 have a sample at the 24-bit limit;"
              f" share of samples at the limit {100 * targets['overload_sample_share']:.3f} %.", ""]
    lines += ["Spectrum correction of the matched variant (dB, third-octave centre frequency):", "",
              "| Band | " + " | ".join(DATASET_TITLES[dataset] for dataset in calibrations) + " |",
              "| --- | " + " | ".join("---" for _ in calibrations) + " |"]
    centres = chain_model.match_band_centres_hz()
    for index, centre in enumerate(centres):
        lines.append(f"| {nominal_band_label(centre)} | "
                     + " | ".join(f"{calibrations[dataset].spectrum_correction_db[index]:+.1f}" for dataset in calibrations) + " |")
    lines += ["", "## How close (medians over recordings)", "",
              "Own: rest condition compared with rest-1, rest-2, elevated-1; overload with elevated-2, elevated-3.", "",
              "| Measure | Condition | Own | " + " | ".join(
                  f"{DATASET_TITLES[dataset]} {VARIANT_TITLES[variant]}" for dataset in modelled for variant in chain_model.SPECTRUM_VARIANTS) + " |",
              "| --- | --- | --- | " + " | ".join("---" for _ in modelled for _ in chain_model.SPECTRUM_VARIANTS) + " |"]
    for row in table_rows:
        lines.append(f"| {row['measure']} | {row['condition']} | {row['own']:.2f} | "
                     + " | ".join(f"{row[f'{dataset} {variant}']:.2f}" for dataset in modelled for variant in chain_model.SPECTRUM_VARIANTS) + " |")
    lines += ["", "Spectral shape per third-octave band, modelled minus own median (dB, rest condition; each spectrum relative to"
              " its 20 Hz-1 kHz band sum, so overall level does not enter):", "",
              "| Band | " + " | ".join(f"{DATASET_TITLES[dataset]} before matching | {DATASET_TITLES[dataset]} after matching" for dataset in modelled) + " |",
              "| --- | " + " | ".join("--- | ---" for _ in modelled) + " |"]
    for row in band_rows:
        lines.append(f"| {row['band']} | " + " | ".join(f"{row[f'{dataset} before']:+.1f} | {row[f'{dataset} after']:+.1f}" for dataset in modelled) + " |")
    lines += ["", "Figures: `figures/long_term_spectra.png`, `figures/band_difference.png`, `figures/time_domain.png`.", ""]
    path = CALIBRATION_DIRECTORY / "SUMMARY.md"
    path.write_text("\n".join(lines) + "\n" + METHOD_TEXT, encoding="utf-8")
    return path


METHOD_TEXT = """
## Modelling choices and their sources

- Resampling: `scipy.signal.resample_poly` (polyphase, Kaiser window beta 5.0, cutoff at the lower Nyquist frequency).
  The public data carry nothing above their own Nyquist frequency: CirCor (4 kHz) nothing above 2 kHz, EPHNOGRAM
  (8 kHz) nothing above 4 kHz; the model then fills that region with the own recordings' floor only (rates: dataset
  headers, read by `hfs.circor` / `hfs.ephnogram`).
- INMP441: numbers from `Development/system/testing/AUDIO/chain-measurement/microphone_model.py` (DigitalStethoscope
  repository; datasheet record `tdk_inmp441_datasheet_2014`, DS-INMP441-00 rev. 1.0). Acoustic high-pass 60 Hz
  (checked in the record); digital high-pass 3.7 Hz at 48 kHz scaled to 1.23 Hz at 16 kHz and pass band
  0.423 x fS are NOT yet checked against the datasheet page (unverified, as marked in that file); first order for both
  corners and the scaling with fS are project assumptions of that file. Applied as causal first-order sections
  (a first-order high-pass is minimum phase); the 17.2-sample group delay is omitted so that dataset segmentations stay
  aligned. Phase is not what the model is trusted for.
- Chest-piece: none applied (lead decision R2-4 in `STATE.md`). The public sensors stay inside the signal.
- Spectrum match (variant): smooth third-octave correction 20 Hz-1 kHz, limit +-12 dB, three-point smoothing, linear
  interpolation over octaves inside, tapering to 0 dB within one octave outside; zero-phase linear-phase FIR,
  8191 taps (Blackman window, `firwin2`). It moves the dataset's median long-term spectral shape onto the own median
  shape. It stands for chest-piece, tube and sensor differences together AND for differences between persons (one
  adult man, own recordings, against the dataset's subjects); an empirical match, not a physical model (project decision).
- Level measure: median over beats of the largest absolute value of the zero-phase 4th-order Butterworth 20-400 Hz
  band. Chosen because it measures the heart sounds themselves (beat by beat, robust to a few loud beats and to
  between-beat noise) on the band where heart-sound energy lies, and it is computable the same way on own data
  (reference beats) and on public data (CirCor S1 starts, EPHNOGRAM ECG R peaks); below 20 Hz is excluded because the
  public sensors deliver little there (project decision). One gain per dataset and condition (median over recordings),
  so differences between recordings stay; `per_recording_normalisation=True` switches to one gain per recording.
- Overload: the gain at which the same share of beats as in elevated-2/elevated-3 contains a sample at a 24-bit limit
  (quantile of the per-beat gains to reach a limit). Beat segments run from midpoint to midpoint between beat times.
- Noise floor: per third-octave band 20 Hz-6.3 kHz, the 10th percentile of 250 ms frame power (hop 62.5 ms),
  median over the five own recordings (own measurement, 23 Nov 2026). This floor contains room and body sound and the
  chest-piece's pick-up, not only microphone noise. Added: Gaussian noise (seeded) shaped so that the floor reaches the
  target where the modelled floor lies below it; nothing is subtracted. The INMP441 datasheet signal-to-noise ratio /
  equivalent input noise is NOT recorded in `thesis-material/quellen.md` (the `tdk_inmp441_datasheet_2014` record
  lists only frequency response, group delay and interface data), so no comparison with a datasheet noise figure is
  made here (unverified).
- Hard limit: the own recordings reach exactly -8388608 (lower 24-bit limit; 473 samples in elevated-2, 457 in
  elevated-3) in flat runs of up to 33 samples, while the positive peaks stay below +8388607 (largest 8313073 in
  elevated-2); rest-1 hits both limits only during its movement artefact (own measurement 23 Nov 2026, `load_recording`).
  At the clipped samples the part below 20 Hz (4th-order zero-phase split at 20 Hz) contributes a median of
  -0.37 full scale (elevated-2) and -0.19 (elevated-3), the part from 20 Hz upward -0.64 and -0.81; with the part below
  20 Hz removed only 3 of 129 and 5 of 127 beats would reach the limit instead of 42 and 45 (own measurement,
  23 Nov 2026). So the overload is a heart-sound peak riding on a negative slow excursion, and it is one-sided because
  of that excursion, not because the positive limit differs. The model clips symmetrically at -8388608 / +8388607 and
  rounds to integers: clipping lands on whichever polarity reaches the limit.

## Where the model cannot reach the real chain

- Content below about 20 Hz: the own recordings carry a large share of their energy there (see table); the public
  sensors deliver much less (their own sensors' low-frequency roll-off is unknown; the cause on the own side, chest
  motion or pressure in chest-piece and tube, is not measured). In elevated-2/-3 a negative slow excursion adds
  0.2-0.4 full scale under the heart sound at the clipped samples (see above). In the model the overload gain must
  push the heart sounds themselves to full scale, so clipping hits both polarities rather than only the lower limit,
  and the gain is higher than the real loudness difference between rest and elevated recordings.
- The spectrum match is limited to +-12 dB and to 20 Hz-1 kHz; where the correction hits the limit, the shape stays off
  (see the band table).
- No content above 2 kHz (CirCor) or 4 kHz (EPHNOGRAM): the region is filled with floor noise only.
- Floor: the public recordings' own noise (their sensors, rooms, children crying in CirCor) remains; where it lies above
  the own floor nothing is removed.
- The 17.2-sample microphone delay and the microphone phase are not modelled.
## Known problems

- The overload gain matches the pooled share of beats (all beats of all recordings together). Per recording the
  share scatters widely, so the median over recordings lies below the target (see the two rows in the table).
- At the rest gain the public data clip more often than the own rest recordings (pooled 3-12 % of beats against
  1.2 %): their beat-to-beat and recording-to-recording level spread is wider than the own three rest recordings'.
- The EPHNOGRAM selection takes records whose ECG reference file exists in `reference-public/ephnogram/` at run time;
  while that folder still grows, a rerun may pick other records (the selection used is in `selection.json`).
- The EPHNOGRAM beat times are ECG R peaks, the own ones S1 energy centroids and the CirCor ones S1 onsets; the
  midpoint-to-midpoint beat segments still contain S1 and S2 in all three cases at the heart rates seen.
- Matching hits the +-12 dB limit from 125 Hz upward for both datasets; CirCor stays 15-33 dB above the own shape
  from 200 Hz to 1 kHz even after matching.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--circor-count", type=int, default=CIRCOR_RECORDING_COUNT)
    parser.add_argument("--ephnogram-count", type=int, default=EPHNOGRAM_RECORD_LIMIT)
    arguments = parser.parse_args()
    started = time.perf_counter()

    own_measures = {name: measure(recordings.load_recording(name), chain_model.own_reference_beat_times_s(name),
                                  recordings.DISCARDED_SECONDS) for name in recordings.RECORDING_NAMES}
    datasets = {"ephnogram": ephnogram_items(arguments.ephnogram_count), "circor": circor_items(arguments.circor_count)}
    print({dataset: len(items) for dataset, items in datasets.items()}, f"{time.perf_counter() - started:.0f} s")
    calibrations, modelled, modelled_segments, selections = {}, {}, {}, {}
    for dataset, items in datasets.items():
        calibration = chain_model.fit_calibration(dataset, items)
        calibrations[dataset] = calibration
        selections[dataset] = [{key: (value if not isinstance(value, numpy.floating) else float(value))
                                for key, value in item.items() if key in ("name", "subject", "group", "excerpt_start_seconds")}
                               for item in items]
        results = {}
        for variant in chain_model.SPECTRUM_VARIANTS:
            for condition in chain_model.LEVEL_CONDITIONS:
                entries = []
                for index, item in enumerate(items):
                    output = chain_model.model_through_capture_chain(item["samples"], item["sample_rate_hz"],
                                                                     level_condition=condition, spectrum_variant=variant,
                                                                     calibration=calibration, seed=index)
                    entries.append(measure(output, item["beat_times_s"]))
                    if index == 0 and variant == "microphone_only":
                        start = 5 * chain_model.TARGET_SAMPLE_RATE_HZ
                        modelled_segments.setdefault(dataset, {})[condition] = (
                            f"modelled {DATASET_TITLES[dataset]} {item['name']} ({item['group'][:28]}), {condition}, 5-8 s",
                            output[start:start + 3 * chain_model.TARGET_SAMPLE_RATE_HZ])
                results[(variant, condition)] = entries
        modelled[dataset] = results
        print(dataset, "modelled", f"{time.perf_counter() - started:.0f} s")

    table_rows = []
    for key, label in SCALAR_MEASURES:
        for condition in chain_model.LEVEL_CONDITIONS:
            row = {"measure": label, "condition": condition,
                   "own": median_of([own_measures[name] for name in CONDITION_OWN_RECORDINGS[condition]], key)}
            for dataset, results in modelled.items():
                for variant in chain_model.SPECTRUM_VARIANTS:
                    row[f"{dataset} {variant}"] = median_of(results[(variant, condition)], key)
            table_rows.append(row)
    own_median_shape = numpy.median([own_measures[name]["band_shape_db"] for name in recordings.RECORDING_NAMES], axis=0)
    band_rows = []
    for index, centre in enumerate(chain_model.match_band_centres_hz()):
        row = {"band": nominal_band_label(centre)}
        for dataset, results in modelled.items():
            for variant, suffix in (("microphone_only", "before"), ("matched_to_own_recordings", "after")):
                row[f"{dataset} {suffix}"] = float(numpy.median([entry["band_shape_db"][index] for entry in results[(variant, "rest")]])
                                                   - own_median_shape[index])
        band_rows.append(row)

    CALIBRATION_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with open(CALIBRATION_DIRECTORY / "how_close.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table_rows[0].keys()))
        writer.writeheader()
        writer.writerows(table_rows)
    with open(CALIBRATION_DIRECTORY / "band_difference.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(band_rows[0].keys()))
        writer.writeheader()
        writer.writerows(band_rows)
    (CALIBRATION_DIRECTORY / "selection.json").write_text(json.dumps(selections, indent=1), encoding="utf-8")

    own_rest = recordings.load_recording("rest-2")
    own_overload = recordings.load_recording("elevated-2")
    second = chain_model.TARGET_SAMPLE_RATE_HZ
    own_segments = {"rest": ("own rest-2, 12-15 s from file start", own_rest[10 * second:13 * second]),
                    "overload": ("own elevated-2, 12-15 s from file start", own_overload[10 * second:13 * second])}
    figure_long_term_spectra(own_measures, modelled)
    figure_band_difference(own_median_shape, modelled)
    figure_time_domain(own_segments, modelled_segments)
    path = write_summary(calibrations, own_measures, modelled, {dataset: len(items) for dataset, items in datasets.items()},
                         table_rows, band_rows, time.perf_counter() - started)
    print("wrote", path, f"{time.perf_counter() - started:.0f} s")


if __name__ == "__main__":
    main()
