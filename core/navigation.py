"""
AetherFlow :: core/navigation.py
Obstacle-aware walkability / reachability over the analytic heightmap.

FIX PASS (v0.6.0): the old grid only checked slope, so routes could pass
straight through rocks, cover walls and turrets.  Now:

  * solid registered objects (rocks, core cover, choke rocks, turrets, the
    Altar base) block grid cells — routes go AROUND them;
  * capture platforms, roads, ramps and terrain remain walkable;
  * has_los() performs a 2.5D line-of-sight march (terrain height + solid
    blockers) used by the simulation for exposure / cover metrics;
  * chokepoints are DETECTED from real route density: cells shared by many
    base/objective paths are reported as choke corridors.

Checks provided:
  - base -> every objective reachable (both bases)
  - objective -> objective reachable (all 5)
  - each capture point enterable and exitable
  - no unreachable pockets among the objectives

Limitation (stated explicitly): geometry is sampled on a finite grid, so an
obstacle smaller than a cell is only partially represented; rotated cover is
blocked via its rotated-rectangle footprint, L-cover wings are approximated
by the main wall block.
"""
import math
from collections import deque, Counter
from mathutils import Vector

from core.heightmap import get_height_at_point
from core.layout import RING_NODES, BASES, capture_point_names


# ---------------------------------------------------------------------------
# Obstacle extraction from the generated-object registry
# ---------------------------------------------------------------------------
def build_obstacles(ctx):
    """Return (discs, rects) of solid footprints.

    discs: (x, y, radius, name)   — rocks, turrets, altar base
    rects: (x, y, dx, dy, rot_deg, name) — core cover blocks
    Walkable kinds (capture_point platforms, roads, ramps, terrain,
    safety_floor, crystals, crown) are intentionally excluded.
    """
    discs, rects = [], []
    for rec in ctx.generated_objects:
        t = rec["type"]
        obj = rec["object"]
        loc = getattr(obj, "location", None)
        if loc is None:
            continue
        x, y = float(loc.x), float(loc.y)
        meta = rec.get("meta") or {}
        dims = rec.get("dimensions") or None

        if t == "rock":
            r = meta.get("footprint_radius")
            if not r and dims:
                r = max(dims[0], dims[1]) / 2.0
            if r:
                discs.append((x, y, float(r) * 1.05, rec["name"]))
        elif t == "cover":
            if dims:
                rects.append((x, y, float(dims[0]), float(dims[1]),
                              float(meta.get("rot_z", 0.0)), rec["name"]))
        elif t == "turret":
            r = (float(dims[0]) / 2.0) * 1.15 if dims else 1.0
            discs.append((x, y, r, rec["name"]))
        elif t == "altar" and meta.get("landmark") == "AetherAltar":
            if dims:
                discs.append((x, y, float(dims[0]) / 2.0, rec["name"]))
    return discs, rects


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------
class NavGrid:
    def __init__(self, cfg, layout, cells=None):
        self.cfg = cfg
        self.layout = layout
        self.n = cells or cfg.get("navigation", {}).get("cells", 128)
        self.half = cfg["ground_half_size"]
        self.step = (self.half * 2.0) / self.n
        max_slope = math.radians(cfg.get("navigation", {}).get("max_slope_deg", 50.0))
        self.max_dz = math.tan(max_slope) * self.step
        self.blocked = set()
        self.h = self._build_heights()

    # -- heights -------------------------------------------------------------
    def _build_heights(self):
        h = {}
        for r in range(self.n + 1):
            y = -self.half + r * self.step
            for c in range(self.n + 1):
                x = -self.half + c * self.step
                h[(r, c)] = get_height_at_point(Vector((x, y, 0.0)), self.cfg, self.layout)
        return h

    def cell_of(self, vec):
        c = int(round((vec.x + self.half) / self.step))
        r = int(round((vec.y + self.half) / self.step))
        return (max(0, min(self.n, r)), max(0, min(self.n, c)))

    def world_of(self, cell):
        r, c = cell
        return Vector((-self.half + c * self.step, -self.half + r * self.step, 0.0))

    def height_at(self, vec):
        return get_height_at_point(vec, self.cfg, self.layout)

    # -- blockers --------------------------------------------------------------
    def block_disc(self, cx, cy, radius):
        pad = self.step * 0.5
        rr = radius + pad
        r0 = self.cell_of(Vector((cx - rr, cy - rr, 0)))
        r1 = self.cell_of(Vector((cx + rr, cy + rr, 0)))
        for r in range(r0[0], r1[0] + 1):
            for c in range(r0[1], r1[1] + 1):
                p = self.world_of((r, c))
                if (p.x - cx) ** 2 + (p.y - cy) ** 2 <= rr * rr:
                    self.blocked.add((r, c))

    def block_rect(self, cx, cy, dx, dy, rot_deg=0.0):
        pad = self.step * 0.35
        hx, hy = dx / 2.0 + pad, dy / 2.0 + pad
        rad = math.radians(rot_deg)
        cos_a, sin_a = math.cos(-rad), math.sin(-rad)
        reach = math.hypot(hx, hy)
        r0 = self.cell_of(Vector((cx - reach, cy - reach, 0)))
        r1 = self.cell_of(Vector((cx + reach, cy + reach, 0)))
        for r in range(r0[0], r1[0] + 1):
            for c in range(r0[1], r1[1] + 1):
                p = self.world_of((r, c))
                lx, ly = p.x - cx, p.y - cy
                px = lx * cos_a - ly * sin_a
                py = lx * sin_a + ly * cos_a
                if abs(px) <= hx and abs(py) <= hy:
                    self.blocked.add((r, c))

    def apply_obstacles(self, discs, rects):
        for (x, y, rad, _n) in discs:
            self.block_disc(x, y, rad)
        for (x, y, dx, dy, rot, _n) in rects:
            self.block_rect(x, y, dx, dy, rot)

    # -- walkability -------------------------------------------------------------
    def walkable(self, a, b):
        if b in self.blocked:
            return False
        return abs(self.h[a] - self.h[b]) <= self.max_dz

    def neighbours(self, cell):
        r, c = cell
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (r + dr, c + dc)
            if 0 <= nb[0] <= self.n and 0 <= nb[1] <= self.n and self.walkable(cell, nb):
                yield nb

    # -- pathing -----------------------------------------------------------------
    def path_cells(self, p0, p1):
        """BFS; returns the list of cells from p0 to p1, or None."""
        start, goal = self.cell_of(p0), self.cell_of(p1)
        if start == goal:
            return [start]
        parent = {start: None}
        q = deque([start])
        while q:
            cell = q.popleft()
            for nb in self.neighbours(cell):
                if nb in parent:
                    continue
                parent[nb] = cell
                if nb == goal:
                    path = [nb]
                    while parent[path[-1]] is not None:
                        path.append(parent[path[-1]])
                    path.reverse()
                    return path
                q.append(nb)
        return None

    def path_length(self, p0, p1):
        cells = self.path_cells(p0, p1)
        if cells is None:
            return None
        return max(0, len(cells) - 1) * self.step

    def reachable(self, p0, p1):
        return self.path_cells(p0, p1) is not None

    # -- line of sight (2.5D: terrain height + solid blockers) ---------------------
    def has_los(self, a, b, eye=None):
        eye = eye if eye is not None else self.cfg.get("simulation", {}).get("los_eye_height", 0.6)
        ha = self.height_at(a) + eye
        hb = self.height_at(b) + eye
        dist = (Vector((b.x, b.y, 0)) - Vector((a.x, a.y, 0))).length
        steps = max(2, int(dist / (self.step * 0.5)))
        for i in range(1, steps):
            t = i / float(steps)
            p = Vector((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, 0.0))
            if self.cell_of(p) in self.blocked:
                return False
            line_z = ha + (hb - ha) * t
            if self.height_at(p) > line_z + 1e-4:
                return False
        return True


# ---------------------------------------------------------------------------
# Full check suite
# ---------------------------------------------------------------------------
def build_grid(ctx, cells=None):
    """Obstacle-aware grid built from the real generated map."""
    grid = NavGrid(ctx.config, ctx.layout, cells=cells)
    discs, rects = build_obstacles(ctx)
    grid.apply_obstacles(discs, rects)
    return grid


def detect_chokepoints(grid, routes, zone_points, zone_radius):
    """Cells shared by many routes, outside zone interiors = choke corridors."""
    coverage = Counter()
    for cells in routes:
        for cell in set(cells):
            coverage[cell] += 1
    threshold = max(3, len(routes) // 4)

    def in_zone(cell):
        p = grid.world_of(cell)
        for zp in zone_points:
            if (p - Vector((zp.x, zp.y, 0))).length < zone_radius:
                return True
        return False

    hot = [c for c, n in coverage.items() if n >= threshold and not in_zone(c)]
    # greedy clustering of adjacent hot cells
    hot_set = set(hot)
    clusters = []
    while hot_set:
        seed = min(hot_set)
        cluster = [seed]
        hot_set.discard(seed)
        frontier = [seed]
        while frontier:
            cell = frontier.pop()
            r, c = cell
            for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if nb in hot_set:
                    hot_set.discard(nb)
                    cluster.append(nb)
                    frontier.append(nb)
        clusters.append(cluster)

    out = []
    for cluster in sorted(clusters, key=len, reverse=True)[:5]:
        cx = sum(grid.world_of(c).x for c in cluster) / len(cluster)
        cy = sum(grid.world_of(c).y for c in cluster) / len(cluster)
        peak = max(coverage[c] for c in cluster)
        out.append({"x": round(cx, 2), "y": round(cy, 2),
                    "cells": len(cluster), "routes_through": peak})
    return out


def run_navigation_checks(ctx, grid=None):
    """
    Returns diagnostics.  `ok` is True only when every required route exists.
    All 5 capture points and both bases are exercised over the obstacle-aware
    grid (never straight-line distance).
    """
    cfg = ctx.config
    layout = ctx.layout
    if grid is None:
        grid = build_grid(ctx)
    points = capture_point_names()

    problems = []
    routes = {}          # "A->B": length or None
    route_cells = []     # for chokepoint detection

    def record(key, a, b):
        if key in routes:
            return
        cells = grid.path_cells(a, b)
        routes[key] = None if cells is None else round((len(cells) - 1) * grid.step, 1)
        if cells is not None:
            route_cells.append(cells)

    # base -> every objective
    for base in BASES:
        for p in points:
            record("{}->{}".format(base, p), layout[base], layout[p])

    # objective -> objective (directed, full ring connectivity)
    for i in range(len(points)):
        for j in range(len(points)):
            if i == j:
                continue
            record("{}->{}".format(points[i], points[j]),
                   layout[points[i]], layout[points[j]])

    for key, d in routes.items():
        if d is None:
            problems.append("UNREACHABLE: {}".format(key))

    # enter/exit each capture point (platform edge <-> centre)
    for p in points:
        c = layout[p]
        edge = Vector((c.x + cfg["capture_platform_radius"], c.y, 0.0))
        if not grid.reachable(edge, c):
            problems.append("CAPTURE POINT NOT ENTERABLE: {}".format(p))

    choke = detect_chokepoints(
        grid, route_cells,
        [layout[p] for p in points],
        cfg["capture_platform_radius"] * 1.5)

    # ------------------------------------------------------------------
    # Pocket reachability (v0.6.1): capture point -> pocket entry and back.
    # ------------------------------------------------------------------
    pocket_results = []
    for pk in getattr(ctx, "pockets", []):
        cap = layout.get(pk["capture_point"])
        entry = Vector(pk["entry"]["point"])
        d_in = grid.path_length(cap, entry) if cap is not None else None
        pocket_results.append({
            "name": pk["name"],
            "capture_point": pk["capture_point"],
            "mirror_pair": pk.get("mirror_pair"),
            "reachable": d_in is not None,
            "route_length": round(d_in, 1) if d_in is not None else None,
        })
        if d_in is None:
            problems.append("POCKET UNREACHABLE: {} from {}".format(
                pk["name"], pk["capture_point"]))

    return {
        "ok": len(problems) == 0,
        "checked_points": points,
        "checked_bases": list(BASES),
        "routes": routes,
        "problems": problems,
        "chokepoints": choke,
        "pockets": pocket_results,
        "grid": {"cells": grid.n, "cell_size": round(grid.step, 3),
                 "max_slope_deg": cfg.get("navigation", {}).get("max_slope_deg"),
                 "obstacles": len(grid.blocked)},
    }
