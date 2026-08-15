
import time
from validators.base_validator import ValidationResult
from validators.registry import register_validator

@register_validator
def validate_terrain(ctx):
    start = time.perf_counter()
    res = ValidationResult("Terrain Bounds")
    cfg = ctx.config
    val_cfg = cfg["validation"]

    terrain_col = ctx.get_collection("Terrain")
    if terrain_col:
        for obj in terrain_col.objects:
            if obj.type == 'MESH':
                min_z = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
                if min_z < val_cfg["min_allowed_z"]:
                    res.errors.append(f"Object {obj.name} drops below floor ({min_z:.2f}m)")

    res.duration = time.perf_counter() - start
    return res
