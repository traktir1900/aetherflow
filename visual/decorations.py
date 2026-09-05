import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.utils import finalize_bmesh
from geometry.roads import create_height_adapted_road

def generate_speed_shrines_with_offset(ctx):
    cfg = ctx.config
    shrine_configs = [
        ("Blue", ctx.layout["BlueBase"], ctx.layout["SWMonolith"]),
        ("Red", ctx.layout["RedBase"], ctx.layout["SEMonolith"]),
    ]

    for team, p_base, p_target in shrine_configs:
        mid_point = (p_base + p_target) / 2.0
        road_dir = (p_target - p_base).normalized()
        base_direction = Vector((p_base.x, p_base.y, 0.0)).normalized()
        
        perp_outward = Vector((-road_dir.y, road_dir.x, 0.0))
        if perp_outward.dot(base_direction) < 0:
            perp_outward *= -1.0

        shrine_pos = mid_point + perp_outward * cfg["shrine_road_offset"]
        shrine_pos.z = get_height_at_point(shrine_pos, cfg, ctx.layout)

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=cfg["speed_shrine_radius"], depth=0.3)
        bmesh.ops.translate(bm, verts=bm.verts, vec=shrine_pos + Vector((0, 0, 0.15)))
        finalize_bmesh(bm, f"SpeedShrine_{team}", "Decorations", ctx.get_material("shrine"), ctx)

        create_height_adapted_road(f"ShrinePath_{team}", mid_point, shrine_pos, 4.0, ctx.get_material("road"), ctx)

def generate_3_health_relics(ctx):
    cfg = ctx.config
    crown_dir_outward = Vector((ctx.layout["Crown"].x, ctx.layout["Crown"].y, 0.0)).normalized()
    crown_relic_pos = ctx.layout["Crown"] + crown_dir_outward * (cfg["capture_platform_radius"] + 3.5)

    relic_locations = [
        ("SouthRift", ctx.layout["SouthRift"]),
        ("AetherCore", ctx.layout["Center"]),
        ("CrownApex", crown_relic_pos),
    ]

    for name, pos in relic_locations:
        z = max(get_height_at_point(pos, cfg, ctx.layout), cfg["heights"]["Crown"]) if name == "CrownApex" else get_height_at_point(pos, cfg, ctx.layout)
        r_pos = Vector((pos.x, pos.y, z))

        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=cfg["health_relic_radius"], depth=0.4)
        bmesh.ops.translate(bm, verts=bm.verts, vec=r_pos + Vector((0, 0, 0.2)))
        finalize_bmesh(bm, f"HealthRelic_{name}", "Decorations", ctx.get_material("relic"), ctx)
