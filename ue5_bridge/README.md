# AetherFlow UE5 Remote Control Bridge v1

## Purpose

This package creates the first executable bridge between the AetherFlow generator and Unreal Editor.

Architecture:

```text
AetherFlow / Blender
        |
        | manifest.json
        v
external ue5_bridge/cli.py
        |
        | HTTP JSON
        v
UE5 Remote Control API :30010
        |
        | ExecutePythonCommand
        v
Content/Python/aetherflow_ue5_bridge.py
        |
        v
Current Unreal Level
```

Unreal's Remote Control API exposes HTTP endpoints for calling Blueprint-callable functions and batching requests. The default HTTP port is 30010, configurable in Project Settings. The Python Editor Script Plugin is required for the Python-side bridge. See the official Epic documentation before enabling this in a project distributed outside development environments.

## UE5 setup

Enable these Editor plugins:

- Web Remote Control
- Python Editor Script Plugin
- Editor Scripting Utilities

Copy `ue5/aetherflow_ue5_bridge.py` into the UE project's `Content/Python/` folder, or add the directory containing that file to the UE Python path.

Make sure Web Remote Control is listening on `127.0.0.1:30010` (or configure another host/port in the CLI).

## First synchronization

Generate an AetherFlow `manifest.json` with the existing Blender pipeline, then run from a normal Python installation:

```text
python ue5_bridge/cli.py --manifest "C:\path\to\manifest.json"
```

The bridge connects to the currently running Unreal Editor and executes the UE-side synchronization script.

## v1 behavior

v1 deliberately creates tagged Editor actors as synchronization markers. It does **not** guess project-specific art assets, collision meshes, materials, Landscape assets, or gameplay Blueprints.

Tags use the prefix `AetherFlow:` and group names such as `AetherFlow:Terrain`, `AetherFlow:Objectives`, `AetherFlow:Roads`, etc.

Running synchronization again removes only actors carrying the AetherFlow bridge tags unless `--keep-generated` is supplied.

## Next implementation layer

The next bridge milestone is an explicit project asset registry, for example:

```json
{
  "Terrain": {"asset": "/Game/AetherFlow/Meshes/M_AetherTerrain"},
  "Objectives": {"asset": "/Game/AetherFlow/Blueprints/BP_AetherObjective"},
  "Bases": {"asset": "/Game/AetherFlow/Blueprints/BP_AetherBase"}
}
```

The registry must be project-owned. AetherFlow remains the source of truth for map topology and generated metadata; UE5 remains the authority for engine assets, actors, collision, navigation and runtime gameplay.
