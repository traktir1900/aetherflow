# v0.6.2.1 — Local test note (2026-09-05)

## Latest Blender 5.2 runtime

The supplied run executed the `v0.6.2.1` pipeline from the `v0-6-2-1-cover-refinement` checkout.

Evidence:
- gameplay map: `200 x 200 m`;
- graded ramps built: `5`;
- procedural core rocks: `6`;
- Altar obstacles generated: `4` non-blocking;
- objective gameplay cover: `10` across `5` objectives;
- pockets: `4/4` reachable, each with `10.0 m` entry, `3` cover pieces and continuous perimeter;
- macro rotation: average `34.07 s`, min `26.55 s`, max `37.50 s`, variance `10.95 s`;
- navigation problems: `0`;
- evaluated-mesh intersections: `0`;
- Blue/Red average route-time difference: `0.0%`;
- auditor score: `89.8/100`;
- Altar camping risk: `HIGH` in the pasted auditor run;
- pasted auditor measured CoreCover-to-Altar minimum vertex clearance at `4.464 m`.

## Issues exposed by the run

1. The local validation executable still reported legacy `OuterBoundary_*` bbox errors. The repository validator contains a dedicated outer-boundary rule, but Blender can retain cached project modules between repeated Run Script operations.
2. The local runtime's Altar repair stage printed unchanged clearance values. The branch has since been changed to reload the project modules before every pipeline run and to repair from the closest real world-space mesh vertex iteratively.
3. The pasted auditor classified `AltarObstacles` as `0` even though its live LOS section observed all four `Altar_Obstacle_*` objects. This is a local auditor classification mismatch.
4. The latest pasted run did not show the previous `Core_Cover_Pocket_SE` vs `Core_Rock_06` overlap warning; evaluated-mesh intersections remained `0`.
5. The legacy auditor's `21.6 s` rotation variance is not the new macro-rotation metric. The pipeline now exports the real five-objective adjacent-ring metric (`34.07/26.55–37.50 s`, variance `10.95 s`).

## Code corrections after this run

- `core/altar_rotation.py`: closest-vertex iterative Altar clearance repair;
- `core/altar_rotation.py`: central `Core_Rock_*` outward repair;
- `core/pipeline.py`: explicit reload of `gameplay_cover`, `altar_rotation` and `validation` before each Blender pipeline rerun, eliminating stale-module mixing;
- branch remains `v0-6-2-1-cover-refinement`; no new development branch was created.

## Merge gate

Do not merge to `main` yet. Fresh Blender 5.2 regeneration is required after updating to the latest branch commit.

Required:
- validation has no genuine geometry errors;
- actual evaluated-mesh intersections = `0`;
- navigation problems = `0`;
- pockets reachable = `4/4`;
- objective gameplay cover = `10`;
- minimum CoreCover-to-Altar clearance >= `8.0 m`;
- four `Altar_Obstacle_*` objects present;
- `navigation.macro_rotation.all_reachable == true`.
