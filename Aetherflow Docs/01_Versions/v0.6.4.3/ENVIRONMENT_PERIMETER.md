# v0.6.4.3 — Environment + Perimeter

## Goal

Remove the flat-prototype feeling from the world by adding a deterministic visual environment layer around the existing gameplay map.

## Implemented

- perimeter rock formations authored on one side and mirrored exactly;
- low ridge/height-language accents that visually reinforce existing terrain elevation without modifying the authoritative heightfield;
- four Crown approach landmarks framing the arrival to Crown;
- six AetherCore landmark spires plus a north frame reinforcing the Core silhouette;
- all new geometry lives in `Decorations` and is explicitly visual-only;
- new objects set `navigation_blocker=False` and `los_blocker=False`;
- all paired gameplay-facing visual forms use `(x,y,z) -> (-x,y,z)`;
- generation uses existing authoritative `ctx.layout` and `get_height_at_point()` only for placement.

## Gameplay safety contract

This pass does **not** redefine or move:

- capture point anchors;
- base anchors;
- roads;
- ramps;
- gameplay cover;
- pockets;
- authoritative terrain heights;
- navigation grid rules;
- minion corridors.

The environment layer is a visual overlay. It may sit on existing terrain height, but it does not deform or replace the gameplay terrain.

## Composition

| Layer | Objects | Purpose |
|---|---:|---|
| Perimeter formations | 12 | Break the flat horizon and create a natural cliff/rock silhouette |
| Height ridges | 6 | Reinforce existing high/low-ground language |
| Crown landmarks | 4 | Give the Crown approach a recognizable arrival frame |
| AetherCore landmarks | 7 | Give the Core a strong readable central silhouette |
| **Total** | **29** | Visual-only environment layer |

## Determinism

The pass does not introduce independent gameplay-affecting randomness. Placement is fixed from the authoritative layout and mirrored geometry.

## Validation state

**STATIC CHECK:** module and main-entry integration reviewed; no gameplay module was rewritten.

**RUNTIME:** Blender 5.2 execution and viewport review are still required. Before considering v0.6.4.3 complete, verify:

1. the environment pass generates without exceptions;
2. symmetry audit reports `PASS`;
3. Stage 9 validation does not gain geometry-related errors;
4. navigation/chokepoint results remain unchanged;
5. Crown and AetherCore remain visually framed without blocking routes or combat space;
6. the final scene remains team-symmetric.
