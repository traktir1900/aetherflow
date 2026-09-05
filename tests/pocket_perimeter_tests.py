#!/usr/bin/env python3
"""Engine-free tests for the boundary-first pocket rock perimeter planner.

The test loads only the pure planner functions from geometry/pockets.py via AST,
so Blender/bmesh are not required. It validates the design contract without
executing or mutating a Blender scene.
"""
import ast
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.config import CONFIG  # noqa: E402


class Vec2:
    def __init__(self, xyz):
        self.x = xyz[0]
        self.y = xyz[1]
        self.z = xyz[2] if len(xyz) > 2 else 0.0

    def __neg__(self):
        return Vec2((-self.x, -self.y, -self.z))


def load_pure_planner():
    path = os.path.join(ROOT, "geometry", "pockets.py")
    tree = ast.parse(open(path, "r", encoding="utf-8").read())
    wanted = {
        "_super_pt", "_arc_length_table", "_clamp", "_smooth_wave",
        "_smooth_series", "_class_schedule", "_fit_gaps_to_length",
        "_validate_rock_arc_specs", "_rock_arc_plan",
    }
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    ns = {"math": math, "Vector": Vec2, "SUPER_N": 2.5, "N_SEG": 16}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), path, "exec"), ns)
    return ns


def pocket_span_deg():
    pcfg = CONFIG["pockets"]
    g = pcfg["entry_gate"]
    target = g["target_width"]
    r0 = g["rock_radius"]
    irr = g["irregularity"]
    r_safe = r0 * (1.0 + irr)
    half_gap = target / 2.0 + r_safe
    x_stop = max(0.5, half_gap - r_safe - 0.5)
    a = pcfg["side_size"]["width"] / 2.0
    e = 2.0 / 2.5
    fx = min(0.999, abs(x_stop) / a)
    cos_t = fx ** (1.0 / e)
    t_stop = -math.degrees(math.acos(cos_t))
    half_span = 90.0 - t_stop
    return 2.0 * half_span


def run():
    ns = load_pure_planner()
    pcfg = CONFIG["pockets"]
    rcfg = pcfg["rock_arc"]
    span_deg = pocket_span_deg()
    W = pcfg["side_size"]["width"]
    D = pcfg["side_size"]["depth"]

    plans = [ns["_rock_arc_plan"](W, D, {"rock_arc": rcfg}, None, span_deg) for _ in range(3)]
    specs, metrics = plans[0]
    assert 22 <= len(specs) <= 30, len(specs)
    assert 24 <= len(specs) <= 27, "baseline should stay near ~26 perimeter rocks"

    labels = [s["cls"] for s in specs]
    large = labels.count("large") / len(labels)
    small = labels.count("small") / len(labels)
    medium = labels.count("medium") / len(labels)
    assert 0.15 <= large <= 0.20, large
    assert 0.15 <= small <= 0.20, small
    assert 0.60 <= medium <= 0.70, medium

    assert metrics["continuity"] is True, metrics
    assert metrics["spacing_ok"] is True, metrics
    assert metrics["inner_intrusion_ok"] is True, metrics
    assert metrics["outer_deviation_ok"] is True, metrics
    assert metrics["gap_min"] >= rcfg["gap_min"] - 0.05, metrics
    assert metrics["gap_max"] <= rcfg["gap_max"] + 0.05, metrics
    assert metrics["center_spacing_ratio"] <= 1.6, metrics
    assert metrics["max_inward"] <= rcfg["inward_limit"] + 1e-6, metrics
    assert metrics["max_outward"] <= rcfg["outward_limit"] + 1e-6, metrics
    assert metrics["entry_clear"] is True
    assert metrics["floor_contact"] == "BY_CONSTRUCTION"

    # Same W/D/config must produce the identical canonical profile for every
    # pocket pair; mirroring is handled by the existing world-space mirror.
    assert plans[0] == plans[1] == plans[2]

    # The canonical pocket invariants remain untouched.
    assert pcfg["side_size"]["width"] == 28.0
    assert pcfg["side_size"]["depth"] == 18.0
    assert pcfg["entry_gate"]["target_width"] == 10.0
    assert pcfg["cover"]["max_objects"] == 3
    print("POCKET PERIMETER TESTS: PASS")
    print("  segments:", len(specs))
    print("  classes: large={} medium={} small={}".format(
        labels.count("large"), labels.count("medium"), labels.count("small")))
    print("  gap: {:.3f}..{:.3f} m".format(metrics["gap_min"], metrics["gap_max"]))
    print("  center spacing ratio: {:.3f}".format(metrics["center_spacing_ratio"]))
    print("  inward/outward: {:.3f}/{:.3f} m".format(
        metrics["max_inward"], metrics["max_outward"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
