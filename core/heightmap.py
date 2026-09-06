"""
AetherFlow :: core/heightmap.py
Analytic height field for the map.

v0.6.3.2 fixes measured height-field discontinuities at both the AetherCore
shoulder and South Rift boundary. The fields now meet continuously, preserving
all XY anchors and gameplay topology while removing artificial one-cell steps
that were breaking minion traversal.

v0.6.4.4 adds deterministic, low-amplitude gameplay relief. Relief is mirrored
across the Y axis and intentionally softened around objectives, bases, the
AetherCore and main transition corridors so elevation creates high-ground,
low-ground and flank choices without becoming an accidental blocker.
"""
import math
from mathutils import Vector

from core.terrain_refinement import get_effective_heights, get_transition_radius


def _smoothstep01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _gaussian2d(x, y, cx, cy, sx, sy):
    dx = (x - cx) / max(1e-6, sx)
    dy = (y - cy) / max(1e-6, sy)
    return math.exp(-0.5 * (dx * dx + dy * dy))


def _corridor_protection(pos, cfg, layout):
    """Return 0..1 relief suppression around critical gameplay anchors."""
    protected = [
        (layout["Center"], 13.0),
        (layout["Crown"], 11.0),
        (layout["WestMonolith"], 10.0),
        (layout["EastMonolith"], 10.0),
        (layout["SWMonolith"], 10.0),
        (layout["SEMonolith"], 10.0),
        (layout["BlueBase"], 12.0),
        (layout["RedBase"], 12.0),
    ]
    suppression = 0.0
    for anchor, radius in protected:
        d = math.hypot(pos.x - anchor.x, pos.y - anchor.y)
        suppression = max(suppression, 1.0 - _smoothstep01(d / radius))

    # Keep the ring approach band and the south return corridor comparatively
    # calm so the relief shapes decisions around them rather than replacing them.
    ring_r = float(cfg["outer_ring_radius"])
    ring_band = 7.0
    d_ring = abs(math.hypot(pos.x, pos.y) - ring_r)
    suppression = max(suppression, 0.70 * (1.0 - _smoothstep01(d_ring / ring_band)))

    south_rift = layout["SouthRift"]
    d_south = math.hypot(pos.x - south_rift.x, pos.y - south_rift.y)
    suppression = max(suppression, 0.55 * (1.0 - _smoothstep01(d_south / 12.0)))
    return max(0.0, min(1.0, suppression))


def _gameplay_relief(pos, cfg, layout):
    """Deterministic mirrored macro-relief for gameplay readability."""
    relief_cfg = cfg.get("gameplay_landscape", {})
    if not relief_cfg.get("enabled", True):
        return 0.0

    # Absolute X guarantees exact team-side symmetry by construction.
    ax = abs(float(pos.x))
    y = float(pos.y)

    value = 0.0

    # Side high-ground shelves: create readable flank routes and ranged
    # advantage positions without blocking the main ring road.
    value += float(relief_cfg.get("side_highland_height", 0.90)) * _gaussian2d(
        ax, y, 66.0, 24.0, 20.0, 18.0)
    value += float(relief_cfg.get("side_highland_height", 0.90)) * _gaussian2d(
        ax, y, 62.0, -20.0, 18.0, 20.0)

    # Matching low ground behind the shelves creates two-level flank choices.
    value -= float(relief_cfg.get("side_lowland_depth", 0.65)) * _gaussian2d(
        ax, y, 67.0, 2.0, 22.0, 15.0)

    # South shoulders frame the base approaches without touching the base pads.
    value += float(relief_cfg.get("south_shoulder_height", 0.55)) * _gaussian2d(
        ax, y, 38.0, -68.0, 24.0, 16.0)

    # North shoulders shape the Crown approach while the explicit Crown/ramp
    # protection above keeps the objective transition readable.
    value += float(relief_cfg.get("north_shoulder_height", 0.45)) * _gaussian2d(
        ax, y, 40.0, 68.0, 25.0, 16.0)

    # Very low-frequency undulation prevents the terrain from feeling planar.
    wave_amp = float(relief_cfg.get("broad_undulation", 0.18))
    wave = (
        math.sin(ax * 0.075 + 0.6) * 0.60 +
        math.cos(y * 0.060 - 0.4) * 0.40
    )
    value += wave_amp * wave

    # Keep the relief subordinate to the authoritative sector height field.
    suppression = _corridor_protection(pos, cfg, layout)
    return value * (1.0 - suppression)


def get_height_at_point(pos, cfg, layout):
    p2d = Vector((pos.x, pos.y))
    dist_center = p2d.length

    heights = get_effective_heights(cfg)
    core_r = cfg["center_radius"]

    # Central AetherCore depression. The bowl reaches zero at core_r so the
    # inner and outer fields share the same boundary elevation.
    if dist_center < core_r:
        t = dist_center / core_r
        z = heights["AetherCore"] * ((1.0 - t) ** 2)
        return _clamp(z, cfg)

    # Wider smooth shoulder into the surrounding sectors. IMPORTANT: the
    # outer field starts at the same z=0 boundary used by the core bowl.
    transition_r = get_transition_radius(cfg)
    if dist_center < core_r + transition_r:
        raw_t = (dist_center - core_r) / transition_r
        smooth_t = raw_t * raw_t * (3.0 - 2.0 * raw_t)

        angle = math.degrees(math.atan2(p2d.y, p2d.x)) % 360
        if 45 <= angle <= 135:
            target_h = heights["Crown"]
        elif 135 < angle < 225:
            target_h = heights["WestMonolith"]
        elif 225 <= angle <= 315:
            target_h = heights["SouthRift"]
        else:
            target_h = heights["EastMonolith"]

        z = target_h * smooth_t
        return _clamp(z + _gameplay_relief(pos, cfg, layout) * smooth_t, cfg)

    # Build the smooth raised-sector field first. South Rift is then applied
    # as a continuous depression on top of that field, so its outer edge is
    # guaranteed to meet the surrounding terrain instead of jumping to 0m.
    crown_pos = Vector((layout["Crown"].x, layout["Crown"].y))
    west_pos = Vector((layout["WestMonolith"].x, layout["WestMonolith"].y))
    east_pos = Vector((layout["EastMonolith"].x, layout["EastMonolith"].y))

    d_crown = max(0.0, (p2d - crown_pos).length)
    d_west = max(0.0, (p2d - west_pos).length)
    d_east = max(0.0, (p2d - east_pos).length)

    w_crown = max(0.0, 1.0 - d_crown / cfg["crown_influence_radius"])
    w_west = max(0.0, 1.0 - d_west / cfg["monolith_influence_radius"])
    w_east = max(0.0, 1.0 - d_east / cfg["monolith_influence_radius"])

    base_z = (w_crown * heights["Crown"] +
              w_west * heights["WestMonolith"] +
              w_east * heights["EastMonolith"])
    base_z = min(heights["Crown"], base_z)

    south_mid = layout["SouthRift"]
    dist_south = (p2d - Vector((south_mid.x, south_mid.y))).length
    rift_r = cfg["south_rift_blend_radius"]
    if dist_south < rift_r:
        t = 1.0 - (dist_south / rift_r)
        blend = t ** 1.5
        z = base_z * (1.0 - blend) + heights["SouthRift"] * blend
        return _clamp(z + _gameplay_relief(pos, cfg, layout), cfg)

    return _clamp(base_z + _gameplay_relief(pos, cfg, layout), cfg)


def _clamp(z, cfg):
    """Safety floor: nothing is allowed below the configured floor."""
    floor = cfg.get("safety_floor_z", -6.0)
    return z if z > floor else floor
