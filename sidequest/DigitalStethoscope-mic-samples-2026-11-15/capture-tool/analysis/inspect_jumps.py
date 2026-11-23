"""Look at the fast jumps in a raw recording: size, direction, spacing, what precedes them and how the signal decays after them.

Usage: inspect_jumps.py <picture> <raw recording>
"""
import sys
import wave

import matplotlib

matplotlib.use("Agg")
import numpy
from matplotlib import pyplot
from scipy import optimize, signal

FULL_SCALE = 2**23
JUMP_WINDOW_SECONDS = 0.004
JUMP_SIZE = 0.3
BACKGROUND, PANEL, TEXT, GRID = "#0f1419", "#161c24", "#d7dde5", "#2a3340"

picture, path = sys.argv[1], sys.argv[2]
with wave.open(path) as recording:
    rate = recording.getframerate()
    raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / FULL_SCALE
window = int(JUMP_WINDOW_SECONDS * rate)
change = samples[window:] - samples[:-window]
candidates = numpy.flatnonzero(numpy.abs(change) >= JUMP_SIZE)
jumps = []
for index in candidates:
    if not jumps or index - jumps[-1][-1] > rate // 50:
        jumps.append([index, index])
    else:
        jumps[-1][-1] = index
print("====", path.replace("\\", "/").split("/")[-1])
print(f"jumps of at least {JUMP_SIZE} of the range within {JUMP_WINDOW_SECONDS * 1000:.0f} ms: {len(jumps)}")
rows = []
for start, end in jumps:
    centre = start + int(numpy.argmax(numpy.abs(change[start:end + 1])))
    before = samples[max(centre - 2, 0)]
    after_start = centre + window + 2
    after = samples[min(after_start, len(samples) - 1)]
    slope = numpy.abs(numpy.diff(samples[centre:centre + window + 1])).max()
    rows.append((centre / rate, before, after, slope, after_start))
rows = numpy.array(rows)
if len(rows):
    times, before, after, slope = rows[:, 0], rows[:, 1], rows[:, 2], rows[:, 3]
    up = after > before
    print(f"  upward {up.sum()}, downward {(~up).sum()}; value before: median {numpy.median(numpy.abs(before)):.2f}, "
          f"10th-90th percentile {numpy.percentile(numpy.abs(before), 10):.2f}-{numpy.percentile(numpy.abs(before), 90):.2f}")
    print(f"  value after: median {numpy.median(numpy.abs(after)):.2f}; size: median {numpy.median(numpy.abs(after - before)):.2f}, "
          f"largest {numpy.abs(after - before).max():.2f}; steepest single step inside a jump: median {numpy.median(slope):.3f}, largest {slope.max():.3f}")
    print(f"  jump moves away from zero in {100 * numpy.mean(numpy.abs(after) > numpy.abs(before)):.0f} % of cases; "
          f"sign flips across the jump in {100 * numpy.mean(numpy.sign(after) != numpy.sign(before)):.0f} %")
    gaps = numpy.diff(times)
    print(f"  spacing: median {numpy.median(gaps) * 1000:.0f} ms, 10th-90th percentile {numpy.percentile(gaps, 10) * 1000:.0f}-"
          f"{numpy.percentile(gaps, 90) * 1000:.0f} ms, variation {100 * gaps.std() / gaps.mean():.0f} %")
    constants = []
    for (_, _, _, _, after_start), next_time in zip(rows[:-1], times[1:]):
        first = int(after_start)
        last = int(next_time * rate) - window
        if last - first < rate // 50:
            continue
        part = samples[first:last]
        axis = numpy.arange(len(part)) / rate
        try:
            fitted, _ = optimize.curve_fit(lambda t, a, tau, c: a * numpy.exp(-t / tau) + c, axis, part,
                                           p0=(part[0] - part[-1], 0.03, part[-1]), maxfev=4000)
        except RuntimeError:
            continue
        residual = part - (fitted[0] * numpy.exp(-axis / fitted[1]) + fitted[2])
        if 0.001 < fitted[1] < 1 and residual.std() < 0.1 * abs(fitted[0]):
            constants.append((fitted[1], fitted[2]))
    if constants:
        constants = numpy.array(constants)
        print(f"  decay after a jump fits one exponential in {len(constants)} of {len(rows) - 1} cases: time constant median "
              f"{numpy.median(constants[:, 0]) * 1000:.0f} ms (10th-90th percentile {numpy.percentile(constants[:, 0], 10) * 1000:.0f}-"
              f"{numpy.percentile(constants[:, 0], 90) * 1000:.0f} ms), equal to a high-pass corner of "
              f"{1 / (2 * numpy.pi * numpy.median(constants[:, 0])):.1f} Hz; it settles towards {numpy.median(constants[:, 1]):+.2f}")

high = signal.sosfiltfilt(signal.butter(4, 1000, "highpass", fs=rate, output="sos"), samples)
block = rate // 50
noise = 20 * numpy.log10(numpy.sqrt(numpy.mean(high[: len(high) // block * block].reshape(-1, block) ** 2, axis=1)) + 1e-12)
level = numpy.abs(samples[: len(samples) // block * block].reshape(-1, block)).mean(axis=1)
print("  content above 1 kHz in 20 ms blocks, by where the signal sits:")
for low, top in ((0, 0.1), (0.1, 0.3), (0.3, 0.6), (0.6, 0.9), (0.9, 1.01)):
    inside = (level >= low) & (level < top)
    if inside.any():
        print(f"    signal at {low:.1f}-{min(top, 1):.1f} of the range ({100 * inside.mean():4.1f} % of the time): median {numpy.median(noise[inside]):6.1f} dBFS, "
              f"muted (below -100 dBFS) in {100 * numpy.mean(noise[inside] < -100):3.0f} %")

centre_time = rows[len(rows) // 2, 0] if len(rows) else 7.0
figure, axes = pyplot.subplots(3, 1, figsize=(12, 10), constrained_layout=True, facecolor=BACKGROUND)
for axis, (span, title) in zip(axes, ((None, "whole clip"), (1.0, "1 s"), (0.12, "120 ms around one jump"))):
    first = 0 if span is None else max(int((centre_time - span / 2) * rate), 0)
    last = len(samples) if span is None else int((centre_time + span / 2) * rate)
    axis.set_facecolor(PANEL)
    axis.plot(numpy.arange(first, last) / rate, samples[first:last], color="#7aa2f7", linewidth=0.7,
              marker="." if span == 0.12 else None, markersize=3)
    for edge in (-1, 1):
        axis.axhline(edge, color="#f7768e", linewidth=0.8, linestyle="--")
    axis.set_title(f"Raw samples, {title}", color=TEXT)
    axis.set_ylabel("Share of the range", color=TEXT)
    axis.tick_params(colors=TEXT)
    axis.grid(color=GRID, linewidth=0.5)
    for spine in axis.spines.values():
        spine.set_color(GRID)
axes[-1].set_xlabel("Time (s)", color=TEXT)
figure.savefig(picture, dpi=100, facecolor=BACKGROUND)
print("  picture:", picture)
