# v0.6.4.0 — VIZ-01 Implementation

## Scope

VIZ-01 adds the first macro visual layer to the existing Blender map. It does not replace or redefine the authoritative gameplay layout.

## Implemented

- deterministic macro cliff/ridge framing;
- Crown and base visual framing;
- AetherCore side framing;
- mirrored L/R generation using `(x,y,z) -> (-x,y,z)`;
- explicit `visual_only`, `navigation_blocker=False`, and `los_blocker=False` metadata;
- generation-time L/R symmetry audit with `1e-5 m` location tolerance;
- integration into the existing `main.py` Blender entry flow after outer-boundary generation.

## Gameplay safety contract

The pass must not change:

- objective anchors;
- base anchors;
- road topology;
- ramps;
- pockets;
- minion corridors;
- navigation blockers;
- gameplay cover;
- authoritative terrain layout.

Team-critical geometry remains mirrored for Blue and Red. Visual macro forms are authored as exact mirrored pairs rather than independently randomized on each side.

## Validation state

**STATIC CHECK:** repository integration and dependency mapping were reviewed.

**RUNTIME:** Blender 5.2 generation and viewport validation have not yet been executed in this session. VIZ-01 must therefore not be considered visually validated or release-closed yet.
