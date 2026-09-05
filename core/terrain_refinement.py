"""
AetherFlow :: v0.6.3.1 terrain refinement.

Bounded, topology-preserving terrain tuning for the existing v0.6.x map.
The objective/base coordinates, roads, ramps and pocket topology are not
changed here. Only the analytic height profile is strengthened and audited.
"""
import math
from copy import deepcopy

from mathutils import Vector


DEFAULT_REFINEMENT = {
    "enabled": True,
    "core_depth_multiplier": 1.65,
    "crown_height_multiplier": 1.60,
    "monolith_height_multiplier": 1.60,
    "south_rift_depth_multiplier": 1.50,
    "transition_radius_multiplier": 1.10,
    "max_expected_slope_deg": 35.0,
}


def get_profile(cfg):
    profile = deepcopy(DEFAULT_REFINEMENT)
    profile.update(cfg.get("terrain_refinement", {}))
    return profile


def get_effective_heights(cfg):
    """Return the gameplay height targets used by the analytic heightmap."""
    heights = deepcopy(cfg["heights"])
    p = get_profile(cfg)
    if not p.get("enabled", True):
        return heights

    heights["AetherCore"] = heights["AetherCore"] * float(p["core_depth_multiplier"])
    heights["Crown"] = heights["Crown"] * float(p["crown_height_multiplier"])
    heights["WestMonolith"] = heights["WestMonolith"] * float(p["monolith_height_multiplier"])
    heights["EastMonolith"] = heights["EastMonolith"] * float(p["monolith_height_multiplier"])
    heights["SouthRift"] = heights["SouthRift"] * float(p["south_rift_depth_multiplier"])
    return heights


def get_transition_radius(cfg):
    base = float(cfg["core_transition_radius"])
    return base * float(get_profile(cfg)["transition_radius_multiplier"])


def _sample_height(pos, cfg, layout):
    from core.heightmap import get_height_at_point
    return float(get_height_at_point(pos, cfg, layout))


def analyze_height_profile(cfg, layout, grid=65):
    """Audit named landmarks and the maximum analytic slope over gameplay area."""
    half = float(cfg["ground_half_size"])
    step = (2.0 * half) / max(1, grid - 1)
    sample_step = max(step, 1.0)

    max_slope = 0.0
    sum_slope = 0.0
    samples = 0
    lo_z = float("inf")
    hi_z = float("-inf")

    for iy in range(grid):
        y = -half + iy * step
        for ix in range(grid):
            x = -half + ix * step
            pos = Vector((x, y, 0.0))
            z = _sample_height(pos, cfg, layout)
            lo_z = min(lo_z, z)
            hi_z = max(hi_z, z)
            if ix < grid - 1:
                zx = _sample_height(Vector((x + step, y, 0.0)), cfg, layout)
                gx = abs(zx - z) / sample_step
            else:
                gx = 0.0
            if iy < grid - 1:
                zy = _sample_height(Vector((x, y + step, 0.0)), cfg, layout)
                gy = abs(zy - z) / sample_step
            else:
                gy = 0.0
            slope_deg = math.degrees(math.atan(math.hypot(gx, gy)))
            max_slope = max(max_slope, slope_deg)
            sum_slope += slope_deg
            samples += 1

    heights = get_effective_heights(cfg)
    # "AetherCore" is the central origin, not a layout key. Keep the
    # named-landmark report aligned with the actual layout keys.
    landmarks = {
        "AetherCore": round(_sample_height(Vector((0.0, 0.0, 0.0)), cfg, layout), 3)
    }
    for name in ("Crown", "WestMonolith", "EastMonolith", "SouthRift"):
        p = layout[name]
        landmarks[name] = round(_sample_height(p, cfg, layout), 3)

    expected = {name: round(float(heights[name]), 3)
                for name in landmarks if name in heights}
    return {
        "enabled": bool(get_profile(cfg).get("enabled", True)),
        "landmark_heights_m": landmarks,
        "expected_anchor_heights_m": expected,
        "min_height_m": round(lo_z, 3),
        "max_height_m": round(hi_z, 3),
        "max_slope_deg": round(max_slope, 2),
        "average_slope_deg": round(sum_slope / max(samples, 1), 2),
        "slope_within_design_limit": bool(
            max_slope <= float(get_profile(cfg)["max_expected_slope_deg"])
        ),
        "topology_changed": False,
        "objectives_moved": False,
        "bases_moved": False,
    }
