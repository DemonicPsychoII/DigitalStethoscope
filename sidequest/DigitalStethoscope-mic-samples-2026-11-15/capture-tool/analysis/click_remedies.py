"""Relate clicks to signal level and compare remedies: zeroing clipped samples, bridging them, and band-limiting."""
import sys
import wave

import numpy
from scipy import signal

source, stem = sys.argv[1], sys.argv[2]
with wave.open(source) as recording:
    rate = recording.getframerate()
    raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / 2**23
samples = samples[rate // 2:]
at_limit = numpy.abs(samples) >= 0.9999


def sections(kind, frequency):
    return signal.butter(4, frequency, kind, fs=rate, output="sos")


def click_level(candidate):
    """Level of the content above 1 kHz, where only clicks and noise live: 99.9th percentile and RMS."""
    high = signal.sosfiltfilt(sections("highpass", 1000), candidate)
    return 20 * numpy.log10(numpy.percentile(numpy.abs(high), 99.9)), 20 * numpy.log10(high.std())


high = signal.sosfiltfilt(sections("highpass", 1000), samples)
threshold = 12 * numpy.median(numpy.abs(high)) * 1.4826
click_samples = numpy.abs(high) > threshold
print(source.split("/")[-1])
print("share of click samples by signal level (share of all samples at that level in brackets):")
for low, top in ((0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 0.9999), (0.9999, 1.1)):
    in_band = (numpy.abs(samples) >= low) & (numpy.abs(samples) < top)
    print(f"  {low:.2f}-{min(top, 1):.2f} of full scale: {100 * (click_samples & in_band).sum() / click_samples.sum():5.1f} % "
          f"({100 * in_band.mean():5.1f} %), click rate there {100 * (click_samples & in_band).sum() / max(in_band.sum(), 1):.2f} %")

zeroed = numpy.where(at_limit, 0.0, samples)
bridged = samples.copy()
good = numpy.flatnonzero(~at_limit)
# A smooth curve through the neighbours estimates what the microphone would have delivered beyond its limit.
bridged[at_limit] = signal.sosfiltfilt(sections("lowpass", 60), samples)[at_limit] * 0 + numpy.interp(
    numpy.flatnonzero(at_limit), good, samples[good])

candidates = {
    "20 Hz high-pass only": signal.sosfiltfilt(sections("highpass", 20), samples),
    "clipped samples set to 0, then 20 Hz high-pass": signal.sosfiltfilt(sections("highpass", 20), zeroed),
    "20-400 Hz band-pass": signal.sosfiltfilt(sections("lowpass", 400), signal.sosfiltfilt(sections("highpass", 20), samples)),
    "20-200 Hz band-pass": signal.sosfiltfilt(sections("lowpass", 200), signal.sosfiltfilt(sections("highpass", 20), samples)),
}
print("click content above 1 kHz (99.9th percentile / RMS, dBFS):")
for name, candidate in candidates.items():
    percentile, rms = click_level(candidate)
    print(f"  {name}: {percentile:.1f} / {rms:.1f}")

for name, key in (("20-400 Hz band-pass", "bandpass-20-400Hz"), ("20-200 Hz band-pass", "bandpass-20-200Hz"),
                  ("clipped samples set to 0, then 20 Hz high-pass", "clipping-zeroed-highpass-20Hz")):
    candidate = candidates[name]
    listening = numpy.clip(numpy.concatenate([numpy.zeros(rate // 2), candidate * 0.9 / numpy.abs(candidate).max()]), -1, 1)
    with wave.open(f"{stem}-{key}-listen.wav", "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes((listening * 32767).astype("<i2").tobytes())
