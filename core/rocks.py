"""
AetherFlow :: core/rocks.py
Procedural rock generator.

Central gameplay rocks are generated from one canonical +X-side rock per pair
and mirrored exactly across the world Y axis: (x, y, z) -> (-x, y, z).
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh


def _build_rock_mesh(ctx, radius, seed_rng):
    """Build one rock in LOCAL coordinates only.

    Keeping the mesh centered at its own origin is important: the world-space
    mirror is then represented by the object transform, so there can be no
    hidden translation baked into the mesh that makes one side look shifted.
    """
    cfg = ctx.config
    rock_cfg = cfg.get("rock", {})
    irregularity = float(rock_cfg.get("irregularity", 0.32))

    bm = bmesh.new()
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)

        for v in bm.verts:
            n = v.normal
            disp = seed_rng.uniform(-irregularity, irregularity) * radius
            v.co += n * disp
            if v.co.z < -radius * 0.55:
                v.co.z = -radius * 0.55 + seed_rng.uniform(0.0, radius * 0.08)

        sx = seed_rng.uniform(0.85, 1.25)
        sy = seed_rng.uniform(rock_cfg.get("scale_y_min", 0.7), rock_cfg.get("scale_y_max", 1.15))
        sz = seed_rng.uniform(0.8, 1.2)
        bmesh.ops.scale(bm, vec=Vector((sx, sz, sy)), verts=bm.verts)

        yaw = seed_rng.uniform(0.0, math.pi * 2.0)
        bmesh.ops.rotate(
            bm,
            cent=Vector((0.0, 0.0, 0.0)),
            matrix=Matrix.Rotation(yaw, 4, 'Z'),
            verts=bm.verts,
        )

        for f in bm.faces:
            f.smooth = True

        return bm, sx, sy, sz, yaw
    except Exception:
        bm.free()
        raise


def make_rock(ctx, name, position, radius, collection_key="Rocks", material=None,
              element=None, rng=None):
    """Create a rock whose mesh remains local and whose center is exact."""
    cfg = ctx.config
    rng = rng or ctx.rng
    bm, sx, sy, sz, yaw = _build_rock_mesh(ctx, radius, rng)

    ground_z = get_height_at_point(position, cfg, ctx.layout)
    world_position = Vector((float(position.x), float(position.y), float(ground_z)))
    mat = material or ctx.get_material("rock")
    meta = {
        "footprint_radius": float(radius),
        "yaw_deg": float(math.degrees(yaw)),
        "world_center": [round(world_position.x, 4), round(world_position.y, 4), round(world_position.z, 4)],
    }
    if element is not None:
        meta["element"] = element

    obj = finalize_bmesh(
        bm,
        name,
        collection_key,
        mat,
        ctx,
        kind="rock",
        dims=(radius * 2.0 * sx, radius * 2.0 * sz, radius * 2.0 * sy),
        meta=meta,
    )
    obj.location = world_position
    return obj


def _mirror_rock_object(ctx, source, name, collection_key="Rocks"):
    """Create an exact Y-axis mirror of a canonical rock."""
    src_mesh = source.data
    mesh = src_mesh.copy()

    # Mirror LOCAL geometry so the irregular silhouette itself is mirrored.
    for vert in mesh.vertices:
        vert.co.x = -float(vert.co.x)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    src_pos = source.location.copy()
    obj.location = Vector((-float(src_pos.x), float(src_pos.y), float(src_pos.z)))
    obj.rotation_euler = Vector((source.rotation_euler.x,
                                 source.rotation_euler.y,
                                 math.radians((180.0 - math.degrees(source.rotation_euler.z)) % 360.0)))
    obj.scale = source.scale.copy()
    ctx.get_collection(collection_key).objects.link(obj)

    for mat in src_mesh.materials:
        obj.data.materials.append(mat)

    src_rec = next((r for r in ctx.generated_objects if r.get("object") == source), None)
    dims = tuple(src_rec.get("dimensions") or ()) if src_rec else ()
    src_meta = dict(src_rec.get("meta") or {}) if src_rec else {}
    yaw = float(src_meta.get("yaw_deg", 0.0))
    meta = dict(src_meta)
    meta.update({
        "yaw_deg": (180.0 - yaw) % 360.0,
        "mirror_source": source.name,
        "mirror_rule": "(x,y,z) -> (-x,y,z)",
        "gameplay_symmetry": True,
        "symmetry_axis": "Y_AXIS",
        "world_center": [round(obj.location.x, 4), round(obj.location.y, 4), round(obj.location.z, 4)],
    })
    ctx.register(obj, "rock", dims=dims, meta=meta)
    return obj


def _tag_symmetry(ctx, names, pair_id):
    by_name = {rec.get("name"): rec for rec in ctx.generated_objects}
    for name in names:
        rec = by_name.get(name)
        if rec is None:
            continue
        meta = rec.setdefault("meta", {})
        meta["gameplay_symmetry"] = True
        meta["symmetry_axis"] = "Y_AXIS"
        meta["mirror_rule"] = "(x,y,z) -> (-x,y,z)"
        meta["symmetry_pair"] = pair_id
        meta["identical_geometry_pair"] = True


def scatter_core_rocks(ctx, count=None, ring_radius=None):
    """Generate central gameplay rocks as exact mirror pairs.

    Exactly one canonical rock is randomized for each pair. The mirrored rock
    receives the exact mirrored world center and a mirrored mesh. Both members
    therefore have identical size, height and gameplay footprint.
    """
    cfg = ctx.config
    rock_cfg = cfg.get("rock", {})
    count = int(count or rock_cfg.get("count_core", 6))
    if count % 2 != 0:
        raise ValueError("Core gameplay rocks require an even count for symmetry")

    ring = float(ring_radius or (cfg["center_radius"] + cfg["core_transition_radius"] * 0.6))
    pair_count = count // 2
    objs = []

    if pair_count == 1:
        angles = [0.0]
    else:
        span = math.radians(120.0)
        start = -span * 0.5
        step = span / float(pair_count - 1)
        angles = [start + step * i for i in range(pair_count)]

    # Keep canonical rocks comfortably away from the mirror plane so each pair
    # remains visibly distinct and cannot overlap the center line.
    min_x = max(5.0, ring * 0.42)

    for pair_index, ang in enumerate(angles, 1):
        r = ring + ctx.rand(-ring * 0.08, ring * 0.08)
        x = max(min_x, abs(math.cos(ang) * r))
        y = math.sin(ang) * r
        radius = ctx.rand(rock_cfg.get("radius_min", 1.0), rock_cfg.get("radius_max", 2.0))
        right_pos = Vector((x, y, 0.0))

        # One source of randomness only. The opposite side is never generated
        # independently, eliminating the old visible positional drift.
        right = make_rock(
            ctx,
            "Core_Rock_{:02d}".format(pair_index + pair_count),
            right_pos,
            radius,
        )
        left = _mirror_rock_object(
            ctx,
            right,
            "Core_Rock_{:02d}".format(pair_index),
        )

        pair_id = "CORE_{:02d}".format(pair_index)
        _tag_symmetry(ctx, [left.name, right.name], pair_id)
        objs.extend((left, right))

    return objs
