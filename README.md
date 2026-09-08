# AetherFlow 0.6.4.0

Procedural Blender pipeline for the AetherFlow arena map. It creates the
terrain, objectives, bases, roads, ramps, pockets, gameplay cover, resources,
navigation report, validation report and UE5 export manifest.

The current map contract is a 200 × 200 m gameplay arena with five objectives,
two mirrored team bases and four pockets. The project is inspired by the
capture-and-rotation structure of Dominion, while retaining its own world,
geometry and systems.

## Run

Open the project in Blender and execute `main.py`. The pipeline writes
`export/map_data.json` and `AetherFlow_UE5_Export/manifest.json` only when its
validation gate passes.

## Verification

Run the engine-free regression suite from the repository root:

```text
python tests/run_tests.py
```

Blender runtime validation remains required before a release or MAP LOCK.
