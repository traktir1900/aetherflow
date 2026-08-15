import math
from mathutils import Vector

RING_NODES = ["Crown", "EastMonolith", "SEMonolith", "SWMonolith", "WestMonolith"]
RING_ANGLES = {"Crown": 90.0, "EastMonolith": 18.0, "SEMonolith": 306.0, "SWMonolith": 234.0, "WestMonolith": 162.0}

def polar(radius, deg):
    rad = math.radians(deg)
    return Vector((radius * math.cos(rad), radius * math.sin(rad), 0.0))

def build_layout(cfg):
    R = cfg["outer_ring_radius"]
    layout = {"Center": Vector((0.0, 0.0, 0.0))}
    for name, ang in RING_ANGLES.items():
        layout[name] = polar(R, ang)

    B = cfg["base_radius"]
    spread = cfg["base_spread_deg"] / 2.0
    layout["BlueBase"] = polar(B, 270.0 - spread)
    layout["RedBase"] = polar(B, 270.0 + spread)
    layout["SouthRift"] = (layout["SWMonolith"] + layout["SEMonolith"]) / 2.0
    return layout
