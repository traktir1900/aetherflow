#!/usr/bin/env python3
"""
AetherFlow :: tests/run_tests.py  (v0.6.4)

Engine-free automated tests.  Run with plain Python 3 (no Blender needed):

    python3 tests/run_tests.py

Covers: config scale, version source of truth, layout (5/5), heightmap
safety/determinism, navigation (obstacles + reachability), simulation
(5/5, real cover_usage, determinism, nav-driven), validation (all error
classes), export (map_data.json contract), and hygiene guards
(no hardcoded roots, no global random).

Modules that require bpy/bmesh (terrain mesh, structures, rocks, pipeline)
are NOT exercised here — those need the real Blender run.
"""
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# mathutils stub FIRST, then the project root.
sys.path.insert(0, os.path.join(HERE, "mathutils_stub"))
sys.path.insert(0, ROOT)

from core.config import CONFIG, GROUND_HALF_SIZE          # noqa: E402
from core import version as version_mod                   # noqa: E402
from core.layout import RING_NODES, BASES, build_layout, capture_point_names  # noqa: E402
from core.heightmap import get_height_at_point            # noqa: E402
from core.context import MapContext                       # noqa: E402
from core.navigation import NavGrid, build_grid, run_navigation_checks  # noqa: E402
from core.validation import run_validation, validate_pocket_fairness   # noqa: E402
from core.export import build_map_data, write_map_data    # noqa: E402
from core.ue5_export import build_manifest, export_group_for_record  # noqa: E402
from combat.simulation import run_simulation              # noqa: E402
from mathutils import Vector                              # noqa: E402

RESULTS = []


def check(group, name, cond, detail=""):
    RESULTS.append((group, name, bool(cond), detail))
    mark = "PASS" if cond else "FAIL"
    line = "  [{}] {} :: {}".format(mark, group, name)
    if detail and not cond:
        line += "  -- " + str(detail)
    print(line)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
class FakeObj:
    def __init__(self, x, y, z, name="obj"):
        self.location = Vector((x, y, z))
        self.rotation_euler = [0.0, 0.0, 0.0]
        self.scale = [1.0, 1.0, 1.0]
        self.name = name


class FakeCtx:
    def __init__(self, config=None):
        self.config = config if config is not None else CONFIG
        self.layout = build_layout(self.config)
        self.generated_objects = []
        self.pockets = []
        self.materials = {}
        self.collections = {}

    def add(self, name, kind, x, y, z, dims=None, meta=None):
        rec = {
            "object": FakeObj(x, y, z, name),
            "name": name,
            "type": kind,
            "dimensions": dims,
            "meta": meta or {},
        }
        self.generated_objects.append(rec)
        return rec


def good_scene():
    """A minimal but complete valid map record set."""
    ctx = FakeCtx()
    cfg = ctx.config
    for p in RING_NODES:
        pos = ctx.layout[p]
        ctx.add("CapturePlatform_" + p, "capture_point", pos.x, pos.y, 0.0,
                dims=(cfg["capture_platform_radius"] * 2,) * 2 + (cfg["capture_platform_height"],),
                meta={"point": p, "radius": cfg["capture_platform_radius"],
                      "height": cfg["capture_platform_height"]})
    for team, key in (("Blue", "BlueBase"), ("Red", "RedBase")):
        pos = ctx.layout[key]
        ctx.add(team + "_BasePlatform", "base", pos.x, pos.y, 0.0,
                dims=(cfg["base_platform_radius"] * 2,) * 2 + (cfg["base_platform_height"],),
                meta={"team": team, "radius": cfg["base_platform_radius"]})
    ctx.add("Altar_Base", "altar", 0.0, 0.0, -0.5, dims=(3.0, 3.0, 0.3),
            meta={"landmark": "AetherAltar"})
    ctx.add("Altar_PowerCore", "altar", 0.0, 0.0, 0.0, dims=(0.9, 0.9, 0.9),
            meta={"landmark": "AetherCrown"})
    ctx.add("Terrain_Real", "terrain", 0.0, 0.0, -0.3, dims=(220.0, 220.0, None),
            meta={"resolution": 130})
    ctx.add("Terrain_SafetyFloor", "safety_floor", 0.0, 0.0, -2.5,
            dims=(240.0, 240.0, 1.0))
    ctx.add("Core_Cover_Pillar_North", "cover", 0.0, 2.5, -0.4,
            dims=(2.1, 2.1, 2.9), meta={"rot_z": 0.0})
    ctx.add("RingRoad_Crown_EastMonolith", "road", 20.0, 40.0, 0.1,
            dims=(4.0, 30.0, None))
    ctx.add("Ramp_Crown", "ramp", 0.0, 55.0, 0.3, dims=(2.4, 8.0, 0.5),
            meta={"graded": True, "slope_deg": 12.0, "point": "Crown"})
    ctx.add("Core_Rock_01", "rock", 30.0, 0.0, 0.2, dims=(2.0, 2.0, 1.6),
            meta={"footprint_radius": 1.0})
    # Minimal mirrored pocket metadata so the validation fixture matches the
    # current 0.6.1 contract (four required pockets).
    for name, capture, mirror, cx, sy in (
        ("WestPocket", "WestMonolith", "EastPocket", -40.0, 35.0),
        ("EastPocket", "EastMonolith", "WestPocket", 40.0, 35.0),
        ("SWPocket", "SWMonolith", "SEPocket", -40.0, -15.0),
        ("SEPocket", "SEMonolith", "SWPocket", 40.0, -15.0),
    ):
        ctx.pockets.append({
            "name": name, "capture_point": capture, "mirror_pair": mirror,
            "location": [cx, sy, 0.0], "dimensions": [28.0, 18.0],
            "bounds": {"min": [cx - 14.0, sy - 9.0], "max": [cx + 14.0, sy + 9.0]},
            "entry": {"width": 10.0, "point": [cx, sy - 9.0, 0.0], "side": "inward"},
            "exits": [{"width": 10.0}], "cover": [name + "_C1", name + "_C2", name + "_C3"],
            "cover_positions": [
                [cx - 5.0, sy + 1.0, 1.0], [cx + 5.0, sy + 1.0, 1.0], [cx, sy + 4.0, 1.0]
            ],
            "height_range": [0.0, 5.0], "floor_area": 415.9,
            "perimeter_continuous": True,
        })
    return ctx


# ---------------------------------------------------------------------------
# T1 — config & unified scale
# ---------------------------------------------------------------------------
def t1_config():
    g = "T1 config"
    check(g, "GROUND_HALF_SIZE == 100 (200x200 m)", GROUND_HALF_SIZE == 100.0)
    cfg = CONFIG
    check(g, "config ground_half_size", cfg["ground_half_size"] == 100.0)
    check(g, "config world floor 220", cfg.get("world_floor_half_size") == 110.0)
    check(g, "outer_ring_radius scaled", abs(cfg["outer_ring_radius"] - 137.5 / 3.0) < 1e-9)
    check(g, "Crown height scaled", abs(cfg["heights"]["Crown"] - 0.5) < 1e-9)
    check(g, "AetherCore scaled", abs(cfg["heights"]["AetherCore"] + 2.0 / 3.0) < 1e-9)
    check(g, "safety floor scaled", abs(cfg["safety_floor_z"] + 2.0) < 1e-9)
    check(g, "platform radius uses gameplay geometry scale",
          abs(cfg["capture_platform_radius"] - (20.0 / 3.0 * 0.4)) < 1e-9)
    # every top-level spatial scalar must fit the 200x200 map
    skip = {"terrain_resolution", "circle_segments", "seed", "base_spread_deg",
            "debug_sightlines", "world_floor_half_size"}
    bad = []
    for k, v in cfg.items():
        if k in skip or isinstance(v, (dict, bool)):
            continue
        if isinstance(v, (int, float)) and abs(v) > 100.0:
            bad.append((k, v))
    check(g, "no oversized scalar keys", not bad, str(bad))


# ---------------------------------------------------------------------------
# T2 — version single source of truth
# ---------------------------------------------------------------------------
def t2_version():
    g = "T2 version"
    v = version_mod.get_version()
    check(g, "version == 0.6.4.0", v == "0.6.4.0", v)
    with open(os.path.join(ROOT, "VERSION.txt"), "r", encoding="utf-8") as f:
        check(g, "matches VERSION.txt", f.read().strip() == v)
    check(g, "banner carries version", ("v" + v) in version_mod.banner())


# ---------------------------------------------------------------------------
# T3 — layout: 5/5 points, bases, symmetry
# ---------------------------------------------------------------------------
def t3_layout():
    g = "T3 layout"
    pts = capture_point_names()
    check(g, "exactly 5 capture points", len(pts) == 5 and set(pts) == set(RING_NODES))
    layout = build_layout(CONFIG)
    check(g, "Center at origin", layout["Center"].length < 1e-9)
    crown = layout["Crown"]
    check(g, "Crown on ring radius",
          abs(Vector((crown.x, crown.y, 0)).length - CONFIG["outer_ring_radius"]) < 1e-6)
    check(g, "Crown due north", abs(math.degrees(math.atan2(crown.y, crown.x)) - 90.0) < 1e-6)
    for name, ang in (("EastMonolith", 18.0), ("SEMonolith", 306.0),
                      ("SWMonolith", 234.0), ("WestMonolith", 162.0)):
        p = layout[name]
        got = math.degrees(math.atan2(p.y, p.x)) % 360
        check(g, name + " angle", abs(got - ang) < 1e-6, got)
    b, r = layout["BlueBase"], layout["RedBase"]
    check(g, "bases symmetric", abs(b.x + r.x) < 1e-6 and abs(b.y - r.y) < 1e-6)
    check(g, "base radius", abs(Vector((b.x, b.y, 0)).length - CONFIG["base_radius"]) < 1e-6)
    sr = layout["SouthRift"]
    mid = (layout["SWMonolith"] + layout["SEMonolith"]) / 2.0
    check(g, "SouthRift is SW/SE midpoint", (sr - mid).length < 1e-6)


# ---------------------------------------------------------------------------
# T4 — heightmap: design values, safety floor, no NaN
# ---------------------------------------------------------------------------
def t4_heightmap():
    g = "T4 heightmap"
    cfg = CONFIG
    layout = build_layout(cfg)
    zc = get_height_at_point(Vector((0.0, 0.0, 0.0)), cfg, layout)
    check(g, "center is a raised landform", zc > 0.0, zc)
    zcrown = get_height_at_point(layout["Crown"], cfg, layout)
    check(g, "Crown anchor remains finite", math.isfinite(zcrown), zcrown)
    half = cfg["ground_half_size"]
    mn, mx, bad = float("inf"), float("-inf"), 0
    n = 41
    for i in range(n + 1):
        for j in range(n + 1):
            x = -half + 2 * half * i / n
            y = -half + 2 * half * j / n
            z = get_height_at_point(Vector((x, y, 0.0)), cfg, layout)
            if z != z or z in (float("inf"), float("-inf")):
                bad += 1
                continue
            mn, mx = min(mn, z), max(mx, z)
    check(g, "no NaN/Inf on 41x41 sample", bad == 0, bad)
    check(g, "min >= safety floor", mn >= cfg["safety_floor_z"] - 1e-9, mn)
    check(g, "terrain stays within design height bound", mx < 2.0, mx)


# ---------------------------------------------------------------------------
# T5 — determinism of the engine-free stack
# ---------------------------------------------------------------------------
def t5_determinism():
    g = "T5 determinism"
    cfg = CONFIG

    def sample_field():
        layout = build_layout(cfg)
        out = []
        for i in range(11):
            for j in range(11):
                x = -100 + 20 * i
                y = -100 + 20 * j
                out.append(round(get_height_at_point(Vector((x, y, 0.0)), cfg, layout), 9))
        return out

    check(g, "heightmap repeatable", sample_field() == sample_field())

    layout = build_layout(cfg)
    g1 = NavGrid(cfg, layout, cells=48)
    g2 = NavGrid(cfg, layout, cells=48)
    d1 = g1.path_length(layout["BlueBase"], layout["Crown"])
    d2 = g2.path_length(layout["BlueBase"], layout["Crown"])
    check(g, "nav path repeatable", d1 == d2 and d1 is not None, (d1, d2))

    ctx = FakeCtx()
    ctx.add("Core_Cover_X", "cover", 0.0, 40.8, 0.0, dims=(4.0, 1.0, 2.0),
            meta={"rot_z": 0.0})
    grid = build_grid(ctx, cells=48)
    s1 = json.dumps(run_simulation(ctx, grid), sort_keys=True)
    s2 = json.dumps(run_simulation(ctx, grid), sort_keys=True)
    check(g, "simulation repeatable (no RNG)", s1 == s2)
    rng_a = MapContext(cfg).rng.random()
    rng_b = MapContext(cfg).rng.random()
    check(g, "ctx.rng seeded identically", rng_a == rng_b)


# ---------------------------------------------------------------------------
# T6 — navigation: obstacles really block, reachability 5/5
# ---------------------------------------------------------------------------
def t6_navigation():
    g = "T6 navigation"
    cfg = CONFIG
    layout = build_layout(cfg)
    grid = NavGrid(cfg, layout, cells=64)

    base0 = grid.path_length(layout["BlueBase"], layout["RedBase"])
    check(g, "bases connected (open map)", base0 is not None)

    # partial wall across the actual base-to-base corridor (y ~ -86 at this
    # scale) -> still connected, but strictly longer
    for y in range(-96, -75, 2):
        grid.block_disc(0.0, float(y), 1.0)
    base1 = grid.path_length(layout["BlueBase"], layout["RedBase"])
    check(g, "partial wall forces detour", base1 is not None and base1 > base0,
          (base0, base1))

    # full wall -> unreachable
    grid2 = NavGrid(cfg, layout, cells=64)
    for y in range(-100, 101, 2):
        grid2.block_disc(0.0, float(y), 1.6)
    check(g, "full wall => unreachable",
          grid2.path_length(layout["BlueBase"], layout["RedBase"]) is None)

    # rect blocker hits its own cell
    grid3 = NavGrid(cfg, layout, cells=64)
    grid3.block_rect(0.0, 0.0, 4.0, 4.0, 0.0)
    check(g, "rect blocker blocks centre cell", grid3.cell_of(Vector((0, 0, 0))) in grid3.blocked)

    # full check suite over the clean map: 5/5 objectives, 2/2 bases
    ctx = FakeCtx()
    rep = run_navigation_checks(ctx, NavGrid(cfg, layout, cells=64))
    check(g, "suite ok on clean map", rep["ok"], rep["problems"])
    check(g, "checks all 5 points", rep["checked_points"] == list(RING_NODES))
    check(g, "checks both bases", rep["checked_bases"] == list(BASES))
    check(g, "30 routes evaluated", len(rep["routes"]) == 30, len(rep["routes"]))
    check(g, "no unreachable objectives", not rep["problems"])

    # a blocked objective must be reported
    ctx2 = FakeCtx()
    grid4 = NavGrid(cfg, layout, cells=64)
    crown = layout["Crown"]
    for a in range(0, 360, 6):
        grid4.block_disc(crown.x + 12.0 * math.cos(math.radians(a)),
                         crown.y + 12.0 * math.sin(math.radians(a)), 1.4)
    rep2 = run_navigation_checks(ctx2, grid4)
    check(g, "encircled point reported unreachable", not rep2["ok"] and
          any("Crown" in p for p in rep2["problems"]), rep2["problems"][:3])


# ---------------------------------------------------------------------------
# T7 — simulation: 5/5, real cover_usage, nav-driven
# ---------------------------------------------------------------------------
def t7_simulation():
    g = "T7 simulation"
    ctx = FakeCtx()
    crown = ctx.layout["Crown"]
    ctx.add("Core_Cover_Test", "cover", crown.x, crown.y - 5.0, 0.0,
            dims=(4.0, 1.0, 2.0), meta={"rot_z": 0.0})
    grid = build_grid(ctx, cells=64)

    sim = run_simulation(ctx, grid)
    states = sim["metrics"]["objective_states"]
    check(g, "objective_states has all 5", set(states.keys()) == set(RING_NODES),
          sorted(states.keys()))
    check(g, "zones cover 5 + bases + core",
          set(RING_NODES) | set(BASES) | {"AetherCore"} <= set(sim["zones"].keys()))
    z = sim["zones"]["Crown"]
    check(g, "Crown sees the cover object", z["cover_objects_in_zone"] >= 1, z)
    check(g, "exposure measured (0..1)", 0.0 <= z["exposure"] <= 1.0)
    check(g, "cover blocks >=1 direction", z["covered_fraction"] > 0.0, z)
    check(g, "Crown cover_usage > 0 (real data)", z["cover_usage"] > 0, z)
    check(g, "no fights without traffic",
          all(v["fights"] >= 0 and v["cover_usage"] >= 0 for v in sim["zones"].values()))
    check(g, "first contact nav-driven", sim["meta"]["nav_driven"] is True)
    check(g, "first contact positive", (sim["metrics"]["first_contact_sec"] or 0) > 0)
    check(g, "travel distances for all points",
          all(set(sim["zones"][p]["travel_distance"].keys()) == set(BASES) for p in RING_NODES))

    # cover-free zone => honest zero
    empty = FakeCtx()
    g2 = build_grid(empty, cells=64)
    sim2 = run_simulation(empty, g2)
    far = sim2["zones"]["Crown"]
    check(g, "no cover => cover_usage 0", far["cover_objects_in_zone"] == 0
          and far["cover_usage"] == 0, far)

    # fallback only without nav, and explicitly flagged
    sim3 = run_simulation(ctx, None)
    check(g, "fallback flagged in estimates", len(sim3["meta"]["estimates"]) == 1)


# ---------------------------------------------------------------------------
# T8 — validation error classes
# ---------------------------------------------------------------------------
def t8_validation():
    g = "T8 validation"
    ok = run_validation(good_scene())
    check(g, "clean scene passes", ok["ok"], ok["errors"])

    def expect(name, mutate, needle, nav=None):
        ctx = good_scene()
        mutate(ctx)
        rep = run_validation(ctx, nav_report=nav)
        check(g, name, (not rep["ok"]) and any(needle in e for e in rep["errors"]),
              rep["errors"][:4])

    expect("duplicate names", lambda c: c.add("Terrain_Real", "road", 1, 1, 0,
           dims=(1, 1, 1)), "DUPLICATE OBJECT NAME")
    expect("missing SEMonolith",
           lambda c: [c.generated_objects.remove(r) for r in list(c.generated_objects)
                      if r["meta"].get("point") == "SEMonolith"],
           "MISSING CAPTURE POINT: SEMonolith")
    expect("out of map bounds", lambda c: c.add("Turret_X", "turret", 150.0, 0.0, 0.0,
           dims=(3, 3, 3)), "OUT OF MAP BOUNDS")
    expect("invalid dimensions", lambda c: c.add("Bad_Dims", "rock", 20.0, 20.0, 0.0,
           dims=(-1, 2, 2), meta={"footprint_radius": 1.0}), "INVALID DIMENSIONS")
    expect("NaN transform", lambda c: c.add("NaN_Obj", "rock", float("nan"), 0.0, 0.0,
           dims=(2, 2, 2), meta={"footprint_radius": 1.0}), "INVALID TRANSFORM")
    expect("ramp too steep",
           lambda c: [r["meta"].update({"slope_deg": 60.0}) for r in c.generated_objects
                      if r["type"] == "ramp"],
           "RAMP TOO STEEP")
    crown = build_layout(CONFIG)["Crown"]
    expect("solid blocks capture area",
           lambda c: c.add("Blocker", "cover", crown.x, crown.y, 0.0, dims=(2, 1, 2),
                           meta={"rot_z": 0.0}),
           "BLOCKS CAPTURE AREA")
    expect("missing terrain",
           lambda c: [c.generated_objects.remove(r) for r in list(c.generated_objects)
                      if r["type"] == "terrain"],
           "MISSING TERRAIN")
    expect("missing altar landmarks",
           lambda c: [c.generated_objects.remove(r) for r in list(c.generated_objects)
                      if r["type"] == "altar"],
           "MISSING LANDMARK")
    expect("nav problem propagated", lambda c: None, "NAVIGATION: UNREACHABLE",
           nav={"ok": False, "problems": ["UNREACHABLE: BlueBase->Crown"]})


# ---------------------------------------------------------------------------
# T9 — export contract (map_data.json)
# ---------------------------------------------------------------------------
def t9_export():
    g = "T9 export"
    ctx = good_scene()
    grid = build_grid(ctx, cells=48)
    nav = run_navigation_checks(ctx, grid)
    sim = run_simulation(ctx, grid, nav_report=nav)
    val = run_validation(ctx, nav_report=nav)
    data = build_map_data(ctx, sim=sim, nav=nav, validation=val)

    check(g, "version 0.6.4.0", data["version"] == "0.6.4.0")
    check(g, "map 200x200", data["map"]["width"] == 200.0 and data["map"]["height"] == 200.0)
    check(g, "4 physical capture points with radius/height",
          len(data["capture_points"]) == 4 and
          all("radius" in p and "height" in p and "position" in p
              for p in data["capture_points"]))
    check(g, "Crown is a PvE logical anchor", data["crown"] == {
        "mode": "PVE_LORD_SANCTUM", "logical_anchor": "Crown",
        "position": [0.0, 45.833, 0.0], "capture_button": "CaptureButton_Crown",
        "capture_indicator": "CaptureIndicatorRing_Crown", "boss_button": "Crown_BossButton",
        "physical_capture_platform": None,
    }, data["crown"])
    check(g, "2 bases", len(data["bases"]) == 2)
    check(g, "terrain block", data["terrain"].get("world_floor_half_size") == 110.0 and
          set(data["terrain"].get("anchors", {})) >= {"Center", "Crown"})
    check(g, "buckets populated",
          len(data["roads"]) >= 1 and len(data["ramps"]) >= 1 and
          len(data["cover"]) >= 1 and len(data["rocks"]) >= 1 and
          len(data["landmarks"]) >= 2)
    entry = data["landmarks"][0]
    check(g, "object entries full",
          all(k in entry for k in ("name", "type", "location", "dimensions", "meta")))
    check(g, "simulation embedded 5/5",
          set(data["simulation"]["metrics"]["objective_states"].keys()) == set(RING_NODES))
    check(g, "validation embedded", data["validation"]["ok"] is True)

    tmp = os.path.join(tempfile.mkdtemp(prefix="af_test_"), "map_data.json")
    write_map_data(ctx, tmp, sim=sim, nav=nav, validation=val)
    with open(tmp, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    check(g, "json round-trip", loaded["version"] == "0.6.4.0" and
          len(loaded["capture_points"]) == 4)


# ---------------------------------------------------------------------------
# T10 — hygiene guards
# ---------------------------------------------------------------------------
def t10_hygiene():
    g = "T10 hygiene"
    bad_root, bad_random = [], []
    for sub in ("core", "geometry", "combat", "analysis", "navigation",
                "validators", "visual"):
        d = os.path.join(ROOT, sub)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(d, fn)
            with open(p, "r", encoding="utf-8") as f:
                src = f.read()
            if "HARDCODED_ROOT" in src or "C:/Program" in src or "C:\\Program" in src:
                bad_root.append(p)
            if "random.random(" in src or "random.uniform(" in src:
                bad_random.append(p)
    main_src = open(os.path.join(ROOT, "main.py"), "r", encoding="utf-8").read()
    if "HARDCODED_ROOT" in main_src or "C:/Program" in main_src:
        bad_root.append("main.py")
    check(g, "no hardcoded project root anywhere", not bad_root, bad_root)
    check(g, "no unseeded global random calls", not bad_random, bad_random)
    check(g, "scene reset OFF by default",
          CONFIG["scene"]["allow_scene_reset"] is False)
    check(g, "map stays 200x200", CONFIG["ground_half_size"] == 100.0)


# ---------------------------------------------------------------------------
# T11 — pocket fairness (engine-free, synthetic mirrored data)
# ---------------------------------------------------------------------------
def _synthetic_pocket(name, capture, mirror, cx, cover_x):
    cover = [(cover_x, 1.0, 0.5), (-cover_x, 3.0, 0.5)]
    return {
        "name": name, "capture_point": capture, "mirror_pair": mirror,
        "location": [cx, 14.0, 0.0], "dimensions": [28.0, 18.0],
        "bounds": {"min": [cx - 14.0, 5.0], "max": [cx + 14.0, 23.0]},
        "entry": {"width": 6.0, "point": [cx, 5.0, 0.0], "side": "inward"},
        "exits": [{"width": 6.0}], "cover": ["a", "b"],
        "cover_positions": cover, "height_range": [0.0, 2.6],
        "tactical_role": "flank_cover",
    }


def t11_pocket_fairness():
    g = "T11 pockets"
    cfg = CONFIG
    nav = [{"name": "WestPocket", "capture_point": "WestMonolith", "mirror_pair": "EastPocket",
            "reachable": True, "route_length": 30.0},
           {"name": "EastPocket", "capture_point": "EastMonolith", "mirror_pair": "WestPocket",
            "reachable": True, "route_length": 30.0},
           {"name": "SWPocket", "capture_point": "SWMonolith", "mirror_pair": "SEPocket",
            "reachable": True, "route_length": 40.0},
           {"name": "SEPocket", "capture_point": "SEMonolith", "mirror_pair": "SWPocket",
            "reachable": True, "route_length": 40.0}]

    west = _synthetic_pocket("WestPocket", "WestMonolith", "EastPocket", -66.5, 5.0)
    east = _synthetic_pocket("EastPocket", "EastMonolith", "WestPocket", 66.5, 5.0)
    # east is the exact mirror of west: negate x of location & cover
    east["location"][0] = -west["location"][0]
    east["cover_positions"] = [(-x, y, z) for (x, y, z) in west["cover_positions"]]
    sw = _synthetic_pocket("SWPocket", "SWMonolith", "SEPocket", -34.0, 4.0)
    se = _synthetic_pocket("SEPocket", "SEMonolith", "SWPocket", 34.0, 4.0)
    se["location"][0] = -sw["location"][0]
    se["cover_positions"] = [(-x, y, z) for (x, y, z) in sw["cover_positions"]]

    # Exactly 4 side pockets — the Crown area has NO pocket (STEP 1 final).
    pockets = [west, east, sw, se]
    errs, warns = validate_pocket_fairness(pockets, cfg, nav)
    check(g, "4 symmetric pockets -> no fairness errors", not errs, errs)

    # break mirror symmetry -> must produce an error
    broken = _synthetic_pocket("EastPocket", "EastMonolith", "WestPocket", 66.5, 5.0)
    broken["location"][0] = -west["location"][0]
    broken["cover_positions"] = [(-x + 2.0, y, z) for (x, y, z) in west["cover_positions"]]
    errs2, _ = validate_pocket_fairness([west, broken, sw, se], cfg, nav)
    check(g, "broken mirror detected", any("FAIRNESS" in e for e in errs2), errs2)

    # unreachable pocket -> error
    bad_nav = [dict(nav[0], reachable=False)] + nav[1:]
    errs3, _ = validate_pocket_fairness(pockets, cfg, bad_nav)
    check(g, "unreachable pocket detected", any("REACHABLE" in e for e in errs3), errs3)

    # export must carry exactly the 4 pockets (no CrownPocket)
    ctx = FakeCtx()
    ctx.pockets = pockets
    data = build_map_data(ctx)
    check(g, "export includes 4 pockets, no CrownPocket",
          len(data.get("pockets", [])) == 4 and
          all(p["name"] != "CrownPocket" for p in data.get("pockets", [])))


# ---------------------------------------------------------------------------
# T12 — gameplay cover optimiser (engine-free, pure math)
# ---------------------------------------------------------------------------
def t12_pocket_traffic():
    g = "T12 pocket traffic"
    ctx = good_scene()
    cfg = ctx.config
    for name, capture, mirror, cx in (
        ("SWPocket", "SWMonolith", "SEPocket", -48.5),
        ("SEPocket", "SEMonolith", "SWPocket", 48.5),
    ):
        ctx.pockets.append({
            "name": name, "capture_point": capture, "mirror_pair": mirror,
            "location": [cx, -15.8, 0.0], "cover": [],
            "height_range": [0.0, 5.0],
        })
    nav = {
        "pockets": [
            {"name": "SWPocket", "reachable": True, "route_length": 37.5},
            {"name": "SEPocket", "reachable": True, "route_length": 37.5},
        ],
        "chokepoints": [],
    }
    grid = build_grid(ctx, cells=64)
    sim = run_simulation(ctx, grid, nav_report=nav)
    sw = sim["zones"]["SWPocket"]
    se = sim["zones"]["SEPocket"]
    check(g, "reachable mirrored pockets get nonzero traffic", sw["traffic"] > 0 and se["traffic"] > 0, (sw["traffic"], se["traffic"]))
    check(g, "mirrored pocket traffic is equal", sw["traffic"] == se["traffic"], (sw["traffic"], se["traffic"]))
    check(g, "pocket traffic records route state", sw["reachable"] and se["reachable"], (sw["reachable"], se["reachable"]))


def t12_cover_optimiser():
    g = "T12 cover"
    from core.cover_analysis import optimize_cover, _key_points, _footprint
    from core.cover_analysis import los_blocked_fraction

    ccfg = CONFIG["pockets"]["cover"]
    W, D, t = 28.0, 18.0, 1.4

    specs, stats = optimize_cover(W, D, t, ccfg)
    check(g, "optimiser returns cover", len(specs) >= 1, len(specs))
    check(g, "cover stays under 15% of floor", 0 < stats["cover_pct"] <= 15.0, stats)
    check(g, "majority of floor stays free", stats["free_pct"] >= 85.0, stats)
    check(g, "no passage below 3 m (no chokepoints)", stats["min_passage"] >= 3.0, stats)
    check(g, "no fully blocked sightline (not a maze)", stats["fully_blocked_los"] == 0, stats)
    check(g, "object count is bounded (open arena)", 1 <= stats["cover_objects"] <= 8, stats)

    # the main entry->centre path must stay clear of cover
    kp = _key_points(W, D, t)
    obstacles = [(s["local"][0], s["local"][1], _footprint(s)[0]) for s in specs]
    entry_block = los_blocked_fraction(kp["E"], kp["C"], obstacles)
    check(g, "entry->centre path unblocked", entry_block < 0.05, entry_block)

    # entry corridor itself holds no cover
    for s in specs:
        x, y = s["local"]
        in_corridor = abs(x) < 2.8 and y < -(D / 2.0 - t) + 2.5
        check_ok = not in_corridor
        if not check_ok:
            check(g, "no cover in entry corridor", False, (x, y))
            break
    else:
        check(g, "no cover in entry corridor", True)

    # deterministic: identical config -> identical result
    specs2, stats2 = optimize_cover(W, D, t, ccfg)
    check(g, "optimiser is deterministic",
          [s["local"] for s in specs] == [s["local"] for s in specs2] and stats == stats2)


# ---------------------------------------------------------------------------
# T13 — UE5 package manifest (engine-free)
# ---------------------------------------------------------------------------
def t13_ue5_manifest():
    g = "T13 UE5 export"
    ctx = FakeCtx()
    records = [
        ("Terrain_Real", "terrain"), ("Blue_BasePlatform", "base"),
        ("CaptureButton_EastMonolith", "capture_button"),
        ("CaptureButton_Crown", "capture_button"), ("Crown_BossButton", "landmark"),
        ("Altar_Base", "altar"), ("RingRoad_Test", "road"), ("Ramp_Test", "ramp"),
        ("WestPocket_Floor", "floor"), ("ObjectiveCover_Test", "cover"),
        ("OuterBoundary_Segment01", "outer_boundary"),
    ]
    for name, kind in records:
        ctx.add(name, kind, 0, 0, 0)
    for name in ("SpeedShrine_West", "SpeedShrine_East", "SpeedShrine_North"):
        ctx.add(name, "resource_marker", 0, 0, 0, meta={"resource_type": "SpeedShrine"})
    for name in ("HealthRelic_SW", "HealthRelic_SE", "HealthRelic_South",
                 "HealthRelic_Capture_Crown", "HealthRelic_Capture_EastMonolith",
                 "HealthRelic_Capture_SEMonolith", "HealthRelic_Capture_SWMonolith",
                 "HealthRelic_Capture_WestMonolith"):
        ctx.add(name, "resource_marker", 0, 0, 0, meta={"resource_type": "HealthRelic"})
    manifest = build_manifest(ctx, validation={"ok": True})
    check(g, "Crown maps to its own group", export_group_for_record(ctx.generated_objects[3]) == "Crown")
    check(g, "resource counts are exact", manifest["resources"] == {
        "speed_shrines": 3, "health_relics": 8, "total": 11,
        "names": ["SpeedShrine_East", "SpeedShrine_North", "SpeedShrine_West",
                  "HealthRelic_Capture_Crown", "HealthRelic_Capture_EastMonolith",
                  "HealthRelic_Capture_SEMonolith", "HealthRelic_Capture_SWMonolith",
                  "HealthRelic_Capture_WestMonolith", "HealthRelic_SE", "HealthRelic_SW", "HealthRelic_South"],
    }, manifest["resources"])
    check(g, "legacy naming is absent", manifest["naming_passed"], manifest["legacy_objects_present"])
    check(g, "all export groups are present", len(manifest["export_groups"]) == 11)


# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("AetherFlow v0.6.4 — automated engine-free tests")
    print("=" * 70)
    for fn in (t1_config, t2_version, t3_layout, t4_heightmap, t5_determinism,
               t6_navigation, t7_simulation, t8_validation, t9_export,
               t10_hygiene, t11_pocket_fairness, t12_pocket_traffic, t12_cover_optimiser,
               t13_ue5_manifest):
        try:
            fn()
        except Exception as exc:  # pragma: no cover
            check(fn.__name__, "EXCEPTION", False, repr(exc))
    print("-" * 70)
    total = len(RESULTS)
    failed = [r for r in RESULTS if not r[2]]
    print("TOTAL: {}  PASSED: {}  FAILED: {}".format(total, total - len(failed), len(failed)))
    if failed:
        print("\nFailed checks:")
        for grp, name, _, detail in failed:
            print("  - {} :: {} {}".format(grp, name, detail or ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
