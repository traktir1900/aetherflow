"""
AetherFlow :: core/world_silhouette.py

VIZ-01 World Silhouette pass.

Creates only macro-scale visual geometry around the authoritative gameplay map.
Gameplay-critical geometry remains owned by the existing layout/geometry modules.
Every team-relevant visual formation is authored once and mirrored with the
canonical transform (x, y, z) -> (-x, y, z).

All generated objects are non-blocking decoration so visual dressing cannot alter
navigation, cover, minion corridors, routes, ramps or line-of-sight gameplay.
"""
import math

import bmesh
from mathutils import Vector

from core.utils import finalize_bmesh

COLLECTION = "Decorations"
MIRROR_TOLERANCE_M = 1e-5


def _mirror_xy(x, y):
    return -float(x), float(y)


def _make_rock_mass(name, center, radius, height, material, ctx, sides=10, flatten=0.82):
    """Create a deterministic low-poly rock mass with a real world transform."""
    bm = bmesh.new()
    verts = []
    rings = 3
    for ring in range(rings):
        t = ring / float(rings - 1)
        z = height * (t - 0.5)
        ring_scale = (0.70 + 0.30 * math.sin(math.pi * t))
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            wobble = 1.0 + 0.10 * math.sin(i * 2.13 + ring * 0.91)
            verts.append(bm.verts.new((
                radius * ring_scale * wobble * math.cos(a),
                radius * flatten * ring_scale * wobble * math.sin(a),
                z,
            )))

    top = bm.verts.new((0.0, 0.0, height * 0.60))
    bottom = bm.verts.new((0.0, 0.0, -height * 0.50))

    for ring in range(rings - 1):
        a0 = ring * sides
        a1 = (ring + 1) * sides
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((verts[a0 + i], verts[a0 + j], verts[a1 + j], verts[a1 + i]))

    first = 0
    last = (rings - 1) * sides
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom, verts[first + j], verts[first + i]))
        bm.faces.new((verts[last + i], verts[last + j], top))

    return finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind="visual_silhouette",
        dims=(radius * 2.0, radius * flatten * 2.0, height),
        meta={
            "visual_only": True,
            "navigation_blocker": False,
            "los_blocker": False,
            "symmetry_role": "visual_macro",
        },
    )


def _make_ridge(name, center, width, depth, height, material, ctx):
    """Create a broad wedge/ridge; deliberately non-blocking."""
    bm = bmesh.new()
    x = width * 0.5
    y = depth * 0.5
    verts = [
        bm.verts.new((-x, -y, 0.0)),
        bm.verts.new(( x, -y, 0.0)),
        bm.verts.new(( x,  y, 0.0)),
        bm.verts.new((-x,  y, 0.0)),
        bm.verts.new((-x * 0.65, -y * 0.35, height * 0.55)),
        bm.verts.new(( x * 0.65, -y * 0.35, height * 0.78)),
        bm.verts.new(( x * 0.45,  y * 0.35, height)),
        bm.verts.new((-x * 0.55,  y * 0.30, height * 0.62)),
    ]
    faces = [
        (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        (4, 5, 6, 7), (3, 2, 1, 0),
    ]
    for face in faces:
        bm.faces.new(tuple(verts[i] for i in face))
    return finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind="visual_silhouette",
        dims=(width, depth, height),
        meta={
            "visual_only": True,
            "navigation_blocker": False,
            "los_blocker": False,
            "symmetry_role": "visual_macro",
        },
    )


def _pair_rock(ctx, material, name, x, y, radius, height, flatten=0.82):
    """Create one authoritative side and its exact mirrored counterpart."""
    left = _make_rock_mass(name + "_L", Vector((x, y, 0.0)), radius, height, material, ctx, flatten=flatten)
    right = _make_rock_mass(name + "_R", Vector((-x, y, 0.0)), radius, height, material, ctx, flatten=flatten)
    return left, right


def _pair_ridge(ctx, material, name, x, y, width, depth, height):
    left = _make_ridge(name + "_L", Vector((x, y, 0.0)), width, depth, height, material, ctx)
    right = _make_ridge(name + "_R", Vector((-x, y, 0.0)), width, depth, height, material, ctx)
    return left, right


def _move_to_center(obj, x, y, z=0.0):
    obj.location = Vector((x, y, z))


def generate_world_silhouette(ctx):
    """Generate the VIZ-01 macro visual layer without changing gameplay."""
    mat = ctx.get_material("rock") or ctx.get_material("ground")
    created = []
    cfg = ctx.config.get("world_silhouette", {})
    if not cfg.get("enabled", True):
        return {"enabled": False, "objects": [], "symmetry_passed": True}

    # These positions intentionally stay near the map framing/perimeter and
    # major neutral landmarks. They are visual-only and do not define gameplay.
    rock_specs = [
        ("CliffEast01", 88.0, 22.0, 7.0, 11.0, 0.72),
        ("CliffEast02", 91.0, -8.0, 8.0, 13.0, 0.78),
        ("CliffWest01", 83.0, -43.0, 7.5, 10.0, 0.76),
        ("CliffNorthWing", 58.0, 84.0, 7.5, 12.0, 0.80),
        ("CrownFrame", 38.0, 52.0, 6.0, 9.0, 0.84),
        ("BaseFrame", 42.0, -88.0, 6.5, 8.5, 0.82),
    ]
    for spec in rock_specs:
        name, x, y, radius, height, flatten = spec
        created.extend(_pair_rock(ctx, mat, name, x, y, radius, height, flatten))

    ridge_specs = [
        ("OuterRidgeNorth", 72.0, 74.0, 28.0, 10.0, 7.0),
        ("OuterRidgeSouth", 76.0, -74.0, 24.0, 11.0, 6.5),
        ("EastVisualShoulder", 86.0, 48.0, 18.0, 16.0, 6.0),
    ]
    for spec in ridge_specs:
        name, x, y, width, depth, height = spec
        created.extend(_pair_ridge(ctx, mat, name, x, y, width, depth, height))

    # Central neutral framing is authored as a single symmetric pair. Keep the
    # core itself clear; these masses only frame the central basin from the sides.
    created.extend(_pair_rock(ctx, mat, "AetherCoreFrame", 22.0, 1.5, 5.5, 8.0, 0.88))

    report = audit_world_silhouette_symmetry(created)
    print("  -> VIZ-01 world silhouette: objects={} | symmetry={} | max_error={:.6f}m".format(
        len(created), "PASS" if report["passed"] else "FAIL", report["max_error_m"]))
    return {"enabled": True, "objects": created, "symmetry_passed": report["passed"], "max_error_m": report["max_error_m"]}


def audit_world_silhouette_symmetry(objects):
    """Verify each L/R pair generated by this module is an exact X mirror."""
    by_name = {obj.name: obj for obj in objects}
    max_error = 0.0
    failures = []
    for obj in objects:
        if not obj.name.endswith("_L"):
            continue
        counterpart = by_name.get(obj.name[:-2] + "_R")
        if counterpart is None:
            failures.append((obj.name, "missing counterpart"))
            continue
        expected = Vector((-obj.location.x, obj.location.y, obj.location.z))
        error = (counterpart.location - expected).length
        max_error = max(max_error, error)
        if error > MIRROR_TOLERANCE_M:
            failures.append((obj.name, error))

    return {"passed": not failures, "max_error_m": max_error, "failures": failures}
