"""Draw the toolpaths of a sliced Bambu job: all extrusion in 3D plus single layers, and print the job summary.

Usage: render_slices.py <job.gcode.3mf> <picture> <layer height in mm>...
"""
import math
import re
import sys
import zipfile
from collections import defaultdict

import matplotlib
import numpy

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot

BACKGROUND, TEXT, GRID = "#0f1115", "#d0d7de", "#30363d"
FEATURE_COLORS = {"Outer wall": "#ff9f43", "Inner wall": "#5b8def", "Overhang wall": "#f778ba", "Bridge": "#e3b341",
                  "Sparse infill": "#3fb950", "Internal solid infill": "#2ea043", "Top surface": "#d2a8ff",
                  "Bottom surface": "#79c0ff", "Support": "#8b949e", "Support interface": "#c9d1d9",
                  "Support transition": "#6e7681", "Brim": "#6e7681", "Gap infill": "#a5d6ff"}

job, picture, requested_layers = sys.argv[1], sys.argv[2], [float(value) for value in sys.argv[3:]]
archive = zipfile.ZipFile(job)
lines = archive.read("Metadata/plate_1.gcode").decode("utf-8", "replace").splitlines()
summary = {}
for line in lines[:400]:
    for key, label in (("total estimated time", "time"), ("total filament weight", "grams"), ("total layer number", "layers")):
        if key in line:
            summary[label] = line.split(":", 1)[1].strip()
settings = archive.read("Metadata/project_settings.config").decode("utf-8", "replace")
filament = re.search(r'"filament_settings_id": \[\s*"([^"]+)"', settings)
process = re.search(r'"print_settings_id": "([^"]+)"', settings)

feature, height, x, y = "", 0.0, 0.0, 0.0
segments = defaultdict(list)
lengths = defaultdict(float)
for line in lines:
    if line.startswith("; FEATURE:"):
        feature = line[len("; FEATURE:"):].strip()
    elif line.startswith("; Z_HEIGHT:"):
        height = float(line.split(":")[1])
    elif line.startswith(("G0 ", "G1 ", "G2 ", "G3 ")):
        # Arcs are drawn as their chord; at these sizes that is close enough to judge the paths.
        words = dict(re.findall(r"([XYE])(-?\d*\.?\d+)", line.split(";")[0]))
        new_x, new_y = float(words.get("X", x)), float(words.get("Y", y))
        if "E" in words and float(words["E"]) > 0 and ("X" in words or "Y" in words) and feature != "Custom":
            segments[height].append((feature, x, y, new_x, new_y))
            lengths[feature] += math.hypot(new_x - x, new_y - y)
        x, y = new_x, new_y
heights = sorted(segments)
support = sum(value for name, value in lengths.items() if "upport" in name)
print(job.replace("\\", "/").split("/")[-1])
print(f"  {process.group(1) if process else '?'} / {filament.group(1) if filament else '?'}")
print(f"  time {summary.get('time')}, filament {summary.get('grams')} g, {len(heights)} layers up to {heights[-1]:.2f} mm")
print(f"  support {support:.0f} mm, brim {lengths.get('Brim', 0):.0f} mm, overhang wall {lengths.get('Overhang wall', 0):.0f} mm, "
      f"bridge {lengths.get('Bridge', 0):.0f} mm")

all_points = numpy.array([(s[1], s[2]) for height in heights for s in segments[height]])
center = (all_points.min(axis=0) + all_points.max(axis=0)) / 2
span = (all_points.max(axis=0) - all_points.min(axis=0)).max() / 2 + 1.5

figure = pyplot.figure(figsize=(6 + 4.2 * len(requested_layers), 6.4), facecolor=BACKGROUND)
grid = figure.add_gridspec(1, 1 + len(requested_layers), width_ratios=[1.45] + [1] * len(requested_layers))
view = figure.add_subplot(grid[0, 0], projection="3d")
view.set_facecolor(BACKGROUND)
for height in heights[:: max(1, len(heights) // 120)]:
    for name, x0, y0, x1, y1 in segments[height]:
        view.plot([x0, x1], [y0, y1], [height, height], color=FEATURE_COLORS.get(name, "#8b949e"), linewidth=0.35)
view.set_xlim(center[0] - span, center[0] + span)
view.set_ylim(center[1] - span, center[1] + span)
view.set_zlim(0, max(heights[-1], 2 * span) * 1.0)
view.set_box_aspect((1, 1, max(heights[-1], 2 * span) / (2 * span)))
view.view_init(elev=24, azim=-62)
view.set_axis_off()
view.set_title(f"All toolpaths ({summary.get('time')}, {summary.get('grams')} g)", color=TEXT, fontsize=12)
for index, requested in enumerate(requested_layers):
    height = min(heights, key=lambda value: abs(value - requested))
    axis = figure.add_subplot(grid[0, index + 1])
    axis.set_facecolor(BACKGROUND)
    for name, x0, y0, x1, y1 in segments[height]:
        axis.plot([x0, x1], [y0, y1], color=FEATURE_COLORS.get(name, "#8b949e"), linewidth=0.9)
    axis.set_xlim(center[0] - span, center[0] + span)
    axis.set_ylim(center[1] - span, center[1] + span)
    axis.set_aspect("equal")
    axis.set_title(f"Layer at {height:.2f} mm", color=TEXT, fontsize=12)
    axis.tick_params(colors=TEXT)
    for spine in axis.spines.values():
        spine.set_color(GRID)
used = [name for name in FEATURE_COLORS if lengths.get(name)]
handles = [matplotlib.lines.Line2D([], [], color=FEATURE_COLORS[name], linewidth=2) for name in used]
figure.legend(handles, used, loc="lower center", ncol=len(used), facecolor=BACKGROUND, edgecolor=GRID, labelcolor=TEXT,
              fontsize=10)
figure.tight_layout(rect=(0, 0.07, 1, 1))
figure.savefig(picture, dpi=105, facecolor=BACKGROUND)
print("  picture:", picture)
