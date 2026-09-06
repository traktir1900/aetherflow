"""AetherFlow VIZ-01: mirrored macro world silhouette."""
import math
import bmesh
from mathutils import Vector
from core.utils import finalize_bmesh

COLLECTION = "Decorations"
MIRROR_TOLERANCE_M = 1e-5


def _rock(name, center, radius, height, material, ctx, flatten=0.82, sides=10):
    bm = bmesh.new()
    rings = 3
    verts = []
    for ring in range(rings):
        t = ring / float(rings - 1)
        z = height * (t - 0.5)
        ring_scale = 0.70 + 0.30 * math.sin(math.pi * t)
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            wobble = 1.0 + 0.10 * math.sin(i * 2.13 + ring * 0.91)
            verts.append(bm.verts.new((
                radius * ring_scale * wobble * math.cos(a),
                radius * flatten * ring_scale * wobble * math.sin(a), z)))
    top = bm.verts.new((0.0, 0.0, height * 0.60))
    bottom = bm.verts.new((0.0, 0.0, -height * 0.50))
    for ring in range(rings - 1):
        a0, a1 = ring * sides, (ring + 1) * sides
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((verts[a0+i], verts[a0+j], verts[a1+j], verts[a1+i]))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bottom, verts[j], verts[i]))
        bm.faces.new((verts[(rings-1)*sides+i], verts[(rings-1)*sides+j], top))
    obj = finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind="visual_silhouette",
        dims=(radius * 2.0, radius * flatten * 2.0, height),
        meta={"visual_only": True, "navigation_blocker": False,
              "los_blocker": False, "symmetry_role": "visual_macro"})
    obj.location = Vector(center)
    return obj


def _ridge(name, center, width, depth, height, material, ctx):
    bm = bmesh.new()
    x, y = width * 0.5, depth * 0.5
    verts = [
        bm.verts.new((-x,-y,0)), bm.verts.new((x,-y,0)), bm.verts.new((x,y,0)), bm.verts.new((-x,y,0)),
        bm.verts.new((-x*.65,-y*.35,height*.55)), bm.verts.new((x*.65,-y*.35,height*.78)),
        bm.verts.new((x*.45,y*.35,height)), bm.verts.new((-x*.55,y*.30,height*.62))]
    for ids in [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7),(3,2,1,0)]:
        bm.faces.new(tuple(verts[i] for i in ids))
    obj = finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind="visual_silhouette",
        dims=(width, depth, height),
        meta={"visual_only": True, "navigation_blocker": False,
              "los_blocker": False, "symmetry_role": "visual_macro"})
    obj.location = Vector(center)
    return obj


def _pair_rock(ctx, material, name, x, y, radius, height, flatten):
    return [
        _rock(name + "_L", (x, y, 0.0), radius, height, material, ctx, flatten),
        _rock(name + "_R", (-x, y, 0.0), radius, height, material, ctx, flatten),
    ]


def _pair_ridge(ctx, material, name, x, y, width, depth, height):
    return [
        _ridge(name + "_L", (x, y, 0.0), width, depth, height, material, ctx),
        _ridge(name + "_R", (-x, y, 0.0), width, depth, height, material, ctx),
    ]


def audit_world_silhouette_symmetry(objects):
    by_name = {obj.name: obj for obj in objects}
    max_error = 0.0
    failures = []
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


def generate_world_silhouette(ctx):
    """Build macro visual framing; never blocks gameplay/navigation."""
    cfg = ctx.config.get("world_silhouette", {})
    if not cfg.get("enabled", True):
        return {"enabled": False, "objects": [], "symmetry_passed": True, "max_error_m": 0.0}
    material = ctx.get_material("rock") or ctx.get_material("ground")
    created = []
    rock_specs = [
        ("OuterCliff01", 88.0, 22.0, 7.0, 11.0, 0.72),
        ("OuterCliff02", 91.0, -8.0, 8.0, 13.0, 0.78),
        ("OuterCliff03", 83.0, -43.0, 7.5, 10.0, 0.76),
        ("NorthCliffWing", 58.0, 84.0, 7.5, 12.0, 0.80),
        ("CrownFrame", 38.0, 52.0, 6.0, 9.0, 0.84),
        ("BaseFrame", 42.0, -88.0, 6.5, 8.5, 0.82),
        ("AetherCoreFrame", 22.0, 1.5, 5.5, 8.0, 0.88),
    ]
    for item in rock_specs:
        created.extend(_pair_rock(ctx, material, *item))
    ridge_specs = [
        ("OuterRidgeNorth", 72.0, 74.0, 28.0, 10.0, 7.0),
        ("OuterRidgeSouth", 76.0, -74.0, 24.0, 11.0, 6.5),
        ("VisualShoulder", 86.0, 48.0, 18.0, 16.0, 6.0),
    ]
    for item in ridge_specs:
        created.extend(_pair_ridge(ctx, material, *item))
    report = audit_world_silhouette_symmetry(created)
    print("  -> VIZ-01 world silhouette: objects={} | symmetry={} | max_error={:.6f}m".format(
        len(created), "PASS" if report["passed"] else "FAIL", report["max_error_m"]))
    return {"enabled": True, "objects": created, **report}
