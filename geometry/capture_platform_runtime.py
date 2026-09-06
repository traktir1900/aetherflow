"""AetherFlow capture platform runtime geometry + logical anchors.

Each capture platform gets a central interaction button taking exactly 70% of
the platform radius. The remaining 30% is a circular capture indicator ring.
The button is now registered as the logical capture-control anchor used by
roads/ramps/export, while capture-state gameplay itself remains unchanged.
"""
import math
import bmesh
from mathutils import Vector

from core.heightmap import get_height_at_point
from core.layout import RING_NODES
from core.utils import finalize_bmesh


COLLECTION = "CapturePoints"
WRAPPER_MARKER = "_aetherflow_capture_platform_runtime"


def _annulus(ctx, name, center, inner_r, outer_r, height, material, meta=None):
    """Create a solid annulus as one mesh object."""
    segments = max(24, int(ctx.config.get("circle_segments", 28)))
    top_z = center.z + height
    bm = bmesh.new()

    verts_top_inner = []
    verts_top_outer = []
    verts_bottom_inner = []
    verts_bottom_outer = []

    for i in range(segments):
        a = 2.0 * math.pi * (i / float(segments))
        ca, sa = math.cos(a), math.sin(a)
        verts_bottom_inner.append(
            bm.verts.new((center.x + inner_r * ca, center.y + inner_r * sa, center.z))
        )
        verts_bottom_outer.append(
            bm.verts.new((center.x + outer_r * ca, center.y + outer_r * sa, center.z))
        )
        verts_top_inner.append(
            bm.verts.new((center.x + inner_r * ca, center.y + inner_r * sa, top_z))
        )
        verts_top_outer.append(
            bm.verts.new((center.x + outer_r * ca, center.y + outer_r * sa, top_z))
        )

    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((verts_top_outer[i], verts_top_outer[j],
                      verts_top_inner[j], verts_top_inner[i]))
        bm.faces.new((verts_bottom_inner[i], verts_bottom_inner[j],
                      verts_bottom_outer[j], verts_bottom_outer[i]))
        bm.faces.new((verts_top_inner[i], verts_top_inner[j],
                      verts_bottom_inner[j], verts_bottom_inner[i]))
        bm.faces.new((verts_bottom_outer[i], verts_bottom_outer[j],
                      verts_top_outer[j], verts_top_outer[i]))

    return finalize_bmesh(
        bm, name, COLLECTION, material, ctx, kind="capture_indicator",
        dims=(outer_r * 2.0, outer_r * 2.0, height), meta=meta or {},
    )


def _button(ctx, pname, center, radius, height):
    bm = bmesh.new()
    segments = max(24, int(ctx.config.get("circle_segments", 28)))
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=segments,
        radius1=radius, radius2=radius, depth=height,
    )
    bmesh.ops.translate(
        bm, verts=bm.verts,
        vec=center + Vector((0.0, 0.0, height / 2.0)),
    )
    return finalize_bmesh(
        bm, "CaptureButton_{}".format(pname), COLLECTION,
        ctx.get_material("stone"), ctx, kind="capture_button",
        dims=(radius * 2.0, radius * 2.0, height),
        meta={
            "point": pname,
            "platform_radius_fraction": 0.70,
            "radius": round(radius, 3),
            "height": round(height, 3),
            "visual_only": False,
            "logical_capture_control": True,
            "road_anchor": pname,
            "capture_zone_center": [round(center.x, 3), round(center.y, 3), round(center.z, 3)],
        },
    )


def _build_overlays(ctx):
    cfg = ctx.config
    plat_r = cfg["capture_platform_radius"]
    plat_h = cfg["capture_platform_height"]
    button_r = plat_r * 0.70
    indicator_inner_r = button_r
    indicator_outer_r = plat_r
    ring_h = max(0.025, plat_h * 0.20)
    button_h = max(0.08, plat_h * 0.50)
    platform_lift = max(0.02, plat_h * 0.10)

    built = 0
    ctx.capture_buttons.clear()

    for pname in RING_NODES:
        pos = ctx.layout[pname].copy()
        terrain_z = get_height_at_point(pos, cfg, ctx.layout)
        platform_top_z = terrain_z + plat_h
        ring_base = Vector((pos.x, pos.y, platform_top_z + platform_lift))

        _annulus(
            ctx,
            "CaptureIndicatorRing_{}".format(pname),
            ring_base,
            indicator_inner_r,
            indicator_outer_r,
            ring_h,
            ctx.get_material("altar_glow"),
            meta={
                "point": pname,
                "indicator": "capture",
                "inner_radius": round(indicator_inner_r, 3),
                "outer_radius": round(indicator_outer_r, 3),
                "visual_only": True,
                "logical_capture_ring": True,
                "capture_anchor": pname,
            },
        )

        button_base = Vector((pos.x, pos.y, platform_top_z + platform_lift + ring_h))
        button = _button(ctx, pname, button_base, button_r, button_h)
        ctx.capture_buttons[pname] = button
        built += 2

    print(
        "  -> Capture platform overlays: button=70% radius | "
        "remaining 30%=capture indicator ring | logical anchors=5 | built={}".format(built)
    )
    return built


def bind_capture_buttons_to_routes(ctx):
    """Attach every objective-touching road/ramp record to its button anchor."""
    bindings = []
    missing = []
    button_names = {p: "CaptureButton_{}".format(p) for p in RING_NODES}

    def bind_record(rec, endpoint, point):
        if point not in button_names:
            return False
        meta = rec.setdefault("meta", {})
        meta["capture_button_{}".format(endpoint)] = button_names[point]
        meta["logical_capture_endpoint_{}".format(endpoint)] = point
        bindings.append("{}:{}->{}".format(rec["name"], endpoint, button_names[point]))
        return True

    for rec in ctx.generated_objects:
        if rec.get("type") not in ("road", "ramp"):
            continue
        meta = rec.setdefault("meta", {})
        start = meta.get("start")
        end = meta.get("end")
        point = meta.get("point")

        if start in button_names:
            bind_record(rec, "start", start)
        if end in button_names:
            bind_record(rec, "end", end)
        if point in button_names:
            bind_record(rec, "end", point)

        # North ramp uses its explicit generated name/curve rather than a
        # start/end metadata pair; its destination is the Crown button.
        if rec["name"] == "North_Ramp_Crown_Core":
            bind_record(rec, "end", "Crown")

    for pname in RING_NODES:
        touching = [
            b for b in bindings
            if "CaptureButton_{}".format(pname) in b
        ]
        if not touching:
            missing.append(pname)

    print(
        "  -> Capture button route binding: {} endpoints linked | missing={}".format(
            len(bindings), missing or "NONE"
        )
    )
    return {"bindings": bindings, "missing": missing, "passed": not missing}


def install_capture_platform_runtime(structures_module):
    """Wrap capture-point generation and add platform button + ring geometry."""
    original = getattr(structures_module, "generate_capture_points", None)
    if original is None or getattr(original, WRAPPER_MARKER, False):
        return False

    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        ctx = args[0] if args else kwargs.get("ctx")
        if ctx is not None:
            _build_overlays(ctx)
        return result

    setattr(wrapper, WRAPPER_MARKER, True)
    structures_module.generate_capture_points = wrapper
    return True
