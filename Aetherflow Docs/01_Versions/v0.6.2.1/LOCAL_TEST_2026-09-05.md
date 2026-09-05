# v0.6.2.1 — Local test note (2026-09-05)

The Blender run supplied during development was successful as a process, but it executed the local v0.6.1 codebase.

Evidence from the run:
- pipeline banner: `AETHER FLOW GENERATION PIPELINE :: v0.6.1`;
- export: `map_data.json` version `0.6.1`;
- Blender input file: `Aetherflow v 0.6.1.blend`;
- auditor still reports `Cover = 0` for all five capture points;
- no `ObjectiveCover_*` objects appear in the audited scene.

Therefore the run is **not a valid visual verification of v0.6.2.1**.

Next action: switch the local checkout to branch `v0-6-2-1` (or update local `main` with the v0.6.2.1 commits), then rerun Blender and auditor.
