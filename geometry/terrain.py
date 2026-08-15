import bpy
import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point

def generate_heightmapped_terrain(ctx):
    cfg = ctx.config
    size = cfg["ground_half_size"]
    bm = bmesh.new()
    res = cfg.get("terrain_resolution", 52)  # Dominion x2.5: config-driven (was hardcoded 52); preserves original mesh density per meter at the new scale
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
