"""Murmur excerpts for listening: 8 s of chain-modelled capture (resting level, microphone model only) from CirCor,
written as 24-bit mono 16 kHz WAV to recordings-public/<label>/capture.wav with recordings-public/README.md.

Selection, fixed before listening: a stretch of consecutive complete annotated heart cycles of at least 8 s at the
patient's most audible location (for murmur-absent patients: any location), no modelled sample at the 24-bit limit
inside the excerpt; among the eligible recordings the one with the largest systole-to-diastole power ratio in the
50-800 Hz band of the dataset signal (loud and soft murmur), or the median ratio (no murmur)."""
import json
import sys
from pathlib import Path

SOURCE_DIRECTORY = Path(__file__).resolve().parent
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))

import numpy  # noqa: E402
import soundfile  # noqa: E402
from scipy import signal  # noqa: E402

import listening_public_compute as compute  # noqa: E402
from hfs import circor  # noqa: E402
from hfs.recordings import SAMPLE_MAXIMUM, SAMPLE_MINIMUM, SAMPLE_RATE_HZ  # noqa: E402

EXCERPT_SECONDS = 8.0
OUTPUT_DIRECTORY = compute.STUDY_DIRECTORY / "recordings-public"
CONDITION = "rest_microphone_only"
CONTIGUITY_TOLERANCE_SECONDS = 1e-6


def clean_stretches(recording) -> list[tuple[float, float]]:
    """(start, end) in seconds of runs of consecutive complete cycles."""
    cycles = circor.heart_cycle_intervals(recording.segments)
    stretches = []
    for cycle in cycles:
        if stretches and abs(cycle.start_seconds - stretches[-1][1]) <= CONTIGUITY_TOLERANCE_SECONDS:
            stretches[-1] = (stretches[-1][0], cycle.end_seconds)
        else:
            stretches.append((cycle.start_seconds, cycle.end_seconds))
    return [stretch for stretch in stretches if stretch[1] - stretch[0] >= EXCERPT_SECONDS
            and stretch[0] >= compute.SETTLING_SECONDS]


def systole_to_diastole_db(recording, start: float, end: float) -> float:
    band = signal.butter(4, [50.0, 800.0], btype="bandpass", fs=recording.sample_rate_hz, output="sos")
    filtered = signal.sosfiltfilt(band, recording.samples)
    powers = {circor.STATE_SYSTOLE: [], circor.STATE_DIASTOLE: []}
    for cycle in circor.heart_cycle_intervals(recording.segments):
        if cycle.start_seconds < start or cycle.end_seconds > end:
            continue
        for state, (low, high) in ((circor.STATE_SYSTOLE, cycle.systole), (circor.STATE_DIASTOLE, cycle.diastole)):
            segment = filtered[int(low * recording.sample_rate_hz):int(high * recording.sample_rate_hz)]
            if len(segment):
                powers[state].append(float(numpy.mean(segment ** 2)))
    return float(10.0 * numpy.log10(numpy.median(powers[circor.STATE_SYSTOLE]) / numpy.median(powers[circor.STATE_DIASTOLE])))


def candidates(patients, location_rule) -> list[dict]:
    found = []
    for patient in patients:
        for info in circor.list_recordings(patient.patient_identifier):
            if not location_rule(patient, info):
                continue
            recording = circor.load_recording(info.file_stem)
            for start, end in clean_stretches(recording):
                found.append({"patient": patient, "info": info, "recording": recording, "start": start,
                              "end": start + EXCERPT_SECONDS,
                              "ratio_db": systole_to_diastole_db(recording, start, start + EXCERPT_SECONDS)})
                break
    return found


def modelled_excerpt(choice) -> numpy.ndarray:
    recording = choice["recording"]
    capture = compute.model_capture(recording.samples, recording.sample_rate_hz, CONDITION,
                                    compute.recording_seed(choice["info"].file_stem))
    delay = compute.load_delays().get(CONDITION, 0.0)
    first = int(round((choice["start"] + delay) * SAMPLE_RATE_HZ))
    return capture[first:first + int(EXCERPT_SECONDS * SAMPLE_RATE_HZ)]


def without_clipping(choice) -> bool:
    excerpt = modelled_excerpt(choice)
    return not numpy.any((excerpt >= SAMPLE_MAXIMUM) | (excerpt <= SAMPLE_MINIMUM))


def pick(found, order: str):
    ranked = sorted(found, key=lambda item: item["ratio_db"], reverse=True)
    if order == "median":
        median = numpy.median([item["ratio_db"] for item in found])
        ranked = sorted(found, key=lambda item: abs(item["ratio_db"] - median))
    for item in ranked:
        if without_clipping(item):
            return item
    return None


def describe(choice, label: str) -> dict:
    patient, info = choice["patient"], choice["info"]
    return {"label": label, "patient": patient.patient_identifier, "file_stem": info.file_stem, "location": info.location,
            "start_s": round(choice["start"], 3), "end_s": round(choice["end"], 3), "murmur": patient.murmur,
            "murmur_locations": "+".join(patient.murmur_locations), "most_audible_location": patient.most_audible_location,
            "age_category": patient.age_category, "sex": patient.sex, "height_cm": patient.height_centimetres,
            "systolic": {"timing": patient.systolic_murmur_timing, "shape": patient.systolic_murmur_shape,
                         "grade": patient.systolic_murmur_grading, "pitch": patient.systolic_murmur_pitch,
                         "quality": patient.systolic_murmur_quality},
            "diastolic": {"timing": patient.diastolic_murmur_timing, "shape": patient.diastolic_murmur_shape,
                          "grade": patient.diastolic_murmur_grading, "pitch": patient.diastolic_murmur_pitch,
                          "quality": patient.diastolic_murmur_quality},
            "systole_to_diastole_50_800_hz_db": round(choice["ratio_db"], 2)}


def write_capture(choice, label: str) -> dict:
    excerpt = modelled_excerpt(choice)
    folder = OUTPUT_DIRECTORY / label
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "capture.wav"
    soundfile.write(str(path), excerpt.astype(numpy.int32) << 8, SAMPLE_RATE_HZ, subtype="PCM_24")
    check, rate = soundfile.read(str(path), dtype="int32")
    if rate != SAMPLE_RATE_HZ or not numpy.array_equal(check >> 8, excerpt):
        raise RuntimeError(f"{path}: read-back differs")
    record = describe(choice, label)
    record.update({"file": f"recordings-public/{label}/capture.wav",
                   "peak_dbfs": round(float(20 * numpy.log10(max(numpy.abs(excerpt).max(), 1) / 8388608.0)), 2)})
    return record


def main() -> None:
    if not compute.chain_model_available():
        raise SystemExit("the chain model and its CirCor calibration are needed for the excerpts")
    patients = circor.list_patients()
    at_most_audible = lambda patient, info: info.location == patient.most_audible_location  # noqa: E731
    loud = pick(candidates([patient for patient in patients if patient.murmur == "Present"
                            and patient.systolic_murmur_grading == "III/VI" and patient.systolic_murmur_quality == "Harsh"],
                           at_most_audible), "largest")
    soft = pick(candidates([patient for patient in patients if patient.murmur == "Present"
                            and patient.systolic_murmur_grading == "I/VI"
                            and patient.age_category == loud["patient"].age_category], at_most_audible), "largest")
    absent_pool = [patient for patient in patients if patient.murmur == "Absent"
                   and patient.age_category == loud["patient"].age_category]
    if loud["patient"].height_centimetres is not None:
        absent_pool = sorted([patient for patient in absent_pool if patient.height_centimetres is not None],
                             key=lambda patient: abs(patient.height_centimetres - loud["patient"].height_centimetres))[:40]
    absent = pick(candidates(absent_pool, lambda patient, info: info.location == loud["info"].location), "median")
    diastolic = candidates([patient for patient in patients if patient.murmur == "Present"
                            and patient.diastolic_murmur_timing is not None],
                           lambda patient, info: info.location in patient.murmur_locations)
    records = [write_capture(loud, "murmur-loud"), write_capture(soft, "murmur-soft"),
               write_capture(absent, "no-murmur-child")]
    optional = [describe(item, "optional diastolic") for item in sorted(diastolic, key=lambda item: -item["ratio_db"])]
    (OUTPUT_DIRECTORY / "excerpts.json").write_text(json.dumps({"excerpts": records, "diastolic_options": optional},
                                                               indent=2), encoding="utf-8")
    write_readme(records, optional)
    for record in records:
        print(record)


def label_text(record) -> str:
    systolic = record["systolic"]
    if record["murmur"] != "Present":
        return f"murmur {record['murmur']}"
    parts = [f"systolic murmur grade {systolic['grade']}", f"timing {systolic['timing']}", f"shape {systolic['shape']}",
             f"pitch {systolic['pitch']}", f"quality {systolic['quality']}"]
    if record["diastolic"]["timing"]:
        parts.append(f"also diastolic {record['diastolic']['grade']}")
    return ", ".join(parts) + f"; heard at {record['murmur_locations']}, most audible at {record['most_audible_location']}"


def write_readme(records, optional) -> None:
    lines = ["# Public murmur excerpts (CirCor DigiScope 1.0.3, chain-modelled)", "",
             "Each `capture.wav` is 8 s of a CirCor recording passed through the capture-chain model "
             "(`hfs.chain_model.model_through_capture_chain`, `level_condition=\"rest\"`, "
             "`spectrum_variant=\"microphone_only\"`, CirCor calibration, seed = CRC-32 of the file stem): 24-bit mono "
             "16 kHz, the same format as `recordings/<name>/capture.wav`, so the device chain takes it unchanged. "
             "Not filtered. The source is sampled at 4 kHz, so there is nothing above 2 kHz.", "",
             "Selection rule (fixed before listening): consecutive complete annotated heart cycles for at least 8 s, "
             "the patient's most audible location, no modelled sample at the 24-bit limit in the excerpt; murmurs: the "
             "recording with the largest systole-to-diastole power ratio (50-800 Hz) in its group; no murmur: same age "
             "category and location as the loud murmur, among the 40 closest in height, the median ratio.", "",
             "| Label | Patient | Recording | Location | Time range in the source (s) | Age category, sex, height | Labels | "
             "Systole/diastole 50-800 Hz (dB) |", "| --- | --- | --- | --- | --- | --- | --- | ---: |"]
    for record in records:
        lines.append(f"| `{record['label']}` | {record['patient']} | {record['file_stem']} | {record['location']} | "
                     f"{record['start_s']:.3f}-{record['end_s']:.3f} | {record['age_category']}, {record['sex']}, "
                     f"{record['height_cm']} cm | {label_text(record)} | {record['systole_to_diastole_50_800_hz_db']:+.1f} |")
    lines.append("")
    if optional:
        best = optional[0]
        lines.append(f"Optional fourth (diastolic murmur, not written): patient {best['patient']}, {best['file_stem']}, "
                     f"{best['start_s']:.3f}-{best['end_s']:.3f} s, diastolic grade {best['diastolic']['grade']}, timing "
                     f"{best['diastolic']['timing']}, pitch {best['diastolic']['pitch']}, quality "
                     f"{best['diastolic']['quality']}; systolic grade {best['systolic']['grade']}. "
                     f"{len(optional)} diastolic-murmur recording(s) with 8 s of clean annotation exist in total "
                     f"(`excerpts.json`).")
    else:
        lines.append("Optional fourth (diastolic murmur): no diastolic-murmur recording has 8 s of consecutive complete "
                     "annotated cycles at a location where the murmur is heard.")
    lines += ["", "## Source and licence", "",
              "CirCor DigiScope Phonocardiogram Dataset, version 1.0.3, PhysioNet, DOI 10.13026/tshs-mw03, "
              "https://physionet.org/content/circor-heart-sound/1.0.3/ (accessed 2026-11-23). Licence: Open Data "
              "Commons Attribution License v1.0 (`public-data/circor-1.0.3/LICENSE.txt`); attribution required when "
              "these excerpts are shared. Dataset paper: J. Oliveira et al., \"The CirCor DigiScope Dataset: From "
              "Murmur Detection to Murmur Classification\", 2022, arXiv:2108.00813 (journal pages not verified here).",
              "", "Written by `src/listening_public.py excerpts`."]
    (OUTPUT_DIRECTORY / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
