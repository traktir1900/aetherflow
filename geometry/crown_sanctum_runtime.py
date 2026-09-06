"""AetherFlow Crown Boss Sanctum runtime geometry.

Keeps the existing Crown XY anchor. Adds a smooth approach mound, a raised
boss button, and a symmetric ruined half-oval coliseum open toward the south.
The current generated pocket footprint is 16x10 m in this scaled build, so the
half-oval is 15% larger by footprint dimensions: 18.4 x 11.5 m.
"""
import math
import bmesh
from mathutils import Vector, Matrix

from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

COLLECTION = "CapturePoints"


def _cube(ctx, name, center, size, rot_z, kind="cover", material_key="rock", meta=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if rot_z:
        bmesh.ops.rotate(
            bm,
            cent=Vector((0, 0, 0)),
            matrix=Matrix.Rotation(math.radians(rot_z), 4, "Z"),
            verts=bm.verts,
        )
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(center))
    return finalize_bmesh(
        bm, name, COLLECTION, ctx.get_material(material_key), ctx,
        kind=kind, dims=size, meta=meta or {},
    )


def _smooth_rise(ctx, center, ground_z):
    outer_r = 10.5
    button_r = 3.2
    height = 1.4
    rings = 10
    segs = 48
    bm = bmesh.new()
    rings_v = []
    for j in range(rings + 1):
        t = j / float(rings)
        s = t * t * (3.0 - 2.0 * t)
        r = outer_r + (button_r - outer_r) * t
        z = ground_z + height * s
        row = []
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            row.append(
                bm.verts.new(
                    (
                        center.x + r * math.cos(a),
                        center.y + r * math.sin(a),
                        z,
                    )
                )
            )
        rings_v.append(row)
    for j in range(rings):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new(
                (
                    rings_v[j][i],
                    rings_v[j][ni],
                    rings_v[j + 1][ni],
                    rings_v[j + 1][i],
                )
            )
    bm.faces.new(tuple(reversed(rings_v[-1])))
    return finalize_bmesh(
        bm,
        "Crown_BossRise",
        COLLECTION,
        ctx.get_material("stone"),
        ctx,
        kind="landmark",
        dims=(outer_r * 2, outer_r * 2, height),
        meta={
            "landmark": "CrownBossSanctum",
            "element": "smooth_rise",
            "walkable": True,
            "rise_height_m": height,
            "approach": "SMOOTH_RADIAL",
            "anchor_unchanged": True,
        },
    )


def _boss_button(ctx, center, ground_z):
    radius = 3.2
    height = 0.25
    top_z = ground_z + 1.4
    bm = bmesh.new()
    bmesh.ops.create_cylinder(
        bm, cap_ends=True, vertices=40, radius=radius, depth=height
    )
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=Vector((center.x, center.y, top_z - height / 2.0)),
    )
    return finalize_bmesh(
        bm,
        "Crown_BossButton",
        COLLECTION,
        ctx.get_material("altar_glow"),
        ctx,
        kind="landmark",
        dims=(radius * 2, radius * 2, height),
        meta={
            "landmark": "CrownBoss",
            "element": "button",
            "boss_stand_point": [
                round(center.x, 3),
                round(center.y, 3),
                round(top_z, 3),
            ],
            "active_when_boss_dead": True,
        },
    )


def _half_coliseum(ctx, center, ground_z):
    # Actual generated pocket is 16x10 m in this scaled build.
    # 16x10 * 1.15 = 18.4x11.5 m sanctum footprint.
    a = 9.2
    b = 5.75
    wall_t = 0.55
    min_h = 1.0
    max_h = 2.2
    segments = 16
    created = []

    # Upper/northern half of the oval; southern/front side is deliberately open.
    for i in range(segments):
        theta0 = math.pi * i / segments
        theta1 = math.pi * (i + 1) / segments
        theta = 0.5 * (theta0 + theta1)
        if i in (3, 7, 11, 15):
            continue

        x = a * math.cos(theta)
        y = b * math.sin(theta)
        tx = -a * math.sin(theta)
        ty = b * math.cos(theta)
        yaw = math.degrees(math.atan2(ty, tx))

        wave = 0.5 + 0.5 * math.sin(theta * 3.0 + 1.37)
        centre_bias = math.sin(theta)
        h = min_h + (max_h - min_h) * (0.65 * centre_bias + 0.35 * wave)
        h = max(min_h, min(max_h, h))
        span = max(1.3, min(2.0, a * math.pi / segments * 1.10))

        created.append(
            _cube(
                ctx,
                "Crown_ColiseumBlock{:02d}".format(i + 1),
                (center.x + x, center.y + y, ground_z + h / 2.0),
                (span, wall_t, h),
                yaw,
                kind="cover",
                material_key="rock",
                meta={
                    "landmark": "CrownBossSanctum",
                    "element": "ruined_half_coliseum",
                    "segment": i + 1,
                    "open_direction": "south",
                    "symmetry": "x -> -x",
                },
            )
        )

    # Symmetric broken pillars at the two flank transitions.
    for idx, (px, py, h) in enumerate(
        (
            (-0.88, 0.36, 1.65),
            (-0.62, 0.78, 2.35),
            (0.62, 0.78, 2.35),
            (0.88, 0.36, 1.65),
        ),
        1,
    ):
        size = 0.65 if abs(px) > 0.8 else 0.8
        created.append(
            _cube(
                ctx,
                "Crown_ColiseumPillar{:02d}".format(idx),
                (
                    center.x + a * px,
                    center.y + b * py,
                    ground_z + h / 2.0,
                ),
                (size, size, h),
                0.0,
                kind="cover",
                material_key="rock",
                meta={
                    "landmark": "CrownBossSanctum",
                    "element": "ruined_pillar",
                    "symmetry": "x -> -x",
                    "open_direction": "south",
                },
            )
        )
    return created


def generate(ctx):
    if ctx.layout.get("Crown") is None:
        return []
    center = ctx.layout["Crown"].copy()
    ground_z = get_height_at_point(
        Vector((center.x, center.y, 0.0)), ctx.config, ctx.layout
    )
    created = [
        _smooth_rise(ctx, center, ground_z),
        _boss_button(ctx, center, ground_z),
    ]
    created.extend(_half_coliseum(ctx, center, ground_z))
    print(
        "  -> Crown Sanctum: smooth rise=1.40m | boss button Ø6.40m | "
        "ruined half-coliseum=18.4x11.5m | actual pocket 16x10m | pocket +15%"
    )
    return created
