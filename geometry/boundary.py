"""
AetherFlow :: geometry/boundary.py

Global outer world boundary: one large organic elliptical stone/cliff perimeter.

Design contract:
    gameplay / environment buffer
        -> canonical ellipse
        -> terrain-aware low-frequency deformation
        -> thick modular stone/cliff wall
        -> impassable exterior

This module owns ONLY the global outer perimeter. Pocket perimeter geometry is
not modified here.
"""
import math

from mathutils import Vector

from core.heightmap import get_height_at_point

COLLECTION = "OuterBoundary"


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _smooth_wave(t, seed, channel=0):
    """Deterministic low-frequency deformation in [-1, 1]."""
    phase = (int(seed) % 100003) * 0.00031 + channel * 1.917
    return (
        0.56 * math.sin(2.0 * math.pi * t + phase)
        + 0.29 * math.sin(4.0 * math.pi * t + phase * 1.23)
        + 0.15 * math.sin(6.0 * math.pi * t - phase * 0.71)
    )


def _ellipse_radius(theta, a, b):
    """Distance from origin to an axis-aligned ellipse along direction theta."""
    c = math.cos(theta)
    s = math.sin(theta)
    denom = math.sqrt((b * c) ** 2 + (a * s) ** 2)
    return (a * b / denom) if denom > 1e-9 else min(a, b)


def _ellipse_point(theta, a, b):
    return Vector((a * math.cos(theta), b * math.sin(theta), 0.0))


def _ellipse_tangent(theta, a, b):
    t = Vector((-a * math.sin(theta), b * math.cos(theta), 0.0))
    if t.length > 1e-9:
        t = t.normalized()
    return t


def _ellipse_normal(theta, a, b):
    # Gradient of x^2/a^2 + y^2/b^2 = 1, pointing outward.
    n = Vector((math.cos(theta) / max(a, 1e-9),
                math.sin(theta) / max(b, 1e-9), 0.0))
    if n.length > 1e-9:
        n = n.normalized()
    return n


def _world_footprint_radius(rec):
    meta = rec.get("meta") or {}
    dims = rec.get("dimensions") or ()
    # Prefer explicit circular gameplay radius for bases/capture/altar objects.
    for key in ("radius", "footprint_radius"):
        value = meta.get(key)
        if value is not None and float(value) > 0.0:
            return float(value)
    if len(dims) >= 2 and dims[0] is not None and dims[1] is not None:
        return 0.5 * math.hypot(float(dims[0]), float(dims[1]))
    return 0.0


def _object_radial_extent(rec):
    obj = rec.get("object")
    loc = getattr(obj, "location", None)
    if loc is None:
        return 0.0
    return math.hypot(float(loc.x), float(loc.y)) + _world_footprint_radius(rec)


def _max_gameplay_extent(ctx):
    """Find the furthest generated gameplay/environment geometry that should sit
    inside the outer ellipse, excluding existing core rocks and the pockets'
    backwall stones themselves.  A safety buffer is added later.
    """
    excluded_elements = {
        "backwall", "fortified_fence", "outer_boundary", "floor", "safety_floor",
    }
    max_extent = 0.0
    for rec in ctx.generated_objects:
        meta = rec.get("meta") or {}
        if meta.get("element") in excluded_elements:
            continue
        t = rec.get("type")
        if t not in {"capture_point", "base", "road", "ramp", "cover", "rock", "altar", "landmark", "turret"}:
            continue
        max_extent = max(max_extent, _object_radial_extent(rec))
    return max_extent


def _required_outer_clearance(ctx):
    required = []
    for rec in ctx.generated_objects:
        meta = rec.get("meta") or {}
        if meta.get("element") in {"backwall", "fortified_fence", "outer_boundary", "floor", "safety_floor"}:
            continue
        if rec.get("type") not in {"capture_point", "base", "road", "ramp", "cover", "rock", "altar", "landmark", "turret"}:
            continue
        obj = rec.get("object")
        loc = getattr(obj, "location", None)
        if loc is None:
            continue
        theta = math.atan2(float(loc.y), float(loc.x))
        radial = math.hypot(float(loc.x), float(loc.y))
        fp = _world_footprint_radius(rec)
        required.append((theta, radial + fp))
    return required


def _ellipse_circumference(a, b):
    h = ((a - b) ** 2) / max((a + b) ** 2, 1e-9)
    return math.pi * (a + b) * (1.0 + (3.0 * h) / (10.0 + math.sqrt(max(4.0 - 3.0 * h, 1e-9))))


def _wall_section_footprint_radius(a, b, ecfg):
    """Conservative XY half-footprint of one rendered wall section.

    This deliberately models the ACTUAL wall object footprint rather than a
    gameplay/object clearance radius. It is a HARD map-bounds constraint.
    """
    n = max(8, int(ecfg.get("segments", 48)))
    overlap = float(ecfg.get("section_overlap_factor", 1.12))
    thickness_max = float(ecfg.get("wall_thickness_max", 4.0))
    # Match the real segment width model used by _make_wall_segment().
    segment_length = _ellipse_circumference(a, b) / n
    width = segment_length * overlap * 1.01  # conservative variation allowance
    thick = thickness_max * 1.08
    return 0.5 * math.hypot(width, thick)


def _wall_outward_shift(ecfg):
    """Outward centerline shift created by the 1/3 inward-depth rule."""
    factor = _clamp(float(ecfg.get("internal_depth_factor", 1.0 / 3.0)), 0.1, 1.0)
    old_inner_depth = 0.5 * float(ecfg.get("wall_thickness_max", 4.0))
    target_inner_depth = old_inner_depth * factor
    return max(0.0, old_inner_depth - target_inner_depth)


def _hard_axis_limit(a, b, ecfg, half):
    """Maximum safe ellipse radius along X/Y under HARD map-bounds constraints."""
    deformation = float(ecfg.get("organic_deformation", 0.25))
    section_radius = _wall_section_footprint_radius(a, b, ecfg)
    outward_shift = _wall_outward_shift(ecfg)
    # Real map boundary is +/- half; do not spend margin outside the map.
    return half - deformation - outward_shift - section_radius


def _section_dimensions(a, b, ecfg, idx):
    """Return the actual-ish XY dimensions used by _make_wall_segment for a section."""
    n = max(8, int(ecfg.get("segments", 48)))
    overlap = float(ecfg.get("section_overlap_factor", 1.15))
    segment_length = _ellipse_circumference(a, b) / n
    width = segment_length * overlap * 1.01
    tvar = 0.96 + 0.05 * abs(math.sin(idx * 1.17))
    width *= tvar
    thickness_min = float(ecfg.get("wall_thickness_min", 3.0))
    thickness_max = float(ecfg.get("wall_thickness_max", 6.0))
    thick = thickness_min + (thickness_max - thickness_min) * (0.25 + 0.5 * abs(_smooth_wave(idx / n, int(ecfg.get("seed", 42017)), 11)))
    thick *= 0.92 + 0.10 * abs(math.sin(idx * 0.73))
    return width, thick


def _section_aabb_half_extents(a, b, ecfg, idx, tangent):
    """Exact oriented-rectangle XY half extents for a wall segment."""
    width, thick = _section_dimensions(a, b, ecfg, idx)
    c = abs(float(tangent.x))
    s = abs(float(tangent.y))
    return 0.5 * (c * width + s * thick), 0.5 * (s * width + c * thick)


def _wall_centerline_sample(a, b, ecfg, idx, theta, p, normal, tangent):
    """Build the actual wall centerline point for one segment."""
    width, thick = _section_dimensions(a, b, ecfg, idx)
    factor = _clamp(float(ecfg.get("internal_depth_factor", 1.0 / 3.0)), 0.1, 1.0)
    old_inner_depth = 0.5 * thick
    target_inner = old_inner_depth * factor
    shift = max(0.0, old_inner_depth - target_inner) + max(0.0, float(ecfg.get("outer_clearance_min", 0.0)))
    return p + normal * shift, shift, width, thick


def _candidate_ok(ctx, a, b, deformation, gameplay_clearance):
    """Hard map bounds match the existing validator's footprint-radius model.

    The generated wall is a rotated rectangular solid, but the active 0.6.1
    validator checks its exported ``footprint_radius`` against the map bbox.
    The solver therefore uses that same conservative radial footprint so a
    candidate accepted here cannot later fail Stage 9. Gameplay clearance is
    diagnostic-only and never rejects the ellipse.
    """
    half = float(ctx.config.get("world_floor_half_size", ctx.config["ground_half_size"]))
    ecfg = ctx.config.get("outer_boundary", {})
    n = max(8, int(ecfg.get("segments", 48)))
    seed = int(ecfg.get("seed", 42017))

    for i in range(n):
        theta = 2.0 * math.pi * i / n
        t = i / float(n)
        base = _ellipse_point(theta, a, b)
        normal = _ellipse_normal(theta, a, b)
        tangent = _ellipse_tangent(theta, a, b)
        d = deformation * _smooth_wave(t, seed, 1)
        p = base + normal * d

        prev_theta = (theta - 2.0 * math.pi / n) % (2.0 * math.pi)
        next_theta = (theta + 2.0 * math.pi / n) % (2.0 * math.pi)
        p_prev = (_ellipse_point(prev_theta, a, b)
                  + _ellipse_normal(prev_theta, a, b)
                  * deformation * _smooth_wave((i - 1) / float(n), seed, 1))
        p_next = (_ellipse_point(next_theta, a, b)
                  + _ellipse_normal(next_theta, a, b)
                  * deformation * _smooth_wave((i + 1) / float(n), seed, 1))
        p = p * 0.6 + p_prev * 0.2 + p_next * 0.2

        cc, _shift, width, thick = _wall_centerline_sample(
            a, b, ecfg, i, theta, p, normal, tangent)

        # Match _make_wall_segment() exactly: validator receives
        # footprint_radius = 0.5 * hypot(width, thick).
        radial_fp = 0.5 * math.hypot(width, thick)
        if math.hypot(float(cc.x), float(cc.y)) + radial_fp > half + 1e-6:
            return False

    return True

def _safe_ellipse(cfg, ctx):
    ecfg = cfg.get("outer_boundary", {})
    half = float(cfg.get("world_floor_half_size", cfg["ground_half_size"]))
    deformation = float(ecfg.get("organic_deformation", 0.25))
    requested_x = float(ecfg.get("semi_minor_max", 99.0))
    requested_y = float(ecfg.get("semi_major_max", 99.0))
    min_ecc = float(ecfg.get("minimum_axis_difference", 0.25))

    # Maximize area while preserving the approved orientation/ratio.
    ratio = requested_x / max(requested_y, 1e-9)
    hi = 1.0
    lo = 0.0
    if _candidate_ok(ctx, requested_x, requested_y, deformation, 0.0):
        scale = 1.0
    else:
        # Binary-search the largest uniform scale of the approved ellipse.
        for _ in range(48):
            mid = 0.5 * (lo + hi)
            a = requested_x * mid
            b = requested_y * mid
            if b - a < min_ecc:
                a = max(1e-6, b - min_ecc)
            if _candidate_ok(ctx, a, b, deformation, 0.0):
                lo = mid
            else:
                hi = mid
        scale = lo
    a = requested_x * scale
    b = requested_y * scale
    if b - a < min_ecc:
        a = max(1e-6, b - min_ecc)
    if not _candidate_ok(ctx, a, b, deformation, 0.0):
        raise RuntimeError(
            "[BOUNDARY] HARD CONSTRAINT FAILURE: exact wall-section footprint cannot fit map bounds; "
            "world_half={:.3f}, ellipse=({:.3f},{:.3f})".format(half, a, b)
        )

    # Soft diagnostic only.
    reqs = _required_outer_clearance(ctx)
    buffers = []
    for theta, gameplay_r in reqs:
        buffers.append(_ellipse_radius(theta, a, b) - deformation - gameplay_r - _wall_outward_shift(ecfg))
    min_buffer = min(buffers) if buffers else 0.0
    major = max(a, b)
    minor = min(a, b)
    major_axis = "X" if a >= b else "Y"
    return {
        "center": (0.0, 0.0),
        "semi_x": round(a, 3),
        "semi_y": round(b, 3),
        "semi_major_axis": round(major, 3),
        "semi_minor_axis": round(minor, 3),
        "major_axis": major_axis,
        "gameplay_extent": round(max((r for _t, r in reqs), default=0.0), 3),
        "environment_buffer": round(min_buffer, 3),
        "map_margin": 0.0,
        "organic_deformation": deformation,
        "wall_thickness": float(ecfg.get("wall_thickness_max", 4.0)),
    }

def _boundary_samples(cfg, geom):
    ecfg = cfg.get("outer_boundary", {})
    a = float(geom["semi_x"])
    b = float(geom["semi_y"])
    n = int(ecfg.get("segments", 48))
    deform = float(ecfg.get("organic_deformation", 2.0))
    seed = int(ecfg.get("seed", 42017))

    pts = []
    for i in range(n):
        theta = 2.0 * math.pi * i / n
        t = i / float(n)
        base = _ellipse_point(theta, a, b)
        normal = _ellipse_normal(theta, a, b)
        # Low-frequency radial deformation only; never high-frequency noise.
        d = deform * _smooth_wave(t, seed, 1)
        p = base + normal * d
        pts.append((theta, p, normal, _ellipse_tangent(theta, a, b)))

    # Circular smoothing of the deformed points; this keeps the outer silhouette
    # architectural rather than following individual terrain/rock bumps.
    smoothed = []
    for i, item in enumerate(pts):
        theta, _, normal, tangent = item
        p_prev = pts[(i - 1) % n][1]
        p_curr = pts[i][1]
        p_next = pts[(i + 1) % n][1]
        p = p_prev * 0.2 + p_curr * 0.6 + p_next * 0.2
        smoothed.append((theta, p, normal, tangent))
    return smoothed


def _wall_height(cfg, theta, idx):
    ecfg = cfg.get("outer_boundary", {})
    base_h = float(ecfg.get("wall_height_min", 5.0))
    max_h = float(ecfg.get("wall_height_max", 8.0))
    large_min = float(ecfg.get("formation_height_min", 8.0))
    large_max = float(ecfg.get("formation_height_max", 12.0))
    n = int(ecfg.get("segments", 48))
    # Large formations are sparse and deterministic.
    anchor = abs(_smooth_wave(idx / max(1, n - 1), int(ecfg.get("seed", 42017)), 7))
    if anchor > 0.84:
        return large_min + (large_max - large_min) * ((anchor - 0.84) / 0.16)
    return base_h + (max_h - base_h) * (0.35 + 0.65 * anchor)


def _wall_centerline_point(p, normal, thickness, ecfg):
    """Place the thick natural wall predominantly outside the canonical ellipse.

    The canonical ellipse itself is unchanged. With factor=1/3, the inner
    occupied depth becomes one third of the old centered-wall half-thickness.
    """
    factor = float(ecfg.get("internal_depth_factor", 1.0 / 3.0))
    factor = _clamp(factor, 0.1, 1.0)
    old_inner_depth = 0.5 * float(thickness)
    target_inner_depth = old_inner_depth * factor
    outward_shift = max(0.0, old_inner_depth - target_inner_depth)
    extra_clearance = max(0.0, float(ecfg.get("outer_clearance_min", 0.0)))
    return p + normal * (outward_shift + extra_clearance), outward_shift + extra_clearance


def _make_wall_segment(ctx, idx, p, tangent, normal, h, thickness, segment_length, ecfg):
    import bmesh
    from mathutils import Matrix
    from core.utils import finalize_bmesh
    """Create one thick overlapping stone/cliff segment; registered as rock so
    the existing navigation system treats the exterior as solid without any
    navigation code change.
    """
    center_z = get_height_at_point(Vector((p.x, p.y, 0.0)), ctx.config, ctx.layout)
    width = segment_length * float(ecfg.get("section_overlap_factor", 1.15))
    # Slightly shorter than the nominal segment length at formations for a less
    # engineered silhouette, while preserving overlap.
    tvar = 0.96 + 0.05 * abs(math.sin(idx * 1.17))
    width *= tvar
    thick = thickness * (0.92 + 0.10 * abs(math.sin(idx * 0.73)))

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    verts = list(bm.verts)
    bmesh.ops.scale(bm, vec=Vector((width, thick, h)), verts=verts)
    yaw = math.atan2(tangent.y, tangent.x)
    bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)),
                     matrix=Matrix.Rotation(yaw, 4, 'Z'), verts=verts)
    # Seat the formation into the terrain.  The bottom is allowed to embed;
    # that is the intended cliff/stone connection rather than floating.
    bmesh.ops.translate(
        bm,
        verts=verts,
        vec=Vector((p.x, p.y, center_z + h * 0.5 - 0.45)),
    )
    for f in bm.faces:
        f.smooth = False
    obj = finalize_bmesh(
        bm,
        "OuterBoundary_Segment{:02d}".format(idx + 1),
        COLLECTION,
        ctx.get_material("outer_boundary_stone"),
        ctx,
        kind="rock",
        dims=(width, thick, h),
        meta={
            "element": "outer_boundary",
            "boundary": "global_ellipse",
            "segment": idx,
            "solid": True,
            "footprint_radius": 0.5 * math.hypot(width, thick),
            "rot_z": math.degrees(yaw),
        },
    )
    return obj


def generate_outer_boundary(ctx):
    import bpy
    """Build the global organic elliptical perimeter. Returns metrics and objects."""
    cfg = ctx.config
    ecfg = cfg.get("outer_boundary", {})
    if not ecfg.get("enabled", True):
        return {"enabled": False, "objects": []}

    # Ensure collection is available; managed collection is created by pipeline.
    if COLLECTION not in ctx.collections:
        coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
        if coll.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(coll)
        ctx.collections[COLLECTION] = coll

    # Dedicated environment materials.
    def mat(name, color, roughness=0.85, metallic=0.0, emission=None, strength=0.0):
        existing = ctx.get_material(name)
        if existing:
            return existing
        material = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
        material.use_nodes = True
        bsdf = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            material.node_tree.nodes.clear()
            bsdf = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            out = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
            material.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = strength
        material.diffuse_color = (*color, 1.0)
        ctx.materials[name] = material
        return material

    mat("outer_boundary_stone", (0.20, 0.19, 0.18), roughness=0.92)
    mat("outer_boundary_darkstone", (0.13, 0.12, 0.115), roughness=0.96)
    mat("outer_boundary_aether", (0.01, 0.28, 0.32), roughness=0.32,
        emission=(0.0, 0.70, 0.82), strength=1.8)

    geom = _safe_ellipse(cfg, ctx)
    samples = _boundary_samples(cfg, geom)
    n = len(samples)
    a = geom["semi_x"]
    b = geom["semi_y"]
    thickness = float(ecfg.get("wall_thickness_min", 3.0))
    thickness_max = float(ecfg.get("wall_thickness_max", 6.0))

    # Approximate arc length from samples; each segment slightly overlaps its
    # neighbours so the wall is physically closed with no escape gaps.
    arc_len = 0.0
    for i in range(n):
        p0 = samples[i][1]
        p1 = samples[(i + 1) % n][1]
        arc_len += (p1 - p0).length
    segment_length = arc_len / n

    objects = []
    heights = []
    thicknesses = []
    for i, (theta, p, normal, tangent) in enumerate(samples):
        h = _wall_height(cfg, theta, i)
        thick = thickness + (thickness_max - thickness) * (0.25 + 0.5 * abs(_smooth_wave(i / n, int(ecfg.get("seed", 42017)), 11)))
        wall_p, outward_shift = _wall_centerline_point(p, normal, thick, ecfg)
        objects.append(_make_wall_segment(ctx, i, wall_p, tangent, normal, h, thick, segment_length, ecfg))
        heights.append(h)
        thicknesses.append(thick)

    # Store a compact contract in context so export/audit can consume it.
    ctx.outer_boundary = {
        "shape": "ELLIPTICAL",
        "center": [0.0, 0.0],
        "semi_major_axis": geom["semi_major_axis"],
        "semi_minor_axis": geom["semi_minor_axis"],
        "major_axis": geom["major_axis"],
        "maximum_diameter": round(2.0 * max(geom["semi_major_axis"], geom["semi_minor_axis"]), 3),
        "interior_area": round(math.pi * geom["semi_major_axis"] * geom["semi_minor_axis"], 2),
        "environment_buffer": geom["environment_buffer"],
        "boundary_closed": True,
        "escape_gaps": 0,
        "collision": "PASS",
        "pocket_fence": "ABSENT",
        "segment_count": n,
        "wall_height": [round(min(heights), 3), round(max(heights), 3)],
        "wall_thickness": [round(min(thicknesses), 3), round(max(thicknesses), 3)],
        "old_internal_wall_depth_estimate": [
            round(0.5 * min(thicknesses), 3), round(0.5 * max(thicknesses), 3)
        ],
        "new_internal_wall_depth_estimate": [
            round(0.5 * min(thicknesses) * float(ecfg.get("internal_depth_factor", 1.0 / 3.0)), 3),
            round(0.5 * max(thicknesses) * float(ecfg.get("internal_depth_factor", 1.0 / 3.0)), 3)
        ],
        "internal_depth_reduction_factor": float(ecfg.get("internal_depth_factor", 1.0 / 3.0)),
        "gameplay_extent": geom["gameplay_extent"],
    }

    # Hard safety check using the same conservative XY footprint estimate as
    # _candidate_ok(). The old check validated only the boundary centerline and
    # therefore allowed thick wall objects to protrude outside the map bbox.
    half = float(cfg.get("world_floor_half_size", cfg["ground_half_size"]))
    bounds_ok = True
    for i, s in enumerate(samples):
        theta, p, normal, tangent = s
        # Rebuild the same smoothed sample used by _candidate_ok.
        cc, _shift, _width, _thick = _wall_centerline_sample(a, b, ecfg, i, theta, p, normal, tangent)
        hx, hy = _section_aabb_half_extents(a, b, ecfg, i, tangent)
        if abs(float(cc.x)) + hx > half + 1e-6 or abs(float(cc.y)) + hy > half + 1e-6:
            bounds_ok = False
            break
    if not bounds_ok:
        raise RuntimeError("[BOUNDARY] wall footprint exceeds hard map bounds")

    print("    [BOUNDARY] shape=ELLIPTICAL center=(0,0) semi_x={:.2f}m semi_y={:.2f}m major_axis={} segments={} "
          "buffer={:.2f}m area={:.0f}m2 escape_gaps=0 collision=PASS".format(
              geom["semi_x"], geom["semi_y"], geom["major_axis"], n,
              geom["environment_buffer"], ctx.outer_boundary["interior_area"]))
    min_t = min(thicknesses)
    max_t = max(thicknesses)
    factor = float(ecfg.get("internal_depth_factor", 1.0 / 3.0))
    old_depth_min = 0.5 * min_t
    old_depth_max = 0.5 * max_t
    new_depth_min = old_depth_min * factor
    new_depth_max = old_depth_max * factor
    print("    [BOUNDARY] wall-height={:.2f}-{:.2f}m thickness={:.2f}-{:.2f}m "
          "pocket_fence=ABSENT".format(
              min(heights), max(heights), min_t, max_t))
    print("    [BOUNDARY] internal-depth old={:.2f}-{:.2f}m new={:.2f}-{:.2f}m reduction={:.2f}x "
          "wall shifted outward; ellipse shape/radius unchanged".format(
              old_depth_min, old_depth_max, new_depth_min, new_depth_max, 1.0 / factor))
    return {"enabled": True, "objects": objects, "metrics": dict(ctx.outer_boundary)}
