"""
AetherFlow :: core/altar_rotation.py

Focused gameplay hardening for the v0.6.2.1 map:
  * remove the old inherited Core_Cover_* clutter around the Altar;
  * add a distinct non-blocking Altar protector category;
  * compute real adjacent-objective macro rotation;
  * keep central rocks from re-colliding with repaired cover;
  * keep all Altar protectors symmetric across the authoritative X -> -X plane.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from core.layout import RING_NODES
from core.utils import finalize_bmesh


def _world_xy_vertices(obj):
    mw = obj.matrix_world
    for v in obj.data.vertices:
        p = mw @ v.co
        yield float(p.x), float(p.y)


def _closest_vertex_xy(obj):
    best = None
    best_d2 = float("inf")
    for x, y in _world_xy_vertices(obj):
        d2 = x * x + y * y
        if d2 < best_d2:
            best_d2 = d2
            best = (x, y)
    return best, math.sqrt(best_d2) if best is not None else float("inf")


def _min_clearance_to_altar(obj, altar_radius):
    _, radius = _closest_vertex_xy(obj)
    return radius - altar_radius


def _sync_scene():
    """Force Blender dependency graph/object matrices to reflect moves."""
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass


def remove_legacy_core_cover(ctx):
    """Delete obsolete inherited Core_Cover_* pieces around the Altar.

    ObjectiveCover_* is deliberately left untouched. The central Altar combat
    space is now dressed only by the five dedicated symmetric Altar_Obstacle_*
    barricades plus the normal map geometry.

    The five-piece layout leaves the entire north/Crown side open.

    IMPORTANT: capture the Blender object name *before* unlink/removal. A
    StructRNA object becomes invalid immediately after bpy.data.objects.remove().
    """
    removed = 0
    removed_names = set()

    for rec in list(ctx.generated_objects):
        name = str(rec.get("name", ""))
        if not name.startswith("Core_Cover_"):
            continue
        obj = rec.get("object")
        if obj is not None:
            try:
                obj_name = str(obj.name)
                if obj_name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                removed_names.add(name)
                removed += 1
            except ReferenceError:
                removed_names.add(name)

    for obj in list(bpy.data.objects):
        obj_name = str(obj.name)
        if obj_name.startswith("Core_Cover_"):
            bpy.data.objects.remove(obj, do_unlink=True)
            if obj_name not in removed_names:
                removed_names.add(obj_name)
                removed += 1

    if removed_names:
        ctx.generated_objects[:] = [
            rec for rec in ctx.generated_objects
            if str(rec.get("name", "")) not in removed_names
        ]
    _sync_scene()
    return removed


def _repair_central_rocks(ctx, push=2.75):
    moved = []
    for rec in ctx.generated_objects:
        name = rec.get("name", "")
        if not name.startswith("Core_Rock_"):
            continue
        obj = rec.get("object")
        if obj is None:
            continue
        try:
            x, y = float(obj.location.x), float(obj.location.y)
        except ReferenceError:
            continue
        radius = math.hypot(x, y)
        if radius < 1e-6:
            continue
        obj.location.x += (x / radius) * push
        obj.location.y += (y / radius) * push
        _sync_scene()
        meta = rec.setdefault("meta", {})
        meta["central_space_repair_m"] = round(float(meta.get("central_space_repair_m", 0.0)) + push, 3)
        moved.append((name, push))
    return moved


def ensure_altar_clearance(ctx, min_clearance=8.0, target_clearance=8.5):
    """Keep the old API as a cleanup/compatibility stage.

    The legacy Core_Cover_* Altar pieces are intentionally gone, so there is
    no longer a CoreCover-to-Altar clearance repair to perform here.
    """
    removed = remove_legacy_core_cover(ctx)
    _repair_central_rocks(ctx)
    if removed:
        print("  -> removed legacy Altar Core_Cover pieces: {}".format(removed))
    return []


def _build_rectangular_protector(name, position, size, rotation_z, ctx, meta):
    """Build one chunky stone barricade with identical dimensions at every side."""
    bm = bmesh.new()
    try:
        bmesh.ops.create_cube(bm, size=2.0)
        sx, sy, sz = (size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
        bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
        bmesh.ops.rotate(
            bm,
            verts=bm.verts,
            cent=Vector((0.0, 0.0, 0.0)),
            matrix=Matrix.Rotation(rotation_z, 4, 'Z'),
        )
        bmesh.ops.translate(
            bm,
            verts=bm.verts,
            vec=Vector((position[0], position[1], position[2] + size[2] * 0.5)),
        )
        return finalize_bmesh(
            bm,
            name,
            "Decorations",
            ctx.get_material("rock"),
            ctx,
            kind="altar_obstacle",
            dims=size,
            meta=meta,
        )
    except Exception:
        bm.free()
        raise


def generate_altar_obstacles(ctx):
    """Create Altar barricades only when explicitly enabled in config."""
    cfg = ctx.config
    protector_cfg = cfg.get("altar_protectors", {})
    if not protector_cfg.get("enabled", False):
        return []

    altar_r = float(cfg["altar"]["base_radius1"])
    count = int(protector_cfg.get("count", 5))
    if count != 5:
        raise ValueError("Altar protectors require exactly 5 pieces for the Crown-side-open layout")

    offset = float(protector_cfg.get("ring_offset_from_altar_m", 3.25))
    wall_length = float(protector_cfg.get("protector_length_m", 3.6))
    wall_depth = float(protector_cfg.get("protector_depth_m", 1.25))
    wall_height = float(protector_cfg.get("protector_height_m", 2.4))
    ring_r = altar_r + offset + wall_depth * 0.5
    size = (wall_length, wall_depth, wall_height)

    lateral_r = ring_r * math.sin(math.radians(45.0))
    axial_r = ring_r * math.cos(math.radians(45.0))
    specs = [
        (1, "NE", +lateral_r, +axial_r, math.radians(45.0), "NE_NW"),
        (2, "NW", -lateral_r, +axial_r, math.radians(-45.0), "NE_NW"),
        (3, "W", -ring_r, 0.0, 0.0, "W_E"),
        (4, "E", +ring_r, 0.0, 0.0, "W_E"),
        (5, "S", 0.0, -ring_r, 0.0, "S_AXIS"),
    ]

    built = []
    for i, side, px, py, rot_z, pair_id in specs:
        built.append(_build_rectangular_protector(
            "Altar_Obstacle_{:02d}".format(i),
            (px, py, float(cfg["heights"]["AetherCore"])),
            size,
            rot_z,
            ctx,
            {
                "landmark": "AetherAltar",
                "non_blocking": True,
                "side": side,
                "ring_radius": round(ring_r, 3),
                "offset_from_altar_edge_m": round(offset, 3),
                "role": "altar_centered_barricade",
                "symmetry_plane": "Y_AXIS",
                "symmetry_pair": pair_id,
                "mirror_of_blue_red": True,
                "cardinal_centered": side in ("W", "E", "S"),
                "crown_side_open": True,
                "identical_geometry": True,
            },
        ))

    return built


def analyze_macro_rotation(ctx, nav_report):
    """Measure the real 5-objective ring rotation from obstacle-aware nav data."""
    routes = nav_report.get("routes", {}) if nav_report else {}
    points = list(RING_NODES)
    speed = float(ctx.config.get("simulation", {}).get("agent_speed", 6.0))
    speed = speed if speed > 0.0 else 6.0
    rows = []

    for i, a in enumerate(points):
        b = points[(i + 1) % len(points)]
        key_ab = "{}->{}".format(a, b)
        key_ba = "{}->{}".format(b, a)
        d = routes.get(key_ab)
        if d is None:
            d = routes.get(key_ba)
        rows.append({"from": a, "to": b, "distance_m": d,
                     "time_s": None if d is None else round(float(d) / speed, 2)})

    valid = [r["time_s"] for r in rows if r["time_s"] is not None]
    result = {
        "definition": "adjacent_capture_point_ring_edges",
        "routes": rows,
        "all_reachable": len(valid) == len(rows),
        "average_time_s": None,
        "min_time_s": None,
        "max_time_s": None,
        "variance_s": None,
        "agent_speed_mps": speed,
    }
    if valid:
        result["average_time_s"] = round(sum(valid) / len(valid), 2)
        result["min_time_s"] = round(min(valid), 2)
        result["max_time_s"] = round(max(valid), 2)
        result["variance_s"] = round(max(valid) - min(valid), 2)
    return result
