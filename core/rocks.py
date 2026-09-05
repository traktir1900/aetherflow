"""
AetherFlow :: core/rocks.py
Procedural rock generator.

Rock generation remains seeded and varied, but central gameplay rocks are now
created as exact geometric mirror pairs across the world Y axis.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh


def make_rock(ctx, name, position, radius, collection_key="Rocks", material=None,
              element=None):
    cfg = ctx.config
    rock_cfg = cfg.get("rock", {})
    irregularity = rock_cfg.get("irregularity", 0.32)
    rng = ctx.rng

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)

    for v in bm.verts:
        n = v.normal
        disp = rng.uniform(-irregularity, irregularity) * radius
        v.co += n * disp
        if v.co.z < -radius * 0.55:
            v.co.z = -radius * 0.55 + rng.uniform(0.0, radius * 0.08)

    sx = rng.uniform(0.85, 1.25)
    sy = rng.uniform(rock_cfg.get("scale_y_min", 0.7), rock_cfg.get("scale_y_max", 1.15))
    sz = rng.uniform(0.8, 1.2)
    bmesh.ops.scale(bm, vec=Vector((sx, sz, sy)), verts=bm.verts)

    yaw = rng.uniform(0.0, math.pi * 2.0)
    bmesh.ops.rotate(
        bm,
        cent=Vector((0, 0, 0)),
        matrix=Matrix.Rotation(yaw, 4, 'Z'),
        verts=bm.verts,
    )

    for f in bm.faces:
        f.smooth = True

    ground_z = get_height_at_point(position, cfg, ctx.layout)
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=Vector((position.x, position.y, ground_z + radius * 0.35)),
    )

    mat = material or ctx.get_material("rock")
    meta = {"footprint_radius": radius, "yaw_deg": yaw * 180.0 / math.pi}
    if element is not None:
        meta["element"] = element
    return finalize_bmesh(
        bm, name, collection_key, mat, ctx, kind="rock",
        dims=(radius * 2 * sx, radius * 2 * sz, radius * 2 * sy),
        meta=meta,
    )


def _mirror_rock_object(ctx, source, name, collection_key="Rocks"):
    """Create a true geometric mirror of a generated rock across world Y axis."""
    src_mesh = source.data
    mesh = src_mesh.copy()
    for vert in mesh.vertices:
        vert.co.x = -vert.co.x
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector((-source.location.x, source.location.y, source.location.z))
    ctx.get_collection(collection_key).objects.link(obj)
    for mat in src_mesh.materials:
        obj.data.materials.append(mat)

    src_rec = next((r for r in ctx.generated_objects if r.get("object") == source), None)
    dims = tuple(src_rec.get("dimensions") or ()) if src_rec else ()
    src_meta = dict(src_rec.get("meta") or {}) if src_rec else {}
    yaw = float(src_meta.get("yaw_deg", 0.0))
    meta = dict(src_meta)
    meta["yaw_deg"] = (180.0 - yaw) % 360.0
    meta["mirror_source"] = source.name
    meta["mirror_rule"] = "(x,y,z) -> (-x,y,z)"
    meta["gameplay_symmetry"] = True
    meta["symmetry_axis"] = "Y_AXIS"
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
    """Generate central gameplay rocks as exact geometric mirror pairs.

    The previous implementation independently randomized every rock. That is
    now prohibited for central combat geometry because it can change LOS,
    movement cover and engagement space for one team only. An even core-rock
    count is therefore a hard invariant.
    """
    cfg = ctx.config
    rock_cfg = cfg.get("rock", {})
    count = int(count or rock_cfg.get("count_core", 6))
    if count % 2 != 0:
        raise ValueError("Core gameplay rocks require an even count for symmetry")

    ring = ring_radius or (cfg["center_radius"] + cfg["core_transition_radius"] * 0.6)
    pair_count = count // 2
    objs = []

    # Canonical positions are always on the +X half-plane. Their true geometric
    # mirrors occupy -X. Y coordinates cover both front/back portions.
    if pair_count == 1:
        angles = [0.0]
    else:
        span = math.radians(160.0)
        start = -span * 0.5
        step = span / float(pair_count - 1)
        angles = [start + step * i for i in range(pair_count)]

    for pair_index, ang in enumerate(angles, 1):
        if abs(math.cos(ang)) < 0.08:
            ang += math.radians(7.5 if math.sin(ang) >= 0.0 else -7.5)

        r = ring + ctx.rand(-ring * 0.10, ring * 0.10)
        radius = ctx.rand(rock_cfg.get("radius_min", 1.0), rock_cfg.get("radius_max", 2.0))
        x = math.cos(ang) * r
        y = math.sin(ang) * r
        right_pos = Vector((x, y, 0.0))

        # Generate one canonical rock, then create an actual mesh mirror. This
        # preserves identical proportions/irregularity while also mirroring the
        # irregular silhouette itself, not merely copying the same mesh.
        right = make_rock(ctx, "Core_Rock_{:02d}".format(pair_index + pair_count), right_pos, radius)
        left = _mirror_rock_object(ctx, right, "Core_Rock_{:02d}".format(pair_index))

        pair_id = "CORE_{:02d}".format(pair_index)
        _tag_symmetry(ctx, [left.name, right.name], pair_id)
        objs.extend((left, right))

    return objs
