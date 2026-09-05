"""AetherFlow :: v0.6.2.1 gameplay cover pass.

Extends the existing cover concept to capture objectives.  The pass repairs
known inherited cover contacts, then adds deterministic objective cover without
changing layout/topology.
"""
import math
import bmesh
from mathutils import Vector, Matrix

from core.layout import RING_NODES
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh


def _make_cover(ctx, name, objective_name, point, local_x, local_y, radius, height, yaw_deg, side):
    cfg = ctx.config
    u = Vector((point.x, point.y, 0.0)).normalized()
    t = Vector((-u.y, u.x, 0.0))
    pos = point + t * local_x + u * local_y
    pos.z = get_height_at_point(pos, cfg, ctx.layout)

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)
    rng = ctx.rng
    irr = 0.12
    for v in bm.verts:
        v.co += v.normal * rng.uniform(-irr, irr) * radius
        if v.co.z < -radius * 0.55:
            v.co.z = -radius * 0.55
    bmesh.ops.scale(bm, vec=Vector((1.15, 0.85, height / (2.0 * radius))), verts=bm.verts)
    bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)),
                     matrix=Matrix.Rotation(math.radians(yaw_deg), 4, 'Z'), verts=bm.verts)
    for f in bm.faces:
        f.smooth = True
    bmesh.ops.translate(bm, verts=bm.verts,
                        vec=pos + Vector((0, 0, height * 0.35)))

    return finalize_bmesh(
        bm, name, "CoreCover", ctx.get_material("rock"), ctx,
        kind="cover", dims=(radius * 2.3, radius * 1.7, height),
        meta={
            "gameplay_cover": True,
            "cover_role": "objective",
            "objective": objective_name,
            "side": side,
            "footprint_radius": radius * 1.15,
            "rot_z": yaw_deg,
        })


def _repair_known_cover_contacts(ctx):
    """Repair exact inherited contacts reported by the v0.6.1 auditor."""
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
    """Create two controlled cover pieces around each of the five objectives."""
    scale = float(ctx.config.get("ground_half_size", 100.0)) / 100.0
    radius = ctx.config.get("objective_cover_radius", 1.35 * scale)
    height = ctx.config.get("objective_cover_height", 2.25 * scale)
    tangent = ctx.config.get("objective_cover_tangent_offset", 8.5 * scale)
    inward = ctx.config.get("objective_cover_inward_offset", -2.5 * scale)
    built = []

    for pname in RING_NODES:
        point = ctx.layout[pname]
        for side, sign in (("West", -1.0), ("East", 1.0)):
            built.append(_make_cover(
                ctx, "ObjectiveCover_{}_{}".format(pname, side), pname, point,
                sign * tangent, inward, radius, height,
                90.0 if sign < 0 else -90.0, side))
    return built


def run_gameplay_cover_pass(ctx):
    """Run repairs first, then add objective cover."""
    _repair_known_cover_contacts(ctx)
    built = generate_objective_cover(ctx)
    return {
        "objective_cover_count": len(built),
        "objectives_covered": len(RING_NODES),
        "deterministic_seed": int(ctx.config.get("seed", 1337)),
    }
