# AetherFlow UE5 Remote Control Bridge

## End-to-end architecture

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

Copy `asset_registry.example.json` to a project-owned location and replace empty asset paths with real paths from that UE5 project's Content Browser.

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

Supported registry modes:

- `blueprint`: spawn the registered Blueprint class.
- `static_mesh` / `auto_static_mesh`: spawn a StaticMeshActor with the registered mesh.
- Empty or missing asset: create a tagged marker when fallback is enabled.

## Synchronization

Generate the AetherFlow manifest through the existing Blender pipeline, then run from the repository root:

```text
python ue5_bridge/cli.py --manifest "C:\AetherFlow\export\manifest.json" --asset-registry "C:\AetherFlow\ue5\asset_registry.json"
```

The bridge:

1. Contacts the running Unreal Editor through Web Remote Control.
2. Executes the UE-side Python bridge.
3. Removes only previous AetherFlow-tagged actors when cleanup is enabled.
4. Reads semantic object records from manifest schema v2.
5. Converts Blender metres to Unreal centimetres.
6. Applies recorded location/rotation.
7. Spawns mapped Blueprint or Static Mesh assets.
8. Falls back to tagged markers for missing asset mappings.
9. Saves dirty UE packages.
10. Returns a machine-readable synchronization report.

Run without `--asset-registry` for structural marker import only.

## Current scope

The bridge carries object transforms and metadata from Blender to UE5. It establishes deterministic placement and explicit asset binding. It does not fabricate Landscape assets, materials, collision authoring or gameplay Blueprints; those remain explicit UE5 project assets/systems.

## Verification status

Repository implementation is isolated on the Bridge feature branch. Live Unreal execution requires the user's UE5 project with the required plugins enabled; live UE execution is **NOT TESTED** in this session.
