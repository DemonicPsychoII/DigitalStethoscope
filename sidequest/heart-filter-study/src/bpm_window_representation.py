"""What holding filtered audio in PSRAM buys: 8 s of BPM-filtered audio at 1 kHz (8000 float32 = 32 kB) with the
envelope computed at update time (zero-phase inside the window), against the streaming 100 Hz envelope (3.2 kB).

Usage: python src/bpm_window_representation.py --reference reference
"""
import argparse
import sys
from pathlib import Path

import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpm_evaluate as evaluation
from hfs import bpm_estimator, device_chain, filters
from hfs.bpm_estimator import EstimatorConfiguration
from hfs.recordings import DISCARDED_SECONDS, RECORDING_NAMES, STUDY_DIRECTORY, load_recording

FINAL_ESTIMATOR = EstimatorConfiguration(envelope_lowpass="two_pole", envelope_lowpass_hz=5.0, peak_choice="half_check")
CANDIDATES = [("decimated", 25, 150, 2, 2), ("decimated", 30, 300, 4, 2), ("decimated", 40, 300, 2, 2)]


def one_pole_forward_backward(values, coefficient):
    output = values.copy()
    for direction in (1, -1):
        sequence = output if direction == 1 else output[::-1]
        state = sequence[0]
        result = numpy.empty_like(sequence)
        for index in range(sequence.shape[0]):
            state = state + coefficient * (sequence[index] - state)
            result[index] = state
        output = result if direction == 1 else result[::-1]
    return output.astype(numpy.float32)


def update_time_envelope_estimates(filtered_1khz, configuration):
    rate = 1000
    window_samples = int(configuration.window_seconds * rate)
    decimation = rate // configuration.envelope_rate_hz
    coefficient = numpy.float32(1.0 - numpy.exp(-2.0 * numpy.pi * configuration.envelope_lowpass_hz / rate))
    estimator = bpm_estimator.BPMEstimator(configuration, rate)
    results = {}
    for end_time in range(10, 61):
        stop = int(round((end_time - DISCARDED_SECONDS) * rate))
        if stop > filtered_1khz.shape[0]:
            break
        window = numpy.abs(filtered_1khz[stop - window_samples:stop])
        envelope = one_pole_forward_backward(window, coefficient)
        envelope = one_pole_forward_backward(envelope, coefficient)
        estimator.ring_buffer[:] = envelope[decimation - 1::decimation][:estimator.window_length]
        estimator.ring_position = 0
        estimator.ring_filled = estimator.window_length
        results[end_time] = estimator.update()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", default="reference")
    arguments = parser.parse_args()
    reference_directory = Path(arguments.reference)
    if not reference_directory.is_absolute() and not reference_directory.exists():
        reference_directory = STUDY_DIRECTORY / reference_directory
    reference = evaluation.load_reference(reference_directory)
    lines = ["# Window representation: streaming envelope versus filtered audio held in PSRAM", "",
             f"Estimator: {FINAL_ESTIMATOR.key()}; analysis filter: decimated design (64-tap anti-alias FIR, 1 kHz, Butterworth).",
             "Streaming: causal envelope at 16 kHz -> 100 Hz ring buffer of 800 float32 (3.2 kB).",
             "Audio window: 8000 float32 of filtered audio at 1 kHz (32 kB); at each update |x| -> forward-backward two-pole 5 Hz -> 100 Hz -> same autocorrelation.", "",
             "| filter | representation | window bytes | MAE reliable | within tolerance reliable | gross errors reliable | MAE all windows | gross errors all windows |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for family, highpass, lowpass, highpass_order, lowpass_order in CANDIDATES:
        candidate = filters.design_filter(family, highpass, lowpass, highpass_order, lowpass_order)
        streaming, audio_window = {}, {}
        for name in RECORDING_NAMES:
            filtered = device_chain.apply_filter_blockwise(candidate, load_recording(name))
            stream_results, _ = bpm_estimator.run_estimator(filtered, candidate.output_rate_hz, FINAL_ESTIMATOR)
            streaming[name] = [[time, result.bpm, result.valid, result.quality, result.margin, result.reason] for time, result in stream_results.items()]
            window_results = update_time_envelope_estimates(filtered, FINAL_ESTIMATOR)
            audio_window[name] = [[time, result.bpm, result.valid, result.quality, result.margin, result.reason] for time, result in window_results.items()]
        for label, estimates, window_bytes in (("streaming envelope", streaming, 3200), ("filtered audio at 1 kHz", audio_window, 32000)):
            metrics = evaluation.compute_metrics(evaluation.aligned_arrays(estimates, reference))
            lines.append(f"| {candidate.identifier} | {label} | {window_bytes} | {metrics['reliable_mae_bpm']:.2f} | "
                         f"{100 * metrics['reliable_within_tolerance_share']:.0f} % | {metrics['reliable_gross_error_count']} | "
                         f"{metrics['all_mae_bpm']:.2f} | {metrics['all_gross_error_count']} |")
    output = STUDY_DIRECTORY / "results" / "bpm_window_representation.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
