# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "scipy>=1.14"]
# ///
"""Band levels of raw recordings, side by side.

Usage: compare_room_noise_clips.py <raw recording>...
"""
import sys
import wave

import numpy
from scipy import signal

FULL_SCALE = 2**23
BANDS_HZ = ((20, 50), (50, 100), (100, 200), (200, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000))
SKIPPED_SECONDS = 1

levels = {}
for path in sys.argv[1:]:
    with wave.open(path) as recording:
        rate = recording.getframerate()
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
    samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / FULL_SCALE
    frequencies, density = signal.welch(samples[SKIPPED_SECONDS * rate:], rate, nperseg=8192)
    step = frequencies[1] - frequencies[0]
    levels[path.replace("\\", "/").split("/")[-1][:2]] = [
        10 * numpy.log10(density[(frequencies >= low) & (frequencies < high)].sum() * step) for low, high in BANDS_HZ]
print("band Hz      " + "".join(f"{name:>9}" for name in levels))
for index, (low, high) in enumerate(BANDS_HZ):
    print(f"{low:>5}-{high:<6}" + "".join(f"{values[index]:9.1f}" for values in levels.values()))
