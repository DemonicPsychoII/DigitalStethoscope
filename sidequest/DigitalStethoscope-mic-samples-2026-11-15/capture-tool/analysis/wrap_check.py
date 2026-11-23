import sys, wave, numpy
FULL = 2**24
for path in sys.argv[1:]:
    with wave.open(path) as recording:
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int64)
    samples = ((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000
    print("====", path[-30:])
    print("bit set share, bit0..bit7:", " ".join(f"{((samples >> bit) & 1).mean():.2f}" for bit in range(8)))
    difference = numpy.diff(samples)
    wrapped_difference = (difference + FULL // 2) % FULL - FULL // 2
    unwrapped = numpy.concatenate(([samples[0]], samples[0] + numpy.cumsum(wrapped_difference)))
    print("largest step before unwrap %.2f FS, after unwrap %.3f FS (FS = 2^23)" % (numpy.abs(difference).max() / 2**23, numpy.abs(wrapped_difference).max() / 2**23))
    print("unwrapped range %.2f .. %.2f FS; end drift %.2f FS" % (unwrapped.min() / 2**23, unwrapped.max() / 2**23, (unwrapped[-1] - samples[-1]) / 2**23))
    index = int(numpy.argmax(numpy.abs(difference)))
    print("around the largest jump (raw / FS):", numpy.round(samples[index - 6:index + 8] / 2**23, 3))
    print("same, unwrapped:", numpy.round(unwrapped[index - 6:index + 8] / 2**23, 3))
    wraps = numpy.flatnonzero(numpy.abs(difference) > 2**23)
    print("wrap events:", len(wraps), "| flat runs >= 20 samples:", end=" ")
    flat = numpy.flatnonzero(difference == 0); print(len(flat))
    if len(flat):
        start = flat[0]; print("first flat run values / FS:", numpy.round(samples[start - 3:start + 12] / 2**23, 4))
