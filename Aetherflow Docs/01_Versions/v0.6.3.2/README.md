# AetherFlow v0.6.3.2 — Height Transitions

## Status

**MINION TRANSITION FIX APPLIED — FRESH BLENDER RUNTIME PASS REQUIRED**

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

The stage evaluates terrain transitions by actual obstacle-aware navigation paths instead of relying only on a global maximum slope.

## Implemented audit system

`core/height_transitions.py` is part of the active pipeline and prints a dedicated `MINION TRAVERSAL` section during Stage 7A.

It measures:

- Base → nearest objective;
- Base → farthest objective;
- every Base → Objective route;
- every Objective → Objective route;
- Altar/AetherCore → every objective;
- SouthRift → southern Monoliths;
- Main/Pocket transitions in both directions;
- every generated ramp;
- dedicated minion scenario for both teams.

Each measured transition reports reachability, route length, total height delta, maximum local slope, average local slope, maximum adjacent height delta and concrete problem flags.

## Runtime finding — confirmed transition defect

The fresh Blender 5.2 run confirmed the dedicated minion scenario was being rejected on both teams. Reachability itself was **YES**, and the route contained **0 rock/cover blocker hits** and **0 terrain-edge exits**, but several hops exceeded the minion-safe slope / height-step limits. The worst measured transitions were approximately **34.89–35.07°** with **1.090–1.097 m** adjacent height deltas. The same pattern appeared on mirrored routes, preserving gameplay symmetry.

The measured root cause was a discontinuity in the analytic height field:

1. the AetherCore bowl approached **z=0** at the edge of `center_radius`, but the following shoulder formula restarted from the deep Core height, creating an artificial one-cell downward step;
2. the South Rift branch replaced the surrounding terrain with its depression height at the rift boundary, creating another artificial one-cell step.

These were geometric field discontinuities, not navigation-blocker collisions.

## Applied repair

`core/heightmap.py` was repaired without changing any base/objective XY coordinates or gameplay topology:

- the outer Core shoulder now starts from the same **z=0** boundary as the inner bowl;
- South Rift now blends continuously from the surrounding raised terrain into its target depression instead of replacing the terrain abruptly at the rift boundary.

This is a local height-field continuity repair. Team symmetry remains authoritative because the height field itself is derived from the canonical symmetric map layout.

## Minion traversal regression

The dedicated deterministic scenario is:

`Base → Objective → Objective → enemy Base`

The current mirrored scenarios are:

- Blue: `BlueBase → Crown → SEMonolith → RedBase`;
- Red: `RedBase → WestMonolith → SWMonolith → BlueBase`.

Every hop is checked for:

- slope above the configured **Minion-safe** threshold;
- adjacent height step above **0.75 m**;
- direct contact with rocks or gameplay cover represented as blocked navigation cells;
- ramp-base proximity and associated height discontinuity;
- terrain-edge exits;
- corridor clearance for a minion.

The final gate requires both mirrored scenarios to be reachable, minion-safe and problem-free.

The regression is a deterministic geometry/navigation test, not a full Unreal minion actor simulation.

## Diagnostic thresholds

The audit uses configurable engineering thresholds, separate from the hard 35° terrain ceiling:

- **Combat slope**: ≤ 15°;
- **Minion-safe**: ≤ 18°;
- **Walkable**: ≤ 25°;
- **Ramp**: ≤ 30° when represented by a ramp;
- **Too steep**: > 35°;
- adjacent height step above **0.75 m** is a hard transition warning;
- single-minion corridor target: **1.5 m**;
- group corridor target: **4.0 m**.

The 1.5 m single-minion corridor threshold is intentionally separated from the 4.0 m group/ramp width requirement: a 2.4 m capture ramp can be valid for one minion while still being unsuitable for a full combat group.

## Ramp inspection

Every registered ramp is inspected for width, run length, height delta, graded/terrain-following mode, reachability and sampled slope where endpoints are available.

The current five capture ramps are **2.4 m** wide. This remains a group-width diagnostic warning, not automatically a single-minion collision failure.

## Non-minion findings retained

The same runtime still reports the following known items that are outside the minion transition repair:

- global outer boundary bbox warnings caused by the legacy bbox validator;
- 10 pocket-cover vs pocket-floor mesh intersection warnings;
- live Altar obstacle data present in Blender but stale/missing in `map_data.json`;
- macro rotation variance of **21.6 s** is reported as an approximation warning.

Navigation remained reachable, evaluated-mesh intersections remained **0**, and gameplay symmetry remained **PASS**. Blue/Red route fairness remained **0.0%**.

## Required runtime re-pass

A fresh Blender 5.2 generation from this branch is now required to verify the repair. Source changes establish the intended continuity but cannot prove the final evaluated mesh by themselves.

The re-pass must verify:

- minion scenario passes for **both teams**;
- no slope > 18° on minion scenario hops unless the segment is explicitly a ramp exception;
- no adjacent height step > 0.75 m;
- no rock/cover blocker collisions;
- no ramp-base transition defect;
- no terrain-edge exits;
- reasonable minion corridor clearance;
- Blue/Red average route-time difference remains **0.0%**;
- 5/5 objectives;
- 4/4 pockets reachable;
- navigation problems = **0**;
- evaluated-mesh intersections = **0**;
- gameplay symmetry = **PASS**;
- base/objective XY unchanged.

## Next stage

After closure of v0.6.3.2, proceed to **v0.6.3.3 — ROAD NETWORK REFINEMENT**.
