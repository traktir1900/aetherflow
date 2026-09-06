"""AetherFlow V0.6.4.1 — Resource Foundation.

Creates six neutral visual resource locations from the authoritative map layout:
three Speed Shrines and three Health Relics. The placement is gameplay-driven,
deterministic, and team-symmetric wherever a flank pair exists. Geometry is
visual-only and non-blocking; actual resource gameplay remains a future
UE5/runtime system.
"""
import math

import bmesh
from mathutils import Vector

from core.utils import finalize_bmesh
from core.heightmap import get_height_at_point

COLLECTION = "Decorations"
MIRROR_TOLERANCE_M = 1e-5
CENTERLINE_TOLERANCE_M = 1e-5


def _terrain_z(ctx, x, y):
    return get_height_at_point(Vector((x, y, 0.0)), ctx.config, ctx.layout)


def _material(ctx, name, fallback="rock"):
    return ctx.get_material(name) or ctx.get_material(fallback) or ctx.get_material("ground")


def _new_resource_mesh(name, center, radius, material, ctx, resource_type, resource_id,
                       anchor, supporting, role, mirror_id=None):
    """Create one complete resource marker as one Blender object.

    Keeping each gameplay resource as a single object makes the six-resource
    layout explicit and avoids turning one gameplay pickup into four unrelated
    scene objects.
    """
    bm = bmesh.new()

    # Low technical plinth.
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=24,
        radius1=radius,
        radius2=radius * 0.92,
        depth=0.34,
        calc_uvs=False,
    )

    # Raised central beacon.
    beacon_radius = radius * 0.18
    beacon_height = radius * 0.95
    beacon = bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=12,
        radius1=beacon_radius,
        radius2=beacon_radius * 0.72,
        depth=beacon_height,
        calc_uvs=False,
    )
    bmesh.ops.translate(
        bm,
        vec=Vector((0.0, 0.0, 0.17 + beacon_height * 0.5)),
        verts=beacon.get("verts", []),
    )

    # One visible ring, built procedurally for Blender 5.2 compatibility.
    ring_radius = radius * 0.78
    tube = max(radius * 0.08, 0.06)
    segments = 28
    minor_segments = 6
    ring_verts = []
    for i in range(segments):
        a = (2.0 * math.pi * i) / segments
        ca, sa = math.cos(a), math.sin(a)
        for j in range(minor_segments):
            b = (2.0 * math.pi * j) / minor_segments
            cb, sb = math.cos(b), math.sin(b)
            r = ring_radius + tube * cb
            ring_verts.append((r * ca, r * sa, 0.38 + tube * sb))

    for co in ring_verts:
        bm.verts.new(co)
    bm.verts.ensure_lookup_table()
    ring_start = len(bm.verts) - len(ring_verts)
    for i in range(segments):
        ni = (i + 1) % segments
        for j in range(minor_segments):
            nj = (j + 1) % minor_segments
            a = ring_start + i * minor_segments + j
            b = ring_start + ni * minor_segments + j
            c = ring_start + ni * minor_segments + nj
            d = ring_start + i * minor_segments + nj
            try:
                bm.faces.new((bm.verts[a], bm.verts[b], bm.verts[c], bm.verts[d]))
            except ValueError:
                pass

    bm.faces.ensure_lookup_table()
    x, y, z = center
    obj = finalize_bmesh(
        bm,
        name,
        COLLECTION,
        material,
        ctx,
        kind="resource_marker",
        dims=(radius * 2.0, radius * 2.0, max(0.80, beacon_height + 0.40)),
        meta={
            "visual_only": True,
            "navigation_blocker": False,
            "los_blocker": False,
            "gameplay_marker": True,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_anchor": anchor,
            "supporting_landmark": supporting,
            "resource_role": role,
            "mirror_id": mirror_id,
        },
    )
    obj.location = Vector((x, y, z))
    return obj


def _resource_location(ctx, resource_type, resource_id, x, y, radius, anchor,
                       supporting, role, material, mirror_id=None):
    z = _terrain_z(ctx, x, y)
    return _new_resource_mesh(
        resource_id,
        (x, y, z + 0.01),
        radius,
        material,
        ctx,
        resource_type,
        resource_id,
        anchor,
        supporting,
        role,
        mirror_id=mirror_id,
    )


def audit_resource_symmetry(objects):
    """Validate paired flank resources and centerline resources."""
    by_id = {o.get("resource_id"): o for o in objects}
    failures = []
    max_error = 0.0

    for obj in objects:
        mirror_id = obj.get("mirror_id")
        if mirror_id:
            pair = by_id.get(mirror_id)
            if pair is None:
                failures.append((obj.name, "missing counterpart"))
                continue
            expected = Vector((-obj.location.x, obj.location.y, obj.location.z))
            err = (pair.location - expected).length
            max_error = max(max_error, err)
            if err > MIRROR_TOLERANCE_M:
                failures.append((obj.name, err))
        elif abs(obj.location.x) > CENTERLINE_TOLERANCE_M:
            failures.append((obj.name, "center resource is off symmetry axis"))

    return {"passed": not failures, "max_error_m": max_error, "failures": failures}


def generate_resource_foundation(ctx):
    cfg = ctx.config.get("resource_foundation", {})
    if not cfg.get("enabled", True):
        return {"enabled": False, "objects": [], "symmetry_passed": True, "max_error_m": 0.0}

    layout = ctx.layout
    center = layout["Center"]
    west = layout["WestMonolith"]
    east = layout["EastMonolith"]
    sw = layout["SWMonolith"]
    se = layout["SEMonolith"]
    crown = layout["Crown"]
    blue_base = layout["BlueBase"]
    red_base = layout["RedBase"]

    speed_t = float(cfg.get("speed_anchor_t", 0.52))
    health_t = float(cfg.get("health_anchor_t", 0.52))
    speed_offset_y = float(cfg.get("speed_offset_y", -3.5))
    health_offset_y = float(cfg.get("health_offset_y", -3.5))
    speed_north_t = float(cfg.get("speed_north_t", 0.55))
    health_south_t = float(cfg.get("health_south_t", 0.55))

    speed_flank = center.lerp(west, speed_t)
    speed_flank_y = float(speed_flank.y) + speed_offset_y
    speed_x = abs(float(speed_flank.x))

    health_flank = center.lerp(sw, health_t)
    health_flank_y = float(health_flank.y) + health_offset_y
    health_x = abs(float(health_flank.x))

    # Central Speed Shrine controls the Crown approach / north rotation.
    speed_north = center.lerp(crown, speed_north_t)

    # Central Health Relic controls the south return / base approach. The
    # midpoint between the two bases keeps the location team-neutral.
    base_midpoint = blue_base.lerp(red_base, 0.5)
    health_south = center.lerp(base_midpoint, health_south_t)

    speed_material = _material(ctx, "outer_boundary_aether")
    health_material = _material(ctx, "outer_boundary_stone")
    speed_radius = float(cfg.get("speed_shrine_radius", 1.4))
    health_radius = float(cfg.get("health_relic_radius", 1.2))

    created = [
        _resource_location(
            ctx, "SpeedShrine", "SpeedShrine_West", speed_x, speed_flank_y,
            speed_radius, "Center↔West/EastMonolith", "SideApproachLandmark",
            "flank_west", speed_material, mirror_id="SpeedShrine_East"),
        _resource_location(
            ctx, "SpeedShrine", "SpeedShrine_East", -speed_x, speed_flank_y,
            speed_radius, "Center↔West/EastMonolith", "SideApproachLandmark",
            "flank_east", speed_material, mirror_id="SpeedShrine_West"),
        _resource_location(
            ctx, "SpeedShrine", "SpeedShrine_North", float(speed_north.x), float(speed_north.y),
            speed_radius, "Center↔Crown", "CrownApproach", "north_central",
            speed_material),
        _resource_location(
            ctx, "HealthRelic", "HealthRelic_SW", health_x, health_flank_y,
            health_radius, "Center↔SW/SEMonolith", "SouthApproachLandmark",
            "flank_southwest", health_material, mirror_id="HealthRelic_SE"),
        _resource_location(
            ctx, "HealthRelic", "HealthRelic_SE", -health_x, health_flank_y,
            health_radius, "Center↔SW/SEMonolith", "SouthApproachLandmark",
            "flank_southeast", health_material, mirror_id="HealthRelic_SW"),
        _resource_location(
            ctx, "HealthRelic", "HealthRelic_South", float(health_south.x), float(health_south.y),
            health_radius, "Center↔Bases", "SouthReturnApproach", "south_central",
            health_material),
    ]

    report = audit_resource_symmetry(created)
    print(
        "  -> V0.6.4.1 resources: total=6 | SpeedShrine=3 | HealthRelic=3 | "
        "visual_objects={} | symmetry={} | max_error={:.6f}m".format(
            len(created), len([o for o in created if o.get("resource_type") == "SpeedShrine"]),
            len([o for o in created if o.get("resource_type") == "HealthRelic"]),
            "PASS" if report["passed"] else "FAIL", report["max_error_m"])
    )
    return {
        "enabled": True,
        "pairs": ["SpeedShrine", "HealthRelic"],
        "resource_types": ["SpeedShrine", "HealthRelic"],
        "markers": 6,
        "objects": created,
        **report,
    }
