"""AetherFlow UE5 Editor-side bridge.

Consumes the AetherFlow manifest inside Unreal Editor. The bridge can spawn
project-owned Blueprint or Static Mesh assets from an explicit asset registry.
Missing assets fall back to deterministic tagged markers instead of silently
inventing project content.
"""
from __future__ import annotations

import json
import os
from typing import Any

import unreal


ROOT_NAME = "AetherFlow_BRIDGE"
TAG_PREFIX = "AetherFlow:"
BRIDGE_TAG = "AetherFlow:Bridge"


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _delete_previous_generated_actors() -> int:
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    doomed = [actor for actor in actors if any(str(tag).startswith(TAG_PREFIX) for tag in actor.tags)]
    if doomed:
        subsystem.destroy_actors(doomed)
    return len(doomed)


def _set_transform(actor: unreal.Actor, record: dict[str, Any]) -> None:
    location = record.get("location_m") or {}
    rotation = record.get("rotation_deg") or {}
    # AetherFlow uses metres; Unreal uses centimetres.
    loc = unreal.Vector(
        float(location.get("x", 0.0)) * 100.0,
        float(location.get("y", 0.0)) * 100.0,
        float(location.get("z", 0.0)) * 100.0,
    )
    rot = unreal.Rotator(
        float(rotation.get("pitch", 0.0)),
        float(rotation.get("yaw", 0.0)),
        float(rotation.get("roll", 0.0)),
    )
    actor.set_actor_transform(unreal.Transform(location=loc, rotation=rot), sweep=False, teleport=True)


def _tag_actor(actor: unreal.Actor, group: str, record: dict[str, Any], mode: str) -> None:
    name = str(record.get("name", "AetherFlow_Object"))
    actor.set_actor_label(name)
    actor.tags = [
        BRIDGE_TAG,
        f"{TAG_PREFIX}{group}",
        f"{TAG_PREFIX}Type={record.get('type', '')}",
        f"{TAG_PREFIX}Mode={mode}",
    ]
    metadata = record.get("meta") or {}
    for key in ("objective_id", "team", "resource_type", "role", "zone"):
        if key in metadata:
            actor.tags.append(f"{TAG_PREFIX}{key}={metadata[key]}")


def _make_marker(record: dict[str, Any]) -> unreal.Actor:
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if actor is None:
        raise RuntimeError(f"Failed to spawn bridge marker: {record.get('name')}")
    _set_transform(actor, record)
    _tag_actor(actor, str(record.get("group", "GameplayCover")), record, "marker")
    return actor


def _load_registry(path: str | None) -> dict[str, Any]:
    if not path:
        return {"registry_version": 1, "groups": {}, "fallback": {"enabled": True, "create_markers_when_asset_missing": True}}
    registry = _load_json(path)
    if registry.get("registry_version") != 1:
        raise ValueError("Unsupported UE5 asset registry version")
    return registry


def _load_asset(asset_path: str):
    if not asset_path:
        return None
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset is None:
        unreal.log_warning(f"[AetherFlow UE5] Asset not found: {asset_path}")
    return asset


def _spawn_real_asset(record: dict[str, Any], asset_spec: dict[str, Any]) -> unreal.Actor | None:
    mode = str(asset_spec.get("mode", ""))
    asset_path = str(asset_spec.get("asset", ""))
    if not asset_path:
        return None
    asset = _load_asset(asset_path)
    if asset is None:
        return None
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    location = record.get("location_m") or {}
    rotation = record.get("rotation_deg") or {}
    loc = unreal.Vector(float(location.get("x", 0)) * 100.0, float(location.get("y", 0)) * 100.0, float(location.get("z", 0)) * 100.0)
    rot = unreal.Rotator(float(rotation.get("pitch", 0)), float(rotation.get("yaw", 0)), float(rotation.get("roll", 0)))

    actor = None
    if mode in ("blueprint", "class"):
        asset_data = unreal.EditorAssetLibrary.find_asset_data(asset_path)
        if not asset_data.is_valid():
            return None
        actor_class = asset_data.get_asset() if hasattr(asset_data, "get_asset") else None
        if hasattr(asset_data, "get_asset_class"):
            loaded_class = unreal.EditorAssetLibrary.load_blueprint_class(asset_path)
            if loaded_class:
                actor = subsystem.spawn_actor_from_class(loaded_class, loc, rot)
        if actor is None and isinstance(actor_class, type):
            actor = subsystem.spawn_actor_from_class(actor_class, loc, rot)
    elif mode in ("static_mesh", "auto_static_mesh") and isinstance(asset, unreal.StaticMesh):
        actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        if actor is not None:
            component = actor.static_mesh_component
            component.set_static_mesh(asset)
    if actor is not None:
        _tag_actor(actor, str(record.get("group", "GameplayCover")), record, mode)
    return actor


def _manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    groups = manifest.get("export_groups") or {}
    return {
        "schema_version": manifest.get("schema_version"),
        "map_version": manifest.get("map_version"),
        "seed": manifest.get("seed"),
        "map_dimensions": manifest.get("map_dimensions"),
        "groups": {name: value.get("object_count", 0) for name, value in groups.items()},
    }


def sync_manifest(manifest_path: str, registry_path: str | None = None, clear_previous: bool = True) -> dict[str, Any]:
    manifest_path = os.path.abspath(manifest_path)
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(manifest_path)
    manifest = _load_json(manifest_path)
    if manifest.get("export_root") != "AetherFlow_EXPORT":
        raise ValueError("Unsupported or missing AetherFlow export_root")

    registry = _load_registry(registry_path)
    removed = _delete_previous_generated_actors() if clear_previous else 0
    created_real = 0
    created_markers = 0
    skipped = 0
    failures = []

    for record in manifest.get("objects") or []:
        group = str(record.get("group", "GameplayCover"))
        spec = (registry.get("groups") or {}).get(group) or {}
        actor = _spawn_real_asset(record, spec)
        if actor is not None:
            created_real += 1
            continue
        if (registry.get("fallback") or {}).get("create_markers_when_asset_missing", True):
            try:
                _make_marker(record)
                created_markers += 1
            except Exception as exc:
                failures.append({"name": record.get("name"), "error": str(exc)})
        else:
            skipped += 1

    unreal.EditorAssetLibrary.save_dirty_packages(True, True)
    report = {
        "ok": not failures,
        "manifest": manifest_path,
        "registry": os.path.abspath(registry_path) if registry_path else None,
        "removed_previous": removed,
        "created_real_assets": created_real,
        "created_markers": created_markers,
        "skipped": skipped,
        "failures": failures,
        "summary": _manifest_summary(manifest),
    }
    unreal.log(f"[AetherFlow UE5] Sync complete: {report}")
    return report


def validate_bridge_state() -> dict[str, Any]:
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    generated = [a for a in actors if any(str(tag).startswith(TAG_PREFIX) for tag in a.tags)]
    groups: dict[str, int] = {}
    for actor in generated:
        for tag in actor.tags:
            text = str(tag)
            if text.startswith(TAG_PREFIX) and "Index=" not in text and "Type=" not in text and "Mode=" not in text and "Bridge" not in text:
                groups[text[len(TAG_PREFIX):]] = groups.get(text[len(TAG_PREFIX):], 0) + 1
    return {"ok": True, "generated_actor_count": len(generated), "groups": groups}


if __name__ == "__main__":
    raise RuntimeError("Import this module and call sync_manifest(); do not execute it without a manifest path")
