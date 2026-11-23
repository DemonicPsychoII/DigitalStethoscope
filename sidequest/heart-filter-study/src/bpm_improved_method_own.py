"""Own recordings (run 1) with the improved method, and proof that the existing estimator options are unchanged.

Usage: python -I src/bpm_improved_method_own.py
1. Re-runs the cached run-1 comparison on recording rest-1, Butterworth 2+2 40-150 Hz, for every cached existing
   configuration and compares estimate, valid flag, quality, margin and reason with the run-1 cache, bit for bit.
2. Scores the run-1 final method and the improved methods on all five recordings and the study filters.
Writes results-public/improved_method_own_recordings.csv and improved_method_identity_check.json.
"""
import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy

import bpm_evaluate
import bpm_improved_method_common as improved
import public_evaluation_common as common
from hfs import bpm_estimator, device_chain
from hfs.bpm_estimator import EstimatorConfiguration
from hfs.recordings import RECORDING_NAMES, SAMPLE_MAXIMUM, SAMPLE_MINIMUM, load_recording

IDENTITY_RECORDING = "rest-1"
IDENTITY_FILTER = "butterworth_hp2_40_lp2_150"


def chosen_configurations():
    choice = json.loads((common.RESULTS_DIRECTORY / "improved_method_choice.json").read_text(encoding="utf-8"))
    chosen = EstimatorConfiguration(**choice["chosen_configuration"])
    peak_only = EstimatorConfiguration(**choice["peak_choice_configuration"])
    return {"final": common.FINAL_METHOD, "half_check_only": common.HALF_CHECK_ONLY,
            "improved_peak_choice": peak_only, "improved": chosen}


def identity_check():
    """Every distinct cached run-1 configuration, on 40-150 Hz where cached, else 25-150 Hz, else its first filter."""
    specifications = bpm_evaluate.filter_grid()
    filters_by_digest = {}
    for path in sorted(bpm_evaluate.CACHE_DIRECTORY.glob("*.json")):
        identifier, digest = path.stem.rsplit("__", 1)
        filters_by_digest.setdefault(digest, []).append(identifier)
    work = {}
    for digest, identifiers in filters_by_digest.items():
        preferred = [name for name in (IDENTITY_FILTER, "butterworth_hp2_25_lp2_150") if name in identifiers]
        identifier = (preferred or identifiers)[0]
        work.setdefault(identifier, []).append(bpm_evaluate.CACHE_DIRECTORY / f"{identifier}__{digest}.json")
    samples = load_recording(IDENTITY_RECORDING)
    clipped_flags = ((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM)).astype(numpy.int8)
    normalised = device_chain.normalise(samples)
    checked = []
    for identifier, paths in work.items():
        candidate = bpm_evaluate.build_candidate(specifications[identifier])
        filtered = device_chain.apply_filter_to_normalised(candidate, normalised)
        for path in paths:
            document = json.loads(path.read_text())
            configuration = EstimatorConfiguration(**document["estimator"])
            results, _ = bpm_estimator.run_estimator(filtered, candidate.output_rate_hz, configuration, clipped_flags)
            fresh = [[end_time, result.bpm, result.valid, result.quality, result.margin, result.reason]
                     for end_time, result in results.items()]
            cached = document["recordings"][IDENTITY_RECORDING]
            identical = json.loads(json.dumps(fresh)) == cached
            checked.append({"filter": identifier, "configuration": configuration.key(), "windows": len(cached),
                            "bit_identical": identical})
            print(f"{'identical' if identical else 'DIFFERENT'}: {identifier} {configuration.key()} ({len(cached)} windows)",
                  flush=True)
    return checked


def score_item(item):
    identifier, method_name, configuration = item
    candidate = bpm_evaluate.build_candidate(bpm_evaluate.filter_grid()[identifier] if identifier in bpm_evaluate.filter_grid()
                                             else common.candidate_specifications()[identifier])
    reference = bpm_evaluate.load_reference(common.STUDY_DIRECTORY / "reference")
    rows = []
    for name in RECORDING_NAMES:
        samples = load_recording(name)
        clipped_flags = ((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM)).astype(numpy.int8)
        filtered = device_chain.apply_filter_to_normalised(candidate, device_chain.normalise(samples))
        results, _ = bpm_estimator.run_estimator(filtered, candidate.output_rate_hz, configuration, clipped_flags)
        for end_time, result in results.items():
            window = reference[name].get(end_time)
            if window is None or window.get("reference_bpm") is None or not numpy.isfinite(window["reference_bpm"]):
                continue
            rows.append((name, end_time, window["reference_bpm"], result.bpm, result.valid, bool(window.get("reliable", True))))
    return identifier, method_name, rows


def main():
    checked = identity_check()
    (common.RESULTS_DIRECTORY / "improved_method_identity_check.json").write_text(json.dumps(
        {"recording": IDENTITY_RECORDING, "configurations": checked}, indent=1), encoding="utf-8")
    methods = chosen_configurations()
    items = [(identifier, method_name, configuration) for identifier in improved.FILTER_LABELS
             for method_name, configuration in methods.items()]
    output = []
    with ProcessPoolExecutor(max_workers=6) as executor:
        for identifier, method_name, rows in executor.map(score_item, items):
            reference = numpy.array([row[2] for row in rows])
            estimate = numpy.array([row[3] for row in rows])
            valid = numpy.array([row[4] for row in rows])
            reliable = numpy.array([row[5] for row in rows])
            measures = improved.window_measures(reference, estimate, valid)
            for subset, mask in (("all", numpy.ones_like(reliable)), ("reliable", reliable)):
                result = improved.pooled(measures, mask.astype(bool))
                output.append({"filter": improved.FILTER_LABELS[identifier], "method": method_name, "windows": subset,
                               **result})
                print(f"{improved.FILTER_LABELS[identifier]:14s} {method_name:22s} {subset:8s} MAE {result['mae_bpm']:.3f} "
                      f"within {result['within_tolerance_share']:.3f} gross {result['gross_count']} valid {result['valid_share']:.3f} "
                      f"windows {result['window_count']}", flush=True)
    fields = list(dict.fromkeys(name for row in output for name in row))
    with (common.RESULTS_DIRECTORY / "improved_method_own_recordings.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)


if __name__ == "__main__":
    main()
