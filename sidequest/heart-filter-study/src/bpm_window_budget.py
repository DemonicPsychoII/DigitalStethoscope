"""Device budget ESTIMATE for the whole-window BPM methods on the ESP32-S3 (240 MHz), not measured on the target.

Usage: python -I src/bpm_window_budget.py   -> results-window/device_budget.csv
Cost assumptions are those of run 1 (src/bpm_evaluate.py): 4 cycles per filter multiplication, 2 per correlation
multiplication, 60 per logarithm. The ESP-DSP benchmark figures come from the repository's thesis material
(thesis-material/03-grundlagen-technisch/04-dsp-filter.md, lines 18 and 26, marked there as still to be checked
against the original table): dsps_biquad_f32 17,552 cycles per 1,024 values, dsps_fft2r_fc32 97,847 cycles for 1,024
complex points. Larger FFTs are scaled by N log2 N from that figure (assumption). Exponential and square root are
assumed to cost as much as a logarithm (60 cycles, assumption). PSRAM access penalty: unknown, not measured.
"""
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpm_evaluate
from hfs.recordings import STUDY_DIRECTORY

RESULTS_DIRECTORY = STUDY_DIRECTORY / "results-window"
CLOCK_HZ = bpm_evaluate.ESP32_CLOCK_HZ
CYCLES_PER_FILTER_MULTIPLY = bpm_evaluate.CYCLES_PER_FILTER_MULTIPLY
CYCLES_PER_CORRELATION_MULTIPLY = bpm_evaluate.CYCLES_PER_CORRELATION_MULTIPLY
CYCLES_PER_LOGARITHM = bpm_evaluate.CYCLES_PER_LOGARITHM
CYCLES_PER_EXPONENTIAL_OR_SQUARE_ROOT = CYCLES_PER_LOGARITHM
BIQUAD_CYCLES_PER_VALUE = 17552 / 1024
FFT_CYCLES_1024_COMPLEX = 97847
MULTIPLIES_PER_SECTION = 5
BLOCK_SECONDS = 64 / 16000
AUTOCORRELATION_MULTIPLIES_800 = 240199
ENVELOPE_RATE_HZ = 100
FLOAT_BYTES = 4


def fft_cycles(point_count):
    return FFT_CYCLES_1024_COMPLEX * (point_count * math.log2(point_count)) / (1024 * 10)


def autocorrelation_multiplies(length, lag_count):
    return length * lag_count - lag_count * (lag_count + 1) // 2


def zero_phase_row(key, label, rate_hz, sections, passes, envelope_passes, padding, window_seconds_stored, continuous_cycles,
                   continuous_text, extra_psram_bytes=0):
    samples = int(rate_hz * 8)
    filter_multiplies = (samples + 2 * padding) * sections * passes * MULTIPLIES_PER_SECTION
    envelope_multiplies = samples * envelope_passes
    filter_cycles = filter_multiplies * CYCLES_PER_FILTER_MULTIPLY
    filter_cycles_benchmark = (samples + 2 * padding) * sections * passes * BIQUAD_CYCLES_PER_VALUE
    correlation_cycles = AUTOCORRELATION_MULTIPLIES_800 * CYCLES_PER_CORRELATION_MULTIPLY
    per_update = filter_cycles + envelope_multiplies * CYCLES_PER_FILTER_MULTIPLY + correlation_cycles
    window_bytes = int(rate_hz * window_seconds_stored) * FLOAT_BYTES
    return {"method": key, "description": label, "window_input_rate_hz": rate_hz,
            "filter_multiplies_per_update": filter_multiplies, "envelope_multiplies_per_update": envelope_multiplies,
            "autocorrelation_multiplies_per_update": AUTOCORRELATION_MULTIPLIES_800, "logarithms_per_update": 0,
            "fft_per_update": "", "per_update_cycles": per_update,
            "per_update_cycles_with_esp_dsp_biquad_figure": per_update - filter_cycles + filter_cycles_benchmark,
            "continuous_cycles_per_second": continuous_cycles, "continuous_work": continuous_text,
            "psram_bytes": window_bytes + extra_psram_bytes, "internal_ram_bytes": 3 * 800 * FLOAT_BYTES + 1024}


def build_rows():
    causal_continuous = 16000 * (10 + 2) * CYCLES_PER_FILTER_MULTIPLY
    rows = [{
        "method": "causal_40_150", "description": "run 1 causal method (baseline): 2+2 Butterworth per block, two one-pole "
        "low-passes, 800 envelope values, autocorrelation once per second",
        "window_input_rate_hz": 100, "filter_multiplies_per_update": 0, "envelope_multiplies_per_update": 0,
        "autocorrelation_multiplies_per_update": AUTOCORRELATION_MULTIPLIES_800, "logarithms_per_update": 0, "fft_per_update": "",
        "per_update_cycles": AUTOCORRELATION_MULTIPLIES_800 * CYCLES_PER_CORRELATION_MULTIPLY,
        "per_update_cycles_with_esp_dsp_biquad_figure": AUTOCORRELATION_MULTIPLIES_800 * CYCLES_PER_CORRELATION_MULTIPLY,
        "continuous_cycles_per_second": causal_continuous,
        "continuous_work": "band-pass 10 and envelope 2 multiplications per sample at 16 kHz",
        "psram_bytes": 0, "internal_ram_bytes": 800 * FLOAT_BYTES * 2 + 1024}]
    rows.append({**rows[0], "method": "causal_40_150_twice",
                 "description": "run 1 causal method with the 2+2 band-pass sections run twice in a row while recording "
                 "(the magnitude of the forward-backward filter, with doubled delay)",
                 "continuous_cycles_per_second": 16000 * (20 + 2) * CYCLES_PER_FILTER_MULTIPLY,
                 "continuous_work": "band-pass 20 and envelope 2 multiplications per sample at 16 kHz"})
    stored_continuous = causal_continuous
    rows.append({**rows[0], "method": "stored_envelope_smooth5hz_taper0",
                 "description": "run 1 causal chain; the 800 stored values smoothed forward and backward at 5 Hz before the autocorrelation",
                 "envelope_multiplies_per_update": 2 * 800,
                 "per_update_cycles": rows[0]["per_update_cycles"] + 2 * 800 * CYCLES_PER_FILTER_MULTIPLY,
                 "per_update_cycles_with_esp_dsp_biquad_figure": rows[0]["per_update_cycles"] + 2 * 800 * CYCLES_PER_FILTER_MULTIPLY,
                 "continuous_cycles_per_second": stored_continuous})
    rows.append({**rows[0], "method": "stored_envelope_nosmooth_taper20",
                 "description": "run 1 causal chain; 20 % cosine taper on the 800 stored values before the autocorrelation",
                 "envelope_multiplies_per_update": 800,
                 "per_update_cycles": rows[0]["per_update_cycles"] + 800 * CYCLES_PER_FILTER_MULTIPLY,
                 "per_update_cycles_with_esp_dsp_biquad_figure": rows[0]["per_update_cycles"] + 800 * CYCLES_PER_FILTER_MULTIPLY})
    raw_window_extra = 128000 * FLOAT_BYTES
    rows.append(zero_phase_row("zero_phase_40_150_order2_reflect_zpenv",
                               "16 kHz raw window, 2+2 Butterworth forward and backward with odd reflection, envelope smoothed forward and backward",
                               16000, 2, 2, 2, 15, 8, 0, "none (raw samples copied into the PSRAM ring)", raw_window_extra))
    rows.append(zero_phase_row("zero_phase_40_150_order1_matched_reflect_zpenv",
                               "16 kHz raw window, 1+1 Butterworth with edges moved for -3 dB after two passes, forward and backward",
                               16000, 2, 2, 2, 9, 8, 0, "none (raw samples copied into the PSRAM ring)", raw_window_extra))
    rows.append(zero_phase_row("streamed_forward_backward_window_40_150_order2_reflect_zpenv",
                               "causal 2+2 filter streamed per block into a 16 kHz PSRAM window; per update only the backward pass",
                               16000, 2, 1, 2, 15, 8, 16000 * 10 * CYCLES_PER_FILTER_MULTIPLY,
                               "band-pass 10 multiplications per sample at 16 kHz"))
    for rate_hz in (1000, 2000):
        anti_alias = 64 * rate_hz * CYCLES_PER_FILTER_MULTIPLY
        rows.append(zero_phase_row(f"reduced_{rate_hz // 1000}k_zero_phase_40_150_order2_reflect_zpenv",
                                   f"64-tap causal anti-alias filter at capture time, {rate_hz} values per second stored; "
                                   "2+2 Butterworth forward and backward on that window",
                                   rate_hz, 2, 2, 2, 15, 8, anti_alias,
                                   f"64-tap anti-alias filter, one output per {16000 // rate_hz} samples", int(rate_hz * 8) * FLOAT_BYTES))
    springer_samples = 8000
    anti_alias = 64 * 1000 * CYCLES_PER_FILTER_MULTIPLY
    band_pass_multiplies = (springer_samples + 2 * 6) * 2 * 2 * MULTIPLIES_PER_SECTION
    hilbert_cycles = 2 * fft_cycles(8192)
    homomorphic_multiplies = springer_samples * 2 * 3 + springer_samples * 2
    transcendental_cycles = springer_samples * (CYCLES_PER_LOGARITHM + 2 * CYCLES_PER_EXPONENTIAL_OR_SQUARE_ROOT)
    spike_removal_cycles = 3 * springer_samples * 2
    correlation_fft_cycles = 2 * fft_cycles(16384) + 16384 * 4 * CYCLES_PER_CORRELATION_MULTIPLY
    springer_update = (band_pass_multiplies + homomorphic_multiplies) * CYCLES_PER_FILTER_MULTIPLY + hilbert_cycles + \
        transcendental_cycles + spike_removal_cycles + correlation_fft_cycles
    springer_buffers = 8192 * 8 + 16384 * 8 + springer_samples * FLOAT_BYTES
    homomorphic_update = (band_pass_multiplies + homomorphic_multiplies) * CYCLES_PER_FILTER_MULTIPLY + hilbert_cycles + \
        transcendental_cycles + AUTOCORRELATION_MULTIPLIES_800 * CYCLES_PER_CORRELATION_MULTIPLY
    rows.append({"method": "reduced_1k_zero_phase_40_150_order2_reflect_homomorphic",
                 "description": "64-tap anti-alias filter at capture time, 1 kHz window; 2+2 Butterworth 40-150 Hz forward and backward; "
                 "homomorphic envelope as Springer (Hilbert transform by FFT, logarithm, 8 Hz low-pass forward and backward, "
                 "exponential); 100 values per second; run 1's autocorrelation and half-rate check",
                 "window_input_rate_hz": 1000, "filter_multiplies_per_update": band_pass_multiplies,
                 "envelope_multiplies_per_update": homomorphic_multiplies,
                 "autocorrelation_multiplies_per_update": AUTOCORRELATION_MULTIPLIES_800,
                 "logarithms_per_update": springer_samples * 3, "fft_per_update": "2 x 8192 complex (Hilbert)",
                 "per_update_cycles": homomorphic_update, "per_update_cycles_with_esp_dsp_biquad_figure": homomorphic_update,
                 "continuous_cycles_per_second": anti_alias, "continuous_work": "64-tap anti-alias filter, one output per 16 samples",
                 "psram_bytes": springer_samples * FLOAT_BYTES, "internal_ram_bytes": 8192 * 8 + springer_samples * FLOAT_BYTES + 3 * 800 * FLOAT_BYTES})
    rows.append({"method": "springer_heart_rate_range_30_200",
                 "description": "Springer reference heart rate on a 1 kHz window: 2+2 Butterworth forward and backward, spike removal, "
                 "homomorphic envelope (Hilbert transform by FFT, logarithm, 8 Hz low-pass forward and backward, exponential), "
                 "autocorrelation by FFT at 1 kHz",
                 "window_input_rate_hz": 1000, "filter_multiplies_per_update": band_pass_multiplies,
                 "envelope_multiplies_per_update": homomorphic_multiplies, "autocorrelation_multiplies_per_update": "by FFT",
                 "logarithms_per_update": springer_samples * 3,
                 "fft_per_update": "2 x 8192 complex (Hilbert), 2 x 16384 complex (autocorrelation); spike removal assumed 3 passes",
                 "per_update_cycles": springer_update, "per_update_cycles_with_esp_dsp_biquad_figure": springer_update,
                 "continuous_cycles_per_second": anti_alias, "continuous_work": "64-tap anti-alias filter, one output per 16 samples",
                 "psram_bytes": springer_samples * FLOAT_BYTES, "internal_ram_bytes": springer_buffers})
    rows.append({**rows[-1], "method": "springer_heart_rate", "description": "as above, reference search range 0.5-2 s (30-120 BPM)"})
    rows.append({**rows[-1], "method": "springer_heart_rate_half_check", "description": "as above, run 1's half-rate check"})
    feature_samples = 400
    spectrogram_complex_multiplies = 21 * 25 * ((springer_samples - 13) // 12)
    combined_update = (band_pass_multiplies + homomorphic_multiplies + 4 * spectrogram_complex_multiplies) * CYCLES_PER_FILTER_MULTIPLY \
        + hilbert_cycles + transcendental_cycles + spike_removal_cycles \
        + 3 * autocorrelation_multiplies(feature_samples, 101) * CYCLES_PER_CORRELATION_MULTIPLY + 3 * feature_samples * 20
    rows.append({"method": "springer_envelopes_combined_50hz_half_check",
                 "description": "Springer homomorphic, Hilbert and 40-60 Hz spectral power envelopes at 50 values per second, "
                 "three autocorrelations averaged, half-rate check",
                 "window_input_rate_hz": 1000, "filter_multiplies_per_update": band_pass_multiplies,
                 "envelope_multiplies_per_update": homomorphic_multiplies + 4 * spectrogram_complex_multiplies,
                 "autocorrelation_multiplies_per_update": 3 * autocorrelation_multiplies(feature_samples, 101),
                 "logarithms_per_update": springer_samples * 3, "fft_per_update": "2 x 8192 complex (Hilbert)",
                 "per_update_cycles": combined_update, "per_update_cycles_with_esp_dsp_biquad_figure": combined_update,
                 "continuous_cycles_per_second": anti_alias, "continuous_work": "64-tap anti-alias filter, one output per 16 samples",
                 "psram_bytes": springer_samples * FLOAT_BYTES, "internal_ram_bytes": 8192 * 8 + springer_samples * FLOAT_BYTES * 2})
    rows.append({**rows[-1], "method": "springer_envelopes_combined_50hz_highest_30_200",
                 "description": "as above, highest peak in 0.3-2 s"})
    for row in rows:
        update_milliseconds = 1000 * row["per_update_cycles"] / CLOCK_HZ
        continuous_share = row["continuous_cycles_per_second"] / CLOCK_HZ
        row["per_update_milliseconds"] = round(update_milliseconds, 3)
        row["per_update_milliseconds_with_esp_dsp_biquad_figure"] = round(1000 * row["per_update_cycles_with_esp_dsp_biquad_figure"] / CLOCK_HZ, 3)
        row["core_share_percent_at_one_update_per_second"] = round(100 * (continuous_share + row["per_update_cycles"] / CLOCK_HZ), 3)
        for limit in (0.10, 0.50):
            available = limit * CLOCK_HZ - row["continuous_cycles_per_second"]
            row[f"maximum_updates_per_second_at_{int(limit * 100)}_percent"] = round(available / row["per_update_cycles"], 1)
        row["blocks_of_4_ms_to_spread_one_update_at_10_percent"] = math.ceil(
            row["per_update_cycles"] / (0.10 * CLOCK_HZ * BLOCK_SECONDS - row["continuous_cycles_per_second"] * BLOCK_SECONDS))
        row["psram_kilobytes"] = round(row["psram_bytes"] / 1024, 1)
        row["internal_ram_kilobytes"] = round(row["internal_ram_bytes"] / 1024, 1)
        row["psram_access_penalty"] = "unknown, not measured" if row["psram_bytes"] else "no PSRAM use"
        row["estimate"] = "estimate, not measured on the target"
    return rows


def main():
    rows = build_rows()
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(name for row in rows for name in row))
    with open(RESULTS_DIRECTORY / "device_budget.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(f"{row['method'][:58]:58s} {row['per_update_milliseconds']:8.2f} ms  {row['core_share_percent_at_one_update_per_second']:6.2f} %  "
              f"10%: {row['maximum_updates_per_second_at_10_percent']:6.1f}/s  50%: {row['maximum_updates_per_second_at_50_percent']:6.1f}/s  "
              f"blocks {row['blocks_of_4_ms_to_spread_one_update_at_10_percent']:4d}  PSRAM {row['psram_kilobytes']:7.1f} kB  RAM {row['internal_ram_kilobytes']:6.1f} kB")


if __name__ == "__main__":
    main()
