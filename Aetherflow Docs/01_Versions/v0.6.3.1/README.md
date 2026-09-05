# AetherFlow v0.6.3.1 — Terrain Refinement

## Status

**BALANCE VALIDATED — CLOSED; TECHNICAL PERIMETER/EXPORT WARNINGS REMAIN**

## Result

Fresh Blender 5.2 runtime validated the gameplay-balance targets:

- Blue/Red average route time: **19.1 s / 19.1 s**;
- Blue/Red fairness difference: **0.0% — BALANCED**;
- nearest objective distance: **45.3 m / 45.3 m**;
- 4/4 gameplay pockets reachable and mirrored;
- objective cover symmetry: **PASS** for West↔East, SW↔SE and Crown;
- 4 live Altar_Obstacle_* objects present and symmetric;
- evaluated-mesh intersections: **0**;
- navigation problems: **0**;
- Deathball risk: **LOW**;
- Snowball risk: **LOW**;
- 4 flank/comeback pockets available.

Overall auditor score: **89.0/100**. The remaining deductions/warnings are technical validation/export issues, not team-balance asymmetry.

## Remaining technical warnings

The generation still reports legacy bbox warnings for the decorative outer boundary sections extending beyond the old 200 m gameplay bbox. The live boundary itself is outside the playable envelope by design.

The auditor also reports the four live Altar obstacles as absent from `map_data.json`; the live-scene scan simultaneously confirms all four exist. This is an export/inspection mismatch and must be cleaned up before final MAP LOCK.

## Hard symmetry rule

All team-critical gameplay geometry must be mirrored across the world Y axis:

`(x, y, z) -> (-x, y, z)`

Tolerance: `0.25 m`.

This applies to bases, objectives, roads, ramps, gameplay cover, pockets, Altar protectors, central gameplay rocks, terrain and future gameplay markers. Decorative assets may vary only when they cannot affect movement, LOS, cover, collision, pathing or access.

## Core rock refinement

Central gameplay rocks are generated as exact geometric mirror pairs. With `count_core = 6`, the center contains **3 pairs / 6 large gameplay rocks**. Each pair shares the same dimensions, irregular silhouette and gameplay footprint, with world-space mirror placement.

## Objective-cover symmetry hardening

Each mirrored objective pair now uses one canonical cover plan, then derives the opposite side from the exact world-space Y-axis mirror. Crown is self-mirrored. This removes local-basis handedness drift.

## Safe failed-generation rollback

The pipeline snapshots managed AetherFlow objects before destructive regeneration and restores them if a later stage fails. The snapshot is discarded after successful generation.

## Terrain changes

- AetherCore depression: `×1.65`;
- Crown elevation: `×1.60`;
- West/East Monolith elevation: `×1.60`;
- SouthRift depression: `×1.50`;
- central transition radius: `×1.10`;
- maximum sampled terrain slope validated at **26.14°**, below the **35°** design limit.

## Closure

The **balance-validation objective of v0.6.3.1 is complete**. The project now moves to **v0.6.3.2 — HEIGHT TRANSITIONS**. The outer-boundary bbox and Altar export mismatch remain tracked technical cleanup items and must be resolved before final MAP LOCK.
