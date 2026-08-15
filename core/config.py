CONFIG = {
    "seed": 1337,
    "debug_sightlines": True,
    "map_radius": 250.0,
    "ground_half_size": 300.0,      # Dominion x2.5 target (600m x 600m terrain)
    "outer_ring_radius": 137.5,     # Dominion x2.5: pentagon_radius 55.0 -> 137.5
    "base_radius": 275.0,           # Dominion x2.5: base_radius 110.0 -> 275.0 (see report: source file had 88.0, not 110.0 -- migrated to the task-specified 275.0 target regardless)
    "base_spread_deg": 40.0,
    "center_radius": 50.0,          # Dominion x2.5: scaled x2.5 (20.0 -> 50.0). Feeds core transition + choke geometry -- see hidden-dependency note in report.

    # --- Dominion x2.5: NEW config keys, replacing values that were
    # hardcoded directly inside core/heightmap.py and geometry/terrain.py.
    # Added per Phase 3 requirement ("remove old hardcoded scale values;
    # use configuration parameters"). All scaled x2.5 from their original
    # hardcoded literals to preserve terrain-feature proportions relative
    # to the new pentagon/base scale (Phase 4 requirement).
    "core_transition_radius": 35.0,     # was hardcoded 14.0 in heightmap.py
    "south_rift_blend_radius": 62.5,    # was hardcoded 25.0 in heightmap.py
    "crown_influence_radius": 112.5,    # was hardcoded 45.0 in heightmap.py
    "monolith_influence_radius": 100.0, # was hardcoded 40.0 in heightmap.py
    "terrain_resolution": 130,          # was hardcoded `res = 52` in terrain.py (52 * 2.5, preserves original mesh density per meter)
    "heights": {
        "Crown": 1.5,
        "WestMonolith": 0.75,
        "EastMonolith": 0.75,
        "SWMonolith": 0.0,
        "SEMonolith": 0.0,
        "BlueBase": 0.0,
        "RedBase": 0.0,
        "SouthRift": -0.75,
        "AetherCore": -2.0,
    },
    "capture_platform_radius": 20.0,    # Dominion x2.5: 8.0 -> 20.0 (scaled to match enlarged pentagon; not explicitly listed in the task's parameter table, see report Assumption #1)
    "capture_platform_height": 1.5,     # Dominion x2.5: 0.6 -> 1.5
    "turret_offset": 27.5,              # Dominion x2.5: 11.0 -> 27.5 (MUST track capture_platform_radius -- see hidden-dependency note in report; left unscaled it would place turrets inside the enlarged platform)
    "core_cover": {
        "north_pillar_size": (6.25, 6.25, 8.75),
        "north_pillar_offset": 2.5,
        "side_wall_main": (10.0, 3.0, 6.25),
        "side_wall_wing": (3.75, 3.0, 5.0),
        "pocket_block_size": (7.5, 3.75, 5.0),
        "south_screen_size": (12.5, 3.75, 7.0),
    },
    "ring_road_width": 12.0,            # Dominion x2.5: task-specified absolute target (Primary roads: 12m) -- was 15.0
    "base_road_width": 8.0,             # Dominion x2.5: task-specified absolute target (Secondary roads: 8m) -- was 10.0
    "north_ramp_width": 12.0,           # unchanged -- not listed in task's road spec; already equals the Primary width, left as-is (see report)
    "flank_choke_width": 12.5,          # Dominion x2.5: 5.0 -> 12.5
    "road_z_offset": 0.05,              # unchanged -- small terrain-clearance offset, not scale-dependent
    "shrine_road_offset": 25.0,         # Dominion x2.5: 10.0 -> 25.0
    "speed_shrine_radius": 8.75,        # Dominion x2.5: 3.5 -> 8.75
    "health_relic_radius": 6.25,        # Dominion x2.5: 2.5 -> 6.25
    "base_platform_radius": 35.0,       # Dominion x2.5: 14.0 -> 35.0
    "base_platform_height": 1.5,        # Dominion x2.5: 0.6 -> 1.5
    "base_crystal_height": 15.0,        # Dominion x2.5: 6.0 -> 15.0 (see report: this key existed in the original config but geometry/bases.py never actually read it -- wired it up as part of this migration, see Fixed Bug note)
    "base_crystal_radius": 5.0,         # Dominion x2.5: NEW key, was hardcoded radius=2.0 directly in geometry/bases.py
    "turret_radius_base": 4.5,          # Dominion x2.5: NEW key, was hardcoded radius1=1.8 directly in geometry/bases.py
    "turret_radius_top": 2.25,          # Dominion x2.5: NEW key, was hardcoded radius2=0.9 directly in geometry/bases.py
    "turret_depth": 10.0,               # Dominion x2.5: NEW key, was hardcoded depth=4.0 directly in geometry/bases.py
    "turret_z_offset": 5.0,             # Dominion x2.5: NEW key, was hardcoded Vector z=2.0 directly in geometry/bases.py
    "circle_segments": 28,
}
