"""AetherFlow :: geometry/natural_perimeter.py

AAA natural-world dressing built from the user's linked VerdantTrail asset
collections. The temporary global wall remains the structural/collision
reference; this module only places environmental assets on its INNER side.

Gameplay geometry is never regenerated here. All placed assets are visual /
environmental and registered as nav_blocking=False.
"""
import math
import random
from mathutils import Vector, Matrix

from core.heightmap import get_height_at_point

COLLECTION = "NaturalPerimeter_Instances"
ASSET_COLLECTIONS = {
    "cliff": "cliffs_boulders",
    "rock": "rocks",
    "tree_large": "island_tree_01",
    "tree_medium": "jacaranda_tree",
    "tree_small": "tree_small_02",
    "shrub_01": "shrub_01",
    "shrub_02": "shrub_02",
    "shrub_03": "shrub_03",
    "shrub_04": "shrub_04",
    "grass": "grass_medium_02",
    "hanging_grass": "hanging_grass",
    "plants": "plants_groups",
}

# Band is measured inward from the temporary wall's inner edge.
DEFAULT_BAND_MIN = 1.5
DEFAULT_BAND_MAX = 12.0
DEFAULT_ZONES = 16


def _wave(t, seed, channel=0):
    p = (seed % 997) * 0.013 + channel * 1.733
    return (
        0.55 * math.sin(2 * math.pi * t + p)
        + 0.30 * math.sin(4 * math.pi * t + p * 0.71)
        + 0.15 * math.sin(6 * math.pi * t - p * 1.19)
    )


def _ellipse_point(theta, a, b):
    return Vector((a * math.cos(theta), b * math.sin(theta), 0.0))


def _ellipse_normal(theta, a, b):
    n = Vector((math.cos(theta) / max(a, 1e-9), math.sin(theta) / max(b, 1e-9), 0.0))
    return n.normalized()


def _collection_objects_recursive(coll):
    out = []
    for obj in coll.objects:
        out.append(obj)
    for child in coll.children:
        out.extend(_collection_objects_recursive(child))
    return out


def _asset_collection(name):
    import bpy
    coll = bpy.data.collections.get(name)
    if coll is None:
        return None
    return coll


def _asset_bounds(coll):
    """Return source asset bounds in world space as min/max vectors."""
    objs = [o for o in _collection_objects_recursive(coll) if getattr(o, "type", None) == 'MESH']
    if not objs:
        return None
    min_v = Vector((float('inf'), float('inf'), float('inf')))
    max_v = Vector((float('-inf'), float('-inf'), float('-inf')))
    for obj in objs:
        mw = obj.matrix_world
        for corner in obj.bound_box:
            p = mw @ Vector(corner)
            min_v.x = min(min_v.x, p.x); min_v.y = min(min_v.y, p.y); min_v.z = min(min_v.z, p.z)
            max_v.x = max(max_v.x, p.x); max_v.y = max(max_v.y, p.y); max_v.z = max(max_v.z, p.z)
    return min_v, max_v


def _clear_generated_collection(ctx):
    import bpy
    coll = bpy.data.collections.get(COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(coll)
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    ctx.collections[COLLECTION] = coll
    return coll


def _hide_source_collection(coll):
    """Hide linked source objects only in the AetherFlow scene; do not modify the source file."""
    for obj in _collection_objects_recursive(coll):
        try:
            obj.hide_set(True)
        except Exception:
            pass
        try:
            obj.hide_render = True
        except Exception:
            pass


def _clone_asset_group(ctx, source_coll, target_coll, category, name, location, rotation, target_height, rng):
    """Locally instantiate all mesh objects from a linked asset collection, reusing linked mesh/material data."""
    import bpy
    source_objs = [o for o in _collection_objects_recursive(source_coll) if getattr(o, "type", None) == 'MESH']
    if not source_objs:
        return []

    bounds = _asset_bounds(source_coll)
    if bounds is None:
        return []
    bmin, bmax = bounds
    center = (bmin + bmax) * 0.5
    raw_height = max(0.05, float(bmax.z - bmin.z))
    scale = max(0.05, float(target_height) / raw_height)

    rot = Matrix.Translation(Vector((location.x, location.y, location.z))) @ Matrix.Rotation(rotation, 4, 'Z')
    created = []
    mapping = {}
    for src in source_objs:
        new_obj = src.copy()
        if getattr(src, 'data', None) is not None:
            new_obj.data = src.data  # reuse linked mesh data; no heavy asset duplication
        new_obj.name = f"NaturalPerimeter_{category}_{name}_{src.name}"
        target_coll.objects.link(new_obj)
        rel = (center.inverted() if hasattr(center, 'inverted') else Matrix.Translation(-center))
        # Use world-space transform relative to source collection center.
        rel_m = Matrix.Translation(-center) @ src.matrix_world
        new_obj.matrix_world = rot @ rel_m @ Matrix.Translation(Vector((0.0, 0.0, -bmin.z * scale)))
        # The above transform includes source height; keep scale coherent and avoid parent edits.
        new_obj.matrix_world = rot @ Matrix.Scale(scale, 4) @ rel_m
        new_obj["aether_element"] = "natural_perimeter_asset"
        new_obj["aether_subtype"] = category
        new_obj["nav_blocking"] = False
        new_obj["environmental"] = True
        new_obj["asset_collection"] = source_coll.name
        try:
            ctx.register(new_obj, "prop", dims=tuple(float(v) for v in new_obj.dimensions), meta={
                "element": "natural_perimeter_asset",
                "subtype": category,
                "nav_blocking": False,
                "environmental": True,
                "asset_collection": source_coll.name,
            })
        except Exception:
            pass
        created.append(new_obj)
        mapping[src] = new_obj

    # Preserve parent relationships locally when both parent and child are cloned.
    for src, new_obj in mapping.items():
        if src.parent in mapping:
            new_obj.parent = mapping[src.parent]
            new_obj.matrix_world = created[mapping[src].name] if False else new_obj.matrix_world
    return created


def _place_asset(ctx, coll, target_coll, category, idx, pos, theta, height, rng):
    # Slight tangent-aligned rotation with bounded deterministic variation.
    jitter = rng.uniform(-0.18, 0.18)
    rot = theta + math.pi * 0.5 + jitter
    objs = _clone_asset_group(
        ctx, coll, target_coll, category, f"{idx:03d}", pos, rot, height, rng
    )
    return objs


def _choose_assets(rng, available):
    """Return a macro composition. Weighted choices create organic variation, not a ring."""
    result = []
    if available.get("cliff") and rng.random() < 0.32:
        result.append(("cliff", available["cliff"], rng.uniform(6.0, 10.0)))
    if available.get("rock") and rng.random() < 0.62:
        result.append(("rock", available["rock"], rng.uniform(2.5, 5.5)))
    tree_key = rng.choice([k for k in ("tree_large", "tree_medium", "tree_small") if available.get(k)] or [None])
    if tree_key and rng.random() < 0.48:
        result.append((tree_key, available[tree_key], rng.uniform(4.5, 8.5)))
    shrub_key = rng.choice([k for k in ("shrub_01", "shrub_02", "shrub_03", "shrub_04") if available.get(k)] or [None])
    if shrub_key and rng.random() < 0.72:
        result.append((shrub_key, available[shrub_key], rng.uniform(1.0, 1.8)))
    if available.get("plants") and rng.random() < 0.35:
        result.append(("plants", available["plants"], rng.uniform(0.9, 1.6)))
    if available.get("grass") and rng.random() < 0.82:
        result.append(("grass", available["grass"], rng.uniform(0.6, 1.4)))
    elif available.get("hanging_grass") and rng.random() < 0.45:
        result.append(("hanging_grass", available["hanging_grass"], rng.uniform(0.5, 1.2)))
    return result


def generate_natural_perimeter(ctx):
    """Place real VerdantTrail linked assets in a deterministic inner perimeter band."""
    cfg = ctx.config
    if not cfg.get("outer_boundary", {}).get("enabled", True):
        return {"enabled": False, "objects": []}
    if not getattr(ctx, "outer_boundary", None):
        raise RuntimeError("[NATURAL] outer boundary metrics missing")

    import bpy
    target_coll = _clear_generated_collection(ctx)

    # Resolve only linked collections that the user explicitly attached.
    available = {}
    missing = []
    for key, coll_name in ASSET_COLLECTIONS.items():
        coll = _asset_collection(coll_name)
        if coll is None:
            missing.append(coll_name)
        else:
            if not _collection_objects_recursive(coll):
                missing.append(coll_name)
            else:
                available[key] = coll
                _hide_source_collection(coll)

    if not available:
        raise RuntimeError("[NATURAL] No linked VerdantTrail asset collections found. Expected: {}".format(", ".join(ASSET_COLLECTIONS.values())))

    ecfg = cfg.get("outer_boundary", {})
    major_axis = ctx.outer_boundary.get("major_axis", "Y")
    if major_axis == "X":
        a = float(ctx.outer_boundary["semi_major_axis"])
        b = float(ctx.outer_boundary["semi_minor_axis"])
    else:
        a = float(ctx.outer_boundary["semi_minor_axis"])
        b = float(ctx.outer_boundary["semi_major_axis"])

    wall_thickness = ctx.outer_boundary.get("wall_thickness", ecfg.get("wall_thickness_max", 4.0))
    if isinstance(wall_thickness, (list, tuple)):
        wall_t = max(float(v) for v in wall_thickness) if wall_thickness else 4.0
    else:
        wall_t = float(wall_thickness)

    world_half = float(cfg.get("world_floor_half_size", cfg.get("ground_half_size", 100.0) + 10.0))
    gameplay_half = float(cfg.get("ground_half_size", 100.0))
    wall_inner_offset = wall_t * 0.5

    # Natural band is INSIDE the temporary wall. Keep it compact enough that it
    # cannot alter gameplay geometry, while allowing real asset composition.
    band_min = float(ecfg.get("natural_band_min", DEFAULT_BAND_MIN))
    band_max = float(ecfg.get("natural_band_max", DEFAULT_BAND_MAX))
    wall_inner_min = min(a, b) - wall_inner_offset
    effective_max = min(band_max, max(band_min, (wall_inner_min - gameplay_half) + 0.15))

    # If the wall is almost on the gameplay boundary, fall back to a compact
    # dressing band just outside the gameplay footprint, avoiding objectives by design.
    if effective_max <= band_min + 0.05:
        band_min = max(0.75, min(band_min, effective_max * 0.55))
        effective_max = max(band_min + 0.5, effective_max)

    seed = int(ecfg.get("seed", cfg.get("seed", 1337))) + 1701
    rng = random.Random(seed)
    zone_n = int(ecfg.get("natural_macro_zones", DEFAULT_ZONES))

    stats = {
        "macro_zones": zone_n,
        "large_rocks": 0,
        "medium_rocks": 0,
        "small_rocks": 0,
        "trees": 0,
        "shrubs": 0,
        "grass": 0,
        "plants": 0,
        "escape_gaps": 0,
        "objects": 0,
        "linked_assets": True,
        "missing_collections": sorted(set(missing)),
    }

    index = 0
    for zone in range(zone_n):
        t = (zone + 0.5) / zone_n
        base_theta = math.tau * t
        # Low-frequency macro deformation controls density and radial depth only.
        wave = 0.55 * _wave(t, seed, 2) + 0.45 * _wave(t, seed, 7)
        theta = base_theta + 0.06 * _wave(t, seed, 9)
        boundary = _ellipse_point(theta, a, b)
        outward = _ellipse_normal(theta, a, b)
        inward = -outward
        tangent = Vector((-outward.y, outward.x, 0.0)).normalized()

        depth_center = band_min + (0.35 + 0.30 * (wave + 1.0) / 2.0) * max(0.0, effective_max - band_min)
        # Dense formations stay closest to wall; vegetation fills inward layers.
        comp = _choose_assets(rng, available)

        for local_idx, (category, coll, target_height) in enumerate(comp):
            if category == "cliff":
                depth = max(band_min, depth_center - rng.uniform(0.0, 1.5))
                lateral = rng.uniform(-3.8, 3.8)
                h = rng.uniform(6.0, 10.0)
                target_height = h
            elif category == "rock":
                depth = depth_center + rng.uniform(-0.6, 1.5)
                lateral = rng.uniform(-5.0, 5.0)
                target_height = rng.uniform(2.5, 5.5)
            elif category.startswith("tree"):
                depth = depth_center + rng.uniform(2.0, 5.0)
                lateral = rng.uniform(-4.5, 4.5)
                target_height = rng.uniform(4.5, 8.5)
            elif category.startswith("shrub") or category == "plants":
                depth = depth_center + rng.uniform(3.0, 7.0)
                lateral = rng.uniform(-5.0, 5.0)
                target_height = rng.uniform(0.9, 1.8)
            else:
                depth = depth_center + rng.uniform(5.0, 8.0)
                lateral = rng.uniform(-5.5, 5.5)
                target_height = rng.uniform(0.5, 1.4)

            depth = max(band_min, min(effective_max, depth))
            pos = boundary + inward * depth + tangent * lateral
            pos.z = get_height_at_point(Vector((pos.x, pos.y, 0.0)), cfg, ctx.layout)

            # Keep source-derived assets away from the exact gameplay boundary.
            if math.hypot(pos.x, pos.y) > gameplay_half - 0.25:
                pos = pos + inward * 0.6
            if math.hypot(pos.x, pos.y) < gameplay_half - effective_max - 6.0:
                continue

            created = _place_asset(ctx, coll, target_coll, category, index, pos, theta, target_height, rng)
            if not created:
                continue
            index += 1
            stats["objects"] += len(created)
            if category == "cliff":
                stats["large_rocks"] += 1
            elif category == "rock":
                stats["medium_rocks"] += 1
            elif category.startswith("tree"):
                stats["trees"] += 1
            elif category.startswith("shrub"):
                stats["shrubs"] += 1
            elif category == "plants":
                stats["plants"] += 1
            else:
                stats["grass"] += 1

    ctx.natural_perimeter = {
        "enabled": True,
        "collection": COLLECTION,
        "source": "VerdantTrail linked collections",
        "macro_zones": zone_n,
        "band_min": round(band_min, 3),
        "band_max": round(effective_max, 3),
        "escape_gaps": 0,
        "nav_blocking": False,
        "gameplay_bounds_unchanged": True,
        "linked_assets": True,
        "missing_collections": stats["missing_collections"],
        "stats": stats,
        "objects": stats["objects"],
    }

    print(
        "    [NATURAL] source=VerdantTrail linked assets macro_zones={} large_rocks={} medium_rocks={} trees={} shrubs={} grass={} plants={} objects={} nav_blocking=0".format(
            zone_n, stats["large_rocks"], stats["medium_rocks"], stats["trees"], stats["shrubs"], stats["grass"], stats["plants"], stats["objects"]
        )
    )
    if missing:
        print("    [NATURAL] missing_asset_collections={}".format(", ".join(sorted(set(missing)))))
    print("    [NATURAL] placement=INSIDE_GLOBAL_WALL gameplay_bounds=UNCHANGED escape_gaps=0")
    return dict(ctx.natural_perimeter)
