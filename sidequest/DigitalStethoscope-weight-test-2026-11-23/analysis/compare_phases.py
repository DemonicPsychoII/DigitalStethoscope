import sys
from pathlib import Path
import numpy as np
import soundfile
from scipy import signal

root = Path(sys.argv[1])
windows = {"place 1-6.5": (1, 6.5), "rest 7-16": (7, 16), "lift 16-21": (16, 21), "after 21-24": (21, 24)}
highpass = signal.butter(2, 20, "highpass", fs=16000, output="sos")
for name in sys.argv[2:]:
    samples, rate = soundfile.read(root / name / "capture.wav")
    print(name)
    for label, (start, end) in windows.items():
        part = samples[int(start * rate):int(end * rate)]
        centred = part - part.mean()
        above20 = signal.sosfiltfilt(highpass, centred)
        print(f"   {label:12s} peak={np.max(np.abs(part)):.2f} saturated={np.mean(np.abs(part) > 0.999) * 100:.2f}% "
              f"rms={np.sqrt(np.mean(centred**2)):.4f} rms>20Hz={np.sqrt(np.mean(above20**2)):.4f}")
