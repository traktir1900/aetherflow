import bpy

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
    names = [
        "Terrain", "Bases", "CapturePoints", "Roads", 
        "Decorations", "Rocks", "CoreCover", 
        "DebugSightlines", "CombatAnalysis", "ThreatMarkers",
        "CoverCandidates", "ApprovedCovers", "RejectedCovers"
    ]
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
