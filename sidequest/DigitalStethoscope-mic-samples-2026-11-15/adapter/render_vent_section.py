"""Draw the adapter cut along the vent axis and across it, in the dark theme."""
import sys

import matplotlib
import numpy

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot

import check_mesh
import generate_adapter_stl as adapter

solid = check_mesh.build_solid()
vent_height = (adapter.cavity_height + adapter.rubber_plate_thickness + adapter.barb_base_height - adapter.latch_root_thickness) / 2
vent_degrees = float(numpy.degrees(adapter.vent_angle))

background, part_color, board_color, text_color, vent_color = "#0f1115", "#5b8def", "#3fb950", "#d0d7de", "#ff9f43"
figure, axes = pyplot.subplots(1, 2, figsize=(13, 7.5), facecolor=background)

# Turning the vent axis onto x and the section plane onto z = 0 lets Manifold slice it.
lengthwise = solid.rotate((0, 0, -vent_degrees)).rotate((90, 0, 0)).slice(0)
for polygon in lengthwise.to_polygons():
    points = numpy.array(polygon)
    axes[0].fill(points[:, 0], -points[:, 1], color=part_color, alpha=0.85, linewidth=0)
board_top = -adapter.latch_clearance_below_pcb
board_radius = adapter.pcb_diameter / 2
axes[0].fill([-board_radius, board_radius, board_radius, -board_radius],
             [board_top - adapter.pcb_thickness] * 2 + [board_top] * 2, color=board_color, alpha=0.8)
axes[0].text(0, board_top - adapter.pcb_thickness / 2, "mic board", color=background, ha="center", va="center", fontsize=11)
axes[0].plot([adapter.channel_radius, adapter.outer_radius + 3], [vent_height, vent_height], color=vent_color, linewidth=1, linestyle=":")
axes[0].annotate("vent: 0.4 mm hole, 2.3 mm long,\nfrom the sound channel into the open hollow",
                 xy=(2.2, vent_height), xytext=(-9.7, 19), color=text_color, fontsize=11, arrowprops={"arrowstyle": "->", "color": text_color})
axes[0].annotate("1.2 mm hole in the outer wall,\nonly for the cleaning needle",
                 xy=(7.8, vent_height), xytext=(3.5, 14.5), color=text_color, fontsize=11, arrowprops={"arrowstyle": "->", "color": text_color})
axes[0].annotate("sound channel", xy=(0, 16), xytext=(-9.7, 24), color=text_color, fontsize=11,
                 arrowprops={"arrowstyle": "->", "color": text_color})
axes[0].set_title("Cut along the vent", color=text_color, fontsize=14)
axes[0].set_xlim(-10, 12.5)
axes[0].set_ylim(-4.5, 29)

crosswise = solid.slice(vent_height)
for polygon in crosswise.to_polygons():
    points = numpy.array(polygon)
    axes[1].fill(points[:, 0], points[:, 1], color=part_color, alpha=0.85, linewidth=0)
direction = numpy.array([numpy.cos(adapter.vent_angle), numpy.sin(adapter.vent_angle)])
axes[1].plot(*zip(direction * adapter.channel_radius, direction * (adapter.outer_radius + 3)), color=vent_color, linewidth=1, linestyle=":")
axes[1].annotate("needle path", xy=tuple(direction * (adapter.outer_radius + 2)), xytext=(-9.7, 3), color=text_color, fontsize=11,
                 arrowprops={"arrowstyle": "->", "color": text_color})
axes[1].annotate("clip arm", xy=(0, 7.5), xytext=(3, 9.3), color=text_color, fontsize=11, arrowprops={"arrowstyle": "->", "color": text_color})
axes[1].annotate("stem with sound channel", xy=(1.5, -2.5), xytext=(1, -9.6), color=text_color, fontsize=11,
                 arrowprops={"arrowstyle": "->", "color": text_color})
axes[1].set_title(f"Cut across the housing at the vent, {vent_height:.1f} mm above the board", color=text_color, fontsize=14)
axes[1].set_xlim(-11, 11)
axes[1].set_ylim(-11, 11)

for axis in axes:
    axis.set_aspect("equal")
    axis.set_facecolor(background)
    axis.tick_params(colors=text_color)
    axis.set_xlabel("mm", color=text_color)
    for spine in axis.spines.values():
        spine.set_color("#30363d")
figure.tight_layout()
figure.savefig(sys.argv[1], dpi=120, facecolor=background)
