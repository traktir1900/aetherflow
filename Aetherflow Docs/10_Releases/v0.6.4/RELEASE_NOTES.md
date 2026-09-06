# AetherFlow v0.6.4 — Release Notes

## Release status

**NOT RELEASE-READY**

v0.6.4 documentation is established, but the current Blender 5.2 runtime still ends with `validation FAILED`. The version must remain open until genuine validation issues are closed and a fresh runtime confirms the corrected state.

## Included in v0.6.4 documentation

- global elliptical outer boundary and Crown opening contract;
- Crown Sanctum / Crown capture presentation separation;
- capture button and indicator-ring specification;
- visual-only Crown capture links;
- road center light-guide specification;
- ramp-width correction requirement;
- runtime validation status and closure gate;
- explicit resource/environment gap tracking.

## Runtime evidence carried into this release record

From the latest supplied v0.6.4 Blender run:

- map: **200 × 200 m**;
- world floor: **220 × 220 m**;
- terrain max sampled slope: **19.88° — PASS**;
- Crown Sanctum: generated and symmetric;
- capture overlays: **5 logical objectives / 10 overlay objects**;
- Crown visual correction: executed;
- road center light guides: generated;
- capture button route binding: **18 links / PASS**;
- graded ramps: **5**;
- pockets: **4/4 reachable**;
- gameplay symmetry: **PASS**;
- dedicated minion traversal: **PASS** for both test scenarios;
- final validation: **FAILED**.

## Release blockers

1. Fresh runtime validation after the latest validation compatibility changes is still missing.
2. Ramp width correction has not yet been confirmed by a new Blender run.
3. Crown structural overlap warnings remain open for review.
4. The new Resource Foundation stage has not been verified in a fresh Blender runtime.
5. No final MAP LOCK approval exists.

## Release gate

Do not label v0.6.4 as a closed/released version until a fresh Blender 5.2 run shows no genuine validation errors and the closure criteria in `Aetherflow Docs/01_Versions/v0.6.4/README.md` are satisfied.
