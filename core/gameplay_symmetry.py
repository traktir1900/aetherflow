"""
AetherFlow :: gameplay symmetry gate

HARD GAMEPLAY RULE:
    Team-critical gameplay geometry must be mirror-symmetric across the
    world Y axis: (x, y, z) -> (-x, y, z).

This is a balance invariant, not a visual suggestion. A generation is not
validation-clean when the two team sides differ beyond the configured
geometric tolerance.

Decorative-only assets may remain asymmetric, but all gameplay-critical
geometry/data checked here must remain mirror-equivalent.
"""
import math

from core.heightmap import get_height_at_point
from core.layout import RING_NODES


MIRROR_PAIRS = (
    ("BlueBase", "RedBase"),
    ("WestMonolith", "EastMonolith"),
    ("SWMonolith", "SEMonolith"),
)

# Object record types that materially affect gameplay balance.
CRITICAL_TYPES = {
    "base",
    "capture_point",
    "road",
    "ramp",
    "cover",
    "pocket_floor",
    "pocket_cover",
    "pocket_gate",
    "altar_obstacle",
}


def _xy(p):
    return float(p[0]), float(p[1])


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
            errors.append(
                "GAMEPLAY SYMMETRY LAYOUT: {} <-> {} expected ({:.3f},{:.3f}) mirror, got ({:.3f},{:.3f})".format(
                    a, b, float(pa.x), float(pa.y), float(-pa.x), float(pa.y), float(pb.x), float(pb.y)))

    crown = layout.get("Crown")
    if crown is not None and abs(float(crown.x)) > tol:
        errors.append("GAMEPLAY SYMMETRY CROWN must lie on Y axis: x={:.3f}".format(float(crown.x)))


def _terrain_symmetry(ctx, cfg, tol, errors):
    """Sample the analytic terrain on mirrored points inside the gameplay map."""
    half = float(cfg.get("ground_half_size", 100.0))
    # Deterministic interior grid; edge samples are included at a safe margin.
    samples = 17
    for ix in range(samples):
        x = -half + (2.0 * half) * ix / (samples - 1)
        for iy in range(samples):
            y = -half + (2.0 * half) * iy / (samples - 1)
            za = float(get_height_at_point(__import__("mathutils").Vector((x, y, 0.0)), cfg, ctx.layout))
            zb = float(get_height_at_point(__import__("mathutils").Vector((-x, y, 0.0)), cfg, ctx.layout))
            if abs(za - zb) > tol:
                errors.append(
                    "GAMEPLAY SYMMETRY TERRAIN: ({:.2f},{:.2f}) z={:.3f} vs mirror z={:.3f}".format(
                        x, y, za, zb))
                return


def _record_signature(rec, tol):
    obj = rec.get("object")
    loc = getattr(obj, "location", None) if obj is not None else None
    if loc is None:
        return None
    dims = rec.get("dimensions") or ()
    dims_sig = tuple(round(float(d), 3) for d in dims if d is not None)
    meta = rec.get("meta") or {}
    rot = float(meta.get("rot_z", 0.0))
    return (
        round(abs(float(loc.x)), 3),
        round(float(loc.y), 3),
        round(float(loc.z), 3),
        dims_sig,
        round(math.sin(rot), 3),
        round(math.cos(rot), 3),
    )


def _critical_records_symmetry(ctx, cfg, tol, errors):
    """Compare the world-space signatures of team-critical generated records."""
    records = [r for r in getattr(ctx, "generated_objects", []) if r.get("type") in CRITICAL_TYPES]

    def mirror_sig(rec):
        obj = rec.get("object")
        if obj is None:
            return None
        dims = rec.get("dimensions") or ()
        dims_sig = tuple(round(float(d), 3) for d in dims if d is not None)
        meta = rec.get("meta") or {}
        rot = float(meta.get("rot_z", 0.0))
        # Mirror across Y: x sign flips and yaw changes sign. For cardinal
        # Altar barricades this remains equivalent because 0/90-degree pairs
        # are explicitly constructed on both sides.
        return (
            round(-float(obj.location.x), 3),
            round(float(obj.location.y), 3),
            round(float(obj.location.z), 3),
            dims_sig,
            round(-math.sin(rot), 3),
            round(math.cos(rot), 3),
        )

    pool = [
        {
            "sig": _record_signature(r, tol),
            "mirror": mirror_sig(r),
            "name": r.get("name", ""),
        }
        for r in records
    ]

    # Compare multisets of critical geometry signatures. Self-mirrored objects
    # on the Y axis (x ~= 0) are allowed to satisfy their own mirror partner.
    remaining = list(range(len(pool)))
    for i, entry in enumerate(pool):
        if i not in remaining:
            continue
        target = entry["mirror"]
        found = None
        for j in remaining:
            if j == i:
                sig = pool[j]["sig"]
                if sig == target:
                    found = j
                    break
                continue
            cand = pool[j]["sig"]
            if cand is None or target is None:
                continue
            if cand == target:
                found = j
                break
        if found is None:
            errors.append("GAMEPLAY SYMMETRY OBJECT MISSING MIRROR: {}".format(entry["name"]))
            remaining.remove(i)
        else:
            remaining.remove(i)
            if found in remaining:
                remaining.remove(found)


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
    _critical_records_symmetry(ctx, cfg, tol, errors)

    return errors, {
        "enabled": True,
        "passed": not errors,
        "plane": "Y_AXIS",
        "transform": "(x,y,z) -> (-x,y,z)",
        "tolerance_m": tol,
        "checked_types": sorted(CRITICAL_TYPES),
        "mirror_pairs": [list(p) for p in MIRROR_PAIRS],
    }
