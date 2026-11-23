"""Improved-method study: store the per-second normalised autocorrelation of every EPHNOGRAM record so that
peak choices and validity rules can be evaluated without recomputing the capture chain.

Usage: python -I src/bpm_improved_method_compute.py [--workers 6] [--conditions rest,overload]
Writes cache/bpm-improved/<condition>/<record>/<filter>__<envelope>.npz with arrays
correlation (updates x lags, float16), end_time_seconds and clipped_per_second.
The window, mean removal and autocorrelation are those of BPMEstimator.update.
"""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpm_evaluate
import bpm_evaluate_public
import public_evaluation_common as common
from hfs import bpm_estimator, device_chain, ephnogram

CACHE_DIRECTORY = common.STUDY_DIRECTORY / "cache" / "bpm-improved"
FILTERS = ("raw", "butterworth_hp2_25_lp2_150", "butterworth_hp2_30_lp2_150", "butterworth_hp2_40_lp2_150",
           "butterworth_hp2_50_lp2_150", "butterworth_hp2_60_lp2_150", "butterworth_hp2_80_lp2_150",
           "butterworth_hp2_40_lp2_400", "butterworth_hp4_60_lp4_150")
ENVELOPES = {"two_pole_5hz": common.FINAL_METHOD, "one_pole_12hz": common.HALF_CHECK_ONLY}


def envelope_of(filtered, input_rate_hz, configuration):
    estimator = bpm_estimator.BPMEstimator(configuration, input_rate_hz)
    envelope = numpy.zeros(filtered.shape[0] // estimator.decimation_factor + 2, dtype=numpy.float32)
    bpm_estimator._envelope_block(numpy.ascontiguousarray(filtered, dtype=numpy.float32), estimator.rectification_code,
                                  estimator.lowpass_code, estimator.lowpass_coefficient, estimator.lowpass_state,
                                  estimator.counter_state, estimator.decimation_factor, estimator.boxcar_scale, envelope)
    return envelope, estimator


def correlations_of(filtered, input_rate_hz, configuration):
    """Per update (end time 1, 2, ... s): the correlation the estimator computes, NaN before the window is full."""
    envelope, estimator = envelope_of(filtered, input_rate_hz, configuration)
    samples_per_update = int(round(configuration.update_seconds * input_rate_hz))
    update_count = filtered.shape[0] // samples_per_update
    window_length = estimator.window_length
    output = numpy.full((update_count, estimator.correlation.shape[0]), numpy.nan, dtype=numpy.float32)
    window = estimator.chronological_window
    for update_index in range(update_count):
        envelope_count = (update_index + 1) * samples_per_update // estimator.decimation_factor
        if envelope_count < window_length:
            continue
        window[:] = envelope[envelope_count - window_length:envelope_count]
        window -= numpy.float32(window.mean(dtype=numpy.float32))
        bpm_estimator._normalised_autocorrelation(window, estimator.correlation_lag_count, estimator.correlation)
        output[update_index] = estimator.correlation
    end_times = numpy.arange(1, update_count + 1, dtype=numpy.float64) * configuration.update_seconds
    return output, end_times


def output_path(condition, record_name, identifier, envelope_name):
    return CACHE_DIRECTORY / condition / record_name / f"{identifier}__{envelope_name}.npz"


def compute_item(item):
    record_name, condition = item
    started = time.perf_counter()
    todo = [(identifier, envelope_name) for identifier in FILTERS for envelope_name in ENVELOPES
            if not output_path(condition, record_name, identifier, envelope_name).exists()]
    if not todo:
        return record_name, condition, 0.0
    specifications = common.candidate_specifications()
    record = ephnogram.load_record(record_name)
    samples = numpy.asarray(bpm_evaluate_public.modelled_capture(record, condition))
    del record
    clipped = common.clipped_per_second(samples)
    normalised = device_chain.normalise(samples)
    del samples
    for identifier in dict.fromkeys(identifier for identifier, _ in todo):
        candidate = bpm_evaluate.build_candidate(specifications[identifier])
        filtered = device_chain.apply_filter_to_normalised(candidate, normalised)
        for envelope_name in [name for other, name in todo if other == identifier]:
            correlation, end_times = correlations_of(filtered, candidate.output_rate_hz, ENVELOPES[envelope_name])
            path = output_path(condition, record_name, identifier, envelope_name)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.stem + ".partial.npz")
            numpy.savez(temporary, correlation=correlation.astype(numpy.float16), end_time_seconds=end_times,
                        clipped_per_second=clipped)
            temporary.replace(path)
        del filtered
    return record_name, condition, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--conditions", default="rest,overload")
    parser.add_argument("--records", default="")
    arguments = parser.parse_args()
    records = sorted(bpm_evaluate_public.usable_records(), key=lambda info: -info.duration_seconds)
    if arguments.records:
        wanted = set(arguments.records.split(","))
        records = [info for info in records if info.record_name in wanted]
    items = [(info.record_name, condition) for condition in arguments.conditions.split(",") for info in records]
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=min(6, arguments.workers)) as executor:
        futures = [executor.submit(compute_item, item) for item in items]
        for done, future in enumerate(as_completed(futures), 1):
            record_name, condition, elapsed = future.result()
            print(f"[{done}/{len(items)}] {record_name} {condition} {elapsed:.0f} s (total {time.perf_counter() - started:.0f} s)",
                  flush=True)


if __name__ == "__main__":
    main()
