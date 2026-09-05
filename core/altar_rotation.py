"""
AetherFlow :: core/altar_rotation.py

Focused gameplay hardening for the v0.6.2.1 map:

  * enforce a real minimum planar clearance between CoreCover geometry and
    the Aether Altar surface;
  * add a distinct, NON-BLOCKING Altar_Obstacle_* visual landmark category so
    the altar is no longer represented exclusively by CoreCover;
  * compute a deterministic macro-rotation metric from the real nav routes
    between adjacent objectives, instead of treating every Base->Objective
    route as "rotation".

The altar obstacles intentionally use an unrecognised navigation/export kind
(`altar_obstacle`), so they are exported as props and do not alter walkability.
"""
import math

import bmesh
from mathutils import Vector

from core.layout import RING_NODES
from core.utils import finalize_bmesh


def _world_xy_vertices(obj):
    """Yield evaluated world-space XY vertices for an object."""
    mw = obj.matrix_world
    for v in obj.data.vertices:
        p = mw @ v.co
        yield float(p.x), float(p.y)


def _min_clearance_to_altar(obj, altar_radius):
    """Minimum planar vertex-to-altar-surface distance in metres."""
    values = []
    for x, y in _world_xy_vertices(obj):
        values.append(math.hypot(x, y) - altar_radius)
    return min(values) if values else float("inf")


def ensure_altar_clearance(ctx, min_clearance=8.0, target_clearance=8.5):
    """Push CoreCover objects outward until their real mesh clears the altar.

    The repair is deterministic and idempotent.  It operates on actual mesh
    vertices rather than only object pivots, which matches the gameplay audit's
    vertex-to-surface measurement.
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

        clearance = _min_clearance_to_altar(obj, altar_radius)
        if clearance >= min_clearance:
            continue

        cx, cy = float(obj.location.x), float(obj.location.y)
        radius = math.hypot(cx, cy)
        if radius < 1e-6:
            continue

        # Move the whole cover radially outward just enough to reach the
        # target, preserving its local shape and rotation.
        shift = target_clearance - clearance
        obj.location.x += (cx / radius) * shift
        obj.location.y += (cy / radius) * shift
        new_clearance = _min_clearance_to_altar(obj, altar_radius)
        rec.setdefault("meta", {})["altar_clearance_repair"] = {
            "before_m": round(clearance, 3),
            "after_m": round(new_clearance, 3),
            "target_m": round(target_clearance, 3),
        }
        moved.append((name, clearance, new_clearance))

    return moved


def generate_altar_obstacles(ctx):
    """Create four distinct non-blocking altar perimeter obstacles."""
    cfg = ctx.config
    altar_r = float(cfg["altar"]["base_radius1"])
    ring_r = max(10.0, altar_r + 9.0)
    height = max(2.0, cfg["heights"]["AetherCore"] * 0.0 + 2.6)
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
    rows = []

    for i, a in enumerate(RING_NODES):
        b = RING_NODES[(i + 1) % len(RING_NODES)]
        key_ab = "{}->{}".format(a, b)
        key_ba = "{}->{}".format(b, a)
        d = routes.get(key_ab)
        if d is None:
            d = routes.get(key_ba)
        rows.append({"from": a, "to": b, "distance_m": d,
                     "time_s": None if d is None else round(float(d) / 6.0, 2)})

    valid = [r["time_s"] for r in rows if r["time_s"] is not None]
    result = {
        "definition": "adjacent_capture_point_ring_edges",
        "routes": rows,
        "all_reachable": len(valid) == len(rows),
        "average_time_s": None,
        "min_time_s": None,
        "max_time_s": None,
        "variance_s": None,
    }
    if valid:
        result["average_time_s"] = round(sum(valid) / len(valid), 2)
        result["min_time_s"] = round(min(valid), 2)
        result["max_time_s"] = round(max(valid), 2)
        result["variance_s"] = round(max(valid) - min(valid), 2)
    return result
