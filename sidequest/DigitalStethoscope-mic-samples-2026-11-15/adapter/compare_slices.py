"""Summarise sliced jobs: time, filament, plate contact of the part, unsupported overhang and bridge length, support length."""
import math
import re
import sys
import zipfile
from collections import defaultdict

for path in sys.argv[1:]:
    lines = zipfile.ZipFile(path).read("Metadata/plate_1.gcode").decode("utf-8", "replace").splitlines()
    summary = {}
    for line in lines[:400]:
        if "total estimated time" in line:
            summary["time"] = line.split("total estimated time:")[1].strip()
        if "total filament weight" in line:
            summary["grams"] = line.split(":")[1].strip()
    feature, height, x, y = "", 0.0, 0.0, 0.0
    lengths = defaultdict(float)
    first_layer_part = 0.0
    first_height = None
    for line in lines:
        if line.startswith("; FEATURE:"):
            feature = line[len("; FEATURE:"):].strip()
        elif line.startswith("; Z_HEIGHT:"):
            height = float(line.split(":")[1])
            first_height = first_height or height
        elif line.startswith("G1 "):
            words = dict(re.findall(r"([XYE])(-?\d*\.?\d+)", line.split(";")[0]))
            new_x, new_y = float(words.get("X", x)), float(words.get("Y", y))
            if "E" in words and float(words["E"]) > 0 and ("X" in words or "Y" in words):
                distance = math.hypot(new_x - x, new_y - y)
                lengths[feature] += distance
                if height == first_height and "upport" not in feature and feature != "Brim":
                    first_layer_part += distance
            x, y = new_x, new_y
    support = sum(value for name, value in lengths.items() if "upport" in name)
    print(path.split("/")[-1])
    print(f"  time {summary.get('time')}, filament {summary.get('grams')} g")
    print(f"  part touching the plate: {first_layer_part:.0f} mm of line, brim {lengths.get('Brim', 0):.0f} mm")
    print(f"  overhang wall {lengths.get('Overhang wall', 0):.0f} mm, bridge {lengths.get('Bridge', 0):.0f} mm, support {support:.0f} mm")
