"""Access to the downloaded EPHNOGRAM database (simultaneous ECG and PCG, PhysioNet, WFDB format).

Data come from public-data/ephnogram-1.0.0/, written by src/public_download_ephnogram.py.
Headers are parsed with the wfdb package; samples are read with numpy from the interleaved
16-bit signal file, only for the requested channels.
"""
import csv
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy
import wfdb

STUDY_DIRECTORY = Path(__file__).resolve().parents[2]
DATABASE_DIRECTORY = STUDY_DIRECTORY / "public-data" / "ephnogram-1.0.0"
WFDB_DIRECTORY = DATABASE_DIRECTORY / "WFDB"
SPREADSHEET_PATH = DATABASE_DIRECTORY / "ECGPCGSpreadsheet.csv"
MANIFEST_PATH = DATABASE_DIRECTORY / "MANIFEST.json"
FORMAT_16_MINIMUM = -32768
FORMAT_16_MAXIMUM = 32767


@dataclass(frozen=True)
class RecordInfo:
    record_name: str
    subject_id: str
    scenario: str
    ecg_quality: str
    pcg_quality: str
    duration_seconds: float
    sample_rate_hz: float
    channel_names: tuple
    available: bool
    housekeeping_note: str = ""


@dataclass
class Record:
    """ecg and pcg in physical units (header units, mV for this database); pcg2 is None if absent.

    ecg_digital_limits_physical gives the 16-bit ADC range converted to physical units, so callers
    can detect ADC saturation. WFDB marks invalid samples in format 16 with -32768; this database
    uses no separate invalid marker, so that value is kept as a sample at the lower ADC limit.
    """
    ecg: numpy.ndarray
    pcg: numpy.ndarray
    pcg2: numpy.ndarray | None
    sample_rate_hz: float
    info: RecordInfo
    ecg_digital_limits_physical: tuple
    units: dict


def _verified_files():
    if not MANIFEST_PATH.exists():
        return {}
    files = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("files", {})
    return {path: entry for path, entry in files.items() if entry.get("verified")}


def _is_available(record_name, verified_files):
    relative_path = f"WFDB/{record_name}.dat"
    entry = verified_files.get(relative_path)
    data_path = DATABASE_DIRECTORY / relative_path
    return bool(entry) and data_path.exists() and data_path.stat().st_size == entry["size_bytes"]


@lru_cache(maxsize=None)
def _read_header(record_name):
    header = wfdb.rdheader(str(WFDB_DIRECTORY / record_name))
    for channel_index in range(header.n_sig):
        if header.fmt[channel_index] != "16":
            raise ValueError(f"{record_name}: unsupported WFDB format {header.fmt[channel_index]}")
        if (header.samps_per_frame or [1] * header.n_sig)[channel_index] != 1:
            raise ValueError(f"{record_name}: multiple samples per frame are not supported")
        if (header.skew or [None] * header.n_sig)[channel_index] not in (None, 0):
            raise ValueError(f"{record_name}: signal skew is not supported")
        if (header.byte_offset or [None] * header.n_sig)[channel_index] not in (None, 0):
            raise ValueError(f"{record_name}: byte offset is not supported")
    if len(set(header.file_name)) != 1:
        raise ValueError(f"{record_name}: signals spread over several files are not supported")
    return header


def _spreadsheet_rows():
    with open(SPREADSHEET_PATH, newline="", encoding="utf-8-sig") as handle:
        return [row for row in csv.DictReader(handle) if row.get("Record Name")]


def _record_info(row, verified_files):
    record_name = row["Record Name"].strip()
    header_path = WFDB_DIRECTORY / f"{record_name}.hea"
    if header_path.exists():
        header = _read_header(record_name)
        duration_seconds = header.sig_len / header.fs
        sample_rate_hz = float(header.fs)
        channel_names = tuple(header.sig_name)
    else:
        duration_seconds = float(row["Record Duration (min)"]) * 60.0
        sample_rate_hz = float("nan")
        channel_names = ()
    return RecordInfo(
        record_name=record_name,
        subject_id=row["Subject ID"].strip(),
        scenario=" ".join(row["Recording Scenario"].split()),
        ecg_quality=row["ECG Notes"].strip(),
        pcg_quality=row["PCG Notes"].strip(),
        duration_seconds=duration_seconds,
        sample_rate_hz=sample_rate_hz,
        channel_names=channel_names,
        available=_is_available(record_name, verified_files),
        housekeeping_note=(row.get("Database Housekeeping") or "").strip(),
    )


def list_records() -> list[RecordInfo]:
    verified_files = _verified_files()
    return [_record_info(row, verified_files) for row in _spreadsheet_rows()]


def record_info(record_name: str) -> RecordInfo:
    for info in list_records():
        if info.record_name == record_name:
            return info
    raise KeyError(record_name)


def duplicate_signal_groups() -> list[tuple[str, ...]]:
    """Records whose ECG and PCG header lines (gain, baseline, initial value, checksum) are identical,
    which means the same signal was stored under several record names."""
    groups = {}
    for header_path in sorted(WFDB_DIRECTORY.glob("ECGPCG*.hea")):
        header = _read_header(header_path.stem)
        names = list(header.sig_name)
        signature = tuple(
            (header.adc_gain[index], header.baseline[index], header.init_value[index], header.checksum[index])
            for index in (names.index("ECG"), names.index("PCG"))
        )
        groups.setdefault(signature, []).append(header_path.stem)
    return [tuple(group) for group in groups.values() if len(group) > 1]


def _read_channels(record_name, header, channel_indices):
    data_path = WFDB_DIRECTORY / header.file_name[0]
    frames = numpy.memmap(data_path, dtype="<i2", mode="r")
    if frames.size != header.sig_len * header.n_sig:
        raise ValueError(f"{record_name}: signal file holds {frames.size} samples, header expects "
                         f"{header.sig_len * header.n_sig}")
    frames = frames.reshape(header.sig_len, header.n_sig)
    channels = []
    for channel_index in channel_indices:
        digital = numpy.asarray(frames[:, channel_index], dtype=numpy.float64)
        gain = header.adc_gain[channel_index] or 200.0
        channels.append((digital - header.baseline[channel_index]) / gain)
    del frames
    return channels


def load_record(record_name: str) -> Record:
    info = record_info(record_name)
    if not info.available:
        raise FileNotFoundError(f"{record_name}: signal file not downloaded or not verified")
    header = _read_header(record_name)
    names = list(header.sig_name)
    if "ECG" not in names or "PCG" not in names:
        raise ValueError(f"{record_name}: expected ECG and PCG channels, found {names}")
    wanted = [names.index("ECG"), names.index("PCG")] + ([names.index("PCG2")] if "PCG2" in names else [])
    channels = _read_channels(record_name, header, wanted)
    ecg_index = names.index("ECG")
    ecg_gain = header.adc_gain[ecg_index] or 200.0
    limits = tuple((value - header.baseline[ecg_index]) / ecg_gain for value in (FORMAT_16_MINIMUM, FORMAT_16_MAXIMUM))
    return Record(
        ecg=channels[0],
        pcg=channels[1],
        pcg2=channels[2] if len(channels) > 2 else None,
        sample_rate_hz=float(header.fs),
        info=info,
        ecg_digital_limits_physical=limits,
        units={name: header.units[names.index(name)] for name in ("ECG", "PCG", "PCG2") if name in names},
    )
