import math
import bpy
from mathutils import Vector
from core.logger import log

MOVEMENT_PROFILE = {
    "base_speed": 6.0,  # м/с
    "slope_penalty": {
        "flat": 1.0,     # 0-5 deg
        "medium": 0.85,  # 5-12 deg
        "steep": 0.65   # 12-25 deg
    },
    "downhill_bonus": 1.05
}

CHOKE_PROFILE = {
    "CenterSouth": {"width": 5.0, "traffic_penalty": 0.85},
    "CenterNorth": {"width": 5.0, "traffic_penalty": 0.85},
    "AetherCore":  {"width": 8.0, "traffic_penalty": 0.95},
    "BlueEntrance": {"width": 6.0, "traffic_penalty": 0.90},
    "RedEntrance":  {"width": 6.0, "traffic_penalty": 0.90}
}

KEY_OBJECTIVES = ["BlueBase", "WestMonolith", "EastMonolith", "Crown", "AetherCore", "RedBase"]

class TraversalEdge:
    def __init__(self, start_node, end_node):
        self.start_node = start_node
        self.end_node = end_node
        
        pos1 = start_node.position
        pos2 = end_node.position
        
        self.distance = (pos2 - pos1).length
        self.height_delta = pos2.z - pos1.z
        
        horizontal_dist = math.sqrt((pos2.x - pos1.x)**2 + (pos2.y - pos1.y)**2)
        if horizontal_dist > 0.0001:
            self.slope_angle = math.degrees(math.atan(abs(self.height_delta) / horizontal_dist))
        else:
            self.slope_angle = 90.0 if self.height_delta != 0 else 0.0

        if self.height_delta > 0.1:  # Подъем
            if self.slope_angle <= 5.0:
                slope_mult = MOVEMENT_PROFILE["slope_penalty"]["flat"]
            elif self.slope_angle <= 12.0:
                slope_mult = MOVEMENT_PROFILE["slope_penalty"]["medium"]
            elif self.slope_angle <= 25.0:
                slope_mult = MOVEMENT_PROFILE["slope_penalty"]["steep"]
            else:
                slope_mult = 0.0  # Заблокировано
        elif self.height_delta < -0.1:  # Спуск
            slope_mult = MOVEMENT_PROFILE["downhill_bonus"]
        else:
            slope_mult = 1.0

        choke_mult = 1.0
        target_choke = CHOKE_PROFILE.get(end_node.name) or CHOKE_PROFILE.get(start_node.name)
        if target_choke:
            choke_mult = target_choke["traffic_penalty"]

        self.speed_multiplier = slope_mult * choke_mult
        self.effective_speed = MOVEMENT_PROFILE["base_speed"] * self.speed_multiplier
        self.traversal_time = self.distance / self.effective_speed if self.effective_speed > 0 else float('inf')

class TraversalPathResult:
    def __init__(self, path_nodes, nav_graph):
        self.path_nodes = path_nodes
        self.edges = []
        self.total_distance = 0.0
        self.total_height_change = 0.0
        self.total_time = 0.0

        for i in range(len(path_nodes) - 1):
            n1 = nav_graph.nodes[path_nodes[i]]
            n2 = nav_graph.nodes[path_nodes[i+1]]
            edge = TraversalEdge(n1, n2)
            self.edges.append(edge)
            
            self.total_distance += edge.distance
            self.total_height_change += edge.height_delta
            self.total_time += edge.traversal_time

        self.average_speed = self.total_distance / self.total_time if self.total_time > 0 else 0.0

def run_traversal_analysis(ctx):
    log.info("Running Real Traversal Analysis (Task #0.4.2)...")
    graph = ctx.nav_graph
    
    blue_path, _ = graph.find_path_a_star("BlueBase", "AetherCore")
    red_path, _ = graph.find_path_a_star("RedBase", "AetherCore")
    
    blue_res = TraversalPathResult(blue_path, graph) if blue_path else None
    red_res = TraversalPathResult(red_path, graph) if red_path else None

    blue_crown_path, _ = graph.find_path_a_star("BlueBase", "Crown")
    red_crown_path, _ = graph.find_path_a_star("RedBase", "Crown")
    
    blue_crown_res = TraversalPathResult(blue_crown_path, graph) if blue_crown_path else None
    red_crown_res = TraversalPathResult(red_crown_path, graph) if red_crown_path else None

    print("\n" + "="*45)
    print(" AETHERFLOW REAL TRAVERSAL REPORT ")
    print("="*45)
    print(f"Movement Profile:\n  Base Speed: {MOVEMENT_PROFILE['base_speed']} m/s\n")

    if blue_res:
        print("[BLUE BASE -> AETHER CORE]")
        print(f"  Route:          {' > '.join(blue_res.path_nodes)}")
        print(f"  Distance:       {blue_res.total_distance:.2f}m")
        print(f"  Height Change:  {blue_res.total_height_change:+.1f}m")
        print(f"  Average Speed:  {blue_res.average_speed:.2f} m/s")
        print(f"  Travel Time:    {blue_res.total_time:.2f} sec")
        print("-" * 45)

    matrix = {}
    for start in KEY_OBJECTIVES:
        matrix[start] = {}
        for goal in KEY_OBJECTIVES:
            if start == goal:
                matrix[start][goal] = 0.0
            else:
                p, _ = graph.find_path_a_star(start, goal)
                if p:
                    res = TraversalPathResult(p, graph)
                    matrix[start][goal] = res.total_time
                else:
                    matrix[start][goal] = float('inf')

    print("\n[FULL ROTATION MATRIX (TRAVEL TIME IN SECONDS)]")
    header = f"{'From/To':<14} | " + " | ".join([f"{obj[:6]:<6}" for obj in KEY_OBJECTIVES])
    print(header)
    print("-" * len(header))
    for start in KEY_OBJECTIVES:
        row = f"{start:<14} | " + " | ".join([f"{matrix[start][g]:6.1f}" for g in KEY_OBJECTIVES])
        print(row)

    print("-" * 45)
    print("[ROTATION BALANCE AUDIT]")
    b_time = blue_crown_res.total_time if blue_crown_res else 0.0
    r_time = red_crown_res.total_time if red_crown_res else 0.0
    diff = abs(b_time - r_time)
    
    print(f"  Blue Base -> Crown: {b_time:.2f} sec")
    print(f"  Red Base -> Crown:  {r_time:.2f} sec")
    print(f"  Difference:         {diff:.2f} sec")
    
    if diff <= 0.5:
        print("  STATUS:             ✓ BALANCED")
    else:
        print("  STATUS:             ⚠ UNBALANCED")
    print("="*45 + "\n")

    visualize_debug_traversal(ctx, graph)

def visualize_debug_traversal(ctx, graph):
    col = ctx.get_collection("Traversal") if hasattr(ctx, "get_collection") else None
    if not col:
        debug_col = bpy.data.collections.get("Debug")
        if not debug_col:
            debug_col = bpy.data.collections.new("Debug")
            bpy.context.scene.collection.children.link(debug_col)
        
        col = bpy.data.collections.get("Traversal")
        if not col:
            col = bpy.data.collections.new("Traversal")
            debug_col.children.link(col)

    old_obj = bpy.data.objects.get("Traversal_Debug_Overlay")
    if old_obj:
        bpy.data.objects.remove(old_obj, do_unlink=True)

    mesh = bpy.data.meshes.new("TraversalDebugMesh")
    obj = bpy.data.objects.new("Traversal_Debug_Overlay", mesh)
    col.objects.link(obj)

    import bmesh
    bm = bmesh.new()
    node_verts = {}

    for name, node in graph.nodes.items():
        v = bm.verts.new(node.position + Vector((0, 0, 0.2)))
        node_verts[name] = v

    bm.verts.ensure_lookup_table()

    created_edges = set()
    for name, node in graph.nodes.items():
        for neighbor in node.neighbors:
            edge_key = tuple(sorted([name, neighbor]))
            if edge_key not in created_edges:
                v1 = node_verts[name]
                v2 = node_verts[neighbor]
                if not bm.edges.get((v1, v2)):
                    bm.edges.new((v1, v2))
                created_edges.add(edge_key)

    bm.to_mesh(mesh)
    bm.free()
