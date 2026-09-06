"""AetherFlow map export."""
import json
import os

from core.layout import BASES, capture_point_names
from core.version import get_version


def _vec3(v):
    return [round(float(v.x), 3), round(float(v.y), 3), round(float(v.z), 3)]


def build_map_data(ctx, sim=None, nav=None, validation=None):
    cfg = ctx.config
    layout = ctx.layout
    half = cfg["ground_half_size"]
    world_half = cfg["world_floor_half_size"]

    terrain = {
        "ground_half_size": half,
        "world_floor_half_size": world_half,
        "anchors": {},
    }
    for key in ("Center", "Crown", "WestMonolith", "EastMonolith", "SWMonolith", "SEMonolith", "BlueBase", "RedBase", "SouthRift"):
        if key in layout:
            terrain["anchors"][key] = _vec3(layout[key])

    capture_points = [{
        "name": p,
        "position": _vec3(layout[p]),
        "radius": cfg["capture_platform_radius"],
        "height": cfg["capture_platform_height"],
        "button": "CaptureButton_{}".format(p),
        "indicator": "CaptureIndicatorRing_{}".format(p),
    } for p in capture_point_names()]

    bases = []
    base_width = cfg.get("base_platform_width_radius", cfg.get("base_platform_radius", 0.0) / 2.0) * 2.0
    base_depth = cfg.get("base_platform_depth", cfg.get("base_platform_radius", 0.0))
    for b in BASES:
        shape = "semi_oval" if "base_platform_width_radius" in cfg else "circle"
        entry = {
            "name": b,
            "position": _vec3(layout[b]),
            "shape": shape,
            "height": cfg["base_platform_height"],
            "width": base_width,
            "depth": base_depth,
        }
        # Backward-compatible radius field for consumers still expecting it.
        entry["radius"] = cfg.get("base_platform_radius", base_width / 2.0)
        bases.append(entry)

    data = {
        "version": get_version(),
        "generator": "AetherFlow procedural pipeline",
        "seed": cfg.get("seed"),
        "map": {
            "width": round(half * 2.0, 2),
            "height": round(half * 2.0, 2),
            "ground_half_size": round(half, 2),
            "world_floor_half_size": round(world_half, 2),
        },
        "terrain": terrain,
        "capture_points": capture_points,
        "bases": bases,
        "simulation": sim,
        "navigation": nav,
        "validation": validation,
    }
    return data


def write_map_data(ctx, path, sim=None, nav=None, validation=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = build_map_data(ctx, sim=sim, nav=nav, validation=validation)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path
