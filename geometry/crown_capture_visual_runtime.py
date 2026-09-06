"""AetherFlow v0.6.4 Crown capture presentation correction.

Crown is a PvE Sanctum logical anchor. Its named indicator and button are
export/navigation anchors only; there is deliberately no CapturePlatform_Crown.
The boss stack is:

    Crown_BossRise / Crown_Throne
        -> Crown_BossButton (Aether Button)

The named controls are seated on the Sanctum rise and must never be treated as
the boss button or as normal capture gameplay.
"""
import bmesh
from mathutils import Vector

from core.layout import RING_NODES
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

COLLECTION = "Roads"
MARKER = "_aetherflow_crown_capture_visual_fix"


def _world_z_bounds(obj):
    if obj is None or getattr(obj, "type", None) != "MESH" or obj.data is None:
        return None, None
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if not verts:
        return None, None
    zs = [float(v.z) for v in verts]
    return min(zs), max(zs)


def _set_bottom_z(obj, target_z):
    bottom, _ = _world_z_bounds(obj)
    if bottom is None:
        return False
    obj.location.z += float(target_z) - bottom
    return True


def _set_material(obj, material):
    if obj is None or getattr(obj, "type", None) != "MESH" or material is None:
        return
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def _remove_registry_name(ctx, name):
    if not hasattr(ctx, "generated_objects"):
        return
    ctx.generated_objects[:] = [
        rec for rec in ctx.generated_objects if rec.get("name") != name
    ]


def _ribbon(ctx, name, start, end, width, material, meta):
    """Create a thin center guide that follows the terrain between two buttons."""
    a = Vector(start)
    b = Vector(end)
    pts = []
    samples = 12
    cfg = ctx.config
    for i in range(samples + 1):
        t = i / float(samples)
        x = a.x + (b.x - a.x) * t
        y = a.y + (b.y - a.y) * t
        terrain_z = get_height_at_point(Vector((x, y, 0.0)), cfg, ctx.layout)
        linear_z = a.z + (b.z - a.z) * t
        pts.append(Vector((x, y, max(terrain_z + 0.06, linear_z))))

    bm = bmesh.new()
    prev = None
    for i, point in enumerate(pts):
        if i == 0:
            tangent = pts[1] - pts[0]
        elif i == len(pts) - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[i + 1] - pts[i - 1]
        tangent = Vector((tangent.x, tangent.y, 0.0))
        if tangent.length < 1e-6:
            tangent = Vector((1.0, 0.0, 0.0))
        tangent.normalize()
        perp = Vector((-tangent.y, tangent.x, 0.0)) * (width * 0.5)
        left = point - perp
        right = point + perp
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
        bm,
        name,
        COLLECTION,
        material,
        ctx,
        kind="road_light_guide",
        dims=dims,
        meta=meta,
    )


def _button_record(ctx, name):
    for rec in getattr(ctx, "generated_objects", []):
        if rec.get("name") == name:
            return rec
    return None


def apply(ctx):
    """Seat Crown logical controls on the Sanctum rise without a platform."""
    import bpy

    crown_button = bpy.data.objects.get("CaptureButton_Crown")
    crown_ring = bpy.data.objects.get("CaptureIndicatorRing_Crown")
    boss_button = bpy.data.objects.get("Crown_BossButton")
    boss_rise = bpy.data.objects.get("Crown_BossRise")

    if crown_button is None or crown_ring is None or boss_rise is None:
        print("  [CROWN VISUAL] missing Crown Sanctum/logical overlay objects")
        return {"passed": False, "reason": "MISSING_CROWN_CAPTURE_OBJECTS"}

    _boss_min, _boss_top = _world_z_bounds(boss_button)
    rise_min, rise_top = _world_z_bounds(boss_rise)
    if rise_top is None:
        return {"passed": False, "reason": "NO_CROWN_SANCTUM_SUPPORT_HEIGHT"}

    capture_support_top = rise_top

    ring_clearance = 0.08
    button_clearance = 0.06

    capture_material = ctx.get_material("road_light") or ctx.get_material("altar_glow")
    _set_material(crown_ring, capture_material)
    _set_material(crown_button, capture_material)

    ring_bottom = capture_support_top + ring_clearance
    _set_bottom_z(crown_ring, ring_bottom)
    ring_min, ring_top = _world_z_bounds(crown_ring)

    button_bottom = (ring_top if ring_top is not None else ring_bottom) + button_clearance
    _set_bottom_z(crown_button, button_bottom)
    btn_min, btn_top = _world_z_bounds(crown_button)

    for rec, role in (
        (_button_record(ctx, "CaptureButton_Crown"), "capture_button"),
        (_button_record(ctx, "CaptureIndicatorRing_Crown"), "capture_indicator"),
    ):
        if rec is None:
            continue
        meta = rec.setdefault("meta", {})
        meta.update({
            "surface_anchor": "Crown_BossRise",
            "capture_platform": None,
            "capture_indicator": "CaptureIndicatorRing_Crown",
            "capture_control": "CaptureButton_Crown",
            "boss_button_separate": "Crown_BossButton",
            "actual_sanctum_support_top_z": round(capture_support_top, 3),
            "actual_world_bottom_z": round(
                btn_min if role == "capture_button" and btn_min is not None
                else ring_min if role == "capture_indicator" and ring_min is not None
                else 0.0,
                3,
            ),
            "pve_sanctum_anchor": True,
            "normal_capture_platform_absent": True,
            "boss_button_not_support": True,
            "post_generation_corrected": True,
        })

    # Two short visual links: Crown capture control -> adjacent capture controls.
    guide_width = float(ctx.config["ring_road_width"]) * 0.20
    made = 0
    for neighbor in ("WestMonolith", "EastMonolith"):
        neighbor_obj = bpy.data.objects.get("CaptureButton_{}".format(neighbor))
        if neighbor_obj is None:
            continue
        nmin, _ntop = _world_z_bounds(neighbor_obj)
        ncenter = neighbor_obj.matrix_world.translation
        ccenter = crown_button.matrix_world.translation
        start_z = btn_top if btn_top is not None else button_bottom
        end_z = nmin if nmin is not None else get_height_at_point(
            neighbor_obj.location, ctx.config, ctx.layout
        ) + 0.15
        name = "CrownCaptureLink_Crown_{}".format(neighbor)
        old = bpy.data.objects.get(name)
        if old is not None:
            try:
                bpy.data.objects.remove(old, do_unlink=True)
            except Exception:
                pass
            _remove_registry_name(ctx, name)
        obj = _ribbon(
            ctx,
            name,
            (ccenter.x, ccenter.y, start_z),
            (ncenter.x, ncenter.y, end_z),
            guide_width,
            ctx.get_material("road_light"),
            meta={
                "guide": "crown_capture_button_link",
                "from_button": "CaptureButton_Crown",
                "to_button": "CaptureButton_{}".format(neighbor),
                "from_platform": "Crown",
                "to_platform": neighbor,
                "width_fraction_of_parent_road": 0.20,
                "visual_only": True,
                "raised_platform_aware": True,
            },
        )
        if obj is not None:
            made += 1

    bpy.context.view_layer.update()
    print(
        "  -> [CROWN VISUAL] sanctum_support=Crown_BossRise | "
        "support_top={:.3f}m | indicator_bottom={}m | button_bottom={}m | "
        "boss_button=Crown_BossButton (SEPARATE)".format(
            capture_support_top,
            "{:.3f}".format(ring_min) if ring_min is not None else "NA",
            "{:.3f}".format(btn_min) if btn_min is not None else "NA",
        )
    )
    print(
        "  -> [CROWN VISUAL] capture links={} | neighbors=WestMonolith,EastMonolith | visual-only".format(made)
    )
    return {
        "passed": True,
        "sanctum_support_top_z": round(capture_support_top, 3),
        "boss_button_separate": True,
        "indicator_bottom_z": round(ring_min, 3) if ring_min is not None else None,
        "button_bottom_z": round(btn_min, 3) if btn_min is not None else None,
        "neighbor_links": made,
    }
