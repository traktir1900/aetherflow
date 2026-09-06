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

### EitherFlow Map
The complete playable arena generated in Blender and later consumed by Unreal Engine.

### Gameplay Area
The authoritative playable map envelope. Current target: **200 × 200 m**.

### World Floor
The larger non-gameplay floor surrounding the gameplay area. Current target: **220 × 220 m**.

### Outer Boundary
The impassable outer perimeter defining the playable-world edge.

### AetherCore
The central terrain/combat landmark around the exact world origin. This is the implementation/landmark name.

### Aether Altar / Altar
The central altar/combat area at the center of the map. **The gameplay name remains Altar.** Do not rename the Altar to Core or Crown.

### Crown
The **fifth capture point at the top/northern part of the map**. Crown is a capture objective and is distinct from the central Altar.

### Monolith
A capture objective located on the eastern or western portion of the objective ring.

### South Rift / SouthRift
The central southern terrain depression between the SW and SE Monoliths.

---

# 2. Capture Objectives

### Capture Point / Objective
A strategic location that teams can capture and control.

The map currently contains five ring objectives:

- Crown
- EastMonolith
- SEMonolith
- SWMonolith
- WestMonolith

### Objective Ring
The five-objective structure around the map center.

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

### Blue Core
The home base of the Blue team.

### Red Core
The home base of the Red team.

### Core
A team home base. The canonical team-specific names are **Blue Core** and **Red Core**. In gameplay terminology, Core refers to a team base; the central altar remains **Altar**.

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

- Blue Core ↔ Red Core
- WestMonolith ↔ EastMonolith
- SWMonolith ↔ SEMonolith
- WestPocket ↔ EastPocket
- SWPocket ↔ SEPocket

---

# 4. Flows and Routes

### Flow
A persistent strategic movement corridor running from a team's Core toward the upper/northern part of the map. A Flow is a gameplay movement concept, not necessarily a single road mesh or a straight line.

### Top Flow
The upper base-to-north strategic movement corridor. It carries players and minions from a Core toward the upper portion of the map.

### Middle Flow
The central base-to-north strategic movement corridor. It carries players and minions from a Core through the central portion of the map toward the upper area and the central Altar combat space.

### Bottom Flow
The lower base-to-north strategic movement corridor. It carries players and minions from a Core through the lower portion of the map toward the upper area.

### Flow Rule
Top Flow, Middle Flow and Bottom Flow describe **three strategic Core-to-north movement corridors**. They are not intended to turn the map into three rigid classical MOBA lanes. Each Flow may contain multiple roads, branches, ramps, intersections, pockets and rotation connections.

### Main Road
A primary traversable route connecting major map regions.

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
One of the four dedicated non-blocking barricades around the central Altar. **This term remains the canonical name.**

Current arrangement: N / E / S / W.

### Core Protector
Deprecated. Do not use this name in new gameplay or design documentation.

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

# 6.1 Crown Boss / Crown Sanctum

### Crown Boss
The neutral boss located at the northern Crown area. The Crown Boss is a PvE objective that can be defeated by either team and grants a temporary team-wide strategic buff.

The Crown Boss is **not** a capture point and does not replace the Crown objective.

### Crown Sanctum
The dedicated boss arena structure built around the Crown Boss. Crown Sanctum is the canonical name for the complete boss location, including the raised platform, boss button, surrounding combat ring and access ramps.

### Crown Throne
The raised central boss platform inside Crown Sanctum where the Crown Boss stands. Crown Throne is a physical gameplay structure, not a separate objective.

### Boss Button / Aether Button
The central pressure-button platform on the Crown Throne. The Crown Boss stands directly on the Aether Button while alive. The button visually and mechanically represents the active boss state.

### Boss Platform
The raised central platform supporting the Crown Boss and Aether Button. Use **Crown Throne** when referring specifically to the complete central raised boss structure.

### Boss Arena
The walkable combat space surrounding the Crown Throne inside Crown Sanctum. The arena must remain open enough for players to maneuver around the boss from multiple directions.

### Sanctum Upper Ring
The outer raised ring surrounding the Crown Throne. It is part of Crown Sanctum and provides the primary player combat surface around the boss.

### Sanctum Ramp
One of the broad, symmetric traversable ramps connecting the surrounding terrain to Crown Sanctum's elevated boss area.

The preferred layout is **four-way symmetric access**, avoiding a single mandatory choke entrance.

### Crown Blessing
The temporary team-wide reward granted after a team defeats the Crown Boss. Crown Blessing is a strategic buff intended to improve the team's ability to contest or push the map rather than provide an automatic victory condition.

### Crown Blessing Duration
The time for which Crown Blessing remains active. The current design target is **90 seconds** unless later balance testing changes it.

### Crown Blessing Type
The specific category of temporary buff granted by the Crown Boss. Planned categories include:

- **Aether Might** — hero combat power.
- **Aether March** — minion durability, movement and push power.
- **Aether Dominion** — objective capture and structure pressure.

These are gameplay design terms; their exact numerical values remain subject to balance testing.

### Aether Obelisk
One of the four large visual/functional obelisks surrounding Crown Sanctum. Obelisks remain symmetrical and activate visually when the Crown Blessing is granted.

### Crown Boss Pit
Deprecated informal name. Use **Crown Sanctum** for the complete location and **Boss Arena** for its combat surface.

### Boss Room
Deprecated. Do not use; Crown Sanctum is an open PvP/PvE combat structure, not a closed room.

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
5. Existing objectives and Cores must not drift during refinement stages unless the roadmap explicitly allows it.
6. Geometry changes must be validated with navigation, LOS, intersection and balance regression tests.
7. `EXACT`, `APPROXIMATION`, `FALLBACK` and `DATA MISSING` must retain their literal meanings in reports.
8. A version is not complete while a mandatory validation gate is failing.
9. Top Flow, Middle Flow and Bottom Flow are strategic Core-to-north corridors, not rigid three-lane MOBA lanes.
10. **Blue Core** and **Red Core** are the canonical names for the two team bases.
11. **Crown** is the fifth, northern capture point.
12. **Altar** remains the canonical name for the central altar/combat objective.
13. **Altar Protector** remains the canonical name for its four dedicated protectors.
14. **Crown Sanctum** is the canonical name for the northern Crown boss location.
15. **Crown Boss** is the canonical name for the neutral boss located there.
16. **Aether Button** is the canonical name for the central pressure button under the living boss.
17. **Crown Blessing** is the canonical name for the temporary team buff awarded for defeating the Crown Boss.
18. Crown Sanctum access should remain broadly symmetric and should not depend on a single mandatory choke entrance.

---

# 12. Terminology Growth Rule

Whenever a new gameplay system introduces a project-specific term, its definition must be added here before the term becomes part of the canonical design vocabulary.

Deprecated gameplay terms must be explicitly marked and must not be used for new design or implementation naming unless required for backwards-compatible code identifiers.
