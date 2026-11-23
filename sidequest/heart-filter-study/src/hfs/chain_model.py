"""Model of the capture chain (INMP441 to 24-bit samples at 16 kHz) for public heart-sound recordings.

The output has the format of `hfs.recordings.load_recording`, so the run-1 device chain (`hfs.device_chain`)
takes it unchanged. Steps, in order (each a separate function below):

1. `remove_mean_and_resample`: mean removal, polyphase resampling to 16 kHz (`scipy.signal.resample_poly`,
   Kaiser window with beta 5.0, cutoff at the lower of the two Nyquist frequencies, filter length
   2 * 10 * max(up, down) + 1 taps at the intermediate rate). Public data carry nothing above their own
   Nyquist frequency (CirCor 4 kHz: 2 kHz, EPHNOGRAM 8 kHz: 4 kHz), so the model output is band limited there.
2. `apply_microphone_response`: INMP441 datasheet model, numbers copied from the DigitalStethoscope
   repository file `Development/system/testing/AUDIO/chain-measurement/microphone_model.py` (record
   `tdk_inmp441_datasheet_2014`): acoustic high-pass 60 Hz (checked), digital high-pass 3.7 Hz at 48 kHz scaled
   with the sample rate (1.23 Hz at 16 kHz; NOT yet checked against the datasheet page), pass-band edge
   0.423 x fS (6.77 kHz at 16 kHz; NOT yet checked). First order for both corners and the scaling are project
   assumptions of that file, not datasheet statements. Applied as causal first-order sections (minimum phase,
   which is what a first-order high-pass is); the 17.2-sample group delay is left out so that dataset
   segmentation stays aligned. The pass-band edge (0.423 x fS) lies above the band limit of step 1 and is
   therefore not applied.
3. `apply_spectrum_correction` (variant `matched_to_own_recordings` only): smooth third-octave correction
   (20 Hz-1 kHz, limited to +-12 dB, tapering to 0 dB one octave outside), zero-phase application of a
   linear-phase FIR. It stands for chest-piece, tube and sensor differences together, but also for the
   difference between persons (Nico versus the dataset's subjects): an empirical match, not a physical model.
4. Level gain per dataset and level condition (`Calibration.gain`), see `fit_calibration`. Level measure: median
   over beats of the peak of the zero-phase 20-400 Hz band (`heart_sound_level`), the same on own and public data.
   "rest": the dataset median of that level equals the median of rest-1, rest-2, elevated-1. "overload": the share
   of beats with a sample at a 24-bit limit equals that of elevated-2 and elevated-3 (87 of 256 beats); without
   beat times the share of samples at a limit is matched instead (`Calibration.overload_share_method`).
5. `add_missing_noise_floor`: Gaussian noise shaped per third-octave band so that the floor is not below the
   real chain's floor measured on the own recordings; only the missing part is added, nothing is subtracted.
6. `limit_to_24_bit`: hard limit at -8388608...8388607 and rounding to integers, as the own recordings show.
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import math
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Iterable

import numpy
import scipy.fft
from scipy import signal

from . import recordings

STUDY_DIRECTORY = Path(__file__).resolve().parents[2]
CALIBRATION_DIRECTORY = STUDY_DIRECTORY / "calibration"
REFERENCE_DIRECTORY = STUDY_DIRECTORY / "reference"
TARGET_SAMPLE_RATE_HZ = 16000
FULL_SCALE = 8388608.0
POSITIVE_LIMIT_FULL_SCALE = recordings.SAMPLE_MAXIMUM / FULL_SCALE
NEGATIVE_LIMIT_FULL_SCALE = recordings.SAMPLE_MINIMUM / FULL_SCALE

# Values from Development/system/testing/AUDIO/chain-measurement/microphone_model.py (DigitalStethoscope
# repository), copied because the study runs outside the repository.
MICROPHONE_ACOUSTIC_HIGH_PASS_HZ = 60.0
MICROPHONE_DIGITAL_HIGH_PASS_HZ_AT_48_KHZ = 3.7

SPECTRUM_VARIANTS = ("microphone_only", "matched_to_own_recordings")
LEVEL_CONDITIONS = ("rest", "overload")
REST_LEVEL_RECORDINGS = ("rest-1", "rest-2", "elevated-1")
OVERLOAD_RECORDINGS = ("elevated-2", "elevated-3")

MATCH_LOWEST_BAND_HZ = 20.0
MATCH_HIGHEST_BAND_HZ = 1000.0
MATCH_LIMIT_DB = 12.0
MATCH_FIR_TAP_COUNT = 8191
NOISE_LOWEST_BAND_HZ = 20.0
NOISE_HIGHEST_BAND_HZ = 6300.0
NOISE_FRAME_SECONDS = 0.25
NOISE_FLOOR_PERCENTILE = 10.0
LEVEL_BAND_HZ = (20.0, 400.0)
LEVEL_PERCENTILE = 95.0
WELCH_SEGMENT_SAMPLES = 16384


def third_octave_centres_hz(lowest_hz: float, highest_hz: float) -> numpy.ndarray:
    """Nominal base-10 third-octave centres (IEC 61260 exact values 1000 * 10^(n/10))."""
    lowest_index = int(math.floor(10 * math.log10(lowest_hz / 1000.0) + 0.5))
    highest_index = int(math.floor(10 * math.log10(highest_hz / 1000.0) + 0.5))
    return 1000.0 * 10.0 ** (numpy.arange(lowest_index, highest_index + 1) / 10.0)


def band_edges_hz(centres_hz: numpy.ndarray) -> tuple[numpy.ndarray, numpy.ndarray]:
    half_band = 10.0 ** (1.0 / 20.0)
    return centres_hz / half_band, centres_hz * half_band


@dataclass
class Calibration:
    dataset_name: str
    source_sample_rates_hz: list[float]
    recording_count: int
    gain: dict[str, dict[str, float]]
    overload_share_method: str
    level_measure: str
    spectrum_correction_band_centres_hz: list[float]
    spectrum_correction_db: list[float]
    own_median_band_shape_db: list[float]
    dataset_median_band_shape_db: list[float]
    noise_band_centres_hz: list[float]
    own_floor_band_power_db: list[float]
    targets: dict[str, float]
    created: str
    notes: list[str] = field(default_factory=list)

    def save(self, directory: Path = CALIBRATION_DIRECTORY) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"chain_model_{self.dataset_name}.json"
        path.write_text(json.dumps(dataclasses.asdict(self), indent=1), encoding="utf-8")
        return path


def load_calibration(dataset_name: str, directory: Path = CALIBRATION_DIRECTORY) -> Calibration:
    data = json.loads((directory / f"chain_model_{dataset_name}.json").read_text(encoding="utf-8"))
    return Calibration(**data)


# Step 1 ------------------------------------------------------------------------------------------------------

def remove_mean_and_resample(samples: numpy.ndarray, sample_rate_hz: float) -> numpy.ndarray:
    values = numpy.asarray(samples, dtype=numpy.float64)
    values = values - values.mean()
    ratio = Fraction(TARGET_SAMPLE_RATE_HZ) / Fraction(sample_rate_hz).limit_denominator(1000)
    if ratio == 1:
        return values
    return signal.resample_poly(values, ratio.numerator, ratio.denominator)


# Step 2 ------------------------------------------------------------------------------------------------------

def microphone_digital_high_pass_hz(sample_rate_hz: float = TARGET_SAMPLE_RATE_HZ) -> float:
    return MICROPHONE_DIGITAL_HIGH_PASS_HZ_AT_48_KHZ * sample_rate_hz / 48000.0


def microphone_sections(sample_rate_hz: float = TARGET_SAMPLE_RATE_HZ) -> numpy.ndarray:
    acoustic = signal.butter(1, MICROPHONE_ACOUSTIC_HIGH_PASS_HZ, "highpass", fs=sample_rate_hz, output="sos")
    digital = signal.butter(1, microphone_digital_high_pass_hz(sample_rate_hz), "highpass", fs=sample_rate_hz,
                            output="sos")
    return numpy.vstack([acoustic, digital])


def apply_microphone_response(samples_16_khz: numpy.ndarray) -> numpy.ndarray:
    return signal.sosfilt(microphone_sections(), samples_16_khz)


# Step 3 ------------------------------------------------------------------------------------------------------

def match_band_centres_hz() -> numpy.ndarray:
    return third_octave_centres_hz(MATCH_LOWEST_BAND_HZ, MATCH_HIGHEST_BAND_HZ)


def correction_gain_db_at(frequencies_hz: numpy.ndarray, band_centres_hz: numpy.ndarray,
                          correction_db: numpy.ndarray) -> numpy.ndarray:
    """Interpolated over log frequency inside the bands; tapers linearly to 0 dB over one octave outside."""
    frequencies = numpy.maximum(numpy.asarray(frequencies_hz, dtype=float), 1e-3)
    log_frequency = numpy.log2(frequencies)
    log_centres = numpy.log2(band_centres_hz)
    gain_db = numpy.interp(log_frequency, log_centres, correction_db)
    below = log_frequency < log_centres[0]
    above = log_frequency > log_centres[-1]
    gain_db[below] = correction_db[0] * numpy.clip(1.0 - (log_centres[0] - log_frequency[below]), 0.0, 1.0)
    gain_db[above] = correction_db[-1] * numpy.clip(1.0 - (log_frequency[above] - log_centres[-1]), 0.0, 1.0)
    return gain_db


def correction_fir(band_centres_hz: numpy.ndarray, correction_db: numpy.ndarray,
                   tap_count: int = MATCH_FIR_TAP_COUNT) -> numpy.ndarray:
    nyquist = TARGET_SAMPLE_RATE_HZ / 2.0
    grid_hz = numpy.concatenate([[0.0], numpy.geomspace(1.0, nyquist - 1.0, 600), [nyquist]])
    gains = 10.0 ** (correction_gain_db_at(grid_hz, band_centres_hz, numpy.asarray(correction_db)) / 20.0)
    gains[0] = gains[1]
    return signal.firwin2(tap_count, grid_hz, gains, fs=TARGET_SAMPLE_RATE_HZ, window="blackman")


def apply_spectrum_correction(samples_16_khz: numpy.ndarray, calibration: Calibration) -> numpy.ndarray:
    taps = correction_fir(numpy.asarray(calibration.spectrum_correction_band_centres_hz),
                          numpy.asarray(calibration.spectrum_correction_db))
    return signal.fftconvolve(samples_16_khz, taps, mode="same")


def smooth_limited_correction(difference_db: numpy.ndarray) -> numpy.ndarray:
    limited = numpy.clip(difference_db, -MATCH_LIMIT_DB, MATCH_LIMIT_DB)
    padded = numpy.concatenate([[limited[0]], limited, [limited[-1]]])
    smoothed = 0.25 * padded[:-2] + 0.5 * padded[1:-1] + 0.25 * padded[2:]
    return numpy.clip(smoothed, -MATCH_LIMIT_DB, MATCH_LIMIT_DB)


# Measures shared by own and public data -----------------------------------------------------------------------

def band_power_spectrum(samples: numpy.ndarray, sample_rate_hz: float, band_centres_hz: numpy.ndarray) -> numpy.ndarray:
    """Long-term power per band (Welch, Hann, 16384 samples, half overlap), in the samples' units squared."""
    segment = min(WELCH_SEGMENT_SAMPLES, len(samples))
    frequencies, density = signal.welch(samples, fs=sample_rate_hz, nperseg=segment)
    resolution = frequencies[1] - frequencies[0]
    lower, upper = band_edges_hz(band_centres_hz)
    return numpy.array([density[(frequencies >= low) & (frequencies < high)].sum() * resolution
                        for low, high in zip(lower, upper)])


def band_shape_db(samples: numpy.ndarray, sample_rate_hz: float) -> numpy.ndarray:
    """Third-octave band levels 20 Hz-1 kHz relative to their sum: spectral shape without overall level."""
    powers = band_power_spectrum(samples, sample_rate_hz, match_band_centres_hz())
    return 10.0 * numpy.log10(numpy.maximum(powers, 1e-30) / max(powers.sum(), 1e-30))


LEVEL_MEASURES = ("median_beat_peak", "envelope_95th_percentile")


def heart_sound_band(samples_full_scale: numpy.ndarray, sample_rate_hz: float = TARGET_SAMPLE_RATE_HZ) -> numpy.ndarray:
    sections = signal.butter(4, LEVEL_BAND_HZ, "bandpass", fs=sample_rate_hz, output="sos")
    return signal.sosfiltfilt(sections, samples_full_scale)


def heart_sound_level(samples_full_scale: numpy.ndarray, beat_times_s=None, time_offset_s: float = 0.0,
                      level_measure: str = "median_beat_peak") -> float:
    """Heart-sound level of a 16 kHz signal (full-scale units), on the zero-phase 4th-order 20-400 Hz band.
    median_beat_peak: median over beats of the band's largest absolute value (needs beat times);
    envelope_95th_percentile: 95th percentile of the band's Hilbert envelope (fallback without beat times)."""
    band = heart_sound_band(samples_full_scale)
    if level_measure == "median_beat_peak":
        bounds = beat_segment_bounds(beat_times_s, len(band), TARGET_SAMPLE_RATE_HZ, time_offset_s)
        if not bounds:
            raise ValueError("median_beat_peak needs at least two beat times inside the signal")
        return float(numpy.median([numpy.abs(band[first:last]).max() for first, last in bounds]))
    envelope = numpy.abs(signal.hilbert(band, scipy.fft.next_fast_len(len(band))))[:len(band)]
    return float(numpy.percentile(envelope, LEVEL_PERCENTILE))


def noise_band_centres_hz() -> numpy.ndarray:
    return third_octave_centres_hz(NOISE_LOWEST_BAND_HZ, NOISE_HIGHEST_BAND_HZ)


def floor_band_power(samples_full_scale: numpy.ndarray, sample_rate_hz: float = TARGET_SAMPLE_RATE_HZ) -> numpy.ndarray:
    """Floor per third-octave band (FS^2): 10th percentile over 250 ms Hann frames (hop 62.5 ms) of the frame's
    band power. 250 ms gives 4 Hz bins, enough to resolve the 20-31.5 Hz bands. The quietest tenth of the frames
    lies in the gaps between beats; the measure needs no beat times, so it is the same on all data."""
    frame = int(round(NOISE_FRAME_SECONDS * sample_rate_hz))
    hop = frame // 4
    window = signal.windows.hann(frame, sym=False)
    window_power = float(numpy.sum(window ** 2))
    frequencies = numpy.fft.rfftfreq(frame, 1.0 / sample_rate_hz)
    lower, upper = band_edges_hz(noise_band_centres_hz())
    band_masks = [(frequencies >= low) & (frequencies < high) for low, high in zip(lower, upper)]
    frame_count = max(0, (len(samples_full_scale) - frame) // hop + 1)
    if frame_count == 0:
        return numpy.zeros(len(band_masks))
    frame_powers = numpy.zeros((len(band_masks), frame_count))
    frames = numpy.lib.stride_tricks.sliding_window_view(samples_full_scale, frame)[::hop]
    for start in range(0, frame_count, 2048):
        spectrum = numpy.fft.rfft(frames[start:start + 2048] * window, axis=1)
        # One-sided power, normalised so that a band's sum equals the band's mean-square value.
        power = 2.0 * numpy.abs(spectrum) ** 2 / (frame * window_power)
        for band_index, mask in enumerate(band_masks):
            frame_powers[band_index, start:start + 2048] = power[:, mask].sum(axis=1)
    return numpy.percentile(frame_powers, NOISE_FLOOR_PERCENTILE, axis=1) * numpy.array([mask.any() for mask in band_masks])


def beat_segment_bounds(beat_times_s: numpy.ndarray, sample_count: int, sample_rate_hz: float,
                        time_offset_s: float = 0.0) -> list[tuple[int, int]]:
    """Each beat owns the time from the midpoint to the previous beat to the midpoint to the next beat."""
    times = numpy.sort(numpy.asarray(beat_times_s, dtype=float)) - time_offset_s
    times = times[(times >= 0.0) & (times < sample_count / sample_rate_hz)]
    if len(times) < 2:
        return []
    midpoints = (times[1:] + times[:-1]) / 2.0
    starts = numpy.concatenate([[max(0.0, times[0] - (midpoints[0] - times[0]))], midpoints])
    stops = numpy.concatenate([midpoints, [times[-1] + (times[-1] - midpoints[-1])]])
    bounds = []
    for start, stop in zip(starts, stops):
        first, last = int(start * sample_rate_hz), min(sample_count, int(stop * sample_rate_hz))
        if last > first:
            bounds.append((first, last))
    return bounds


def gain_to_reach_full_scale(samples_full_scale: numpy.ndarray) -> float:
    """Smallest gain at which some sample of the segment reaches either 24-bit limit."""
    positive_peak = float(samples_full_scale.max(initial=0.0))
    negative_peak = float(-samples_full_scale.min(initial=0.0))
    candidates = [limit / peak for limit, peak in ((POSITIVE_LIMIT_FULL_SCALE, positive_peak),
                                                   (-NEGATIVE_LIMIT_FULL_SCALE, negative_peak)) if peak > 0.0]
    return min(candidates) if candidates else math.inf


def per_beat_gains_to_full_scale(samples_full_scale: numpy.ndarray, beat_times_s, sample_rate_hz: float,
                                 time_offset_s: float = 0.0) -> numpy.ndarray:
    bounds = beat_segment_bounds(beat_times_s, len(samples_full_scale), sample_rate_hz, time_offset_s)
    return numpy.array([gain_to_reach_full_scale(samples_full_scale[first:last]) for first, last in bounds])


def per_sample_gains_to_full_scale(samples_full_scale: numpy.ndarray) -> numpy.ndarray:
    with numpy.errstate(divide="ignore"):
        return numpy.where(samples_full_scale > 0, POSITIVE_LIMIT_FULL_SCALE / samples_full_scale,
                           numpy.where(samples_full_scale < 0, NEGATIVE_LIMIT_FULL_SCALE / samples_full_scale,
                                       numpy.inf))


def share_of_beats_at_full_scale(samples_int24: numpy.ndarray, beat_times_s, sample_rate_hz: float = TARGET_SAMPLE_RATE_HZ,
                                 time_offset_s: float = 0.0) -> tuple[int, int]:
    """(beats with at least one sample at a 24-bit limit, beats)."""
    values = numpy.asarray(samples_int24)
    bounds = beat_segment_bounds(beat_times_s, len(values), sample_rate_hz, time_offset_s)
    at_limit = (values >= recordings.SAMPLE_MAXIMUM) | (values <= recordings.SAMPLE_MINIMUM)
    return sum(bool(at_limit[first:last].any()) for first, last in bounds), len(bounds)


def share_of_samples_at_full_scale(samples_int24: numpy.ndarray) -> float:
    values = numpy.asarray(samples_int24)
    return float(numpy.mean((values >= recordings.SAMPLE_MAXIMUM) | (values <= recordings.SAMPLE_MINIMUM)))


# Own recordings (the real chain) ------------------------------------------------------------------------------

def own_reference_beat_times_s(name: str) -> numpy.ndarray:
    data = json.loads((REFERENCE_DIRECTORY / f"{name}.json").read_text(encoding="utf-8"))
    return numpy.asarray(data["beat_times_s"], dtype=float)


def own_recording_full_scale(name: str) -> numpy.ndarray:
    return recordings.load_recording(name).astype(numpy.float64) / FULL_SCALE


_own_targets_cache: dict | None = None


def own_targets() -> dict:
    """Targets measured on the five own recordings (23 Nov 2026, capture firmware, raw INMP441)."""
    global _own_targets_cache
    if _own_targets_cache is not None:
        return _own_targets_cache
    shapes, levels, floors = {}, {}, {}
    beats_at_limit, beat_count, samples_at_limit = 0, 0, []
    for name in recordings.RECORDING_NAMES:
        samples = own_recording_full_scale(name)
        shapes[name] = band_shape_db(samples - samples.mean(), TARGET_SAMPLE_RATE_HZ)
        beat_times = own_reference_beat_times_s(name)
        levels[name] = {measure: heart_sound_level(samples - samples.mean(), beat_times, recordings.DISCARDED_SECONDS,
                                                   measure) for measure in LEVEL_MEASURES}
        floors[name] = floor_band_power(samples - samples.mean())
        if name in OVERLOAD_RECORDINGS:
            clipped, total = share_of_beats_at_full_scale(recordings.load_recording(name),
                                                          beat_times,
                                                          time_offset_s=recordings.DISCARDED_SECONDS)
            beats_at_limit += clipped
            beat_count += total
            samples_at_limit.append(share_of_samples_at_full_scale(recordings.load_recording(name)))
    _own_targets_cache = {
        "band_shape_db": shapes,
        "median_band_shape_db": numpy.median(numpy.array(list(shapes.values())), axis=0),
        "heart_sound_level": levels,
        "rest_level": {measure: float(numpy.median([levels[name][measure] for name in REST_LEVEL_RECORDINGS]))
                       for measure in LEVEL_MEASURES},
        "overload_beat_share": beats_at_limit / beat_count,
        "overload_beats_at_limit": beats_at_limit,
        "overload_beat_count": beat_count,
        "overload_sample_share": float(numpy.mean(samples_at_limit)),
        "floor_band_power": floors,
        "median_floor_band_power": numpy.median(numpy.array(list(floors.values())), axis=0),
    }
    return _own_targets_cache


# Steps 5 and 6 -----------------------------------------------------------------------------------------------

def shaped_noise(band_power: numpy.ndarray, sample_count: int, generator: numpy.random.Generator) -> numpy.ndarray:
    """Gaussian noise whose expected power per third-octave band equals band_power (FS^2)."""
    transform_length = scipy.fft.next_fast_len(sample_count, real=True)
    spectrum = numpy.fft.rfft(generator.standard_normal(transform_length))
    frequencies = numpy.fft.rfftfreq(transform_length, 1.0 / TARGET_SAMPLE_RATE_HZ)
    scale = numpy.zeros_like(frequencies)
    lower, upper = band_edges_hz(noise_band_centres_hz())
    for low, high, power in zip(lower, upper, band_power):
        selected = (frequencies >= low) & (frequencies < high)
        bin_count = int(selected.sum())
        if bin_count and power > 0.0:
            # A unit-variance white sequence has expected power 2 * bins / sample_count in a band of `bins` rfft bins.
            scale[selected] = math.sqrt(power / (2.0 * bin_count / transform_length))
    return numpy.fft.irfft(spectrum * scale, n=transform_length)[:sample_count]


_floor_to_mean_cache: numpy.ndarray | None = None


def floor_to_mean_power_ratio() -> numpy.ndarray:
    """Per band: floor measure of stationary shaped noise divided by its mean band power. Narrow low bands hold
    few frequency bins, so their frame powers scatter widely and the 10th percentile lies far below the mean."""
    global _floor_to_mean_cache
    if _floor_to_mean_cache is None:
        unit = numpy.ones(len(noise_band_centres_hz()))
        noise = shaped_noise(unit, 60 * TARGET_SAMPLE_RATE_HZ, numpy.random.default_rng(12345))
        _floor_to_mean_cache = floor_band_power(noise) / unit
    return _floor_to_mean_cache


def add_missing_noise_floor(samples_full_scale: numpy.ndarray, calibration: Calibration,
                            generator: numpy.random.Generator) -> numpy.ndarray:
    target = 10.0 ** (numpy.asarray(calibration.own_floor_band_power_db) / 10.0)
    present = floor_band_power(samples_full_scale)
    # A percentile floor of signal plus independent noise is roughly the sum of the two floors.
    missing_floor = numpy.maximum(target - present, 0.0)
    missing_mean_power = missing_floor / floor_to_mean_power_ratio()
    return samples_full_scale + shaped_noise(missing_mean_power, len(samples_full_scale), generator)


def limit_to_24_bit(samples_full_scale: numpy.ndarray) -> numpy.ndarray:
    scaled = numpy.rint(numpy.asarray(samples_full_scale) * FULL_SCALE)
    return numpy.clip(scaled, recordings.SAMPLE_MINIMUM, recordings.SAMPLE_MAXIMUM).astype(numpy.int32)


# Whole model ------------------------------------------------------------------------------------------------

def shaped_signal(samples: numpy.ndarray, sample_rate_hz: float, spectrum_variant: str,
                  calibration: Calibration | None) -> numpy.ndarray:
    """Steps 1-3: 16 kHz signal in the input's units, before level gain."""
    if spectrum_variant not in SPECTRUM_VARIANTS:
        raise ValueError(f"spectrum_variant must be one of {SPECTRUM_VARIANTS}")
    shaped = apply_microphone_response(remove_mean_and_resample(samples, sample_rate_hz))
    if spectrum_variant == "matched_to_own_recordings":
        if calibration is None:
            raise ValueError("the matched variant needs a calibration")
        shaped = apply_spectrum_correction(shaped, calibration)
    return shaped


def per_recording_gain(shaped: numpy.ndarray, level_condition: str, calibration: Calibration, beat_times_s,
                       time_offset_s: float) -> float:
    targets = calibration.targets
    if level_condition == "rest":
        if calibration.level_measure == "median_beat_peak" and beat_times_s is not None and len(beat_times_s) >= 2:
            level = heart_sound_level(shaped, beat_times_s, time_offset_s, "median_beat_peak")
            return targets["rest_level_median_beat_peak"] / level
        return targets["rest_level_envelope_95th_percentile"] / heart_sound_level(
            shaped, level_measure="envelope_95th_percentile")
    if beat_times_s is not None and len(beat_times_s) >= 2:
        gains = per_beat_gains_to_full_scale(shaped, beat_times_s, TARGET_SAMPLE_RATE_HZ, time_offset_s)
        return float(numpy.quantile(gains, targets["overload_beat_share"]))
    return float(numpy.quantile(per_sample_gains_to_full_scale(shaped), targets["overload_sample_share"]))


def model_through_capture_chain(samples: numpy.ndarray, sample_rate_hz: float, *, level_condition: str,
                                spectrum_variant: str = "microphone_only", calibration: Calibration | None = None,
                                seed: int = 0, per_recording_normalisation: bool = False,
                                beat_times_s=None, beat_time_offset_s: float = 0.0) -> numpy.ndarray:
    """Public recording -> int32 24-bit samples at 16 kHz as the real capture chain would deliver them.

    level_condition: "rest" or "overload". calibration: from `fit_calibration` / `load_calibration` (required).
    per_recording_normalisation: gain from this recording alone instead of the dataset gain (beat_times_s, in
    seconds of the input, is used for the overload condition; without it the sample share is used)."""
    if calibration is None:
        raise ValueError("a calibration is required: fit_calibration(...) or load_calibration(dataset_name)")
    if level_condition not in LEVEL_CONDITIONS:
        raise ValueError(f"level_condition must be one of {LEVEL_CONDITIONS}")
    shaped = shaped_signal(samples, sample_rate_hz, spectrum_variant, calibration)
    if per_recording_normalisation:
        gain = per_recording_gain(shaped, level_condition, calibration, beat_times_s, beat_time_offset_s)
    else:
        gain = calibration.gain[spectrum_variant][level_condition]
    with_noise = add_missing_noise_floor(shaped * gain, calibration, numpy.random.default_rng(seed))
    return limit_to_24_bit(with_noise)


# Calibration ------------------------------------------------------------------------------------------------

def _as_item(item) -> tuple[numpy.ndarray, float, numpy.ndarray | None]:
    if isinstance(item, dict):
        return numpy.asarray(item["samples"]), float(item["sample_rate_hz"]), item.get("beat_times_s")
    if isinstance(item, (tuple, list)):
        samples, sample_rate_hz = item[0], item[1]
        beat_times = item[2] if len(item) > 2 else None
        return numpy.asarray(samples), float(sample_rate_hz), beat_times
    return numpy.asarray(item.samples), float(item.sample_rate_hz), getattr(item, "beat_times_s", None)


def fit_calibration(dataset_name: str, recordings_iterable: Iterable, *, save: bool = True) -> Calibration:
    """Fit gains, spectrum correction and noise target for one dataset.

    Each item: (samples, sample_rate_hz[, beat_times_s]) or a dict / object with these names; beat times in
    seconds from the start of the given samples (None if not available)."""
    targets = own_targets()
    items = [_as_item(item) for item in recordings_iterable]
    if not items:
        raise ValueError("no recordings given")
    shaped_by_variant = {"microphone_only": [shaped_signal(samples, rate, "microphone_only", None)
                                             for samples, rate, _ in items]}
    dataset_shapes = numpy.array([band_shape_db(shaped, TARGET_SAMPLE_RATE_HZ)
                                  for shaped in shaped_by_variant["microphone_only"]])
    dataset_median_shape = numpy.median(dataset_shapes, axis=0)
    correction_db = smooth_limited_correction(targets["median_band_shape_db"] - dataset_median_shape)
    beats_available = all(beat_times is not None and len(beat_times) >= 2 for _, _, beat_times in items)
    level_measure = "median_beat_peak" if beats_available else "envelope_95th_percentile"
    calibration = Calibration(
        dataset_name=dataset_name,
        source_sample_rates_hz=sorted({rate for _, rate, _ in items}),
        recording_count=len(items),
        gain={},
        overload_share_method="beats" if beats_available else "samples",
        level_measure=level_measure,
        spectrum_correction_band_centres_hz=match_band_centres_hz().tolist(),
        spectrum_correction_db=correction_db.tolist(),
        own_median_band_shape_db=targets["median_band_shape_db"].tolist(),
        dataset_median_band_shape_db=dataset_median_shape.tolist(),
        noise_band_centres_hz=noise_band_centres_hz().tolist(),
        own_floor_band_power_db=(10.0 * numpy.log10(numpy.maximum(targets["median_floor_band_power"], 1e-30))).tolist(),
        targets={
            "rest_level": targets["rest_level"][level_measure],
            "rest_level_median_beat_peak": targets["rest_level"]["median_beat_peak"],
            "rest_level_envelope_95th_percentile": targets["rest_level"]["envelope_95th_percentile"],
            "overload_beat_share": targets["overload_beat_share"],
            "overload_beats_at_limit": targets["overload_beats_at_limit"],
            "overload_beat_count": targets["overload_beat_count"],
            "overload_sample_share": targets["overload_sample_share"],
        },
        created=datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        notes=[
            "level measure (field level_measure): median per-beat peak of the zero-phase 20-400 Hz band, same on"
            " own and public data; 95th percentile of its Hilbert envelope only if a dataset has no beat times",
            "rest target: median of that level over rest-1, rest-2, elevated-1",
            "overload target: share of beats with a sample at a 24-bit limit in elevated-2 and elevated-3",
            "overload share method 'samples' means the dataset had no beat times: share of samples at a limit",
            "noise target: median over the five own recordings of the 10th percentile of 250 ms band power",
            "spectrum correction contains chest-piece, tube, sensor AND person differences (empirical)",
        ],
    )
    shaped_by_variant["matched_to_own_recordings"] = [apply_spectrum_correction(shaped, calibration)
                                                      for shaped in shaped_by_variant["microphone_only"]]
    for variant, shaped_list in shaped_by_variant.items():
        levels = [heart_sound_level(shaped, beat_times, 0.0, level_measure)
                  for shaped, (_, _, beat_times) in zip(shaped_list, items)]
        rest_gain = targets["rest_level"][level_measure] / float(numpy.median(levels))
        if beats_available:
            gains = numpy.concatenate([per_beat_gains_to_full_scale(shaped, beat_times, TARGET_SAMPLE_RATE_HZ)
                                       for shaped, (_, _, beat_times) in zip(shaped_list, items)])
            overload_gain = float(numpy.quantile(gains, targets["overload_beat_share"]))
        else:
            gains = numpy.concatenate([per_sample_gains_to_full_scale(shaped) for shaped in shaped_list])
            overload_gain = float(numpy.quantile(gains, targets["overload_sample_share"]))
        calibration.gain[variant] = {"rest": rest_gain, "overload": overload_gain}
    if save:
        calibration.save()
    return calibration
