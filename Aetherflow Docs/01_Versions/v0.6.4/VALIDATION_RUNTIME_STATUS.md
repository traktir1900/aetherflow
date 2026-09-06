# AetherFlow v0.6.4 — Runtime Validation Status

## Source runtime

Blender 5.2 generation log supplied on 2026-09-06 from:

`C:\Users\mypc\Desktop\aetherflow-0-6-3-2-height-transitions`

Pipeline banner: **AETHER FLOW GENERATION PIPELINE :: v0.6.4**.

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
| Stage 9 validation | **FAILED** |

## Stage 9 failure details

The supplied runtime reported:

1. two `INVALID DIMENSIONS` errors for `CrownCaptureLink_Crown_*` visual-only meshes;
2. multiple `OUT OF MAP BOUNDS (bbox)` errors for `OuterBoundary_Segment*.002`;
3. several Crown structural-overlap warnings involving the coliseum and lower throne plate.

The first two classes were identified as validator-model mismatches rather than intended gameplay solids and received narrowly scoped runtime handling in the current implementation. The Crown overlap warnings remain genuine review items.

## Height-transition details

The supplied run reported 31 route audits, 4 pocket transitions and 6 ramp audits.

Five `Altar/Core -> Objective` routes inherited two flags:

- `corridor_below_minion_width`;
- `solid_blocker_on_path`.

The dedicated minion traversal scenarios nevertheless passed with:

- maximum slope: **13.50°**;
- maximum adjacent height delta: **0.375 m**;
- blockers: **0**;
- ramp-base contacts: **0**;
- terrain-edge hits: **0**;
- narrow hits: **0**.

This distinction must remain explicit: the dedicated minion regression passes, while some general Altar-approach audit records still need review.

## Ramp state

The same runtime showed the ramp audit using these widths:

- `North_Ramp_Crown_Core`: 1.6 m;
- capture ramps: 0.96 m in the pre-correction generated scene.

The repository configuration has since been adjusted so the explicit ramp builder targets the 4.0 m group-width contract. This change is **not runtime-verified yet** and therefore is not marked PASS in this document.

## Crown state

The runtime confirms the Crown Sanctum generator executed with:

- smooth semi-oval rise: **0.441 m**;
- semi-oval footprint: **7.88 × 5.25 m**;
- ruined half-coliseum: **18.4 × 11.5 m**;
- lower throne tier only;
- symmetric generation.

The Crown capture control is distinct from the boss button and has a post-generation elevation correction based on the actual generated mesh support surface.

## Acceptance policy

No individual source-level fix becomes a runtime PASS until Blender 5.2 is rerun and the resulting log confirms it.

The authoritative status remains **VALIDATION FAILED / OPEN** until the next runtime closes the remaining genuine issues.
