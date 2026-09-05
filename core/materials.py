"""
AetherFlow :: core/materials.py
Self-contained material setup for the procedural pipeline (no art pass —
simple PBR placeholders only; a real art pass is a later, separate stage).
"""
import bpy


def make_material(ctx, name, base_color, emission_color=None, emission_strength=0.0,
                  roughness=0.7, metallic=0.0):
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
    # Functional pocket floor: a lighter, distinct tone so each pocket reads as
    # ONE clear gameplay zone from the top-down view (readability, not decor).
    make_material(ctx, "pocket_floor", (0.34, 0.32, 0.28), roughness=0.85)
    make_material(ctx, "altar", (0.55, 0.45, 0.15), roughness=0.4, metallic=0.3)
    make_material(ctx, "altar_glow", (0.7, 0.4, 1.0),
                  emission_color=(0.7, 0.4, 1.0), emission_strength=4.0)
    make_material(ctx, "blue_team", (0.05, 0.25, 0.85),
                  emission_color=(0.1, 0.4, 1.0), emission_strength=1.2)
    make_material(ctx, "red_team", (0.85, 0.08, 0.08),
                  emission_color=(1.0, 0.15, 0.1), emission_strength=1.2)
    make_material(ctx, "blue_crystal", (0.1, 0.3, 0.9),
                  emission_color=(0.2, 0.5, 1.0), emission_strength=3.5)
    make_material(ctx, "red_crystal", (0.9, 0.1, 0.1),
                  emission_color=(1.0, 0.2, 0.15), emission_strength=3.5)

    # Height-tint debug material (visualization only, used by Terrain_Real).
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
