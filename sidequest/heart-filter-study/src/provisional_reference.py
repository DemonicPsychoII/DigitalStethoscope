"""PROVISIONAL reference heart rate, only for development until reference/<name>.json exists.

Zero-phase 25-150 Hz Butterworth, absolute value, zero-phase 10 Hz low-pass, 100 Hz envelope,
autocorrelation peak in 0.3-2.0 s per 8 s window. It shares the method of the estimator under test,
so it favours 25-150 Hz filters and must not be used for conclusions.
"""
import json
import sys
from pathlib import Path

import numpy
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hfs.recordings import DISCARDED_SECONDS, RECORDING_NAMES, SAMPLE_RATE_HZ, STUDY_DIRECTORY, load_recording

OUTPUT_DIRECTORY = STUDY_DIRECTORY / "cache" / "provisional_reference"
ENVELOPE_RATE_HZ = 100


def provisional_windows(name: str) -> list[dict]:
    samples = load_recording(name).astype(numpy.float64) / 8388608.0
    bandpass = signal.butter(2, [25, 150], "bandpass", fs=SAMPLE_RATE_HZ, output="sos")
    envelope = numpy.abs(signal.sosfiltfilt(bandpass, samples))
    envelope = signal.sosfiltfilt(signal.butter(2, 10, fs=SAMPLE_RATE_HZ, output="sos"), envelope)
    envelope = envelope[::SAMPLE_RATE_HZ // ENVELOPE_RATE_HZ]
    windows = []
    for end_time in range(10, 61):
        stop = int(round((end_time - DISCARDED_SECONDS) * ENVELOPE_RATE_HZ))
        segment = envelope[stop - 8 * ENVELOPE_RATE_HZ:stop]
        segment = segment - segment.mean()
        correlation = numpy.correlate(segment, segment, "full")[len(segment) - 1:]
        correlation /= correlation[0] * (len(segment) - numpy.arange(len(segment))) / len(segment)
        lags = numpy.arange(30, 201)
        best = lags[numpy.argmax(correlation[lags])]
        previous_value, peak_value, next_value = correlation[best - 1:best + 2]
        offset = 0.5 * (previous_value - next_value) / (previous_value - 2 * peak_value + next_value)
        windows.append({"end_time_s": end_time, "reference_bpm": float(60.0 * ENVELOPE_RATE_HZ / (best + offset)),
                        "reliable": True, "method_spread_bpm": 0.0, "rate_change_in_window_bpm": 0.0})
    return windows


def main():
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name in RECORDING_NAMES:
        document = {"recording": name, "provisional": True, "method": __doc__.strip(), "windows": provisional_windows(name)}
        (OUTPUT_DIRECTORY / f"{name}.json").write_text(json.dumps(document, indent=1))
        print(name, " ".join(f"{window['reference_bpm']:.0f}" for window in document["windows"]))


if __name__ == "__main__":
    main()
