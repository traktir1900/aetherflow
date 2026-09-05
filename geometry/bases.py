import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.layout import RING_NODES
from core.utils import finalize_bmesh

def generate_capture_points(ctx):
    cfg = ctx.config
    plat_r = cfg["capture_platform_radius"]
    plat_h = cfg["capture_platform_height"]

    for pname in RING_NODES:
        pos = ctx.layout[pname].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=cfg["circle_segments"], radius1=plat_r, radius2=plat_r, depth=plat_h)
        bmesh.ops.translate(bm, verts=bm.verts, vec=pos + Vector((0, 0, plat_h / 2.0)))
        finalize_bmesh(bm, f"CapturePlatform_{pname}", "CapturePoints", ctx.get_material("stone"), ctx)

        dir_vec = Vector((pos.x, pos.y, 0.0)).normalized()
        turret_pos = pos + dir_vec * cfg["turret_offset"]
        turret_pos.z = get_height_at_point(turret_pos, cfg, ctx.layout)
        
        bm_t = bmesh.new()
        bmesh.ops.create_cone(bm_t, cap_ends=True, segments=12, radius1=1.8, radius2=0.9, depth=4.0)
        bmesh.ops.translate(bm_t, verts=bm_t.verts, vec=turret_pos + Vector((0, 0, 2.0)))
        finalize_bmesh(bm_t, f"Turret_{pname}", "CapturePoints", ctx.get_material("stone"), ctx)

def generate_bases(ctx):
    cfg = ctx.config
    plat_r = cfg["base_platform_radius"]

    for team, base_key, mat_team, mat_cryst in [
        ("Blue", "BlueBase", ctx.get_material("blue_team"), ctx.get_material("blue_crystal")),
        ("Red", "RedBase", ctx.get_material("red_team"), ctx.get_material("red_crystal"))
    ]:
        pos = ctx.layout[base_key].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=plat_r, radius2=plat_r, depth=cfg["base_platform_height"])
        bmesh.ops.translate(bm, verts=bm.verts, vec=pos + Vector((0, 0, cfg["base_platform_height"] / 2.0)))
        finalize_bmesh(bm, f"{team}_BasePlatform", "Bases", mat_team, ctx)

        bm_c = bmesh.new()
        bmesh.ops.create_icosphere(bm_c, subdivisions=2, radius=2.0)
        bmesh.ops.translate(bm_c, verts=bm_c.verts, vec=pos + Vector((0, 0, 4.0)))
        finalize_bmesh(bm_c, f"{team}_Crystal", "Bases", mat_cryst, ctx)
