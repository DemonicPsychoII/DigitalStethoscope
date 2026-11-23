"""Remove everything below a cut-off from a raw 24-bit recording and write a 16-bit listening file."""
import sys
import wave

import numpy
from scipy import signal

source, target, cutoff_hz = sys.argv[1], sys.argv[2], float(sys.argv[3])
with wave.open(source) as recording:
    rate = recording.getframerate()
    raw = numpy.frombuffer(recording.readframes(recording.getnframes()), numpy.uint8).reshape(-1, 3).astype(numpy.int32)
samples = (((raw[:, 0] | raw[:, 1] << 8 | raw[:, 2] << 16) ^ 0x800000) - 0x800000) / 2**23

at_limit = numpy.abs(samples) >= 0.9999
# Zero-phase filtering keeps the heart sounds where they are in time.
filter_sections = signal.butter(4, cutoff_hz, "highpass", fs=rate, output="sos")
filtered = signal.sosfiltfilt(filter_sections, samples)

# The first half second holds the button click.
settled = filtered[rate // 2:]
peak = numpy.abs(settled).max()
rms = settled.std()
gain = 0.9 / peak
print(f"{source.split('/')[-1]}: before filter peak {20 * numpy.log10(numpy.abs(samples).max()):.1f} dBFS, "
      f"at the microphone limit {100 * at_limit.mean():.2f} % of the time")
print(f"  after {cutoff_hz:g} Hz high-pass: peak {20 * numpy.log10(peak):.1f} dBFS, RMS {20 * numpy.log10(rms):.1f} dBFS, "
      f"gain applied for listening {20 * numpy.log10(gain):.1f} dB")
listening = numpy.clip(numpy.concatenate([numpy.zeros(rate // 2), settled * gain]), -1, 1)
with wave.open(target, "wb") as output:
    output.setnchannels(1)
    output.setsampwidth(2)
    output.setframerate(rate)
    output.writeframes((listening * 32767).astype("<i2").tobytes())
