"""BPM filter evaluation: filter grid x estimator variants on the five recordings against a reference.

Usage: python src/bpm_evaluate.py --reference reference [--workers 14]
Staging: (1) all filters with the default estimator, (2) estimator and input-limiter variants on the top
filters, (3) the best variants combined on the top filters. Results are cached per (candidate, variant).
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hfs import bpm_estimator, device_chain, filters
from hfs.bpm_estimator import EstimatorConfiguration
from hfs.recordings import RECORDING_NAMES, SAMPLE_MAXIMUM, SAMPLE_MINIMUM, STUDY_DIRECTORY, load_recording

CACHE_DIRECTORY = STUDY_DIRECTORY / "cache" / "bpm"
RESULTS_DIRECTORY = STUDY_DIRECTORY / "results"
FIGURES_DIRECTORY = RESULTS_DIRECTORY / "figures"
EVALUATION_VERSION = "4"
DEFAULT_ESTIMATOR = EstimatorConfiguration()
BASELINE_IDENTIFIERS = ("raw", "butterworth_hp2_25_lp2_150", "butterworth_hp2_40_lp2_800")
HIGHPASS_EDGES = [None, 10, 15, 20, 25, 30, 40, 50, 60, 80]
LOWPASS_EDGES = [60, 80, 100, 120, 150, 200, 250, 300, 400, 600, 800, None]
ORDER_PAIRS_OTHER_FAMILIES = [(1, 1), (2, 2), (4, 4), (2, 4), (4, 2)]
STAGE_TOP_COUNT = 10
ESP32_CLOCK_HZ = 240e6
CYCLES_PER_FILTER_MULTIPLY = 4.0
CYCLES_PER_CORRELATION_MULTIPLY = 2.0
CYCLES_PER_LOGARITHM = 60.0


def specification(family, highpass_hz, lowpass_hz, highpass_order=2, lowpass_order=2, fir_tap_count=None, input_limit=None):
    return {"family": family, "highpass_hz": highpass_hz, "lowpass_hz": lowpass_hz, "highpass_order": highpass_order,
            "lowpass_order": lowpass_order, "fir_tap_count": fir_tap_count, "input_limit": input_limit}


_CANDIDATE_MEMORY = {}


def build_candidate(spec):
    memory_key = tuple(sorted((name, repr(value)) for name, value in spec.items()))
    if memory_key not in _CANDIDATE_MEMORY:
        _CANDIDATE_MEMORY[memory_key] = _design_candidate(spec)
    return _CANDIDATE_MEMORY[memory_key]


def _design_candidate(spec):
    candidate = filters.design_filter(spec["family"], spec["highpass_hz"], spec["lowpass_hz"], spec["highpass_order"],
                                      spec["lowpass_order"], fir_tap_count=spec["fir_tap_count"])
    return candidate


def candidate_identifier(spec):
    identifier = build_candidate(spec).identifier
    if spec["input_limit"]:
        mode, level = spec["input_limit"]
        identifier += f"__{mode}limit{level:g}".replace(".", "p")
    return identifier


def filter_grid():
    specs = [specification("raw", None, None)]
    for highpass in HIGHPASS_EDGES:
        for lowpass in LOWPASS_EDGES:
            if highpass is None and lowpass is None:
                continue
            if highpass is not None and lowpass is not None and lowpass < 1.5 * highpass:
                continue
            specs.append(specification("butterworth", highpass, lowpass))
    order_highpass = [15, 20, 25, 30, 40, 60]
    order_lowpass = [80, 100, 150, 200, 300, 600]
    for highpass in order_highpass:
        for lowpass in order_lowpass:
            if lowpass < 1.5 * highpass:
                continue
            for highpass_order in (1, 2, 3, 4):
                for lowpass_order in (1, 2, 3, 4):
                    specs.append(specification("butterworth", highpass, lowpass, highpass_order, lowpass_order))
    for family in ("bessel", "chebyshev1", "chebyshev2", "elliptic"):
        for highpass in order_highpass:
            for lowpass in (100, 150, 200, 300):
                if lowpass < 1.5 * highpass:
                    continue
                for highpass_order, lowpass_order in ORDER_PAIRS_OTHER_FAMILIES:
                    specs.append(specification(family, highpass, lowpass, highpass_order, lowpass_order))
    for tap_count in (65, 129, 257):
        for highpass in (None, 25, 40, 60, 100):
            for lowpass in (150, 300, 800):
                specs.append(specification("fir", highpass, lowpass, fir_tap_count=tap_count))
    for highpass in (None, 10, 15, 20, 25, 30, 40, 60):
        for lowpass in (80, 100, 150, 200, 300):
            if highpass is not None and lowpass < 1.5 * highpass:
                continue
            for highpass_order, lowpass_order in ((2, 2), (4, 4), (2, 4), (4, 2)):
                specs.append(specification("decimated", highpass, lowpass, highpass_order, lowpass_order))
    unique = {}
    for spec in specs:
        unique.setdefault(candidate_identifier(spec), spec)
    return unique


def listening_filter_specs():
    specs = [specification("raw", None, None)]
    for highpass, lowpass in ((40, 800), (20, 800), (60, 800), (100, 800), (40, 400), (40, 1500)):
        specs.append(specification("butterworth", highpass, lowpass))
    return {candidate_identifier(spec): spec for spec in specs}


def cache_path(identifier, configuration):
    digest = hashlib.sha1((EVALUATION_VERSION + configuration.key()).encode()).hexdigest()[:12]
    return CACHE_DIRECTORY / f"{identifier}__{digest}.json"


def apply_input_limit(normalised, input_limit):
    if not input_limit:
        return normalised
    mode, level = input_limit
    level = numpy.float32(level)
    if mode == "hard":
        return numpy.clip(normalised, -level, level)
    return (level * numpy.tanh(normalised / level)).astype(numpy.float32)


def evaluate_work_item(item):
    identifier, spec, configurations = item
    missing = [configuration for configuration in configurations if not cache_path(identifier, configuration).exists()]
    if not missing:
        return identifier
    candidate = build_candidate(spec)
    per_configuration = {configuration: {} for configuration in missing}
    for name in RECORDING_NAMES:
        samples = load_recording(name)
        clipped_flags = ((samples >= SAMPLE_MAXIMUM) | (samples <= SAMPLE_MINIMUM)).astype(numpy.int8)
        normalised = apply_input_limit(device_chain.normalise(samples), spec["input_limit"])
        filtered = device_chain.apply_filter_to_normalised(candidate, normalised)
        for configuration in missing:
            results, _ = bpm_estimator.run_estimator(filtered, candidate.output_rate_hz, configuration, clipped_flags)
            per_configuration[configuration][name] = [
                [end_time, result.bpm, result.valid, result.quality, result.margin, result.reason]
                for end_time, result in results.items()]
    for configuration, document in per_configuration.items():
        cache_path(identifier, configuration).write_text(json.dumps({"identifier": identifier, "estimator": asdict(configuration),
                                                                      "recordings": document}))
    return identifier


def run_items(items, workers):
    CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    todo = [item for item in items if not all(cache_path(item[0], configuration).exists() for configuration in item[2])]
    if todo:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for _ in executor.map(evaluate_work_item, todo, chunksize=4):
                pass
    loaded = {}
    for identifier, _, configurations in items:
        for configuration in configurations:
            loaded[(identifier, configuration)] = json.loads(cache_path(identifier, configuration).read_text())["recordings"]
    return loaded, len(todo)


def load_reference(directory):
    reference = {}
    for name in RECORDING_NAMES:
        path = Path(directory) / f"{name}.json"
        if not path.exists():
            raise SystemExit(f"reference file missing: {path}")
        document = json.loads(path.read_text())
        reference[name] = {int(round(window["end_time_s"])): window for window in document["windows"]}
    return reference


def aligned_arrays(estimates, reference):
    """Per recording: arrays of reference, estimate, valid, quality, reliable over the common end times."""
    arrays = {}
    for name in RECORDING_NAMES:
        rows = [row for row in estimates[name] if row[0] in reference[name]
                and reference[name][row[0]].get("reference_bpm") is not None
                and numpy.isfinite(reference[name][row[0]]["reference_bpm"])]
        arrays[name] = {
            "end_time": numpy.array([row[0] for row in rows]),
            "reference": numpy.array([reference[name][row[0]]["reference_bpm"] for row in rows], dtype=float),
            "estimate": numpy.array([row[1] for row in rows], dtype=float),
            "valid": numpy.array([bool(row[2]) for row in rows]),
            "quality": numpy.array([row[3] for row in rows], dtype=float),
            "reliable": numpy.array([bool(reference[name][row[0]].get("reliable", True)) for row in rows]),
        }
    return arrays


def metric_block(reference, estimate, valid, prefix):
    if reference.size == 0:
        return {}
    error = estimate - reference
    absolute = numpy.abs(error)
    tolerance = numpy.maximum(5.0, 0.1 * reference)
    within = absolute <= tolerance
    metrics = {f"{prefix}mae_bpm": absolute.mean(), f"{prefix}median_absolute_error_bpm": numpy.median(absolute),
               f"{prefix}bias_bpm": error.mean(), f"{prefix}rmse_bpm": numpy.sqrt(numpy.mean(error ** 2)),
               f"{prefix}within_tolerance_share": within.mean(), f"{prefix}valid_share": valid.mean(),
               f"{prefix}gross_error_count": int(numpy.count_nonzero(absolute > 0.2 * reference)),
               f"{prefix}window_count": int(reference.size)}
    if valid.any():
        metrics[f"{prefix}valid_mae_bpm"] = absolute[valid].mean()
        metrics[f"{prefix}valid_within_tolerance_share"] = within[valid].mean()
    else:
        metrics[f"{prefix}valid_mae_bpm"] = float("nan")
        metrics[f"{prefix}valid_within_tolerance_share"] = float("nan")
    return metrics


def compute_metrics(arrays, recordings=RECORDING_NAMES):
    metrics = {}
    for subset, prefix in (("all", "all_"), ("reliable", "reliable_")):
        pooled = {key: [] for key in ("reference", "estimate", "valid")}
        for name in recordings:
            mask = numpy.ones(arrays[name]["reference"].shape, bool) if subset == "all" else arrays[name]["reliable"]
            for key in pooled:
                pooled[key].append(arrays[name][key][mask])
            per_recording = metric_block(arrays[name]["reference"][mask], arrays[name]["estimate"][mask],
                                         arrays[name]["valid"][mask], f"{prefix}{name}_")
            for key in ("mae_bpm", "within_tolerance_share", "valid_share", "gross_error_count"):
                if f"{prefix}{name}_{key}" in per_recording:
                    metrics[f"{prefix}{name}_{key}"] = per_recording[f"{prefix}{name}_{key}"]
        metrics.update(metric_block(*(numpy.concatenate(pooled[key]) for key in ("reference", "estimate", "valid")), prefix))
    return metrics


def estimator_cost(configuration, input_rate_hz, filter_cost):
    estimator = bpm_estimator.BPMEstimator(configuration, input_rate_hz)
    operations = estimator.operations_per_second()
    memory = estimator.memory_bytes()
    filter_cycles = filter_cost["multiplies_per_sample"] * 16000 * CYCLES_PER_FILTER_MULTIPLY
    envelope_cycles = operations["envelope_multiplies_per_second"] * CYCLES_PER_FILTER_MULTIPLY + \
        operations["logarithms_per_second"] * CYCLES_PER_LOGARITHM
    correlation_cycles = operations["autocorrelation_multiplies_per_second"] * CYCLES_PER_CORRELATION_MULTIPLY
    total = filter_cycles + envelope_cycles + correlation_cycles
    return {"filter_multiplies_per_second": filter_cost["multiplies_per_sample"] * 16000,
            "envelope_multiplies_per_second": operations["envelope_multiplies_per_second"],
            "autocorrelation_multiplies_per_update": operations["autocorrelation_multiplies_per_update"],
            "estimator_ram_bytes": sum(memory.values()), "window_bytes": memory["window_bytes"],
            "estimated_cpu_share_percent": 100.0 * total / ESP32_CLOCK_HZ,
            "estimated_autocorrelation_milliseconds_per_update": 1000.0 * operations["autocorrelation_multiplies_per_update"]
            * CYCLES_PER_CORRELATION_MULTIPLY / ESP32_CLOCK_HZ}


def describe_row(identifier, spec, configuration, stage, arrays):
    candidate = build_candidate(spec)
    filter_cost = filters.cost(candidate)
    row = {"stage": stage, "identifier": identifier, "estimator": configuration.key(), "family": candidate.family,
           "highpass_hz": candidate.highpass_hz if candidate.highpass_hz is not None else "",
           "lowpass_hz": candidate.lowpass_hz if candidate.lowpass_hz is not None else "",
           "highpass_order": candidate.highpass_order, "lowpass_order": candidate.lowpass_order,
           "fir_tap_count": len(candidate.fir_coefficients) if candidate.fir_coefficients is not None else "",
           "input_limit": "" if not spec["input_limit"] else f"{spec['input_limit'][0]} {spec['input_limit'][1]:g}",
           "multiplies_per_sample": filter_cost["multiplies_per_sample"], "state_bytes": filter_cost["state_bytes"],
           "coefficient_bytes": filter_cost["coefficient_bytes"]}
    row.update(estimator_cost(configuration, candidate.output_rate_hz, filter_cost))
    row.update(compute_metrics(arrays))
    return row


def estimator_variants():
    base = DEFAULT_ESTIMATOR
    variants = [base]
    variants += [replace(base, rectification=value) for value in ("square", "shannon")]
    variants += [replace(base, envelope_lowpass_hz=value) for value in (5.0, 8.0, 20.0)]
    variants += [replace(base, envelope_lowpass="two_pole"), replace(base, envelope_lowpass="boxcar")]
    variants += [replace(base, envelope_rate_hz=value) for value in (50, 200)]
    variants += [replace(base, compression=value) for value in ("log", "clip_mean3")]
    variants += [replace(base, peak_choice=value) for value in ("half_check", "first_above", "comb")]
    return variants


INPUT_LIMITS = [("hard", 0.5), ("hard", 0.25), ("soft", 0.25)]


def bootstrap_indistinguishable(arrays_by_key, best_key, keys, resample_count=1000, block_length=8, seed=7):
    """Moving-block bootstrap over windows within each recording of the MAE difference to the best,
    on the windows the reference marks reliable (the ranking metric)."""
    generator = numpy.random.default_rng(seed)

    def masked_errors(key):
        return {name: numpy.where(arrays_by_key[key][name]["reliable"],
                                  numpy.abs(arrays_by_key[key][name]["estimate"] - arrays_by_key[key][name]["reference"]), 0.0)
                for name in RECORDING_NAMES}

    reliable = {name: arrays_by_key[best_key][name]["reliable"].astype(float) for name in RECORDING_NAMES}
    best_errors = masked_errors(best_key)
    index_sets = []
    for _ in range(resample_count):
        chosen = {}
        for name in RECORDING_NAMES:
            count = best_errors[name].size
            starts = generator.integers(0, max(1, count - block_length + 1), int(numpy.ceil(count / block_length)))
            chosen[name] = (starts[:, None] + numpy.arange(block_length)[None, :]).ravel()[:count]
        index_sets.append(chosen)
    outcome = {}
    for key in keys:
        errors = masked_errors(key)
        differences = []
        for chosen in index_sets:
            candidate_total = sum(errors[name][chosen[name]].sum() for name in RECORDING_NAMES)
            best_total = sum(best_errors[name][chosen[name]].sum() for name in RECORDING_NAMES)
            window_total = sum(reliable[name][chosen[name]].sum() for name in RECORDING_NAMES)
            differences.append((candidate_total - best_total) / max(window_total, 1.0))
        low, high = numpy.percentile(differences, [2.5, 97.5])
        outcome[key] = (float(low), float(high))
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", default="reference", help="directory with <recording>.json reference files")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    arguments = parser.parse_args()
    started = time.perf_counter()
    reference_directory = Path(arguments.reference)
    if not reference_directory.is_absolute():
        reference_directory = (Path.cwd() / reference_directory) if (Path.cwd() / reference_directory).exists() else STUDY_DIRECTORY / reference_directory
    reference = load_reference(reference_directory)
    provisional = any(json.loads((reference_directory / f"{name}.json").read_text()).get("provisional") for name in RECORDING_NAMES)

    import bpm_report
    grid = filter_grid()
    listening = listening_filter_specs()
    all_specs = {**grid, **listening}

    stage_one_items = [(identifier, spec, [DEFAULT_ESTIMATOR]) for identifier, spec in all_specs.items()]
    loaded, computed = run_items(stage_one_items, arguments.workers)
    arrays_by_key = {key: aligned_arrays(value, reference) for key, value in loaded.items()}
    rows = {}
    for identifier, spec in grid.items():
        rows[(identifier, DEFAULT_ESTIMATOR)] = describe_row(identifier, spec, DEFAULT_ESTIMATOR, "1 filter sweep", arrays_by_key[(identifier, DEFAULT_ESTIMATOR)])
    print(f"stage 1: {len(grid)} filters, {computed} computed, {time.perf_counter() - started:.0f} s")

    def ranking_key(row):
        return (row["reliable_mae_bpm"], -row["reliable_within_tolerance_share"])

    stage_one_ranked = sorted(rows.values(), key=ranking_key)
    top_filters = [row["identifier"] for row in stage_one_ranked[:STAGE_TOP_COUNT]]
    stage_two_identifiers = list(dict.fromkeys(top_filters + list(BASELINE_IDENTIFIERS)))
    variants = estimator_variants()
    stage_two_items = [(identifier, grid[identifier], variants) for identifier in stage_two_identifiers]
    limited_specs = {}
    for identifier in stage_two_identifiers:
        for input_limit in INPUT_LIMITS:
            spec = dict(grid[identifier], input_limit=input_limit)
            limited_specs[candidate_identifier(spec)] = spec
    stage_two_items += [(identifier, spec, [DEFAULT_ESTIMATOR]) for identifier, spec in limited_specs.items()]
    loaded, computed = run_items(stage_two_items, arguments.workers)
    for (identifier, configuration), value in loaded.items():
        arrays_by_key[(identifier, configuration)] = aligned_arrays(value, reference)
        spec = grid.get(identifier) or limited_specs[identifier]
        if (identifier, configuration) not in rows:
            rows[(identifier, configuration)] = describe_row(identifier, spec, configuration, "2 estimator and limiter variants",
                                                             arrays_by_key[(identifier, configuration)])
    all_specs.update(limited_specs)
    print(f"stage 2: {len(stage_two_items)} items, {computed} computed, {time.perf_counter() - started:.0f} s")

    # Judged over the top filters and the baselines, by mean change, so that a variant that adds
    # half-rate errors on some filters is not hidden by a median over near-identical top filters.
    variant_gain = {}
    for configuration in variants[1:]:
        differences = [rows[(identifier, configuration)]["reliable_mae_bpm"] - rows[(identifier, DEFAULT_ESTIMATOR)]["reliable_mae_bpm"]
                       for identifier in stage_two_identifiers]
        gross = sum(rows[(identifier, configuration)]["reliable_gross_error_count"] for identifier in stage_two_identifiers)
        variant_gain[configuration] = {"median": float(numpy.median(differences)), "mean": float(numpy.mean(differences)),
                                       "gross_errors": int(gross)}
    default_gross = sum(rows[(identifier, DEFAULT_ESTIMATOR)]["reliable_gross_error_count"] for identifier in stage_two_identifiers)
    variant_gain[DEFAULT_ESTIMATOR] = {"median": 0.0, "mean": 0.0, "gross_errors": int(default_gross)}
    improving = sorted([configuration for configuration, gain in variant_gain.items()
                        if configuration != DEFAULT_ESTIMATOR and (gain["mean"] < 0 or gain["median"] < 0)],
                       key=lambda configuration: variant_gain[configuration]["mean"])[:4]

    def merge(*configurations):
        merged = asdict(DEFAULT_ESTIMATOR)
        for configuration in configurations:
            for name, value in asdict(configuration).items():
                if value != getattr(DEFAULT_ESTIMATOR, name):
                    merged[name] = value
        return EstimatorConfiguration(**merged)

    half_check = replace(DEFAULT_ESTIMATOR, peak_choice="half_check")
    combined = []
    for first_index in range(len(improving)):
        for second_index in range(first_index + 1, len(improving)):
            combined.append(merge(improving[first_index], improving[second_index]))
    combined += [merge(configuration, half_check) for configuration in improving + combined]
    stage_three_configurations = list(dict.fromkeys([DEFAULT_ESTIMATOR, half_check] + improving
                                                    + [configuration for configuration in combined if configuration not in variants]))
    stage_three_items = [(identifier, grid[identifier], stage_three_configurations) for identifier in stage_two_identifiers]
    loaded, computed = run_items(stage_three_items, arguments.workers)
    for (identifier, configuration), value in loaded.items():
        arrays_by_key[(identifier, configuration)] = aligned_arrays(value, reference)
        if (identifier, configuration) not in rows:
            rows[(identifier, configuration)] = describe_row(identifier, grid[identifier], configuration, "3 joint confirmation",
                                                             arrays_by_key[(identifier, configuration)])
    print(f"stage 3: {len(stage_three_configurations)} estimator configurations, {computed} computed, {time.perf_counter() - started:.0f} s")

    # The final estimator is the one that is best across all stage-2 filters (mean MAE, then gross errors),
    # not the one of the single best row: the single best row is a near-tie among many and its estimator
    # can add half-rate errors on other filters.
    def robustness(configuration):
        values = [rows[(identifier, configuration)] for identifier in stage_two_identifiers]
        return (numpy.mean([row["reliable_mae_bpm"] for row in values]), sum(row["reliable_gross_error_count"] for row in values))

    best_configuration = min(stage_three_configurations, key=robustness)
    stage_four_items = [(identifier, spec, [best_configuration]) for identifier, spec in grid.items()]
    loaded, computed = run_items(stage_four_items, arguments.workers)
    for (identifier, configuration), value in loaded.items():
        arrays_by_key[(identifier, configuration)] = aligned_arrays(value, reference)
        if (identifier, configuration) not in rows:
            rows[(identifier, configuration)] = describe_row(identifier, grid[identifier], configuration, "4 final estimator over all filters",
                                                             arrays_by_key[(identifier, configuration)])
    print(f"stage 4: final estimator {best_configuration.key()} over {len(grid)} filters, {computed} computed, {time.perf_counter() - started:.0f} s")
    final_ranked = sorted([row for row in rows.values() if row["estimator"] == best_configuration.key()], key=ranking_key)
    best_row = final_ranked[0]

    listening_items = [(identifier, spec, list(dict.fromkeys([DEFAULT_ESTIMATOR, best_configuration])))
                       for identifier, spec in listening.items()]
    loaded, _ = run_items(listening_items, arguments.workers)
    listening_rows = []
    for (identifier, configuration), value in loaded.items():
        arrays_by_key[(identifier, configuration)] = aligned_arrays(value, reference)
        listening_rows.append(describe_row(identifier, listening[identifier], configuration, "listening filter as analysis",
                                           arrays_by_key[(identifier, configuration)]))

    bpm_report.write_outputs(rows=rows, final_ranked=final_ranked, stage_one_ranked=stage_one_ranked,
                             listening_rows=listening_rows, arrays_by_key=arrays_by_key, all_specs=all_specs,
                             best_configuration=best_configuration, variant_gain=variant_gain,
                             stage_three_configurations=stage_three_configurations, provisional=provisional,
                             reference_directory=reference_directory, bootstrap=bootstrap_indistinguishable,
                             ranking_key=ranking_key, top_filters=top_filters, build_candidate=build_candidate,
                             estimator_cost=estimator_cost)
    print(f"done in {time.perf_counter() - started:.0f} s; best {best_row['identifier']} / {best_row['estimator']}")


if __name__ == "__main__":
    main()
