# AetherFlow UE5 Export Foundation

## Status

Implemented in source; Blender runtime export remains required before this is
marked validated.

## Authoritative object model

- Five logical objectives remain available to navigation and simulation.
- Four normal physical capture platforms exist: EastMonolith, SEMonolith,
  SWMonolith and WestMonolith.
- Crown is `PVE_LORD_SANCTUM`. It has no `CapturePlatform_Crown` and no
  `Turret_Crown`.
- `CaptureButton_Crown` and `CaptureIndicatorRing_Crown` remain deterministic
  logical/export anchors, seated on `Crown_BossRise` and kept distinct from
  `Crown_BossButton`.

## Export collections

At pipeline Stage 10, `core.ue5_export` moves every registered generated object
into exactly one child collection of `AetherFlow_EXPORT`:

```text
AetherFlow_EXPORT/
├── Terrain
├── Bases
├── Objectives
├── Roads
├── Ramps
├── Pockets
├── Crown
├── Altar
├── Resources
├── GameplayCover
└── Boundary
```

The stage also writes `AetherFlow_UE5_Export/manifest.json` and creates a
directory for each group. It does not create a monolithic FBX; per-collection
geometry export is intentionally left to the Blender/UE5 export operator.

## Manifest contract

The manifest records map version/seed/dimensions, logical and physical
objective counts, bases, pockets, the exact three Speed Shrines and eight
Health Relics, Crown mode, per-group object names/counts, legacy-name findings,
collection preparation status and validation status.

## Runtime gate

Before UE5 handoff, run Blender 5.2 and verify the generated collections,
actual transforms, isolated per-collection exports, collision, navigation,
minion traversal, symmetry, resource counts, legacy-object absence and final
validation. Source tests alone do not constitute a Blender/FBX validation.
