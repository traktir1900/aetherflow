# AetherFlow v0.6.4 — New Canonical Terms

This file records the terminology introduced or clarified by the v0.6.4 runtime/presentation work. The main glossary remains authoritative; these definitions explain the v0.6.4 additions.

## Capture Platform
`CapturePlatform_<Point>` is the **real physical platform of the capture objective**. It is the gameplay surface on which the capture indicator and capture control are presented.

For Crown specifically, `CapturePlatform_Crown` remains the capture objective platform even though the separate Crown Sanctum boss geometry occupies the same northern gameplay area.

## Capture Button
`CaptureButton_<Point>` is the logical interaction control for a capture objective. It is gameplay-relevant and is not merely decorative.

The capture button occupies **70% of the objective platform radius** and is seated on its capture platform.

## Capture Indicator Ring
`CaptureIndicatorRing_<Point>` is the visual capture-state indicator surrounding the central capture button. It occupies the remaining **30% of the objective platform radius** and is visual-only.

## Crown Boss Button / Aether Button
`Crown_BossButton` is the separate boss-state pressure button on the Crown Throne / Crown Boss Rise. It belongs to the Crown Boss system and is **not** the Crown capture platform, capture button or capture indicator.

## Crown Capture Stack
The canonical Crown capture presentation stack is:

```text
CapturePlatform_Crown
├── CaptureIndicatorRing_Crown
└── CaptureButton_Crown
```

The boss stack is separate:

```text
Crown_BossRise / Crown_Throne
└── Crown_BossButton (Aether Button)
```

## Road Light Guide
A thin luminous visual guide following the center of a road or route. It exists for readability/presentation and must not affect navigation, collision, or route topology.

## Capture Button Route Binding
The explicit association between an objective-touching road/ramp endpoint and the corresponding `CaptureButton_<Point>` logical anchor. All five objectives are expected to have complete binding coverage.

## Raised-Platform Correction
A post-generation presentation pass that reads the actual world-space mesh elevation of the **physical capture platform** and repositions the capture indicator/button so they remain visibly attached to that platform.

The correction must not use `Crown_BossRise` or `Crown_BossButton` as the capture-system support surface.

## Crown Capture Link
A visual-only link from the Crown capture button to an adjacent Monolith capture button. Current v0.6.4 links:

- Crown → WestMonolith;
- Crown → EastMonolith.

These links do not create additional gameplay routes.

## Boundary Footprint Validation
The dedicated hard validation of outer-boundary wall geometry using its real rendered footprint. It is distinct from the ordinary gameplay-object bbox check because the external wall intentionally occupies the map-edge envelope.

## Runtime Validation Compatibility Pass
A narrowly scoped runtime layer that removes only confirmed false-positive diagnostics for known visual-only guide meshes and dedicated outer-boundary geometry. It must never hide unrelated validation errors.

## v0.6.4 Terminology Rule
The following distinctions are mandatory:

- **Crown** = fifth northern capture objective;
- **Capture Platform** = physical objective platform;
- **Capture Button** = separate capture interaction control on that platform;
- **Capture Indicator Ring** = separate visual capture-state indicator on that platform;
- **Crown Boss** = separate neutral PvE boss;
- **Crown Sanctum** = boss location/structure;
- **Aether Button** = boss-state pressure button on the Crown boss structure;
- **Road Light Guide** = visual-only route presentation element.
