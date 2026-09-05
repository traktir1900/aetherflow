# AetherFlow v0.6.3.2 — Height Transition Audit

## Purpose

v0.6.3.2 now evaluates terrain transitions as gameplay movement paths rather than only checking one global maximum slope.

## Audit matrix

The runtime audit measures actual obstacle-aware navigation paths for:

- Blue Core / Red Core -> nearest objective;
- Blue Core / Red Core -> farthest objective;
- every base -> every objective;
- every objective -> every other objective;
- Altar / AetherCore -> every objective;
- SouthRift -> SWMonolith / SEMonolith;
- each gameplay pocket connection in both directions;
- every generated ramp.

## Per-transition measurements

Each measured route records:

- reachability;
- route length;
- total height delta;
- maximum local slope;
- average local slope;
- maximum adjacent height delta;
- length spent above the combat-slope threshold;
- gameplay classification;
- concrete problem flags.

## Gameplay categories

The current engineering thresholds are configurable and intentionally separated from the hard 35 degree terrain-design ceiling:

| Category | Initial threshold |
|---|---:|
| Combat slope | <= 15 deg |
| Minion-safe | <= 18 deg |
| Walkable | <= 25 deg |
| Ramp | <= 30 deg when represented by a ramp |
| Too steep | > 35 deg |

An additional transition-step check flags adjacent height changes above **0.75 m**. These thresholds are diagnostic controls for v0.6.3.2 and do not move objectives or bases.

## Ramp audit

Every registered `ramp` object is inspected for:

- width;
- configured run length;
- recorded height delta;
- graded vs terrain-following mode;
- reachability;
- sampled slope when endpoints are available;
- group-width warning;
- concrete transition problems.

The capture-point ramps already record authoritative `p0`/`p1` endpoints and grade metadata. The northern Crown access ramp is intentionally terrain-following and is kept distinct from the dedicated graded platform ramps.

## Repair policy

The audit module is read-only. It does **not** modify geometry automatically.

A repair is allowed only after the Blender runtime identifies a real problem. The preferred order is:

1. increase transition radius;
2. smooth the local height profile;
3. reduce the local height difference;
4. adjust an existing ramp;
5. improve road/ramp continuity.

Base/objective XY coordinates remain frozen and gameplay symmetry remains a hard gate.

## Runtime requirement

The repository now contains the complete audit path, but a fresh Blender 5.2 generation is still required to populate the measured route/ramp results. Source inspection alone is not sufficient evidence for hero/minion traversal, LOS readability or evaluated-mesh behaviour.

The next closure record must compare the measured v0.6.3.2 report against the v0.6.3.1 baseline:

- Blue/Red route difference = 0.0%;
- 5/5 objectives;
- 4/4 pockets reachable;
- navigation problems = 0;
- evaluated-mesh intersections = 0;
- gameplay symmetry = PASS;
- terrain design slope limit = 35 deg;
- base/objective XY unchanged.
