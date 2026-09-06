# AetherFlow v0.6.4.0 — Canonical Terminology

This document records the terminology introduced or clarified by the v0.6.4.0 runtime/presentation work.

## Capture Platform
`CapturePlatform_<Point>` is the real physical platform of the capture objective. For Crown specifically, it remains the capture objective platform even though the separate Crown Sanctum boss geometry occupies the same northern gameplay area.

## Capture Button
`CaptureButton_<Point>` is the logical interaction control for a capture objective. It is gameplay-relevant and occupies 70% of the objective platform radius.

## Capture Indicator Ring
`CaptureIndicatorRing_<Point>` is the visual capture-state indicator surrounding the central capture button. It occupies the remaining 30% of the platform radius and is visual-only.

## Crown Boss Button / Aether Button
`Crown_BossButton` is the separate boss-state pressure button on the Crown Throne / Crown Boss Rise. It is not the Crown capture platform, capture button, or capture indicator.

## Altar Reward
While a team controls the central Altar:
- +20 Gold/min to the controlling team;
- +5% Movement Speed only on Roads / Flow roads for the controlling team.

On capture:
- 10-second global enemy-hero reveal for the capturing team.

This remains separate from `Crown Blessing` and must not create an automatic stacked super-buff state.

## Road Light Guide
A thin luminous visual guide following the center of a road or route. It exists for readability and must not affect navigation, collision, or route topology.

## Capture Button Route Binding
The explicit association between an objective-touching road/ramp endpoint and its corresponding `CaptureButton_<Point>` logical anchor. All five objectives are expected to have complete binding coverage.

## Raised-Platform Correction
A post-generation presentation pass that reads the actual world-space mesh elevation of the physical capture platform and repositions the capture indicator/button so they remain attached to that platform.

## Crown Capture Link
A visual-only link from the Crown capture button to an adjacent Monolith capture button. Current links: Crown → WestMonolith and Crown → EastMonolith.

## Boundary Footprint Validation
Dedicated hard validation of outer-boundary wall geometry using its real rendered footprint. It is distinct from the ordinary gameplay-object bbox check.

## Runtime Validation Compatibility Pass
A narrowly scoped runtime layer that removes only confirmed false-positive diagnostics for known visual-only guide meshes and dedicated outer-boundary geometry. It must never hide unrelated validation errors.

## Mandatory distinctions
- Crown = fifth northern capture objective;
- Capture Platform = physical objective platform;
- Capture Button = capture interaction control on that platform;
- Capture Indicator Ring = visual capture-state indicator;
- Altar Reward = strategic economy/rotation/information reward;
- Crown Boss = separate neutral PvE boss;
- Crown Sanctum = boss location/structure;
- Aether Button = boss-state pressure button;
- Road Light Guide = visual-only route presentation element.
