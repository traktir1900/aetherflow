"""AetherFlow Crown Boss Sanctum runtime geometry.

Crown Boss Sanctum keeps the existing Crown XY anchor. The boss button is
physically seated on top of the smooth semi-oval rise rather than floating or
sitting inside it.
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
    outer_a = 15.75
    outer_b = 10.50
    button_r = 3.2
    height = 0.441
    rings = 18
    segs = 72
    bm = bmesh.new()
    rings_v = []

    for j in range(rings + 1):
        t = j / float(rings)
        s = t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
        a = outer_a + (button_r - outer_a) * t
        b = outer_b + (button_r - outer_b) * t
        z = ground_z + height * s
        row = []
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            row.append(bm.verts.new((center.x + a * math.cos(ang), center.y + b * math.sin(ang), z)))
        rings_v.append(row)

    for j in range(rings):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new((rings_v[j][i], rings_v[j][ni], rings_v[j + 1][ni], rings_v[j + 1][i]))
    bm.faces.new(tuple(reversed(rings_v[-1])))

    return finalize_bmesh(
        bm,
        "Crown_BossRise",
        COLLECTION,
        ctx.get_material("stone"),
        ctx,
        kind="landmark",
        dims=(outer_a * 2, outer_b * 2, height),
        meta={
            "landmark": "CrownBossSanctum",
            "element": "smooth_semi_oval_rise",
            "walkable": True,
            "rise_height_m": height,
            "approach": "SMOOTH_SEMI_OVAL",
            "alignment": "ALONG_COLISEUM_WALL",
            "outer_extent_scale": 1.50,
            "height_scale": 0.315,
            "button_seated_on_rise": True,
            "anchor_unchanged": True,
        },
    )


def _boss_button(ctx, center, ground_z):
    radius = 3.2
    height = 0.25
    rise_height = 0.441
    # The button is placed ON TOP of the rise. Its bottom rests exactly at the
    # rise top and its center is half its thickness above that surface.
    top_z = ground_z + rise_height + height
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=radius, radius2=radius, depth=height)
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=Vector((center.x, center.y, ground_z + rise_height + height / 2.0)),
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
            "boss_stand_point": [round(center.x, 3), round(center.y, 3), round(top_z, 3)],
            "button_on_rise": True,
            "button_base_z": round(ground_z + rise_height, 3),
            "active_when_boss_dead": True,
        },
    )


def _half_coliseum(ctx, center, ground_z):
    a = 9.2
    b = 5.75
    wall_t = 0.55
    min_h = 1.0
    max_h = 2.2
    segments = 16
    created = []

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
        created.append(_cube(
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
        ))

    for idx, (px, py, h) in enumerate((
        (-0.88, 0.36, 1.65),
        (-0.62, 0.78, 2.35),
        (0.62, 0.78, 2.35),
        (0.88, 0.36, 1.65),
    ), 1):
        size = 0.65 if abs(px) > 0.8 else 0.8
        created.append(_cube(
            ctx,
            "Crown_ColiseumPillar{:02d}".format(idx),
            (center.x + a * px, center.y + b * py, ground_z + h / 2.0),
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
        ))
    return created


def generate(ctx):
    if ctx.layout.get("Crown") is None:
        return []
    center = ctx.layout["Crown"].copy()
    ground_z = get_height_at_point(Vector((center.x, center.y, 0.0)), ctx.config, ctx.layout)
    created = [_smooth_rise(ctx, center, ground_z), _boss_button(ctx, center, ground_z)]
    created.extend(_half_coliseum(ctx, center, ground_z))
    print(
        "  -> Crown Sanctum: rise=0.441m | button seated on rise | "
        "semi-oval approach=31.5x21.0m | ruined half-coliseum=18.4x11.5m"
    )
    return created
