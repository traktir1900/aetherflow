# EitherFlow — Project Terminology

## Purpose

This document is the canonical terminology glossary for EitherFlow / AetherFlow development.

All design, level-design, gameplay, programming and documentation work should use these terms consistently.

## Naming convention

**EitherFlow** is the game/design terminology used for the game concept.

**AetherFlow** is the project/repository/code name used for the implementation.

When a term refers to an implementation asset, generator module, exported field or code symbol, the AetherFlow naming used by the repository has priority.

---

# 1. Core Map Terms

### AetherFlow Map
The complete playable arena generated in Blender and later consumed by Unreal Engine.

### Gameplay Area
The authoritative playable map envelope. Current target: **200 × 200 m**.

### World Floor
The larger non-gameplay floor surrounding the gameplay area. Current target: **220 × 220 m**.

### Outer Boundary
The impassable outer perimeter defining the playable-world edge.

### AetherCore
The central terrain/combat landmark around the exact world origin.

### Aether Altar
The central altar/combat area associated with AetherCore.

### Aether Crown / Crown
The northern capture objective and central strategic landmark.

### Monolith
A capture objective located on the eastern or western portion of the objective ring.

### South Rift / SouthRift
The central southern terrain depression between the SW and SE Monoliths.

---

# 2. Capture Objectives

### Capture Point / Objective
A strategic location that teams can capture and control.

The map currently contains five objectives:

- Crown
- EastMonolith
- SEMonolith
- SWMonolith
- WestMonolith

### Objective Ring
The five-objective structure around the center. The authoritative implementation uses `RING_NODES`.

### Objective Platform
The physical circular platform representing a capture point in the generated scene.

### Objective Approach
A route used to enter or contest an objective.

### Objective Retreat Route
A route allowing a team to disengage from an objective.

### Objective Rotation
Movement from one objective to another as part of macro gameplay.

### Macro Rotation
Strategic movement between capture points. In the current validator, adjacent objective ring edges are measured as the first macro-rotation metric.

---

# 3. Bases and Teams

### Blue Base
The canonical base for the Blue team.

### Red Base
The canonical base for the Red team.

### Team-Critical Geometry
Any geometry that can affect movement, line of sight, cover, collision, pathing, access, rotation or combat balance.

### Gameplay Symmetry
The hard rule that team-critical gameplay geometry must be mirrored across the world Y axis.

Authoritative transform:

`(x, y, z) -> (-x, y, z)`

Current acceptance tolerance: **0.25 m**.

### Mirror Pair
Two gameplay elements that must correspond under the authoritative symmetry transform.

Examples:

- BlueBase ↔ RedBase
- WestMonolith ↔ EastMonolith
- SWMonolith ↔ SEMonolith
- WestPocket ↔ EastPocket
- SWPocket ↔ SEPocket

---

# 4. Roads, Routes and Movement Space

### Main Road
A primary traversable route connecting major map regions.

### Top Flow
The strategic route family serving the **northern/top portion of the map**, centered around the Crown side of the objective ring. Top Flow describes the preferred movement and rotation corridor through the northern gameplay space.

Top Flow is not a third lane. It is a **strategic flow layer** used to describe movement, rotation, interception and pressure through the top side of the map.

### Middle Flow
The strategic route family serving the **central/middle portion of the map**, connecting the central AetherCore / Aether Altar combat space with surrounding objectives and major rotation routes.

Middle Flow is the primary central rotation concept and must remain open enough to support interception, team fights and objective rotation without becoming a single mandatory corridor.

### Bottom Flow
The strategic route family serving the **southern/bottom portion of the map**, including the Blue/Red base side, SouthRift and the southern objective approach space.

Bottom Flow describes the southern strategic movement layer and includes base departures, southern objective approaches, retreat and comeback movement.

### Flow Layer
A strategic classification of connected movement space used to describe where and how teams rotate across the map. Flow Layers are **not equivalent to classic MOBA lanes**.

Current canonical flow terms:

- **Top Flow** — northern strategic movement layer;
- **Middle Flow** — central strategic movement layer;
- **Bottom Flow** — southern strategic movement layer.

A route may interact with more than one Flow Layer. A Flow Layer is a design-analysis concept, not necessarily one physical road or one uninterrupted path.

### Flank Route
A route allowing a player or team to approach from a less direct angle.

### Retreat Route
A route intended for safe disengagement from a fight or objective.

### Interception Route
A route enabling one team to cut across or intercept another team's rotation.

### Pocket
A secondary gameplay area connected to the main map, intended to support flank, ambush and retreat gameplay.

Current pockets:

- WestPocket
- EastPocket
- SWPocket
- SEPocket

### Pocket Entrance / Gate
The controlled entry/exit connection between a pocket and the main route network.

### Chokepoint
A strategically constrained passage through which many routes or players may concentrate.

The current validator distinguishes route-density chokepoints from measured physical corridor width.

---

# 5. Terrain and Height Terms

### Height Field
The analytic representation of terrain elevation as a function of world position.

### Height Transition
A change between terrain height levels or slopes that must remain readable and traversable.

### Terrain Slope
The local surface inclination.

### Walkable Slope
A slope intended to support normal player movement.

### Minion-Safe Transition
A terrain or ramp transition designed to support minion traversal without invalid navigation behaviour.

### Ramp
A deliberately constructed traversable structure used to bridge a height difference.

### Transition Radius
The spatial radius over which a terrain height change is smoothed.

### Terrain Readability
How clearly players can understand elevation, ramps, depressions, high ground and low ground during play.

---

# 6. Combat Space

### Combat Space
The physical area in which players can maneuver, engage, retreat, flank and reposition during combat.

### Combat Cover
Gameplay geometry that provides meaningful line-of-sight or positional protection during combat.

### Objective Cover
Cover located around a capture objective, intentionally positioned without blocking the objective itself or creating unfair camping.

### Pocket Cover
Gameplay cover placed inside a pocket to support ambush and retreat gameplay.

### Altar Protector
One of the four dedicated non-blocking barricades around Aether Altar.

Current arrangement: N / E / S / W.

### Central Gameplay Rock / Core Rock
A large rock in the central combat area that can affect movement, line of sight and engagement geometry.

Current target: **6 rocks = 3 mirror pairs**.

### Cover Value
A heuristic estimate of the tactical usefulness of a cover object. It is not a substitute for player playtesting.

### Line of Sight / LOS
Whether a direct visibility ray between gameplay positions is blocked by map geometry.

### Camping Risk
The risk that a player can hold a disproportionately strong stationary position with limited counterplay.

---

# 7. Dominion-Style Strategic Terms

### Deathball
A gameplay pattern where a team stays grouped and gains excessive value by moving as one large force.

### Snowball
A feedback loop where an early advantage becomes progressively harder to overcome.

### Comeback Route
A viable route or strategic option available to the losing team for regaining map control.

### Recovery Route
A practical route allowing a team to return to contested or important areas after losing ground.

### Time-to-Objective
The travel time required to reach a strategic objective from a defined origin.

### Rotation Variance
The spread between the fastest and slowest measured strategic rotation times.

---

# 8. Generation and Validation Terms

### Procedural Generation
Deterministic construction of map geometry from configuration, seed and generation rules.

### Deterministic Generation
Generation that produces the same intended result from the same configuration and seed.

### Seed
The deterministic random-generation seed. Current development seed: **1337**.

### Pipeline
The ordered AetherFlow generation process that builds terrain, structures, rocks, cover, pockets, navigation, simulation, validation and export.

### Validation Gate
A hard check that must pass before a version can be considered complete.

### Gameplay Symmetry Gate
The hard validator that enforces team-critical mirror symmetry.

### Navigation Validation
Checks whether important regions and routes remain reachable through the generated movement space.

### Evaluated-Mesh Intersection
An actual intersection detected on evaluated Blender geometry. This is stronger evidence than comparing nominal object bounds.

### DATA MISSING
A metric could not be measured from the available data. It must not be interpreted as a pass.

### APPROXIMATION
A result derived from a heuristic, fallback calculation or incomplete simulation and therefore not equivalent to an exact gameplay measurement.

### EXACT
A result directly supported by authoritative generated data or a live Blender geometric measurement.

### FALLBACK
A route or measurement used because the preferred authoritative data was unavailable.

### Regression Test
A repeatable test confirming that a change did not break already-validated map behaviour.

---

# 9. Export and UE5 Terms

### map_data.json
The authoritative structured export produced by Blender for the future UE5 runtime pipeline.

### MAP LOCK
The point at which the Blender gameplay map is considered geometrically and structurally frozen for UE5 integration.

### UE5 Foundation
The next major project phase beginning after the Blender map reaches MAP LOCK.

---

# 10. Version Terminology

### v0.6.x
Blender / Python / procedural map development and validation phase.

### v0.6.3.1 — Terrain Refinement
Terrain height refinement, terrain symmetry and central gameplay-space refinement.

### v0.6.3.2 — Height Transitions
Validation and refinement of slopes, ramps, walkability, minion traversal, LOS and combat readability.

### v0.6.3.3 — Road Network Refinement
Validation and refinement of primary, flank, rotation, pocket and retreat routes.

### v0.6.4
Boundary, environment and resources phase.

### v0.6.5
Full Dominion-style simulation and map balance phase.

### v0.6.6
Final validation, export and MAP LOCK.

### v0.7.0
Unreal Engine 5 foundation and runtime integration.

---

# 11. Canonical Rules

1. Team-critical geometry must be symmetric.
2. The authoritative symmetry transform is `(x, y, z) -> (-x, y, z)`.
3. Symmetry tolerance is 0.25 m unless a subsystem defines a stricter rule.
4. Decorative geometry is exempt only when it cannot affect gameplay.
5. Existing objectives and bases must not drift during refinement stages unless the roadmap explicitly allows it.
6. Geometry changes must be validated with navigation, LOS, intersection and balance regression tests.
7. `EXACT`, `APPROXIMATION`, `FALLBACK` and `DATA MISSING` must retain their literal meanings in reports.
8. A version is not complete while a mandatory validation gate is failing.
9. Top Flow, Middle Flow and Bottom Flow are strategic flow layers, not a return to a fixed three-lane MOBA layout.

---

# 12. Terminology Growth Rule

Whenever a new gameplay system introduces a project-specific term, its definition must be added here before the term becomes part of the canonical design vocabulary.
