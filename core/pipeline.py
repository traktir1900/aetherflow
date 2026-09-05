"""
AetherFlow :: core/pipeline.py  (v0.6.2.1)

The SINGLE active generation pipeline.
v0.6.2.1 adds the gameplay-cover pass without rebuilding map topology.
"""
import os
import time

import bpy

from core.config import CONFIG
from core.context import MapContext
from core.version import get_version, banner
from core.utils import clear_scene, setup_collections
from core.materials import setup_materials
from core.layout import build_layout
from core.navigation import build_grid, run_navigation_checks
from core.validation import run_validation
from core.export import write_map_data
from core.rocks import scatter_core_rocks
from core.gameplay_cover import run_gameplay_cover_pass, repair_outer_boundary_for_legacy_bounds

import geometry.terrain as terrain
import geometry.structures as structures
import geometry.pockets as pockets
import geometry.boundary as boundary
import combat.simulation as simulation


def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def run_pipeline(ctx=None, export=True):
    start = time.time()
    print(banner("AETHER FLOW GENERATION PIPELINE"))

    cfg = CONFIG
    half = cfg.get("ground_half_size", 0)
    world_half = cfg.get("world_floor_half_size", half)
    print("[SCALE] gameplay_half={} -> {}x{} m gameplay map | world_floor_half={} -> {}x{} m floor".format(
        half, half * 2, half * 2, world_half, world_half * 2, world_half * 2))
    if half <= 0:
        raise ValueError("ground_half_size must be positive (got {})".format(half))

    if ctx is None:
        ctx = MapContext(cfg, _project_root())
    ctx.reseed()

    print("\n[STAGE 1/10] Scene (safe) + materials")
    clear_scene(ctx)
    setup_collections(ctx)
    setup_materials(ctx)

    print("[STAGE 2/10] Layout (5 capture points + 2 bases)")
    ctx.layout = build_layout(cfg)

    print("[STAGE 3/10] Terrain + safety floor")
    terrain.generate_terrain(ctx, debug_tint=cfg.get("debug_sightlines", True))
    terrain.generate_safety_floor(ctx)

    print("[STAGE 4/10] Structures (altar/crown, points, bases, cover, roads, ramps)")
    structures.generate_core_and_entrances(ctx)
    structures.generate_capture_points(ctx)
    structures.generate_bases(ctx)
    structures.generate_core_combat_cover(ctx)
    structures.generate_roads(ctx)
    ramps = structures.generate_ramps(ctx)
    print("  -> graded ramps built: {}".format(len(ramps)))

    print("[STAGE 5/10] Procedural rocks")
    rocks = scatter_core_rocks(ctx)
    print("  -> rocks built: {}".format(len(rocks)))

    print("[STAGE 6/10] Gameplay pockets (4 symmetrical)")
    pkts = pockets.generate_pockets(ctx)
    print("  -> pockets built: {} ({} objects)".format(len(ctx.pockets), len(pkts)))

    print("[STAGE 6A/10] Gameplay Cover 2.0")
    cover = run_gameplay_cover_pass(ctx)
    print("  -> objective gameplay cover: {} across {} objectives".format(
        cover["objective_cover_count"], cover["objectives_covered"]))

    print("[STAGE 6B/10] Global outer elliptical perimeter")
    boundary.generate_outer_boundary(ctx)
    moved_boundary = repair_outer_boundary_for_legacy_bounds(ctx)
    print("  -> legacy-bounds boundary repair: {} sections adjusted".format(moved_boundary))

    bpy.context.view_layer.update()

    print("[STAGE 7/10] Navigation (obstacle-aware grid)")
    grid = build_grid(ctx)
    nav = run_navigation_checks(ctx, grid)
    for prob in nav["problems"]:
        print("  [NAV] " + prob)
    print("  -> chokepoints detected: {}".format(len(nav["chokepoints"])))
    print("  -> pockets reachable: {}/{}".format(
        sum(1 for p in nav.get("pockets", []) if p["reachable"]),
        len(nav.get("pockets", []))))

    print("[STAGE 8/10] Combat simulation (5/5 capture points, nav-driven)")
    sim = simulation.run_simulation(ctx, grid, nav_report=nav)

    print("[STAGE 9/10] Validation")
    report = run_validation(ctx, nav_report=nav)
    for e in report["errors"]:
        print("  [VALIDATION ERROR] " + e)
    for w in report["warnings"]:
        print("  [validation warn] " + w)

    out_path = None
    if export:
        print("[STAGE 10/10] Export map_data.json")
        out_path = write_map_data(
            ctx, os.path.join(_project_root(), "export", "map_data.json"),
            sim=sim, nav=nav, validation=report)

        if report.get("ok", False):
            bpy.ops.wm.save_as_mainfile()
            print("[SAVE] Blender scene saved -> {}".format(bpy.data.filepath))

    elapsed = round(time.time() - start, 2)
    print("\n" + "=" * 70)
    print(">>> AETHER FLOW v{} FINISHED in {}s — validation {} <<<".format(
        get_version(), elapsed, "PASSED" if report["ok"] else "FAILED"))
    print("=" * 70 + "\n")

    return {
        "version": get_version(),
        "validation": report,
        "navigation": nav,
        "simulation": sim,
        "gameplay_cover": cover,
        "map_data": out_path,
    }
