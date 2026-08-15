import bpy
from mathutils import Vector

def audit_traversal_metrics(ctx):
    layout = getattr(ctx, "layout", {})
    
    # Безопасное получение векторов с дефолтными значениями
    blue_base = layout.get("BlueBase", Vector((0.0, -88.0, 0.0)))
    red_base = layout.get("RedBase", Vector((0.0, 88.0, 0.0)))
    altar = layout.get("Altar", Vector((0.0, 0.0, 0.0)))
    
    if blue_base is None: blue_base = Vector((0.0, -88.0, 0.0))
    if red_base is None: red_base = Vector((0.0, 88.0, 0.0))
    if altar is None: altar = Vector((0.0, 0.0, 0.0))

    dist_blue = (altar - blue_base).length
    dist_red = (altar - red_base).length

    print(f"[AUDIT] Blue Base to Altar Distance: {dist_blue:.2f}m")
    print(f"[AUDIT] Red Base to Altar Distance: {dist_red:.2f}m")
    print(f"[AUDIT] Path Symmetry Delta: {abs(dist_blue - dist_red):.2f}m")