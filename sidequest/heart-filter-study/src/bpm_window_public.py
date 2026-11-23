"""Whole-window BPM methods on EPHNOGRAM sound through the modelled capture chain, against the ECG reference.

Usage:
  python -I src/bpm_window_public.py compute [--conditions rest,overload] [--workers 4] [--diagnostic]
  python -I src/bpm_window_public.py report
Subset: every available record (as src/bpm_evaluate_public.py selects them), windows ending every 4th second from
12 s on (12, 16, 20, ... s after the record start; time zero is the record start as in reference-public/).
The capture chain and its seed are those of src/bpm_evaluate_public.py, so the samples equal that evaluation's.
Cache: cache/window/public/<condition>/<record>/<method>.json, so reruns only add.
"""
import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy

import bpm_evaluate_public
import bpm_window_methods as own
import public_evaluation_common as common
from hfs import device_chain, ephnogram
from hfs.recordings import SAMPLE_MAXIMUM, SAMPLE_MINIMUM, STUDY_DIRECTORY

CACHE_DIRECTORY = STUDY_DIRECTORY / "cache" / "window" / "public"
FIRST_END_TIME_SECONDS = 12
END_TIME_STEP_SECONDS = 4
# Sample-identical copies of ECGPCG0031 and ECGPCG0069 under other subject labels (ephnogram.duplicate_signal_groups()).
EXCLUDED_DUPLICATES = ("ECGPCG0001", "ECGPCG0002")
PUBLIC_METHODS = [
    "causal_40_150", "causal_25_150", "causal_raw", "causal_40_150_twice",
    "zero_phase_40_150_order2_reflect_zpenv", "zero_phase_40_150_order2_none_zpenv",
    "zero_phase_40_150_order2_discard025_zpenv", "zero_phase_40_150_order2_discard050_zpenv",
    "zero_phase_25_150_order2_none_zpenv", "zero_phase_25_150_order2_reflect_zpenv",
    "zero_phase_25_400_order2_reflect_zpenv", "zero_phase_40_150_order1_matched_reflect_zpenv",
    "streamed_forward_backward_window_40_150_order2_reflect_zpenv",
    "forward_once_40_150_order2_reflect_causalenv", "forward_twice_40_150_order1_matched_reflect_causalenv",
    "forward_twice_40_150_order2_reflect_causalenv", "zero_phase_40_150_order2_reflect_causalenv",
    "reduced_1k_zero_phase_40_150_order2_reflect_zpenv", "reduced_2k_zero_phase_40_150_order2_reflect_zpenv",
    "stored_envelope_smooth5hz_taper0", "stored_envelope_nosmooth_taper20",
    "springer_heart_rate", "springer_heart_rate_range_30_200", "springer_heart_rate_half_check",
    "springer_envelopes_combined_50hz_highest_30_200", "springer_envelopes_combined_50hz_half_check",
]

# Added after the first rest results, to find which ingredient of the Springer pre-processing helps; rest condition only.
DIAGNOSTIC_METHODS = [
    "reduced_1k_zero_phase_40_150_order2_reflect_spikes_removed_zpenv",
    "reduced_1k_zero_phase_40_150_order2_reflect_homomorphic",
    "reduced_1k_zero_phase_40_150_order2_reflect_spikes_removed_homomorphic",
]


def cache_path(condition, record_name, method_key):
    return CACHE_DIRECTORY / condition / record_name / f"{method_key}__v{own.CACHE_VERSION}.json"


def end_samples(sample_count):
    last_end = sample_count // own.SAMPLE_RATE_HZ
    return {end_time: end_time * own.SAMPLE_RATE_HZ
            for end_time in range(FIRST_END_TIME_SECONDS, last_end + 1, END_TIME_STEP_SECONDS)}


def compute_item(item):
    record_name, condition, method_keys = item
    missing = [key for key in method_keys if not cache_path(condition, record_name, key).exists()]
    if not missing:
        return record_name, condition, 0, 0.0
    started = time.perf_counter()
    record = ephnogram.load_record(record_name)
    samples = numpy.asarray(bpm_evaluate_public.modelled_capture(record, condition))
    del record
    clipped_flags = ((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM)).astype(numpy.int8)
    normalised = device_chain.normalise(samples)
    del samples
    ends = end_samples(normalised.shape[0])
    registry = own.method_registry()
    source = own.WindowSource(normalised, clipped_flags)
    for key in missing:
        method_started = time.perf_counter()
        if key in own.CAUSAL_BASELINES:
            all_rows = own.causal_rows(normalised, clipped_flags, key, 0.0, FIRST_END_TIME_SECONDS, max(ends))
            rows = [row for row in all_rows if row[0] in ends]
        else:
            kind, method = registry[key]
            rows = own.estimate_windows(source, kind, method, ends)
        path = cache_path(condition, record_name, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"record": record_name, "condition": condition, "method": key, "rows": rows,
                                    "seconds": time.perf_counter() - method_started}))
    return record_name, condition, len(missing), time.perf_counter() - started


def evaluated_records():
    return [info for info in bpm_evaluate_public.usable_records() if info.record_name not in EXCLUDED_DUPLICATES]


def compute(arguments):
    records = sorted(evaluated_records(), key=lambda info: -info.duration_seconds)
    methods = PUBLIC_METHODS + (DIAGNOSTIC_METHODS if arguments.diagnostic else [])
    items = [(info.record_name, condition, methods) for condition in arguments.conditions.split(",") for info in records]
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=arguments.workers) as executor:
        futures = [executor.submit(compute_item, item) for item in items]
        for future in as_completed(futures):
            record_name, condition, count, seconds = future.result()
            print(f"{time.strftime('%H:%M:%S')} {condition} {record_name}: {count} methods in {seconds:.0f} s "
                  f"(total {time.perf_counter() - started:.0f} s)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("compute", "report"))
    parser.add_argument("--conditions", default="rest")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--diagnostic", action="store_true", help="also compute DIAGNOSTIC_METHODS")
    arguments = parser.parse_args()
    if arguments.action == "compute":
        compute(arguments)
    else:
        import bpm_window_public_report
        bpm_window_public_report.report(arguments)


if __name__ == "__main__":
    main()
