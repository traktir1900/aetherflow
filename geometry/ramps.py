import bmesh
import math
from mathutils import Vector, Matrix
from core.heightmap import get_height_at_point
from core.layout import polar
from core.utils import finalize_bmesh

def generate_ramps_and_ledges(ctx):
    cfg = ctx.config
    ramp_cfg = cfg["ramps"]
    ledge_cfg = cfg["monolith_ledges"]
    mat_stone = ctx.get_material("stone")

    # 1. Северная Игровая Рампа (Crown -> Core)
    crown_pos = ctx.layout["Crown"]
    core_north_gate = polar(cfg["center_radius"], 90.0)
    core_north_gate.z = cfg["heights"]["AetherCore"]

    _build_smooth_combat_ramp(
        "North_CombatRamp_Crown_Core",
        crown_pos,
        core_north_gate,
        width=ramp_cfg["combat_width"],
        res=ramp_cfg["step_resolution"],
        material=mat_stone,
        ctx=ctx
    )

    # 2. Высотные Карнизы Monolith (West & East Ledges)
    ledge_thick = cfg["metrics"]["ledge_thickness"]
    for mono_name in ["WestMonolith", "EastMonolith"]:
        mono_pos = ctx.layout[mono_name].copy()
        mono_pos.z = get_height_at_point(mono_pos, cfg, ctx.layout)

        dir_to_center = (Vector((0, 0, 0)) - Vector((mono_pos.x, mono_pos.y, 0))).normalized()
        ledge_center = mono_pos + dir_to_center * ledge_cfg["ledge_offset"]
        ledge_center.z += ledge_cfg["high_ground_extra"]

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(
            bm,
            vec=Vector((ledge_cfg["ledge_width"], ledge_cfg["ledge_depth"], ledge_thick)),
            verts=bm.verts
        )
        
        angle_z = math.atan2(dir_to_center.y, dir_to_center.x)
        rot_mat = Matrix.Rotation(angle_z, 4, 'Z')
        bmesh.ops.transform(bm, matrix=rot_mat, verts=bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts, vec=ledge_center)

        finalize_bmesh(bm, f"HighGround_Ledge_{mono_name}", "CapturePoints", mat_stone, ctx)

        _build_smooth_combat_ramp(
            f"Ledge_AccessRamp_{mono_name}",
            mono_pos,
            ledge_center,
            width=ramp_cfg["min_width"],
            res=6,
            material=mat_stone,
            ctx=ctx
        )

def _build_smooth_combat_ramp(name, p_start, p_end, width, res, material, ctx):
    cfg = ctx.config
    delta = p_end - p_start
    if delta.length < cfg["metrics"]["min_delta_threshold"]:
        return

    bm = bmesh.new()
    flat_dir = Vector((delta.x, delta.y, 0.0)).normalized()
    perp_vec = Vector((-flat_dir.y, flat_dir.x, 0.0)) * (width / 2.0)

    prev_left, prev_right = None, None

    for i in range(res + 1):
        t = i / res
        smooth_t = t * t * (3.0 - 2.0 * t)
        
        curr_x = p_start.x + delta.x * t
        curr_y = p_start.y + delta.y * t
        
        terrain_z = get_height_at_point(Vector((curr_x, curr_y, 0.0)), cfg, ctx.layout)
        target_z = p_start.z + delta.z * smooth_t
        curr_z = max(terrain_z, target_z) + cfg["road_z_offset"]

        curr_center = Vector((curr_x, curr_y, curr_z))
        
        v_left = bm.verts.new(curr_center - perp_vec)
        v_right = bm.verts.new(curr_center + perp_vec)

        if prev_left and prev_right:
            try:
                bm.faces.new((prev_left, prev_right, v_right, v_left))
            except ValueError:
                pass

        prev_left, prev_right = v_left, v_right

    finalize_bmesh(bm, name, "Roads", material, ctx)
