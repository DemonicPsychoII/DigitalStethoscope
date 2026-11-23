"""Diagnosis of the one-third-rate error of run 2 (EPHNOGRAM, final run-1 method, 40-150 Hz).

Usage: python -I src/bpm_improved_method_diagnosis.py
Writes results-public/one_third_diagnosis_numbers.json and results-public/figures/one_third_*.png.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib

matplotlib.use("Agg")
import numpy
from matplotlib import pyplot
from scipy import signal

import bpm_evaluate
import bpm_evaluate_public
import bpm_improved_method_compute as compute
import public_evaluation_common as common
from hfs import bpm_estimator, device_chain, ephnogram

RECORDS = {"ECGPCG0064": 900, "ECGPCG0032": None, "ECGPCG0052": None}
FIGURES_DIRECTORY = common.RESULTS_DIRECTORY / "figures"
ENVELOPE_RATE_HZ = 100
WINDOW_LENGTH = 800
BACKGROUND = "#0f1115"
FOREGROUND = "#d8dee9"


def style_axis(axis):
    axis.set_facecolor(BACKGROUND)
    axis.tick_params(colors=FOREGROUND)
    for spine in axis.spines.values():
        spine.set_color("#4c566a")
    axis.xaxis.label.set_color(FOREGROUND)
    axis.yaxis.label.set_color(FOREGROUND)
    axis.title.set_color(FOREGROUND)


def peak_near(correlation, lag, tolerance=0.1):
    low = max(1, int(numpy.floor(lag * (1 - tolerance))))
    high = min(correlation.shape[0] - 1, int(numpy.ceil(lag * (1 + tolerance))))
    if low > high:
        return numpy.nan
    return float(numpy.max(correlation[low:high + 1]))


def biased_autocorrelation(window, lag_count):
    centred = window - window.mean()
    full = numpy.correlate(centred, centred, mode="full")[centred.shape[0] - 1:centred.shape[0] + lag_count]
    return full / full[0]


def envelopes_for(record_name, condition, configuration):
    record = ephnogram.load_record(record_name)
    samples = numpy.asarray(bpm_evaluate_public.modelled_capture(record, condition))
    del record
    candidate = bpm_evaluate.build_candidate(common.candidate_specifications()[common.RECOMMENDED])
    filtered = device_chain.apply_filter_to_normalised(candidate, device_chain.normalise(samples))
    envelope, _ = compute.envelope_of(filtered, candidate.output_rate_hz, configuration)
    return envelope


def window_at(envelope, end_time):
    stop = int(end_time * ENVELOPE_RATE_HZ)
    return envelope[stop - WINDOW_LENGTH:stop].astype(numpy.float32)


def normalised(window):
    centred = (window - numpy.float32(window.mean(dtype=numpy.float32))).astype(numpy.float32)
    correlation = numpy.zeros(402, dtype=numpy.float32)
    bpm_estimator._normalised_autocorrelation(centred, 401, correlation)
    return correlation


def record_statistics(envelope, reference, end_times):
    """Over the given window ends: r near T, 2T, 3T for the estimator's and the plain (biased) correlation."""
    rows = []
    for end_time in end_times:
        window = window_at(envelope, end_time)
        period_lags = 60.0 / reference[end_time]["reference_bpm"] * ENVELOPE_RATE_HZ
        correlation = normalised(window)
        plain = biased_autocorrelation(window.astype(numpy.float64), 401)
        rows.append([peak_near(correlation, period_lags), peak_near(correlation, 2 * period_lags),
                     peak_near(correlation, 3 * period_lags), peak_near(plain, period_lags),
                     peak_near(plain, 3 * period_lags)])
    return numpy.array(rows)


def spectrum_ratio(envelope, reference, end_times, segment_seconds=8):
    """Envelope power at one third of the heart rate relative to the power at the heart rate, per window."""
    ratios = []
    for end_time in end_times:
        window = window_at(envelope, end_time).astype(numpy.float64)
        window = (window - window.mean()) * numpy.hanning(window.shape[0])
        spectrum = numpy.abs(numpy.fft.rfft(window, 8192)) ** 2
        frequencies = numpy.fft.rfftfreq(8192, 1.0 / ENVELOPE_RATE_HZ)
        heart_hz = reference[end_time]["reference_bpm"] / 60.0

        def power_near(frequency):
            selection = numpy.abs(frequencies - frequency) <= 0.04 * frequency + 0.07
            return spectrum[selection].max()
        ratios.append([power_near(heart_hz / 3.0), power_near(2 * heart_hz / 3.0), power_near(heart_hz),
                       numpy.median(spectrum[(frequencies > 0.3) & (frequencies < 8)])])
    return numpy.array(ratios)


def main():
    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    key = common.configuration_key(common.FINAL_METHOD)
    numbers = {}
    figure, axes = pyplot.subplots(len(RECORDS), 2, figsize=(14, 3.6 * len(RECORDS)), facecolor=BACKGROUND)
    spectrum_figure, spectrum_axes = pyplot.subplots(1, len(RECORDS), figsize=(14, 4.2), facecolor=BACKGROUND)
    for row_index, (record_name, chosen_end) in enumerate(RECORDS.items()):
        info = ephnogram.record_info(record_name)
        reference = common.load_reference(record_name)
        estimates = common.cached_estimates(record_name, "rest", common.RECOMMENDED)[key]
        types = {}
        for estimate_row in estimates:
            end_time = int(round(estimate_row[0]))
            window_reference = reference.get(end_time)
            if end_time < 10 or window_reference is None or not window_reference["reliable"]:
                continue
            types[end_time] = (common.error_type(estimate_row[1], window_reference["reference_bpm"]), estimate_row[1])
        one_third_ends = [end for end, (kind, _) in types.items() if kind == "one third"]
        correct_ends = [end for end, (kind, _) in types.items() if kind == "none"]
        if chosen_end is None or chosen_end not in one_third_ends:
            candidates = one_third_ends if chosen_end is None else [end for end in one_third_ends if abs(end - chosen_end) < 120]
            chosen_end = sorted(candidates or one_third_ends)[len(candidates or one_third_ends) // 2]
        record_numbers = {"subject": info.subject_id, "scenario": info.scenario, "chosen_end_time_s": chosen_end,
                          "reference_bpm_at_chosen": reference[chosen_end]["reference_bpm"],
                          "estimate_at_chosen": float(types[chosen_end][1]),
                          "one_third_windows": len(one_third_ends), "correct_windows": len(correct_ends)}
        envelopes = {}
        for label, condition, configuration in (("model_final", "rest", common.FINAL_METHOD),
                                                ("resample_only_final", bpm_evaluate_public.STAND_IN_CONDITION, common.FINAL_METHOD),
                                                ("model_one_pole_12hz", "rest", common.HALF_CHECK_ONLY)):
            envelopes[label] = envelopes_for(record_name, condition, configuration)
            for subset_name, ends in (("one_third_windows", one_third_ends), ("correct_windows", correct_ends)):
                if not ends:
                    continue
                statistics = record_statistics(envelopes[label], reference, ends)
                ratios = spectrum_ratio(envelopes[label], reference, ends)
                record_numbers[f"{label}:{subset_name}"] = {
                    "median_r_T": float(numpy.nanmedian(statistics[:, 0])),
                    "median_r_2T": float(numpy.nanmedian(statistics[:, 1])),
                    "median_r_3T": float(numpy.nanmedian(statistics[:, 2])),
                    "share_r_3T_above_r_T": float(numpy.nanmean(statistics[:, 2] > statistics[:, 0])),
                    "plain_share_r_3T_above_r_T": float(numpy.nanmean(statistics[:, 4] > statistics[:, 3])),
                    "median_power_third_over_heart": float(numpy.median(ratios[:, 0] / ratios[:, 2])),
                    "median_power_third_over_background": float(numpy.median(ratios[:, 0] / ratios[:, 3])),
                    "median_power_heart_over_background": float(numpy.median(ratios[:, 2] / ratios[:, 3]))}
        numbers[record_name] = record_numbers
        period_lags = 60.0 / reference[chosen_end]["reference_bpm"] * ENVELOPE_RATE_HZ
        record = ephnogram.load_record(record_name)
        beat_times = numpy.array(json.loads((common.REFERENCE_DIRECTORY / f"{record_name}.json").read_text())["beat_times_s"])
        del record
        envelope_axis, correlation_axis = axes[row_index]
        time_axis = numpy.arange(WINDOW_LENGTH) / ENVELOPE_RATE_HZ + chosen_end - 8
        for label, colour, name in (("model_final", "#88c0d0", "through the modelled device"),
                                    ("resample_only_final", "#ebcb8b", "sound only resampled")):
            window = window_at(envelopes[label], chosen_end)
            envelope_axis.plot(time_axis, window / window.max(), color=colour, linewidth=1.1, label=name)
            correlation = normalised(window)
            correlation_axis.plot(numpy.arange(402) / ENVELOPE_RATE_HZ, correlation, color=colour, linewidth=1.3, label=name)
        in_window = beat_times[(beat_times >= chosen_end - 8) & (beat_times <= chosen_end)]
        for beat_index, beat_time in enumerate(in_window):
            envelope_axis.axvline(beat_time, color="#bf616a", linewidth=0.8, alpha=0.9 if beat_index % 3 == 0 else 0.35)
        for multiple, colour in ((1, "#a3be8c"), (2, "#b48ead"), (3, "#bf616a")):
            correlation_axis.axvline(multiple * period_lags / ENVELOPE_RATE_HZ, color=colour, linestyle="--", linewidth=1.2,
                                     label=f"{multiple} x beat spacing from ECG")
        correlation_axis.axvspan(0, 0.3, color="#3b4252", alpha=0.6)
        correlation_axis.axvspan(2.0, 4.02, color="#3b4252", alpha=0.6)
        envelope_axis.set_title(f"{info.subject_id}, {info.scenario}, window ending at {chosen_end} s: "
                                f"ECG {reference[chosen_end]['reference_bpm']:.0f} BPM, device {types[chosen_end][1]:.0f} BPM",
                                fontsize=9.5, loc="left", color=FOREGROUND)
        envelope_axis.set_xlabel("record time (s); red lines = ECG beats, every third one stronger")
        envelope_axis.set_ylabel("loudness envelope (scaled)")
        correlation_axis.set_xlabel("shift (s); grey = outside 30-200 BPM")
        correlation_axis.set_ylabel("self-similarity")
        for axis in (envelope_axis, correlation_axis):
            style_axis(axis)
        if row_index == 0:
            envelope_axis.legend(fontsize=8, facecolor=BACKGROUND, labelcolor=FOREGROUND, loc="upper right")
            correlation_axis.legend(fontsize=8, facecolor=BACKGROUND, labelcolor=FOREGROUND, loc="upper right")
        spectrum_axis = spectrum_axes[row_index]
        segment = envelopes["model_final"][int((chosen_end - 32) * ENVELOPE_RATE_HZ):int(chosen_end * ENVELOPE_RATE_HZ)].astype(numpy.float64)
        frequencies, power = signal.welch(segment - segment.mean(), fs=ENVELOPE_RATE_HZ, nperseg=1600, noverlap=1200)
        heart_hz = reference[chosen_end]["reference_bpm"] / 60.0
        spectrum_axis.semilogy(frequencies * 60, power, color="#88c0d0", linewidth=1.2)
        for multiple, colour, name in ((1 / 3, "#bf616a", "one third"), (2 / 3, "#b48ead", "two thirds"), (1, "#a3be8c", "heart rate"),
                                       (2, "#a3be8c", "twice")):
            spectrum_axis.axvline(heart_hz * multiple * 60, color=colour, linestyle="--", linewidth=1, label=name)
        spectrum_axis.set_xlim(0, 420)
        spectrum_axis.set_xlabel("repetition rate (per minute)")
        spectrum_axis.set_ylabel("envelope power")
        spectrum_axis.set_title(f"{info.subject_id}: 32 s up to {chosen_end} s", fontsize=9.5, loc="left", color=FOREGROUND)
        style_axis(spectrum_axis)
        if row_index == 0:
            spectrum_axis.legend(fontsize=8, facecolor=BACKGROUND, labelcolor=FOREGROUND)
    figure.tight_layout()
    figure.savefig(FIGURES_DIRECTORY / "one_third_envelope_and_correlation.png", dpi=110, facecolor=BACKGROUND)
    spectrum_figure.tight_layout()
    spectrum_figure.savefig(FIGURES_DIRECTORY / "one_third_envelope_spectrum.png", dpi=110, facecolor=BACKGROUND)
    (common.RESULTS_DIRECTORY / "one_third_diagnosis_numbers.json").write_text(json.dumps(numbers, indent=1), encoding="utf-8")
    print(json.dumps(numbers, indent=1))


if __name__ == "__main__":
    main()
