# AetherFlow v0.6.4 — Crown Capture Presentation

## Purpose

This document records the v0.6.4 Crown capture presentation contract. The goal is to keep the fifth capture objective visually readable even though Crown is also the location of the separate Crown Sanctum / Crown Boss structure.

## Separation of gameplay roles

Crown contains two distinct gameplay identities:

- **Crown capture objective** — the fifth capture point and its normal capture control;
- **Crown Boss / Crown Sanctum** — the separate PvE boss landmark layered onto the same northern area.

The boss button must never replace the capture control.

## Capture control

The generated capture overlay uses:

- `CaptureButton_Crown` — logical capture interaction anchor;
- `CaptureIndicatorRing_Crown` — visual capture indicator;
- central button radius = **70%** of the capture platform radius;
- outer 30% of the platform radius = indicator ring zone.

The capture button stores Crown as its logical road anchor and links to its two neighboring objective buttons:

- `CaptureButton_WestMonolith`;
- `CaptureButton_EastMonolith`.

## Raised-platform correction

Because the Crown area is vertically layered, the normal objective overlay can be visually buried by the Crown Boss geometry.

The v0.6.4 runtime pass therefore:

1. reads actual world-space mesh Z bounds of the Crown platform, Crown Boss Button and Crown Boss Rise;
2. selects the highest generated support surface;
3. places the capture indicator above that support surface;
4. places the capture button above the indicator;
5. records the correction in the runtime context.

This is a presentation correction only. It does not move the authoritative Crown XY anchor.

## Visual-only links

Two thin visual links are created from Crown's capture button to the adjacent capture buttons:

- Crown → WestMonolith;
- Crown → EastMonolith.

These are presentation guides and must not become navigation blockers or collision geometry.

## Validation contract

The visual system is considered correct only when:

- `CaptureButton_Crown` exists;
- `CaptureIndicatorRing_Crown` exists;
- both remain distinct from `Crown_BossButton`;
- the button and indicator sit above the actual Crown support surface;
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
