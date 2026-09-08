# AetherFlow UE5 Remote Control Bridge

## Architecture

```text
AetherFlow / Blender
        |
        | manifest.json (schema v2)
        | semantic objects + transforms + metadata
        v
external ue5_bridge/cli.py
        |
        | HTTP JSON
        v
UE5 Web Remote Control :30010
        |
        | ExecutePythonCommand
        v
Content/Python/aetherflow_ue5_bridge.py
        |
        +--> explicit project asset registry
        |       |
        |       +--> Blueprint actors
        |       +--> Static Mesh actors
        |
        +--> deterministic marker fallback
        v
Current Unreal Level
```

AetherFlow remains the source of truth for topology, object identity and generated metadata. Unreal remains the authority for project assets, actor instances, collision, navigation, rendering and runtime gameplay.

## UE5 setup

Enable these Editor plugins:

- Web Remote Control
- Python Editor Script Plugin
- Editor Scripting Utilities

Copy `ue5/aetherflow_ue5_bridge.py` into the UE project's `Content/Python/` folder, or add the directory to the UE Python path.

Configure Web Remote Control on `127.0.0.1:30010` or pass another host/port to the CLI.

## Asset registry

Start from `asset_registry.example.json` and create a project-owned registry. Do not put guessed or machine-specific asset paths into AetherFlow core code.

Example:

```json
{
  "registry_version": 1,
  "groups": {
    "Bases": {"mode": "blueprint", "asset": "/Game/AetherFlow/Blueprints/BP_AetherBase"},
    "Objectives": {"mode": "blueprint", "asset": "/Game/AetherFlow/Blueprints/BP_AetherObjective"},
    "Roads": {"mode": "auto_static_mesh", "asset": "/Game/AetherFlow/Meshes/SM_AetherRoad"}
  },
  "fallback": {"enabled": true, "create_markers_when_asset_missing": true}
}
```

Supported registry modes in v2:

- `blueprint`: spawn the registered Blueprint class.
- `static_mesh` / `auto_static_mesh`: spawn a StaticMeshActor with the registered mesh.
- missing/empty asset: create a tagged synchronization marker when fallback is enabled.

## Synchronization

Generate the AetherFlow manifest through the existing Blender pipeline, then run:

```text
python ue5_bridge/cli.py --manifest "C:\path\to\manifest.json" --asset-registry "C:\path\to\asset_registry.json"
```

The bridge removes only previous AetherFlow-tagged actors, converts metres to Unreal centimetres, preserves transforms and metadata, spawns mapped project assets where possible, and reports fallback markers/failures.

Run without an asset registry for a safe structural import using markers only.

## Verification status

The repository implementation is statically reviewed and isolated on the feature branch. Live execution requires a running Unreal Editor project with the required plugins enabled; that environment is not available inside this development session, so live UE execution is **NOT TESTED** here.
