"""Whole-window BPM methods against run 1's causal method on the five own recordings.

Usage: python -I src/bpm_window_methods.py [--workers 4] [--methods key1,key2]
Windows: 8 s ending at every full second 10-60 s after the 2 s discard, exactly as src/bpm_evaluate.py.
Cache: cache/window/own/<recording>__<method>.json, so reruns only add.
"""
import argparse
import csv
import dataclasses
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy
from scipy import signal

import bpm_evaluate
from hfs import bpm_estimator, device_chain, filters, window_bpm
from hfs.recordings import RECORDING_NAMES, SAMPLE_MAXIMUM, SAMPLE_MINIMUM, STUDY_DIRECTORY, load_recording

CACHE_VERSION = "1"
CACHE_DIRECTORY = STUDY_DIRECTORY / "cache" / "window"
RESULTS_DIRECTORY = STUDY_DIRECTORY / "results-window"
SAMPLE_RATE_HZ = 16000
WINDOW_SAMPLES = 128000
FINAL_ESTIMATOR = window_bpm.FINAL_ESTIMATOR
ANTI_ALIAS_TAP_COUNT = filters.ANTI_ALIAS_TAP_COUNT
CAUSAL_BASELINES = {
    "causal_raw": ("raw", None, None),
    "causal_25_150": ("butterworth", 25, 150),
    "causal_40_150": ("butterworth", 40, 150),
    "causal_40_150_twice": ("butterworth", 40, 150),
}
# Same 2+2 sections run twice in a row while recording: the magnitude of the forward-backward filter, causal.
CAUSAL_SECTIONS_TWICE = ("causal_40_150_twice",)
BASELINE_KEY = "causal_40_150"
RUN_ONE_PUBLISHED = {"causal_40_150": (0.30, 0.35, 0), "causal_25_150": (0.30, 0.69, 1), "causal_raw": (0.42, 4.22, 16)}


# Method registry -----------------------------------------------------------------------------------------------

def _band_text(low, high):
    return f"{low:g}_{high:g}"


def method_registry():
    """key -> (input kind, method object). Input kinds: raw_16k, capture_1k, capture_2k, stored_envelope."""
    methods = {}
    edge_variants = [("reflect", 0.0), ("none", 0.0), ("discard", 0.25), ("discard", 0.5)]
    for low, high in ((25, 150), (40, 150), (30, 150), (40, 400), (25, 400)):
        for order in (1, 2):
            for edge_mode, discard in edge_variants:
                for envelope_mode, envelope_text in (("zero_phase_one_pole", "zpenv"), ("causal_two_pole", "causalenv")):
                    edge_text = edge_mode if not discard else f"discard{int(discard * 100):03d}"
                    key = f"zero_phase_{_band_text(low, high)}_order{order}_{edge_text}_{envelope_text}"
                    methods[key] = ("raw_16k", window_bpm.ZeroPhaseMethod(
                        key, low, high, order, "forward_backward", edge_mode, discard, envelope_mode))
    for low, high in ((40, 150), (25, 150)):
        for order in (1, 2):
            key = f"zero_phase_{_band_text(low, high)}_order{order}_matched_reflect_zpenv"
            methods[key] = ("raw_16k", window_bpm.ZeroPhaseMethod(key, low, high, order, "forward_backward", "reflect", 0.0,
                                                                  "zero_phase_one_pole", True))
    for order in (1, 2):
        for matched in (False, True):
            key = f"forward_twice_40_150_order{order}{'_matched' if matched else ''}_reflect_causalenv"
            methods[key] = ("raw_16k", window_bpm.ZeroPhaseMethod(key, 40, 150, order, "forward_twice", "reflect", 0.0,
                                                                  "causal_two_pole", matched))
    methods["forward_once_40_150_order2_reflect_causalenv"] = ("raw_16k", window_bpm.ZeroPhaseMethod(
        "forward_once_40_150_order2_reflect_causalenv", 40, 150, 2, "forward_once", "reflect", 0.0, "causal_two_pole"))
    for edge_mode in ("reflect", "none"):
        key = f"streamed_forward_backward_window_40_150_order2_{edge_mode}_zpenv"
        methods[key] = ("causal_filtered_16k", window_bpm.ZeroPhaseMethod(key, 40, 150, 2, "backward_only", edge_mode, 0.0,
                                                                         "zero_phase_one_pole"))
    for rate_text, kind in (("1k", "capture_1k"), ("2k", "capture_2k")):
        for low, high in ((40, 150), (25, 150)):
            for order, matched in ((2, False), (1, True), (2, True)):
                key = f"reduced_{rate_text}_zero_phase_{_band_text(low, high)}_order{order}{'_matched' if matched else ''}_reflect_zpenv"
                methods[key] = (kind, window_bpm.ZeroPhaseMethod(key, low, high, order, "forward_backward", "reflect", 0.0,
                                                                 "zero_phase_one_pole", matched))
        key = f"reduced_{rate_text}_forward_once_40_150_order2_reflect_causalenv"
        methods[key] = (kind, window_bpm.ZeroPhaseMethod(key, 40, 150, 2, "forward_once", "reflect", 0.0, "causal_two_pole"))
    for spike_removal, envelope_mode, text in ((True, "zero_phase_one_pole", "spikes_removed_zpenv"),
                                               (False, "homomorphic", "homomorphic"),
                                               (True, "homomorphic", "spikes_removed_homomorphic")):
        key = f"reduced_1k_zero_phase_40_150_order2_reflect_{text}"
        methods[key] = ("capture_1k", window_bpm.ZeroPhaseMethod(key, 40, 150, 2, "forward_backward", "reflect", 0.0,
                                                                 envelope_mode, False, spike_removal))
    for smoothing in (None, 5.0, 3.0):
        for taper in (0.0, 0.2):
            if smoothing is None and taper == 0.0:
                key = "stored_envelope_plain"
            else:
                key = f"stored_envelope_{'smooth' + format(smoothing, 'g') + 'hz' if smoothing else 'nosmooth'}_taper{int(taper * 100)}"
            methods[key] = ("stored_envelope", window_bpm.StoredEnvelopeMethod(key, smoothing, taper))
    methods["springer_heart_rate"] = ("raw_16k", window_bpm.SpringerHeartRateMethod("springer_heart_rate"))
    methods["springer_heart_rate_range_30_200"] = ("raw_16k", window_bpm.SpringerHeartRateMethod(
        "springer_heart_rate_range_30_200", minimum_seconds=0.3))
    methods["springer_heart_rate_half_check"] = ("raw_16k", window_bpm.SpringerHeartRateMethod(
        "springer_heart_rate_half_check", peak_choice="half_check"))
    for rate in (50, 100):
        for peak_choice, minimum_seconds, text in (("highest_in_range", 0.5, "highest_30_120"),
                                                   ("highest_in_range", 0.3, "highest_30_200"),
                                                   ("half_check", 0.3, "half_check")):
            key = f"springer_envelopes_combined_{rate}hz_{text}"
            methods[key] = ("raw_16k", window_bpm.SpringerEnvelopesCombinedMethod(
                key, feature_rate_hz=rate, minimum_seconds=minimum_seconds, peak_choice=peak_choice))
    return methods


# Inputs per recording ------------------------------------------------------------------------------------------

def anti_alias_taps(output_rate_hz):
    return signal.firwin(ANTI_ALIAS_TAP_COUNT, 0.4 * output_rate_hz, fs=SAMPLE_RATE_HZ, window=("kaiser", 6.0)).astype(numpy.float32)


def capture_reduced(normalised, output_rate_hz):
    """Causal capture-time rate reduction: run 1's 64-tap anti-alias FIR, keep the last sample of each group."""
    factor = SAMPLE_RATE_HZ // output_rate_hz
    filtered = signal.lfilter(anti_alias_taps(output_rate_hz).astype(numpy.float64), [1.0], normalised.astype(numpy.float64))
    return filtered[factor - 1::factor].astype(numpy.float32)


def stored_envelope_stream(normalised):
    """Run 1's causal chain: 40-150 Hz 2+2 Butterworth, absolute value, two one-poles at 5 Hz, 100 values per second."""
    candidate = filters.design_filter("butterworth", 40, 150)
    filtered = device_chain.apply_filter_to_normalised(candidate, normalised)
    coefficient = numpy.float32(1.0 - numpy.exp(-2.0 * numpy.pi * 5.0 / SAMPLE_RATE_HZ))
    output = numpy.zeros(filtered.shape[0] // 160 + 2, dtype=numpy.float32)
    written = bpm_estimator._envelope_block(filtered, 0, 1, coefficient, numpy.zeros(2, numpy.float32),
                                            numpy.zeros(1, numpy.int64), 160, numpy.float32(1 / 160), output)
    return output[:written]


class WindowSource:
    """Signals of one recording; window(end_sample_16k, kind) returns the last 8 s of that input."""

    def __init__(self, normalised, clipped_flags):
        self.normalised = normalised
        self.clipped_flags = clipped_flags
        self._inputs = {}

    def signal_for(self, kind):
        if kind not in self._inputs:
            if kind == "raw_16k":
                self._inputs[kind] = (self.normalised, SAMPLE_RATE_HZ)
            elif kind == "capture_1k":
                self._inputs[kind] = (capture_reduced(self.normalised, 1000), 1000)
            elif kind == "capture_2k":
                self._inputs[kind] = (capture_reduced(self.normalised, 2000), 2000)
            elif kind == "causal_filtered_16k":
                candidate = filters.design_filter("butterworth", 40, 150)
                self._inputs[kind] = (device_chain.apply_filter_to_normalised(candidate, self.normalised), SAMPLE_RATE_HZ)
            elif kind == "stored_envelope":
                self._inputs[kind] = (stored_envelope_stream(self.normalised), window_bpm.ENVELOPE_RATE_HZ)
            else:
                raise ValueError(kind)
        return self._inputs[kind]

    def window(self, end_sample, kind):
        values, rate = self.signal_for(kind)
        stop = end_sample * rate // SAMPLE_RATE_HZ
        length = int(window_bpm.WINDOW_SECONDS * rate)
        return values[stop - length:stop], rate

    def clipped_share(self, end_sample):
        return float(self.clipped_flags[end_sample - WINDOW_SAMPLES:end_sample].mean())


def estimate_windows(source, method_kind, method, end_samples_by_time):
    rows = []
    for end_time, end_sample in end_samples_by_time.items():
        window, rate = source.window(end_sample, method_kind)
        result = method.estimate(window, rate)
        valid = bool(result.valid) and source.clipped_share(end_sample) <= FINAL_ESTIMATOR.clipping_invalid_share
        bpm = float(result.bpm) if numpy.isfinite(result.bpm) else float("nan")
        rows.append([int(end_time), bpm, valid, float(result.quality), 0.0, result.details.get("reason", "")])
    return rows


def causal_rows(normalised, clipped_flags, baseline_key, start_time_seconds, first_end, last_end):
    family, low, high = CAUSAL_BASELINES[baseline_key]
    candidate = filters.design_filter(family, low, high)
    if baseline_key in CAUSAL_SECTIONS_TWICE:
        candidate = dataclasses.replace(candidate, identifier=candidate.identifier + "_twice",
                                        second_order_sections=numpy.vstack([candidate.second_order_sections] * 2))
    filtered = device_chain.apply_filter_to_normalised(candidate, normalised)
    results, _ = bpm_estimator.run_estimator(filtered, candidate.output_rate_hz, FINAL_ESTIMATOR, clipped_flags,
                                             start_time_seconds=start_time_seconds, first_end_time_seconds=first_end,
                                             last_end_time_seconds=last_end)
    return [[end_time, result.bpm, result.valid, result.quality, result.margin, result.reason] for end_time, result in results.items()]


# Own recordings ------------------------------------------------------------------------------------------------

def own_cache_path(recording, method_key):
    return CACHE_DIRECTORY / "own" / f"{recording}__{method_key}__v{CACHE_VERSION}.json"


def own_end_samples():
    # run_estimator: after k seconds of samples the update time is 2 + k, so window end time T ends at sample (T - 2) * 16000.
    return {end_time: (end_time - 2) * SAMPLE_RATE_HZ for end_time in range(10, 61)}


def own_work_item(item):
    recording, method_keys = item
    missing = [key for key in method_keys if not own_cache_path(recording, key).exists()]
    if not missing:
        return recording, 0
    samples = load_recording(recording)
    clipped_flags = ((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM)).astype(numpy.int8)
    normalised = device_chain.normalise(samples)
    registry = method_registry()
    source = WindowSource(normalised, clipped_flags)
    for key in missing:
        started = time.perf_counter()
        if key in CAUSAL_BASELINES:
            rows = causal_rows(normalised, clipped_flags, key, 2.0, 10, 60)
        else:
            kind, method = registry[key]
            rows = estimate_windows(source, kind, method, own_end_samples())
        path = own_cache_path(recording, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"recording": recording, "method": key, "rows": rows,
                                    "seconds": time.perf_counter() - started}))
    return recording, len(missing)


def error_types(reference, estimate):
    ratio = estimate / reference
    half = numpy.abs(ratio - 0.5) <= 0.05
    third = numpy.abs(ratio - 1 / 3) <= 1 / 30
    double = numpy.abs(ratio - 2.0) <= 0.2
    gross = numpy.abs(estimate - reference) > 0.2 * reference
    return {"half_rate_count": int(half.sum()), "third_rate_count": int(third.sum()), "double_rate_count": int(double.sum()),
            "other_gross_count": int((gross & ~half & ~third & ~double).sum())}


def describe_method(key, registry):
    if key in CAUSAL_BASELINES:
        family, low, high = CAUSAL_BASELINES[key]
        return {"group": "causal baseline (run 1)", "input": "16 kHz stream", "band_hz": "" if low is None else f"{low}-{high}"}
    kind, method = registry[key]
    group = type(method).__name__
    band = ""
    if hasattr(method, "highpass_hz"):
        band = f"{method.highpass_hz}-{method.lowpass_hz}"
    return {"group": group, "input": kind, "band_hz": band}


def run_own(arguments):
    registry = method_registry()
    method_keys = list(CAUSAL_BASELINES) + list(registry)
    if arguments.methods:
        method_keys = [key for key in method_keys if key in arguments.methods.split(",") or key in CAUSAL_BASELINES]
    started = time.perf_counter()
    items = [(recording, method_keys) for recording in RECORDING_NAMES]
    # Split per recording and method group so four workers stay busy.
    split_items = []
    for recording, keys in items:
        for start in range(0, len(keys), 8):
            split_items.append((recording, keys[start:start + 8]))
    with ProcessPoolExecutor(max_workers=arguments.workers) as executor:
        computed = sum(count for _, count in executor.map(own_work_item, split_items))
    print(f"own recordings: {computed} (recording, method) results computed in {time.perf_counter() - started:.0f} s")
    reference = bpm_evaluate.load_reference(STUDY_DIRECTORY / "reference")
    table_rows = []
    per_window = {}
    for key in method_keys:
        estimates = {recording: json.loads(own_cache_path(recording, key).read_text())["rows"] for recording in RECORDING_NAMES}
        arrays = bpm_evaluate.aligned_arrays(estimates, reference)
        metrics = bpm_evaluate.compute_metrics(arrays)
        all_reference = numpy.concatenate([arrays[name]["reference"] for name in RECORDING_NAMES])
        all_estimate = numpy.concatenate([arrays[name]["estimate"] for name in RECORDING_NAMES])
        seconds = sum(json.loads(own_cache_path(recording, key).read_text()).get("seconds", 0.0) for recording in RECORDING_NAMES)
        row = {"method": key, **describe_method(key, registry),
               "reliable_mae_bpm": metrics["reliable_mae_bpm"], "all_mae_bpm": metrics["all_mae_bpm"],
               "all_within_tolerance_share": metrics["all_within_tolerance_share"],
               "all_within_tolerance_count": int(round(metrics["all_within_tolerance_share"] * metrics["all_window_count"])),
               "reliable_within_tolerance_share": metrics["reliable_within_tolerance_share"],
               "all_gross_error_count": metrics["all_gross_error_count"],
               "reliable_gross_error_count": metrics["reliable_gross_error_count"],
               "all_valid_share": metrics["all_valid_share"], "all_window_count": metrics["all_window_count"],
               "reliable_window_count": metrics["reliable_window_count"], **error_types(all_reference, all_estimate),
               "simulation_seconds_all_windows": round(seconds, 2)}
        for name in RECORDING_NAMES:
            row[f"all_{name}_mae_bpm"] = metrics.get(f"all_{name}_mae_bpm")
            row[f"reliable_{name}_mae_bpm"] = metrics.get(f"reliable_{name}_mae_bpm")
            row[f"all_{name}_gross_error_count"] = metrics.get(f"all_{name}_gross_error_count")
        table_rows.append(row)
        per_window[key] = arrays
    check_baselines(table_rows)
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS_DIRECTORY / "own_recordings.csv", table_rows)
    write_per_window(RESULTS_DIRECTORY / "per_window_own_recordings.csv", per_window, main_method_keys(method_keys))
    return table_rows


def check_baselines(table_rows):
    by_key = {row["method"]: row for row in table_rows}
    problems = []
    for key, (reliable, overall, gross) in RUN_ONE_PUBLISHED.items():
        row = by_key[key]
        if round(row["reliable_mae_bpm"], 2) != reliable or round(row["all_mae_bpm"], 2) != overall \
                or row["all_gross_error_count"] != gross:
            problems.append(f"{key}: {row['reliable_mae_bpm']:.3f} / {row['all_mae_bpm']:.3f} / {row['all_gross_error_count']} "
                            f"vs published {reliable} / {overall} / {gross}")
    if problems:
        raise SystemExit("baseline does not reproduce run 1:\n" + "\n".join(problems))
    print("baselines reproduce run 1: " + ", ".join(
        f"{key} {by_key[key]['reliable_mae_bpm']:.2f}/{by_key[key]['all_mae_bpm']:.2f}/{by_key[key]['all_gross_error_count']}"
        for key in RUN_ONE_PUBLISHED))


MAIN_METHODS = ["causal_40_150", "causal_25_150", "causal_raw", "causal_40_150_twice",
                "reduced_1k_zero_phase_40_150_order2_reflect_homomorphic", "zero_phase_40_150_order2_reflect_zpenv",
                "zero_phase_40_150_order1_matched_reflect_zpenv", "zero_phase_25_400_order2_reflect_zpenv",
                "reduced_1k_zero_phase_40_150_order2_reflect_zpenv", "reduced_2k_zero_phase_40_150_order2_reflect_zpenv",
                "stored_envelope_smooth5hz_taper20", "stored_envelope_nosmooth_taper20",
                "springer_heart_rate", "springer_heart_rate_range_30_200", "springer_heart_rate_half_check",
                "springer_envelopes_combined_50hz_highest_30_120", "springer_envelopes_combined_50hz_half_check",
                "springer_envelopes_combined_100hz_half_check"]


def main_method_keys(method_keys):
    return [key for key in MAIN_METHODS if key in method_keys]


def write_csv(path, rows):
    fields = list(dict.fromkeys(name for row in rows for name in row))
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: (f"{value:.4f}" if isinstance(value, float) else value) for name, value in row.items()})


def write_per_window(path, per_window, keys):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["recording", "end_time_s", "reference_bpm", "reliable"] + [f"{key}_bpm" for key in keys])
        first = per_window[keys[0]]
        for name in RECORDING_NAMES:
            for index, end_time in enumerate(first[name]["end_time"]):
                writer.writerow([name, int(end_time), f"{first[name]['reference'][index]:.2f}", bool(first[name]["reliable"][index])]
                                + [f"{per_window[key][name]['estimate'][index]:.2f}" for key in keys])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--methods", default="", help="comma-separated method keys (default: all)")
    arguments = parser.parse_args()
    run_own(arguments)


if __name__ == "__main__":
    main()
