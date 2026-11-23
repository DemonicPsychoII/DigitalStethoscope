"""Locate clicks in a raw recording and report whether they coincide with the microphone sitting at its limit."""
import sys
import wave

import numpy
from scipy import signal

path = sys.argv[1]
with wave.open(path) as recording:
    rate = recording.getframerate()
    raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / 2**23
samples = samples[rate // 2:]

at_limit = numpy.abs(samples) >= 0.9999
edges = numpy.flatnonzero(numpy.diff(at_limit.astype(int)))
print(f"{path.split('/')[-1]}: {len(edges) // 2} separate stays at the limit, {100 * at_limit.mean():.2f} % of the time")

# Clicks are broadband; heart sounds and pressure swing have almost nothing above 1 kHz.
high = signal.sosfiltfilt(signal.butter(4, 1000, "highpass", fs=rate, output="sos"), samples)
floor = numpy.median(numpy.abs(high)) * 1.4826
threshold = 12 * floor
print(f"content above 1 kHz: noise floor {20 * numpy.log10(floor):.1f} dBFS, click threshold {20 * numpy.log10(threshold):.1f} dBFS")
hits = numpy.flatnonzero(numpy.abs(high) > threshold)
clicks = []
for index in hits:
    if not clicks or index - clicks[-1][-1] > rate // 200:
        clicks.append([index, index])
    else:
        clicks[-1][-1] = index
near_limit_window = rate // 100
limit_indices = numpy.flatnonzero(at_limit)
near, far = [], []
for start, end in clicks:
    position = numpy.searchsorted(limit_indices, start)
    distances = [abs(limit_indices[k] - start) for k in (position - 1, position) if 0 <= k < len(limit_indices)]
    (near if distances and min(distances) <= near_limit_window else far).append((start, end))
print(f"clicks: {len(clicks)} total, {len(near)} within 10 ms of the microphone limit, {len(far)} elsewhere")
for label, group in (("at the limit", near), ("elsewhere", far)):
    if group:
        peaks = [numpy.abs(high[start:end + 1]).max() for start, end in group]
        print(f"  {label}: strongest {20 * numpy.log10(max(peaks)):.1f} dBFS, median {20 * numpy.log10(numpy.median(peaks)):.1f} dBFS")
for start, end in far[:6]:
    window = samples[max(start - 6, 0):start + 10]
    print(f"  elsewhere at {start / rate + 0.5:.3f} s, value {samples[start]:+.3f}:", numpy.round(window, 3))
steps = numpy.abs(numpy.diff(samples))
print("largest sample-to-sample steps:", numpy.round(numpy.sort(steps)[-5:], 3), "median step", round(float(numpy.median(steps)), 5))
