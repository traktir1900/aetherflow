"""
AetherFlow :: geometry/pockets.py  (v0.6.3 — continuous back-wall geometry)

Four symmetrical gameplay pockets placed in the SIDE ZONES between adjacent
capture points, along (just outside) the main ring road — NOT glued to the
capture platforms:

    WestPocket  <-> EastPocket   — strict mirror pair (West-Crown / Crown-East edges).
    SWPocket    <-> SEPocket     — strict mirror pair (SW-West / East-SE edges).

    (The former CrownPocket was removed in the STEP 1 finalization: the Crown
     capture area is kept as an OPEN central zone with no pocket of its own.)

    CAPTURE POINT ───────────── CAPTURE POINT
           \\                       /
            \\      POCKET         /
             \\                   /
              ───────────────────

The ring road stays the fast open route; a pocket is the slower, covered
flank/ambush alternative.

A pocket is ONE readable rounded-rect zone, built as
  FLOOR + BACK WALL + ENTRY + INTERIOR COVER.
  * FLOOR     — a single contiguous raised pad with its own material, so the
                zone reads clearly from the top-down view.
  * BACK WALL (v0.6.3, spec "POCKET BACK WALL FINAL GEOMETRY") — ONE
                continuous, solid, curved rock-wall mesh wrapping the back
                ~50-60% of the outline (super-ellipse centreline), NOT a
                chain of separate boulders:
                  - height varies smoothly along the arc (highest at the
                    back centre, tapering toward the sides / entry);
                  - thickness varies smoothly (~1.5-3.0 m);
                  - faceted, irregular rock surface (not a smooth curved wall);
                  - a few (2-5) large accent boulders may sit at the base /
                    transitions for silhouette variety, but never replace the
                    solid wall itself;
                  - the wall's own collision/LOS footprint is represented by
                    a handful of invisible rotated-box proxies encased inside
                    the visible rock shell (kept well within its silhouette),
                    so navigation blocks the real curved footprint instead of
                    one oversized disc.
  * FRONT     — fully open toward the ring road; a 6 m entry in the centre is
                kept completely clear (0 wall / 0 rock / 0 cover).
  * INTERIOR COVER (v0.6.2, spec "POCKETS - INTERNAL COVER") — 2-3 rock cover
             objects chosen by core.cover_analysis.optimize_cover: partial LOS
             blocking (never fully closes a sightline), a flank route left AND
             right of every cover object, the centre kept open for the fight,
             and the 6 m entry corridor kept completely clear. Rock sizes come
             from three classes (small/medium/large — see
             core.cover_analysis.ROCK_CLASSES), matching the large/medium/
             small rock reference sizes in the spec. No pillars, no walls, no
             decoration — cover only.
The outline is a 16-sided super-ellipse (wide centre + rounded corners, not a
sharp rectangle, not a perfect circle). The back wall is now a single
continuous solid, so perimeter continuity is guaranteed by construction (no
gap-checking needed, unlike the old discrete rock-chain).

Symmetry (fairness-critical): ONE canonical pocket is built per pair (West/SW);
the opposite side (East/SE) is produced by an EXACT world-space mirror
(x -> -x about the map's vertical axis) with winding reversed, so dimensions,
cover sizes/spacing/heights and mirrored positions are identical.  Pair
equivalence is enforced by validation (validate_pocket_fairness).

Heights: the analytic heightmap is itself symmetric about the vertical axis,
so mirror pairs automatically share an identical height profile.

Terrain / layout / capture points / bases / roads / ramps are NOT modified;
the external rock ring and base geometry are untouched.
"""
import math
import bmesh
from mathutils import Vector, Matrix

from core.layout import polar
from core.utils import finalize_bmesh
from core.heightmap import get_height_at_point
from core.cover_analysis import optimize_cover

COLLECTION = "Pockets"
N_SEG = 16          # 16-sided rounded outline
SUPER_N = 2.5       # super-ellipse exponent -- lower = rounder/oval, no sharp
                     # corners (was 4.0 = boxier rounded-rect); v0.6.1 SHAPE FIX


# ---------------------------------------------------------------------------
# local -> world transform (x = tangential, y = radial-outward from map centre)
# ---------------------------------------------------------------------------
def _local_to_world_xy(local_xy, center, angle_rad):
    """Map pocket-local (x tangential, y radial-out) to world XY (z handled by caller)."""
    lx, ly = local_xy
    ux, uy = math.cos(angle_rad), math.sin(angle_rad)      # radial unit (outward)
    tx, ty = -math.sin(angle_rad), math.cos(angle_rad)     # tangential unit
    return (center.x + lx * tx + ly * ux, center.y + lx * ty + ly * uy)


def _place_box(ctx, name, world_xy, size, rot_rad, element, pocket_name):
    """Axis box whose BASE sits on the heightmap (z = ground + height/2)."""
    gx, gy = world_xy
    ground_z = get_height_at_point(Vector((gx, gy, 0.0)), ctx.config, ctx.layout)
    wc = Vector((gx, gy, ground_z + size[2] / 2.0))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if rot_rad:
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)),
                         matrix=Matrix.Rotation(rot_rad, 4, 'Z'), verts=bm.verts)
    bmesh.ops.translate(bm, verts=bm.verts, vec=wc)
    return finalize_bmesh(
        bm, name, COLLECTION, ctx.get_material("cover"), ctx, kind="cover",
        dims=size, meta={"pocket": pocket_name, "element": element,
                         "rot_z": math.degrees(rot_rad) if rot_rad else 0.0})


# ---------------------------------------------------------------------------
# rounded 16-sided outline (super-ellipse)
# ---------------------------------------------------------------------------
def _rounded_outline(a, b, n_pts=N_SEG):
    """16 points on a super-ellipse (rounded rect a x b), offset half a segment
    so chord centres sit on clean angles — the entry chord lands exactly on the
    local -y (inward) axis, keeping it symmetric."""
    e = 2.0 / SUPER_N
    pts = []
    for i in range(n_pts):
        t = (i + 0.5) * (2.0 * math.pi / n_pts)
        ct, st = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(ct) ** e, ct)
        y = b * math.copysign(abs(st) ** e, st)
        pts.append((x, y))
    return pts


# ---------------------------------------------------------------------------
# exact world-space mirror (guarantees strict pair symmetry)
# ---------------------------------------------------------------------------
def _mirror_object_world(ctx, src_obj, new_name, pocket_name, mirror_pair, rot_override=None):
    """Mirror an object's world geometry about the vertical axis (x -> -x)."""
    bm = bmesh.new()
    bm.from_mesh(src_obj.data)
    # verts are centroid-relative with identity rotation/scale, so world space
    # is a pure translation by obj.location (independent of depsgraph update)
    bm.transform(Matrix.Translation(Vector(src_obj.location)))
    for v in bm.verts:
        v.co.x = -v.co.x
    bm.faces.ensure_lookup_table()
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))  # fix winding after mirror

    src_meta = {}
    for rec in ctx.generated_objects:
        if rec["object"] is src_obj:
            src_meta = rec
            break
    dims = src_meta.get("dimensions")
    meta = dict(src_meta.get("meta") or {})
    meta["pocket"] = pocket_name
    meta["mirror_pair"] = mirror_pair
    if rot_override is not None:
        meta["rot_z"] = rot_override
    mats = src_obj.data.materials
    material = mats[0] if len(mats) else ctx.get_material("cover")
    return finalize_bmesh(bm, new_name, COLLECTION, material, ctx,
                          kind=src_meta.get("type", "cover"), dims=dims, meta=meta)


# ---------------------------------------------------------------------------
# canonical pocket builder (rounded walls + interior cover)
# ---------------------------------------------------------------------------
def _is_pair(name):
    return name in ("WestPocket", "SWPocket")


def _pair_of(name):
    return {"WestPocket": "EastPocket", "SWPocket": "SEPocket"}[name]


# ---------------------------------------------------------------------------
# NATURAL ROCK ARC perimeter (GAMEPLAY SPACE FIRST, cover later).
#
# Each pocket is ONE readable rounded-rect zone:
#     FLOOR  = a single contiguous raised pad (own material) — reads top-down
#     ARC    = a single natural rock boundary wrapping the BACK ~50-60%
#              (local +y, away from the ring road).  Rocks follow a parametric
#              arc (theta) — densest + largest at the back centre, tapering in
#              size / height / density toward the sides.  NO rectangular walls.
#     FRONT  (local -y, toward the ring road) = fully open; a 6 m entry in the
#              centre is kept completely clear (0 rocks / 0 walls / 0 cover).
#
# The arc is a super-ellipse sweep centred on the back (+y).  Rock count is NOT
# fixed — it is derived from the arc length, the rock diameters and the target
# gap, so the result reads as ONE rock massif, not "N rocks in a row".
# ---------------------------------------------------------------------------


def _super_pt(a, b, angle_rad):
    """Point on the super-ellipse outline at the given local angle."""
    e = 2.0 / SUPER_N
    ct, st = math.cos(angle_rad), math.sin(angle_rad)
    return (a * math.copysign(abs(ct) ** e, ct),
            b * math.copysign(abs(st) ** e, st))


def _make_arc_rock(ctx, name, pocket_name, world_xy, radius, height, elong,
                   yaw_rad, tilt_rad, element="backwall", irregularity=None):
    """One irregular, elongated rock formation (deterministic).

    `radius`  — base footprint radius (icosphere radius before elongation).
    `height`  — target vertical extent in metres.
    `elong`   — (major, minor) multipliers of the footprint in the rock frame.
    `yaw_rad` — rotation about Z (aligns the major axis with/ across the arc).
    `tilt_rad`— small lean for a natural silhouette.
    `element` — "backwall" (perimeter arc, blocks nav, not gameplay cover) or
                "cover" (interior pocket cover, blocks nav AND counts as
                gameplay cover in the pocket's cover list).
    `irregularity` — override for the vertex-jitter fraction (default: the
                config's rock.irregularity). Pass a small value (e.g. 0.04)
                when the rock's footprint must be measured precisely (a gate
                rock defining a tolerance-critical passage width), since the
                default jitter can bulge the true mesh surface noticeably
                beyond the nominal `radius`.
    Always registered as kind="rock" (blocks navigation as a disc)."""
    cfg = ctx.config
    rng = ctx.rng
    irr = cfg.get("rock", {}).get("irregularity", 0.32) if irregularity is None else irregularity

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)
    for v in bm.verts:
        v.co += v.normal * rng.uniform(-irr, irr) * radius
        if v.co.z < -radius * 0.5:                       # flatten the base
            v.co.z = -radius * 0.5 + rng.uniform(0.0, radius * 0.08)

    ex, ey = elong
    bmesh.ops.scale(bm, vec=Vector((ex, ey, height / (2.0 * radius))), verts=bm.verts)
    if yaw_rad:
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)),
                         matrix=Matrix.Rotation(yaw_rad, 4, 'Z'), verts=bm.verts)
    if tilt_rad:
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)),
                         matrix=Matrix.Rotation(tilt_rad, 4, 'X'), verts=bm.verts)
    for f in bm.faces:
        f.smooth = True

    gx, gy = world_xy
    ground_z = get_height_at_point(Vector((gx, gy, 0.0)), cfg, ctx.layout)
    bmesh.ops.translate(bm, verts=bm.verts,
                        vec=Vector((gx, gy, ground_z + height * 0.35)))

    foot_r = radius * max(ex, ey)                       # conservative footprint
    return finalize_bmesh(
        bm, name, COLLECTION, ctx.get_material("rock"), ctx, kind="rock",
        dims=(radius * 2 * ex, radius * 2 * ey, height),
        meta={"pocket": pocket_name, "element": element,
              "footprint_radius": foot_r,
              "yaw_deg": math.degrees(yaw_rad) if yaw_rad else 0.0})


def _entry_boundary_y(W, D, half_gap):
    """Local y of the true pocket outline (super-ellipse) at local x = +-half_gap,
    on the front (entry) side. Solves |x/a|^N + |y/b|^N = 1 for y < 0."""
    a, b = W / 2.0, D / 2.0
    fx = min(0.999, abs(half_gap) / a)
    return -b * (1.0 - fx ** SUPER_N) ** (1.0 / SUPER_N)


def _front_angle_deg(W, D, x):
    """Parametric super-ellipse angle (degrees, same convention as _super_pt)
    of the FRONT-side (y < 0) outline point whose local x-coordinate is `x`
    (0 < x < a). Returned in (-90, 0): the front-right quadrant."""
    a = W / 2.0
    e = 2.0 / SUPER_N
    fx = min(0.999, max(0.0, x) / a)
    cos_t = fx ** (1.0 / e)                 # = fx ** (N/2)
    cos_t = min(1.0, max(-1.0, cos_t))
    return -math.degrees(math.acos(cos_t))


# ---------------------------------------------------------------------------
# ENTRY GATE (spec v0.6.1 "POCKET ENTRY WIDTH"): two small flanking rocks pin
# down the ACTUAL clear surface-to-surface passage (not a pivot/centre
# distance) at the front centre. Rocks use reduced mesh irregularity so their
# true surface stays predictably close to the nominal radius (tolerance-
# critical). The back/side rock boundary is then extended (see
# `_arc_span_to_gate`) all the way down the sides to meet the gates, so the
# ONLY opening in the whole perimeter is the gate gap itself.
# ---------------------------------------------------------------------------
def _entry_gate_geometry(W, D, pcfg):
    """Pure config/outline math (no ctx/objects) -- identical for a canonical
    pocket and its exact mirror. Returns dict with half_gap, r0, r_safe, y0,
    irr, height, measured_gap."""
    gcfg = pcfg.get("entry_gate", {})
    target = gcfg.get("target_width", 5.0)
    r0 = gcfg.get("rock_radius", 1.3)
    irr = gcfg.get("irregularity", 0.04)
    height = gcfg.get("height", 2.4)
    r_safe = r0 * (1.0 + irr)
    half_gap = target / 2.0 + r_safe
    y0 = _entry_boundary_y(W, D, half_gap)
    measured_gap = 2.0 * half_gap - 2.0 * r_safe   # == target, by construction
    return {"half_gap": half_gap, "r0": r0, "r_safe": r_safe, "y0": y0,
            "irr": irr, "height": height, "measured_gap": measured_gap}


def _entry_gate_gap(pcfg):
    """The ACTUAL clear passage width (m) the entry gate is built to (pure
    target/radius/irregularity math -- independent of W, D)."""
    gcfg = pcfg.get("entry_gate", {})
    target = gcfg.get("target_width", 5.0)
    r0 = gcfg.get("rock_radius", 1.3)
    irr = gcfg.get("irregularity", 0.04)
    r_safe = r0 * (1.0 + irr)
    half_gap = target / 2.0 + r_safe
    return 2.0 * half_gap - 2.0 * r_safe


def _arc_span_to_gate(W, D, pcfg, connect_buffer=0.5):
    """Total span_deg (centred on the back) the rock boundary must cover so it
    runs continuously from the back, down BOTH sides, and stops just short of
    each gate rock's footprint (leaving only a small `connect_buffer` gap --
    the boundary and the gate read as one touching border)."""
    g = _entry_gate_geometry(W, D, pcfg)
    x_stop = max(0.5, g["half_gap"] - g["r_safe"] - connect_buffer)
    t_stop = _front_angle_deg(W, D, x_stop)     # in (-90, 0)
    half_span = 90.0 - t_stop                   # > 90: wraps past the sides
    return 2.0 * half_span


def _build_entry_gate(ctx, name, W, D, center, a_rad, pcfg):
    """Returns (objects, measured_gap_m, keep-outs)."""
    g = _entry_gate_geometry(W, D, pcfg)
    r0, irr, height = g["r0"], g["irr"], g["height"]
    half_gap, r_safe, y0 = g["half_gap"], g["r_safe"], g["y0"]

    objs = []
    for i, sx in enumerate((-half_gap, half_gap)):
        wxy = _local_to_world_xy((sx, y0), center, a_rad)
        objs.append(_make_arc_rock(
            ctx, "{}_GateRock{:02d}".format(name, i + 1), name, wxy,
            r0, height, (1.0, 1.0), 0.0, 0.0,
            element="backwall", irregularity=irr))

    keep = [(-half_gap, y0, r_safe + 0.5), (half_gap, y0, r_safe + 0.5)]
    return objs, g["measured_gap"], keep



def _arc_length_table(W, D, t0, t1, dense=240):
    """Dense arc-length lookup table for the super-ellipse outline between
    local angles t0 and t1.  Returns (at_length_fn, total_length)."""
    a, b = W / 2.0, D / 2.0
    pts = [_super_pt(a, b, t0 + (t1 - t0) * k / dense) for k in range(dense + 1)]
    cum = [0.0]
    for k in range(1, dense + 1):
        cum.append(cum[-1] + math.hypot(pts[k][0] - pts[k - 1][0],
                                        pts[k][1] - pts[k - 1][1]))
    total = cum[-1]

    def at_length(s):
        s = max(0.0, min(total, s))
        for k in range(1, dense + 1):
            if cum[k] >= s:
                f = (s - cum[k - 1]) / max(1e-9, cum[k] - cum[k - 1])
                return (pts[k - 1][0] + f * (pts[k][0] - pts[k - 1][0]),
                        pts[k - 1][1] + f * (pts[k][1] - pts[k - 1][1]))
        return pts[-1]

    return at_length, total


# ---------------------------------------------------------------------------
# ROCK BOUNDARY (spec v0.6.1 "POCKET SHAPE FINAL FIX"): a single readable,
# ROUNDED/OVAL boundary made of INDIVIDUAL natural rocks (NOT a smooth solid
# mesh wall).  Rocks are walked along the (now rounder) super-ellipse arc by
# arc-length; they wrap smoothly from the back into the sides with NO sharp
# 90-degree corners and NO abrupt cutoff — size/height fade out gradually as
# the arc approaches the entry, so the transition into the open front reads
# as a natural taper rather than a wall stopping dead. Rocks are placed close
# / overlapping enough to read as ONE continuous rounded border from the top
# view, while each stays its own separate object (own collision disc).
# ---------------------------------------------------------------------------
def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _smooth_wave(t, seed, channel=0):
    """Deterministic smooth signal in [-1, 1]; never changes global RNG state."""
    phase = (seed % 100003) * 0.00037 + channel * 1.731
    return (
        0.55 * math.sin(2.0 * math.pi * t + phase) +
        0.30 * math.sin(4.0 * math.pi * t + phase * 1.37) +
        0.15 * math.sin(6.0 * math.pi * t - phase * 0.61)
    )


def _smooth_series(values, passes=2):
    out = list(values)
    for _ in range(max(0, passes)):
        if len(out) < 3:
            break
        nxt = list(out)
        for i in range(1, len(out) - 1):
            nxt[i] = 0.25 * out[i - 1] + 0.5 * out[i] + 0.25 * out[i + 1]
        out = nxt
    return out


def _class_schedule(count, large_ratio, small_ratio, seed):
    """Deterministically distribute size classes without adjacent large anchors."""
    count = int(count)
    labels = ["medium"] * count
    if count <= 0:
        return labels

    large_n = max(1, int(round(count * large_ratio)))
    small_n = max(1, int(round(count * small_ratio)))
    while large_n + small_n >= count:
        if large_n >= small_n and large_n > 1:
            large_n -= 1
        elif small_n > 1:
            small_n -= 1
        else:
            break

    large = []
    start_idx = min(3, max(1, count // 8))
    end_idx = max(start_idx, count - 1 - start_idx)
    for k in range(large_n):
        if large_n == 1:
            idx = count // 2
        else:
            f = (k + 0.5) / large_n
            idx = int(round(start_idx + f * (end_idx - start_idx)))
        if large and idx <= large[-1] + 1:
            idx = large[-1] + 2
        idx = min(max(idx, 1), count - 2)
        if idx not in large:
            large.append(idx)
    for idx in large:
        labels[idx] = "large"

    small_candidates = [i for i in range(count) if labels[i] != "large"]
    preferred = []
    edge_n = small_n // 2
    preferred.extend(range(min(edge_n, count)))
    preferred.extend(range(max(0, count - edge_n), count))

    # Any odd remainder uses the lowest smooth-noise candidate, not a random pick.
    remaining = small_n - len(set(preferred))
    if remaining > 0:
        ranked = sorted(
            (i for i in small_candidates if i not in preferred),
            key=lambda i: (_smooth_wave(i / max(1, count - 1), seed, 7), i),
        )
        preferred.extend(ranked[:remaining])

    used = set()
    for idx in preferred:
        if idx in used or labels[idx] == "large":
            continue
        labels[idx] = "small"
        used.add(idx)
        if len(used) >= small_n:
            break
    return labels


def _fit_gaps_to_length(gaps, required_span, gap_min, gap_max):
    """Adjust only inter-rock gaps so the packed profile fits the arc exactly."""
    gaps = [_clamp(g, gap_min, gap_max) for g in gaps]
    if not gaps:
        return gaps
    residual = required_span - sum(gaps)
    for _ in range(4):
        if abs(residual) < 1e-6:
            break
        if residual > 0.0:
            room = [gap_max - g for g in gaps]
        else:
            room = [g - gap_min for g in gaps]
        total_room = sum(room)
        if total_room <= 1e-9:
            break
        for i, r in enumerate(room):
            if r <= 0.0:
                continue
            delta = residual * (r / total_room)
            if residual > 0.0:
                delta = min(delta, r)
            else:
                delta = max(delta, -r)
            gaps[i] += delta
        residual = required_span - sum(gaps)
    return [_clamp(g, gap_min, gap_max) for g in gaps]


def _rock_arc_plan(W, D, pcfg, rng=None, span_deg_override=None):
    """Build a canonical, boundary-first rock perimeter profile.

    Architectural placement is derived from the canonical super-ellipse and
    arc-length packing.  Variation is deterministic smooth noise, not
    independent random placement.  The profile therefore stays visually
    coherent and mirror-safe while retaining natural size/rotation variation.
    """
    arc = pcfg.get("rock_arc", {})
    span_deg = span_deg_override if span_deg_override is not None else arc.get("span_deg", 168.0)
    span = math.radians(span_deg) / 2.0
    gap_min = float(arc.get("gap_min", 0.15))
    gap_max = float(arc.get("gap_max", 0.35))
    target_spacing = float(arc.get("target_spacing", 2.65))
    min_segments = int(arc.get("min_segments", 22))
    max_segments = int(arc.get("max_segments", 30))
    large_ratio = float(arc.get("large_ratio", 0.18))
    small_ratio = float(arc.get("small_ratio", 0.18))
    inward_limit = float(arc.get("inward_limit", 0.35))
    outward_limit = float(arc.get("outward_limit", 0.45))
    rotation_variance = float(arc.get("rotation_variance", 0.14))
    seed = int(arc.get("seed", pcfg.get("seed", 1337)))
    end_clear = float(arc.get("entry_end_clear", 0.25))
    taper_start = float(arc.get("taper_start", 0.68))
    classes = arc.get("classes", {})

    back = math.pi / 2.0
    t0, t1 = back - span, back + span
    at_length, total = _arc_length_table(W, D, t0, t1)
    available = max(0.0, total - 2.0 * end_clear)

    def pick_noise(t, channel):
        return 0.5 + 0.5 * _smooth_wave(t, seed, channel)

    def effective_diam(diam, t):
        major = 1.06 + 0.08 * pick_noise(t, 11)
        return diam * major

    def build_profile(count):
        labels = _class_schedule(count, large_ratio, small_ratio, seed)
        base_diams = []
        base_heights = []
        for i, cls_name in enumerate(labels):
            spec = classes.get(cls_name) or classes.get("medium")
            if not spec:
                spec = {"diam": (2.6, 3.2), "height": (2.6, 3.5)}
            t = i / max(1, count - 1)
            dn = pick_noise(t, 3)
            hn = pick_noise(t, 5)
            d0, d1 = spec.get("diam", (2.6, 3.2))
            h0, h1 = spec.get("height", (2.6, 3.5))
            diam = d0 + (d1 - d0) * dn
            height = h0 + (h1 - h0) * hn
            u = abs(t - 0.5) * 2.0
            fade = 1.0
            if u > taper_start:
                f = _clamp((u - taper_start) / max(1e-6, 1.0 - taper_start), 0.0, 1.0)
                f = f * f * (3.0 - 2.0 * f)
                fade = 1.0 - 0.15 * f
            base_diams.append(diam * fade)
            base_heights.append(height * (0.93 + 0.07 * fade))

        diams = _smooth_series(base_diams, passes=2)
        heights = _smooth_series(base_heights, passes=2)

        # Keep the class identity, but allow a little bleed across boundaries
        # so neighboring rocks do not produce SMALL -> HUGE transitions.
        for i, cls_name in enumerate(labels):
            spec = classes.get(cls_name) or classes.get("medium")
            lo_d, hi_d = spec.get("diam", (2.6, 3.2))
            lo_h, hi_h = spec.get("height", (2.6, 3.5))
            diams[i] = _clamp(diams[i], lo_d * 0.92, hi_d * 1.06)
            heights[i] = _clamp(heights[i], lo_h * 0.90, hi_h * 1.05)

        gaps = []
        for i in range(count - 1):
            t = i / max(1, count - 2)
            g = gap_min + (gap_max - gap_min) * pick_noise(t, 13)
            gaps.append(g)

        eff_diams = [effective_diam(d, i / max(1, count - 1)) for i, d in enumerate(diams)]
        halfs = [0.5 * d for d in eff_diams]
        min_pack = 2.0 * end_clear + sum(eff_diams) + gap_min * max(0, count - 1)
        max_pack = 2.0 * end_clear + sum(eff_diams) + gap_max * max(0, count - 1)
        return labels, diams, heights, gaps, halfs, eff_diams, min_pack, max_pack

    count = int(round(total / max(1e-6, target_spacing)))
    count = int(_clamp(count, min_segments, max_segments))
    profile = None
    for _ in range(8):
        profile = build_profile(count)
        _labels, _diams, _heights, _gaps, _halfs, _eff_diams, min_pack, max_pack = profile
        if min_pack > available * 1.01 and count > min_segments:
            count -= 1
            continue
        if max_pack < available * 0.96 and count < max_segments:
            count += 1
            continue
        break

    labels, diams, heights, gaps, halfs, eff_diams, min_pack, max_pack = profile
    required_span = available - sum(eff_diams)
    if required_span < gap_min * max(0, count - 1):
        # One last safe reduction if the chosen anchor sizes cannot physically
        # fit while preserving the configured minimum gap.
        count = max(min_segments, count - 1)
        labels, diams, heights, gaps, halfs, eff_diams, min_pack, max_pack = build_profile(count)
        required_span = available - sum(eff_diams)

    gaps = _fit_gaps_to_length(gaps, required_span, gap_min, gap_max)

    positions = []
    s = end_clear + halfs[0]
    positions.append(s)
    for i, gap in enumerate(gaps):
        s += gap + halfs[i] + halfs[i + 1]
        positions.append(s)

    # Re-center tiny numerical drift without changing the entry clearance.
    final_target = total - end_clear - halfs[-1]
    if positions and abs(positions[-1] - final_target) > 1e-5:
        delta = final_target - positions[-1]
        positions = [p + delta * (i / max(1, len(positions) - 1)) for i, p in enumerate(positions)]

    def tangent_angle(s0):
        ds = min(0.20, total * 0.01)
        p0 = at_length(max(0.0, s0 - ds))
        p1 = at_length(min(total, s0 + ds))
        return math.atan2(p1[1] - p0[1], p1[0] - p0[0])

    specs = []
    for i, s0 in enumerate(positions):
        x, y = at_length(s0)
        t_norm = i / max(1, count - 1)
        local_u = abs(t_norm - 0.5) * 2.0
        tangent = tangent_angle(s0)
        tx, ty = math.cos(tangent), math.sin(tangent)
        n1 = Vector((-ty, tx))
        radial = Vector((x, y, 0.0))
        if n1.x * radial.x + n1.y * radial.y < 0.0:
            n1 = -n1

        variation = _smooth_wave(t_norm, seed, 17)
        outward = 0.5 * (variation + 1.0)
        inward_outward = -inward_limit + (inward_limit + outward_limit) * outward
        # Push slightly outward near the entry transition so the inner edge
        # stays clean while the wall tapers into the gate rocks.
        if local_u > taper_start:
            f = _clamp((local_u - taper_start) / max(1e-6, 1.0 - taper_start), 0.0, 1.0)
            f = f * f * (3.0 - 2.0 * f)
            inward_outward += 0.10 * f
        inward_outward = _clamp(inward_outward, -inward_limit, outward_limit)
        x += n1.x * inward_outward
        y += n1.y * inward_outward

        # Orientation follows the boundary tangent with small deterministic
        # variation; elongation is restrained so neighboring silhouettes flow.
        rot_noise = _smooth_wave(t_norm, seed, 19)
        yaw = tangent + rotation_variance * rot_noise
        major = 1.05 + 0.10 * pick_noise(t_norm, 21)
        minor = 0.94 + 0.05 * pick_noise(t_norm, 23)
        elong = (major, minor)
        tilt = math.radians(5.0) * _smooth_wave(t_norm, seed, 29)
        specs.append({
            "local": (x, y),
            "radius": max(0.35, diams[i] / 2.0),
            "height": max(0.5, heights[i]),
            "elong": elong,
            "yaw_local": yaw,
            "tilt": tilt,
            "cls": labels[i],
            "radial_offset": inward_outward,
            "u": local_u,
        })

    metrics = _validate_rock_arc_specs(specs, total, pcfg, end_clear=end_clear)
    metrics["segment_count"] = len(specs)
    metrics["target_spacing"] = target_spacing
    metrics["boundary_length"] = total
    return specs, metrics


def _validate_rock_arc_specs(specs, total, pcfg, end_clear=0.25):
    """Validate only the perimeter plan; does not inspect or mutate scene state."""
    arc = pcfg.get("rock_arc", {})
    gap_min = float(arc.get("gap_min", 0.15))
    gap_max = float(arc.get("gap_max", 0.35))
    inward_limit = float(arc.get("inward_limit", 0.35))
    outward_limit = float(arc.get("outward_limit", 0.45))

    centers = [sp["local"] for sp in specs]
    eff_r = [sp["radius"] * max(sp["elong"]) for sp in specs]
    gaps = []
    for i in range(len(centers) - 1):
        d = math.hypot(centers[i + 1][0] - centers[i][0], centers[i + 1][1] - centers[i][1])
        gaps.append(d - eff_r[i] - eff_r[i + 1])

    min_gap = min(gaps) if gaps else float("inf")
    max_gap = max(gaps) if gaps else 0.0
    center_spacings = []
    for i in range(len(centers) - 1):
        center_spacings.append(math.hypot(centers[i + 1][0] - centers[i][0],
                                          centers[i + 1][1] - centers[i][1]))
    min_center_spacing = min(center_spacings) if center_spacings else float("inf")
    max_center_spacing = max(center_spacings) if center_spacings else 0.0
    center_spacing_ratio = (max_center_spacing / min_center_spacing) if min_center_spacing > 1e-6 else 1.0
    overlap_count = sum(1 for g in gaps if g < -0.15)
    max_inward = max([max(0.0, -sp.get("radial_offset", 0.0)) for sp in specs] or [0.0])
    max_outward = max([max(0.0, sp.get("radial_offset", 0.0)) for sp in specs] or [0.0])

    return {
        "continuity": bool(specs) and overlap_count == 0 and min_gap >= gap_min - 0.05,
        "spacing_ok": bool(gaps) and min_gap >= gap_min - 0.05 and max_gap <= gap_max + 0.05 and center_spacing_ratio <= 1.6,
        "inner_intrusion_ok": max_inward <= inward_limit + 1e-6,
        "outer_deviation_ok": max_outward <= outward_limit + 1e-6,
        "gap_min": round(min_gap, 3) if gaps else None,
        "gap_max": round(max_gap, 3) if gaps else None,
        "center_spacing_ratio": round(center_spacing_ratio, 3),
        "center_spacing_min": round(min_center_spacing, 3) if center_spacings else None,
        "center_spacing_max": round(max_center_spacing, 3),
        "max_inward": round(max_inward, 3),
        "max_outward": round(max_outward, 3),
        "entry_clear": bool(specs) and abs(centers[0][1]) >= 0.0 and abs(centers[-1][1]) >= 0.0,
        "floor_contact": "BY_CONSTRUCTION",
    }


def _build_rock_arc(ctx, name, W, D, center, a_rad, pcfg, span_deg_override=None):
    """Instantiate the boundary-first perimeter plan in world space."""
    specs, metrics = _rock_arc_plan(W, D, pcfg, ctx.rng, span_deg_override=span_deg_override)
    objs, keep = [], []
    for i, sp in enumerate(specs):
        wxy = _local_to_world_xy(sp["local"], center, a_rad)
        ca, sa = math.cos(sp["yaw_local"]), math.sin(sp["yaw_local"])
        wx = ca * (-math.sin(a_rad)) + sa * math.cos(a_rad)
        wy = ca * math.cos(a_rad) + sa * math.sin(a_rad)
        yaw_world = math.atan2(wy, wx)
        objs.append(_make_arc_rock(
            ctx, "{}_ArcRock{:02d}_{}".format(name, i + 1, sp["cls"]), name,
            wxy, sp["radius"], sp["height"], sp["elong"], yaw_world, sp["tilt"]))
        keep.append((sp["local"][0], sp["local"][1], sp["radius"] * max(sp["elong"]) + 0.5))
    return objs, keep, metrics


def _perimeter_continuous(ctx, back_objs, pcfg):
    """True when every neighbouring pair of arc rocks is close enough that the
    boundary reads as ONE rounded border (overlap, or a gap no larger than
    connect_gap) rather than scattered stones."""
    if len(back_objs) < 2:
        return True
    connect_gap = pcfg.get("rock_arc", {}).get("connect_gap", 1.0)
    radii = {}
    for rec in ctx.generated_objects:
        m = rec.get("meta") or {}
        if m.get("element") == "backwall" and m.get("footprint_radius"):
            radii[rec["name"]] = m["footprint_radius"]
    recs = []
    for obj in back_objs:
        r = radii.get(obj.name)
        if r is None:
            continue
        recs.append((obj.location.x, obj.location.y, r))
    for i in range(len(recs) - 1):
        x1, y1, r1 = recs[i]
        x2, y2, r2 = recs[i + 1]
        if math.hypot(x2 - x1, y2 - y1) > (r1 + r2 + connect_gap):
            return False
    return True


# ---------------------------------------------------------------------------
# INTERIOR COVER (spec v0.6.2 "POCKETS - INTERNAL COVER"): 2-3 optimised
# gameplay rocks per pocket, chosen by core.cover_analysis.optimize_cover —
# centre and the 6 m entry stay clear, both flanks (left/right) stay passable,
# sightlines are only partially blocked. Fully deterministic (no RNG feeds the
# candidate selection), so the canonical pocket and its exact mirror always
# choose identical local positions/sizes; only cosmetic irregularity (from
# ctx.rng) differs per rock mesh -- and that mesh is itself mirrored, not
# regenerated, by _mirror_pocket.
# ---------------------------------------------------------------------------
def _build_interior_cover(ctx, name, W, D, center, a_rad, pcfg, exclusions):
    ccfg = pcfg.get("cover", {})
    margin = pcfg.get("cover_margin", 1.4)
    kept, stats = optimize_cover(W, D, margin, ccfg, exclusions=exclusions)

    objs = []
    for i, sp in enumerate(kept):
        wxy = _local_to_world_xy(sp["local"], center, a_rad)
        # gentle, mostly-round boulder (not an elongated wall segment)
        major = ctx.rng.uniform(1.05, 1.25)
        minor = ctx.rng.uniform(0.95, 1.05)
        elong = (major, minor) if ctx.rng.random() < 0.5 else (minor, major)
        yaw_local = ctx.rng.uniform(0.0, 2.0 * math.pi)
        ca, sa = math.cos(yaw_local), math.sin(yaw_local)
        wx = ca * (-math.sin(a_rad)) + sa * math.cos(a_rad)
        wy = ca * math.cos(a_rad) + sa * math.sin(a_rad)
        yaw_world = math.atan2(wy, wx)
        tilt = ctx.rng.uniform(-0.08, 0.08)
        objs.append(_make_arc_rock(
            ctx, "{}_Cover{:02d}_{}".format(name, i + 1, sp["cls"]), name,
            wxy, sp["radius"], sp["height"], elong, yaw_world, tilt,
            element="cover"))
    return objs, stats


def _build_floor(ctx, name, W, D, center, a_rad, pcfg):
    """ONE contiguous gameplay floor for the pocket.

    A solid rounded-rect pad with its own material so the pocket reads as a
    single clear zone from the top-down view.  The top surface follows the
    terrain (heightmap) raised by a small lift, and a buried skirt guarantees
    no floating / no light gap — the floor merges smoothly with the terrain.
    Kind is "floor" (walkable, not blocked by navigation, not counted as cover).
    """
    lift = pcfg.get("floor_lift", 0.15)
    skirt = pcfg.get("floor_skirt", 0.5)
    a, b = W / 2.0, D / 2.0
    outline = [_super_pt(a, b, (i + 0.5) * 2.0 * math.pi / N_SEG) for i in range(N_SEG)]

    bm = bmesh.new()
    top, bot = [], []
    for (lx, ly) in outline:
        wx, wy = _local_to_world_xy((lx, ly), center, a_rad)
        gz = get_height_at_point(Vector((wx, wy, 0.0)), ctx.config, ctx.layout)
        top.append(bm.verts.new((wx, wy, gz + lift)))
        bot.append(bm.verts.new((wx, wy, gz - skirt)))
    bm.verts.ensure_lookup_table()

    bm.faces.new(top)                            # top surface (the zone)
    bm.faces.new(list(reversed(bot)))            # bottom (buried)
    n = len(top)
    for i in range(n):                           # side skirt
        j = (i + 1) % n
        bm.faces.new((top[i], top[j], bot[j], bot[i]))

    obj = finalize_bmesh(
        bm, "{}_Floor".format(name), COLLECTION,
        ctx.get_material("pocket_floor"), ctx, kind="floor",
        dims=(W, D, lift + skirt),
        meta={"pocket": name, "element": "floor"})
    return obj


def _build_pocket(ctx, name, capture, angle_deg, center_radius, size, pcfg):
    """Build ONE readable pocket zone: floor + rock boundary (back+sides, now
    extended all the way to the entry gate) + entry gate + interior cover.

    v0.6.1 ENTRY WIDTH: two small flanking "gate" rocks define an ACTUAL
    measured clear passage (surface-to-surface, not pivot distance) at the
    front centre, and the rock boundary is extended down BOTH sides to meet
    them -- the only opening in the whole pocket perimeter is the gate gap
    itself. Floor size/position and interior cover (C1/C2/C3) are untouched.
    """
    W, D = size["width"], size["depth"]
    center = polar(center_radius, angle_deg)
    a_rad = math.radians(angle_deg)

    objs = []

    # 1) FLOOR — a single contiguous, readable gameplay pad (the zone itself)
    objs.append(_build_floor(ctx, name, W, D, center, a_rad, pcfg))

    # 2) ROCK BOUNDARY — individual natural rocks along the rounded outline,
    #    now spanning back + BOTH full sides, stopping just short of the
    #    entry gate (span computed from the gate's own position, below).
    span_deg = _arc_span_to_gate(W, D, pcfg)
    arc_objs, arc_keep, arc_metrics = _build_rock_arc(ctx, name, W, D, center, a_rad, pcfg,
                                                       span_deg_override=span_deg)
    objs += arc_objs

    # 3) ENTRY GATE — two small flanking rocks pin down the ACTUAL clear
    #    passage width at the front centre (measured surface-to-surface);
    #    the boundary above already runs right up to them.
    gate_objs, gate_gap, gate_keep = _build_entry_gate(
        ctx, name, W, D, center, a_rad, pcfg)
    objs += gate_objs
    print("    {} entry = {:.2f} m".format(name, gate_gap))

    # 4) INTERIOR COVER — 2-3 optimised gameplay rocks (centre + entry stay
    #    clear, both flanks stay passable). Kept clear of the boundary rocks
    #    AND the new gate rocks (arc_keep + gate_keep, local coords).
    cover_objs, cover_stats = _build_interior_cover(
        ctx, name, W, D, center, a_rad, pcfg, arc_keep + gate_keep)
    objs += cover_objs

    # boundary continuity: neighbouring rocks close enough to read as ONE
    # rounded border rather than scattered stones.
    continuous = _perimeter_continuous(ctx, arc_objs, pcfg)
    print("    [PERIMETER] {} segments={} target={:.2f}m center-spacing={:.2f}-{:.2f}m "
          "gap={:.2f}-{:.2f}m inward<={:.2f}m outward<={:.2f}m continuity={} spacing={}".format(
        name, arc_metrics["segment_count"], arc_metrics["target_spacing"],
        arc_metrics.get("center_spacing_min") or 0.0, arc_metrics.get("center_spacing_max") or 0.0,
        arc_metrics.get("gap_min") or 0.0, arc_metrics.get("gap_max") or 0.0,
        arc_metrics["max_inward"], arc_metrics["max_outward"],
        "PASS" if arc_metrics["continuity"] else "FAIL",
        "PASS" if arc_metrics["spacing_ok"] else "FAIL"))

    # entry point: front centre, inside the fully open gap
    exy = _local_to_world_xy((0.0, -(D / 2.0) + 1.0), center, a_rad)
    entry_point = Vector((exy[0], exy[1], 0.0))
    entry_width = pcfg.get("entry_width", 10.0)
    _register_pocket_meta(ctx, objs, name, capture,
                          _pair_of(name) if _is_pair(name) else None,
                          center, (W, D), entry_width, entry_point,
                          cover_stats=cover_stats, floor_area=_floor_area(W, D),
                          perimeter_continuous=continuous)
    _print_pocket_stats(ctx.pockets[-1])
    return objs


def _floor_area(W, D):
    """Usable floor area of the rounded-rect (super-ellipse) pocket."""
    try:
        from core.cover_analysis import polygon_area, rounded_outline
        return round(polygon_area(rounded_outline(W / 2.0, D / 2.0)), 1)
    except Exception:
        return round(W * D * 0.9, 1)


def _print_pocket_stats(meta):
    """Per-pocket report line."""
    print("    [POCKET] {:<12} {}x{} m | floor {:>6.1f} m2 | entry {:>3.1f} m | "
          "perimeter {} | cover {}".format(
        meta["name"],
        int(meta["dimensions"][0]), int(meta["dimensions"][1]),
        meta.get("floor_area") or 0.0,
        meta["entry"]["width"],
        "continuous" if meta.get("perimeter_continuous") else "BROKEN",
        len(meta["cover"])))


def _register_pocket_meta(ctx, objs, name, capture, mirror_pair, center, dims,
                          entry_w, entry_point, cover_stats=None,
                          floor_area=None, perimeter_continuous=True):
    base_z = get_height_at_point(center, ctx.config, ctx.layout)
    positions = []
    cover_names = []
    minz, maxz = base_z, base_z
    for obj in objs:
        loc = obj.location
        d = None
        for rec in ctx.generated_objects:
            if rec["object"] is obj:
                d = rec.get("dimensions")
                # interior cover only: the floor, perimeter walls and the back
                # rock wall are structural, not counted as gameplay cover
                if (rec.get("meta") or {}).get("element") not in ("wall", "backwall", "floor"):
                    cover_names.append(rec["name"])
                break
        positions.append((round(loc.x, 3), round(loc.y, 3), round(loc.z, 3)))
        if d and d[2]:
            minz = min(minz, loc.z - d[2] / 2.0)
            maxz = max(maxz, loc.z + d[2] / 2.0)

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    ctx.pockets.append({
        "name": name,
        "capture_point": capture,
        "mirror_pair": mirror_pair,
        "location": [round(center.x, 3), round(center.y, 3), round(base_z, 3)],
        "dimensions": [round(dims[0], 3), round(dims[1], 3)],
        "bounds": {"min": [round(min(xs), 3), round(min(ys), 3)],
                   "max": [round(max(xs), 3), round(max(ys), 3)]},
        "entry": {"width": round(entry_w, 3),
                  "point": [round(entry_point.x, 3), round(entry_point.y, 3),
                            round(base_z, 3)],
                  "side": "inward"},
        "exits": [{"width": round(entry_w, 3)}],
        "cover": cover_names,
        "cover_positions": positions,
        "height_range": [round(minz, 3), round(maxz, 3)],
        "tactical_role": "flank_cover",
        "cover_analysis": cover_stats,
        "floor_area": floor_area,
        "perimeter_continuous": perimeter_continuous,
    })


# ---------------------------------------------------------------------------
# mirror a whole built pocket to its partner side
# ---------------------------------------------------------------------------
def _mirror_pocket(ctx, src_objs, src_name, dst_name, dst_capture, dst_center, pcfg):
    dst = []
    for obj in src_objs:
        src_rot = None
        for rec in ctx.generated_objects:
            if rec["object"] is obj:
                src_rot = (rec.get("meta") or {}).get("rot_z")
                break
        # mirror about vertical axis maps rotation theta -> 180 - theta
        new_rot = None if src_rot is None else (180.0 - src_rot) % 360.0
        new_label = obj.name.replace(src_name, dst_name)
        dst.append(_mirror_object_world(ctx, obj, new_label, dst_name, src_name,
                                        rot_override=new_rot))

    W = pcfg["side_size"]["width"]
    D = pcfg["side_size"]["depth"]
    src_meta = ctx.pockets[-1]
    # mirror the source entry point about the vertical axis
    sx, sy, _sz = src_meta["entry"]["point"]
    entry_dst = Vector((-sx, sy, 0.0))
    # the mirror is exact, so floor area / continuity / analysis are identical
    _register_pocket_meta(ctx, dst, dst_name, dst_capture, src_name,
                          dst_center, (W, D), pcfg["_last_entry_width"], entry_dst,
                          src_meta.get("cover_analysis"),
                          floor_area=src_meta.get("floor_area"),
                          perimeter_continuous=src_meta.get("perimeter_continuous", True))
    print("    {} entry = {:.2f} m".format(dst_name, _entry_gate_gap(pcfg)))
    _print_pocket_stats(ctx.pockets[-1])
    return dst


# ---------------------------------------------------------------------------
# public entry
# ---------------------------------------------------------------------------
def generate_pockets(ctx):
    cfg = ctx.config
    pcfg = dict(cfg.get("pockets", {}))
    if not pcfg.get("enabled", True):
        return []

    R = pcfg["center_radius"]
    side = pcfg["side_size"]
    created = []

    # CrownPocket was removed in the STEP 1 finalization: the Crown capture
    # area stays an OPEN central zone with no pocket of its own.  Exactly four
    # side pockets remain — West/East and SW/SE as strict mirror pairs.

    # 1) WestPocket (West-Crown edge) -> exact mirror -> EastPocket (Crown-East edge).
    west = _build_pocket(ctx, "WestPocket", "WestMonolith", 126.0, R, side, pcfg)
    created += west
    pcfg["_last_entry_width"] = ctx.pockets[-1]["entry"]["width"]
    created += _mirror_pocket(ctx, west, "WestPocket", "EastPocket", "EastMonolith",
                              polar(R, 54.0), pcfg)

    # 3) SWPocket (SW-West edge) -> exact mirror -> SEPocket (East-SE edge).
    sw = _build_pocket(ctx, "SWPocket", "SWMonolith", 198.0, R, side, pcfg)
    created += sw
    pcfg["_last_entry_width"] = ctx.pockets[-1]["entry"]["width"]
    created += _mirror_pocket(ctx, sw, "SWPocket", "SEPocket", "SEMonolith",
                              polar(R, 342.0), pcfg)

    return created
