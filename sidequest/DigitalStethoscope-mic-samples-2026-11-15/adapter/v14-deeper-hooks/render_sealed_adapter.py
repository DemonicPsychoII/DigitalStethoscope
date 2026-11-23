"""Draw adapter v13 with its seal on the latched board: two cuts and an exploded view, in the dark theme.

Usage: render_sealed_adapter.py <section picture> <exploded picture>
"""
import sys

import matplotlib
import numpy

matplotlib.use("Agg")
import matplotlib.pyplot as pyplot
from manifold3d import Manifold
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import generate_adapter_stl as adapter
import generate_seal_stl as seal_design

background, part_color, seal_color, board_color, pin_color, text_color, vent_color = (
    "#0f1115", "#5b8def", "#ff9f43", "#3fb950", "#8b949e", "#d0d7de", "#f778ba")
solid = adapter.build_solid("tilted")
seal = seal_design.build_seal()
board_top = seal_design.latched_board_top
board_bottom = board_top - adapter.pcb_thickness
board_radius = adapter.pcb_diameter / 2
vent_height = (adapter.cavity_height + adapter.rubber_plate_thickness + adapter.barb_base_height - adapter.latch_root_thickness) / 2


def fill_slice(axis, part, plane_rotation, color, alpha=0.9):
    for polygon in part.rotate(plane_rotation).rotate((90, 0, 0)).slice(0).to_polygons():
        points = numpy.array(polygon)
        axis.fill(points[:, 0], -points[:, 1], color=color, alpha=alpha, linewidth=0)


def label(axis, text, point, text_position):
    axis.annotate(text, xy=point, xytext=text_position, color=text_color, fontsize=10.5,
                  arrowprops={"arrowstyle": "->", "color": text_color})


figure, axes = pyplot.subplots(1, 3, figsize=(17, 8), facecolor=background, gridspec_kw={"width_ratios": (1, 1, 1.1)})
for axis, rotation, title in ((axes[0], (0, 0, -90), "Cut along the seal, between the pin rows"),
                              (axes[1], (0, 0, 0), "Cut across the seal, through the pin stubs")):
    fill_slice(axis, solid, rotation, part_color)
    fill_slice(axis, seal, rotation, seal_color)
    axis.fill([-board_radius, board_radius, board_radius, -board_radius], [board_bottom] * 2 + [board_top] * 2,
              color=board_color, alpha=0.8)
    axis.text(0, board_bottom - 0.9, "mic board, latched", color=board_color, ha="center", fontsize=10.5)
    axis.set_title(title, color=text_color, fontsize=13)
    axis.set_xlim(-10, 10)
    axis.set_ylim(-5, 18.5)
for row in (-3.9, 3.9):
    axes[1].fill([row - 0.85, row + 0.85, row + 0.85, row - 0.85],
                 [board_top] * 2 + [board_top + adapter.pin_stub_height] * 2, color=pin_color, alpha=0.9)
label(axes[0], "TPU seal, 2.6 mm thick", (3.5, 2.0), (2.5, 9.5))
label(axes[0], "oval boss with rim:\nthe seal clicks onto it", (2.9, 2.3), (-9.6, 9.5))
label(axes[0], "lip ring, 1.0 mm high,\nbends 0.3 mm onto the board", (-2.2, -0.2), (-9.6, -3.2))
label(axes[1], "pin stub", (3.9, board_top + 1.2), (5.0, 5.5))
label(axes[1], "0.3 mm side gap", (3.0, 1.6), (-9.6, 7.5))
label(axes[1], "sound channel", (0, 6), (-9.6, 11))
label(axes[0], "hook reaches 2.0 mm under the board", (5.6, -1.4), (-3.0, -4.6))

crosswise = solid.slice(vent_height)
for polygon in crosswise.to_polygons():
    points = numpy.array(polygon)
    axes[2].fill(points[:, 0], points[:, 1], color=part_color, alpha=0.9, linewidth=0)
direction = numpy.array([numpy.cos(adapter.vent_slot_angle), numpy.sin(adapter.vent_slot_angle)])
axes[2].plot(*zip(direction * 0, direction * adapter.stem_radius), color=vent_color, linewidth=3)
label(axes[2], "vent slot through the stem wall:\n10 layers (0.8 mm) high, 0.7 mm wide,\nlevel in the tilted print",
      tuple(direction * 2.2), (-10.5, -9.8))
seal_outline = seal.slice(seal_design.seal_top - 0.3)
for polygon in seal_outline.to_polygons():
    points = numpy.array(polygon)
    axes[2].plot(numpy.append(points[:, 0], points[0, 0]), numpy.append(points[:, 1], points[0, 1]), color=seal_color,
                 linewidth=1.2, linestyle="--")
for row in (-3.9, 3.9):
    for along in (-2.54, 0, 2.54):
        axes[2].add_patch(pyplot.Circle((row, along), 0.85, color=pin_color, fill=False, linewidth=1, linestyle="--"))
label(axes[2], "seal outline below (dashed)", (2.4, 4.6), (2.5, 10.2))
label(axes[2], "pin stubs below", (3.9, -2.54), (4.5, -10.2))
axes[2].set_title(f"Cut across the housing at the vent, {vent_height - board_top:.1f} mm above the board", color=text_color, fontsize=13)
axes[2].set_xlim(-11, 11)
axes[2].set_ylim(-11, 11)
for axis in axes:
    axis.set_aspect("equal")
    axis.set_facecolor(background)
    axis.tick_params(colors=text_color)
    axis.set_xlabel("mm", color=text_color)
    for spine in axis.spines.values():
        spine.set_color("#30363d")
figure.tight_layout()
figure.savefig(sys.argv[1], dpi=110, facecolor=background)

light = LightSource(azdeg=315, altdeg=40)


def draw_part(axis, part, color, offset):
    mesh = part.translate(offset).to_mesh()
    vertices = numpy.array(mesh.vert_properties)[:, :3]
    triangles = vertices[numpy.array(mesh.tri_verts)]
    normals = numpy.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= numpy.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
    shade = light.shade_normals(normals, fraction=1.0)
    base = numpy.array(matplotlib.colors.to_rgb(color))
    faces = numpy.clip(base * (0.35 + 0.75 * shade[:, None]), 0, 1)
    axis.add_collection3d(Poly3DCollection(triangles, facecolors=faces, edgecolors="none"))


exploded, views = pyplot.subplots(1, 2, figsize=(15, 8), facecolor=background, subplot_kw={"projection": "3d"})
board_part = Manifold.cylinder(adapter.pcb_thickness, board_radius, board_radius, 96).translate((0, 0, board_bottom))
for key_angle in adapter.key_angles:
    center = (adapter.key_center_distance * numpy.cos(key_angle), adapter.key_center_distance * numpy.sin(key_angle), -5)
    board_part = board_part - Manifold.cylinder(10, adapter.notch_radius, adapter.notch_radius, 48).translate(center)
pin_parts = Manifold()
for row in (-3.9, 3.9):
    for along in (-2.54, 0, 2.54):
        pin_parts = pin_parts + Manifold.cylinder(adapter.pin_stub_height, 0.85, 0.85, 24).translate((row, along, board_top))
for view, (elevation, azimuth, title) in zip(views, ((22, -60, "Exploded, from above"), (-28, -60, "Exploded, from below"))):
    view.set_facecolor(background)
    draw_part(view, board_part, board_color, (0, 0, 0))
    draw_part(view, pin_parts, pin_color, (0, 0, 0))
    draw_part(view, seal, seal_color, (0, 0, 9))
    draw_part(view, solid, part_color, (0, 0, 20))
    view.view_init(elev=elevation, azim=azimuth)
    view.set_box_aspect((1, 1, 2.4))
    view.set_xlim(-9, 9)
    view.set_ylim(-9, 9)
    view.set_zlim(-3, 47)
    view.set_axis_off()
    view.set_title(title, color=text_color, fontsize=13)
exploded.tight_layout()
exploded.savefig(sys.argv[2], dpi=110, facecolor=background)
