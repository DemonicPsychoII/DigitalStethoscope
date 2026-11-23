"""Describe the stretches of a raw recording in which the microphone delivers an almost constant value."""
import sys
import wave

import numpy

FULL_SCALE = 2**23
QUIET_STEP = 64

for path in sys.argv[1:]:
    with wave.open(path) as recording:
        rate = recording.getframerate()
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
    samples = ((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000
    steps = numpy.abs(numpy.diff(samples))
    quiet = numpy.concatenate(([False], steps <= QUIET_STEP, [False]))
    edges = numpy.flatnonzero(numpy.diff(quiet.astype(int)))
    starts, ends = edges[::2], edges[1::2]
    lengths = ends - starts
    long_runs = lengths >= rate // 100
    print("====", path.replace("\\", "/").split("/")[-1])
    print(f"  identical neighbours: {100 * (steps == 0).mean():.1f} % of samples; steps of at most {QUIET_STEP} LSB: {100 * (steps <= QUIET_STEP).mean():.1f} %")
    print(f"  stretches of at least 10 ms with steps of at most {QUIET_STEP} LSB: {long_runs.sum()}, "
          f"together {100 * lengths[long_runs].sum() / len(samples):.1f} % of the clip")
    if long_runs.any():
        durations = lengths[long_runs] / rate * 1000
        print(f"  their length: median {numpy.median(durations):.0f} ms, longest {durations.max():.0f} ms")
        values = [samples[start:end + 1] for start, end in zip(starts[long_runs], ends[long_runs])]
        means = numpy.array([part.mean() for part in values])
        spreads = numpy.array([part.std() for part in values])
        print(f"  value held: median {numpy.median(means):.0f} LSB ({numpy.median(means) / FULL_SCALE:+.4f} of full scale), "
              f"range {means.min():.0f} to {means.max():.0f}; noise inside them: median {numpy.median(spreads):.1f} LSB RMS")
        gaps = numpy.diff(starts[long_runs]) / rate
        print(f"  from one stretch to the next: median {numpy.median(gaps) * 1000:.0f} ms ({1 / numpy.median(gaps):.1f} per second)")
        for start, end in list(zip(starts[long_runs], ends[long_runs]))[3:6]:
            before = samples[max(start - 400, 0):start]
            after = samples[end:end + 400]
            print(f"  stretch at {start / rate:.3f}-{end / rate:.3f} s: holds {samples[start]}; "
                  f"before it the signal spans {before.min()} to {before.max()}, after it {after.min()} to {after.max()}")
    print(f"  lowest bit is 1 in {100 * (samples & 1).mean():.1f} % of samples; low byte is 0 in {100 * ((samples & 0xFF) == 0).mean():.1f} %")
