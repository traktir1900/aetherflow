"""AetherFlow Crown Boss Sanctum runtime geometry.

Crown Boss Sanctum keeps the existing Crown XY anchor. The boss button is
physically seated on top of the smooth semi-oval rise. The rear half-oval
coliseum is layered upward with four architectural plate tiers: the original
two lower tiers plus two additional upper throne tiers. The added throne
elements sit OUTSIDE/ON TOP of the existing wall silhouette instead of
penetrating into the original coliseum blocks.
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

    # Lower two-tier throne: the original arrangement remains unchanged.
    # Four tapered columns are anchored on the LOWER/FIRST plate and rise to
    # the SECOND/UPPER plate.
    lower_two_tiers = (
        (1, 1.10, 0.16, 0.30, 0.72),
        (2, 1.04, 1.55, 0.26, 0.55),
    )
    col_angles = (30.0, 60.0, 120.0, 150.0)

    wall_h_at = {}
    for i in range(segments):
        theta0 = math.pi * i / segments
        theta1 = math.pi * (i + 1) / segments
        theta = 0.5 * (theta0 + theta1)
        if i in (3, 7, 11, 15):
            continue
        wave = 0.5 + 0.5 * math.sin(theta * 3.0 + 1.37)
        centre_bias = math.sin(theta)
        wall_h_at[i] = max(
            min_h,
            min(max_h, min_h + (max_h - min_h) * (0.65 * centre_bias + 0.35 * wave)),
        )

    for tier, radial_mul, z_lift, slab_t, plate_depth in lower_two_tiers:
        ta = a * radial_mul
        tb = b * radial_mul
        for i in range(segments):
            theta0 = math.pi * i / segments
            theta1 = math.pi * (i + 1) / segments
            theta = 0.5 * (theta0 + theta1)
            if i in (3, 7, 11, 15):
                continue
            wall_h = wall_h_at[i]
            x = ta * math.cos(theta)
            y = tb * math.sin(theta)
            tx = -ta * math.sin(theta)
            ty = tb * math.cos(theta)
            yaw = math.degrees(math.atan2(ty, tx))
            span = max(0.82, min(1.42, ta * math.pi / segments * 0.88))
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
                        "tier_count": 4,
                        "placement": "ON_LOWER_WALL_AND_STEPPED_UPWARD",
                        "symmetry": "x -> -x",
                        "open_direction": "south",
                        "progressive_taper": tier == 2,
                    },
                )
            )

    lower_tier = lower_two_tiers[0]
    upper_tier = lower_two_tiers[1]
    lower_mul, lower_lift, lower_slab_t = lower_tier[1], lower_tier[2], lower_tier[3]
    upper_mul, upper_lift, upper_slab_t = upper_tier[1], upper_tier[2], upper_tier[3]
    ta = a * lower_mul
    tb = b * lower_mul
    col_r_x = ta + 0.14
    col_r_y = tb + 0.14

    for idx, angle_deg in enumerate(col_angles, 1):
        ang = math.radians(angle_deg)
        x = col_r_x * math.cos(ang)
        y = col_r_y * math.sin(ang)
        lower_wall_h = min_h + (max_h - min_h) * (
            0.65 * math.sin(ang) + 0.35 * (0.5 + 0.5 * math.sin(ang * 3.0 + 1.37))
        )
        lower_wall_h = max(min_h, min(max_h, lower_wall_h))
        base_z = ground_z + lower_wall_h + lower_lift + lower_slab_t
        top_z = ground_z + lower_wall_h + upper_lift
        col_h = max(0.55, top_z - base_z)
        created.append(
            _tapered_column(
                ctx,
                "Crown_ThroneColumn_{:02d}".format(idx),
                (center.x + x, center.y + y, base_z),
                col_h,
                0.40,
                0.18,
                material_key="rock",
                meta={
                    "landmark": "CrownBossSanctum",
                    "element": "tapered_throne_column",
                    "support": "LOWER_TIER_TO_UPPER_TIER",
                    "tier_base": 1,
                    "tier_support": 2,
                    "symmetry": "x -> -x",
                    "open_direction": "south",
                    "taper": "WIDE_BOTTOM_NARROW_TOP",
                },
            )
        )

    # Two additional upper throne tiers.
    # Each upper tier is deliberately built from SIX broad rectangular plates
    # rather than a full ring. The six-piece construction reads more like a
    # heavy stone throne crest. Tier 3 supports Tier 4 with four columns; Tier
    # 4 receives two smaller top columns as a final crown-like finish.
    upper_tiers = (
        (3, 0.96, 2.35, 0.24, 0.56),
        (4, 0.82, 3.00, 0.22, 0.48),
    )
    six_angles = (18.0, 48.0, 78.0, 102.0, 132.0, 162.0)

    for tier, radial_mul, z_lift, slab_t, plate_depth in upper_tiers:
        ta = a * radial_mul
        tb = b * radial_mul
        for idx, angle_deg in enumerate(six_angles, 1):
            ang = math.radians(angle_deg)
            # Wider rectangles at the lower upper-tier and slightly narrower
            # at the final tier, preserving a clear upward taper.
            span = 2.20 if tier == 3 else 1.85
            x = ta * math.cos(ang)
            y = tb * math.sin(ang)
            tx = -ta * math.sin(ang)
            ty = tb * math.cos(ang)
            yaw = math.degrees(math.atan2(ty, tx))
            # Height references the central top silhouette rather than the
            # irregular wall blocks, preventing the new layers from burying
            # the lower throne.
            plate_z = ground_z + max_h + z_lift + slab_t / 2.0
            created.append(
                _cube(
                    ctx,
                    "Crown_ThroneUpperPlate_T{}_{:02d}".format(tier, idx),
                    (center.x + x, center.y + y, plate_z),
                    (span, plate_depth, slab_t),
                    yaw,
                    kind="cover",
                    material_key="stone",
                    meta={
                        "landmark": "CrownBossSanctum",
                        "element": "throne_upper_rectangular_plate",
                        "tier": tier,
                        "tier_count": 4,
                        "plate_count": 6,
                        "placement": "UPPER_STEPPED_THRONE",
                        "symmetry": "x -> -x",
                        "open_direction": "south",
                        "progressive_taper": True,
                    },
                )
            )

    # Four tapered support columns between the sixth-piece Tier 3 and Tier 4.
    # They are centered on the lower upper tier and stop beneath the Tier 4
    # plates, so they visibly belong to the Tier 3 -> Tier 4 transition.
    tier3 = upper_tiers[0]
    tier4 = upper_tiers[1]
    ta3, tb3 = a * tier3[1], b * tier3[1]
    ta4, tb4 = a * tier4[1], b * tier4[1]
    four_angles = (34.0, 56.0, 124.0, 146.0)
    for idx, angle_deg in enumerate(four_angles, 1):
        ang = math.radians(angle_deg)
        x = ta3 * math.cos(ang)
        y = tb3 * math.sin(ang)
        base_z = ground_z + max_h + tier3[2] + tier3[3]
        top_z = ground_z + max_h + tier4[2]
        col_h = max(0.45, top_z - base_z)
        created.append(
            _tapered_column(
                ctx,
                "Crown_ThroneUpperColumn_{:02d}".format(idx),
                (center.x + x, center.y + y, base_z),
                col_h,
                0.34,
                0.15,
                material_key="rock",
                meta={
                    "landmark": "CrownBossSanctum",
                    "element": "tapered_throne_upper_column",
                    "support": "UPPER_TIER_3_TO_4",
                    "tier_base": 3,
                    "tier_support": 4,
                    "symmetry": "x -> -x",
                    "open_direction": "south",
                    "taper": "WIDE_BOTTOM_NARROW_TOP",
                },
            )
        )

    # Two final top columns, centered on the highest tier as a paired crest.
    top_tier = upper_tiers[1]
    ta4, tb4 = a * top_tier[1], b * top_tier[1]
    for idx, angle_deg in enumerate((72.0, 108.0), 1):
        ang = math.radians(angle_deg)
        x = ta4 * math.cos(ang)
        y = tb4 * math.sin(ang)
        base_z = ground_z + max_h + top_tier[2] + top_tier[3]
        created.append(
            _tapered_column(
                ctx,
                "Crown_ThroneTopColumn_{:02d}".format(idx),
                (center.x + x, center.y + y, base_z),
                0.72,
                0.26,
                0.10,
                material_key="rock",
                meta={
                    "landmark": "CrownBossSanctum",
                    "element": "top_twin_throne_column",
                    "tier": 4,
                    "symmetry": "x -> -x",
                    "open_direction": "south",
                    "taper": "WIDE_BOTTOM_NARROW_TOP",
                    "top_pair": True,
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
        "throne tiers=4 | upper tiers=6 plates each | 4 upper supports | 2 top columns | symmetric"
    )
    return created
