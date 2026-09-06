"""
AetherFlow :: core/heightmap.py
Analytic height field for the map.

v0.6.3.2 fixes measured height-field discontinuities at both the AetherCore
shoulder and South Rift boundary. The fields now meet continuously, preserving
all XY anchors and gameplay topology while removing artificial one-cell steps
that were breaking minion traversal.

v0.6.4.4 adds deterministic, gameplay-safe unevenness to the existing terrain
without changing the authored macro landform or gameplay anchors.
"""
import math
from mathutils import Vector

from core.terrain_refinement import get_effective_heights, get_transition_radius


def _terrain_unevenness(pos, cfg, layout):
    """Add only a subtle, deterministic, gameplay-safe surface unevenness.

    This is an additive relief layer: the existing macro height field remains
    authoritative. Absolute X guarantees exact team-side symmetry.
    """
    amplitude = 0.18
    ax = abs(float(pos.x))
    y = float(pos.y)

    seed = float(cfg.get("seed", 1337))
    value = (
        math.sin(ax * 0.19 + y * 0.11 + seed * 0.001) * 0.60 +
        math.cos(ax * 0.07 - y * 0.17 - seed * 0.002) * 0.30 +
        math.sin(ax * 0.035 + y * 0.043 + seed * 0.003) * 0.10
    )

    # Keep authored gameplay anchors visually stable at their exact centers,
    # while allowing natural unevenness through the surrounding center area.
    anchors = (
        ("Crown", 10.0),
        ("EastMonolith", 9.0),
        ("SEMonolith", 9.0),
        ("SWMonolith", 9.0),
        ("WestMonolith", 9.0),
        ("BlueBase", 12.0),
        ("RedBase", 12.0),
    )
    suppression = 0.0
    for name, radius in anchors:
        anchor = layout[name]
        d = math.hypot(pos.x - anchor.x, pos.y - anchor.y)
        t = max(0.0, min(1.0, d / radius))
        smooth = t * t * (3.0 - 2.0 * t)
        suppression = max(suppression, 1.0 - smooth)

    return amplitude * value * (1.0 - suppression)


def get_height_at_point(pos, cfg, layout):
    p2d = Vector((pos.x, pos.y))
    dist_center = p2d.length

    heights = get_effective_heights(cfg)
    core_r = cfg["center_radius"]

    # Central AetherCore depression. Keep the original bowl geometry and add
    # only the subtle surface unevenness on top of it.
    if dist_center < core_r:
        t = dist_center / core_r
        z = heights["AetherCore"] * ((1.0 - t) ** 2)
        return _clamp(z + _terrain_unevenness(pos, cfg, layout), cfg)

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
        return _clamp(z + _terrain_unevenness(pos, cfg, layout), cfg)

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
        return _clamp(z + _terrain_unevenness(pos, cfg, layout), cfg)

    return _clamp(base_z + _terrain_unevenness(pos, cfg, layout), cfg)


def _clamp(z, cfg):
    """Safety floor: nothing is allowed below the configured floor."""
    floor = cfg.get("safety_floor_z", -6.0)
    return z if z > floor else floor
