"""Undo the one-bit shift and wrap-around of a raw recording, report true levels, write a listening file and a picture."""
import sys
import wave

import numpy
from matplotlib import pyplot

source, listening_path, picture_path = sys.argv[1:4]
with wave.open(source) as recording:
    rate = recording.getframerate()
    raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int64)
shifted = ((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000
step = (numpy.diff(shifted) + 2**23) % 2**24 - 2**23
unwrapped = numpy.concatenate(([shifted[0]], shifted[0] + numpy.cumsum(step)))
true_signal = unwrapped / 2 / 2**23

print("raw samples exactly 0:", int((shifted == 0).sum()), "| exactly -2:", int((shifted == -2).sum()))
print("true signal min %.4f max %.4f of microphone full scale" % (true_signal.min(), true_signal.max()))
at_limit = numpy.abs(true_signal) >= 0.9999
print("time at the microphone limit: %.1f %% (%d samples)" % (100 * at_limit.mean(), at_limit.sum()))
print("time above half of full scale (where the shifted data wraps): %.1f %%" % (100 * (numpy.abs(true_signal) >= 0.5).mean()))
centred = true_signal - true_signal.mean()
print("true RMS %.1f dBFS, about %.0f dB SPL (full-scale sine = 120 dB SPL)"
      % (20 * numpy.log10(centred.std()), 123 + 20 * numpy.log10(centred.std())))
spectrum = numpy.fft.rfft(centred)
frequency = numpy.fft.rfftfreq(len(centred), 1 / rate)
for low in (20, 50, 100):
    kept = spectrum.copy()
    kept[frequency < low] = 0
    band = numpy.fft.irfft(kept, len(centred))
    print("  above %3d Hz only: RMS %.1f dBFS, peak %.1f dBFS" % (low, 20 * numpy.log10(band.std()), 20 * numpy.log10(numpy.abs(band).max())))

kept = spectrum.copy()
kept[frequency < 20] = 0
audible = numpy.fft.irfft(kept, len(centred))
with wave.open(listening_path, "wb") as listening:
    listening.setnchannels(1)
    listening.setsampwidth(2)
    listening.setframerate(rate)
    listening.writeframes((numpy.clip(audible / numpy.abs(audible).max() * 0.9, -1, 1) * 32767).astype("<i2").tobytes())

background, panel, text, grid = "#0f1115", "#161a22", "#d7dce5", "#2a303c"
pyplot.rcParams.update({"figure.facecolor": background, "axes.facecolor": panel, "axes.edgecolor": grid, "text.color": text,
                        "axes.labelcolor": text, "xtick.color": text, "ytick.color": text, "grid.color": grid, "font.size": 10})
figure, axes = pyplot.subplots(3, 1, figsize=(12, 9.5), constrained_layout=True)
time = numpy.arange(len(shifted)) / rate
window = (time >= 3.0) & (time < 3.6)


def mark_limits(axis):
    axis.axhspan(-0.5, 0.5, color="#3ecf8e", alpha=0.10)
    for limit in (-1, 1):
        axis.axhline(limit, color="#ff6b6b", linewidth=1)


axes[0].plot(time, true_signal, color="#5b8def", linewidth=0.5)
mark_limits(axes[0])
axes[0].set(title="Whole 15 s, reconstructed true microphone signal (red: microphone limit, green: range the firmware passes correctly)",
            xlabel="Time (s)", ylabel="Share of microphone full scale", xlim=(0, 15), ylim=(-1.1, 1.1))
axes[1].plot(time[window], shifted[window] / 2**23, color="#ff9f43", linewidth=0.8)
axes[1].set(title="0.6 s as the firmware delivers it, which is what you hear: jumps from one limit to the other",
            xlabel="Time (s)", ylabel="Share of 24-bit range", ylim=(-1.1, 1.1))
axes[2].plot(time[window], true_signal[window], color="#5b8def", linewidth=0.8)
mark_limits(axes[2])
axes[2].set(title="The same 0.6 s reconstructed: a smooth low-frequency swing",
            xlabel="Time (s)", ylabel="Share of microphone full scale", ylim=(-1.1, 1.1))
for axis in axes:
    axis.grid(True, linewidth=0.5)
figure.savefig(picture_path, dpi=110)
