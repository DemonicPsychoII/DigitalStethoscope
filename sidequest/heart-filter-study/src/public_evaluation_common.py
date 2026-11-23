"""Shared pieces of the run-2 BPM evaluation on EPHNOGRAM: candidates, estimator variants, the streaming
estimator driver for long records, the per-record cache and the metric definitions of run 1."""
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpm_evaluate
from hfs import bpm_estimator
from hfs.bpm_estimator import EstimatorConfiguration
from hfs.recordings import SAMPLE_MAXIMUM, SAMPLE_MINIMUM, STUDY_DIRECTORY

CACHE_DIRECTORY = STUDY_DIRECTORY / "cache" / "bpm-public"
RESULTS_DIRECTORY = STUDY_DIRECTORY / "results-public"
REFERENCE_DIRECTORY = STUDY_DIRECTORY / "reference-public" / "ephnogram"
EVALUATION_VERSION = "1"
FIRST_SCORED_END_TIME_SECONDS = 10

FIRST_DRAFT = EstimatorConfiguration()
HALF_CHECK_ONLY = replace(FIRST_DRAFT, peak_choice="half_check")
FINAL_METHOD = replace(FIRST_DRAFT, envelope_lowpass="two_pole", envelope_lowpass_hz=5.0, peak_choice="half_check")
ALTERNATIVE_METHOD = replace(FIRST_DRAFT, envelope_lowpass="two_pole", envelope_lowpass_hz=8.0, peak_choice="half_check")
ESTIMATOR_VARIANTS = {"first_draft": FIRST_DRAFT, "half_check_only": HALF_CHECK_ONLY, "final": FINAL_METHOD,
                      "alternative_8hz": ALTERNATIVE_METHOD}
ESTIMATOR_LABELS = {"first_draft": "first draft (one smoothing step at 12 Hz, highest peak)",
                    "half_check_only": "half-rate check only",
                    "final": "final run-1 method (two smoothing steps at 5 Hz + half-rate check)",
                    "alternative_8hz": "alternative (two smoothing steps at 8 Hz + half-rate check)"}

CONDITIONS = {"rest": ("rest", "microphone_only"), "overload": ("overload", "microphone_only"),
              "rest_matched": ("rest", "matched_to_own_recordings")}

specification = bpm_evaluate.specification


def candidate_specifications():
    """Ordered {identifier: spec}; the order is the computation priority (main candidates first)."""
    specs = [specification("raw", None, None)]
    specs += [specification("butterworth", 25, 150), specification("butterworth", 40, 150),
              specification("butterworth", 40, 800), specification("butterworth", 100, 800)]
    specs += [specification("butterworth", edge, 150) for edge in (10, 20, 30, 50, 60, 80)]
    specs += [specification("butterworth", lower, upper) for lower in (40, 25) for upper in (100, 200, 300, 400)]
    specs += [specification("butterworth", lower, 150, 4, 4) for lower in (25, 40, 60)]
    specs += [specification(family, 40, 150) for family in ("bessel", "chebyshev1", "elliptic")]
    shortlist = json.loads((STUDY_DIRECTORY / "listening" / "shortlist.json").read_text(encoding="utf-8"))
    for entry in shortlist["candidates"]:
        if entry["family"] == "raw":
            continue
        specs.append(specification(entry["family"], entry.get("highpass_hz"), entry.get("lowpass_hz"),
                                   entry.get("highpass_order", 2), entry.get("lowpass_order", 2)))
    specs.append(specification("decimated", 30, 300, 4, 2))
    specs.append(specification("fir", 40, 150, fir_tap_count=129))
    ordered = {}
    for spec in specs:
        ordered.setdefault(bpm_evaluate.candidate_identifier(spec), spec)
    return ordered


MAIN_CANDIDATES = ("raw", "butterworth_hp2_25_lp2_150", "butterworth_hp2_40_lp2_150", "butterworth_hp2_40_lp2_800",
                   "butterworth_hp2_100_lp2_800")
LOWER_EDGE_SWEEP = {None: "raw", 10: "butterworth_hp2_10_lp2_150", 20: "butterworth_hp2_20_lp2_150",
                    25: "butterworth_hp2_25_lp2_150", 30: "butterworth_hp2_30_lp2_150", 40: "butterworth_hp2_40_lp2_150",
                    50: "butterworth_hp2_50_lp2_150", 60: "butterworth_hp2_60_lp2_150", 80: "butterworth_hp2_80_lp2_150"}
RECOMMENDED = "butterworth_hp2_40_lp2_150"
PLANNED = "butterworth_hp2_25_lp2_150"
CANDIDATE_LABELS = {"raw": "no filter", PLANNED: "planned 25-150 Hz", RECOMMENDED: "recommended 40-150 Hz",
                    "butterworth_hp2_40_lp2_800": "40-800 Hz (listening design)",
                    "butterworth_hp2_100_lp2_800": "100-800 Hz (listening)"}


def estimate_record(filtered, input_rate_hz, configurations, clipped_per_second):
    """Equivalent to bpm_estimator.run_estimator with start time 0 for every configuration, but the envelope
    is computed for the whole record in one call: the envelope state carries sample by sample, so block
    boundaries do not change it. Configurations that differ only in the peak choice share one
    autocorrelation. Returns {configuration: array (end_time, bpm, valid, quality)}."""
    filtered = numpy.ascontiguousarray(filtered, dtype=numpy.float32)
    samples_per_update = int(round(configurations[0].update_seconds * input_rate_hz))
    update_count = filtered.shape[0] // samples_per_update
    groups = {}
    for configuration in configurations:
        groups.setdefault(replace(configuration, peak_choice="highest"), []).append(configuration)
    outcome = {}
    for envelope_configuration, members in groups.items():
        estimator = bpm_estimator.BPMEstimator(envelope_configuration, input_rate_hz)
        envelope = numpy.zeros(filtered.shape[0] // estimator.decimation_factor + 2, dtype=numpy.float32)
        bpm_estimator._envelope_block(filtered, estimator.rectification_code, estimator.lowpass_code,
                                      estimator.lowpass_coefficient, estimator.lowpass_state, estimator.counter_state,
                                      estimator.decimation_factor, estimator.boxcar_scale, envelope)
        rows = {member: numpy.full((update_count, 4), numpy.nan) for member in members}
        window_length = estimator.window_length
        for update_index in range(update_count):
            end_sample = (update_index + 1) * samples_per_update
            envelope_count = end_sample // estimator.decimation_factor
            estimator.clipped_since_update = int(clipped_per_second[update_index])
            if envelope_count >= window_length:
                estimator.ring_buffer[:] = envelope[envelope_count - window_length:envelope_count]
                estimator.ring_position = 0
                estimator.ring_filled = window_length
            else:
                estimator.ring_filled = envelope_count
            end_time = (update_index + 1) * envelope_configuration.update_seconds
            for member_index, member in enumerate(members):
                estimator.configuration = member
                if member_index == 0:
                    result = estimator.update()
                elif estimator.ring_filled >= window_length:
                    result = estimator._choose_peak()
                else:
                    result = bpm_estimator.EstimateResult(float("nan"), False, 0.0, 0.0, "window_not_full", float("nan"))
                rows[member][update_index] = (end_time, result.bpm, float(result.valid), result.quality)
        outcome.update(rows)
    return outcome


def clipped_per_second(samples_int24, sample_rate_hz=16000):
    flags = (samples_int24 >= SAMPLE_MAXIMUM) | (samples_int24 <= SAMPLE_MINIMUM)
    seconds = flags.shape[0] // sample_rate_hz
    return flags[:seconds * sample_rate_hz].reshape(seconds, sample_rate_hz).sum(axis=1)


def cache_path(record_name, condition, identifier):
    return CACHE_DIRECTORY / condition / record_name / f"{identifier}.npz"


def configuration_key(configuration):
    return EVALUATION_VERSION + ":" + configuration.key()


def cached_estimates(record_name, condition, identifier):
    path = cache_path(record_name, condition, identifier)
    if not path.exists():
        return {}
    with numpy.load(path) as archive:
        return {key: archive[key] for key in archive.files}


def store_estimates(record_name, condition, identifier, estimates_by_key):
    path = cache_path(record_name, condition, identifier)
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = cached_estimates(record_name, condition, identifier)
    merged.update(estimates_by_key)
    temporary = path.with_name(path.stem + ".partial.npz")
    numpy.savez(temporary, **merged)
    temporary.replace(path)


_DUPLICATES = None


def duplicate_records_excluded():
    """Records that store the same signal as another record under a different subject label; the later
    record name of each group is kept (ECGPCG0001 = 0031, ECGPCG0002 = 0069)."""
    global _DUPLICATES
    if _DUPLICATES is None:
        from hfs import ephnogram
        _DUPLICATES = frozenset(name for group in ephnogram.duplicate_signal_groups() for name in sorted(group)[:-1])
    return _DUPLICATES


def load_reference(record_name):
    path = REFERENCE_DIRECTORY / f"{record_name}.json"
    if not path.exists():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    return {int(round(window["end_time_s"])): window for window in document["windows"]}


HEART_RATE_BANDS = [(0, 70, "below 70"), (70, 90, "70-90"), (90, 110, "90-110"), (110, 130, "110-130"),
                    (130, 150, "130-150"), (150, 170, "150-170"), (170, 1000, "above 170")]


def heart_rate_band(reference_bpm):
    for low, high, label in HEART_RATE_BANDS:
        if low <= reference_bpm < high:
            return label
    return "none"


def error_type(estimate, reference):
    """Gross errors (more than 20 % off) split by the ratio estimate / reference."""
    if not numpy.isfinite(estimate):
        return "no estimate"
    ratio = estimate / reference
    if abs(ratio - 1.0) <= 0.2:
        return "none"
    for target, label in ((0.5, "half rate"), (2.0, "double rate"), (1.0 / 3.0, "one third")):
        if abs(ratio / target - 1.0) <= 0.1:
            return label
    return "other"


def metric_block(reference, estimate, valid):
    """Run-1 definitions (bpm_evaluate.metric_block) on pooled windows, without prefix."""
    if reference.size == 0:
        return {"window_count": 0}
    block = bpm_evaluate.metric_block(reference, estimate, valid, "")
    return block
