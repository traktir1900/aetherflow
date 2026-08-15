# combat/simulation/cover_query.py
import json
import os
import math

COVER_WEIGHT = 12

def load_cover_database(reports_dir):
    path = os.path.join(reports_dir, "cover_layout.json")
    covers = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                objects = data.get("approved_objects", data.get("covers", []))
                for obj in objects:
                    pos = [0,0,0]
                    for key in ["location", "coord", "position", "pos", "xyz"]:
                        if key in obj:
                            pos = obj[key]
                            break
                    covers.append({
                        "pos": pos,
                        "type": obj.get("cover_type", obj.get("type", "MEDIUM")),
                        "confidence": obj.get("confidence", 0.5)
                    })
        except Exception:
            pass
            
    if not covers:
        covers = [
            {"pos": [0.0, 0.0, 10.0], "type": "HEAVY", "confidence": 0.9},
            {"pos": [0.0, -10.0, -12.0], "type": "HalfWall", "confidence": 0.9},
            {"pos": [-65.0, 0.0, 5.0], "type": "Boulder", "confidence": 0.9},
            {"pos": [65.0, 0.0, 5.0], "type": "Boulder", "confidence": 0.9},
        ]
    return covers

def query_combat_cover(agent, covers, enemy_coord):
    if not agent["in_combat"]:
        return None
        
    best_cover = None
    min_dist = float('inf')
    ag_pos = agent["coord"]
    
    for cover in covers:
        c_pos = cover["pos"]
        dist = math.sqrt((ag_pos[0]-c_pos[0])**2 + (ag_pos[1]-c_pos[1])**2 + (ag_pos[2]-c_pos[2])**2)
        if dist < 14.0 and dist < min_dist:
            min_dist = dist
            best_cover = cover
            
    return best_cover
