# AetherFlow — Development Roadmap

> **Status:** ACTIVE / CANONICAL  
> **Starting point:** v0.6.4.0  
> **Rule:** Do not redo completed systems. Every next version extends the verified current foundation.

## 0. CURRENT STATE — v0.6.4.0

AetherFlow is **not being created from zero**. The current project already contains a procedural 200×200 m gameplay map with 5 objectives, 2 bases, terrain/heightmap, roads, ramps, 4 gameplay pockets, cover, boundary, navigation, LOS analysis, deterministic generation, validation and `map_data.json` export.

The current generator also contains capture-platform overlays, route bindings, Crown Sanctum/Crown Boss presentation and base-shop blockouts. The current technical simulation measures traffic, fights, exposure, cover usage and route data, but it is **not yet a full match simulation**: objective ownership is still synthetic and there is no complete player/minion/economy runtime.

Latest recorded runtime state must be treated literally:

- dedicated terrain/minion traversal checks: PASS;
- 5/5 objectives: present;
- 4/4 pockets: reachable;
- gameplay symmetry: PASS;
- capture-button route binding: PASS;
- Stage 9 overall validation: FAILED;
- Crown structural overlap review: OPEN;
- resource generation: NOT IMPLEMENTED;
- final MAP LOCK: NOT REACHED.

The roadmap therefore starts with **v0.6.4.0 closure**, not with map creation from scratch.

---

# PHASE 1 — FINISH THE EXISTING MAP FOUNDATION

## v0.6.4.0 — MAP FOUNDATION CLOSURE

**Current version.**

### Goal
Bring the existing map generator and generated scene to a clean, repeatable technical baseline.

### Actions
1. Run the fresh Blender 5.2 generation from a clean managed scene.
2. Verify the outer boundary and intentional Crown opening.
3. Verify all 5 capture platforms, buttons and indicator rings.
4. Verify Crown capture layer is separate from Crown Boss layer.
5. Verify ramp generation and 4 m group-width target.
6. Review genuine Crown overlaps; do not hide them with broad validation filters.
7. Verify navigation, LOS, symmetry, pocket reachability and objective access.
8. Verify obsolete default Cube cleanup.
9. Verify `map_data.json` export and stable IDs.
10. Record one authoritative runtime report.

### Exit gate
No unexplained Stage 9 errors. Any remaining warning must have an explicit design disposition. This version is closed only on real Blender evidence.

---

## v0.6.4.1 — RESOURCE FOUNDATION

### Goal
Add the first strategic map resources that make rotation decisions meaningful.

### Actions
1. Define Health Relic spatial markers.
2. Define Speed Shrine spatial markers.
3. Define the central Aether resource / landmark resource.
4. Give every resource a stable ID, radius and gameplay role.
5. Define respawn placeholders/timers in data only.
6. Define visibility and interaction anchors.
7. Add resources to `map_data.json`.
8. Test Blue/Red access symmetry and alternative approaches.

### Exit gate
Resources exist in the generated scene and export, do not block roads/navigation, and have measured fairness data.

---

## v0.6.4.2 — ENVIRONMENT + PERIMETER COMPLETION

### Goal
Finish gameplay-aware environmental dressing without changing the map's authoritative topology.

### Actions
1. Integrate natural perimeter assets into the active generation path.
2. Improve rocks, cliffs, shrubs, grass and plants by gameplay zone.
3. Keep objectives, roads, ramps, pockets and combat corridors protected from decorative blockage.
4. Remove duplicate boundary/pocket fence generation.
5. Verify visual hierarchy and repetition.
6. Verify deterministic environment generation.

### Exit gate
Environment is deterministic, gameplay-safe and validated against navigation/LOS.

---

## v0.6.4.3 — GAMEPLAY MARKERS + MAP DATA CONTRACT

### Goal
Complete the Blender-side spatial data contract required by UE5.

### Actions
1. Unified objective markers.
2. Base and spawn markers.
3. Shop markers.
4. Resource markers.
5. Capture interaction points.
6. UI anchors.
7. Route IDs.
8. Objective adjacency data.
9. Minion route source/destination data.
10. Stable schema/versioning for `map_data.json`.

### Exit gate
All gameplay-critical spatial entities are exported through one consistent schema.

---

## v0.6.4.4 — MAP GAMEPLAY READABILITY PASS

### Goal
Ensure the physical map communicates the intended fast capture/rotation gameplay before runtime implementation.

### Actions
1. Verify every objective has multiple approaches.
2. Verify macro loop and internal shortcuts.
3. Verify flank/interception routes.
4. Verify retreat routes.
5. Verify no objective becomes a dead-end.
6. Verify central AetherCore does not become an accidental choke trap.
7. Verify Crown approach/opening readability.
8. Measure travel-time symmetry.

### Exit gate
The map supports fast 5v5 rotation without turning into a conventional three-lane MOBA.

---

# PHASE 2 — PRE-UE5 GAMEPLAY SIMULATION

## v0.6.5.0 — MATCH SIMULATION FOUNDATION

### Goal
Turn the current technical map simulation into a deterministic model of an actual AetherFlow match.

### Actions
1. Replace synthetic objective ownership with a real objective state machine.
2. Define Neutral / Blue / Red / Contested / Capturing / Neutralizing states.
3. Define capture and neutralization timing.
4. Define interruption rules.
5. Define multi-player capture acceleration and diminishing returns.
6. Define objective control pressure.
7. Define Team Core / Ticket model.
8. Define victory/defeat conditions.
9. Add match clock and match phases.

### Important
AetherFlow is **inspired by Dominion's objective-control structure**, but exact values are original AetherFlow balance decisions.

### Exit gate
A complete deterministic simulated match can start, change objective ownership and end with a valid winner.

---

## v0.6.5.1 — MINION OBJECTIVE PRESSURE

### Goal
Create objective-driven minion pressure rather than traditional three-lane farming.

### Actions
1. Objective-to-objective wave definitions.
2. Source objective.
3. Destination objective.
4. Route selection.
5. Spawn cadence.
6. Minion role composition.
7. Target selection.
8. Objective interaction.
9. Wave termination.
10. Gold/reward hooks.

### Exit gate
Every simulated wave has an explicit reason, route and destination.

---

## v0.6.5.2 — RESOURCES + MAP EVENTS

### Goal
Connect resources and controlled events to the match simulation.

### Actions
1. Health recovery resource behavior.
2. Speed/rotation resource behavior.
3. Central Aether resource contest.
4. Respawn timers.
5. Visibility rules.
6. Resource denial.
7. Risk/reward scoring.
8. Optional timed map events.

### Exit gate
Resources measurably change rotation decisions without dominating the match.

---

## v0.6.5.3 — 5v5 SCENARIO SUITE

### Goal
Stress-test the map/gameplay loop before UE5 implementation.

### Required scenarios
- equal opening;
- early one-point lead;
- two-point lead;
- center pressure;
- split pressure;
- deathball;
- backdoor attempt;
- contested objective;
- resource contest;
- resource denial;
- comeback;
- prolonged 5v5 fight;
- double-flank interception.

### Metrics
- first contact;
- time-to-objective;
- capture time;
- neutralization time;
- retreat time;
- route asymmetry;
- flank availability;
- objective exposure;
- cover/LOS advantage;
- resource access;
- deathball concentration;
- backdoor success;
- comeback frequency;
- match duration.

### Exit gate
Known balance problems are measurable rather than anecdotal.

---

## v0.6.5.4 — DOMINION-STYLE BALANCE PASS, AETHERFLOW RULES

### Goal
Use the lessons of capture-control games while defining AetherFlow's own numbers and rules.

### Actions
1. Tune objective pressure.
2. Tune Team Core / Ticket drain.
3. Tune kill contribution.
4. Tune capture-event impact.
5. Tune comeback potential.
6. Tune minion pressure.
7. Tune resources.
8. Tune map event frequency.
9. Tune target match duration.
10. Remove snowball states that become irreversible too early.

### Exit gate
The game produces meaningful map-control advantage without making the first successful rotation decide the match.

---

# PHASE 3 — MAP LOCK

## v0.6.6.0 — FINAL MAP VALIDATION

### Goal
Freeze the Blender/Python map as the source asset for UE5.

### Actions
1. Clean generation from empty managed scene.
2. Determinism test with identical seed.
3. Full navigation regression.
4. Full LOS regression.
5. Full symmetry regression.
6. Full objective/base/resource validation.
7. Full minion-route validation.
8. Full export validation.
9. Validate object IDs and transforms.
10. Compare final metrics against baseline.

### Exit gate
Validation PASS with no unexplained regressions.

---

## v0.6.6.1 — MAP LOCK

Freeze:

- objective positions;
- base positions;
- macro route topology;
- roads;
- ramps;
- pockets;
- gameplay cover;
- resource positions;
- gameplay markers;
- export schema.

After MAP LOCK, gameplay development must not casually modify fundamental map topology. Changes become explicit map revisions.

---

# PHASE 4 — UNREAL ENGINE 5 FOUNDATION

## v0.7.0.0 — UE5 PROJECT FOUNDATION

### Goal
Create the runtime architecture around the locked map.

### Actions
1. UE5 project structure.
2. C++ gameplay modules.
3. source control integration.
4. gameplay folder/naming conventions.
5. GameMode.
6. GameState.
7. PlayerState.
8. TeamState.
9. data assets/config strategy.
10. logging/debug strategy.

---

## v0.7.1.0 — MAP IMPORT + PARITY

### Actions
1. Import terrain.
2. Import structures.
3. Import roads and ramps.
4. Import rocks/environment/boundary.
5. Import `map_data.json`.
6. Bind stable IDs.
7. Rebuild collision.
8. Rebuild NavMesh.
9. Verify Blender ↔ UE5 transform parity.

### Exit gate
UE5 map matches the locked Blender map within defined tolerances.

---

# PHASE 5 — PLAYABLE AETHERFLOW CORE

## v0.8.0 — OBJECTIVE RUNTIME

1. Objective Actor.
2. Ownership.
3. Neutralization.
4. Capture.
5. Contest.
6. Capture interruption.
7. Objective UI data.
8. Objective alerts.
9. Team Core / Ticket integration.
10. Victory/defeat.

### Exit gate
A player can join a match and change the state of all five objectives through actual gameplay.

---

## v0.8.1 — MATCH FLOW

1. Match initialization.
2. Team assignment.
3. Spawn.
4. Pre-match countdown.
5. Live match.
6. Victory/defeat.
7. Post-match state.
8. Restart/reset.

---

## v0.9.0 — PLAYER FOUNDATION

1. Character.
2. Controller.
3. Camera.
4. Movement.
5. interaction.
6. targeting.
7. death.
8. respawn.
9. capture interaction.
10. movement modifiers from map resources.

---

## v0.10.0 — COMBAT FOUNDATION

1. Health.
2. Damage.
3. Death.
4. Basic attack.
5. Targeting.
6. Combat states.
7. Damage feedback.
8. Basic combat logging.

---

## v0.11.0 — HERO FRAMEWORK

1. Hero stats.
2. Ability framework.
3. Cooldowns.
4. Resources.
5. Status effects.
6. Targeting rules.
7. Ability feedback.
8. Hero data assets.

---

## v0.12.0 — HERO #1

Build the first complete playable AetherFlow hero and use it as the reference implementation for the hero framework.

Exit gate: one hero can move, fight, capture, die, respawn and participate meaningfully in objective play.

---

# PHASE 6 — MINIONS / ECONOMY / ITEMS

## v0.13.0 — MINIONS

1. Wave spawning.
2. Objective source/destination.
3. Navigation.
4. AI.
5. Combat.
6. Targeting.
7. Capture pressure.
8. Death/reward.
9. Wave pacing.

## v0.14.0 — ECONOMY

1. Gold.
2. Kill rewards.
3. Objective rewards.
4. Resource rewards.
5. Match economy.
6. Anti-snowball rules.

## v0.15.0 — SHOP + ITEMS

1. Shop runtime.
2. Item definitions.
3. Purchases.
4. Inventory.
5. Stats.
6. Item effects.
7. Base shop interaction.

---

# PHASE 7 — TEAM / FULL 5v5

## v0.16.0 — TEAM SYSTEM

1. Teams.
2. Allies/enemies.
3. Team spawn.
4. Team score.
5. Team state.
6. shared objective state.

## v0.17.0 — COMPLETE 5v5 PLAYABLE

The first complete playable AetherFlow match:

- 5 players per team;
- five objectives;
- Team Core/Ticket model;
- minions;
- combat;
- economy;
- shop/items;
- resources;
- respawn;
- victory conditions.

This is the major **vertical slice** milestone.

---

# PHASE 8 — AETHERFLOW GAME MODES

## v0.18.0 — STATIC

The stable baseline mode. Geometry and core rules remain predictable.

## v0.19.0 — HYBRID

Controlled combination of fixed and dynamic objective/event rules.

## v0.20.0 — DYNAMIC

Dynamic objective state and controlled map-state events.

Each mode must reuse the same authoritative core systems instead of creating parallel objective/combat implementations.

---

# PHASE 9 — MULTIPLAYER

## v0.21.0 — NETWORK FOUNDATION

1. Server authority.
2. Replication.
3. Player state.
4. Team state.
5. Objective replication.
6. Minion replication.
7. Resource replication.

## v0.22.0 — ONLINE MATCH FLOW

1. Lobby.
2. Session.
3. Match start.
4. Connect/disconnect.
5. Rejoin handling.
6. Match completion.

---

# PHASE 10 — UI / GAME FEEL / CONTENT

## v0.23.0 — CORE HUD

The HUD must prioritize battlefield information:

- Team Core/Ticket state;
- five objective states;
- minimap;
- player state;
- active event/resource state;
- combat feedback.

## v0.24.0 — GAME FEEL

- VFX;
- SFX;
- hit feedback;
- capture feedback;
- movement feedback;
- camera polish;
- objective feedback.

## v0.25.0 — HERO ROSTER

Expand the hero roster only after the first hero and core combat framework are stable.

## v0.26.0 — CONTENT

- environment polish;
- additional objectives/events;
- audio;
- effects;
- cosmetics where appropriate;
- additional map/content only after the primary loop is stable.

---

# PHASE 11 — BALANCE / QA / RELEASE

## v0.27.0 — BALANCE

- objective balance;
- heroes;
- items;
- economy;
- minions;
- resources;
- game modes;
- match duration.

## v0.28.0 — QA

- functional testing;
- regression;
- multiplayer testing;
- exploit testing;
- edge cases;
- save/load/reset tests where applicable.

## v0.29.0 — PERFORMANCE

- CPU;
- GPU;
- memory;
- network;
- loading;
- scalability;
- server performance.

## v0.30 — ALPHA

First internally complete playable build.

## v0.40 — BETA

Feature-complete candidate focused on balance and stability.

## v0.90 — RELEASE CANDIDATE

Final stabilization and certification.

## v1.0.0 — RELEASE

First official AetherFlow release.

---

# DEVELOPMENT RULES

1. **Start from the current verified state, never from zero.**
2. **No duplicate gameplay systems.** One authoritative source of truth per state.
3. **Map topology stays frozen after MAP LOCK.**
4. **Gameplay first, decoration second.**
5. **Every major mechanic gets design + acceptance criteria before implementation.**
6. **Use measured simulation and test results for balance decisions.**
7. **Do not copy League of Legends assets, names, UI art, proprietary map geometry or exact rules.** Use Dominion only as a system-level reference.
8. **Never claim PASS, TESTED or DONE without evidence.**
9. **Every version must have an explicit exit gate.**
10. **Every regression must be recorded in `Aetherflow Docs/08_Testing_QA`.**
11. **Version documentation belongs in `Aetherflow Docs/01_Versions/<version>/`.**
12. **The roadmap is the canonical development order; implementation details belong in the relevant Design/Gameplay/Technical documents.**

# CURRENT PRIORITY

**v0.6.4.0 closure → v0.6.4.1 resources → v0.6.4.2 environment → v0.6.4.3 gameplay data contract → v0.6.4.4 map readability → v0.6.5 match simulation → v0.6.6 MAP LOCK → v0.7 UE5.**
