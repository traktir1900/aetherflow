# AetherFlow v0.6.4.0 — Crown Capture Presentation

## Purpose

This document records the v0.6.4.0 Crown capture presentation contract. Crown is both the fifth capture objective and the location of the separate Crown Sanctum / Crown Boss structure, so the two gameplay identities must remain explicit and separate.

## Capture objective stack

```text
CapturePlatform_Crown
├── CaptureIndicatorRing_Crown
└── CaptureButton_Crown
```

- `CapturePlatform_Crown` — real physical capture-objective platform;
- `CaptureIndicatorRing_Crown` — visual capture-state indicator;
- `CaptureButton_Crown` — logical capture-control surface.

The boss stack is separate:

```text
Crown_BossRise / Crown_Throne
└── Crown_BossButton (Aether Button)
```

`Crown_BossButton` is not the Crown capture platform, indicator, or capture-control node.

## Capture control

The central capture-control radius is 70% of the platform radius. The outer 30% is reserved for the capture indicator ring.

## Raised-platform correction

The capture overlay reads the actual world-space Z bounds of `CapturePlatform_Crown` and places the indicator/button on that physical platform. It must not use `Crown_BossRise` or `Crown_BossButton` as the support surface.

This correction does not move the authoritative Crown XY anchor.

## Visual-only links

Current links:
- Crown → WestMonolith;
- Crown → EastMonolith.

These are presentation guides only and must not affect navigation or collision.

## Validation contract

The system is correct only when the physical capture platform, capture control, indicator, and boss interaction remain separate and navigation/collision are unaffected.

## Runtime status

The supplied runtime observed the Crown capture node, raised-platform correction, and two visual-only links, but the overall validation gate remained failed elsewhere. Therefore this pass is implemented and runtime-observed, not release-closed.
