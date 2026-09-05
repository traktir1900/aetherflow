# v0.6.2.1 — Local test note (2026-09-05)

## Latest Blender 5.2 runtime

The supplied run executed the `v0.6.2.1` pipeline from the `v0-6-2-1-cover-refinement` checkout.

Evidence:
- gameplay map: `200 x 200 m`;
- graded ramps built: `5`;
- procedural core rocks: `6`;
- Altar hardening stage started but failed while creating the new rectangular protectors;
- failure: `Matrix.Rotation(): axis of rotation for 3d and 4d matrices is required`;
- therefore the run did not reach pockets, navigation, validation or export after Stage 5A.

## Failure diagnosis

The new `_build_rectangular_protector()` used `Matrix.Rotation(rotation_z, 4)` without an explicit rotation axis. Blender 5.2 requires the axis argument for a 3D/4D rotation matrix. The error occurred before the barricade object could be finalized.

## Code corrections

- `core/altar_rotation.py`: fixed the Blender rotation call to `Matrix.Rotation(rotation_z, 4, 'Z')`;
- `core/altar_rotation.py`: uses explicit `Matrix`/`Vector` imports instead of dynamic `__import__` for this geometry path;
- `core/altar_rotation.py`: rectangular barricades remain centered on the Altar with exact cardinal positions and identical dimensions;
- `core/config.py`: explicit Altar protector geometry is now `3.6 m × 1.25 m × 2.4 m`, with `3.25 m` clearance from the Altar edge and `CARDINAL_CENTERED` layout;
- branch remains `v0-6-2-1-cover-refinement`; no new development branch was created.

## Altar protector balance contract

This is a gameplay invariant:

- exactly **4** Altar protectors;
- North/South and East/West are exact mirror pairs;
- positions are `(0,+R)`, `(+R,0)`, `(0,-R)`, `(-R,0)` around the exact Altar centre;
- all four pieces have identical geometry, dimensions and radial distance;
- Blue and Red approaches are mirror-equivalent;
- front/back is mirrored;
- protectors are non-blocking for navigation;
- protectors belong to the immediate Altar combat space.

## Merge gate

Do not merge to `main` yet. A fresh Blender 5.2 regeneration is required after this fix.

Required:
- pipeline completes all 10 stages;
- validation has no genuine geometry errors;
- actual evaluated-mesh intersections = `0`;
- navigation problems = `0`;
- pockets reachable = `4/4`;
- objective gameplay cover = `10`;
- minimum CoreCover-to-Altar clearance >= `8.0 m`;
- four `Altar_Obstacle_*` objects present;
- strict team symmetry of all four Altar protectors;
- protectors visibly centered close to the Altar on the four cardinal axes;
- `navigation.macro_rotation.all_reachable == true`.
