"""Report of the improved method on EPHNOGRAM: development and test subjects, all study filters, both level
conditions, by activity group and ECG rate band, with subject-bootstrap intervals.

Usage: python -I src/bpm_improved_method_report.py
Reads results-public/improved_method_choice.json (written by bpm_improved_method_select.py) and the correlation
cache of bpm_improved_method_compute.py. Writes results-public/improved_method.csv,
improved_method_paired.csv and improved_method_tables.md.
"""
import csv
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy

import bpm_improved_method_common as improved
import bpm_improved_method_own as own
import public_evaluation_common as common

HALVES = ("development", "test")
METHOD_LABELS = {"final": "run-1 final method", "half_check_only": "half-rate check only (12 Hz envelope)",
                 "improved_peak_choice": "improved peak choice, run-1 validity", "improved": "improved peak choice and validity"}
INTERVAL_STATISTICS = ("mae_bpm", "within_tolerance_share", "gross_share", "valid_share", "valid_mae_bpm", "valid_gross_share")


def measure_filter(identifier):
    """{(method, condition): dict of per-window arrays incl. subject, group, band}."""
    methods = own.chosen_configurations()
    collected = {}
    for condition in improved.CONDITIONS:
        for info in improved.records_for():
            record = improved.RecordData(info, condition)
            for method_name, configuration in methods.items():
                reference, estimate, valid = record.scored(identifier, configuration)
                measures = improved.window_measures(reference, estimate, valid)
                measures["reference"] = reference
                measures["subject"] = numpy.array([info.subject_id] * reference.shape[0])
                measures["group"] = numpy.array([record.group] * reference.shape[0])
                collected.setdefault((method_name, condition), []).append(measures)
            record.correlations.clear()
    merged = {key: {name: numpy.concatenate([part[name] for part in parts]) for name in parts[0]}
              for key, parts in collected.items()}
    for measures in merged.values():
        measures["band"] = numpy.array([common.heart_rate_band(value) for value in measures["reference"]])
    return identifier, merged


def slices(measures):
    yield "overall", "all", numpy.ones(measures["reference"].shape[0], dtype=bool)
    for group in improved.ACTIVITY_GROUPS:
        yield "activity", group, measures["group"] == group
    for _, _, band in common.HEART_RATE_BANDS:
        yield "rate band", band, measures["band"] == band


def summarise(identifier, merged, split):
    rows, paired = [], []
    for half in HALVES:
        subjects = sorted(subject for subject, assigned in split.items() if assigned == half)
        subject_position = {subject: index for index, subject in enumerate(subjects)}
        resamples = improved.bootstrap_indices(subjects)
        for condition in improved.CONDITIONS:
            sums_by_method = {}
            for method_name in METHOD_LABELS:
                measures = merged[(method_name, condition)]
                in_half = numpy.array([subject in subject_position for subject in measures["subject"]])
                for slice_type, slice_name, mask in slices(measures):
                    selection = mask & in_half
                    window_measures = {name: measures[name][selection] for name in
                                       ("absolute", "within", "gross", "half", "double", "third", "other", "valid")}
                    result = improved.pooled(window_measures)
                    if result["window_count"] == 0:
                        continue
                    subject_index = numpy.array([subject_position[subject] for subject in measures["subject"][selection]])
                    sums = improved.subject_sums(window_measures, subject_index, len(subjects))
                    sums_by_method[(method_name, slice_type, slice_name)] = sums
                    row = {"method": method_name, "filter": improved.FILTER_LABELS[identifier], "condition": condition,
                           "subjects_half": half, "slice_type": slice_type, "slice": slice_name,
                           "subject_count": int(len(numpy.unique(subject_index))), **result}
                    for statistic in INTERVAL_STATISTICS:
                        low, high = improved.bootstrap_interval(sums, resamples, improved.STATISTICS[statistic])
                        row[f"{statistic}_low"] = low
                        row[f"{statistic}_high"] = high
                    rows.append(row)
            for (method_name, slice_type, slice_name), sums in sums_by_method.items():
                if method_name == "final":
                    continue
                anchor = sums_by_method.get(("final", slice_type, slice_name))
                if anchor is None:
                    continue
                totals = sums[resamples].sum(axis=1)
                anchor_totals = anchor[resamples].sum(axis=1)
                difference = totals[:, 1] / totals[:, 0] - anchor_totals[:, 1] / anchor_totals[:, 0]
                difference = difference[numpy.isfinite(difference)]
                point = sums[:, 1].sum() / sums[:, 0].sum() - anchor[:, 1].sum() / anchor[:, 0].sum()
                paired.append({"method": method_name, "anchor": "final", "filter": improved.FILTER_LABELS[identifier],
                               "condition": condition, "subjects_half": half, "slice_type": slice_type, "slice": slice_name,
                               "mae_difference_bpm": float(point),
                               "mae_difference_low": float(numpy.percentile(difference, 2.5)),
                               "mae_difference_high": float(numpy.percentile(difference, 97.5)),
                               "subject_count": int((sums[:, 0] > 0).sum()), "window_count": int(sums[:, 0].sum())})
    return rows, paired


def run_filter(identifier):
    identifier, merged = measure_filter(identifier)
    rows, paired = summarise(identifier, merged, improved.subject_split())
    print(f"done {identifier}", flush=True)
    return rows, paired


def write_csv(path, rows):
    fields = list(dict.fromkeys(name for row in rows for name in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def interval(row, statistic, scale=1.0, digits=2):
    value = row.get(statistic, float("nan"))
    return (f"{value * scale:.{digits}f} ({row[statistic + '_low'] * scale:.{digits}f}-"
            f"{row[statistic + '_high'] * scale:.{digits}f})")


def tables(rows, paired):
    lines = ["# Improved method: generated tables", "",
             "Generated by `src/bpm_improved_method_report.py`. ECG-reliable windows only. Intervals: subject bootstrap, "
             "2,000 resamples, seed 20261123, within the subjects of each half. MAE in BPM. 'valid' = shown as valid by "
             "the method's own rule. Target = valid share >= 90 % and MAE of valid windows <= 5 BPM.", ""]
    index = {(row["method"], row["filter"], row["condition"], row["subjects_half"], row["slice_type"], row["slice"]): row
             for row in rows}
    for half in HALVES:
        for condition in improved.CONDITIONS:
            lines += [f"## {half} subjects, {condition} level: every filter, overall", "",
                      "| filter | method | MAE (interval) | median | within tolerance (interval) | gross half / third / double / other | "
                      "valid (interval) | MAE of valid (interval) | gross among valid (interval) | target | subjects / windows |",
                      "|---|---|---|---|---|---|---|---|---|---|---|"]
            for filter_label in improved.FILTER_LABELS.values():
                for method_name in METHOD_LABELS:
                    row = index.get((method_name, filter_label, condition, half, "overall", "all"))
                    if row is None:
                        continue
                    lines.append(f"| {filter_label} | {METHOD_LABELS[method_name]} | {interval(row, 'mae_bpm')} | "
                                 f"{row['median_absolute_error_bpm']:.2f} | {interval(row, 'within_tolerance_share', 100, 1)} | "
                                 f"{row['half_count']} / {row['third_count']} / {row['double_count']} / {row['other_count']} | "
                                 f"{interval(row, 'valid_share', 100, 1)} | {interval(row, 'valid_mae_bpm')} | "
                                 f"{interval(row, 'valid_gross_share', 100, 1)} | {'yes' if row['target_met'] else 'no'} | "
                                 f"{row['subject_count']} / {row['window_count']} |")
            lines.append("")
    for half in HALVES:
        for condition in improved.CONDITIONS:
            for slice_type in ("activity", "rate band"):
                lines += [f"## {half} subjects, {condition} level, 40-150 Hz: by {slice_type}", "",
                          f"| {slice_type} | method | MAE (interval) | median | within tolerance | gross half / third / double / other | "
                          "valid | MAE of valid | gross among valid | target | subjects / windows |",
                          "|---|---|---|---|---|---|---|---|---|---|---|"]
                names = improved.ACTIVITY_GROUPS if slice_type == "activity" else [band for _, _, band in common.HEART_RATE_BANDS]
                for name in names:
                    for method_name in METHOD_LABELS:
                        row = index.get((method_name, "40-150 Hz", condition, half, slice_type, name))
                        if row is None:
                            continue
                        lines.append(f"| {name} | {METHOD_LABELS[method_name]} | {interval(row, 'mae_bpm')} | "
                                     f"{row['median_absolute_error_bpm']:.2f} | {row['within_tolerance_share'] * 100:.1f} % | "
                                     f"{row['half_count']} / {row['third_count']} / {row['double_count']} / {row['other_count']} | "
                                     f"{row['valid_share'] * 100:.1f} % | {row['valid_mae_bpm']:.2f} | "
                                     f"{row['valid_gross_share'] * 100:.2f} % | {'yes' if row['target_met'] else 'no'} | "
                                     f"{row['subject_count']} / {row['window_count']} |")
                lines.append("")
    lines += ["## Paired MAE difference to the run-1 final method (same filter, same windows), overall", "",
              "| half | condition | filter | method | difference (interval) | subjects / windows |", "|---|---|---|---|---|---|"]
    for row in paired:
        if row["slice_type"] != "overall":
            continue
        lines.append(f"| {row['subjects_half']} | {row['condition']} | {row['filter']} | {METHOD_LABELS[row['method']]} | "
                     f"{row['mae_difference_bpm']:+.2f} ({row['mae_difference_low']:+.2f} to {row['mae_difference_high']:+.2f}) | "
                     f"{row['subject_count']} / {row['window_count']} |")
    return "\n".join(lines) + "\n"


def main():
    with ProcessPoolExecutor(max_workers=6) as executor:
        outcomes = list(executor.map(run_filter, list(improved.FILTER_LABELS)))
    rows = [row for outcome in outcomes for row in outcome[0]]
    paired = [row for outcome in outcomes for row in outcome[1]]
    write_csv(common.RESULTS_DIRECTORY / "improved_method.csv", rows)
    write_csv(common.RESULTS_DIRECTORY / "improved_method_paired.csv", paired)
    (common.RESULTS_DIRECTORY / "improved_method_tables.md").write_text(tables(rows, paired), encoding="utf-8")


if __name__ == "__main__":
    main()
