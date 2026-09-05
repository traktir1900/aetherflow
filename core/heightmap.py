"""
AetherFlow :: core/heightmap.py
Analytic height field for the map.  Design is UNCHANGED from the original:

  - central AetherCore crater (parabolic, deepest at the centre)
  - smooth transition ring toward the sector heights
  - SouthRift depression
  - Crown / WestMonolith / EastMonolith raised influence domes

All radii/heights come from config (already scale-driven), and the result is
clamped to config["safety_floor_z"] so nothing can fall through the world.
"""
import math
from mathutils import Vector


def get_height_at_point(pos, cfg, layout):
    p2d = Vector((pos.x, pos.y))
    dist_center = p2d.length

    heights = cfg["heights"]
    core_r = cfg["center_radius"]

    # Central crater.
    if dist_center < core_r:
        t = dist_center / core_r
        z = heights["AetherCore"] * ((1.0 - t) ** 2)
        return _clamp(z, cfg)

    # Transition ring around the crater, blended toward the local sector.
    transition_r = cfg["core_transition_radius"]
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

        z = heights["AetherCore"] * (1.0 - smooth_t) + target_h * smooth_t
        return _clamp(z, cfg)

    # SouthRift depression.
    south_mid = layout["SouthRift"]
    dist_south = (p2d - Vector((south_mid.x, south_mid.y))).length
    rift_r = cfg["south_rift_blend_radius"]
    if dist_south < rift_r:
        t = 1.0 - (dist_south / rift_r)
        z = heights["SouthRift"] * (t ** 1.5)
        return _clamp(z, cfg)

    # Raised domes: Crown + both monoliths, distance-weighted.
    crown_pos = Vector((layout["Crown"].x, layout["Crown"].y))
    west_pos = Vector((layout["WestMonolith"].x, layout["WestMonolith"].y))
    east_pos = Vector((layout["EastMonolith"].x, layout["EastMonolith"].y))

    # Exact zero distance is allowed: at an anchor point the weight must be
    # exactly 1.0 so the anchor height is reproduced with no epsilon drift
    # (Crown must read exactly heights["Crown"]).
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
