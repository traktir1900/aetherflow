# v0.6.4.1 — Resource Placement

## Gameplay decision

The resource foundation uses exactly **6 resource locations**:

- **3 Speed Shrines**
- **3 Health Relics**

The goal is to create meaningful rotation incentives without cluttering the battlefield with redundant pickups.

## Speed Shrines

1. **SpeedShrine_West** — Center ↔ WestMonolith flank route.
2. **SpeedShrine_East** — Center ↔ EastMonolith flank route.
3. **SpeedShrine_North** — Center ↔ Crown approach.

The west/east pair is an exact mirror. The north shrine sits on the symmetry axis and supports Crown rotations.

## Health Relics

1. **HealthRelic_SW** — Center ↔ SWMonolith approach.
2. **HealthRelic_SE** — Center ↔ SEMonolith approach.
3. **HealthRelic_South** — Center ↔ base/south return approach.

The southwest/southeast pair is an exact mirror. The south relic sits on the symmetry axis and supports recovery after central fights and return rotations.

## Safety contract

- Total resource objects generated: **6**.
- No resource object blocks navigation.
- No resource object blocks LOS.
- Existing objective, road, ramp, pocket, terrain and gameplay-cover geometry remains authoritative.
- Team-critical flank placements use `(x,y,z) -> (-x,y,z)`.
- Centerline resources must remain on `x = 0` within generation tolerance.
- Resource radius remains controlled by `resource_foundation.speed_shrine_radius` and `resource_foundation.health_relic_radius`.

## Validation state

**STATIC CHECK:** placement logic and symmetry rules are encoded in `core/resource_foundation.py`.

**RUNTIME:** Blender 5.2 must be run to confirm the six objects appear at the intended gameplay locations and that the existing Stage 9 validation remains clean.
