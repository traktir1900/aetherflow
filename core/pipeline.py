"""
AetherFlow :: core/pipeline.py  (v0.6.3.2)

The SINGLE active generation pipeline.
v0.6.3.2 adds route-based height-transition auditing while preserving map
 topology, objective/base anchors, roads, ramps and pocket layout.
"""
import importlib
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
from core.export import write_map_data
from core.rocks import scatter_core_rocks

import core.gameplay_cover as gameplay_cover_module
import core.altar_rotation as altar_rotation_module
import core.validation as validation_module
import core.terrain_refinement as terrain_refinement_module
import core.gameplay_symmetry as gameplay_symmetry_module
import core.height_transitions as height_transitions_module

import geometry.terrain as terrain
import geometry.structures as structures
import geometry.pockets as pockets
import geometry.boundary as boundary
import combat.simulation as simulation


_GENERATION_BACKUP_COLLECTION = "__AETHERFLOW_GENERATION_BACKUP__"


def _project_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def _reload_runtime_modules():
    """Reload modules intentionally edited during iterative Blender runs."""
    global gameplay_cover_module, altar_rotation_module, validation_module
    global terrain_refinement_module, gameplay_symmetry_module, height_transitions_module, terrain
    terrain_refinement_module = importlib.reload(terrain_refinement_module)
    import core.heightmap as heightmap_module
    heightmap_module = importlib.reload(heightmap_module)
    terrain = importlib.reload(terrain)
    gameplay_cover_module = importlib.reload(gameplay_cover_module)
    altar_rotation_module = importlib.reload(altar_rotation_module)
    validation_module = importlib.reload(validation_module)
    gameplay_symmetry_module = importlib.reload(gameplay_symmetry_module)
    height_transitions_module = importlib.reload(height_transitions_module)


def _get_backup_collection():
    coll = bpy.data.collections.get(_GENERATION_BACKUP_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(_GENERATION_BACKUP_COLLECTION)
        bpy.context.scene.collection.children.link(coll)
    return coll


def _clear_backup_collection():
    coll = bpy.data.collections.get(_GENERATION_BACKUP_COLLECTION)
    if coll is None:
        return
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    if coll.users == 0:
        bpy.data.collections.remove(coll)


def _snapshot_managed_scene():
    """Snapshot current managed AetherFlow objects before destructive regeneration."""
    _clear_backup_collection()
    backup = _get_backup_collection()
    records = []
    managed_names = CONFIG.get("scene", {}).get("managed_collections", [])

    for coll_name in managed_names:
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            continue
        for obj in list(coll.objects):
            clone = obj.copy()
            if obj.data is not None:
                try:
                    clone.data = obj.data.copy()
                except (AttributeError, RuntimeError):
                    clone.data = obj.data
            backup.objects.link(clone)
            records.append({
                "clone": clone,
                "collections": [
                    c.name for c in obj.users_collection
                    if c.name in managed_names
                ],
            })

    print("[SCENE] GENERATION SNAPSHOT: {} managed objects backed up.".format(len(records)))
    return records


def _restore_managed_scene(records):
    """Restore the pre-run managed scene from the generation snapshot."""
    managed_names = CONFIG.get("scene", {}).get("managed_collections", [])
    for coll_name in managed_names:
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            continue
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

    restored = 0
    for rec in records:
        clone = rec["clone"]
        if clone.name not in bpy.data.objects:
            continue
        for coll_name in rec["collections"]:
            coll = bpy.data.collections.get(coll_name)
            if coll is not None and clone.name not in coll.objects:
                coll.objects.link(clone)
        backup = bpy.data.collections.get(_GENERATION_BACKUP_COLLECTION)
        if backup is not None and clone.name in backup.objects:
            backup.objects.unlink(clone)
        restored += 1

    _clear_backup_collection()
    bpy.context.view_layer.update()
    print("[SCENE] ROLLBACK: restored {} managed objects from pre-run snapshot.".format(restored))


def _discard_generation_snapshot():
    """Remove the temporary backup after a successful generation."""
    _clear_backup_collection()
    print("[SCENE] GENERATION SNAPSHOT: discarded after successful run.")


def _print_minion_traversal(report):
    """Print the dedicated Base->Objective->Objective->enemy Base regression."""
    print("  -> MINION TRAVERSAL: {} | scenario={}".format(
        "PASS" if report.get("passed") else "REVIEW REQUIRED",
        report.get("scenario", "Base -> Objective -> Objective -> enemy Base")))
    rules = report.get("rules", {})
    print("     rules: slope<= {:.1f}° | adjacent_dz<= {:.2f}m | corridor>= {:.2f}m | radius={:.2f}m".format(
        rules.get("minion_safe_max_deg", -1.0),
        rules.get("max_step_m", -1.0),
        rules.get("minion_corridor_width_m", -1.0),
        rules.get("minion_radius_m", -1.0)))
    for scenario in report.get("scenarios", []):
        print("     [{}] {} | reachable={} | minion_safe={} | max_slope={:.2f}° | max_dz={:.3f}m | blockers={} | ramp_base={} | edge={} | narrow={}".format(
            scenario.get("team", "?"),
            " -> ".join(scenario.get("path", [])),
            scenario.get("reachable"),
            scenario.get("minion_safe"),
            scenario.get("max_slope_deg", 0.0),
            scenario.get("max_adjacent_height_delta_m", 0.0),
            scenario.get("solid_blocker_hits", 0),
            scenario.get("ramp_base_contacts", 0),
            scenario.get("terrain_edge_hits", 0),
            scenario.get("narrow_corridor_hits", 0)))
        for hop in scenario.get("hops", []):
            analysis = hop.get("analysis", {})
            problems = analysis.get("problems", [])
            if problems:
                print("       [MINION] {} -> {} | slope={:.2f}° dz={:.3f}m | {}".format(
                    hop.get("from"), hop.get("to"),
                    analysis.get("max_local_slope_deg", -1.0),
                    analysis.get("max_adjacent_height_delta_m", -1.0),
                    problems))


def run_pipeline(ctx=None, export=True):
    start = time.time()
    print(banner("AETHER FLOW GENERATION PIPELINE"))

    _reload_runtime_modules()

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

    snapshot = _snapshot_managed_scene()
    generation_started = False
    try:
        generation_started = True

        print("\n[STAGE 1/10] Scene (safe) + materials")
        clear_scene(ctx)
        setup_collections(ctx)
        setup_materials(ctx)

        print("[STAGE 2/10] Layout (5 capture points + 2 bases)")
        ctx.layout = build_layout(cfg)

        print("[STAGE 3/10] Terrain + safety floor")
        terrain.generate_terrain(ctx, debug_tint=cfg.get("debug_sightlines", True))
        profile = terrain_refinement_module.analyze_height_profile(cfg, ctx.layout)
        p = terrain_refinement_module.get_profile(cfg)
        print("  -> terrain refinement: enabled={} | core_depth x{:.2f} | Crown x{:.2f} | monolith x{:.2f} | SouthRift x{:.2f}".format(
            profile["enabled"], p["core_depth_multiplier"], p["crown_height_multiplier"],
            p["monolith_height_multiplier"], p["south_rift_depth_multiplier"]))
        print("  -> terrain anchors: Core={:.3f}m Crown={:.3f}m West={:.3f}m East={:.3f}m SouthRift={:.3f}m".format(
            profile["landmark_heights_m"]["AetherCore"], profile["landmark_heights_m"]["Crown"],
            profile["landmark_heights_m"]["WestMonolith"], profile["landmark_heights_m"]["EastMonolith"],
            profile["landmark_heights_m"]["SouthRift"]))
        print("  -> terrain slope audit: max {:.2f}° | avg {:.2f}° | limit {}° | {}".format(
            profile["max_slope_deg"], profile["average_slope_deg"],
            p["max_expected_slope_deg"],
            "PASS" if profile["slope_within_design_limit"] else "FAIL"))
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

        print("[STAGE 5A/10] Altar hardening")
        altar_built = altar_rotation_module.generate_altar_obstacles(ctx)
        altar_repairs = altar_rotation_module.ensure_altar_clearance(ctx)
        print("  -> altar obstacles: {} (non-blocking)".format(len(altar_built)))
        for name, before, after in altar_repairs:
            print("  -> altar clearance repair: {} {:.2f}m -> {:.2f}m".format(name, before, after))

        print("[STAGE 6/10] Gameplay pockets (4 symmetrical)")
        pkts = pockets.generate_pockets(ctx)
        print("  -> pockets built: {} ({} objects)".format(len(ctx.pockets), len(pkts)))

        print("[STAGE 6A/10] Gameplay Cover 2.0")
        cover = gameplay_cover_module.run_gameplay_cover_pass(ctx)
        altar_repairs_after_cover = altar_rotation_module.ensure_altar_clearance(ctx)
        print("  -> objective gameplay cover: {} across {} objectives".format(
            cover["objective_cover_count"], cover["objectives_covered"]))
        for name, before, after in altar_repairs_after_cover:
            print("  -> post-cover altar clearance repair: {} {:.2f}m -> {:.2f}m".format(
                name, before, after))

        print("[STAGE 6B/10] Global outer elliptical perimeter")
        boundary.generate_outer_boundary(ctx)
        moved_boundary = gameplay_cover_module.repair_outer_boundary_for_legacy_bounds(ctx)
        print("  -> legacy-bounds boundary repair: {} sections adjusted".format(moved_boundary))

        bpy.context.view_layer.update()

        print("[STAGE 7/10] Navigation (obstacle-aware grid)")
        grid = build_grid(ctx)
        nav = run_navigation_checks(ctx, grid)
        nav["macro_rotation"] = altar_rotation_module.analyze_macro_rotation(ctx, nav)
        for prob in nav["problems"]:
            print("  [NAV] " + prob)
        print("  -> chokepoints detected: {}".format(len(nav["chokepoints"])))
        print("  -> pockets reachable: {}/{}".format(
            sum(1 for p in nav.get("pockets", []) if p["reachable"]),
            len(nav.get("pockets", []))))

        mr = nav["macro_rotation"]
        if mr["variance_s"] is not None:
            print("  -> macro rotation (adjacent objectives): avg {:.2f}s | min {:.2f}s | max {:.2f}s | variance {:.2f}s".format(
                mr["average_time_s"], mr["min_time_s"], mr["max_time_s"], mr["variance_s"]))

        print("[STAGE 7A/10] Height transitions (route + ramp audit)")
        height_transition_report = height_transitions_module.analyze_height_transitions(ctx, grid)
        print("  -> transition audit: {} routes | {} pocket transitions | {} ramps".format(
            len(height_transition_report["routes"]),
            len(height_transition_report["pocket_transitions"]),
            len(height_transition_report["ramps"])))
        print("  -> transition problems: routes={} pockets={} ramps={} | {}".format(
            height_transition_report["problem_route_count"],
            height_transition_report["problem_pocket_count"],
            height_transition_report["problem_ramp_count"],
            "PASS" if height_transition_report["passed"] else "REVIEW REQUIRED"))
        for r in height_transition_report["routes"]:
            if r.get("problems"):
                print("  [HEIGHT] {} -> {} | slope {:.2f}° | dz {:.3f}m | {}".format(
                    r["label"], r["classification"], r.get("max_local_slope_deg", -1.0),
                    r.get("max_adjacent_height_delta_m", -1.0), r["problems"]))
        for r in height_transition_report["ramps"]:
            if r.get("problems") or r.get("sampled_problems"):
                print("  [RAMP] {} | width={}m | slope={}° | {}".format(
                    r["name"], r.get("width_m"), r.get("sampled_max_slope_deg"),
                    r.get("problems") or r.get("sampled_problems")))
        _print_minion_traversal(height_transition_report.get("minion_traversal", {}))

        print("[STAGE 8/10] Combat simulation (5/5 capture points, nav-driven)")
        sim = simulation.run_simulation(ctx, grid, nav_report=nav)

        print("[STAGE 9/10] Validation")
        report = validation_module.run_validation(ctx, nav_report=nav)
        report["height_transitions"] = height_transition_report

        symmetry_errors, symmetry_summary = gameplay_symmetry_module.validate_gameplay_symmetry(ctx, cfg)
        report["gameplay_symmetry"] = symmetry_summary
        report["errors"].extend(symmetry_errors)
        report["ok"] = len(report["errors"]) == 0
        print("  -> GAMEPLAY SYMMETRY: {} | plane={} | tolerance={:.2f}m".format(
            "PASS" if symmetry_summary["passed"] else "FAIL",
            symmetry_summary["plane"], symmetry_summary["tolerance_m"]))
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

        _discard_generation_snapshot()
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
            "terrain_refinement": profile,
            "height_transitions": height_transition_report,
            "map_data": out_path,
        }

    except Exception as exc:
        if generation_started:
            print("\n[GENERATION ERROR] {}: {}".format(type(exc).__name__, exc))
            try:
                _restore_managed_scene(snapshot)
            except Exception as rollback_exc:
                print("[ROLLBACK ERROR] {}: {}".format(type(rollback_exc).__name__, rollback_exc))
        raise
