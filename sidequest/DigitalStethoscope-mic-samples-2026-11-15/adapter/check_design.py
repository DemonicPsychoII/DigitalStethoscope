import numpy

import generate_adapter_stl as adapter

arm_top = adapter.barb_base_height - adapter.latch_root_thickness
board_radius = adapter.pcb_diameter / 2
hook_tip_radius = adapter.pocket_radius - adapter.latch_depth
deflection = board_radius - hook_tip_radius
arm_length = arm_top - adapter.relief_fillet_radius / 2 - adapter.latch_catch_height
flat_strain = 1.5 * deflection * adapter.latch_tab_thickness / arm_length ** 2
arm_half_angle = adapter.latch_slit_angle
mean_radius = adapter.pocket_radius + adapter.latch_tab_thickness / 2
sagitta = mean_radius * (1 - numpy.cos(arm_half_angle))
print("latched board to ceiling", adapter.cavity_height + adapter.latch_clearance_below_pcb)
print("tube end above latched board", adapter.boss_face_height + adapter.latch_clearance_below_pcb)
print("hook reach under board", board_radius - hook_tip_radius)
print("arm bend needed", deflection, "arm length", round(arm_length, 2))
print("arm width", round(2 * mean_radius * arm_half_angle, 2), "curve depth", round(sagitta, 2))
print("strain flat arm %", round(100 * flat_strain, 2), "with curved section %",
      round(100 * flat_strain * (adapter.latch_tab_thickness + sagitta) / adapter.latch_tab_thickness, 2))
print("rim below latched board underside", -adapter.skirt_bottom - adapter.pcb_thickness - adapter.latch_clearance_below_pcb)
print("slit width", adapter.latch_slit_width, "barb ridges",
      [round(adapter.tube_inner_diameter_maximum + adapter.barb_oversize + adapter.barb_base_spread - i * adapter.barb_step, 2) for i in range(adapter.barb_count)])
print("wall at print flat", adapter.wall_thickness - adapter.print_flat_depth, "channel length", adapter.barb_base_height + adapter.barb_length - adapter.boss_face_height)
