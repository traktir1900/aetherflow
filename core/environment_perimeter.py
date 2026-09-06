"""AetherFlow V0.6.4.3 — Environment + Perimeter.

Visual-only environment pass layered on top of authoritative gameplay geometry.
Perimeter spires are intentionally disabled; remaining environment accents do
not change terrain, roads, ramps, navigation, LOS, or gameplay blockers.
"""
import math

import bmesh
from mathutils import Vector

from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

COLLECTION = "Decorations"
MIRROR_TOLERANCE_M = 1e-5


def _terrain_z(ctx, x, y):
    return get_height_at_point(Vector((x, y, 0.0)), ctx.config, ctx.layout)


def _material(ctx, name, fallback="rock"):
    return ctx.get_material(name) or ctx.get_material(fallback) or ctx.get_material("ground")


def _cone(name, x, y, radius, height, material, ctx, taper=0.72, sides=10, role="environment"):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=sides,
        radius1=radius,
        radius2=radius * taper,
        depth=height,
        calc_uvs=False,
    )
    z = _terrain_z(ctx, x, y)
    obj = finalize_bmesh(
        bm, name, COLLECTION, material, ctx,
        kind="environment_landmark",
        dims=(radius * 2.0, radius * 2.0, height),
        meta={
            "visual_only": True,
            "navigation_blocker": False,
            "los_blocker": False,
            "environment_pass": "v0.6.4.3",
            "environment_role": role,
        },
    )
    obj.location = Vector((x, y, z + height * 0.5))
    return obj


def _low_ridge(name, x, y, width, depth, height, material, ctx, role="height_accent"):
    bm = bmesh.new()
    hx, hy = width * 0.5, depth * 0.5
    verts = [
        bm.verts.new((-hx, -hy, 0.0)), bm.verts.new((hx, -hy, 0.0)),
        bm.verts.new((hx, hy, 0.0)), bm.verts.new((-hx, hy, 0.0)),
        bm.verts.new((-hx * 0.55, -hy * 0.30, height * 0.55)),
        bm.verts.new((hx * 0.60, -hy * 0.25, height * 0.72)),
        bm.verts.new((hx * 0.45, hy * 0.35, height)),
        bm.verts.new((-hx * 0.50, hy * 0.30, height * 0.58)),
    ]
    for ids in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6),
                (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)):
        bm.faces.new(tuple(verts[i] for i in ids))
    z = _terrain_z(ctx, x, y)
    obj = finalize_bmesh(
        bm, name, COLLECTION, material, ctx,
        kind="environment_landmark",
        dims=(width, depth, height),
        meta={
            "visual_only": True,
            "navigation_blocker": False,
            "los_blocker": False,
            "environment_pass": "v0.6.4.3",
            "environment_role": role,
        },
    )
    obj.location = Vector((x, y, z))
    return obj


def _mirror_cone_pair(ctx, material, name, x, y, radius, height, taper, role):
    return [
        _cone(f"{name}_L", x, y, radius, height, material, ctx, taper=taper, role=role),
        _cone(f"{name}_R", -x, y, radius, height, material, ctx, taper=taper, role=role),
    ]


def _mirror_ridge_pair(ctx, material, name, x, y, width, depth, height, role):
    return [
        _low_ridge(f"{name}_L", x, y, width, depth, height, material, ctx, role=role),
        _low_ridge(f"{name}_R", -x, y, width, depth, height, material, ctx, role=role),
    ]


def audit_symmetry(objects):
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
        error = (pair.location - expected).length
        max_error = max(max_error, error)
        if error > MIRROR_TOLERANCE_M:
            failures.append((obj.name, error))
    return {"passed": not failures, "max_error_m": max_error, "failures": failures}


def generate_environment_perimeter(ctx):
    """Generate V0.6.4.3 visual environment without perimeter spires."""
    cfg = ctx.config.get("environment_perimeter", {})
    if not cfg.get("enabled", True):
        return {"enabled": False, "objects": [], "symmetry_passed": True, "max_error_m": 0.0}

    rock_mat = _material(ctx, "rock")
    aether_mat = _material(ctx, "outer_boundary_aether", "rock")
    created = []

    # Perimeter spires intentionally disabled after visual review.
    perimeter_specs = []

    ridge_specs = [
        ("EnvHeightRidge01", 74.0, 58.0, 15.0, 7.0, 2.8),
        ("EnvHeightRidge02", 83.0, -56.0, 18.0, 8.0, 3.2),
        ("EnvHeightRidge03", 55.0, 88.0, 20.0, 7.0, 3.0),
    ]
    for name, x, y, width, depth, height in ridge_specs:
        created.extend(_mirror_ridge_pair(ctx, rock_mat, name, x, y, width, depth, height, "existing_height_language"))

    crown = ctx.layout["Crown"]
    for idx, (dx, dy, r, h) in enumerate(((7.5, -2.5, 1.35, 4.8), (5.5, 7.0, 1.1, 4.2))):
        created.extend(_mirror_cone_pair(
            ctx, aether_mat, f"CrownApproachLandmark{idx+1:02d}",
            float(crown.x) + dx, float(crown.y) + dy,
            r, h, 0.58, "crown_approach_landmark"))

    # AetherCore landmark spires intentionally disabled after visual review.
    # Keep only the low north frame; remove all central green-keg landmarks.
    core = ctx.layout["Center"]
    # Central AetherCoreLandmark01-03 generation intentionally omitted.

    created.append(_low_ridge(
        "AetherCoreNorthFrame", float(core.x), float(core.y) + 6.8,
        7.0, 2.0, 2.4, aether_mat, ctx, role="aethercore_north_frame"))

    report = audit_symmetry(created)
    print(
        "  -> V0.6.4.3 environment perimeter: objects={} | perimeter_spires=0 | "
        "height_ridges=6 | crown_landmarks=4 | core_landmarks=0 | symmetry={} | "
        "max_error={:.6f}m".format(
            len(created),
            "PASS" if report["passed"] else "FAIL",
            report["max_error_m"],
        )
    )
    return {"enabled": True, "objects": created, **report}
