"""Access to the CirCor DigiScope Phonocardiogram Dataset 1.0.3 (murmur labels and heart-cycle segmentation).

The data lives in public-data/circor-1.0.3/ and is fetched by src/public_download_circor.py.
All files are parsed as data only: csv for the tables, plain text for headers and segmentations,
soundfile for the WAV audio.
"""
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy
import soundfile

STUDY_DIRECTORY = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = STUDY_DIRECTORY / "public-data" / "circor-1.0.3"
RECORDING_DIRECTORY = DATA_DIRECTORY / "training_data"
PATIENT_TABLE_PATH = DATA_DIRECTORY / "training_data.csv"
READY_MARKER_PATH = DATA_DIRECTORY / "READY"

STATE_UNANNOTATED = 0
STATE_S1 = 1
STATE_SYSTOLE = 2
STATE_S2 = 3
STATE_DIASTOLE = 4
STATE_NAMES = {
    STATE_UNANNOTATED: "unannotated",
    STATE_S1: "S1",
    STATE_SYSTOLE: "systole",
    STATE_S2: "S2",
    STATE_DIASTOLE: "diastole",
}
SEGMENT_DATA_TYPE = numpy.dtype([("start_seconds", "f8"), ("end_seconds", "f8"), ("state", "i1")])
CONTIGUITY_TOLERANCE_SECONDS = 1e-6
MISSING_VALUE = "nan"
WAV_FULL_SCALE = 32768.0


@dataclass(frozen=True)
class PatientInfo:
    patient_identifier: str
    recording_locations: tuple[str, ...]
    age_category: str | None
    sex: str | None
    height_centimetres: float | None
    weight_kilograms: float | None
    pregnancy_status: bool | None
    murmur: str
    murmur_locations: tuple[str, ...]
    most_audible_location: str | None
    systolic_murmur_timing: str | None
    systolic_murmur_shape: str | None
    systolic_murmur_grading: str | None
    systolic_murmur_pitch: str | None
    systolic_murmur_quality: str | None
    diastolic_murmur_timing: str | None
    diastolic_murmur_shape: str | None
    diastolic_murmur_grading: str | None
    diastolic_murmur_pitch: str | None
    diastolic_murmur_quality: str | None
    outcome: str | None
    campaign: str | None
    additional_identifier: str | None


@dataclass(frozen=True)
class RecordingInfo:
    patient_identifier: str
    location: str
    file_stem: str
    sample_rate_hz: int
    sample_count: int
    duration_seconds: float
    has_segmentation: bool
    annotated_duration_seconds: float
    murmur_heard_at_location: bool | None
    """True or False for patients labelled Present or Absent; None when the patient's murmur is Unknown."""


@dataclass(frozen=True)
class Recording:
    samples: numpy.ndarray
    sample_rate_hz: int
    segments: numpy.ndarray
    info: RecordingInfo


@dataclass(frozen=True)
class HeartCycle:
    s1: tuple[float, float]
    systole: tuple[float, float]
    s2: tuple[float, float]
    diastole: tuple[float, float]

    @property
    def start_seconds(self) -> float:
        return self.s1[0]

    @property
    def end_seconds(self) -> float:
        return self.diastole[1]

    @property
    def duration_seconds(self) -> float:
        return self.diastole[1] - self.s1[0]


def data_is_ready() -> bool:
    return READY_MARKER_PATH.exists()


def _optional_text(value: str) -> str | None:
    value = value.strip()
    return None if value in ("", MISSING_VALUE) else value


def _optional_float(value: str) -> float | None:
    text = _optional_text(value)
    return None if text is None else float(text)


def _optional_boolean(value: str) -> bool | None:
    text = _optional_text(value)
    if text is None:
        return None
    if text not in ("True", "False"):
        raise ValueError(f"unexpected boolean value {value!r}")
    return text == "True"


def _location_list(value: str) -> tuple[str, ...]:
    text = _optional_text(value)
    return () if text is None else tuple(text.split("+"))


@lru_cache(maxsize=1)
def _patients_by_identifier() -> dict[str, PatientInfo]:
    patients = {}
    with open(PATIENT_TABLE_PATH, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            patient = PatientInfo(
                patient_identifier=row["Patient ID"].strip(),
                recording_locations=_location_list(row["Recording locations:"]),
                age_category=_optional_text(row["Age"]),
                sex=_optional_text(row["Sex"]),
                height_centimetres=_optional_float(row["Height"]),
                weight_kilograms=_optional_float(row["Weight"]),
                pregnancy_status=_optional_boolean(row["Pregnancy status"]),
                murmur=row["Murmur"].strip(),
                murmur_locations=_location_list(row["Murmur locations"]),
                most_audible_location=_optional_text(row["Most audible location"]),
                systolic_murmur_timing=_optional_text(row["Systolic murmur timing"]),
                systolic_murmur_shape=_optional_text(row["Systolic murmur shape"]),
                systolic_murmur_grading=_optional_text(row["Systolic murmur grading"]),
                systolic_murmur_pitch=_optional_text(row["Systolic murmur pitch"]),
                systolic_murmur_quality=_optional_text(row["Systolic murmur quality"]),
                diastolic_murmur_timing=_optional_text(row["Diastolic murmur timing"]),
                diastolic_murmur_shape=_optional_text(row["Diastolic murmur shape"]),
                diastolic_murmur_grading=_optional_text(row["Diastolic murmur grading"]),
                diastolic_murmur_pitch=_optional_text(row["Diastolic murmur pitch"]),
                diastolic_murmur_quality=_optional_text(row["Diastolic murmur quality"]),
                outcome=_optional_text(row["Outcome"]),
                campaign=_optional_text(row["Campaign"]),
                additional_identifier=_optional_text(row["Additional ID"]),
            )
            if patient.murmur not in ("Present", "Absent", "Unknown"):
                raise ValueError(f"patient {patient.patient_identifier}: unexpected murmur label {patient.murmur!r}")
            patients[patient.patient_identifier] = patient
    return patients


def list_patients() -> list[PatientInfo]:
    return list(_patients_by_identifier().values())


def read_header(file_stem: str) -> tuple[int, int]:
    """Returns (sample rate in Hz, sample count) from the WFDB header record line."""
    with open(RECORDING_DIRECTORY / f"{file_stem}.hea", encoding="utf-8") as stream:
        record_line = stream.readline().split()
    if len(record_line) < 4 or record_line[0] != file_stem or record_line[1] != "1":
        raise ValueError(f"{file_stem}: unexpected header record line {record_line}")
    return int(float(record_line[2])), int(record_line[3])


def read_segments(file_stem: str) -> numpy.ndarray:
    segmentation_path = RECORDING_DIRECTORY / f"{file_stem}.tsv"
    if not segmentation_path.exists():
        return numpy.zeros(0, dtype=SEGMENT_DATA_TYPE)
    rows = []
    with open(segmentation_path, encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) != 3:
                raise ValueError(f"{segmentation_path.name}:{line_number}: expected three fields")
            state = int(float(fields[2]))
            if state not in STATE_NAMES:
                raise ValueError(f"{segmentation_path.name}:{line_number}: unknown state {state}")
            rows.append((float(fields[0]), float(fields[1]), state))
    return numpy.array(rows, dtype=SEGMENT_DATA_TYPE)


def location_from_file_stem(patient_identifier: str, file_stem: str) -> str:
    # Repeated recordings at one location carry a numeric suffix, for example 50782_MV_1.
    return file_stem[len(patient_identifier) + 1:].split("_")[0]


def read_recording_info(patient: PatientInfo, file_stem: str) -> RecordingInfo:
    sample_rate_hz, sample_count = read_header(file_stem)
    segments = read_segments(file_stem)
    annotated = segments[segments["state"] != STATE_UNANNOTATED]
    location = location_from_file_stem(patient.patient_identifier, file_stem)
    if patient.murmur == "Unknown":
        murmur_heard_at_location = None
    else:
        murmur_heard_at_location = patient.murmur == "Present" and location in patient.murmur_locations
    return RecordingInfo(
        patient_identifier=patient.patient_identifier,
        location=location,
        file_stem=file_stem,
        sample_rate_hz=sample_rate_hz,
        sample_count=sample_count,
        duration_seconds=sample_count / sample_rate_hz,
        has_segmentation=(RECORDING_DIRECTORY / f"{file_stem}.tsv").exists(),
        annotated_duration_seconds=float(numpy.sum(annotated["end_seconds"] - annotated["start_seconds"])),
        murmur_heard_at_location=murmur_heard_at_location,
    )


def file_stems_of_patient(patient_identifier: str) -> list[str]:
    """File stems from the patient's .txt file (second column of every recording line)."""
    stems = []
    with open(RECORDING_DIRECTORY / f"{patient_identifier}.txt", encoding="utf-8") as stream:
        first_line = stream.readline().split()
        recording_count = int(first_line[1])
        for _ in range(recording_count):
            fields = stream.readline().split()
            stems.append(Path(fields[1]).stem)
    return stems


@lru_cache(maxsize=1)
def _recordings_and_parse_failures() -> tuple[dict[str, RecordingInfo], dict[str, str]]:
    recordings = {}
    parse_failures = {}
    for patient in list_patients():
        try:
            file_stems = file_stems_of_patient(patient.patient_identifier)
        except (OSError, ValueError, IndexError) as error:
            parse_failures[f"{patient.patient_identifier}.txt"] = f"{type(error).__name__}: {error}"
            continue
        for file_stem in file_stems:
            try:
                recordings[file_stem] = read_recording_info(patient, file_stem)
            except (OSError, ValueError) as error:
                parse_failures[file_stem] = f"{type(error).__name__}: {error}"
    return recordings, parse_failures


def _recordings_by_stem() -> dict[str, RecordingInfo]:
    return _recordings_and_parse_failures()[0]


def list_parse_failures() -> dict[str, str]:
    """Recordings or patient files that list_recordings skips, with the reason."""
    return dict(_recordings_and_parse_failures()[1])


def list_recordings(patient_identifier: str | None = None) -> list[RecordingInfo]:
    recordings = _recordings_by_stem().values()
    if patient_identifier is None:
        return list(recordings)
    return [recording for recording in recordings if recording.patient_identifier == str(patient_identifier)]


def load_recording(file_stem: str) -> Recording:
    recordings, parse_failures = _recordings_and_parse_failures()
    if file_stem in parse_failures:
        raise ValueError(f"{file_stem}: could not be parsed: {parse_failures[file_stem]}")
    if file_stem not in recordings:
        raise KeyError(f"{file_stem}: no such recording")
    info = recordings[file_stem]
    audio_path = RECORDING_DIRECTORY / f"{file_stem}.wav"
    audio_format = soundfile.info(str(audio_path))
    if audio_format.subtype != "PCM_16" or audio_format.channels != 1:
        raise ValueError(f"{file_stem}: expected mono 16-bit PCM, found {audio_format.channels} channels {audio_format.subtype}")
    integer_samples, sample_rate_hz = soundfile.read(str(audio_path), dtype="int16")
    if sample_rate_hz != info.sample_rate_hz:
        raise ValueError(f"{file_stem}: WAV sample rate {sample_rate_hz} Hz differs from header {info.sample_rate_hz} Hz")
    samples = integer_samples.astype(numpy.float64) / WAV_FULL_SCALE
    samples.setflags(write=False)
    return Recording(samples=samples, sample_rate_hz=sample_rate_hz, segments=read_segments(file_stem), info=info)


def heart_cycle_intervals(recording: Recording | numpy.ndarray) -> list[HeartCycle]:
    """Complete S1-systole-S2-diastole cycles whose four segments follow each other without a gap."""
    segments = recording.segments if isinstance(recording, Recording) else recording
    expected_states = (STATE_S1, STATE_SYSTOLE, STATE_S2, STATE_DIASTOLE)
    cycles = []
    index = 0
    while index + 4 <= len(segments):
        window = segments[index:index + 4]
        states_match = tuple(int(state) for state in window["state"]) == expected_states
        contiguous = bool(numpy.all(numpy.abs(window["start_seconds"][1:] - window["end_seconds"][:-1]) <= CONTIGUITY_TOLERANCE_SECONDS))
        if states_match and contiguous:
            intervals = [(float(segment["start_seconds"]), float(segment["end_seconds"])) for segment in window]
            cycles.append(HeartCycle(s1=intervals[0], systole=intervals[1], s2=intervals[2], diastole=intervals[3]))
            index += 4
        else:
            index += 1
    return cycles
