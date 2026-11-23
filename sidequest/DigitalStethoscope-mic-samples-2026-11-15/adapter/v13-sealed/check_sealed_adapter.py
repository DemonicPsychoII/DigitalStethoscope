"""Check adapter v13 and its seal against each other, the board and the pin stubs, in the latched position."""
import numpy
from manifold3d import Manifold

import generate_adapter_stl as adapter
import generate_seal_stl as seal_design


def disc(radius, bottom, top, center=(0.0, 0.0)):
    return Manifold.cylinder(top - bottom, radius, radius, 128).translate((center[0], center[1], bottom))


def radial_extent(solid, height, angle_degrees):
    probe = Manifold.cube((20, 0.02, 0.02)).translate((0, -0.01, height - 0.01)).rotate((0, 0, angle_degrees))
    hit = solid ^ probe
    if hit.is_empty():
        return None
    points = numpy.array(hit.to_mesh().vert_properties)[:, :2]
    radii = numpy.hypot(points[:, 0], points[:, 1])
    return round(float(radii.min()), 3), round(float(radii.max()), 3)


solid = adapter.build_solid("tilted")
print("adapter: status", solid.status(), "pieces", len(solid.decompose()), "volume cm3", round(solid.volume() / 1000, 3))
arm_top = adapter.barb_base_height - adapter.latch_root_thickness
below_root = solid ^ Manifold.cube((40, 40, 40)).translate((-20, -20, arm_top - adapter.relief_fillet_radius - 40))
print("pieces below the arm roots (expect 3: body and two free arms)", len(below_root.decompose()))

board_top = seal_design.latched_board_top
board = disc(adapter.pcb_diameter / 2, board_top - adapter.pcb_thickness, board_top)
for key_angle in adapter.key_angles:
    center = (adapter.key_center_distance * numpy.cos(key_angle), adapter.key_center_distance * numpy.sin(key_angle))
    board = board - disc(adapter.notch_radius, -5, 5, center)
pins = Manifold()
for row in (-3.9, 3.9):
    for along in (-2.54, 0, 2.54):
        pins = pins + disc(0.85, board_top, board_top + adapter.pin_stub_height, (row, along))
print("adapter overlap with latched board mm3", round((solid ^ board).volume(), 4),
      "with pin stubs mm3", round((solid ^ pins).volume(), 4))

for interference in (0.2, 0.3, 0.4):
    seal = seal_design.build_seal(interference)
    lip_tip = seal.bounding_box()[2]
    print(f"seal with {interference} mm lip interference: pieces {len(seal.decompose())}, lip tip {lip_tip:.2f} mm "
          f"(board top {board_top:.2f}), overlap with board {(seal ^ board).volume():.3f} mm3, "
          f"with pin stubs {(seal ^ pins).volume():.4f} mm3, with adapter {(seal ^ solid).volume():.3f} mm3")

seal = seal_design.build_seal()
gap_to_pins = 3.9 - 0.85 - seal_design.seal_width / 2
print(f"side gap from seal to pin stubs {gap_to_pins:.2f} mm; seal end at y {seal_design.seal_length / 2:.2f}, pocket wall at "
      f"{adapter.pocket_radius:.2f}")
turned = seal.rotate((0, 0, 90))
print("seal turned 90 degrees overlaps the adapter boss mm3 (expect large: the oval only fits one way)",
      round((turned ^ adapter.boss_solid()).volume(), 2))
flipped = seal.mirror((0, 0, 1)).translate((0, 0, seal_design.seal_top + seal.bounding_box()[2]))
print("seal upside down overlaps the adapter mm3 (expect large: the lip side has no pocket)", round((flipped ^ solid).volume(), 2))

vent_height = (adapter.cavity_height + adapter.rubber_plate_thickness + arm_top) / 2
slot_degrees = numpy.degrees(adapter.vent_slot_angle)
print(f"vent slot at {vent_height:.2f} mm above the board, {slot_degrees:.0f} degrees; first material on its line "
      f"(expect the clip arm beyond {adapter.pocket_radius:.2f} mm, nothing in the stem wall)", radial_extent(solid, vent_height, slot_degrees))
print("boss face above the board top", round(adapter.boss_face_height - board_top, 2), "mm; pocket depth in the seal",
      round(adapter.boss_insertion + seal_design.pocket_extra_depth, 2), "mm, boss length", adapter.boss_insertion, "mm")

for interference in (0.2, 0.3, 0.4):
    body_bottom = board_top - interference + seal_design.lip_height
    print(f"lip {interference} mm: board can rise {body_bottom - board_top:.2f} mm above the latched position before it "
          f"meets the seal body, so the hooks can snap under it")
hook_inner_radius = adapter.pocket_radius - adapter.latch_depth
print(f"hook reaches {adapter.pcb_diameter / 2 - hook_inner_radius:.2f} mm under the board edge; arm deflects "
      f"{adapter.latch_depth:.2f} mm while the board passes")
bending_length = adapter.barb_base_height - adapter.latch_root_thickness - adapter.latch_catch_height
strain = 3 * adapter.latch_tab_thickness * adapter.latch_depth / (2 * bending_length ** 2)
print(f"arm {adapter.latch_tab_thickness} mm thick, {bending_length:.1f} mm from root to hook: peak bending strain "
      f"{strain * 100:.2f} % (PLA yields at about 2-3 %)")
ramp_height = adapter.latch_catch_height - adapter.skirt_bottom
print(f"lead-in ramp {ramp_height:.2f} mm high for {adapter.latch_depth:.2f} mm depth: "
      f"{numpy.degrees(numpy.arctan(adapter.latch_depth / ramp_height)):.0f} degrees from vertical")
