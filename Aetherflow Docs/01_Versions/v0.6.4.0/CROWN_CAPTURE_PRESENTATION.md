# AetherFlow v0.6.4 — Crown Capture Presentation

## Purpose

This document records the v0.6.4 Crown capture presentation contract. The goal is to keep the fifth capture objective visually readable even though Crown is also the location of the separate Crown Sanctum / Crown Boss structure.

## Separation of gameplay roles

Crown contains two distinct gameplay identities:

- **Crown capture objective** — the fifth capture point with its own physical capture platform and normal capture control;
- **Crown Boss / Crown Sanctum** — the separate PvE boss landmark layered onto the same northern area.

The boss button must never replace the capture platform or capture control.

## Capture objective stack

The Crown capture objective is explicitly composed of three separate entities:

```text
CapturePlatform_Crown
├── CaptureIndicatorRing_Crown
└── CaptureButton_Crown
```

Roles:

- `CapturePlatform_Crown` — **real physical capture-objective platform**;
- `CaptureIndicatorRing_Crown` — visual capture-state indicator occupying the outer 30% of the platform radius;
- `CaptureButton_Crown` — central logical capture-control surface occupying 70% of the platform radius.

The boss stack is separate:

```text
Crown_BossRise / Crown_Throne
└── Crown_BossButton (Aether Button)
```

`Crown_BossButton` is therefore not the Crown capture platform, not the capture indicator and not the capture-control node.

## Capture control

The generated capture overlay uses:

- `CaptureButton_Crown` — logical capture interaction anchor;
- `CaptureIndicatorRing_Crown` — visual capture indicator;
- `CapturePlatform_Crown` — physical objective surface;
- central capture-control radius = **70%** of the capture platform radius;
- outer 30% of the platform radius = indicator ring zone.

The capture button stores Crown as its logical road anchor and links to its two neighboring objective buttons:

- `CaptureButton_WestMonolith`;
- `CaptureButton_EastMonolith`.

## Raised-platform correction

Because the Crown area is vertically layered, the capture overlay must remain attached to the **capture platform itself**, rather than floating over the higher boss geometry.

The v0.6.4 runtime pass therefore:

1. reads the actual world-space Z bounds of `CapturePlatform_Crown`;
2. uses the **top of the physical capture platform** as the capture-system support surface;
3. places the capture indicator just above that platform;
4. places the capture button just above the indicator;
5. leaves `Crown_BossRise` / `Crown_BossButton` independent on their own boss surface;
6. records the separation explicitly in runtime metadata.

This is a presentation correction only. It does not move the authoritative Crown XY anchor.

## Visual-only links

Two thin visual links are created from Crown's capture button to the adjacent capture buttons:

- Crown → WestMonolith;
- Crown → EastMonolith.

These are presentation guides and must not become navigation blockers or collision geometry.

## Validation contract

The visual system is considered correct only when:

- `CapturePlatform_Crown` exists and is the real physical capture platform;
- `CaptureButton_Crown` exists on that platform;
- `CaptureIndicatorRing_Crown` exists on that platform;
- `Crown_BossButton` remains a separate boss interaction;
- the capture controls do not use the boss button/rise as their support surface;
- the two visual links are present and marked visual-only;
- gameplay symmetry remains PASS;
- navigation and collision remain unaffected.

## Latest runtime evidence

The supplied v0.6.4 runtime reports:

- Crown capture node present;
- raised-platform correction executed;
- `raised_platform=True`;
- `visible=True`;
- 2 visual-only Crown capture links generated.

The overall validation gate still failed elsewhere, so this presentation pass is **implemented and runtime-observed, but not a standalone release gate closure**.
