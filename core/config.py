"""
AetherFlow :: core/config.py  (v0.6.3.2)
SCALE-DRIVEN CONFIG — the single source for all map dimensions.
"""

GROUND_HALF_SIZE = 100.0
WORLD_FLOOR_HALF_SIZE = 110.0
_BASE_HALF = 300.0
_S = GROUND_HALF_SIZE / _BASE_HALF

# Visual/gameplay prop scale: keep the map footprint and anchors fixed,
# but reduce pocket and objective-turret geometry to 40% of the old size.
# This is a 60% size reduction. Gameplay-critical symmetry remains enforced.
POCKET_TURRET_GEOMETRY_SCALE = 0.40


def _s(v):
    return v * _S

CONFIG = {
    "seed": 1337,
    "debug_sightlines": True,
    "ground_half_size": GROUND_HALF_SIZE,
    "world_floor_half_size": WORLD_FLOOR_HALF_SIZE,
    "map_radius": _s(250.0),
    "outer_ring_radius": _s(137.5),
    "base_radius": _s(255.0),
    "base_spread_deg": 40.0,
    "center_radius": _s(50.0),
    "core_transition_radius": _s(35.0),
    "south_rift_blend_radius": _s(62.5),
    "crown_influence_radius": _s(112.5),
    "monolith_influence_radius": _s(100.0),
    "terrain_resolution": 130,
    "heights": {
        "Crown": _s(1.5), "WestMonolith": _s(0.75), "EastMonolith": _s(0.75),
        "SWMonolith": 0.0, "SEMonolith": 0.0,
        "BlueBase": 0.0, "RedBase": 0.0,
        "SouthRift": _s(-0.75), "AetherCore": _s(-2.0),
    },
    "terrain_refinement": {
        "enabled": True,
        "core_depth_multiplier": 1.65,
        "crown_height_multiplier": 1.60,
        "monolith_height_multiplier": 1.60,
        "south_rift_depth_multiplier": 1.50,
        "transition_radius_multiplier": 1.10,
        "max_expected_slope_deg": 35.0,
        "require_team_symmetry": True,
        "symmetry_plane": "Y_AXIS",
        "mirror_axis": "x -> -x",
    },
    "height_transitions": {
        "combat_max_deg": 15.0,
        "minion_safe_max_deg": 18.0,
        "walkable_max_deg": 25.0,
        "ramp_max_deg": 30.0,
        "hard_max_deg": 35.0,
        "max_step_m": 0.75,
        "min_group_width_m": 4.0,
        "minion_corridor_width_m": 1.30,
    },
    "gameplay_symmetry": {
        "enabled": True,
        "rule": "ALL_TEAM_CRITICAL_GEOMETRY_MUST_BE_MIRROR_SYMMETRIC",
        "plane": "Y_AXIS",
        "transform": "(x,y,z) -> (-x,y,z)",
        "tolerance_m": 0.25,
        "apply_to": [
            "bases", "capture_points", "roads", "ramps", "pockets",
            "gameplay_cover", "altar_protectors", "terrain_heights",
            "gameplay_markers", "future_spawns", "future_shops"
        ],
        "decorative_exempt": True,
        "validation_is_hard_gate": True,
    },
    "capture_platform_radius": _s(20.0),
    "capture_platform_height": _s(1.5),
    "turret_offset": _s(27.5) * POCKET_TURRET_GEOMETRY_SCALE,
    "turret_radius_base": _s(4.5) * POCKET_TURRET_GEOMETRY_SCALE,
    "turret_radius_top": _s(2.25) * POCKET_TURRET_GEOMETRY_SCALE,
    "turret_depth": _s(10.0) * POCKET_TURRET_GEOMETRY_SCALE,
    "turret_z_offset": _s(5.0) * POCKET_TURRET_GEOMETRY_SCALE,
    "altar": {
        "base_radius1": _s(4.5), "base_radius2": _s(4.0),
        "base_depth": _s(0.8), "crown_radius": _s(1.4), "crown_z": _s(2.0),
    },
    "choke_rock": {
        "radius1": _s(2.8), "radius2": _s(1.5), "depth": _s(4.5),
        "lateral_extra": _s(2.5), "z_offset": _s(2.25),
    },
    "core_cover": {
        "north_pillar_size": (_s(6.25), _s(6.25), _s(8.75)),
        "north_pillar_offset": _s(2.5),
        "side_wall_main": (_s(10.0), _s(3.0), _s(6.25)),
        "side_wall_wing": (_s(3.75), _s(3.0), _s(5.0)),
        "pocket_block_size": (_s(7.5), _s(3.75), _s(5.0)),
        "south_screen_size": (_s(12.5), _s(3.75), _s(7.0)),
    },
    "core_cover_positions": {
        "north_pillar_y": _s(10.0), "side_wall_x": _s(11.0), "side_wall_y": _s(2.0),
        "pocket_x": _s(7.5), "pocket_y": _s(-9.0), "south_screen_y": _s(-14.0),
    },
    "altar_protectors": {
        "enabled": True,
        "count": 4,
        "symmetry_plane": "BOTH_AXES",
        "mirror_axis": "x -> -x; y -> -y",
        "front_back_mirror": True,
        "non_blocking_navigation": True,
        "ring_offset_from_altar_m": 3.5,
        "protector_radius_m": 0.8,
        "protector_height_m": 2.6,
        "layout": "CARDINAL_CENTERED",
    },
    "ring_road_width": _s(12.0), "base_road_width": _s(8.0),
    "north_ramp_width": _s(12.0), "flank_choke_width": _s(12.5),
    "road_z_offset": _s(0.05), "ramp_run_length": _s(24.0),
    "shrine_road_offset": _s(25.0), "speed_shrine_radius": _s(8.75), "health_relic_radius": _s(6.25),
    "base_platform_radius": _s(35.0), "base_platform_height": _s(1.5),
    "base_crystal_height": _s(15.0), "base_crystal_radius": _s(5.0),
    "rock": {
        "count_core": 6, "radius_min": _s(2.0), "radius_max": _s(4.2),
        "scale_y_min": 0.7, "scale_y_max": 1.15, "irregularity": 0.32,
    },
    "navigation": {"cells": 128, "max_slope_deg": 50.0},
    "simulation": {
        "agent_speed": _s(6.0), "agents_per_route": 12,
        "engagement_base": 0.08, "engagement_exposure_factor": 0.25,
        "los_eye_height": _s(1.7), "cover_los_range_factor": 2.5,
    },
    "safety_floor_z": _s(-6.0),
    "validation": {
        "bounds_margin": _s(6.0), "max_object_height": _s(30.0),
        "overlap_tolerance": _s(0.2), "require_all_capture_points": True,
        "require_both_bases": True, "reject_duplicate_names": True,
        "require_gameplay_symmetry": True,
        "gameplay_symmetry_tolerance_m": 0.25,
    },
    "scene": {
        "allow_scene_reset": False,
        "managed_collections": ["Terrain", "Bases", "CapturePoints", "Roads", "Ramps", "Decorations", "Rocks", "CoreCover", "Pockets", "DebugSightlines"],
    },
    "pockets": {
        "enabled": True,
        "center_radius": _s(153.0), "entry_width": _s(30.0) * POCKET_TURRET_GEOMETRY_SCALE,
        "entry_gate": {"target_width": 10.0 * POCKET_TURRET_GEOMETRY_SCALE, "rock_radius": 1.3 * POCKET_TURRET_GEOMETRY_SCALE, "irregularity": 0.04, "height": 2.4 * POCKET_TURRET_GEOMETRY_SCALE},
        "rock_arc": {
            "span_deg": 168.0, "target_spacing": _s(7.95) * POCKET_TURRET_GEOMETRY_SCALE, "min_segments": 22, "max_segments": 30,
            "large_ratio": 0.18, "small_ratio": 0.18, "gap_min": _s(0.45) * POCKET_TURRET_GEOMETRY_SCALE, "gap_max": _s(1.05) * POCKET_TURRET_GEOMETRY_SCALE,
            "inward_limit": _s(0.75) * POCKET_TURRET_GEOMETRY_SCALE, "outward_limit": _s(1.05) * POCKET_TURRET_GEOMETRY_SCALE, "rotation_variance": 0.14,
            "entry_end_clear": _s(0.75) * POCKET_TURRET_GEOMETRY_SCALE, "taper_start": 0.68, "seed": 1337, "connect_gap": _s(1.5) * POCKET_TURRET_GEOMETRY_SCALE,
            "classes": {
                "small": {"diam": (_s(5.4) * POCKET_TURRET_GEOMETRY_SCALE, _s(6.3) * POCKET_TURRET_GEOMETRY_SCALE), "height": (_s(6.9) * POCKET_TURRET_GEOMETRY_SCALE, _s(8.1) * POCKET_TURRET_GEOMETRY_SCALE)},
                "medium": {"diam": (_s(6.3) * POCKET_TURRET_GEOMETRY_SCALE, _s(7.2) * POCKET_TURRET_GEOMETRY_SCALE), "height": (_s(8.1) * POCKET_TURRET_GEOMETRY_SCALE, _s(9.6) * POCKET_TURRET_GEOMETRY_SCALE)},
                "large": {"diam": (_s(7.2) * POCKET_TURRET_GEOMETRY_SCALE, _s(8.1) * POCKET_TURRET_GEOMETRY_SCALE), "height": (_s(9.6) * POCKET_TURRET_GEOMETRY_SCALE, _s(11.4) * POCKET_TURRET_GEOMETRY_SCALE)},
            },
            "fortified_fence": {
                "enabled": True, "anchor_every_v3": 2, "wall_height_v3": 1.72 * POCKET_TURRET_GEOMETRY_SCALE,
                "terminal_height_v3": 1.48 * POCKET_TURRET_GEOMETRY_SCALE, "wall_thickness_v3": 0.88 * POCKET_TURRET_GEOMETRY_SCALE,
                "wall_outward_offset_v3": 0.64 * POCKET_TURRET_GEOMETRY_SCALE, "foundation_thickness_v3": 0.92 * POCKET_TURRET_GEOMETRY_SCALE,
                "foundation_height_v3": 0.36 * POCKET_TURRET_GEOMETRY_SCALE, "cap_height_v3": 0.28 * POCKET_TURRET_GEOMETRY_SCALE, "cap_overhang_v3": 0.12 * POCKET_TURRET_GEOMETRY_SCALE,
                "anchor_post_thickness_v3": 0.24 * POCKET_TURRET_GEOMETRY_SCALE, "anchor_post_height_v3": 1.88 * POCKET_TURRET_GEOMETRY_SCALE,
                "brace_thickness_v3": 0.075 * POCKET_TURRET_GEOMETRY_SCALE, "aether_every_v3": 4, "structure_seed": 7349,
            },
        },
        "side_size": {"width": _s(84.0) * POCKET_TURRET_GEOMETRY_SCALE, "depth": _s(54.0) * POCKET_TURRET_GEOMETRY_SCALE},
        "cover_margin": _s(4.2) * POCKET_TURRET_GEOMETRY_SCALE, "fairness_tolerance": _s(1.5),
        "cover": {
            "pct_max": 0.15, "min_passage": _s(9.0) * POCKET_TURRET_GEOMETRY_SCALE, "max_objects": 3,
            "min_score": 1.5, "w_los": 3.0, "w_flank": 1.0,
            "w_defensive": 1.5, "w_movement": 3.0, "w_choke": 4.0,
        },
    },
    "outer_boundary": {
        "enabled": True, "segments": 48, "semi_minor_max": 109.0, "semi_major_max": 109.0,
        "organic_deformation": 0.25, "wall_height_min": 5.0, "wall_height_max": 8.0,
        "formation_height_min": 8.0, "formation_height_max": 12.0,
        "wall_thickness_min": 3.0, "wall_thickness_max": 6.0,
        "internal_depth_factor": 1.0, "outer_clearance_min": 0.0,
        "section_overlap_factor": 1.12, "seed": 42017,
    },
    "circle_segments": 28,
}


def get(key, default=None):
    return CONFIG.get(key, default)
