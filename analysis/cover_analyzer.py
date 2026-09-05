import bpy
from mathutils import Vector
from core.logger import log

EYE_HEIGHT = Vector((0.0, 0.0, 1.6))  # Уровень глаз персонажа (1.6м)

KEY_TARGETS = ["AetherCore", "Crown", "WestMonolith", "EastMonolith"]

def perform_raycast(depsgraph, origin, target):
    """Выполняет Raycast с учетом оффсета высоты глаз."""
    ray_origin = origin + EYE_HEIGHT
    ray_target = target + EYE_HEIGHT
    direction = ray_target - ray_origin
    distance = direction.length
    
    if distance < 0.001:
        return False, None, 0.0
        
    direction.normalize()
    
    # Raycast по сцене Blender
    hit, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(
        depsgraph, 
        ray_origin, 
        direction, 
        distance=distance
    )
    
    return hit, location, distance

class SightlineAnalysisResult:
    def __init__(self):
        self.sightlines = []
        self.open_corridors = []
        self.cover_exposure = {}

def run_cover_analysis(ctx):
    log.info("Running Cover & Sightline Analysis (Task #0.4.3)...")
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    graph = getattr(ctx, "nav_graph", None)
    
    if not graph:
        log.error("Navigation Graph not found in Context! Run Task #0.4.2 first.")
        return

    result = SightlineAnalysisResult()
    nodes = graph.nodes
    node_names = list(nodes.keys())

    # 1. Проверка прямых прострелов между всеми узлами
    blocked_count = 0
    open_count = 0

    print("\n" + "="*45)
    print(" AETHERFLOW COVER & SIGHTLINE REPORT ")
    print("="*45)

    for i in range(len(node_names)):
        for j in range(i + 1, len(node_names)):
            name1, name2 = node_names[i], node_names[j]
            pos1, pos2 = nodes[name1].position, nodes[name2].position
            
            hit, hit_loc, dist = perform_raycast(depsgraph, pos1, pos2)
            
            if hit:
                blocked_count += 1
            else:
                open_count += 1
                if dist > 40.0:  # Длинный открытый коридор (>40м)
                    result.open_corridors.append((name1, name2, dist))

    # 2. Анализ экспозиции (защищенности) ключевых объектов
    print("\n[OBJECTIVE COVER EXPOSURE AUDIT]")
    print(f"{'Objective':<15} | {'Threat Vectors':<15} | {'Blocked':<8} | {'Exposure Rate'}")
    print("-" * 55)

    exposure_data = {}
    for target_name in KEY_TARGETS:
        if target_name not in nodes:
            continue
            
        target_pos = nodes[target_name].position
        total_vectors = 0
        blocked_vectors = 0
        
        for name, node in nodes.items():
            if name == target_name:
                continue
            
            total_vectors += 1
            hit, _, _ = perform_raycast(depsgraph, target_pos, node.position)
            if hit:
                blocked_vectors += 1

        exposure_percentage = ((total_vectors - blocked_vectors) / total_vectors * 100) if total_vectors > 0 else 0.0
        exposure_data[target_name] = exposure_percentage
        
        print(f"{target_name:<15} | {total_vectors:<15} | {blocked_vectors:<8} | {exposure_percentage:.1f}% open")

    # 3. Анализ снайперских коридоров
    print("-" * 45)
    print("[LONG SIGHTLINES / SNIPER CORRIDORS (>40m)]")
    if result.open_corridors:
        for u, v, d in result.open_corridors:
            print(f"  ⚠ {u} <---> {v} ({d:.1f}m open)")
    else:
        print("  ✓ No long open corridors detected.")

    # 4. Аудит симметрии укрытий между флангами
    west_exp = exposure_data.get("WestMonolith", 0.0)
    east_exp = exposure_data.get("EastMonolith", 0.0)
    flank_diff = abs(west_exp - east_exp)

    print("-" * 45)
    print("[COVER BALANCE AUDIT]")
    print(f"  West Monolith Exposure: {west_exp:.1f}%")
    print(f"  East Monolith Exposure: {east_exp:.1f}%")
    print(f"  Flank Cover Delta:      {flank_diff:.1f}%")

    if flank_diff <= 5.0:
        print("  STATUS:                 ✓ BALANCED COVER")
    else:
        print("  STATUS:                 ⚠ UNBALANCED FLANKS")
    print("="*45 + "\n")

    visualize_sightlines(ctx, graph, depsgraph)

def visualize_sightlines(ctx, graph, depsgraph):
    """Визуализация прямых прострелов в Blender."""
    col = bpy.data.collections.get("Debug")
    if not col:
        col = bpy.data.collections.new("Debug")
        bpy.context.scene.collection.children.link(col)

    sight_col = bpy.data.collections.get("Sightlines")
    if not sight_col:
        sight_col = bpy.data.collections.new("Sightlines")
        col.children.link(sight_col)

    old_obj = bpy.data.objects.get("Sightlines_Debug_Overlay")
    if old_obj:
        bpy.data.objects.remove(old_obj, do_unlink=True)

    mesh = bpy.data.meshes.new("SightlinesDebugMesh")
    obj = bpy.data.objects.new("Sightlines_Debug_Overlay", mesh)
    sight_col.objects.link(obj)

    import bmesh
    bm = bmesh.new()
    nodes = graph.nodes
    node_names = list(nodes.keys())

    for i in range(len(node_names)):
        for j in range(i + 1, len(node_names)):
            name1, name2 = node_names[i], node_names[j]
            p1, p2 = nodes[name1].position, nodes[name2].position
            
            hit, _, dist = perform_raycast(depsgraph, p1, p2)
            
            # Рисуем только открытые линии прострела
            if not hit and dist > 20.0:
                v1 = bm.verts.new(p1 + EYE_HEIGHT)
                v2 = bm.verts.new(p2 + EYE_HEIGHT)
                bm.edges.new((v1, v2))

    bm.to_mesh(mesh)
    bm.free()
