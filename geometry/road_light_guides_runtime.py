"""AetherFlow capture-platform road-center light guides.

One luminous strip runs along the exact center of every ring road connecting
one capture platform to the next. Its width is exactly 20% of the parent road
width. This is visual-only geometry and does not alter navigation.
"""
import math
import bmesh
from mathutils import Vector

from core.layout import RING_NODES, RING_ANGLES, polar
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

COLLECTION = "Roads"


def _arc_points(radius, start_deg, end_deg, segments=14):
    delta = end_deg - start_deg
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    count = max(8, int(abs(delta) / 6.0) + 1, segments)
    return [polar(radius, start_deg + delta * i / float(count))
            for i in range(count + 1)]


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


def generate(ctx):
    cfg = ctx.config
    guide_width = cfg["ring_road_width"] * 0.20
    built = []

    # The authoritative road network already forms the complete 5-platform
    # ring. Mirror its exact objective order and radius for the light guide.
    for i in range(len(RING_NODES)):
        a = RING_NODES[i]
        b = RING_NODES[(i + 1) % len(RING_NODES)]
        points = _arc_points(
            cfg["outer_ring_radius"],
            RING_ANGLES[a],
            RING_ANGLES[b],
        )
        obj = _ribbon(
            ctx,
            "RoadLightGuide_{}_{}".format(a, b),
            points,
            guide_width,
            ctx.get_material("road_light"),
            meta={
                "guide": "road_center_light",
                "width_fraction_of_parent_road": 0.20,
                "parent_road": "RingRoad_{}_{}".format(a, b),
                "from_platform": a,
                "to_platform": b,
                "visual_only": True,
                "connects_capture_platforms": True,
                "platform_endpoint_a": "CaptureButton_{}".format(a),
                "platform_endpoint_b": "CaptureButton_{}".format(b),
            },
        )
        if obj is not None:
            built.append(obj)

    print(
        "  -> Road center light guides: 20% road width | "
        "platform-to-platform ring links={} | visual-only".format(len(built))
    )
    return built
