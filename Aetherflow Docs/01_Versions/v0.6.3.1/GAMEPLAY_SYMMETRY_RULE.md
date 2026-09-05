# AetherFlow — Gameplay Symmetry Rule

## Mandatory rule

Both teams must receive the same gameplay conditions. Team-critical map geometry is therefore mirrored across the world Y axis.

**Authoritative transform**

`(x, y, z) -> (-x, y, z)`

## What must be symmetric

- Blue Base ↔ Red Base;
- WestMonolith ↔ EastMonolith;
- SWMonolith ↔ SEMonolith;
- objective approach and retreat routes;
- roads and ramps used for team rotation;
- pocket position, entry and gameplay cover;
- objective gameplay cover;
- Altar protectors;
- terrain elevation and slope profile;
- gameplay markers, spawn points and future shop/interactions.

## Acceptance

A mismatch greater than `0.25 m` in checked gameplay geometry is a hard validation error.

The symmetry validator checks both static layout data and the generated scene records. It also samples the analytic terrain at mirrored coordinates.

Decorative assets are exempt only when they cannot change movement, line of sight, cover, collision, pathing, or access. A decorative asymmetry that changes gameplay is not considered decorative and must fail the symmetry gate.

## Development rule

Every future map-generation feature that affects gameplay must be designed from one canonical side and mirrored, or otherwise prove exact mirror equivalence. Random generation must never independently place team-critical elements on the two sides.

A version cannot be considered complete while the `GAMEPLAY SYMMETRY` validation gate is failing.
