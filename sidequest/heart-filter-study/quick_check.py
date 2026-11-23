"""Quick look at a heart recording: level, clipping, rough BPM from the 20-150 Hz envelope."""

import sys

import numpy as np
import soundfile
from scipy import signal

samples, rate = soundfile.read(sys.argv[1])
samples = samples[2 * rate :]
samples = samples - np.mean(samples)
print(f"peak {np.max(np.abs(samples)):.3f} FS, rms {20*np.log10(np.std(samples)):.1f} dBFS, "
      f"samples >= 0.99 FS: {int(np.sum(np.abs(samples) >= 0.99))}")
sos = signal.butter(2, [25, 150], "bandpass", fs=rate, output="sos")
band = signal.sosfiltfilt(sos, samples)
envelope = signal.sosfiltfilt(signal.butter(2, 8, fs=rate, output="sos"), np.abs(band))
envelope = signal.decimate(envelope, 16)
envelope_rate = rate / 16
for start in range(0, int(len(envelope) / envelope_rate) - 8 + 1, 8):
    window = envelope[int(start * envelope_rate) : int((start + 8) * envelope_rate)]
    window = window - window.mean()
    correlation = np.correlate(window, window, "full")[len(window) - 1 :]
    lags = np.arange(len(correlation)) / envelope_rate
    valid = (lags >= 60 / 200) & (lags <= 60 / 40)
    best = lags[valid][np.argmax(correlation[valid])]
    print(f"  {start+2:3d}-{start+10:3d} s: about {60/best:5.1f} BPM")
