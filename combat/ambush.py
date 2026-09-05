import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

def generate_south_rift_ambush(ctx):
    south_mid = ctx.layout["SouthRift"]
    rift_z = get_height_at_point(south_mid, ctx.config, ctx.layout)
    
    offsets = [Vector((-6.0, 2.0, 0)), Vector((6.0, -2.0, 0))]
    for i, off in enumerate(offsets):
        r_pos = south_mid + off
        r_pos.z = rift_z
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=3.2)
        bmesh.ops.scale(bm, vec=Vector((1.4, 0.9, 1.1)), verts=bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts, vec=r_pos + Vector((0, 0, 1.5)))
        finalize_bmesh(bm, f"SouthRift_LoSRock_{i+1}", "Rocks", ctx.get_material("rock"), ctx)
