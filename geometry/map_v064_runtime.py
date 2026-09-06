"""AetherFlow v0.6.4 map cleanup + Crown perimeter opening patch.

Runtime-only compatibility layer for the iterative Blender generator:
- removes the obsolete central/default Cube including Blender suffix variants;
- removes the default cube even when an older scene has renamed or transformed
  the primitive, as long as it is still the small cube at the map origin;
- opens the global outer wall on the Crown axis with 1 m clearance on each side;
- keeps the opening deterministic and records it in ctx.outer_boundary.
"""
import math


_MARKER = "_aetherflow_v064_map_patch"
_CUBE_NAMES = {
    "cube",
    "centralcube",
    "central_cube",
    "centercube",
}


def _normalized_name(name):
    key = str(name or "").strip().lower()
    # Blender automatically creates Cube.001 / Cube.002 / ... when the old
    # default object is duplicated. Treat only a numeric suffix as equivalent
    # to the canonical name.
    if "." in key:
        base, suffix = key.rsplit(".", 1)
        if suffix.isdigit():
            key = base
    return key


def _looks_like_small_default_cube(obj):
    """Detect an old Blender default cube by geometry, not only by object name."""
    data = getattr(obj, "data", None)
    verts = getattr(data, "vertices", None)
    if verts is None or len(verts) != 8:
        return False

    try:
        xs = [float(v.co.x) for v in verts]
        ys = [float(v.co.y) for v in verts]
        zs = [float(v.co.z) for v in verts]
        dims = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    except Exception:
        return False

    # The Blender default Cube is a small near-unit cube after scene creation.
    # Allow modest transforms so old scenes with a renamed/scaled default cube
    # are still cleaned, but do not touch large gameplay structures.
    if min(dims) <= 1e-6 or max(dims) > 4.0:
        return False
    if max(dims) / min(dims) > 1.15:
        return False
    return True


def _is_obsolete_central_cube(obj):
    """Match the old central/default cube robustly without deleting real props."""
    if obj is None or getattr(obj, "type", None) != "MESH":
        return False

    loc = getattr(obj, "location", None)
    if loc is None:
        return False

    # The obsolete cube belongs to the original scene origin. Keep cleanup
    # local so legitimate cube/box props elsewhere on the map survive.
    if math.hypot(float(loc.x), float(loc.y)) > 10.0:
        return False

    name_match = _normalized_name(getattr(obj, "name", "")) in _CUBE_NAMES
    return name_match or _looks_like_small_default_cube(obj)


def remove_obsolete_central_cube(ctx=None):
    """Remove every obsolete default/central cube near the map origin."""
    import bpy

    removed = []
    for obj in list(bpy.data.objects):
        if not _is_obsolete_central_cube(obj):
            continue
        obj_name = str(obj.name)
        removed.append(obj_name)
        bpy.data.objects.remove(obj, do_unlink=True)

    if ctx is not None and removed and hasattr(ctx, "generated_objects"):
        removed_set = set(removed)
        ctx.generated_objects[:] = [
            rec for rec in ctx.generated_objects if rec.get("name") not in removed_set
        ]

    print("  -> v0.6.4 central cube cleanup: removed={}".format(removed or "NONE"))
    return removed


def _angle_delta(a, b):
    d = (a - b + math.pi) % (2.0 * math.pi) - math.pi
    return abs(d)


def install_outer_boundary_crown_opening(boundary_module):
    """Wrap generate_outer_boundary once and cut the north/Crown wall opening."""
    original = getattr(boundary_module, "generate_outer_boundary", None)
    if original is None or getattr(original, _MARKER, False):
        return False

    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        ctx = args[0] if args else kwargs.get("ctx")
        if ctx is None:
            return result

        try:
            _apply_crown_opening(ctx, result)
        except Exception as exc:
            print("  [CROWN OPENING] patch skipped: {}".format(exc))
        return result

    setattr(wrapper, _MARKER, True)
    boundary_module.generate_outer_boundary = wrapper
    return True


def _apply_crown_opening(ctx, result):
    import bpy

    crown = ctx.layout.get("Crown")
    if crown is None:
        return

    cfg = ctx.config
    radius = float(cfg.get("capture_platform_radius", 0.0))
    clearance = 1.0
    required_gap = 2.0 * radius + 2.0 * clearance
    crown_angle = math.atan2(float(crown.y), float(crown.x))

    wall_records = [
        rec for rec in ctx.generated_objects
        if rec.get("type") == "outer_boundary"
        or (rec.get("meta") or {}).get("element") == "outer_boundary"
    ]
    if not wall_records:
        return

    candidates = []
    boundary_radii = []
    for rec in wall_records:
        obj = rec.get("object")
        loc = getattr(obj, "location", None)
        if loc is None:
            continue
        r = math.hypot(float(loc.x), float(loc.y))
        boundary_radii.append(r)
        candidates.append((rec, obj, math.atan2(float(loc.y), float(loc.x)), r))

    if not candidates:
        return

    local_r = sum(boundary_radii) / float(len(boundary_radii))
    half_linear = required_gap * 0.5
    required_half_angle = math.atan2(half_linear, max(local_r, 1e-6))

    angles = sorted(item[2] for item in candidates)
    if len(angles) > 1:
        gaps = []
        for i, a0 in enumerate(angles):
            a1 = angles[(i + 1) % len(angles)]
            d = (a1 - a0) % (2.0 * math.pi)
            if d > 1e-6:
                gaps.append(d)
        pitch = min(gaps) if gaps else (2.0 * math.pi / max(len(angles), 1))
    else:
        pitch = 2.0 * math.pi
    removal_half_angle = required_half_angle + 0.5 * pitch

    removed = []
    removed_ids = set()
    for rec, obj, angle, _r in candidates:
        if _angle_delta(angle, crown_angle) <= removal_half_angle + 1e-9:
            removed.append(obj.name)
            removed_ids.add(id(obj))
            bpy.data.objects.remove(obj, do_unlink=True)

    if removed:
        removed_set = set(removed)
        ctx.generated_objects[:] = [
            rec for rec in ctx.generated_objects if rec.get("name") not in removed_set
        ]
        if isinstance(result, dict) and isinstance(result.get("objects"), list):
            result["objects"][:] = [
                obj for obj in result["objects"] if id(obj) not in removed_ids
            ]

    metrics = dict(getattr(ctx, "outer_boundary", {}) or {})
    metrics["crown_platform_opening"] = {
        "enabled": True,
        "alignment": "CROWN_NORTH_AXIS",
        "clearance_each_side_m": clearance,
        "platform_radius_m": round(radius, 3),
        "required_clear_width_m": round(required_gap, 3),
        "removed_wall_segments": removed,
        "intentional": True,
    }
    metrics["intentional_openings"] = ["CROWN_PLATFORM"]
    metrics["segment_count"] = max(0, int(metrics.get("segment_count", len(candidates))) - len(removed))
    metrics["boundary_closed"] = False if removed else metrics.get("boundary_closed", True)
    metrics["escape_gaps"] = 0
    ctx.outer_boundary = metrics

    print(
        "  -> Crown outer-wall opening: width>= {:.2f}m | clearance=1.00m each side | "
        "segments_removed={} | intentional entrance".format(required_gap, len(removed))
    )
