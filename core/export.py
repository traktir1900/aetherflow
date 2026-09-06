"""
AetherFlow :: core/export.py
map_data.json — the OFFICIAL data contract between Blender and the future
UE5 pipeline (v0.7.0).  It serializes the real generated map: map, terrain,
capture_points, bases, roads, ramps, cover, rocks, landmarks, props — with
name / type / location / rotation / scale / dimensions for every object.

Deterministic output (sorted keys, stable ordering) so identical config+seed
always produces an identical file.  This is what v0.7.0 will consume.
"""
import json
import os

from core.version import get_version
from core.layout import capture_point_names, BASES

_TYPE_BUCKETS = {
    "capture_point": "capture_points",
    "capture_button": "capture_buttons",
    "capture_indicator": "capture_indicators",
    "base": "bases",
    "road": "roads",
    "ramp": "ramps",
    "cover": "cover",
    "rock": "rocks",
    "altar": "landmarks",
    "altar_obstacle": "props",
    "landmark": "landmarks",
    "turret": "props",
    "safety_floor": "props",
    "outer_boundary": "props",
}


def _vec3(v):
    return [round(float(v.x), 4), round(float(v.y), 4), round(float(v.z), 4)]


def _object_entry(rec):
    obj = rec["object"]
    loc = getattr(obj, "location", None)
    rot = getattr(obj, "rotation_euler", None)
    scl = getattr(obj, "scale", None)
    dims = rec.get("dimensions")
    return {
        "name": rec["name"],
        "type": rec["type"],
        "location": _vec3(loc) if loc is not None else None,
        "rotation": [round(float(a), 4) for a in rot] if rot is not None else None,
        "scale": [round(float(s), 4) for s in scl] if scl is not None else None,
        "dimensions": [round(float(d), 4) if d is not None else None for d in dims] if dims else None,
        "meta": rec.get("meta", {}),
    }


def build_map_data(ctx, sim=None, nav=None, validation=None):
    cfg = ctx.config
    layout = ctx.layout
    half = cfg["ground_half_size"]
    world_half = cfg.get("world_floor_half_size", half)

    buckets = {b: [] for b in set(_TYPE_BUCKETS.values())}
    for rec in ctx.generated_objects:
        bucket = _TYPE_BUCKETS.get(rec["type"], "props")
        buckets[bucket].append(_object_entry(rec))
    for b in buckets:
        buckets[b].sort(key=lambda e: e["name"])

    terrain = {}
    for rec in ctx.generated_objects:
        if rec["type"] == "terrain":
            terrain = {
                "width": round(world_half * 2.0, 2),
                "height": round(world_half * 2.0, 2),
                "resolution": rec.get("meta", {}).get("resolution"),
                "parameters": {
                    "heights": cfg["heights"],
                    "center_radius": cfg["center_radius"],
                    "core_transition_radius": cfg["core_transition_radius"],
                    "south_rift_blend_radius": cfg["south_rift_blend_radius"],
                    "crown_influence_radius": cfg["crown_influence_radius"],
                    "monolith_influence_radius": cfg["monolith_influence_radius"],
                    "safety_floor_z": cfg.get("safety_floor_z"),
                },
            }
            break

    capture_points = [{
        "name": p,
        "position": _vec3(layout[p]),
        "radius": cfg["capture_platform_radius"],
        "height": cfg["capture_platform_height"],
        "button": "CaptureButton_{}".format(p),
        "indicator": "CaptureIndicatorRing_{}".format(p),
    } for p in capture_point_names()]

    bases = [{
        "name": b,
        "position": _vec3(layout[b]),
        "radius": cfg["base_platform_radius"],
    } for b in BASES]

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
        "capture_buttons": buckets["capture_buttons"],
        "capture_indicators": buckets["capture_indicators"],
        "bases": bases,
        "pockets": getattr(ctx, "pockets", []),
        "roads": buckets["roads"],
        "ramps": buckets["ramps"],
        "cover": buckets["cover"],
        "rocks": buckets["rocks"],
        "landmarks": buckets["landmarks"],
        "props": buckets["props"],
        "simulation": sim,
        "navigation": nav,
        "outer_boundary": getattr(ctx, "outer_boundary", None),
        "validation": {k: validation[k] for k in ("ok", "errors", "warnings")} if validation else None,
    }
    return data


def write_map_data(ctx, path, sim=None, nav=None, validation=None):
    data = build_map_data(ctx, sim=sim, nav=nav, validation=validation)
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=False)
    print("[EXPORT] map_data.json written -> {}".format(path))
    return path
