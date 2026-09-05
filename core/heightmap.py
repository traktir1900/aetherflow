"""
AetherFlow :: core/heightmap.py
Analytic height field for the map.

v0.6.3.2 fixes the measured discontinuity at the AetherCore shoulder: the
inner core bowl and the outer transition now meet continuously at
``core_radius``. This preserves all XY anchors and topology while removing
the artificial ~1.1 m one-cell height step that was breaking minion traversal.
"""
import math
from mathutils import Vector

from core.terrain_refinement import get_effective_heights, get_transition_radius


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

    # Wider smooth shoulder into the surrounding sectors.  IMPORTANT: the
    # outer field starts at the same z=0 boundary used by the core bowl;
    # starting from AetherCore here would introduce a discontinuous step.
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
        return _clamp(z, cfg)

    # SouthRift depression.
    south_mid = layout["SouthRift"]
    dist_south = (p2d - Vector((south_mid.x, south_mid.y))).length
    rift_r = cfg["south_rift_blend_radius"]
    if dist_south < rift_r:
        t = 1.0 - (dist_south / rift_r)
        z = heights["SouthRift"] * (t ** 1.5)
        return _clamp(z, cfg)

    # Raised sector influence around Crown and the east/west monoliths.
    crown_pos = Vector((layout["Crown"].x, layout["Crown"].y))
    west_pos = Vector((layout["WestMonolith"].x, layout["WestMonolith"].y))
    east_pos = Vector((layout["EastMonolith"].x, layout["EastMonolith"].y))

    d_crown = max(0.0, (p2d - crown_pos).length)
    d_west = max(0.0, (p2d - west_pos).length)
    d_east = max(0.0, (p2d - east_pos).length)

    w_crown = max(0.0, 1.0 - d_crown / cfg["crown_influence_radius"])
    w_west = max(0.0, 1.0 - d_west / cfg["monolith_influence_radius"])
    w_east = max(0.0, 1.0 - d_east / cfg["monolith_influence_radius"])

    z = (w_crown * heights["Crown"] +
         w_west * heights["WestMonolith"] +
         w_east * heights["EastMonolith"])

    z = min(heights["Crown"], z)
    return _clamp(z, cfg)


def _clamp(z, cfg):
    """Safety floor: nothing is allowed below the configured floor."""
    floor = cfg.get("safety_floor_z", -6.0)
    return z if z > floor else floor
