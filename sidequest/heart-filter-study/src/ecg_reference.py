"""ECG heart-rate reference for the EPHNOGRAM records, independent of the heart sound.

Two offline R-peak detectors on different principles find beats in the ECG channel; per 8 s
window (one per second, as in reference_beats.py) the rate from each detector is stored and the
window is marked reliable only if both agree and the beat sequence is physiologically plausible.

Usage:
    .venv/Scripts/python.exe -I src/ecg_reference.py [--workers N] [--records ECGPCG0003 ...] [--force]
"""

import sys
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE_DIRECTORY))

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import matplotlib
import numpy as np
from scipy import ndimage, signal

from hfs import ephnogram

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

STUDY_DIRECTORY = SOURCE_DIRECTORY.parent
OUTPUT_DIRECTORY = STUDY_DIRECTORY / "reference-public" / "ephnogram"
FIGURE_DIRECTORY = OUTPUT_DIRECTORY / "figures"
ANALYSIS_RATE_HZ = 1000
WINDOW_SECONDS = 8.0
MINIMUM_INTERVAL_S = 60.0 / 220.0
MAXIMUM_INTERVAL_S = 60.0 / 30.0
PEAK_DISTANCE_S = 0.25
PAN_TOMPKINS_LOW_HZ = 10.0
PAN_TOMPKINS_HIGH_HZ = 25.0
DETECTOR_AGREEMENT_LIMIT_BPM = 2.0
BEAT_MATCH_TOLERANCE_S = 0.050
INTERVAL_JUMP_HIGH = 1.4
INTERVAL_JUMP_LOW = 0.7
EDGE_GAP_LIMIT = 1.3
LIMIT_RUN_SAMPLES = 8
FLAT_AMPLITUDE_RATIO = 0.1
TEMPLATE_BLOCK_S = 60.0
TEMPLATE_HALF_WIDTH_S = 0.060
HEART_RATE_BANDS = [(0, 70), (70, 90), (90, 110), (110, 130), (130, 150), (150, 170), (170, 1000)]
DETECTOR_NAMES = ["detector_1_pan_tompkins", "detector_2_wavelet_template"]
DETECTOR_DESCRIPTIONS = {
    DETECTOR_NAMES[0]: (
        "Pan-Tompkins style, zero-phase: 10-25 Hz band-pass (above the classic 5-15 Hz because tall exercise T waves dominated that band), derivative, squaring, centred 150 ms "
        "moving integration. Peaks at least 0.25 s apart above noise + 0.25 x (beat level - noise), "
        "with beat level the 10 s running median of 2 s maxima and noise the 10 s running median. "
        "Search-back for gaps over 1.66 x the local median interval at half threshold; a peak less "
        "than 0.36 s after a beat with under half its maximum slope is dropped as a T wave."
    ),
    DETECTOR_NAMES[1]: (
        "Wavelet and matched template: geometric mean of the Mexican-hat wavelet moduli at 6, 10 "
        "and 16 ms scales gives QRS candidates; the strongest candidates of each 60 s block form a "
        "median QRS template (+-60 ms, 5-40 Hz ECG). Beats are peaks of the normalised "
        "cross-correlation with that template above 0.6, at least 0.25 s apart, whose wavelet "
        "product within +-30 ms reaches 0.3 x the median of the template beats (rejects T waves, "
        "which match in shape but lack fine-scale energy), with search-back down to correlation "
        "0.35 and wavelet ratio 0.2 for gaps over 1.6 x the local median interval."
    ),
}
REFINEMENT_HALF_WIDTH_S = 0.075
REFINEMENT_DESCRIPTION = (
    "Each detection is refined to the local maximum, within +-75 ms, of the 5-40 Hz zero-phase "
    "band-passed ECG at 1 kHz multiplied by the dominant QRS sign of its 60 s block (sign of the "
    "skewness of that signal, computed independently of both detectors and shared by them), with "
    "parabolic interpolation."
)


def band_pass(samples, low_hz, high_hz, sample_rate_hz, order=2):
    sections = signal.butter(order, [low_hz, high_hz], "bandpass", fs=sample_rate_hz, output="sos")
    return signal.sosfiltfilt(sections, samples)


def parabolic_offset(left, centre, right):
    denominator = left - 2.0 * centre + right
    if denominator >= 0:
        return 0.0
    return float(np.clip(0.5 * (left - right) / denominator, -0.5, 0.5))


def running_median_on_grid(values, grid_step, window_length):
    """Median filter of a decimated copy, interpolated back; full-rate median filters are too slow."""
    coarse = values[::grid_step]
    filtered = ndimage.median_filter(coarse, size=max(1, window_length // grid_step), mode="nearest")
    return np.interp(np.arange(len(values)), np.arange(len(coarse)) * grid_step, filtered)


def local_median_intervals(beat_samples, neighbours=8):
    intervals = np.diff(beat_samples).astype(float)
    if len(intervals) == 0:
        return intervals
    padded = np.pad(intervals, neighbours // 2, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, neighbours + 1)
    return np.median(windows, axis=1)[: len(intervals)]


def search_back(beats, candidates, candidate_heights, threshold_at, gap_factor, minimum_height_factor):
    beats = sorted(beats)
    minimum_distance = int(PEAK_DISTANCE_S * ANALYSIS_RATE_HZ)
    for _ in range(3):
        if len(beats) < 3:
            return np.array(beats, dtype=int)
        local = local_median_intervals(np.array(beats))
        additions = []
        for index in range(len(beats) - 1):
            if beats[index + 1] - beats[index] <= gap_factor * local[index]:
                continue
            inside = (candidates > beats[index] + minimum_distance) & (candidates < beats[index + 1] - minimum_distance)
            if not np.any(inside):
                continue
            chosen = np.nonzero(inside)[0][np.argmax(candidate_heights[inside])]
            if candidate_heights[chosen] >= minimum_height_factor * threshold_at(candidates[chosen]):
                additions.append(int(candidates[chosen]))
        if not additions:
            break
        beats = sorted(set(beats) | set(additions))
    return np.array(beats, dtype=int)


def refine_to_local_maximum(detections, oriented_ecg, half_width_s):
    half_width = int(half_width_s * ANALYSIS_RATE_HZ)
    refined = []
    for detection in detections:
        start = max(detection - half_width, 1)
        end = min(detection + half_width + 1, len(oriented_ecg) - 1)
        if end <= start:
            continue
        peak = start + int(np.argmax(oriented_ecg[start:end]))
        offset = parabolic_offset(*oriented_ecg[peak - 1 : peak + 2]) if 0 < peak < len(oriented_ecg) - 1 else 0.0
        refined.append((peak + offset) / ANALYSIS_RATE_HZ)
    refined = np.unique(np.round(np.array(refined), 4))
    if len(refined) > 1:
        keep = np.concatenate([[True], np.diff(refined) >= MINIMUM_INTERVAL_S * 0.9])
        refined = refined[keep]
    return refined


def block_polarity(refinement_ecg):
    """Dominant QRS sign per 60 s block from the skewness of the 5-40 Hz ECG, where the QRS
    dominates the T wave. Shared by both detectors so that they mark the same fiducial point."""
    block = int(TEMPLATE_BLOCK_S * ANALYSIS_RATE_HZ)
    polarity = np.ones(len(refinement_ecg))
    for block_start in range(0, len(refinement_ecg), block):
        segment = refinement_ecg[block_start : block_start + block]
        centred = segment - segment.mean()
        skewness = np.mean(centred ** 3) / max(np.mean(centred ** 2) ** 1.5, 1e-30)
        polarity[block_start : block_start + block] = 1.0 if skewness >= 0 else -1.0
    return polarity


def detector_1_pan_tompkins(ecg, oriented_ecg):
    sample_rate = ANALYSIS_RATE_HZ
    band = band_pass(ecg, PAN_TOMPKINS_LOW_HZ, PAN_TOMPKINS_HIGH_HZ, sample_rate)
    slope = np.gradient(band)
    integrated = ndimage.uniform_filter1d(slope ** 2, int(0.150 * sample_rate))
    candidates, properties = signal.find_peaks(integrated, distance=int(PEAK_DISTANCE_S * sample_rate), height=0.0)
    heights = properties["peak_heights"]
    beat_level = running_median_on_grid(ndimage.maximum_filter1d(integrated, 2 * sample_rate), 100, 10 * sample_rate)
    noise_level = running_median_on_grid(integrated, 100, 10 * sample_rate)
    threshold = noise_level + 0.25 * (beat_level - noise_level)
    accepted = candidates[heights > threshold[candidates]]
    beats = search_back(list(accepted), candidates, heights, lambda position: threshold[position], 1.66, 0.5)
    absolute_slope = np.abs(slope)
    slope_window = int(0.075 * sample_rate)
    maximum_slope = np.array([absolute_slope[max(b - slope_window, 0) : b + slope_window].max() for b in beats]) if len(beats) else np.array([])
    kept = []
    for index, beat in enumerate(beats):
        if kept and beat - kept[-1][0] < 0.36 * sample_rate and maximum_slope[index] < 0.5 * kept[-1][1]:
            continue
        kept.append((beat, maximum_slope[index]))
    positions = np.array([beat for beat, _ in kept], dtype=int)
    return refine_to_local_maximum(positions, oriented_ecg, REFINEMENT_HALF_WIDTH_S)


def ricker_response(samples, width_s):
    width = width_s * ANALYSIS_RATE_HZ
    support = np.arange(-int(5 * width), int(5 * width) + 1)
    wavelet = (1.0 - (support / width) ** 2) * np.exp(-0.5 * (support / width) ** 2)
    wavelet -= wavelet.mean()
    return signal.fftconvolve(samples, wavelet / np.sqrt(width), mode="same")


def normalised_cross_correlation(samples, template):
    template = template - template.mean()
    template_norm = np.linalg.norm(template)
    length = len(template)
    if template_norm == 0 or len(samples) < length:
        return np.zeros(len(samples))
    numerator = signal.fftconvolve(samples, template[::-1], mode="valid")
    cumulative = np.concatenate([[0.0], np.cumsum(samples)])
    cumulative_squares = np.concatenate([[0.0], np.cumsum(samples ** 2)])
    window_sum = cumulative[length:] - cumulative[:-length]
    window_square_sum = cumulative_squares[length:] - cumulative_squares[:-length]
    energy = np.maximum(window_square_sum - window_sum ** 2 / length, 1e-30)
    correlation = numerator / (np.sqrt(energy) * template_norm)
    result = np.zeros(len(samples))
    result[length // 2 : length // 2 + len(correlation)] = correlation
    return result


def detector_2_wavelet_template(ecg, oriented_ecg):
    sample_rate = ANALYSIS_RATE_HZ
    centred = ecg - ndimage.uniform_filter1d(ecg, int(0.3 * sample_rate))
    product = np.ones(len(ecg))
    for width_s in (0.006, 0.010, 0.016):
        product *= np.abs(ricker_response(centred, width_s))
    multiscale = ndimage.uniform_filter1d(np.cbrt(product), int(0.020 * sample_rate))
    candidates, properties = signal.find_peaks(multiscale, distance=int(PEAK_DISTANCE_S * sample_rate), height=0.0)
    heights = properties["peak_heights"]
    template_ecg = band_pass(ecg, 5.0, 40.0, sample_rate)
    half_width = int(TEMPLATE_HALF_WIDTH_S * sample_rate)
    block = int(TEMPLATE_BLOCK_S * sample_rate)
    correlation = np.zeros(len(ecg))
    wavelet_ratio = np.zeros(len(ecg))
    local_wavelet_maximum = ndimage.maximum_filter1d(multiscale, int(0.060 * sample_rate))
    for block_start in range(0, len(ecg), block):
        block_end = min(block_start + block, len(ecg))
        in_block = (candidates >= block_start + half_width) & (candidates < block_end - half_width)
        if np.count_nonzero(in_block) < 3:
            continue
        block_candidates, block_heights = candidates[in_block], heights[in_block]
        strong = block_candidates[block_heights >= np.percentile(block_heights, 50)]
        segments = []
        for position in strong:
            segment = template_ecg[position - half_width : position + half_width + 1]
            alignment = int(np.argmax(np.abs(segment[half_width // 2 : -half_width // 2]))) + half_width // 2 - half_width
            aligned = position + alignment
            if aligned - half_width >= 0 and aligned + half_width + 1 <= len(template_ecg):
                segments.append(template_ecg[aligned - half_width : aligned + half_width + 1])
        if len(segments) < 3:
            continue
        template = np.median(np.array(segments), axis=0)
        margin_start = max(block_start - half_width * 2, 0)
        margin_end = min(block_end + half_width * 2, len(ecg))
        block_correlation = normalised_cross_correlation(template_ecg[margin_start:margin_end], template)
        correlation[block_start:block_end] = block_correlation[block_start - margin_start : block_end - margin_start]
        wavelet_ratio[block_start:block_end] = local_wavelet_maximum[block_start:block_end] / np.median(multiscale[strong])
    peaks, peak_properties = signal.find_peaks(correlation, distance=int(PEAK_DISTANCE_S * sample_rate), height=0.0)
    peak_heights = peak_properties["peak_heights"]
    accepted = peaks[(peak_heights >= 0.6) & (wavelet_ratio[peaks] >= 0.3)]
    plausible = wavelet_ratio[peaks] >= 0.2
    beats = search_back(list(accepted), peaks[plausible], peak_heights[plausible], lambda position: 0.6, 1.6, 0.35 / 0.6)
    return refine_to_local_maximum(beats, oriented_ecg, REFINEMENT_HALF_WIDTH_S)


def window_rate(beat_times, window_start, window_end):
    inside = beat_times[(beat_times >= window_start) & (beat_times <= window_end)]
    if len(inside) < 2:
        return None, inside
    return 60.0 * (len(inside) - 1) / (inside[-1] - inside[0]), inside


def rounded(value, digits=4):
    return None if value is None else round(float(value), digits)


def unmatched_mask(beats, other_beats):
    if len(other_beats) == 0:
        return np.ones(len(beats), dtype=bool)
    index = np.clip(np.searchsorted(other_beats, beats), 1, len(other_beats) - 1)
    nearest = np.minimum(np.abs(other_beats[index] - beats), np.abs(other_beats[index - 1] - beats))
    return nearest > BEAT_MATCH_TOLERANCE_S


def saturation_intervals(ecg_full_rate, sample_rate_hz, digital_limits):
    """Runs of samples at the 16-bit limits. Every record reaches both limits once (peak
    normalisation to -32767..32767) and the coarse quantisation leaves plateaus of 2-4 identical
    samples at that peak, so only runs of at least 1 ms count as saturation. Runs of identical
    values elsewhere are not used: the ECG is coarsely quantised and repeats values on the baseline."""
    least_significant_bit = (digital_limits[1] - digital_limits[0]) / 65535.0
    at_limit = (ecg_full_rate <= digital_limits[0] + 1.5 * least_significant_bit) | (
        ecg_full_rate >= digital_limits[1] - 1.5 * least_significant_bit
    )
    flagged_seconds = set()
    edges = np.diff(np.concatenate([[0], at_limit.astype(np.int8), [0]]))
    for start, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if end - start >= LIMIT_RUN_SAMPLES:
            flagged_seconds.update(range(int(start / sample_rate_hz), int(end / sample_rate_hz) + 1))
    return flagged_seconds, int(np.count_nonzero(at_limit))


def analyse_record(record_name):
    record = ephnogram.load_record(record_name)
    sample_rate_hz = record.sample_rate_hz
    decimation = int(round(sample_rate_hz / ANALYSIS_RATE_HZ))
    if abs(sample_rate_hz / decimation - ANALYSIS_RATE_HZ) > 1e-6:
        raise ValueError(f"{record_name}: sample rate {sample_rate_hz} Hz is not a multiple of {ANALYSIS_RATE_HZ} Hz")
    saturated_seconds, saturated_sample_count = saturation_intervals(record.ecg, sample_rate_hz, record.ecg_digital_limits_physical)
    ecg = signal.resample_poly(record.ecg - np.median(record.ecg), 1, decimation)
    duration_s = len(record.ecg) / sample_rate_hz
    del record
    refinement_ecg = band_pass(ecg, 5.0, 40.0, ANALYSIS_RATE_HZ)
    polarity = block_polarity(refinement_ecg)
    oriented_ecg = polarity * refinement_ecg
    beats_1 = detector_1_pan_tompkins(ecg, oriented_ecg)
    beats_2 = detector_2_wavelet_template(ecg, oriented_ecg)
    polarity_blocks = polarity[:: int(TEMPLATE_BLOCK_S * ANALYSIS_RATE_HZ)]

    amplitude_band = band_pass(ecg, 5.0, 15.0, ANALYSIS_RATE_HZ)
    second_count = int(np.floor(duration_s))
    second_standard_deviation = np.array(
        [np.std(amplitude_band[second * ANALYSIS_RATE_HZ : (second + 1) * ANALYSIS_RATE_HZ]) for second in range(second_count)]
    )
    flat_reference = np.median(second_standard_deviation) if second_count else 0.0

    unmatched_1 = unmatched_mask(beats_1, beats_2)
    unmatched_2 = unmatched_mask(beats_2, beats_1)
    windows = []
    for end in range(int(WINDOW_SECONDS), second_count + 1):
        start = end - WINDOW_SECONDS
        rate_1, inside_1 = window_rate(beats_1, start, end)
        rate_2, inside_2 = window_rate(beats_2, start, end)
        per_detector = {DETECTOR_NAMES[0]: rounded(rate_1, 2), DETECTOR_NAMES[1]: rounded(rate_2, 2)}
        difference = None if rate_1 is None or rate_2 is None else rate_1 - rate_2
        reference_bpm = None if difference is None else 0.5 * (rate_1 + rate_2)
        reasons = []
        if difference is None:
            reasons.append("a detector has fewer than two beats")
        elif abs(difference) > DETECTOR_AGREEMENT_LIMIT_BPM:
            reasons.append(f"detectors disagree by {abs(difference):.1f} BPM")
        in_window_1 = (beats_1 >= start) & (beats_1 <= end)
        in_window_2 = (beats_2 >= start) & (beats_2 <= end)
        unmatched_count = int(np.count_nonzero(unmatched_1 & in_window_1) + np.count_nonzero(unmatched_2 & in_window_2))
        if unmatched_count:
            reasons.append(f"{unmatched_count} beats found by one detector only")
        rates_inside = np.array([])
        if len(inside_1) >= 2:
            intervals = np.diff(inside_1)
            rates_inside = 60.0 / intervals
            median_interval = float(np.median(intervals))
            if np.any(intervals < MINIMUM_INTERVAL_S) or np.any(intervals > MAXIMUM_INTERVAL_S):
                reasons.append("interval outside 0.27-2.0 s")
            if np.any(intervals > INTERVAL_JUMP_HIGH * median_interval) or np.any(intervals < INTERVAL_JUMP_LOW * median_interval):
                reasons.append("interval jump (missed or extra beat)")
            if inside_1[0] - start > EDGE_GAP_LIMIT * median_interval or end - inside_1[-1] > EDGE_GAP_LIMIT * median_interval:
                reasons.append("missing beat at window edge")
        window_seconds = range(int(start), end)
        if any(second in saturated_seconds for second in window_seconds):
            reasons.append("ECG saturated")
        if flat_reference > 0 and np.any(second_standard_deviation[int(start) : end] < FLAT_AMPLITUDE_RATIO * flat_reference):
            reasons.append("ECG flat")
        windows.append({
            "end_time_s": end,
            "reference_bpm": rounded(reference_bpm, 2),
            "reference_bpm_per_method": per_detector,
            "method_spread_bpm": rounded(None if difference is None else abs(difference), 2),
            "detector_difference_bpm": rounded(difference, 2),
            "beats_in_window": int(len(inside_1)),
            "rate_change_in_window_bpm": rounded(float(rates_inside.max() - rates_inside.min()), 2) if len(rates_inside) else None,
            "reliable": not reasons,
            "unreliable_reason": "; ".join(reasons) if reasons else None,
        })

    matched_1 = beats_1[~unmatched_1]
    if len(matched_1) and len(beats_2):
        index = np.clip(np.searchsorted(beats_2, matched_1), 1, len(beats_2) - 1)
        nearest = np.where(np.abs(beats_2[index] - matched_1) < np.abs(beats_2[index - 1] - matched_1), beats_2[index], beats_2[index - 1])
        timing_offsets = nearest - matched_1
    else:
        timing_offsets = np.array([])
    return {
        "name": record_name,
        "source": "EPHNOGRAM 1.0.0, PhysioNet, DOI 10.13026/tjtq-5911, ODC-By 1.0",
        "sample_rate_hz": float(sample_rate_hz),
        "analysis_rate_hz": ANALYSIS_RATE_HZ,
        "duration_s": duration_s,
        "discarded_seconds": 0.0,
        "beat_mark": "ECG R peak: " + REFINEMENT_DESCRIPTION,
        "window_definition": (
            "8 s windows ending at every whole second from 8 s (file start = 0 s); rate = 60 x (beats in "
            "window - 1) / (last - first beat time); reference_bpm = mean of the two detector rates"
        ),
        "reliable_definition": (
            f"detectors agree within {DETECTOR_AGREEMENT_LIMIT_BPM} BPM; every beat of both detectors in the "
            f"window matched by the other within {BEAT_MATCH_TOLERANCE_S * 1000:.0f} ms; all intervals 0.27-2.0 s; "
            f"no interval above {INTERVAL_JUMP_HIGH} x or below {INTERVAL_JUMP_LOW} x the window median; no gap "
            f"over {EDGE_GAP_LIMIT} x median at the window edges; no run of {LIMIT_RUN_SAMPLES} ECG samples at the "
            f"16-bit limits (within 1.5 LSB); no second whose 5-15 Hz ECG standard deviation is below "
            f"{FLAT_AMPLITUDE_RATIO} x the record median"
        ),
        "info": {
            "subject_id": ephnogram.record_info(record_name).subject_id,
            "scenario": ephnogram.record_info(record_name).scenario,
            "ecg_quality": ephnogram.record_info(record_name).ecg_quality,
            "pcg_quality": ephnogram.record_info(record_name).pcg_quality,
        },
        "ecg_saturated_sample_count": saturated_sample_count,
        "beat_times_s": [rounded(time) for time in beats_1],
        "methods": {
            DETECTOR_NAMES[0]: {"beat_times_s": [rounded(time) for time in beats_1],
                                "description": DETECTOR_DESCRIPTIONS[DETECTOR_NAMES[0]]},
            DETECTOR_NAMES[1]: {"beat_times_s": [rounded(time) for time in beats_2],
                                "description": DETECTOR_DESCRIPTIONS[DETECTOR_NAMES[1]]},
        },
        "qrs_polarity_per_60_s_block": [int(value) for value in polarity_blocks],
        "agreement": {
            "beats_detector_1": int(len(beats_1)),
            "beats_detector_2": int(len(beats_2)),
            "matched_beats": int(len(matched_1)),
            "unmatched_detector_1": int(np.count_nonzero(unmatched_1)),
            "unmatched_detector_2": int(np.count_nonzero(unmatched_2)),
            "median_timing_offset_ms": rounded(np.median(timing_offsets) * 1000, 2) if len(timing_offsets) else None,
            "timing_offset_95th_percentile_absolute_ms": rounded(np.percentile(np.abs(timing_offsets), 95) * 1000, 2) if len(timing_offsets) else None,
        },
        "windows": windows,
    }


def plot_record(result):
    record = ephnogram.load_record(result["name"])
    sample_rate_hz = record.sample_rate_hz
    ecg = record.ecg - np.median(record.ecg)
    del record
    windows = result["windows"]
    beats_1 = np.array(result["methods"][DETECTOR_NAMES[0]]["beat_times_s"])
    beats_2 = np.array(result["methods"][DETECTOR_NAMES[1]]["beat_times_s"])
    reliable_rates = [(window["reference_bpm"], window["end_time_s"]) for window in windows if window["reliable"]]
    candidates = reliable_rates or [(window["reference_bpm"] or 0, window["end_time_s"]) for window in windows]
    highest_end = max(candidates)[1] if candidates else WINDOW_SECONDS
    excerpt_ends = [min(10.0, result["duration_s"]), float(highest_end)]

    plt.style.use("dark_background")
    figure = plt.figure(figsize=(13, 9), facecolor="#111418")
    grid = figure.add_gridspec(3, 1, height_ratios=[1, 1, 1.2], hspace=0.45)
    titles = ["ECG excerpt at the start", "ECG excerpt: 8 s window with the highest reference rate"]
    for row, excerpt_end in enumerate(excerpt_ends):
        axis = figure.add_subplot(grid[row])
        excerpt_start = max(excerpt_end - WINDOW_SECONDS, 0.0)
        first, last = int(excerpt_start * sample_rate_hz), int(excerpt_end * sample_rate_hz)
        time = np.arange(first, last) / sample_rate_hz
        segment = ecg[first:last]
        filtered = band_pass(segment, 0.5, 40.0, sample_rate_hz) if len(segment) > 100 else segment
        axis.plot(time, filtered, color="#d0d6de", linewidth=0.7, label="ECG 0.5-40 Hz")
        for beats, colour, marker, label in [(beats_1, "#ffb454", "v", "detector 1 (Pan-Tompkins)"),
                                             (beats_2, "#59c2ff", "^", "detector 2 (wavelet + template)")]:
            shown = beats[(beats >= excerpt_start) & (beats <= excerpt_end)]
            values = np.interp(shown, time, filtered) if len(shown) else []
            axis.plot(shown, values, linestyle="none", marker=marker, color=colour, markersize=7, label=label)
        axis.set_title(f"{titles[row]} ({excerpt_start:.0f}-{excerpt_end:.0f} s)", fontsize=10)
        axis.set_xlabel("time from record start (s)")
        axis.set_ylabel("ECG (header units)")
        axis.legend(loc="upper right", fontsize=8)
    rate_axis = figure.add_subplot(grid[2])
    ends = np.array([window["end_time_s"] for window in windows])
    for name, colour in zip(DETECTOR_NAMES, ("#ffb454", "#59c2ff")):
        values = np.array([np.nan if window["reference_bpm_per_method"][name] is None else window["reference_bpm_per_method"][name] for window in windows])
        rate_axis.plot(ends, values, color=colour, linewidth=0.9, label=name.replace("_", " "))
    unreliable = np.array([not window["reliable"] for window in windows])
    if len(ends):
        lower, upper = rate_axis.get_ylim()
        rate_axis.fill_between(ends, lower, upper, where=unreliable, color="#ff5c5c", alpha=0.18, step="mid", linewidth=0, label="unreliable window")
        rate_axis.set_ylim(lower, upper)
    rate_axis.set_xlabel("8 s window end time (s)")
    rate_axis.set_ylabel("heart rate (BPM)")
    rate_axis.legend(loc="upper left", fontsize=8)
    info = result["info"]
    reliable_share = 100.0 * sum(window["reliable"] for window in windows) / max(len(windows), 1)
    figure.suptitle(f"{result['name']} | {info['subject_id']} | {info['scenario']} | ECG note: {info['ecg_quality']} | "
                    f"reliable windows {reliable_share:.0f} %", fontsize=10)
    FIGURE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_DIRECTORY / f"{result['name']}.png", dpi=110, facecolor=figure.get_facecolor())
    plt.close(figure)


def is_current(record_name):
    output = OUTPUT_DIRECTORY / f"{record_name}.json"
    figure = FIGURE_DIRECTORY / f"{record_name}.png"
    if not output.exists() or not figure.exists():
        return False
    dependencies = [Path(__file__), Path(ephnogram.__file__),
                    ephnogram.WFDB_DIRECTORY / f"{record_name}.dat", ephnogram.WFDB_DIRECTORY / f"{record_name}.hea"]
    newest = max(path.stat().st_mtime for path in dependencies)
    return output.stat().st_mtime > newest and figure.stat().st_mtime > newest


def process_record(record_name):
    result = analyse_record(record_name)
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_DIRECTORY / f"{record_name}.json.tmp"
    temporary.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    plot_record(result)
    temporary.replace(OUTPUT_DIRECTORY / f"{record_name}.json")
    reliable = sum(window["reliable"] for window in result["windows"])
    return f"{record_name}: {result['agreement']['beats_detector_1']} / {result['agreement']['beats_detector_2']} beats, {reliable}/{len(result['windows'])} reliable windows"


def band_label(low, high):
    if low == 0:
        return f"<{high}"
    if high >= 1000:
        return f">{low}"
    return f"{low}-{high}"


def write_summary(all_records):
    results = []
    for info in all_records:
        path = OUTPUT_DIRECTORY / f"{info.record_name}.json"
        if path.exists():
            results.append(json.loads(path.read_text(encoding="utf-8")))
    housekeeping = {info.record_name: info.housekeeping_note for info in all_records}
    duplicate_groups = ephnogram.duplicate_signal_groups()
    excluded = set()
    for group in duplicate_groups:
        replaced = [name for name in group if housekeeping.get(name, "").startswith("Replaced")]
        excluded.update(replaced if len(replaced) < len(group) else group[1:])
    all_results = results
    results = [result for result in all_results if result["name"] not in excluded]
    lines = [
        "# EPHNOGRAM ECG heart-rate reference",
        "",
        "Source: EPHNOGRAM v1.0.0 (PhysioNet), DOI 10.13026/tjtq-5911, Open Data Commons Attribution "
        "License v1.0. Generated by `src/ecg_reference.py` from the ECG channel only.",
        "",
        "## Method",
        "",
        f"- Detector 1: {DETECTOR_DESCRIPTIONS[DETECTOR_NAMES[0]]}",
        f"- Detector 2: {DETECTOR_DESCRIPTIONS[DETECTOR_NAMES[1]]}",
        f"- Refinement: {REFINEMENT_DESCRIPTION}",
        "- Windows as in run 1 (`src/reference_beats.py`): 8 s, one ending at every whole second, rate = "
        "60 x (beats - 1) / (last - first beat time). Time zero is the record start (nothing discarded), "
        "so the first window ends at 8 s. `reference_bpm` is the mean of both detector rates.",
        f"- Reliable window: {results[0]['reliable_definition'] if results else ''}.",
        "",
        f"Records processed: {len(all_results)} of {len(all_records)} listed in the spreadsheet.",
        "",
    ]
    if duplicate_groups:
        lines += [
            "## Duplicate signals",
            "",
            "These records have identical ECG and PCG header lines (ADC gain, baseline, initial value and "
            "checksum), so they hold the same signal under different record names, subject IDs and "
            "scenarios: " + "; ".join(
                " = ".join(f"{name} ({next((info.subject_id for info in all_records if info.record_name == name), '?')}, "
                           f"{housekeeping.get(name) or 'no housekeeping note'})" for name in group)
                for group in duplicate_groups) + ". "
            "Which labels are correct is unverified. The copy whose spreadsheet housekeeping note says "
            f"\"Replaced file\" ({', '.join(sorted(excluded))}) is left out of the agreement statistics, "
            "the band table and the subject counts; it still has its own JSON and row below.",
            "",
        ]
    total_beats_1 = sum(result["agreement"]["beats_detector_1"] for result in results)
    total_beats_2 = sum(result["agreement"]["beats_detector_2"] for result in results)
    total_matched = sum(result["agreement"]["matched_beats"] for result in results)
    all_windows = [window for result in results for window in result["windows"]]
    differences = np.array([abs(window["detector_difference_bpm"]) for window in all_windows if window["detector_difference_bpm"] is not None])
    reliable_windows = [window for window in all_windows if window["reliable"]]
    lines += ["## Detector agreement", ""]
    if results:
        lines += [
            f"- Beats: detector 1 {total_beats_1}, detector 2 {total_beats_2}, matched within "
            f"{BEAT_MATCH_TOLERANCE_S * 1000:.0f} ms {total_matched} "
            f"({100 * total_matched / max(total_beats_1, 1):.2f} % of detector 1, {100 * total_matched / max(total_beats_2, 1):.2f} % of detector 2).",
            f"- Windows: {len(all_windows)}; absolute rate difference median {np.median(differences):.3f} BPM, "
            f"95th percentile {np.percentile(differences, 95):.2f} BPM; within 2 BPM {100 * np.mean(differences <= 2):.1f} %.",
            f"- Reliable windows: {len(reliable_windows)} ({100 * len(reliable_windows) / max(len(all_windows), 1):.1f} %).",
            "",
        ]
    reason_counts = {}
    for window in all_windows:
        if window["unreliable_reason"]:
            for reason in window["unreliable_reason"].split("; "):
                key = reason.split(" by ")[0] if reason.startswith("detectors disagree") else (
                    "beats found by one detector only" if reason.endswith("one detector only") else reason)
                reason_counts[key] = reason_counts.get(key, 0) + 1
    if reason_counts:
        lines += ["Unreliable-window reasons (a window can have several): " +
                  "; ".join(f"{reason}: {count}" for reason, count in sorted(reason_counts.items(), key=lambda item: -item[1])), ""]

    lines += ["## Reliable windows per heart-rate band", "",
              "| Band (BPM) | Reliable windows | Subjects | Records |", "|---|---:|---:|---:|"]
    for low, high in HEART_RATE_BANDS:
        windows_in_band, subjects, records = 0, set(), set()
        for result in results:
            count = sum(1 for window in result["windows"] if window["reliable"] and low <= window["reference_bpm"] < high)
            if count:
                windows_in_band += count
                subjects.add(result["info"]["subject_id"])
                records.add(result["name"])
        lines.append(f"| {band_label(low, high)} | {windows_in_band} | {len(subjects)} | {len(records)} |")
    lines += ["", "## Per record", "",
              "| Record | Subject | Scenario | Duration (s) | Spreadsheet ECG note | Reliable windows | "
              "HR 5th-95th pct (BPM) | HR min-max (BPM) | Beats det. 1 / det. 2 / matched |",
              "|---|---|---|---:|---|---:|---|---|---|"]
    for result in all_results:
        rates = np.array([window["reference_bpm"] for window in result["windows"] if window["reliable"]])
        share = 100 * len(rates) / max(len(result["windows"]), 1)
        percentile_text = f"{np.percentile(rates, 5):.1f}-{np.percentile(rates, 95):.1f}" if len(rates) else "-"
        range_text = f"{rates.min():.1f}-{rates.max():.1f}" if len(rates) else "-"
        agreement = result["agreement"]
        info = result["info"]
        lines.append(
            f"| {result['name']}{' (duplicate, excluded)' if result['name'] in excluded else ''} | {info['subject_id']} | {info['scenario']} | {result['duration_s']:.0f} | "
            f"{info['ecg_quality']} | {len(rates)}/{len(result['windows'])} ({share:.0f} %) | {percentile_text} | "
            f"{range_text} | {agreement['beats_detector_1']} / {agreement['beats_detector_2']} / {agreement['matched_beats']} |"
        )
    missing = [info.record_name for info in all_records if not (OUTPUT_DIRECTORY / f"{info.record_name}.json").exists()]
    if missing:
        lines += ["", f"Not processed (signal file not downloaded or verified yet): {', '.join(missing)}."]
    lines += ["", "Figures: `figures/<record>.png` (ECG excerpts with both detectors' R peaks; rates over time, "
              "unreliable windows shaded red).", ""]
    (OUTPUT_DIRECTORY / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workers", type=int, default=max(1, min(4, (os.cpu_count() or 2) // 2)))
    parser.add_argument("--records", nargs="*")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    all_records = ephnogram.list_records()
    selected = [info for info in all_records if info.available and (not arguments.records or info.record_name in arguments.records)]
    pending = [info.record_name for info in selected if arguments.force or not is_current(info.record_name)]
    print(f"{len(selected)} available records, {len(pending)} to process", flush=True)
    with ProcessPoolExecutor(max_workers=arguments.workers) as executor:
        futures = {executor.submit(process_record, name): name for name in pending}
        for future in as_completed(futures):
            try:
                print(future.result(), flush=True)
            except Exception as error:  # noqa: BLE001 - report and continue with the other records
                print(f"{futures[future]}: FAILED {type(error).__name__}: {error}", flush=True)
    write_summary(all_records)
    print(f"summary written to {OUTPUT_DIRECTORY / 'SUMMARY.md'}", flush=True)


if __name__ == "__main__":
    main()
