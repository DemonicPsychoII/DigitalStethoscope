"""Access to the raw INMP441 captures of the study."""
from functools import lru_cache
from pathlib import Path

import numpy
import soundfile

STUDY_DIRECTORY = Path(__file__).resolve().parents[2]
RECORDINGS_DIRECTORY = STUDY_DIRECTORY / "recordings"
RECORDING_NAMES = ["rest-1", "rest-2", "elevated-1", "elevated-2", "elevated-3"]
SAMPLE_RATE_HZ = 16000
DISCARDED_SECONDS = 2.0
SAMPLE_MAXIMUM = 8388607
SAMPLE_MINIMUM = -8388608


@lru_cache(maxsize=None)
def _load_cached(name: str) -> numpy.ndarray:
    left_aligned, sample_rate = soundfile.read(RECORDINGS_DIRECTORY / name / "capture.wav", dtype="int32")
    if sample_rate != SAMPLE_RATE_HZ:
        raise ValueError(f"{name}: sample rate {sample_rate} Hz, expected {SAMPLE_RATE_HZ} Hz")
    if left_aligned.ndim != 1:
        raise ValueError(f"{name}: expected mono")
    samples = (left_aligned >> 8).astype(numpy.int32)
    samples = samples[int(round(DISCARDED_SECONDS * SAMPLE_RATE_HZ)):]
    samples.setflags(write=False)
    return samples


def load_recording(name: str) -> numpy.ndarray:
    """int32 array of 24-bit sample values (-8388608...8388607) after discarding the first 2 s.
    Sample i is at time DISCARDED_SECONDS + i / SAMPLE_RATE_HZ from file start."""
    return _load_cached(name).copy()


def sample_times_seconds(sample_count: int, sample_rate_hz: float = SAMPLE_RATE_HZ) -> numpy.ndarray:
    return DISCARDED_SECONDS + numpy.arange(sample_count) / sample_rate_hz
