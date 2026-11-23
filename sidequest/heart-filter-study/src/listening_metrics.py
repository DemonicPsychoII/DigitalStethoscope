"""Objective metrics of listening-filter candidates on the study recordings: headroom, loudness, cleanliness, transients.

Writes listening/metrics.csv, listening/metrics_summary.csv, listening/SUMMARY.md and listening/figures/*.png.
"""
import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache

import numpy
from scipy import ndimage, signal

import listening_common as common
from listening_common import (RECORDING_NAMES, SAMPLE_RATE_HZ, DISCARDED_SECONDS, LISTENING_DIRECTORY, FIGURES_DIRECTORY,
                              database, load_recording, apply_filter_blockwise, apply_gain_and_output, count_clipped,
                              candidate_from_entry, frequency_response, group_delay_seconds, cost)

HIGHPASS_EDGES_HZ = [10, 20, 30, 40, 50, 60, 80, 100, 150]
LOWPASS_EDGES_HZ = [200, 300, 400, 600, 800, 1000, 1500, 2000, None]
ORDER_PAIRS = [(2, 2), (4, 4)]
OTHER_FAMILIES = ["bessel", "chebyshev1", "elliptic"]
OTHER_HIGHPASS_EDGES_HZ = [20, 40, 60, 100]
OTHER_LOWPASS_EDGES_HZ = [400, 800, 1500]
MURMUR_DESIGN = {"family": "butterworth", "highpass_hz": 40, "lowpass_hz": 800, "highpass_order": 2, "lowpass_order": 2}
BPM_DESIGN = {"family": "butterworth", "highpass_hz": 25, "lowpass_hz": 150, "highpass_order": 2, "lowpass_order": 2}
WELCH_SEGMENT_SAMPLES = 16384
IMPULSE_SECONDS = 4.0
RINGING_THRESHOLD_DB = -40.0
ENVELOPE_HOLD_SAMPLES = 32
# Every candidate is excited by the same click band-limited to 2 kHz, so the ringing figure does not depend on how
# much of an ideal impulse the candidate's own low-pass removes.
REFERENCE_CLICK_SECTIONS = signal.butter(4, 2000.0, btype="lowpass", fs=SAMPLE_RATE_HZ, output="sos")
GROUP_DELAY_BAND_HZ = (40.0, 400.0)
FAMILY_NAMES = {"raw": "Raw", "butterworth": "Butterworth", "bessel": "Bessel", "chebyshev1": "Chebyshev I 0.5 dB",
                "elliptic": "elliptic 0.5/40 dB"}


def candidate_grid() -> list[dict]:
    entries = [{"family": "raw"}]
    for highpass_order, lowpass_order in ORDER_PAIRS:
        for highpass_hz in HIGHPASS_EDGES_HZ:
            for lowpass_hz in LOWPASS_EDGES_HZ:
                if lowpass_hz is not None and lowpass_hz <= highpass_hz:
                    continue
                entries.append({"family": "butterworth", "highpass_hz": highpass_hz, "lowpass_hz": lowpass_hz,
                                "highpass_order": highpass_order, "lowpass_order": lowpass_order})
        for family in OTHER_FAMILIES:
            for highpass_hz in OTHER_HIGHPASS_EDGES_HZ:
                for lowpass_hz in OTHER_LOWPASS_EDGES_HZ:
                    entries.append({"family": family, "highpass_hz": highpass_hz, "lowpass_hz": lowpass_hz,
                                    "highpass_order": highpass_order, "lowpass_order": lowpass_order})
    entries.append(dict(BPM_DESIGN))
    unique = {}
    for entry in entries:
        unique.setdefault(candidate_from_entry(entry).identifier, entry)
    return list(unique.values())


@lru_cache(maxsize=None)
def recording_context(name: str) -> dict:
    samples = load_recording(name)
    frame_samples = common.frame_samples_count(SAMPLE_RATE_HZ)
    segments = common.segment_frames(samples, name, SAMPLE_RATE_HZ)
    return {"samples": samples, "frame_samples": frame_samples, "segments": segments,
            "input_clipped": count_clipped(samples)}


def transient_metrics(candidate) -> dict:
    frequencies = numpy.geomspace(*GROUP_DELAY_BAND_HZ, 200)
    click = signal.sosfilt(REFERENCE_CLICK_SECTIONS, numpy.r_[1.0, numpy.zeros(int(IMPULSE_SECONDS * SAMPLE_RATE_HZ) - 1)])
    if candidate.family == "raw":
        delays = numpy.zeros(len(frequencies))
        named = {50: 0.0, 100: 0.0, 200: 0.0}
        impulse = click
    else:
        delays = group_delay_seconds(candidate, frequencies)
        named = {frequency: float(group_delay_seconds(candidate, [frequency])[0]) for frequency in (50, 100, 200)}
        impulse = signal.sosfilt(candidate.second_order_sections.astype(numpy.float64), click) * candidate.gain
    envelope = ndimage.maximum_filter1d(numpy.abs(impulse), size=ENVELOPE_HOLD_SAMPLES)
    above = numpy.nonzero(envelope >= envelope.max() * 10.0 ** (RINGING_THRESHOLD_DB / 20.0))[0]
    ringing_seconds = (above[-1] + 1) / SAMPLE_RATE_HZ
    step = numpy.cumsum(impulse)
    undershoot = -step.min() / step.max() if step.max() > 0 else 0.0
    return {"group_delay_50hz_ms": 1e3 * named[50], "group_delay_100hz_ms": 1e3 * named[100],
            "group_delay_200hz_ms": 1e3 * named[200],
            "group_delay_variation_40_400hz_ms": 1e3 * float(numpy.nanmax(delays) - numpy.nanmin(delays)),
            "ringing_to_minus40db_ms": 1e3 * ringing_seconds,
            "step_undershoot_percent": 100.0 * float(max(undershoot, 0.0)),
            "ringing_truncated": bool(above[-1] >= len(impulse) - 1)}


def spectral_shares(output_full_scale: numpy.ndarray) -> tuple[float, float, float, numpy.ndarray, numpy.ndarray]:
    frequencies, density = signal.welch(output_full_scale, fs=SAMPLE_RATE_HZ, nperseg=WELCH_SEGMENT_SAMPLES)
    resolution = frequencies[1] - frequencies[0]
    total = density.sum()
    above_1khz = density[frequencies > 1000.0].sum() / total if total > 0 else 0.0
    below_20hz = density[frequencies < 20.0].sum() / total if total > 0 else 0.0
    iso_power = float(numpy.sum(density * resolution * 10.0 ** (common.iso226_weighting_db(frequencies) / 10.0)))
    return float(above_1khz), float(below_20hz), iso_power, frequencies, density


def analyse_candidate(entry: dict) -> dict:
    candidate = candidate_from_entry(entry)
    rows = []
    filtered_by_recording = {}
    for name in RECORDING_NAMES:
        context = recording_context(name)
        filtered = apply_filter_blockwise(candidate, context["samples"])
        filtered_by_recording[name] = filtered
        output = common.to_full_scale(apply_gain_and_output(filtered, 0.0))
        peak = float(numpy.max(numpy.abs(output)))
        mean_power = float(numpy.mean(output ** 2))
        a_weighted = common.weighted(output, common.A_WEIGHTING)
        k_weighted = common.weighted(output, common.K_WEIGHTING)
        block_powers = common.bs1770_block_powers(k_weighted, SAMPLE_RATE_HZ)
        gated, ungated = common.bs1770_loudness(block_powers)
        above_1khz, below_20hz, iso_power, _, _ = spectral_shares(output)
        frame_samples = context["frame_samples"]
        a_frames = common.frame_powers(a_weighted, frame_samples)
        plain_frames = common.frame_powers(output, frame_samples)
        heart, between = context["segments"]["heart"], context["segments"]["between"]
        rows.append({
            "identifier": candidate.identifier, "recording": name,
            "input_samples_at_limit": context["input_clipped"],
            "output_samples_at_limit": count_clipped(apply_gain_and_output(filtered, 0.0)),
            "output_peak_dbfs": 20.0 * numpy.log10(max(peak, 1e-12)),
            "output_rms_dbfs": database(mean_power),
            "crest_factor_db": 20.0 * numpy.log10(max(peak, 1e-12)) - database(mean_power),
            "headroom_gain_zero_saturation_db": common.zero_saturation_gain_db(filtered),
            "headroom_gain_0p01_percent_db": common.share_saturation_gain_db(filtered),
            "headroom_gain_zero_saturation_without_artefact_db": common.zero_saturation_gain_db(
                filtered[common.outside_artefact_mask(name, len(filtered))]),
            "a_weighted_level_db": database(float(numpy.mean(a_weighted ** 2))),
            "k_loudness_gated_lufs": gated, "k_loudness_ungated_lufs": ungated,
            "iso226_60phon_level_db": database(iso_power),
            "between_to_heart_a_weighted_db": database(a_frames[between].mean()) - database(a_frames[heart].mean()),
            "between_to_heart_unweighted_db": database(plain_frames[between].mean()) - database(plain_frames[heart].mean()),
            "between_a_weighted_level_db": database(a_frames[between].mean()),
            "heart_a_weighted_level_db": database(a_frames[heart].mean()),
            "energy_share_above_1khz_percent": 100.0 * above_1khz,
            "energy_share_below_20hz_percent": 100.0 * below_20hz,
            "_block_powers": block_powers,
        })
    safe_zero = min(row["headroom_gain_zero_saturation_db"] for row in rows)
    safe_share = min(row["headroom_gain_0p01_percent_db"] for row in rows)
    limiting = min(rows, key=lambda row: row["headroom_gain_zero_saturation_db"])["recording"]
    safe_without_artefact = min(row["headroom_gain_zero_saturation_without_artefact_db"] for row in rows)
    limiting_without_artefact = min(rows, key=lambda row: row["headroom_gain_zero_saturation_without_artefact_db"])["recording"]
    for row in rows:
        check = count_clipped(apply_gain_and_output(filtered_by_recording[row["recording"]], safe_zero))
        block_powers = row.pop("_block_powers")
        gated_safe, ungated_safe = common.bs1770_loudness(block_powers, safe_zero)
        gated_without_artefact, _ = common.bs1770_loudness(block_powers, safe_without_artefact)
        row.update({
            "safe_gain_all_recordings_zero_saturation_db": safe_zero,
            "safe_gain_all_recordings_0p01_percent_db": safe_share,
            "safe_gain_limiting_recording": limiting,
            "safe_gain_without_artefact_db": safe_without_artefact,
            "safe_gain_without_artefact_limiting_recording": limiting_without_artefact,
            "output_samples_at_limit_at_safe_gain_without_artefact": count_clipped(
                apply_gain_and_output(filtered_by_recording[row["recording"]], safe_without_artefact)),
            "output_samples_at_limit_at_safe_gain": check,
            "a_weighted_level_at_safe_gain_db": row["a_weighted_level_db"] + safe_zero,
            "k_loudness_gated_at_safe_gain_lufs": gated_safe,
            "k_loudness_ungated_at_safe_gain_lufs": ungated_safe,
            "iso226_60phon_level_at_safe_gain_db": row["iso226_60phon_level_db"] + safe_zero,
            "between_a_weighted_level_at_safe_gain_db": row["between_a_weighted_level_db"] + safe_zero,
            "a_weighted_level_at_safe_gain_without_artefact_db": row["a_weighted_level_db"] + safe_without_artefact,
            "k_loudness_gated_at_safe_gain_without_artefact_lufs": gated_without_artefact,
            "iso226_60phon_level_at_safe_gain_without_artefact_db": row["iso226_60phon_level_db"] + safe_without_artefact,
            "between_a_weighted_level_at_safe_gain_without_artefact_db": row["between_a_weighted_level_db"] + safe_without_artefact,
        })
    candidate_cost = cost(candidate)
    shared = {"family": candidate.family, "description": candidate.description,
              "highpass_hz": candidate.highpass_hz, "lowpass_hz": candidate.lowpass_hz,
              "highpass_order": candidate.highpass_order, "lowpass_order": candidate.lowpass_order,
              "multiplies_per_sample": candidate_cost["multiplies_per_sample"], **transient_metrics(candidate)}
    for row in rows:
        row.update(shared)
    return {"identifier": candidate.identifier, "entry": entry, "rows": rows}


METRIC_COLUMNS = [
    "identifier", "recording", "family", "highpass_hz", "lowpass_hz", "highpass_order", "lowpass_order",
    "input_samples_at_limit", "output_samples_at_limit", "output_peak_dbfs", "output_rms_dbfs", "crest_factor_db",
    "headroom_gain_zero_saturation_db", "headroom_gain_0p01_percent_db",
    "safe_gain_all_recordings_zero_saturation_db", "safe_gain_all_recordings_0p01_percent_db",
    "safe_gain_limiting_recording", "output_samples_at_limit_at_safe_gain",
    "headroom_gain_zero_saturation_without_artefact_db", "safe_gain_without_artefact_db",
    "safe_gain_without_artefact_limiting_recording", "output_samples_at_limit_at_safe_gain_without_artefact",
    "a_weighted_level_db", "a_weighted_level_at_safe_gain_db",
    "k_loudness_gated_lufs", "k_loudness_ungated_lufs", "k_loudness_gated_at_safe_gain_lufs",
    "k_loudness_ungated_at_safe_gain_lufs", "iso226_60phon_level_db", "iso226_60phon_level_at_safe_gain_db",
    "between_to_heart_a_weighted_db", "between_to_heart_unweighted_db", "heart_a_weighted_level_db",
    "between_a_weighted_level_db", "between_a_weighted_level_at_safe_gain_db",
    "a_weighted_level_at_safe_gain_without_artefact_db", "k_loudness_gated_at_safe_gain_without_artefact_lufs",
    "iso226_60phon_level_at_safe_gain_without_artefact_db", "between_a_weighted_level_at_safe_gain_without_artefact_db",
    "energy_share_above_1khz_percent", "energy_share_below_20hz_percent",
    "group_delay_50hz_ms", "group_delay_100hz_ms", "group_delay_200hz_ms", "group_delay_variation_40_400hz_ms",
    "ringing_to_minus40db_ms", "ringing_truncated", "step_undershoot_percent", "multiplies_per_sample", "description"]

SUMMARY_MEAN_AND_WORST = [
    ("a_weighted_level_at_safe_gain_db", min), ("k_loudness_gated_at_safe_gain_lufs", min),
    ("k_loudness_ungated_at_safe_gain_lufs", min), ("iso226_60phon_level_at_safe_gain_db", min),
    ("between_to_heart_a_weighted_db", max), ("between_a_weighted_level_at_safe_gain_db", max),
    ("energy_share_above_1khz_percent", max), ("energy_share_below_20hz_percent", max),
    ("a_weighted_level_at_safe_gain_without_artefact_db", min),
    ("k_loudness_gated_at_safe_gain_without_artefact_lufs", min),
    ("iso226_60phon_level_at_safe_gain_without_artefact_db", min),
    ("between_a_weighted_level_at_safe_gain_without_artefact_db", max),
    ("output_peak_dbfs", max), ("crest_factor_db", max), ("headroom_gain_zero_saturation_db", min)]


def format_value(value):
    if isinstance(value, float):
        return "" if numpy.isnan(value) else f"{value:.3f}"
    if value is None:
        return ""
    return value


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(row.get(key)) for key in columns})


def summarise(results: list[dict]) -> list[dict]:
    summary = []
    for result in results:
        rows = result["rows"]
        first = rows[0]
        record = {key: first[key] for key in (
            "identifier", "family", "highpass_hz", "lowpass_hz", "highpass_order", "lowpass_order",
            "safe_gain_all_recordings_zero_saturation_db", "safe_gain_all_recordings_0p01_percent_db",
            "safe_gain_limiting_recording", "safe_gain_without_artefact_db",
            "safe_gain_without_artefact_limiting_recording", "group_delay_50hz_ms", "group_delay_100hz_ms", "group_delay_200hz_ms",
            "group_delay_variation_40_400hz_ms", "ringing_to_minus40db_ms", "step_undershoot_percent",
            "multiplies_per_sample", "description")}
        record["output_samples_at_limit_total"] = sum(row["output_samples_at_limit"] for row in rows)
        record["output_samples_at_limit_at_safe_gain_total"] = sum(row["output_samples_at_limit_at_safe_gain"] for row in rows)
        record["output_samples_at_limit_at_safe_gain_without_artefact_total"] = sum(
            row["output_samples_at_limit_at_safe_gain_without_artefact"] for row in rows)
        record["input_samples_at_limit_total"] = sum(row["input_samples_at_limit"] for row in rows)
        for key, worst in SUMMARY_MEAN_AND_WORST:
            values = [row[key] for row in rows]
            record[f"{key}_mean"] = float(numpy.mean(values))
            record[f"{key}_worst"] = float(worst(values))
        summary.append(record)
    raw = next(record for record in summary if record["family"] == "raw")
    for record in summary:
        for key in ("a_weighted_level_at_safe_gain_db", "k_loudness_gated_at_safe_gain_lufs",
                    "iso226_60phon_level_at_safe_gain_db", "a_weighted_level_at_safe_gain_without_artefact_db",
                    "k_loudness_gated_at_safe_gain_without_artefact_lufs",
                    "iso226_60phon_level_at_safe_gain_without_artefact_db"):
            record[f"{key}_over_raw"] = record[f"{key}_mean"] - raw[f"{key}_mean"]
    return summary


def summary_columns(summary):
    return list(summary[0].keys())


def label_of(record_or_entry) -> str:
    family = record_or_entry["family"]
    if family == "raw":
        return "Raw (no filter)"
    lowpass = record_or_entry.get("lowpass_hz")
    band = f"{record_or_entry['highpass_hz']:g}-{lowpass:g} Hz" if lowpass else f"from {record_or_entry['highpass_hz']:g} Hz"
    return f"{FAMILY_NAMES[family]} {record_or_entry['highpass_order']}+{record_or_entry['lowpass_order'] or 0} {band}"


SHORTLIST_ENTRIES = [
    ({"family": "raw"}, "Reference: what the microphone delivers; the device's Raw position."),
    (MURMUR_DESIGN, "Current design candidate for Murmur; safe gain is near 0 dB because elevated-2 and the rest-1 "
                    "movement artefact still reach full scale after a 40 Hz high-pass."),
    ({"family": "butterworth", "highpass_hz": 100, "lowpass_hz": 800, "highpass_order": 2, "lowpass_order": 2},
     "Same structure and cost as the design with the high-pass moved to 100 Hz: about 6 dB more fixed gain; tests "
     "whether the thinner, louder sound is preferred."),
    ({"family": "butterworth", "highpass_hz": 100, "lowpass_hz": 800, "highpass_order": 4, "lowpass_order": 4},
     "Steeper version of the 100 Hz band: more headroom and the higher loudness proxy at twice the cost; tests "
     "whether order matters audibly."),
    ({"family": "butterworth", "highpass_hz": 150, "lowpass_hz": 800, "highpass_order": 4, "lowpass_order": 4},
     "Extreme of the trade-off: the most fixed gain among the band-limited candidates, with most of the heart-sound "
     "fundamental removed; shows where it gets too thin."),
    ({"family": "elliptic", "highpass_hz": 60, "lowpass_hz": 800, "highpass_order": 4, "lowpass_order": 4},
     "Steep high-pass at a lower edge: keeps more body than 100 Hz while still gaining about 4 dB; long ringing "
     "and a large group-delay spread test whether S1/S2 sound smeared."),
    ({"family": "butterworth", "highpass_hz": 80, "lowpass_hz": None, "highpass_order": 2, "lowpass_order": 2},
     "High-pass only, cheapest filter (5 multiplies): tests whether a low-pass is needed at all, since the "
     "recordings carry very little energy above 1 kHz."),
    (BPM_DESIGN, "The BPM switch position as it will sound; narrow band, cleanest for the beat but no murmur range."),
]


def write_shortlist() -> None:
    path = LISTENING_DIRECTORY / "shortlist.json"
    if path.exists():
        return
    candidates = []
    for entry, _ in SHORTLIST_ENTRIES:
        candidate = candidate_from_entry(entry)
        candidates.append({"identifier": candidate.identifier, "label": label_of(
            {"family": candidate.family, "highpass_hz": candidate.highpass_hz, "lowpass_hz": candidate.lowpass_hz,
             "highpass_order": candidate.highpass_order, "lowpass_order": candidate.lowpass_order}), **entry})
    excerpts = [
        {"recording": "rest-2", "start_s": 20.0, "duration_s": 10.0, "label": "resting"},
        {"recording": "elevated-1", "start_s": 12.0, "duration_s": 10.0, "label": "elevated-clean"},
        {"recording": "elevated-2", "start_s": 20.0, "duration_s": 10.0, "label": "elevated-overload"},
        {"recording": "rest-1", "start_s": 36.0, "duration_s": 10.0, "label": "movement-artefact"},
    ]
    path.write_text(json.dumps({"excerpts": excerpts, "candidates": candidates}, indent=2) + "\n", encoding="utf-8")


def figure_spectra(pyplot) -> None:
    figure, axes = pyplot.subplots(len(RECORDING_NAMES), 1, figsize=(9, 2.4 * len(RECORDING_NAMES)), sharex=True)
    for axis, name in zip(axes, RECORDING_NAMES):
        context = recording_context(name)
        samples = context["samples"] / common.FULL_SCALE
        frequencies, density = signal.welch(samples, fs=SAMPLE_RATE_HZ, nperseg=WELCH_SEGMENT_SAMPLES)
        axis.plot(frequencies[1:], database(density[1:]), label="whole recording (1 Hz resolution)", linewidth=1.2)
        segment_samples = 2048
        stft_frequencies, _, spectrogram = signal.spectrogram(samples, fs=SAMPLE_RATE_HZ, nperseg=segment_samples,
                                                              noverlap=segment_samples // 2, mode="psd")
        frame_samples = context["frame_samples"]
        centres = (numpy.arange(spectrogram.shape[1]) * (segment_samples // 2) + segment_samples // 2)
        for mask_key, label in (("heart", "heart-sound windows"), ("between", "between-beat windows")):
            mask = context["segments"][mask_key]
            window_frames = segment_samples // frame_samples
            shares = []
            for centre in centres:
                first = max(0, (centre - segment_samples // 2) // frame_samples)
                shares.append(mask[first:first + window_frames].mean() if first < len(mask) else 0.0)
            selected = numpy.asarray(shares) >= 0.5
            if selected.any():
                axis.plot(stft_frequencies[1:], database(spectrogram[1:, selected].mean(axis=1)),
                          label=f"{label} (7.8 Hz resolution, {selected.sum()} windows)", linewidth=1.0)
        common.hertz_axis(axis, 5, 8000)
        axis.tick_params(labelbottom=True)
        axis.set_ylabel("PSD (dB re FS²/Hz)")
        axis.set_title(f"{name}: averaged input spectrum", fontsize=10)
        axis.set_ylim(-160, -20)
        axis.legend(fontsize=7, loc="upper right")
    figure.tight_layout()
    figure.savefig(FIGURES_DIRECTORY / "spectra.png", dpi=110)
    pyplot.close(figure)


def figure_headroom(pyplot, summary) -> None:
    figure, axes = pyplot.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    raw = next(record for record in summary if record["family"] == "raw")
    for axis, order in zip(axes, (2, 4)):
        for lowpass in (200, 400, 800, 1500, None):
            points = sorted((record["highpass_hz"], record["safe_gain_all_recordings_zero_saturation_db"])
                            for record in summary if record["family"] == "butterworth"
                            and record["highpass_order"] == order and record["lowpass_hz"] == lowpass)
            if points:
                axis.plot(*zip(*points), marker="o", markersize=3,
                          label=f"low-pass {lowpass:g} Hz" if lowpass else "no low-pass")
        axis.axhline(raw["safe_gain_all_recordings_zero_saturation_db"], color="#c0c0c0", linestyle="--", linewidth=1,
                     label="Raw")
        common.hertz_axis(axis, 8, 200)
        axis.set_xlabel("High-pass edge")
        axis.set_title(f"Butterworth {order}+{order}: gain safe for all five recordings", fontsize=10)
        axis.legend(fontsize=8)
    axes[0].set_ylabel("Largest fixed gain without output saturation (dB)")
    figure.tight_layout()
    figure.savefig(FIGURES_DIRECTORY / "headroom_gain.png", dpi=110)
    pyplot.close(figure)


def figure_loudness_cleanliness(pyplot, summary, shortlist) -> None:
    figure, axis = pyplot.subplots(figsize=(9.5, 6.5))
    markers = {"raw": "*", "butterworth": "o", "bessel": "s", "chebyshev1": "^", "elliptic": "D"}
    for family, marker in markers.items():
        records = [record for record in summary if record["family"] == family]
        axis.scatter([record["between_to_heart_a_weighted_db_mean"] for record in records],
                     [record["iso226_60phon_level_at_safe_gain_db_mean"] for record in records],
                     marker=marker, s=60 if family == "raw" else 16, alpha=0.75, label=FAMILY_NAMES[family])
    for record in shortlist:
        x_value = record["between_to_heart_a_weighted_db_mean"]
        y_value = record["iso226_60phon_level_at_safe_gain_db_mean"]
        axis.scatter([x_value], [y_value], s=90, facecolors="none", edgecolors="#ffffff", linewidths=1.2)
        axis.annotate(label_of(record), (x_value, y_value), xytext=(6, 4), textcoords="offset points", fontsize=8,
                      color="#ffffff")
    axis.set_xlabel("Between-beat background relative to heart sounds, A-weighted (dB, mean over recordings)  → noisier")
    axis.set_ylabel("Loudness proxy at safe gain: ISO 226 60-phon weighted level (dB re FS)  → louder")
    axis.set_title("Loudness at the all-recordings-safe fixed gain against background between beats\n"
                   "(the background ratio does not depend on gain)", fontsize=10)
    axis.legend(fontsize=8, loc="lower right")
    figure.tight_layout()
    figure.savefig(FIGURES_DIRECTORY / "loudness_vs_cleanliness.png", dpi=110)
    pyplot.close(figure)


def figure_responses(pyplot, shortlist, results_by_identifier) -> None:
    figure, axes = pyplot.subplots(2, 1, figsize=(9, 7), sharex=True)
    frequencies = numpy.geomspace(5, 8000, 800)
    for record in shortlist:
        candidate = candidate_from_entry(results_by_identifier[record["identifier"]]["entry"])
        response = frequency_response(candidate, frequencies) if candidate.family != "raw" else numpy.ones(len(frequencies))
        axes[0].plot(frequencies, 20 * numpy.log10(numpy.maximum(numpy.abs(response), 1e-9)), label=label_of(record),
                     linewidth=1.2)
        gain = record["safe_gain_all_recordings_zero_saturation_db"]
        axes[1].plot(frequencies, 20 * numpy.log10(numpy.maximum(numpy.abs(response), 1e-9)) + gain,
                     label=f"{label_of(record)} (+{gain:.1f} dB)" if gain >= 0 else f"{label_of(record)} ({gain:.1f} dB)",
                     linewidth=1.2)
    axes[0].set_title("Shortlist magnitude responses (gain 1.0)", fontsize=10)
    axes[1].set_title("Including the all-recordings-safe make-up gain", fontsize=10)
    for axis in axes:
        axis.set_ylim(-60, 25)
        axis.set_ylabel("Magnitude (dB)")
        common.hertz_axis(axis, 5, 8000)
        axis.legend(fontsize=7, loc="lower center", ncol=2)
    figure.tight_layout()
    figure.savefig(FIGURES_DIRECTORY / "shortlist_responses.png", dpi=110)
    pyplot.close(figure)


WAVEFORM_WINDOWS_S = {"rest-1": 37.0, "rest-2": 20.0, "elevated-1": 12.0, "elevated-2": 20.0, "elevated-3": 10.0}


def figure_waveforms(pyplot, shortlist, results_by_identifier) -> None:
    for name in RECORDING_NAMES:
        context = recording_context(name)
        start = int((WAVEFORM_WINDOWS_S[name] - DISCARDED_SECONDS) * SAMPLE_RATE_HZ)
        stop = start + 3 * SAMPLE_RATE_HZ
        times = DISCARDED_SECONDS + numpy.arange(start, stop) / SAMPLE_RATE_HZ
        figure, axes = pyplot.subplots(len(shortlist), 1, figsize=(10, 1.45 * len(shortlist) + 0.6), sharex=True)
        for axis, record in zip(axes, shortlist):
            candidate = candidate_from_entry(results_by_identifier[record["identifier"]]["entry"])
            filtered = apply_filter_blockwise(candidate, context["samples"])
            gain = record["safe_gain_all_recordings_zero_saturation_db"]
            made_up = common.to_full_scale(apply_gain_and_output(filtered, gain))[start:stop]
            device = common.to_full_scale(apply_gain_and_output(filtered, 0.0))[start:stop]
            axis.plot(times, made_up, color="#f2a541", linewidth=0.6, alpha=0.7, label=f"with safe gain {gain:+.1f} dB")
            axis.plot(times, device, color="#5aa9e6", linewidth=0.6, label="device today (gain 1.0)")
            for level in (1.0, -1.0):
                axis.axhline(level, color="#f25f5c", linewidth=0.8, linestyle="--")
            axis.set_ylim(-1.15, 1.15)
            axis.set_yticks([-1, 0, 1])
            axis.set_ylabel("FS", fontsize=8)
            axis.set_title(label_of(record), fontsize=8, loc="left", pad=2)
            axis.legend(fontsize=6, loc="upper right", ncol=2)
        axes[-1].set_xlabel("Time from file start (s)")
        figure.suptitle(f"{name}: 3 s at the DAC, ±full scale dashed", fontsize=10)
        figure.tight_layout()
        figure.savefig(FIGURES_DIRECTORY / f"waveforms_{name}.png", dpi=105)
        pyplot.close(figure)


def markdown_table(records, columns):
    header = "| " + " | ".join(title for title, _ in columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, rule]
    for record in records:
        lines.append("| " + " | ".join(formatter(record) for _, formatter in columns) + " |")
    return "\n".join(lines)


def write_summary_markdown(summary, shortlist, results_by_identifier, segment_sources) -> None:
    by_identifier = {record["identifier"]: record for record in summary}
    raw = next(record for record in summary if record["family"] == "raw")
    first_rows = {name: next(row for row in results_by_identifier["raw"]["rows"] if row["recording"] == name)
                  for name in RECORDING_NAMES}
    loudness_key = "iso226_60phon_level_at_safe_gain_db_mean"
    ranked = sorted([record for record in summary if record["family"] != "raw"], key=lambda record: -record[loudness_key])
    columns = [
        ("Candidate", label_of),
        ("Safe gain (dB)", lambda record: f"{record['safe_gain_all_recordings_zero_saturation_db']:+.1f}"),
        ("ISO 226 60 phon at safe gain, vs Raw (dB)", lambda record: f"{record['iso226_60phon_level_at_safe_gain_db_over_raw']:+.1f}"),
        ("A-weighted vs Raw (dB)", lambda record: f"{record['a_weighted_level_at_safe_gain_db_over_raw']:+.1f}"),
        ("LUFS gated vs Raw (dB)", lambda record: f"{record['k_loudness_gated_at_safe_gain_lufs_over_raw']:+.1f}"),
        ("Between/heart A-wtd (dB)", lambda record: f"{record['between_to_heart_a_weighted_db_mean']:.1f}"),
        ("Background A-wtd at safe gain (dB re FS)", lambda record: f"{record['between_a_weighted_level_at_safe_gain_db_mean']:.1f}"),
        (">1 kHz share (%)", lambda record: f"{record['energy_share_above_1khz_percent_mean']:.3f}"),
        ("Ringing to −40 dB (ms)", lambda record: f"{record['ringing_to_minus40db_ms']:.0f}"),
        ("Group-delay spread 40–400 Hz (ms)", lambda record: f"{record['group_delay_variation_40_400hz_ms']:.1f}"),
        ("Multiplies/sample", lambda record: f"{record['multiplies_per_sample']}"),
    ]
    headroom_lines = []
    for order in (2, 4):
        cells = []
        for highpass in HIGHPASS_EDGES_HZ:
            identifier = candidate_from_entry({"family": "butterworth", "highpass_hz": highpass, "lowpass_hz": 800,
                                               "highpass_order": order, "lowpass_order": order}).identifier
            cells.append(f"{by_identifier[identifier]['safe_gain_all_recordings_zero_saturation_db']:+.1f}")
        headroom_lines.append(f"| Butterworth {order}+{order}, low-pass 800 Hz | " + " | ".join(cells) + " |")
    lowpass_lines = []
    for lowpass in LOWPASS_EDGES_HZ:
        identifier = candidate_from_entry({"family": "butterworth", "highpass_hz": 40, "lowpass_hz": lowpass,
                                           "highpass_order": 2, "lowpass_order": 2}).identifier
        record = by_identifier[identifier]
        lowpass_lines.append(
            f"| {lowpass if lowpass else 'none'} | {record['safe_gain_all_recordings_zero_saturation_db']:+.1f} | "
            f"{record['iso226_60phon_level_at_safe_gain_db_over_raw']:+.1f} | {record['a_weighted_level_at_safe_gain_db_over_raw']:+.1f} | "
            f"{record['between_to_heart_a_weighted_db_mean']:.1f} | {record['energy_share_above_1khz_percent_mean']:.3f} |")
    shortlist_json = json.loads((LISTENING_DIRECTORY / "shortlist.json").read_text(encoding="utf-8"))
    per_recording_lines = []
    for record in shortlist:
        rows = {row["recording"]: row for row in results_by_identifier[record["identifier"]]["rows"]}
        cells = [f"{rows[name]['headroom_gain_zero_saturation_db']:+.1f}" for name in RECORDING_NAMES]
        per_recording_lines.append(
            f"| {label_of(record)} | " + " | ".join(cells)
            + f" | {record['safe_gain_all_recordings_zero_saturation_db']:+.1f} ({record['safe_gain_limiting_recording']})"
            + f" | {record['safe_gain_all_recordings_0p01_percent_db']:+.1f}"
            + f" | {record['safe_gain_without_artefact_db']:+.1f} |")
    per_recording = "\n".join(per_recording_lines)
    findings = findings_text(summary, by_identifier, raw, results_by_identifier)
    gating_differences = [row["k_loudness_gated_lufs"] - row["k_loudness_ungated_lufs"]
                          for result in results_by_identifier.values() for row in result["rows"]]
    gating_median = float(numpy.median(gating_differences))
    gating_maximum = float(numpy.max(numpy.abs(gating_differences)))
    text = f"""# Listening-filter metrics: summary

Generated by `src/listening_metrics.py`. Grid: {len(summary)} candidates × {len(RECORDING_NAMES)} recordings, whole
recording after the first {DISCARDED_SECONDS:g} s, volume 100 %, device chain from `hfs` (64-frame blocks, float32
biquads, firmware-exact volume stage and 24-bit saturation). Full tables: `metrics.csv` (per recording),
`metrics_summary.csv` (mean and worst case over recordings).

**The proxies do not replace listening.** They rank candidates by weighted energy; they do not know what a murmur
sounds like, how distortion or ringing is perceived, or how loud the earpieces really are. Use them to choose what to
listen to, then judge by ear with `samples/`.

## How the numbers are defined

- **Safe gain**: the largest single fixed gain (dB, 0.01 dB margin) after the filter for which *none* of the five
  recordings produces a sample at the 24-bit limits at the output (`metrics.csv` also has the per-recording value and
  the gain at which ≤ 0.01 % of samples saturate). It is limited by the recording named in `safe_gain_limiting_recording`.
- **Loudness proxies** (all relative to digital full scale, mean over the recordings, at the safe gain):
  A-weighted level per IEC 61672-1:2013 (A-weighting); K-weighted loudness per ITU-R BS.1770-4 (2015), gated
  integrated and ungated, in LUFS; and a level weighted with the inverse ISO 226:2003 equal-loudness contour at
  {common.ISO226_PHON_LEVEL:g} phon (relative to 1 kHz, extrapolated below 20 Hz at the 20–25 Hz slope; computed from the
  Welch power spectrum). The ISO 226 proxy is the closest of the three to hearing at a moderate listening level, but
  {common.ISO226_PHON_LEVEL:g} phon is an assumption, not a measured earpiece level. None of these is a loudness model
  (no ISO 532 / Zwicker or Moore-Glasberg model was used); they are proxies.
- BS.1770 gating: the recordings are short beats in relative quiet, and a 400 ms gating block nearly always contains
  part of a beat at these heart rates, so the relative gate (−10 LU) removes few blocks. Gated and ungated values are
  both in the CSV; over all candidates and recordings they differ by {gating_median:.2f} LU (median) and at most
  {gating_maximum:.2f} LU. The ranking uses the gated value.
- **Other sound**: `between_to_heart_a_weighted_db` = A-weighted power in between-beat frames over that in heart-sound
  frames (lower = cleaner). Segments: {segment_sources}.
  `energy_share_above_1khz_percent` and `energy_share_below_20hz_percent` are unweighted shares of output energy.
- **Transients**: group delay from the float32 coefficients; ringing = time until the envelope of the impulse response
  stays below −40 dB of its peak, for a click band-limited by a 4th-order 2 kHz Butterworth low-pass (the same click for
  every candidate, so Raw shows the click's own ~2 ms); step undershoot = largest negative step response relative to
  its peak (a high-pass always undershoots; larger means a deeper rebound after each beat).

## Input overload (cannot be removed by any filter)

| Recording | Input samples at the 24-bit limit | Raw output peak (dBFS) | Raw per-recording headroom (dB) | Raw energy below 20 Hz (%) |
| --- | --- | --- | --- | --- |
""" + "\n".join(
        f"| {name} | {row['input_samples_at_limit']} | {row['output_peak_dbfs']:.2f} | "
        f"{row['headroom_gain_zero_saturation_db']:+.2f} | {row['energy_share_below_20hz_percent']:.1f} |"
        for name, row in first_rows.items()) + f"""

Raw has no headroom on any recording that touches full scale at the microphone. Its all-recordings-safe gain is
{raw['safe_gain_all_recordings_zero_saturation_db']:+.2f} dB.

## Headroom gained by the high-pass (all-recordings-safe gain, dB)

| Filter | """ + " | ".join(f"HP {edge} Hz" for edge in HIGHPASS_EDGES_HZ) + """ |
| --- | """ + " | ".join("---" for _ in HIGHPASS_EDGES_HZ) + " |\n" + "\n".join(headroom_lines) + """

What the low-pass edge costs or gains (Butterworth 2+2, high-pass 40 Hz; loudness at the safe gain relative to Raw):

| Low-pass (Hz) | Safe gain (dB) | ISO 226 proxy vs Raw (dB) | A-weighted vs Raw (dB) | Between/heart A-wtd (dB) | >1 kHz share (%) |
| --- | --- | --- | --- | --- | --- |
""" + "\n".join(lowpass_lines) + f"""

## Findings from the numbers

{findings}

## Per-recording headroom of the shortlist (largest gain without output saturation, dB)

| Candidate | """ + " | ".join(RECORDING_NAMES) + """ | All five | All five, ≤ 0.01 % saturated | All five without the rest-1 movement artefact |
| --- | """ + " | ".join("---" for _ in RECORDING_NAMES) + " | --- | --- | --- |\n" + per_recording + f"""

## Loudest candidates by the ISO 226 proxy at the safe gain (top 15, no output saturation by construction)

{markdown_table(ranked[:15], columns)}

## Recommended shortlist ({len(shortlist)} candidates)

{markdown_table(shortlist, columns)}

Reasons:

""" + "\n".join(f"- **{candidate['label']}** (`{candidate['identifier']}`): {SHORTLIST_REASONS.get(candidate['identifier'], 'added by the study lead')}"
                for candidate in shortlist_json['candidates']) + """

The shortlist file `shortlist.json` drives `src/listening_samples.py`; edit it and rerun to change the listening set.
"""
    (LISTENING_DIRECTORY / "SUMMARY.md").write_text(text, encoding="utf-8")


def findings_text(summary, by_identifier, raw, results_by_identifier) -> str:
    def butterworth(highpass, lowpass, order=2):
        return by_identifier[candidate_from_entry({"family": "butterworth", "highpass_hz": highpass, "lowpass_hz": lowpass,
                                                   "highpass_order": order, "lowpass_order": order}).identifier]
    filtered = [record for record in summary if record["family"] != "raw"]
    with_low_edge = [record for record in filtered if record["highpass_hz"] <= 40]
    non_positive = [record for record in with_low_edge if record["safe_gain_all_recordings_zero_saturation_db"] <= 0.0]
    limiting_counts = {}
    for record in filtered:
        limiting_counts[record["safe_gain_limiting_recording"]] = limiting_counts.get(record["safe_gain_limiting_recording"], 0) + 1
    positive_edges = sorted({record["highpass_hz"] for record in filtered if record["family"] == "butterworth"
                             and record["lowpass_hz"] == 800 and record["highpass_order"] == 2
                             and record["iso226_60phon_level_at_safe_gain_db_over_raw"] > 0})
    k_better = [record for record in filtered if record["k_loudness_gated_at_safe_gain_lufs_over_raw"] > 0]
    design = butterworth(40, 800)
    narrow, wide = butterworth(40, 200), butterworth(40, None)
    loudest = max(filtered, key=lambda record: record["iso226_60phon_level_at_safe_gain_db_mean"])
    above_1khz_maximum = max(record["energy_share_above_1khz_percent_mean"] for record in summary)
    design_rest_2 = next(row for row in results_by_identifier[design["identifier"]]["rows"] if row["recording"] == "rest-2")
    lines = [
        f"- **Low high-pass edges buy no headroom.** {len(non_positive)} of {len(with_low_edge)} candidates with a "
        f"high-pass at or below 40 Hz have a safe gain ≤ 0 dB: at gain 1.0 they already saturate on at least one "
        f"recording (Raw: {raw['safe_gain_all_recordings_zero_saturation_db']:+.2f} dB, only because its input touches "
        f"full scale). Removing the infrasound re-centres the hard-clipped, flat-topped overload beats and the movement "
        f"artefact so that their audible part overshoots full scale. Limiting recording over all filtered candidates: "
        + ", ".join(f"{name} {count}×" for name, count in sorted(limiting_counts.items(), key=lambda item: -item[1])) + ".",
        f"- **Headroom grows only from about 50–60 Hz upwards** (Butterworth 2+2 with 800 Hz low-pass: 40 Hz "
        f"{design['safe_gain_all_recordings_zero_saturation_db']:+.1f} dB, 100 Hz "
        f"{butterworth(100, 800)['safe_gain_all_recordings_zero_saturation_db']:+.1f} dB, 150 Hz "
        f"{butterworth(150, 800)['safe_gain_all_recordings_zero_saturation_db']:+.1f} dB). The one fixed gain is set by "
        f"the overload cases; on the clean rest-2 alone the design could take "
        f"{design_rest_2['headroom_gain_zero_saturation_db']:+.1f} dB.",
        f"- **Loudness at the safe gain exceeds Raw by the ISO 226 and A-weighted proxies only for high-pass edges of "
        f"{positive_edges[0] if positive_edges else 'none'} Hz and above** (Butterworth 2+2, 800 Hz). The loudest "
        f"candidate overall by the ISO 226 proxy is {label_of(loudest)} at "
        f"{loudest['iso226_60phon_level_at_safe_gain_db_over_raw']:+.1f} dB over Raw. The design 40–800 Hz is at "
        f"{design['iso226_60phon_level_at_safe_gain_db_over_raw']:+.1f} dB (ISO 226) / "
        f"{design['a_weighted_level_at_safe_gain_db_over_raw']:+.1f} dB (A) relative to Raw.",
        f"- **The K-weighted loudness disagrees:** {len(k_better)} filtered candidates are louder than Raw in LUFS. "
        f"K-weighting is nearly flat down to about 40 Hz, so it counts the 20–100 Hz heart-sound energy that a high-pass "
        f"removes, whereas at moderate listening levels the ear is far less sensitive there (ISO 226). Which proxy is "
        f"closer depends on the real earpiece level, which is not known; listening decides.",
        f"- **The low-pass edge matters little for level:** from 200 Hz to no low-pass the ISO 226 proxy changes by "
        f"{wide['iso226_60phon_level_at_safe_gain_db_over_raw'] - narrow['iso226_60phon_level_at_safe_gain_db_over_raw']:+.1f} dB "
        f"(high-pass 40 Hz). No candidate output carries more than {above_1khz_maximum:.2f} % of its energy above 1 kHz "
        f"(mean over recordings), so the low-pass mainly affects audible hiss and friction noise, which energy numbers "
        f"cannot rank.",
        f"- **Cleanliness:** the between-beat/heart ratio (A-weighted) is {raw['between_to_heart_a_weighted_db_mean']:.1f} dB "
        f"for Raw and {design['between_to_heart_a_weighted_db_mean']:.1f} dB for the design; higher high-pass edges make "
        f"it worse (150 Hz, 2+2: {butterworth(150, 800)['between_to_heart_a_weighted_db_mean']:.1f} dB) because they "
        f"remove the heart-sound fundamental but not the broadband noise between beats; a narrower low-pass makes it "
        f"slightly better (40–200 Hz: {narrow['between_to_heart_a_weighted_db_mean']:.1f} dB).",
        f"- **Transients:** 4th-order Chebyshev I and elliptic sections at 40–60 Hz have the longest ringing and "
        f"group-delay spread (up to {max(record['group_delay_variation_40_400hz_ms'] for record in filtered):.0f} ms "
        f"across 40–400 Hz); Bessel and 2nd-order Butterworth the shortest. Whether that smears S1/S2 audibly is for "
        f"listening.",
    ]
    return "\n".join(lines)


SHORTLIST_REASONS = {candidate_from_entry(entry).identifier: reason for entry, reason in SHORTLIST_ENTRIES}


def main() -> None:
    LISTENING_DIRECTORY.mkdir(exist_ok=True)
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    grid = candidate_grid()
    worker_count = max(1, min(12, (os.cpu_count() or 2) - 2))
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(analyse_candidate, grid, chunksize=4))
    results_by_identifier = {result["identifier"]: result for result in results}
    rows = [row for result in results for row in result["rows"]]
    write_csv(LISTENING_DIRECTORY / "metrics.csv", rows, METRIC_COLUMNS)
    summary = summarise(results)
    write_csv(LISTENING_DIRECTORY / "metrics_summary.csv", summary, summary_columns(summary))
    write_shortlist()
    shortlist_identifiers = [entry["identifier"] for entry in
                             json.loads((LISTENING_DIRECTORY / "shortlist.json").read_text(encoding="utf-8"))["candidates"]]
    by_identifier = {record["identifier"]: record for record in summary}
    missing = [identifier for identifier in shortlist_identifiers if identifier not in by_identifier]
    for identifier in missing:
        entry = next(candidate for candidate in json.loads((LISTENING_DIRECTORY / "shortlist.json").read_text(
            encoding="utf-8"))["candidates"] if candidate["identifier"] == identifier)
        entry = {key: value for key, value in entry.items() if key not in ("identifier", "label")}
        extra = analyse_candidate(entry)
        results_by_identifier[extra["identifier"]] = extra
        summary.extend(summarise([results_by_identifier["raw"], extra])[1:])
        by_identifier = {record["identifier"]: record for record in summary}
    shortlist = [by_identifier[identifier] for identifier in shortlist_identifiers]
    sources = {name: recording_context(name)["segments"]["source"] for name in RECORDING_NAMES}
    segment_sources = (next(iter(sources.values())) + " for all recordings" if len(set(sources.values())) == 1
                       else "; ".join(f"{name}: {source}" for name, source in sources.items()))
    write_summary_markdown(summary, shortlist, results_by_identifier, segment_sources)
    common.apply_dark_style()
    from matplotlib import pyplot
    figure_spectra(pyplot)
    figure_headroom(pyplot, summary)
    figure_loudness_cleanliness(pyplot, summary, shortlist)
    figure_responses(pyplot, shortlist, results_by_identifier)
    figure_waveforms(pyplot, shortlist, results_by_identifier)
    print(f"{len(summary)} candidates, segments: {segment_sources}")


if __name__ == "__main__":
    main()
