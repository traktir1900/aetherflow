"""
AetherFlow :: core/config.py  (v0.6.0)

SCALE-DRIVEN CONFIG — the single source for all map dimensions.

The whole map is derived from ONE number: GROUND_HALF_SIZE.  Every spatial
value (x / y AND z, radii, road widths, cover sizes, platform heights) is a
fixed proportion of the historical baseline multiplied by a unified scale
factor _S = GROUND_HALF_SIZE / _BASE_HALF.  Changing the map size therefore
means changing a single value — no per-system manual rescaling, and Z can
never drift out of sync with X/Y.

Gameplay target: 200 x 200 m  ->  GROUND_HALF_SIZE = 100.0
World floor target: 220 x 220 m  ->  WORLD_FLOOR_HALF_SIZE = 110.0
"""

# ---------------------------------------------------------------------------
# The ONE knob that controls map scale.  110.0 == 220 x 220 m map.
# ---------------------------------------------------------------------------
GROUND_HALF_SIZE = 100.0

# Outer/world floor envelope. This expands only the terrain/floor, not gameplay geometry.
WORLD_FLOOR_HALF_SIZE = 110.0

# Unified scale vs the historical baseline (half-size 300).
_BASE_HALF = 300.0
_S = GROUND_HALF_SIZE / _BASE_HALF


def _s(v):
    """Scale a baseline length/height into the current map scale."""
    return v * _S


CONFIG = {
    # --- identity / determinism -------------------------------------------
    "seed": 1337,                     # drives all procedural randomness
    "debug_sightlines": True,

    # --- map scale (single source of truth) --------------------------------
    "ground_half_size": GROUND_HALF_SIZE,          # 100 -> 200 x 200 m
    "world_floor_half_size": WORLD_FLOOR_HALF_SIZE,  # 110 -> 220 x 220 m
    "map_radius": _s(250.0),
    "outer_ring_radius": _s(137.5),    # pentagon radius for the 5 points
    # 255 (was 275): guarantees base_radius + base_platform_radius <= half-size
    # at ANY unified scale, so both bases always fit fully inside the map
    # (at 200x200: 85 + 11.67 = 96.67 < 100).  The old 275 left the platform
    # edge 10 m outside the map at every scale — a real bounds violation.
    "base_radius": _s(255.0),          # distance of Blue/Red base from centre
    "base_spread_deg": 40.0,           # angular separation of the two bases
    "center_radius": _s(50.0),         # central crater radius

    # --- heightmap feature radii (scaled) -----------------------------------
    "core_transition_radius": _s(35.0),
    "south_rift_blend_radius": _s(62.5),
    "crown_influence_radius": _s(112.5),
    "monolith_influence_radius": _s(100.0),
    "terrain_resolution": 130,         # mesh density (count, not a length)

    # --- vertical scale (same factor — no Z drift) ---------------------------
    "heights": {
        "Crown":        _s(1.5),
        "WestMonolith": _s(0.75),
        "EastMonolith": _s(0.75),
        "SWMonolith":   0.0,
        "SEMonolith":   0.0,
        "BlueBase":     0.0,
        "RedBase":      0.0,
        "SouthRift":    _s(-0.75),
        "AetherCore":   _s(-2.0),
    },

    # --- capture points ----------------------------------------------------
    "capture_platform_radius": _s(20.0),
    "capture_platform_height": _s(1.5),
    "turret_offset": _s(27.5),
    "turret_radius_base": _s(4.5),
    "turret_radius_top": _s(2.25),
    "turret_depth": _s(10.0),
    "turret_z_offset": _s(5.0),

    # --- central landmarks (Aether Altar + Aether Crown) ---------------------
    "altar": {
        "base_radius1": _s(4.5),
        "base_radius2": _s(4.0),
        "base_depth":   _s(0.8),
        "crown_radius": _s(1.4),
        "crown_z":      _s(2.0),
    },

    # --- choke rocks flanking the central west/east gateways -----------------
    "choke_rock": {
        "radius1":       _s(2.8),
        "radius2":       _s(1.5),
        "depth":         _s(4.5),
        "lateral_extra": _s(2.5),
        "z_offset":      _s(2.25),
    },

    # --- central combat cover (all scaled by the same factor) --------------
    "core_cover": {
        "north_pillar_size":   (_s(6.25), _s(6.25), _s(8.75)),
        "north_pillar_offset": _s(2.5),
        "side_wall_main":      (_s(10.0), _s(3.0),  _s(6.25)),
        "side_wall_wing":      (_s(3.75), _s(3.0),  _s(5.0)),
        "pocket_block_size":   (_s(7.5),  _s(3.75), _s(5.0)),
        "south_screen_size":   (_s(12.5), _s(3.75), _s(7.0)),
    },
    # Anchor positions follow the same unified scale, so the whole central
    # arrangement shrinks/grows together with the map.
    "core_cover_positions": {
        "north_pillar_y":   _s(10.0),
        "side_wall_x":      _s(11.0),
        "side_wall_y":      _s(2.0),
        "pocket_x":         _s(7.5),
        "pocket_y":         _s(-9.0),
        "south_screen_y":   _s(-14.0),
    },

    # --- roads / ramps / chokes --------------------------------------------
    "ring_road_width":   _s(12.0),
    "base_road_width":   _s(8.0),
    "north_ramp_width":  _s(12.0),
    "flank_choke_width": _s(12.5),
    "road_z_offset":     _s(0.05),
    "ramp_run_length":   _s(24.0),

    # --- pickups -----------------------------------------------------------
    "shrine_road_offset":  _s(25.0),
    "speed_shrine_radius": _s(8.75),
    "health_relic_radius": _s(6.25),

    # --- bases -------------------------------------------------------------
    "base_platform_radius": _s(35.0),
    "base_platform_height": _s(1.5),
    "base_crystal_height":  _s(15.0),
    "base_crystal_radius":  _s(5.0),

    # --- rocks (procedural, variation ranges) ------------------------------
    "rock": {
        "count_core": 6,
        "radius_min": _s(2.0),
        "radius_max": _s(4.2),
        "scale_y_min": 0.7,
        "scale_y_max": 1.15,
        "irregularity": 0.32,   # 0..1  surface noise amount
    },

    # --- navigation ----------------------------------------------------------
    "navigation": {
        "cells": 128,            # grid resolution across the full map
        "max_slope_deg": 50.0,
    },

    # --- simulation model (deterministic; all constants documented) ----------
    "simulation": {
        "agent_speed":      _s(6.0),   # world units per second
        "agents_per_route": 12,        # traffic = routes_through_zone * this
        "engagement_base":  0.08,      # base fraction of traffic that fights
        "engagement_exposure_factor": 0.25,  # + exposure * this
        "los_eye_height":   _s(1.7),
        "cover_los_range_factor": 2.5, # exposure rays reach plat_radius * this
    },

    # --- safety / validation ------------------------------------------------
    "safety_floor_z": _s(-6.0),   # player can never fall below this
    "validation": {
        "bounds_margin": _s(6.0),
        "max_object_height": _s(30.0),
        # Intersections deeper than this are reported as SOLID OVERLAP.
        # Contacts within it (e.g. the Pillar deliberately abutting the Altar,
        # pockets touching the South Screen — inherited from the original
        # 600 m design) are reported as STRUCTURAL CONTACT, not overlap.
        "overlap_tolerance": _s(0.2),   # 6.7 cm at the 200 m scale
        "require_all_capture_points": True,
        "require_both_bases": True,
        "reject_duplicate_names": True,
    },

    # --- scene safety -------------------------------------------------------
    "scene": {
        # Destructive full-scene wipe is OFF by default.  Set True only in a
        # dedicated procedural scene.  Manual .blend content is never erased
        # unless this is explicitly enabled.
        "allow_scene_reset": False,
        "managed_collections": [
            "Terrain", "Bases", "CapturePoints", "Roads", "Ramps",
            "Decorations", "Rocks", "CoreCover", "Pockets", "DebugSightlines",
        ],
    },

    # --- gameplay pockets (v0.6.1 STEP 1 FINAL — 4 pockets) -------------------
    # Four side pockets (West/East and SW/SE strict mirror pairs).  The Crown
    # capture area is intentionally left OPEN — no CrownPocket (removed in the
    # STEP 1 finalization).
    "pockets": {
        "enabled": True,
        # Pockets sit in the side zones ALONG the ring road (pentagon edge
        # midpoints, apothem ~37 m): just outside the road, not glued to the
        # capture platforms, and clear of both bases.
        "center_radius":       _s(153.0),   # 51 m — side pocket centres (West/East/SW/SE)
        "entry_width":         _s(30.0),    # 10.0 m — now backed by real gate rocks (see entry_gate)
        # ENTRY GATE (spec v0.6.1 "POCKET ENTRY WIDTH"): two small flanking
        # rocks that pin down the ACTUAL clear surface-to-surface passage
        # (not a pivot/centre distance). `irregularity` is kept low so the
        # true mesh surface stays predictably close to `rock_radius`,
        # guaranteeing target_width +0.0/+~0.1 m (never under target).
        "entry_gate": {
            "target_width": 10.0,
            "rock_radius":  1.3,
            "irregularity": 0.04,
            "height":       2.4,
        },
        # contiguous gameplay floor (reads as ONE zone top-down)
        "floor_lift":          _s(0.45),    # 0.15 m raised pad (walkable lip)
        "floor_skirt":         _s(1.5),     # 0.5 m buried skirt (no floating)
        # Natural rock BOUNDARY around the back + smoothly rounded sides (spec
        # v0.6.1 "POCKET SHAPE FINAL FIX"). Individual rocks (NOT a mesh wall)
        # walk along the (now rounder) super-ellipse arc, densest + largest at
        # the back centre, fading size/height smoothly toward the arc ends so
        # the transition into the open front is a natural taper, not a cutoff.
        "rock_arc": {
            # Boundary-first perimeter design: architecture comes from the
            # canonical super-ellipse; rock variation is cosmetic and seeded.
            "span_deg": 168.0,
            "target_spacing": _s(7.95),        # 2.65 m target centre spacing
            "min_segments": 22,
            "max_segments": 30,
            "large_ratio": 0.18,
            "small_ratio": 0.18,
            "gap_min": _s(0.45),               # 0.15 m visual gap target
            "gap_max": _s(1.05),               # 0.35 m visual gap target
            "inward_limit": _s(0.75),          # 0.25 m maximum inward intrusion
            "outward_limit": _s(1.05),         # 0.35 m maximum outward deviation
            "rotation_variance": 0.14,          # radians, tangent-relative
            "entry_end_clear": _s(0.75),       # 0.25 m from gate transition
            "taper_start": 0.68,
            "seed": 1337,
            "connect_gap": _s(1.5),             # 0.50 m continuity tolerance
            "classes": {
                "small":  {"diam": (_s(5.4),  _s(6.3)),  "height": (_s(6.9),  _s(8.1))},
                "medium": {"diam": (_s(6.3),  _s(7.2)),  "height": (_s(8.1),  _s(9.6))},
                "large":  {"diam": (_s(7.2),  _s(8.1)),  "height": (_s(9.6),  _s(11.4))},
            },
            # AAA fortified perimeter: visual structure only. Existing rock arc
            # remains the gameplay/collision foundation; these props are deliberately
            # registered as non-blocking visual structure so navigation is unchanged.
            "fortified_fence": {
                "enabled": True,
                "anchor_every_v3": 2,
                "wall_height_v3": 1.72,
                "terminal_height_v3": 1.48,
                "wall_thickness_v3": 0.88,
                "wall_outward_offset_v3": 0.64,
                "foundation_thickness_v3": 0.92,
                "foundation_height_v3": 0.36,
                "cap_height_v3": 0.28,
                "cap_overhang_v3": 0.12,
                "anchor_post_thickness_v3": 0.24,
                "anchor_post_height_v3": 1.88,
                "brace_thickness_v3": 0.075,
                "aether_every_v3": 4,
                "structure_seed": 7349,
            },
        },
        "side_size":  {"width": _s(84.0), "depth": _s(54.0)},  # 28 x 18 m
        "cover_margin": _s(4.2),           # 1.4 m
        "fairness_tolerance":  _s(1.5),     # 0.5 m
        "cover": {
            "pct_max": 0.15,
            "min_passage": _s(9.0),
            "max_objects": 3,
            "min_score": 1.5,
            "w_los": 3.0,
            "w_flank": 1.0,
            "w_defensive": 1.5,
            "w_movement": 3.0,
            "w_choke": 4.0,
        },
    },

    "outer_boundary": {
        "enabled": True,
        "segments": 48,
        "semi_minor_max": 109.0,
        "semi_major_max": 109.0,
        "organic_deformation": 0.25,
        "wall_height_min": 5.0,
        "wall_height_max": 8.0,
        "formation_height_min": 8.0,
        "formation_height_max": 12.0,
        "wall_thickness_min": 3.0,
        "wall_thickness_max": 6.0,
        "internal_depth_factor": 1.0,
        "outer_clearance_min": 0.0,
        "section_overlap_factor": 1.12,
        "seed": 42017,
    },

    "circle_segments": 28,
}


def get(key, default=None):
    return CONFIG.get(key, default)
