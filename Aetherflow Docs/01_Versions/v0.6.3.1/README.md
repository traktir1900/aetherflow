# AetherFlow v0.6.3.1 — Terrain Refinement

## Status

**IMPLEMENTED — RUNTIME VALIDATION PENDING**

## Purpose

Strengthen the readability of the existing terrain profile without rebuilding the map. The existing 5-objective layout, 2 bases, roads, ramps and 4 pockets remain fixed.

## NEW HARD PROJECT RULE — TEAM SYMMETRY

From v0.6.3 onward, **all team-critical gameplay geometry must be symmetric for both teams**.

The authoritative mirror is the world Y axis:

`(x, y, z) -> (-x, y, z)`

This is a balance invariant, not a visual preference.

The hard symmetry gate covers:

- Blue Base ↔ Red Base;
- WestMonolith ↔ EastMonolith;
- SWMonolith ↔ SEMonolith;
- roads and ramps that form team-critical routes;
- gameplay cover;
- pockets and pocket entrances;
- Altar protectors;
- central Core_Rock_* gameplay rocks;
- terrain height field;
- gameplay markers and future spawn/shop locations.

Allowed geometric tolerance: `0.25 m` unless a stricter subsystem-specific rule applies.

Decorative-only assets may vary, but they must never create a gameplay advantage. Any gameplay-critical asymmetry is a **validation error** and blocks a clean generation.

## Core rock refinement

The central rock system is required to be mirror-symmetric because central rocks affect line of sight, movement and combat space.

The intended generator contract is:

- even central-rock count only;
- canonical rocks on the +X half of the arena;
- exact geometric mirrors on the -X half;
- mirrored position, irregular silhouette and orientation across the Y axis;
- deterministic seeded generation;
- stable symmetry pair IDs;
- generation failure when the configured central-rock count is odd.

With the current `count_core = 6`, the central field is intended to be **3 mirror pairs / 6 rocks**.

## Safe failed-generation rollback

The active pipeline now snapshots all managed AetherFlow objects before Stage 1 clears the managed collections.

If any later generation stage raises an exception, the pipeline:

- reports the generation error;
- removes the incomplete generated managed scene;
- restores the pre-run managed objects from the temporary snapshot;
- leaves the user/hand-placed scene untouched;
- re-raises the original exception so the actual code error remains visible.

After a successful generation, the temporary snapshot is discarded.

This prevents a failed terrain or later-stage run from leaving Blender with only the partial perimeter/fence geometry.

## Objective-cover symmetry hardening

The fresh v0.6 auditor run on the generated map confirmed that the map is otherwise structurally healthy, but exposed a **real objective-cover generation defect**:

- WestMonolith ↔ EastMonolith objective cover symmetry: FAIL;
- SWMonolith ↔ SEMonolith objective cover symmetry: FAIL;
- Crown self-symmetry: FAIL;
- route fairness: `0.0%` difference;
- pockets: `4/4` reachable and mirrored;
- live Altar obstacles: `4` detected and symmetric;
- evaluated-mesh intersections: `0`;
- navigation problems: `0`;
- Deathball risk: LOW;
- Snowball risk: LOW.

Root cause: objective covers were selected independently in an objective-local tangent basis. That basis changes handedness under the world-Y mirror, so identical local coordinates did **not** guarantee mirrored world coordinates.

The generator has now been changed to:

- select one canonical cover plan for each mirrored objective pair;
- derive the opposite objective's positions from the exact world-space mirror `(x,y) -> (-x,y)`;
- convert the mirrored world position back into the target objective's local basis;
- construct Crown's second cover as an exact self-mirror;
- preserve the existing near/deep tactical rings and two-cover-per-objective contract.

The fix is committed in `core/gameplay_cover.py` and requires a fresh Blender 5.2 generation run before v0.6.3.1 can be marked complete.

## Auditor note

The standalone v0.6 auditor now correctly finds the four live `Altar_Obstacle_*` objects in Blender. Its `map_data.json` comparison still reports those objects as absent from the export path it inspects, even though the live scene contains all four. Treat that as an auditor/export-inspection mismatch, not as evidence that the four barriers are missing from the generated Blender scene.

The auditor also reports `Export Core Cover: 0` because the legacy central Core Cover pieces were intentionally removed in v0.6.2.1. This is expected; the new Altar composition uses the four dedicated `Altar_Obstacle_*` barricades instead.

## Changes

The shared analytic terrain profile applies bounded multipliers to the existing anchors:

- AetherCore depression: `×1.65`;
- Crown elevation: `×1.60`;
- West/East Monolith elevation: `×1.60`, identically;
- SouthRift depression: `×1.50`;
- central transition radius: `×1.10`.

These multipliers are applied at height evaluation time; the original spatial radii and layout coordinates remain unchanged.

The pipeline runs a dedicated `gameplay_symmetry` hard gate after normal validation. The result is exported inside the validation report and printed as `GAMEPLAY SYMMETRY: PASS/FAIL`.

## Terrain audit

The pipeline reports:

- effective height at AetherCore/Crown/WestMonolith/EastMonolith/SouthRift;
- sampled minimum and maximum terrain height;
- maximum sampled slope;
- average sampled slope;
- pass/fail against the `35°` design limit;
- explicit symmetry validation for the analytic terrain;
- explicit core-rock symmetry validation;
- explicit flags confirming topology, objective and base coordinates remain unchanged.

## Next test

Run the complete pipeline in Blender 5.2 and inspect:

1. central AetherCore slope/readability;
2. Crown and monolith elevation readability;
3. South Rift depression;
4. central rock layout from top view;
5. terrain slope audit;
6. **GAMEPLAY SYMMETRY: PASS**;
7. navigation reachability;
8. existing Altar/objective cover composition;
9. mesh intersections and validation errors.

Do not mark v0.6.3.1 complete until the fresh runtime confirms both gameplay balance symmetry and the existing gameplay metrics remain valid.
