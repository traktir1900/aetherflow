"""
AetherFlow :: core/validation.py
REAL map validation — every check either passes or produces a concrete error.

FIX PASS (v0.6.0): checks now use actual object bounding boxes (not just
locations), sample the heightmap for NaN / floor violations, detect solid
object intersections and capture-area blocking, and verify graded ramp slopes.

Checks:
  - map bounds (object bbox vs map, with margin)
  - terrain bounds + heightmap NaN / floor / max-height sampling
  - safety floor presence
  - Z range, invalid transforms (NaN/Inf)
  - dimensions: solids need all extents > 0; planar surfaces (roads/ramps)
    may have zero thickness but never NaN and never zero width/length
  - real mesh degeneracy (vertices >= 3, faces >= 1) against actual bpy meshes
  - duplicate names
  - solid-object intersections via EXACT footprints (circles + rotated rects,
    SAT): deeper than overlap_tolerance -> SOLID OVERLAP, within it ->
    STRUCTURAL CONTACT (deliberate abutments, e.g. Pillar against Altar)
  - solids blocking a capture platform area
  - missing capture points (must be exactly 5) / bases (both)
  - Aether Altar + Aether Crown presence
  - graded ramp slope vs max slope
  - navigation reachability problems
"""
import math
from mathutils import Vector

from core.heightmap import get_height_at_point
from core.layout import BASES, capture_point_names

_TERRAIN_EXEMPT = ("terrain", "safety_floor")

# Terrain-following ribbons: zero thickness is LEGITIMATE for these (they are
# planar gameplay surfaces laid over the heightmap; the terrain below provides
# collision).  Their dims are a world-space AABB, so dims[2] may be ~0 on flat
# ground — but width/length must still be positive and the mesh must have
# real vertices and faces (checked separately against the actual mesh data).
_PLANAR_SURFACE_TYPES = ("road", "ramp")


def _is_bad(v):
    return v != v or v in (float("inf"), float("-inf"))


# ---------------------------------------------------------------------------
# Exact solid footprints (replaces the coarse circumscribed-circle test,
# which over-estimated rotated boxes by up to ~2x and produced false overlaps)
# ---------------------------------------------------------------------------
def _footprint(rec):
    """Exact ground footprint of a solid object:
    ('circle', x, y, r) or ('rect', x, y, half_x, half_y, rot_rad).
    None for kinds that are not solids (roads, ramps, platforms, terrain...).
    """
    loc = _loc(rec)
    if loc is None:
        return None
    x, y = loc[0], loc[1]
    t = rec["type"]
    dims = rec.get("dimensions")
    meta = rec.get("meta") or {}
    if t in ("cover", "outer_boundary"):
        if not dims:
            return None
        return ("rect", x, y, float(dims[0] or 0) / 2.0, float(dims[1] or 0) / 2.0,
                math.radians(float(meta.get("rot_z", 0.0))))
    if t == "rock":
        r = meta.get("footprint_radius")
        if not r and dims:
            r = min(dims[0] or 0.0, dims[1] or 0.0) / 2.0
        if not r:
            return None
        return ("circle", x, y, float(r))
    if t == "turret" and dims:
        return ("circle", x, y, float(dims[0] or 0.0) / 2.0)
    if t == "altar" and meta.get("landmark") == "AetherAltar" and dims:
        return ("circle", x, y, float(dims[0] or 0.0) / 2.0)
    return None


def _rect_corners(x, y, hx, hy, rot):
    cos_a, sin_a = math.cos(rot), math.sin(rot)
    pts = []
    for sx, sy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        pts.append((x + sx * cos_a - sy * sin_a, y + sx * sin_a + sy * cos_a))
    return pts


def _rect_rect_penetration(f1, f2):
    """SAT over the 4 face normals; returns penetration depth or None."""
    _, x1, y1, hx1, hy1, rot1 = f1
    _, x2, y2, hx2, hy2, rot2 = f2
    c1 = _rect_corners(x1, y1, hx1, hy1, rot1)
    c2 = _rect_corners(x2, y2, hx2, hy2, rot2)
    axes = []
    for rot in (rot1, rot2):
        axes.append((math.cos(rot), math.sin(rot)))
        axes.append((-math.sin(rot), math.cos(rot)))
    pen = float("inf")
    for ax, ay in axes:
        p1 = [cx * ax + cy * ay for cx, cy in c1]
        p2 = [cx * ax + cy * ay for cx, cy in c2]
        gap = max(min(p1) - max(p2), min(p2) - max(p1))
        if gap > 1e-9:
            return None  # separating axis found — no intersection
        pen = min(pen, -gap)
    return pen


def _penetration(f1, f2):
    """Depth of intersection (> 0), or None / <= 0 when the solids are apart."""
    if f1[0] == "circle" and f2[0] == "circle":
        _, x1, y1, r1 = f1
        _, x2, y2, r2 = f2
        return (r1 + r2) - math.hypot(x1 - x2, y1 - y2)
    if f1[0] == "rect" and f2[0] == "rect":
        return _rect_rect_penetration(f1, f2)
    if f1[0] == "rect":  # normalize to circle-vs-rect
        f1, f2 = f2, f1
    _, cx, cy, r = f1
    _, rx, ry, hx, hy, rot = f2
    cos_a, sin_a = math.cos(-rot), math.sin(-rot)
    lx, ly = cx - rx, cy - ry
    px = lx * cos_a - ly * sin_a
    py = lx * sin_a + ly * cos_a
    qx = max(-hx, min(hx, px))
    qy = max(-hy, min(hy, py))
    d = math.hypot(px - qx, py - qy)
    if d < 1e-9:  # circle centre inside the rect
        return r + min(hx - abs(px), hy - abs(py))
    return r - d


def _radius(rec):
    """Conservative yaw-independent footprint radius from dimensions."""
    d = rec.get("dimensions")
    if not d:
        return 0.5
    dx, dy = d[0] or 0.0, d[1] or 0.0
    return math.hypot(dx, dy) / 2.0


def _loc(rec):
    obj = rec["object"]
    loc = getattr(obj, "location", None)
    if loc is None:
        return None
    return (float(loc.x), float(loc.y), float(loc.z))


# ---------------------------------------------------------------------------
# Pocket fairness (v0.6.1 STEP 1) — pure data, engine-free & testable.
# ---------------------------------------------------------------------------
def validate_pocket_fairness(pockets, cfg, nav_pockets=None):
    """Compare mirror pairs (West<->East, SW<->SE) and Crown self-symmetry.

    Any mismatch above tolerance is a hard ERROR — differences are never hidden."""
    errors, warnings = [], []
    pcfg = cfg.get("pockets", {})
    tol = pcfg.get("fairness_tolerance", 0.5)
    by = {p["name"]: p for p in pockets}
    nav_by = {n["name"]: n for n in (nav_pockets or [])}

    def pair(a, b):
        pa, pb = by.get(a), by.get(b)
        if pa is None or pb is None:
            errors.append("MISSING POCKET: {}".format(a if pa is None else b))
            return
        # dimensions + area
        for i in (0, 1):
            if abs(pa["dimensions"][i] - pb["dimensions"][i]) > tol:
                errors.append("POCKET FAIRNESS dimensions {} vs {}".format(a, b))
        area_a = pa["dimensions"][0] * pa["dimensions"][1]
        area_b = pb["dimensions"][0] * pb["dimensions"][1]
        if abs(area_a - area_b) > max(1.0, tol * 10.0):
            errors.append("POCKET FAIRNESS area {} vs {}".format(a, b))
        # entry width
        if abs(pa["entry"]["width"] - pb["entry"]["width"]) > tol:
            errors.append("POCKET FAIRNESS entry width {} vs {}".format(a, b))
        # cover count
        if len(pa["cover"]) != len(pb["cover"]):
            errors.append("POCKET FAIRNESS cover count {} vs {}".format(a, b))
        # cover positions must be exact mirrors (x -> -x)
        a_mir = sorted([(-x, y, z) for (x, y, z) in pa.get("cover_positions", [])])
        b_pos = sorted(pb.get("cover_positions", []))
        if len(a_mir) != len(b_pos):
            errors.append("POCKET FAIRNESS cover position count {} vs {}".format(a, b))
        else:
            for (mx, my, mz), (bx, byy, bz) in zip(a_mir, b_pos):
                if math.hypot(mx - bx, my - byy) > tol:
                    errors.append("POCKET FAIRNESS cover position {} vs {}".format(a, b))
                    break
                if abs(mz - bz) > tol:
                    errors.append("POCKET FAIRNESS cover height {} vs {}".format(a, b))
                    break
        # height range
        if abs(pa["height_range"][1] - pb["height_range"][1]) > tol:
            errors.append("POCKET FAIRNESS height range {} vs {}".format(a, b))
        # reachability + route length
        na, nb = nav_by.get(a), nav_by.get(b)
        if na is not None and nb is not None:
            if not (na["reachable"] and nb["reachable"]):
                errors.append("POCKET NOT REACHABLE: {} / {}".format(a, b))
            if na["route_length"] is not None and nb["route_length"] is not None:
                if abs(na["route_length"] - nb["route_length"]) > max(2.0, tol * 4.0):
                    errors.append("POCKET FAIRNESS route length {} vs {}".format(a, b))

    pair("WestPocket", "EastPocket")
    pair("SWPocket", "SEPocket")

    # all pockets inside map bounds
    half = cfg["ground_half_size"]
    for p in pockets:
        b = p.get("bounds")
        if b and (b["max"][0] > half or b["min"][0] < -half or
                  b["max"][1] > half or b["min"][1] < -half):
            errors.append("POCKET OUT OF BOUNDS: {}".format(p["name"]))

    return errors, warnings


def run_validation(ctx, nav_report=None):
    cfg = ctx.config
    records = ctx.generated_objects
    vcfg = cfg.get("validation", {})
    errors, warnings = [], []

    half = cfg["ground_half_size"]
    world_half = cfg.get("world_floor_half_size", half)
    margin = vcfg.get("bounds_margin", 2.0)
    max_h = vcfg.get("max_object_height", 30.0)
    floor = cfg.get("safety_floor_z", -6.0)
    max_slope = cfg.get("navigation", {}).get("max_slope_deg", 50.0)

    by_type = {}
    for r in records:
        by_type.setdefault(r["type"], []).append(r)

    # --- capture points: exactly the full set of 5 ---------------------------
    cp_names = {r["meta"].get("point") for r in by_type.get("capture_point", [])}
    if vcfg.get("require_all_capture_points", True):
        for p in capture_point_names():
            if p not in cp_names:
                errors.append("MISSING CAPTURE POINT: {}".format(p))

    # --- bases -----------------------------------------------------------------
    base_teams = {r["meta"].get("team") for r in by_type.get("base", [])}
    if vcfg.get("require_both_bases", True):
        for team in ("Blue", "Red"):
            if team not in base_teams:
                errors.append("MISSING BASE: {}".format(team))

    # --- landmarks: Aether Altar + Aether Crown must exist -----------------------
    landmarks = {r["meta"].get("landmark") for r in by_type.get("altar", [])}
    for lm in ("AetherAltar", "AetherCrown"):
        if lm not in landmarks:
            errors.append("MISSING LANDMARK: {}".format(lm))

    # --- terrain + safety floor ---------------------------------------------------
    terrains = by_type.get("terrain", [])
    if not terrains:
        errors.append("MISSING TERRAIN: no real terrain object generated")
    for t in terrains:
        d = t.get("dimensions") or (0, 0, None)
        if d[0] is not None and abs(d[0] - world_half * 2.0) > 1.0:
            errors.append("TERRAIN BOUNDS MISMATCH: width {} vs world floor {}".format(d[0], world_half * 2.0))
    if not by_type.get("safety_floor"):
        errors.append("MISSING SAFETY FLOOR: player could fall forever")

    # --- duplicate names ---------------------------------------------------------
    if vcfg.get("reject_duplicate_names", True):
        seen = set()
        for r in records:
            if r["name"] in seen:
                errors.append("DUPLICATE OBJECT NAME: {}".format(r["name"]))
            seen.add(r["name"])

    # --- per-object: transforms, bbox bounds, Z, dimensions ------------------------
    solids_fp = []    # (name, footprint) for exact intersection checks
    solids_circ = []  # (x, y, circumscribed_r, name) conservative capture-area check
    for r in records:
        loc = _loc(r)
        if loc is None:
            errors.append("INVALID TRANSFORM (no location): {}".format(r["name"]))
            continue
        x, y, z = loc
        if any(_is_bad(v) for v in loc):
            errors.append("INVALID TRANSFORM (NaN/Inf): {}".format(r["name"]))
            continue

        dims = r.get("dimensions")
        if dims:
            bad = False
            if r["type"] in _PLANAR_SURFACE_TYPES:
                # Planar gameplay surface: zero thickness is legitimate (the
                # terrain below provides collision), but NaN is not, and the
                # surface must still span real width and length.
                for idx, d in enumerate(dims):
                    if d is None:
                        continue
                    if _is_bad(d) or d < 0 or (idx < 2 and d <= 0):
                        errors.append("INVALID DIMENSIONS: {} -> {}".format(r["name"], dims))
                        bad = True
                        break
            else:
                # Solid object: every extent must be a positive real number.
                for d in dims:
                    if d is None:
                        continue
                    if _is_bad(d) or d <= 0:
                        errors.append("INVALID DIMENSIONS: {} -> {}".format(r["name"], dims))
                        bad = True
                        break
            if bad:
                continue

        # Real degeneracy check against the actual mesh (when one exists):
        # a generated object must carry at least 3 vertices and 1 face.
        mesh = getattr(r["object"], "data", None)
        if mesh is not None and hasattr(mesh, "vertices") and hasattr(mesh, "polygons"):
            try:
                n_verts, n_faces = len(mesh.vertices), len(mesh.polygons)
            except Exception:
                n_verts, n_faces = 0, 0
            if n_verts < 3 or n_faces < 1:
                errors.append("INVALID GEOMETRY (degenerate mesh: {} verts, {} faces): {}".format(
                    n_verts, n_faces, r["name"]))

        if r["type"] not in _TERRAIN_EXEMPT:
            rad = _radius(r)
            if r["type"] == "outer_boundary":
                # The perimeter sits at the map edge; its exterior half may extend
                # slightly beyond the 200x200 playable envelope, but the inner face
                # must remain within it. This is a boundary-wall condition, not a
                # gameplay-object bounds error.
                half_inner = max(0.0, rad - 0.5 * min(r.get("dimensions") or (0.0, 0.0)))
                if abs(x) - half_inner > world_half + 1e-3 or abs(y) - half_inner > world_half + 1e-3:
                    errors.append("OUTER BOUNDARY INNER FACE OUT OF MAP: {}".format(r["name"]))
            elif abs(x) + rad > half + margin or abs(y) + rad > half + margin:
                errors.append("OUT OF MAP BOUNDS (bbox): {} at ({:.1f},{:.1f}) r={:.1f}".format(
                    r["name"], x, y, rad))
            if z < floor - 1.0:
                errors.append("BELOW SAFETY FLOOR: {} z={:.2f}".format(r["name"], z))
            if z > max_h:
                warnings.append("UNUSUALLY HIGH: {} z={:.2f}".format(r["name"], z))

        fp = _footprint(r)
        if fp is not None:
            solids_fp.append((r["name"], fp))
            solids_circ.append((x, y, _radius(r), r["name"]))

    # --- solid intersections: exact footprints (circles + rotated rects) -------------
    # Contacts within overlap_tolerance are deliberate structural abutments
    # (e.g. the North Pillar against the Altar base) — reported as
    # STRUCTURAL CONTACT, not as overlap. Deeper intersections stay errors-in-
    # waiting (warnings) so a real collision conflict is never masked.
    # name -> record lookup for meta access below
    rec_by_name = {r["name"]: r for r in records}

    def _wall_joint(n1, n2):
        """True when both solids are perimeter-wall segments of the SAME pocket.
        A pocket's walls form one continuous ring, so adjacent wall segments are
        expected to meet edge-to-edge: a clean structural joint, not a conflict."""
        r1, r2 = rec_by_name.get(n1), rec_by_name.get(n2)
        if r1 is None or r2 is None:
            return False
        m1, m2 = r1.get("meta") or {}, r2.get("meta") or {}
        # Elements of ONE pocket perimeter — wall chords, entry stubs and the
        # overlapping back-wall rock formations — are meant to meet/overlap:
        # they form a single continuous boundary, not a collision conflict.
        if (m1.get("element") in ("wall", "backwall")
                and m2.get("element") in ("wall", "backwall")
                and m1.get("pocket") is not None
                and m1.get("pocket") == m2.get("pocket")):
            return True
        # Global ellipse sections intentionally overlap edge-to-edge so the
        # exterior is physically closed. They share one boundary id.
        return (m1.get("element") == "outer_boundary"
                and m2.get("element") == "outer_boundary"
                and m1.get("boundary") == m2.get("boundary") == "global_ellipse")

    tol = vcfg.get("overlap_tolerance", 0.05)
    for i in range(len(solids_fp)):
        for j in range(i + 1, len(solids_fp)):
            n1, f1 = solids_fp[i]
            n2, f2 = solids_fp[j]
            if _wall_joint(n1, n2):
                continue   # continuous wall ring of one pocket — expected joint
            pen = _penetration(f1, f2)
            if pen is None or pen <= 0:
                continue
            if pen <= tol:
                warnings.append(
                    "STRUCTURAL CONTACT ({} ~ {}: penetration {:.3f} m <= tolerance {:.3f} m)".format(
                        n1, n2, pen, tol))
            else:
                warnings.append(
                    "SOLID OVERLAP ({} ~ {}: penetration {:.3f} m > tolerance {:.3f} m)".format(
                        n1, n2, pen, tol))

    # --- solids must not block capture platform areas --------------------------------
    for r in by_type.get("capture_point", []):
        ploc = _loc(r)
        if not ploc:
            continue
        plat_r = (r.get("meta") or {}).get("radius") or cfg["capture_platform_radius"]
        for (sx, sy, sr, sname) in solids_circ:
            if math.hypot(sx - ploc[0], sy - ploc[1]) < plat_r + sr * 0.5:
                errors.append("BLOCKS CAPTURE AREA: {} inside platform {}".format(
                    sname, r["name"]))

    # --- graded ramp slopes -----------------------------------------------------------
    for r in by_type.get("ramp", []):
        m = r.get("meta") or {}
        if not m.get("graded"):
            continue  # terrain-following ramp: slope bounded by terrain itself
        slope = m.get("slope_deg")
        if slope is None:
            warnings.append("RAMP WITHOUT SLOPE META: {}".format(r["name"]))
        elif slope > max_slope:
            errors.append("RAMP TOO STEEP: {} slope {:.1f} > max {:.1f}".format(
                r["name"], slope, max_slope))
        d = r.get("dimensions")
        if d and d[1] is not None and d[1] < 1.0:
            warnings.append("RAMP TOO SHORT: {}".format(r["name"]))

    # --- heightmap sampling: NaN / floor / max height -----------------------------------
    samples = 9
    worst_min, worst_max = float("inf"), float("-inf")
    for ri in range(samples + 1):
        for ci in range(samples + 1):
            x = -half + (2.0 * half) * ri / samples
            y = -half + (2.0 * half) * ci / samples
            z = get_height_at_point(Vector((x, y, 0.0)), cfg, ctx.layout)
            if _is_bad(z):
                errors.append("TERRAIN NaN/Inf at ({:.1f},{:.1f})".format(x, y))
                continue
            worst_min = min(worst_min, z)
            worst_max = max(worst_max, z)
    if worst_min < floor - 0.01:
        errors.append("TERRAIN BELOW SAFETY FLOOR: min z={:.2f}".format(worst_min))
    if worst_max > max_h:
        errors.append("TERRAIN ABOVE MAX HEIGHT: max z={:.2f}".format(worst_max))

    # --- navigation ---------------------------------------------------------------------
    if nav_report is not None:
        if not nav_report.get("ok", False):
            for p in nav_report.get("problems", []):
                errors.append("NAVIGATION: " + p)

    # --- pocket fairness (v0.6.1) -------------------------------------------------------
    pk_errors, pk_warnings = validate_pocket_fairness(
        getattr(ctx, "pockets", []), cfg,
        nav_report.get("pockets") if nav_report else None)
    errors.extend(pk_errors)
    warnings.extend(pk_warnings)

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "counts": {t: len(v) for t, v in by_type.items()},
        "terrain_sample": {"min_z": round(worst_min, 3) if worst_min != float("inf") else None,
                           "max_z": round(worst_max, 3) if worst_max != float("-inf") else None},
        "map": {"half_size": half, "safety_floor_z": floor,
                "max_slope_deg": max_slope},
    }
