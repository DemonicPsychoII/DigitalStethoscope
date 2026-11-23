"""Summarise the CirCor DigiScope dataset into public-data-summary/circor.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
from collections import Counter, defaultdict

import numpy
import soundfile

from hfs import circor

SUMMARY_PATH = circor.STUDY_DIRECTORY / "public-data-summary" / "circor.md"
MINIMUM_CYCLES_FOR_HEART_RATE = 3
MINIMUM_CYCLES_FOR_MURMUR_TEST = 5
LOCATION_ORDER = ["AV", "PV", "TV", "MV", "Phc"]


def label(value) -> str:
    return "not stated" if value is None else str(value)


def count_table(title: str, counter: Counter, key_order=None) -> list[str]:
    keys = key_order if key_order is not None else sorted(counter, key=lambda key: (-counter[key], str(key)))
    lines = [f"| {title} | Count |", "|---|---:|"]
    lines += [f"| {label(key)} | {counter[key]} |" for key in keys if key in counter]
    lines += [f"| {label(key)} | {counter[key]} |" for key in counter if key_order is not None and key not in key_order]
    return lines + [""]


def cross_table(title: str, rows: dict, column_names: list[str]) -> list[str]:
    lines = [f"| {title} | " + " | ".join(column_names) + " | Total |", "|---|" + "---:|" * (len(column_names) + 1)]
    for row_key, counter in rows.items():
        cells = [str(counter.get(column, 0)) for column in column_names]
        lines.append(f"| {label(row_key)} | " + " | ".join(cells) + f" | {sum(counter.values())} |")
    return lines + [""]


def distribution_line(values) -> str:
    values = numpy.asarray(values, dtype=float)
    if values.size == 0:
        return "no values"
    percentiles = numpy.percentile(values, [0, 5, 25, 50, 75, 95, 100])
    return ("minimum {:.2f}, 5th {:.2f}, 25th {:.2f}, median {:.2f}, 75th {:.2f}, 95th {:.2f}, maximum {:.2f}"
            .format(*percentiles))


def main() -> int:
    failures = []
    manifest_path = circor.DATA_DIRECTORY / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None

    patients = circor.list_patients()
    patient_by_identifier = {patient.patient_identifier: patient for patient in patients}

    recordings = []
    cycles_by_stem = {}
    audio_formats = Counter()
    wav_sample_rates = Counter()
    for patient in patients:
        try:
            file_stems = circor.file_stems_of_patient(patient.patient_identifier)
        except (OSError, ValueError, IndexError) as error:
            failures.append(f"{patient.patient_identifier}.txt: {error}")
            continue
        listed_locations = sorted({circor.location_from_file_stem(patient.patient_identifier, stem) for stem in file_stems})
        if listed_locations != sorted(set(patient.recording_locations)):
            failures.append(f"{patient.patient_identifier}: locations in .txt {listed_locations} differ from "
                            f"training_data.csv {sorted(set(patient.recording_locations))}")
        for file_stem in file_stems:
            try:
                info = circor.read_recording_info(patient, file_stem)
                audio_info = soundfile.info(str(circor.RECORDING_DIRECTORY / f"{file_stem}.wav"))
                if audio_info.frames != info.sample_count:
                    failures.append(f"{file_stem}: WAV has {audio_info.frames} frames, header states {info.sample_count}")
                audio_formats[(audio_info.channels, audio_info.subtype)] += 1
                wav_sample_rates[audio_info.samplerate] += 1
                cycles_by_stem[file_stem] = circor.heart_cycle_intervals(circor.read_segments(file_stem))
                recordings.append(info)
            except (OSError, ValueError, RuntimeError, soundfile.LibsndfileError) as error:
                failures.append(f"{file_stem}: {type(error).__name__}: {error}")

    records_listed = (circor.DATA_DIRECTORY / "RECORDS").read_text(encoding="utf-8").split()
    stems_listed_in_records = {Path(entry).name for entry in records_listed}
    stems_found = {recording.file_stem for recording in recordings}
    stems_with_failure = {failure.split(":", 1)[0] for failure in failures}
    for missing in sorted(stems_listed_in_records - stems_found - stems_with_failure):
        failures.append(f"{missing}: listed in RECORDS but not referenced by any patient .txt file")
    for extra in sorted(stems_found - stems_listed_in_records):
        failures.append(f"{extra}: parsed but not listed in RECORDS")

    patients_by_murmur = Counter(patient.murmur for patient in patients)
    patients_by_age = Counter(patient.age_category for patient in patients)
    patients_by_age_and_murmur = defaultdict(Counter)
    for patient in patients:
        patients_by_age_and_murmur[patient.age_category][patient.murmur] += 1
    recordings_by_location_and_murmur = defaultdict(Counter)
    recordings_by_age_and_murmur = defaultdict(Counter)
    for recording in recordings:
        patient = patient_by_identifier[recording.patient_identifier]
        recordings_by_location_and_murmur[recording.location][patient.murmur] += 1
        recordings_by_age_and_murmur[patient.age_category][patient.murmur] += 1
    murmur_columns = ["Present", "Absent", "Unknown"]
    age_order = ["Neonate", "Infant", "Child", "Adolescent", "Young adult", None]

    def ordered(rows: dict, order: list) -> dict:
        return {key: rows[key] for key in order + sorted((key for key in rows if key not in order), key=str) if key in rows}

    header_sample_rates = Counter(recording.sample_rate_hz for recording in recordings)
    durations = [recording.duration_seconds for recording in recordings]
    segmented = [recording for recording in recordings if recording.has_segmentation]
    annotated_durations = [recording.annotated_duration_seconds for recording in segmented]
    cycle_counts = [len(cycles_by_stem[recording.file_stem]) for recording in recordings]

    systolic_patients = [patient for patient in patients if patient.systolic_murmur_timing is not None]
    diastolic_patients = [patient for patient in patients if patient.diastolic_murmur_timing is not None]

    heart_rates_by_age = defaultdict(list)
    for recording in recordings:
        cycles = cycles_by_stem[recording.file_stem]
        if len(cycles) >= MINIMUM_CYCLES_FOR_HEART_RATE:
            median_cycle_seconds = float(numpy.median([cycle.duration_seconds for cycle in cycles]))
            heart_rates_by_age[patient_by_identifier[recording.patient_identifier].age_category].append(60.0 / median_cycle_seconds)

    murmur_present_usable = set()
    murmur_present_usable_recordings = 0
    murmur_absent_usable = set()
    murmur_absent_usable_recordings = 0
    for recording in recordings:
        if len(cycles_by_stem[recording.file_stem]) < MINIMUM_CYCLES_FOR_MURMUR_TEST:
            continue
        murmur = patient_by_identifier[recording.patient_identifier].murmur
        if murmur == "Present" and recording.murmur_heard_at_location:
            murmur_present_usable.add(recording.patient_identifier)
            murmur_present_usable_recordings += 1
        elif murmur == "Absent":
            murmur_absent_usable.add(recording.patient_identifier)
            murmur_absent_usable_recordings += 1

    lines = ["# CirCor DigiScope Phonocardiogram Dataset 1.0.3: summary", ""]
    lines += ["Generated by `src/circor_summary.py` from the files in `public-data/circor-1.0.3/`.", ""]
    lines += ["## Source", ""]
    if manifest is not None:
        lines += [f"- Source: {manifest['source_url']} (landing page {manifest['landing_page_url']})",
                  f"- Version {manifest['version']}, DOI {manifest['doi']}, licence: {manifest['licence']}",
                  f"- Accessed {manifest['access_date']}; {manifest['verified_count']} of {manifest['file_count']} files "
                  f"verified against SHA256SUMS.txt ({manifest['total_bytes'] / 1e6:.1f} MB); "
                  f"{len(manifest['failures'])} download failures",
                  f"- READY marker present: {circor.data_is_ready()}", ""]
    else:
        lines += ["- MANIFEST.json missing: download not verified.", ""]
    lines += ["The published files contain only the training part with the counts below. The figures of "
              "1,568 patients and 5,272 recordings quoted for the dataset are not reproducible from these files "
              "(unverified here whether they include unpublished validation and test parts).", ""]

    lines += ["## Patients and recordings", "",
              f"- Patients in training_data.csv: {len(patients)}",
              f"- Recordings parsed: {len(recordings)} (RECORDS lists {len(records_listed)})",
              f"- Recordings with a segmentation file: {len(segmented)}", ""]
    lines += count_table("Patients by murmur", patients_by_murmur, murmur_columns)
    lines += count_table("Patients by age category", patients_by_age, age_order)
    lines += cross_table("Patients: age category / murmur", ordered(patients_by_age_and_murmur, age_order), murmur_columns)
    lines += cross_table("Recordings: age category / murmur", ordered(recordings_by_age_and_murmur, age_order), murmur_columns)
    lines += cross_table("Recordings: location / murmur", ordered(recordings_by_location_and_murmur, LOCATION_ORDER), murmur_columns)
    patients_without_age = [patient for patient in patients if patient.age_category is None]
    lines += [f"Age category `not stated` means `nan` in training_data.csv. Of these {len(patients_without_age)} patients, "
              f"{sum(1 for patient in patients_without_age if patient.pregnancy_status)} have pregnancy status True "
              f"(all patients with pregnancy status True: {sum(1 for patient in patients if patient.pregnancy_status)}).", ""]

    lines += ["## Audio format", ""]
    lines += count_table("Sample rate from header (Hz)", header_sample_rates)
    lines += count_table("Sample rate from WAV (Hz)", wav_sample_rates)
    lines += count_table("WAV channels, subtype", Counter({f"{channels} channel(s), {subtype}": count
                                                           for (channels, subtype), count in audio_formats.items()}))
    lines += ["## Durations", "",
              f"- Recording duration (s): {distribution_line(durations)}",
              f"- Total recording time: {sum(durations) / 3600:.2f} h",
              f"- Annotated duration per segmented recording (s, states 1-4): {distribution_line(annotated_durations)}",
              f"- Total annotated time: {sum(annotated_durations) / 3600:.2f} h",
              f"- Complete annotated cycles (S1-systole-S2-diastole without gap): {sum(cycle_counts)} in total; "
              f"per recording {distribution_line(cycle_counts)}",
              f"- Recordings with no complete cycle: {sum(1 for count in cycle_counts if count == 0)}", ""]

    lines += ["## Murmur characteristics (patients)", "",
              f"Systolic murmur patients: {len(systolic_patients)}. Diastolic murmur patients: {len(diastolic_patients)}.", ""]
    lines += count_table("Systolic murmur timing", Counter(patient.systolic_murmur_timing for patient in systolic_patients))
    lines += count_table("Systolic murmur grading", Counter(patient.systolic_murmur_grading for patient in systolic_patients),
                         ["I/VI", "II/VI", "III/VI"])
    lines += count_table("Systolic murmur pitch", Counter(patient.systolic_murmur_pitch for patient in systolic_patients),
                         ["Low", "Medium", "High"])
    lines += count_table("Diastolic murmur timing", Counter(patient.diastolic_murmur_timing for patient in diastolic_patients))
    lines += count_table("Diastolic murmur grading", Counter(patient.diastolic_murmur_grading for patient in diastolic_patients))
    lines += count_table("Diastolic murmur pitch", Counter(patient.diastolic_murmur_pitch for patient in diastolic_patients))

    lines += ["## Heart rate from the segmentation", "",
              f"Per recording: 60 / median duration of its complete cycles, recordings with at least "
              f"{MINIMUM_CYCLES_FOR_HEART_RATE} complete cycles. Statistics across recordings.", "",
              "| Age category | Recordings | Median (bpm) | 5th percentile | 95th percentile |", "|---|---:|---:|---:|---:|"]
    for age in [key for key in age_order if key in heart_rates_by_age] + [key for key in heart_rates_by_age if key not in age_order]:
        rates = numpy.asarray(heart_rates_by_age[age])
        lines.append(f"| {label(age)} | {rates.size} | {numpy.median(rates):.1f} | "
                     f"{numpy.percentile(rates, 5):.1f} | {numpy.percentile(rates, 95):.1f} |")
    lines += [""]

    lines += ["## Material for the murmur audibility test", "",
              f"- Murmur-present patients with at least one recording of at least {MINIMUM_CYCLES_FOR_MURMUR_TEST} complete "
              f"cycles at a location where the murmur is heard: {len(murmur_present_usable)} patients, "
              f"{murmur_present_usable_recordings} recordings",
              f"- Murmur-absent patients with at least one recording of at least {MINIMUM_CYCLES_FOR_MURMUR_TEST} complete "
              f"cycles: {len(murmur_absent_usable)} patients, {murmur_absent_usable_recordings} recordings", ""]

    lines += ["## Parse failures and consistency deviations", ""]
    lines += [f"- {failure}" for failure in failures] or ["None."]
    lines += [""]

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {SUMMARY_PATH} ({len(recordings)} recordings, {len(failures)} failures)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
