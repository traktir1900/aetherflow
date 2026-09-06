"""AetherFlow Crown Boss Sanctum runtime geometry.

Crown Boss Sanctum keeps the existing Crown XY anchor. The boss button is
physically seated on top of the smooth semi-oval rise. The rear half-oval
coliseum is layered upward with four architectural plate tiers. The upper
throne tiers use four centered rectangular plates, taper inward as they rise,
and are connected by solid rectangular support webs instead of free-standing
columns.
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

    # Existing ruined half-coliseum wall. Kept exactly as the established shape.
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

    # Lower two-tier throne: preserve the established lower two plate tiers.
    lower_two_tiers = (
        (1, 1.10, 0.16, 0.30, 0.72),
        (2, 1.04, 1.55, 0.26, 0.55),
    )

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

    # Upper throne tiers: centered 4-piece layout, symmetric around the Y axis.
    # The two outermost pieces from the previous 6-piece layout are removed.
    # Each higher tier is narrower and higher, giving a clear stepped taper.
    upper_tiers = (
        (3, 0.96, 2.35, 0.24, 0.56),
        (4, 0.82, 3.00, 0.22, 0.48),
    )
    upper_angles = (48.0, 78.0, 102.0, 132.0)

    # Four broad rectangular plates per upper tier.
    upper_plate_cache = {}
    for tier, radial_mul, z_lift, slab_t, plate_depth in upper_tiers:
        ta = a * radial_mul
        tb = b * radial_mul
        upper_plate_cache[tier] = {}
        for idx, angle_deg in enumerate(upper_angles, 1):
            ang = math.radians(angle_deg)
            span = 2.20 if tier == 3 else 1.82
            x = ta * math.cos(ang)
            y = tb * math.sin(ang)
            tx = -ta * math.sin(ang)
            ty = tb * math.cos(ang)
            yaw = math.degrees(math.atan2(ty, tx))
            plate_z = ground_z + max_h + z_lift + slab_t / 2.0
            plate = _cube(
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
                    "plate_count": 4,
                    "placement": "UPPER_STEPPED_THRONE",
                    "symmetry": "x -> -x",
                    "open_direction": "south",
                    "progressive_taper": True,
                    "outer_edge_pieces_removed": 2,
                },
            )
            created.append(plate)
            upper_plate_cache[tier][idx] = (ta, tb, ang, plate_z, slab_t, span, plate_depth)

    # Solid rectangular connector webs replace the previous free-standing
    # columns. They directly bridge lower->upper levels and touch the plates,
    # so no throne piece appears to float in the air.
    connector_specs = (
        (2, 3, upper_angles, 1.04, 0.96, 1.55, 2.35, 0.26, 0.24),
        (3, 4, upper_angles, 0.96, 0.82, 2.35, 3.00, 0.24, 0.22),
    )
    for lower_tier, upper_tier, angles, lower_mul, upper_mul, lower_lift, upper_lift, lower_slab_t, upper_slab_t in connector_specs:
        for idx, angle_deg in enumerate(angles, 1):
            ang = math.radians(angle_deg)
            lower_x = a * lower_mul * math.cos(ang)
            lower_y = b * lower_mul * math.sin(ang)
            upper_x = a * upper_mul * math.cos(ang)
            upper_y = b * upper_mul * math.sin(ang)

            bottom_z = ground_z + max_h + lower_lift + lower_slab_t / 2.0
            top_z = ground_z + max_h + upper_lift - upper_slab_t / 2.0
            if top_z <= bottom_z:
                continue

            mid_x = 0.5 * (lower_x + upper_x)
            mid_y = 0.5 * (lower_y + upper_y)
            web_h = top_z - bottom_z
            web_w = 1.05 if upper_tier == 3 else 0.92
            web_d = 0.70 if upper_tier == 3 else 0.62

            tx = -(b * 0.5) * math.sin(ang)
            ty = (a * 0.5) * math.cos(ang)
            yaw = math.degrees(math.atan2(ty, tx))
            created.append(
                _cube(
                    ctx,
                    "Crown_ThroneConnector_T{}_{}_{:02d}".format(lower_tier, upper_tier, idx),
                    (center.x + mid_x, center.y + mid_y, bottom_z + web_h / 2.0),
                    (web_w, web_d, web_h),
                    yaw,
                    kind="cover",
                    material_key="rock",
                    meta={
                        "landmark": "CrownBossSanctum",
                        "element": "rectangular_throne_connector",
                        "from_tier": lower_tier,
                        "to_tier": upper_tier,
                        "support": "DIRECT_PLATE_TO_PLATE",
                        "symmetry": "x -> -x",
                        "open_direction": "south",
                        "tapered_upward": True,
                    },
                )
            )

    # A thin continuous rear brace ties each upper four-piece set together.
    # It is inset behind the plate faces and follows the same symmetric arc.
    for tier, radial_mul, z_lift, slab_t, plate_depth in upper_tiers:
        ta = a * radial_mul
        tb = b * radial_mul
        brace_t = 0.26 if tier == 3 else 0.22
        brace_z = ground_z + max_h + z_lift - brace_t / 2.0
        for idx, (ang0_deg, ang1_deg) in enumerate(((48.0, 78.0), (78.0, 102.0), (102.0, 132.0)), 1):
            ang0 = math.radians(ang0_deg)
            ang1 = math.radians(ang1_deg)
            ang = 0.5 * (ang0 + ang1)
            x0 = ta * math.cos(ang0)
            y0 = tb * math.sin(ang0)
            x1 = ta * math.cos(ang1)
            y1 = tb * math.sin(ang1)
            dx = x1 - x0
            dy = y1 - y0
            length = math.hypot(dx, dy)
            yaw = math.degrees(math.atan2(dy, dx))
            created.append(
                _cube(
                    ctx,
                    "Crown_ThroneRearBrace_T{}_{:02d}".format(tier, idx),
                    (center.x + 0.5 * (x0 + x1), center.y + 0.5 * (y0 + y1), brace_z),
                    (max(0.85, length + 0.16), 0.30, brace_t),
                    yaw,
                    kind="cover",
                    material_key="rock",
                    meta={
                        "landmark": "CrownBossSanctum",
                        "element": "continuous_rear_throne_brace",
                        "tier": tier,
                        "plate_count": 4,
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
    ground_z = get_height_at_point(Vector((center.x, center.y, 0.0)), ctx.config, ctx.layout)
    created = [_smooth_rise(ctx, center, ground_z), _boss_button(ctx, center, ground_z)]
    created.extend(_half_coliseum(ctx, center, ground_z))
    print(
        "  -> Crown Sanctum: rise=0.441m | button seated on rise | "
        "semi-oval=7.88x5.25m | coliseum=18.4x11.5m | "
        "throne tiers=4 | upper tiers=4 plates each | columns removed | solid connectors | symmetric taper"
    )
    return created
