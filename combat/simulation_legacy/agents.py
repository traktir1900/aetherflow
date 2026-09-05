# combat/simulation/agents.py
import math
from .flow_graph import get_node, get_best_path

BLUE_TEAM = [
    ("B1", "Fighter"), ("B2", "Fighter"), 
    ("B3", "Anchor"), 
    ("B4", "Flanker"), ("B5", "Flanker")
]
RED_TEAM = [
    ("R1", "Fighter"), ("R2", "Fighter"), 
    ("R3", "Anchor"), 
    ("R4", "Flanker"), ("R5", "Flanker")
]

FRIENDLY_OCCUPANCY_PENALTY = 0.5
ENEMY_PRESSURE_BONUS = 90.0

def evaluate_live_objectives(agent, agents, all_nodes, objective_states, time_sec):
    role = agent["role"]
    team = agent["team"]
    pos = agent["coord"]
    
    candidates = ["Crown", "WestMonolith", "EastMonolith", "SouthRift"]
    
    best_obj = candidates[0]
    best_score = -float('inf')
    
    for obj_name in candidates:
        if obj_name not in all_nodes: continue
        node_pos = all_nodes[obj_name]["pos"]
        base_val = all_nodes[obj_name]["strategic_value"]
        obj_state = objective_states.get(obj_name, {"owner": "Neutral", "status": "Neutral"})
        
        dist = math.sqrt((pos[0]-node_pos[0])**2 + (pos[1]-node_pos[1])**2 + (pos[2]-node_pos[2])**2)
        
        friendly_count = sum(1 for a in agents if a["team"] == team and math.sqrt((a["coord"][0]-node_pos[0])**2 + (a["coord"][1]-node_pos[1])**2 + (a["coord"][2]-node_pos[2])**2) < 45.0)
        enemy_count = sum(1 for a in agents if a["team"] != team and math.sqrt((a["coord"][0]-node_pos[0])**2 + (a["coord"][1]-node_pos[1])**2 + (a["coord"][2]-node_pos[2])**2) < 45.0)
        
        role_weight = 1.0
        if role == "Fighter":
            if obj_name in ["Crown", "WestMonolith", "EastMonolith"]: role_weight = 3.5
        elif role == "Anchor":
            if obj_name in ["SouthRift", "WestMonolith", "EastMonolith"]: role_weight = 3.5
        elif role == "Flanker":
            if obj_name in ["WestMonolith", "EastMonolith"]: role_weight = 4.5
            
        # Более динамичное распределение сбалансированное под перекрестный маятник
        dynamic_bias = math.sin(time_sec * 0.02 + (ord(agent["id"][1]) * 0.6)) * 45.0
        
        ownership_incentive = 0.0
        if obj_state["owner"] != team:
            ownership_incentive = 95.0  # Повышенный стимул атаковать неподконтрольные зоны
        elif enemy_count > 0:
            ownership_incentive = 55.0
            
        score = (base_val * role_weight) + (enemy_count * ENEMY_PRESSURE_BONUS) + dynamic_bias + ownership_incentive - (friendly_count * FRIENDLY_OCCUPANCY_PENALTY) - (dist * 0.03)
        
        if score > best_score:
            best_score = score
            best_obj = obj_name
            
    return best_obj

def update_combat_state(agent, agents):
    pos = agent["coord"]
    team = agent["team"]
    
    nearby_enemies = [a for a in agents if a["team"] != team and math.sqrt((a["coord"][0]-pos[0])**2 + (a["coord"][1]-pos[1])**2 + (a["coord"][2]-pos[2])**2) < 22.0]
    nearby_friends = [a for a in agents if a["team"] == team and math.sqrt((a["coord"][0]-pos[0])**2 + (a["coord"][1]-pos[1])**2 + (a["coord"][2]-pos[2])**2) < 22.0]
    
    enemy_count = len(nearby_enemies)
    friend_count = len(nearby_friends)
    
    if enemy_count > 0:
        agent["in_combat"] = True
        if enemy_count > friend_count + 3:
            agent["state"] = "RETREAT"
        elif enemy_count >= friend_count:
            agent["state"] = "CONTEST"
        else:
            agent["state"] = "ATTACK"
    else:
        agent["in_combat"] = False
        if agent["route_idx"] < len(agent.get("route_plan", [])):
            agent["state"] = "MARCH"
        else:
            agent["state"] = "DEFEND"

def create_agents():
    agents = []
    
    for idx, (aid, role) in enumerate(BLUE_TEAM):
        start_node = get_node("BlueBase")
        start_pos = start_node["pos"].copy()
        start_pos[0] += (idx - 2) * 2.5 
        
        initial_target = "Crown" if idx < 2 else ("WestMonolith" if idx == 2 else "EastMonolith")
        route = get_best_path("BlueBase", [initial_target], role, "Blue")
        
        agents.append({
            "id": aid, "team": "Blue", "role": role, 
            "speed": 5.4, "decision_delay": 0.0,
            "coord": start_pos, "path_history": [start_pos.copy()], 
            "route_plan": route, "route_idx": 1,
            "final_objective": initial_target,
            "cover_usage": 0, "in_combat": False, "state": "MARCH",
            "reeval_timer": 0.0
        })
        
    for idx, (aid, role) in enumerate(RED_TEAM):
        start_node = get_node("RedBase")
        start_pos = start_node["pos"].copy()
        start_pos[0] += (idx - 2) * 2.5
        
        initial_target = "SouthRift" if idx < 2 else ("WestMonolith" if idx == 2 else "Crown")
        route = get_best_path("RedBase", [initial_target], role, "Red")
        
        agents.append({
            "id": aid, "team": "Red", "role": role, 
            "speed": 4.2, "decision_delay": 0.0,
            "coord": start_pos, "path_history": [start_pos.copy()], 
            "route_plan": route, "route_idx": 1,
            "final_objective": initial_target,
            "cover_usage": 0, "in_combat": False, "state": "MARCH",
            "reeval_timer": 0.0
        })
    return agents
