# AetherFlow v0.6.4.0 — Runtime Validation Status

## Source runtime

Blender 5.2 generation log supplied on 2026-09-06 from:
`C:\Users\mypc\Desktop\aetherflow-0-6-3-2-height-transitions`

Pipeline banner: AETHER FLOW GENERATION PIPELINE :: v0.6.4.

## Verified by the supplied run

| Check | Result |
|---|---|
| Gameplay map | 200 × 200 m |
| World floor | 220 × 220 m |
| Terrain slope audit | PASS — 19.88° max |
| Capture objectives | 5/5 |
| Capture overlays | 10 objects / 5 logical anchors |
| Crown capture node | Present |
| Crown visual correction | Executed / visible flag = true |
| Road center light guides | Generated |
| Capture route binding | PASS — 18 links |
| Graded ramps built | 5 |
| Pockets reachable | 4/4 |
| Gameplay symmetry | PASS |
| Minion traversal | PASS — both mirrored scenarios |
| Stage 9 validation | FAILED |

## Stage 9 failure details

The supplied runtime reported invalid-dimension errors for visual-only Crown capture links, out-of-map-bounds bbox diagnostics for perimeter segments, and Crown structural-overlap warnings. The first two classes were identified as validator-model mismatches and received narrowly scoped runtime handling. Crown overlap warnings remain genuine review items.

## Height-transition details

The supplied run reported 31 route audits, 4 pocket transitions and 6 ramp audits. Five Altar/Core → Objective routes inherited `corridor_below_minion_width` and `solid_blocker_on_path` flags, while the dedicated minion traversal scenarios passed with maximum slope 13.50°, maximum adjacent height delta 0.375 m, blockers 0, ramp-base contacts 0, terrain-edge hits 0 and narrow hits 0.

## Ramp state

The same runtime showed pre-correction widths of 1.6 m for `North_Ramp_Crown_Core` and 0.96 m for capture ramps. Repository configuration was subsequently adjusted to target the 4.0 m group-width contract. That adjustment is not runtime-verified yet.

## Acceptance policy

A source-level fix becomes runtime PASS only after Blender 5.2 is rerun and the resulting log confirms it. The authoritative status remains **VALIDATION FAILED / OPEN** until genuine remaining issues are closed.
