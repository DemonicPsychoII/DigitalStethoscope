"""Choose the improved peak choice and validity rule on the DEVELOPMENT subjects only (40-150 Hz, rest and overload).

Usage: python -I src/bpm_improved_method_select.py
Writes results-public/improved_method_selection.csv and results-public/improved_method_choice.json.
"""
import csv
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy

import bpm_improved_method_common as improved
import public_evaluation_common as common

SELECTION_FILTER = common.RECOMMENDED
ENVELOPES = {"two_pole_5hz": common.FINAL_METHOD, "one_pole_12hz": common.HALF_CHECK_ONLY}


def peak_choice_variants():
    variants = {}
    for envelope_label, base in ENVELOPES.items():
        for weighting in ("none", "overlap"):
            stem = replace(base, lag_weighting=weighting)
            variants[(envelope_label, weighting, "highest")] = replace(stem, peak_choice="highest")
            variants[(envelope_label, weighting, "half_check 0.8")] = replace(stem, peak_choice="half_check")
            for fraction in (0.6, 0.65, 0.7, 0.8, 0.85, 0.9, 0.95):
                variants[(envelope_label, weighting, f"first_above {fraction}")] = replace(stem, peak_choice="first_above",
                                                                                         first_above_fraction=fraction)
            for divisor in (3, 4):
                for fraction in (0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9):
                    variants[(envelope_label, weighting, f"submultiple {fraction} up to {divisor}")] = replace(
                        stem, peak_choice="submultiple", submultiple_fraction=fraction, submultiple_largest_divisor=divisor)
            variants[(envelope_label, weighting, "harmonic_sum")] = replace(stem, peak_choice="harmonic_sum")
    return variants


def evaluate(records, configuration):
    measures = []
    for record in records:
        reference, estimate, valid = record.scored(SELECTION_FILTER, configuration)
        measures.append(improved.window_measures(reference, estimate, valid))
    merged = {name: numpy.concatenate([measure[name] for measure in measures]) for name in measures[0]}
    groups = numpy.concatenate([[record.group] * measure["absolute"].shape[0] for record, measure in zip(records, measures)])
    result = improved.pooled(merged)
    for group in improved.ACTIVITY_GROUPS:
        group_result = improved.pooled(merged, groups == group)
        result[f"{group}:mae_bpm"] = group_result.get("mae_bpm", float("nan"))
        result[f"{group}:valid_share"] = group_result.get("valid_share", float("nan"))
        result[f"{group}:valid_mae_bpm"] = group_result.get("valid_mae_bpm", float("nan"))
    return result


def main():
    split = improved.subject_split()
    development = {subject for subject, half in split.items() if half == "development"}
    records = [improved.RecordData(info, condition) for condition in improved.CONDITIONS
               for info in improved.records_for(development)]
    rows = []
    variants = peak_choice_variants()
    for (envelope_label, weighting, choice), configuration in variants.items():
        result = evaluate(records, configuration)
        rows.append({"stage": "peak choice", "envelope": envelope_label, "lag_weighting": weighting, "peak_choice": choice,
                     "configuration": configuration.key(), **result})
        print(f"{envelope_label:14s} {weighting:8s} {choice:28s} MAE {result['mae_bpm']:6.2f} median "
              f"{result['median_absolute_error_bpm']:5.2f} within {result['within_tolerance_share']:.3f} third "
              f"{result['third_count']:6d} half {result['half_count']:6d} other {result['other_count']:6d}", flush=True)
    best_peak_row = min((row for row in rows), key=lambda row: row["mae_bpm"])
    best_configuration = next(configuration for key, configuration in variants.items()
                              if configuration.key() == best_peak_row["configuration"])
    print("best peak choice:", best_peak_row["configuration"], flush=True)
    validity_rows = []
    for quality in (0.3, 0.4, 0.5, 0.6):
        for margin in (-2.0, 0.0, 0.05, 0.1, 0.15):
            for agreement in (0.0, 0.1, 0.15):
                configuration = replace(best_configuration, quality_threshold=quality, minimum_rival_margin=margin,
                                        agreement_fraction=agreement)
                result = evaluate(records, configuration)
                row = {"stage": "validity", "envelope": best_peak_row["envelope"], "lag_weighting": best_peak_row["lag_weighting"],
                       "peak_choice": best_peak_row["peak_choice"], "quality_threshold": quality,
                       "minimum_rival_margin": margin, "agreement_fraction": agreement,
                       "configuration": configuration.key(), **result}
                validity_rows.append(row)
                print(f"quality {quality} margin {margin} agreement {agreement}: valid {result['valid_share']:.3f} "
                      f"valid MAE {result['valid_mae_bpm']:.2f} valid gross {result['valid_gross_share']:.4f}", flush=True)
    # The lowest share of gross errors shown as valid among rules that lose at most 5 points of valid share against
    # the quality threshold alone; ties broken by the larger valid share.
    quality_only = next(row for row in validity_rows if row["quality_threshold"] == best_configuration.quality_threshold
                        and row["minimum_rival_margin"] == -2.0 and row["agreement_fraction"] == 0.0)
    eligible = [row for row in validity_rows if row["valid_share"] >= quality_only["valid_share"] - 0.05]
    best_validity_row = min(eligible, key=lambda row: (round(row["valid_gross_share"], 4), -row["valid_share"]))
    chosen = replace(best_configuration, quality_threshold=best_validity_row["quality_threshold"],
                     minimum_rival_margin=best_validity_row["minimum_rival_margin"],
                     agreement_fraction=best_validity_row["agreement_fraction"])
    all_rows = rows + validity_rows
    fields = list(dict.fromkeys(name for row in all_rows for name in row))
    with (common.RESULTS_DIRECTORY / "improved_method_selection.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)
    (common.RESULTS_DIRECTORY / "improved_method_choice.json").write_text(json.dumps(
        {"development_subjects": sorted(development), "split": split, "peak_choice_configuration": asdict(best_configuration),
         "chosen_configuration": asdict(chosen), "peak_choice_development": best_peak_row,
         "validity_development": best_validity_row}, indent=1), encoding="utf-8")
    print("chosen:", chosen.key())


if __name__ == "__main__":
    main()
