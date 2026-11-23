"""Write a self-contained three.js page that shows adapter v13, the seal and the board exploded and cut open.

Usage: build_render_page.py <html page>
"""
import base64
import sys

import numpy
from manifold3d import Manifold

import generate_adapter_stl as adapter
import generate_seal_stl as seal_design


def stl_base64(part):
    mesh = part.to_mesh()
    vertices = numpy.array(mesh.vert_properties, dtype=float)[:, :3]
    triangles = numpy.array(mesh.tri_verts, dtype=int)
    path = "render_part.stl"
    adapter.write_binary_stl(path, vertices, triangles)
    return base64.b64encode(open(path, "rb").read()).decode()


board_top = seal_design.latched_board_top
board = Manifold.cylinder(adapter.pcb_thickness, adapter.pcb_diameter / 2, adapter.pcb_diameter / 2, 96)
board = board.translate((0, 0, board_top - adapter.pcb_thickness))
for key_angle in adapter.key_angles:
    center = (adapter.key_center_distance * numpy.cos(key_angle), adapter.key_center_distance * numpy.sin(key_angle), -5)
    board = board - Manifold.cylinder(10, adapter.notch_radius, adapter.notch_radius, 48).translate(center)
board = board - Manifold.cylinder(10, 0.4, 0.4, 24).translate((0, 0, -5))
for row in (-3.9, 3.9):
    for along in (-2.54, 0, 2.54):
        board = board + Manifold.cylinder(adapter.pin_stub_height, 0.85, 0.85, 24).translate((row, along, board_top))

parts = {"adapter": stl_base64(adapter.build_solid("tilted")), "seal": stl_base64(seal_design.build_seal()),
         "board": stl_base64(board)}

page = """<!doctype html><html><head><meta charset="utf-8"><style>
.wrap{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
canvas{width:100%;height:440px;display:block;border-radius:var(--radius);background:var(--card)}
.label{font-size:14px;color:var(--muted-foreground);margin-top:4px}
.legend{display:flex;gap:18px;font-size:14px;margin-top:10px;color:var(--muted-foreground)}
.legend span::before{content:"";display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:var(--swatch)}
@media (max-width:640px){.wrap{grid-template-columns:1fr}}
</style>
<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}</script>
</head><body>
<div class="wrap">
<div><canvas id="above"></canvas><div class="label">Exploded from above: the seal slips over the oval boss</div></div>
<div><canvas id="below"></canvas><div class="label">Exploded from below: lip ring around the sound port</div></div>
<div><canvas id="cut"></canvas><div class="label">Assembled and cut open along the seal</div></div>
</div>
<div class="legend"><span style="--swatch:#e6edf3">adapter, white PLA</span><span style="--swatch:#ff9f43">seal, TPU for AMS</span><span style="--swatch:#3fb950">mic board with pin stubs</span></div>
<script type="module">
import * as THREE from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
const parts = PARTS;
const colors = { adapter: 0xe6edf3, seal: 0xff9f43, board: 0x3fb950 };
const loader = new STLLoader();
const geometries = {};
for (const [name, data] of Object.entries(parts)) {
  geometries[name] = loader.parse(Uint8Array.from(atob(data), c => c.charCodeAt(0)).buffer);
  geometries[name].computeVertexNormals();
}
function view(id, offsets, cameraPosition, cut) {
  const canvas = document.getElementById(id);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(2);
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
  renderer.localClippingEnabled = true;
  const scene = new THREE.Scene();
  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(40, -60, 80);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.7);
  fill.position.set(-50, 40, -40);
  scene.add(fill);
  const planes = cut ? [new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0)] : [];
  for (const name of Object.keys(parts)) {
    const material = new THREE.MeshStandardMaterial({ color: colors[name], roughness: 0.6, metalness: 0.0,
      side: THREE.DoubleSide, clippingPlanes: planes });
    const mesh = new THREE.Mesh(geometries[name], material);
    mesh.position.z = offsets[name];
    scene.add(mesh);
  }
  const camera = new THREE.PerspectiveCamera(30, canvas.clientWidth / canvas.clientHeight, 1, 1000);
  camera.up.set(0, 0, 1);
  camera.position.set(...cameraPosition);
  camera.lookAt(0, 0, cut ? 4 : 22);
  renderer.render(scene, camera);
}
const exploded = { adapter: 22, seal: 9, board: 0 };
view("above", exploded, [80, -95, 95], false);
view("below", exploded, [85, -100, -45], false);
view("cut", { adapter: 0, seal: 0, board: 0 }, [48, -6, 14], true);
</script></body></html>"""
page = page.replace("PARTS", "{" + ", ".join(f'{name}: "{data}"' for name, data in parts.items()) + "}")
open(sys.argv[1], "w", encoding="utf-8").write(page)
print("page written,", len(page) // 1024, "kB")
