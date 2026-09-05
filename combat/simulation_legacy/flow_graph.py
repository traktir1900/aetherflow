# combat/simulation/flow_graph.py
import math

CROWN_WEIGHT = 110
MONOLITH_WEIGHT = 100
SOUTHRIFT_WEIGHT = 70
COVER_WEIGHT = 12

GRAPH_NODES = {
    "BlueBase": {"pos": [0.0, -110.0, 0.0], "danger": 0.0, "strategic_value": 0.0},
    "BlueMid": {"pos": [0.0, -55.0, 2.0], "danger": 1.0, "strategic_value": 30.0},
    "BlueWest": {"pos": [-45.0, -55.0, 0.0], "danger": 1.0, "strategic_value": 35.0},
    "BlueEast": {"pos": [45.0, -55.0, 0.0], "danger": 1.0, "strategic_value": 35.0},
    
    "RedBase": {"pos": [0.0, 110.0, 0.0], "danger": 0.0, "strategic_value": 0.0},
    "RedMid": {"pos": [0.0, 55.0, 2.0], "danger": 1.0, "strategic_value": 30.0},
    "RedWest": {"pos": [-45.0, 55.0, 0.0], "danger": 1.0, "strategic_value": 35.0},
    "RedEast": {"pos": [45.0, 55.0, 0.0], "danger": 1.0, "strategic_value": 35.0},

    "Crown": {"pos": [0.0, 0.0, 10.0], "danger": 3.0, "strategic_value": CROWN_WEIGHT},
    "WestMonolith": {"pos": [-65.0, 0.0, 5.0], "danger": 2.0, "strategic_value": MONOLITH_WEIGHT},
    "EastMonolith": {"pos": [65.0, 0.0, 5.0], "danger": 2.0, "strategic_value": MONOLITH_WEIGHT},
    "SouthRift": {"pos": [0.0, 0.0, -12.0], "danger": 2.5, "strategic_value": SOUTHRIFT_WEIGHT},
}

GRAPH_EDGES = [
    ("BlueBase", "BlueMid"), ("BlueBase", "BlueWest"), ("BlueBase", "BlueEast"),
    ("RedBase", "RedMid"), ("RedBase", "RedWest"), ("RedBase", "RedEast"),
    ("BlueMid", "Crown"), ("BlueMid", "SouthRift"), 
    ("RedMid", "Crown"), ("RedMid", "SouthRift"),
    ("BlueWest", "WestMonolith"), ("RedWest", "WestMonolith"),
    ("BlueEast", "EastMonolith"), ("RedEast", "EastMonolith"),
    ("WestMonolith", "Crown"), ("EastMonolith", "Crown"),
    ("SouthRift", "WestMonolith"), ("SouthRift", "EastMonolith")
]

def get_node(name):
    return GRAPH_NODES.get(name, GRAPH_NODES["Crown"])

def build_adjacency():
    adj = {k: [] for k in GRAPH_NODES.keys()}
    for n1, n2 in GRAPH_EDGES:
        adj[n1].append(n2)
        adj[n2].append(n1)
    return adj

def calculate_route_score(start, end, role, team="Blue"):
    node_a = get_node(start)
    node_b = get_node(end)
    
    dx = node_b["pos"][0] - node_a["pos"][0]
    dy = node_b["pos"][1] - node_a["pos"][1]
    dz = node_b["pos"][2] - node_a["pos"][2]
    
    dist_cost = math.sqrt(dx**2 + dy**2 + dz**2) 
    danger_cost = node_b["danger"]
    strategic_value = node_b["strategic_value"]
    
    role_multiplier = 1.0
    if role == "Flanker":
        if end in ["WestMonolith", "EastMonolith", "BlueWest", "RedWest", "BlueEast", "RedEast"]:
            role_multiplier = 5.0
    elif role == "Anchor":
        if end in ["SouthRift", "WestMonolith", "EastMonolith"]:
            role_multiplier = 4.0
    elif role == "Fighter":
        if end in ["Crown", "WestMonolith", "EastMonolith"]:
            role_multiplier = 4.0
            
    team_bias = 2.0
        
    route_score = (dist_cost * 0.05) + (danger_cost * 0.01) - (strategic_value * role_multiplier * team_bias * 4.5)
    return route_score

def get_best_path(start, target_zones, role, team="Blue"):
    adj = build_adjacency()
    queue = [(start, [start], 0.0)]
    visited = set()
    best_path = []
    best_score = float('inf')
    
    while queue:
        queue.sort(key=lambda x: x[2])
        curr, path, score = queue.pop(0)
        
        if curr in target_zones:
            if score < best_score:
                best_score = score
                best_path = path
            continue
            
        if curr in visited: continue
        visited.add(curr)
        
        for neighbor in adj[curr]:
            if neighbor not in visited:
                step_score = calculate_route_score(curr, neighbor, role, team)
                queue.append((neighbor, path + [neighbor], score + step_score))
                
    return best_path if best_path else [start]
