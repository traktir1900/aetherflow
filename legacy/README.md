# AetherFlow :: legacy/

This folder isolates **historical** generators that are NOT part of the active
v0.6.0 pipeline. They are kept only for reference and must never be executed.

## What belongs here

| File | Why it is legacy |
|------|------------------|
| `setup_files.py` | v0.4.0 self-extracting bootstrap. On run it **overwrites 14 modules** with the old 210 m map config — executing it would silently roll back the whole x2.5/v0.6.0 migration. |
| `AetherFlow_Map.blend.py` | Same v0.4.0 bootstrap (runs from a `.blend`). Same overwrite hazard. |

## Why they are dangerous

Both embed a full copy of the old module set and write it to disk
unconditionally. The active pipeline is now:

```
main.py -> core/pipeline.py -> (config, layout, heightmap, geometry, combat, navigation, validation, export)
```

The legacy scripts know nothing about `core/pipeline.py`, the unified scale,
the 200x200 m map, or `map_data.json`. Running them produces a conflicting,
out-of-date generator — exactly the "two competing pipelines" problem v0.6.0
removes.

## How to isolate (run once, in the repo root)

```bash
mkdir -p legacy
git mv setup_files.py legacy/setup_files.py
git mv AetherFlow_Map.blend.py legacy/AetherFlow_Map.blend.py
```

After moving, they remain in history for reference but are out of the active
tree. Nothing in the active pipeline imports or calls them.

## Rule

Do **not** run anything in this folder. If an old generator is ever needed for
archaeology, copy it to a scratch directory outside the project first.
