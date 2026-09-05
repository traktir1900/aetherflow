import bmesh
from mathutils import Vector
from core.layout import polar
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

def generate_core_and_entrances(ctx):
    cfg = ctx.config
    center = ctx.layout["Center"]
    core_z = cfg["heights"]["AetherCore"]
    center_pos = Vector((center.x, center.y, core_z))

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=4.5, radius2=4.0, depth=0.8)
    bmesh.ops.translate(bm, verts=bm.verts, vec=center_pos + Vector((0, 0, 0.4)))
    finalize_bmesh(bm, "Altar_Base", "CapturePoints", ctx.get_material("altar"), ctx)

    bm_core = bmesh.new()
    bmesh.ops.create_icosphere(bm_core, subdivisions=2, radius=1.4)
    bmesh.ops.translate(bm_core, verts=bm_core.verts, vec=center_pos + Vector((0, 0, 2.0)))
    finalize_bmesh(bm_core, "Altar_PowerCore", "CapturePoints", ctx.get_material("altar_glow"), ctx)

    for side, ang in [("West", 180.0), ("East", 0.0)]:
        dir_vec = polar(1.0, ang)
        perp_vec = Vector((-dir_vec.y, dir_vec.x, 0))
        choke_center = center + dir_vec * cfg["center_radius"]
        choke_z = get_height_at_point(choke_center, cfg, ctx.layout)
        
        for p_sign in [-1, 1]:
            rock_pos = choke_center + perp_vec * (cfg["flank_choke_width"] / 2.0 + 2.5) * p_sign
            rock_pos.z = choke_z
            bm_r = bmesh.new()
            bmesh.ops.create_cone(bm_r, cap_ends=True, segments=7, radius1=2.8, radius2=1.5, depth=4.5)
            bmesh.ops.translate(bm_r, verts=bm_r.verts, vec=rock_pos + Vector((0, 0, 2.25)))
            finalize_bmesh(bm_r, f"Core_ChokeRock_{side}_{p_sign}", "Rocks", ctx.get_material("rock"), ctx)
