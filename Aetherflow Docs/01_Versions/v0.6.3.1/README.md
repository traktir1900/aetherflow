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

The intended generator contract is now stricter:

- even central-rock count only;
- one canonical rock per pair on the +X half of the arena;
- exact world-center mirror on the -X half;
- mirrored irregular silhouette;
- identical dimensions and gameplay footprint for both members;
- deterministic seeded generation;
- stable symmetry pair IDs;
- generation failure when the configured central-rock count is odd.

The rock mesh is kept in local coordinates and the world position is assigned separately. This prevents hidden mesh-space translation from producing the visible positional drift that was observed between the two sides.

With the current `count_core = 6`, the central field is **3 mirror pairs / 6 large gameplay rocks**.

## Objective-cover symmetry hardening

The fresh v0.6 auditor run exposed a real objective-cover symmetry defect. The generator was independently selecting cover in each objective-local tangent basis, which could produce different world-space positions after the Y-axis mirror.

The fix now selects one canonical cover plan for each mirrored objective pair and derives the other side from the exact world-space mirror `(x,y) -> (-x,y)`. Crown uses the same rule as a self-mirrored objective.

## Safe failed-generation rollback

The active pipeline now snapshots all managed AetherFlow objects before Stage 1 clears the managed collections.

If any later generation stage raises an exception, the pipeline:

- reports the generation error;
- removes the incomplete generated managed scene;
- restores the pre-run managed objects from the temporary snapshot;
- leaves the user/hand-placed scene untouched;
- re-raises the original exception so the actual code error remains visible.

After a successful generation, the temporary snapshot is discarded.

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
4. **large central rock pairs from top view — both sides must be exact Y-axis mirrors**;
5. terrain slope audit;
6. **GAMEPLAY SYMMETRY: PASS**;
7. navigation reachability;
8. existing Altar/objective cover composition;
9. mesh intersections and validation errors.

Do not mark v0.6.3.1 complete until the fresh runtime confirms both gameplay balance symmetry and the existing gameplay metrics remain valid.
