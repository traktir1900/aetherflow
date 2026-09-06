"""
AetherFlow :: geometry/structures.py
All fixed map structures, generated from config + layout:

  - 5 capture points (pentagon) + turrets
  - Blue Base / Red Base platforms + crystals
  - central Aether Altar + Aether Crown
  - core combat cover (L-covers / pockets / south screen)
  - choke rocks at the central west/east gateways
  - curved Dominion-style ring roads + base roads + north ramp
  - GRADED access ramps onto every raised capture point

Every object is registered (name / transform / dimensions / type) so the
exporter, navigation blockers and validator see the full, real set.  All
positions and sizes are config-driven and follow the unified scale.
"""
import math
import bmesh
import mathutils
from mathutils import Vector

from core.heightmap import get_height_at_point
from core.layout import RING_NODES, RING_ANGLES, polar
from core.utils import finalize_bmesh


def _capture_turret_direction(pos):
    radial = Vector((pos.x, pos.y, 0.0))
    if radial.length < 1e-6:
        return Vector((0.0, -1.0, 0.0))
    radial.normalize()
    if abs(pos.x) < 1e-6:
        return -radial
    tangent = Vector((-radial.y, radial.x, 0.0))
    side = 1.0 if pos.x > 0.0 else -1.0
    rotated = radial * math.cos(math.radians(60.0)) + tangent * side * math.sin(math.radians(60.0))
    return rotated.normalized()


def generate_capture_points(ctx):
    cfg = ctx.config
    plat_r = cfg["capture_platform_radius"]
    plat_h = cfg["capture_platform_height"]
    for pname in RING_NODES:
        # Crown is a logical/PvE Lord anchor. Its Sanctum owns the physical
        # geometry; do not create a normal capture platform or turret there.
        if pname == "Crown":
            continue
        pos = ctx.layout[pname].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=cfg["circle_segments"], radius1=plat_r, radius2=plat_r, depth=plat_h)
        bmesh.ops.translate(bm, verts=bm.verts, vec=pos + Vector((0, 0, plat_h / 2.0)))
        finalize_bmesh(bm, "CapturePlatform_{}".format(pname), "CapturePoints", ctx.get_material("stone"), ctx, kind="capture_point", dims=(plat_r * 2, plat_r * 2, plat_h), meta={"point": pname, "radius": plat_r, "height": plat_h})
        turret_dir = _capture_turret_direction(pos)
        turret_pos = pos + turret_dir * cfg["turret_offset"]
        turret_pos.z = get_height_at_point(turret_pos, cfg, ctx.layout)
        bm_t = bmesh.new()
        bmesh.ops.create_cone(bm_t, cap_ends=True, segments=12, radius1=cfg["turret_radius_base"], radius2=cfg["turret_radius_top"], depth=cfg["turret_depth"])
        bmesh.ops.translate(bm_t, verts=bm_t.verts, vec=turret_pos + Vector((0, 0, cfg["turret_z_offset"])))
        finalize_bmesh(bm_t, "Turret_{}".format(pname), "CapturePoints", ctx.get_material("stone"), ctx, kind="turret", dims=(cfg["turret_radius_base"] * 2, cfg["turret_radius_base"] * 2, cfg["turret_depth"]), meta={"point": pname, "ramp_clearance": True})


def _create_semi_oval_platform(ctx, name, pos, width_radius, depth, height, material, team):
    flat_dir = Vector((-pos.x, -pos.y, 0.0))
    if flat_dir.length < 1e-6:
        flat_dir = Vector((0.0, 1.0, 0.0))
    flat_dir.normalize()
    side_dir = Vector((-flat_dir.y, flat_dir.x, 0.0))
    segments = max(24, int(ctx.config.get("circle_segments", 28)))
    bottom = []
    top = []
    for sx in (-width_radius, width_radius):
        p = pos + side_dir * sx
        p.z = pos.z
        bottom.append(p)
        top.append(p + Vector((0.0, 0.0, height)))
    arc = []
    for i in range(segments + 1):
        theta = math.pi * (i / float(segments))
        local_x = width_radius * math.cos(theta)
        local_y = depth * math.sin(theta)
        p = pos + side_dir * local_x + flat_dir * local_y
        p.z = pos.z
        arc.append(p)
    boundary = [bottom[1]] + arc[1:-1] + [bottom[0]]
    boundary_top = [p + Vector((0.0, 0.0, height)) for p in boundary]
    bm = bmesh.new()
    bottom_verts = [bm.verts.new(p) for p in boundary]
    top_verts = [bm.verts.new(p) for p in boundary_top]
    bm.faces.new(tuple(reversed(bottom_verts)))
    bm.faces.new(tuple(top_verts))
    count = len(bottom_verts)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((bottom_verts[i], bottom_verts[j], top_verts[j], top_verts[i]))
    return finalize_bmesh(bm, name, "Bases", material, ctx, kind="base", dims=(width_radius * 2.0, depth, height), meta={"team": team, "shape": "semi_oval", "flat_edge": "outward", "rounded_edge": "toward_center", "width": round(width_radius * 2.0, 3), "depth": round(depth, 3)})


def generate_bases(ctx):
    cfg = ctx.config
    width_radius = cfg["base_platform_width_radius"]
    depth = cfg["base_platform_depth"]
    plat_h = cfg["base_platform_height"]
    for team, base_key, mat_team, mat_cryst in [("Blue", "BlueBase", "blue_team", "blue_crystal"), ("Red", "RedBase", "red_team", "red_crystal")]:
        pos = ctx.layout[base_key].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)
        _create_semi_oval_platform(ctx, "{}_BasePlatform".format(team), pos, width_radius, depth, plat_h, ctx.get_material(mat_team), team)
        toward_center = Vector((-pos.x, -pos.y, 0.0))
        if toward_center.length > 1e-6:
            toward_center.normalize()
        crystal_pos = pos + toward_center * (depth * 0.38)
        bm_c = bmesh.new()
        bmesh.ops.create_icosphere(bm_c, subdivisions=2, radius=cfg["base_crystal_radius"])
        bmesh.ops.translate(bm_c, verts=bm_c.verts, vec=crystal_pos + Vector((0, 0, cfg["base_crystal_height"] * 0.5)))
        finalize_bmesh(bm_c, "{}_Crystal".format(team), "Bases", ctx.get_material(mat_cryst), ctx, kind="landmark", dims=(cfg["base_crystal_radius"] * 2,) * 3, meta={"team": team, "platform": "{}_BasePlatform".format(team)})


# ---------------------------------------------------------------------------
# Central zone: Aether Altar + Aether Crown + gateway choke rocks
# ---------------------------------------------------------------------------
def generate_core_and_entrances(ctx):
    cfg = ctx.config
    altar = cfg["altar"]
    choke = cfg["choke_rock"]
    center = ctx.layout["Center"]
    core_z = get_height_at_point(center, cfg, ctx.layout)
    center_pos = Vector((center.x, center.y, core_z))

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=altar["base_radius1"], radius2=altar["base_radius2"], depth=altar["base_depth"])
    bmesh.ops.translate(bm, verts=bm.verts, vec=center_pos + Vector((0, 0, altar["base_depth"] / 2.0)))
    finalize_bmesh(bm, "Altar_Base", "CapturePoints", ctx.get_material("altar"), ctx, kind="altar", dims=(altar["base_radius1"] * 2, altar["base_radius1"] * 2, altar["base_depth"]), meta={"landmark": "AetherAltar"})

    bm_core = bmesh.new()
    bmesh.ops.create_icosphere(bm_core, subdivisions=2, radius=altar["crown_radius"])
    bmesh.ops.translate(bm_core, verts=bm_core.verts, vec=center_pos + Vector((0, 0, altar["crown_z"])))
    finalize_bmesh(bm_core, "Altar_PowerCore", "CapturePoints", ctx.get_material("altar_glow"), ctx, kind="altar", dims=(altar["crown_radius"] * 2,) * 3, meta={"landmark": "AetherCrown"})

    for side, ang in [("West", 180.0), ("East", 0.0)]:
        dir_vec = polar(1.0, ang)
        perp_vec = Vector((-dir_vec.y, dir_vec.x, 0))
        choke_center = center + dir_vec * cfg["center_radius"]
        choke_z = get_height_at_point(choke_center, cfg, ctx.layout)
        for p_sign in [-1, 1]:
            rock_pos = choke_center + perp_vec * (cfg["flank_choke_width"] / 2.0 + choke["lateral_extra"]) * p_sign
            rock_pos.z = choke_z
            bm_r = bmesh.new()
            bmesh.ops.create_cone(bm_r, cap_ends=True, segments=7, radius1=choke["radius1"], radius2=choke["radius2"], depth=choke["depth"])
            bmesh.ops.translate(bm_r, verts=bm_r.verts, vec=rock_pos + Vector((0, 0, choke["z_offset"])))
            finalize_bmesh(bm_r, "Core_ChokeRock_{}_{}".format(side, p_sign), "Rocks", ctx.get_material("rock"), ctx, kind="rock", dims=(choke["radius1"] * 2, choke["radius1"] * 2, choke["depth"]), meta={"choke": side, "footprint_radius": choke["radius1"]})


def generate_core_combat_cover(ctx):
    cfg = ctx.config
    cc = cfg["core_cover"]
    cp = cfg.get("core_cover_positions", {})
    core_z = cfg["heights"]["AetherCore"]

    def cube(name, size, pos, rot_z=0.0):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
        if rot_z:
            bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=mathutils.Matrix.Rotation(math.radians(rot_z), 4, 'Z'), verts=bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts, vec=Vector((pos[0], pos[1], core_z + size[2] / 2.0)))
        finalize_bmesh(bm, name, "CoreCover", ctx.get_material("cover"), ctx, kind="cover", dims=size, meta={"rot_z": rot_z})

    for side, sign, angle in [("West", -1.0, 15.0), ("East", 1.0, -15.0)]:
        cube("Core_Cover_LCover_{}".format(side), cc["side_wall_main"], (sign * cp.get("side_wall_x", 11.0), cp.get("side_wall_y", 2.0)), angle)
    for side, sign in [("SW", -1.0), ("SE", 1.0)]:
        cube("Core_Cover_Pocket_{}".format(side), cc["pocket_block_size"], (sign * cp.get("pocket_x", 7.5), cp.get("pocket_y", -9.0)), sign * 25.0)
    cube("Core_Cover_SouthScreen", cc["south_screen_size"], (0.0, cp.get("south_screen_y", -14.0)))


def _road_mesh_from_points(ctx, points, width, material=None, kind="road", meta=None):
    cfg = ctx.config
    mat = material or ctx.get_material("road")
    pts = [Vector(p) for p in points]
    if len(pts) < 2:
        return None
    bm = bmesh.new()
    prev = None
    total_length = 0.0
    for idx, point in enumerate(pts):
        if idx == 0:
            tangent = pts[1] - pts[0]
        elif idx == len(pts) - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[idx + 1] - pts[idx - 1]
        flat_tangent = Vector((tangent.x, tangent.y, 0.0))
        if flat_tangent.length < 1e-6:
            flat_tangent = Vector((1.0, 0.0, 0.0))
        flat_tangent.normalize()
        perp = Vector((-flat_tangent.y, flat_tangent.x, 0.0)) * (width / 2.0)
        left = point - perp
        right = point + perp
        left.z = get_height_at_point(left, cfg, ctx.layout) + cfg["road_z_offset"]
        right.z = get_height_at_point(right, cfg, ctx.layout) + cfg["road_z_offset"]
        vl = bm.verts.new(left)
        vr = bm.verts.new(right)
        if prev is not None:
            bm.faces.new((prev[0], prev[1], vr, vl))
            total_length += (point - pts[idx - 1]).length
        prev = (vl, vr)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    aabb = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    out_meta = dict(meta or {})
    out_meta.setdefault("width", round(width, 3))
    out_meta.setdefault("length", round(total_length, 3))
    out_meta.setdefault("centerline_points", len(pts))
    return finalize_bmesh(bm, meta.pop("_name", "CurvedRoad") if meta else "CurvedRoad", "Roads", mat, ctx, kind=kind, dims=aabb, meta=out_meta)


def create_height_adapted_road(ctx, name, p0, p1, width, material=None, kind="road", grade=False, meta=None):
    cfg = ctx.config
    mat = material or ctx.get_material("road")
    length = (p1 - p0).length
    steps = max(4, int(length / 4.0))
    flat_dir = Vector((p1.x - p0.x, p1.y - p0.y, 0.0)).normalized()
    perp = Vector((-flat_dir.y, flat_dir.x, 0.0)) * (width / 2.0)
    bm = bmesh.new()
    prev = None
    for i in range(steps + 1):
        t = i / float(steps)
        c = p0 + (p1 - p0) * t
        lp = c - perp
        rp = c + perp
        if grade:
            z = p0.z + (p1.z - p0.z) * t + cfg["road_z_offset"]
            lp.z = z
            rp.z = z
        else:
            lp.z = get_height_at_point(lp, cfg, ctx.layout) + cfg["road_z_offset"]
            rp.z = get_height_at_point(rp, cfg, ctx.layout) + cfg["road_z_offset"]
        vl = bm.verts.new(lp)
        vr = bm.verts.new(rp)
        if prev:
            bm.faces.new((prev[0], prev[1], vr, vl))
        prev = (vl, vr)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    aabb = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    out_meta = dict(meta or {})
    out_meta.setdefault("width", round(width, 3))
    out_meta.setdefault("length", round(length, 3))
    out_meta.setdefault("drop", round(abs(p1.z - p0.z), 3))
    return finalize_bmesh(bm, name, "Roads", mat, ctx, kind=kind, dims=aabb, meta=out_meta)


def _smooth_arc_points(radius, start_deg, end_deg, segments=12):
    delta = end_deg - start_deg
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    count = max(4, int(abs(delta) / 8.0) + 1, segments)
    return [polar(radius, start_deg + delta * (i / float(count))) for i in range(count + 1)]


def _quadratic_curve_points(p0, p1, inward_bend, samples=14):
    p0 = Vector(p0)
    p1 = Vector(p1)
    mid = (p0 + p1) * 0.5
    radial = Vector((mid.x, mid.y, 0.0))
    if radial.length < 1e-6:
        control = mid
    else:
        radial.normalize()
        control = mid - radial * inward_bend
    pts = []
    for i in range(max(6, samples) + 1):
        t = i / float(max(6, samples))
        u = 1.0 - t
        pts.append((u * u) * p0 + (2.0 * u * t) * control + (t * t) * p1)
    return pts


def _create_curved_road(ctx, name, points, width, meta=None):
    payload = dict(meta or {})
    payload["_name"] = name
    return _road_mesh_from_points(ctx, points, width, meta=payload)


def generate_roads(ctx):
    cfg = ctx.config
    ring_radius = cfg["outer_ring_radius"]
    for i in range(len(RING_NODES)):
        a = RING_NODES[i]
        b = RING_NODES[(i + 1) % len(RING_NODES)]
        start_ang = RING_ANGLES[a]
        end_ang = RING_ANGLES[b]
        points = _smooth_arc_points(ring_radius, start_ang, end_ang, segments=10)
        _create_curved_road(ctx, "RingRoad_{}_{}".format(a, b), points, cfg["ring_road_width"], meta={"curve_type": "circular_arc", "start": a, "end": b, "radius_m": round(ring_radius, 3)})
    blue_points = _quadratic_curve_points(ctx.layout["BlueBase"], ctx.layout["SWMonolith"], inward_bend=7.5, samples=12)
    red_points = _quadratic_curve_points(ctx.layout["RedBase"], ctx.layout["SEMonolith"], inward_bend=7.5, samples=12)
    _create_curved_road(ctx, "BaseRoad_Blue_SW", blue_points, cfg["base_road_width"], meta={"curve_type": "quadratic_inward", "start": "BlueBase", "end": "SWMonolith"})
    _create_curved_road(ctx, "BaseRoad_Red_SE", red_points, cfg["base_road_width"], meta={"curve_type": "quadratic_inward", "start": "RedBase", "end": "SEMonolith"})
    crown = ctx.layout["Crown"]
    north_gate = polar(cfg["center_radius"], 90.0)
    create_height_adapted_road(ctx, "North_Ramp_Crown_Core", crown, north_gate, cfg["north_ramp_width"], kind="ramp", meta={"graded": False, "terrain_following": True, "curve_type": "straight_axis_approach", "p0": [round(crown.x, 3), round(crown.y, 3), round(get_height_at_point(crown, cfg, ctx.layout), 3)], "p1": [round(north_gate.x, 3), round(north_gate.y, 3), round(get_height_at_point(north_gate, cfg, ctx.layout), 3)]})


def generate_ramps(ctx):
    cfg = ctx.config
    plat_r = cfg["capture_platform_radius"]
    plat_h = cfg["capture_platform_height"]
    run = cfg.get("ramp_run_length", 8.0)
    built = []
    for pname in RING_NODES:
        pos = ctx.layout[pname]
        terrain_z = get_height_at_point(pos, cfg, ctx.layout)
        top_z = terrain_z + plat_h
        dir_vec = Vector((pos.x, pos.y, 0.0)).normalized()
        end = pos + dir_vec * (plat_r * 0.9)
        end.z = top_z
        start = end + dir_vec * run
        start.z = get_height_at_point(start, cfg, ctx.layout)
        rise = end.z - start.z
        if abs(rise) < 0.02:
            continue
        slope_deg = math.degrees(math.atan2(abs(rise), run))
        built.append(create_height_adapted_road(ctx, "Ramp_{}".format(pname), start, end, cfg["north_ramp_width"] * 0.6, kind="ramp", grade=True, meta={"graded": True, "p0": [round(start.x, 3), round(start.y, 3), round(start.z, 3)], "p1": [round(end.x, 3), round(end.y, 3), round(end.z, 3)], "slope_deg": round(slope_deg, 2), "point": pname}))
    return built
