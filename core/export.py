"""AetherFlow map export."""
import json
import math
import os

import bmesh
from mathutils import Matrix, Vector

from core.layout import BASES, capture_point_names
from core.version import get_version
from core.utils import finalize_bmesh


def _vec3(v):
    return [round(float(v.x), 3), round(float(v.y), 3), round(float(v.z), 3)]


def _plain(value):
    """Convert Blender/math values into JSON-safe plain Python values."""
    if isinstance(value, Vector):
        return _vec3(value)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _record_export(rec):
    """Serialize one ctx.generated_objects record without losing live identity."""
    obj = rec.get("object")
    dims = rec.get("dimensions")
    if dims is None and obj is not None:
        dims = tuple(float(v) for v in obj.dimensions)
    location = _vec3(obj.location) if obj is not None else [0.0, 0.0, 0.0]
    return {
        "name": str(rec.get("name", getattr(obj, "name", "Object"))),
        "type": str(rec.get("type", "unknown")),
        "location": location,
        "dimensions": _plain(list(dims)) if dims is not None else None,
        "meta": _plain(rec.get("meta") or {}),
    }


def _build_generated_buckets(ctx):
    """Export the complete generated-object registry into stable audit buckets.

    The registry is the authoritative per-run source for geometry that used to
    exist only in Blender memory.  Buckets are intentionally redundant: each
    object is kept in `objects`, while gameplay consumers also get focused
    `cover`, `rocks`, `roads`, `ramps`, `floors`, and `props` lists.
    """
    objects = [_record_export(rec) for rec in ctx.generated_objects]
    buckets = {
        "objects": objects,
        "cover": [],
        "rocks": [],
        "roads": [],
        "ramps": [],
        "floors": [],
        "props": [],
        "terrain_objects": [],
        "landmarks": [],
    }

    for item in objects:
        kind = item["type"]
        meta = item.get("meta") or {}
        name = item["name"]
        element = str(meta.get("element", "")).lower()

        if kind == "cover":
            buckets["cover"].append(item)
        elif kind == "altar_obstacle":
            # Keep altar blockers visible to both legacy and v0.6 auditors.
            buckets["cover"].append(item)
            buckets["rocks"].append(item)
        elif kind == "rock":
            buckets["rocks"].append(item)
        elif kind == "road":
            buckets["roads"].append(item)
        elif kind == "ramp":
            buckets["ramps"].append(item)
        elif kind == "floor":
            buckets["floors"].append(item)
        elif kind in ("terrain", "safety_floor"):
            buckets["terrain_objects"].append(item)
        elif kind in ("altar", "landmark"):
            buckets["landmarks"].append(item)
        else:
            buckets["props"].append(item)

        # Some legacy tooling classifies by element rather than type.
        if element == "interior_cover" and item not in buckets["cover"]:
            buckets["cover"].append(item)
        if element == "cover" and item not in buckets["cover"]:
            buckets["cover"].append(item)

    return buckets


def _build_base_shops(ctx):
    """Create temporary rectangular shop shells immediately outside each base's flat D-edge.

    The shop width spans the complete straight edge of the semi-oval base. Its
    local Y axis points outward, so the block sits beside the straight edge
    instead of extending back across the rounded/base area.
    """
    cfg = ctx.config
    width = float(cfg.get("base_shop_width", cfg.get("base_platform_width_radius", 0.0) * 2.0))
    depth = float(cfg.get("base_shop_depth", 0.0))
    height = float(cfg.get("base_shop_height", 0.0))
    gap = float(cfg.get("base_shop_gap", 0.0))
    built = []

    if width <= 0.0 or depth <= 0.0 or height <= 0.0:
        return built

    for team, base_key, material_name in [("Blue", "BlueBase", "blue_team"), ("Red", "RedBase", "red_team")]:
        base_pos = ctx.layout[base_key].copy()
        base_pos.z = float(base_pos.z)

        toward_center = Vector((-base_pos.x, -base_pos.y, 0.0))
        if toward_center.length < 1e-6:
            toward_center = Vector((0.0, 1.0, 0.0))
        toward_center.normalize()
        outward = -toward_center

        # Local X spans the flat D-edge; local Y points outward from the base.
        rot_z = math.atan2(outward.y, outward.x) - math.pi / 2.0
        center = base_pos + outward * (gap + depth * 0.5)

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((width, depth, height)), verts=bm.verts)
        bmesh.ops.rotate(
            bm,
            cent=Vector((0.0, 0.0, 0.0)),
            matrix=Matrix.Rotation(rot_z, 4, 'Z'),
            verts=bm.verts,
        )
        bmesh.ops.translate(
            bm,
            verts=bm.verts,
            vec=center + Vector((0.0, 0.0, height * 0.5)),
        )

        obj = finalize_bmesh(
            bm,
            "{}_Shop".format(team),
            "Bases",
            ctx.get_material(material_name),
            ctx,
            kind="shop",
            dims=(width, depth, height),
            meta={
                "team": team,
                "shape": "rectangle",
                "stage": "blockout",
                "purpose": "base_shop",
                "rear_of_base": True,
                "spans_full_base_flat_edge": True,
                "adjacent_to_flat_edge": True,
                "orientation": "outward_from_base",
                "navigation_blocker": False,
                "los_blocker": False,
            },
        )
        built.append(obj)

    print("  -> Base shops: {} temporary rectangles | adjacent to straight D-edge | full-width | non-blocking".format(len(built)))
    return built


def build_map_data(ctx, sim=None, nav=None, validation=None):
    cfg = ctx.config
    layout = ctx.layout
    half = cfg["ground_half_size"]
    world_half = cfg["world_floor_half_size"]

    _build_base_shops(ctx)
    buckets = _build_generated_buckets(ctx)

    terrain = {"ground_half_size": half, "world_floor_half_size": world_half, "anchors": {}}
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
    shop_width = cfg.get("base_shop_width", base_width)
    shop_depth = cfg.get("base_shop_depth", 0.0)
    shop_height = cfg.get("base_shop_height", 0.0)
    for b in BASES:
        shape = "semi_oval" if "base_platform_width_radius" in cfg else "circle"
        entry = {
            "name": b,
            "position": _vec3(layout[b]),
            "shape": shape,
            "height": cfg["base_platform_height"],
            "width": base_width,
            "depth": base_depth,
            "shop": {
                "name": "{}_Shop".format("Blue" if b == "BlueBase" else "Red"),
                "shape": "rectangle",
                "stage": "blockout",
                "width": shop_width,
                "depth": shop_depth,
                "height": shop_height,
                "rear_of_base": True,
                "spans_full_base_flat_edge": True,
                "adjacent_to_flat_edge": True,
                "orientation": "outward_from_base",
                "navigation_blocker": False,
                "los_blocker": False,
            },
        }
        entry["radius"] = cfg.get("base_platform_radius", base_width / 2.0)
        bases.append(entry)

    # Stable Altar landmark contract used by the gameplay auditor.
    landmarks = list(buckets["landmarks"])
    if not any(item.get("type") == "altar" for item in landmarks):
        altar = buckets["objects"]
        altar = next((item for item in altar if item["name"] == "Altar_Base"), None)
        if altar is not None:
            landmarks.append({
                "name": altar["name"],
                "type": "altar",
                "location": altar["location"],
                "dimensions": altar["dimensions"],
                "meta": altar.get("meta", {}),
            })

    return {
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
        "pockets": _plain(ctx.pockets),
        "landmarks": _plain(landmarks),
        "cover": buckets["cover"],
        "rocks": buckets["rocks"],
        "roads": buckets["roads"],
        "ramps": buckets["ramps"],
        "floors": buckets["floors"],
        "props": buckets["props"],
        "terrain_objects": buckets["terrain_objects"],
        "objects": buckets["objects"],
        "simulation": sim,
        "navigation": nav,
        "validation": validation,
    }


def write_map_data(ctx, path, sim=None, nav=None, validation=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = build_map_data(ctx, sim=sim, nav=nav, validation=validation)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=_plain)
    return path
