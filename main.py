import sys
import os
import importlib
import bpy


# ==============================================================================
# 1. ОПРЕДЕЛЕНИЕ КОРНЯ ПРОЕКТА (PROJECT_ROOT)
# ==============================================================================

HARDCODED_ROOT = r"C:\Program Files\Blender Foundation\Blender 5.2\AetherFlow"

PROJECT_ROOT = ""
if "__file__" in globals() and __file__:
    path = os.path.abspath(__file__)
    while path and (not os.path.isdir(path) or path.lower().endswith(".blend")):
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    PROJECT_ROOT = path

# Перехват сброса пути до диска C:\
if not PROJECT_ROOT or len(PROJECT_ROOT.rstrip("\\/")) <= 3:
    PROJECT_ROOT = HARDCODED_ROOT

print("\n" + "=" * 60)
print("AETHER FLOW ROOT DIRECTORY:")
print(PROJECT_ROOT)
print("=" * 60)


# ==============================================================================
# 2. ИЗОЛЯЦИЯ SYS.PATH И СБРОС Python-КЭША
# ==============================================================================

FORBIDDEN_PATHS = {
    "c:\\", "c:/",
    "c:\\core", "c:/core",
    "c:\\geometry", "c:/geometry",
    "c:\\visual", "c:/visual",
    "c:\\combat", "c:/combat",
    "c:\\analysis", "c:/analysis",
    "c:\\navigation", "c:/navigation",
    "c:\\validators", "c:/validators"
}

# Очищаем sys.path от внешних конфликтующих папок
sys.path = [
    p for p in sys.path 
    if p.rstrip("\\/").lower() not in FORBIDDEN_PATHS
]

# Устанавливаем PROJECT_ROOT строго на индекс 0
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

# Полная очистка cached modules для всех пакетов проекта
PROJECT_NAMESPACES = (
    "core", 
    "geometry", 
    "visual", 
    "combat", 
    "analysis", 
    "navigation", 
    "validators"
)

for mod in list(sys.modules.keys()):
    if any(mod == ns or mod.startswith(ns + ".") for ns in PROJECT_NAMESPACES):
        del sys.modules[mod]

print("[INFO] Python module cache cleared successfully.")


# ==============================================================================
# 3. ИМПОРТ МОДУЛЕЙ ПАЙПЛАЙНА
# ==============================================================================

import core.config
import core.context
import core.utils
import core.layout
import core.heightmap

import visual.materials
import visual.decorations

import geometry.terrain
import geometry.core_geometry
import geometry.bases
import geometry.roads

import combat.combat_cover
import combat.ambush
import combat.sightlines


# ==============================================================================
# 4. ПРОВЕРКА ИСТОЧНИКА ЗАГРУЗКИ (ASSERTION)
# ==============================================================================

CHECK_MODULES = [
    core.config,
    core.context,
    core.utils,
    core.layout,
    core.heightmap,
    visual.materials,
    visual.decorations,
    geometry.terrain,
    geometry.core_geometry,
    geometry.bases,
    geometry.roads,
    combat.combat_cover,
    combat.ambush,
    combat.sightlines
]

print("\n========= MODULE PATH CHECK =========")
for m in CHECK_MODULES:
    print(f"{m.__name__:<25} => {getattr(m, '__file__', 'UNKNOWN')}")
print("====================================\n")

if not core.config.__file__.startswith(PROJECT_ROOT):
    raise RuntimeError(
        f"\n[CRITICAL ERROR] CORE MODULE LOADED FROM WRONG PATH!\n"
        f"Expected path starting with: {PROJECT_ROOT}\n"
        f"Actually loaded from:        {core.config.__file__}"
    )


# ==============================================================================
# 5. ГЛАВНЫЙ ЦИКЛ ГЕНЕРАЦИИ (PIPELINE EXECUTION)
# ==============================================================================

def run():
    print(">>> STARTING AETHER FLOW GENERATION (500m Scale) <<<")

    # Инициализация контекста
    try:
        ctx = core.context.MapContext(
            core.config.CONFIG,
            PROJECT_ROOT
        )
    except TypeError:
        ctx = core.context.MapContext(
            core.config.CONFIG
        )

    # Проверка размеров карты из конфига
    print("\nMAP SIZE CONFIGURATION:")
    if isinstance(ctx.config, dict):
        print("  ground_half_size:", ctx.config.get("ground_half_size", "N/A"))
        print("  map_radius:      ", ctx.config.get("map_radius", "N/A"))
        print("  base_radius:     ", ctx.config.get("base_radius", "N/A"))
    else:
        print("  ground_half_size:", getattr(ctx.config, "ground_half_size", "N/A"))
        print("  map_radius:      ", getattr(ctx.config, "map_radius", "N/A"))
        print("  base_radius:     ", getattr(ctx.config, "base_radius", "N/A"))
    print("-" * 40 + "\n")

    # 1. Очистка сцены и подготовка
    print("[INIT] Clearing scene...")
    core.utils.clear_scene()

    print("[INIT] Setting up collections...")
    core.utils.setup_collections(ctx)

    print("[INIT] Setting up materials...")
    visual.materials.setup_materials(ctx)

    # 2. Построение макета
    print("[BUILD] Layout...")
    ctx.layout = core.layout.build_layout(ctx.config)

    # 3. Генерация геометрии
    print("[GEN] Heightmapped terrain...")
    geometry.terrain.generate_heightmapped_terrain(ctx)

    print("[GEN] Core geometry and entrances...")
    geometry.core_geometry.generate_core_and_entrances(ctx)

    print("[GEN] Capture points & bases...")
    geometry.bases.generate_capture_points(ctx)
    geometry.bases.generate_bases(ctx)

    print("[GEN] Roads...")
    geometry.roads.generate_roads(ctx)

    # 4. Декорации и боевые зоны
    print("[GEN] Speed shrines and health relics...")
    visual.decorations.generate_speed_shrines_with_offset(ctx)
    visual.decorations.generate_3_health_relics(ctx)

    print("[GEN] Combat cover & South rift ambush...")
    combat.combat_cover.generate_core_combat_cover(ctx)
    combat.ambush.generate_south_rift_ambush(ctx)

    # 5. Проверка линий видимости
    print("[AUDIT] Sightlines...")
    combat.sightlines.audit_sightlines(ctx)

    bpy.context.view_layer.update()

    print("\n>>> AETHER FLOW MAP GENERATED SUCCESSFULLY <<<")


if __name__ == "__main__":
    run()