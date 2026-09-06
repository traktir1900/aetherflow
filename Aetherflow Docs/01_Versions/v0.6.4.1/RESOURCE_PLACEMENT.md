# v0.6.4.1 — Resource Placement

## Gameplay decision

The resource foundation now uses exactly **11 resource locations**:

- **3 Speed Shrines**
- **8 Health Relics**

The goal is to create meaningful rotation incentives while also giving every capture point a nearby recovery option. The capture-point relics sit just inside the objective approach, not on the capture platform itself.

## Speed Shrines

1. **SpeedShrine_West** — Center ↔ WestMonolith flank route.
2. **SpeedShrine_East** — Center ↔ EastMonolith flank route.
3. **SpeedShrine_North** — Center ↔ Crown approach.

The west/east pair is an exact mirror. The north shrine sits on the symmetry axis and supports Crown rotations.

## Health Relics — rotation/return layer

1. **HealthRelic_SW** — Center ↔ SWMonolith approach.
2. **HealthRelic_SE** — Center ↔ SEMonolith approach.
3. **HealthRelic_South** — Center ↔ base/south return approach.

The southwest/southeast pair is an exact mirror. The south relic sits on the symmetry axis and supports recovery after central fights and return rotations.

## Health Relics — capture-point layer

One additional Health Relic is placed at each of the five capture points:

1. **HealthRelic_Capture_Crown** — inward side of Crown.
2. **HealthRelic_Capture_EastMonolith** — inward side of EastMonolith.
3. **HealthRelic_Capture_SEMonolith** — inward side of SEMonolith.
4. **HealthRelic_Capture_SWMonolith** — inward side of SWMonolith.
5. **HealthRelic_Capture_WestMonolith** — inward side of WestMonolith.

Each capture relic is derived from the authoritative objective position and offset toward the center/rotation path by `capture_platform_radius + capture_health_offset_m`. West/East and SW/SE remain exact mirror pairs; Crown lies on the symmetry axis.

## Safety contract

- Total resource objects generated: **11**.
- No resource object blocks navigation.
- No resource object blocks LOS.
- Existing objective, road, ramp, pocket, terrain and gameplay-cover geometry remains authoritative.
- Team-critical flank placements use `(x,y,z) -> (-x,y,z)`.
- Centerline resources must remain on `x = 0` within generation tolerance.
- Resource radius remains controlled by `resource_foundation.speed_shrine_radius` and `resource_foundation.health_relic_radius`.
- Capture-point Health Relics are placed outside the objective platform rather than on the capture surface.

## Validation state

**STATIC CHECK:** placement logic and symmetry rules are encoded in `core/resource_foundation.py`.

**RUNTIME:** Blender 5.2 must be run to confirm all eleven objects appear at the intended gameplay locations and that the existing Stage 9 validation remains clean.
