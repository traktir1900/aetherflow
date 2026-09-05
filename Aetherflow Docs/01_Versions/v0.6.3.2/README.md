# AetherFlow v0.6.3.2 — Height Transitions

## Status

**MINION TRAVERSAL AUDIT INTEGRATED — DEDICATED RUNTIME OUTPUT ENABLED**

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

`core/height_transitions.py` is now part of the active pipeline.

It measures:

- Base → nearest objective;
- Base → farthest objective;
- every Base → Objective route;
- every Objective → Objective route;
- Altar/AetherCore → every objective;
- SouthRift → southern Monoliths;
- Main/Pocket transitions in both directions;
- every generated ramp.

Each measured transition reports reachability, route length, total height delta, maximum local slope, average local slope, maximum adjacent height delta and concrete problem flags.

## Gameplay slope categories

The audit uses configurable engineering thresholds, separate from the hard 35° terrain ceiling:

- **Combat slope**: ≤ 15°;
- **Minion-safe**: ≤ 18°;
- **Walkable**: ≤ 25°;
- **Ramp**: ≤ 30° when represented by a ramp;
- **Too steep**: > 35°.

Adjacent height changes above **0.75 m** are also flagged as possible hard transition steps.

These numbers are diagnostic controls for v0.6.3.2, not a justification for changing the map when no problem is measured.

## Ramp inspection

Every registered ramp is inspected for width, run length, height delta, graded/terrain-following mode, reachability and sampled slope where endpoints are available. Capture-point ramps already expose authoritative endpoints in metadata; the northern Crown access ramp remains a terrain-following ramp and is audited separately.

## Minion traversal regression

A dedicated deterministic scenario now runs for both teams:

`Base → Objective → Objective → enemy Base`

The two scenarios use mirrored objective sequences and actual obstacle-aware NavGrid paths. Every hop is checked for:

- slope above the configured **Minion-safe** threshold;
- adjacent height step above **0.75 m**;
- direct contact with rocks or gameplay cover represented as blocked navigation cells;
- ramp-base proximity and associated height discontinuity;
- terrain-edge exits;
- corridor clearance below the configured minimum for a minion.

The report retains hop-level diagnostics and a final `passed` gate rather than hiding individual failures behind a single reachability result.

The active Blender pipeline now prints a dedicated `MINION TRAVERSAL` summary during Stage 7A, including the Blue and Red scenario paths, pass/fail state, maximum slope, maximum adjacent height delta, blocker hits, ramp-base contacts, terrain-edge hits and narrow-corridor hits. Individual failing hops are printed explicitly.

This is still a geometric/navigation regression, not a full Unreal minion simulation. A fresh Blender 5.2 runtime remains required to confirm the generated mesh behaves correctly for an actual minion actor.

## Repair policy

The audit module is read-only. It never changes geometry automatically.

When the runtime confirms a real transition problem, the smallest suitable repair is applied in this order:

1. increase transition radius;
2. smooth the local height profile;
3. reduce the local height difference;
4. adjust an existing ramp;
5. improve road/ramp continuity.

Base/objective XY coordinates remain frozen and gameplay symmetry remains a hard validation gate.

## Runtime result from latest user run

The latest Blender 5.2 run successfully reached Stage 7A and generated the height-transition audit, but the log did not contain the dedicated `MINION TRAVERSAL` summary. The run therefore cannot be used as a final minion-traversal pass/fail result.

The same run did expose concrete height-transition issues: 28 route problems, 4 pocket problems and 5 ramp problems. The repeated `corridor_below_minion_width` flag on routes is diagnostic and must be separated from actual minion traversal failure before any geometry repair is made.

The next runtime must be taken from the branch after the pipeline logging change and must contain the dedicated Blue/Red minion regression output. Only those results should trigger geometry repair decisions.

## Required runtime pass

A fresh Blender 5.2 generation from this branch is required before declaring any height-transition or minion-traversal problem confirmed or any repair necessary. Source inspection cannot prove hero/minion traversal, LOS readability or evaluated-mesh behaviour.

The runtime report must then be compared with the baseline for:

- Blue/Red route difference = 0.0%;
- 5/5 objectives;
- 4/4 pockets reachable;
- navigation problems = 0;
- evaluated-mesh intersections = 0;
- gameplay symmetry = PASS;
- terrain slope limit = 35°;
- base/objective XY unchanged;
- **minion traversal scenario passes for both teams**.

## Next stage

After closure of v0.6.3.2, proceed to **v0.6.3.3 — ROAD NETWORK REFINEMENT**.
