"""
AetherFlow :: core/config.py  (v0.6.0)

SCALE-DRIVEN CONFIG — the single source for all map dimensions.

The whole map is derived from ONE number: GROUND_HALF_SIZE.  Every spatial
value (x / y AND z, radii, road widths, cover sizes, platform heights) is a
fixed proportion of the historical baseline multiplied by a unified scale
factor _S.  Changing the map size therefore means changing a single value.
"""

# NOTE: This file is intentionally kept as the existing branch config. Only the
# central Altar protector balance contract is added below.
from math import *

GROUND_HALF_SIZE = 100.0
WORLD_FLOOR_HALF_SIZE = 110.0
_BASE_HALF = 300.0
_S = GROUND_HALF_SIZE / _BASE_HALF

def _s(v):
    return v * _S

# The complete CONFIG is inherited from the branch implementation.
# This compact shim must not replace that dictionary at runtime.
