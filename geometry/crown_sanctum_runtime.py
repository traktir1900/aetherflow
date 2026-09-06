"""AetherFlow Crown Boss Sanctum runtime geometry.

Crown Boss Sanctum keeps the existing Crown XY anchor. The boss button is
physically seated on top of the smooth semi-oval rise. The rear half-oval
coliseum is layered upward with two architectural plate tiers and tapered
columns. The added throne elements sit OUTSIDE/ON TOP of the existing wall
silhouette instead of penetrating into the original coliseum blocks.
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


def _tapered_column(ctx, name, center, height, radius_bottom, radius_top, material_key="rock", meta=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=12,
        radius1=radius_bottom,
        radius2=radius_top,
        depth=height,
    )
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=Vector((center[0], center[1], center[2] + height / 2.0)),
    )
    return finalize_bmesh(
        bm,
        name,
        COLLECTION,
        ctx.get_material(material_key),
        ctx,
        kind="cover",
        dims=(radius_bottom * 2, radius_bottom * 2, height),
        meta=meta or {},
    )


def _smooth_rise(ctx, center, ground_z):
    outer_a = 7.875
    outer_b = 5.25
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
            row.append(
                bm.verts.new(
                    (center.x + a * math.cos(ang), center.y + b * math.sin(ang), z)
                )
            )
        rings_v.append(row)

    for j in range(rings):
        for i in range(segs):
            ni = (i + 1) % segs
            bm.faces.new(
                (rings_v[j][i], rings_v[j][ni], rings_v[j + 1][ni], rings_v[j + 1][i])
            )
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
            "outer_extent_scale": 0.75,
            "footprint_scale_from_previous": 0.50,
            "button_seated_on_rise": True,
            "anchor_unchanged": True,
        },
    )


def _boss_button(ctx, center, ground_z):
    radius = 3.2
    height = 0.25
    rise_height = 0.441
    top_z = ground_z + rise_height + height
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=40,
        radius1=radius,
        radius2=radius,
        depth=height,
    )
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

    # Existing ruined wall.
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

    # Original four broken flanking pillars.
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
            )
        )

    # NEW: two throne-like architectural layers are attached just OUTSIDE the
    # existing wall centerline, not placed at the same ellipse.  Each tier is
    # a narrow ledge running along the top of the ruined wall.  Its Z follows
    # the corresponding wall block height so it visibly sits on the wall.
    # The second tier is smaller and slightly higher, creating the stepped
    # crown/throne silhouette without burying the original wall.
    for tier, radial_mul, z_lift, slab_t in (
        (1, 1.10, 0.16, 0.30),
        (2, 1.18, 0.34, 0.26),
    ):
        ta = a * radial_mul
        tb = b * radial_mul
        plate_depth = 0.72 if tier == 1 else 0.62

        for i in range(segments):
            theta0 = math.pi * i / segments
            theta1 = math.pi * (i + 1) / segments
            theta = 0.5 * (theta0 + theta1)
            if i in (3, 7, 11, 15):
                continue

            # Estimate the underlying wall top at the same angular position.
            wave = 0.5 + 0.5 * math.sin(theta * 3.0 + 1.37)
            centre_bias = math.sin(theta)
            wall_h = min_h + (max_h - min_h) * (0.65 * centre_bias + 0.35 * wave)
            wall_h = max(min_h, min(max_h, wall_h))

            x = ta * math.cos(theta)
            y = tb * math.sin(theta)
            tx = -ta * math.sin(theta)
            ty = tb * math.cos(theta)
            yaw = math.degrees(math.atan2(ty, tx))
            span = max(0.95, min(1.50, ta * math.pi / segments * 0.92))

            plate_z = ground_z + wall_h + z_lift + slab_t / 2.0
            created.append(
                _cube(
                    ctx,
                    "Crown_ThronePlate_T{}_{:02d}".format(tier, i + 1),
                    (center.x + x, center.y + y, plate_z),
                    (span, plate_depth, slab_t),
                    yaw,
                    kind="cover",
                    material_key="stone",
                    meta={
                        "landmark": "CrownBossSanctum",
                        "element": "throne_plate",
                        "tier": tier,
                        "placement": "OUTSIDE_ON_TOP_OF_EXISTING_WALL",
                        "symmetry": "x -> -x",
                        "open_direction": "south",
                    },
                )
            )

        # Four tapered throne columns, placed in the outer tier line and seated
        # on the previous plate. Wide at the base, narrow at the top.
        col_angles = (30.0, 60.0, 120.0, 150.0)
        col_r = ta + 0.15
        for idx, angle_deg in enumerate(col_angles, 1):
            ang = math.radians(angle_deg)
            wall_h = min_h + (max_h - min_h) * (
                0.65 * math.sin(ang) + 0.35 * (0.5 + 0.5 * math.sin(ang * 3.0 + 1.37))
            )
            wall_h = max(min_h, min(max_h, wall_h))
            base_z = ground_z + wall_h + z_lift + slab_t
            col_h = 1.10 if tier == 1 else 0.88
            rb = 0.38 if tier == 1 else 0.32
            rt = 0.18 if tier == 1 else 0.14
            x = col_r * math.cos(ang)
            y = (b * radial_mul + 0.15) * math.sin(ang)
            created.append(
                _tapered_column(
                    ctx,
                    "Crown_ThroneColumn_T{}_{:02d}".format(tier, idx),
                    (center.x + x, center.y + y, base_z),
                    col_h,
                    rb,
                    rt,
                    material_key="rock",
                    meta={
                        "landmark": "CrownBossSanctum",
                        "element": "tapered_throne_column",
                        "tier": tier,
                        "placement": "OUTER_WALL_LINE",
                        "symmetry": "x -> -x",
                        "open_direction": "south",
                        "taper": "WIDE_BOTTOM_NARROW_TOP",
                    },
                )
            )

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
        "semi-oval=7.88x5.25m | coliseum=18.4x11.5m | "
        "throne tiers=2 OUTSIDE wall | tapered columns | symmetric"
    )
    return created
