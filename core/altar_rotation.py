"""
AetherFlow :: core/altar_rotation.py

Focused gameplay hardening for the v0.6.2.1 map:

  * enforce a real minimum planar clearance between CoreCover geometry and
    the Aether Altar surface;
  * add a distinct, NON-BLOCKING Altar_Obstacle_* visual landmark category so
    the altar is no longer represented exclusively by CoreCover;
  * compute a deterministic macro-rotation metric from the real nav routes
    between adjacent objectives, instead of treating every Base->Objective
    route as "rotation";
  * keep secondary central rocks from re-colliding with repaired CoreCover.

The altar obstacles intentionally use an unrecognised navigation/export kind
(`altar_obstacle`), so they are exported as props and do not alter walkability.
"""
import math

import bmesh
from mathutils import Vector

from core.layout import RING_NODES
from core.utils import finalize_bmesh


def _world_xy_vertices(obj):
    """Yield world-space XY vertices for an object."""
    mw = obj.matrix_world
    for v in obj.data.vertices:
        p = mw @ v.co
        yield float(p.x), float(p.y)


def _closest_vertex_xy(obj):
    best = None
    best_d2 = float("inf")
    for x, y in _world_xy_vertices(obj):
        d2 = x * x + y * y
        if d2 < best_d2:
            best_d2 = d2
            best = (x, y)
    return best, math.sqrt(best_d2) if best is not None else float("inf")


def _min_clearance_to_altar(obj, altar_radius):
    """Minimum planar vertex-to-altar-surface distance in metres."""
    _, radius = _closest_vertex_xy(obj)
    return radius - altar_radius


def _repair_central_rocks(ctx, push=2.75):
    """Move Core_Rock_* anchors outward to keep central combat lanes clear."""
    moved = []
    for rec in ctx.generated_objects:
        name = rec.get("name", "")
        if not name.startswith("Core_Rock_"):
            continue
        obj = rec.get("object")
        if obj is None:
            continue
        x, y = float(obj.location.x), float(obj.location.y)
        radius = math.hypot(x, y)
        if radius < 1e-6:
            continue
        obj.location.x += (x / radius) * push
        obj.location.y += (y / radius) * push
        meta = rec.setdefault("meta", {})
        meta["central_space_repair_m"] = round(
            float(meta.get("central_space_repair_m", 0.0)) + push, 3)
        moved.append((name, push))
    return moved


def ensure_altar_clearance(ctx, min_clearance=8.0, target_clearance=8.5):
    """Push CoreCover objects outward until real mesh clearance reaches target.

    The repair uses the actual closest world-space mesh vertex. It applies
    deterministic iterations because the nearest point on a rotated footprint
    does not generally lie on the object's pivot-to-origin radial.
    """
    cfg = ctx.config
    altar_radius = float(cfg["altar"]["base_radius1"])
    moved = []

    for rec in ctx.generated_objects:
        name = rec.get("name", "")
        if not name.startswith("Core_Cover_"):
            continue
        obj = rec.get("object")
        if obj is None:
            continue

        before = _min_clearance_to_altar(obj, altar_radius)
        if before >= min_clearance:
            continue

        last = before
        for _ in range(12):
            (vx, vy), _ = _closest_vertex_xy(obj)
            direction = Vector((vx, vy, 0.0))
            if direction.length < 1e-6:
                direction = Vector((float(obj.location.x), float(obj.location.y), 0.0))
            if direction.length < 1e-6:
                direction = Vector((1.0, 0.0, 0.0))
            direction.normalize()

            needed = target_clearance - last
            if needed <= 0.0:
                break
            obj.location.x += direction.x * max(needed * 1.08, 0.05)
            obj.location.y += direction.y * max(needed * 1.08, 0.05)
            new_clearance = _min_clearance_to_altar(obj, altar_radius)
            if new_clearance <= last + 1e-4:
                break
            last = new_clearance
            if last >= target_clearance:
                break

        after = _min_clearance_to_altar(obj, altar_radius)
        rec.setdefault("meta", {})["altar_clearance_repair"] = {
            "before_m": round(before, 3),
            "after_m": round(after, 3),
            "target_m": round(target_clearance, 3),
            "verified": bool(after >= min_clearance),
        }
        moved.append((name, before, after))

    # The central secondary rocks are decorative tactical blockers. Shift them
    # outward as part of the same repair stage so a later cover move cannot
    # recreate a solid overlap inside the Aether fight space.
    _repair_central_rocks(ctx)
    return moved


def generate_altar_obstacles(ctx):
    """Create four distinct non-blocking altar perimeter obstacles."""
    cfg = ctx.config
    altar_r = float(cfg["altar"]["base_radius1"])
    ring_r = max(10.0, altar_r + 9.0)
    height = 2.6
    radius = 0.8
    built = []

    # Four diagonal positions keep the altar's cardinal sightlines usable.
    for i, ang in enumerate((45.0, 135.0, 225.0, 315.0), 1):
        rad = math.radians(ang)
        pos = Vector((ring_r * math.cos(rad), ring_r * math.sin(rad),
                      cfg["heights"]["AetherCore"]))

        bm = bmesh.new()
        bmesh.ops.create_cone(
            bm, cap_ends=True, segments=8,
            radius1=radius, radius2=radius * 0.72, depth=height,
        )
        bmesh.ops.translate(bm, verts=bm.verts,
                            vec=pos + Vector((0.0, 0.0, height / 2.0)))

        built.append(finalize_bmesh(
            bm,
            "Altar_Obstacle_{:02d}".format(i),
            "Decorations",
            ctx.get_material("rock"),
            ctx,
            kind="altar_obstacle",
            dims=(radius * 2.0, radius * 2.0, height),
            meta={
                "landmark": "AetherAltar",
                "non_blocking": True,
                "ring_radius": round(ring_r, 3),
                "role": "altar_perimeter_visual",
            },
        ))

    return built


def analyze_macro_rotation(ctx, nav_report):
    """Measure the real 5-objective ring rotation from obstacle-aware nav data."""
    routes = nav_report.get("routes", {}) if nav_report else {}
    points = list(RING_NODES)
    speed = float(ctx.config.get("simulation", {}).get("agent_speed", 6.0))
    speed = speed if speed > 0.0 else 6.0
    rows = []

    for i, a in enumerate(points):
        b = points[(i + 1) % len(points)]
        key_ab = "{}->{}".format(a, b)
        key_ba = "{}->{}".format(b, a)
        d = routes.get(key_ab)
        if d is None:
            d = routes.get(key_ba)
        rows.append({"from": a, "to": b, "distance_m": d,
                     "time_s": None if d is None else round(float(d) / speed, 2)})

    valid = [r["time_s"] for r in rows if r["time_s"] is not None]
    result = {
        "definition": "adjacent_capture_point_ring_edges",
        "routes": rows,
        "all_reachable": len(valid) == len(rows),
        "average_time_s": None,
        "min_time_s": None,
        "max_time_s": None,
        "variance_s": None,
        "agent_speed_mps": speed,
    }
    if valid:
        result["average_time_s"] = round(sum(valid) / len(valid), 2)
        result["min_time_s"] = round(min(valid), 2)
        result["max_time_s"] = round(max(valid), 2)
        result["variance_s"] = round(max(valid) - min(valid), 2)
    return result
