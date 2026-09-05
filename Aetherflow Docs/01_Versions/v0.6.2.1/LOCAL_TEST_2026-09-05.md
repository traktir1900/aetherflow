# v0.6.2.1 — Local test note (2026-09-05)

## Latest Blender 5.2 runtime

The latest supplied run executed the `v0.6.2.1` pipeline from `v0-6-2-1-cover-refinement`.

### Successful sections
- gameplay map: `200 x 200 m`;
- graded ramps built: `5`;
- procedural core rocks: `6`;
- Altar protectors generated: `4` non-blocking;
- objective gameplay cover: `10` across `5` objectives;
- pockets: `4/4` reachable, `10.0 m` entry, `3` cover pieces each;
- macro rotation: average `34.07 s`, min `26.55 s`, max `37.50 s`, variance `10.95 s`;
- navigation problems: `0`;
- evaluated-mesh intersections: `0`;
- Blue/Red average route-time difference: `0.0%`;
- LOS visibly detects the four cardinal Altar protectors.

## User-requested Altar cleanup

The red-marked objects in the supplied Blender view were the six inherited `Core_Cover_*` pieces surrounding the Altar. They were visually cluttering the central combat space and were removed from the generated scene.

The intended Altar dressing is now only the four dedicated, symmetric `Altar_Obstacle_*` barricades in the immediate N/E/S/W positions. `ObjectiveCover_*` objects elsewhere on the five capture points are unchanged.

## Code correction

- `core/altar_rotation.py`: added `remove_legacy_core_cover(ctx)`, which removes all `Core_Cover_*` objects from both generated-object tracking and the live Blender scene while leaving `ObjectiveCover_*` untouched;
- `core/altar_rotation.py`: `ensure_altar_clearance()` is now a compatibility cleanup stage rather than a repair for the removed legacy CoreCover field;
- `core/altar_rotation.py`: retained Blender 5.2-safe `Matrix.Rotation(rotation_z, 4, 'Z')` for the four Altar barricades;
- branch remains `v0-6-2-1-cover-refinement`; no new development branch was created.

## Altar protector balance contract

This is a gameplay invariant:

- exactly **4** Altar protectors;
- exact North/South and East/West mirror pairs;
- positions `(0,+R)`, `(+R,0)`, `(0,-R)`, `(-R,0)` around the exact Altar centre;
- all four pieces have identical geometry, dimensions and radial distance;
- Blue and Red approaches are mirror-equivalent;
- front/back is mirrored;
- protectors are non-blocking for navigation;
- protectors belong to the immediate Altar combat space.

## Remaining separate validation issues

1. The local validator still reports legacy `OuterBoundary_*` bbox errors. This is separate from the Altar cleanup and is not being hidden.
2. The auditor's `AltarObstacles: 0` classification is stale/inconsistent with live LOS detection; this should be corrected separately.
3. The auditor's old rotation metric is still the legacy Base->CapturePoint metric; the pipeline's adjacent-objective macro metric remains separate.

## Merge gate

Do not merge to `main` yet. A fresh Blender 5.2 regeneration is required after the Altar cleanup.

Required:
- pipeline completes all 10 stages;
- validation has no genuine geometry errors;
- actual evaluated-mesh intersections = `0`;
- navigation problems = `0`;
- pockets reachable = `4/4`;
- objective gameplay cover = `10`;
- four `Altar_Obstacle_*` objects present;
- strict team symmetry of all four Altar protectors;
- protectors visibly centered close to the Altar on the four cardinal axes;
- `navigation.macro_rotation.all_reachable == true`.
