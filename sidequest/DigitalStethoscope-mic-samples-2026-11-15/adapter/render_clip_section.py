import sys

import matplotlib
import numpy
from manifold3d import Manifold, Mesh

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot

import generate_adapter_stl as adapter

vertices, triangles = adapter.revolve(adapter.adapter_profile())
solid = Manifold(Mesh(vert_properties=vertices.astype(numpy.float32), tri_verts=triangles.astype(numpy.uint32)))
for cut in adapter.latch_tab_cuts() + adapter.material_relief_cuts() + adapter.vent_cuts() + [adapter.print_flat_cut()]:
    solid = solid - cut

background, part_color, board_color, text_color = "#0f1115", "#5b8def", "#3fb950", "#d0d7de"
figure, axes = pyplot.subplots(1, 2, figsize=(13, 7.5), facecolor=background)
sections = [("Section through both clips", (0, 90, 0), adapter.pcb_diameter / 2),
            ("Section through both notch fill-ins", (90, 0, 0), adapter.notch_floor_diameter / 2)]
for axis, (title, rotation, board_radius) in zip(axes, sections):
    # Rotating the section plane onto z = 0 lets Manifold slice it; the remaining two axes become radius and height.
    section = solid.rotate(rotation).slice(0)
    for polygon in section.to_polygons():
        points = numpy.array(polygon)
        if rotation[1]:
            radius, height = points[:, 1], points[:, 0]
        else:
            radius, height = points[:, 0], -points[:, 1]
        axis.fill(radius, height, color=part_color, alpha=0.85, linewidth=0)
    board_top = -adapter.latch_clearance_below_pcb
    board_bottom = board_top - adapter.pcb_thickness
    axis.fill([-board_radius, board_radius, board_radius, -board_radius],
              [board_bottom, board_bottom, board_top, board_top], color=board_color, alpha=0.8)
    axis.text(0, (board_top + board_bottom) / 2, "mic board", color=background, ha="center", va="center", fontsize=11)
    axis.set_title(title, color=text_color, fontsize=14)
    axis.set_aspect("equal")
    axis.set_xlim(-10, 10)
    axis.set_ylim(-4.5, 29)
    axis.set_facecolor(background)
    axis.tick_params(colors=text_color)
    axis.set_xlabel("mm", color=text_color)
    for spine in axis.spines.values():
        spine.set_color("#30363d")
axes[0].annotate("1.4 mm hook, sharp tip", xy=(6.3, -1.3), xytext=(1.5, -3.8), color=text_color, fontsize=11,
                 arrowprops={"arrowstyle": "->", "color": text_color})
axes[0].annotate("clip arm, 1 mm thick,\nfree over about 11 mm", xy=(7.5, 4.5), xytext=(-9.5, 14), color=text_color, fontsize=11,
                 arrowprops={"arrowstyle": "->", "color": text_color})
axes[0].annotate("gap so the arm\ncan bend outward", xy=(-6.65, 6.5), xytext=(-9.5, 19), color=text_color, fontsize=11,
                 arrowprops={"arrowstyle": "->", "color": text_color})
axes[0].annotate("latched: board to ceiling 3.3 mm, rubber 3.5 mm", xy=(4.3, 1.7), xytext=(-9.5, 26.5), color=text_color, fontsize=11,
                 arrowprops={"arrowstyle": "->", "color": text_color})
figure.tight_layout()
figure.savefig(sys.argv[1], dpi=120, facecolor=background)
