import math
from mathutils import Vector

def get_height_at_point(pos, cfg, layout):
    p2d = Vector((pos.x, pos.y))
    dist_center = p2d.length

    core_r = cfg["center_radius"]
    if dist_center < core_r:
        t = dist_center / core_r
        return cfg["heights"]["AetherCore"] * ((1.0 - t) ** 2)

    transition_r = cfg["core_transition_radius"]
    if dist_center < core_r + transition_r:
        raw_t = (dist_center - core_r) / transition_r
        smooth_t = raw_t * raw_t * (3.0 - 2.0 * raw_t)

        angle = math.degrees(math.atan2(p2d.y, p2d.x)) % 360
        if 45 <= angle <= 135:
            target_h = cfg["heights"]["Crown"]
        elif 135 < angle < 225:
            target_h = cfg["heights"]["WestMonolith"]
        elif 225 <= angle <= 315:
            target_h = cfg["heights"]["SouthRift"]
        else:
            target_h = cfg["heights"]["EastMonolith"]

        return cfg["heights"]["AetherCore"] * (1.0 - smooth_t) + target_h * smooth_t

    south_mid = layout["SouthRift"]
    dist_south = (p2d - Vector((south_mid.x, south_mid.y))).length
    south_rift_r = cfg["south_rift_blend_radius"]
    if dist_south < south_rift_r:
        t = 1.0 - (dist_south / south_rift_r)
        return cfg["heights"]["SouthRift"] * (t ** 1.5)

    crown_pos = Vector((layout["Crown"].x, layout["Crown"].y))
    west_pos = Vector((layout["WestMonolith"].x, layout["WestMonolith"].y))
    east_pos = Vector((layout["EastMonolith"].x, layout["EastMonolith"].y))

    d_crown = max(0.001, (p2d - crown_pos).length)
    d_west = max(0.001, (p2d - west_pos).length)
    d_east = max(0.001, (p2d - east_pos).length)

    w_crown = max(0.0, 1.0 - d_crown / cfg["crown_influence_radius"])
    w_west = max(0.0, 1.0 - d_west / cfg["monolith_influence_radius"])
    w_east = max(0.0, 1.0 - d_east / cfg["monolith_influence_radius"])

    z = (w_crown * cfg["heights"]["Crown"] +
         w_west * cfg["heights"]["WestMonolith"] +
         w_east * cfg["heights"]["EastMonolith"])

    return min(1.5, z)
