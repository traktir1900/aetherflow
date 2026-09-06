# AetherFlow v0.6.4.4 — Gameplay Landscape

## Goal

Introduce deterministic terrain relief that improves combat readability and creates meaningful high-ground / low-ground / flank choices without replacing the established objective layout, roads, ramps, pockets, bases, or navigation rules.

## Gameplay rules

- The authoritative XY layout does not change.
- Terrain remains analytic and is still generated from `core/heightmap.py`.
- Relief is exactly mirrored by `x -> -x`.
- Objective, base, center and major transition areas are softened/protected.
- The outer ring approach band is kept comparatively calm so the ring route remains the predictable macro traversal layer.
- Relief amplitude is intentionally low enough to remain walkable rather than creating accidental hard barriers.

## Current terrain language

### Side high ground
Paired elevated shelves on the west/east flanks create optional higher ground for ranged play, scouting and lateral pressure.

### Side low ground
A paired shallow depression behind the shelves creates a readable two-level flank choice rather than a uniformly flat side lane.

### South shoulders
Paired gentle rises frame the two-team base approach while leaving base pads themselves protected and readable.

### North shoulders
Paired gentle rises shape the Crown approach while the Crown objective and its future Lord/BossButton sanctuary remain protected from relief distortion.

### Broad undulation
A very low-frequency mirrored undulation removes the completely planar look without introducing tight bumps that could destabilize navigation or minion traversal.

## Validation expectations

The existing navigation and height-transition audits remain authoritative. Any generated result must still satisfy:

- gameplay symmetry hard gate;
- objective/base reachability;
- minion traversal regression;
- ramp continuity;
- max-step and slope rules;
- no changes to objective/base anchors.

No Blender runtime validation was performed in the development environment for this change.
