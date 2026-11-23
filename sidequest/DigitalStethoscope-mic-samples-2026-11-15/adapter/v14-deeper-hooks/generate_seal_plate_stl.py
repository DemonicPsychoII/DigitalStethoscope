"""All three seal variants side by side in print orientation, as one model for one TPU job.

Usage: generate_seal_plate_stl.py <output stl>
The variant with lip interference 0.2, 0.3 and 0.4 mm carries 1, 2 and 3 pits on its lower face, next to the lip.
"""
import sys

import numpy
from manifold3d import Manifold

import generate_adapter_stl as adapter
import generate_seal_stl as seal_design

VARIANTS = (0.2, 0.3, 0.4)
SPACING = seal_design.seal_width + 4

plate = Manifold()
for index, interference in enumerate(VARIANTS):
    seal = seal_design.build_seal(interference, marker_count=index + 1)
    printed = seal.mirror((0, 0, 1))
    printed = printed.translate((index * SPACING, 0, -printed.bounding_box()[2]))
    plate = plate + printed
mesh = plate.to_mesh()
vertices = numpy.array(mesh.vert_properties, dtype=float)[:, :3]
triangles = numpy.array(mesh.tri_verts, dtype=int)
adapter.assert_watertight(triangles)
adapter.write_binary_stl(sys.argv[1], vertices, triangles)
print(f"{len(plate.decompose())} seals, bounding box {vertices.min(axis=0).round(2)} to {vertices.max(axis=0).round(2)}")
