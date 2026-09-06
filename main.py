"""AetherFlow Blender entry point."""
import importlib
import os
import sys

_MARKER = os.path.join("core", "config.py")

def _find_project_root():
    starts = []
    try:
        starts.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    try:
        import bpy
        if bpy.data.filepath:
            starts.append(os.path.dirname(os.path.abspath(bpy.data.filepath)))
        for t in list(bpy.data.texts):
            fp = getattr(t, "filepath", "") or ""
            if fp:
                starts.append(os.path.dirname(os.path.abspath(fp)))
    except Exception:
        pass
    starts.extend(p for p in sys.path if p and os.path.isdir(p))
    starts.append(os.getcwd())
    for start in dict.fromkeys(starts):
        p = os.path.abspath(start)
        while True:
            if os.path.isfile(os.path.join(p, _MARKER)):
                return p
            parent = os.path.dirname(p)
            if parent == p:
                break
            p = parent
    raise RuntimeError("[CRITICAL] Cannot detect AetherFlow project root")

PROJECT_ROOT = _find_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("=" * 60)
print("AETHER FLOW PROJECT ROOT:")
print(PROJECT_ROOT)
print("=" * 60)

import core.pipeline
import geometry.structures
import geometry.pockets
import geometry.boundary
import geometry.crown_sanctum_runtime
import geometry.map_v064_runtime
import core.world_silhouette
import core.environment_perimeter

geometry.structures = importlib.reload(geometry.structures)
geometry.pockets = importlib.reload(geometry.pockets)
geometry.boundary = importlib.reload(geometry.boundary)
geometry.crown_sanctum_runtime = importlib.reload(geometry.crown_sanctum_runtime)
geometry.map_v064_runtime = importlib.reload(geometry.map_v064_runtime)
core.world_silhouette = importlib.reload(core.world_silhouette)
core.environment_perimeter = importlib.reload(core.environment_perimeter)

KEEP_MIN, KEEP_MAX = 5, 24


def _remove_named_objects(ctx, names):
    """Remove only explicit legacy props without touching gameplay structures."""
    import bpy
    targets = set(names)
    removed = []
    for obj in list(bpy.data.objects):
        if obj.name in targets:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    if ctx is not None and hasattr(ctx, "generated_objects") and removed:
        removed_set = set(removed)
        ctx.generated_objects[:] = [
            rec for rec in ctx.generated_objects
            if str(rec.get("name", "")) not in removed_set
        ]
    return removed


def _install_pocket_opening():
    original = geometry.pockets._build_rock_arc
    if getattr(original, "_aetherflow_opening", False):
        return
    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        if not isinstance(result, tuple) or len(result) != 3:
            return result
        arc_objs, arc_keep, metrics = result
        kept, kept_keep, removed_names = [], [], []
        for ordinal, (obj, keep) in enumerate(zip(arc_objs, arc_keep), start=1):
            name = getattr(obj, "name", "")
            if KEEP_MIN <= ordinal <= KEEP_MAX:
                kept.append(obj); kept_keep.append(keep)
            else:
                removed_names.append(name)
                try:
                    import bpy
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass
        ctx = args[0] if args else kwargs.get("ctx")
        if ctx is not None and hasattr(ctx, "generated_objects") and removed_names:
            removed = set(removed_names)
            ctx.generated_objects[:] = [r for r in ctx.generated_objects if r.get("name") not in removed]
        m = dict(metrics or {})
        m["segment_count"] = len(kept)
        m["opening"] = "ArcRock24 -> ArcRock05"
        m["opening_removed"] = removed_names
        return kept, kept_keep, m
    wrapper._aetherflow_opening = True
    geometry.pockets._build_rock_arc = wrapper


def _install_crown_sanctum():
    original = geometry.structures.generate_capture_points
    if getattr(original, "_aetherflow_crown_sanctum", False):
        return
    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        ctx = args[0] if args else kwargs.get("ctx")
        if ctx is not None:
            geometry.crown_sanctum_runtime.generate(ctx)
            # Crown Sanctum should keep the architectural half-coliseum, rise,
            # and boss button, but not the four legacy flanking pillar props.
            try:
                import bpy
                for obj in list(bpy.data.objects):
                    if obj.name.startswith("Crown_ColiseumPillar"):
                        bpy.data.objects.remove(obj, do_unlink=True)
                if hasattr(ctx, "generated_objects"):
                    ctx.generated_objects[:] = [
                        rec for rec in ctx.generated_objects
                        if not str(rec.get("name", "")).startswith("Crown_ColiseumPillar")
                    ]
            except Exception:
                pass
            removed_turret = _remove_named_objects(ctx, {"Turret_Crown"})
            if removed_turret:
                print("  -> removed unwanted Crown turret: {}".format(removed_turret))
        return result
    wrapper._aetherflow_crown_sanctum = True
    geometry.structures.generate_capture_points = wrapper


def _install_base_prop_cleanup():
    original = geometry.structures.generate_bases
    if getattr(original, "_aetherflow_base_prop_cleanup", False):
        return
    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        ctx = args[0] if args else kwargs.get("ctx")
        if ctx is not None:
            removed = _remove_named_objects(ctx, {"Blue_Shop", "Red_Shop", "Blue_Shop.001", "Red_Shop.001"})
            if removed:
                print("  -> removed unwanted base shops: {}".format(removed))
        return result
    wrapper._aetherflow_base_prop_cleanup = True
    geometry.structures.generate_bases = wrapper


def _install_v064_map_patches():
    geometry.map_v064_runtime.install_outer_boundary_crown_opening(geometry.boundary)


def _install_viz01():
    """Append VIZ-01 and V0.6.4.3 visual generation after the perimeter pass."""
    original = geometry.boundary.generate_outer_boundary
    if getattr(original, "_aetherflow_viz01", False):
        return
    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        ctx = args[0] if args else kwargs.get("ctx")
        if ctx is not None:
            viz = core.world_silhouette.generate_world_silhouette(ctx)
            env = core.environment_perimeter.generate_environment_perimeter(ctx)
            if isinstance(result, dict):
                result["viz01"] = viz
                result["v0643_environment"] = env
        return result
    wrapper._aetherflow_viz01 = True
    geometry.boundary.generate_outer_boundary = wrapper

_install_pocket_opening()
_install_crown_sanctum()
_install_base_prop_cleanup()
_install_v064_map_patches()
_install_viz01()
core.pipeline = importlib.reload(core.pipeline)

print("[POCKET OPENING] PATCH ACTIVE: ArcRock01-04 + ArcRock25-28 removed")
print("[CROWN SANCTUM] PATCH ACTIVE: smooth rise + boss button + ruined half-coliseum")
print("[v0.6.4] PATCH ACTIVE: obsolete central cube cleanup + Crown outer-wall opening")
print("[VIZ-01] PATCH ACTIVE: mirrored macro world silhouette, non-blocking")
print("[V0.6.4.1] RESOURCE FOUNDATION: loaded by core.pipeline as Stage 6C")
print("[V0.6.4.3] ENVIRONMENT + PERIMETER: visual-only perimeter formations + Crown/Core landmarks")
print("[LEGACY PROPS] PATCH ACTIVE: Turret_Crown + Blue_Shop + Red_Shop removed")

def run():
    geometry.map_v064_runtime.remove_obsolete_central_cube()
    return core.pipeline.run_pipeline()

if __name__ == "__main__":
    run()
