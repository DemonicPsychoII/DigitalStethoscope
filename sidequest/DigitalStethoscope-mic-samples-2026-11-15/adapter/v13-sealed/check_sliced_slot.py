"""Measure the vent slot of the tilted adapter in the sliced G-code: free layers and free width per layer.

Usage: check_sliced_slot.py <job.gcode.3mf> <plate offset x> <plate offset y>
"""
import re
import sys
import zipfile

import numpy

import generate_adapter_stl as adapter

LINE_WIDTH = 0.42
job, offset_x, offset_y = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
body = numpy.array(adapter.build_solid("tilted").to_mesh().vert_properties, dtype=float)[:, :3]
tilt = adapter.plate_tilt(body)
along = numpy.array([-numpy.sin(tilt), 0.0, numpy.cos(tilt)])
vent_height = (adapter.cavity_height + adapter.rubber_plate_thickness + adapter.barb_base_height - adapter.latch_root_thickness) / 2
slot_x = numpy.array([0.0, 0.0, vent_height]) @ along + offset_x
slot_length = adapter.stem_radius + 0.6

lines = zipfile.ZipFile(job).read("Metadata/plate_1.gcode").decode("utf-8", "replace").splitlines()
height, x, y = 0.0, 0.0, 0.0
layers = {}
for line in lines:
    if line.startswith("; Z_HEIGHT:"):
        height = round(float(line.split(":")[1]), 3)
        layers.setdefault(height, [])
    elif line.startswith(("G0 ", "G1 ", "G2 ", "G3 ")):
        words = dict(re.findall(r"([XYE])(-?\d*\.?\d+)", line.split(";")[0]))
        new_x, new_y = float(words.get("X", x)), float(words.get("Y", y))
        if "E" in words and float(words["E"]) > 0 and ("X" in words or "Y" in words):
            for fraction in numpy.linspace(0, 1, max(2, int(numpy.hypot(new_x - x, new_y - y) / 0.02))):
                layers.setdefault(height, []).append((x + fraction * (new_x - x), y + fraction * (new_y - y)))
        x, y = new_x, new_y

# The stem wall the slot must cross: from the sound channel to the stem surface, measured along the part's y axis.
print(f"slot expected at print x {slot_x:.2f} mm, y {offset_y + adapter.channel_radius:.2f} to {offset_y + adapter.stem_radius:.2f} mm")
for layer_top in sorted(layers):
    if not 8.3 < layer_top < 9.9:
        continue
    points = numpy.array(layers[layer_top]) if layers[layer_top] else numpy.zeros((0, 2))
    across_wall = (points[:, 1] > offset_y + adapter.channel_radius + 0.3) & (points[:, 1] < offset_y + adapter.stem_radius - 0.3)
    near = points[across_wall & (numpy.abs(points[:, 0] - slot_x) < 1.5)]
    left = near[near[:, 0] < slot_x][:, 0]
    right = near[near[:, 0] >= slot_x][:, 0]
    if len(left) and len(right):
        gap = (right.min() - left.max()) - LINE_WIDTH
        verdict = f"open, {gap:.2f} mm between the line edges" if gap > 0.05 else "closed"
    elif len(left) or len(right):
        verdict = "lines on one side only"
    else:
        verdict = "no lines near the slot"
    print(f"  layer up to {layer_top:.2f} mm: {verdict}")
