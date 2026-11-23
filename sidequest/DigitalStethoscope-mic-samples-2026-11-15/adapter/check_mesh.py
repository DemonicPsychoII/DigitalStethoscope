import numpy
from manifold3d import CrossSection, Manifold, Mesh

import generate_adapter_stl as adapter


def build_solid():
    vertices, triangles = adapter.revolve(adapter.adapter_profile())
    solid = Manifold(Mesh(vert_properties=vertices.astype(numpy.float32), tri_verts=triangles.astype(numpy.uint32)))
    for cut in adapter.latch_tab_cuts() + adapter.material_relief_cuts() + adapter.vent_cuts() + [adapter.print_flat_cut()]:
        solid = solid - cut
    return solid


def disc(radius, bottom, top, center=(0.0, 0.0)):
    return Manifold.cylinder(top - bottom, radius, radius, 128).translate((center[0], center[1], bottom))


def radial_extent(solid, height, angle_degrees):
    """Inner and outer radius of the material met by a ray at this height and angle."""
    probe = Manifold.cube((20, 0.02, 0.02)).translate((0, -0.01, height - 0.01)).rotate((0, 0, angle_degrees))
    hit = solid ^ probe
    if hit.is_empty():
        return None
    points = numpy.array(hit.to_mesh().vert_properties)[:, :2]
    radii = numpy.hypot(points[:, 0], points[:, 1])
    return round(float(radii.min()), 3), round(float(radii.max()), 3)


solid = build_solid()
arm_top = adapter.barb_base_height - adapter.latch_root_thickness
print("status", solid.status(), "genus", solid.genus(), "volume cm3", round(solid.volume() / 1000, 3))
print("pieces of whole part", len(solid.decompose()))

below_root = solid ^ Manifold.cube((40, 40, 40)).translate((-20, -20, arm_top - adapter.relief_fillet_radius - 40))
pieces = below_root.decompose()
print("pieces when cut below the arm roots (expect 3: body and two free arms)", len(pieces),
      [round(piece.volume(), 1) for piece in pieces])

board_top = -adapter.latch_clearance_below_pcb
board = disc(adapter.pcb_diameter / 2, board_top - adapter.pcb_thickness, board_top)
for key_angle in adapter.key_angles:
    center = (adapter.key_center_distance * numpy.cos(key_angle), adapter.key_center_distance * numpy.sin(key_angle))
    board = board - disc(adapter.notch_radius, -5, 5, center)
print("overlap with latched board mm3", round((solid ^ board).volume(), 4))

pressed_board = board.translate((0, 0, adapter.latch_clearance_below_pcb))
pins = Manifold()
for row in (-3.9, 3.9):
    for along in (-2.54, 0, 2.54):
        pins = pins + disc(0.85, 0, adapter.pin_stub_height, (row, along))
print("overlap with board pushed fully in mm3", round((solid ^ pressed_board).volume(), 4),
      "overlap with pin stubs mm3", round((solid ^ pins).volume(), 4))

rubber_strip = Manifold.cube((5.5, 13.75, adapter.cavity_height - 0.02)).translate((-2.75, -6.875, 0.01))
rubber_strip = rubber_strip - disc(adapter.boss_diameter / 2 + 0.1, -1, 5)
print("overlap with rubber strip space mm3", round((solid ^ rubber_strip).volume(), 4))

print("hook just below the board, at the clip (inner, outer radius)", radial_extent(solid, board_top - adapter.pcb_thickness - 0.05, 90))
print("arm beside the board edge, at the clip", radial_extent(solid, -0.5, 90))
print("arm half way up, at the clip", radial_extent(solid, arm_top / 2 + 2, 90))
print("in the slit, half way up (expect None)", radial_extent(solid, 2.0, 90 + numpy.degrees(adapter.latch_slit_angle) + 2))
print("wall next to the slit", radial_extent(solid, -0.5, 90 + 35))
print("wall at the notch fill-in, opposite the print flat", radial_extent(solid, -0.5, 180))
print("wall at the print flat", radial_extent(solid, -0.5, 0))
print("web at the arm root", radial_extent(solid, arm_top + 0.75, 90))
print("plate over the rubber, between the clips", radial_extent(solid, adapter.cavity_height + 0.6, 45))
print("plate behind the arm (must stop before the arm)", radial_extent(solid, adapter.cavity_height + 0.6, 90))
