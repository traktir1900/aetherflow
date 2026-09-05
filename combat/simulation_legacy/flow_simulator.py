# combat/simulation/flow_simulator.py
import math
from .agents import create_agents, evaluate_live_objectives, update_combat_state
from .flow_graph import get_node, GRAPH_NODES, calculate_route_score, get_best_path
from .cover_query import load_cover_database, query_combat_cover, COVER_WEIGHT

def run_simulation(reports_dir):
    agents = create_agents()
    covers = load_cover_database(reports_dir)
    first_contact_time = None
    combat_events = []
    zone_stats = {z: {"traffic": 0, "fights": 0, "cover_usage": 0, "occupancy": 0} for z in GRAPH_NODES.keys()}
    
    zone_ownership_time = {z: {"Blue": 0.0, "Red": 0.0, "Neutral": 0.0} for z in ["Crown", "WestMonolith", "EastMonolith", "SouthRift"]}
    
    # Отслеживание времени непрерывного владения для Anti-Stagnation механизма
    zone_holding_duration = {z: 0.0 for z in ["Crown", "WestMonolith", "EastMonolith", "SouthRift"]}
    zone_last_owner = {z: "Neutral" for z in ["Crown", "WestMonolith", "EastMonolith", "SouthRift"]}
    
    objective_states = {
        "Crown": {"owner": "Blue", "status": "Blue Owned", "progress": 100.0},
        "WestMonolith": {"owner": "Red", "status": "Red Owned", "progress": -100.0},
        "EastMonolith": {"owner": "Blue", "status": "Blue Owned", "progress": 100.0},
        "SouthRift": {"owner": "Red", "status": "Red Owned", "progress": -100.0}
    }
    
    dt = 0.1 
    print("\n[v0.5.7.1 CONTROLLED OSCILLATION TRACE]")
    for a in agents:
        print(f"Agent: {a['id']} ({a['team']} / {a['role']}) -> Initial Target: {a['final_objective']}")

    debug_printed = False
    
    for tick in range(1, 9001):
        time_sec = tick * dt
        blues = [a for a in agents if a["team"] == "Blue"]
        reds = [a for a in agents if a["team"] == "Red"]
        
        if tick % 15 == 0:
            for agent in agents:
                new_target = evaluate_live_objectives(agent, agents, GRAPH_NODES, objective_states, time_sec)
                if new_target != agent["final_objective"]:
                    agent["final_objective"] = new_target
                    agent["route_plan"] = get_best_path(agent["route_plan"][min(agent["route_idx"], len(agent["route_plan"])-1)], [new_target], agent["role"], agent["team"])
                    agent["route_idx"] = 0
                    
            for obj_name, state in objective_states.items():
                if obj_name not in GRAPH_NODES: continue
                node_pos = GRAPH_NODES[obj_name]["pos"]
                b_near = sum(1 for a in blues if math.sqrt((a["coord"][0]-node_pos[0])**2 + (a["coord"][1]-node_pos[1])**2 + (a["coord"][2]-node_pos[2])**2) < 35.0)
                r_near = sum(1 for a in reds if math.sqrt((a["coord"][0]-node_pos[0])**2 + (a["coord"][1]-node_pos[1])**2 + (a["coord"][2]-node_pos[2])**2) < 35.0)
                
                net_advantage = b_near - r_near
                
                # Anti-Stagnation Pressure: если точка долго удерживается одной командой, добавляем бонус захвата врагу
                current_owner = state["owner"]
                if current_owner == zone_last_owner[obj_name] and current_owner != "Neutral":
                    zone_holding_duration[obj_name] += 1.5 # 15 ticks * 0.1
                else:
                    zone_holding_duration[obj_name] = 0.0
                    zone_last_owner[obj_name] = current_owner
                
                stagnation_boost = 1.0
                if zone_holding_duration[obj_name] > 180.0:  # > 3 минут стагнации
                    stagnation_boost = 1.25
                
                delta = net_advantage * 2.3 * 0.72 * stagnation_boost # LONG_MATCH_DAMPING = 0.72 + Anti-Stagnation
                
                state["progress"] = max(-100.0, min(100.0, state["progress"] + delta))
                
                prog = state["progress"]
                if prog >= 100.0:
                    state["owner"] = "Blue"
                    state["status"] = "Blue Owned"
                elif prog <= -100.0:
                    state["owner"] = "Red"
                    state["status"] = "Red Owned"
                elif prog > 0.0:
                    state["owner"] = "Neutral"
                    state["status"] = "Blue Capturing" if b_near > r_near else "Blue Contested"
                elif prog < 0.0:
                    state["owner"] = "Neutral"
                    state["status"] = "Red Capturing" if r_near > b_near else "Red Contested"
                else:
                    state["owner"] = "Neutral"
                    state["status"] = "Contested 50/50"
                    
                if obj_name in zone_ownership_time:
                    zone_ownership_time[obj_name][state["owner"]] += dt

        for agent in agents:
            update_combat_state(agent, agents)
            
        for b in blues:
            for r in reds:
                dist = math.sqrt((b["coord"][0]-r["coord"][0])**2 + (b["coord"][1]-r["coord"][1])**2 + (b["coord"][2]-r["coord"][2])**2)
                if dist < 15.0:
                    if first_contact_time is None:
                        first_contact_time = time_sec
                    if tick % 10 == 0:
                        combat_events.append([(b["coord"][0]+r["coord"][0])/2, (b["coord"][1]+r["coord"][1])/2, (b["coord"][2]+r["coord"][2])/2])
                    
                    if b["decision_delay"] <= 0:
                        bcov = query_combat_cover(b, covers, r["coord"])
                        if bcov:
                            b["cover_usage"] += 1
                            b["decision_delay"] = 0.12
                    if r["decision_delay"] <= 0:
                        rcov = query_combat_cover(r, covers, b["coord"])
                        if rcov:
                            r["cover_usage"] += 1
                            r["decision_delay"] = 0.12

        if not debug_printed and agents:
            sample_agent = agents[0]
            print(f"\n[DEBUG LOG v0.5.7.1] Agent {sample_agent['id']} ({sample_agent['role']}):")
            print(f"  - combat state: {sample_agent['state']}")
            print(f"  - live objective: {sample_agent['final_objective']}")
            print(f"  - match time: {round(time_sec, 1)}s")
            debug_printed = True

        for agent in agents:
            if agent["decision_delay"] > 0:
                agent["decision_delay"] -= dt
                agent["path_history"].append(agent["coord"].copy())
                continue 
            
            if agent["state"] == "RETREAT":
                base_name = "BlueBase" if agent["team"] == "Blue" else "RedBase"
                target_pos = get_node(base_name)["pos"]
            else:
                if agent["route_idx"] < len(agent["route_plan"]):
                    target_node_name = agent["route_plan"][agent["route_idx"]]
                    target_pos = get_node(target_node_name)["pos"]
                else:
                    target_pos = get_node(agent["final_objective"])["pos"]
                
            dx = target_pos[0] - agent["coord"][0]
            dy = target_pos[1] - agent["coord"][1]
            dz = target_pos[2] - agent["coord"][2]
            dist_to_target = math.sqrt(dx**2 + dy**2 + dz**2)
            
            step = agent["speed"] * dt
            
            if dist_to_target > 1.5:
                agent["coord"][0] += (dx / dist_to_target) * step
                agent["coord"][1] += (dy / dist_to_target) * step
                agent["coord"][2] += (dz / dist_to_target) * step
            else:
                if agent["state"] != "RETREAT" and agent["route_idx"] < len(agent["route_plan"]):
                    agent["route_idx"] += 1 
                    
            agent["path_history"].append(agent["coord"].copy())
            
            if tick % 10 == 0:
                for zname, zdata in GRAPH_NODES.items():
                    zd = math.sqrt((agent["coord"][0]-zdata["pos"][0])**2 + (agent["coord"][1]-zdata["pos"][1])**2 + (agent["coord"][2]-zdata["pos"][2])**2)
                    if zd < 35.0:
                        zone_stats[zname]["traffic"] += 1
                        zone_stats[zname]["occupancy"] += 1
                        if agent["in_combat"]: zone_stats[zname]["fights"] += 1
                        if agent["decision_delay"] > 0: zone_stats[zname]["cover_usage"] += 1
                    
    metrics = {
        "first_contact": round(first_contact_time, 2) if first_contact_time else 0.0,
        "total_engagements": len(combat_events),
        "objective_states": objective_states,
        "zone_ownership_time": zone_ownership_time
    }
    return metrics, zone_stats, combat_events, agents
