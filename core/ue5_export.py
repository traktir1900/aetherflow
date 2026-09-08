"""Deterministic UE5 export grouping and manifest generation.

The manifest contains semantic object records so the UE5 bridge can place
real project-owned assets without reverse-engineering Blender scene state.
"""
import json
import os

from core.version import get_version


EXPORT_ROOT = "AetherFlow_EXPORT"
EXPORT_GROUPS = (
    "Terrain", "Bases", "Objectives", "Roads", "Ramps", "Pockets",
    "Crown", "Altar", "Resources", "GameplayCover", "Boundary",
)
FORBIDDEN_PREFIXES = (
    "CapturePlatform_Crown", "Turret_Crown", "Blue_Shop", "Red_Shop",
    "EnvPerimeterSpire", "EnvironmentPerimeterSpire", "EnvHeightRidge",
    "AetherCoreNorthFrame", "CrownApproachLandmark01", "CrownApproachLandmark02",
)


def export_group_for_record(record):
    name = str(record.get("name", ""))
    kind = str(record.get("type", ""))
    meta = record.get("meta") or {}
    if name.startswith("Crown_") or name.startswith("CaptureButton_Crown") or name.startswith("CaptureIndicatorRing_Crown"):
        return "Crown"
    if name.startswith("Altar_") or kind in ("altar", "altar_obstacle"):
        return "Altar"
    if name.startswith(("SpeedShrine_", "HealthRelic_")) or meta.get("resource_type"):
        return "Resources"
    if name.startswith(("WestPocket_", "EastPocket_", "SWPocket_", "SEPocket_")) or "Pocket" in name:
        return "Pockets"
    if kind in ("terrain", "safety_floor"):
        return "Terrain"
    if kind == "base" or name.startswith(("Blue_", "Red_")):
        return "Bases"
    if kind in ("capture_point", "capture_button", "capture_indicator", "turret"):
        return "Objectives"
    if kind == "road" or name.startswith(("Road", "RingRoad")):
        return "Roads"
    if kind == "ramp" or name.startswith("Ramp_") or name.startswith("North_Ramp"):
        return "Ramps"
    if kind == "outer_boundary" or name.startswith("OuterBoundary_"):
        return "Boundary"
    if kind == "cover" or name.startswith(("ObjectiveCover_", "Core_Cover_")):
        return "GameplayCover"
    return "Terrain" if name.startswith("Terrain_") else "GameplayCover"


def _vec3(value):
    if value is None:
        return None
    return {"x": float(value[0]), "y": float(value[1]), "z": float(value[2])}


def _record_for_ue5(record, group):
    obj = record.get("object")
    location = rotation = scale = None
    dimensions = record.get("dimensions")
    if obj is not None:
        try:
            location = _vec3((obj.location.x, obj.location.y, obj.location.z))
            rotation = {"pitch": float(obj.rotation_euler.x * 57.29577951308232), "yaw": float(obj.rotation_euler.z * 57.29577951308232), "roll": float(obj.rotation_euler.y * 57.29577951308232)}
            scale = _vec3((obj.scale.x, obj.scale.y, obj.scale.z))
            dimensions = _vec3((obj.dimensions.x, obj.dimensions.y, obj.dimensions.z))
        except AttributeError:
            pass
    return {
        "name": str(record.get("name", "")),
        "type": str(record.get("type", "")),
        "group": group,
        "location_m": location,
        "rotation_deg": rotation,
        "scale": scale,
        "dimensions_m": dimensions,
        "meta": record.get("meta") or {},
    }


def build_manifest(ctx, validation=None, collection_report=None):
    grouped = {group: [] for group in EXPORT_GROUPS}
    legacy = []
    object_records = []
    for record in getattr(ctx, "generated_objects", []):
        name = str(record.get("name", ""))
        group = export_group_for_record(record)
        grouped[group].append(name)
        object_records.append(_record_for_ue5(record, group))
        if name.startswith(FORBIDDEN_PREFIXES):
            legacy.append(name)
    for names in grouped.values():
        names.sort()
    object_records.sort(key=lambda item: (item["group"], item["name"]))
    speed = [n for n in grouped["Resources"] if n.startswith("SpeedShrine_")]
    health = [n for n in grouped["Resources"] if n.startswith("HealthRelic_")]
    return {
        "schema_version": 2,
        "map_version": get_version(),
        "seed": ctx.config.get("seed"),
        "unit_system": {"source": "meters", "ue5": "centimeters"},
        "map_dimensions": [ctx.config.get("ground_half_size", 0) * 2] * 2,
        "objectives": {"logical": 5, "physical_capture_platforms": 4},
        "bases": 2,
        "pockets": 4,
        "resources": {"speed_shrines": len(speed), "health_relics": len(health), "total": len(speed) + len(health), "names": speed + health},
        "crown_mode": "PVE_LORD_SANCTUM",
        "export_root": EXPORT_ROOT,
        "export_groups": {group: {"object_count": len(names), "objects": names} for group, names in grouped.items()},
        "objects": object_records,
        "legacy_objects_present": legacy,
        "naming_passed": not legacy and len({n for names in grouped.values() for n in names}) == sum(len(names) for names in grouped.values()),
        "collection_report": collection_report or {"prepared": False, "reason": "NOT_RUN"},
        "validation_status": (validation or {}).get("ok") if validation else None,
    }


def prepare_collections(ctx):
    import bpy
    root = bpy.data.collections.get(EXPORT_ROOT) or bpy.data.collections.new(EXPORT_ROOT)
    if root.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(root)
    groups = {}
    for name in EXPORT_GROUPS:
        coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
        if coll.name not in root.children:
            root.children.link(coll)
        groups[name] = coll
    moved = 0
    missing = []
    for record in getattr(ctx, "generated_objects", []):
        obj = record.get("object")
        if obj is None:
            missing.append(record.get("name", "<unnamed>"))
            continue
        target = groups[export_group_for_record(record)]
        if target.objects.get(obj.name) is None:
            target.objects.link(obj)
        for coll in list(obj.users_collection):
            if coll != target:
                coll.objects.unlink(obj)
        moved += 1
    return {"prepared": not missing, "root": EXPORT_ROOT, "moved": moved, "missing": missing}


def write_manifest(ctx, package_root, validation=None, collection_report=None):
    manifest = build_manifest(ctx, validation=validation, collection_report=collection_report)
    for group in EXPORT_GROUPS:
        os.makedirs(os.path.join(package_root, group), exist_ok=True)
    os.makedirs(package_root, exist_ok=True)
    path = os.path.join(package_root, "manifest.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
    return path, manifest
