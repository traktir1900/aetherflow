"""
AetherFlow :: gameplay symmetry gate

HARD GAMEPLAY RULE:
    Team-critical gameplay geometry must be mirror-symmetric across the
    world Y axis: (x, y, z) -> (-x, y, z).
"""
import math

from mathutils import Vector
from core.heightmap import get_height_at_point

MIRROR_PAIRS = (
    ("BlueBase", "RedBase"),
    ("WestMonolith", "EastMonolith"),
    ("SWMonolith", "SEMonolith"),
)

CRITICAL_TYPES = {
    "base", "capture_point", "road", "ramp",
    "pocket_floor", "pocket_cover", "pocket_gate", "altar_obstacle",
}

OBJECTIVE_MIRRORS = {
    "WestMonolith": "EastMonolith",
    "EastMonolith": "WestMonolith",
    "SWMonolith": "SEMonolith",
    "SEMonolith": "SWMonolith",
    "Crown": "Crown",
}


def _near(a, b, tol):
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol


def _layout_symmetry(ctx, tol, errors):
    layout = ctx.layout
    for a, b in MIRROR_PAIRS:
        pa, pb = layout.get(a), layout.get(b)
        if pa is None or pb is None:
            errors.append("GAMEPLAY SYMMETRY MISSING LAYOUT PAIR: {} <-> {}".format(a, b))
            continue
        if abs(float(pa.x) + float(pb.x)) > tol or abs(float(pa.y) - float(pb.y)) > tol:
            errors.append("GAMEPLAY SYMMETRY LAYOUT: {} <-> {} is not a Y-axis mirror".format(a, b))

    crown = layout.get("Crown")
    if crown is not None and abs(float(crown.x)) > tol:
        errors.append("GAMEPLAY SYMMETRY CROWN must lie on Y axis: x={:.3f}".format(float(crown.x)))


def _terrain_symmetry(ctx, cfg, tol, errors):
    half = float(cfg.get("ground_half_size", 100.0))
    samples = 17
    for ix in range(samples):
        x = -half + (2.0 * half) * ix / (samples - 1)
        for iy in range(samples):
            y = -half + (2.0 * half) * iy / (samples - 1)
            za = float(get_height_at_point(Vector((x, y, 0.0)), cfg, ctx.layout))
            zb = float(get_height_at_point(Vector((-x, y, 0.0)), cfg, ctx.layout))
            if abs(za - zb) > tol:
                errors.append("GAMEPLAY SYMMETRY TERRAIN: ({:.2f},{:.2f}) {:.3f}m vs mirror {:.3f}m".format(x, y, za, zb))
                return


def _record_signature(rec):
    obj = rec.get("object")
    loc = getattr(obj, "location", None) if obj is not None else None
    if loc is None:
        return None
    dims = rec.get("dimensions") or ()
    return (
        round(float(loc.x), 3), round(float(loc.y), 3), round(float(loc.z), 3),
        tuple(round(float(d), 3) for d in dims if d is not None),
    )


def _find_mirror(records, target, tol):
    best_idx = None
    best_score = float("inf")
    tx, ty, tz, tdims = target
    for idx, rec in enumerate(records):
        sig = _record_signature(rec)
        if sig is None:
            continue
        x, y, z, dims = sig
        if len(dims) != len(tdims):
            continue
        if not _near((x, y), (tx, ty), tol) or abs(z - tz) > tol:
            continue
        if any(abs(a - b) > tol for a, b in zip(dims, tdims)):
            continue
        score = math.hypot(x - tx, y - ty) + abs(z - tz)
        if score < best_score:
            best_score = score
            best_idx = idx
    return best_idx


def _objective_cover_symmetry(ctx, tol, errors):
    """Validate ObjectiveCover_* by logical objective pair, not global type multiset.

    The cover meshes are generated in each objective's local basis. Their
    rotation is baked into the mesh, so comparing meta rot_z across objectives
    is incorrect. Gameplay symmetry is therefore checked on the authoritative
    world-space transform and footprint dimensions. Crown is self-mirrored.
    """
    covers = [
        r for r in getattr(ctx, "generated_objects", [])
        if r.get("type") == "cover"
        and ((r.get("meta") or {}).get("gameplay_cover") or (r.get("meta") or {}).get("objective"))
    ]
    by_objective = {}
    for rec in covers:
        objective = (rec.get("meta") or {}).get("objective")
        if objective:
            by_objective.setdefault(str(objective), []).append(rec)

    checked = set()
    for a, b in OBJECTIVE_MIRRORS.items():
        pair_key = tuple(sorted((a, b)))
        if pair_key in checked:
            continue
        checked.add(pair_key)
        left = list(by_objective.get(a, []))
        right = list(by_objective.get(b, []))

        # For Crown, the two cover pieces must mirror each other as a set.
        if a == b:
            remaining = list(right)
            for rec in left:
                sig = _record_signature(rec)
                if sig is None:
                    errors.append("GAMEPLAY SYMMETRY OBJECT INVALID: {}".format(rec.get("name", "")))
                    continue
                x, y, z, dims = sig
                target = (-x, y, z, dims)
                idx = _find_mirror(remaining, target, tol)
                if idx is None:
                    errors.append("GAMEPLAY SYMMETRY OBJECT MISSING MIRROR: {}".format(rec.get("name", "")))
                else:
                    remaining.pop(idx)
            continue

        if not left or not right:
            errors.append("GAMEPLAY SYMMETRY OBJECTIVE COVER SET MISSING: {} <-> {}".format(a, b))
            continue
        if len(left) != len(right):
            errors.append("GAMEPLAY SYMMETRY OBJECTIVE COVER COUNT: {}={} vs {}={}".format(a, len(left), b, len(right)))
            continue

        remaining = list(right)
        for rec in left:
            sig = _record_signature(rec)
            if sig is None:
                errors.append("GAMEPLAY SYMMETRY OBJECT INVALID: {}".format(rec.get("name", "")))
                continue
            x, y, z, dims = sig
            idx = _find_mirror(remaining, (-x, y, z, dims), tol)
            if idx is None:
                errors.append("GAMEPLAY SYMMETRY OBJECT MISSING MIRROR: {}".format(rec.get("name", "")))
            else:
                remaining.pop(idx)


def _critical_records_symmetry(ctx, tol, errors):
    records = [r for r in getattr(ctx, "generated_objects", []) if r.get("type") in CRITICAL_TYPES]
    unmatched = list(records)

    while unmatched:
        rec = unmatched.pop(0)
        sig = _record_signature(rec)
        if sig is None:
            errors.append("GAMEPLAY SYMMETRY INVALID OBJECT: {}".format(rec.get("name", "")))
            continue
        x, y, z, dims = sig
        target = (-x, y, z, dims)
        found_index = _find_mirror(unmatched, target, tol)
        if found_index is None:
            # Objects on the mirror plane can legally mirror themselves.
            if abs(x) <= tol:
                continue
            errors.append("GAMEPLAY SYMMETRY OBJECT MISSING MIRROR: {}".format(rec.get("name", "")))
            continue
        unmatched.pop(found_index)


def _core_rock_symmetry(ctx, tol, errors):
    """Hard-check central Core_Rock_* pairs created by the rock generator."""
    core = [r for r in getattr(ctx, "generated_objects", []) if r.get("name", "").startswith("Core_Rock_")]
    if not core:
        return
    by_pair = {}
    for rec in core:
        pair_id = (rec.get("meta") or {}).get("symmetry_pair")
        if not pair_id:
            errors.append("GAMEPLAY SYMMETRY CORE ROCK MISSING PAIR ID: {}".format(rec.get("name", "")))
            continue
        by_pair.setdefault(pair_id, []).append(rec)

    for pair_id, pair in sorted(by_pair.items()):
        if len(pair) != 2:
            errors.append("GAMEPLAY SYMMETRY CORE ROCK PAIR {} has {} objects, expected 2".format(pair_id, len(pair)))
            continue
        a, b = pair
        sa = _record_signature(a)
        sb = _record_signature(b)
        if sa is None or sb is None:
            errors.append("GAMEPLAY SYMMETRY CORE ROCK PAIR {} has invalid transform".format(pair_id))
            continue
        if not _near(sa[:2], (-sb[0], sb[1]), tol) or abs(sa[2] - sb[2]) > tol:
            errors.append("GAMEPLAY SYMMETRY CORE ROCK PAIR {} position mismatch".format(pair_id))
        if sa[3] != sb[3]:
            errors.append("GAMEPLAY SYMMETRY CORE ROCK PAIR {} dimension mismatch".format(pair_id))


def validate_gameplay_symmetry(ctx, cfg=None):
    """Return (errors, summary) for the hard team-balance symmetry gate."""
    cfg = cfg or ctx.config
    scfg = cfg.get("gameplay_symmetry", {})
    if not scfg.get("enabled", True):
        return [], {"enabled": False, "passed": True, "rule": "disabled"}

    tol = float(scfg.get("tolerance_m", 0.25))
    errors = []
    _layout_symmetry(ctx, tol, errors)
    _terrain_symmetry(ctx, cfg, tol, errors)
    _critical_records_symmetry(ctx, tol, errors)
    _objective_cover_symmetry(ctx, tol, errors)
    _core_rock_symmetry(ctx, tol, errors)

    return errors, {
        "enabled": True,
        "passed": not errors,
        "plane": "Y_AXIS",
        "transform": "(x,y,z) -> (-x,y,z)",
        "tolerance_m": tol,
        "checked_types": sorted(CRITICAL_TYPES) + ["cover:ObjectiveCover_*", "Core_Rock_*"],
        "mirror_pairs": [list(p) for p in MIRROR_PAIRS],
    }
