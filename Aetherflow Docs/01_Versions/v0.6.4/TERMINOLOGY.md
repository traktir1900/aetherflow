# AetherFlow v0.6.4 — New Canonical Terms

This file records the terminology introduced or clarified by the v0.6.4 runtime/presentation work. The main glossary remains authoritative; these definitions explain the v0.6.4 additions.

## Capture Button
`CaptureButton_<Point>` is the logical interaction anchor for a capture objective. It is gameplay-relevant and is not merely decorative.

The capture button occupies **70% of the objective platform radius**.

## Capture Indicator Ring
`CaptureIndicatorRing_<Point>` is the visual capture-state indicator surrounding the central capture button. It occupies the remaining **30% of the objective platform radius** and is visual-only.

## Road Light Guide
A thin luminous visual guide following the center of a road or route. It exists for readability/presentation and must not affect navigation, collision, or route topology.

## Capture Button Route Binding
The explicit association between an objective-touching road/ramp endpoint and the corresponding `CaptureButton_<Point>` logical anchor. All five objectives are expected to have complete binding coverage.

## Raised-Platform Correction
A post-generation presentation pass that reads the actual world-space mesh elevation of a raised objective structure and repositions its capture indicator/button so the interaction control remains visibly above the supporting geometry.

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
- **Crown Boss** = separate neutral PvE boss;
- **Crown Sanctum** = boss location/structure;
- **Aether Button** = boss-state pressure button;
- **Capture Button** = separate Crown capture interaction control;
- **Capture Indicator Ring** = separate visual capture-state indicator;
- **Road Light Guide** = visual-only route presentation element.
