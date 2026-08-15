# combat/simulation/sim_visualizer.py
import bpy
import math

def setup_simulation_collections():
    base_name = "CombatSimulation_v3"
    base_col = bpy.data.collections.get(base_name)
    if not base_col:
        base_col = bpy.data.collections.new(base_name)
        bpy.context.scene.collection.children.link(base_col)
        
    sub_cols = ["Agents_Final", "MovementPaths", "CombatHotspots", "HeatMarkers"]
    cols = {}
    for name in sub_cols:
        c = bpy.data.collections.get(name)
        if not c:
            c = bpy.data.collections.new(name)
            base_col.children.link(c)
        else:
            for obj in list(c.objects):
                if isinstance(obj, bpy.types.Object):
                    bpy.data.objects.remove(obj, do_unlink=True)
        cols[name] = c
    return cols

def get_safe_material(name, color):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = next((node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
        if bsdf and 'Base Color' in bsdf.inputs:
            bsdf.inputs['Base Color'].default_value = color
    return mat

def draw_agent_paths(agents, collection):
    for agent in agents:
        curve_data = bpy.data.curves.new(name=f"PathData_{agent['id']}", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.2
        color = (0.0, 0.4, 1.0, 1.0) if agent['team'] == 'Blue' else (1.0, 0.1, 0.1, 1.0)
        mat = get_safe_material(f"Mat_Path_{agent['team']}", color)
        curve_data.materials.append(mat)

        spline = curve_data.splines.new('POLY')
        spline.points.add(len(agent["path_history"]) - 1)
        for i, pt in enumerate(agent["path_history"]):
            spline.points[i].co = (pt[0], pt[1], pt[2], 1)
            
        curve_obj = bpy.data.objects.new(f"Path_{agent['id']}_{agent['role']}", curve_data)
        collection.objects.link(curve_obj)

def draw_hotspots(events, collection):
    unique_hotspots = []
    for h in events:
        if not any(math.sqrt((h[0]-u[0])**2 + (h[1]-u[1])**2 + (h[2]-u[2])**2) < 3.0 for u in unique_hotspots):
            unique_hotspots.append(h)
            
    mat = get_safe_material("Mat_Hotspot", (1.0, 0.5, 0.0, 0.8))
    for idx, pos in enumerate(unique_hotspots):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=2.0, location=(pos[0], pos[1], pos[2]))
        obj = bpy.context.active_object
        obj.name = f"Hotspot_{idx}"
        if obj.data.materials: obj.data.materials[0] = mat
        else: obj.data.materials.append(mat)
        
        for coll in list(obj.users_collection):
            if hasattr(coll, "objects") and obj.name in coll.objects:
                coll.objects.unlink(obj)
        collection.objects.link(obj)
