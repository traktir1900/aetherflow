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

    # Dominion x2.5: these prop dimensions are not yet config-driven (see
    # report "remaining cleanup" item) -- scaled inline x2.5 for this
    # migration: radius1 4.5->11.25, radius2 4.0->10.0, depth 0.8->2.0, z-offset 0.4->1.0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=11.25, radius2=10.0, depth=2.0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=center_pos + Vector((0, 0, 1.0)))
    finalize_bmesh(bm, "Altar_Base", "CapturePoints", ctx.get_material("altar"), ctx)

    # Dominion x2.5: radius 1.4->3.5, z-offset 2.0->5.0
    bm_core = bmesh.new()
    bmesh.ops.create_icosphere(bm_core, subdivisions=2, radius=3.5)
    bmesh.ops.translate(bm_core, verts=bm_core.verts, vec=center_pos + Vector((0, 0, 5.0)))
    finalize_bmesh(bm_core, "Altar_PowerCore", "CapturePoints", ctx.get_material("altar_glow"), ctx)

    for side, ang in [("West", 180.0), ("East", 0.0)]:
        dir_vec = polar(1.0, ang)
        perp_vec = Vector((-dir_vec.y, dir_vec.x, 0))
        choke_center = center + dir_vec * cfg["center_radius"]
        choke_z = get_height_at_point(choke_center, cfg, ctx.layout)
        
        for p_sign in [-1, 1]:
            # Dominion x2.5: lateral clearance addend 2.5->6.25 (flank_choke_width itself already scaled via config)
            rock_pos = choke_center + perp_vec * (cfg["flank_choke_width"] / 2.0 + 6.25) * p_sign
            rock_pos.z = choke_z
            bm_r = bmesh.new()
            # Dominion x2.5: radius1 2.8->7.0, radius2 1.5->3.75, depth 4.5->11.25
            bmesh.ops.create_cone(bm_r, cap_ends=True, segments=7, radius1=7.0, radius2=3.75, depth=11.25)
            bmesh.ops.translate(bm_r, verts=bm_r.verts, vec=rock_pos + Vector((0, 0, 5.625)))
            finalize_bmesh(bm_r, f"Core_ChokeRock_{side}_{p_sign}", "Rocks", ctx.get_material("rock"), ctx)
