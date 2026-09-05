"""AetherFlow :: v0.6.2.1 gameplay cover refinement.

Objective cover is selected with the shared cover-analysis optimiser instead of
using a hard-coded symmetric pair. Cover is deliberately held outside a
capture-objective stand-off ring so the point remains readable and contestable.
"""
import math
import bmesh
from mathutils import Vector, Matrix

from core.layout import RING_NODES
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh
from core.cover_analysis import optimize_cover


OBJECTIVE_ARENA_WIDTH = 38.0
OBJECTIVE_ARENA_DEPTH = 38.0
OBJECTIVE_WALL_CLEAR = 2.5
OBJECTIVE_COVER_MAX = 2
OBJECTIVE_COVER_MIN_SCORE = 0.35
OBJECTIVE_COVER_COVER_PCT = 0.12
OBJECTIVE_COVER_MIN_PASSAGE = 4.5
OBJECTIVE_COVER_MIN_STANDOFF = 13.0
OBJECTIVE_COVER_MAX_STANDOFF = 18.0
OBJECTIVE_COVER_MIN_SEPARATION = 10.0


def _objective_basis(point):
    u = Vector((point.x, point.y, 0.0))
    if u.length < 1e-6:
        u = Vector((0.0, 1.0, 0.0))
    else:
        u.normalize()
    t = Vector((-u.y, u.x, 0.0))
    return u, t


def _filter_objective_specs(specs, scale, platform_r):
    """Keep flank cover outside the capture fight, with enough separation."""
    min_standoff = max(OBJECTIVE_COVER_MIN_STANDOFF * scale, platform_r + 5.5 * scale)
    max_standoff = OBJECTIVE_COVER_MAX_STANDOFF * scale
    min_sep = OBJECTIVE_COVER_MIN_SEPARATION * scale
    centre_clear = max(6.0 * scale, platform_r + 0.25 * scale)

    ranked = []
    for spec in specs:
        x, y = spec["local"]
        dist = math.hypot(x, y)
        if dist < min_standoff or dist > max_standoff:
            continue
        if abs(x) < centre_clear:
            continue
        score = float(spec.get("score", spec.get("optimizer_score", 0.0)))
        ranked.append((score, dist, spec))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    chosen = []
    for _score, _dist, spec in ranked:
        x, y = spec["local"]
        if any(math.hypot(x - ox, y - oy) < min_sep for ox, oy in [s["local"] for s in chosen]):
            continue
        chosen.append(spec)
        if len(chosen) >= OBJECTIVE_COVER_MAX:
            break
    return chosen


def _pick_objective_cover(ctx, pname, point):
    """Choose up to two flank cover pieces while keeping the point open."""
    del pname, point
    cfg = ctx.config
    scale = float(cfg.get("ground_half_size", 100.0)) / 100.0
    ccfg = {
        "pct_max": OBJECTIVE_COVER_COVER_PCT,
        "min_passage": OBJECTIVE_COVER_MIN_PASSAGE * scale,
        "max_objects": OBJECTIVE_COVER_MAX,
        "min_score": OBJECTIVE_COVER_MIN_SCORE,
        "w_los": 2.0,
        "w_flank": 1.8,
        "w_defensive": 0.7,
        "w_movement": 5.0,
        "w_choke": 5.5,
    }

    platform_r = float(cfg.get("capture_platform_radius", 20.0))
    arena_w = OBJECTIVE_ARENA_WIDTH * scale
    arena_d = OBJECTIVE_ARENA_DEPTH * scale
    wall_clear = OBJECTIVE_WALL_CLEAR * scale

    # Optimizer works in its canonical local arena.  Add a capture-zone hard
    # exclusion, then apply the tactical stand-off and centre-lane filters.
    exclusions = [(0.0, 0.0, platform_r + 1.0 * scale)]
    kept, stats = optimize_cover(arena_w, arena_d, wall_clear, ccfg, exclusions=exclusions)
    for spec in kept:
        spec["score"] = float(stats.get("gameplay_score", 0.0))

    filtered = _filter_objective_specs(kept, scale, platform_r)

    # Deterministic fallback: large flank silhouettes well outside the capture
    # platform. No fallback is allowed to invade the direct entry lane.
    if len(filtered) < OBJECTIVE_COVER_MAX:
        fallback = [
            (-15.0 * scale, 4.0 * scale, 2.25 * scale, 3.4 * scale),
            (15.0 * scale, 4.0 * scale, 1.95 * scale, 3.0 * scale),
        ]
        for idx, (x, y, radius, height) in enumerate(fallback):
            if len(filtered) >= OBJECTIVE_COVER_MAX:
                break
            if math.hypot(x, y) < max(OBJECTIVE_COVER_MIN_STANDOFF * scale, platform_r + 5.5 * scale):
                continue
            if any(math.hypot(x - sx, y - sy) < OBJECTIVE_COVER_MIN_SEPARATION * scale
                   for sx, sy in [s["local"] for s in filtered]):
                continue
            filtered.append({
                "kind": "rock",
                "cls": "large" if idx == 0 else "medium",
                "label": "ObjectiveFallback{}".format(idx + 1),
                "local": (x, y),
                "radius": radius,
                "height": height,
                "size": None,
                "optimizer_score": 0.0,
                "score": 0.0,
            })

    return filtered[:OBJECTIVE_COVER_MAX], stats


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
    """Create optimizer-driven flank cover for all five objectives."""
    built = []
    analyses = {}

    for pname in RING_NODES:
        point = ctx.layout[pname]
        specs, stats = _pick_objective_cover(ctx, pname, point)
        analyses[pname] = stats

        for index, spec in enumerate(specs):
            x, y = spec["local"]
            radius = float(spec.get("radius", 1.9))
            height = float(spec.get("height", 3.0))
            role = "flank_defensive" if index == 0 else "flank_attack"
            yaw = 90.0 if index == 0 else -90.0
            score = float(spec.get("optimizer_score", spec.get("score", 0.0)))
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
        "stand_off_min_m": OBJECTIVE_COVER_MIN_STANDOFF,
        "stand_off_max_m": OBJECTIVE_COVER_MAX_STANDOFF,
        "min_cover_separation_m": OBJECTIVE_COVER_MIN_SEPARATION,
    }
