# AetherFlow — Dominion-Style Road Network

## Status

**Implemented in v0.6.3.3 direction / current working branch:** `v0-6-3-2-height-transitions`

## Design decision

AetherFlow roads use a **smooth arena-flow network** inspired by the movement language of Dominion-style maps: broad curved routes, ring-like circulation around the central combat zone, and soft transitions between objectives instead of rigid straight MOBA lanes.

This is a **design reference and flow principle**, not a copy of the original map layout.

## Geometry rules

- Keep all existing Base and Objective XY anchors fixed.
- Preserve the authoritative gameplay mirror: `(x, y, z) -> (-x, y, z)`.
- Keep both team sides gameplay-equivalent.
- Prefer smooth arcs and rounded turns over hard 90-degree road corners.
- Preserve clear inner and outer rotation around AetherCore.
- Keep flank, retreat, pocket, and interception routes connected to the main circulation network.
- Do not convert the map into three classical MOBA lanes.
- Roads must remain compatible with terrain height adaptation, navigation, ramps and minion traversal.

## Road-network pattern

The target movement language is:

1. **Outer circulation:** a smooth curved route connecting the five capture objectives.
2. **Inner circulation:** readable curved movement around AetherCore rather than a single straight central line.
3. **Radial connections:** objective-to-inner-zone connections should enter the circulation naturally.
4. **Base approaches:** Blue and Red base routes should curve into the network instead of terminating as rigid straight corridors.
5. **North flow:** the Crown connection should read as a natural continuation of the arena circulation.

## Gameplay intent

Curved roads are used to improve:

- movement readability;
- visual continuity of the arena;
- approach-angle variety;
- ambush and interception opportunities;
- natural rotation between objectives;
- Dominion-like arena flow without copying Dominion's exact geometry.

The curves are a **gameplay geometry change**, not only a visual bevel. The generated road path, navigation representation and downstream movement checks must continue to use the same underlying route intent.

## Validation requirements

After material road-network changes, run the normal regression pipeline and inspect:

- Base -> Objective routes;
- Objective -> Objective routes;
- outer/inner rotation;
- flank and retreat routes;
- pocket access;
- minion traversal;
- navigation problems;
- evaluated-mesh intersections;
- gameplay symmetry;
- Blue/Red route-time fairness.

Any gameplay-critical asymmetry is a hard failure.

## Current implementation note

The generated road system is implemented through the procedural geometry layer in `geometry/structures.py`. The current road generator builds terrain-adapted ribbons from route points, while Blender's Python module cache is explicitly refreshed on rerun so edited geometry is used without restarting Blender.

## Known state at documentation update

The latest Blender runtime confirms:

- gameplay map: **200 x 200 m**;
- roads detected in live scene: **7**;
- graded ramps built: **5**;
- navigation chokepoints detected: **5**;
- pockets reachable: **4/4**;
- gameplay symmetry: **PASS**;
- Blue/Red route-time difference: **0.0%**;
- minion traversal scenario: **PASS** for both teams.

The same runtime still reports separate technical validation issues around some ramp widths, central-route blockers and outer-boundary bbox checks. Those are tracked independently and must not be silently marked resolved by the road-style change.
