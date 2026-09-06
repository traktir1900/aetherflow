# AetherFlow v0.6.4 — Boundary, Environment & Runtime Presentation

## Status

**IN PROGRESS — implementation present; fresh Blender runtime still required for final closure.**

v0.6.4 is the current documentation version for the boundary/environment pass and the associated gameplay-presentation work that became necessary while exercising the v0.6.3.2 pipeline.

## Scope

v0.6.4 covers:

- global outer elliptical boundary;
- Crown outer-wall opening;
- Crown Sanctum presentation and raised-objective visibility;
- capture-point interaction overlays;
- visual center-light road guides;
- route binding from roads/ramps to capture controls;
- runtime validation compatibility for visual-only and boundary-specific geometry;
- ramp-width correction toward the 4 m group-width contract;
- preparation for future environment/resources work.

The map topology, Base/Objective XY anchors and authoritative gameplay symmetry remain frozen.

## Current map contract

- gameplay area: **200 × 200 m**;
- world floor: **220 × 220 m**;
- capture objectives: **5/5**;
- team bases: **2**;
- gameplay pockets: **4**;
- outer boundary: **elliptical, 48 segments**;
- gameplay symmetry: `(x,y,z) -> (-x,y,z)`;
- symmetry tolerance: **0.25 m**;
- deterministic seed: **1337**.

## Implemented in the current branch

### 1. Outer Boundary

The global perimeter is generated as a single organic elliptical wall system. The generator performs a hard footprint fit against the world boundary rather than relying only on object-center placement.

The Crown north sector receives an intentional opening so that the perimeter does not seal the Crown approach.

The normal validator must treat these boundary segments as a dedicated perimeter condition rather than ordinary gameplay-object bbox checks.

### 2. Crown Sanctum integration

The Crown remains the fifth northern capture point and is augmented by a separate Crown Sanctum PvE landmark.

Current Crown presentation contract:

- smooth semi-oval rise;
- central Crown Boss Button / Aether Button;
- ruined half-coliseum open toward the south/front;
- **lower throne plate only**;
- upper throne tiers and connector structures removed;
- capture control remains distinct from the boss button.

The latest runtime reports a raised Crown support surface and a post-generation visibility correction for the capture control.

### 3. Capture Button + Indicator

All five objectives receive:

- `CaptureButton_<Point>` — logical interaction anchor;
- `CaptureIndicatorRing_<Point>` — visual capture-state ring.

The button occupies **70% of the objective-platform radius**. The remaining outer 30% is reserved for the indicator ring.

The capture button metadata stores its objective identity, logical capture role, road anchor and neighboring capture buttons. Roads and ramps are then bound to these logical anchors.

### 4. Crown visual links and road light guides

The Crown capture control receives two short visual-only links to the neighboring objective controls:

- Crown → WestMonolith;
- Crown → EastMonolith.

The ring road network receives thin center light guides. These guides are visual-only and must not affect navigation or collision.

### 5. Ramp-width correction

The explicit ramp builder previously generated ramps below the intended 4 m group-width contract. The current configuration was increased so that the builder's 60% runtime multiplier targets the required minimum group width.

This is a geometry correction only; it does not move the objective anchors.

## Latest runtime evidence

The latest supplied Blender 5.2 run confirms:

- terrain slope audit: **PASS**, maximum sampled terrain slope **19.88°**;
- Crown Sanctum generated and symmetric;
- capture overlays: **10 objects / 5 logical anchors**;
- Crown capture node present;
- Crown visual correction executed;
- road center light guides generated;
- capture button routing: **PASS, 18 links**;
- graded ramps built: **5**;
- pockets reachable: **4/4**;
- gameplay symmetry: **PASS**;
- dedicated minion traversal regression: **PASS** for both tested team scenarios;
- validation gate: **FAILED** on this runtime.

The validation failure is not accepted as a release state.

## Validation findings from the latest run

The latest run reported the following classes of issues:

### A. Visual-guide dimension false positives

Two Crown capture-link objects were reported as invalid solids even though they are thin visual-only guide meshes. The current runtime validation compatibility pass filters this exact class while preserving unrelated validation errors.

### B. Legacy outer-boundary bbox false positives

Several `OuterBoundary_Segment*.002` objects were reported by the ordinary gameplay bbox validator because the external wall intentionally occupies the perimeter envelope. The current boundary generator already performs a dedicated hard footprint test; the runtime validation compatibility pass removes only the duplicated legacy bbox failure.

### C. Height-audit false positives at Altar

The central Altar is a deliberate solid landmark. The height-transition audit could interpret the anchored start cell as a blocking cell and then incorrectly flag corridor width / blocker problems. The runtime correction makes the first anchored segment endpoint-aware and leaves later route measurements unchanged.

### D. Ramp group width

The runtime that produced this record showed several ramp widths below the 4 m group target. The configuration has now been corrected. A fresh Blender run is required to confirm the generated ramp widths and reachability.

### E. Crown structural overlap warnings

The runtime still reports several `SOLID OVERLAP` warnings among Crown coliseum pieces and the lower throne plate. These remain **warnings**, not silently accepted design facts. They must be reviewed against the actual generated geometry before MAP LOCK.

## Resources / Environment status

The v0.6.4 roadmap still reserves this phase for environment and resources, but the supplied runtime/auditor explicitly reports that no Shrine/Relic/Resource-named objects were created by the current tool.

Therefore:

- resource system: **NOT IMPLEMENTED in the current map generator**;
- environment dressing beyond existing procedural geometry: **not closed**;
- resource placement must be tracked as separate implementation work rather than claimed complete.

## Non-negotiable constraints

1. Base and Objective XY coordinates remain unchanged.
2. Team-critical geometry remains mirrored under `(x,y,z) -> (-x,y,z)`.
3. Decorative visual guides must remain navigation-neutral.
4. Outer Boundary may occupy the perimeter envelope but must pass its dedicated hard footprint test.
5. A validation filter may remove only a confirmed false positive with an explicit reason and narrow name/type scope.
6. A version is not closed while genuine validation errors remain.
7. `PASS`, `FAILED`, `WARNING`, `EXACT`, `APPROXIMATION` and `DATA MISSING` must retain their literal report meaning.

## Closure gate

v0.6.4 is complete only after a fresh Blender 5.2 runtime verifies:

- validation gate passes with no genuine errors;
- Crown visual correction remains visible;
- capture buttons and indicator rings exist for all 5 objectives;
- capture routing remains complete;
- Crown outer-wall opening remains intentional and reachable;
- ramp widths meet the 4 m group target;
- minion traversal remains PASS for both mirrored scenarios;
- navigation problems = **0**;
- pockets reachable = **4/4**;
- gameplay symmetry = **PASS**;
- Blue/Red route fairness remains **0.0%**;
- evaluated-mesh intersections remain **0**;
- genuine Crown structural overlaps are resolved or explicitly accepted with measured evidence;
- resource/environment work is either implemented and validated or explicitly moved to the next tracked task.

## Next

After v0.6.4 closure, continue with **v0.6.5 — FULL DOMINION SIMULATION + MAP BALANCE**, followed by v0.6.6 MAP LOCK.
