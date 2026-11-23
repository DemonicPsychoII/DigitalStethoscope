"""Measure the noise-free ramps in raw recordings: where they start, how they decay and how they end."""
import sys
import wave

import numpy
from scipy import signal

FULL_SCALE = 2**23
QUIET_SECOND_DIFFERENCE = 6e-6

for path in sys.argv[1:]:
    with wave.open(path) as recording:
        rate = recording.getframerate()
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
    samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / FULL_SCALE
    # A decaying filter output is smooth from sample to sample; sound and microphone noise are not.
    curvature = numpy.abs(numpy.diff(samples, 2))
    smooth = numpy.concatenate(([False], signal.medfilt(curvature, 9) < QUIET_SECOND_DIFFERENCE, [False]))
    edges = numpy.flatnonzero(numpy.diff(smooth.astype(int)))
    starts, ends = edges[::2], edges[1::2]
    keep = (ends - starts) >= rate // 100
    starts, ends = starts[keep], ends[keep]
    print("====", path.replace("\\", "/").split("/")[-1])
    print(f"  normal microphone noise, median sample-to-sample curvature: {numpy.median(curvature) * FULL_SCALE:.0f} LSB")
    print(f"  noise-free ramps of at least 10 ms: {len(starts)}, together {100 * (ends - starts).sum() / len(samples):.1f} % of the clip")
    if not len(starts):
        continue
    durations = (ends - starts) / rate
    first_values = samples[starts + 2]
    last_values = samples[ends - 2]
    at_rail_before = numpy.array([numpy.abs(samples[max(start - rate // 100, 0):start + 3]).max() >= 0.9999 for start in starts])
    constants = []
    for start, end in zip(starts, ends):
        part = samples[start + 2:end - 2]
        if len(part) < rate // 50 or abs(part[0]) < 0.2:
            continue
        slope = numpy.polyfit(numpy.arange(len(part)) / rate, numpy.log(numpy.abs(part)), 1)[0]
        if slope < 0:
            constants.append(-1 / slope)
    print(f"  length: median {numpy.median(durations) * 1000:.0f} ms, longest {durations.max() * 1000:.0f} ms")
    print(f"  the signal was at the limit within 10 ms before the ramp in {100 * at_rail_before.mean():.0f} % of them")
    print(f"  ramp starts at a median of {numpy.median(numpy.abs(first_values)):.2f} of the range and ends at {numpy.median(numpy.abs(last_values)):.2f}; "
          f"it moves towards zero in {100 * numpy.mean(numpy.abs(last_values) < numpy.abs(first_values)):.0f} %")
    if constants:
        constants = numpy.array(constants)
        print(f"  decay towards zero as an exponential: time constant median {numpy.median(constants) * 1000:.0f} ms "
              f"(25th-75th percentile {numpy.percentile(constants, 25) * 1000:.0f}-{numpy.percentile(constants, 75) * 1000:.0f} ms, {len(constants)} ramps), "
              f"equal to a high-pass corner of {1 / (2 * numpy.pi * numpy.median(constants)):.2f} Hz")
    step_at_end = numpy.abs(samples[numpy.minimum(ends + 8, len(samples) - 1)] - samples[ends - 2])
    print(f"  change within 0.6 ms after a ramp ends: median {numpy.median(step_at_end):.3f} of the range, above 0.02 in {100 * numpy.mean(step_at_end > 0.02):.0f} %")
