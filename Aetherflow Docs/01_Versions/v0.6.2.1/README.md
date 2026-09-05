# AetherFlow v0.6.2.1 — Gameplay Cover 2.0

## Status

**IN PROGRESS — implementation pass**

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

Source audit: `Вставленный текст(20260905-161516).txt`, generated from the v0.6.1 Blender scene/export.

## Implemented

### Gameplay Cover 2.0 foundation

Added `core/gameplay_cover.py`.

The module:

- reuses the existing cover architecture rather than introducing a second optimizer;
- creates deterministic objective cover for all 5 objectives;
- creates 2 controlled cover objects per objective (10 total);
- registers explicit gameplay metadata for future navigation / LOS / UE5 export;
- includes a targeted repair pass for inherited cover contacts found by the v0.6.1 audit.

### Inherited geometry repairs

The repair pass currently addresses:

- central north pillar contact with the Aether Altar;
- central SW/SE pocket-cover contacts;
- central south-screen contact;
- pocket cover vertical placement relative to the pocket floor lift.

The repair pass intentionally does not modify layout, terrain, roads, ramps, pocket topology, or capture-point positions.

### Pipeline integration

The gameplay cover pass is integrated into the active generation pipeline after the fixed structural map is generated and before navigation/validation.

## Versioning

`VERSION.txt` is now `0.6.2.1` on this implementation branch.

## Verification state

The code has been committed to branch `v0-6-2-1` and opened as Draft PR #1 against `main`.

Blender 5.2 runtime verification still remains a required next step. The implementation must be validated against the real generated scene before this sub-version is considered complete.

## Next checks

1. Generate the map in Blender 5.2.
2. Run the gameplay auditor against the new `map_data.json`.
3. Verify navigation coverage and route stability.
4. Verify objective-cover counts and LOS impact.
5. Verify actual mesh intersections are reduced, not merely hidden by metadata.
6. Fix any regressions before moving to expanded rocks/environment.

## Completion criteria

v0.6.2.1 is complete only when the regenerated scene passes the geometry/navigation/cover validation targets and the measured results are recorded here.