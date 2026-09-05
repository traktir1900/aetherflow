#!/usr/bin/env python3
"""Engine-free math/regression tests for the global outer ellipse."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "mathutils_stub"))
sys.path.insert(0, ROOT)

from core.config import CONFIG
from geometry.boundary import _ellipse_radius, _ellipse_point, _boundary_samples


def check(name, cond):
    if not cond:
        raise AssertionError(name)
    print("[PASS]", name)


def main():
    cfg = CONFIG
    geom = {"semi_x": 98.0, "semi_y": 97.75}
    pts = _boundary_samples(cfg, geom)
    check("48 samples", len(pts) == 48)
    check("closed sampling", _ellipse_point(0.0, 98.0, 97.75).length > 0)
    radii = [math.hypot(p.x, p.y) for _, p, _, _ in pts]
    check("all points inside map", max(max(abs(p.x), abs(p.y)) for _, p, _, _ in pts) < CONFIG["ground_half_size"])
    check("organic deformation bounded", max(radii) - min(radii) < 5.0)
    check("ellipse radius valid", _ellipse_radius(0.0, 98.0, 97.75) == 98.0)
    print("BOUNDARY TESTS: PASS")


if __name__ == "__main__":
    main()
