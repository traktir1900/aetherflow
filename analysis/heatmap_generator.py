import bpy
import bmesh
from mathutils import Vector
from core.logger import log

def get_graph_path(graph, start, end):
    """Универсальный вызов поиска пути в NavigationGraph."""
    if hasattr(graph, "get_shortest_path"):
        return graph.get_shortest_path(start, end)
    elif hasattr(graph, "find_shortest_path"):
        return graph.find_shortest_path(start, end)
    elif hasattr(graph, "a_star"):
        return graph.a_star(start, end)
    return []

def calculate_heatmap_data(graph, open_corridors):
    """Рассчитывает трафик, интенсивность боя и опасные зоны."""
    nodes = graph.nodes
    traffic_density = {name: 0.0 for name in nodes}
    combat_intensity = {name: 0.0 for name in nodes}
    danger_zones = {name: 0.0 for name in nodes}

    # 1. Плотность трафика (A* Routes)
    node_names = list(nodes.keys())
    for i in range(len(node_names)):
        for j in range(i + 1, len(node_names)):
            path = get_graph_path(graph, node_names[i], node_names[j])
            if path:
                for node_name in path:
                    if node_name in traffic_density:
                        traffic_density[node_name] += 1.0

    # 2. Опасность прострелов (Danger Zones по данным Sniper Corridors)
    if open_corridors:
        for u, v, dist in open_corridors:
            weight = dist / 40.0 # Чем длиннее коридор, тем выше опасность
            if u in danger_zones:
                danger_zones[u] += weight
            if v in danger_zones:
                danger_zones[v] += weight

    # 3. Интенсивность боя (Combat Intensity = Traffic + Exposure Danger)
    for name in nodes:
        combat_intensity[name] = traffic_density[name] * 0.6 + danger_zones[name] * 0.4
        
    # Буст контрольных точек
    for key in ["AetherCore", "Crown", "WestMonolith", "EastMonolith"]:
        if key in combat_intensity:
            combat_intensity[key] *= 1.25

    return traffic_density, combat_intensity, danger_zones

def run_heatmap_generation(ctx):
    log.info("Running Combat & Navigation Heatmap Analysis (Task #0.4.4)...")
    
    graph = getattr(ctx, "nav_graph", None)
    sightline_result = getattr(ctx, "sightline_result", None)
    
    if not graph:
        log.error("Navigation Graph not found in Context! Run Task #0.4.2 first.")
        return

    open_corridors = []
    if sightline_result and hasattr(sightline_result, "open_corridors"):
        open_corridors = sightline_result.open_corridors
    
    traffic, combat, danger = calculate_heatmap_data(graph, open_corridors)
    
    # Отчет в консоль
    print("\n" + "="*45)
    print(" AETHERFLOW COMBAT HEATMAP REPORT ")
    print("="*45)
    
    print("[TRAFFIC DENSITY]")
    print(f"  Blue Base -> Center: {'High' if traffic.get('CenterSouth', 0) > 10 else 'Normal'}")
    print(f"  Red Base -> Center:  {'High' if traffic.get('CenterNorth', 0) > 10 else 'Normal'}")
    
    print("\n[COMBAT HOTSPOTS]")
    for obj in ["AetherCore", "WestMonolith", "EastMonolith"]:
        val = combat.get(obj, 0.0)
        level = "HIGH 🔴" if val > 15 else ("MEDIUM 🟡" if val > 8 else "LOW 🔵")
        print(f"  {obj:<15}: {level}")

    print("\n[OPEN FIELD WARNING]")
    north_danger = danger.get("CenterNorth", 0.0) + danger.get("NorthWestNode", 0.0)
    south_danger = danger.get("CenterSouth", 0.0) + danger.get("SouthWestNode", 0.0)
    print(f"  North Corridor: {'NEED COVER ⚠' if north_danger > 5.0 else 'ACCEPTABLE ✓'}")
    print(f"  South Corridor: {'NEED COVER ⚠' if south_danger > 5.0 else 'ACCEPTABLE ✓'}")

    # Аудит баланса тепловой карты между сторонами
    blue_side_heat = combat.get("BlueEntrance", 0) + combat.get("SouthWestNode", 0) + combat.get("SouthEastNode", 0)
    red_side_heat = combat.get("RedEntrance", 0) + combat.get("NorthWestNode", 0) + combat.get("NorthEastNode", 0)
    heat_diff = abs(blue_side_heat - red_side_heat)

    print("-" * 45)
    print("[HEAT BALANCE AUDIT]")
    print(f"  Blue Sector Heat Index: {blue_side_heat:.1f}")
    print(f"  Red Sector Heat Index:  {red_side_heat:.1f}")
    print(f"  Heat Delta:             {heat_diff:.1f}")
    
    if heat_diff <= 2.0:
        print("  STATUS:                 ✓ BALANCED")
    else:
        print("  STATUS:                 ⚠ UNBALANCED HEATMAP")
    print("="*45 + "\n")

    generate_heatmap_visual_layers(graph, traffic, combat, danger)

def create_heatmap_submesh(bm, center, color, radius=2.5):
    """Вспомогательная функция построения локального полигона тепловой карты."""
    color_layer = bm.loops.layers.color.get("HeatColor")
    if not color_layer:
        color_layer = bm.loops.layers.color.new("HeatColor")
        
    v1 = bm.verts.new(center + Vector((-radius, -radius, 0.1)))
    v2 = bm.verts.new(center + Vector((radius, -radius, 0.1)))
    v3 = bm.verts.new(center + Vector((radius, radius, 0.1)))
    v4 = bm.verts.new(center + Vector((-radius, radius, 0.1)))
    
    face = bm.faces.new((v1, v2, v3, v4))
    for loop in face.loops:
        loop[color_layer] = color

def generate_heatmap_visual_layers(graph, traffic, combat, danger):
    """Создает иерархию коллекций Debug/Heatmap/... и визуальные оверлеи."""
    debug_col = bpy.data.collections.get("Debug")
    if not debug_col:
        debug_col = bpy.data.collections.new("Debug")
        bpy.context.scene.collection.children.link(debug_col)

    heatmap_root = bpy.data.collections.get("Heatmap")
    if not heatmap_root:
        heatmap_root = bpy.data.collections.new("Heatmap")
        debug_col.children.link(heatmap_root)

    sub_layers = ["TrafficDensity", "CombatIntensity", "DangerZones"]
    sub_cols = {}
    for layer_name in sub_layers:
        col = bpy.data.collections.get(layer_name)
        if not col:
            col = bpy.data.collections.new(layer_name)
            heatmap_root.children.link(col)
        sub_cols[layer_name] = col

    for layer_name in sub_layers:
        old_obj = bpy.data.objects.get(f"Overlay_{layer_name}")
        if old_obj:
            bpy.data.objects.remove(old_obj, do_unlink=True)

    nodes = graph.nodes
    max_tr = max(traffic.values()) if traffic.values() and max(traffic.values()) > 0 else 1.0
    max_cm = max(combat.values()) if combat.values() and max(combat.values()) > 0 else 1.0
    max_dn = max(danger.values()) if danger.values() and max(danger.values()) > 0 else 1.0

    # 1. Traffic Density Mesh
    bm_tr = bmesh.new()
    for name, node in nodes.items():
        val = traffic.get(name, 0.0) / max_tr
        color = (0.0, val, 1.0, 1.0)
        create_heatmap_submesh(bm_tr, node.position, color)
    mesh_tr = bpy.data.meshes.new("TrafficMesh")
    bm_tr.to_mesh(mesh_tr)
    bm_tr.free()
    obj_tr = bpy.data.objects.new("Overlay_TrafficDensity", mesh_tr)
    sub_cols["TrafficDensity"].objects.link(obj_tr)

    # 2. Combat Intensity Mesh
    bm_cm = bmesh.new()
    for name, node in nodes.items():
        val = combat.get(name, 0.0) / max_cm
        color = (1.0, 1.0 - val, 0.0, 1.0)
        create_heatmap_submesh(bm_cm, node.position, color)
    mesh_cm = bpy.data.meshes.new("CombatMesh")
    bm_cm.to_mesh(mesh_cm)
    bm_cm.free()
    obj_cm = bpy.data.objects.new("Overlay_CombatIntensity", mesh_cm)
    sub_cols["CombatIntensity"].objects.link(obj_cm)

    # 3. Danger Zones Mesh
    bm_dn = bmesh.new()
    for name, node in nodes.items():
        val = danger.get(name, 0.0) / max_dn
        color = (val, 0.0, val, 1.0)
        create_heatmap_submesh(bm_dn, node.position, color)
    mesh_dn = bpy.data.meshes.new("DangerMesh")
    bm_dn.to_mesh(mesh_dn)
    bm_dn.free()
    obj_dn = bpy.data.objects.new("Overlay_DangerZones", mesh_dn)
    sub_cols["DangerZones"].objects.link(obj_dn)
