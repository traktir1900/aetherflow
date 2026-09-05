"""
AetherFlow :: core/altar_rotation.py

Focused gameplay hardening for the v0.6.2.1 map:
  * enforce CoreCover clearance from the Aether Altar;
  * add a distinct non-blocking Altar protector category;
  * compute real adjacent-objective macro rotation;
  * keep central rocks from re-colliding with repaired cover;
  * keep all Altar protectors strictly symmetric.
"""
import math

import bmesh
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


def _repair_central_rocks(ctx, push=2.75):
    moved = []
    for rec in ctx.generated_objects:
        name = rec.get("name", "")
        if not name.startswith("Core_Rock_"):
            continue
        obj = rec.get("object")
        if obj is None:
            continue
        x, y = float(obj.location.x), float(obj.location.y)
        radius = math.hypot(x, y)
        if radius < 1e-6:
            continue
        obj.location.x += (x / radius) * push
        obj.location.y += (y / radius) * push
        meta = rec.setdefault("meta", {})
        meta["central_space_repair_m"] = round(float(meta.get("central_space_repair_m", 0.0)) + push, 3)
        moved.append((name, push))
    return moved


def ensure_altar_clearance(ctx, min_clearance=8.0, target_clearance=8.5):
    cfg = ctx.config
    altar_radius = float(cfg["altar"]["base_radius1"])
    moved = []

    for rec in ctx.generated_objects:
        name = rec.get("name", "")
        if not name.startswith("Core_Cover_"):
            continue
        obj = rec.get("object")
        if obj is None:
            continue

        before = _min_clearance_to_altar(obj, altar_radius)
        if before >= min_clearance:
            continue

        last = before
        for _ in range(12):
            (vx, vy), _ = _closest_vertex_xy(obj)
            direction = Vector((vx, vy, 0.0))
            if direction.length < 1e-6:
                direction = Vector((float(obj.location.x), float(obj.location.y), 0.0))
            if direction.length < 1e-6:
                direction = Vector((1.0, 0.0, 0.0))
            direction.normalize()

            needed = target_clearance - last
            if needed <= 0.0:
                break
            obj.location.x += direction.x * max(needed * 1.08, 0.05)
            obj.location.y += direction.y * max(needed * 1.08, 0.05)
            new_clearance = _min_clearance_to_altar(obj, altar_radius)
            if new_clearance <= last + 1e-4:
                break
            last = new_clearance
            if last >= target_clearance:
                break

        after = _min_clearance_to_altar(obj, altar_radius)
        rec.setdefault("meta", {})["altar_clearance_repair"] = {
            "before_m": round(before, 3),
            "after_m": round(after, 3),
            "target_m": round(target_clearance, 3),
            "verified": bool(after >= min_clearance),
        }
        moved.append((name, before, after))

    _repair_central_rocks(ctx)
    return moved


def _build_rectangular_protector(name, position, size, rotation_z, ctx, meta):
    """Build one chunky stone barricade with identical dimensions at every side."""
    bm = bmesh.new()
    try:
        bmesh.ops.create_cube(bm, size=2.0)
        sx, sy, sz = (size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
        bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
        # Blender's 4D rotation matrix still requires an explicit 3D axis.
        # Always rotate around world/local Z to keep the barricade orientation
        # deterministic and compatible with Blender 5.2.
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
    """Create four chunky, centered, cardinal Altar barricades.

    The four pieces are the same size and are placed at equal radius on the
    cardinal axes around the exact Altar center (0,0). North/South share one
    orientation; East/West are rotated 90 degrees. The arrangement is exactly
    symmetric around both world axes, guaranteeing Blue/Red fairness.

    The barricades are intentionally close to the Altar rather than spread
    across the surrounding CoreCover field.
    """
    cfg = ctx.config
    altar_r = float(cfg["altar"]["base_radius1"])
    protector_cfg = cfg.get("altar_protectors", {})
    count = int(protector_cfg.get("count", 4))
    if count != 4:
        raise ValueError("Altar protectors require exactly 4 pieces for symmetry")

    # Compact centered layout. Offset is measured from the Altar edge to the
    # nearest barricade face; the footprint is then included in ring_r.
    offset = float(protector_cfg.get("ring_offset_from_altar_m", 3.25))
    wall_length = float(protector_cfg.get("protector_length_m", 3.6))
    wall_depth = float(protector_cfg.get("protector_depth_m", 1.25))
    wall_height = float(protector_cfg.get("protector_height_m", 2.4))
    ring_r = altar_r + offset + wall_depth * 0.5
    size = (wall_length, wall_depth, wall_height)

    specs = [
        (1, "N", 0.0, +ring_r, 0.0, "NORTH_SOUTH"),
        (2, "E", +ring_r, 0.0, math.pi / 2.0, "EAST_WEST"),
        (3, "S", 0.0, -ring_r, 0.0, "NORTH_SOUTH"),
        (4, "W", -ring_r, 0.0, math.pi / 2.0, "EAST_WEST"),
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
                "symmetry_plane": "BOTH_AXES",
                "symmetry_pair": pair_id,
                "mirror_of_blue_red": True,
                "cardinal_centered": True,
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
