"""AetherFlow road-center light guides.

Adds a thin luminous strip down the center of every generated strategic road,
using 20% of that road's width. The guide follows the exact road centerline
and visually links capture platforms together without changing navigation.
"""
import math
import bmesh
from mathutils import Vector

from core.layout import RING_NODES, RING_ANGLES, polar
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

COLLECTION = "Roads"
WRAPPER_MARKER = "_aetherflow_road_light_guides_runtime"


def _ribbon(ctx, name, points, width, material, meta=None):
    pts = [Vector(p) for p in points]
    if len(pts) < 2:
        return None
    cfg = ctx.config
    lift = max(0.025, cfg.get("road_z_offset", 0.02) + 0.02)
    bm = bmesh.new()
    prev = None
    for idx, point in enumerate(pts):
        if idx == 0:
            tangent = pts[1] - pts[0]
        elif idx == len(pts) - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[idx + 1] - pts[idx - 1]
        tangent = Vector((tangent.x, tangent.y, 0.0))
        if tangent.length < 1e-6:
            tangent = Vector((1.0, 0.0, 0.0))
        tangent.normalize()
        perp = Vector((-tangent.y, tangent.x, 0.0)) * (width / 2.0)
        left = point - perp
        right = point + perp
        left.z = get_height_at_point(left, cfg, ctx.layout) + lift
        right.z = get_height_at_point(right, cfg, ctx.layout) + lift
        vl = bm.verts.new(left)
        vr = bm.verts.new(right)
        if prev is not None:
            bm.faces.new((prev[0], prev[1], vr, vl))
        prev = (vl, vr)

    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    return finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind="road_light_guide",
        dims=dims, meta=meta or {},
    )


def _arc_points(radius, start_deg, end_deg, segments=14):
    delta = end_deg - start_deg
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    count = max(8, int(abs(delta) / 6.0) + 1, segments)
    return [polar(radius, start_deg + delta * i / float(count)) for i in range(count + 1)]


def _quadratic_points(p0, p1, inward_bend, samples=18):
    p0, p1 = Vector(p0), Vector(p1)
    mid = (p0 + p1) * 0.5
    radial = Vector((mid.x, mid.y, 0.0))
    control = mid if radial.length < 1e-6 else mid - radial.normalized() * inward_bend
    n = max(10, samples)
    return [(1-t)*(1-t)*p0 + 2*(1-t)*t*control + t*t*p1 for t in [i/n for i in range(n+1)]]


def generate(ctx):
    cfg = ctx.config
    guide_width = cfg["ring_road_width"] * 0.20
    built = []

    for i in range(len(RING_NODES)):
        a = RING_NODES[i]
        b = RING_NODES[(i + 1) % len(RING_NODES)]
        points = _arc_points(cfg["outer_ring_radius"], RING_ANGLES[a], RING_ANGLES[b])
        built.append(_ribbon(
            ctx, "RoadLightGuide_{}_{}".format(a, b), points, guide_width,
            ctx.get_material("road_light"),
            meta={
                "guide": "road_center_light",
                "width_fraction_of_parent_road": 0.20,
                "parent_road": "RingRoad_{}_{}".format(a, b),
                "from_platform": a,
                "to_platform": b,
                "visual_only": True,
                "connects_capture_platforms": True,
            }
        ))

    base_pairs = [("BlueBase", "SWMonolith", "Blue_SW"), ("RedBase", "SEMonolith", "Red_SE")]
    for start, end, tag in base_pairs:
        points = _quadratic_points(ctx.layout[start], ctx.layout[end], inward_bend=7.5, samples=18)
        built.append(_ribbon(
            ctx, "RoadLightGuide_Base_{}".format(tag), points, cfg["base_road_width"] * 0.20,
            ctx.get_material("road_light"),
            meta={
                "guide": "road_center_light",
                "width_fraction_of_parent_road": 0.20,
                "parent_road": "BaseRoad_{}".format(tag),
                "from_platform": start,
                "to_platform": end,
                "visual_only": True,
                "connects_capture_platforms": start in RING_NODES or end in RING_NODES,
            }
        ))

    points = _quadratic_points(ctx.layout["Crown"], polar(cfg["center_radius"], 90.0), inward_bend=0.0, samples=18)
    built.append(_ribbon(
        ctx, "RoadLightGuide_Crown_Core", points, cfg["north_ramp_width"] * 0.20,
        ctx.get_material("road_light"),
        meta={
            "guide": "road_center_light",
            "width_fraction_of_parent_road": 0.20,
            "parent_road": "North_Ramp_Crown_Core",
            "from_platform": "Crown",
            "to_platform": "Center",
            "visual_only": True,
            "connects_capture_platforms": True,
        }
    ))

    print("  -> Road center light guides: width=20% of parent road | segments={} | platform-linked".format(len(built)))
    return built
