"""
AetherFlow :: core/height_transitions.py
v0.6.3.2 route-based terrain / transition audit.

The audit is deliberately stricter than a single max-slope check. It samples
actual navigation paths, measures local grade and height deltas, inspects all
registered ramps, and reports gameplay-oriented categories. No geometry is
mutated here: repairs must be evidence-driven and happen only after the audit
identifies a real problem.
"""
import math

from mathutils import Vector

from core.layout import BASES, RING_NODES


DEFAULT_RULES = {
    # Diagnostic engineering thresholds, separate from the hard 35 deg terrain ceiling.
    "combat_max_deg": 15.0,
    "minion_safe_max_deg": 18.0,
    "walkable_max_deg": 25.0,
    "ramp_max_deg": 30.0,
    "hard_max_deg": 35.0,
    "max_step_m": 0.75,
    "min_group_width_m": 4.0,
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
    for a, b in zip(pts, pts[1:]):
        dx = b.x - a.x
        dy = b.y - a.y
        run = math.hypot(dx, dy)
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
        segments.append({
            "angle_deg": round(angle, 2),
            "dz_m": round(dz, 3),
            "run_m": round(run, 3),
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
        "problems": problems,
        "hero_walkable": max_angle <= rules["walkable_max_deg"] and max_dz <= rules["max_step_m"],
        "minion_safe": max_angle <= rules["minion_safe_max_deg"] and max_dz <= rules["max_step_m"],
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
    """Recover endpoints for ramps whose metadata predates p0/p1 support."""
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

            if width is not None:
                result["group_traversable"] = bool(width >= rules["min_group_width_m"] and rp.get("reachable"))
            else:
                result["group_traversable"] = False

            expected_dir = Vector((b.x, b.y, 0.0))
            if name == "North_Ramp_Crown_Core":
                expected_dir = Vector((0.0, -1.0, 0.0))
            result["alignment_error_deg"] = round(
                _direction_alignment_error_deg(a, b, expected_dir), 2
            ) if _direction_alignment_error_deg(a, b, expected_dir) is not None else None
        else:
            result["problems"].append("endpoint_data_missing")
            result["group_traversable"] = False

        ramps.append(result)
    return ramps


def analyze_height_transitions(ctx, grid):
    """Complete v0.6.3.2 audit matrix over actual navigation paths."""
    layout = ctx.layout
    points = list(RING_NODES)
    routes = []

    # Base -> nearest/farthest and full base->objective matrix.
    for base in BASES:
        near, far = _nearest_farthest(layout, base, points, grid, ctx)
        if near:
            _record_route(grid, ctx, base, near, "{} -> nearest objective ({})".format(base, near), routes)
        if far and far != near:
            _record_route(grid, ctx, base, far, "{} -> farthest objective ({})".format(base, far), routes)
        for p in points:
            _record_route(grid, ctx, base, p, "{} -> {}".format(base, p), routes)

    # All objective->objective paths.
    for i, a in enumerate(points):
        for b in points[i + 1:]:
            _record_route(grid, ctx, a, b, "{} -> {}".format(a, b), routes, kind="objective_rotation")

    # Central Altar / AetherCore approaches.
    for p in points:
        _record_route(grid, ctx, "Center", p, "Altar/Core -> {}".format(p), routes, kind="altar_approach")

    # SouthRift -> southern objectives.
    for p in ("SWMonolith", "SEMonolith"):
        _record_route(grid, ctx, "SouthRift", p, "SouthRift -> {}".format(p), routes, kind="south_rift")

    # Pocket transitions: capture point <-> pocket entry are the authoritative
    # connected transition points stored by the pocket generator.
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
        pocket_routes.append({
            "name": pk.get("name"),
            "capture_point": pk.get("capture_point"),
            "in": in_result,
            "out": out_result,
        })

    ramps = analyze_ramps(ctx, grid)

    problem_routes = [r for r in routes if r.get("problems")]
    problem_pockets = [p for p in pocket_routes
                       if p.get("in", {}).get("problems") or p.get("out", {}).get("problems")]
    problem_ramps = [r for r in ramps if r.get("problems") or r.get("sampled_problems")]

    return {
        "rules": _rules(ctx.config),
        "routes": routes,
        "pocket_transitions": pocket_routes,
        "ramps": ramps,
        "problem_route_count": len(problem_routes),
        "problem_pocket_count": len(problem_pockets),
        "problem_ramp_count": len(problem_ramps),
        "passed": not (problem_routes or problem_pockets or problem_ramps),
    }
