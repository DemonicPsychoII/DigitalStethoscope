"""Run 2: BPM filter x counting method on EPHNOGRAM sound through the modelled capture chain, against ECG.

Usage:
  python -I src/bpm_evaluate_public.py compute [--set main|all|matched] [--conditions rest,overload] [--workers 8]
  python -I src/bpm_evaluate_public.py report
Estimates are cached per (condition, record, candidate) with one array per estimator variant in
cache/bpm-public/; reruns only add what is missing. The report reads whatever is cached.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import public_evaluation_common as common
import bpm_evaluate
from hfs import device_chain, ephnogram

STUDY_DIRECTORY = common.STUDY_DIRECTORY
CHAIN_MODEL_MARKER = STUDY_DIRECTORY / "src" / "hfs" / "CHAIN_MODEL_READY"
UNUSABLE_SOUND_NOTES = ("disconnected",)
MATCHED_CANDIDATES = ("raw", "butterworth_hp2_25_lp2_150", "butterworth_hp2_40_lp2_150", "butterworth_hp2_40_lp2_800",
                      "butterworth_hp2_100_lp2_800")
STAND_IN_CONDITION = "stand_in_resample"


def usable_records():
    records = []
    excluded = common.duplicate_records_excluded()
    for info in ephnogram.list_records():
        if not info.available or info.record_name in excluded:
            continue
        if any(note in info.pcg_quality.lower() for note in UNUSABLE_SOUND_NOTES):
            continue
        records.append(info)
    return records


def record_seed(record_name):
    return int("".join(character for character in record_name if character.isdigit()) or 0)


def modelled_capture(record, condition):
    if condition == STAND_IN_CONDITION:
        from scipy import signal
        sound = record.pcg - numpy.mean(record.pcg)
        resampled = signal.resample_poly(sound, 16000, int(record.sample_rate_hz))
        scale = 0.05 / max(numpy.percentile(numpy.abs(resampled), 99.9), 1e-12)
        return numpy.clip(numpy.rint(resampled * scale * 8388608.0), -8388608, 8388607).astype(numpy.int32)
    from hfs import chain_model
    level_condition, spectrum_variant = common.CONDITIONS[condition]
    calibration = chain_model.load_calibration("ephnogram")
    return chain_model.model_through_capture_chain(record.pcg, record.sample_rate_hz, level_condition=level_condition,
                                                   spectrum_variant=spectrum_variant, calibration=calibration,
                                                   seed=record_seed(record.info.record_name))


def missing_keys(record_name, condition, identifier):
    cached = common.cached_estimates(record_name, condition, identifier)
    return [key for key, configuration in common.ESTIMATOR_VARIANTS.items()
            if common.configuration_key(configuration) not in cached]


def compute_item(item):
    record_name, condition, identifiers = item
    started = time.perf_counter()
    todo = [(identifier, missing_keys(record_name, condition, identifier)) for identifier in identifiers]
    todo = [(identifier, keys) for identifier, keys in todo if keys]
    if not todo:
        return record_name, condition, 0, 0.0
    specifications = common.candidate_specifications()
    record = ephnogram.load_record(record_name)
    samples = numpy.asarray(modelled_capture(record, condition))
    del record
    per_second = common.clipped_per_second(samples)
    normalised = device_chain.normalise(samples)
    del samples
    for identifier, keys in todo:
        candidate = bpm_evaluate.build_candidate(specifications[identifier])
        filtered = device_chain.apply_filter_to_normalised(candidate, normalised)
        configurations = [common.ESTIMATOR_VARIANTS[key] for key in keys]
        estimates = common.estimate_record(filtered, candidate.output_rate_hz, configurations, per_second)
        del filtered
        common.store_estimates(record_name, condition, identifier,
                               {common.configuration_key(configuration): rows.astype(numpy.float32)
                                for configuration, rows in estimates.items()})
    return record_name, condition, len(todo), time.perf_counter() - started


def candidate_set(name):
    specifications = common.candidate_specifications()
    if name == "main":
        return list(dict.fromkeys(list(common.MAIN_CANDIDATES) + list(common.LOWER_EDGE_SWEEP.values())))
    if name == "matched":
        return list(MATCHED_CANDIDATES)
    return list(specifications)


def compute(arguments):
    conditions = arguments.conditions.split(",")
    if any(condition != STAND_IN_CONDITION for condition in conditions) and not CHAIN_MODEL_MARKER.exists():
        raise SystemExit("chain model not ready (src/hfs/CHAIN_MODEL_READY missing); use --conditions stand_in_resample to develop")
    identifiers = candidate_set(arguments.set)
    records = sorted(usable_records(), key=lambda info: -info.duration_seconds)
    items = [(info.record_name, condition, identifiers) for condition in conditions for info in records]
    items = [item for item in items if any(missing_keys(item[0], item[1], identifier) for identifier in item[2])]
    print(f"{len(records)} usable records, {len(items)} work items, {len(identifiers)} candidates, conditions {conditions}", flush=True)
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=arguments.workers) as executor:
        futures = [executor.submit(compute_item, item) for item in items]
        for done, future in enumerate(as_completed(futures), 1):
            record_name, condition, count, elapsed = future.result()
            print(f"[{done}/{len(items)}] {record_name} {condition}: {count} candidates in {elapsed:.0f} s "
                  f"(total {time.perf_counter() - started:.0f} s)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)
    compute_parser = subparsers.add_parser("compute")
    compute_parser.add_argument("--set", choices=("main", "all", "matched"), default="main")
    compute_parser.add_argument("--conditions", default="rest,overload")
    compute_parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 2))
    subparsers.add_parser("report")
    arguments = parser.parse_args()
    if arguments.command == "compute":
        compute(arguments)
    else:
        import bpm_public_report
        bpm_public_report.write_report()


if __name__ == "__main__":
    main()
