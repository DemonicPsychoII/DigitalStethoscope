"""Confirm the vent connects the sound channel to the open hollow and the access hole lines up with it."""
import numpy
from manifold3d import Manifold

import check_mesh
import generate_adapter_stl as adapter

solid = check_mesh.build_solid()
height = (adapter.cavity_height + adapter.rubber_plate_thickness + adapter.barb_base_height - adapter.latch_root_thickness) / 2
angle = numpy.degrees(adapter.vent_angle)
print("vent height above board top", round(height, 2), "angle", angle)
print("material along the vent axis (expect None: free line from channel to outside)", check_mesh.radial_extent(solid, height, angle))
print("material 0.5 mm above the vent axis (stem, then wall)", check_mesh.radial_extent(solid, height + 0.5, angle))
needle = Manifold.cylinder(12, 0.2, 0.2, 24).rotate((0, 90, 0)).translate((0, 0, height)).rotate((0, 0, angle))
print("overlap of a 0.4 mm needle pushed in from outside mm3", round((solid ^ needle).volume(), 5))
for name, other in (("clip at 90", 90), ("notch key at 180", 180)):
    print(f"angle from vent to {name}: {abs(angle - other):.0f} degrees")
