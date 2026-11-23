"""Apply listening-filter candidates to raw recordings and compare them by spectrum and by numbers.

Usage: evaluate_filters.py <output directory> <raw recording>...
Per recording: a picture with waveform and spectra, listening files, and one table row per candidate.
"""
import sys
import wave
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy
from matplotlib import pyplot
from scipy import signal

FULL_SCALE = 2**23
FILTER_ORDER = 4
SLOW_BAND_HZ = (1, 20)
HEART_BAND_HZ = (20, 200)
CLICK_BAND_HZ = (1000, 8000)
# The INMP441 data sheet gives a noise floor of -87 dBFS (A-weighted); far below it the microphone is not listening.
MUTE_LEVEL_DBFS = -100
MUTE_WINDOW_SECONDS = 0.02
LISTENING_PEAK = 0.9

BACKGROUND = "#0f1419"
PANEL = "#161c24"
TEXT = "#d7dde5"
GRID = "#2a3340"
COLOURS = ("#8b95a3", "#e0af68", "#7aa2f7", "#9ece6a", "#f7768e", "#bb9af7")


def load(path):
    with wave.open(str(path)) as recording:
        rate = recording.getframerate()
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
    return rate, (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / FULL_SCALE


def sections(kind, frequency, rate):
    return signal.butter(FILTER_ORDER, frequency, kind, fs=rate, output="sos")


def band_pass(samples, rate, low, high, zero_phase=False):
    run = signal.sosfiltfilt if zero_phase else signal.sosfilt
    filtered = run(sections("highpass", low, rate), samples)
    return run(sections("lowpass", high, rate), filtered) if high else filtered


def decibels(value):
    return 20 * numpy.log10(max(float(value), 1e-12))


def band_level(frequencies, density, band):
    inside = (frequencies >= band[0]) & (frequencies < band[1])
    return 10 * numpy.log10(max(numpy.sum(density[inside]) * (frequencies[1] - frequencies[0]), 1e-24))


def muted_share(samples, rate):
    """Share of the time in which the content above 1 kHz is far below the microphone's own noise."""
    high = signal.sosfiltfilt(sections("highpass", CLICK_BAND_HZ[0], rate), samples)
    window = int(MUTE_WINDOW_SECONDS * rate)
    levels = numpy.sqrt(numpy.mean(high[: len(high) // window * window].reshape(-1, window) ** 2, axis=1))
    return float(numpy.mean(20 * numpy.log10(levels + 1e-12) < MUTE_LEVEL_DBFS))


def write_listening(path, samples, rate):
    listening = numpy.clip(samples * LISTENING_PEAK / numpy.abs(samples).max(), -1, 1)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes((listening * 32767).astype("<i2").tobytes())


def evaluate(path, output_directory):
    rate, samples = load(path)
    stem = path.name.removesuffix("-raw.wav")
    # The button press and the filter settling stay out of the numbers.
    skip = rate // 2
    candidates = {
        "Unfiltered (board today)": samples - samples[skip:].mean(),
        "High-pass 20 Hz": band_pass(samples, rate, 20, None),
        "Band-pass 20-400 Hz": band_pass(samples, rate, 20, 400),
        "Band-pass 20-200 Hz": band_pass(samples, rate, 20, 200),
        "Band-pass 40-400 Hz": band_pass(samples, rate, 40, 400),
        "Band-pass 20-400 Hz, forward and backward (PC only)": band_pass(samples, rate, 20, 400, zero_phase=True),
    }
    at_limit = numpy.abs(samples[skip:]) >= 0.9999
    print(f"\n### {stem}\n")
    print(f"Raw signal: at the microphone limit {100 * at_limit.mean():.2f} % of the time, "
          f"microphone muted {100 * muted_share(samples[skip:], rate):.0f} % of the time.\n")
    print("| Filter | Slow swing 1-20 Hz | Heart band 20-200 Hz | Clicks above 1 kHz | Peak | Heart band below peak | Heart band share of energy |")
    print("|---|---|---|---|---|---|---|")

    figure, (waveform_axis, spectrum_axis) = pyplot.subplots(2, 1, figsize=(12, 9), constrained_layout=True, facecolor=BACKGROUND)
    for axis in (waveform_axis, spectrum_axis):
        axis.set_facecolor(PANEL)
        axis.tick_params(colors=TEXT, which="both")
        axis.grid(color=GRID, which="both", linewidth=0.5)
        for spine in axis.spines.values():
            spine.set_color(GRID)
    time_axis = numpy.arange(len(samples) - skip) / rate + skip / rate

    for (name, candidate), colour in zip(candidates.items(), COLOURS):
        settled = candidate[skip:]
        frequencies, density = signal.welch(settled, fs=rate, window="hann", nperseg=16384, noverlap=8192)
        slow = band_level(frequencies, density, SLOW_BAND_HZ)
        heart = band_level(frequencies, density, HEART_BAND_HZ)
        clicks = band_level(frequencies, density, CLICK_BAND_HZ)
        total = band_level(frequencies, density, (SLOW_BAND_HZ[0], rate / 2))
        peak = decibels(numpy.abs(settled).max())
        print(f"| {name} | {slow:.1f} dBFS | {heart:.1f} dBFS | {clicks:.1f} dBFS | {peak:.1f} dBFS | "
              f"{peak - heart:.1f} dB | {100 * 10 ** ((heart - total) / 10):.1f} % |")
        shown = frequencies >= 1
        spectrum_axis.semilogx(frequencies[shown], 10 * numpy.log10(density[shown] + 1e-24), color=colour, linewidth=1.1, label=name)
        if name in ("Unfiltered (board today)", "Band-pass 20-400 Hz"):
            waveform_axis.plot(time_axis, settled, color=colour, linewidth=0.5, label=name)

    for edge in (-1, 1):
        waveform_axis.axhline(edge, color="#f7768e", linewidth=0.8, linestyle="--")
    waveform_axis.set_title(f"{stem}: waveform (dashed: microphone limit)", color=TEXT)
    waveform_axis.set_xlabel("Time (s)", color=TEXT)
    waveform_axis.set_ylabel("Amplitude (full scale = 1)", color=TEXT)
    spectrum_axis.axvspan(*HEART_BAND_HZ, color="#9ece6a", alpha=0.08)
    spectrum_axis.text(HEART_BAND_HZ[0] * 1.1, -22, "heart band", color="#9ece6a")
    spectrum_axis.set_xlim(1, rate / 2)
    spectrum_axis.set_ylim(-150, -15)
    spectrum_axis.set_title("Spectrum of each filter candidate (Welch, Hann, 1 Hz resolution)", color=TEXT)
    spectrum_axis.set_xlabel("Frequency (Hz)", color=TEXT)
    spectrum_axis.set_ylabel("Power density (dBFS per Hz)", color=TEXT)
    for axis in (waveform_axis, spectrum_axis):
        axis.legend(facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT, loc="upper right")
    picture = output_directory / f"{stem}-filter-comparison.png"
    figure.savefig(picture, dpi=110, facecolor=BACKGROUND)
    pyplot.close(figure)

    # Silence instead of the button press, as in the other listening files.
    for name, key in (("Band-pass 20-400 Hz", "bandpass-20-400Hz-one-pass"),
                      ("Band-pass 20-400 Hz, forward and backward (PC only)", "bandpass-20-400Hz")):
        write_listening(output_directory / f"{stem}-{key}-listen.wav",
                        numpy.concatenate([numpy.zeros(skip), candidates[name][skip:]]), rate)
    print(f"\nPicture: {picture.resolve()}")


target = Path(sys.argv[1])
for argument in sys.argv[2:]:
    evaluate(Path(argument), target)
