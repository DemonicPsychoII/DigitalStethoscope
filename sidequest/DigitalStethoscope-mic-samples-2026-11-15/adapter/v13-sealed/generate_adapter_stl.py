import struct
import sys
from collections import Counter
from pathlib import Path

import numpy
from manifold3d import CrossSection, JoinType, Manifold, Mesh

pcb_diameter = 13.73
pcb_thickness = 1.0
skirt_extension = 1.9
pin_stub_height = 1.5
fit_clearance = 0.1
wall_thickness = 1.6
ceiling_thickness = 9.0
boss_width = 3.6
boss_length = 5.6
boss_insertion = 1.2
boss_plate_overlap = 0.3
rubber_thickness = 3.5
rubber_compression = 0.2
latch_catch = 1.0
latch_tab_thickness = 0.9
latch_root_thickness = 1.5
latch_back_gap = 0.6
rubber_plate_thickness = 1.2
stem_radius = 3.3
latch_web_margin_angle = numpy.radians(4)
relief_fillet_radius = 0.8
housing_top_fillet_radius = 0.8
rim_fillet_radius = 0.5
barb_base_fillet_radius = 0.4
slit_end_radius = 0.5
print_flat_depth = 0.5
tilted_contact_depth = 0.4
print_flat_angle = numpy.radians(0)
latch_slit_width = 1.0
latch_clearance_below_pcb = 0.1
latch_half_angle = numpy.radians(12)
latch_ramp_angle = numpy.radians(2)
latch_angles = tuple(numpy.radians((90, 270)))
channel_diameter = 2.0
vent_diameter = 1.0
vent_slot_layers = 10
vent_slot_width = 0.7
print_layer_height = 0.08
print_first_layer_height = 0.2
vent_slot_angle = numpy.radians(90)
vent_angle = numpy.radians(135)
tube_inner_diameter_minimum = 4.5
tube_inner_diameter_maximum = 5.0
barb_oversize = 0.6
barb_base_spread = 0.2
barb_retention = 0.6
barb_length = 15.0
barb_count = 4
segment_count = 160
notch_floor_diameter = 12.22
notch_radius = 1.0
key_clearance = 0.15
key_angles = (0.0, numpy.pi)

pocket_radius = (pcb_diameter + 2 * fit_clearance) / 2
outer_radius = pocket_radius + wall_thickness
# The latched board rests on the hooks, latch_clearance_below_pcb lower than fully pushed in.
cavity_height = rubber_thickness - rubber_compression - latch_clearance_below_pcb
barb_base_height = cavity_height + ceiling_thickness
barb_pitch = barb_length / barb_count
barb_step = (tube_inner_diameter_maximum - tube_inner_diameter_minimum + barb_base_spread) / (barb_count - 1)
barb_depth = barb_step + barb_retention
tip_diameter = tube_inner_diameter_minimum - 0.4
skirt_bottom = -(pcb_thickness + skirt_extension)
latch_depth = latch_catch + fit_clearance
latch_slit_angle = latch_half_angle + latch_ramp_angle + numpy.radians(1)
boss_face_height = cavity_height - boss_insertion
latch_catch_height = -(pcb_thickness + latch_clearance_below_pcb)
channel_radius = channel_diameter / 2
key_radius = notch_radius - key_clearance
key_center_distance = notch_floor_diameter / 2 + notch_radius


def arc_points(center_radius, center_height, arc_radius, start_degrees, end_degrees, point_count=9):
    angles = numpy.radians(numpy.linspace(start_degrees, end_degrees, point_count))
    return [(center_radius + arc_radius * numpy.cos(angle), center_height + arc_radius * numpy.sin(angle))
            for angle in angles]


def rounded(cross_section, corner_radius):
    """Round the convex corners of a cut, which become fillets in the part."""
    return cross_section.offset(-corner_radius, JoinType.Round).offset(corner_radius, JoinType.Round, 2.0, 32)


def adapter_profile():
    base_ridge_radius = (tube_inner_diameter_maximum + barb_oversize + barb_base_spread) / 2
    profile = [
        (channel_radius, cavity_height),
        ("pocket", cavity_height),
        ("pocket", latch_catch_height),
        ("latch", latch_catch_height),
        ("pocket", skirt_bottom),
        *arc_points(outer_radius - rim_fillet_radius, skirt_bottom + rim_fillet_radius, rim_fillet_radius, -90, 0),
        *arc_points(outer_radius - housing_top_fillet_radius, barb_base_height - housing_top_fillet_radius,
                    housing_top_fillet_radius, 0, 90),
        *arc_points(base_ridge_radius + barb_base_fillet_radius, barb_base_height + barb_base_fillet_radius,
                    barb_base_fillet_radius, 270, 180)[:-1],
    ]
    for barb_index in range(barb_count):
        bottom = barb_base_height + barb_index * barb_pitch
        is_tip_barb = barb_index == barb_count - 1
        ridge_diameter = tube_inner_diameter_maximum + barb_oversize + barb_base_spread - barb_index * barb_step
        end_diameter = tip_diameter if is_tip_barb else ridge_diameter - barb_depth
        profile.append((ridge_diameter / 2, bottom + (barb_base_fillet_radius if barb_index == 0 else 0)))
        profile.append((end_diameter / 2, bottom + barb_pitch))
    profile.append((channel_radius, barb_base_height + barb_length))
    return profile


def keyed_pocket_radius(angle):
    radius = pocket_radius
    for key_angle in key_angles:
        offset = angle - key_angle
        lateral = key_center_distance * numpy.sin(offset)
        if numpy.cos(offset) > 0 and abs(lateral) < key_radius:
            near_side = key_center_distance * numpy.cos(offset) - numpy.sqrt(key_radius ** 2 - lateral ** 2)
            radius = min(radius, near_side)
    return radius


def latch_depth_at(angle):
    for latch_angle in latch_angles:
        offset = abs((angle - latch_angle + numpy.pi) % (2 * numpy.pi) - numpy.pi)
        if offset <= latch_half_angle:
            return latch_depth
        if offset < latch_half_angle + latch_ramp_angle:
            return latch_depth * (latch_half_angle + latch_ramp_angle - offset) / latch_ramp_angle
    return 0.0


def surface_radius(profile_radius, angle):
    if profile_radius == "pocket":
        return keyed_pocket_radius(angle)
    if profile_radius == "latch":
        return keyed_pocket_radius(angle) - latch_depth_at(angle)
    return profile_radius


def revolve_angles():
    key_half_angle = numpy.arcsin(key_radius / key_center_distance)
    crossing_cosine = (pocket_radius ** 2 + key_center_distance ** 2 - key_radius ** 2) / (
        2 * pocket_radius * key_center_distance)
    crossing_angle = numpy.arccos(crossing_cosine)
    angles = list(numpy.linspace(0, 2 * numpy.pi, segment_count, endpoint=False))
    for key_angle in key_angles:
        angles.extend(key_angle + numpy.linspace(-key_half_angle, key_half_angle, 49) * 1.1)
        angles.extend((key_angle - crossing_angle, key_angle + crossing_angle))
    for latch_angle in latch_angles:
        latch_edge = latch_half_angle + latch_ramp_angle
        angles.extend(latch_angle + numpy.linspace(-latch_edge, latch_edge, 13))
        angles.extend((latch_angle - latch_half_angle, latch_angle + latch_half_angle))
    return numpy.unique(numpy.round(numpy.mod(angles, 2 * numpy.pi), 6))


def revolve(profile):
    angles = revolve_angles()
    segment_count = len(angles)
    vertices = numpy.array([
        (radius * numpy.cos(angle), radius * numpy.sin(angle), height)
        for profile_radius, height in profile
        for angle in angles
        for radius in [surface_radius(profile_radius, angle)]
    ])
    triangles = []
    point_count = len(profile)
    for point_index in range(point_count):
        next_point = (point_index + 1) % point_count
        for segment_index in range(segment_count):
            next_segment = (segment_index + 1) % segment_count
            a = point_index * segment_count + segment_index
            b = next_point * segment_count + segment_index
            c = next_point * segment_count + next_segment
            d = point_index * segment_count + next_segment
            triangles.append((a, b, c))
            triangles.append((a, c, d))
    triangles = numpy.array(triangles)
    if signed_volume(vertices, triangles) < 0:
        triangles = triangles[:, ::-1]
    return vertices, triangles


def signed_volume(vertices, triangles):
    first, second, third = (vertices[triangles[:, index]] for index in range(3))
    return numpy.einsum("ij,ij->i", first, numpy.cross(second, third)).sum() / 6


def assert_watertight(triangles):
    directed_edges = Counter()
    for first, second, third in triangles:
        for edge in ((first, second), (second, third), (third, first)):
            directed_edges[edge] += 1
    for (start, end), count in directed_edges.items():
        if count != 1 or directed_edges.get((end, start)) != 1:
            raise ValueError(f"Non-manifold edge {start}-{end}")


def write_binary_stl(path, vertices, triangles):
    with open(path, "wb") as stl_file:
        stl_file.write(b"stethoscope_microphone_adapter".ljust(80, b"\0"))
        stl_file.write(struct.pack("<I", len(triangles)))
        for triangle in triangles:
            first, second, third = vertices[triangle]
            normal = numpy.cross(second - first, third - first)
            length = numpy.linalg.norm(normal)
            normal = normal / length if length else normal
            stl_file.write(struct.pack("<12fH", *normal, *first, *second, *third, 0))


def annular_sector(inner_radius, outer_radius, start_angle, end_angle, bottom, top, corner_radius=0.0):
    angles = numpy.linspace(start_angle, end_angle, 48)
    outline = [(outer_radius * numpy.cos(angle), outer_radius * numpy.sin(angle)) for angle in angles]
    outline += [(inner_radius * numpy.cos(angle), inner_radius * numpy.sin(angle)) for angle in angles[::-1]]
    cross_section = CrossSection([outline])
    if corner_radius:
        cross_section = rounded(cross_section, corner_radius)
    return cross_section.extrude(top - bottom).translate((0, 0, bottom))


def latch_tab_cuts():
    """Slits, a gap behind the arm and a thinned outer wall turn each latch into a long arm rooted at the housing top.

    The arm has to bend outward by the full catch depth, which only a long arm survives.
    """
    arm_top = barb_base_height - latch_root_thickness
    slit_angular_width = latch_slit_width / pocket_radius
    cuts = []
    for latch_angle in latch_angles:
        for side in (-1, 1):
            slit_start = latch_angle + side * latch_slit_angle
            slit_end = slit_start + side * slit_angular_width
            cuts.append(annular_sector(pocket_radius - latch_back_gap, outer_radius + 1, min(slit_start, slit_end),
                                       max(slit_start, slit_end), skirt_bottom - 1, arm_top))
            # A round end spreads the bending stress where the slit stops at the arm root.
            slit_end = Manifold.cylinder(wall_thickness + latch_back_gap + 1, slit_end_radius, slit_end_radius, 32)
            slit_end = slit_end.translate((0, 0, pocket_radius - latch_back_gap)).rotate((0, 90, 0))
            slit_end = slit_end.translate((0, 0, arm_top + latch_slit_width / 2 - slit_end_radius))
            cuts.append(slit_end.rotate((0, 0, numpy.degrees(slit_start + side * slit_angular_width / 2))))
        arm_edge_angle = latch_slit_angle + slit_angular_width
        cuts.append(annular_sector(pocket_radius - latch_back_gap, pocket_radius,
                                   latch_angle - arm_edge_angle, latch_angle + arm_edge_angle,
                                   cavity_height - 0.5, cavity_height + rubber_plate_thickness + relief_fillet_radius))
        cuts.append(annular_sector(pocket_radius + latch_tab_thickness, outer_radius + 1,
                                   latch_angle - latch_slit_angle, latch_angle + latch_slit_angle,
                                   skirt_bottom - 1, barb_base_height + 1))
    return cuts


def material_relief_cuts():
    """Hollow the tall housing: what stays is the plate over the rubber, the stem, the wall and a web to each arm root."""
    arm_top = barb_base_height - latch_root_thickness
    plate_top = cavity_height + rubber_plate_thickness
    ring_section = CrossSection([[(stem_radius, plate_top), (pocket_radius, plate_top),
                                  (pocket_radius, arm_top), (stem_radius, arm_top)]])
    cuts = [rounded(ring_section, relief_fillet_radius).revolve(128)]
    web_half_angle = latch_slit_angle + latch_slit_width / pocket_radius + latch_web_margin_angle
    for latch_index, latch_angle in enumerate(latch_angles):
        next_latch_angle = latch_angles[(latch_index + 1) % len(latch_angles)]
        if next_latch_angle <= latch_angle:
            next_latch_angle += 2 * numpy.pi
        cuts.append(annular_sector(stem_radius, pocket_radius, latch_angle + web_half_angle,
                                   next_latch_angle - web_half_angle, arm_top - relief_fillet_radius, barb_base_height + 1,
                                   relief_fillet_radius))
    return cuts


def stadium(width, length):
    """Outline of two half circles joined by straight sides, long along y."""
    radius = width / 2
    straight = length / 2 - radius
    angles = numpy.linspace(0, numpy.pi, 33)
    top = [(radius * numpy.cos(angle), straight + radius * numpy.sin(angle)) for angle in angles]
    bottom = [(-radius * numpy.cos(angle), -straight - radius * numpy.sin(angle)) for angle in angles]
    return CrossSection([top + bottom])


def boss_solid():
    """An oval boss below the ceiling that the seal slips over; being oval, it holds the seal in line with the pin rows."""
    boss = stadium(boss_width, boss_length).extrude(boss_insertion + boss_plate_overlap)
    boss = boss.translate((0, 0, boss_face_height))
    return boss - Manifold.cylinder(boss_insertion * 3, channel_radius, channel_radius, 64).translate(
        (0, 0, boss_face_height - boss_insertion))


def vent_cuts():
    """One straight hole from outside through the wall, across the hollow and into the sound channel.

    A sealed air volume turns slow chest movement into pressure swings that overload the microphone; a drilled 0.8 mm
    hole let them escape in the recordings, while 0.5 mm did not. The tilted print narrows a small hole by about
    0.2 to 0.5 mm, so it is modelled at 1.0 mm to come out near 0.8 mm; a 0.8 mm drill trues it if it comes out smaller.
    """
    vent_height = (cavity_height + rubber_plate_thickness + barb_base_height - latch_root_thickness) / 2
    hole = Manifold.cylinder(outer_radius + 1, vent_diameter / 2, vent_diameter / 2, 32)
    hole = hole.rotate((0, 90, 0)).translate((0, 0, vent_height))
    return [hole.rotate((0, 0, numpy.degrees(vent_angle)))]


def vent_slot_cut(tilt, print_height_offset):
    """A slot through the stem wall, flat in the tilted print, exactly vent_slot_layers layers high.

    A round hole printed at a slant comes out narrower and sags at the top. A slot that runs level in the print gets
    its height from the layer count, which the printer holds exactly, and its roof is a short bridge across
    vent_slot_width. It only has to reach the hollow, which is open to the outside through the clip slits.
    """
    down = numpy.array([numpy.cos(tilt), 0.0, numpy.sin(tilt)])
    up = -down
    vent_height = (cavity_height + rubber_plate_thickness + barb_base_height - latch_root_thickness) / 2
    center = numpy.array([0.0, 0.0, vent_height])
    center_print_height = -(center @ down) - print_height_offset
    slot_height = vent_slot_layers * print_layer_height
    layers_below = round((center_print_height - slot_height / 2 - print_first_layer_height) / print_layer_height)
    slot_bottom = print_first_layer_height + layers_below * print_layer_height
    shift = slot_bottom + slot_height / 2 - center_print_height
    length = stem_radius + 0.6
    slot = Manifold.cube((vent_slot_width, length, slot_height), True).translate((0, length / 2, 0))
    # Turning about y by this angle points the slot's height along the print's up direction.
    slot = slot.rotate((0, numpy.degrees(numpy.arctan2(-numpy.cos(tilt), -numpy.sin(tilt))), 0))
    slot = slot.rotate((0, 0, numpy.degrees(vent_slot_angle) - 90))
    print(f"vent slot: {slot_height:.2f} mm high from print height {slot_bottom:.2f} to {slot_bottom + slot_height:.2f} mm, "
          f"{vent_slot_width} mm wide")
    return slot.translate(tuple(center + up * shift))


def print_flat_cut():
    """Flat on the housing so the part can lie on its side, which puts the print layers along the latch tabs."""
    height = barb_base_height - skirt_bottom + 2
    block = Manifold.cube((4 * outer_radius, outer_radius, height))
    block = block.translate((-2 * outer_radius, outer_radius - print_flat_depth, skirt_bottom - 1))
    return block.rotate((0, 0, numpy.degrees(print_flat_angle) - 90))


def lay_on_print_flat(vertices):
    rotated = vertices @ numpy.array([[numpy.cos(print_flat_angle - numpy.pi / 2), -numpy.sin(print_flat_angle - numpy.pi / 2), 0],
                                      [numpy.sin(print_flat_angle - numpy.pi / 2), numpy.cos(print_flat_angle - numpy.pi / 2), 0],
                                      [0, 0, 1]])
    return numpy.column_stack([rotated[:, 0], rotated[:, 2], -rotated[:, 1]])


def plate_tilt(vertices):
    """Tilt at which the tube tip and the housing shoulder next to a notch key both touch the build plate."""
    tube = vertices[vertices[:, 2] > barb_base_height + barb_length / 2]
    housing = vertices[vertices[:, 2] <= barb_base_height + 0.01]

    def down_direction(tilt):
        return numpy.array([numpy.cos(tilt), 0.0, numpy.sin(tilt)])

    low, high = 0.0, numpy.pi / 2
    for _ in range(60):
        tilt = (low + high) / 2
        if (tube @ down_direction(tilt)).max() < (housing @ down_direction(tilt)).max():
            low = tilt
        else:
            high = tilt
    return tilt


def rest_on_tip_and_housing_edge(vertices):
    """Tilt the part until the tube tip and the housing shoulder next to a notch key both touch the build plate."""
    tilt = plate_tilt(vertices)
    down = numpy.array([numpy.cos(tilt), 0.0, numpy.sin(tilt)])
    along = numpy.array([-numpy.sin(tilt), 0.0, numpy.cos(tilt)])
    print(f"sound channel tilt above the build plate: {numpy.degrees(tilt):.1f} degrees")
    return numpy.column_stack([vertices @ along, vertices[:, 1], -(vertices @ down)])


def build_solid(orientation="tilted"):
    """The adapter in its working position: board top at z = 0 when pushed fully in, tube upward."""
    vertices, triangles = revolve(adapter_profile())
    assert_watertight(triangles)
    solid = Manifold(Mesh(vert_properties=vertices.astype(numpy.float32), tri_verts=triangles.astype(numpy.uint32)))
    solid = solid + boss_solid()
    for cut in latch_tab_cuts() + material_relief_cuts() + ([print_flat_cut()] if orientation == "side" else []):
        solid = solid - cut
    if orientation != "tilted":
        return solid - vent_cuts()[0]
    body = numpy.array(solid.to_mesh().vert_properties, dtype=float)[:, :3]
    tilt = plate_tilt(body)
    down = numpy.array([numpy.cos(tilt), 0.0, numpy.sin(tilt)])
    print_height_offset = (-(body @ down)).min() + tilted_contact_depth
    return solid - vent_slot_cut(tilt, print_height_offset)


def main():
    output_path = Path(sys.argv[1])
    orientation = sys.argv[2] if len(sys.argv) > 2 else "side"
    solid = build_solid(orientation)
    if solid.is_empty() or solid.genus() < 1:
        raise ValueError(f"Unexpected solid after cutting latch tabs: {solid.status()}")
    mesh = solid.to_mesh()
    vertices = numpy.array(mesh.vert_properties, dtype=float)[:, :3]
    triangles = numpy.array(mesh.tri_verts, dtype=int)
    assert_watertight(triangles)
    if orientation == "tip_down":
        vertices = vertices * numpy.array([1, -1, -1])
    elif orientation == "tilted":
        vertices = rest_on_tip_and_housing_edge(vertices)
        vertices[:, 2] -= vertices[:, 2].min()
        # Two point contacts cannot hold the print, so the lowest sliver is cut off to leave two small flats.
        resting = Manifold(Mesh(vert_properties=vertices.astype(numpy.float32), tri_verts=triangles.astype(numpy.uint32)))
        resting = resting ^ Manifold.cube((200, 200, 200)).translate((-100, -100, tilted_contact_depth))
        mesh = resting.to_mesh()
        vertices = numpy.array(mesh.vert_properties, dtype=float)[:, :3]
        triangles = numpy.array(mesh.tri_verts, dtype=int)
    else:
        vertices = lay_on_print_flat(vertices)
    vertices[:, 2] -= vertices[:, 2].min()
    write_binary_stl(output_path, vertices, triangles)
    print(f"triangles: {len(triangles)}")
    print(f"volume: {signed_volume(vertices, triangles) / 1000:.3f} cm^3")
    print(f"bounding box: {vertices.min(axis=0).round(3)} to {vertices.max(axis=0).round(3)}")


if __name__ == "__main__":
    main()
