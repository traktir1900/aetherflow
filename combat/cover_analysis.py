import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh

def analyze_zone_threats(ctx):
    cfg = ctx.config
    layout = ctx.layout
    
    zone_metrics = {
        "Crown":        {"open_lines": 17, "height_adv": 1.4, "importance": 0.9},
        "WestMonolith": {"open_lines": 11, "height_adv": 1.2, "importance": 0.7},
        "EastMonolith": {"open_lines": 11, "height_adv": 1.2, "importance": 0.7},
        "SouthMonolith":{"open_lines": 7,  "height_adv": 1.0, "importance": 0.5},
        "SEMonolith":   {"open_lines": 7,  "height_adv": 1.0, "importance": 0.5},
        "SWMonolith":   {"open_lines": 7,  "height_adv": 1.0, "importance": 0.5},
        "SouthRift":    {"open_lines": 4,  "height_adv": 0.8, "importance": 0.3}
    }

    altar_pos = Vector((layout["Center"].x, layout["Center"].y, cfg["heights"]["AetherCore"]))
    zone_analysis_contract = {}

    for zone_name, pos in layout.items():
        if zone_name == "Center" or "Base" in zone_name:
            continue
            
        dist = (Vector((pos.x, pos.y)) - Vector((altar_pos.x, altar_pos.y))).length
        metrics = zone_metrics.get(zone_name, {"open_lines": 5, "height_adv": 1.0, "importance": 0.5})
        
        los_factor = metrics["open_lines"] / 20.0
        h_adv = metrics["height_adv"]
        importance = metrics["importance"]
        exposure = 1.0 if dist > 40.0 else 0.8
        
        threat_score = (los_factor * 0.4) + (h_adv * 0.3) + (importance * 0.2) + (exposure * 0.1)
        threat_score = min(1.0, max(0.0, threat_score))

        if threat_score >= 0.70:
            classification = "HIGH"
            cover_type = "MEDIUM"
            intent = "ANTI_SNIPER"
            priority = 0.95
        elif threat_score >= 0.45:
            classification = "MEDIUM"
            cover_type = "LOW"
            intent = "FLANK_SUPPORT"
            priority = 0.60
        else:
            classification = "LOW"
            cover_type = "LOW"
            intent = "RETREAT_COVER"
            priority = 0.25

        zone_analysis_contract[zone_name] = {
            "distance": round(dist, 1),
            "height_advantage": h_adv,
            "open_lines_count": metrics["open_lines"],
            "threat_score": round(threat_score, 2),
            "classification": classification,
            "cover_type": cover_type,
            "intent": intent,
            "priority": priority
        }

    return zone_analysis_contract
