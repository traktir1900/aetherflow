"""AetherFlow V0.6.4.3 — Environment + Perimeter.

All reviewed-out environment accents are disabled. This module keeps the
entry point intact but does not generate perimeter spires, height ridges,
Crown approach landmarks, or AetherCore frame/core landmarks.
"""


def generate_environment_perimeter(ctx):
    """Return an empty environment-perimeter pass; gameplay geometry untouched."""
    cfg = ctx.config.get("environment_perimeter", {})
    if not cfg.get("enabled", True):
        return {"enabled": False, "objects": [], "symmetry_passed": True, "max_error_m": 0.0}

    print(
        "  -> V0.6.4.3 environment perimeter: objects=0 | perimeter_spires=0 | "
        "height_ridges=0 | crown_landmarks=0 | core_landmarks=0 | symmetry=PASS | "
        "max_error=0.000000m"
    )
    return {
        "enabled": True,
        "objects": [],
        "symmetry_passed": True,
        "max_error_m": 0.0,
        "perimeter_spires": 0,
        "height_ridges": 0,
        "crown_landmarks": 0,
        "core_landmarks": 0,
        "north_frame": 0,
    }
