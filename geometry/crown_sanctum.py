"""
AetherFlow :: geometry/crown_sanctum.py
Crown Boss Sanctum geometry for v0.6.3.2.

Gameplay intent:
  - Crown stays at its existing XY anchor.
  - A smooth radial elevation approaches the boss button instead of a hard step.
  - A large half-oval ruined coliseum surrounds the north/back half of the button.
  - The south/front side remains open for PvP approach and retreat.
  - The sanctum is symmetric across x=0.

Pocket reference: current enlarged pocket footprint is 28 x 18 m.
Sanctum footprint target is 15% larger: 32.2 x 20.7 m.
"""
import math
import bmesh
from mathutils import Vector, Matrix

from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh


COLLECTION = "CapturePoints"


def _cube(ctx, name, center, size, rot_z=0.0, kind="landmark", meta=None,
          material_key="stone"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if rot_z:
        bmesh.ops.rotate(
            bm,
            cent=Vector((0.0, 0.0, 0.0)),
            matrix=Matrix.Rotation(math.radians(rot_z), 4, "Z"),
            verts=bm.verts,
        )
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(center))
    return finalize_bmesh(
        bm, name, COLLECTION, ctx.get_material(material_key), ctx,
        kind=kind, dims=size, meta=meta or {},
    )


def _build_smooth_rise(ctx, center, ground_z, scfg):
    """Generate a smooth radial mound rising continuously into the boss button."""
    outer_r = float(scfg["rise_outer_radius_m"])
    inner_r = float(scfg["button_radius_m"])
    rise_h = float(scfg["rise_height_m"])
    segments = int(scfg.get("rise_segments", 40))
    rings = int(scfg.get("rise_rings", 9))

    bm = bmesh.new()
    ring_verts = []
    for j in range(rings + 1):
        t = j / float(rings)
        # Smoothstep keeps the outside gentle and flattens naturally near button.
        s = t * t * (3.0 - 2.0 * t)
        radius = outer_r + (inner_r - outer_r) * t
        z = ground_z + rise_h * s
        ring = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ring.append(bm.verts.new((
                center.x + radius * math.cos(a),
                center.y + radius * math.sin(a),
                z,
            )))
        ring_verts.append(ring)

    for j in range(rings):
        for i in range(segments):
            ni = (i + 1) % segments
            bm.faces.new((
                ring_verts[j][i], ring_verts[j][ni],
                ring_verts[j + 1][ni], ring_verts[j + 1][i],
            ))

    # Flat top under the boss button; bottom is omitted because terrain is below.
    bm.faces.new(tuple(reversed(ring_verts[-1])))

    return finalize_bmesh(
        bm,
        "Crown_BossRise",
        COLLECTION,
        ctx.get_material("stone"),
        ctx,
        kind="landmark",
        dims=(outer_r * 2.0, outer_r * 2.0, rise_h),
        meta={
            "landmark": "CrownBossSanctum",
            "element": "smooth_rise",
            "walkable": True,
            "rise_height_m": rise_h,
            "outer_radius_m": outer_r,
            "button_radius_m": inner_r,
        },
    )


def _build_button(ctx, center, ground_z, scfg):
    """Raised circular boss button / throne pad."""
    radius = float(scfg["button_radius_m"])
    height = float(scfg["button_height_m"])
    z = ground_z + float(scfg["rise_height_m"])

    bm = bmesh.new()
    bmesh.ops.create_cylinder(
        bm, cap_ends=True, vertices=40, radius=radius, depth=height,
    )
    bmesh.ops.translate(
        bm, verts=bm.verts,
        vec=Vector((center.x, center.y, z + height / 2.0)),
    )
    return finalize_bmesh(
        bm,
        "Crown_BossButton",
        COLLECTION,
        ctx.get_material("altar_glow"),
        ctx,
        kind="landmark",
        dims=(radius * 2.0, radius * 2.0, height),
        meta={
            "landmark": "CrownBoss",
            "element": "button",
            "boss_stand_point": [round(center.x, 3), round(center.y, 3), round(z + height, 3)],
            "active_when_boss_dead": True,
        },
    )


def _build_half_coliseum(ctx, center, ground_z, scfg):
    """Broken half-oval coliseum around the north/back half of Crown."""
    a = float(scfg["sanctum_width_m"]) / 2.0
    b = float(scfg["sanctum_depth_m"]) / 2.0
    wall_t = float(scfg["coliseum_wall_thickness_m"])
    min_h = float(scfg["coliseum_min_height_m"])
    max_h = float(scfg["coliseum_max_height_m"])
    segs = int(scfg.get("coliseum_segments", 14))
    gap_every = int(scfg.get("coliseum_gap_every", 4))
    seed = int(scfg.get("seed", 1337))

    objs = []
    # theta 0..pi = north/front-facing half of the oval, open toward the south.
    for i in range(segs):
        theta0 = math.pi * i / segs
        theta1 = math.pi * (i + 1) / segs
        theta = 0.5 * (theta0 + theta1)
        x = a * math.cos(theta)
        y = b * math.sin(theta)

        # Skip alternating joints to create deliberate ruined gaps.
        if i % gap_every == gap_every - 1:
            continue

        # Ellipse tangent orientation.
        tx = -a * math.sin(theta)
        ty = b * math.cos(theta)
        yaw = math.degrees(math.atan2(ty, tx))

        # Deterministic broken-height profile; centre is slightly taller.
        phase = (seed % 997) * 0.013
        wave = 0.5 + 0.5 * math.sin(theta * 3.0 + phase)
        back_bias = math.sin(theta)
        height = min_h + (max_h - min_h) * (0.62 * back_bias + 0.38 * wave)
        height = max(min_h, min(max_h, height))

        span = math.hypot(a * math.sin(theta), b * math.cos(theta)) * (math.pi / segs) * 1.25
        span = max(1.0, min(span, 3.4))

        cx = center.x + x
        cy = center.y + y
        z = ground_z + height / 2.0
        obj = _cube(
            ctx,
            "Crown_ColiseumBlock{:02d}".format(i + 1),
            (cx, cy, z),
            (span, wall_t, height),
            rot_z=yaw,
            kind="cover",
            material_key="rock",
            meta={
                "landmark": "CrownBossSanctum",
                "element": "ruined_half_coliseum",
                "segment": i + 1,
                "mirror_axis": "x -> -x",
                "open_direction": "south",
            },
        )
        objs.append(obj)

    # Four broken vertical remnants make the ruin read as an ancient arena.
    column_specs = [
        (-0.82, 0.36, 2.4),
        (-0.56, 0.78, 3.0),
        (0.56, 0.78, 3.0),
        (0.82, 0.36, 2.4),
    ]
    for idx, (px, py, h) in enumerate(column_specs, start=1):
        x = center.x + a * px
        y = center.y + b * py
        size = 0.9 if abs(px) > 0.7 else 1.05
        obj = _cube(
            ctx,
            "Crown_ColiseumPillar{:02d}".format(idx),
            (x, y, ground_z + h / 2.0),
            (size, size, h),
            rot_z=0.0,
            kind="cover",
            material_key="rock",
            meta={
                "landmark": "CrownBossSanctum",
                "element": "ruined_pillar",
                "mirror_axis": "x -> -x",
                "open_direction": "south",
            },
        )
        objs.append(obj)
    return objs


def generate_crown_sanctum(ctx):
    """Generate Crown boss rise, button and half-oval ruined coliseum."""
    cfg = ctx.config
    scfg = cfg.get("crown_sanctum", {})
    if not scfg.get("enabled", True):
        return []

    center = ctx.layout["Crown"].copy()
    ground_z = get_height_at_point(Vector((center.x, center.y, 0.0)), cfg, ctx.layout)

    created = []
    created.append(_build_smooth_rise(ctx, center, ground_z, scfg))
    created.append(_build_button(ctx, center, ground_z, scfg))
    created.extend(_build_half_coliseum(ctx, center, ground_z, scfg))

    print(
        "  -> Crown Sanctum: rise={}m button={}m half-coliseum={}x{}m (pocket +15%)".format(
            scfg["rise_height_m"], scfg["button_radius_m"],
            scfg["sanctum_width_m"], scfg["sanctum_depth_m"],
        )
    )
    return created
