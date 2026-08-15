import bpy
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

        location, normal, index, dist = bvh.ray_cast(p_start, direction, distance)
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
