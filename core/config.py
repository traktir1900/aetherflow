"""
AetherFlow :: core/config.py (v0.6.3.2)
SCALE-DRIVEN CONFIG — single source for map dimensions.
"""

GROUND_HALF_SIZE = 100.0
WORLD_FLOOR_HALF_SIZE = 110.0
_BASE_HALF = 300.0
_S = GROUND_HALF_SIZE / _BASE_HALF

GEOMETRY_SCALE = 0.40
POCKET_TURRET_GEOMETRY_SCALE = GEOMETRY_SCALE
POCKET_GEOMETRY_SCALE = 1.50

def _s(v): return v * _S
def _g(v): return v * GEOMETRY_SCALE
def _gs(v): return _s(v) * GEOMETRY_SCALE
def _p(v): return _s(v) * GEOMETRY_SCALE * POCKET_GEOMETRY_SCALE

CONFIG = {
    "seed": 1337, "debug_sightlines": True,
    "ground_half_size": GROUND_HALF_SIZE, "world_floor_half_size": WORLD_FLOOR_HALF_SIZE,
    "map_radius": _s(250.0), "outer_ring_radius": _s(137.5), "base_radius": _s(255.0),
    "base_spread_deg": 40.0, "center_radius": _s(165.0), "core_transition_radius": _s(35.0),
    "south_rift_blend_radius": _s(62.5), "crown_influence_radius": _s(112.5),
    "monolith_influence_radius": _s(100.0), "terrain_resolution": 130,
    "heights": {"Crown": _s(1.5), "WestMonolith": _s(0.75), "EastMonolith": _s(0.75),
                 "SWMonolith": 0.0, "SEMonolith": 0.0, "BlueBase": 0.0, "RedBase": 0.0,
                 "SouthRift": _s(-0.75), "AetherCore": _s(-2.0)},
    "terrain_refinement": {"enabled": True, "core_depth_multiplier": 1.65,
        "crown_height_multiplier": 1.60, "monolith_height_multiplier": 1.60,
        "south_rift_depth_multiplier": 1.50, "transition_radius_multiplier": 1.10,
        "max_expected_slope_deg": 35.0, "require_team_symmetry": True,
        "symmetry_plane": "Y_AXIS", "mirror_axis": "x -> -x"},
    "height_transitions": {"combat_max_deg": 15.0, "minion_safe_max_deg": 18.0,
        "walkable_max_deg": 25.0, "ramp_max_deg": 30.0, "hard_max_deg": 35.0,
        "max_step_m": 0.75, "min_group_width_m": 4.0, "minion_corridor_width_m": 1.30},
    "gameplay_symmetry": {"enabled": True,
        "rule": "ALL_TEAM_CRITICAL_GEOMETRY_MUST_BE_MIRROR_SYMMETRIC",
        "plane": "Y_AXIS", "transform": "(x,y,z) -> (-x,y,z)", "tolerance_m": 0.25,
        "apply_to": ["bases", "capture_points", "roads", "ramps", "pockets", "gameplay_cover",
                      "altar_protectors", "terrain_heights", "gameplay_markers", "future_spawns", "future_shops"],
        "decorative_exempt": True, "validation_is_hard_gate": True},
    "capture_platform_radius": _gs(20.0), "capture_platform_height": _gs(1.5),
    "turret_offset": _gs(27.5), "turret_radius_base": _gs(4.5), "turret_radius_top": _gs(2.25),
    "turret_depth": _gs(10.0), "turret_z_offset": _gs(5.0),
    "altar": {"base_radius1": _gs(4.5), "base_radius2": _gs(4.0), "base_depth": _gs(0.8),
              "crown_radius": _gs(1.4), "crown_z": _gs(2.0)},
    "choke_rock": {"radius1": _gs(2.8), "radius2": _gs(1.5), "depth": _gs(4.5),
                    "lateral_extra": _gs(2.5), "z_offset": _gs(2.25)},
    "core_cover": {"north_pillar_size": tuple(_gs(v) for v in (6.25,6.25,8.75)),
        "north_pillar_offset": _gs(2.5), "side_wall_main": tuple(_gs(v) for v in (10.0,3.0,6.25)),
        "side_wall_wing": tuple(_gs(v) for v in (3.75,3.0,5.0)),
        "pocket_block_size": tuple(_gs(v) for v in (7.5,3.75,5.0)),
        "south_screen_size": tuple(_gs(v) for v in (12.5,3.75,7.0))},
    "core_cover_positions": {"north_pillar_y": _s(10.0), "side_wall_x": _s(11.0),
        "side_wall_y": _s(2.0), "pocket_x": _s(7.5), "pocket_y": _s(-9.0), "south_screen_y": _s(-14.0)},
    "altar_protectors": {"enabled": True, "count": 5, "symmetry_plane": "Y_AXIS",
        "mirror_axis": "x -> -x", "front_back_mirror": False, "non_blocking_navigation": True,
        "ring_offset_from_altar_m": 3.5, "protector_radius_m": 0.8, "protector_height_m": 2.6,
        "protector_length_m": 1.8, "protector_depth_m": 0.625, "layout": "CROWN_SIDE_OPEN_FIVE"},
    "ring_road_width": _gs(12.0), "base_road_width": _gs(8.0), "north_ramp_width": _gs(50.0),
    "flank_choke_width": _gs(12.5), "road_z_offset": _s(0.05), "ramp_run_length": _s(24.0),
    "shrine_road_offset": _s(25.0), "speed_shrine_radius": _gs(8.75), "health_relic_radius": _gs(6.25),
    "resource_foundation": {"enabled": True, "speed_anchor_t": 0.52, "health_anchor_t": 0.52,
        "speed_offset_y": -3.5, "health_offset_y": -3.5, "speed_shrine_radius": 1.4,
        "health_relic_radius": 1.2, "capture_health_offset_m": 0.75, "require_exact_mirror": True},
    "gameplay_landscape": {
        "enabled": True,
        "side_highland_height": 0.90,
        "side_lowland_depth": 0.65,
        "south_shoulder_height": 0.55,
        "north_shoulder_height": 0.45,
        "broad_undulation": 0.18,
        "design_intent": "gentle_high_ground_low_ground_flank_choices_without_blocking_main_routes",
        "symmetry": "x -> -x",
    },
    "base_platform_width_radius": _gs(52.5), "base_platform_depth": _gs(52.5),
    "base_platform_height": _gs(1.5), "base_crystal_height": _gs(15.0), "base_crystal_radius": _gs(5.0),
    "base_shop_width": _gs(105.0), "base_shop_depth": _gs(18.0), "base_shop_height": _gs(16.0),
    "base_shop_gap": _gs(0.0),
    "rock": {"count_core": 0, "radius_min": _gs(2.0), "radius_max": _gs(4.2),
             "scale_y_min": 0.7, "scale_y_max": 1.15, "irregularity": 0.32},
    "navigation": {"cells": 128, "max_slope_deg": 50.0},
    "simulation": {"agent_speed": _s(6.0), "agents_per_route": 12, "engagement_base": 0.08,
                    "engagement_exposure_factor": 0.25, "los_eye_height": _s(1.7), "cover_los_range_factor": 2.5},
    "safety_floor_z": _s(-6.0),
    "validation": {"bounds_margin": _s(6.0), "max_object_height": _s(30.0),
        "overlap_tolerance": _s(0.2), "require_all_capture_points": True, "require_both_bases": True,
        "reject_duplicate_names": True, "require_gameplay_symmetry": True, "gameplay_symmetry_tolerance_m": 0.25},
    "scene": {"allow_scene_reset": False,
        "managed_collections": ["Terrain", "Bases", "CapturePoints", "Roads", "Ramps", "Decorations", "Rocks", "CoreCover", "Pockets", "DebugSightlines"]},
    "pockets": {"enabled": True, "center_radius": _s(165.0), "entry_width": _p(30.0),
        "entry_gate": {"target_width": _p(10.0), "rock_radius": _p(1.3), "irregularity": 0.04, "height": _p(2.4)},
        "rock_arc": {"span_deg": 168.0, "target_spacing": _p(7.95), "min_segments": 22, "max_segments": 30,
            "large_ratio": 0.18, "small_ratio": 0.18, "gap_min": _p(0.45), "gap_max": _p(1.05),
            "inward_limit": _p(0.75), "outward_limit": _p(1.05), "rotation_variance": 0.14,
            "entry_end_clear": _p(0.75), "taper_start": 0.68, "seed": 1337, "connect_gap": _p(1.5),
            "classes": {"small": {"diam": (_p(5.4),_p(6.3)), "height": (_p(6.9),_p(8.1))},
                        "medium": {"diam": (_p(6.3),_p(7.2)), "height": (_p(8.1),_p(9.6))},
                        "large": {"diam": (_p(7.2),_p(8.1)), "height": (_p(9.6),_p(11.4))}},
            "fortified_fence": {"enabled": True, "anchor_every_v3": 2, "wall_height_v3": _p(1.72),
                "terminal_height_v3": _p(1.48), "wall_thickness_v3": _p(0.88), "wall_outward_offset_v3": _p(0.64),
                "foundation_thickness_v3": _p(0.92), "foundation_height_v3": _p(0.36), "cap_height_v3": _p(0.28),
                "cap_overhang_v3": _p(0.12), "anchor_post_thickness_v3": _p(0.24), "anchor_post_height_v3": _p(1.88),
                "brace_thickness_v3": _p(0.075), "aether_every_v3": 4, "structure_seed": 7349}},
        "side_size": {"width": _p(84.0), "depth": _p(54.0)}, "cover_margin": _p(4.2), "fairness_tolerance": _s(1.5),
        "cover": {"pct_max": 0.15, "min_passage": _p(9.0), "max_objects": 3, "min_score": 1.5,
                  "w_los": 3.0, "w_flank": 1.0, "w_defensive": 1.5, "w_movement": 3.0, "w_choke": 4.0}},
    "outer_boundary": {"enabled": True, "segments": 48, "semi_minor_max": 109.0, "semi_major_max": 109.0,
        "organic_deformation": 0.25, "wall_height_min": 5.0, "wall_height_max": 8.0,
        "formation_height_min": 8.0, "formation_height_max": 12.0, "wall_thickness_min": 3.0,
        "wall_thickness_max": 6.0, "internal_depth_factor": 1.0, "outer_clearance_min": 0.0,
        "section_overlap_factor": 1.12, "seed": 42017},
    "world_silhouette": {"enabled": False, "symmetry_required": True, "navigation_blocking": False},
    "circle_segments": 28,
}

def get(key, default=None): return CONFIG.get(key, default)
