"""
AetherFlow :: core/layout.py
Canonical map layout.  The design is FIXED and must not drift:

  - 5 capture points on a pentagon: Crown, EastMonolith, SEMonolith,
    SWMonolith, WestMonolith.
  - Blue Base and Red Base on the south arc.
  - SouthRift midpoint between the two southern monoliths.
  - Center / AetherCore at the origin.

Only the SCALE changes (via config); angles and topology are constant.
"""
import math
from mathutils import Vector

# The authoritative list of capture points.  Anything that iterates points
# (simulation, heatmaps, validation, export) MUST use this, never a local
# subset — this is what guarantees 5/5 coverage.
RING_NODES = ["Crown", "EastMonolith", "SEMonolith", "SWMonolith", "WestMonolith"]
# Crown remains a logical navigation/objective anchor, but its physical space
# is the PvE Lord Sanctum rather than a normal capture platform.
PHYSICAL_CAPTURE_POINTS = ["EastMonolith", "SEMonolith", "SWMonolith", "WestMonolith"]

RING_ANGLES = {
    "Crown": 90.0,
    "EastMonolith": 18.0,
    "SEMonolith": 306.0,
    "SWMonolith": 234.0,
    "WestMonolith": 162.0,
}

BASES = ["BlueBase", "RedBase"]


def polar(radius, deg):
    rad = math.radians(deg)
    return Vector((radius * math.cos(rad), radius * math.sin(rad), 0.0))


def build_layout(cfg):
    layout = {"Center": Vector((0.0, 0.0, 0.0))}

    R = cfg["outer_ring_radius"]
    for name, ang in RING_ANGLES.items():
        layout[name] = polar(R, ang)

    B = cfg["base_radius"]
    spread = cfg["base_spread_deg"] / 2.0
    layout["BlueBase"] = polar(B, 270.0 - spread)
    layout["RedBase"] = polar(B, 270.0 + spread)

    layout["SouthRift"] = (layout["SWMonolith"] + layout["SEMonolith"]) / 2.0
    return layout


def capture_point_names():
    """Always the full set of 5 — single source for simulation/validation."""
    return list(RING_NODES)


def physical_capture_point_names():
    """Return the four objectives that own physical capture platforms."""
    return list(PHYSICAL_CAPTURE_POINTS)
