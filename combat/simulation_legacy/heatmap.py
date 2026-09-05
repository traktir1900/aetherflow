# combat/simulation/heatmap.py
import json
import os

def generate_heatmap_report(reports_dir, metrics, zone_stats):
    total_traffic = sum(z["traffic"] for z in zone_stats.values()) or 1
    west_traffic = zone_stats["WestMonolith"]["traffic"] + zone_stats["BlueWest"]["traffic"] + zone_stats["RedWest"]["traffic"]
    east_traffic = zone_stats["EastMonolith"]["traffic"] + zone_stats["BlueEast"]["traffic"] + zone_stats["RedEast"]["traffic"]
    
    report = {
        "meta": {"version": "0.5.7.1", "design_phase": "Controlled Oscillation Correction"},
        "metrics": {
            "first_contact_sec": metrics["first_contact"],
            "total_combat_events": metrics["total_engagements"],
            "objective_states": metrics["objective_states"],
            "zone_ownership_time": metrics["zone_ownership_time"],
            "distributions": {
                "Crown": round((zone_stats["Crown"]["traffic"] / total_traffic) * 100, 1),
                "SouthRift": round((zone_stats["SouthRift"]["traffic"] / total_traffic) * 100, 1),
                "WestWing": round((west_traffic / total_traffic) * 100, 1),
                "EastWing": round((east_traffic / total_traffic) * 100, 1)
            }
        },
        "zones": zone_stats
    }
    
    path = os.path.join(reports_dir, "flow_heatmap.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    return path, report["metrics"]["distributions"]
