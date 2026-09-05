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
- auditor score: `89.5/100`;
- Altar camping risk improved from `HIGH` to `MEDIUM`;
- auditor measured CoreCover-to-Altar minimum vertex clearance at `23.512 m` in the exported scene.

## Issues exposed by the run

1. The local validation executable used during this run still reported legacy `OuterBoundary_*` bbox errors even though the current repository validator contains a dedicated outer-boundary inner-face check. This indicates a stale/local validator mismatch rather than a proven boundary-geometry failure.
2. The same run reported one solid-overlap warning between `Core_Cover_Pocket_SE` and `Core_Rock_06` (`0.474 m`), so the central rock placement was still too close to the repaired CoreCover geometry.
3. The pasted auditor used on the local machine still classified `AltarObstacles` as `0` even though the live LOS scan observed all four `Altar_Obstacle_*` objects. This is an auditor-version/classification mismatch, not evidence that the generator failed to create them.
4. The legacy auditor's `21.6 s` rotation variance remains an approximation over Base→CapturePoint routes. The new pipeline now exports a separate real five-objective adjacent-ring macro-rotation metric (`34.07/26.55–37.50 s`).

## Latest code corrections after this run

- `core/altar_rotation.py` now repairs Altar clearance from the closest real world-space mesh vertex using deterministic iterations, rather than assuming the object pivot radial is the limiting point.
- The same repair stage pushes `Core_Rock_*` anchors outward so central secondary rocks cannot recreate CoreCover overlap after the Altar/cover repair.
- The branch remains `v0-6-2-1-cover-refinement`; no new development branch was created.

## Merge gate

Do not merge to `main` until a fresh Blender 5.2 regeneration confirms:
- validation has no genuine geometry errors;
- actual evaluated-mesh intersections remain `0`;
- navigation problems remain `0`;
- pockets remain `4/4` reachable;
- objective gameplay cover remains `10`;
- Altar minimum CoreCover clearance is `>= 8.0 m`;
- the four `Altar_Obstacle_*` objects are present;
- `navigation.macro_rotation.all_reachable == true`.
