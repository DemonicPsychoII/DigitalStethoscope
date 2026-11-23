"""Report clipping, level over time and band energies of raw 24-bit microphone recordings."""
import sys
import wave

import numpy

FULL_SCALE = 2**23


def load(path):
    with wave.open(path) as recording:
        rate = recording.getframerate()
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
    samples = ((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000
    return rate, samples


def decibels(value):
    return 20 * numpy.log10(max(value, 1) / FULL_SCALE)


for path in sys.argv[1:]:
    rate, samples = load(path)
    print("====", path.split("/")[-1].split("\\")[-1])
    print(f"raw min {samples.min()} max {samples.max()} (limits {-FULL_SCALE} / {FULL_SCALE - 1}), mean {samples.mean():.0f}")
    for limit in (0.999, 0.98, 0.9):
        at_limit = numpy.abs(samples) >= limit * FULL_SCALE
        print(f"  samples at or above {limit:.3f} of full scale: {at_limit.sum()} ({100 * at_limit.mean():.2f} %)")
    stuck = numpy.diff(samples) == 0
    runs = numpy.diff(numpy.flatnonzero(numpy.diff(numpy.concatenate(([0], stuck.astype(int), [0])))))[::2]
    print(f"  longest run of identical samples: {runs.max() + 1 if len(runs) else 1}")
    jumps = numpy.abs(numpy.diff(samples.astype(numpy.int64)))
    print(f"  sample-to-sample jumps above half of full scale (wrap-around sign): {(jumps > FULL_SCALE // 2).sum()}; largest jump {jumps.max() / FULL_SCALE:.2f} of full scale")
    centred = samples - samples.mean()
    print("  per second: peak dBFS / RMS dBFS / share of samples above 0.98")
    for second in range(len(samples) // rate):
        part = samples[second * rate:(second + 1) * rate]
        part_centred = centred[second * rate:(second + 1) * rate]
        print(f"    {second:2d} s: {decibels(numpy.abs(part).max()):6.1f} / {decibels(numpy.sqrt(numpy.mean(part_centred**2))):6.1f} / {100 * (numpy.abs(part) >= 0.98 * FULL_SCALE).mean():5.1f} %")
    spectrum = numpy.abs(numpy.fft.rfft(centred * numpy.hanning(len(centred))))**2
    frequency = numpy.fft.rfftfreq(len(centred), 1 / rate)
    total = spectrum.sum()
    for low, high in ((0, 5), (5, 20), (20, 50), (50, 100), (100, 200), (200, 500), (500, 1000), (1000, 4000), (4000, 8000)):
        share = spectrum[(frequency >= low) & (frequency < high)].sum() / total
        print(f"  {low:5d}-{high:<5d} Hz: {100 * share:6.2f} % of energy")
    strongest = frequency[numpy.argsort(spectrum)[-8:][::-1]]
    print("  strongest spectral lines (Hz):", ", ".join(f"{value:.1f}" for value in strongest))
