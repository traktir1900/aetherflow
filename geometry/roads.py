import bmesh
from mathutils import Vector
from core.heightmap import get_height_at_point
from core.layout import RING_NODES, polar
from core.utils import finalize_bmesh

def create_height_adapted_road(name, p0, p1, width, material, ctx):
    cfg = ctx.config
    length = (p1 - p0).length
    steps = max(4, int(length / 4.0))

    flat_dir = Vector((p1.x - p0.x, p1.y - p0.y, 0.0)).normalized()
    perp_vec = Vector((-flat_dir.y, flat_dir.x, 0.0)) * (width / 2.0)

    bm = bmesh.new()
    prev_left, prev_right = None, None

    for i in range(steps + 1):
        t = i / steps
        curr_center = p0 + (p1 - p0) * t
        
        left_pos = curr_center - perp_vec
        right_pos = curr_center + perp_vec

        left_pos.z = get_height_at_point(left_pos, cfg, ctx.layout) + cfg["road_z_offset"]
        right_pos.z = get_height_at_point(right_pos, cfg, ctx.layout) + cfg["road_z_offset"]

        v_left = bm.verts.new(left_pos)
        v_right = bm.verts.new(right_pos)

        if prev_left and prev_right:
            bm.faces.new((prev_left, prev_right, v_right, v_left))

        prev_left, prev_right = v_left, v_right

    finalize_bmesh(bm, name, "Roads", material, ctx)

def generate_roads(ctx):
    cfg = ctx.config
    mat_road = ctx.get_material("road")
    for i in range(len(RING_NODES)):
        a, b = RING_NODES[i], RING_NODES[(i + 1) % len(RING_NODES)]
        create_height_adapted_road(f"RingRoad_{a}_{b}", ctx.layout[a], ctx.layout[b], cfg["ring_road_width"], mat_road, ctx)

    create_height_adapted_road("BaseRoad_Blue_SW", ctx.layout["BlueBase"], ctx.layout["SWMonolith"], cfg["base_road_width"], mat_road, ctx)
    create_height_adapted_road("BaseRoad_Red_SE", ctx.layout["RedBase"], ctx.layout["SEMonolith"], cfg["base_road_width"], mat_road, ctx)

    crown_pos = ctx.layout["Crown"]
    core_north_gate = polar(cfg["center_radius"], 90.0)
    create_height_adapted_road("North_Ramp_Crown_Core", crown_pos, core_north_gate, cfg["north_ramp_width"], mat_road, ctx)
