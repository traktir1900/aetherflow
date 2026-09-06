# ADR — Dominion-Style Curved Road Network

## Date

2026-09-06

## Decision

Adopt a **smooth curved arena road network** as the canonical AetherFlow road-language for v0.6.3.3.

The map should use broad arcs, rounded turns and continuous circulation around the central AetherCore zone, while keeping the existing objective/base anchors and the team's strict mirror symmetry.

This is an inspiration in **movement language and spatial flow**, not a reproduction of the original Dominion map.

## Reason

The previous road network was too straight and visually rigid. The curved network better communicates a fast arena with continuous rotation and multiple approach angles while preserving AetherFlow's own topology.

## Alternatives considered

### Straight point-to-point roads
Rejected because they create rigid corridors and read too much like conventional lane-based MOBA geometry.

### Purely decorative beveling of straight roads
Rejected because only changing the visual edge would not change the route shape or gameplay flow.

### Fully free-form winding roads
Rejected because excessive curvature would reduce readability and make routes harder to reason about for navigation, combat and minion traversal.

## Constraints

- Base and Objective XY anchors remain frozen.
- Gameplay symmetry remains `(x,y,z) -> (-x,y,z)` with the existing hard validation gate.
- Inner and outer rotation remain readable.
- Flank, retreat, pocket and interception routes remain connected.
- No three-lane MOBA conversion.
- Road geometry must remain terrain-adapted and navigation-compatible.
- Regression validation is required after material route changes.

## Consequences

### Positive

- smoother and more readable arena flow;
- more natural visual continuity;
- better support for curved approaches, interception and rotation;
- stronger Dominion-like movement feel without copying its exact map.

### Negative / follow-up work

- curved route geometry must be revalidated for navigation and height transitions;
- route distances and rotation times may change and must be measured;
- ramps and pocket connections may require refinement after the new road geometry is fully exercised.

## Implementation

The procedural road geometry is generated in `geometry/structures.py`. The current implementation uses the same procedural geometry pipeline and keeps the map anchors unchanged. Blender reruns explicitly reload the edited geometry module.
