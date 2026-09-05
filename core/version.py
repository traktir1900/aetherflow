"""
AetherFlow :: core/version.py
Single source of truth for the project version.

Reads VERSION.txt at the project root. Every banner / report must use
get_version() instead of hardcoding a version string, so there is exactly
one version across the pipeline.
"""
import os

VERSION_FILE = "VERSION.txt"
_FALLBACK = "0.6.1"
_cache = None


def _find_project_root():
    """Locate the directory that contains VERSION.txt (core/ -> parent)."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.dirname(here)  # core/.. == project root
    if os.path.isfile(os.path.join(candidate, VERSION_FILE)):
        return candidate
    # Fallback: walk up a couple of levels.
    probe = here
    for _ in range(3):
        if os.path.isfile(os.path.join(probe, VERSION_FILE)):
            return probe
        probe = os.path.dirname(probe)
    return None


def get_version():
    """Return the version string from VERSION.txt (cached)."""
    global _cache
    if _cache is not None:
        return _cache
    root = _find_project_root()
    if root is None:
        _cache = _FALLBACK
        return _cache
    try:
        with open(os.path.join(root, VERSION_FILE), "r", encoding="utf-8") as f:
            _cache = f.read().strip() or _FALLBACK
    except OSError:
        _cache = _FALLBACK
    return _cache


def banner(title="AETHER FLOW PIPELINE"):
    v = get_version()
    line = "=" * 70
    return "\n".join([line, ">>> {} :: v{} <<<".format(title, v), line])
