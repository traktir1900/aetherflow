"""
AetherFlow :: geometry/terrain.py
Generates the REAL playable terrain from the analytic heightmap.

Design note: the historical object was called "Terrain_Heightmap_DEBUG".  It
WAS the real terrain (the DEBUG suffix only referred to the height-tint vertex
colors).  Here the geometry is produced as first-class terrain ("Terrain_Real")
and the height-tint is kept strictly as an optional debug visualization, so the
real terrain is never mistaken for, or removed as, a debug helper.
"""
import bpy
import bmesh
from mathutils import Vector

from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh


def _height_tint(z, cfg):
    """Optional debug vertex color by elevation (visualization only)."""
    crown = cfg["heights"]["Crown"]
    if crown <= 0:
        crown = 1.0
    t = max(0.0, min(1.0, (z - cfg["heights"]["AetherCore"]) / (crown - cfg["heights"]["AetherCore"])))
    return (0.2 + 0.6 * t, 0.2 + 0.6 * t, 0.25 + 0.6 * t, 1.0)


def generate_terrain(ctx, debug_tint=True):
    cfg = ctx.config
    size = cfg.get("world_floor_half_size", cfg["ground_half_size"])
    res = cfg["terrain_resolution"]
    step = (size * 2.0) / res

    bm = bmesh.new()
    vcol_layer = bm.loops.layers.color.new("HeightDebug") if debug_tint else None

    grid = []
    for row in range(res + 1):
        y = -size + row * step
        line = []
        for col in range(res + 1):
            x = -size + col * step
            z = get_height_at_point(Vector((x, y, 0.0)), cfg, ctx.layout)
            line.append(bm.verts.new((x, y, z)))
        grid.append(line)

    for r in range(res):
        for c in range(res):
            v0, v1, v2, v3 = grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]
            face = bm.faces.new((v0, v1, v2, v3))
            if vcol_layer:
                for loop in face.loops:
                    loop[vcol_layer] = _height_tint(loop.vert.co.z, cfg)

    obj = finalize_bmesh(
        bm, "Terrain_Real", "Terrain",
        ctx.get_material("height_debug" if debug_tint else "ground"),
        ctx, kind="terrain",
        dims=(size * 2.0, size * 2.0, None),
        meta={"resolution": res, "safety_floor_z": cfg.get("safety_floor_z")},
    )
    return obj


def generate_safety_floor(ctx):
    """A solid slab far below the map so a player can never fall forever."""
    cfg = ctx.config
    size = cfg.get("world_floor_half_size", cfg["ground_half_size"]) * 1.2
    z = cfg.get("safety_floor_z", -6.0) - 0.5

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((size * 2.0, size * 2.0, 1.0)), verts=bm.verts)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((0, 0, z)))
    finalize_bmesh(bm, "Terrain_SafetyFloor", "Terrain",
                   ctx.get_material("ground"), ctx, kind="safety_floor",
                   dims=(size * 2.0, size * 2.0, 1.0))
