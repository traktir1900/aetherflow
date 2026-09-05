"""
AetherFlow :: geometry/structures.py
All fixed map structures, generated from config + layout:

  - 5 capture points (pentagon) + turrets
  - Blue Base / Red Base platforms + crystals
  - central Aether Altar + Aether Crown
  - core combat cover (pillar / L-covers / pockets / south screen)
  - choke rocks at the central west/east gateways
  - ring roads + base roads + north ramp
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
from core.layout import RING_NODES, polar
from core.utils import finalize_bmesh


# ---------------------------------------------------------------------------
# Capture points (always all 5) + bases
# ---------------------------------------------------------------------------
def generate_capture_points(ctx):
    cfg = ctx.config
    plat_r = cfg["capture_platform_radius"]
    plat_h = cfg["capture_platform_height"]

    for pname in RING_NODES:
        pos = ctx.layout[pname].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=cfg["circle_segments"],
                              radius1=plat_r, radius2=plat_r, depth=plat_h)
        bmesh.ops.translate(bm, verts=bm.verts, vec=pos + Vector((0, 0, plat_h / 2.0)))
        finalize_bmesh(bm, "CapturePlatform_{}".format(pname), "CapturePoints",
                       ctx.get_material("stone"), ctx, kind="capture_point",
                       dims=(plat_r * 2, plat_r * 2, plat_h),
                       meta={"point": pname, "radius": plat_r, "height": plat_h})

        dir_vec = Vector((pos.x, pos.y, 0.0)).normalized()
        turret_pos = pos + dir_vec * cfg["turret_offset"]
        turret_pos.z = get_height_at_point(turret_pos, cfg, ctx.layout)
        bm_t = bmesh.new()
        bmesh.ops.create_cone(bm_t, cap_ends=True, segments=12,
                              radius1=cfg["turret_radius_base"],
                              radius2=cfg["turret_radius_top"],
                              depth=cfg["turret_depth"])
        bmesh.ops.translate(bm_t, verts=bm_t.verts,
                            vec=turret_pos + Vector((0, 0, cfg["turret_z_offset"])))
        finalize_bmesh(bm_t, "Turret_{}".format(pname), "CapturePoints",
                       ctx.get_material("stone"), ctx, kind="turret",
                       dims=(cfg["turret_radius_base"] * 2,
                             cfg["turret_radius_base"] * 2, cfg["turret_depth"]))


def generate_bases(ctx):
    cfg = ctx.config
    plat_r = cfg["base_platform_radius"]
    plat_h = cfg["base_platform_height"]

    for team, base_key, mat_team, mat_cryst in [
        ("Blue", "BlueBase", "blue_team", "blue_crystal"),
        ("Red", "RedBase", "red_team", "red_crystal"),
    ]:
        pos = ctx.layout[base_key].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=cfg["circle_segments"],
                              radius1=plat_r, radius2=plat_r, depth=plat_h)
        bmesh.ops.translate(bm, verts=bm.verts, vec=pos + Vector((0, 0, plat_h / 2.0)))
        finalize_bmesh(bm, "{}_BasePlatform".format(team), "Bases",
                       ctx.get_material(mat_team), ctx, kind="base",
                       dims=(plat_r * 2, plat_r * 2, plat_h),
                       meta={"team": team, "radius": plat_r})

        bm_c = bmesh.new()
        bmesh.ops.create_icosphere(bm_c, subdivisions=2,
                                   radius=cfg["base_crystal_radius"])
        bmesh.ops.translate(bm_c, verts=bm_c.verts,
                            vec=pos + Vector((0, 0, cfg["base_crystal_height"] * 0.5)))
        finalize_bmesh(bm_c, "{}_Crystal".format(team), "Bases",
                       ctx.get_material(mat_cryst), ctx, kind="landmark",
                       dims=(cfg["base_crystal_radius"] * 2,) * 3)


# ---------------------------------------------------------------------------
# Central zone: Aether Altar + Aether Crown + gateway choke rocks
# ---------------------------------------------------------------------------
def generate_core_and_entrances(ctx):
    cfg = ctx.config
    altar = cfg["altar"]
    choke = cfg["choke_rock"]
    center = ctx.layout["Center"]
    core_z = cfg["heights"]["AetherCore"]
    center_pos = Vector((center.x, center.y, core_z))

    # Aether Altar base (dimensions from config — unified scale).
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16,
                          radius1=altar["base_radius1"],
                          radius2=altar["base_radius2"],
                          depth=altar["base_depth"])
    bmesh.ops.translate(bm, verts=bm.verts,
                        vec=center_pos + Vector((0, 0, altar["base_depth"] / 2.0)))
    finalize_bmesh(bm, "Altar_Base", "CapturePoints", ctx.get_material("altar"),
                   ctx, kind="altar",
                   dims=(altar["base_radius1"] * 2, altar["base_radius1"] * 2,
                         altar["base_depth"]),
                   meta={"landmark": "AetherAltar"})

    # Aether Crown — the glowing power core above the altar.
    bm_core = bmesh.new()
    bmesh.ops.create_icosphere(bm_core, subdivisions=2, radius=altar["crown_radius"])
    bmesh.ops.translate(bm_core, verts=bm_core.verts,
                        vec=center_pos + Vector((0, 0, altar["crown_z"])))
    finalize_bmesh(bm_core, "Altar_PowerCore", "CapturePoints",
                   ctx.get_material("altar_glow"), ctx, kind="altar",
                   dims=(altar["crown_radius"] * 2,) * 3,
                   meta={"landmark": "AetherCrown"})

    # West / East choke rocks flanking the central gateways.
    for side, ang in [("West", 180.0), ("East", 0.0)]:
        dir_vec = polar(1.0, ang)
        perp_vec = Vector((-dir_vec.y, dir_vec.x, 0))
        choke_center = center + dir_vec * cfg["center_radius"]
        choke_z = get_height_at_point(choke_center, cfg, ctx.layout)
        for p_sign in [-1, 1]:
            rock_pos = choke_center + perp_vec * (
                cfg["flank_choke_width"] / 2.0 + choke["lateral_extra"]) * p_sign
            rock_pos.z = choke_z
            bm_r = bmesh.new()
            bmesh.ops.create_cone(bm_r, cap_ends=True, segments=7,
                                  radius1=choke["radius1"],
                                  radius2=choke["radius2"],
                                  depth=choke["depth"])
            bmesh.ops.translate(bm_r, verts=bm_r.verts,
                                vec=rock_pos + Vector((0, 0, choke["z_offset"])))
            finalize_bmesh(bm_r, "Core_ChokeRock_{}_{}".format(side, p_sign),
                           "Rocks", ctx.get_material("rock"), ctx, kind="rock",
                           dims=(choke["radius1"] * 2, choke["radius1"] * 2,
                                 choke["depth"]),
                           meta={"choke": side, "footprint_radius": choke["radius1"]})


def generate_core_combat_cover(ctx):
    """Central combat cover.  Positions AND sizes come from config so the
    arrangement follows the unified scale (fixes the old X/Y-vs-Z drift)."""
    cfg = ctx.config
    cc = cfg["core_cover"]
    cp = cfg.get("core_cover_positions", {})
    core_z = cfg["heights"]["AetherCore"]

    def cube(name, size, pos, rot_z=0.0):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
        if rot_z:
            bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)),
                             matrix=mathutils.Matrix.Rotation(math.radians(rot_z), 4, 'Z'),
                             verts=bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts,
                            vec=Vector((pos[0], pos[1], core_z + size[2] / 2.0)))
        finalize_bmesh(bm, name, "CoreCover", ctx.get_material("cover"),
                       ctx, kind="cover", dims=size,
                       meta={"rot_z": rot_z})

    cube("Core_Cover_Pillar_North", cc["north_pillar_size"],
         (0.0, cp.get("north_pillar_y", 10.0) - cc["north_pillar_offset"]))

    for side, sign, angle in [("West", -1.0, 15.0), ("East", 1.0, -15.0)]:
        cube("Core_Cover_LCover_{}".format(side), cc["side_wall_main"],
             (sign * cp.get("side_wall_x", 11.0), cp.get("side_wall_y", 2.0)), angle)

    for side, sign in [("SW", -1.0), ("SE", 1.0)]:
        cube("Core_Cover_Pocket_{}".format(side), cc["pocket_block_size"],
             (sign * cp.get("pocket_x", 7.5), cp.get("pocket_y", -9.0)), sign * 25.0)

    cube("Core_Cover_SouthScreen", cc["south_screen_size"],
         (0.0, cp.get("south_screen_y", -14.0)))


# ---------------------------------------------------------------------------
# Roads + graded ramps
# ---------------------------------------------------------------------------
def create_height_adapted_road(ctx, name, p0, p1, width, material=None,
                               kind="road", grade=False, meta=None):
    """Road / ramp ribbon between p0 and p1.

    grade=False : cross-sections follow the terrain heightmap (roads).
    grade=True  : cross-sections rise LINEARLY from p0.z to p1.z (true graded
                  ramp between two levels).
    """
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

    # Real world-space AABB of the ribbon mesh.  The old tuple
    # (width, length, drop) was computed from the LAYOUT vectors, which always
    # carry z == 0 (heights live in the heightmap), so every road reported a
    # false zero thickness.  width/length/drop are preserved in meta.
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    aabb = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

    out_meta = dict(meta or {})
    out_meta.setdefault("width", round(width, 3))
    out_meta.setdefault("length", round(length, 3))
    out_meta.setdefault("drop", round(abs(p1.z - p0.z), 3))
    return finalize_bmesh(bm, name, "Roads", mat, ctx, kind=kind,
                          dims=aabb, meta=out_meta)


def generate_roads(ctx):
    cfg = ctx.config
    for i in range(len(RING_NODES)):
        a = RING_NODES[i]
        b = RING_NODES[(i + 1) % len(RING_NODES)]
        create_height_adapted_road(ctx, "RingRoad_{}_{}".format(a, b),
                                   ctx.layout[a], ctx.layout[b],
                                   cfg["ring_road_width"])

    create_height_adapted_road(ctx, "BaseRoad_Blue_SW",
                               ctx.layout["BlueBase"], ctx.layout["SWMonolith"],
                               cfg["base_road_width"])
    create_height_adapted_road(ctx, "BaseRoad_Red_SE",
                               ctx.layout["RedBase"], ctx.layout["SEMonolith"],
                               cfg["base_road_width"])

    crown = ctx.layout["Crown"]
    north_gate = polar(cfg["center_radius"], 90.0)
    create_height_adapted_road(ctx, "North_Ramp_Crown_Core", crown, north_gate,
                               cfg["north_ramp_width"], kind="ramp",
                               meta={"graded": False, "terrain_following": True})


def generate_ramps(ctx):
    """Explicit GRADED access ramps onto every raised capture platform.

    The pipeline previously called generate_ramps() while the module exposed
    another name, so ramps silently never ran.  This is the single canonical
    generate_ramps(): for each of the 5 points it builds a linear-grade ramp
    from surrounding ground up to the platform top, and records p0 / p1 /
    slope_deg in meta so validation can verify the grade.
    """
    cfg = ctx.config
    plat_r = cfg["capture_platform_radius"]
    plat_h = cfg["capture_platform_height"]
    run = cfg.get("ramp_run_length", 8.0)
    built = []

    for pname in RING_NODES:
        pos = ctx.layout[pname]
        terrain_z = get_height_at_point(pos, cfg, ctx.layout)
        top_z = terrain_z + plat_h            # platform top the player walks on
        dir_vec = Vector((pos.x, pos.y, 0.0)).normalized()

        end = pos + dir_vec * (plat_r * 0.9)
        end.z = top_z
        start = end + dir_vec * run
        start.z = get_height_at_point(start, cfg, ctx.layout)

        rise = end.z - start.z
        if abs(rise) < 0.02:
            continue  # already at grade, no ramp needed

        slope_deg = math.degrees(math.atan2(abs(rise), run))
        built.append(create_height_adapted_road(
            ctx, "Ramp_{}".format(pname), start, end,
            cfg["north_ramp_width"] * 0.6, kind="ramp", grade=True,
            meta={"graded": True,
                  "p0": [round(start.x, 3), round(start.y, 3), round(start.z, 3)],
                  "p1": [round(end.x, 3), round(end.y, 3), round(end.z, 3)],
                  "slope_deg": round(slope_deg, 2),
                  "point": pname}))
    return built
