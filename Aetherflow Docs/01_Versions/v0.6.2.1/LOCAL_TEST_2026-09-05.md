# v0.6.2.1 — Local test note (2026-09-05)

## Latest Blender 5.2 runtime before v0.6.3.1

The supplied run executed the `v0.6.2.1` pipeline from the `v0-6-2-1-cover-refinement` checkout.

Evidence:
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
- LOS visibly detected the four cardinal Altar protectors: `N:Altar_Obstacle_01`, `E:Altar_Obstacle_02`, `S:Altar_Obstacle_03`, `W:Altar_Obstacle_04`.

## Problems carried into v0.6.3.1

1. The six inherited `Core_Cover_*` objects cluttered the immediate Altar combat space and were removed intentionally. The four dedicated Altar barricades remain.
2. The local validator still reports legacy `OuterBoundary_*` bbox errors even though boundary generation reports collision PASS.
3. The old auditor still reports `AltarObstacles: 0` even though live LOS sees all four protectors. This is classification/export mismatch.
4. The old auditor's `21.6 s` rotation value is a legacy Base->CapturePoint metric; the pipeline's real adjacent-objective macro rotation is `34.07/26.55–37.50 s`.
5. Terrain readability was too weak in the original analytic profile because the scaled landmark height differences were shallow. v0.6.3.1 addresses this without changing XY topology.

## v0.6.3.1 terrain refinement

Implemented on the SAME branch:
- new `core/terrain_refinement.py` shared terrain profile;
- AetherCore depression strengthened by a bounded multiplier;
- Crown elevation strengthened by a bounded multiplier;
- West/East Monolith elevation strengthened equally;
- South Rift depression strengthened by a bounded multiplier;
- central transition radius widened slightly to keep slopes gradual;
- terrain audit added to the pipeline with landmark heights and sampled max/average slope;
- design slope target is `< 35°`;
- objective coordinates, base coordinates and topology remain unchanged;
- VERSION bumped to `0.6.3.1`.

## Current status

v0.6.3.1 is **implemented but not yet runtime-validated**. Fresh Blender 5.2 generation is required before the terrain refinement can be marked complete.

## Merge gate

Do not merge to `main` yet.

Required after fresh generation:
- pipeline completes all 10 stages;
- terrain slope audit passes `< 35°`;
- validation has no genuine geometry errors;
- evaluated-mesh intersections = `0`;
- navigation problems = `0`;
- pockets reachable = `4/4`;
- objective gameplay cover = `10`;
- four `Altar_Obstacle_*` objects present and centered/symmetric;
- existing Blue/Red fairness remains within tolerance;
- `navigation.macro_rotation.all_reachable == true`.

All work remains on `v0-6-2-1-cover-refinement`; no new development branch was created.
