import bpy
import bmesh
from mathutils import Vector
from core.utils import finalize_bmesh

AMBUSH_ZONES = [
    {
        "name": "SouthRift_Main",
        "offset": Vector((4.0, 0.0, 1.0)),
        "scale": Vector((3.0, 2.0, 2.0)),
    }
]

def generate_ambush_ecology(ctx):
    mat_stone = ctx.get_material("stone")
    
    # Защищенное получение вектора: если ключ None, используем дефолтные координаты
    rift_pos = ctx.layout.get("SouthRift")
    if rift_pos is None:
        rift_pos = Vector((0.0, -40.0, 0.0))
    
    for zone in AMBUSH_ZONES:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=zone["scale"], verts=bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts, vec=rift_pos + zone["offset"])
        
        finalize_bmesh(bm, f"Ambush_{zone['name']}_Cover", "CombatCover", mat_stone, ctx)