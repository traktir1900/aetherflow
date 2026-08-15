
import time
from mathutils import Vector
from validators.base_validator import ValidationResult

def validate_bounds(ctx):
    start = time.perf_counter()
    res = ValidationResult("Arena Bounds")
    cfg = ctx.config
    max_r = cfg["map_radius"] + 15.0

    for col_name in ["CapturePoints", "CombatCover", "Roads"]:
        col = ctx.get_collection(col_name)
        if col:
            for obj in col.objects:
                dist = Vector((obj.location.x, obj.location.y)).length
                if dist > max_r:
                    res.warnings.append(f"Object {obj.name} outside radius ({dist:.1f}m)")

    res.duration = time.perf_counter() - start
    return res
