"""
AetherFlow :: core/rocks.py
Procedural rock generator.

Rock generation remains seeded and varied, but team-critical / central gameplay
rocks are now generated as exact mirror pairs across the world Y axis.
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

    import math
    import mathutils
    yaw = rng.uniform(0.0, math.pi * 2.0)
    bmesh.ops.rotate(
        bm,
        cent=Vector((0, 0, 0)),
        matrix=mathutils.Matrix.Rotation(yaw, 4, 'Z'),
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
    obj = finalize_bmesh(
        bm, name, collection_key, mat, ctx, kind="rock",
        dims=(radius * 2 * sx, radius * 2 * sz, radius * 2 * sy),
        meta=meta,
    )
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
    """Generate central rocks as exact mirror pairs for gameplay fairness.

    The old implementation independently randomized every rock, which could
    create a geometry advantage for one team. Central rocks are team-critical
    because they shape the AetherCore combat space, so an even count is now a
    hard invariant. Each pair uses one canonical seed/state, then regenerates
    the identical mesh on the mirrored position x -> -x.
    """
    cfg = ctx.config
    rock_cfg = cfg.get("rock", {})
    count = int(count or rock_cfg.get("count_core", 6))
    if count % 2 != 0:
        raise ValueError("Core gameplay rocks require an even count for symmetry")

    ring = ring_radius or (cfg["center_radius"] + cfg["core_transition_radius"] * 0.6)
    pair_count = count // 2
    objs = []

    import math

    # Canonical positions occupy the right half of the arena. Their exact
    # mirrors populate the left half. This gives balanced spatial distribution
    # without placing two rocks on the symmetry axis.
    if pair_count == 1:
        angles = [0.0]
    else:
        span = math.radians(160.0)
        start = -span * 0.5
        step = span / float(pair_count - 1)
        angles = [start + step * i for i in range(pair_count)]

    for pair_index, ang in enumerate(angles, 1):
        # x is non-negative in this canonical half. Avoid the Y axis by nudging
        # the exact midpoint slightly; its mirror would otherwise overlap it.
        if abs(math.cos(ang)) < 0.08:
            ang += math.radians(7.5 if math.sin(ang) >= 0.0 else -7.5)

        r = ring + ctx.rand(-ring * 0.10, ring * 0.10)
        radius = ctx.rand(rock_cfg.get("radius_min", 1.0), rock_cfg.get("radius_max", 2.0))
        x = math.cos(ang) * r
        y = math.sin(ang) * r
        left_pos = Vector((-x, y, 0.0))
        right_pos = Vector((x, y, 0.0))

        # Generate identical geometry twice by replaying exactly the same RNG
        # state. The terrain profile is itself symmetry-controlled, so the two
        # mirrored anchors receive the same ground height.
        state = ctx.rng.getstate()
        left = make_rock(ctx, "Core_Rock_{:02d}".format(pair_index), left_pos, radius)
        ctx.rng.setstate(state)
        right = make_rock(ctx, "Core_Rock_{:02d}".format(pair_index + pair_count), right_pos, radius)

        pair_id = "CORE_{:02d}".format(pair_index)
        _tag_symmetry(ctx, [left.name, right.name], pair_id)
        objs.extend((left, right))

    return objs
