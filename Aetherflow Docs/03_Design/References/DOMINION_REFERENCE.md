# AetherFlow — League of Legends: Dominion Reference Study

> **Purpose:** systems-level reference for designing AetherFlow. This document describes historical Dominion mechanics and converts them into original AetherFlow design requirements. It is not an instruction to copy Riot Games assets, art, names or exact level geometry.

## 1. What made Dominion different

Dominion was a fast capture-and-hold mode on Crystal Scar. It replaced the classic three-lane structure with five capture points distributed around a looping map. The central gameplay problem was not destroying towers on lanes; it was constantly deciding where the next fight, capture, defense or rotation should happen. citeturn547633search1turn584165search2

### AetherFlow design takeaway

The primary strategic verbs must be:

**CAPTURE → DEFEND → ROTATE → INTERCEPT → PRESSURE → RETREAT → RECAPTURE**

Traditional lane farming must not become the dominant activity.

---

## 2. Crystal Scar map structure

Crystal Scar had five major capture points arranged around a circular/looping outer route. The outer path was broadly readable, while internal passages enabled ambushes and shortcuts. The five locations included Windmill, Drill, Refinery, Quarry and Boneyard. citeturn444619image0turn547633search3turn547633search8

The bases were positioned near different objective pairs, creating immediate asymmetry of access but not a standard three-lane layout. citeturn547633search8

### AetherFlow application

Keep:

- five-objective macro loop;
- neighboring-objective relationships;
- multiple internal routes;
- fast outer rotations;
- deliberate ambush corridors;
- objectives as the map's primary landmarks.

Do not copy:

- Crystal Scar's exact coordinates;
- its terrain silhouette;
- its buildings;
- its visual language;
- its named locations.

AetherFlow's existing Crown / Monolith / AetherCore structure remains the authoritative identity.

---

## 3. Capture point mechanics

A Dominion capture point could be neutral, allied or enemy controlled. Capturing an enemy point required neutralizing it first and then capturing it. A single champion took roughly 10 seconds for one alignment transition; capturing an enemy-controlled point therefore required two transitions. Additional participants accelerated progress. Champion movement or taking champion damage could interrupt channeling. citeturn547633search2turn547633search4

Points could also be pressured by minions. A capture point behaved similarly to a weaker turret and could stop attacking while it was being neutralized. citeturn584165search2

### AetherFlow canonical requirement

The objective state machine must support:

`NEUTRAL`
`BLUE_CONTROLLED`
`RED_CONTROLLED`
`CAPTURE_IN_PROGRESS`
`NEUTRALIZATION_IN_PROGRESS`
`CONTESTED`
`DISABLED`

The implementation must separate:

- ownership state;
- capture progress;
- contest state;
- defensive attack state;
- minion pressure;
- UI state;
- minimap state.

One authoritative objective state must drive all consumers.

---

## 4. Objective pressure and minions

Dominion minions were tied to objective pressure. When an owned objective was adjacent to an enemy objective, a wave could be spawned toward that neighboring target. The wave had a concrete programmed destination rather than endlessly travelling around the map. citeturn584165search0

Historical Dominion waves could include two regular minions plus one super/anti-turret cannon unit. The super unit was particularly effective at helping capture points. citeturn584165search0turn584165search5

### AetherFlow canonical requirement

Every minion wave must contain:

- source objective;
- destination objective;
- route ID;
- spawn marker;
- formation;
- pressure priority;
- termination condition.

Minions must not recreate a permanent three-lane farming layer.

---

## 5. Victory / Core model

Dominion used an untargetable Nexus with 500 health. The enemy Nexus lost health primarily through objective advantage. If one team controlled more capture points than the other, the difference generated periodic damage. Champion takedowns also removed 2 Nexus health. Taking a capture point caused an immediate damage event. Kill-based damage was disabled once a Nexus reached 100 health, preventing a cheap final kill from deciding the game. citeturn547633search0turn547633search1

### AetherFlow canonical requirement

Use an **Aether Core / Team Ticket** abstraction rather than a copy of the League Nexus.

The system must support:

- passive drain from objective advantage;
- capture event damage;
- kill event contribution;
- low-health protection;
- comeback potential;
- explicit victory state.

Numbers are AetherFlow balance values and must not be assumed equal to Dominion.

---

## 6. Map resources

Crystal Scar used several resource systems:

### Health Relics

Health relics were positioned around the map and restored health/mana. A health relic existed behind each capture point, with additional relics around the center. citeturn547633search5

### Speed Shrines

Three speed-shrine areas created short movement-speed boosts and encouraged rotations through the central region. citeturn547633search5turn584165search4

### Greater Relics / Storm Shield

The center contained team-specific high-value relics. The Storm Shield supplied both defensive and offensive benefits and respawned after being consumed. citeturn547633search11turn584165search4

### AetherFlow application

Our resource layer should have at least three strategic roles:

1. **Sustain** — lets a damaged player remain active instead of always returning to base.
2. **Mobility** — changes route choice and contest timing.
3. **High-value contest** — creates a reason for both teams to fight away from the nearest capture point.

The exact AetherFlow resources must remain original and will be specified in the gameplay documents before UE5 implementation.

---

## 7. Dynamic quests / events

Dominion introduced capture/defense quests after the early match phase. A quest could ask a team to capture an enemy point and defend one of its own; completion damaged the enemy Nexus and awarded a temporary team combat buff. New quests could appear later. citeturn584165search0

### AetherFlow application

Create a dynamic event layer only after the base objective loop is stable.

Events should:

- create a new strategic choice;
- pull players into conflict;
- be clearly announced;
- have counterplay;
- never make the previous map state irrelevant;
- avoid stacking excessive permanent buffs.

AetherFlow's Crown Boss and Aether Altar systems must remain separate from the ordinary capture state.

---

## 8. Vision / fog of war

Crystal Scar exposed much of the outer rotation route while preserving hidden internal passages for surprise movement. The central relic area was deliberately prominent but not completely visible. citeturn584165search0turn584165search3

### AetherFlow application

Vision should be layered:

**Macro-visible layer** — major rotation information.

**Local fog layer** — flank corridors, pockets and interception zones.

**Objective visibility layer** — objective ownership and critical status remain readable even when nearby terrain is obscured.

**Resource visibility layer** — important resources can be telegraphed globally while their approach remains tactically uncertain.

---

## 9. UI / information architecture

Historical Crystal Scar HUD screenshots show the core League HUD architecture combined with a strong top-level team-state display, minimap and prominent event/capture notifications. citeturn444619image2turn278551image1turn278551image4

### AetherFlow HUD requirements

## Top center

- Blue Team Core/Tickets;
- Red Team Core/Tickets;
- five objective states;
- current global match/event state.

## Objective strip

Each of the five objectives should display:

- owner;
- neutral/contested state;
- capture progress;
- incoming pressure where useful;
- alert state.

## Bottom HUD

- hero/character identity;
- health;
- resource/mana equivalent;
- abilities;
- cooldowns;
- consumables;
- movement/combat state.

## Minimap

The minimap must prioritize:

- five objectives;
- allies;
- visible enemies;
- active minion pressure;
- resources;
- major event location;
- route readability.

## World-space information

Capture points should have a clear readable hierarchy:

`platform → ownership indicator → capture progress → interaction state`

Crown additionally has:

`Crown capture layer + Crown Boss/Sanctum layer`

The boss layer must never visually masquerade as the capture layer.

---

## 10. Economy and pacing

Historical Crystal Scar changed economy and itemization to support faster matches. Sources document higher early-game resources, faster passive income in the relevant Crystal Scar variants, and specialized items. citeturn584165search8turn584165search0

### AetherFlow application

Economy must support the map's strategic loop:

- players should reach meaningful item decisions early;
- returning to base should have an opportunity cost;
- kills should matter but not replace objectives;
- objective participation should produce meaningful rewards;
- resource contests should create economic tension.

Exact gold values belong in the economy balance specification, not in this reference document.

---

## 11. What AetherFlow should improve over Dominion

Dominion is the reference for the **macro gameplay shape**, not a blueprint to reproduce every historical problem.

AetherFlow should specifically test and improve:

- runaway deathball;
- impossible backdoor defense;
- over-centralized objective snowball;
- overly safe capture channels;
- low-value peripheral areas;
- unclear comeback paths;
- excessive visual clutter;
- poor explanation of why a team is winning.

The existing AetherFlow roadmap already reserves v0.6.5 for full simulation and balance; those tests now need to become objective-state, route, resource and ticket-driven rather than generic combat simulations.

---

## 12. AetherFlow implementation priorities derived from the reference

### Priority 1 — Map flow

Verify the five-point loop and all meaningful rotations.

### Priority 2 — Objective state machine

Make capture, neutralization and contest authoritative.

### Priority 3 — Team Core/Ticket simulation

Create a real win-condition model.

### Priority 4 — Objective-directed minions

Create and test source → destination pressure.

### Priority 5 — Resources

Implement sustain, mobility and high-value contested resources.

### Priority 6 — Vision

Define macro visibility versus local ambush fog.

### Priority 7 — Dynamic events

Introduce quests/events only after the base loop works.

### Priority 8 — Macro HUD

Expose all strategic state without forcing the player to read the minimap constantly.

### Priority 9 — Balance simulation

Measure deathball, backdoor, comeback, route fairness and objective pressure.

### Priority 10 — UE5

Only after the Blender map and simulation satisfy MAP LOCK criteria.
