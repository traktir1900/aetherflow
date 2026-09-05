"""
AetherFlow :: core/height_transitions.py
v0.6.3.2 route-based terrain / transition audit.

The audit is deliberately stricter than a single max-slope check. It samples
actual navigation paths, measures local grade and height deltas, inspects all
registered ramps, and reports gameplay-oriented categories.

This module also contains the dedicated minion traversal regression required
by v0.6.3.2. The scenario is:

    Base -> Objective -> Objective -> enemy Base

It follows actual NavGrid paths and rejects a route if any sampled transition
is too steep, has a forbidden adjacent height step, crosses a ramp-base
transition without continuity, collides with a solid gameplay blocker, or
runs outside the terrain envelope.

No geometry is mutated here: repairs must be evidence-driven and happen only
after the audit identifies a real problem.
"""
import math

from mathutils import Vector

from core.layout import BASES, RING_NODES


DEFAULT_RULES = {
    "combat_max_deg": 15.0,
    "minion_safe_max_deg": 18.0,
    "walkable_max_deg": 25.0,
    "ramp_max_deg": 30.0,
    "hard_max_deg": 35.0,
    "max_step_m": 0.75,
    "min_group_width_m": 4.0,
    "minion_corridor_width_m": 2.5,
    "ramp_base_tolerance_m": 0.20,
    "terrain_edge_margin_m": 0.25,
    "minion_radius_m": 0.65,
}


def _rules(cfg):
    out = dict(DEFAULT_RULES)
    out.update(cfg.get("height_transitions", {}))
    return out


def _ground_z(ctx, p):
    from core.heightmap import get_height_at_point
    return float(get_height_at_point(Vector((p.x, p.y, 0.0)), ctx.config, ctx.layout))


def _path_points(ctx, grid, cells):
    pts = []
    for cell in cells:
        p = grid.world_of(cell)
        pts.append(Vector((p.x, p.y, _ground_z(ctx, p))))
    return pts


def _terrain_inside(ctx, p, margin=None):
    half = float(ctx.config["ground_half_size"])
    margin = _rules(ctx.config)["terrain_edge_margin_m"] if margin is None else float(margin)
    return (-half + margin <= p.x <= half - margin and
            -half + margin <= p.y <= half - margin)


def _ramp_base_proximity(ctx, p, tolerance):
    """Return nearest generated ramp endpoint inside tolerance, if any."""
    best = None
    best_d = None
    for rec in ctx.generated_objects:
        if rec.get("type") != "ramp":
            continue
        meta = rec.get("meta") or {}
        for endpoint_key in ("p0", "p1"):
            endpoint = meta.get(endpoint_key)
            if endpoint is None:
                continue
            ep = Vector((float(endpoint[0]), float(endpoint[1]), float(endpoint[2])))
            d = math.hypot(p.x - ep.x, p.y - ep.y)
            if d <= tolerance and (best_d is None or d < best_d):
                best_d = d
                best = {"ramp": rec.get("name"), "endpoint": endpoint_key, "distance_m": round(d, 3)}
    return best


def _local_width_clearance(ctx, grid, p, direction, probe_length=1.5):
    """Estimate lateral free width by probing both sides of the minion centerline."""
    if direction.length <= 1e-6:
        return None
    d = Vector((direction.x, direction.y, 0.0)).normalized()
    n = Vector((-d.y, d.x, 0.0))
    center = Vector((p.x, p.y, 0.0))
    max_free = 0.0
    for offset in (1.5, 2.0, 2.5, 3.0):
        left = center + n * offset
        right = center - n * offset
        left_blocked = not _terrain_inside(ctx, left) or grid.cell_of(left) in grid.blocked
        right_blocked = not _terrain_inside(ctx, right) or grid.cell_of(right) in grid.blocked
        if left_blocked or right_blocked:
            break
        max_free = 2.0 * offset
    return max_free


def analyze_path(ctx, grid, p0, p1, label, cells=None, kind="route"):
    """Measure grade along an actual navigation path when available."""
    if cells is None:
        cells = grid.path_cells(p0, p1)
    if not cells:
        return {
            "label": label, "kind": kind, "reachable": False,
            "classification": "Too steep", "reason": "unreachable",
            "problems": ["unreachable"],
            "hero_walkable": False,
            "minion_safe": False,
            "group_traversable": False,
        }

    pts = _path_points(ctx, grid, cells)
    max_angle = 0.0
    sum_angle = 0.0
    max_dz = 0.0
    high_segments = 0
    transition_len = 0.0
    segments = []
    rules = _rules(ctx.config)

    for idx, (a, b) in enumerate(zip(pts, pts[1:])):
        run = math.hypot(b.x - a.x, b.y - a.y)
        if run <= 1e-6:
            continue
        dz = abs(b.z - a.z)
        angle = math.degrees(math.atan2(dz, run))
        max_angle = max(max_angle, angle)
        sum_angle += angle
        max_dz = max(max_dz, dz)
        if angle > rules["minion_safe_max_deg"]:
            high_segments += 1
        if angle > rules["combat_max_deg"]:
            transition_len += run
        direction = Vector((b.x - a.x, b.y - a.y, 0.0))
        width = _local_width_clearance(ctx, grid, a, direction)
        segments.append({
            "index": idx,
            "angle_deg": round(angle, 2),
            "dz_m": round(dz, 3),
            "run_m": round(run, 3),
            "terrain_inside": _terrain_inside(ctx, a) and _terrain_inside(ctx, b),
            "solid_blocked": grid.cell_of(a) in grid.blocked or grid.cell_of(b) in grid.blocked,
            "lateral_clear_width_m": None if width is None else round(width, 3),
        })

    route_length = sum(s["run_m"] for s in segments)
    avg_angle = sum_angle / max(1, len(segments))

    if max_angle > rules["hard_max_deg"]:
        classification = "Too steep"
    elif kind == "ramp" and max_angle <= rules["ramp_max_deg"]:
        classification = "Ramp"
    elif max_angle <= rules["combat_max_deg"] and max_dz <= rules["max_step_m"]:
        classification = "Combat slope"
    elif max_angle <= rules["minion_safe_max_deg"] and max_dz <= rules["max_step_m"]:
        classification = "Minion-safe"
    elif max_angle <= rules["walkable_max_deg"]:
        classification = "Walkable"
    else:
        classification = "Ramp"

    problems = []
    if max_angle > rules["hard_max_deg"]:
        problems.append("slope_over_35deg")
    elif max_angle > rules["walkable_max_deg"] and kind != "ramp":
        problems.append("ramp_or_smoothing_required")
    if max_dz > rules["max_step_m"]:
        problems.append("height_step_over_limit")
    if any(not s["terrain_inside"] for s in segments):
        problems.append("terrain_edge_exit")
    if any(s["solid_blocked"] for s in segments):
        problems.append("solid_blocker_on_path")
    if any((s["lateral_clear_width_m"] is not None and s["lateral_clear_width_m"] < rules["minion_corridor_width_m"]) for s in segments):
        problems.append("corridor_below_minion_width")

    minion_safe = (
        max_angle <= rules["minion_safe_max_deg"] and
        max_dz <= rules["max_step_m"] and
        not any(not s["terrain_inside"] or s["solid_blocked"] for s in segments) and
        not any((s["lateral_clear_width_m"] is not None and s["lateral_clear_width_m"] < rules["minion_corridor_width_m"]) for s in segments)
    )

    return {
        "label": label,
        "kind": kind,
        "reachable": True,
        "classification": classification,
        "route_length_m": round(route_length, 2),
        "height_delta_m": round(abs(pts[-1].z - pts[0].z), 3),
        "max_local_slope_deg": round(max_angle, 2),
        "average_local_slope_deg": round(avg_angle, 2),
        "max_adjacent_height_delta_m": round(max_dz, 3),
        "segments_over_combat_deg": high_segments,
        "combat_transition_length_m": round(transition_len, 2),
        "problems": sorted(set(problems)),
        "hero_walkable": max_angle <= rules["walkable_max_deg"] and max_dz <= rules["max_step_m"],
        "minion_safe": minion_safe,
        "group_traversable": True,
        "sampled_segments": segments,
    }


def _record_route(grid, ctx, a, b, label, out, kind="route"):
    cells = grid.path_cells(ctx.layout[a], ctx.layout[b])
    result = analyze_path(ctx, grid, ctx.layout[a], ctx.layout[b], label, cells=cells, kind=kind)
    out.append(result)
    return result


def _nearest_farthest(layout, base, points, grid, ctx):
    ranked = []
    for p in points:
        cells = grid.path_cells(layout[base], layout[p])
        d = None if cells is None else (len(cells) - 1) * grid.step
        ranked.append((float("inf") if d is None else d, p))
    ranked.sort()
    return (ranked[0][1] if ranked else None, ranked[-1][1] if ranked else None)


def _vector_from(value):
    if value is None:
        return None
    return Vector((float(value[0]), float(value[1]), float(value[2] if len(value) > 2 else 0.0)))


def _inferred_ramp_endpoints(ctx, name):
    cfg = ctx.config
    if name == "North_Ramp_Crown_Core":
        crown = ctx.layout["Crown"].copy()
        north_gate = Vector((0.0, cfg["center_radius"], 0.0))
        crown.z = _ground_z(ctx, crown)
        north_gate.z = _ground_z(ctx, north_gate)
        return crown, north_gate
    for pname in RING_NODES:
        if name != "Ramp_{}".format(pname):
            continue
        pos = ctx.layout[pname].copy()
        pos.z = _ground_z(ctx, pos)
        flat = Vector((pos.x, pos.y, 0.0)).normalized()
        end = pos + flat * (cfg["capture_platform_radius"] * 0.9)
        end.z = _ground_z(ctx, end) + cfg["capture_platform_height"]
        start = end + flat * cfg.get("ramp_run_length", 8.0)
        start.z = _ground_z(ctx, start)
        return start, end
    return None, None


def _direction_alignment_error_deg(a, b, expected_dir):
    route = Vector((b.x - a.x, b.y - a.y, 0.0))
    exp = Vector((expected_dir.x, expected_dir.y, 0.0))
    if route.length <= 1e-6 or exp.length <= 1e-6:
        return None
    route.normalize()
    exp.normalize()
    dot = max(-1.0, min(1.0, route.dot(exp)))
    return abs(math.degrees(math.acos(dot)))


def analyze_ramps(ctx, grid):
    """Audit every generated ramp, including legacy metadata without endpoints."""
    ramps = []
    rules = _rules(ctx.config)
    for rec in ctx.generated_objects:
        if rec.get("type") != "ramp":
            continue
        name = rec.get("name", "Ramp")
        meta = rec.get("meta") or {}
        dims = rec.get("dimensions") or ()
        width = meta.get("width")
        length = meta.get("length")
        drop = meta.get("drop")
        if width is None and len(dims) >= 2:
            width = min(float(dims[0]), float(dims[1]))
        result = {
            "name": name,
            "width_m": round(float(width), 3) if width is not None else None,
            "length_m": round(float(length), 3) if length is not None else None,
            "height_delta_m": round(float(drop), 3) if drop is not None else None,
            "graded": bool(meta.get("graded", name != "North_Ramp_Crown_Core")),
            "terrain_following": bool(meta.get("terrain_following", False)),
            "classification": "DATA MISSING",
            "problems": [],
        }
        if width is not None and float(width) < rules["min_group_width_m"]:
            result["problems"].append("group_width_below_4m")
        a = _vector_from(meta.get("p0"))
        b = _vector_from(meta.get("p1"))
        if a is None or b is None:
            a, b = _inferred_ramp_endpoints(ctx, name)
        if a is not None and b is not None:
            rp = analyze_path(ctx, grid, a, b, name, kind="ramp")
            result.update({
                "classification": rp.get("classification"),
                "sampled_max_slope_deg": rp.get("max_local_slope_deg"),
                "sampled_avg_slope_deg": rp.get("average_local_slope_deg"),
                "sampled_height_delta_m": rp.get("height_delta_m"),
                "sampled_max_adjacent_height_delta_m": rp.get("max_adjacent_height_delta_m"),
                "sampled_reachable": rp.get("reachable"),
                "hero_walkable": rp.get("hero_walkable"),
                "minion_safe": rp.get("minion_safe"),
                "sampled_problems": list(rp.get("problems", [])),
                "entry_point": [round(a.x, 3), round(a.y, 3), round(a.z, 3)],
                "exit_point": [round(b.x, 3), round(b.y, 3), round(b.z, 3)],
            })
            result["height_delta_m"] = rp.get("height_delta_m", result["height_delta_m"])
            result["problems"].extend(rp.get("problems", []))
            result["problems"] = sorted(set(result["problems"]))
            result["group_traversable"] = bool(width is not None and width >= rules["min_group_width_m"] and rp.get("reachable"))
            expected_dir = Vector((b.x, b.y, 0.0))
            if name == "North_Ramp_Crown_Core":
                expected_dir = Vector((0.0, -1.0, 0.0))
            align = _direction_alignment_error_deg(a, b, expected_dir)
            result["alignment_error_deg"] = round(align, 2) if align is not None else None
        else:
            result["problems"].append("endpoint_data_missing")
            result["group_traversable"] = False
        ramps.append(result)
    return ramps


def _route_blocker_report(ctx, grid, cells):
    rules = _rules(ctx.config)
    blocker_hits = []
    ramp_contacts = []
    terrain_edge_hits = []
    narrow_hits = []
    pts = _path_points(ctx, grid, cells)
    for i, p in enumerate(pts):
        if not _terrain_inside(ctx, p):
            terrain_edge_hits.append({"segment": i, "point": [round(p.x, 3), round(p.y, 3)]})
        # The NavGrid already models rocks and gameplay cover as blocked cells.
        # We nevertheless keep a separate audit channel so the minion scenario
        # says exactly why a route is unsafe.
        if grid.cell_of(Vector((p.x, p.y, 0.0))) in grid.blocked:
            blocker_hits.append({"segment": i, "point": [round(p.x, 3), round(p.y, 3)]})
        ramp = _ramp_base_proximity(ctx, p, rules["ramp_base_tolerance_m"])
        if ramp:
            ramp_contacts.append({"segment": i, **ramp})
        if i < len(pts) - 1:
            direction = Vector((pts[i + 1].x - p.x, pts[i + 1].y - p.y, 0.0))
            width = _local_width_clearance(ctx, grid, p, direction)
            if width is not None and width < rules["minion_corridor_width_m"]:
                narrow_hits.append({"segment": i, "clear_width_m": round(width, 3)})
    return {
        "solid_blocker_hits": blocker_hits,
        "ramp_base_contacts": ramp_contacts,
        "terrain_edge_hits": terrain_edge_hits,
        "narrow_corridor_hits": narrow_hits,
    }


def _minion_hop(ctx, grid, a_name, b_name):
    a = ctx.layout[a_name]
    b = ctx.layout[b_name]
    cells = grid.path_cells(a, b)
    analysis = analyze_path(ctx, grid, a, b,
                           "Minion {} -> {}".format(a_name, b_name),
                           cells=cells, kind="minion_route")
    blockers = _route_blocker_report(ctx, grid, cells) if cells else {
        "solid_blocker_hits": [], "ramp_base_contacts": [],
        "terrain_edge_hits": [], "narrow_corridor_hits": [],
    }
    problems = list(analysis.get("problems", []))
    if blockers["solid_blocker_hits"]:
        problems.append("minion_blocker_collision")
    if blockers["ramp_base_contacts"]:
        # Endpoint contact itself is not a defect; the route is only rejected
        # when the recorded ramp base is accompanied by a bad transition.
        if any(s.get("dz_m", 0.0) > _rules(ctx.config)["max_step_m"] for s in analysis.get("sampled_segments", [])):
            problems.append("ramp_base_or_height_step")
    if blockers["terrain_edge_hits"]:
        problems.append("minion_left_terrain")
    if blockers["narrow_corridor_hits"]:
        problems.append("minion_corridor_too_narrow")
    analysis["problems"] = sorted(set(problems))
    return {"from": a_name, "to": b_name, "analysis": analysis, "blockers": blockers}


def run_minion_traversal(ctx, grid):
    """Run Base -> Objective -> Objective -> enemy Base for both teams.

    Both teams use a deterministic mirrored two-objective sequence. Every hop
    uses the real obstacle-aware NavGrid; the report exposes slope, height
    discontinuity, ramp-base contacts, blockers, corridor width and terrain
    edge hits.
    """
    points = list(RING_NODES)
    scenarios = []
    sequences = [
        ("Blue", "BlueBase", "RedBase", [points[0], points[2]]),
        ("Red", "RedBase", "BlueBase", [points[4], points[3]]),
    ]

    for team, base, enemy_base, objectives in sequences:
        route_keys = [base] + objectives + [enemy_base]
        hops = [_minion_hop(ctx, grid, a, b) for a, b in zip(route_keys, route_keys[1:])]
        scenarios.append({
            "team": team,
            "path": route_keys,
            "hops": hops,
            "reachable": all(h["analysis"].get("reachable", False) for h in hops),
            "minion_safe": all(h["analysis"].get("minion_safe", False) and not h["analysis"].get("problems") for h in hops),
            "problems": sorted(set(p for h in hops for p in h["analysis"].get("problems", []))),
            "max_slope_deg": round(max((h["analysis"].get("max_local_slope_deg", 0.0) for h in hops), default=0.0), 2),
            "max_adjacent_height_delta_m": round(max((h["analysis"].get("max_adjacent_height_delta_m", 0.0) for h in hops), default=0.0), 3),
            "solid_blocker_hits": sum(len(h["blockers"]["solid_blocker_hits"]) for h in hops),
            "ramp_base_contacts": sum(len(h["blockers"]["ramp_base_contacts"]) for h in hops),
            "terrain_edge_hits": sum(len(h["blockers"]["terrain_edge_hits"]) for h in hops),
            "narrow_corridor_hits": sum(len(h["blockers"]["narrow_corridor_hits"]) for h in hops),
        })

    return {
        "scenario": "Base -> Objective -> Objective -> enemy Base",
        "rules": {
            "minion_safe_max_deg": _rules(ctx.config)["minion_safe_max_deg"],
            "max_step_m": _rules(ctx.config)["max_step_m"],
            "minion_corridor_width_m": _rules(ctx.config)["minion_corridor_width_m"],
            "minion_radius_m": _rules(ctx.config)["minion_radius_m"],
        },
        "scenarios": scenarios,
        "mirrored_test": len(scenarios) == 2,
        "passed": len(scenarios) == 2 and all(s["reachable"] and s["minion_safe"] and not s["problems"] for s in scenarios),
    }


def analyze_height_transitions(ctx, grid):
    """Complete v0.6.3.2 audit matrix over actual navigation paths."""
    layout = ctx.layout
    points = list(RING_NODES)
    routes = []

    for base in BASES:
        near, far = _nearest_farthest(layout, base, points, grid, ctx)
        if near:
            _record_route(grid, ctx, base, near, "{} -> nearest objective ({})".format(base, near), routes)
        if far and far != near:
            _record_route(grid, ctx, base, far, "{} -> farthest objective ({})".format(base, far), routes)
        for p in points:
            _record_route(grid, ctx, base, p, "{} -> {}".format(base, p), routes)

    for i, a in enumerate(points):
        for b in points[i + 1:]:
            _record_route(grid, ctx, a, b, "{} -> {}".format(a, b), routes, kind="objective_rotation")

    for p in points:
        _record_route(grid, ctx, "Center", p, "Altar/Core -> {}".format(p), routes, kind="altar_approach")

    for p in ("SWMonolith", "SEMonolith"):
        _record_route(grid, ctx, "SouthRift", p, "SouthRift -> {}".format(p), routes, kind="south_rift")

    pocket_routes = []
    for pk in getattr(ctx, "pockets", []):
        cap = layout.get(pk.get("capture_point"))
        entry = pk.get("entry", {}).get("point")
        if cap is None or entry is None:
            pocket_routes.append({"name": pk.get("name"), "classification": "DATA MISSING"})
            continue
        entry_v = Vector(entry)
        in_result = analyze_path(ctx, grid, cap, entry_v, "{} -> Main/Pocket".format(pk["capture_point"]), kind="pocket")
        out_result = analyze_path(ctx, grid, entry_v, cap, "Main/Pocket -> {}".format(pk["capture_point"]), kind="pocket")
        pocket_routes.append({"name": pk.get("name"), "capture_point": pk.get("capture_point"), "in": in_result, "out": out_result})

    ramps = analyze_ramps(ctx, grid)
    minion = run_minion_traversal(ctx, grid)

    problem_routes = [r for r in routes if r.get("problems")]
    problem_pockets = [p for p in pocket_routes if p.get("in", {}).get("problems") or p.get("out", {}).get("problems")]
    problem_ramps = [r for r in ramps if r.get("problems") or r.get("sampled_problems")]

    return {
        "rules": _rules(ctx.config),
        "routes": routes,
        "pocket_transitions": pocket_routes,
        "ramps": ramps,
        "minion_traversal": minion,
        "problem_route_count": len(problem_routes),
        "problem_pocket_count": len(problem_pockets),
        "problem_ramp_count": len(problem_ramps),
        "passed": not (problem_routes or problem_pockets or problem_ramps) and minion.get("passed", False),
    }
