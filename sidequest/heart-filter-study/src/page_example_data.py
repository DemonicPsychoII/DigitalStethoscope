"""Generate synthetic example data for the page generator: lub-dub WAVs, a sample index, a figure and a CSV.

Usage: python src/page_example_data.py   (writes page/example-data/)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import soundfile
from scipy import signal

STUDY_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_FOLDER = STUDY_ROOT / "page" / "example-data"
SAMPLE_RATE = 16000
DURATION_SECONDS = 5.0
DEVICE_GAIN_DB = 12.0
MATCHED_TARGET_RMS_DB = -27.0

EXCERPTS = {"resting": {"heart_rate_bpm": 68, "seed": 1, "beat_amplitude": 0.22},
            "after-exercise": {"heart_rate_bpm": 112, "seed": 2, "beat_amplitude": 0.4}}
FILTERS = {
    "raw": ("Raw (no filter)", None),
    "butterworth_hp2_25_lp2_150": ("Band-pass 25–150 Hz (Butterworth)", signal.butter(2, [25, 150], "bandpass", fs=SAMPLE_RATE, output="sos")),
    "bell_lp2_100": ("Bell mode, low-pass 100 Hz", signal.butter(2, 100, "lowpass", fs=SAMPLE_RATE, output="sos")),
}


def heart_sound(length_seconds: float, frequency: float, amplitude: float, rng) -> np.ndarray:
    time = np.arange(int(length_seconds * SAMPLE_RATE)) / SAMPLE_RATE
    envelope = np.sin(np.pi * time / length_seconds) ** 2 * np.exp(-time / (length_seconds / 2.5))
    phase = rng.uniform(0, 2 * np.pi)
    tone = np.sin(2 * np.pi * frequency * time + phase) + 0.35 * np.sin(2 * np.pi * 2.3 * frequency * time + phase)
    return amplitude * envelope * tone


def synthesize_excerpt(heart_rate_bpm: float, seed: int, beat_amplitude: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sample_count = int(DURATION_SECONDS * SAMPLE_RATE)
    output = np.zeros(sample_count)
    period = 60.0 / heart_rate_bpm
    for beat_start in np.arange(0.15, DURATION_SECONDS - 0.3, period):
        for offset, frequency, length, relative_amplitude in ((0.0, 48, 0.1, 1.0), (0.3 * period + 0.08, 70, 0.075, 0.7)):
            sound = heart_sound(length, frequency * rng.uniform(0.92, 1.08), beat_amplitude * relative_amplitude, rng)
            start = int((beat_start + offset) * SAMPLE_RATE)
            end = min(sample_count, start + len(sound))
            output[start:end] += sound[: end - start]
    rumble = signal.sosfilt(signal.butter(2, 12, "lowpass", fs=SAMPLE_RATE, output="sos"), rng.normal(0, 1, sample_count))
    output += 0.12 * rumble / np.max(np.abs(rumble))
    output += 0.012 * np.sin(2 * np.pi * 50 * np.arange(sample_count) / SAMPLE_RATE)
    output += 0.004 * rng.normal(0, 1, sample_count)
    return output


def level_db(samples: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt(np.mean(samples ** 2)) + 1e-12))


def peak_dbfs(samples: np.ndarray) -> float:
    return float(20 * np.log10(np.max(np.abs(samples)) + 1e-12))


def apply_filter(samples: np.ndarray, sos) -> np.ndarray:
    return samples if sos is None else signal.sosfilt(sos, samples)


def write_sample(excerpt: str, variant: str, identifier: str, samples: np.ndarray) -> tuple[str, str]:
    file_relative = Path("page", "example-data", "listening", "samples", excerpt, variant, identifier + ".wav")
    web_relative = Path("page", "example-data", "listening", "samples_web", excerpt, variant, identifier + ".wav")
    for relative, subtype in ((file_relative, "PCM_24"), (web_relative, "PCM_16")):
        path = STUDY_ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        soundfile.write(path, samples, SAMPLE_RATE, subtype=subtype)
    return file_relative.as_posix(), web_relative.as_posix()


def build_samples() -> list[dict]:
    filtered = {excerpt: {identifier: apply_filter(synthesize_excerpt(**settings), sos) for identifier, (_, sos) in FILTERS.items()}
                for excerpt, settings in EXCERPTS.items()}
    fixed_gain_db = {identifier: min(-1.0 - peak_dbfs(filtered[excerpt][identifier]) for excerpt in EXCERPTS) for identifier in FILTERS}
    entries = []
    for excerpt in EXCERPTS:
        for variant in ("device", "madeup", "matched"):
            for identifier, (label, _) in FILTERS.items():
                source = filtered[excerpt][identifier]
                gain_db = {"device": DEVICE_GAIN_DB, "madeup": fixed_gain_db[identifier],
                           "matched": MATCHED_TARGET_RMS_DB - level_db(source)}[variant]
                amplified = source * 10 ** (gain_db / 20)
                clipped_samples = int(np.count_nonzero(np.abs(amplified) >= 1.0))
                output = np.clip(amplified, -1.0, 1.0)
                file_path, web_path = write_sample(excerpt, variant, identifier, output)
                level = level_db(output)
                entry = {
                    "excerpt": excerpt, "variant": variant,
                    "applied_gain_db": round(gain_db, 2), "output_peak_dbfs": round(peak_dbfs(output), 2),
                    "clipped_samples": clipped_samples,
                    "a_weighted_level_db": round(level - 3.1, 1), "k_weighted_level_lufs": round(level - 0.7, 1),
                    "file": file_path, "web_file": web_path,
                }
                if excerpt == "after-exercise":
                    entry["candidate_identifier"], entry["candidate_label"] = identifier, label
                else:
                    entry["identifier"], entry["label"] = identifier, label
                if identifier == "bell_lp2_100" and variant == "device":
                    del entry["k_weighted_level_lufs"]
                entries.append(entry)
    return entries


def build_figure():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colours = {"text": "#cdd5d5", "muted": "#96a3a4", "grid": "#192021", "background": "#0b0f10"}
    figure, axis = plt.subplots(figsize=(10, 4.6), dpi=150)
    figure.patch.set_facecolor(colours["background"])
    axis.set_facecolor(colours["background"])
    frequencies = np.geomspace(5, 2000, 600)
    for (identifier, (label, sos)), colour in zip(FILTERS.items(), ("#96a3a4", "#52c7b4", "#f2c14e")):
        if sos is None:
            response_db = np.zeros_like(frequencies)
        else:
            _, response = signal.sosfreqz(sos, worN=frequencies, fs=SAMPLE_RATE)
            response_db = 20 * np.log10(np.abs(response) + 1e-9)
        axis.semilogx(frequencies, response_db, color=colour, linewidth=2, label=label)
    axis.set_ylim(-40, 5)
    axis.set_xlabel("Frequency (Hz)", color=colours["text"])
    axis.set_ylabel("Gain (dB)", color=colours["text"])
    axis.set_title("Example: magnitude response of the candidate filters", color=colours["text"])
    axis.grid(True, which="both", color=colours["grid"])
    axis.tick_params(colors=colours["muted"])
    for spine in axis.spines.values():
        spine.set_color(colours["grid"])
    legend = axis.legend(facecolor=colours["background"], edgecolor=colours["grid"])
    for text in legend.get_texts():
        text.set_color(colours["text"])
    figure.tight_layout()
    path = EXAMPLE_FOLDER / "figures" / "example-filter-response.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, facecolor=colours["background"])
    plt.close(figure)


def build_csv():
    rows = [
        ("raw", "Raw (no filter)", 9.84, 0.712, 0),
        ("butterworth_hp2_25_lp2_150", "Band-pass 25–150 Hz (Butterworth)", 1.912, 0.981, 4),
        ("bell_lp2_100", "Bell mode, low-pass 100 Hz", 3.455, 0.934, 3),
        ("butterworth_hp4_20_lp4_200", "Band-pass 20–200 Hz, 4th order", 2.207, 0.966, 7),
        ("bessel_hp2_30_lp2_120", "Band-pass 30–120 Hz (Bessel)", 2.631, 0.952, 2),
        ("chebyshev_hp2_25_lp2_180", "Band-pass 25–180 Hz (Chebyshev)", 12.3456, 0.901, 5),
    ]
    path = EXAMPLE_FOLDER / "filter-results.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["identifier", "label", "mean_absolute_error_bpm", "detection_rate", "latency_ms"])
        writer.writerows(rows)


def main():
    EXAMPLE_FOLDER.mkdir(parents=True, exist_ok=True)
    entries = build_samples()
    (EXAMPLE_FOLDER / "index.json").write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    build_figure()
    build_csv()
    print(f"Example data written to {EXAMPLE_FOLDER}: {len(entries)} samples, 1 figure, 1 CSV")


if __name__ == "__main__":
    main()
