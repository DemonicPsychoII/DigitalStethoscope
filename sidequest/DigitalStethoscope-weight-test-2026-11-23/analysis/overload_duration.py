import sys
from pathlib import Path
import numpy as np
import soundfile

root = Path(sys.argv[1])
for name in sys.argv[2:]:
    samples, rate = soundfile.read(root / name / "capture.wav")
    results = []
    for start, end in ((1, 7), (16, 21)):
        part = np.abs(samples[int(start * rate):int(end * rate)])
        loud = np.nonzero(part > 0.5)[0]
        if loud.size == 0:
            results.append("no peak > 0.5"); continue
        last_loud = loud[-1]
        settled = np.nonzero(part[last_loud:] < 0.05)[0]
        first_loud = loud[0]
        results.append(f"above 0.5 from {start + first_loud / rate:5.2f} to {start + last_loud / rate:5.2f} s "
                       f"({(last_loud - first_loud) / rate * 1000:4.0f} ms), below 0.05 after "
                       f"{settled[0] / rate * 1000 if settled.size else float('nan'):4.0f} ms")
    print(f"{name:28s} place: {results[0]} | lift: {results[1]}")
