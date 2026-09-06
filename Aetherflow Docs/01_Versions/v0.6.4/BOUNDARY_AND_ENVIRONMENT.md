# AetherFlow v0.6.4 — Boundary & Environment

## Outer Boundary

The map uses one global organic elliptical perimeter with 48 generated segments.

Current runtime evidence:

- semi_x ≈ **101.95 m**;
- semi_y ≈ **102.20 m**;
- major axis = **Y**;
- wall height ≈ **6.10–11.28 m**;
- wall thickness ≈ **3.80–5.04 m**;
- escape gaps = **0**;
- collision = **PASS**;
- pocket fence = **ABSENT**.

The perimeter is environmental collision geometry and must not be treated as an ordinary gameplay cover object by the generic map-bounds validator.

## Crown opening

The northern Crown sector has an intentional opening in the outer wall.

Contract:

- opening width >= **7.33 m**;
- side clearance = **1.00 m** on each side;
- one boundary segment removed at the Crown north axis;
- opening is an intentional entrance, not an accidental escape gap.

The opening must remain reachable from the Crown approach and must not create an unintended route outside the playable terrain.

## Pocket relation

The global outer boundary must coexist with the four existing gameplay pockets. Pocket perimeter geometry remains owned by the pocket system; v0.6.4 does not add a second pocket fence around the global ellipse.

## Environment status

The current active generator contains the global boundary and existing procedural rocks/cover, but the supplied auditor explicitly reports:

`RESOURCE DATA: NOT FOUND`

No Shrine/Relic/Resource-named objects are currently created by the active pipeline.

Therefore resource placement is **not complete** in v0.6.4.

## Environment completion rule

Future environment dressing may improve visual quality only when it does not compromise:

- navigation;
- combat sightlines;
- objective readability;
- gameplay symmetry;
- pocket access;
- minion traversal;
- boundary integrity.

Environmental asymmetry is allowed only for assets proven to be gameplay-neutral and therefore outside the team-critical geometry contract.

## Validation

Boundary validation must use actual wall footprints. The ordinary gameplay bbox check is insufficient for the external perimeter because wall thickness intentionally occupies the map-edge envelope.
