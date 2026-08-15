import time
import bpy

import core.logger as logger
import core.utils as utils
import core.layout as layout
import core.heightmap as heightmap
import core.validation as validation

import geometry.terrain as terrain
import geometry.core_geometry as core_geometry
import geometry.bases as bases
import geometry.ramps as ramps
import geometry.roads as roads

import visual.materials as materials
import visual.decorations as decorations

import combat.combat_cover as combat_cover
import combat.cover_balance as cover_balance
import combat.cover_orientation as cover_orientation
import combat.cover_rules as cover_rules
import combat.cover_variants as cover_variants
import combat.ambush as ambush
import combat.ambush_ecology as ambush_ecology
import combat.sightlines as sightlines
import combat.traversal_metrics as traversal_metrics
import combat.cover_analysis as cover_analysis

import validators.registry as validator_registry


def run_pipeline(ctx):
    start_time = time.time()

    print("\n" + "=" * 70)
    print(">>> PIPELINE EXECUTION: AETHER FLOW v0.5.7.2 <<<")
    print("=" * 70)

    # 1. Проверка масштаба
    cfg = ctx.config if isinstance(ctx.config, dict) else ctx.config.__dict__
    ground_half_size = cfg.get("ground_half_size", 0)

    print(f"[PIPELINE] Target ground_half_size: {ground_half_size}")
    if ground_half_size < 200.0:
        raise ValueError(
            f"[CRITICAL ERROR] Detected old config! ground_half_size = {ground_half_size}. "
            f"Expected >= 250.0 for v0.5.7.2 scale."
        )

    # 2. Подготовка сцены
    print("\n[STAGE 1/6] Scene Cleanup & Materials Setup...")
    utils.clear_scene()
    utils.setup_collections(ctx)
    materials.setup_materials(ctx)

    # 3. Макет и карта высот
    print("\n[STAGE 2/6] Building Layout & Heightmap Grid...")
    ctx.layout = layout.build_layout(ctx.config)
    if hasattr(heightmap, "generate_heightmap"):
        heightmap.generate_heightmap(ctx)

    # 4. Геометрия
    print("\n[STAGE 3/6] Constructing Terrain & World Geometry...")
    terrain.generate_heightmapped_terrain(ctx)
    core_geometry.generate_core_and_entrances(ctx)
    bases.generate_capture_points(ctx)
    bases.generate_bases(ctx)

    if hasattr(ramps, "generate_ramps"):
        print("  -> Generating vertical access ramps...")
        ramps.generate_ramps(ctx)

    roads.generate_roads(ctx)

    # 5. Декорации и укрытия
    print("\n[STAGE 4/6] Placing Props, Cover System & Ambush Ecology...")
    decorations.generate_speed_shrines_with_offset(ctx)
    decorations.generate_3_health_relics(ctx)

    combat_cover.generate_core_combat_cover(ctx)
    if hasattr(cover_balance, "balance_tactical_cover"):
        cover_balance.balance_tactical_cover(ctx)

    ambush.generate_south_rift_ambush(ctx)
    if hasattr(ambush_ecology, "apply_ambush_ecology"):
        ambush_ecology.apply_ambush_ecology(ctx)

    # 6. Валидаторы
    print("\n[STAGE 5/6] Executing Validators & Traversal Metrics...")
    if hasattr(validator_registry, "run_all_validators"):
        validator_registry.run_all_validators(ctx)
    elif hasattr(validator_registry, "validate_all"):
        validator_registry.validate_all(ctx)

    if hasattr(traversal_metrics, "calculate_traversal_metrics"):
        traversal_metrics.calculate_traversal_metrics(ctx)

    # 7. Линии видимости
    print("\n[STAGE 6/6] Auditing Sightlines & Exporting Reports...")
    sightlines.audit_sightlines(ctx)

    if hasattr(cover_analysis, "export_cover_report"):
        cover_analysis.export_cover_report(ctx)

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 70)
    print(f">>> PIPELINE v0.5.7.2 FINISHED SUCCESSFULLY IN {elapsed}s <<<")
    print("=" * 70 + "\n")