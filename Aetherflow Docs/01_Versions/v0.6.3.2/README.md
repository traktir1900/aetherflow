# AetherFlow v0.6.3.2 — Height Transitions

## Status

**BASELINE LOCKED — WORK STARTED**

## Baseline v0.6.3.1

The following values are the mandatory regression baseline for v0.6.3.2:

- Blue/Red average route-time difference: **0.0%**;
- objectives: **5/5**;
- gameplay pockets reachable: **4/4**;
- navigation problems: **0**;
- evaluated-mesh intersections: **0**;
- gameplay symmetry: **PASS**;
- terrain design slope limit: **35°**;
- XY coordinates of all bases and objectives: **FROZEN / MUST NOT CHANGE**.

These values are the control set. Any v0.6.3.2 change must be compared against this baseline.

## Scope

v0.6.3.2 improves **height transitions** and traversal quality without redesigning the map topology.

The stage evaluates:

- terrain height changes;
- slopes;
- ramps;
- hero walkability;
- minion traversal;
- line-of-sight changes caused by elevation;
- combat readability of high/low ground;
- transition quality between Core/Altar, Crown, Monolith platforms and SouthRift;
- regression impact on Blue/Red fairness.

## Hard rules

1. Do not move base or objective XY coordinates.
2. Preserve the authoritative Y-axis gameplay symmetry: `(x,y,z) -> (-x,y,z)`.
3. Do not introduce a team-critical asymmetry greater than **0.25 m**.
4. Do not create new gameplay-breaking chokepoints.
5. Fix only measured problems; do not redesign geometry by visual preference alone.
6. Every geometry change requires regression validation.

## Work sequence

### 1. Terrain transition audit

Measure representative routes:

- Core → Crown;
- Core → East/West Monolith;
- Core → SE/SW Monolith;
- SouthRift → southern objectives;
- Flow routes through elevated/depressed areas;
- pocket ↔ main-route transitions.

Record local slope, height delta and transition length.

### 2. Walkability classification

Classify transitions as:

- Walkable;
- Minion-safe;
- Ramp-required;
- Combat-readable;
- Too steep / problematic.

The goal is not simply to stay below 35°: the transition must also remain practical for the intended gameplay agents.

### 3. Ramp inspection

Audit every existing ramp for:

- height delta;
- longitudinal slope;
- width;
- entry/exit continuity;
- alignment with roads;
- hero traversal;
- minion traversal;
- group traversal;
- collision/intersection safety.

### 4. Height transition refinement

Where a real problem is confirmed, apply the smallest suitable correction:

- increase transition radius;
- smooth a local height change;
- reduce excessive local slope;
- adjust an existing ramp;
- improve road/ramp continuity.

Objective/base coordinates and map topology remain fixed.

### 5. Minion traversal regression

Test a representative continuous path:

`Core → objectives → opposing side`

Confirm no unacceptable steep section, height discontinuity, ramp failure or navigation break prevents a minion wave from traversing the route.

### 6. LOS regression

After every material height change, re-check objective and route LOS for:

- Crown;
- East/West Monoliths;
- SE/SW Monoliths;
- Core/Altar;
- elevated approaches;
- defensive high-ground positions.

Avoid creating a one-sided high-ground advantage.

### 7. Combat readability

Confirm that elevation changes communicate clearly where:

- high ground begins;
- low ground begins;
- ramps start/end;
- routes remain traversable;
- objectives remain visually readable.

### 8. Symmetry validation

All team-critical terrain and transition edits must remain mirrored across the Y axis. Corresponding ramps and route transitions must receive equivalent corrections.

### 9. Navigation regression

Required result:

- navigation problems = **0**;
- pockets reachable = **4/4**;
- no new dead-end gameplay zones;
- no loss of key routes.

### 10. Geometry regression

Required result:

- evaluated-mesh intersections = **0**;
- no new terrain/ramp/road/cover collisions;
- no invalid overlap introduced by transition repair.

### 11. Balance regression

Compare against v0.6.3.1 baseline:

- Blue/Red average route difference must remain **0.0%** or any deviation must be explicitly measured and judged acceptable;
- nearest-objective equivalence must remain intact;
- pocket route symmetry must remain intact;
- macro rotation must not become disproportionately worse for one team.

## Exit criteria

v0.6.3.2 is complete only when all mandatory gates pass:

- terrain transitions PASS;
- walkability PASS;
- minion traversal PASS;
- ramps PASS;
- LOS regression PASS;
- combat readability PASS;
- gameplay symmetry PASS;
- navigation problems = **0**;
- pockets = **4/4 reachable**;
- evaluated-mesh intersections = **0**;
- Blue/Red fairness preserved against baseline;
- base/objective XY unchanged.

## Next stage

After closure of v0.6.3.2, proceed to **v0.6.3.3 — ROAD NETWORK REFINEMENT**.
