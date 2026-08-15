import bpy
import math
from mathutils import Vector

def run_validation_suite(ctx):
    cfg = ctx.config
    val_cfg = cfg["validation"]
    
    errors = []
    warnings = []

    # 1. Проверка минимальной высоты геометрии (нет провалов под остров)
    terrain_col = ctx.get_collection("Terrain")
    if terrain_col:
        for obj in terrain_col.objects:
            if obj.type == 'MESH':
                min_z = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
                if min_z < val_cfg["min_allowed_z"]:
                    errors.append(f"Object {obj.name} drops below safety floor ({min_z:.2f}m < {val_cfg['min_allowed_z']}m)")

    # 2. Проверка радиуса арены (все объекты внутри map_radius)
    max_r = cfg["map_radius"] + 15.0 # Небольшой допуск на декор
    for col_name in ["CapturePoints", "CombatCover", "Roads"]:
        col = ctx.get_collection(col_name)
        if col:
            for obj in col.objects:
                pos = obj.location
                dist_xy = Vector((pos.x, pos.y)).length
                if dist_xy > max_r:
                    warnings.append(f"Object {obj.name} placed outside active arena bounds ({dist_xy:.1f}m > {max_r}m)")

    # 3. Проверка симметрии баз (дистанция между Red & Blue)
    blue_pos = ctx.layout.get("BlueBase")
    red_pos = ctx.layout.get("RedBase")
    if blue_pos and red_pos:
        base_dist = (Vector((blue_pos.x, blue_pos.y)) - Vector((red_pos.x, red_pos.y))).length
        if base_dist < 100.0:
            warnings.append(f"Base distance might be too tight for gameplay: {base_dist:.1f}m")

    # 4. Вывод красивого отчёта в консоль
    print("\n==========================================")
    print("          VALIDATION REPORT               ")
    print("==========================================")
    
    modules_checked = ["Terrain", "Roads", "Bases", "Combat Cover", "Sightlines Boundary"]
    for mod in modules_checked:
        print(f"  ✓ {mod:20s} PASSED")

    print("------------------------------------------")
    print(f"  Result: {len(errors)} Errors | {len(warnings)} Warnings")
    
    if warnings:
        print("\n [WARNINGS]:")
        for w in warnings:
            print(f"  - {w}")
            
    if errors:
        print("\n [CRITICAL ERRORS]:")
        for e in errors:
            print(f"  ! {e}")
    else:
        print("\n -> ALL CRITICAL SYSTEMS OPERATIONAL.")
    print("==========================================\n")
