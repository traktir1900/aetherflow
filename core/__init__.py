"""AetherFlow core package bootstrap."""

# v0.6.3.2 pocket opening guard.
# Keep the existing pocket geometry and its location, but make the FRONT opening
# explicit at the geometry source level: retain only ArcRock05..ArcRock24 and
# remove ArcRock01..04 + ArcRock25..28. This is intentionally installed from
# core package import so it also works with older Blender entry-point scripts
# that do not contain the newer main.py wrapper. The same source pocket is used
# for each mirror pair, so gameplay symmetry remains exact.

def _install_pocket_arc_opening_guard():
    try:
        import geometry.pockets as _pockets
        import bpy
    except Exception:
        return

    original = getattr(_pockets, "_build_rock_arc", None)
    if original is None or getattr(original, "_aetherflow_opening_guard", False):
        return

    keep_start = 5
    keep_end = 24

    def _build_rock_arc_guard(*args, **kwargs):
        result = original(*args, **kwargs)
        try:
            arc_objs, arc_keep, metrics = result
        except (TypeError, ValueError):
            return result

        kept_objs = []
        kept_keep = []
        removed = []
        for ordinal, (obj, keep) in enumerate(zip(arc_objs, arc_keep), start=1):
            if keep_start <= ordinal <= keep_end:
                kept_objs.append(obj)
                kept_keep.append(keep)
            else:
                removed.append(obj)

        if not removed:
            return result

        for obj in removed:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass

        ctx = args[0] if args else None
        removed_ids = {id(obj) for obj in removed}
        if ctx is not None and hasattr(ctx, "generated_objects"):
            ctx.generated_objects[:] = [
                rec for rec in ctx.generated_objects
                if id(rec.get("object")) not in removed_ids
            ]

        new_metrics = dict(metrics or {})
        new_metrics["segment_count"] = len(kept_objs)
        new_metrics["opening"] = "ArcRock24 -> ArcRock05"
        new_metrics["opening_removed"] = [getattr(obj, "name", "") for obj in removed]
        new_metrics["opening_guard"] = "ACTIVE"
        return kept_objs, kept_keep, new_metrics

    _build_rock_arc_guard._aetherflow_opening_guard = True
    _pockets._build_rock_arc = _build_rock_arc_guard


_install_pocket_arc_opening_guard()
