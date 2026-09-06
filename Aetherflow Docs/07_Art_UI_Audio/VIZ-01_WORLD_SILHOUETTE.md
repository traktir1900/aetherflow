# VIZ-01 — World Silhouette / Gameplay Fairness

## Status

**IMPLEMENTED — STATIC CHECK ONLY.**

The VIZ-01 Blender pass has been integrated into the existing generation entry point. A runtime Blender 5.2 generation/viewport validation has **not** been executed in this session.

## Non-negotiable gameplay rule

AetherFlow is mirror-symmetric for both teams. Any gameplay-relevant geometry must be equivalent under:

`(x, y, z) -> (-x, y, z)`

This applies to terrain/elevation, cliffs, roads, ramps, cover, sightline structure, choke points, objective approaches, minion corridors, bases, resource access and other tactical space.

Visual decoration may vary only when the variation cannot create a gameplay advantage. For VIZ-01 macro formations, the generator does not use independent random placement: it authors a formation once and creates an exact mirrored counterpart.

## Implemented visual layer

The VIZ-01 pass adds deterministic, macro-scale, non-blocking visual forms for:

- outer cliff framing;
- north/south ridges;
- Crown framing;
- Base framing;
- AetherCore side framing;
- large-scale visual shoulders around the battlefield perimeter.

The geometry is generated into the `Decorations` collection with metadata explicitly marking it as visual-only and non-blocking for navigation and LOS.

## Gameplay safety

The pass does not own or redefine the authoritative layout. Existing bases, five capture points, roads, ramps, pockets, navigation and objective systems remain authoritative.

Every generated visual pair is checked at generation time by an exact transform audit. The current audit tolerance is `1e-5 m` for the generated L/R object locations.

## Runtime requirement before closure

Run the current Blender pipeline in Blender 5.2 and verify:

1. VIZ-01 objects generate without exceptions.
2. The mirrored audit prints `PASS`.
3. Existing Stage 9 validation remains free of new geometry-related failures.
4. Navigation and height-transition reports remain unchanged or improve.
5. Top, 45-degree and player-height views show a stronger world silhouette without creating gameplay obstructions.
6. The final scene remains symmetric for both teams.

## Design priority

`GAMEPLAY FAIRNESS -> TEAM SYMMETRY -> NAVIGATION -> READABILITY -> SILHOUETTE -> BEAUTY -> DETAIL`

VIZ-01 is a macro-world pass. Fine foliage, decals, final materials, lighting, VFX and dense environment dressing remain UE5 work.
