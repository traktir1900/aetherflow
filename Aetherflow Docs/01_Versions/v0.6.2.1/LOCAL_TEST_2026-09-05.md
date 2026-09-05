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
5. The legacy auditor's `21.6 s` rotation variance is not the new macro-rotation metric. The pipeline now exports the real five-objective adjacent-ring metric (`34.07/26.55–37.50 s`).
6. The four Altar protectors were not visually close enough to the Altar centre and were arranged diagonally. This did not match the intended centered gameplay dressing.

## Code corrections after this run

- `core/altar_rotation.py`: closest-vertex iterative Altar clearance repair;
- `core/altar_rotation.py`: central `Core_Rock_*` outward repair;
- `core/altar_rotation.py`: Altar protectors now use a compact **cardinal-centered** layout at `(0,+R)`, `(+R,0)`, `(0,-R)`, `(-R,0)`, guaranteeing exact symmetry around the Altar under both X and Y reflection;
- `core/config.py`: explicit `altar_protectors` balance contract with `count=4`, `BOTH_AXES` symmetry, `CARDINAL_CENTERED` layout, `3.5 m` edge offset from the Altar, and fixed protector dimensions;
- `core/pipeline.py`: explicit reload of `gameplay_cover`, `altar_rotation` and `validation` before each Blender pipeline rerun, eliminating stale-module mixing;
- branch remains `v0-6-2-1-cover-refinement`; no new development branch was created.

## Altar protector balance contract

This is a gameplay invariant, not merely a visual preference:

- exactly **4** Altar protectors;
- exactly **2 mirror pairs**: North/South and East/West;
- all four pieces are centered on the Altar and placed on the four cardinal axes;
- Blue and Red approaches are mirror-equivalent under `x -> -x`;
- front/back placement is also mirrored under `y -> -y`;
- every protector has identical geometry, footprint, height and radial distance from the Altar centre;
- no protector may exist only on one team's side;
- protectors are non-blocking for navigation.

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
- strict team symmetry of all four Altar protectors;
- protectors are visibly centered close to the Altar on the four cardinal axes;
- `navigation.macro_rotation.all_reachable == true`.
