# AetherFlow v0.6.2.1 — Gameplay Cover 2.0

## Status

**IN PROGRESS — refinement implementation complete; Blender runtime verification pending**

This version extends the existing v0.6.1 map without changing the fixed layout/topology.

## Measured v0.6.2.1 runtime baseline

The first real Blender 5.2 generation after the initial v0.6.2.1 implementation produced:

- objective cover: 10 objects across all 5 objectives;
- CoreCover total: 26;
- actual evaluated-mesh intersections: 0;
- navigation problems: 0;
- pockets reachable: 4/4;
- Blue/Red base fairness: 0% route-time difference;
- overall auditor score: 88.2/100;
- warnings: 8;
- HIGH camping risk at the four monolith objectives and central Altar;
- OuterBoundary bbox validation errors in the submitted local run.

The runtime log confirms the cover pass executed successfully and produced valid objective-cover entries. filecite is intentionally not embedded here because repository docs must remain standalone.

## Refinement implemented on branch

Branch: `v0-6-2-1-cover-refinement`

### Objective-cover architecture

`core/gameplay_cover.py` uses the shared `core.cover_analysis.optimize_cover(...)` model rather than fixed identical positions.

The refinement now adds:

- optimizer-driven candidate selection;
- LOS, flank, movement and chokepoint weighting;
- capture-platform hard exclusion;
- an explicit radial stand-off zone around the objective;
- a clear direct approach/retreat lane;
- at most 2 objective cover pieces;
- minimum separation between the two cover pieces;
- larger silhouettes for stronger viewport readability;
- explicit gameplay metadata for role, objective and optimizer source.

### Current tactical constraints

Objective cover is deliberately kept outside the immediate capture fight:

- minimum stand-off target: **13 m** from objective centre;
- maximum stand-off target: **18 m**;
- minimum cover-to-cover separation: **10 m**;
- centreline cover is rejected;
- fallback pieces are also subject to the same stand-off and separation rules.

The intended pattern is no longer “two rocks beside the point”. It is a pair of flank shelters positioned outside the capture ring, preserving a readable contest corridor.

### Existing repairs retained

The inherited repair pass remains active for known v0.6.1 cover contacts and pocket-cover vertical placement.

No capture-point, base, terrain, road, ramp or pocket topology changes were introduced by this refinement.

## Validation note

The uploaded Blender run showed `OuterBoundary_*` bbox errors, but the repository version of `core/validation.py` contains a dedicated outer-boundary path that treats the perimeter as a world-edge system instead of a normal gameplay object. The next local regeneration must therefore be done from the current branch ZIP so the runtime source and repository source are synchronized.

## Verification state

The refinement is **not yet runtime-verified**. The user's Blender run before this latest change showed:

- objective cover 10/10;
- 0 navigation problems;
- 0 evaluated-mesh intersections;
- 4/4 reachable pockets;
- but HIGH camping risk around the monoliths and Altar.

These values remain the baseline until a new Blender 5.2 run is completed from the latest branch.

## Next runtime checks

1. Download the latest `v0-6-2-1-cover-refinement` branch ZIP.
2. Regenerate the map in Blender 5.2.
3. Run `tools/aetherflow_gameplay_auditor.py` against the resulting export.
4. Verify objective cover is 13–18 m from objective centres and separated by at least 10 m.
5. Verify the five objective camping risks improve without creating new choke points.
6. Verify navigation remains problem-free and pockets remain reachable 4/4.
7. Verify evaluated-mesh intersections remain zero.
8. Record the new measured score/warnings/routes in this document before merge.

## Known separate issues

- `AltarObstacles` is still a separate missing category in the current generator.
- Resources and vegetation are not yet integrated into the active pipeline.
- Natural perimeter generation exists in code but is not yet called by the main pipeline.
- Full Dominion macro-rotation simulation is not yet implemented.

## Completion criteria

v0.6.2.1 is complete only when the refined cover pass has been regenerated in Blender 5.2, the objective camping-risk result is acceptable, validation/navigation remain clean, and the measured results are recorded here.