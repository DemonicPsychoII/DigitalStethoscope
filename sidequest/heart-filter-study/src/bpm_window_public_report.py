"""Report for src/bpm_window_public.py: tables of the whole-window methods against the causal 40-150 Hz baseline.

Reads whatever is cached in cache/window/public/; writes results-window/public_ephnogram.csv and
results-window/per_window_public_<condition>.csv.
"""
import csv
import json
from pathlib import Path

import numpy

import bpm_evaluate
import bpm_window_public as public
import public_evaluation_common as common

RESULTS_DIRECTORY = public.own.RESULTS_DIRECTORY
BASELINE_KEY = public.own.BASELINE_KEY
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20261123


def load_condition(condition):
    """{method: list of window dicts} over records whose reference exists and every method is cached."""
    records = {info.record_name: info for info in public.evaluated_records()}
    complete_records = [name for name in sorted(records) if common.load_reference(name) is not None and all(
        public.cache_path(condition, name, method).exists() for method in public.PUBLIC_METHODS)]
    methods = public.PUBLIC_METHODS + [method for method in public.DIAGNOSTIC_METHODS if complete_records and all(
        public.cache_path(condition, name, method).exists() for name in complete_records)]
    windows = {method: [] for method in methods}
    for record_name in complete_records:
        info = records[record_name]
        paths = {method: public.cache_path(condition, record_name, method) for method in methods}
        reference = common.load_reference(record_name)
        for method, path in paths.items():
            for end_time, bpm, valid, quality, _, _ in json.loads(path.read_text())["rows"]:
                window = reference.get(int(end_time))
                if window is None or window.get("reference_bpm") is None or not numpy.isfinite(window["reference_bpm"]):
                    continue
                windows[method].append({"record": record_name, "subject": info.subject_id, "end_time": int(end_time),
                                        "reference": float(window["reference_bpm"]), "reliable": bool(window.get("reliable")),
                                        "estimate": float(bpm) if bpm is not None else float("nan"), "valid": bool(valid)})
    return windows, complete_records


def arrays_of(rows):
    return {key: numpy.array([row[key] for row in rows]) for key in ("record", "subject", "end_time", "reference", "reliable",
                                                                       "estimate", "valid")}


def block(arrays, mask):
    reference = arrays["reference"][mask]
    estimate = numpy.nan_to_num(arrays["estimate"][mask], nan=0.0)
    metrics = bpm_evaluate.metric_block(reference, estimate, arrays["valid"][mask], "") if reference.size else {}
    types = {"half rate": 0, "double rate": 0, "one third": 0, "other": 0}
    for value, truth in zip(arrays["estimate"][mask], reference):
        label = common.error_type(value, truth)
        if label in types:
            types[label] += 1
        elif label == "no estimate":
            types["other"] += 1
    return {"window_count": int(reference.size), "subject_count": int(numpy.unique(arrays["subject"][mask]).size),
            "mae_bpm": metrics.get("mae_bpm", float("nan")), "within_tolerance_share": metrics.get("within_tolerance_share", float("nan")),
            "gross_error_count": metrics.get("gross_error_count", 0), "valid_share": metrics.get("valid_share", float("nan")),
            "half_rate_count": types["half rate"], "double_rate_count": types["double rate"],
            "third_rate_count": types["one third"], "other_gross_count": types["other"]}


def cluster_bootstrap(method_arrays, baseline_arrays, mask):
    """Paired difference of mean absolute error (method minus baseline) on the masked windows, subjects resampled."""
    subjects = method_arrays["subject"][mask]
    method_error = numpy.abs(numpy.nan_to_num(method_arrays["estimate"][mask], nan=0.0) - method_arrays["reference"][mask])
    baseline_error = numpy.abs(numpy.nan_to_num(baseline_arrays["estimate"][mask], nan=0.0) - baseline_arrays["reference"][mask])
    unique_subjects, subject_index = numpy.unique(subjects, return_inverse=True)
    difference_sum = numpy.bincount(subject_index, weights=method_error - baseline_error, minlength=unique_subjects.size)
    count = numpy.bincount(subject_index, minlength=unique_subjects.size).astype(float)
    observed = difference_sum.sum() / count.sum()
    generator = numpy.random.default_rng(BOOTSTRAP_SEED)
    draws = generator.integers(0, unique_subjects.size, size=(BOOTSTRAP_RESAMPLES, unique_subjects.size))
    resampled = difference_sum[draws].sum(axis=1) / numpy.maximum(count[draws].sum(axis=1), 1.0)
    low, high = numpy.percentile(resampled, [2.5, 97.5])
    p_value = min(1.0, 2.0 * min((resampled <= 0).mean(), (resampled >= 0).mean()))
    return observed, float(low), float(high), float(max(p_value, 1.0 / BOOTSTRAP_RESAMPLES))


def holm(p_values):
    order = numpy.argsort(p_values)
    adjusted = numpy.empty(len(p_values))
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def report_condition(condition):
    windows, complete_records = load_condition(condition)
    if not complete_records:
        return [], complete_records
    arrays = {method: arrays_of(rows) for method, rows in windows.items()}
    baseline = arrays[BASELINE_KEY]
    for method, values in arrays.items():
        if not (numpy.array_equal(values["record"], baseline["record"]) and numpy.array_equal(values["end_time"], baseline["end_time"])):
            raise SystemExit(f"{condition}: windows of {method} differ from the baseline")
    rows = []
    reliable = baseline["reliable"]
    everything = numpy.ones(reliable.shape, bool)
    compared = [method for method in public.PUBLIC_METHODS if method != BASELINE_KEY]
    diagnostic = [method for method in arrays if method in public.DIAGNOSTIC_METHODS]
    tests = {method: cluster_bootstrap(arrays[method], baseline, reliable) for method in compared}
    adjusted = dict(zip(compared, holm(numpy.array([tests[method][3] for method in compared]))))
    for method in public.PUBLIC_METHODS + diagnostic:
        for scope, mask in (("all windows", everything), ("reliable windows", reliable)):
            row = {"condition": condition, "scope": scope, "group": "overall", "method": method, **block(arrays[method], mask)}
            if scope == "reliable windows" and method in diagnostic:
                observed, low, high, p_value = cluster_bootstrap(arrays[method], baseline, mask)
                row.update({"difference_to_baseline_bpm": observed, "difference_low_95_bpm": low, "difference_high_95_bpm": high,
                            "bootstrap_p": p_value, "note": "diagnostic, added after seeing results; not in the Holm family"})
            elif scope == "reliable windows" and method != BASELINE_KEY:
                observed, low, high, p_value = tests[method]
                row.update({"difference_to_baseline_bpm": observed, "difference_low_95_bpm": low, "difference_high_95_bpm": high,
                            "bootstrap_p": p_value, "holm_adjusted_p": adjusted[method]})
            if scope == "all windows" and method != BASELINE_KEY:
                observed, low, high, p_value = cluster_bootstrap(arrays[method], baseline, everything)
                row.update({"difference_to_baseline_bpm": observed, "difference_low_95_bpm": low, "difference_high_95_bpm": high,
                            "bootstrap_p": p_value})
            rows.append(row)
        bands = numpy.array([common.heart_rate_band(value) for value in baseline["reference"]])
        for _, _, label in common.HEART_RATE_BANDS:
            mask = reliable & (bands == label)
            if mask.any():
                row = {"condition": condition, "scope": "reliable windows", "group": f"ECG band {label} BPM", "method": method,
                       **block(arrays[method], mask)}
                if method != BASELINE_KEY and numpy.unique(baseline["subject"][mask]).size >= 2:
                    observed, low, high, p_value = cluster_bootstrap(arrays[method], baseline, mask)
                    row.update({"difference_to_baseline_bpm": observed, "difference_low_95_bpm": low,
                                "difference_high_95_bpm": high, "bootstrap_p": p_value})
                rows.append(row)
        for subject in numpy.unique(baseline["subject"]):
            mask = reliable & (baseline["subject"] == subject)
            if mask.any():
                rows.append({"condition": condition, "scope": "reliable windows", "group": f"subject {subject}", "method": method,
                             **block(arrays[method], mask)})
    write_per_window(condition, arrays)
    return rows, complete_records


PER_WINDOW_METHODS = ["causal_40_150", "causal_25_150", "causal_raw", "zero_phase_40_150_order2_reflect_zpenv",
                      "streamed_forward_backward_window_40_150_order2_reflect_zpenv",
                      "reduced_1k_zero_phase_40_150_order2_reflect_zpenv", "stored_envelope_smooth5hz_taper0",
                      "springer_heart_rate", "springer_heart_rate_range_30_200", "springer_envelopes_combined_50hz_half_check"]


def write_per_window(condition, arrays):
    baseline = arrays[BASELINE_KEY]
    with open(RESULTS_DIRECTORY / f"per_window_public_{condition}.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record", "subject", "end_time_s", "reference_bpm", "reliable"] + [f"{method}_bpm" for method in PER_WINDOW_METHODS])
        for index in range(baseline["record"].size):
            writer.writerow([baseline["record"][index], baseline["subject"][index], int(baseline["end_time"][index]),
                             f"{baseline['reference'][index]:.2f}", bool(baseline["reliable"][index])]
                            + [f"{arrays[method]['estimate'][index]:.2f}" for method in PER_WINDOW_METHODS])


def report(arguments):
    all_rows = []
    for condition in arguments.conditions.split(","):
        rows, complete_records = report_condition(condition)
        print(f"{condition}: {len(complete_records)} records complete")
        all_rows += rows
        overall = [row for row in rows if row["group"] == "overall" and row["scope"] == "reliable windows"]
        for row in sorted(overall, key=lambda row: row["mae_bpm"]):
            print(f"  {row['method'][:60]:60s} {row['mae_bpm']:7.2f} BPM  within {row['within_tolerance_share']:.3f}  "
                  f"gross {row['gross_error_count']:5d}  diff {row.get('difference_to_baseline_bpm', 0):+.2f} "
                  f"[{row.get('difference_low_95_bpm', 0):+.2f}, {row.get('difference_high_95_bpm', 0):+.2f}] "
                  f"Holm p {row.get('holm_adjusted_p', float('nan')):.3f}  n={row['window_count']} subjects={row['subject_count']}")
    fields = list(dict.fromkeys(name for row in all_rows for name in row))
    with open(RESULTS_DIRECTORY / "public_ephnogram.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({name: (f"{value:.4f}" if isinstance(value, float) else value) for name, value in row.items()})
