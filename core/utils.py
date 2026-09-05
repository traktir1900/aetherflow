"""
AetherFlow :: core/utils.py
Scene helpers with SAFE generation semantics + real object transforms.

clear_scene() is destructive.  It is gated by config["scene"]["allow_scene_reset"]
(default False) so a manual .blend — including the Aether Altar, Aether Crown,
user assets and hand-placed objects — is never erased unless the operator
explicitly enables a full reset in a dedicated procedural scene.

By default the pipeline runs in SAFE_UPDATE mode: only the managed AetherFlow
collections are cleared, everything else is left untouched.

finalize_bmesh() re-bases every mesh around its centroid and stores the
centroid in obj.location, so every generated object carries a REAL world
transform.  Export, navigation blockers and validation all rely on this.
"""
import bpy
from mathutils import Vector, Matrix

from core.config import CONFIG


def _managed_names():
    return CONFIG.get("scene", {}).get("managed_collections", [])


def clear_scene(ctx):
    """
    SAFE_UPDATE (default): remove only objects inside the managed AetherFlow
    collections.  User content outside them is preserved.

    GENERATE_NEW_SCENE: full wipe — only when config["scene"]["allow_scene_reset"]
    is explicitly True.
    """
    scene_cfg = CONFIG.get("scene", {})
    allow_full_reset = bool(scene_cfg.get("allow_scene_reset", False))

    if allow_full_reset:
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for mesh in list(bpy.data.meshes):
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for mat in list(bpy.data.materials):
            if mat.users == 0:
                bpy.data.materials.remove(mat)
        print("[SCENE] GENERATE_NEW_SCENE: full reset performed (explicitly allowed).")
        return

    removed = 0
    for name in _managed_names():
        coll = bpy.data.collections.get(name)
        if not coll:
            continue
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    print("[SCENE] SAFE_UPDATE: cleared {} objects in managed collections "
          "(user scene preserved).".format(removed))


def setup_collections(ctx):
    for name in _managed_names():
        coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if coll.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(coll)
        ctx.collections[name] = coll


def finalize_bmesh(bm, name, collection_key, material, ctx, kind="prop", dims=None, meta=None):
    """Turn a bmesh into a real object with a real transform, then register it
    for export / navigation / validation."""
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # Re-base around the centroid so obj.location carries the true world
    # position (previously everything lived at the origin with baked verts).
    n = len(mesh.vertices)
    if n:
        cx = sum(v.co.x for v in mesh.vertices) / n
        cy = sum(v.co.y for v in mesh.vertices) / n
        cz = sum(v.co.z for v in mesh.vertices) / n
        mesh.transform(Matrix.Translation(Vector((-cx, -cy, -cz))))
        mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    if n:
        obj.location = Vector((cx, cy, cz))
    ctx.get_collection(collection_key).objects.link(obj)
    if material:
        obj.data.materials.append(material)
    ctx.register(obj, kind, dims=dims, meta=meta)
    return obj
