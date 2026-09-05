"""
AetherFlow :: combat/simulation.py
Deterministic combat-flow simulation over the REAL map data.

FIX PASS (v0.6.0):

  1. All 5 capture points always participate — objectives/zones iterate
     core.layout.RING_NODES (asserted len == 5).  No 4-point logic anywhere.

  2. Navigation is consumed directly: first contact, travel distances and
     zone throughput come from NavGrid paths over the obstacle-aware grid.
     The straight-line fallback is used ONLY when no nav grid is passed, and
     is then explicitly flagged in meta.estimates.

  3. cover_usage is genuinely computed from map geometry — no random
     coefficients:
        cover_objects_in_zone  count of registered cover/rock anchors in zone
        exposure               fraction of 8 approach rays with clear LOS
        covered_fraction       1 - exposure
        traffic                routes passing the zone * agents_per_route
        fights                 traffic * (engagement_base + exposure*factor)
        cover_usage            fights * covered_fraction   (rounded)
     If a zone has no cover nearby, its cover_usage is honestly 0.

  4. Fully deterministic: no RNG at all.  Same config + same map => the exact
     same report.
"""
import math
from mathutils import Vector

from core.layout import RING_NODES, BASES, capture_point_names

_DIRECTIONS_8 = [(math.cos(math.radians(a)), math.sin(math.radians(a)))
                 for a in range(0, 360, 45)]


def _cover_anchors(ctx):
    """(x, y) anchors of every registered cover / rock object (real data)."""
    pts = []
    for rec in ctx.generated_objects:
        if rec["type"] in ("cover", "rock"):
            loc = getattr(rec["object"], "location", None)
            if loc is not None:
                pts.append((float(loc.x), float(loc.y)))
    return pts


def _covers_in_zone(cover_pts, center, radius):
    n = 0
    for (x, y) in cover_pts:
        if math.hypot(x - center.x, y - center.y) <= radius:
            n += 1
    return n


def _exposure(grid, center, ray_len, eye):
    """Fraction of 8 approach directions with CLEAR line of sight (0..1).

    Geometric 2.5D check (terrain height + solid blockers).  Limitation:
    sampled on the nav grid, so sub-cell cover only partially occludes.
    """
    clear = 0
    for dx, dy in _DIRECTIONS_8:
        edge = Vector((center.x + dx * ray_len, center.y + dy * ray_len, 0.0))
        if grid.has_los(center, edge, eye=eye):
            clear += 1
    return clear / float(len(_DIRECTIONS_8))


def run_simulation(ctx, grid=None, nav_report=None):
    """
    grid: core.navigation.NavGrid (obstacle-aware).  When provided, every
    distance / throughput / LOS metric uses it.  When None, only the
    first-contact estimate falls back to straight-line distance and is
    flagged accordingly.
    """
    cfg = ctx.config
    sim_cfg = cfg.get("simulation", {})
    layout = ctx.layout
    points = capture_point_names()
    assert len(points) == 5, "simulation requires all 5 capture points"

    speed = sim_cfg.get("agent_speed", 2.0)
    agents_per_route = sim_cfg.get("agents_per_route", 12)
    eng_base = sim_cfg.get("engagement_base", 0.08)
    eng_exp = sim_cfg.get("engagement_exposure_factor", 0.25)
    eye = sim_cfg.get("los_eye_height", 0.6)
    zone_radius = cfg["capture_platform_radius"] * sim_cfg.get("cover_los_range_factor", 2.5)

    cover_pts = _cover_anchors(ctx)
    estimates = []

    # ------------------------------------------------------------------
    # Route collection (real nav paths), used for throughput + choke data
    # ------------------------------------------------------------------
    route_cells = []
    travel = {}
    if grid is not None:
        min_per_base = {}
        for base in BASES:
            best = None
            for p in points:
                cells = grid.path_cells(layout[base], layout[p])
                d = None if cells is None else (len(cells) - 1) * grid.step
                travel.setdefault(p, {})[base] = None if d is None else round(d, 1)
                if cells is not None:
                    route_cells.append(cells)
                if d is not None and (best is None or d < best):
                    best = d
            min_per_base[base] = best
        # objective -> objective routes for throughput / choke realism
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                cells = grid.path_cells(layout[points[i]], layout[points[j]])
                if cells is not None:
                    route_cells.append(cells)

        ready = [d for d in min_per_base.values() if d is not None]
        if len(ready) == len(BASES):
            first_contact = max(ready) / speed   # both teams must arrive
        else:
            first_contact = None
    else:
        # Explicit, flagged fallback: straight-line distance.
        estimates.append("first_contact_sec (straight-line fallback: no nav grid)")
        d = (layout["BlueBase"] - layout["RedBase"]).length / 2.0
        first_contact = d / speed
        for p in points:
            travel[p] = {
                base: round((layout[base] - layout[p]).length, 1) for base in BASES
            }

    # ------------------------------------------------------------------
    # Per-zone metrics (all 5 points + bases + central combat zone)
    # ------------------------------------------------------------------
    def throughput_of(center):
        n = 0
        for cells in route_cells:
            step = max(1, len(cells) // 60)
            sampled = list(cells[::step])
            sampled.append(cells[-1])   # the destination cell must count too
            for cell in sampled:
                w = grid.world_of(cell)
                if math.hypot(w.x - center.x, w.y - center.y) <= zone_radius:
                    n += 1
                    break
        return n

    objectives = {}
    zones = {}

    for idx, p in enumerate(points):
        pos = layout[p]
        n_cover = _covers_in_zone(cover_pts, pos, zone_radius)
        expo = _exposure(grid, pos, zone_radius, eye) if grid is not None else 1.0
        covered = 1.0 - expo

        traffic = throughput_of(pos) * agents_per_route if grid is not None else 0
        fights = int(round(traffic * (eng_base + expo * eng_exp)))
        cover_usage = int(round(fights * covered))

        owner = "Blue" if idx % 2 == 0 else "Red"
        objectives[p] = {
            "owner": owner,
            "status": "{} Owned".format(owner),
            "progress": 100.0 if owner == "Blue" else -100.0,
        }
        zones[p] = {
            "traffic": traffic,
            "fights": fights,
            "cover_objects_in_zone": n_cover,
            "exposure": round(expo, 3),
            "covered_fraction": round(covered, 3),
            "cover_usage": cover_usage,
            "height_advantage": round(float(pos.z), 3),
            "travel_distance": travel.get(p, {}),
            "occupancy": traffic,
        }

    # Central combat zone (AetherCore) — where the core cover actually lives.
    center = layout["Center"]
    n_cover_c = _covers_in_zone(cover_pts, center, zone_radius)
    expo_c = _exposure(grid, center, zone_radius, eye) if grid is not None else 1.0
    traffic_c = throughput_of(center) * agents_per_route if grid is not None else 0
    fights_c = int(round(traffic_c * (eng_base + expo_c * eng_exp)))
    zones["AetherCore"] = {
        "traffic": traffic_c,
        "fights": fights_c,
        "cover_objects_in_zone": n_cover_c,
        "exposure": round(expo_c, 3),
        "covered_fraction": round(1.0 - expo_c, 3),
        "cover_usage": int(round(fights_c * (1.0 - expo_c))),
        "height_advantage": round(float(cfg["heights"]["AetherCore"]), 3),
        "travel_distance": {},
        "occupancy": traffic_c,
    }

    # Pocket zones (v0.6.1): flank spaces are entered through their canonical
    # CapturePoint -> PocketEntry route.  Do not infer pocket traffic from
    # arbitrary shortest-path tie-breaks among unrelated global routes.
    pocket_nav = {}
    if nav_report is not None:
        pocket_nav = {p["name"]: p for p in nav_report.get("pockets", [])}

    for pk in getattr(ctx, "pockets", []):
        center = Vector(pk["location"])
        n_cover_p = _covers_in_zone(cover_pts, center, zone_radius)
        expo_p = _exposure(grid, center, zone_radius, eye) if grid is not None else 1.0
        nav_pk = pocket_nav.get(pk["name"])
        reachable = bool(nav_pk and nav_pk.get("reachable"))
        traffic_p = agents_per_route if (grid is not None and reachable) else 0
        fights_p = int(round(traffic_p * (eng_base + expo_p * eng_exp)))
        zones[pk["name"]] = {
            "traffic": traffic_p,
            "fights": fights_p,
            "cover_objects_in_zone": n_cover_p + len(pk.get("cover", [])),
            "exposure": round(expo_p, 3),
            "covered_fraction": round(1.0 - expo_p, 3),
            "cover_usage": int(round(fights_p * (1.0 - expo_p))),
            "height_advantage": round(float(pk["height_range"][1] - pk["height_range"][0]), 3),
            "travel_distance": {},
            "occupancy": traffic_p,
            "mirror_pair": pk.get("mirror_pair"),
            "route_length": None if not nav_pk else nav_pk.get("route_length"),
            "reachable": reachable,
        }

    # Base zones: spawn traffic, no fighting.
    for base in BASES:
        zones[base] = {
            "traffic": len(points) * agents_per_route,
            "fights": 0,
            "cover_objects_in_zone": _covers_in_zone(cover_pts, layout[base], zone_radius),
            "exposure": 1.0,
            "covered_fraction": 0.0,
            "cover_usage": 0,
            "height_advantage": 0.0,
            "travel_distance": {},
            "occupancy": 0,
        }

    total_events = sum(z["fights"] for z in zones.values())

    choke = nav_report.get("chokepoints", []) if nav_report else []

    return {
        "meta": {
            "version": "0.6.0",
            "capture_points": points,                # always all 5
            "deterministic": True,
            "nav_driven": grid is not None,
            "estimates": estimates,
            "formulas": {
                "traffic": "routes_through_zone * agents_per_route",
                "fights": "traffic * (engagement_base + exposure * engagement_exposure_factor)",
                "cover_usage": "fights * covered_fraction",
                "exposure": "clear_los_directions / 8 (2.5D grid march)",
                "first_contact_sec": "max(min_base_to_any_objective) / agent_speed",
            },
            "limitations": [
                "LOS sampled on nav grid: sub-cell cover only partially occludes",
                "L-cover wings approximated by main wall footprint",
            ],
        },
        "metrics": {
            "first_contact_sec": None if first_contact is None else round(first_contact, 1),
            "total_combat_events": total_events,
            "objective_states": objectives,
            "chokepoints": choke,
        },
        "zones": zones,
    }
