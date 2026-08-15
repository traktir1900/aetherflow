import os
import json
from mathutils import Vector
from combat.cover_rules import CONFIG_RULES
from combat.cover_variants import select_cover_variant
from combat.cover_orientation import calculate_cover_rotation

def run_cover_placement_engine(ctx, zone_contracts):
    print("\n[TASK #0.5.2.4] Running Advanced Tactical Placement Engine")
    
    approved_covers = []
    rejected_covers = []
    
    altar_pos = Vector((0.0, 0.0, ctx.config["heights"]["AetherCore"]))
    target_zones = ["Crown", "WestMonolith", "EastMonolith", "SouthRift"]
    
    for zone_name in target_zones:
        if zone_name not in zone_contracts:
            continue
            
        zone_data = zone_contracts[zone_name]
        pos = ctx.layout[zone_name]
        
        cover_type = zone_data.get("cover_type", "LOW")
        intent = zone_data.get("intent", "FLANK_SUPPORT")
        base_threat = zone_data.get("threat_score", 0.5)
        
        dir_to_center = (Vector((altar_pos.x, altar_pos.y)) - Vector((pos.x, pos.y))).normalized()
        zone_2d = Vector((pos.x, pos.y))
        
        candidate_offsets = [16.0, 24.0, 32.0, 39.0]
        threshold = CONFIG_RULES["min_score_threshold_medium"] if cover_type == "MEDIUM" else CONFIG_RULES["min_score_threshold_low"]
        
        for idx, dist_offset in enumerate(candidate_offsets):
            cand_pos_2d = zone_2d + dir_to_center * dist_offset
            cand_dist_center = (cand_pos_2d - Vector((altar_pos.x, altar_pos.y))).length
            
            threat_reduction = base_threat * (0.95 - idx * 0.04)
            
            road_penalty = CONFIG_RULES["road_penalty"] if (cand_dist_center < CONFIG_RULES["min_dist_from_center"] or cand_dist_center > CONFIG_RULES["max_dist_from_center"]) else 0.0
            
            density_penalty = 0.0
            for ac in approved_covers:
                if (Vector((ac["position"][0], ac["position"][1])) - cand_pos_2d).length < CONFIG_RULES["min_cover_spacing"]:
                    density_penalty = CONFIG_RULES["density_penalty"]
                    break
                    
            over_block_pen = CONFIG_RULES["over_block_penalty"] if cand_dist_center < 18.0 else 0.0
            
            final_score = threat_reduction - road_penalty - density_penalty - over_block_pen
            final_score = round(max(0.0, min(1.0, final_score)), 2)
            
            approved = final_score >= threshold
            
            reason = ""
            if not approved:
                if road_penalty > 0:
                    reason = "Blocks rotation path / outside range"
                elif density_penalty > 0:
                    reason = "High density / overlaps existing cover"
                elif over_block_pen > 0:
                    reason = "Blocks core observation"
                else:
                    reason = f"Low threat reduction ({final_score}) — Score below threshold"
            
            sub_type = select_cover_variant(cover_type, intent, idx)
            rotation = calculate_cover_rotation((cand_pos_2d.x, cand_pos_2d.y), (altar_pos.x, altar_pos.y), intent)
            height = 2.0 if cover_type == "MEDIUM" else 1.2
            
            candidate = {
                "name": f"{zone_name}_Cover_{idx+1}",
                "cover_type": cover_type,
                "sub_type": sub_type,
                "position": [round(cand_pos_2d.x, 2), round(cand_pos_2d.y, 2), 0.0],
                "rotation": round(rotation, 1),
                "height": height,
                "intent": intent,
                "source_zone": zone_name,
                "confidence": round(0.5 + (final_score * 0.45), 2),
                "final_score": final_score,
                "approved": approved,
                "reason": reason
            }
            
            status_str = "APPROVED" if approved else "REJECTED"
            print(f"[TACTICAL CANDIDATE] Zone: {zone_name:13} | Type: {cover_type:6} | Sub: {sub_type:14} | Score: {final_score:4.2f} | Status: {status_str}")
            if not approved:
                print(f"                     Reason: {reason}")
                
            if approved:
                approved_covers.append(candidate)
            else:
                rejected_covers.append(candidate)

    report_data = {
        "map_name": "AetherFlow_Core",
        "version": "0.5.2.4",
        "seed": ctx.config["seed"],
        "generation_mode": "STATIC",
        "approved_count": len(approved_covers),
        "rejected_count": len(rejected_covers),
        "layout_objects": approved_covers,
        "rejected_objects": rejected_covers
    }
    
    reports_dir = os.path.join(ctx.project_dir, "combat", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    layout_path = os.path.join(reports_dir, "cover_layout.json")
    threat_map_path = os.path.join(reports_dir, "threat_map.json")
    
    with open(layout_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4)
        
    with open(threat_map_path, "w", encoding="utf-8") as f:
        json.dump({"meta": report_data["meta"] if "meta" in report_data else {"version": "0.5.2.4"}, "zones": zone_contracts}, f, indent=4)
        
    print(f"\n--- TACTICAL COVER REFINEMENT COMPLETE ---")
    print(f"Approved Tactical Objects: {len(approved_covers)}")
    print(f"Rejected Objects: {len(rejected_covers)}")
    print(f"UE5 Datasmith Export saved to: {layout_path}\n")
    
    return approved_covers, rejected_covers
