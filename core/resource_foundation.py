"""AetherFlow V0.6.4.1 — Resource Foundation.

Creates neutral visual resource locations from the authoritative map layout.
Each gameplay-relevant resource marker is authored from one canonical side and
mirrored on X for the opposing side. Geometry is visual-only and non-blocking;
actual resource gameplay remains a future UE5/runtime system.
"""
import math

import bmesh
from mathutils import Vector

from core.utils import finalize_bmesh
from core.heightmap import get_height_at_point

COLLECTION = "Decorations"
MIRROR_TOLERANCE_M = 1e-5


def _terrain_z(ctx, x, y):
    return get_height_at_point(Vector((x, y, 0.0)), ctx.config, ctx.layout)


def _material(ctx, name, fallback="rock"):
    return ctx.get_material(name) or ctx.get_material(fallback) or ctx.get_material("ground")


def _cylinder(name, center, radius, depth, material, ctx, kind="resource_marker", sides=24, meta=None):
    bm = bmesh.new()
    # Blender 5.2 exposes this primitive through create_cone(); equal top and
    # bottom radii produce a cylinder. create_cylinder is not a BMesh operator.
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sides,
        radius1=radius,
        radius2=radius,
        depth=depth,
        calc_uvs=False,
    )
    x, y, z = center
    obj = finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind=kind,
        dims=(radius * 2.0, radius * 2.0, depth),
        meta={
            "visual_only": True,
            "navigation_blocker": False,
            "los_blocker": False,
            "gameplay_marker": True,
            **(meta or {}),
        },
    )
    obj.location = Vector((x, y, z))
    return obj


def _ring(name, center, radius, tube, material, ctx, meta=None, segments=32):
    bm = bmesh.new()
    bmesh.ops.create_torus(bm, major_segments=segments, minor_segments=8,
                           location=(0.0, 0.0, 0.0),
                           major_radius=radius, minor_radius=tube)
    x, y, z = center
    obj = finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind="resource_marker",
        dims=(2.0 * (radius + tube), 2.0 * (radius + tube), 2.0 * tube),
        meta={
            "visual_only": True, "navigation_blocker": False,
            "los_blocker": False, "gameplay_marker": True,
            **(meta or {}),
        },
    )
    obj.location = Vector((x, y, z))
    return obj


def _pillar(name, center, radius, height, material, ctx, meta=None):
    return _cylinder(name, center, radius, height, material, ctx,
                      kind="resource_landmark", sides=8, meta=meta)


def _make_resource_pair(ctx, resource_type, pair_name, x, y, radius, anchor, supporting):
    """Create the canonical L marker and its exact mirrored R counterpart."""
    mats = {
        "SpeedShrine": _material(ctx, "outer_boundary_aether"),
        "HealthRelic": _material(ctx, "outer_boundary_stone"),
    }
    marker_mat = mats.get(resource_type) or _material(ctx, "rock")
    z = _terrain_z(ctx, x, y)
    mirror_z = _terrain_z(ctx, -x, y)
    assert abs(z - mirror_z) <= MIRROR_TOLERANCE_M, (
        "resource terrain is not symmetric: {} {}".format(resource_type, pair_name)
    )

    objects = []
    for suffix, mx in (("L", x), ("R", -x)):
        base = _cylinder(
            "{}_Base_{}".format(pair_name, suffix),
            (mx, y, z + 0.20),
            radius,
            0.40,
            _material(ctx, "outer_boundary_stone"),
            ctx,
            meta={
                "resource_type": resource_type,
                "resource_id": pair_name,
                "team_pair": "{}_L<->{}_R".format(pair_name, pair_name),
                "resource_anchor": anchor,
                "supporting_landmark": supporting,
            },
        )
        ring = _ring(
            "{}_Ring_{}".format(pair_name, suffix),
            (mx, y, z + 0.42),
            radius * 0.78,
            0.18,
            marker_mat,
            ctx,
            meta={"resource_type": resource_type, "resource_id": pair_name},
        )
        post = _pillar(
            "{}_Pillar_{}".format(pair_name, suffix),
            (mx, y, z + 1.35),
            radius * 0.16,
            1.90,
            marker_mat,
            ctx,
            meta={"resource_type": resource_type, "resource_id": pair_name},
        )
        post2 = _pillar(
            "{}_PillarB_{}".format(pair_name, suffix),
            (mx, y, z + 1.00),
            radius * 0.10,
            1.20,
            _material(ctx, "outer_boundary_stone"),
            ctx,
            meta={"resource_type": resource_type, "resource_id": pair_name},
        )
        objects.extend((base, ring, post, post2))
    return objects


def audit_resource_symmetry(objects):
    by_name = {o.name: o for o in objects}
    failures = []
    max_error = 0.0
    for obj in objects:
        if not obj.name.endswith("_L"):
            continue
        pair = by_name.get(obj.name[:-2] + "_R")
        if pair is None:
            failures.append((obj.name, "missing counterpart"))
            continue
        expected = Vector((-obj.location.x, obj.location.y, obj.location.z))
        err = (pair.location - expected).length
        max_error = max(max_error, err)
        if err > MIRROR_TOLERANCE_M:
            failures.append((obj.name, err))
    return {"passed": not failures, "max_error_m": max_error, "failures": failures}


def generate_resource_foundation(ctx):
    cfg = ctx.config.get("resource_foundation", {})
    if not cfg.get("enabled", True):
        return {"enabled": False, "objects": [], "symmetry_passed": True, "max_error_m": 0.0}

    layout = ctx.layout
    center = layout["Center"]
    west = layout["WestMonolith"]
    sw = layout["SWMonolith"]

    west_anchor = center.lerp(west, float(cfg.get("speed_anchor_t", 0.52)))
    south_anchor = center.lerp(sw, float(cfg.get("health_anchor_t", 0.52)))

    speed_offset = float(cfg.get("speed_offset_y", -3.5))
    health_offset = float(cfg.get("health_offset_y", -3.5))

    speed_x = abs(float(west_anchor.x))
    speed_y = float(west_anchor.y) + speed_offset
    health_x = abs(float(south_anchor.x))
    health_y = float(south_anchor.y) + health_offset

    created = []
    created.extend(_make_resource_pair(
        ctx, "SpeedShrine", "SpeedShrinePair",
        speed_x, speed_y, float(cfg.get("speed_shrine_radius", 2.8)),
        anchor="Center↔West/EastMonolith", supporting="SideApproachLandmark"))
    created.extend(_make_resource_pair(
        ctx, "HealthRelic", "HealthRelicPair",
        health_x, health_y, float(cfg.get("health_relic_radius", 2.4)),
        anchor="Center↔SW/SEMonolith", supporting="SouthApproachLandmark"))

    report = audit_resource_symmetry(created)
    print("  -> V0.6.4.1 resources: pairs=2 | markers=2 | visual_objects={} | symmetry={} | max_error={:.6f}m".format(
        len(created), "PASS" if report["passed"] else "FAIL", report["max_error_m"]))
    return {
        "enabled": True,
        "pairs": ["SpeedShrinePair", "HealthRelicPair"],
        "resource_types": ["SpeedShrine", "HealthRelic"],
        "objects": created,
        **report,
    }