# AetherFlow — Canonical Development Roadmap

> **Document status:** ACTIVE / CANONICAL
>
> This roadmap defines the development order for AetherFlow. It is inspired by the gameplay principles of League of Legends: Dominion / Crystal Scar, but AetherFlow is an original game and must not copy Riot's assets, names, UI art, map geometry or proprietary presentation.

---

# 0. PRODUCT TARGET

AetherFlow is a fast 5v5 competitive action game built around **capture-and-hold territory control**, rapid rotations, short combat cycles and constant objective pressure.

The core experience target is the part of Dominion that made the mode structurally different from a traditional MOBA:

- five important capture objectives;
- a continuous circular/looping rotation network instead of three lanes;
- control of objectives is the primary source of team advantage;
- the enemy base has an abstract health/ticket value rather than being directly attacked;
- kills, captures and objective advantage all contribute to victory;
- short travel times and frequent fights;
- strong comeback potential;
- meaningful neutral resources and map events;
- highly readable macro UI showing the state of the whole battlefield.

AetherFlow adds its own identity through **AetherCore / Aether Altar**, **Crown Sanctum / Crown Boss**, the future **Static / Hybrid / Dynamic** modes, and its own art direction and terminology.

---

# 1. DESIGN REFERENCE: WHAT WE ARE REPRODUCING AT THE SYSTEM LEVEL

The Dominion reference research establishes several high-value principles.

## 1.1 Map structure

Crystal Scar used five capture points arranged around a circular map. The outer route was the primary rotation layer, while inner connections created interceptions, ambushes and shortcuts. The map was deliberately unlike a conventional three-lane MOBA. citeturn584165search2turn584165search7

**AetherFlow target:** preserve the 5-objective loop, multiple entry/exit routes, internal shortcuts and flank opportunities, while keeping our own geometry, landmarks and base layout.

## 1.2 Objective structure

Dominion capture points had three states: allied, enemy and neutral. Capturing an enemy point required first neutralizing it, then capturing it. A normal champion channel took approximately 10 seconds for one transition; additional participants accelerated progress. Champion damage/movement could interrupt a capture channel. citeturn547633search2turn584165search0

**AetherFlow target:** objectives are not simple on/off buttons. They have ownership, neutralization, capture progress, contesting, defensive pressure and route-driven reinforcement.

## 1.3 Victory model

The Dominion Nexus was untargetable and started at 500 health. Team objective advantage drained enemy Nexus health over time; equal objective control stopped passive drain. Champion takedowns also reduced Nexus health by 2, with kill-based damage disabled once the Nexus was at or below 100 health. A capture also immediately damaged the enemy Nexus. citeturn547633search0turn547633search1

**AetherFlow target:** use an abstract **Team Core / Ticket** model rather than a standard MOBA Nexus siege. Exact values will be balance-tuned in v0.6.5.

## 1.4 Minion pressure

In Dominion, controlled neighboring objectives could create minion waves whose destination was another capture point. The wave did not continue indefinitely around the map; it had a specific objective destination. citeturn584165search0

**AetherFlow target:** minions exist to create objective pressure, not to recreate three-lane farming. Every wave needs a clear source, destination, route and reason for existence.

## 1.5 Map resources

Crystal Scar used health relics, speed shrines and central Greater Relics. Health relics supported sustain, speed shrines accelerated rotations, and the central Greater Relics created contested high-value fights. citeturn547633search5turn584165search4

**AetherFlow target:** resources must change rotation decisions and create risk/reward choices. They should not become random decorative pickups.

## 1.6 Quests / dynamic objectives

Dominion introduced timed capture quests. After roughly five minutes, teams received objectives such as taking an enemy point and defending an allied point; completing them damaged the enemy Nexus and granted a team combat reward. New quests could appear later. citeturn584165search0

**AetherFlow target:** introduce dynamic match objectives only after the basic capture loop is stable. These belong in the later simulation layer, not in the base map generator.

## 1.7 Vision model

The outer route of Crystal Scar was largely revealed, while specific inner passages retained fog-of-war opportunities for ambushes and movement masking. Health relics around objectives were not simply always visible, while central relics were intentionally prominent. citeturn584165search0turn584165search3

**AetherFlow target:** combine a readable macro layer with deliberate local fog pockets. The entire map should not become either fully visible or fully hidden.

## 1.8 UI / information architecture

Historical Dominion HUD screenshots show a persistent top-level team score display, player combat HUD at the bottom, minimap on the right, and prominent event/capture announcements during combat. citeturn444619image2turn278551image1turn278551image4

**AetherFlow target:** prioritize battlefield state over clutter. The player must understand, at a glance:

- team Core/Ticket health;
- which of five objectives are Blue / Red / Neutral / Contested;
- where teammates are;
- where objective pressure is moving;
- which dynamic event is active;
- current personal combat state.

---

# 2. AETHERFLOW CURRENT FOUNDATION

Current repository work already provides a strong technical map foundation:

- 200 × 200 m gameplay area;
- 220 × 220 m world floor;
- 5 capture objectives;
- 2 team bases;
- 4 gameplay pockets;
- road network and ramps;
- central AetherCore / Aether Altar;
- Crown Sanctum presentation;
- procedural terrain;
- outer boundary;
- navigation grid;
- gameplay cover;
- deterministic generation;
- validation;
- `map_data.json` export.

The current v0.6.4 runtime documentation still records **Stage 9 validation as FAILED**, so the map is not considered locked. The current runtime also records resource generation as not implemented. These are open gates, not completed features.

---

# 3. PHASE 1 — BLENDER / PYTHON / MAP DEVELOPMENT

## v0.6.1 — FOUNDATION — CLOSED

Historical baseline.

Purpose:
- establish the procedural map;
- establish deterministic generation;
- establish five objectives and two bases;
- establish roads, ramps, pockets, terrain and validation.

No redesign from scratch is permitted.

---

## v0.6.2 — GAMEPLAY DRESSING / INTERACTION FOUNDATION

Purpose:
- convert geometry into a readable gameplay space;
- create the data foundation required by UE5;
- add tactical cover and environmental rules without damaging topology.

Key work:
- gameplay cover;
- rocks and tactical formations;
- natural environment integration;
- objective dressing;
- capture markers;
- interaction anchors;
- future shop markers;
- unified gameplay markers;
- export extensions;
- deterministic environment safety.

---

## v0.6.3 — TERRAIN / ROUTES / COMBAT-SPACE REFINEMENT

Purpose:
- fix real measured problems in movement and combat space;
- preserve objective/base anchors;
- avoid arbitrary geometry churn.

### v0.6.3.1 — Terrain refinement
Crown, Core, Monoliths, South Rift and transition profiles.

### v0.6.3.2 — Height transitions
Hero/minion slopes, ramp safety, group width, route height deltas and traversal audits.

### v0.6.3.3 — Road network refinement
Base → objective, objective → objective, outer rotation, inner rotation, flank and retreat routes.

### v0.6.3.4 — Ramp refinement
Verify ramps for hero, minion, group and five-player movement.

### v0.6.3.5 — Pocket refinement
West/East/SW/SE pockets remain flank, ambush and retreat spaces.

### v0.6.3.6 — Combat cover refinement
Use the existing optimizer only where tests identify LOS/combat-space problems.

### v0.6.3.7 — Combat-space testing
1v1, 2v2, 3v3 and 5v5 objective fights plus retreat, flank, interception, defense and assault scenarios.

### v0.6.3.8 — Deathball mitigation
Use route topology, LOS breaks, controlled chokes and flank opportunities; do not solve deathball by filling the map with obstacles.

---

# 4. v0.6.4 — DOMINION-STYLE MAP LOOP COMPLETION

**CURRENT PHASE**

The goal of v0.6.4 is no longer merely "environment polish". It is to make the physical map support the intended fast capture-and-rotate gameplay loop.

## 4.1 Objective network

Verify the five-point macro loop:

`Base → Objective → Objective → Objective → Objective → Objective → Base`

Requirements:

- every objective has multiple meaningful approaches;
- at least one fast macro rotation path exists;
- flank/interception routes exist without creating a second three-lane map;
- no objective should become a dead-end;
- route times between neighboring objectives must remain tightly controlled;
- Blue/Red symmetry/fairness remains within the existing hard tolerance.

## 4.2 Objective gameplay presentation

Every objective must expose the same conceptual layers:

```text
Objective Actor
├── Physical Capture Platform
├── Capture Indicator
├── Capture Interaction
├── Defensive/Offensive tactical space
└── World-space UI anchor
```

Crown additionally contains its separate boss layer:

```text
Crown Capture Objective
+
Crown Sanctum / Crown Boss
```

The boss interaction must never substitute for capture interaction.

## 4.3 Resources

Implement map-resource foundations required for rotation:

- Health Relics;
- Speed Shrines;
- central high-value resource / Aether resource;
- stable respawn timers;
- resource ownership/visibility rules;
- UI anchors;
- export IDs.

The exact AetherFlow resource names and buffs are proprietary AetherFlow design decisions and must be documented before implementation.

## 4.4 Minion objective pressure foundation

Add Blender-side data for:

- source objective;
- destination objective;
- route ID;
- wave spawn point;
- lane/road class;
- tactical priority.

No infinite free-roaming minions.

## 4.5 Vision / fog foundation

Define gameplay vision zones:

- permanently readable outer macro routes;
- controlled fog corridors;
- pocket ambush zones;
- objective visibility rules;
- resource visibility rules.

These rules must later be implemented in UE5, but the map must expose the required spatial markers now.

## 4.6 Capture UI data contract

Prepare data for:

- Neutral;
- Blue-controlled;
- Red-controlled;
- contested;
- capture progress;
- neutralization progress;
- capture direction;
- objective alert;
- world-space objective anchor;
- minimap icon state.

## 4.7 Validation gate

v0.6.4 cannot close while:

- genuine Stage 9 errors remain;
- Crown structural overlaps remain unresolved without measured acceptance;
- ramp width is not runtime-verified;
- navigation problems exist;
- 4/4 pockets are not reachable;
- objective route fairness fails;
- resource generation remains untracked.

---

# 5. v0.6.5 — FULL DOMINION-STYLE MATCH SIMULATION + BALANCE

This is the most important pre-UE5 gameplay phase.

## 5.1 Team Core / Ticket model

Implement deterministic team health/ticket simulation.

The model must support:

- starting health;
- passive drain based on objective advantage;
- capture event damage;
- champion-kill contribution;
- minimum-health anti-ninja-cap protection;
- comeback potential;
- explicit victory condition.

Reference baseline: Dominion historically used 500 Nexus health, objective differential drain and -2 for champion takedowns. citeturn547633search0turn547633search1

AetherFlow values must be tuned independently during balance testing.

## 5.2 Objective state machine

Authoritative states:

`NEUTRAL → CAPTURING → BLUE / RED → NEUTRALIZING → CONTESTED`

Requirements:

- champion capture channel;
- interrupt rules;
- multi-player acceleration with diminishing returns;
- minion capture pressure;
- point defense;
- turret/objective attack behavior where applicable;
- capture event notifications.

## 5.3 Objective differential pressure

Model the strategic pressure generated by holding:

- 0 objectives;
- 1 objective;
- 2 objectives;
- 3 objectives;
- 4 objectives;
- 5 objectives.

The system must reward map control without creating an irreversible early snowball.

## 5.4 Minion pressure

Build explicit objective-to-objective waves.

Each wave has:

- source;
- destination;
- route;
- spawn cadence;
- combat behavior;
- capture behavior;
- termination condition.

Reference principle: Dominion minions had explicit neighboring objective destinations rather than travelling indefinitely. citeturn584165search0

## 5.5 5v5 scenarios

Mandatory deterministic scenarios:

- equal start;
- one-point advantage;
- two-point advantage;
- early center pressure;
- split push;
- deathball;
- backdoor capture;
- stalled contest;
- comeback from low Core/Ticket value;
- prolonged 5v5 objective fight;
- resource contest;
- resource denial;
- double-flank interception.

## 5.6 Balance metrics

Collect:

- time-to-first-contact;
- time-to-objective;
- objective capture time;
- neutralization time;
- route asymmetry;
- retreat time;
- flank availability;
- objective exposure;
- LOS advantage;
- resource access;
- deathball concentration;
- comeback frequency;
- backdoor success rate;
- match duration.

## 5.7 Dynamic objective events

Introduce a controlled event layer inspired by Dominion's timed quests, but with original AetherFlow objectives and rewards. Dominion used timed capture/defense quests that rewarded successful teams with Nexus damage and a team combat buff. citeturn584165search0

AetherFlow events must be:

- readable;
- optional where appropriate;
- contested;
- strategically meaningful;
- non-dominating;
- deterministic in test mode.

---

# 6. v0.6.6 — MAP LOCK / EXPORT LOCK

The last Blender/Python milestone before UE5.

Requirements:

- clean generation from empty managed scene;
- deterministic repeatability;
- 5 objectives;
- 2 bases;
- all required routes;
- ramps;
- pockets;
- resources;
- cover;
- LOS;
- minion routes;
- gameplay markers;
- map export;
- validation PASS;
- no unexplained geometry regressions.

At MAP LOCK freeze:

- objective anchors;
- base anchors;
- macro route topology;
- gameplay geometry;
- resource locations;
- marker IDs;
- export schema.

After MAP LOCK, map changes require an explicit map revision.

---

# 7. PHASE 2 — UNREAL ENGINE 5

## v0.7.0 — UE5 FOUNDATION

Import the locked Blender map into UE5.

### v0.7.0.1 — Project foundation
- project structure;
- C++ modules;
- source control;
- naming conventions;
- gameplay folder structure.

### v0.7.0.2 — Map import
- terrain;
- structures;
- roads;
- ramps;
- rocks;
- environment;
- boundary.

### v0.7.0.3 — Collision / NavMesh
- player walkability;
- minion navigation;
- ramps;
- collision;
- perimeter.

### v0.7.0.4 — Map-data import
Import and bind:

- objectives;
- bases;
- shops;
- capture zones;
- markers;
- resources;
- UI anchors;
- route data.

### v0.7.0.5 — Blender ↔ UE5 parity
Compare:

- dimensions;
- transforms;
- IDs;
- collision;
- navigation;
- gameplay zones.

---

# 8. PHASE 3 — DOMINION-STYLE GAMEPLAY CORE

## v0.8.x — MATCH / OBJECTIVES

- match state;
- Team Core/Ticket system;
- objective ownership;
- neutralization;
- capture/contest;
- objective drain;
- win/lose conditions;
- event system.

## v0.9.x — PLAYER FOUNDATION

- character;
- controller;
- movement;
- camera;
- spawn;
- respawn;
- interaction;
- objective capture interaction.

## v0.10.x — COMBAT FOUNDATION

- health;
- damage;
- death;
- targeting;
- basic attack;
- combat feedback.

## v0.11.x — ABILITY FRAMEWORK

- abilities;
- cooldowns;
- resources;
- targeting;
- effects;
- status effects.

## v0.12.x — HERO #1

First complete AetherFlow hero used as the combat/reference implementation.

## v0.13.x — MINIONS

- objective-directed spawning;
- route-following;
- objective combat;
- capture pressure;
- anti-stall rules;
- rewards.

## v0.14.x — ECONOMY

- passive income;
- kill rewards;
- objective rewards;
- resource rewards;
- match economy.

## v0.15.x — SHOP / ITEMS

- shop;
- item definitions;
- purchases;
- inventory;
- item stats;
- item effects.

## v0.16.x — TEAM SYSTEM

- allies/enemies;
- team state;
- team score;
- spawn ownership;
- team events.

## v0.17.x — COMPLETE 5v5 MATCH

Complete local/online-capable match loop:

- 5v5;
- objectives;
- combat;
- minions;
- economy;
- items;
- respawn;
- victory.

---

# 9. PHASE 4 — AETHERFLOW GAME MODES

## v0.18.x — STATIC MODE

Stable core mode. Objective locations and primary rules remain fixed.

## v0.19.x — HYBRID MODE

Combination of fixed macro structure and controlled dynamic objectives/events.

## v0.20.x — DYNAMIC MODE

Dynamic objective/event behavior and controlled map-state changes.

---

# 10. PHASE 5 — MULTIPLAYER

## v0.21.x — MULTIPLAYER FOUNDATION

- authoritative server;
- replication;
- networked movement;
- player state;
- team state;
- objective state.

## v0.22.x — ONLINE MATCH

- lobby;
- sessions;
- connect/disconnect;
- matchmaking foundation;
- full online match flow.

---

# 11. PHASE 6 — UI / GAME FEEL / CONTENT

## v0.23.x — INFORMATION-FIRST HUD

The HUD must make macro control immediately readable.

Required:

- Team Core/Ticket bars;
- five-objective state strip;
- objective ownership colors/state;
- contested indicators;
- minimap;
- player HUD;
- capture progress;
- event banners;
- objective alerts;
- resource timers;
- scoreboard.

Historical Dominion screenshots support the architectural principle of a persistent team-state area, player combat HUD, minimap and event messaging. citeturn444619image2turn278551image1

## v0.24.x — GAME FEEL

- VFX;
- SFX;
- hit feedback;
- capture feedback;
- movement feedback;
- camera polish;
- objective audio states.

## v0.25.x — HERO ROSTER

Expand the hero roster while balancing around the capture-and-rotate structure.

## v0.26.x — CONTENT

- additional environments;
- objective variants;
- VFX/SFX content;
- cosmetics where applicable.

---

# 12. PHASE 7 — BALANCE / QA / RELEASE

## v0.27.x — BALANCE

Balance around:

- heroes;
- items;
- economy;
- objectives;
- minions;
- resources;
- modes.

## v0.28.x — QA

- functional testing;
- regression;
- exploit testing;
- edge cases;
- multiplayer QA;
- objective-state testing.

## v0.29.x — PERFORMANCE

- CPU;
- GPU;
- memory;
- network;
- loading;
- scalability.

## v0.30+ — ALPHA

First complete playable build.

## v0.40+ — BETA

Feature-complete build focused on balance, retention and stability.

## v0.90+ — RELEASE CANDIDATE

Final release hardening.

## v1.0.0 — RELEASE

First official AetherFlow release.

---

# 13. NON-NEGOTIABLE DEVELOPMENT RULES

1. **Gameplay first.** Every major geometry or environment change must have a gameplay reason.
2. **One authoritative implementation.** Do not create parallel objective, capture, cover or navigation systems.
3. **No topology drift before MAP LOCK.** Change layout only when test evidence proves that the current topology is inadequate.
4. **No three-lane conversion.** AetherFlow is a capture-and-rotate game, not Summoner's Rift with different art.
5. **Objective state is authoritative.** UI, minimap, minions and simulation must consume the same objective state.
6. **Minions need destinations.** No infinite wandering.
7. **Resources must affect decisions.** Decorative pickups are not gameplay systems.
8. **Macro readability is mandatory.** A player must quickly understand the five-objective battlefield.
9. **Evidence before balance changes.** Do not nerf or buff geometry from intuition alone.
10. **Validation truth matters.** `PASS`, `FAILED`, `WARNING`, `DATA MISSING` retain their literal meanings.
11. **Original identity.** We use Dominion as a systems reference, not as a source of copied assets or copied level geometry.
12. **Every completed milestone must have measurable acceptance criteria.**

---

# 14. CURRENT PRIORITY

## Active

**v0.6.4 — Dominion-style map loop completion**

Immediate priority order:

1. close genuine Stage 9 validation errors;
2. runtime-verify ramp/group width;
3. resolve or measure Crown structural overlaps;
4. implement resource foundations;
5. finalize objective route/resource fairness;
6. add minion objective-route metadata;
7. finish vision/fog gameplay markers;
8. rerun full Blender 5.2 validation;
9. only then advance to v0.6.5 simulation.

**Current state:** MAP LOCK = NO. UE5 transition = NOT STARTED.
