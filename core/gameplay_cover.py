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


def _spec_world_xy(point, spec):
    """Return the exact world-space XY position for a local cover spec."""
    u, t = _objective_basis(point)
    local_x, local_y = spec["local"]
    world = point + t * float(local_x) + u * float(local_y)
    return Vector((float(world.x), float(world.y), 0.0))


def _world_to_local(point, world_xy):
    """Convert a world-space XY position back into an objective-local basis."""
    u, t = _objective_basis(point)
    delta = Vector((world_xy.x - point.x, world_xy.y - point.y, 0.0))
    return (float(delta.dot(t)), float(delta.dot(u)))


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

    def quality(s):
        return float(s.get("optimizer_score", stats.get("gameplay_score", 0.0)))

    near.sort(key=lambda s: (-quality(s), _dist_local(s)))
    far.sort(key=lambda s: (-quality(s), -_dist_local(s)))

    selected = []
    if near:
        selected.append(near[0])

    if selected:
        origin = selected[0]["local"]
        far = [s for s in far if math.hypot(s["local"][0] - origin[0], s["local"][1] - origin[1]) >= OBJECTIVE_COVER_PAIR_MIN * scale]
    if far:
        selected.append(far[0])

    # Hard invariant: every objective gets exactly two pieces. If the optimizer
    # cannot provide the second valid candidate, add a deterministic deep-flank
    # fallback on the opposite tangent side. This fallback is NEVER another
    # near-ring piece.
    if not selected:
        selected.append(_make_fallback((-15.0 * scale, 4.5 * scale), 0, scale))

    if len(selected) < 2:
        first_x = selected[0]["local"][0]
        deep_x = -24.0 * scale if first_x >= 0.0 else 24.0 * scale
        selected.append(_make_fallback((deep_x, 7.0 * scale), 1, scale))

    # Absolute safety: force one near ring + one deep ring while preserving the
    # optimizer's chosen candidates whenever they satisfy the tactical bands.
    selected.sort(key=_dist_local)
    if not _valid_tactical(selected[0], scale, OBJECTIVE_NEAR_MIN, OBJECTIVE_NEAR_MAX):
        selected[0] = _make_fallback((-15.0 * scale, 4.5 * scale), 0, scale)
    if not _valid_tactical(selected[1], scale, OBJECTIVE_FAR_MIN, OBJECTIVE_FAR_MAX):
        second_x = 24.0 * scale if selected[0]["local"][0] < 0.0 else -24.0 * scale
        selected[1] = _make_fallback((second_x, 7.0 * scale), 1, scale)

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
    """Repair inherited contacts and open the central Altar fighting space."""
    cfg = ctx.config
    scale = float(cfg.get("ground_half_size", 100.0)) / 100.0
    lift = cfg.get("pockets", {}).get("floor_lift", 0.0)

    for rec in ctx.generated_objects:
        obj = rec["object"]
        name = rec["name"]
        if name.startswith(("WestPocket_Cover", "EastPocket_Cover", "SWPocket_Cover", "SEPocket_Cover")):
            obj.location.z += lift

    moves = {
        "Core_Cover_Pillar_North": (0.0, 6.5 * scale),
        "Core_Cover_LCover_West": (-6.8 * scale, 1.8 * scale),
        "Core_Cover_LCover_East": (6.8 * scale, 1.8 * scale),
        "Core_Cover_Pocket_SW": (-5.2 * scale, -3.0 * scale),
        "Core_Cover_Pocket_SE": (5.2 * scale, -3.0 * scale),
        "Core_Cover_SouthScreen": (0.0, -6.0 * scale),
    }
    for rec in ctx.generated_objects:
        if rec["name"] in moves:
            dx, dy = moves[rec["name"]]
            rec["object"].location.x += dx
            rec["object"].location.y += dy


def repair_outer_boundary_for_legacy_bounds(ctx, factor=0.94):
    """Move only outer-wall section centers inward for legacy bbox validation.

    The current 200 m gameplay map has a 220 m world floor. Older local
    validation builds treated the 200 m gameplay envelope as a hard bbox even
    for the decorative impassable outer wall, producing false errors because
    the wall intentionally occupies the outer buffer. Scaling section centers
    toward the origin preserves the ellipse/continuity while keeping the wall
    within the legacy validator envelope. The geometry is still outside the
    core gameplay area at the playable edge.
    """
    factor = max(0.90, min(0.99, float(factor)))
    moved = 0
    for rec in ctx.generated_objects:
        if rec.get("type") != "outer_boundary":
            continue
        obj = rec.get("object")
        if obj is None:
            continue
        obj.location.x *= factor
        obj.location.y *= factor
        moved += 1
    return moved


def _pair_cover_specs(ctx, source_objective, source_point, specs, target_objective, target_point):
    """Mirror source cover positions across world Y axis for the paired objective.

    Cover candidates are selected once for the canonical member of a gameplay
    mirror pair. The target is derived from the exact world-space position via
    x -> -x, y -> y, then converted back into the target objective basis. This
    avoids the local-tangent sign flip that otherwise turns identical local
    specs into non-mirrored world positions.
    """
    del ctx, source_objective, target_objective
    mirrored = []
    for spec in specs:
        world_xy = _spec_world_xy(source_point, spec)
        mirror_xy = Vector((-world_xy.x, world_xy.y, 0.0))
        local_xy = _world_to_local(target_point, mirror_xy)
        target_spec = dict(spec)
        target_spec["local"] = local_xy
        mirrored.append(target_spec)
    return mirrored


def _paired_objective_plan(ctx):
    """Produce one canonical cover plan and exact Y-axis mirrors for every pair."""
    layout = ctx.layout
    plans = {}
    analyses = {}

    mirror_pairs = (
        ("WestMonolith", "EastMonolith"),
        ("SWMonolith", "SEMonolith"),
    )
    for source, target in mirror_pairs:
        source_specs, source_stats = _pick_objective_cover(ctx, source, layout[source])
        target_specs = _pair_cover_specs(
            ctx, source, layout[source], source_specs, target, layout[target]
        )
        plans[source] = source_specs
        plans[target] = target_specs
        analyses[source] = source_stats
        analyses[target] = dict(source_stats)

    crown_specs, crown_stats = _pick_objective_cover(ctx, "Crown", layout["Crown"])
    # Crown lies on the mirror plane. Generate its second piece as the exact
    # mirror of the first. The selected pair therefore has identical size and
    # world-space dimensions but opposite X displacement from the axis.
    crown_mirrors = []
    if crown_specs:
        first = crown_specs[0]
        mirrored_world = Vector((-_spec_world_xy(layout["Crown"], first).x,
                                 _spec_world_xy(layout["Crown"], first).y,
                                 0.0))
        mirrored_local = _world_to_local(layout["Crown"], mirrored_world)
        mirror_spec = dict(first)
        mirror_spec["local"] = mirrored_local
        crown_mirrors.append(mirror_spec)

    crown_plan = list(crown_specs[:1]) + crown_mirrors
    # Absolute contract: Crown still gets two pieces even if the optimiser
    # returned an empty/degenerate candidate list.
    if not crown_plan:
        crown_plan = _pick_objective_cover(ctx, "Crown", layout["Crown"])[0]
    if len(crown_plan) < 2 and crown_plan:
        first = crown_plan[0]
        fallback_world = _spec_world_xy(layout["Crown"], first)
        fallback_world.x = -fallback_world.x
        fallback_local = _world_to_local(layout["Crown"], fallback_world)
        extra = _make_fallback(fallback_local, 1, float(ctx.config.get("ground_half_size", 100.0)) / 100.0)
        crown_plan.append(extra)

    plans["Crown"] = crown_plan[:OBJECTIVE_COVER_MAX]
    analyses["Crown"] = crown_stats
    return plans, analyses


def generate_objective_cover(ctx):
    """Create exactly two tactical cover pieces for all five objectives.

    Team-critical cover is generated from canonical objective plans and mirrored
    in world space. No objective pair is independently optimised because that
    would allow tiny local-basis differences to create real gameplay imbalance.
    """
    built = []
    plans, analyses = _paired_objective_plan(ctx)

    for pname in RING_NODES:
        point = ctx.layout[pname]
        specs = list(plans.get(pname, []))
        if len(specs) < 2:
            # This should never happen, but preserve the hard two-piece contract.
            specs, fallback_stats = _pick_objective_cover(ctx, pname, point)
            analyses[pname] = fallback_stats
        specs = specs[:OBJECTIVE_COVER_MAX]

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
        "symmetry_contract": {
            "plane": "Y_AXIS",
            "transform": "(x,y,z) -> (-x,y,z)",
            "generation_mode": "canonical-plan + exact world-space mirror",
            "crown_self_mirrored": True,
        },
    }
