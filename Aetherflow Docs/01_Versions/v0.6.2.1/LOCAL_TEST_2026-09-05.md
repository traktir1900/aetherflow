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
- LOS now visibly detects the four cardinal Altar protectors: `N:Altar_Obstacle_01`, `E:Altar_Obstacle_02`, `S:Altar_Obstacle_03`, `W:Altar_Obstacle_04`.

The LOS evidence confirms the requested centered symmetric composition is now actually present in the generated scene, not only encoded in metadata.

## Remaining problems exposed by the run

1. `ensure_altar_clearance()` still logged unchanged values such as `-0.03 -> -0.03` and `0.24 -> 0.24`. The cause is stale Blender object transform/dependency-graph state while measuring `matrix_world` immediately after moving an object.
2. The local validator still reports legacy `OuterBoundary_*` bbox errors even though the boundary generation stage itself reports collision PASS. This remains a separate validation issue and is not considered solved.
3. The auditor still classifies `AltarObstacles: 0` despite the live LOS ray-cast detecting all four `Altar_Obstacle_*` objects. This is an auditor classification/export mismatch, not evidence that the objects are absent from the live scene.
4. The auditor's old `21.6 s` rotation value remains the legacy Base->CapturePoint metric; the pipeline's real adjacent-objective macro rotation remains `34.07/26.55–37.50 s`.
5. Altar camping remains `HIGH` in the current auditor because the surrounding CoreCover field is still too dominant near the Altar.

## Code corrections after this run

- `core/altar_rotation.py`: fixed Blender 5.2 `Matrix.Rotation(..., 'Z')` compatibility;
- `core/altar_rotation.py`: Altar protectors are now four chunky rectangular barricades on the cardinal axes around `(0,0)`;
- `core/altar_rotation.py`: identical protector dimensions and exact N/E/S/W mirror symmetry;
- `core/altar_rotation.py`: added explicit Blender dependency-graph sync after protector/cover/rock movement so world-space clearance measurements use updated transforms;
- `core/config.py`: Altar protector balance contract remains count `4`, centered cardinal layout, non-blocking navigation;
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

## Merge gate

Do not merge to `main` yet. A fresh Blender 5.2 regeneration is required after the latest transform-sync fix.

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
