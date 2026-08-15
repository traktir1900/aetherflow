import bmesh
import math
import mathutils
from mathutils import Vector
from core.utils import finalize_bmesh

def generate_core_combat_cover(ctx):
    cfg = ctx.config["core_cover"]
    core_z = ctx.config["heights"]["AetherCore"]

    p_size = cfg["north_pillar_size"]
    pillar_pos = Vector((0.0, 25.0 - cfg["north_pillar_offset"], core_z))
    bm_p = bmesh.new()
    bmesh.ops.create_cube(bm_p, size=1.0)
    bmesh.ops.scale(bm_p, vec=Vector(p_size), verts=bm_p.verts)
    bmesh.ops.translate(bm_p, verts=bm_p.verts, vec=pillar_pos + Vector((0, 0, p_size[2] / 2.0)))
    finalize_bmesh(bm_p, "Core_Cover_Pillar_North", "CoreCover", ctx.get_material("cover"), ctx)

    m_size = cfg["side_wall_main"]
    w_size = cfg["side_wall_wing"]
    for side, sign, angle in [("West", -1.0, math.radians(15.0)), ("East", 1.0, math.radians(-15.0))]:
        base_pos = Vector((sign * 27.5, 5.0, core_z))
        bm_l = bmesh.new()
        bmesh.ops.create_cube(bm_l, size=1.0)
        bmesh.ops.scale(bm_l, vec=Vector(m_size), verts=bm_l.verts)
        
        bm_w = bmesh.new()
        bmesh.ops.create_cube(bm_w, size=1.0)
        bmesh.ops.scale(bm_w, vec=Vector(w_size), verts=bm_w.verts)
        wing_offset = Vector((sign * (-m_size[0] / 2.0 + w_size[0] / 2.0), -m_size[1] / 2.0 - w_size[1] / 2.0, (w_size[2] - m_size[2]) / 2.0))
        bmesh.ops.translate(bm_w, verts=bm_w.verts, vec=wing_offset)

        for v in bm_w.verts:
            bm_l.verts.new(v.co)
        bm_w.free()

        bmesh.ops.rotate(bm_l, cent=Vector((0, 0, 0)), matrix=mathutils.Matrix.Rotation(angle, 4, 'Z'), verts=bm_l.verts)
        bmesh.ops.translate(bm_l, verts=bm_l.verts, vec=base_pos + Vector((0, 0, m_size[2] / 2.0)))
        finalize_bmesh(bm_l, f"Core_Cover_LCover_{side}", "CoreCover", ctx.get_material("cover"), ctx)

    pk_size = cfg["pocket_block_size"]
    for side, sign in [("SW", -1.0), ("SE", 1.0)]:
        pk_pos = Vector((sign * 18.75, -22.5, core_z))
        bm_pk = bmesh.new()
        bmesh.ops.create_cube(bm_pk, size=1.0)
        bmesh.ops.scale(bm_pk, vec=Vector(pk_size), verts=bm_pk.verts)
        bmesh.ops.rotate(bm_pk, cent=Vector((0, 0, 0)), matrix=mathutils.Matrix.Rotation(math.radians(sign * 25.0), 4, 'Z'), verts=bm_pk.verts)
        bmesh.ops.translate(bm_pk, verts=bm_pk.verts, vec=pk_pos + Vector((0, 0, pk_size[2] / 2.0)))
        finalize_bmesh(bm_pk, f"Core_Cover_Pocket_{side}", "CoreCover", ctx.get_material("cover"), ctx)

    s_size = cfg["south_screen_size"]
    s_pos = Vector((0.0, -35.0, core_z))
    bm_s = bmesh.new()
    bmesh.ops.create_cube(bm_s, size=1.0)
    bmesh.ops.scale(bm_s, vec=Vector(s_size), verts=bm_s.verts)
    bmesh.ops.translate(bm_s, verts=bm_s.verts, vec=s_pos + Vector((0, 0, s_size[2] / 2.0)))
    finalize_bmesh(bm_s, "Core_Cover_SouthScreen", "CoreCover", ctx.get_material("cover"), ctx)
