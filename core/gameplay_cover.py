"""AetherFlow :: v0.6.2.1 objective gameplay cover refinement.

Objective cover is selected with the shared cover-analysis optimiser, then
constrained into two tactical rings: one near-flank piece and one deeper
flank/retreat piece. The capture platform and direct radial lane stay open.
"""
import math
import bmesh
from mathutils import Vector, Matrix

from core.layout import RING_NODES
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh
from core.cover_analysis import optimize_cover

OBJECTIVE_ARENA_WIDTH = 64.0
OBJECTIVE_ARENA_DEPTH = 64.0
OBJECTIVE_WALL_CLEAR = 3.0
OBJECTIVE_COVER_MAX = 2
OBJECTIVE_COVER_MIN_SCORE = 0.35
OBJECTIVE_COVER_COVER_PCT = 0.10
OBJECTIVE_COVER_MIN_PASSAGE = 5.0
OBJECTIVE_NEAR_MIN = 13.0
OBJECTIVE_NEAR_MAX = 18.0
OBJECTIVE_FAR_MIN = 21.0
OBJECTIVE_FAR_MAX = 28.0
OBJECTIVE_COVER_PAIR_MIN = 10.0


def _objective_basis(point):
    u = Vector((point.x, point.y, 0.0))
    if u.length < 1e-6:
        u = Vector((0.0, 1.0, 0.0))
    else:
        u.normalize()
    t = Vector((-u.y, u.x, 0.0))
    return u, t


def _dist_local(spec):
    x, y = spec["local"]
    return math.hypot(x, y)


def _valid_tactical(spec, scale, low, high):
    d = _dist_local(spec)
    return low * scale <= d <= high * scale


def _make_fallback(local_xy, idx, scale):
    x, y = local_xy
    return {
        "kind": "rock",
        "cls": "large" if idx == 0 else "medium",
        "label": "ObjectiveFallback{}".format(idx + 1),
        "local": (x, y),
        "radius": (2.15 if idx == 0 else 1.75) * scale,
        "height": (3.4 if idx == 0 else 2.8) * scale,
        "size": None,
        "optimizer_score": 0.0,
    }


def _pick_objective_cover(ctx, pname, point):
    """Choose one near-flank and one deep-flank cover piece.

    The shared optimiser scores LOS, flank, movement and choke value.
    Tactical post-filtering then enforces two distinct distance bands so
    objectives do not become two-piece camping nests.
    """
    del pname
    cfg = ctx.config
    scale = float(cfg.get("ground_half_size", 100.0)) / 100.0
    ccfg = {
        "pct_max": OBJECTIVE_COVER_COVER_PCT,
        "min_passage": OBJECTIVE_COVER_MIN_PASSAGE * scale,
        "max_objects": 8,
        "min_score": OBJECTIVE_COVER_MIN_SCORE,
        "w_los": 2.2,
        "w_flank": 1.8,
        "w_defensive": 0.8,
        "w_movement": 4.8,
        "w_choke": 5.5,
    }

    arena_w = OBJECTIVE_ARENA_WIDTH * scale
    arena_d = OBJECTIVE_ARENA_DEPTH * scale
    wall_clear = OBJECTIVE_WALL_CLEAR * scale
    platform_r = float(cfg.get("capture_platform_radius", 20.0))
    exclusions = [(0.0, 0.0, platform_r + 2.0 * scale)]

    candidates, stats = optimize_cover(
        arena_w, arena_d, wall_clear, ccfg, exclusions=exclusions)

    usable = [s for s in candidates if abs(s["local"][0]) >= 7.0 * scale]
    near = [s for s in usable if _valid_tactical(s, scale, OBJECTIVE_NEAR_MIN, OBJECTIVE_NEAR_MAX)]
    far = [s for s in usable if _valid_tactical(s, scale, OBJECTIVE_FAR_MIN, OBJECTIVE_FAR_MAX)]

    near.sort(key=lambda s: (-float(s.get("optimizer_score", stats.get("gameplay_score", 0.0))), _dist_local(s)))
    far.sort(key=lambda s: (-float(s.get("optimizer_score", stats.get("gameplay_score", 0.0))), -_dist_local(s)))

    selected = []
    if near:
        selected.append(near[0])

    if selected:
        origin = selected[0]["local"]
        far = [s for s in far if math.hypot(s["local"][0] - origin[0], s["local"][1] - origin[1]) >= OBJECTIVE_COVER_PAIR_MIN * scale]
    if far:
        selected.append(far[0])

    # Deterministic fallback guarantees the second piece is DEEP, never another
    # near-ring piece. If optimizer supplies no valid near candidate, use a near
    # fallback first; if it supplies no valid far candidate, use the deep fallback.
    if not selected:
        selected.append(_make_fallback((-15.0 * scale, 4.5 * scale), 0, scale))

    if len(selected) < OBJECTIVE_COVER_MAX:
        deep_pool = [(-24.0 * scale, 7.0 * scale), (24.0 * scale, 7.0 * scale)]
        deep_xy = None
        for xy in deep_pool:
            if math.hypot(xy[0] - selected[0]["local"][0], xy[1] - selected[0]["local"][1]) >= OBJECTIVE_COVER_PAIR_MIN * scale:
                deep_xy = xy
                break
        if deep_xy is not None:
            selected.append(_make_fallback(deep_xy, 1, scale))

    # Absolute safety: if optimizer selected two pieces, enforce the intended
    # near/deep order. This does not change the optimiser source score; it only
    # chooses which role each accepted piece receives.
    if len(selected) >= 2:
        selected.sort(key=_dist_local)
        if _dist_local(selected[0]) > OBJECTIVE_NEAR_MAX * scale:
            selected[0] = _make_fallback((-15.0 * scale, 4.5 * scale), 0, scale)
        if _dist_local(selected[1]) < OBJECTIVE_FAR_MIN * scale:
            selected[1] = _make_fallback((24.0 * scale, 7.0 * scale), 1, scale)

    return selected[:OBJECTIVE_COVER_MAX], stats


def _make_cover(ctx, name, objective_name, point, local_x, local_y,
                radius, height, yaw_deg, role, source_score):
    cfg = ctx.config
    u, t = _objective_basis(point)
    pos = point + t * local_x + u * local_y
    pos.z = get_height_at_point(pos, cfg, ctx.layout)

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)
    rng = ctx.rng
    for v in bm.verts:
        v.co += v.normal * rng.uniform(-0.10, 0.10) * radius
        if v.co.z < -radius * 0.55:
            v.co.z = -radius * 0.55
    bmesh.ops.scale(
        bm,
        vec=Vector((1.20, 0.82, max(0.9, height / max(2.0 * radius, 1e-6)))),
        verts=bm.verts,
    )
    bmesh.ops.rotate(
        bm,
        cent=Vector((0, 0, 0)),
        matrix=Matrix.Rotation(math.radians(yaw_deg), 4, 'Z'),
        verts=bm.verts,
    )
    for f in bm.faces:
        f.smooth = True
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=pos + Vector((0, 0, height * 0.38)),
    )

    return finalize_bmesh(
        bm,
        name,
        "CoreCover",
        ctx.get_material("rock"),
        ctx,
        kind="cover",
        dims=(radius * 2.4, radius * 1.64, height),
        meta={
            "gameplay_cover": True,
            "cover_role": role,
            "cover_source": "shared_cover_optimizer",
            "objective": objective_name,
            "footprint_radius": radius * 1.20,
            "rot_z": yaw_deg,
            "optimizer_score": round(float(source_score), 3),
        },
    )


def _repair_known_cover_contacts(ctx):
    """Repair exact inherited contacts reported by the v0.6.1 audit."""
    cfg = ctx.config
    scale = float(cfg.get("ground_half_size", 100.0)) / 100.0
    lift = cfg.get("pockets", {}).get("floor_lift", 0.0)

    for rec in ctx.generated_objects:
        obj = rec["object"]
        name = rec["name"]
        if name.startswith(("WestPocket_Cover", "EastPocket_Cover", "SWPocket_Cover", "SEPocket_Cover")):
            obj.location.z += lift

    moves = {
        "Core_Cover_Pillar_North": (0.0, 1.0 * scale),
        "Core_Cover_Pocket_SW": (-0.8 * scale, -0.4 * scale),
        "Core_Cover_Pocket_SE": (0.8 * scale, -0.4 * scale),
        "Core_Cover_SouthScreen": (0.0, -0.6 * scale),
    }
    for rec in ctx.generated_objects:
        if rec["name"] in moves:
            dx, dy = moves[rec["name"]]
            rec["object"].location.x += dx
            rec["object"].location.y += dy


def generate_objective_cover(ctx):
    """Create two tactical cover pieces for all five objectives."""
    built = []
    analyses = {}

    for pname in RING_NODES:
        point = ctx.layout[pname]
        specs, stats = _pick_objective_cover(ctx, pname, point)
        analyses[pname] = stats

        for index, spec in enumerate(specs):
            x, y = spec["local"]
            radius = float(spec.get("radius", 1.6))
            height = float(spec.get("height", 2.7))
            role = "flank_defensive" if index == 0 else "deep_flank_attack"
            yaw = 90.0 if index == 0 else -90.0
            score = float(spec.get("optimizer_score", 0.0))
            built.append(_make_cover(
                ctx,
                "ObjectiveCover_{}_{}".format(pname, index + 1),
                pname,
                point,
                x,
                y,
                radius,
                height,
                yaw,
                role,
                score,
            ))

    return built, analyses


def run_gameplay_cover_pass(ctx):
    """Run repairs first, then add objective cover."""
    _repair_known_cover_contacts(ctx)
    built, analyses = generate_objective_cover(ctx)
    return {
        "objective_cover_count": len(built),
        "objectives_covered": len(RING_NODES),
        "deterministic_seed": int(ctx.config.get("seed", 1337)),
        "optimizer": "shared_cover_analysis.optimize_cover",
        "objective_analyses": analyses,
        "tactical_rings_m": {
            "near": [OBJECTIVE_NEAR_MIN, OBJECTIVE_NEAR_MAX],
            "far": [OBJECTIVE_FAR_MIN, OBJECTIVE_FAR_MAX],
            "pair_min": OBJECTIVE_COVER_PAIR_MIN,
        },
    }
