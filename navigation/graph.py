import math
import heapq
import bpy
from mathutils import Vector
from core.logger import log

class Node:
    def __init__(self, name, position, node_type="waypoint"):
        self.name = name
        self.position = Vector(position)
        self.node_type = node_type
        self.neighbors = {}  # {neighbor_name: weight}

    def add_neighbor(self, neighbor_name, weight):
        self.neighbors[neighbor_name] = weight

class NavigationGraph:
    def __init__(self):
        self.nodes = {}

    def add_node(self, name, position, node_type="waypoint"):
        if name not in self.nodes:
            self.nodes[name] = Node(name, position, node_type)
        return self.nodes[name]

    def add_edge(self, name1, name2, bidirectional=True, custom_weight=None):
        if name1 not in self.nodes or name2 not in self.nodes:
            log.warning(f"Cannot link missing nodes: {name1} <-> {name2}")
            return
        
        pos1 = self.nodes[name1].position
        pos2 = self.nodes[name2].position
        weight = custom_weight if custom_weight is not None else (pos1 - pos2).length
        
        self.nodes[name1].add_neighbor(name2, weight)
        if bidirectional:
            self.nodes[name2].add_neighbor(name1, weight)

    def find_path_a_star(self, start_name, goal_name):
        if start_name not in self.nodes or goal_name not in self.nodes:
            return None, float('inf')

        start_node = self.nodes[start_name]
        goal_node = self.nodes[goal_name]

        open_set = []
        heapq.heappush(open_set, (0, start_name))

        came_from = {}
        g_score = {name: float('inf') for name in self.nodes}
        g_score[start_name] = 0

        f_score = {name: float('inf') for name in self.nodes}
        f_score[start_name] = (start_node.position - goal_node.position).length

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal_name:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path, g_score[goal_name]

            for neighbor, weight in self.nodes[current].neighbors.items():
                tentative_g = g_score[current] + weight
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + (self.nodes[neighbor].position - goal_node.position).length
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None, float('inf')

def build_aetherflow_nav_graph(ctx):
    log.info("Building Navigation Graph (Task #0.4.1/0.4.2)...")
    graph = NavigationGraph()

    out_r = ctx.config.get("outer_ring_radius", 88.0) if hasattr(ctx, "config") else 88.0
    
    nodes_data = [
        ("BlueBase", (0.0, -out_r, 4.0), "base"),
        ("BlueEntrance", (0.0, -out_r * 0.75, 4.0), "choke"),
        ("SouthWestNode", (-out_r * 0.5, -out_r * 0.5, 4.0), "waypoint"),
        ("SouthEastNode", (out_r * 0.5, -out_r * 0.5, 4.0), "waypoint"),
        ("CenterSouth", (0.0, -out_r * 0.25, 5.0), "choke"),
        ("AetherCore", (0.0, 0.0, 6.0), "objective"),
        ("Crown", (0.0, 0.0, 6.0), "objective"),
        ("CenterNorth", (0.0, out_r * 0.25, 5.0), "choke"),
        ("NorthWestNode", (-out_r * 0.5, out_r * 0.5, 4.0), "waypoint"),
        ("NorthEastNode", (out_r * 0.5, out_r * 0.5, 4.0), "waypoint"),
        ("RedEntrance", (0.0, out_r * 0.75, 4.0), "choke"),
        ("RedBase", (0.0, out_r, 4.0), "base"),
        ("WestMonolith", (-out_r, 0.0, 4.0), "objective"),
        ("EastMonolith", (out_r, 0.0, 4.0), "objective")
    ]

    for name, pos, n_type in nodes_data:
        graph.add_node(name, pos, n_type)

    edges_data = [
        ("BlueBase", "BlueEntrance"),
        ("BlueEntrance", "SouthWestNode"),
        ("BlueEntrance", "SouthEastNode"),
        ("SouthWestNode", "WestMonolith"),
        ("SouthEastNode", "EastMonolith"),
        ("SouthWestNode", "CenterSouth"),
        ("SouthEastNode", "CenterSouth"),
        ("CenterSouth", "AetherCore"),
        ("AetherCore", "Crown"),
        ("AetherCore", "CenterNorth"),
        ("CenterNorth", "NorthWestNode"),
        ("CenterNorth", "NorthEastNode"),
        ("WestMonolith", "NorthWestNode"),
        ("EastMonolith", "NorthEastNode"),
        ("NorthWestNode", "RedEntrance"),
        ("NorthEastNode", "RedEntrance"),
        ("RedEntrance", "RedBase")
    ]

    for u, v in edges_data:
        graph.add_edge(u, v)

    ctx.nav_graph = graph
    log.info(f"Navigation Graph constructed with {len(graph.nodes)} nodes.")
    return graph
