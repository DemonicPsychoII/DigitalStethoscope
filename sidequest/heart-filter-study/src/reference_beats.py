"""Offline, non-causal reference beat times and heart rates for the heart-filter study recordings.

Three independent methods find heartbeats in each recording; a consensus of at least two methods
gives the final reference beats. Run without arguments to process all recordings.
"""

import json
from pathlib import Path

import matplotlib
import numpy as np
import soundfile
from scipy import ndimage, signal

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

STUDY_DIRECTORY = Path(__file__).resolve().parent.parent
RECORDING_NAMES = ["rest-1", "rest-2", "elevated-1", "elevated-2", "elevated-3"]
DISCARDED_SECONDS = 2.0
RECORDING_SECONDS = 60.0
ENVELOPE_RATE_HZ = 500
FLUX_FRAME_HOP_SAMPLES = 64
MINIMUM_INTERVAL_S = 60.0 / 200.0
MAXIMUM_INTERVAL_S = 60.0 / 40.0
CONSENSUS_TOLERANCE_S = 0.060
INTERVAL_CHANGE_LIMIT = 0.20
METHOD_SPREAD_LIMIT_BPM = 3.0
WINDOW_SECONDS = 8.0
ARTEFACT_FRAME_S = 0.1
ARTEFACT_PADDING_S = 0.1
LOW_BAND_ARTEFACT_RATIO = 2.5
HIGH_BAND_ARTEFACT_RATIO = 15.0
NO_SIGNAL_RATIO = 0.25
BEAT_MARK = (
    "S1 complex energy centroid: centre of mass of the squared 25-150 Hz Hilbert envelope "
    "(20 Hz low-pass) within +-50 ms, iterated from the consensus time; typically 20-40 ms after "
    "S1 onset"
)

METHOD_DESCRIPTIONS = {
    "A_envelope_peak_dynamic_programming": (
        "Peaks of a log-compressed 25-150 Hz Hilbert envelope (zero-phase, 20 Hz low-pass) are "
        "candidates. A whole-recording dynamic programme over pairs of consecutive beats picks the "
        "sequence maximising peak prominence minus a penalty on beat-to-beat interval change; "
        "intervals limited to 0.3-1.5 s. No tempo prior."
    ),
    "B_spectral_flux_tempo_tracking": (
        "Spectral flux of a 20-400 Hz short-time Fourier transform (40 ms Hann, 4 ms hop). "
        "Biased short-time autocorrelation (5 s window) gives a tempogram over 0.3-1.5 s periods; "
        "a Viterbi path enforces period continuity over the whole recording. Beats are placed by "
        "tempo-guided dynamic programming on the flux (Ellis 2007) and refined to the local flux "
        "maximum."
    ),
    "C_cycle_template_matching": (
        "Mean S1+S2 cycle template of the square-root-compressed 25-400 Hz envelope, built per "
        "15 s block from beats where A and B agree. Normalised cross-correlation with the "
        "envelope (amplitude-invariant, so clipping-compressed beats still match); beats are "
        "correlation peaks above 0.45 at least 0.3 s apart."
    ),
}
METHOD_NAMES = list(METHOD_DESCRIPTIONS)


def band_pass(samples, low_hz, high_hz, sample_rate_hz, order=4):
    second_order_sections = signal.butter(
        order, [low_hz, high_hz], "bandpass", fs=sample_rate_hz, output="sos"
    )
    return signal.sosfiltfilt(second_order_sections, samples)


def low_pass(samples, cutoff_hz, sample_rate_hz, order=2):
    second_order_sections = signal.butter(order, cutoff_hz, "lowpass", fs=sample_rate_hz, output="sos")
    return signal.sosfiltfilt(second_order_sections, samples)


def band_envelope(samples, low_hz, high_hz, sample_rate_hz, smoothing_hz):
    band_signal = band_pass(samples, low_hz, high_hz, sample_rate_hz)
    envelope = low_pass(np.abs(signal.hilbert(band_signal)), smoothing_hz, sample_rate_hz)
    decimation = sample_rate_hz // ENVELOPE_RATE_HZ
    return np.maximum(envelope[::decimation], 0.0)


def moving_average(values, length):
    kernel = np.ones(length) / length
    return np.convolve(values, kernel, mode="same")


def parabolic_offset(left, centre, right):
    denominator = left - 2.0 * centre + right
    if denominator >= 0:
        return 0.0
    return float(np.clip(0.5 * (left - right) / denominator, -0.5, 0.5))


def detect_artefact_intervals(samples, sample_rate_hz):
    """Movement and friction artefacts: 100 ms frames whose 3-20 Hz energy (chest-piece motion)
    or 400-2000 Hz energy (rubbing) far exceeds that recording's 90th percentile."""
    frame_length = int(ARTEFACT_FRAME_S * sample_rate_hz)
    frame_count = len(samples) // frame_length
    flagged = np.zeros(frame_count, dtype=bool)
    for (low_hz, high_hz), ratio_limit in [((3, 20), LOW_BAND_ARTEFACT_RATIO), ((400, 2000), HIGH_BAND_ARTEFACT_RATIO)]:
        band_signal = band_pass(samples, low_hz, high_hz, sample_rate_hz)
        frame_rms = np.sqrt(np.mean(band_signal[: frame_count * frame_length].reshape(frame_count, frame_length) ** 2, axis=1))
        flagged |= frame_rms > ratio_limit * np.percentile(frame_rms, 90)
    intervals = []
    for frame_index in np.nonzero(flagged)[0]:
        start = DISCARDED_SECONDS + frame_index * ARTEFACT_FRAME_S - ARTEFACT_PADDING_S
        end = DISCARDED_SECONDS + (frame_index + 1) * ARTEFACT_FRAME_S + ARTEFACT_PADDING_S
        if intervals and start <= intervals[-1][1]:
            intervals[-1][1] = end
        else:
            intervals.append([start, end])
    return [(round(start, 3), round(end, 3)) for start, end in intervals]


def method_a_envelope_peak_dynamic_programming(feature):
    """feature: log-compressed 25-150 Hz envelope at ENVELOPE_RATE_HZ, time zero at DISCARDED_SECONDS."""
    peaks, properties = signal.find_peaks(feature, distance=int(0.08 * ENVELOPE_RATE_HZ), prominence=0.0)
    prominences = properties["prominences"]
    keep = prominences >= 0.1 * np.percentile(prominences, 95)
    peaks, prominences = peaks[keep], prominences[keep]
    strengths = prominences / np.median(np.sort(prominences)[-max(10, len(prominences) // 3) :])
    times = peaks / ENVELOPE_RATE_HZ
    candidate_count = len(times)
    interval_change_penalty = 4.0
    total_duration = len(feature) / ENVELOPE_RATE_HZ

    predecessors = []
    for current in range(candidate_count):
        intervals = times[current] - times[:current]
        predecessors.append(np.nonzero((intervals >= MINIMUM_INTERVAL_S) & (intervals <= MAXIMUM_INTERVAL_S))[0])

    best_score = {}
    best_previous = {}
    for current in range(candidate_count):
        for previous in predecessors[current]:
            interval = times[current] - times[previous]
            if times[previous] <= MAXIMUM_INTERVAL_S:
                score = strengths[previous] + strengths[current]
                origin = None
            else:
                score = -np.inf
                origin = None
            for before in predecessors[previous]:
                state = (before, previous)
                if state not in best_score:
                    continue
                previous_interval = times[previous] - times[before]
                candidate_score = (
                    best_score[state]
                    + strengths[current]
                    - interval_change_penalty * abs(np.log(interval / previous_interval))
                )
                if candidate_score > score:
                    score = candidate_score
                    origin = before
            if np.isfinite(score):
                best_score[(previous, current)] = score
                best_previous[(previous, current)] = origin

    final_states = [state for state in best_score if total_duration - times[state[1]] <= MAXIMUM_INTERVAL_S]
    state = max(final_states, key=lambda candidate: best_score[candidate])
    sequence = [state[1], state[0]]
    while best_previous[state] is not None:
        state = (best_previous[state], state[0])
        sequence.append(state[0])
    beat_indices = np.array(sequence[::-1])
    refined = []
    for peak in peaks[beat_indices]:
        offset = 0.0
        if 0 < peak < len(feature) - 1:
            offset = parabolic_offset(feature[peak - 1], feature[peak], feature[peak + 1])
        refined.append((peak + offset) / ENVELOPE_RATE_HZ)
    return np.array(refined)


def spectral_flux(samples, sample_rate_hz):
    frame_length = int(0.040 * sample_rate_hz)
    frequencies, _, spectrum = signal.stft(
        samples, fs=sample_rate_hz, window="hann", nperseg=frame_length,
        noverlap=frame_length - FLUX_FRAME_HOP_SAMPLES, boundary="even", padded=True,
    )
    selected = (frequencies >= 20) & (frequencies <= 400)
    magnitude = np.abs(spectrum[selected])
    log_magnitude = np.log1p(magnitude / np.median(magnitude))
    flux = np.sum(np.maximum(np.diff(log_magnitude, axis=1), 0.0), axis=0)
    flux = np.concatenate([[0.0], flux])
    frame_rate_hz = sample_rate_hz / FLUX_FRAME_HOP_SAMPLES
    flux = moving_average(flux, 5)
    flux = np.maximum(flux - moving_average(flux, int(frame_rate_hz)), 0.0)
    return flux / np.std(flux), frame_rate_hz


def tempogram_viterbi(flux, frame_rate_hz):
    window_frames = int(5.0 * frame_rate_hz)
    hop_frames = int(0.25 * frame_rate_hz)
    lags = np.arange(int(np.ceil(MINIMUM_INTERVAL_S * frame_rate_hz)), int(MAXIMUM_INTERVAL_S * frame_rate_hz) + 1)
    centres, autocorrelations = [], []
    taper = np.hanning(window_frames)
    for start in range(0, len(flux) - window_frames + 1, hop_frames):
        segment = flux[start : start + window_frames]
        segment = (segment - segment.mean()) * taper
        spectrum = np.fft.rfft(segment, 2 * window_frames)
        autocorrelation = np.fft.irfft(np.abs(spectrum) ** 2)[: window_frames]
        autocorrelation = autocorrelation / autocorrelation[0]
        centres.append((start + window_frames / 2) / frame_rate_hz)
        autocorrelations.append(autocorrelation)
    autocorrelations = np.array(autocorrelations)
    observation = autocorrelations[:, lags]
    log_lags = np.log(lags)
    change = np.abs(log_lags[:, None] - log_lags[None, :])
    transition = np.where(change <= np.log(1.15), -5.0 * change / np.log(1.01) * 0.01, -np.inf)
    score = observation[0].copy()
    backpointers = np.zeros(observation.shape, dtype=int)
    for frame in range(1, len(observation)):
        total = score[None, :] + transition
        backpointers[frame] = np.argmax(total, axis=1)
        score = total[np.arange(len(lags)), backpointers[frame]] + observation[frame]
    path = np.zeros(len(observation), dtype=int)
    path[-1] = int(np.argmax(score))
    for frame in range(len(observation) - 1, 0, -1):
        path[frame - 1] = backpointers[frame, path[frame]]
    periods = []
    for frame, state in enumerate(path):
        lag = lags[state]
        offset = parabolic_offset(*autocorrelations[frame, lag - 1 : lag + 2])
        periods.append((lag + offset) / frame_rate_hz)
    return np.array(centres), np.array(periods), autocorrelations


def method_b_spectral_flux_tempo_tracking(samples, sample_rate_hz):
    flux, frame_rate_hz = spectral_flux(samples, sample_rate_hz)
    centres, periods, autocorrelations = tempogram_viterbi(flux, frame_rate_hz)
    frame_times = np.arange(len(flux)) / frame_rate_hz
    period_frames = np.interp(frame_times, centres, periods) * frame_rate_hz
    tightness = 50.0
    cumulative = flux.copy()
    previous = np.full(len(flux), -1)
    for frame in range(len(flux)):
        earliest = int(frame - 2.0 * period_frames[frame])
        latest = int(frame - 0.5 * period_frames[frame])
        if latest < 0:
            continue
        candidates = np.arange(max(earliest, 0), latest + 1)
        penalty = -tightness * np.log((frame - candidates) / period_frames[frame]) ** 2
        totals = cumulative[candidates] + penalty
        best = int(np.argmax(totals))
        if totals[best] > 0:
            cumulative[frame] = flux[frame] + totals[best]
            previous[frame] = candidates[best]
    tail_start = int(len(flux) - period_frames[-1])
    frame = tail_start + int(np.argmax(cumulative[tail_start:]))
    beat_frames = []
    while frame >= 0:
        beat_frames.append(frame)
        frame = previous[frame]
    beat_frames = np.array(beat_frames[::-1])
    search = int(0.03 * frame_rate_hz)
    refined = []
    for frame in beat_frames:
        low, high = max(frame - search, 0), min(frame + search + 1, len(flux))
        refined.append((low + int(np.argmax(flux[low:high]))) / frame_rate_hz)
    tempo_track = {"time_s": centres, "period_s": periods, "autocorrelations": autocorrelations,
                   "frame_rate_hz": frame_rate_hz}
    return np.unique(np.array(refined)), tempo_track


def normalised_cross_correlation(feature, template):
    template = template - template.mean()
    template = template / np.linalg.norm(template)
    length = len(template)
    numerator = np.correlate(feature, template, mode="valid")
    cumulative = np.concatenate([[0.0], np.cumsum(feature)])
    cumulative_squares = np.concatenate([[0.0], np.cumsum(feature ** 2)])
    window_sum = cumulative[length:] - cumulative[:-length]
    window_square_sum = cumulative_squares[length:] - cumulative_squares[:-length]
    variance_sum = np.maximum(window_square_sum - window_sum ** 2 / length, 1e-12)
    return numerator / np.sqrt(variance_sum)


def match_beats(reference_times, other_times, tolerance):
    """Pairs each reference beat with the nearest other beat within tolerance."""
    pairs = []
    if len(other_times) == 0:
        return pairs
    for reference_index, reference_time in enumerate(reference_times):
        nearest = int(np.argmin(np.abs(other_times - reference_time)))
        if abs(other_times[nearest] - reference_time) <= tolerance:
            pairs.append((reference_index, nearest))
    return pairs


def method_c_cycle_template_matching(feature, anchor_times):
    """anchor_times: beats where A and B agree; only the template shape comes from them."""
    median_interval = float(np.median(np.diff(anchor_times)))
    pre_samples = int(0.10 * ENVELOPE_RATE_HZ)
    post_samples = int(0.65 * median_interval * ENVELOPE_RATE_HZ)
    total_duration = len(feature) / ENVELOPE_RATE_HZ
    block_edges = np.arange(0.0, total_duration + 1e-9, 15.0)
    block_edges[-1] = total_duration
    correlation = np.full(len(feature), -1.0)
    templates = []
    for block_start, block_end in zip(block_edges[:-1], block_edges[1:]):
        block_anchors = anchor_times[(anchor_times >= block_start - 2.5) & (anchor_times < block_end + 2.5)]
        if len(block_anchors) < 5:
            block_anchors = anchor_times
        segments = []
        for anchor in block_anchors:
            centre = int(round(anchor * ENVELOPE_RATE_HZ))
            if centre - pre_samples >= 0 and centre + post_samples <= len(feature):
                segment = feature[centre - pre_samples : centre + post_samples]
                segments.append(segment / (np.max(segment) + 1e-12))
        template = np.median(np.array(segments), axis=0)
        templates.append(template)
        block_correlation = normalised_cross_correlation(feature, template)
        first = int(block_start * ENVELOPE_RATE_HZ)
        last = int(block_end * ENVELOPE_RATE_HZ)
        aligned = np.full(len(feature), -1.0)
        aligned[pre_samples : pre_samples + len(block_correlation)] = block_correlation
        correlation[first:last] = aligned[first:last]
    peaks, _ = signal.find_peaks(correlation, height=0.45, distance=int(MINIMUM_INTERVAL_S * ENVELOPE_RATE_HZ))
    refined = []
    for peak in peaks:
        offset = parabolic_offset(*correlation[peak - 1 : peak + 2]) if 0 < peak < len(correlation) - 1 else 0.0
        refined.append((peak + offset) / ENVELOPE_RATE_HZ)
    return np.array(refined), correlation, templates, pre_samples


def align_to_reference(reference_times, other_times, half_width_s=8.0):
    """A method may lock onto a different point of the cycle (spectral flux favours S2). Its marks
    are shifted by the local circular mean of their cycle phase relative to the reference beats,
    so the shift follows the systole length as the rate changes. Returns aligned times and the
    shift of every mark in seconds."""
    positions = np.searchsorted(reference_times, other_times)
    valid = (positions > 0) & (positions < len(reference_times))
    previous_beats = reference_times[np.clip(positions - 1, 0, len(reference_times) - 1)]
    next_beats = reference_times[np.clip(positions, 0, len(reference_times) - 1)]
    cycle_lengths = np.where(valid, next_beats - previous_beats, np.nan)
    phases = np.where(valid, 2 * np.pi * (other_times - previous_beats) / cycle_lengths, np.nan)
    shifts = np.zeros(len(other_times))
    for index, time in enumerate(other_times):
        nearby = valid & (np.abs(other_times - time) <= half_width_s)
        mean_phase = np.angle(np.mean(np.exp(1j * phases[nearby])))
        local_cycle = np.nanmedian(cycle_lengths[nearby])
        shifts[index] = mean_phase / (2 * np.pi) * local_cycle
    return other_times - shifts, shifts


def energy_centroid(envelope, time, half_width_s=0.05, iterations=3):
    """The S1 complex often has two humps of similar height (split S1, or a peak flattened by
    clipping); the maximum jumps between them from beat to beat, the energy centroid does not."""
    half_width = int(half_width_s * ENVELOPE_RATE_HZ)
    centre = time * ENVELOPE_RATE_HZ
    for _ in range(iterations):
        low = max(int(round(centre)) - half_width, 0)
        high = min(int(round(centre)) + half_width + 1, len(envelope))
        weights = envelope[low:high] ** 2
        if weights.sum() <= 0:
            break
        centre = float(np.sum(np.arange(low, high) * weights) / weights.sum())
    return centre / ENVELOPE_RATE_HZ


def detect_no_signal_intervals(envelope):
    """Stretches where even the loudest sound within 0.8 s stays far below the recording's typical
    beat level: the chest-piece had no contact or the microphone was still settling."""
    window = int(0.8 * ENVELOPE_RATE_HZ)
    loudest = ndimage.maximum_filter1d(envelope, window)
    quiet = loudest < NO_SIGNAL_RATIO * np.median(loudest)
    intervals = []
    for run_start, run_end in zip(*contiguous_runs(quiet)):
        start = DISCARDED_SECONDS + run_start / ENVELOPE_RATE_HZ - 0.3
        end = DISCARDED_SECONDS + run_end / ENVELOPE_RATE_HZ + 0.3
        intervals.append((round(max(start, DISCARDED_SECONDS), 3), round(min(end, RECORDING_SECONDS), 3)))
    return intervals


def contiguous_runs(mask):
    padded = np.concatenate([[False], mask, [False]]).astype(int)
    changes = np.diff(padded)
    return np.nonzero(changes == 1)[0], np.nonzero(changes == -1)[0]


def combine_methods(method_beats, artefact_intervals, no_signal_intervals, mark_feature):
    """method_beats: name -> times (time zero = DISCARDED_SECONDS). Returns final times, confidences,
    per-method shifts and support counts."""
    reference_name = METHOD_NAMES[0]
    offsets = {reference_name: np.zeros(len(method_beats[reference_name]))}
    aligned = {reference_name: method_beats[reference_name]}
    for name in METHOD_NAMES[1:]:
        aligned[name], offsets[name] = align_to_reference(method_beats[reference_name], method_beats[name])

    marks = sorted((time, name) for name, times in aligned.items() for time in times)
    clusters = []
    for time, name in marks:
        if clusters and time - clusters[-1]["times"][0] <= CONSENSUS_TOLERANCE_S and name not in clusters[-1]["names"]:
            clusters[-1]["times"].append(time)
            clusters[-1]["names"].append(name)
        else:
            clusters.append({"times": [time], "names": [name]})

    supported = [cluster for cluster in clusters if len(cluster["names"]) >= 2]
    supported_times = np.array([np.median(cluster["times"]) for cluster in supported])
    supported_intervals = np.diff(supported_times)
    accepted = [(np.median(c["times"]), len(c["names"])) for c in supported]
    for cluster in clusters:
        if len(cluster["names"]) >= 2:
            continue
        time = cluster["times"][0]
        position = np.searchsorted(supported_times, time)
        if position == 0 or position == len(supported_times):
            continue
        gap = supported_times[position] - supported_times[position - 1]
        local = np.median(supported_intervals[max(position - 6, 0) : position + 5])
        before, after = time - supported_times[position - 1], supported_times[position] - time
        if gap > 1.5 * local and min(before, after) > 0.7 * local and max(before, after) < 1.3 * local:
            accepted.append((time, 1))
    accepted.sort()

    final_times, support_counts = [], []
    for time, support in accepted:
        absolute_time = time + DISCARDED_SECONDS
        if any(start <= absolute_time <= end for start, end in no_signal_intervals):
            continue
        refined_time = energy_centroid(mark_feature, time)
        if final_times and refined_time - final_times[-1] < MINIMUM_INTERVAL_S:
            if support > support_counts[-1]:
                final_times[-1], support_counts[-1] = refined_time, support
            continue
        final_times.append(refined_time)
        support_counts.append(support)
    final_times = np.array(final_times)
    support_counts = np.array(support_counts)

    confidence = np.where(support_counts >= 2, "high", "low").astype(object)
    absolute_times = final_times + DISCARDED_SECONDS
    for start, end in artefact_intervals:
        confidence[(absolute_times >= start) & (absolute_times <= end)] = "low"
    intervals = np.diff(final_times)
    for index in range(1, len(final_times) - 1):
        ratio = intervals[index] / intervals[index - 1]
        if abs(np.log(ratio)) > np.log(1.0 + INTERVAL_CHANGE_LIMIT):
            confidence[index] = "low"
    for index, interval in enumerate(intervals):
        if not MINIMUM_INTERVAL_S <= interval <= MAXIMUM_INTERVAL_S:
            confidence[index] = confidence[index + 1] = "low"
    return final_times, list(confidence), offsets, support_counts


def instantaneous_rate(beat_times, time, half_width=1.0):
    """Mean rate of the inter-beat intervals overlapping [time - half_width, time + half_width]."""
    if len(beat_times) < 2:
        return None
    starts, ends = beat_times[:-1], beat_times[1:]
    overlapping = (ends > time - half_width) & (starts < time + half_width)
    if not np.any(overlapping):
        return None
    return 60.0 / float(np.mean(ends[overlapping] - starts[overlapping]))


def window_rate(beat_times, window_start, window_end):
    inside = beat_times[(beat_times >= window_start) & (beat_times <= window_end)]
    if len(inside) < 2:
        return None, inside
    return 60.0 * (len(inside) - 1) / (inside[-1] - inside[0]), inside


def rounded(value, digits=4):
    return None if value is None else round(float(value), digits)


def half_double_rate_evidence(beat_times, samples, sample_rate_hz):
    """Checks that consecutive marks are one cardiac cycle apart and not S1-S2 or two cycles."""
    intervals = np.diff(beat_times)
    lag_one = np.mean(np.abs(np.diff(intervals)))
    lag_two = np.mean(np.abs(intervals[2:] - intervals[:-2]))
    s1_envelope = band_envelope(samples, 25, 150, sample_rate_hz, 30)
    s2_envelope = band_envelope(samples, 100, 400, sample_rate_hz, 30)
    phase_grid = np.linspace(-0.2, 1.2, 141)
    cycle_profiles = {"25-150 Hz": [], "100-400 Hz": []}
    for index in range(1, len(beat_times) - 1):
        interval = beat_times[index + 1] - beat_times[index]
        positions = (beat_times[index] + phase_grid * interval) * ENVELOPE_RATE_HZ
        if positions[0] < 0 or positions[-1] >= len(s1_envelope) - 1:
            continue
        for label, envelope in [("25-150 Hz", s1_envelope), ("100-400 Hz", s2_envelope)]:
            profile = np.interp(positions, np.arange(len(envelope)), envelope)
            cycle_profiles[label].append(profile / (np.max(profile[(phase_grid >= -0.1) & (phase_grid <= 0.1)]) + 1e-12))
    mean_profiles = {label: np.median(np.array(profiles), axis=0) for label, profiles in cycle_profiles.items()}
    inner = (phase_grid >= 0.2) & (phase_grid <= 0.8)
    secondary = {}
    for label, profile in mean_profiles.items():
        inner_profile = profile[inner]
        peak = int(np.argmax(inner_profile))
        secondary[label] = {"phase": float(phase_grid[inner][peak]), "relative_amplitude": float(inner_profile[peak])}
    s1_profile = mean_profiles["25-150 Hz"]
    at_next_beat = float(np.max(s1_profile[(phase_grid >= 0.9) & (phase_grid <= 1.1)]))
    segment_half = int(0.12 * ENVELOPE_RATE_HZ)
    segments = []
    for time in beat_times:
        centre = int(round(time * ENVELOPE_RATE_HZ))
        if centre - segment_half >= 0 and centre + segment_half < len(s1_envelope):
            segments.append(s1_envelope[centre - segment_half : centre + segment_half])
    segments = np.array(segments)
    correlation_next = np.mean([np.corrcoef(segments[i], segments[i + 1])[0, 1] for i in range(len(segments) - 1)])
    correlation_after_next = np.mean([np.corrcoef(segments[i], segments[i + 2])[0, 1] for i in range(len(segments) - 2)])
    return {
        "interval_alternation_ratio": float(lag_one / lag_two),
        "secondary_sound": secondary,
        "envelope_at_next_mark_relative_to_mark": at_next_beat,
        "beat_shape_correlation_next": float(correlation_next),
        "beat_shape_correlation_after_next": float(correlation_after_next),
        "median_interval_s": float(np.median(intervals)),
        "phase_grid": phase_grid,
        "mean_profiles": mean_profiles,
    }


def process_recording(name):
    samples_full, sample_rate_hz = soundfile.read(STUDY_DIRECTORY / "recordings" / name / "capture.wav", dtype="float64")
    samples = samples_full[int(DISCARDED_SECONDS * sample_rate_hz) :]
    samples = samples - np.mean(samples)

    artefact_intervals = detect_artefact_intervals(samples, sample_rate_hz)
    envelope_a = band_envelope(samples, 25, 150, sample_rate_hz, 20)
    feature_a = np.log1p(envelope_a / np.median(envelope_a))
    feature_c = np.sqrt(band_envelope(samples, 25, 400, sample_rate_hz, 30))
    no_signal_intervals = detect_no_signal_intervals(envelope_a)

    beats_a = method_a_envelope_peak_dynamic_programming(feature_a)
    beats_b, tempo_track = method_b_spectral_flux_tempo_tracking(samples, sample_rate_hz)
    aligned_b, _ = align_to_reference(beats_a, beats_b)
    pairs = match_beats(beats_a, aligned_b, CONSENSUS_TOLERANCE_S)
    anchor_times = np.array([beats_a[ref] for ref, _ in pairs])
    beats_c, template_correlation, templates, template_pre_samples = method_c_cycle_template_matching(feature_c, anchor_times)

    method_beats = {METHOD_NAMES[0]: beats_a, METHOD_NAMES[1]: beats_b, METHOD_NAMES[2]: beats_c}
    final_times, confidence, offsets, support_counts = combine_methods(method_beats, artefact_intervals, no_signal_intervals, envelope_a)

    absolute = final_times + DISCARDED_SECONDS
    absolute_by_method = {method: times + DISCARDED_SECONDS for method, times in method_beats.items()}
    confidence_array = np.array(confidence)

    rate_track = []
    for time in range(3, 61):
        per_method = {method: rounded(instantaneous_rate(times, time), 2) for method, times in absolute_by_method.items()}
        values = [value for value in per_method.values() if value is not None]
        rate_track.append({
            "time_s": time,
            "bpm": rounded(instantaneous_rate(absolute, time), 2),
            "bpm_per_method": per_method,
            "spread_bpm": rounded(max(values) - min(values), 2) if len(values) >= 2 else None,
        })

    intervals = np.diff(absolute)
    windows = []
    for end in range(10, 61):
        start = end - WINDOW_SECONDS
        reference_bpm, inside = window_rate(absolute, start, end)
        per_method = {method: rounded(window_rate(times, start, end)[0], 2) for method, times in absolute_by_method.items()}
        values = [value for value in per_method.values() if value is not None]
        spread = max(values) - min(values) if len(values) == len(per_method) else None
        interval_inside = (absolute[:-1] >= start) & (absolute[1:] <= end)
        rates_inside = 60.0 / intervals[interval_inside] if np.any(interval_inside) else np.array([])
        reasons = []
        if spread is None or spread > METHOD_SPREAD_LIMIT_BPM:
            reasons.append(f"methods disagree by {spread:.1f} BPM" if spread is not None else "a method has no rate")
        inside_mask = (absolute >= start) & (absolute <= end)
        if np.any(confidence_array[inside_mask] == "low"):
            low_times = ", ".join(f"{time:.2f}" for time in absolute[inside_mask & (confidence_array == "low")])
            reasons.append(f"low-confidence beat at {low_times} s")
        for artefact_start, artefact_end in artefact_intervals:
            if artefact_start < end and artefact_end > start:
                reasons.append(f"artefact {artefact_start:.1f}-{artefact_end:.1f} s")
        for quiet_start, quiet_end in no_signal_intervals:
            if quiet_start < end and quiet_end > start:
                reasons.append(f"no heart sound {quiet_start:.1f}-{quiet_end:.1f} s")
        if len(inside) >= 2:
            local_interval = float(np.median(np.diff(inside)))
            if np.any(np.diff(inside) > 1.5 * local_interval):
                reasons.append("missing beat (interval gap) inside window")
            if inside[0] - start > 1.3 * local_interval or end - inside[-1] > 1.3 * local_interval:
                reasons.append("missing beat at window edge")
        else:
            reasons.append("fewer than two beats")
        windows.append({
            "end_time_s": end,
            "reference_bpm": rounded(reference_bpm, 2),
            "reference_bpm_per_method": per_method,
            "method_spread_bpm": rounded(spread, 2),
            "beats_in_window": int(len(inside)),
            "rate_change_in_window_bpm": rounded(float(rates_inside.max() - rates_inside.min()), 2) if len(rates_inside) else None,
            "reliable": not reasons,
            "unreliable_reason": "; ".join(reasons) if reasons else None,
        })

    result = {
        "name": name,
        "sample_rate_hz": int(sample_rate_hz),
        "discarded_seconds": DISCARDED_SECONDS,
        "beat_mark": BEAT_MARK,
        "beat_times_s": [rounded(time) for time in absolute],
        "beat_confidence": confidence,
        "methods": {
            method: {
                "beat_times_s": [rounded(time + DISCARDED_SECONDS) for time in method_beats[method]],
                "description": METHOD_DESCRIPTIONS[method]
                + (f" Raw marks; for the consensus they are shifted toward method A's cycle phase by "
                   f"{np.median(offsets[method]) * 1000:.0f} ms median "
                   f"({np.min(offsets[method]) * 1000:.0f} to {np.max(offsets[method]) * 1000:.0f} ms)."
                   if method != METHOD_NAMES[0] else ""),
            }
            for method in METHOD_NAMES
        },
        "rate_track": rate_track,
        "windows": windows,
    }
    evidence = half_double_rate_evidence(final_times, samples, sample_rate_hz)
    diagnostics = {
        "samples": samples,
        "sample_rate_hz": sample_rate_hz,
        "envelope_a": envelope_a,
        "absolute_by_method": absolute_by_method,
        "artefact_intervals": artefact_intervals,
        "no_signal_intervals": no_signal_intervals,
        "tempo_track": tempo_track,
        "templates": templates,
        "template_pre_samples": template_pre_samples,
        "support_counts": support_counts,
        "evidence": evidence,
        "clipped_sample_share": float(np.mean(np.abs(samples_full[int(DISCARDED_SECONDS * sample_rate_hz) :]) >= 0.99)),
    }
    return result, diagnostics


BACKGROUND = "#0f1419"
TEXT = "#e6e6e6"
GRID = "#2a323c"
METHOD_COLOURS = {METHOD_NAMES[0]: "#6cb6ff", METHOD_NAMES[1]: "#c792ea", METHOD_NAMES[2]: "#ffd166"}
METHOD_SHORT_LABELS = {METHOD_NAMES[0]: "A envelope DP", METHOD_NAMES[1]: "B flux tempo", METHOD_NAMES[2]: "C template"}


def style_axis(axis):
    axis.set_facecolor(BACKGROUND)
    for spine in axis.spines.values():
        spine.set_color(GRID)
    axis.tick_params(colors=TEXT, labelsize=8)
    axis.xaxis.label.set_color(TEXT)
    axis.yaxis.label.set_color(TEXT)
    axis.title.set_color(TEXT)
    axis.grid(color=GRID, linewidth=0.5)


def draw_figure(result, diagnostics, output_path):
    samples = diagnostics["samples"]
    sample_rate_hz = diagnostics["sample_rate_hz"]
    display_decimation = 4
    waveform = band_pass(samples, 25, 400, sample_rate_hz)[::display_decimation]
    waveform = np.clip(waveform / np.percentile(np.abs(waveform), 99.9), -1, 1)
    waveform_times = DISCARDED_SECONDS + np.arange(len(waveform)) * display_decimation / sample_rate_hz
    envelope = diagnostics["envelope_a"]
    envelope = np.clip(envelope / np.percentile(envelope, 99.5), 0, 1.2)
    envelope_times = DISCARDED_SECONDS + np.arange(len(envelope)) / ENVELOPE_RATE_HZ
    beat_times = np.array(result["beat_times_s"])
    confidence = np.array(result["beat_confidence"])

    row_edges = [(0, 15), (15, 30), (30, 45), (45, 60)]
    figure = plt.figure(figsize=(24, 17), facecolor=BACKGROUND)
    grid = figure.add_gridspec(len(row_edges) + 1, 1, height_ratios=[1] * len(row_edges) + [1.3], hspace=0.35)
    for row, (row_start, row_end) in enumerate(row_edges):
        axis = figure.add_subplot(grid[row])
        style_axis(axis)
        if row_start < DISCARDED_SECONDS:
            axis.axvspan(row_start, DISCARDED_SECONDS, color="#333333", alpha=0.6)
        for artefact_start, artefact_end in diagnostics["artefact_intervals"]:
            axis.axvspan(artefact_start, artefact_end, color="#ff5c5c", alpha=0.18)
        for quiet_start, quiet_end in diagnostics["no_signal_intervals"]:
            axis.axvspan(quiet_start, quiet_end, color="#5c8cff", alpha=0.18)
        selected = (waveform_times >= row_start) & (waveform_times <= row_end)
        axis.plot(waveform_times[selected], waveform[selected], color="#7f8fa3", linewidth=0.4)
        selected = (envelope_times >= row_start) & (envelope_times <= row_end)
        axis.plot(envelope_times[selected], envelope[selected], color="#f0b45a", linewidth=0.9)
        in_row = (beat_times >= row_start) & (beat_times <= row_end)
        axis.vlines(beat_times[in_row & (confidence == "high")], -1.05, 1.25, color="#4cd97b", linewidth=0.9)
        axis.vlines(beat_times[in_row & (confidence == "low")], -1.05, 1.25, color="#ff5c5c", linewidth=1.4)
        for level, method in enumerate(METHOD_NAMES):
            times = np.array(result["methods"][method]["beat_times_s"])
            times = times[(times >= row_start) & (times <= row_end)]
            baseline = -1.35 - 0.3 * level
            axis.vlines(times, baseline - 0.12, baseline + 0.12, color=METHOD_COLOURS[method], linewidth=1.2)
        axis.set_xlim(row_start, row_end)
        axis.set_ylim(-2.15, 1.3)
        axis.set_xticks(np.arange(row_start, row_end + 0.01, 1))
        axis.set_yticks([-1.35, -1.65, -1.95, 0])
        axis.set_yticklabels([METHOD_SHORT_LABELS[m] for m in METHOD_NAMES] + ["signal"])
        if row == 0:
            axis.set_title(
                f"{result['name']}: 25-400 Hz waveform (grey), 25-150 Hz envelope (orange), final beats "
                f"(green high, red low confidence), method marks (rows, raw times), artefacts (red shade), no heart sound (blue shade)",
                fontsize=10,
            )
    axis.set_xlabel("time from file start (s)")

    bottom = grid[len(row_edges)].subgridspec(1, 2, width_ratios=[4, 1], wspace=0.12)
    rate_axis = figure.add_subplot(bottom[0])
    style_axis(rate_axis)
    for window in result["windows"]:
        if not window["reliable"]:
            rate_axis.axvspan(window["end_time_s"] - 0.5, window["end_time_s"] + 0.5, color="#ff5c5c", alpha=0.15)
    track_times = [entry["time_s"] for entry in result["rate_track"]]
    for method in METHOD_NAMES:
        values = [entry["bpm_per_method"][method] for entry in result["rate_track"]]
        values = [np.nan if value is None else value for value in values]
        rate_axis.plot(track_times, values, color=METHOD_COLOURS[method], linewidth=1.0, label=f"{METHOD_SHORT_LABELS[method]} (2 s rate)")
    final_track = [np.nan if entry["bpm"] is None else entry["bpm"] for entry in result["rate_track"]]
    rate_axis.plot(track_times, final_track, color="#4cd97b", linewidth=1.6, linestyle="--", label="final beats (2 s rate)")
    window_ends = [window["end_time_s"] for window in result["windows"]]
    window_values = [np.nan if window["reference_bpm"] is None else window["reference_bpm"] for window in result["windows"]]
    rate_axis.plot(window_ends, window_values, color="#ffffff", marker="o", markersize=3, linewidth=1.6, label="8 s window reference (at window end)")
    rate_axis.set_xlim(0, 60)
    rate_axis.set_xticks(np.arange(0, 61, 2))
    rate_axis.set_xlabel("time from file start (s); red shading = unreliable 8 s window ending at that second")
    rate_axis.set_ylabel("BPM")
    legend = rate_axis.legend(loc="upper right", fontsize=8, facecolor=BACKGROUND, edgecolor=GRID)
    for text in legend.get_texts():
        text.set_color(TEXT)
    profile_axis = figure.add_subplot(bottom[1])
    style_axis(profile_axis)
    evidence = diagnostics["evidence"]
    for (label, profile), colour in zip(evidence["mean_profiles"].items(), ["#f0b45a", "#6cb6ff"]):
        profile_axis.plot(evidence["phase_grid"], profile, color=colour, linewidth=1.3, label=f"{label} envelope")
    profile_axis.axvline(0, color="#4cd97b", linewidth=0.8)
    profile_axis.axvline(1, color="#4cd97b", linewidth=0.8)
    profile_axis.set_xlabel("cycle phase (0 = beat mark, 1 = next beat mark)")
    profile_axis.set_title("median cycle profile: S1 at 0, S2 inside the cycle", fontsize=9)
    profile_legend = profile_axis.legend(loc="upper center", fontsize=7, facecolor=BACKGROUND, edgecolor=GRID)
    for text in profile_legend.get_texts():
        text.set_color(TEXT)
    figure.savefig(output_path, dpi=90, facecolor=BACKGROUND, metadata={"Software": None})
    plt.close(figure)


def summarise(results_and_diagnostics):
    lines = [
        "# Reference beat times and heart rates",
        "",
        "Generated by `src/reference_beats.py`. Times are seconds from file start; the first 2.0 s of",
        "each recording are discarded. Per-recording data: `reference/<name>.json`; review figures:",
        "`reference/figures/<name>.png`.",
        "",
        "## Overview",
        "",
        "| Recording | Beats (low conf.) | Interval min / median / max (s) | Window BPM range | Reliable windows | Max window method spread (BPM) | Clipped samples |",
        "|---|---|---|---|---|---|---|",
    ]
    details = []
    for result, diagnostics in results_and_diagnostics:
        beats = np.array(result["beat_times_s"])
        intervals = np.diff(beats)
        low_count = sum(1 for value in result["beat_confidence"] if value == "low")
        window_rates = [w["reference_bpm"] for w in result["windows"] if w["reference_bpm"] is not None]
        reliable = sum(1 for w in result["windows"] if w["reliable"])
        spreads = [w["method_spread_bpm"] for w in result["windows"] if w["method_spread_bpm"] is not None]
        reliable_spreads = [w["method_spread_bpm"] for w in result["windows"] if w["reliable"]]
        largest_spread_window = max(result["windows"], key=lambda w: -1 if w["method_spread_bpm"] is None else w["method_spread_bpm"])
        lines.append(
            f"| {result['name']} | {len(beats)} ({low_count}) | {intervals.min():.3f} / {np.median(intervals):.3f} / {intervals.max():.3f} "
            f"| {min(window_rates):.1f}-{max(window_rates):.1f} | {reliable}/51 ({100 * reliable / 51:.0f} %) "
            f"| {max(spreads):.2f} (window ending {largest_spread_window['end_time_s']} s) | {100 * diagnostics['clipped_sample_share']:.3f} % |"
        )
        evidence = diagnostics["evidence"]
        support = diagnostics["support_counts"]
        method_counts = ", ".join(f"{METHOD_SHORT_LABELS[m]} {len(result['methods'][m]['beat_times_s'])}" for m in METHOD_NAMES)
        unreliable = [w for w in result["windows"] if not w["reliable"]]
        reason_counts = {}
        for window in unreliable:
            for reason in window["unreliable_reason"].split("; "):
                key = reason.split(" at ")[0].split(" by ")[0]
                key = "artefact" if key.startswith("artefact") else key
                key = "no heart sound" if key.startswith("no heart sound") else key
                reason_counts[key] = reason_counts.get(key, 0) + 1
        instantaneous = 60.0 / intervals
        details += [
            f"### {result['name']}",
            "",
            f"- Largest method spread among reliable windows: {max(reliable_spreads) if reliable_spreads else float('nan'):.2f} BPM.",
            f"- Beats per method: {method_counts}; final beats confirmed by 3 methods: {int(np.sum(support == 3))}, "
            f"by 2: {int(np.sum(support == 2))}, by 1 (gap fill): {int(np.sum(support == 1))}.",
            f"- Beat-to-beat rate range: {instantaneous.min():.1f}-{instantaneous.max():.1f} BPM.",
            f"- Artefact intervals detected: {', '.join(f'{s:.1f}-{e:.1f} s' for s, e in diagnostics['artefact_intervals']) or 'none'}.",
            f"- No-heart-sound intervals detected: {', '.join(f'{s:.1f}-{e:.1f} s' for s, e in diagnostics['no_signal_intervals']) or 'none'}.",
            f"- Unreliable windows: {len(unreliable)}; reasons (window counts): "
            f"{', '.join(f'{k}: {v}' for k, v in reason_counts.items()) or 'none'}.",
            f"- Half/double-rate check: interval alternation ratio {evidence['interval_alternation_ratio']:.2f} "
            f"(about 1 or below for a true cycle; S1/S2 picked as separate beats would give well above 1); "
            f"beat-shape correlation with next beat {evidence['beat_shape_correlation_next']:.2f} vs. beat after next "
            f"{evidence['beat_shape_correlation_after_next']:.2f} (equal means no S1/S2 alternation); "
            f"secondary sound inside the cycle in the 100-400 Hz envelope at phase "
            f"{evidence['secondary_sound']['100-400 Hz']['phase']:.2f} "
            f"({evidence['secondary_sound']['100-400 Hz']['phase'] * evidence['median_interval_s'] * 1000:.0f} ms after the mark, "
            f"{evidence['secondary_sound']['100-400 Hz']['relative_amplitude']:.2f} of S1), in the 25-150 Hz envelope at phase "
            f"{evidence['secondary_sound']['25-150 Hz']['phase']:.2f} ({evidence['secondary_sound']['25-150 Hz']['relative_amplitude']:.2f} of S1); "
            f"envelope at the next mark {evidence['envelope_at_next_mark_relative_to_mark']:.2f} of the mark.",
            "",
        ]
    lines += ["", "## Per recording", ""] + details
    lines += METHOD_TEXT.splitlines()
    return "\n".join(lines) + "\n"


METHOD_TEXT = """
## Review notes (from inspecting the figures)

- rest-1: the movement artefact at 39.2-40.4 s is detected; the two beats inside it sit at the
  expected spacing but are low confidence, and the windows ending 40-48 s are unreliable.
- rest-2: the 25.0-25.3 s artefact is high-frequency rubbing only; the beats at 24.84 s and
  25.59 s look clean, so its 8 unreliable windows are conservative.
- elevated-1: almost no heart sound from 2.0 to 3.6 s (one faint beat near 2.47 s, left unmarked),
  then the clipping burst at 3.6-4.4 s. Windows ending 10-17 s are unreliable, so the reference
  does not cover the steepest part of the fall from about 130 BPM. Method C misses the beat at
  56.93 s and B is off phase near 57 s; A's beat there is kept as low confidence.
- elevated-2 and elevated-3: S1 is clipped and often has two humps about 25 ms apart; the energy
  centroid mark stays stable on it. S2 is faint (0.1-0.25 of S1) but visible in the median
  cycle profile at phase 0.35.
- The rough figures given beforehand (rest-1 73-86, rest-2 80-87, elevated-1 128 to 88,
  elevated-2 141 to 120, elevated-3 149 to 116 BPM) agree with this reference to within a few BPM.
## How the reference is made

- **A, envelope peaks with dynamic programming:** the 25-150 Hz band (where S1 is strongest) is
  turned into a smooth, log-compressed loudness curve. Every local peak is a candidate. A
  whole-recording search picks the chain of peaks that is loudest overall while keeping
  consecutive beat-to-beat intervals similar, with intervals between 0.3 s and 1.5 s (200-40 BPM).
  Clipping flattens peaks, but log compression makes a clipped beat look about as loud as an
  unclipped one, so it is still picked.
- **B, spectral flux tempo tracking:** a different feature, the onset strength of new energy in
  the 20-400 Hz spectrum, is analysed for periodicity in 5 s windows. A Viterbi search finds the
  smoothest period path through the whole recording, which rules out sudden half- or double-rate
  jumps. Beats are then placed on onsets spaced by that period. Clipping adds broadband energy at
  each beat, which strengthens the onsets rather than hiding them.
- **C, template matching:** the average shape of one cardiac cycle (S1 and S2 together) is
  learned per 15 s from beats where A and B agree and slid along the recording. The correlation is
  normalised, so it compares shape only, and clipped or quieter beats still match.
- **Combination:** B tends to mark S2 (its onsets are stronger there), so B and C marks are first
  shifted by their local mean cycle phase relative to A's beats (circular mean over ±8 s); the
  per-method rates use the raw marks. A final beat needs marks from at least
  two methods within ±60 ms (high confidence). A single-method mark is kept only where it fills a
  gap at the expected place (low confidence). Each final mark is moved to the energy centroid of
  the 25-150 Hz envelope within ±50 ms (stable when S1 has two humps or is clipped flat). Marks
  inside a no-heart-sound stretch are removed. Beats inside detected artefacts, beats whose interval changes
  by more than 20 % from the previous interval, and intervals outside 40-200 BPM are low
  confidence. An 8 s window is unreliable if the three methods' window rates differ by more than
  3 BPM, it contains a low-confidence beat or an artefact, or a beat seems to be missing.
- **Artefact detection:** 100 ms frames whose 3-20 Hz energy (chest-piece motion) exceeds 2.5 times,
  or whose 400-2000 Hz energy (rubbing) exceeds 15 times, the recording's 90th percentile,
  padded by 0.1 s. No heart sound: the loudest 25-150 Hz envelope value within 0.8 s stays below
  0.25 of its median, padded by 0.3 s. These thresholds were chosen by looking at these five
  recordings.
- **Why this is weaker than an ECG reference:** all three methods look at the same sound. If a beat
  is inaudible, or noise looks like a beat, the methods can agree and still be wrong. There is no
  electrical timing reference, so a constant mark offset is unknown (irrelevant for rate). S1 and S2
  are told apart only by timing and spectrum, not by an R wave. Methods A and C use overlapping
  frequency bands, and C's template comes from A and B, so their errors are not fully independent.
"""


def main():
    reference_directory = STUDY_DIRECTORY / "reference"
    figure_directory = reference_directory / "figures"
    figure_directory.mkdir(parents=True, exist_ok=True)
    results_and_diagnostics = []
    for name in RECORDING_NAMES:
        result, diagnostics = process_recording(name)
        (reference_directory / f"{name}.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        draw_figure(result, diagnostics, figure_directory / f"{name}.png")
        results_and_diagnostics.append((result, diagnostics))
        reliable = sum(1 for window in result["windows"] if window["reliable"])
        print(f"{name}: {len(result['beat_times_s'])} beats, {reliable}/51 reliable windows")
    (reference_directory / "SUMMARY.md").write_text(summarise(results_and_diagnostics), encoding="utf-8")


if __name__ == "__main__":
    main()
