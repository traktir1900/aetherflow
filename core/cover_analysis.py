"""
AetherFlow :: core/cover_analysis.py  (v0.6.1 — gameplay cover math)

Mathematical cover optimisation for the gameplay pockets.

The goal is NOT "3-6 objects per pocket" but an OPEN, tactically useful combat
arena.  Cover is chosen by analysing the real geometry and scoring every
candidate:

    COVER_SCORE = LOS_BENEFIT + FLANK_BENEFIT + DEFENSIVE_VALUE
                  - MOVEMENT_PENALTY - CHOKEPOINT_PENALTY

Only candidates with a positive gameplay value are kept, subject to:
  * total cover footprint <= cover_pct_max of the usable floor (stays open);
  * every passage stays >= min_passage (no artificial chokepoints / dead ends);
  * the entry corridor and the main entry->centre path stay clear;
  * no two covers overlap.

All computation is in pocket-LOCAL coordinates (x = tangential, y = radial-out,
entry on the -y side) and is fully deterministic (no RNG), so the canonical
pocket and its exact mirror always match.
"""
import math

SUPER_N = 2.5   # keep in sync with geometry/pockets.py's SUPER_N (shared pocket outline)


# ---------------------------------------------------------------------------
# geometry helpers (local 2-D coords)
# ---------------------------------------------------------------------------
def rounded_outline(a, b, n_pts=16):
    """16 points on a super-ellipse (rounded rect a x b), half-segment offset."""
    e = 2.0 / SUPER_N
    pts = []
    for i in range(n_pts):
        t = (i + 0.5) * (2.0 * math.pi / n_pts)
        ct, st = math.cos(t), math.sin(t)
        pts.append((a * math.copysign(abs(ct) ** e, ct),
                    b * math.copysign(abs(st) ** e, st)))
    return pts


def polygon_area(pts):
    """Shoelace area of a (convex) polygon."""
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def point_in_polygon(x, y, pts):
    """Ray-cast point-in-polygon (works for the convex rounded rect)."""
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def seg_circle_chord(p0, p1, c, r):
    """Length of segment p0->p1 that lies inside circle (c, r)."""
    ax, ay = p0
    bx, by = p1
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-9:
        return 0.0
    fx, fy = ax - c[0], ay - c[1]
    # solve |p0 + t*d - c|^2 = r^2
    A = L2
    B = 2.0 * (fx * dx + fy * dy)
    C = fx * fx + fy * fy - r * r
    disc = B * B - 4.0 * A * C
    if disc < 0.0:
        return 0.0
    sq = math.sqrt(disc)
    t1 = max(0.0, (-B - sq) / (2.0 * A))
    t2 = min(1.0, (-B + sq) / (2.0 * A))
    if t2 <= t1:
        return 0.0
    return (t2 - t1) * math.sqrt(L2)


def los_blocked_fraction(p0, p1, obstacles):
    """Fraction (0..1) of the sight line p0->p1 occluded by circular obstacles."""
    total = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    if total < 1e-9:
        return 0.0
    blocked = sum(seg_circle_chord(p0, p1, (o[0], o[1]), o[2]) for o in obstacles)
    return min(1.0, blocked / total)


# ---------------------------------------------------------------------------
# cover candidate model
# ---------------------------------------------------------------------------
# type -> (blocking_radius for LOS, footprint_area)
def _footprint(spec):
    if spec["kind"] == "rock":
        r = spec["radius"]
        return r, math.pi * r * r
    w, l, _h = spec["size"]
    # conservative circular approximation of a (possibly rotated) box
    r = 0.5 * math.hypot(w, l) * 0.75
    return r, w * l


def _spec_pos(spec):
    return spec["local"]


# ---------------------------------------------------------------------------
# rock size classes (spec v0.6.2 "POCKETS - INTERNAL COVER"):
#   large:  height 2.5-4.5 m, length 3-6 m
#   medium: height 1.5-3.0 m, length 2-4 m
#   small:  height 1.0-2.0 m, length 1.5-3 m
# Deterministic candidates use the midpoint of each range (no RNG here, so
# canonical <-> mirror stay pixel-identical); radius = length / 2.
# ---------------------------------------------------------------------------
ROCK_CLASSES = {
    "large":  {"diam": 4.5, "height": 3.5},
    "medium": {"diam": 3.0, "height": 2.25},
    "small":  {"diam": 2.25, "height": 1.5},
}


# ---------------------------------------------------------------------------
# candidate scoring
# ---------------------------------------------------------------------------
def _key_points(W, D, t):
    """Entry / centre / flank / rear probes in local coords (entry on -y)."""
    ey = -(D / 2.0 - t) + 1.0          # just inside the entry
    return {
        "E": (0.0, ey),
        "C": (0.0, 0.0),
        "L": (-W * 0.25, 0.0),
        "R": (W * 0.25, 0.0),
        "B": (0.0, D * 0.30),
    }


def score_candidate(spec, kept, W, D, t, weights, min_passage):
    """COVER_SCORE = LOS + FLANK + DEFENSIVE - MOVEMENT - CHOKEPOINT."""
    kp = _key_points(W, D, t)
    r, area = _footprint(spec)
    pos = _spec_pos(spec)

    obstacles = [(_spec_pos(k)[0], _spec_pos(k)[1], _footprint(k)[0]) for k in kept]
    cand = (pos[0], pos[1], r)

    # --- LOS_BENEFIT: breaking the long entry->rear and entry->flank lines ---
    los = 0.0
    for a, b, w in (("E", "B", 1.0), ("E", "L", 0.7), ("E", "R", 0.7)):
        base = los_blocked_fraction(kp[a], kp[b], obstacles)
        with_c = los_blocked_fraction(kp[a], kp[b], obstacles + [cand])
        los += w * max(0.0, with_c - base)
    los_benefit = weights["los"] * min(1.0, los)

    # --- FLANK_BENEFIT: a route can still pass on each side of the cover ----
    flank = 0.0
    for side_x in (-1.0, 1.0):
        probe = (side_x * W * 0.33, pos[1])
        d = math.hypot(probe[0] - pos[0], probe[1] - pos[1])
        if d > r + min_passage * 0.6:          # room to slip past this side
            flank += 0.5
    flank_benefit = weights["flank"] * flank

    # --- DEFENSIVE_VALUE: closer to the perimeter = better edge cover --------
    dx = abs(pos[0]) / (W / 2.0)
    dy = abs(pos[1]) / (D / 2.0)
    edge = max(dx, dy)                         # 1 at wall, 0 at centre
    defensive = weights["defensive"] * edge

    # --- MOVEMENT_PENALTY: must not sit on the main entry->centre path -------
    move_block = los_blocked_fraction(kp["E"], kp["C"], [cand])
    movement = weights["movement"] * move_block

    # --- CHOKEPOINT_PENALTY: would create a gap narrower than min_passage ----
    choke = 0.0
    # gap to the surrounding wall (interior half-extents) — a real narrow gap is
    # penalised regardless of how "edgy" the spot looks
    gap_x = (W / 2.0 - t) - abs(pos[0]) - r
    gap_y = (D / 2.0 - t) - abs(pos[1]) - r
    if min(gap_x, gap_y) < min_passage:
        choke += 1.0                            # squeezed against a wall
    # gap to already-kept cover
    for k in kept:
        kr, _ = _footprint(k)
        kpos = _spec_pos(k)
        d = math.hypot(kpos[0] - pos[0], kpos[1] - pos[1]) - (kr + r)
        if d < min_passage:
            choke += 1.0
    chokepoint = weights["choke"] * min(1.0, choke)

    score = los_benefit + flank_benefit + defensive - movement - chokepoint
    return {
        "score": score,
        "los_benefit": los_benefit,
        "flank_benefit": flank_benefit,
        "defensive": defensive,
        "movement_penalty": movement,
        "chokepoint_penalty": chokepoint,
        "area": area,
    }


# ---------------------------------------------------------------------------
# greedy optimiser
# ---------------------------------------------------------------------------
def _candidate_specs(W, D, t):
    """A fixed, deterministic field of plausible cover spots x types."""
    # x = 0 (centre line) is included so a cover can break the entry->rear ray;
    # the entry-corridor / centre-clear filters below keep it out of the doorway.
    xs = (-0.42, -0.25, -0.125, 0.0, 0.125, 0.25, 0.42)
    ys = (-0.18, 0.05, 0.15, 0.30)
    specs = []
    n = 0
    for fx in xs:
        for fy in ys:
            x, y = fx * W, fy * D
            # keep clear of the entry corridor (near -y centre) and exact centre
            if abs(x) < W * 0.10 and fy < 0.0:
                continue
            if abs(x) < W * 0.06 and abs(y) < D * 0.06:
                continue
            for cls_name, cls in ROCK_CLASSES.items():
                n += 1
                specs.append({
                    "kind": "rock",
                    "cls": cls_name,
                    "label": "Cand{:02d}".format(n),
                    "local": (x, y),
                    "radius": cls["diam"] / 2.0,
                    "height": cls["height"],
                    "size": None,
                })
    return specs


def optimize_cover(W, D, t, ccfg, exclusions=None):
    """Pick the gameplay-optimal cover set for one (canonical) pocket.

    exclusions: optional list of (x, y, r) keep-out circles in local coords
    (perimeter wall rocks, entry stubs) that cover may not overlap.

    Returns (specs, stats): the chosen cover specs and the analysis table.
    """
    exclusions = exclusions or []
    pct_max = ccfg.get("pct_max", 0.15)
    min_passage = ccfg.get("min_passage", 3.0)
    max_objects = ccfg.get("max_objects", 8)
    # only cover with genuine gameplay value survives (quality over quantity)
    min_score = ccfg.get("min_score", 1.5)
    weights = {
        "los": ccfg.get("w_los", 3.0),
        "flank": ccfg.get("w_flank", 1.0),
        "defensive": ccfg.get("w_defensive", 1.5),
        "movement": ccfg.get("w_movement", 3.0),
        "choke": ccfg.get("w_choke", 4.0),
    }

    interior = rounded_outline(W / 2.0 - t, D / 2.0 - t)
    usable = polygon_area(interior)

    candidates = []
    for spec in _candidate_specs(W, D, t):
        x, y = spec["local"]
        if not point_in_polygon(x, y, interior):
            continue
        # keep clear of perimeter keep-outs (back wall rocks, entry stubs)
        r = _footprint(spec)[0]
        if any(math.hypot(x - ex, y - ey) < r + er for (ex, ey, er) in exclusions):
            continue
        candidates.append(spec)

    # score every candidate against the (growing) kept set, greedily
    kept = []
    cover_area = 0.0
    total_score = 0.0
    pool = list(candidates)
    while pool and len(kept) < max_objects:
        best, best_info = None, None
        for spec in pool:
            info = score_candidate(spec, kept, W, D, t, weights, min_passage)
            if best_info is None or info["score"] > best_info["score"]:
                best, best_info = spec, info
        # stop when even the best remaining candidate lacks real gameplay value
        if best is None or best_info["score"] < min_score:
            break
        if cover_area + best_info["area"] > usable * pct_max:
            pool.remove(best)          # too big for the remaining budget
            continue
        kept.append(best)
        cover_area += best_info["area"]
        total_score += best_info["score"]
        pool.remove(best)

    stats = _analyse(W, D, t, kept, usable, total_score)
    return kept, stats


def _route_lengths(W, D, t, obstacles, cell=0.5):
    """Shortest and an alternative entry->back path length (local grid BFS).

    The alternative is forced around the centreline, i.e. a genuine flank
    detour.  Returns (shortest, alternative) or (None, None) if no route.
    """
    from collections import deque
    x_max, y_max = W / 2.0 - t, D / 2.0 - t
    nx = int((2 * x_max) / cell) + 1
    ny = int((2 * y_max) / cell) + 1

    def is_blocked(x, y):
        return any(math.hypot(x - ox, y - oy) < or_ for (ox, oy, or_) in obstacles)

    def cell_of(x, y):
        gx = int(round((x + x_max) / cell))
        gy = int(round((y + y_max) / cell))
        return (max(0, min(nx - 1, gx)), max(0, min(ny - 1, gy)))

    def world_x(g):
        return -x_max + g[0] * cell

    def bfs(centre_blocked):
        start = cell_of(0.0, -y_max + 0.5)
        goal = cell_of(0.0, y_max - 0.5)
        parent = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                steps = 0
                c = cur
                while parent[c] is not None:
                    c = parent[c]
                    steps += 1
                return steps * cell
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (cur[0] + dx, cur[1] + dy)
                if 0 <= nb[0] < nx and 0 <= nb[1] < ny and nb not in parent:
                    wx = world_x(nb)
                    if centre_blocked and abs(wx) < 0.8:
                        continue
                    wy = -y_max + nb[1] * cell
                    if is_blocked(wx, wy):
                        continue
                    parent[nb] = cur
                    q.append(nb)
        return None

    shortest = bfs(False)
    if shortest is None:
        return None, None
    alternative = bfs(True)
    if alternative is None:
        alternative = shortest
    return round(shortest, 1), round(alternative, 1)


def _analyse(W, D, t, kept, usable, total_score=0.0):
    """Produce the gameplay analysis table for the chosen cover set."""
    kp = _key_points(W, D, t)
    obstacles = [(_spec_pos(k)[0], _spec_pos(k)[1], _footprint(k)[0]) for k in kept]

    cover_area = sum(_footprint(k)[1] for k in kept)
    cover_pct = cover_area / usable if usable else 0.0

    rays = (("E", "C"), ("E", "B"), ("E", "L"), ("E", "R"), ("L", "R"), ("C", "B"))
    fracs = [los_blocked_fraction(kp[a], kp[b], obstacles) for a, b in rays]
    avg_los = sum(fracs) / len(fracs)
    fully_blocked = sum(1 for f in fracs if f > 0.95)

    # minimum free passage between cover and the perimeter walls / other cover
    def wall_gap(k):
        x, y = _spec_pos(k)
        r = _footprint(k)[0]
        return min((W / 2.0 - t) - abs(x) - r, (D / 2.0 - t) - abs(y) - r)

    min_pass = min((wall_gap(k) for k in kept), default=(W / 2.0 - t))
    for i in range(len(kept)):
        for j in range(i + 1, len(kept)):
            a, b = _spec_pos(kept[i]), _spec_pos(kept[j])
            gap = math.hypot(a[0] - b[0], a[1] - b[1]) - (
                _footprint(kept[i])[0] + _footprint(kept[j])[0])
            min_pass = min(min_pass, gap)

    chokepoints = sum(1 for f in fracs if f > 0.95)  # fully blocked sightlines
    shortest, alternative = _route_lengths(W, D, t, obstacles)
    return {
        "floor_area": round(usable, 1),
        "cover_objects": len(kept),
        "cover_area": round(cover_area, 1),
        "cover_pct": round(cover_pct * 100.0, 1),
        "free_pct": round((1.0 - cover_pct) * 100.0, 1),
        "avg_los_block_pct": round(avg_los * 100.0, 1),
        "fully_blocked_los": fully_blocked,
        "min_passage": round(min_pass, 1),
        "chokepoints": chokepoints,
        "shortest_path": shortest,
        "alternative_path": alternative,
        "gameplay_score": round(total_score, 1),
    }
