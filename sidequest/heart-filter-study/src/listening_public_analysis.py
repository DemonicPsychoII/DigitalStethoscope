"""Run-2 analysis from the per-recording cache: per-patient metrics, paired tests against Raw, separation (ROC area),
clipping, run-1 metrics on public data, figures and listening-public/SUMMARY.md."""
import csv
import json
import pickle
import sys
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).resolve().parent
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

import numpy  # noqa: E402
from scipy import stats  # noqa: E402

import listening_public as runner  # noqa: E402
import listening_public_compute as compute  # noqa: E402
from hfs import circor  # noqa: E402
from hfs.filters import group_delay_seconds  # noqa: E402
import listening_common as common  # noqa: E402

OUTPUT_DIRECTORY = compute.OUTPUT_DIRECTORY
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20260932
HALF_SPLIT_SEED = 7
PHASE_INDEX = {"S1": 0, "systole": 1, "S2": 2, "diastole": 3}
GRADES = ("I/VI", "II/VI", "III/VI")
PITCHES = ("Low", "Medium", "High")
PRIMARY_CONDITION = "rest_microphone_only"
GAIN_SETTING_NAMES = {0: "fixed", 1: "zero"}
METRICS = {
    "murmur_level_a_weighted_db": "Primary: A-weighted level of the murmur phase (dB re full scale)",
    "murmur_to_heart_sound_db": "Secondary 1: murmur-phase energy over S1 + S2 energy (dB)",
    "murmur_to_quiet_phase_db": "Secondary 2: murmur-phase power over quiet-phase power (dB)",
}
EXPLORATORY_METRICS = {
    "murmur_to_heart_sound_a_weighted_db": "Exploratory: secondary 1 with A-weighting (dB)",
    "murmur_to_quiet_phase_a_weighted_db": "Exploratory: secondary 2 with A-weighting (dB)",
}
RUN1_METRICS = {
    "a_weighted_vs_raw_db": ("a_weighted_level_at_safe_gain_db_mean", "A-weighted level at the safe gain vs Raw (dB)"),
    "iso226_vs_raw_db": ("iso226_60phon_level_at_safe_gain_db_mean", "ISO 226 60-phon level at the safe gain vs Raw (dB)"),
    "k_loudness_vs_raw_db": ("k_loudness_gated_at_safe_gain_lufs_mean", "K-weighted gated loudness at the safe gain vs Raw (LU)"),
    "between_to_heart_a_weighted_db": ("between_to_heart_a_weighted_db_mean", "Between beats over heart sounds, A-weighted (dB)"),
}
SHORT_LABELS = {
    "raw": "No filter (Raw)",
    "butterworth_hp2_40_lp2_800": "40–800 Hz gentle (design)",
    "butterworth_hp2_100_lp2_800": "100–800 Hz gentle",
    "butterworth_hp4_100_lp4_800": "100–800 Hz steep",
    "butterworth_hp4_150_lp4_800": "150–800 Hz steep",
    "elliptic_hp4_60_lp4_800": "60–800 Hz elliptic",
    "butterworth_hp2_80_lp0_none": "Above 80 Hz only",
    "butterworth_hp2_25_lp2_150": "25–150 Hz (BPM position)",
    "butterworth_hp2_40_lp2_150": "40–150 Hz (BPM recommendation)",
    "butterworth_hp2_40_lp2_400": "40–400 Hz gentle",
    "butterworth_hp2_40_lp2_1000": "40–1000 Hz gentle",
    "butterworth_hp2_60_lp2_800": "60–800 Hz gentle",
    "butterworth_hp2_80_lp2_800": "80–800 Hz gentle",
    "butterworth_hp2_100_lp2_600": "100–600 Hz gentle",
    "butterworth_hp2_100_lp2_1000": "100–1000 Hz gentle",
    "butterworth_hp2_100_lp2_2000": "100–2000 Hz gentle",
    "butterworth_hp2_100_lp0_none": "Above 100 Hz only",
}


# ---------------------------------------------------------------- per-patient metrics

def murmur_class(patient) -> str:
    if patient.murmur == "Absent":
        return "absent"
    if patient.murmur != "Present":
        return "unknown"
    if patient.systolic_murmur_timing is not None:
        return "systolic"
    if patient.diastolic_murmur_timing is not None:
        return "diastolic only"
    return "present, timing not given"


def decibel(value):
    return 10.0 * numpy.log10(numpy.maximum(value, 1e-30))


def cycle_metrics(energies: numpy.ndarray, window_samples: numpy.ndarray, murmur_phase: str) -> dict:
    """energies: (candidates, gain settings, weightings, cycles, phases). Returns per-cycle arrays of shape
    (candidates, gain settings, cycles)."""
    murmur = PHASE_INDEX[murmur_phase]
    quiet = PHASE_INDEX["diastole" if murmur_phase == "systole" else "systole"]
    a_weighted, unweighted = energies[:, :, 0], energies[:, :, 1]
    lengths = window_samples.astype(numpy.float64)

    def to_heart(values):
        return decibel(values[..., murmur] / (values[..., 0] + values[..., 2]))

    def to_quiet(values):
        return decibel((values[..., murmur] / lengths[:, murmur]) / (values[..., quiet] / lengths[:, quiet]))

    return {
        "murmur_level_a_weighted_db": decibel(a_weighted[..., murmur] / lengths[:, murmur]),
        "murmur_to_heart_sound_db": to_heart(unweighted),
        "murmur_to_quiet_phase_db": to_quiet(unweighted),
        "murmur_to_heart_sound_a_weighted_db": to_heart(a_weighted),
        "murmur_to_quiet_phase_a_weighted_db": to_quiet(a_weighted),
    }


def load_condition(condition: str) -> dict:
    """{file_stem: cache dict} for all cached recordings of the condition."""
    folder = compute.cache_path(condition, "x").parent
    if not folder.exists():
        return {}
    # Opening thousands of small files is slow on this machine, so loaded results are kept in one combined file.
    combined_path = folder.parent / f"{folder.name}.combined.pickle"
    results = {}
    if combined_path.exists():
        with open(combined_path, "rb") as stream:
            results = pickle.load(stream)
    added = 0
    for path in folder.glob("*.npz"):
        if path.name.endswith(".partial.npz") or path.stem in results:
            continue
        cached = compute.read_cache(condition, path.stem)
        if cached is not None:
            results[path.stem] = cached
            added += 1
    if added:
        with open(combined_path.with_suffix(".partial"), "wb") as stream:
            pickle.dump(results, stream, protocol=pickle.HIGHEST_PROTOCOL)
        combined_path.with_suffix(".partial").replace(combined_path)
    return results


def per_patient_rows(condition: str, cache: dict) -> list[dict]:
    rows = []
    for patient in circor.list_patients():
        category = murmur_class(patient)
        if category == "unknown":
            continue
        stems = [recording.file_stem for recording in runner.analysed_recordings(patient)]
        available = [stem for stem in stems if stem in cache and len(cache[stem]["window_samples"])]
        complete = all(stem in cache for stem in stems)
        if not stems or not complete or not available:
            continue
        identifiers = [str(value) for value in cache[available[0]]["candidate_identifiers"]]
        cycle_count = sum(len(cache[stem]["window_samples"]) for stem in available)
        recording_medians = {}
        for phase in ("systole", "diastole"):
            for stem in available:
                values = cycle_metrics(cache[stem]["energies"], cache[stem]["window_samples"], phase)
                for name, array in values.items():
                    recording_medians.setdefault(f"{phase}_{name}", []).append(numpy.median(array, axis=-1))
        patient_values = {name: numpy.median(numpy.stack(values), axis=0) for name, values in recording_medians.items()}
        for candidate_index, identifier in enumerate(identifiers):
            for gain_index, gain_name in GAIN_SETTING_NAMES.items():
                row = {"patient": patient.patient_identifier, "condition": condition, "candidate": identifier,
                       "gain_setting": gain_name, "murmur": patient.murmur, "murmur_class": category,
                       "systolic_grade": patient.systolic_murmur_grading or "",
                       "systolic_pitch": patient.systolic_murmur_pitch or "",
                       "systolic_quality": patient.systolic_murmur_quality or "",
                       "systolic_timing": patient.systolic_murmur_timing or "",
                       "diastolic_grade": patient.diastolic_murmur_grading or "",
                       "diastolic_timing": patient.diastolic_murmur_timing or "",
                       "age_category": patient.age_category or "", "recordings": len(available), "cycles": cycle_count}
                for name, values in patient_values.items():
                    row[name] = float(values[candidate_index, gain_index])
                rows.append(row)
    return rows


def value_column(metric: str, phase: str) -> str:
    return f"{phase}_{metric}"


# ---------------------------------------------------------------- statistics

def walsh_median(differences: numpy.ndarray) -> float:
    upper, lower = numpy.triu_indices(len(differences))
    return float(numpy.median((differences[upper] + differences[lower]) / 2.0))


def hodges_lehmann_with_interval(differences: numpy.ndarray, generator) -> tuple[float, float, float]:
    estimate = walsh_median(differences)
    count = len(differences)
    draws = generator.integers(0, count, (BOOTSTRAP_RESAMPLES, count))
    upper, lower = numpy.triu_indices(count)
    chunk = max(1, 4_000_000 // len(upper))
    resampled = numpy.empty(BOOTSTRAP_RESAMPLES)
    for first in range(0, BOOTSTRAP_RESAMPLES, chunk):
        values = differences[draws[first:first + chunk]]
        resampled[first:first + chunk] = numpy.median((values[:, upper] + values[:, lower]) / 2.0, axis=1)
    low, high = numpy.percentile(resampled, [2.5, 97.5])
    return estimate, float(low), float(high)


def wilcoxon_p(differences: numpy.ndarray) -> float:
    if numpy.allclose(differences, 0.0):
        return 1.0
    return float(stats.wilcoxon(differences, zero_method="wilcox", alternative="two-sided").pvalue)


def holm(p_values: list[float]) -> list[float]:
    order = numpy.argsort(p_values)
    count = len(p_values)
    adjusted = numpy.empty(count)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (count - rank) * p_values[index]))
        adjusted[index] = running
    return adjusted.tolist()


def area_under_curve(present: numpy.ndarray, absent: numpy.ndarray) -> float:
    """Probability that a murmur-present patient has a higher value than a murmur-absent one (ties count half)."""
    ranks = stats.rankdata(numpy.concatenate([present, absent]))
    present_rank_sum = ranks[:len(present)].sum()
    return float((present_rank_sum - len(present) * (len(present) + 1) / 2.0) / (len(present) * len(absent)))


def table_by(rows, condition, gain_setting):
    selected = {}
    for row in rows:
        if row["condition"] == condition and row["gain_setting"] == gain_setting:
            selected.setdefault(row["candidate"], {})[row["patient"]] = row
    return selected


def paired_tests(rows, condition, gain_setting, patients_filter=None, family_label="", seed_offset=0,
                 metrics=tuple(METRICS) + tuple(EXPLORATORY_METRICS)) -> list[dict]:
    by_candidate = table_by(rows, condition, gain_setting)
    if "raw" not in by_candidate:
        return []
    results = []
    groups = (("systolic", "systole", lambda row: row["murmur_class"] == "systolic"),
              ("diastolic", "diastole", lambda row: row["murmur"] == "Present" and row["diastolic_timing"] != ""))
    for group, phase, member in groups:
        patients = sorted(patient for patient, row in by_candidate["raw"].items() if member(row)
                          and (patients_filter is None or patient in patients_filter))
        if not patients:
            continue
        for candidate, table in by_candidate.items():
            if candidate == "raw":
                continue
            for metric_index, metric in enumerate(metrics):
                column = value_column(metric, phase)
                raw_values = numpy.array([by_candidate["raw"][patient][column] for patient in patients])
                values = numpy.array([table[patient][column] for patient in patients])
                differences = values - raw_values
                record = {"condition": condition, "gain_setting": gain_setting, "family_label": family_label,
                          "murmur_group": group, "phase": phase, "candidate": candidate, "metric": metric,
                          "confirmatory": metric in METRICS and group == "systolic",
                          "patients": len(patients), "raw_median_db": float(numpy.median(raw_values)),
                          "candidate_median_db": float(numpy.median(values)),
                          "median_difference_db": float(numpy.median(differences)),
                          "share_of_patients_higher_than_raw": float(numpy.mean(differences > 0))}
                if group == "systolic" and len(patients) >= 6:
                    generator = numpy.random.default_rng(BOOTSTRAP_SEED + seed_offset + metric_index)
                    estimate, low, high = hodges_lehmann_with_interval(differences, generator)
                    record.update({"hodges_lehmann_db": estimate, "interval_low_db": low, "interval_high_db": high,
                                   "wilcoxon_p": wilcoxon_p(differences)})
                results.append(record)
    return results


def add_holm(results: list[dict]) -> int:
    family = [record for record in results if record["confirmatory"] and "wilcoxon_p" in record]
    adjusted = holm([record["wilcoxon_p"] for record in family])
    for record, value in zip(family, adjusted):
        record["holm_p"] = value
        record["family_size"] = len(family)
    return len(family)


def separation(rows, condition, gain_setting, metric="murmur_to_heart_sound_db", subgroup=None,
               patients_filter=None, resamples=BOOTSTRAP_RESAMPLES) -> list[dict]:
    by_candidate = table_by(rows, condition, gain_setting)
    if "raw" not in by_candidate:
        return []
    column = value_column(metric, "systole")
    raw_rows = by_candidate["raw"]

    def keep(patient):
        return patients_filter is None or patient in patients_filter

    present = sorted(patient for patient, row in raw_rows.items() if row["murmur_class"] == "systolic" and keep(patient)
                     and (subgroup is None or row[subgroup[0]] == subgroup[1]))
    absent = sorted(patient for patient, row in raw_rows.items() if row["murmur_class"] == "absent" and keep(patient))
    if len(present) < 3 or len(absent) < 3:
        return []
    generator = numpy.random.default_rng(BOOTSTRAP_SEED)
    present_draws = generator.integers(0, len(present), (resamples, len(present)))
    absent_draws = generator.integers(0, len(absent), (resamples, len(absent)))

    def values_of(candidate):
        table = by_candidate[candidate]
        return (numpy.array([table[patient][column] for patient in present]),
                numpy.array([table[patient][column] for patient in absent]))

    def bootstrap(present_values, absent_values):
        combined = numpy.concatenate([present_values[present_draws], absent_values[absent_draws]], axis=1)
        ranks = stats.rankdata(combined, axis=1)
        present_count, absent_count = present_draws.shape[1], absent_draws.shape[1]
        rank_sums = ranks[:, :present_count].sum(axis=1)
        return (rank_sums - present_count * (present_count + 1) / 2.0) / (present_count * absent_count)

    raw_present, raw_absent = values_of("raw")
    raw_area = area_under_curve(raw_present, raw_absent)
    raw_bootstrap = bootstrap(raw_present, raw_absent)
    results = []
    for candidate in by_candidate:
        present_values, absent_values = values_of(candidate)
        area = area_under_curve(present_values, absent_values)
        boot = raw_bootstrap if candidate == "raw" else bootstrap(present_values, absent_values)
        difference = boot - raw_bootstrap
        results.append({
            "condition": condition, "gain_setting": gain_setting, "metric": metric,
            "subgroup": "all systolic murmurs" if subgroup is None else f"{subgroup[0]}={subgroup[1]}",
            "candidate": candidate, "present_patients": len(present), "absent_patients": len(absent),
            "area_under_curve": area, "interval_low": float(numpy.percentile(boot, 2.5)),
            "interval_high": float(numpy.percentile(boot, 97.5)), "difference_to_raw": area - raw_area,
            "difference_interval_low": float(numpy.percentile(difference, 2.5)),
            "difference_interval_high": float(numpy.percentile(difference, 97.5)),
        })
    return results


# ---------------------------------------------------------------- clipping and run-1 metrics

def clipping_rows(condition: str, cache: dict, gains: dict) -> list[dict]:
    if not cache:
        return []
    stems = sorted(cache)
    identifiers = [str(value) for value in cache[stems[0]]["candidate_identifiers"]]
    patients_of = {stem: stem.split("_")[0] for stem in stems}
    run1 = run1_summary()
    rows = []
    for candidate_index, identifier in enumerate(identifiers):
        clipped = numpy.array([cache[stem]["clipped_fixed"][candidate_index] > 0 for stem in stems])
        clipped_zero = numpy.array([cache[stem]["clipped_zero"][candidate_index] > 0 for stem in stems])
        headroom = numpy.array([cache[stem]["headroom_db"][candidate_index] for stem in stems])
        clipped_patients = {patients_of[stem] for stem, flag in zip(stems, clipped) if flag}
        rows.append({
            "condition": condition, "candidate": identifier, "recordings": len(stems),
            "patients": len(set(patients_of.values())), "run1_safe_gain_db": gains[identifier],
            "run1_safe_gain_without_artefact_db": run1.get(identifier, {}).get("safe_gain_without_artefact_db", ""),
            "recordings_with_output_at_limit_at_run1_gain_percent": 100.0 * clipped.mean(),
            "patients_with_output_at_limit_at_run1_gain_percent": 100.0 * len(clipped_patients) / len(set(patients_of.values())),
            "recordings_with_output_at_limit_at_0db_percent": 100.0 * clipped_zero.mean(),
            "output_samples_at_limit_at_run1_gain_total": int(sum(cache[stem]["clipped_fixed"][candidate_index] for stem in stems)),
            "safe_gain_for_99_percent_of_recordings_db": float(numpy.percentile(headroom, 1.0)),
            "safe_gain_for_100_percent_of_recordings_db": float(headroom.min()),
            "recordings_with_input_at_limit": int(sum(int(cache[stem]["input_clipped"]) > 0 for stem in stems)),
        })
    return rows


def run1_summary() -> dict:
    with open(common.LISTENING_DIRECTORY / "metrics_summary.csv", newline="", encoding="utf-8") as stream:
        return {row["identifier"]: row for row in csv.DictReader(stream)}


def run1_metrics_on_public(condition: str, cache: dict, gains: dict) -> list[dict]:
    patients = {patient.patient_identifier: patient for patient in circor.list_patients()}
    stems = [stem for stem in sorted(cache) if patients[stem.split("_")[0]].murmur in ("Present", "Absent")]
    absent_stems = [stem for stem in stems if patients[stem.split("_")[0]].murmur == "Absent"
                    and len(cache[stem]["window_samples"])]
    if not stems:
        return []
    identifiers = [str(value) for value in cache[stems[0]]["candidate_identifiers"]]
    raw_index = identifiers.index("raw")
    run1 = run1_summary()
    rows = []
    for candidate_index, identifier in enumerate(identifiers):
        gain_difference = gains[identifier] - gains["raw"]
        a_weighted = [cache[stem]["a_weighted_level_db"][candidate_index] - cache[stem]["a_weighted_level_db"][raw_index]
                      + gain_difference for stem in stems]
        iso226 = [cache[stem]["iso226_level_db"][candidate_index] - cache[stem]["iso226_level_db"][raw_index]
                  + gain_difference for stem in stems]
        k_loudness = [cache[stem]["k_gated_at_fixed_gain_lufs"][candidate_index]
                      - cache[stem]["k_gated_at_fixed_gain_lufs"][raw_index] for stem in stems]
        between = []
        for stem in absent_stems:
            energies = cache[stem]["energies"][candidate_index, 1, 0]
            lengths = cache[stem]["window_samples"].astype(numpy.float64)
            diastole_power = energies[:, 3].sum() / lengths[:, 3].sum()
            heart_power = (energies[:, 0].sum() + energies[:, 2].sum()) / (lengths[:, 0].sum() + lengths[:, 2].sum())
            between.append(float(decibel(diastole_power / heart_power)))
        record = {"condition": condition, "candidate": identifier, "recordings": len(stems),
                  "recordings_between_to_heart": len(absent_stems),
                  "a_weighted_vs_raw_db": float(numpy.mean(a_weighted)),
                  "iso226_vs_raw_db": float(numpy.mean(iso226)),
                  "k_loudness_vs_raw_db": float(numpy.nanmean(k_loudness)),
                  "between_to_heart_a_weighted_db": float(numpy.mean(between)) if between else float("nan")}
        reference = run1.get(identifier)
        raw_reference = run1["raw"]
        if reference is not None:
            for name, (column, _) in RUN1_METRICS.items():
                value = float(reference[column])
                if name != "between_to_heart_a_weighted_db":
                    value -= float(raw_reference[column])
                record[f"run1_{name}"] = value
        rows.append(record)
    return rows


def rank_correlations(rows: list[dict]) -> dict:
    shortlist = [row for row in rows if row["candidate"] in compute.SHORTLIST_IDENTIFIERS and "run1_a_weighted_vs_raw_db" in row]
    correlations = {}
    for name in RUN1_METRICS:
        run1_values = [row[f"run1_{name}"] for row in shortlist]
        public_values = [row[name] for row in shortlist]
        if len(shortlist) >= 3:
            correlations[name] = float(stats.spearmanr(run1_values, public_values).statistic)
    return correlations


# ---------------------------------------------------------------- output

def format_cell(value):
    if isinstance(value, float):
        return "" if numpy.isnan(value) else f"{value:.6g}"
    return value


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_cell(value) for key, value in row.items()})


def group_delays() -> dict:
    delays = {}
    for identifier, entry, _, _ in compute.CANDIDATES:
        candidate = common.candidate_from_entry(entry)
        if candidate.family == "raw":
            delays[identifier] = (0.0, 0.0)
        else:
            values = group_delay_seconds(candidate, [100.0, 200.0])
            delays[identifier] = (1e3 * float(values[0]), 1e3 * float(values[1]))
    return delays


def main() -> None:
    global OUTPUT_DIRECTORY
    import listening_public_report as report
    if not compute.chain_model_available():
        OUTPUT_DIRECTORY = compute.OUTPUT_DIRECTORY / "development_stand_in"
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    gains = compute.load_fixed_gains()
    all_rows, tests, areas, clipping, run1_rows = [], [], [], [], []
    caches = {}
    for condition in compute.CONDITIONS:
        cache = load_condition(condition)
        if not cache:
            continue
        caches[condition] = cache
        rows = per_patient_rows(condition, cache)
        all_rows += rows
        clipping += clipping_rows(condition, cache, gains)
        run1_rows += run1_metrics_on_public(condition, cache, gains)
        print(f"{condition}: {len(cache)} recordings cached, {len({row['patient'] for row in rows})} complete patients",
              flush=True)
    write_csv(OUTPUT_DIRECTORY / "murmur_metrics_per_patient.csv", all_rows)

    family_sizes = {}
    for condition in caches:
        for gain_setting in ("fixed", "zero"):
            if condition != PRIMARY_CONDITION and gain_setting == "zero":
                continue
            metrics = tuple(METRICS) + (tuple(EXPLORATORY_METRICS) if condition == PRIMARY_CONDITION and gain_setting == "fixed" else ())
            results = paired_tests(all_rows, condition, gain_setting, family_label=f"{condition}, {gain_setting} gain",
                                   metrics=metrics)
            family_sizes[(condition, gain_setting)] = add_holm(results)
            tests += results
    split_patients = sorted({row["patient"] for row in all_rows if row["condition"] == PRIMARY_CONDITION})
    order = numpy.random.default_rng(HALF_SPLIT_SEED).permutation(len(split_patients))
    halves = {"half A": {split_patients[index] for index in order[:len(order) // 2]},
              "half B": {split_patients[index] for index in order[len(order) // 2:]}}
    for half_index, (half, members) in enumerate(halves.items()):
        results = paired_tests(all_rows, PRIMARY_CONDITION, "fixed", members,
                               family_label=f"{PRIMARY_CONDITION}, fixed gain, {half}",
                               seed_offset=100 * (half_index + 1), metrics=tuple(METRICS))
        add_holm(results)
        tests += results
    write_csv(OUTPUT_DIRECTORY / "murmur_tests.csv", tests)

    for condition in caches:
        for gain_setting in ("fixed", "zero"):
            if gain_setting == "zero" and condition != PRIMARY_CONDITION:
                continue
            for metric in ("murmur_to_heart_sound_db", "murmur_to_quiet_phase_db"):
                areas += separation(all_rows, condition, gain_setting, metric)
    for subgroup in [("systolic_grade", grade) for grade in GRADES] + [("systolic_pitch", pitch) for pitch in PITCHES]:
        for metric in ("murmur_to_heart_sound_db", "murmur_to_quiet_phase_db"):
            areas += separation(all_rows, PRIMARY_CONDITION, "fixed", metric, subgroup, resamples=1000)
    for half, members in halves.items():
        for record in separation(all_rows, PRIMARY_CONDITION, "fixed", "murmur_to_heart_sound_db", None, members,
                                 resamples=1000):
            record["subgroup"] = f"all systolic murmurs, {half}"
            areas.append(record)
    write_csv(OUTPUT_DIRECTORY / "murmur_auc.csv", areas)
    write_csv(OUTPUT_DIRECTORY / "clipping_public.csv", clipping)
    correlations = {}
    for condition in caches:
        condition_rows = [row for row in run1_rows if row["condition"] == condition]
        correlations[condition] = rank_correlations(condition_rows)
    write_csv(OUTPUT_DIRECTORY / "run1_metrics_on_public.csv", run1_rows)
    (OUTPUT_DIRECTORY / "rank_correlations.json").write_text(json.dumps(correlations, indent=2), encoding="utf-8")
    report.write_everything(all_rows, tests, areas, clipping, run1_rows, correlations, family_sizes, caches, gains,
                            group_delays(), halves)


if __name__ == "__main__":
    main()
