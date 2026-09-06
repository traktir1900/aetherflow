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


def _build_base_shops(ctx):
    """Create temporary rectangular shop shells behind each base's flat edge.

    The shop currently spans the full straight rear edge of the semi-oval base.
    It is deliberately a simple rectangle for the blockout stage; gameplay
    logic, doors, shelves, NPCs and visual detailing are deferred.
    """
    cfg = ctx.config
    width = float(cfg.get(
        "base_shop_width",
        cfg.get("base_platform_width_radius", 0.0) * 2.0,
    ))
    depth = float(cfg.get("base_shop_depth", 0.0))
    height = float(cfg.get("base_shop_height", 0.0))
    gap = float(cfg.get("base_shop_gap", 0.0))
    built = []

    if width <= 0.0 or depth <= 0.0 or height <= 0.0:
        return built

    for team, base_key, material_name in [
        ("Blue", "BlueBase", "blue_team"),
        ("Red", "RedBase", "red_team"),
    ]:
        base_pos = ctx.layout[base_key].copy()
        base_pos.z = float(base_pos.z)

        toward_center = Vector((-base_pos.x, -base_pos.y, 0.0))
        if toward_center.length < 1e-6:
            toward_center = Vector((0.0, 1.0, 0.0))
        toward_center.normalize()

        # Flat base edge is at the anchor. Shop occupies the space outward,
        # i.e. opposite the center-facing direction.
        outward = -toward_center
        side = Vector((-toward_center.y, toward_center.x, 0.0))
        rot_z = math.atan2(side.y, side.x)

        center = base_pos + outward * (gap + depth * 0.5)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(
            bm,
            vec=Vector((width, depth, height)),
            verts=bm.verts,
        )
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
                "navigation_blocker": False,
            },
        )
        built.append(obj)

    print(
        "  -> Base shops: {} temporary rear rectangles | full flat-edge span".format(
            len(built)
        )
    )
    return built


def build_map_data(ctx, sim=None, nav=None, validation=None):
    cfg = ctx.config
    layout = ctx.layout
    half = cfg["ground_half_size"]
    world_half = cfg["world_floor_half_size"]

    # Temporary blockout shop geometry is generated at export/save stage so it
    # remains outside gameplay topology for now.
    _build_base_shops(ctx)

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
            },
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
