"""Per-recording measurement of the listening-filter candidates on CirCor recordings after the capture-chain model.

One call of measure_recording() models one CirCor recording through the capture chain, runs every candidate through
the device chain (filter, fixed gain, 100 % volume, 24-bit saturation) and returns the per-cycle phase energies and
the per-recording quantities the analysis needs. Results are cached per recording and condition.
"""
import json
import sys
import zlib
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).resolve().parent
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

import numpy  # noqa: E402
from scipy import signal  # noqa: E402

import listening_common as common  # noqa: E402
from listening_common import SAMPLE_RATE_HZ, database  # noqa: E402
from hfs import circor  # noqa: E402

STUDY_DIRECTORY = SOURCE_DIRECTORY.parent
OUTPUT_DIRECTORY = STUDY_DIRECTORY / "listening-public"
CACHE_DIRECTORY = OUTPUT_DIRECTORY / "cache"
CHAIN_MODEL_MARKER = SOURCE_DIRECTORY / "hfs" / "CHAIN_MODEL_READY"
CACHE_VERSION = 3

# The device filters run continuously; the simulation starts them from rest, so the first part of every modelled
# recording contains a start-up transient that a running device would not produce.
SETTLING_SECONDS = 0.5
WELCH_SEGMENT_SAMPLES = 16384
SPECTRUM_TRANSFORM_SAMPLES = 8192
SPECTRUM_BAND_EDGES_HZ = numpy.geomspace(20.0, 8000.0, 8 * 12 + 1)
PHASES = ("S1", "systole", "S2", "diastole")
GAIN_SETTINGS = ("fixed", "zero")
WEIGHTINGS = ("a_weighted", "unweighted")

# (identifier, design entry, fixed gain in dB from run 1 or None when it has to be computed, group)
CANDIDATES = [
    ("raw", {"family": "raw"}, -0.010, "shortlist"),
    ("butterworth_hp2_40_lp2_800", {"family": "butterworth", "highpass_hz": 40, "lowpass_hz": 800}, -0.236, "shortlist"),
    ("butterworth_hp2_100_lp2_800", {"family": "butterworth", "highpass_hz": 100, "lowpass_hz": 800}, 5.975, "shortlist"),
    ("butterworth_hp4_100_lp4_800", {"family": "butterworth", "highpass_hz": 100, "lowpass_hz": 800,
                                     "highpass_order": 4, "lowpass_order": 4}, 7.200, "shortlist"),
    ("butterworth_hp4_150_lp4_800", {"family": "butterworth", "highpass_hz": 150, "lowpass_hz": 800,
                                     "highpass_order": 4, "lowpass_order": 4}, 9.760, "shortlist"),
    ("elliptic_hp4_60_lp4_800", {"family": "elliptic", "highpass_hz": 60, "lowpass_hz": 800,
                                 "highpass_order": 4, "lowpass_order": 4}, 3.840, "shortlist"),
    ("butterworth_hp2_80_lp0_none", {"family": "butterworth", "highpass_hz": 80, "lowpass_hz": None}, 3.460, "shortlist"),
    ("butterworth_hp2_25_lp2_150", {"family": "butterworth", "highpass_hz": 25, "lowpass_hz": 150}, -1.843, "shortlist"),
    ("butterworth_hp2_40_lp2_150", {"family": "butterworth", "highpass_hz": 40, "lowpass_hz": 150}, None,
     "bpm recommendation"),
    ("butterworth_hp2_40_lp2_400", {"family": "butterworth", "highpass_hz": 40, "lowpass_hz": 400}, None, "extra"),
    ("butterworth_hp2_40_lp2_1000", {"family": "butterworth", "highpass_hz": 40, "lowpass_hz": 1000}, None, "extra"),
    ("butterworth_hp2_60_lp2_800", {"family": "butterworth", "highpass_hz": 60, "lowpass_hz": 800}, None, "extra"),
    ("butterworth_hp2_80_lp2_800", {"family": "butterworth", "highpass_hz": 80, "lowpass_hz": 800}, None, "extra"),
    ("butterworth_hp2_100_lp2_600", {"family": "butterworth", "highpass_hz": 100, "lowpass_hz": 600}, None, "extra"),
    ("butterworth_hp2_100_lp2_1000", {"family": "butterworth", "highpass_hz": 100, "lowpass_hz": 1000}, None, "extra"),
    ("butterworth_hp2_100_lp2_2000", {"family": "butterworth", "highpass_hz": 100, "lowpass_hz": 2000}, None, "extra"),
    ("butterworth_hp2_100_lp0_none", {"family": "butterworth", "highpass_hz": 100, "lowpass_hz": None}, None, "extra"),
]
CANDIDATE_IDENTIFIERS = [identifier for identifier, _, _, _ in CANDIDATES]
SHORTLIST_IDENTIFIERS = [identifier for identifier, _, _, group in CANDIDATES if group == "shortlist"]

CONDITIONS = {
    "rest_microphone_only": {"level_condition": "rest", "spectrum_variant": "microphone_only"},
    "overload_microphone_only": {"level_condition": "overload", "spectrum_variant": "microphone_only"},
    "rest_matched_to_own_recordings": {"level_condition": "rest", "spectrum_variant": "matched_to_own_recordings"},
}
FIXED_GAINS_PATH = OUTPUT_DIRECTORY / "fixed_gains.json"
DELAYS_PATH = OUTPUT_DIRECTORY / "chain_model_delays.json"


CALIBRATION_PATH = STUDY_DIRECTORY / "calibration" / "chain_model_circor.json"


def chain_model_available() -> bool:
    return CHAIN_MODEL_MARKER.exists() and CALIBRATION_PATH.exists()


def recording_seed(file_stem: str) -> int:
    return zlib.crc32(file_stem.encode("utf-8"))


def model_capture(samples: numpy.ndarray, sample_rate_hz: int, condition: str, seed: int = 0) -> numpy.ndarray:
    """24-bit integer capture at 16 kHz. Without the chain model, a plain resampling stand-in for development only."""
    if chain_model_available():
        from hfs import chain_model
        settings = CONDITIONS[condition]
        calibration = chain_model.load_calibration("circor")
        return numpy.asarray(chain_model.model_through_capture_chain(
            samples, sample_rate_hz, level_condition=settings["level_condition"],
            spectrum_variant=settings["spectrum_variant"], calibration=calibration, seed=seed))
    upsampled = signal.resample_poly(samples, SAMPLE_RATE_HZ, sample_rate_hz)
    return numpy.clip(numpy.rint(upsampled * 0.25 * common.FULL_SCALE), common.SAMPLE_MINIMUM,
                      common.SAMPLE_MAXIMUM).astype(numpy.int32)


def measure_delay_seconds(file_stem: str, condition: str) -> float:
    """Delay of the chain model output relative to the dataset time axis, from the cross-correlation peak of the
    band-limited signals (positive: the modelled capture lags)."""
    recording = circor.load_recording(file_stem)
    capture = model_capture(recording.samples, recording.sample_rate_hz, condition).astype(numpy.float64)
    reference = signal.resample_poly(recording.samples, SAMPLE_RATE_HZ, recording.sample_rate_hz)
    band = signal.butter(4, [50.0, 400.0], btype="bandpass", fs=SAMPLE_RATE_HZ, output="sos")
    capture_band = signal.sosfiltfilt(band, capture)
    reference_band = signal.sosfiltfilt(band, reference)
    length = min(len(capture_band), len(reference_band))
    correlation = signal.correlate(capture_band[:length], reference_band[:length], mode="full", method="fft")
    lags = signal.correlation_lags(length, length, mode="full")
    allowed = numpy.abs(lags) <= int(0.2 * SAMPLE_RATE_HZ)
    best = lags[allowed][numpy.argmax(correlation[allowed])]
    return float(best / SAMPLE_RATE_HZ)


def load_fixed_gains() -> dict[str, float]:
    return json.loads(FIXED_GAINS_PATH.read_text(encoding="utf-8"))["gains_db"]


def load_delays() -> dict[str, float]:
    if not DELAYS_PATH.exists():
        return {}
    return json.loads(DELAYS_PATH.read_text(encoding="utf-8"))["delay_seconds"]


def cache_path(condition: str, file_stem: str) -> Path:
    folder = condition if chain_model_available() else f"{condition}_resampling_stand_in"
    return CACHE_DIRECTORY / folder / f"{file_stem}.npz"


def cycle_windows(recording, delay_seconds: float, sample_count: int) -> numpy.ndarray:
    """Sample index windows [start, stop) per complete cycle and phase at 16 kHz, shifted by the model delay; cycles
    that start inside the settling time or run past the end are dropped. Shape (cycles, phases, 2)."""
    windows = []
    for cycle in circor.heart_cycle_intervals(recording.segments):
        phases = [cycle.s1, cycle.systole, cycle.s2, cycle.diastole]
        indices = [(int(round((start + delay_seconds) * SAMPLE_RATE_HZ)), int(round((end + delay_seconds) * SAMPLE_RATE_HZ)))
                   for start, end in phases]
        if indices[0][0] < SETTLING_SECONDS * SAMPLE_RATE_HZ or indices[-1][1] > sample_count:
            continue
        if any(stop - start < 2 for start, stop in indices):
            continue
        windows.append(indices)
    return numpy.array(windows, dtype=numpy.int64).reshape(-1, 4, 2)


def window_energies(signal_full_scale: numpy.ndarray, windows: numpy.ndarray) -> numpy.ndarray:
    cumulative = numpy.concatenate([[0.0], numpy.cumsum(signal_full_scale.astype(numpy.float64) ** 2)])
    return cumulative[windows[..., 1]] - cumulative[windows[..., 0]]


def systole_spectrum(output_full_scale: numpy.ndarray, windows: numpy.ndarray, phase_index: int) -> numpy.ndarray:
    """Mean power per band (1/12 octave, 20 Hz-8 kHz) over the cycles' segments of one phase, each segment Hann
    windowed and normalised by its window energy, so long and short segments count equally per cycle."""
    frequencies = numpy.fft.rfftfreq(SPECTRUM_TRANSFORM_SAMPLES, 1.0 / SAMPLE_RATE_HZ)
    accumulated = numpy.zeros(len(frequencies))
    count = 0
    for start, stop in windows[:, phase_index]:
        segment = output_full_scale[start:stop][:SPECTRUM_TRANSFORM_SAMPLES]
        if len(segment) < 64:
            continue
        window = numpy.hanning(len(segment))
        spectrum = numpy.abs(numpy.fft.rfft(segment * window, SPECTRUM_TRANSFORM_SAMPLES)) ** 2
        accumulated += spectrum / numpy.sum(window ** 2)
        count += 1
    if count == 0:
        return numpy.full(len(SPECTRUM_BAND_EDGES_HZ) - 1, numpy.nan)
    density = accumulated / count
    band_index = numpy.digitize(frequencies, SPECTRUM_BAND_EDGES_HZ) - 1
    bands = numpy.full(len(SPECTRUM_BAND_EDGES_HZ) - 1, numpy.nan)
    for index in range(len(bands)):
        selected = band_index == index
        if numpy.any(selected):
            bands[index] = density[selected].mean()
    return bands


def iso226_power(output_full_scale: numpy.ndarray) -> float:
    frequencies, density = signal.welch(output_full_scale, fs=SAMPLE_RATE_HZ,
                                        nperseg=min(WELCH_SEGMENT_SAMPLES, len(output_full_scale)))
    resolution = frequencies[1] - frequencies[0]
    return float(numpy.sum(density * resolution * 10.0 ** (common.iso226_weighting_db(frequencies) / 10.0)))


CANDIDATES_BY_IDENTIFIER = {identifier: (identifier, entry, gain, group) for identifier, entry, gain, group in CANDIDATES}


def candidates_for_condition(condition: str) -> list[str]:
    return CANDIDATE_IDENTIFIERS if condition == "rest_microphone_only" else SHORTLIST_IDENTIFIERS


def measure_recording(file_stem: str, condition: str, gains_db: dict[str, float], delay_seconds: float) -> dict:
    recording = circor.load_recording(file_stem)
    capture = model_capture(recording.samples, recording.sample_rate_hz, condition, recording_seed(file_stem))
    identifiers = candidates_for_condition(condition)
    windows = cycle_windows(recording, delay_seconds, len(capture))
    settled = slice(int(SETTLING_SECONDS * SAMPLE_RATE_HZ), None)
    candidate_count = len(identifiers)
    energies = numpy.zeros((candidate_count, len(GAIN_SETTINGS), len(WEIGHTINGS), len(windows), 4))
    clipped_fixed = numpy.zeros(candidate_count, dtype=numpy.int64)
    clipped_zero = numpy.zeros(candidate_count, dtype=numpy.int64)
    headroom = numpy.zeros(candidate_count)
    a_weighted_level = numpy.zeros(candidate_count)
    iso226_level = numpy.zeros(candidate_count)
    k_gated_at_fixed = numpy.zeros(candidate_count)
    spectrum = None
    for candidate_index, identifier in enumerate(identifiers):
        entry = CANDIDATES_BY_IDENTIFIER[identifier][1]
        candidate = common.candidate_from_entry(entry)
        filtered = common.apply_filter_blockwise(candidate, capture)
        headroom[candidate_index] = common.zero_saturation_gain_db(filtered[settled])
        for gain_index, gain_db in enumerate((gains_db[identifier], 0.0)):
            output_values = common.apply_gain_and_output(filtered, gain_db)
            clipped = common.count_clipped(output_values[settled])
            output = common.to_full_scale(output_values)
            a_weighted = common.weighted(output, common.A_WEIGHTING)
            if len(windows):
                energies[candidate_index, gain_index, 0] = window_energies(a_weighted, windows)
                energies[candidate_index, gain_index, 1] = window_energies(output, windows)
            if gain_index == 0:
                clipped_fixed[candidate_index] = clipped
                k_weighted = common.weighted(output[settled], common.K_WEIGHTING)
                k_gated_at_fixed[candidate_index] = common.bs1770_loudness(
                    common.bs1770_block_powers(k_weighted, SAMPLE_RATE_HZ))[0]
            else:
                clipped_zero[candidate_index] = clipped
                a_weighted_level[candidate_index] = database(float(numpy.mean(a_weighted[settled] ** 2)))
                iso226_level[candidate_index] = database(iso226_power(output[settled]))
                if identifier == "raw" and len(windows):
                    spectrum = numpy.stack([systole_spectrum(output, windows, 1), systole_spectrum(output, windows, 3)])
    if spectrum is None:
        spectrum = numpy.full((2, len(SPECTRUM_BAND_EDGES_HZ) - 1), numpy.nan)
    return {
        "cache_version": CACHE_VERSION, "energies": energies, "window_samples": (windows[..., 1] - windows[..., 0]),
        "clipped_fixed": clipped_fixed, "clipped_zero": clipped_zero, "headroom_db": headroom,
        "a_weighted_level_db": a_weighted_level, "iso226_level_db": iso226_level,
        "k_gated_at_fixed_gain_lufs": k_gated_at_fixed, "raw_spectrum": spectrum,
        "capture_samples": len(capture), "input_clipped": common.count_clipped(capture[settled]),
        "chain_model": chain_model_available(), "delay_seconds": delay_seconds,
        "fixed_gains_db": numpy.array([gains_db[identifier] for identifier in identifiers]),
        "candidate_identifiers": numpy.array(identifiers),
    }


def measure_and_cache(arguments: tuple[str, str]) -> tuple[str, str, bool]:
    file_stem, condition = arguments
    path = cache_path(condition, file_stem)
    if path.exists():
        return file_stem, condition, True
    try:
        result = measure_recording(file_stem, condition, load_fixed_gains(), load_delays().get(condition, 0.0))
    except Exception as error:  # noqa: BLE001
        print(f"{file_stem} {condition}: {error!r}", flush=True)
        return file_stem, condition, False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.npz")
    numpy.savez_compressed(temporary, **result)
    temporary.replace(path)
    return file_stem, condition, True


def read_cache(condition: str, file_stem: str) -> dict | None:
    path = cache_path(condition, file_stem)
    if not path.exists():
        return None
    with numpy.load(path) as data:
        result = {key: data[key] for key in data.files}
    if int(result["cache_version"]) != CACHE_VERSION:
        return None
    return result
