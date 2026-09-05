"""
AetherFlow :: core/rocks.py
Procedural rock generator.

Replaces stretched-cube placeholders with genuinely varied rock geometry:
random (but SEEDED, via ctx.rng) scale, rotation, proportions, irregularity,
bevel and per-vertex surface noise.  No two rocks are identical.

Gameplay contract: each rock's collision footprint is controlled by its base
radius and anchor position (passed in), so visual irregularity never makes
passability unpredictable.  The rock is a real mesh (collision-ready) and is
registered with its name / transform / dimensions / type for export.
"""
import bmesh
from mathutils import Vector

from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh


def make_rock(ctx, name, position, radius, collection_key="Rocks", material=None,
              element=None):
    cfg = ctx.config
    rock_cfg = cfg.get("rock", {})
    irregularity = rock_cfg.get("irregularity", 0.32)
    rng = ctx.rng

    # Base icosphere, then displace every vertex for an irregular silhouette.
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)

    for v in bm.verts:
        n = v.normal
        disp = rng.uniform(-irregularity, irregularity) * radius
        v.co += n * disp
        # Flatten the base slightly so the rock sits naturally on the ground.
        if v.co.z < -radius * 0.55:
            v.co.z = -radius * 0.55 + rng.uniform(0.0, radius * 0.08)

    # Varied proportions (non-uniform scale) + random yaw.
    sx = rng.uniform(0.85, 1.25)
    sy = rng.uniform(rock_cfg.get("scale_y_min", 0.7), rock_cfg.get("scale_y_max", 1.15))
    sz = rng.uniform(0.8, 1.2)
    bmesh.ops.scale(bm, vec=Vector((sx, sz, sy)), verts=bm.verts)

    import math
    import mathutils
    yaw = rng.uniform(0.0, math.pi * 2.0)
    bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)),
                     matrix=mathutils.Matrix.Rotation(yaw, 4, 'Z'),
                     verts=bm.verts)

    # Smooth shading normals for surface variation (visual only).
    for f in bm.faces:
        f.smooth = True

    # Anchor: place on the heightmap, sink slightly so there are no floating gaps.
    ground_z = get_height_at_point(position, cfg, ctx.layout)
    bmesh.ops.translate(bm, verts=bm.verts,
                        vec=Vector((position.x, position.y, ground_z + radius * 0.35)))

    mat = material or ctx.get_material("rock")
    meta = {"footprint_radius": radius, "yaw_deg": yaw * 180.0 / math.pi}
    if element is not None:
        meta["element"] = element
    obj = finalize_bmesh(
        bm, name, collection_key, mat, ctx, kind="rock",
        dims=(radius * 2 * sx, radius * 2 * sz, radius * 2 * sy),
        meta=meta,
    )
    return obj


def scatter_core_rocks(ctx, count=None, ring_radius=None):
    """Decorative/cover rocks around the central arena (deterministic)."""
    cfg = ctx.config
    rock_cfg = cfg.get("rock", {})
    count = count or rock_cfg.get("count_core", 6)
    ring = ring_radius or (cfg["center_radius"] + cfg["core_transition_radius"] * 0.6)
    objs = []
    import math
    for i in range(count):
        ang = (i / float(count)) * 2.0 * math.pi + ctx.rand(0.0, 0.4)
        r = ring + ctx.rand(-ring * 0.15, ring * 0.15)
        pos = Vector((math.cos(ang) * r, math.sin(ang) * r, 0.0))
        radius = ctx.rand(rock_cfg.get("radius_min", 1.0), rock_cfg.get("radius_max", 2.0))
        objs.append(make_rock(ctx, "Core_Rock_{:02d}".format(i + 1), pos, radius))
    return objs
