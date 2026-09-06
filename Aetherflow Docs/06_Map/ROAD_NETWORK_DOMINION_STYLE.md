# AetherFlow — Dominion-Style Road Network

## Status

**v0.6.4 runtime presentation integrated; road-network contract retained for v0.6.3.3 / v0.6.4 validation.**

## Design decision

AetherFlow roads use a **smooth curved arena-flow network** inspired by the movement language of Dominion-style maps: broad curved routes, ring-like circulation around the central combat zone, and soft transitions between objectives instead of rigid straight MOBA lanes.

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
- Visual road-light guides are presentation-only and must not alter navigation or collision.

## Road-network pattern

The target movement language is:

1. **Outer circulation:** a smooth curved route connecting the five capture objectives.
2. **Inner circulation:** readable movement around AetherCore rather than a single rigid central line.
3. **Radial connections:** objective-to-inner-zone connections should enter the circulation naturally.
4. **Base approaches:** Blue and Red base routes should curve into the network instead of terminating as rigid straight corridors.
5. **North flow:** the Crown connection should read as a natural continuation of the arena circulation.

## v0.6.4 presentation layer

The v0.6.4 capture-control pass adds a thin luminous center guide to the principal road network. These guides are visual-only and are not the authoritative route geometry.

The five capture objectives also expose logical button anchors. Roads and ramps bind their objective endpoints to these anchors so gameplay interaction remains attached to the existing objective identities without moving the objective XY coordinates.

The Crown receives two additional visual-only links from `CaptureButton_Crown` to the neighboring West/East Monolith capture controls. These links are presentation helpers, not new gameplay routes.

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
- Blue/Red route-time fairness;
- interaction-anchor binding;
- visual guide neutrality.

Any gameplay-critical asymmetry is a hard failure.

## Current implementation note

The generated road system is implemented through the procedural geometry layer in `geometry/structures.py`. The current road generator builds terrain-adapted ribbons from route points. The capture runtime then adds the visual center guides and binds road/ramp endpoints to the five logical capture buttons.

## Latest v0.6.4 runtime evidence

The supplied Blender 5.2 runtime confirms:

- gameplay map: **200 x 200 m**;
- roads: **7**;
- graded ramps built: **5**;
- navigation chokepoints detected: **5**;
- pockets reachable: **4/4**;
- gameplay symmetry: **PASS**;
- Blue/Red route-time difference: **0.0%**;
- dedicated minion traversal: **PASS** for both mirrored scenarios;
- capture button route binding: **PASS — 18 links**;
- road center light guides: generated;
- final Stage 9 validation: **FAILED**.

The same runtime reports five general `Altar/Core -> Objective` height-audit route flags and six ramp-audit flags. These are separate from the dedicated minion traversal regression and remain open until the next runtime confirms the corrected state.

The runtime also reports technical boundary and Crown structural-overlap warnings. Those warnings must be resolved or explicitly accepted with measured evidence before MAP LOCK.

## Non-negotiable road contract

1. Road geometry must not move frozen Base/Objective XY anchors.
2. Team-critical road geometry must retain exact Y-axis mirror symmetry within **0.25 m**.
3. Curved roads must not become rigid three-lane MOBA corridors.
4. Visual light guides must be navigation-neutral.
5. Logical capture bindings must remain complete for all five objectives.
6. Runtime `FAILED` status must not be rewritten as a road-network PASS.
