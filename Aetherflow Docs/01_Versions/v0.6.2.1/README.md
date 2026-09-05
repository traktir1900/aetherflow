# AetherFlow v0.6.2.1 — Gameplay Cover 2.0

## Status

**IN PROGRESS — refinement implementation complete; Blender runtime verification pending**

This version extends the existing v0.6.1 map without changing the fixed layout/topology.

## Baseline

The v0.6.1 gameplay audit reported:

- 5 capture points and 2 bases present;
- navigation fully reachable with no navigation problems;
- Blue/Red base route-time difference: 0.0%;
- 4 gameplay pockets with 3 cover objects each;
- objective cover: 0 in the auditor's objective-cover classification;
- several exact geometry intersections in central cover;
- pocket cover objects intersecting pocket floor mesh;
- no base spawn/shop/health-restore markers;
- no resource or vegetation objects yet.

## Measured v0.6.2.1 runtime baseline

The first real Blender 5.2 generation after the initial v0.6.2.1 implementation produced:

- objective cover: 10 objects across all 5 objectives (2/objective);
- CoreCover total: 26;
- actual evaluated-mesh intersections: 0;
- navigation problems: 0;
- pockets reachable: 4/4;
- Blue/Red base fairness: 0% route-time difference;
- overall auditor score: 88.2/100, up from 81.9/100;
- warnings: 8, down from 20;
- new objective-cover placement still produced **HIGH camping risk** at the four monolith objectives and the central Altar;
- global OuterBoundary bbox warnings/errors remain and are treated as a separate pre-existing boundary task;
- `AltarObstacles` remains data-missing;
- resource and vegetation systems are still not integrated into the main pipeline.

The run confirmed that the initial two-identical-rock implementation was technically active, but its visual impact was weak and its symmetric placement was tactically too camp-friendly.

## Refinement implemented on branch

Branch: `v0-6-2-1-cover-refinement`

### Objective-cover architecture

`core/gameplay_cover.py` was rewritten so objective cover now uses the shared:

`core.cover_analysis.optimize_cover(...)`

instead of hard-coded identical positions.

The refinement adds:

- optimizer-driven candidate selection for each objective;
- LOS, flank, movement and chokepoint weighting through the existing shared cover model;
- a hard exclusion around the capture platform;
- a clear radial approach/retreat lane;
- up to 2 asymmetric flank-oriented cover pieces per objective;
- deterministic fallback placement when optimizer thresholds reject too many candidates;
- explicit metadata identifying `cover_source`, `cover_role`, objective ownership and optimizer score;
- larger, more readable rock silhouettes than the first v0.6.2.1 pass.

### Tactical intent

The target arrangement is no longer “two equal rocks next to the point”.

The intended geometry is:

- cover toward the outer/flank side of the objective;
- direct entry/retreat corridor kept open;
- no cover inside the capture platform footprint;
- asymmetric defensive/attacking roles rather than mirrored camping pockets;
- enough physical mass to read clearly in the Blender viewport.

### Existing repairs retained

The inherited v0.6.1 repair pass remains active for:

- central north pillar contact with the Aether Altar;
- central SW/SE pocket-cover contacts;
- central south-screen contact;
- pocket cover vertical placement relative to pocket floor lift.

The refinement still does **not** change layout, terrain, roads, ramps, pocket topology, capture-point positions, or base positions.

## Verification state

The repository connector can verify the committed source text, but this environment does not contain the user's Blender 5.2 runtime or a mounted copy of the local generated `.blend`, so the refinement has **not** been claimed as Blender-runtime verified yet.

The previous measured run remains valid for the initial v0.6.2.1 implementation; new post-refinement values must be recorded after the user's Blender generation.

## Next runtime checks

1. Generate the map from branch `v0-6-2-1-cover-refinement` in Blender 5.2.
2. Run the existing gameplay auditor against the resulting `map_data.json`.
3. Confirm all 5 objectives still report cover without platform intrusion.
4. Confirm camping risk falls at Monolith and Altar objectives.
5. Confirm navigation remains problem-free and pockets remain reachable 4/4.
6. Confirm evaluated-mesh intersections remain zero.
7. Record the new score, warning count, cover count, and route/camping metrics here before merge to `main`.
8. Only after that, continue toward the vegetation/resource dressing stages.

## Known separate issues

The following are intentionally not mixed into this cover refinement:

- global `OuterBoundary` bbox validation around the outer edge;
- `AltarObstacles` missing data;
- resources/pickups not yet integrated as full gameplay objects;
- natural perimeter generation is present in code but is not yet called by the active pipeline.

## Completion criteria

v0.6.2.1 is complete only when the refined cover pass has been generated in Blender 5.2, the gameplay auditor has been rerun, the five objective camping risks are acceptable, and the resulting measured values are recorded here.