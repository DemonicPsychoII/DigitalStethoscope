"""Print the level per frequency band for parts of raw recordings, given as path:start_second:end_second."""
import sys
import wave

import numpy
from scipy import signal

BANDS = ((1, 5), (5, 10), (10, 20), (20, 50), (50, 100), (100, 200), (200, 500))
print("part".ljust(44) + "".join(f"{low}-{high} Hz".rjust(11) for low, high in BANDS) + "   at limit  clicks/s")
for argument in sys.argv[1:]:
    path, start, end = argument.rsplit(":", 2)
    with wave.open(path) as recording:
        rate = recording.getframerate()
        raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
    samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / 2**23
    high = signal.sosfiltfilt(signal.butter(4, 1000, "highpass", fs=rate, output="sos"), samples)
    part = slice(int(float(start) * rate), int(float(end) * rate))
    levels = []
    for low, top in BANDS:
        band = signal.sosfiltfilt(signal.butter(3, (low, top), "bandpass", fs=rate, output="sos"), samples)[part]
        levels.append(20 * numpy.log10(band.std()))
    threshold = 12 * numpy.median(numpy.abs(high)) * 1.4826
    click_starts = numpy.flatnonzero(numpy.diff((numpy.abs(high[part]) > threshold).astype(int)) == 1)
    click_count = 1 + int((numpy.diff(click_starts) > rate // 200).sum()) if len(click_starts) else 0
    name = f"{path.split('/')[-1][:24]} {start}-{end} s"
    print(name.ljust(44) + "".join(f"{level:11.1f}" for level in levels)
          + f"   {100 * (numpy.abs(samples[part]) >= 0.9999).mean():6.2f} %  {click_count / (float(end) - float(start)):6.1f}")
