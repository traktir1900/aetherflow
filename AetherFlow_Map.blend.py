import os
import sys
import bpy

# Определяем папку, где сохранен текущий .blend файл
project_dir = bpy.path.abspath("//")

if not os.path.exists(project_dir) or project_dir == "":
    raise RuntimeError("ОШИБКА: Сначала сохраните Blender-файл (File -> Save As) в нужную папку!")

print(f"Распаковка проекта в: {project_dir}")

# Словарь со ВСЕМИ файлами проекта
FILES_DATA = {
    "core/__init__.py": "",
    "geometry/__init__.py": "",
    "visual/__init__.py": "",
    "combat/__init__.py": "",

    "core/config.py": '''CONFIG = {
    "seed": 1337,
    "debug_sightlines": True,
    "map_radius": 95.0,
    "ground_half_size": 105.0,
    "outer_ring_radius": 55.0,
    "base_radius": 88.0,
    "base_spread_deg": 40.0,
    "center_radius": 20.0,
    "heights": {
        "Crown": 1.5,
        "WestMonolith": 0.75,
        "EastMonolith": 0.75,
        "SWMonolith": 0.0,
        "SEMonolith": 0.0,
        "BlueBase": 0.0,
        "RedBase": 0.0,
        "SouthRift": -0.75,
        "AetherCore": -2.0,
    },
    "capture_platform_radius": 8.0,
    "capture_platform_height": 0.6,
    "turret_offset": 11.0,
    "core_cover": {
        "north_pillar_size": (2.5, 2.5, 3.5),
        "north_pillar_offset": 1.0,
        "side_wall_main": (4.0, 1.2, 2.2),
        "side_wall_wing": (1.5, 1.2, 1.8),
        "pocket_block_size": (3.0, 1.5, 1.6),
        "south_screen_size": (5.0, 1.5, 2.5),
    },
    "ring_road_width": 15.0,
    "base_road_width": 10.0,
    "north_ramp_width": 12.0,
    "flank_choke_width": 5.0,
    "road_z_offset": 0.05,
    "shrine_road_offset": 10.0,
    "speed_shrine_radius": 3.5,
    "health_relic_radius": 2.5,
    "base_platform_radius": 14.0,
    "base_platform_height": 0.6,
    "base_crystal_height": 6.0,
    "circle_segments": 28,
}
''',

    "core/context.py": '''class MapContext:
    def __init__(self, config):
        self.config = config
        self.layout = {}
        self.collections = {}
        self.materials = {}

    def get_collection(self, name):
        return self.collections.get(name)

    def get_material(self, name):
        return self.materials.get(name)
''',

    "core/utils.py": '''import bpy

def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)

def setup_collections(ctx):
    names = ["Terrain", "Bases", "CapturePoints", "Roads", "Decorations", "Rocks", "CoreCover", "DebugSightlines"]
    for name in names:
        coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if coll.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(coll)
        ctx.collections[name] = coll

def finalize_bmesh(bm, name, collection_key, material, ctx):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    ctx.get_collection(collection_key).objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj
''',

    "core/layout.py": '''import math
from mathutils import Vector

RING_NODES = ["Crown", "EastMonolith", "SEMonolith", "SWMonolith", "WestMonolith"]
RING_ANGLES = {"Crown": 90.0, "EastMonolith": 18.0, "SEMonolith": 306.0, "SWMonolith": 234.0, "WestMonolith": 162.0}

def polar(radius, deg):
    rad = math.radians(deg)
    return Vector((radius * math.cos(rad), radius * math.sin(rad), 0.0))

def build_layout(cfg):
    R = cfg["outer_ring_radius"]
    layout = {"Center": Vector((0.0, 0.0, 0.0))}
    for name, ang in RING_ANGLES.items():
        layout[name] = polar(R, ang)

    B = cfg["base_radius"]
    spread = cfg["base_spread_deg"] / 2.0
    layout["BlueBase"] = polar(B, 270.0 - spread)
    layout["RedBase"] = polar(B, 270.0 + spread)
    layout["SouthRift"] = (layout["SWMonolith"] + layout["SEMonolith"]) / 2.0
    return layout
''',

    "core/heightmap.py": '''import math
from mathutils import Vector

def get_height_at_point(pos, cfg, layout):
    p2d = Vector((pos.x, pos.y))
    dist_center = p2d.length

    core_r = cfg["center_radius"]
    if dist_center < core_r:
        t = dist_center / core_r
        return cfg["heights"]["AetherCore"] * ((1.0 - t) ** 2)

    if dist_center < core_r + 14.0:
        raw_t = (dist_center - core_r) / 14.0
        smooth_t = raw_t * raw_t * (3.0 - 2.0 * raw_t)

        angle = math.degrees(math.atan2(p2d.y, p2d.x)) % 360
        if 45 <= angle <= 135:
            target_h = cfg["heights"]["Crown"]
        elif 135 < angle < 225:
            target_h = cfg["heights"]["WestMonolith"]
        elif 225 <= angle <= 315:
            target_h = cfg["heights"]["SouthRift"]
        else:
            target_h = cfg["heights"]["EastMonolith"]

        return cfg["heights"]["AetherCore"] * (1.0 - smooth_t) + target_h * smooth_t

    south_mid = layout["SouthRift"]
    dist_south = (p2d - Vector((south_mid.x, south_mid.y))).length
    if dist_south < 25.0:
        t = 1.0 - (dist_south / 25.0)
        return cfg["heights"]["SouthRift"] * (t ** 1.5)

    crown_pos = Vector((layout["Crown"].x, layout["Crown"].y))
    west_pos = Vector((layout["WestMonolith"].x, layout["WestMonolith"].y))
    east_pos = Vector((layout["EastMonolith"].x, layout["EastMonolith"].y))

    d_crown = max(0.001, (p2d - crown_pos).length)
    d_west = max(0.001, (p2d - west_pos).length)
    d_east = max(0.001, (p2d - east_pos).length)

    w_crown = max(0.0, 1.0 - d_crown / 45.0)
    w_west = max(0.0, 1.0 - d_west / 40.0)
    w_east = max(0.0, 1.0 - d_east / 40.0)

    z = (w_crown * cfg["heights"]["Crown"] +
         w_west * cfg["heights"]["WestMonolith"] +
         w_east * cfg["heights"]["EastMonolith"])

    return min(1.5, z)
''',

    "visual/materials.py": '''import bpy

def make_material(ctx, name, base_color, emission_color=None, emission_strength=0.0, roughness=0.7, metallic=0.0):
    if name in ctx.materials:
        return ctx.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = None
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break

    if bsdf is None:
        mat.node_tree.nodes.clear()
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if emission_color and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    mat.diffuse_color = (*base_color, 1.0)
    ctx.materials[name] = mat
    return mat

def setup_materials(ctx):
    make_material(ctx, "ground", (0.18, 0.17, 0.16), roughness=0.95)
    make_material(ctx, "stone", (0.35, 0.34, 0.33), roughness=0.85)
    make_material(ctx, "rock", (0.22, 0.21, 0.20), roughness=0.9)
    make_material(ctx, "road", (0.42, 0.38, 0.30), roughness=0.8)
    make_material(ctx, "cover", (0.28, 0.26, 0.24), roughness=0.7, metallic=0.1)

    mat = bpy.data.materials.new(name="MAT_Height_Debug")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    attr = nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "HeightDebug"
    mat.node_tree.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    ctx.materials["height_debug"] = mat

    make_material(ctx, "blue_team", (0.05, 0.25, 0.85), emission_color=(0.1, 0.4, 1.0), emission_strength=1.2)
    make_material(ctx, "red_team", (0.85, 0.08, 0.08), emission_color=(1.0, 0.15, 0.1), emission_strength=1.2)
    make_material(ctx, "blue_crystal", (0.1, 0.3, 0.9), emission_color=(0.2, 0.5, 1.0), emission_strength=3.5)
    make_material(ctx, "red_crystal", (0.9, 0.1, 0.1), emission_color=(1.0, 0.2, 0.15), emission_strength=3.5)
    make_material(ctx, "altar", (0.55, 0.45, 0.15), roughness=0.4, metallic=0.3)
    make_material(ctx, "altar_glow", (0.7, 0.4, 1.0), emission_color=(0.7, 0.4, 1.0), emission_strength=4.0)
    make_material(ctx, "shrine", (0.2, 0.8, 0.6), emission_color=(0.3, 1.0, 0.7), emission_strength=3.0)
    make_material(ctx, "relic", (0.8, 0.7, 0.2), emission_color=(1.0, 0.9, 0.3), emission_strength=2.5)
    make_material(ctx, "ray_clear", (1.0, 0.0, 0.0), emission_color=(1.0, 0.0, 0.0), emission_strength=5.0)
    make_material(ctx, "ray_blocked", (0.0, 1.0, 0.2), emission_color=(0.0, 1.0, 0.2), emission_strength=2.0)
''',

    "visual/decorations.py": '''import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh
from geometry.roads import create_height_adapted_road

def generate_speed_shrines_with_offset(ctx):
    cfg = ctx.config
    shrine_configs = [
        ("Blue", ctx.layout["BlueBase"], ctx.layout["SWMonolith"]),
        ("Red", ctx.layout["RedBase"], ctx.layout["SEMonolith"]),
    ]

    for team, p_base, p_target in shrine_configs:
        mid_point = (p_base + p_target) / 2.0
        road_dir = (p_target - p_base).normalized()
        base_direction = Vector((p_base.x, p_base.y, 0.0)).normalized()
        
        perp_outward = Vector((-road_dir.y, road_dir.x, 0.0))
        if perp_outward.dot(base_direction) < 0:
            perp_outward *= -1.0

        shrine_pos = mid_point + perp_outward * cfg["shrine_road_offset"]
        shrine_pos.z = get_height_at_point(shrine_pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=cfg["speed_shrine_radius"], depth=0.3)
        bmesh.ops.translate(bm, verts=bm.verts, vec=shrine_pos + Vector((0, 0, 0.15)))
        finalize_bmesh(bm, f"SpeedShrine_{team}", "Decorations", ctx.get_material("shrine"), ctx)

        create_height_adapted_road(f"ShrinePath_{team}", mid_point, shrine_pos, 4.0, ctx.get_material("road"), ctx)

def generate_3_health_relics(ctx):
    cfg = ctx.config
    crown_dir_outward = Vector((ctx.layout["Crown"].x, ctx.layout["Crown"].y, 0.0)).normalized()
    crown_relic_pos = ctx.layout["Crown"] + crown_dir_outward * (cfg["capture_platform_radius"] + 3.5)

    relic_locations = [
        ("SouthRift", ctx.layout["SouthRift"]),
        ("AetherCore", ctx.layout["Center"]),
        ("CrownApex", crown_relic_pos),
    ]

    for name, pos in relic_locations:
        z = max(get_height_at_point(pos, cfg, ctx.layout), cfg["heights"]["Crown"]) if name == "CrownApex" else get_height_at_point(pos, cfg, ctx.layout)
        r_pos = Vector((pos.x, pos.y, z))

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=cfg["health_relic_radius"], depth=0.4)
        bmesh.ops.translate(bm, verts=bm.verts, vec=r_pos + Vector((0, 0, 0.2)))
        finalize_bmesh(bm, f"HealthRelic_{name}", "Decorations", ctx.get_material("relic"), ctx)
''',

    "geometry/terrain.py": '''import bpy
import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point

def generate_heightmapped_terrain(ctx):
    cfg = ctx.config
    size = cfg["ground_half_size"]
    bm = bmesh.new()
    res = 52
    step = (size * 2.0) / res
    verts_grid = []
    
    vcol_layer = bm.loops.layers.color.new("HeightDebug")

    for row in range(res + 1):
        row_verts = []
        y = -size + row * step
        for col in range(res + 1):
            x = -size + col * step
            pos_2d = Vector((x, y, 0.0))
            z = get_height_at_point(pos_2d, cfg, ctx.layout)
            v = bm.verts.new((x, y, z))
            row_verts.append(v)
        verts_grid.append(row_verts)

    for r in range(res):
        for c in range(res):
            v0 = verts_grid[r][c]
            v1 = verts_grid[r][c + 1]
            v2 = verts_grid[r + 1][c + 1]
            v3 = verts_grid[r + 1][c]
            face = bm.faces.new((v0, v1, v2, v3))
            
            for loop in face.loops:
                z = loop.vert.co.z
                if z >= 1.2:
                    color = (0.85, 0.85, 0.9, 1.0)
                elif z >= 0.5:
                    color = (0.55, 0.55, 0.55, 1.0)
                elif z >= -0.2:
                    color = (0.35, 0.35, 0.35, 1.0)
                elif z >= -1.2:
                    color = (0.3, 0.22, 0.18, 1.0)
                else:
                    color = (0.2, 0.12, 0.3, 1.0)
                loop[vcol_layer] = color

    mesh = bpy.data.meshes.new("Terrain_Heightmap_DEBUG_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    if not mesh.color_attributes.get("HeightDebug"):
        mesh.color_attributes.new(name="HeightDebug", type='FLOAT_COLOR', domain='CORNER')

    obj = bpy.data.objects.new("Terrain_Heightmap_DEBUG", mesh)
    ctx.get_collection("Terrain").objects.link(obj)
    obj.data.materials.append(ctx.get_material("height_debug"))
    return obj
''',

    "geometry/core_geometry.py": '''import bmesh
from mathutils import Vector
from core.layout import polar
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

def generate_core_and_entrances(ctx):
    cfg = ctx.config
    center = ctx.layout["Center"]
    core_z = cfg["heights"]["AetherCore"]
    center_pos = Vector((center.x, center.y, core_z))

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=4.5, radius2=4.0, depth=0.8)
    bmesh.ops.translate(bm, verts=bm.verts, vec=center_pos + Vector((0, 0, 0.4)))
    finalize_bmesh(bm, "Altar_Base", "CapturePoints", ctx.get_material("altar"), ctx)

    bm_core = bmesh.new()
    bmesh.ops.create_icosphere(bm_core, subdivisions=2, radius=1.4)
    bmesh.ops.translate(bm_core, verts=bm_core.verts, vec=center_pos + Vector((0, 0, 2.0)))
    finalize_bmesh(bm_core, "Altar_PowerCore", "CapturePoints", ctx.get_material("altar_glow"), ctx)

    for side, ang in [("West", 180.0), ("East", 0.0)]:
        dir_vec = polar(1.0, ang)
        perp_vec = Vector((-dir_vec.y, dir_vec.x, 0))
        choke_center = center + dir_vec * cfg["center_radius"]
        choke_z = get_height_at_point(choke_center, cfg, ctx.layout)
        
        for p_sign in [-1, 1]:
            rock_pos = choke_center + perp_vec * (cfg["flank_choke_width"] / 2.0 + 2.5) * p_sign
            rock_pos.z = choke_z
            bm_r = bmesh.new()
            bmesh.ops.create_cone(bm_r, cap_ends=True, segments=7, radius1=2.8, radius2=1.5, depth=4.5)
            bmesh.ops.translate(bm_r, verts=bm_r.verts, vec=rock_pos + Vector((0, 0, 2.25)))
            finalize_bmesh(bm_r, f"Core_ChokeRock_{side}_{p_sign}", "Rocks", ctx.get_material("rock"), ctx)
''',

    "geometry/bases.py": '''import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.layout import RING_NODES
from core.utils import finalize_bmesh

def generate_capture_points(ctx):
    cfg = ctx.config
    plat_r = cfg["capture_platform_radius"]
    plat_h = cfg["capture_platform_height"]

    for pname in RING_NODES:
        pos = ctx.layout[pname].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=cfg["circle_segments"], radius1=plat_r, radius2=plat_r, depth=plat_h)
        bmesh.ops.translate(bm, verts=bm.verts, vec=pos + Vector((0, 0, plat_h / 2.0)))
        finalize_bmesh(bm, f"CapturePlatform_{pname}", "CapturePoints", ctx.get_material("stone"), ctx)

        dir_vec = Vector((pos.x, pos.y, 0.0)).normalized()
        turret_pos = pos + dir_vec * cfg["turret_offset"]
        turret_pos.z = get_height_at_point(turret_pos, cfg, ctx.layout)
        
        bm_t = bmesh.new()
        bmesh.ops.create_cone(bm_t, cap_ends=True, segments=12, radius1=1.8, radius2=0.9, depth=4.0)
        bmesh.ops.translate(bm_t, verts=bm_t.verts, vec=turret_pos + Vector((0, 0, 2.0)))
        finalize_bmesh(bm_t, f"Turret_{pname}", "CapturePoints", ctx.get_material("stone"), ctx)

def generate_bases(ctx):
    cfg = ctx.config
    plat_r = cfg["base_platform_radius"]

    for team, base_key, mat_team, mat_cryst in [
        ("Blue", "BlueBase", ctx.get_material("blue_team"), ctx.get_material("blue_crystal")),
        ("Red", "RedBase", ctx.get_material("red_team"), ctx.get_material("red_crystal"))
    ]:
        pos = ctx.layout[base_key].copy()
        pos.z = get_height_at_point(pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=plat_r, radius2=plat_r, depth=cfg["base_platform_height"])
        bmesh.ops.translate(bm, verts=bm.verts, vec=pos + Vector((0, 0, cfg["base_platform_height"] / 2.0)))
        finalize_bmesh(bm, f"{team}_BasePlatform", "Bases", mat_team, ctx)

        bm_c = bmesh.new()
        bmesh.ops.create_icosphere(bm_c, subdivisions=2, radius=2.0)
        bmesh.ops.translate(bm_c, verts=bm_c.verts, vec=pos + Vector((0, 0, 4.0)))
        finalize_bmesh(bm_c, f"{team}_Crystal", "Bases", mat_cryst, ctx)
''',

    "geometry/roads.py": '''import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.layout import RING_NODES, polar
from core.utils import finalize_bmesh

def create_height_adapted_road(name, p0, p1, width, material, ctx):
    cfg = ctx.config
    length = (p1 - p0).length
    steps = max(4, int(length / 4.0))

    flat_dir = Vector((p1.x - p0.x, p1.y - p0.y, 0.0)).normalized()
    perp_vec = Vector((-flat_dir.y, flat_dir.x, 0.0)) * (width / 2.0)

    bm = bmesh.new()
    prev_left, prev_right = None, None

    for i in range(steps + 1):
        t = i / steps
        curr_center = p0 + (p1 - p0) * t
        
        left_pos = curr_center - perp_vec
        right_pos = curr_center + perp_vec

        left_pos.z = get_height_at_point(left_pos, cfg, ctx.layout) + cfg["road_z_offset"]
        right_pos.z = get_height_at_point(right_pos, cfg, ctx.layout) + cfg["road_z_offset"]

        v_left = bm.verts.new(left_pos)
        v_right = bm.verts.new(right_pos)

        if prev_left and prev_right:
            bm.faces.new((prev_left, prev_right, v_right, v_left))

        prev_left, prev_right = v_left, v_right

    finalize_bmesh(bm, name, "Roads", material, ctx)

def generate_roads(ctx):
    cfg = ctx.config
    mat_road = ctx.get_material("road")
    for i in range(len(RING_NODES)):
        a, b = RING_NODES[i], RING_NODES[(i + 1) % len(RING_NODES)]
        create_height_adapted_road(f"RingRoad_{a}_{b}", ctx.layout[a], ctx.layout[b], cfg["ring_road_width"], mat_road, ctx)

    create_height_adapted_road("BaseRoad_Blue_SW", ctx.layout["BlueBase"], ctx.layout["SWMonolith"], cfg["base_road_width"], mat_road, ctx)
    create_height_adapted_road("BaseRoad_Red_SE", ctx.layout["RedBase"], ctx.layout["SEMonolith"], cfg["base_road_width"], mat_road, ctx)

    crown_pos = ctx.layout["Crown"]
    core_north_gate = polar(cfg["center_radius"], 90.0)
    create_height_adapted_road("North_Ramp_Crown_Core", crown_pos, core_north_gate, cfg["north_ramp_width"], mat_road, ctx)
''',

    "combat/combat_cover.py": '''import bmesh
import math
import mathutils
from mathutils import Vector
from core.utils import finalize_bmesh

def generate_core_combat_cover(ctx):
    cfg = ctx.config["core_cover"]
    core_z = ctx.config["heights"]["AetherCore"]

    p_size = cfg["north_pillar_size"]
    pillar_pos = Vector((0.0, 10.0 - cfg["north_pillar_offset"], core_z))
    bm_p = bmesh.new()
    bmesh.ops.create_cube(bm_p, size=1.0)
    bmesh.ops.scale(bm_p, vec=Vector(p_size), verts=bm_p.verts)
    bmesh.ops.translate(bm_p, verts=bm_p.verts, vec=pillar_pos + Vector((0, 0, p_size[2] / 2.0)))
    finalize_bmesh(bm_p, "Core_Cover_Pillar_North", "CoreCover", ctx.get_material("cover"), ctx)

    m_size = cfg["side_wall_main"]
    w_size = cfg["side_wall_wing"]
    for side, sign, angle in [("West", -1.0, math.radians(15.0)), ("East", 1.0, math.radians(-15.0))]:
        base_pos = Vector((sign * 11.0, 2.0, core_z))
        bm_l = bmesh.new()
        bmesh.ops.create_cube(bm_l, size=1.0)
        bmesh.ops.scale(bm_l, vec=Vector(m_size), verts=bm_l.verts)
        
        bm_w = bmesh.new()
        bmesh.ops.create_cube(bm_w, size=1.0)
        bmesh.ops.scale(bm_w, vec=Vector(w_size), verts=bm_w.verts)
        wing_offset = Vector((sign * (-m_size[0] / 2.0 + w_size[0] / 2.0), -m_size[1] / 2.0 - w_size[1] / 2.0, (w_size[2] - m_size[2]) / 2.0))
        bmesh.ops.translate(bm_w, verts=bm_w.verts, vec=wing_offset)

        for v in bm_w.verts:
            bm_l.verts.new(v.co)
        bm_w.free()

        bmesh.ops.rotate(bm_l, cent=Vector((0, 0, 0)), matrix=mathutils.Matrix.Rotation(angle, 4, 'Z'), verts=bm_l.verts)
        bmesh.ops.translate(bm_l, verts=bm_l.verts, vec=base_pos + Vector((0, 0, m_size[2] / 2.0)))
        finalize_bmesh(bm_l, f"Core_Cover_LCover_{side}", "CoreCover", ctx.get_material("cover"), ctx)

    pk_size = cfg["pocket_block_size"]
    for side, sign in [("SW", -1.0), ("SE", 1.0)]:
        pk_pos = Vector((sign * 7.5, -9.0, core_z))
        bm_pk = bmesh.new()
        bmesh.ops.create_cube(bm_pk, size=1.0)
        bmesh.ops.scale(bm_pk, vec=Vector(pk_size), verts=bm_pk.verts)
        bmesh.ops.rotate(bm_pk, cent=Vector((0, 0, 0)), matrix=mathutils.Matrix.Rotation(math.radians(sign * 25.0), 4, 'Z'), verts=bm_pk.verts)
        bmesh.ops.translate(bm_pk, verts=bm_pk.verts, vec=pk_pos + Vector((0, 0, pk_size[2] / 2.0)))
        finalize_bmesh(bm_pk, f"Core_Cover_Pocket_{side}", "CoreCover", ctx.get_material("cover"), ctx)

    s_size = cfg["south_screen_size"]
    s_pos = Vector((0.0, -14.0, core_z))
    bm_s = bmesh.new()
    bmesh.ops.create_cube(bm_s, size=1.0)
    bmesh.ops.scale(bm_s, vec=Vector(s_size), verts=bm_s.verts)
    bmesh.ops.translate(bm_s, verts=bm_s.verts, vec=s_pos + Vector((0, 0, s_size[2] / 2.0)))
    finalize_bmesh(bm_s, "Core_Cover_SouthScreen", "CoreCover", ctx.get_material("cover"), ctx)
''',

    "combat/ambush.py": '''import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

def generate_south_rift_ambush(ctx):
    south_mid = ctx.layout["SouthRift"]
    rift_z = get_height_at_point(south_mid, ctx.config, ctx.layout)
    
    offsets = [Vector((-6.0, 2.0, 0)), Vector((6.0, -2.0, 0))]
    for i, off in enumerate(offsets):
        r_pos = south_mid + off
        r_pos.z = rift_z
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=3.2)
        bmesh.ops.scale(bm, vec=Vector((1.4, 0.9, 1.1)), verts=bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts, vec=r_pos + Vector((0, 0, 1.5)))
        finalize_bmesh(bm, f"SouthRift_LoSRock_{i+1}", "Rocks", ctx.get_material("rock"), ctx)
''',

    "combat/sightlines.py": '''import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from core.layout import polar
from core.utils import finalize_bmesh

def audit_sightlines(ctx):
    if not ctx.config["debug_sightlines"]:
        return

    target_objs = [obj for obj in ctx.get_collection("CoreCover").objects] + [obj for obj in ctx.get_collection("Rocks").objects]
    if not target_objs:
        return

    depsgraph = bpy.context.evaluated_depsgraph_get()
    bmesh_eval = bmesh.new()
    for obj in target_objs:
        eval_obj = obj.evaluated_get(depsgraph)
        me = eval_obj.to_mesh()
        me.transform(obj.matrix_world)
        bmesh_eval.from_mesh(me)
        eval_obj.to_mesh_clear()

    bmesh_eval.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bmesh_eval)
    bmesh_eval.free()

    eye_offset = Vector((0, 0, 1.6))
    altar_pos = Vector((0, 0, ctx.config["heights"]["AetherCore"])) + Vector((0, 0, 0.8))

    test_rays = [
        ("Crown -> Altar", ctx.layout["Crown"] + eye_offset, altar_pos),
        ("WestChoke -> Altar", polar(ctx.config["center_radius"], 180.0) + eye_offset, altar_pos),
        ("EastChoke -> Altar", polar(ctx.config["center_radius"], 0.0) + eye_offset, altar_pos),
        ("SouthRift -> Altar", ctx.layout["SouthRift"] + eye_offset, altar_pos),
    ]

    for name, p_start, p_end in test_rays:
        direction = (p_end - p_start).normalized()
        distance = (p_end - p_start).length

        location, normal, index, dist = bvh.raycast(p_start, direction, distance)
        is_blocked = location is not None

        mat = ctx.get_material("ray_blocked") if is_blocked else ctx.get_material("ray_clear")
        _create_debug_ray_mesh(f"Ray_{name}_{'BLOCKED' if is_blocked else 'CLEAR'}", p_start, p_end, mat, ctx)

def _create_debug_ray_mesh(name, p0, p1, material, ctx):
    bm = bmesh.new()
    vec = p1 - p0
    length = vec.length
    
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.1, radius2=0.1, depth=length)
    
    up = Vector((0, 0, 1))
    target_dir = vec.normalized()
    rotation_quat = up.rotation_difference(target_dir)
    
    bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=rotation_quat.to_matrix().to_4x4(), verts=bm.verts)
    bmesh.ops.translate(bm, verts=bm.verts, vec=p0 + vec * 0.5)

    finalize_bmesh(bm, name, "DebugSightlines", material, ctx)
'''
}

# 1. Создание всех дирикторий и файлов
for rel_path, content in FILES_DATA.items():
    full_path = os.path.join(project_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Все файлы модулей успешно распакованы на диск!")

# 2. Добавляем папку в путь Python
if project_dir not in sys.path:
    sys.path.append(project_dir)

# 3. Запускаем генерацию карты напрямую
import core.config
import core.context
import core.utils
import core.layout
import core.heightmap
import visual.materials
import visual.decorations
import geometry.terrain
import geometry.core_geometry
import geometry.bases
import geometry.roads
import combat.combat_cover
import combat.ambush
import combat.sightlines

print("Строим карту...")
ctx = core.context.MapContext(core.config.CONFIG)
core.utils.clear_scene()
core.utils.setup_collections(ctx)
visual.materials.setup_materials(ctx)
ctx.layout = core.layout.build_layout(ctx.config)

geometry.terrain.generate_heightmapped_terrain(ctx)
geometry.core_geometry.generate_core_and_entrances(ctx)
geometry.bases.generate_capture_points(ctx)
geometry.bases.generate_bases(ctx)
geometry.roads.generate_roads(ctx)
visual.decorations.generate_speed_shrines_with_offset(ctx)
visual.decorations.generate_3_health_relics(ctx)
combat.combat_cover.generate_core_combat_cover(ctx)
combat.ambush.generate_south_rift_ambush(ctx)
combat.sightlines.audit_sightlines(ctx)

bpy.context.view_layer.update()
print("ГОТОВО! Вся карта сгенерирована!")