"""AetherFlow UE5 Editor-side bridge.

Runs inside Unreal Editor's Python environment. The script consumes the
AetherFlow manifest and creates a deterministic, tagged synchronization layer.
It intentionally uses lightweight Actor markers until project-specific assets
are mapped. This keeps the bridge independent from a particular art library.
"""
from __future__ import annotations

import json
import os
from typing import Any

import unreal


ROOT_NAME = "AetherFlow_BRIDGE"
TAG_PREFIX = "AetherFlow:" 


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("AetherFlow manifest root must be an object")
    return data


def _delete_previous_generated_actors() -> int:
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    doomed = [actor for actor in actors if any(str(tag).startswith(TAG_PREFIX) for tag in actor.tags)]
    if doomed:
        subsystem.destroy_actors(doomed)
    return len(doomed)


def _make_marker(name: str, group: str, index: int) -> unreal.Actor:
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if actor is None:
        raise RuntimeError(f"Failed to spawn bridge marker: {name}")
    actor.set_actor_label(name)
    actor.tags = [f"{TAG_PREFIX}{group}", f"{TAG_PREFIX}Index={index}"]
    return actor


def _manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    groups = manifest.get("export_groups") or {}
    return {
        "map_version": manifest.get("map_version"),
        "seed": manifest.get("seed"),
        "map_dimensions": manifest.get("map_dimensions"),
        "groups": {name: value.get("object_count", 0) for name, value in groups.items()},
    }


def sync_manifest(manifest_path: str, clear_previous: bool = True) -> dict[str, Any]:
    """Synchronize an AetherFlow manifest into the currently open UE Level.

    Phase 1 deliberately creates Editor-only synchronization markers rather
    than guessing which project assets represent each gameplay record.
    """
    manifest_path = os.path.abspath(manifest_path)
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(manifest_path)

    manifest = _load_json(manifest_path)
    if manifest.get("export_root") != "AetherFlow_EXPORT":
        raise ValueError("Unsupported or missing AetherFlow export_root")

    removed = _delete_previous_generated_actors() if clear_previous else 0
    groups = manifest.get("export_groups") or {}
    created = []

    for group_name in sorted(groups):
        if not isinstance(groups[group_name], dict):
            continue
        object_names = groups[group_name].get("objects") or []
        for index, object_name in enumerate(object_names):
            actor = _make_marker(str(object_name), str(group_name), index)
            created.append(actor.get_path_name())

    unreal.EditorAssetLibrary.save_dirty_packages(True, True)
    report = {
        "ok": True,
        "manifest": manifest_path,
        "removed_previous": removed,
        "created_markers": len(created),
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
            if text.startswith(TAG_PREFIX) and "Index=" not in text:
                groups[text[len(TAG_PREFIX):]] = groups.get(text[len(TAG_PREFIX):], 0) + 1
    return {"ok": True, "generated_actor_count": len(generated), "groups": groups}


if __name__ == "__main__":
    raise RuntimeError("Import this module and call sync_manifest(); do not execute it without a manifest path")
