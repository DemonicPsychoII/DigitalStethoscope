"""TPU seal between the microphone board and the adapter, printed flat with the pocket face on the build plate.

Usage: generate_seal_stl.py <output stl> [lip interference in mm, default 0.3]
"""
import sys
from pathlib import Path

import numpy
from manifold3d import CrossSection, Manifold, Mesh

import generate_adapter_stl as adapter

seal_width = 5.5
seal_length = 11.0
boss_interference = 0.1
pocket_extra_depth = 0.2
bore_diameter = 2.0
# TPU for AMS is Shore 68D, too stiff to seal by squeezing a block; a thin slanted lip bends onto the board instead.
lip_height = 1.0
lip_thickness = 0.5
lip_lean = numpy.radians(30)
lip_base_inner_radius = 1.5
default_lip_interference = 0.3
marker_diameter = 0.8
marker_depth = 0.4
marker_pitch = 1.2

latched_board_top = -adapter.latch_clearance_below_pcb
seal_top = adapter.cavity_height


def lip_solid(body_bottom):
    horizontal_thickness = lip_thickness / numpy.cos(lip_lean)
    outward_shift = lip_height * numpy.tan(lip_lean)
    tip = body_bottom - lip_height
    profile = [
        (lip_base_inner_radius, body_bottom + 0.05),
        (lip_base_inner_radius + outward_shift, tip),
        (lip_base_inner_radius + outward_shift + horizontal_thickness, tip),
        (lip_base_inner_radius + horizontal_thickness, body_bottom + 0.05),
    ]
    return CrossSection([profile]).revolve(128)


def markers(count, body_bottom):
    """Small pits on the lower face, outside the lip ring, that tell the printed variants apart."""
    pits = Manifold()
    for index in range(count):
        x = (index - (count - 1) / 2) * marker_pitch
        pits = pits + Manifold.cylinder(marker_depth + 1, marker_diameter / 2, marker_diameter / 2, 24).translate(
            (x, seal_length / 2 - 1.3, body_bottom - 1))
    return pits


def build_seal(lip_interference=default_lip_interference, marker_count=0):
    """The seal in its working position, latched: top against the ceiling, lip tip lip_interference below the board top."""
    body_bottom = latched_board_top - lip_interference + lip_height
    body = adapter.stadium(seal_width, seal_length).extrude(seal_top - body_bottom).translate((0, 0, body_bottom))
    pocket_depth = adapter.boss_insertion + pocket_extra_depth
    pocket = adapter.stadium(adapter.boss_width - boss_interference, adapter.boss_length - boss_interference)
    pocket = pocket.extrude(pocket_depth + 1).translate((0, 0, seal_top - pocket_depth))
    bore = Manifold.cylinder(10, bore_diameter / 2, bore_diameter / 2, 64).translate((0, 0, body_bottom - 5))
    return body - pocket - bore - markers(marker_count, body_bottom) + lip_solid(body_bottom)


def main():
    output_path = Path(sys.argv[1])
    lip_interference = float(sys.argv[2]) if len(sys.argv) > 2 else default_lip_interference
    seal = build_seal(lip_interference)
    if seal.is_empty() or len(seal.decompose()) != 1:
        raise ValueError(f"Unexpected seal: {seal.status()}")
    # Pocket face down on the plate, lip up, so the lip prints last and its slant is a gentle overhang.
    printed = seal.mirror((0, 0, 1)).translate((0, 0, seal_top))
    mesh = printed.to_mesh()
    vertices = numpy.array(mesh.vert_properties, dtype=float)[:, :3]
    triangles = numpy.array(mesh.tri_verts, dtype=int)
    vertices[:, 2] -= vertices[:, 2].min()
    adapter.assert_watertight(triangles)
    adapter.write_binary_stl(output_path, vertices, triangles)
    print(f"lip interference {lip_interference} mm: body {seal_top - (latched_board_top - lip_interference + lip_height):.2f} mm thick, "
          f"volume {seal.volume():.1f} mm^3, bounding box {vertices.min(axis=0).round(2)} to {vertices.max(axis=0).round(2)}")


if __name__ == "__main__":
    main()
