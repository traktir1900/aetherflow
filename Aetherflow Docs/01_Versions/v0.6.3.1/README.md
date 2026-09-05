# AetherFlow v0.6.3.1 — Terrain Refinement

## Goal

Refine the existing v0.6.x terrain profile without changing map topology.
The five objectives, two bases, roads, ramps, pockets and their XY layout remain fixed.

## Implemented

### Central AetherCore
The existing analytic depression remains centered at `(0,0)`, but its depth is increased by a bounded multiplier so the central combat space reads clearly in Blender and later in UE5.

### Crown
The Crown sector receives a stronger but still smooth elevation target. The Crown location itself is unchanged.

### West/East Monoliths
Both monolith sectors receive identical elevation strengthening. The symmetry between the two side sectors is preserved.

### South Rift
The South Rift receives a controlled deeper depression while keeping its existing footprint and location.

### Height transitions
The central transition radius is increased slightly to keep the stronger height differences gradual. No hard terrain walls or new topology are introduced.

## Design limits

- gameplay map remains `200 x 200 m`;
- world floor remains `220 x 220 m`;
- objective/base coordinates are unchanged;
- topology is unchanged;
- terrain is generated from the same analytic heightmap system;
- maximum sampled terrain slope target is `< 35°`;
- safety-floor clamping remains active.

## Runtime audit

The pipeline now prints:

- effective landmark heights for AetherCore, Crown, WestMonolith, EastMonolith and SouthRift;
- minimum/maximum terrain height;
- maximum sampled slope;
- average sampled slope;
- pass/fail against the 35° design limit;
- explicit confirmation that topology/objective/base coordinates are unchanged.

## Validation gate

Fresh Blender 5.2 generation is required before calling v0.6.3.1 complete. The terrain refinement itself is not considered complete until navigation, geometry validation and the existing v0.6.2.1 gameplay checks remain acceptable after the stronger height profile is applied.

The work remains on `v0-6-2-1-cover-refinement`; no new branch is created.
