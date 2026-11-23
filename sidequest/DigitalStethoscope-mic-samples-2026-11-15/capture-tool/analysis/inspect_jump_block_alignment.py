# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2"]
# ///
"""Check whether the fast jumps in raw recordings sit on the boundaries of the I2S blocks.

Usage: inspect_jump_block_alignment.py <raw recording>...
"""
import sys
import wave

import numpy

FULL_SCALE = 2**23
FRAMES_PER_BLOCK = 128
STEP_SIZE = 0.05
MINIMUM_SPACING_SECONDS = 0.02

for path in sys.argv[1:]:
    with wave.open(path) as recording:
        rate = recording.getframerate()
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
    samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / FULL_SCALE
    steps = numpy.abs(numpy.diff(samples))
    steepest = []
    for index in numpy.flatnonzero(steps >= STEP_SIZE):
        if steepest and index - steepest[-1] < MINIMUM_SPACING_SECONDS * rate:
            if steps[index] > steps[steepest[-1]]:
                steepest[-1] = index
        else:
            steepest.append(index)
    positions = (numpy.array(steepest, dtype=int) + 1) % FRAMES_PER_BLOCK
    print("====", path.replace("\\", "/").split("/")[-1])
    print(f"  single-sample steps of at least {STEP_SIZE} of the range: {len(positions)}")
    if len(positions) == 0:
        continue
    counts = numpy.bincount(positions, minlength=FRAMES_PER_BLOCK)
    expected = len(positions) / FRAMES_PER_BLOCK
    chi_square = ((counts - expected) ** 2 / expected).sum()
    print(f"  most common position inside a block: sample {counts.argmax()} with {counts.max()} steps "
          f"(even spread would give {expected:.1f} per position)")
    print(f"  chi-square against an even spread: {chi_square:.0f} for {FRAMES_PER_BLOCK - 1} degrees of freedom "
          f"(about {FRAMES_PER_BLOCK - 1} means evenly spread)")
    exact_repeats = numpy.flatnonzero(numpy.all(raw[1:] == raw[:-1], axis=1))
    print(f"  samples identical to their predecessor: {len(exact_repeats)}")
