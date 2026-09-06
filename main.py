"""
AetherFlow :: main.py  (v0.6.1)

THIN ENTRY POINT.  All generation lives in core.pipeline — main.py only:
  1. locates the project root (NO hardcoded machine paths),
  2. puts it on sys.path,
  3. reloads editable geometry modules for iterative Blender runs,
  4. calls core.pipeline.run_pipeline().

Project-root discovery is intentionally independent from the Blender install
folder and supports scripts opened from Blender's Text Editor.
"""
import importlib
import os
import sys

_MARKER = os.path.join("core", "config.py")


def _is_project_dir(path):
    return bool(path) and os.path.isdir(path) and os.path.isfile(os.path.join(path, _MARKER))


def _walk_up(start_dir, probed):
    try:
        p = os.path.abspath(os.path.realpath(start_dir))
    except (OSError, ValueError):
        return None
    while True:
        if p not in probed:
            probed.append(p)
        if _is_project_dir(p):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            return None
        p = parent


def _candidate_starts():
    starts = []

    def add_file(path):
        try:
            d = os.path.dirname(os.path.abspath(os.path.realpath(path)))
            if d and os.path.isdir(d):
                starts.append(d)
        except (OSError, ValueError):
            pass

    try:
        add_file(__file__)
    except NameError:
        pass

    try:
        import bpy
        texts = []
        try:
            if bpy.context.edit_text is not None:
                texts.append(bpy.context.edit_text)
        except Exception:
            pass
        try:
            space = bpy.context.space_data
            if space is not None and getattr(space, "text", None) is not None:
                texts.append(space.text)
        except Exception:
            pass
        try:
            texts.extend(bpy.data.texts)
        except Exception:
            pass
        for t in texts:
            fp = getattr(t, "filepath", "") or ""
            if fp and os.path.isfile(fp):
                add_file(fp)
    except Exception:
        pass

    try:
        import bpy
        blend = bpy.data.filepath or ""
        if blend and os.path.isfile(blend):
            add_file(blend)
    except Exception:
        pass

    for arg in sys.argv:
        if isinstance(arg, str) and arg.lower().endswith(".py") and os.path.isfile(arg):
            add_file(arg)

    for p in list(sys.path):
        if p and os.path.isdir(p):
            try:
                starts.append(os.path.abspath(os.path.realpath(p)))
            except (OSError, ValueError):
                pass

    starts.append(os.getcwd())
    return starts


def _find_project_root():
    probed = []
    for start in dict.fromkeys(_candidate_starts()):
        found = _walk_up(start, probed)
        if found:
            return found, probed
    return None, probed


PROJECT_ROOT, _PROBED = _find_project_root()

if PROJECT_ROOT is None:
    shown = "\n".join("  - " + p for p in _PROBED[:24])
    raise RuntimeError(
        "[CRITICAL] Cannot detect AetherFlow project root.\n\n"
        "Searched (each entry AND all of its parent directories):\n" + shown +
        "\n\nA project root is any directory containing core" + os.sep + "config.py.\n"
        "How to fix:\n"
        "  * In the Blender Scripting editor use Open... and select the REAL\n"
        "    main.py from the project folder (a pasted Text Block has no\n"
        "    filepath and cannot be resolved), or\n"
        "  * open a .blend that lies inside the project folder, or\n"
        "  * run blender --background <project>" + os.sep + "AetherFlow.blend"
        " --python <project>" + os.sep + "main.py"
    )

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print()
print("=" * 60)
print("AETHER FLOW PROJECT ROOT:")
print(PROJECT_ROOT)
print("=" * 60)

import core.pipeline  # noqa: E402
import geometry.structures  # noqa: E402

# Blender keeps imported Python modules cached. Explicitly reload the edited
# geometry module so rerunning the real main.py immediately uses the curved
# road implementation without restarting Blender.
geometry.structures = importlib.reload(geometry.structures)
core.pipeline = importlib.reload(core.pipeline)
# pipeline imports the same module object, now containing the refreshed code.


def run():
    return core.pipeline.run_pipeline()


if __name__ == "__main__":
    run()
