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

The previous central rock generator independently randomized each `Core_Rock_*` object. That is no longer allowed because central rocks affect line of sight, movement and combat space.

The new generator:

- requires an even central-rock count;
- creates canonical rocks on the +X half of the arena;
- creates exact geometric mirrors on the -X half;
- mirrors position, irregular silhouette and orientation across the Y axis;
- preserves deterministic seeded generation;
- tags every pair with a stable symmetry pair ID;
- fails generation when the configured central-rock count is odd.

With the current `count_core = 6`, the central field is exactly **3 mirror pairs / 6 rocks**.

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
