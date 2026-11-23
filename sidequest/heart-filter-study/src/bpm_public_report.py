"""Tables and summary of the run-2 BPM evaluation (EPHNOGRAM sound through the modelled chain, ECG reference).

Reads the estimate cache written by `bpm_evaluate_public.py compute` and the ECG reference in
reference-public/ephnogram/. Writes results-public/bpm_public_grid.csv, bpm_public_by_band.csv,
bpm_public_by_scenario.csv, bpm_public_per_subject.csv, bpm_public_per_window.csv, bpm_public_run1_comparison.csv
and SUMMARY.md.
"""
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import public_evaluation_common as common
import bpm_evaluate
from hfs import ephnogram

RESULTS_DIRECTORY = common.RESULTS_DIRECTORY
RUN1_GRID = common.STUDY_DIRECTORY / "results" / "bpm_filter_grid.csv"
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20261123
INTERPRETATION_PATH = RESULTS_DIRECTORY / "INTERPRETATION.md"
CONDITION_LABELS = {"rest": "rest level, microphone only", "overload": "overload level, microphone only",
                    "rest_matched": "rest level, spectrum matched to own recordings"}
RUN1_ESTIMATOR_KEYS = {key: configuration.key() for key, configuration in common.ESTIMATOR_VARIANTS.items()}


def scenario_group(scenario):
    text = scenario.lower()
    if text.startswith("rest: sitting"):
        return "rest sitting"
    if text.startswith("rest: laying"):
        return "rest lying"
    if "bruce" in text:
        return "treadmill stress test"
    if "bicycle stress" in text:
        return "bicycle stress test"
    if "pedaling" in text:
        return "bicycle constant"
    if "3.7 km/h" in text:
        return "walking constant"
    if "slow walk" in text:
        return "walk-sit-stand protocol"
    return text


def is_good_sound(record):
    return record.pcg_quality.strip().lower() == "good"


@dataclass
class RecordWindows:
    record_name: str
    subject_id: str
    scenario: str
    pcg_quality: str
    end_time: numpy.ndarray
    reference: numpy.ndarray
    reliable: numpy.ndarray


@dataclass
class RowData:
    condition: str
    identifier: str
    estimator: str
    records: dict = field(default_factory=dict)


def load_reference_windows():
    windows = {}
    excluded = common.duplicate_records_excluded()
    for info in ephnogram.list_records():
        if info.record_name in excluded:
            continue
        reference = common.load_reference(info.record_name)
        if reference is None:
            continue
        end_times = sorted(time for time, window in reference.items()
                           if time >= common.FIRST_SCORED_END_TIME_SECONDS and window.get("reference_bpm") is not None
                           and numpy.isfinite(window["reference_bpm"]))
        windows[info.record_name] = RecordWindows(
            info.record_name, info.subject_id, scenario_group(info.scenario), info.pcg_quality,
            numpy.array(end_times, dtype=int), numpy.array([reference[time]["reference_bpm"] for time in end_times], float),
            numpy.array([bool(reference[time].get("reliable", False)) for time in end_times]))
    return windows


CONSOLIDATED_CACHE_PATH = common.CACHE_DIRECTORY / "consolidated.pickle"


def consolidated_estimates():
    """{(condition, record, identifier): estimates}; re-reads only cache files whose modification time changed,
    because opening thousands of small files dominates the report time on this machine."""
    import pickle
    previous = {}
    if CONSOLIDATED_CACHE_PATH.exists():
        previous = pickle.loads(CONSOLIDATED_CACHE_PATH.read_bytes())
    current = {}
    for condition in common.CONDITIONS:
        condition_directory = common.CACHE_DIRECTORY / condition
        if not condition_directory.exists():
            continue
        for record_directory in condition_directory.iterdir():
            for entry in os.scandir(record_directory):
                if not entry.name.endswith(".npz") or entry.name.endswith(".partial.npz"):
                    continue
                key = (condition, record_directory.name, entry.name[:-4])
                modified = entry.stat().st_mtime_ns
                if key in previous and previous[key][0] == modified:
                    current[key] = previous[key]
                else:
                    current[key] = (modified, common.cached_estimates(record_directory.name, condition, key[2]))
    CONSOLIDATED_CACHE_PATH.write_bytes(pickle.dumps(current, protocol=pickle.HIGHEST_PROTOCOL))
    return {key: value[1] for key, value in current.items()}


def load_rows(reference_windows):
    rows = {}
    consolidated = consolidated_estimates()
    for (condition, record_name, identifier), estimates in sorted(consolidated.items()):
        record = reference_windows.get(record_name)
        if record is None:
            continue
        for estimator_name, configuration in common.ESTIMATOR_VARIANTS.items():
            key = common.configuration_key(configuration)
            if key not in estimates:
                continue
            values = estimates[key]
            index = record.end_time - 1
            if not (index < values.shape[0]).all():
                continue
            row = rows.setdefault((condition, identifier, estimator_name), RowData(condition, identifier, estimator_name))
            row.records[record_name] = {"estimate": values[index, 1].astype(float), "valid": values[index, 2] > 0.5}
    return rows


def pooled(row, reference_windows, record_names=None, mask_function=None):
    names = [name for name in (record_names or row.records) if name in row.records]
    parts = {"reference": [], "estimate": [], "valid": [], "reliable": [], "subject": [], "record": []}
    for name in names:
        record = reference_windows[name]
        mask = numpy.ones(record.end_time.shape, bool) if mask_function is None else mask_function(record)
        parts["reference"].append(record.reference[mask])
        parts["estimate"].append(row.records[name]["estimate"][mask])
        parts["valid"].append(row.records[name]["valid"][mask])
        parts["reliable"].append(record.reliable[mask])
        parts["subject"].append(numpy.full(int(mask.sum()), record.subject_id, dtype=object))
        parts["record"].append(numpy.full(int(mask.sum()), name, dtype=object))
    if not names:
        return {key: numpy.array([]) for key in parts}
    return {key: numpy.concatenate(value) for key, value in parts.items()}


def error_type_counts(reference, estimate):
    """Vectorised form of common.error_type; a missing estimate counts as other."""
    with numpy.errstate(invalid="ignore", divide="ignore"):
        ratio = estimate / reference
    gross = ~(numpy.abs(ratio - 1.0) <= 0.2)
    half = gross & (numpy.abs(ratio / 0.5 - 1.0) <= 0.1)
    double = gross & ~half & (numpy.abs(ratio / 2.0 - 1.0) <= 0.1)
    third = gross & ~half & ~double & (numpy.abs(ratio * 3.0 - 1.0) <= 0.1)
    return {"half rate": int(half.sum()), "double rate": int(double.sum()), "one third": int(third.sum()),
            "other": int((gross & ~half & ~double & ~third).sum())}


def window_metrics(data):
    """Run-1 metrics on all windows and on ECG-reliable windows, plus error types and the acceptance target."""
    metrics = {}
    for subset, prefix in (("all", "all_"), ("reliable", "reliable_")):
        mask = numpy.ones(data["reference"].shape, bool) if subset == "all" else data["reliable"].astype(bool)
        block = bpm_evaluate.metric_block(data["reference"][mask], data["estimate"][mask], data["valid"][mask], prefix) \
            if mask.any() else {f"{prefix}window_count": 0}
        metrics.update(block)
        metrics[f"{prefix}subject_count"] = len(set(data["subject"][mask])) if mask.any() else 0
    reliable = data["reliable"].astype(bool)
    counts = error_type_counts(data["reference"][reliable], data["estimate"][reliable])
    for name, count in counts.items():
        metrics[f"reliable_{name.replace(' ', '_')}_count"] = count
    valid_mae = metrics.get("reliable_valid_mae_bpm", float("nan"))
    valid_share = metrics.get("reliable_valid_share", float("nan"))
    metrics["acceptance_target_met"] = bool(numpy.isfinite(valid_mae) and valid_mae <= 5.0 and valid_share >= 0.9)
    return metrics


def subject_sums(row, reference_windows, subjects, record_names=None, mask_function=None):
    """Per subject (aligned to `subjects`): absolute-error sum and window count on reliable and on all windows."""
    index = {subject: position for position, subject in enumerate(subjects)}
    sums = numpy.zeros((4, len(subjects)))
    for name in (record_names or row.records):
        if name not in row.records:
            continue
        record = reference_windows[name]
        mask = numpy.ones(record.end_time.shape, bool) if mask_function is None else mask_function(record)
        error = numpy.abs(row.records[name]["estimate"][mask] - record.reference[mask])
        reliable = record.reliable[mask]
        position = index[record.subject_id]
        sums[0, position] += error[reliable].sum()
        sums[1, position] += reliable.sum()
        sums[2, position] += error.sum()
        sums[3, position] += mask.sum()
    return sums


def bootstrap_indices(subject_count):
    generator = numpy.random.default_rng(BOOTSTRAP_SEED)
    return generator.integers(0, subject_count, size=(BOOTSTRAP_RESAMPLES, subject_count))


def resampled_mae(sums, indices, error_row, count_row):
    totals = sums[error_row][indices].sum(axis=1)
    counts = sums[count_row][indices].sum(axis=1)
    with numpy.errstate(invalid="ignore", divide="ignore"):
        return totals / counts


def interval(values):
    finite = values[numpy.isfinite(values)]
    if finite.size == 0:
        return float("nan"), float("nan")
    low, high = numpy.percentile(finite, [2.5, 97.5])
    return float(low), float(high)


def two_sided_p(differences):
    finite = differences[numpy.isfinite(differences)]
    if finite.size == 0:
        return float("nan")
    below = (numpy.count_nonzero(finite <= 0) + 1) / (finite.size + 1)
    above = (numpy.count_nonzero(finite >= 0) + 1) / (finite.size + 1)
    return float(min(1.0, 2 * min(below, above)))


def wald_p(observed, differences):
    """Two-sided p from the bootstrap standard error of the paired difference (normal approximation); unlike the
    bootstrap share it is not limited to multiples of 1 / resamples, which a Holm correction over ~100 tests needs."""
    finite = differences[numpy.isfinite(differences)]
    if finite.size < 2:
        return float("nan")
    standard_error = float(numpy.std(finite, ddof=1))
    if standard_error == 0.0:
        return 1.0 if observed == 0 else 0.0
    return float(2 * stats.norm.sf(abs(observed) / standard_error))


def holm(p_values):
    order = numpy.argsort(p_values)
    adjusted = numpy.empty(len(p_values))
    running = 0.0
    count = len(p_values)
    for rank, position in enumerate(order):
        running = max(running, min(1.0, (count - rank) * p_values[position]))
        adjusted[position] = running
    return adjusted


def candidate_description(identifier):
    specifications = common.candidate_specifications()
    if identifier in specifications:
        return bpm_evaluate.build_candidate(specifications[identifier]).description
    return identifier


def format_number(value, digits=2):
    if value is None or (isinstance(value, float) and not numpy.isfinite(value)):
        return "n/a"
    return f"{value:.{digits}f}"


def format_share(value):
    if value is None or not numpy.isfinite(value):
        return "n/a"
    return f"{100 * value:.1f} %"


def read_run1_grid():
    rows = {}
    with open(RUN1_GRID, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.setdefault((row["identifier"], row["estimator"]), row)
    return rows


def write_csv(path, rows, header=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = header or list(dict.fromkeys(key for row in rows for key in row))
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (f"{value:.4g}" if isinstance(value, float) else value) for key, value in row.items()})


def write_report():
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    reference_windows = load_reference_windows()
    rows = load_rows(reference_windows)
    if not rows:
        raise SystemExit("no cached estimates with an ECG reference yet")
    summary_lines = []
    grid_rows, band_rows, scenario_rows, subject_rows = [], [], [], []
    comparisons = {}
    for condition in common.CONDITIONS:
        condition_rows = {key: row for key, row in rows.items() if key[0] == condition}
        if not condition_rows:
            continue
        subjects = sorted({reference_windows[name].subject_id for row in condition_rows.values() for name in row.records})
        indices = bootstrap_indices(len(subjects))
        anchors = {"recommended": (condition, common.RECOMMENDED, "final"), "planned": (condition, common.PLANNED, "final")}
        anchor_sums = {}
        for anchor_name, anchor_key in anchors.items():
            if anchor_key in condition_rows:
                anchor_sums[anchor_name] = anchor_key
        computed = {}
        for key, row in condition_rows.items():
            data = pooled(row, reference_windows)
            metrics = window_metrics(data)
            sums = subject_sums(row, reference_windows, subjects)
            reliable_low, reliable_high = interval(resampled_mae(sums, indices, 0, 1))
            all_low, all_high = interval(resampled_mae(sums, indices, 2, 3))
            subject_mae = []
            for position, subject in enumerate(subjects):
                if sums[1, position] > 0:
                    subject_mae.append(sums[0, position] / sums[1, position])
                    subject_rows.append({"condition": condition, "identifier": row.identifier, "estimator": row.estimator,
                                         "subject_id": subject, "reliable_mae_bpm": sums[0, position] / sums[1, position],
                                         "reliable_window_count": int(sums[1, position]),
                                         "all_mae_bpm": sums[2, position] / max(sums[3, position], 1),
                                         "all_window_count": int(sums[3, position])})
            grid_row = {"condition": condition, "identifier": row.identifier, "estimator": row.estimator,
                        "estimator_key": common.ESTIMATOR_VARIANTS[row.estimator].key(),
                        "description": candidate_description(row.identifier), "record_count": len(row.records),
                        **metrics,
                        "reliable_mae_interval_low": reliable_low, "reliable_mae_interval_high": reliable_high,
                        "all_mae_interval_low": all_low, "all_mae_interval_high": all_high,
                        "subject_mean_reliable_mae_bpm": float(numpy.mean(subject_mae)) if subject_mae else float("nan"),
                        "worst_subject_reliable_mae_bpm": float(numpy.max(subject_mae)) if subject_mae else float("nan"),
                        "worst_subject": subjects[int(numpy.nanargmax(numpy.where(sums[1] > 0, sums[0] / numpy.maximum(sums[1], 1), -1)))]
                        if subject_mae else ""}
            good_records = [name for name in row.records if is_good_sound(reference_windows[name])]
            good_metrics = window_metrics(pooled(row, reference_windows, good_records)) if good_records else {}
            good_sums = subject_sums(row, reference_windows, subjects, good_records)
            good_low, good_high = interval(resampled_mae(good_sums, indices, 0, 1))
            grid_row["good_sound_record_count"] = len(good_records)
            for name in ("reliable_mae_bpm", "reliable_median_absolute_error_bpm", "reliable_within_tolerance_share",
                         "reliable_gross_error_count", "reliable_valid_share", "reliable_valid_mae_bpm", "reliable_window_count",
                         "reliable_subject_count", "all_mae_bpm", "acceptance_target_met"):
                grid_row[f"good_sound_{name}"] = good_metrics.get(name, float("nan"))
            grid_row["good_sound_reliable_mae_interval_low"] = good_low
            grid_row["good_sound_reliable_mae_interval_high"] = good_high
            computed[key] = (grid_row, row)
        for anchor_name, anchor_key in anchor_sums.items():
            anchor_row = condition_rows[anchor_key]
            family = [key for key in computed if key != anchor_key]
            p_values = []
            for key in family:
                row = computed[key][1]
                common_records = [name for name in row.records if name in anchor_row.records]
                candidate_sums = subject_sums(row, reference_windows, subjects, common_records)
                anchor_common = subject_sums(anchor_row, reference_windows, subjects, common_records)
                differences = (resampled_mae(candidate_sums, indices, 0, 1) - resampled_mae(anchor_common, indices, 0, 1))
                observed = candidate_sums[0].sum() / max(candidate_sums[1].sum(), 1) - anchor_common[0].sum() / max(anchor_common[1].sum(), 1)
                low, high = interval(differences)
                p_value = wald_p(observed, differences)
                p_values.append(p_value)
                grid_row = computed[key][0]
                grid_row[f"difference_to_{anchor_name}_reliable_mae_bpm"] = observed
                grid_row[f"difference_to_{anchor_name}_interval_low"] = low
                grid_row[f"difference_to_{anchor_name}_interval_high"] = high
                grid_row[f"difference_to_{anchor_name}_p"] = p_value
                grid_row[f"difference_to_{anchor_name}_subject_count"] = int(numpy.count_nonzero(candidate_sums[1] > 0))
            adjusted = holm(numpy.array(p_values)) if p_values else []
            for key, value in zip(family, adjusted):
                computed[key][0][f"difference_to_{anchor_name}_p_holm"] = float(value)
            comparisons[(condition, anchor_name)] = len(family)
        for key, (grid_row, row) in computed.items():
            grid_rows.append(grid_row)
            band_rows += band_metrics(row, reference_windows, subjects, indices)
            scenario_rows += scenario_metrics(row, reference_windows)
    grid_rows.sort(key=lambda row: (list(common.CONDITIONS).index(row["condition"]), row.get("reliable_mae_bpm", 1e9)))
    write_csv(RESULTS_DIRECTORY / "bpm_public_grid.csv", grid_rows)
    write_csv(RESULTS_DIRECTORY / "bpm_public_by_band.csv", band_rows)
    write_csv(RESULTS_DIRECTORY / "bpm_public_by_scenario.csv", scenario_rows)
    write_csv(RESULTS_DIRECTORY / "bpm_public_per_subject.csv", subject_rows)
    comparison_rows, spearman = run1_comparison(grid_rows)
    write_csv(RESULTS_DIRECTORY / "bpm_public_run1_comparison.csv", comparison_rows)
    write_per_window(rows, reference_windows)
    write_summary(grid_rows, band_rows, scenario_rows, comparison_rows, spearman, comparisons, reference_windows, rows)
    print(f"report: {len(grid_rows)} grid rows")


def band_metrics(row, reference_windows, subjects, indices):
    output = []
    for low, high, label in common.HEART_RATE_BANDS:
        def mask_function(record, low=low, high=high):
            return (record.reference >= low) & (record.reference < high)
        data = pooled(row, reference_windows, mask_function=mask_function)
        if data["reference"].size == 0:
            continue
        metrics = window_metrics(data)
        sums = subject_sums(row, reference_windows, subjects, mask_function=mask_function)
        reliable_low, reliable_high = interval(resampled_mae(sums, indices, 0, 1))
        output.append({"condition": row.condition, "identifier": row.identifier, "estimator": row.estimator,
                       "band_bpm": label, **metrics, "reliable_mae_interval_low": reliable_low,
                       "reliable_mae_interval_high": reliable_high})
    return output


def scenario_metrics(row, reference_windows):
    output = []
    groups = sorted({reference_windows[name].scenario for name in row.records})
    for group in groups:
        data = pooled(row, reference_windows, [name for name in row.records if reference_windows[name].scenario == group])
        output.append({"condition": row.condition, "identifier": row.identifier, "estimator": row.estimator,
                       "scenario": group, **window_metrics(data)})
    return output


def run1_comparison(grid_rows):
    run1 = read_run1_grid()
    comparison = []
    lookup = {(row["condition"], row["identifier"], row["estimator"]): row for row in grid_rows}
    for edge, identifier in common.LOWER_EDGE_SWEEP.items():
        for estimator in common.ESTIMATOR_VARIANTS:
            run1_row = run1.get((identifier, RUN1_ESTIMATOR_KEYS[estimator]))
            entry = {"table": "lower edge sweep" if estimator == "final" else "lower edge sweep, other counting method",
                     "identifier": identifier, "lower_edge_hz": "none" if edge is None else edge, "estimator": estimator}
            if run1_row:
                entry.update({"run1_reliable_mae_bpm": float(run1_row["reliable_mae_bpm"]),
                              "run1_all_mae_bpm": float(run1_row["all_mae_bpm"]),
                              "run1_all_gross_error_count": int(run1_row["all_gross_error_count"]),
                              "run1_all_window_count": int(run1_row["all_window_count"]),
                              "run1_reliable_window_count": int(run1_row["reliable_window_count"])})
            for condition in common.CONDITIONS:
                public = lookup.get((condition, identifier, estimator))
                if public:
                    entry[f"{condition}_reliable_mae_bpm"] = public.get("reliable_mae_bpm")
                    entry[f"{condition}_reliable_interval"] = (f"{public['reliable_mae_interval_low']:.2f}-"
                                                               f"{public['reliable_mae_interval_high']:.2f}")
                    entry[f"{condition}_all_mae_bpm"] = public.get("all_mae_bpm")
                    entry[f"{condition}_reliable_gross_error_count"] = public.get("reliable_gross_error_count")
                    entry[f"{condition}_reliable_window_count"] = public.get("reliable_window_count")
                    entry[f"{condition}_subject_count"] = public.get("reliable_subject_count")
            if run1_row or any(key.endswith("_reliable_mae_bpm") and not key.startswith("run1") for key in entry):
                comparison.append(entry)
    spearman = {}
    for condition in common.CONDITIONS:
        for estimator in ("first_draft", "final"):
            pairs = []
            for row in grid_rows:
                if row["condition"] != condition or row["estimator"] != estimator:
                    continue
                run1_row = run1.get((row["identifier"], RUN1_ESTIMATOR_KEYS[estimator]))
                if run1_row and numpy.isfinite(row.get("reliable_mae_bpm", numpy.nan)):
                    pairs.append((row["identifier"], float(run1_row["reliable_mae_bpm"]), row["reliable_mae_bpm"],
                                  float(run1_row["all_mae_bpm"]), row["all_mae_bpm"]))
            if len(pairs) >= 4:
                reliable = stats.spearmanr([pair[1] for pair in pairs], [pair[2] for pair in pairs])
                all_windows = stats.spearmanr([pair[3] for pair in pairs], [pair[4] for pair in pairs])
                spearman[(condition, estimator)] = {"count": len(pairs), "reliable_rho": float(reliable.statistic),
                                                    "reliable_p": float(reliable.pvalue),
                                                    "all_rho": float(all_windows.statistic), "all_p": float(all_windows.pvalue),
                                                    "pairs": pairs}
    return comparison, spearman


def write_per_window(rows, reference_windows):
    keys = [(identifier, estimator) for identifier in common.MAIN_CANDIDATES for estimator in common.ESTIMATOR_VARIANTS]
    path = RESULTS_DIRECTORY / "bpm_public_per_window.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["condition", "record", "subject_id", "scenario", "end_time_s", "ecg_reference_bpm", "ecg_reliable"]
                        + [f"{identifier}__{estimator}__{field_name}" for identifier, estimator in keys
                           for field_name in ("bpm", "valid")])
        for condition in common.CONDITIONS:
            available = {key: rows.get((condition, *key)) for key in keys}
            if not any(available.values()):
                continue
            record_names = sorted({name for row in available.values() if row for name in row.records})
            for name in record_names:
                record = reference_windows[name]
                columns = []
                for key in keys:
                    row = available[key]
                    if row and name in row.records:
                        columns.append((row.records[name]["estimate"], row.records[name]["valid"]))
                    else:
                        columns.append(None)
                for position, end_time in enumerate(record.end_time):
                    values = []
                    for column in columns:
                        if column is None:
                            values += ["", ""]
                        else:
                            values += [f"{column[0][position]:.2f}", int(column[1][position])]
                    writer.writerow([condition, name, record.subject_id, record.scenario, int(end_time),
                                     f"{record.reference[position]:.2f}", int(record.reliable[position])] + values)


def write_summary(grid_rows, band_rows, scenario_rows, comparison_rows, spearman, comparisons, reference_windows, rows):
    lines = ["# Run 2: BPM filter and counting method on EPHNOGRAM against ECG", "",
             "Generated by `src/bpm_public_report.py` from the estimate cache; numbers are recomputed on every run.", ""]
    lines += data_basis_lines(grid_rows, reference_windows, rows)
    lines += definition_lines(comparisons)
    lines += key_table_lines(grid_rows)
    for condition in common.CONDITIONS:
        condition_rows = [row for row in grid_rows if row["condition"] == condition]
        if not condition_rows:
            continue
        lines += [f"## Overall, {CONDITION_LABELS[condition]}", "",
                  "Ranked by mean absolute error on ECG-reliable windows. Interval: 95 % subject bootstrap. "
                  "Difference: to the recommended 40-150 Hz with the final method (negative = better), Holm-adjusted p.", "",
                  "| candidate | counting method | MAE reliable (95 % interval) | median AE reliable | MAE all | within tolerance | gross errors | "
                  "half / double / third / other | valid | MAE valid | target met | mean / worst subject | "
                  "difference to recommended (interval, Holm p) | subjects / windows |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for row in condition_rows:
            difference = row.get("difference_to_recommended_reliable_mae_bpm")
            difference_text = "reference" if difference is None and row["identifier"] == common.RECOMMENDED and row["estimator"] == "final" \
                else (f"{difference:+.2f} ({row['difference_to_recommended_interval_low']:+.2f} to "
                      f"{row['difference_to_recommended_interval_high']:+.2f}, {format_number(row.get('difference_to_recommended_p_holm'), 3)})"
                      if difference is not None else "n/a")
            lines.append(
                f"| {row['identifier']} | {row['estimator']} | {format_number(row.get('reliable_mae_bpm'))} "
                f"({format_number(row['reliable_mae_interval_low'])}-{format_number(row['reliable_mae_interval_high'])}) | "
                f"{format_number(row.get('reliable_median_absolute_error_bpm'))} | {format_number(row.get('all_mae_bpm'))} | {format_share(row.get('reliable_within_tolerance_share'))} | "
                f"{row.get('reliable_gross_error_count', 'n/a')} | {row['reliable_half_rate_count']} / {row['reliable_double_rate_count']} / "
                f"{row['reliable_one_third_count']} / {row['reliable_other_count']} | {format_share(row.get('reliable_valid_share'))} | "
                f"{format_number(row.get('reliable_valid_mae_bpm'))} | {'yes' if row['acceptance_target_met'] else 'no'} | "
                f"{format_number(row['subject_mean_reliable_mae_bpm'])} / {format_number(row['worst_subject_reliable_mae_bpm'])} "
                f"({row['worst_subject']}) | {difference_text} | {row['reliable_subject_count']} / {row.get('reliable_window_count', 0)} |")
        lines.append("")
        lines += band_table_lines(band_rows, condition)
        lines += scenario_table_lines(scenario_rows, condition)
    lines += run1_table_lines(comparison_rows, spearman)
    if INTERPRETATION_PATH.exists():
        lines += ["", INTERPRETATION_PATH.read_text(encoding="utf-8").strip(), ""]
    (RESULTS_DIRECTORY / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def data_basis_lines(grid_rows, reference_windows, rows):
    lines = ["## Data basis", ""]
    for condition in common.CONDITIONS:
        condition_rows = [row for key, row in rows.items() if key[0] == condition]
        if not condition_rows:
            continue
        record_names = sorted({name for row in condition_rows for name in row.records})
        complete = [row for row in condition_rows if len(row.records) == len(record_names)]
        subjects = {reference_windows[name].subject_id for name in record_names}
        seconds = sum(reference_windows[name].end_time.size for name in record_names)
        reliable = sum(int(reference_windows[name].reliable.sum()) for name in record_names)
        poor = sorted(name for name in record_names if reference_windows[name].pcg_quality.lower() != "good")
        lines.append(f"- {CONDITION_LABELS[condition]}: {len(record_names)} records, {len(subjects)} subjects, "
                     f"{seconds} scored windows ({seconds / 3600:.1f} h of window ends), {reliable} ECG-reliable; "
                     f"{len(complete)} of {len(condition_rows)} candidate x method rows cover every record. "
                     f"Records whose sound the spreadsheet does not call good (kept, flagged): {', '.join(poor) or 'none'}.")
    lines.append("")
    return lines


def definition_lines(comparisons):
    family_text = "; ".join(f"{CONDITION_LABELS[condition]} vs {anchor}: {count} comparisons"
                            for (condition, anchor), count in comparisons.items())
    return ["## Definitions", "",
            f"- Windows: 8 s, one per second, matched to the ECG reference by absolute record time; window ends before "
            f"{common.FIRST_SCORED_END_TIME_SECONDS} s are ignored. The estimator and filters start at record time 0.",
            "- Metrics as run 1 (`bpm_evaluate.metric_block`): MAE, within tolerance max(5 BPM, 10 %), gross error = more than "
            "20 % off, valid share = estimator's own validity flag (quality >= 0.3, clipping share, range 30-200 BPM). "
            "'Reliable' means the ECG reference marks the window reliable (both detectors agree, clean ECG); it says nothing "
            "about the sound.",
            "- Error types (reliable windows, gross errors only): half rate = estimate / ECG within 10 % of 0.5, double rate "
            "within 10 % of 2, one third within 10 % of 1/3, other = the rest.",
            "- Acceptance target (evaluation guide EVAL-GUIDE: provisional BPM MAE <= 5 BPM with >= 90 % valid windows): "
            "here on ECG-reliable windows, MAE of the valid estimates <= 5 BPM and valid share >= 90 %.",
            "- Intervals: cluster bootstrap over subjects, 2,000 resamples, seed 20261123, window-weighted MAE (sum of errors / "
            "number of windows in the resample). Paired differences use the same resamples and the records both rows cover. "
            "p = two-sided normal approximation with the bootstrap standard error of the paired difference (the bootstrap "
            "share itself cannot fall below 1/2,000, too coarse for a Holm correction over ~100 tests); Holm correction within each family. Family = every other candidate x counting-method "
            f"row of the same condition against one anchor ({family_text}).", ""]


def key_table_lines(grid_rows):
    lines = ["## Key results: main candidates", "",
             "MAE and median on ECG-reliable windows (95 % subject-bootstrap interval); 'good sound' = only records whose sound "
             "the spreadsheet calls good.", "",
             "| condition | candidate | counting method | MAE (interval) | median | within tolerance | gross | valid | target met "
             "| subjects / windows | good sound: MAE (interval), within tolerance, target met, subjects / windows |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    lookup = {(row["condition"], row["identifier"], row["estimator"]): row for row in grid_rows}
    for condition in common.CONDITIONS:
        for identifier in common.MAIN_CANDIDATES:
            for estimator in common.ESTIMATOR_VARIANTS:
                row = lookup.get((condition, identifier, estimator))
                if row is None:
                    continue
                lines.append(
                    f"| {condition} | {common.CANDIDATE_LABELS[identifier]} | {estimator} | "
                    f"{format_number(row.get('reliable_mae_bpm'))} ({format_number(row['reliable_mae_interval_low'])}-"
                    f"{format_number(row['reliable_mae_interval_high'])}) | {format_number(row.get('reliable_median_absolute_error_bpm'))} | "
                    f"{format_share(row.get('reliable_within_tolerance_share'))} | {row.get('reliable_gross_error_count')} | "
                    f"{format_share(row.get('reliable_valid_share'))} | {'yes' if row['acceptance_target_met'] else 'no'} | "
                    f"{row['reliable_subject_count']} / {row.get('reliable_window_count')} | "
                    f"{format_number(row.get('good_sound_reliable_mae_bpm'))} ({format_number(row.get('good_sound_reliable_mae_interval_low'))}-"
                    f"{format_number(row.get('good_sound_reliable_mae_interval_high'))}), "
                    f"{format_share(row.get('good_sound_reliable_within_tolerance_share'))}, "
                    f"{'yes' if row.get('good_sound_acceptance_target_met') is True else 'no'}, "
                    f"{row.get('good_sound_reliable_subject_count')} / {row.get('good_sound_reliable_window_count')} |")
    return lines + [""]


def band_table_lines(band_rows, condition):
    lines = ["### By ECG heart-rate band (final counting method)", "",
             "| band (BPM) | " + " | ".join(common.CANDIDATE_LABELS[identifier] for identifier in common.MAIN_CANDIDATES) + " |",
             "|---|" + "---|" * len(common.MAIN_CANDIDATES)]
    for _, _, label in common.HEART_RATE_BANDS:
        cells = []
        for identifier in common.MAIN_CANDIDATES:
            match = [row for row in band_rows if row["condition"] == condition and row["identifier"] == identifier
                     and row["estimator"] == "final" and row["band_bpm"] == label]
            if not match or not match[0].get("reliable_window_count"):
                cells.append("n/a")
                continue
            row = match[0]
            cells.append(f"{format_number(row.get('reliable_mae_bpm'))} ({format_number(row['reliable_mae_interval_low'])}-"
                         f"{format_number(row['reliable_mae_interval_high'])}), {row['reliable_gross_error_count']} gross, "
                         f"{row['reliable_subject_count']} subj / {row['reliable_window_count']} win")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines + [""]


def scenario_table_lines(scenario_rows, condition):
    lines = ["### By activity scenario (final counting method, MAE on reliable windows)", "",
             "| scenario | " + " | ".join(common.CANDIDATE_LABELS[identifier] for identifier in common.MAIN_CANDIDATES) + " |",
             "|---|" + "---|" * len(common.MAIN_CANDIDATES)]
    groups = sorted({row["scenario"] for row in scenario_rows if row["condition"] == condition})
    for group in groups:
        cells = []
        for identifier in common.MAIN_CANDIDATES:
            match = [row for row in scenario_rows if row["condition"] == condition and row["identifier"] == identifier
                     and row["estimator"] == "final" and row["scenario"] == group]
            if not match or not match[0].get("reliable_window_count"):
                cells.append("n/a")
                continue
            row = match[0]
            cells.append(f"{format_number(row.get('reliable_mae_bpm'))}, {format_share(row.get('reliable_within_tolerance_share'))} within, "
                         f"{row['reliable_subject_count']} subj / {row['reliable_window_count']} win")
        lines.append(f"| {group} | " + " | ".join(cells) + " |")
    return lines + [""]


def run1_table_lines(comparison_rows, spearman):
    lines = ["## Comparison with run 1 (own recordings, sound-derived reference)", "",
             "Run 1: 5 recordings of one person, 255 windows (226 reliable by the sound reference). Run 2: ECG reference.", "",
             "| lower edge (150 Hz upper) | counting method | run 1 MAE reliable / all (gross, all windows) | "
             "run 2 rest: MAE reliable (interval) / all | run 2 overload: MAE reliable (interval) / all |",
             "|---|---|---|---|---|"]
    for row in comparison_rows:
        if row["estimator"] != "final" and row["identifier"] not in (common.PLANNED, common.RECOMMENDED):
            continue
        run1_text = (f"{row['run1_reliable_mae_bpm']:.2f} / {row['run1_all_mae_bpm']:.2f} ({row['run1_all_gross_error_count']})"
                     if "run1_reliable_mae_bpm" in row else "n/a")
        cells = []
        for condition in ("rest", "overload"):
            if f"{condition}_reliable_mae_bpm" in row:
                cells.append(f"{format_number(row[f'{condition}_reliable_mae_bpm'])} ({row[f'{condition}_reliable_interval']}) / "
                             f"{format_number(row[f'{condition}_all_mae_bpm'])}")
            else:
                cells.append("n/a")
        lines.append(f"| {row['lower_edge_hz']} | {row['estimator']} | {run1_text} | {cells[0]} | {cells[1]} |")
    lines.append("")
    lines += ["### Rank agreement with run 1 (Spearman, candidates present in both, ranked by MAE)", ""]
    for (condition, estimator), result in spearman.items():
        lines.append(f"- {CONDITION_LABELS[condition]}, {estimator}: {result['count']} candidates; reliable windows rho "
                     f"{result['reliable_rho']:.2f} (p {result['reliable_p']:.3f}); all windows rho {result['all_rho']:.2f} "
                     f"(p {result['all_p']:.3f}).")
        pairs = sorted(result["pairs"], key=lambda pair: pair[2])
        run1_order = sorted(result["pairs"], key=lambda pair: pair[1])
        run1_rank = {pair[0]: rank + 1 for rank, pair in enumerate(run1_order)}
        moved = [(pair[0], run1_rank[pair[0]], rank + 1) for rank, pair in enumerate(pairs)
                 if abs(run1_rank[pair[0]] - (rank + 1)) >= max(3, len(pairs) // 4)]
        if moved:
            lines.append("  Largest rank changes (run 1 rank -> run 2 rank, reliable windows): "
                         + "; ".join(f"{name} {before} -> {after}" for name, before, after in moved[:8]) + ".")
    lines.append("")
    return lines


if __name__ == "__main__":
    write_report()
