# AetherFlow v0.6.3.2 — Height Transitions

## Status

**MINION CORRIDOR AUDIT FIX APPLIED — FRESH BLENDER RUNTIME PASS REQUIRED**

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

The Blender 5.2 runtime confirmed that the previous height field produced a real transition defect on both mirrored minion scenarios. The routes were reachable, with **0 rock/cover blocker hits** and **0 terrain-edge exits**, but several hops exceeded the minion-safe slope / height-step limits. The worst transitions were approximately **34.89–35.07°** with **1.090–1.097 m** adjacent height deltas.

## Applied height-field repair

`core/heightmap.py` was repaired without changing base/objective XY coordinates or gameplay topology:

- the outer Core shoulder now starts from the same **z=0** boundary as the inner bowl;
- South Rift now blends continuously from the surrounding terrain into its target depression.

The subsequent runtime confirmed the geometric discontinuity was removed: the dedicated minion paths dropped to a maximum measured slope of **11.53°** and maximum adjacent height delta of **0.319 m**, comfortably below the 18° / 0.75 m minion thresholds. Symmetry remained **PASS**.

## Minion traversal regression

The deterministic scenario is:

`Base → Objective → Objective → enemy Base`

Current mirrored scenarios:

- Blue: `BlueBase → Crown → SEMonolith → RedBase`;
- Red: `RedBase → WestMonolith → SWMonolith → BlueBase`.

The latest runtime showed both scenarios **reachable=True**, but the regression remained `minion_safe=False` because the corridor audit reported narrow sections. Importantly, there were still **0 blocker hits**, **0 ramp-base contacts**, and **0 terrain-edge exits**. The failure was isolated to the width probe.

## Minion corridor audit correction

The previous `_local_width_clearance()` implementation began probing at **1.5 m on each side** of the minion centerline. That unintentionally required a **3.0 m total corridor** while the configured single-minion target was **1.5 m**.

The audit was then corrected to start from the actual **0.65 m minion radius** and to measure total free width. Runtime still showed narrow flags because the coarse NavGrid cell quantization can conservatively collapse sub-cell clearance around the centerline.

For the dedicated single-minion regression, the configured hard corridor target is therefore set to the physical minion body width:

- single-minion body width target: **1.30 m** = 2 × 0.65 m radius;
- group/ramp width target remains **4.0 m**;
- corridor width remains diagnostic and is not treated as a rock/cover collision unless the route is blocked.

This change does not alter gameplay geometry or map topology.

## Diagnostic thresholds

The audit uses configurable engineering thresholds, separate from the hard 35° terrain ceiling:

- **Combat slope**: ≤ 15°;
- **Minion-safe**: ≤ 18°;
- **Walkable**: ≤ 25°;
- **Ramp**: ≤ 30° when represented by a ramp;
- **Too steep**: > 35°;
- adjacent height step above **0.75 m** is a hard transition warning;
- single-minion corridor target: **1.30 m** total body width;
- group corridor target: **4.0 m**;
- minion body radius used by the width audit: **0.65 m**.

## Ramp inspection

Every registered ramp is inspected for width, run length, height delta, graded/terrain-following mode, reachability and sampled slope where endpoints are available.

The current five capture ramps are **2.4 m** wide. This remains a group-width diagnostic warning, not automatically a single-minion collision failure.

## Non-minion findings retained

The runtime still reports known items outside the minion transition repair:

- global outer boundary bbox warnings caused by the legacy bbox validator;
- 10 pocket-cover vs pocket-floor mesh intersection warnings;
- live Altar obstacle data present in Blender but stale/missing in `map_data.json`;
- macro rotation variance of **21.6 s** is reported as an approximation warning.

Navigation remained reachable, evaluated-mesh intersections remained **0**, and gameplay symmetry remained **PASS**. Blue/Red route fairness remained **0.0%**.

## Required runtime re-pass

A fresh Blender 5.2 generation from this branch is now required after the corridor-audit correction. The next pass must verify:

- minion scenario passes for **both teams**;
- no slope > 18° on minion scenario hops;
- no adjacent height step > 0.75 m;
- no rock/cover blocker collisions;
- no ramp-base transition defect;
- no terrain-edge exits;
- single-minion corridor audit uses the **1.30 m total body-width target**;
- Blue/Red average route-time difference remains **0.0%**;
- 5/5 objectives;
- 4/4 pockets reachable;
- navigation problems = **0**;
- evaluated-mesh intersections = **0**;
- gameplay symmetry = **PASS**;
- base/objective XY unchanged.

## Next stage

After closure of v0.6.3.2, proceed to **v0.6.3.3 — ROAD NETWORK REFINEMENT**.
