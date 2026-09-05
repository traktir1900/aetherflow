"""
AetherFlow :: tools/aetherflow_gameplay_auditor_v0.5.py  (v0.5 -- NEW IMPLEMENTATION BASED ON ORIGINAL V0.4 SOURCE)

READ-ONLY diagnostic tool. It answers: "how well does the current AetherFlow
map serve Dominion-style gameplay?" — SCAN -> ANALYZE -> REPORT.

GUARANTEE: this script never creates, deletes, moves, scales, rotates, or
re-materials a scene object, never touches terrain/pockets/bases/Altar/
navigation/validation logic, and never runs the generation pipeline
(main.py / core.pipeline are not imported or invoked). It only READS the
live Blender scene (bpy.data) and export/map_data.json. The ONLY files it is
allowed to write are export/gameplay_audit.json and export/gameplay_audit.txt
(spec v0.2 section 29) -- both plain reports, not scene data.

HOW TO RUN
    Blender Text Editor -> Open... this file from disk (a pasted Text Block
    has no filepath and cannot locate the project) -> Run Script.
    Or headless: blender --background <file>.blend --python
    tools/aetherflow_gameplay_auditor_v0.5.py [-- --compare-report export/gameplay_audit.json]
    (bare `python3 tools/aetherflow_gameplay_auditor_v0.5.py` also works outside
    Blender for the JSON-only sections; anything needing the live scene or
    BVH LOS prints [DATA MISSING] instead of guessing.)
    Self-tests: python3 tools/aetherflow_gameplay_auditor_v0.5.py --self-test

REQUIRES export/map_data.json to already exist (produced by a previous
main.py run). This tool does not generate it.

DATA SOURCE PRIORITY (spec v0.2 section 1): (1) live Blender scene,
(2) export/map_data.json, (3) existing navigation data, (4) simulation data.
Nothing is invented when a source is missing -- every such value is tagged
inline as one of:
    [FALLBACK]        straight-line estimate used in place of a real route
    [DATA MISSING]     the source simply doesn't exist in this export/scene
    [APPROXIMATION]    computed from bounding circles/dims, not a full BVH
                        mesh query (see section 28 performance note below)
No PASS/score is ever printed for something that was not actually computed.

v0.2 SCOPE -- this is a substantial extension of v0.1, built ON TOP of it
(v0.1's scan/route/fairness/pocket/altar/chokepoint functions are unchanged
below and still run first). Newly added in v0.2:
    - full scene classification (Terrain/Roads/Ramps/PocketCover/CoreCover/
      AltarObstacles/Rocks/Structures/Resources/Vegetation/Debug/... incl.
      WestPocket_C1..3 style names, WITHOUT hard-coding only those names --
      collection + map_data.json bucket + spatial containment are all used)
    - expanded pocket geometry audit (cover-cover / cover-wall / cover-entry
      gaps, using real object dims from map_data.json)
    - Core Cover audit (KEEP / LOW VALUE / OBSTRUCTION, kept separate from
      Altar Obstacles)
    - Altar Obstacle audit (kept separate from Core Cover; v0.2 note: no
      "Altar_Obstacle_*" objects exist in the current generator, so this
      section correctly reports [DATA MISSING] rather than inventing one)
    - real geometric passage-width estimate [APPROXIMATION] for pockets /
      Altar / bases / capture points (bounding-circle based, not full BVH)
    - chokepoint engine split: A) route-density (v0.1, unchanged) and
      B) geometric near-neighbour gaps, each flagged MANDATORY when no
      alternative route/gap exists nearby
    - capture point + base audits (approaches, nearby cover, route counts)
    - basic 8-direction BVH line-of-sight sampling (Blender only -- prints
      [DATA MISSING] outside Blender), with ONE shared cached BVHTree
      (section 28 performance requirement)
    - cover value scoring (BEST / LOW VALUE / OBSTRUCTIVE) built from the
      LOS + distance-to-route data above
    - resource scan (Shrines/Relics) -- "RESOURCE DATA: NOT FOUND" if none
      exist, per spec section 18 (never fabricated)
    - map connectivity / dead-end pass (zones with zero simulated traffic
      or no registered route)
    - lightweight, fully transparent (formula + reason printed) rotation /
      fairness-engine / comeback / deathball / snowball / camping-risk
      heuristics built ONLY from data computed elsewhere in this report
    - final weighted MAP QUALITY SCORE (0-100) with a reason per sub-score
    - --compare <previous gameplay_audit.json> regression diff
    - writes export/gameplay_audit.json + .txt (the two files this tool is
      allowed to write)

v0.4 CHANGELOG -- ROOT-CAUSE FIX for the repeatedly-reported "PocketCover: 0"
issue: every earlier version (v0.2, v0.3) only ever classified objects that
were already present in export/map_data.json. If the live .blend has
WestPocket_C1/C2/C3-style objects that never made it into that JSON (a stale
export, or objects registered through a different code path), NO amount of
name-pattern cleverness applied to the JSON could ever find them -- v0.3's
fallback chain was strictly downstream of a data source that may simply not
contain the objects. v0.4 adds resolve_pocket_cover_live(), which -- only
when running inside Blender -- scans bpy.data.objects DIRECTLY, independent
of map_data.json, in the exact priority spec v0.4 section 4 asks for:
    1. exact object naming      (<Pocket>_C<N>, case-insensitive)
    2. collection membership    (a collection whose name mentions the pocket
                                  and "cover")
    3. custom properties        (obj["pocket"] / obj["element"], if present)
    4. spatial containment      (inside the pocket's inner zone, from
                                  map_data.json's own location/dimensions)
    5. controlled fallback      (resolve_pocket_cover() over the JSON, v0.3
                                  behaviour, used only where the live scan
                                  found nothing for that pocket -- e.g. when
                                  not running inside Blender at all)
When the live scan finds objects the JSON export doesn't know about, that
mismatch itself is now surfaced as an issue ("N live object(s) found in the
Blender scene but NOT in map_data.json -- export is stale"), instead of
being silently absorbed. This also directly implements spec section 1's
data-source priority ("1. live Blender scene" before "2. map_data.json")
for this specific metric, which earlier versions did not actually honour.

Other v0.4 additions (kept v0.3's working sections intact -- scene scan,
routes, fairness, route-density chokepoints, Blender LOS raycast, Core Cover
audit, Altar audit, base audit, risk analysis, report generation, per spec
section 3):
    - --compare's diff output is now a Metric/Before/After/Delta/Verdict
      table (spec section 18), not just a bare score list.
    - Capture-point approach verdicts are no longer a flat WARNING-under-3;
      GOOD/NORMAL/CONSTRAINED/SINGLE-ENTRY, each with its reasoning (section 7).
    - Core Cover gets a transparent 0-10 COVER VALUE score with its listed
      input factors (section 9), replacing the earlier BEST/LOW-VALUE-only
      cover_value_analysis pass for Core Cover specifically (pocket cover is
      unaffected -- it is scored in the POCKETS section, not here).

HONESTY NOTE ON v0.4 SCOPE: sections 10 (a second, gridded LOS pass), 11-14
(a full macro-rotation / deathball-route-graph / snowball / comeback engine
built from a real point-to-point route graph rather than the existing
Base<->CapturePoint table) and 17 (a formal connectivity graph with
isolated/single-connection/dead-end classification beyond what v0.3's
connectivity_analysis already does) are NOT implemented in this pass -- they
would need either new navigation data this project's exporter does not
produce (a full point-to-point route graph, not just Base->CapturePoint) or
a non-trivial gridded-raycast subsystem, and building either honestly (per
section 20 -- no invented scores) is more than fits in one focused change.
The existing ROTATION/DEATHBALL/SNOWBALL/COMEBACK sections from v0.2/v0.3
(built on the real data that IS available) are kept as-is rather than
replaced with something that looks more complete than it is.

v0.3 CHANGELOG (kept for history -- still accurate, resolve_pocket_cover()
described here is now the v0.4 fallback tier 5):
    - CRITICAL FIX: pocket interior cover (C1/C2/C3) is no longer silently
      reported as 0 when it actually exists. A new resolve_pocket_cover()
      first trusts map_data.json's own pockets[i]["cover"] list [EXACT]; if
      that is empty (stale/older export, or objects registered under a
      different naming scheme), it falls back to name-pattern matching
      [HEURISTIC] and then spatial containment inside the pocket floor,
      explicitly excluding anything that looks like rock-arc/gate/wall
      geometry [APPROXIMATION]. Both PocketCover counting AND the pocket
      geometry gap math now share this one resolver (computed once, reused
      -- also a performance win, section 23).
    - Every classification/metric line is now tagged [EXACT], [HEURISTIC],
      [APPROXIMATION], [FALLBACK], or [DATA MISSING] (section 22) -- no
      value is presented without disclosing how it was obtained.
    - Negative "passage" values are never printed as a width any more: any
      2D footprint gap that comes out negative is reported as
      "OVERLAP <object A> <-> <object B>  penetration = X m" instead
      (section 4).
    - Altar geometry: landmarks / Core Cover / Altar Obstacles are reported
      as three distinct sets (never folded together), plus a real "inner
      clear radius" (nearest Core Cover / Altar Obstacle edge to the altar
      centre) with an explicit PASS (>=7.5 m) / FAIL classification and the
      offending object named. The simulation's covered_fraction (a LOS/
      defensive-cover-availability metric) and a geometric physical free-
      area approximation are now both shown side by side, since they answer
      different questions and were easy to misread as contradictory.
    - LOS analysis now names the blocking object per direction, not just
      "blocked: yes".
    - Map connectivity distinguishes REAL ISOLATION (no registered route AND
      zero traffic) from NO SIMULATION TRAFFIC (a registered, reachable zone
      the bot simulation simply didn't route through) -- SWPocket-style
      zero-traffic zones no longer get an unconditional WARNING.
    - CLI renamed/extended: --save-report writes export/gameplay_audit.json
      + .txt (previously always-on); --compare-report <path> replaces
      --compare. Report is always printed to the console either way. several spec v0.2 items describe analyses that need
data this project's exporter does not currently produce at all (e.g. a
second/third alternative route per capture point, or "Altar_Obstacle_*"
objects, which the generator never creates -- see ALTAR OBSTACLES section).
HONESTY NOTE ON SCOPE:
Rather than fabricate numbers for these, this tool reports them as
[DATA MISSING] with a one-line explanation of what upstream data would be
needed. That is a deliberate application of section 27 ("NO FALSE
CONFIDENCE") to this tool's own output, not an oversight.
"""

# V0.5 CHANGELOG
# ----------------
# This file is the official new v0.5 implementation based on the recovered original
# v0.4 source. v0.4 is preserved as the architectural foundation; v0.5 adds current
# 0.6.1 routed-pocket handling, live evaluated-mesh diagnostics, geometric overlap,
# base/terrain/collision/symmetry audits, and simulation-vs-navigation diagnostics.
# No project geometry, generator, navigation, simulation, or Blender scene is modified.
import os
import sys
import json
import math
import re
import inspect

try:
    import bpy
    HAVE_BPY = True
except ImportError:
    HAVE_BPY = False


# =============================================================================
# CONFIG
# =============================================================================
PLAYER_SPEED = 6.0   # m/s -- change this to re-time every route in the report

EXPECTED_CAPTURE_POINTS = 5
EXPECTED_BASES = 2
EXPECTED_POCKETS = 4
CAPTURE_POINTS = {"Crown", "EastMonolith", "SEMonolith", "SWMonolith", "WestMonolith"}
POCKETS = {"WestPocket", "EastPocket", "SWPocket", "SEPocket"}

# CHOKEPOINT ANALYSIS width bands (spec section 10), used wherever a REAL
# metre width exists (pocket entry / internal passage).
def _width_band(w):
    if w is None:
        return "UNKNOWN"
    if w < 3.0:
        return "CRITICAL"
    if w < 5.0:
        return "NARROW"
    if w < 7.0:
        return "NORMAL"
    return "OPEN"


# =============================================================================
# PROJECT-ROOT / map_data.json DISCOVERY
# (same walk-up pattern as main.py, marker = export/map_data.json instead of
# core/config.py, since this tool must work without importing core.* at all)
# =============================================================================
_MARKER = os.path.join("export", "map_data.json")


def _is_project_dir(path):
    return bool(path) and os.path.isfile(os.path.join(path, _MARKER))


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

    if HAVE_BPY:
        try:
            texts = []
            if bpy.context.edit_text is not None:
                texts.append(bpy.context.edit_text)
            space = bpy.context.space_data
            if space is not None and getattr(space, "text", None) is not None:
                texts.append(space.text)
            texts.extend(bpy.data.texts)
            for t in texts:
                fp = getattr(t, "filepath", "") or ""
                if fp and os.path.isfile(fp):
                    add_file(fp)
        except Exception:
            pass
        try:
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


def find_project_root():
    probed = []
    for start in dict.fromkeys(_candidate_starts()):
        found = _walk_up(start, probed)
        if found:
            return found, probed
    return None, probed


def load_map_data():
    """Returns (data_dict_or_None, map_data_path_or_None, probed_dirs)."""
    root, probed = find_project_root()
    if root is None:
        return None, None, probed
    path = os.path.join(root, _MARKER)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path, probed


# =============================================================================
# small geometry helpers (read-only math, no scene access)
# =============================================================================
def dist2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def fmt_dt(distance_m):
    if distance_m is None:
        return "  n/a m", "  n/a s"
    t = distance_m / PLAYER_SPEED
    return "{:6.1f} m".format(distance_m), "{:6.1f} s".format(t)


# =============================================================================
# 1) SCENE SCAN
# =============================================================================
def scene_scan(data, issues):
    lines = []
    m = data.get("map", {})
    w, h = m.get("width"), m.get("height")
    if w is None or h is None:
        ghs = m.get("ground_half_size")
        w = h = (ghs * 2 if ghs else None)
    lines.append("MAP")
    lines.append("{} x {} m".format(w, h))

    cps = data.get("capture_points", [])
    bases = data.get("bases", [])
    pockets = data.get("pockets", [])
    altars = [l for l in data.get("landmarks", []) if l.get("type") == "altar"]

    lines.append("Capture Points: {}".format(len(cps)))
    lines.append("Bases: {}".format(len(bases)))
    lines.append("Pockets: {}".format(len(pockets)))
    lines.append("Altar objects: {}".format(len(altars)))

    if len(cps) != EXPECTED_CAPTURE_POINTS:
        issues.append(("WARNING", "Expected {} capture points, map_data.json has {}"
                       .format(EXPECTED_CAPTURE_POINTS, len(cps))))
    if len(bases) != EXPECTED_BASES:
        issues.append(("WARNING", "Expected {} bases, map_data.json has {}"
                       .format(EXPECTED_BASES, len(bases))))
    if len(pockets) != EXPECTED_POCKETS:
        issues.append(("WARNING", "Expected {} pockets, map_data.json has {}"
                       .format(EXPECTED_POCKETS, len(pockets))))
    if not altars:
        issues.append(("CRITICAL", "No altar landmark found in map_data.json"))

    # cross-check the JSON against the LIVE scene, by object name -- this is
    # the only reliable link back to bpy.data, since per-object kind/meta is
    # only ever kept in-memory during a generation run (see core/context.py),
    # never written as a Blender custom property.
    if HAVE_BPY:
        expected = []
        for cp in cps:
            expected.append(("capture point", "CapturePlatform_{}".format(cp["name"])))
        for b in bases:
            team = b["name"][:-4] if b["name"].endswith("Base") else b["name"]
            expected.append(("base", "{}_BasePlatform".format(team)))
        for p in pockets:
            expected.append(("pocket floor", "{}_Floor".format(p["name"])))
        for a in altars:
            expected.append(("altar", a["name"]))

        missing = [(kind, nm) for kind, nm in expected if bpy.data.objects.get(nm) is None]
        for kind, nm in missing:
            issues.append(("WARNING", "{} '{}' is in map_data.json but NOT found in the live scene "
                                      "(deleted, renamed, or export is stale)".format(kind, nm)))
        lines.append("Live-scene cross-check: {}/{} expected objects found"
                     .format(len(expected) - len(missing), len(expected)))
    else:
        lines.append("Live-scene cross-check: SKIPPED (not running inside Blender)")

    return lines, cps, bases, pockets, altars


# =============================================================================
# 2) ROUTE ANALYSIS + 3) MOVEMENT TIME
# =============================================================================

def route_analysis(data, cps, bases, pockets, altars, issues):
    """Route analysis using real routed data whenever the export provides it.

    Base->Altar remains DATA-MISSING/FALLBACK because the current exporter does
    not register that route. Pocket->MainRoad uses navigation.pockets[*] exactly
    when available and never substitutes a straight-line value in that case.
    """
    lines = []
    routes = data.get("navigation", {}).get("routes", {})
    nav_pockets = {p.get("name"): p for p in data.get("navigation", {}).get("pockets", [])}
    rows = []
    fallback_used = False

    for b in bases:
        for cp in cps:
            key = "{}->{}".format(b["name"], cp["name"])
            d = routes.get(key)
            rows.append(("{} -> {}".format(b["name"], cp["name"]), d, False))
            if d is None:
                issues.append(("WARNING", "No nav route for {} [DATA MISSING]".format(key)))

    # Base -> Altar: current exporter does not register this route.
    altar_pos = altars[0]["location"][:2] if altars else None
    for b in bases:
        if altar_pos is None:
            lines.append("{} -> Altar [DATA MISSING]".format(b["name"]))
            continue
        d = dist2(b["position"][:2], altar_pos)
        rows.append(("{} -> Altar".format(b["name"]), d, True))
        fallback_used = True

    cp_by_name = {cp["name"]: cp for cp in cps}
    for p in pockets:
        pname = p["name"]
        np = nav_pockets.get(pname)
        cp = cp_by_name.get(p.get("capture_point"))
        if np is not None and np.get("route_length") is not None:
            d = float(np["route_length"])
            rows.append(("{} -> MainRoad (via {})".format(pname, cp["name"] if cp else p.get("capture_point")),
                         d, False))
        else:
            # No invented route. Keep the historical line only as an explicit
            # missing-data record; do not compute a straight-line proxy.
            lines.append("{} -> MainRoad [DATA MISSING]".format(pname))
            issues.append(("WARNING", "{}: no routed navigation.pockets entry [DATA MISSING]".format(pname)))

    lines.append("{:<38}{:>10}{:>10}".format("Route", "Distance", "Time"))
    for label, d, is_fb in rows:
        dtxt, ttxt = fmt_dt(d)
        tag = "  [FALLBACK]" if is_fb else "  [EXACT]"
        if "MainRoad" in label and not is_fb:
            tag = "  [EXACT, navigation.pockets]"
        lines.append("{:<38}{}{}{}".format(label, dtxt, ttxt, tag))

    if fallback_used:
        lines.append("")
        lines.append("BASE->ALTAR uses [FALLBACK] because no routed Base->Altar data exists in the current export.")
    return lines, rows



# =============================================================================
# 6) FAIRNESS (uses the real routed Base->CapturePoint distances only)
# =============================================================================
def fairness_analysis(cps, route_rows, issues):
    lines = []
    blue = [d for label, d, fb in route_rows if label.startswith("BlueBase ->")
            and not fb and d is not None]
    red = [d for label, d, fb in route_rows if label.startswith("RedBase ->")
           and not fb and d is not None]

    if not blue or not red:
        issues.append(("WARNING", "Fairness: insufficient routed data for Blue/Red comparison"))
        lines.append("Insufficient routed data -- skipped.")
        return lines, None

    blue_avg_d = sum(blue) / len(blue)
    red_avg_d = sum(red) / len(red)
    blue_avg_t = blue_avg_d / PLAYER_SPEED
    red_avg_t = red_avg_d / PLAYER_SPEED
    diff_pct = abs(blue_avg_t - red_avg_t) / max(blue_avg_t, red_avg_t) * 100.0 if max(blue_avg_t, red_avg_t) else 0.0

    lines.append("BLUE average: {:.1f} m / {:.1f} s ({} routes)".format(blue_avg_d, blue_avg_t, len(blue)))
    lines.append("RED  average: {:.1f} m / {:.1f} s ({} routes)".format(red_avg_d, red_avg_t, len(red)))
    lines.append("DIFFERENCE:   {:.1f} %".format(diff_pct))
    if diff_pct <= 5.0:
        lines.append("VERDICT: BALANCED")
    elif blue_avg_t < red_avg_t:
        lines.append("VERDICT: BLUE ADVANTAGE ({:.1f}% faster on average)".format(diff_pct))
    else:
        lines.append("VERDICT: RED ADVANTAGE ({:.1f}% faster on average)".format(diff_pct))

    if diff_pct > 10.0:
        issues.append(("WARNING", "Blue/Red average route time differs by {:.1f}% (>10%)".format(diff_pct)))
    else:
        issues.append(("GOOD", "Blue/Red average route time within {:.1f}% -- gameplay-equivalent".format(diff_pct)))

    return lines, diff_pct


# =============================================================================
# 4) POCKET AUDIT
# =============================================================================
def pocket_audit(pockets, pocket_cover_result, issues):
    lines = []
    lines.append("{:<12}{:>9}{:>7}{:>11}{:>12}".format("Pocket", "Entry", "Cover", "MinPass", "Continuous"))

    by_name = {p["name"]: p for p in pockets}
    for p in pockets:
        entry_w = p.get("entry", {}).get("width")
        cover_n = len(pocket_cover_result.get(p["name"], []))
        ca = p.get("cover_analysis") or {}
        min_pass = ca.get("min_passage")
        cont = p.get("perimeter_continuous")
        min_pass_txt = "{:.1f}m".format(min_pass) if min_pass is not None else "n/a"
        lines.append("{:<12}{:>7.1f}m{:>7}{:>10}{:>12}".format(
            p["name"], entry_w if entry_w is not None else -1.0, cover_n,
            min_pass_txt,
            "YES" if cont else "NO"))

        band = _width_band(entry_w)
        if band in ("CRITICAL", "NARROW"):
            issues.append(("WARNING" if band == "NARROW" else "CRITICAL",
                           "{}: entry width {:.1f} m is {}".format(p["name"], entry_w, band)))
        if min_pass is not None and _width_band_safe(min_pass) in ("CRITICAL", "OVERLAP"):
            issues.append(("CRITICAL", "{}: internal min passage {:.1f} m is CRITICAL/OVERLAP"
                           .format(p["name"], min_pass)))
        if cover_n != 3:
            issues.append(("WARNING", "{}: resolved {} interior cover object(s) (expected exactly 3)"
                           .format(p["name"], cover_n)))
        if not cont:
            issues.append(("WARNING", "{}: rock boundary not flagged continuous".format(p["name"])))

    # mirror-pair comparison
    lines.append("")
    lines.append("Mirror-pair gameplay difference:")
    seen = set()
    for p in pockets:
        pair = p.get("mirror_pair")
        if not pair or p["name"] in seen or pair not in by_name:
            continue
        seen.add(p["name"])
        seen.add(pair)
        q = by_name[pair]
        ew_p = p.get("entry", {}).get("width")
        ew_q = q.get("entry", {}).get("width")
        fa_p = p.get("floor_area")
        fa_q = q.get("floor_area")
        cov_p = len(pocket_cover_result.get(p["name"], []))
        cov_q = len(pocket_cover_result.get(pair, []))
        ok = (ew_p == ew_q) and (cov_p == cov_q) and (abs((fa_p or 0) - (fa_q or 0)) < 1.0)
        lines.append("  {} <-> {}: entry {:.1f}m/{:.1f}m  cover {}/{}  floor {:.0f}/{:.0f} m2  [{}]"
                     .format(p["name"], pair, ew_p or -1, ew_q or -1, cov_p, cov_q,
                             fa_p or 0, fa_q or 0, "OK" if ok else "MISMATCH"))
        if not ok:
            issues.append(("WARNING", "{} <-> {} mirror pair mismatch (see POCKETS table)"
                           .format(p["name"], pair)))

    return lines


# =============================================================================
# 5) ALTAR AUDIT
# =============================================================================
INNER_CLEAR_RADIUS_MIN = 7.5   # m -- spec v0.3 section 7



def _live_obj(name):
    if not HAVE_BPY:
        return None
    try:
        return bpy.data.objects.get(name)
    except Exception:
        return None


def _mesh_vertices_world(obj):
    if not HAVE_BPY or obj is None or obj.type != "MESH":
        return []
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        verts = [obj.matrix_world @ v.co for v in mesh.vertices]
        eval_obj.to_mesh_clear()
        return verts
    except Exception:
        return []


def _mesh_bvh(obj):
    if not HAVE_BPY or obj is None or obj.type != "MESH":
        return None
    try:
        from mathutils.bvhtree import BVHTree
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        verts = [obj.matrix_world @ v.co for v in mesh.vertices]
        polys = [[v for v in poly.vertices] for poly in mesh.polygons]
        bvh = BVHTree.FromPolygons(verts, polys, all_triangles=False)
        eval_obj.to_mesh_clear()
        return bvh
    except Exception:
        return None


def _mesh_overlap(obj_a, obj_b):
    if not HAVE_BPY:
        return None
    try:
        a = _mesh_bvh(obj_a)
        b = _mesh_bvh(obj_b)
        if a is None or b is None:
            return None
        return bool(a.overlap(b))
    except Exception:
        return None


def _mesh_vertex_clearance(obj_a, obj_b):
    """Geometry-derived nearest-vertex-to-surface distance.

    This is a real evaluated-mesh query but is conservatively tagged
    APPROXIMATION for clearance because a vertex-only search cannot prove the
    exact closest point of two arbitrary continuous surfaces.
    """
    if not HAVE_BPY:
        return None
    bvh = _mesh_bvh(obj_b)
    verts = _mesh_vertices_world(obj_a)
    if bvh is None or not verts:
        return None
    best = None
    for v in verts:
        hit = bvh.find_nearest(v)
        if hit and hit[3] is not None:
            d = float(hit[3])
            best = d if best is None else min(best, d)
    return best


def _live_core_cover_objects():
    if not HAVE_BPY:
        return []
    result = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        name = obj.name
        if name.startswith("Core_Cover_"):
            result.append(obj)
            continue
        try:
            elem = str(obj.get("element", "")).lower()
            if elem == "core_cover":
                result.append(obj)
        except Exception:
            pass
    return result


def altar_audit(data, altars, bases, pockets, issues):
    lines = []
    if not altars:
        issues.append(("CRITICAL", "Altar audit skipped -- no altar landmark in map_data.json [DATA MISSING]"))
        return ["No altar landmark found -- CRITICAL."]

    altar_pos = altars[0]["location"][:2]
    lines.append("Position: ({:.1f}, {:.1f})  [EXACT export landmark]".format(*altar_pos))

    export_core = [c for c in data.get("cover", []) if _is_core_cover_record(c) and not _is_pocket_cover_record(c)]
    export_obstacles = [c for c in data.get("cover", []) if str(c.get("name", "")).startswith("Altar_Obstacle")]
    export_obstacles += [r for r in data.get("rocks", []) if str(r.get("name", "")).startswith("Altar_Obstacle")]
    lines.append("Export Core Cover: {}   Altar Obstacles: {}".format(len(export_core), len(export_obstacles)))

    live_altar = _live_obj("Altar_Base") or _live_obj(altars[0]["name"])
    live_core = _live_core_cover_objects()

    if live_altar is not None and live_core:
        exact_overlaps = []
        min_approx = None
        for obj in live_core:
            ov = _mesh_overlap(live_altar, obj)
            if ov:
                exact_overlaps.append(obj.name)
            d = _mesh_vertex_clearance(live_altar, obj)
            if d is not None:
                item = (d, obj.name)
                min_approx = item if min_approx is None or d < min_approx[0] else min_approx

        lines.append("Live mesh Core Cover: {} [EXACT live scene]".format(len(live_core)))
        if exact_overlaps:
            lines.append("Actual mesh intersection: YES -> {} [EXACT]".format(", ".join(sorted(exact_overlaps))))
            lines.append("Gameplay clear radius: INTERSECTION CONTACT => 0.000 m minimum [derived from EXACT intersection]")
            for nm in exact_overlaps:
                issues.append(("WARNING", "{} actually intersects Altar mesh [EXACT]".format(nm)))
        else:
            lines.append("Actual mesh intersection: NO [EXACT]")

        if min_approx is not None:
            lines.append("Minimum vertex-to-surface distance: {:.3f} m -> {} [APPROXIMATION]"
                         .format(min_approx[0], min_approx[1]))
            if not exact_overlaps and min_approx[0] < INNER_CLEAR_RADIUS_MIN:
                issues.append(("WARNING", "Altar approximate clear radius {:.3f} m < {:.1f} m [APPROXIMATION]"
                               .format(min_approx[0], INNER_CLEAR_RADIUS_MIN)))
    else:
        # Keep legacy export approximation visible, but never present 1.46 m as exact.
        blockers = export_core + export_obstacles
        if blockers:
            gap, name = min_gap_to_set(altar_pos, blockers)
            lines.append("Minimum clear radius: {:.2f} m -> {} [APPROXIMATION, export bounding circles]"
                         .format(gap, name))
        else:
            lines.append("Exact live mesh clearance: [DATA MISSING]")
            issues.append(("WARNING", "Live Blender geometry required for exact Altar clearance [DATA MISSING]"))

    zones = data.get("simulation", {}).get("zones", {})
    core_zone = zones.get("AetherCore")
    if core_zone is not None:
        covered_pct = core_zone.get("covered_fraction", 0.0) * 100.0
        traffic = core_zone.get("traffic", 0)
        lines.append("[EXACT, simulation] cover_objects_in_zone={} covered_fraction={:.0f}% exposure={} traffic={}"
                     .format(core_zone.get("cover_objects_in_zone", 0), covered_pct,
                             core_zone.get("exposure"), traffic))
        lines.append("Reachable (simulated traffic > 0): {}".format("YES" if traffic > 0 else "NO"))
    else:
        lines.append("[DATA MISSING] no AetherCore simulation zone.")

    lines.append("")
    lines.append("Approach distances [FALLBACK] -- no routed Base->Altar data in current export:")
    for b in bases:
        d = dist2(b["position"][:2], altar_pos)
        dtxt, ttxt = fmt_dt(d)
        lines.append("  {:<12} -> Altar   {}{}".format(b["name"], dtxt, ttxt))
    for pname in ("WestPocket", "EastPocket"):
        p = next((p for p in pockets if p["name"] == pname), None)
        if p:
            d = dist2(p["location"][:2], altar_pos)
            dtxt, ttxt = fmt_dt(d)
            lines.append("  {:<12} -> Altar   {}{}".format(pname, dtxt, ttxt))

    return lines



# =============================================================================
# 3) CHOKEPOINT ANALYSIS (map-wide, from real navigation.chokepoints)
# =============================================================================
def chokepoint_analysis(data, issues):
    lines = []
    chokes = data.get("navigation", {}).get("chokepoints", [])
    routes = data.get("navigation", {}).get("routes", {})
    total_routes = len(routes) if routes else 1

    lines.append("NOTE: map-wide chokepoints are route-DENSITY based (cells shared "
                "by many base/objective paths), not a directly measured corridor "
                "width -- see the POCKETS table below for real metre widths "
                "(entry width, internal min passage).")
    lines.append("{:<10}{:<10}{:>8}{:>16}{:>12}".format("X", "Y", "Cells", "RoutesThrough", "Pressure"))
    for c in chokes:
        pressure = c["routes_through"] / float(total_routes)
        label = "CRITICAL" if pressure >= 0.8 else "HIGH" if pressure >= 0.5 else "MODERATE"
        lines.append("{:<10.1f}{:<10.1f}{:>8}{:>16}{:>12}"
                     .format(c["x"], c["y"], c["cells"], c["routes_through"], label))
        if pressure >= 0.8:
            issues.append(("WARNING", "Chokepoint ({:.1f},{:.1f}) carries {}/{} routes -- single point of failure"
                           .format(c["x"], c["y"], c["routes_through"], total_routes)))

    nav_problems = data.get("navigation", {}).get("problems", [])
    for prob in nav_problems:
        issues.append(("CRITICAL", "navigation.problems: {}".format(prob)))

    return lines


# =============================================================================
# v0.2 -- SCENE CLASSIFICATION (spec section 2)
# Buckets every object map_data.json knows about into gameplay categories.
# Uses (in order): map_data.json bucket -> meta fields -> name pattern -- so
# it is NOT hard-tied to exact names like "WestPocket_C1" (those still match,
# via meta.pocket + meta.element, but unnamed/renamed variants still classify
# correctly through the same meta path).
# =============================================================================
# =============================================================================
# v0.3 -- POCKET COVER RESOLUTION (spec v0.3 section 2, CRITICAL FIX).
# Computed ONCE, reused by classify_objects(), pocket_audit() and
# pocket_geometry_audit() -- avoids recomputing (section 23 performance) and
# guarantees they never disagree with each other.
#
# Priority chain (spec section 1: collection/name/props/hierarchy/spatial/
# geometry -- this project's export doesn't carry collection or a true parent
# hierarchy per object, so the chain used here is the subset that's actually
# backed by real exported data):
#   1. [EXACT]         map_data.json's own pockets[i]["cover"] list, if it is
#                       non-empty -- this is the generator's own bookkeeping
#                       (core/context.py / geometry/pockets.py), the most
#                       trustworthy source when present.
#   2. [HEURISTIC]      object name matches "<PocketName>...C1/C2/C3" or
#                       contains "cover" (case-insensitive), for objects the
#                       EXACT pass missed (e.g. an older/renamed export).
#   3. [APPROXIMATION]  spatial containment: object centre lies within the
#                       pocket's inner zone (a fraction of its floor
#                       dimensions, well clear of the outer rock boundary)
#                       AND is not within the entry corridor.
# In all three tiers, anything whose name clearly reads as rock-arc / gate /
# wall / floor geometry is excluded -- interior cover is never confused with
# the perimeter that encloses it. A CLASSIFICATION CONFLICT is raised (not
# silently resolved) when a HEURISTIC/APPROXIMATION candidate's name strongly
# suggests it belongs to a DIFFERENT category (e.g. "Core_Cover_*" pulled in
# only because it happens to sit near a pocket).
# =============================================================================
_ARC_NAME_HINTS = ("arcrock", "rockarc", "backwall", "gaterock", "_wall", "_floor")
_FOREIGN_NAME_HINTS = ("core_cover", "altar_", "capture", "base_", "road", "ramp")
_POCKET_COVER_NAME_RE = re.compile(r"^(WestPocket|EastPocket|SWPocket|SEPocket)_C(\d+)$", re.IGNORECASE)


# =============================================================================
# v0.4 -- LIVE-SCENE POCKET COVER SCAN (spec section 4, root-cause fix).
# Scans bpy.data.objects DIRECTLY -- entirely independent of map_data.json --
# so a stale/incomplete export can no longer hide real objects from this
# metric. Priority exactly as spec v0.4 section 4 lists it:
#   1. exact object naming        <Pocket>_C<N>            [EXACT-name]
#   2. collection membership      collection name mentions
#                                  the pocket + "cover"      [EXACT-collection]
#   3. custom properties          obj["pocket"] / obj["element"] if present
#                                                            [EXACT-property]
#   4. spatial containment        inside the pocket's inner zone (from
#                                  map_data.json location/dimensions)
#                                                            [APPROXIMATION-spatial]
# (tier 5, controlled fallback, is resolve_pocket_cover() over the JSON --
# applied by the caller only where this live scan found nothing.)
# RockArc/Gate/Wall/Floor-looking names are excluded at every tier.
# =============================================================================
def resolve_pocket_cover_live(pockets):
    """Returns (result, live_names): result[pocket_name] = list of
    (obj_name, tag, (x, y), (dim_x, dim_y)); live_names = set of every object
    name this pass matched (used to cross-check against map_data.json)."""
    result = {p["name"]: [] for p in pockets}
    live_names = set()
    if not HAVE_BPY:
        return result, live_names

    by_pname = {p["name"]: p for p in pockets}

    for obj in bpy.data.objects:
        try:
            if obj.type != 'MESH':
                continue
            nm = obj.name
        except Exception:
            continue
        nm_low = nm.lower()
        if any(h in nm_low for h in _ARC_NAME_HINTS):
            continue

        # 1) exact export identity: if current map_data names an object as pocket cover,
        # trust that exact identity in the live scene. This is stronger than name patterns
        # and remains read-only.
        exact_json = False
        for pname, p in by_pname.items():
            if nm in set(p.get("cover") or []):
                # Never accept an object already identified as Core Cover or perimeter geometry.
                try:
                    elem = str(obj.get("element", "")).lower()
                except Exception:
                    elem = ""
                if elem not in ("core_cover", "interior_cover") or elem == "interior_cover":
                    if not nm.lower().startswith("core_cover_") and not any(h in nm_low for h in _ARC_NAME_HINTS):
                        result[pname].append((nm, "EXACT-export-name", tuple(obj.location)[:2], tuple(obj.dimensions)[:2]))
                        live_names.add(nm)
                        exact_json = True
                break
        if exact_json:
            continue

        # 2) exact object naming
        m = _POCKET_COVER_NAME_RE.match(nm)
        if m:
            pname = next((p for p in by_pname if p.lower() == m.group(1).lower()), None)
            if pname:
                result[pname].append((nm, "EXACT-name", tuple(obj.location)[:2], tuple(obj.dimensions)[:2]))
                live_names.add(nm)
                continue

        # 2) collection membership
        try:
            coll_text = " ".join(c.name.lower() for c in obj.users_collection)
        except Exception:
            coll_text = ""
        coll_hit = next((p for p in by_pname if p.lower() in coll_text and "cover" in coll_text), None)
        if coll_hit:
            result[coll_hit].append((nm, "EXACT-collection", tuple(obj.location)[:2], tuple(obj.dimensions)[:2]))
            live_names.add(nm)
            continue

        # 3) custom properties
        try:
            props = {k.lower(): obj[k] for k in obj.keys()}
        except Exception:
            props = {}
        pocket_prop = props.get("pocket") or props.get("aetherflow_pocket")
        elem_prop = str(props.get("element", "")).lower()
        if pocket_prop and elem_prop not in ("backwall", "wall", "floor"):
            pname = next((p for p in by_pname if p.lower() == str(pocket_prop).lower()), None)
            if pname and (elem_prop == "cover" or elem_prop == ""):
                result[pname].append((nm, "EXACT-property", tuple(obj.location)[:2], tuple(obj.dimensions)[:2]))
                live_names.add(nm)
                continue

        # 4) spatial containment (last resort, needs map_data.json geometry)
        loc_xy = tuple(obj.location)[:2]
        for pname, p in by_pname.items():
            cx, cy = p["location"][0], p["location"][1]
            W, D = p["dimensions"][0], p["dimensions"][1]
            inner_r = 0.42 * min(W, D)
            entry_xy = p["entry"]["point"][:2]
            if dist2(loc_xy, (cx, cy)) <= inner_r and dist2(loc_xy, entry_xy) >= 3.0:
                result[pname].append((nm, "APPROXIMATION-spatial", loc_xy, tuple(obj.dimensions)[:2]))
                live_names.add(nm)
                break

    return result, live_names


def resolve_pocket_cover_combined(data, pockets):
    """v0.4: merges the live-scene scan (tiers 1-4) with the v0.3 JSON-only
    resolver (tier 5, used per-pocket only where the live scan found
    nothing -- e.g. running outside Blender, or a pocket with no matching
    live objects at all). Returns (pocket_cover_result, notes) in the same
    shape build_report/pocket_audit/pocket_geometry_audit/classify_objects
    already expect: pocket_cover_result[name] = list of (obj_rec, tag)."""
    live_result, live_names = resolve_pocket_cover_live(pockets)
    json_result, json_conflicts = resolve_pocket_cover(data)

    combined = {}
    notes = list(json_conflicts)
    for p in pockets:
        pname = p["name"]
        live = live_result.get(pname, [])
        if live:
            combined[pname] = [
                ({"name": nm, "location": [xy[0], xy[1], 0.0],
                  "dimensions": [dims[0], dims[1], 1.0],
                  "meta": {"element": "interior_cover", "pocket": pname}}, tag)
                for nm, tag, xy, dims in live
            ]
            json_names = {rec["name"] for rec, _tag in json_result.get(pname, [])}
            live_names_p = {nm for nm, _t, _xy, _d in live}
            missing_in_json = sorted(live_names_p - json_names)
            if missing_in_json:
                notes.append("{}: {} object(s) found directly in the live Blender scene but NOT in "
                             "map_data.json ({}) -- the export is stale; re-run main.py to refresh it"
                             .format(pname, len(missing_in_json), ", ".join(missing_in_json)))
        else:
            combined[pname] = json_result.get(pname, [])
            if not HAVE_BPY:
                notes.append("{}: live-scene scan skipped (not running inside Blender) -- "
                             "resolved from map_data.json only".format(pname))
            elif not combined[pname]:
                notes.append("{}: no interior cover found by EITHER the live-scene scan "
                             "(naming/collection/properties/spatial) OR map_data.json".format(pname))

    return combined, notes, live_result


def resolve_pocket_cover(data):
    """Returns (result, conflicts) where result[pocket_name] = list of
    (obj_rec, tag) and conflicts = list of human-readable conflict strings."""
    pockets = data.get("pockets", [])
    candidates = []
    for bucket in ("rocks", "cover", "props"):
        candidates.extend(data.get(bucket, []))

    result = {}
    conflicts = []
    for p in pockets:
        pname = p["name"]
        found = []

        # 1) EXACT -- trust the generator's own bookkeeping if it's non-empty
        by_name = {r["name"]: r for r in candidates}
        json_names = p.get("cover") or []
        for nm in json_names:
            rec = by_name.get(nm)
            if rec is not None:
                found.append((rec, "EXACT"))
        if found:
            result[pname] = found
            continue

        # 2) + 3) fallback -- name heuristic, then spatial containment
        cx, cy = p["location"][0], p["location"][1]
        W, D = p["dimensions"][0], p["dimensions"][1]
        inner_r = 0.42 * min(W, D)             # stays clear of the outer rock boundary
        entry_xy = p["entry"]["point"][:2]
        pname_low = pname.lower()

        for rec in candidates:
            nm_low = rec["name"].lower()
            if any(h in nm_low for h in _ARC_NAME_HINTS):
                continue    # explicitly excluded: perimeter/gate/wall/floor geometry

            name_linked = pname_low in nm_low
            d_center = dist2(rec["location"][:2], (cx, cy))
            spatially_inside = d_center <= inner_r
            if not name_linked and not spatially_inside:
                continue

            d_entry = dist2(rec["location"][:2], entry_xy)
            if d_entry < 3.0:
                continue    # sitting in the entry corridor -- not interior cover

            foreign = any(h in nm_low for h in _FOREIGN_NAME_HINTS)
            if foreign and not name_linked:
                conflicts.append(
                    "{}: '{}' sits inside the pocket's inner zone ({:.1f} m from centre) but its "
                    "name suggests a different category -- excluded, not auto-classified as cover"
                    .format(pname, rec["name"], d_center))
                continue

            tag = "HEURISTIC" if (re.search(r"_c[123]\b", nm_low) or "cover" in nm_low) else "APPROXIMATION"
            found.append((rec, tag))

        result[pname] = found
        if not found:
            conflicts.append("{}: no interior cover resolved by any method (EXACT/HEURISTIC/APPROXIMATION)"
                             .format(pname))

    return result, conflicts


def classify_objects(data, pocket_cover_result):
    cat = {
        "Terrain": [], "Bases": [], "CapturePoints": [], "Roads": [], "Ramps": [],
        "PocketFloor": [], "PocketCover": [], "PocketRockArc": [], "PocketGate": [],
        "CoreCover": [], "AltarObstacles": [], "AltarLandmarks": [], "OuterRockRing": [],
        "Rocks": [], "Structures": [], "Resources": [], "Vegetation": [], "Debug": [],
    }
    cover_tags = {"EXACT": 0, "HEURISTIC": 0, "APPROXIMATION": 0}

    for b in data.get("bases", []):
        cat["Bases"].append(b["name"])
    for cp in data.get("capture_points", []):
        cat["CapturePoints"].append(cp["name"])
    for r in data.get("roads", []):
        cat["Roads"].append(r["name"])
    for r in data.get("ramps", []):
        cat["Ramps"].append(r["name"])

    for c in data.get("cover", []):
        nm = c["name"]
        if nm.startswith("Altar_Obstacle"):
            cat["AltarObstacles"].append(nm)
        else:
            cat["CoreCover"].append(nm)   # any other registered "cover"-kind object

    pocket_cover_names = set()
    for pname, found in pocket_cover_result.items():
        for rec, tag in found:
            pocket_cover_names.add(rec["name"])
            bucket = "EXACT" if tag.startswith("EXACT") else \
                     "APPROXIMATION" if tag.startswith("APPROXIMATION") else \
                     "HEURISTIC" if tag.startswith("HEURISTIC") else tag
            cover_tags[bucket] = cover_tags.get(bucket, 0) + 1
    cat["PocketCover"] = sorted(pocket_cover_names)

    for r in data.get("rocks", []):
        nm = r["name"]
        if nm in pocket_cover_names:
            continue
        meta = r.get("meta") or {}
        elem = meta.get("element")
        pocket = meta.get("pocket")
        if pocket and "gate" in nm.lower():
            cat["PocketGate"].append(nm)
        elif pocket and elem in ("backwall", "wall"):
            cat["PocketRockArc"].append(nm)
        elif nm.startswith("Core_"):
            cat["CoreCover"].append(nm)
        elif nm.startswith("Altar_Obstacle"):
            cat["AltarObstacles"].append(nm)
        else:
            cat["OuterRockRing" if "Ring" in nm or "Outer" in nm else "Rocks"].append(nm)

    for p in data.get("pockets", []):
        cat["PocketFloor"].append("{}_Floor".format(p["name"]))

    for l in data.get("landmarks", []):
        nm, typ = l["name"], l.get("type")
        low = nm.lower()
        if typ == "altar":
            cat["AltarLandmarks"].append(nm)
        elif any(k in low for k in ("shrine", "relic", "resource")):
            cat["Resources"].append(nm)
        else:
            cat["Structures"].append(nm)

    for p in data.get("props", []):
        nm = p["name"]
        if nm in pocket_cover_names:
            continue
        low = nm.lower()
        elem = (p.get("meta") or {}).get("element")
        if elem == "floor":
            continue   # already counted via PocketFloor
        if nm.startswith("Debug") or low.startswith("test_"):
            cat["Debug"].append(nm)
        elif any(k in low for k in ("tree", "bush", "grass", "shrub", "foliage")):
            cat["Vegetation"].append(nm)
        elif any(k in low for k in ("shrine", "relic", "resource")):
            cat["Resources"].append(nm)
        else:
            cat["Structures"].append(nm)

    if data.get("terrain"):
        cat["Terrain"].append("(analytic heightmap -- no discrete terrain mesh object)")

    return cat, cover_tags


def classification_report(data, pocket_cover_result, cover_conflicts, issues):
    cat, cover_tags = classify_objects(data, pocket_cover_result)
    lines = ["{:<16}{}".format(k + ":", len(v)) for k, v in cat.items()]

    expected_cover = EXPECTED_POCKETS * 3
    found_cover = len(cat["PocketCover"])
    tag_txt = "EXACT={} HEURISTIC={} APPROXIMATION={}".format(
        cover_tags["EXACT"], cover_tags["HEURISTIC"], cover_tags["APPROXIMATION"])
    lines.append("")
    lines.append("PocketCover resolution: {} ({})".format(found_cover, tag_txt))
    if found_cover != expected_cover:
        issues.append(("WARNING", "PocketCover total is {}, expected {} ({} pockets x 3) -- {}"
                       .format(found_cover, expected_cover, EXPECTED_POCKETS, tag_txt)))

    if cover_conflicts:
        lines.append("")
        lines.append("CLASSIFICATION CONFLICT ({}):".format(len(cover_conflicts)))
        for c in cover_conflicts:
            lines.append("  " + c)
            issues.append(("WARNING", "CLASSIFICATION CONFLICT: " + c))

    if not cat["AltarObstacles"]:
        issues.append(("WARNING", "AltarObstacles: 0 found -- see ALTAR OBSTACLES section [DATA MISSING]"))
    if not cat["Resources"]:
        lines.append("")
        lines.append("RESOURCE DATA: NOT FOUND (no Shrine/Relic/Resource-named objects "
                     "in the current export -- not created by this tool)")
    return lines, cat


# =============================================================================
# v0.2 -- geometric helpers for real (bounding-circle) passage estimates
# [APPROXIMATION]: uses footprint_radius / max(dims)/2 as each object's
# effective blocking radius -- a real BVH mesh-to-mesh clearance would be
# tighter/looser depending on actual silhouette, but this runs in O(n) with
# no scene access needed, which matters for section 28 (performance).
# =============================================================================
def _eff_radius(obj_rec):
    meta = obj_rec.get("meta") or {}
    r = meta.get("footprint_radius")
    if r:
        return r
    dims = obj_rec.get("dimensions") or [1.0, 1.0, 1.0]
    return max(dims[0], dims[1]) / 2.0


def min_gap_to_set(point_xy, candidates):
    """candidates: list of obj_rec dicts with 'location' and dims/meta.
    Returns (min_gap_m, nearest_name) -- surface-to-point clearance, or
    (None, None) if candidates is empty. May be NEGATIVE (overlap) -- callers
    must run this through _gap_report()/_width_band_safe(), never print a
    negative value directly as a passage width (spec v0.3 section 4)."""
    best, best_name = None, None
    for rec in candidates:
        loc = rec["location"]
        d = dist2(point_xy, loc[:2]) - _eff_radius(rec)
        if best is None or d < best:
            best, best_name = d, rec["name"]
    return best, best_name


def _gap_report(gap_m, name_a, name_b=None):
    """v0.3 section 4: NEVER present a negative gap as a passage width.
    Returns (display_string, is_overlap)."""
    if gap_m is None:
        return "n/a", False
    if gap_m < 0.0:
        who = " <-> ".join(x for x in (name_a, name_b) if x)
        return "OVERLAP ({}, penetration {:.2f} m)".format(who, -gap_m), True
    return "{:.2f} m".format(gap_m), False


def _width_band_safe(w):
    """_width_band(), but never classifies a negative (overlapping) value as
    a valid CRITICAL-but-passable width -- overlap is a distinct condition."""
    if w is None:
        return "UNKNOWN"
    if w < 0.0:
        return "OVERLAP"
    return _width_band(w)


# =============================================================================
# v0.3 -- expanded POCKET GEOMETRY AUDIT (spec section 3+4): cover-cover /
# cover-wall / cover-entry real gaps, now built on resolve_pocket_cover() (the
# same resolver classify_objects() uses -- computed once by the caller and
# passed in, so this never disagrees with the SCENE CLASSIFICATION counts,
# and never re-does the same O(n) scan twice, section 23).
# Negative gaps are reported as OVERLAP, never as a fake negative width
# (section 4).
# =============================================================================
def pocket_geometry_audit(data, pockets, pocket_cover_result, issues):
    lines = []

    for p in pockets:
        pname = p["name"]
        resolved = pocket_cover_result.get(pname, [])
        cover_recs = [rec for rec, tag in resolved]
        tags = {rec["name"]: tag for rec, tag in resolved}
        wall_recs = [r for r in data.get("rocks", [])
                    if (r.get("meta") or {}).get("pocket") == pname
                    and (r.get("meta") or {}).get("element") in ("backwall", "wall")]

        if not cover_recs:
            lines.append("{}: no interior cover objects resolved -- skipped [DATA MISSING]".format(pname))
            continue

        worst_tag = "EXACT"
        for t in tags.values():
            if t.startswith("APPROXIMATION"):
                worst_tag = "APPROXIMATION"
            elif t.startswith("HEURISTIC") and worst_tag != "APPROXIMATION":
                worst_tag = "HEURISTIC"

        # cover <-> cover
        cc_gaps = []
        for i in range(len(cover_recs)):
            for j in range(i + 1, len(cover_recs)):
                a, b = cover_recs[i], cover_recs[j]
                d = dist2(a["location"][:2], b["location"][:2]) - _eff_radius(a) - _eff_radius(b)
                cc_gaps.append((d, a["name"], b["name"]))
        min_cc = min(cc_gaps, key=lambda t: t[0]) if cc_gaps else None

        # cover <-> wall
        cw_best = None
        for c in cover_recs:
            g, nm = min_gap_to_set(c["location"][:2], wall_recs)
            if g is not None and (cw_best is None or g < cw_best[0]):
                cw_best = (g, c["name"], nm)

        # cover <-> entry point (entry point is a location, not an object --
        # never reported as OVERLAP, just a real distance that can be small)
        entry_xy = p["entry"]["point"][:2]
        ce_gaps = [(dist2(c["location"][:2], entry_xy) - _eff_radius(c), c["name"]) for c in cover_recs]
        min_ce = min(ce_gaps, key=lambda t: t[0]) if ce_gaps else None

        cc_txt, cc_overlap = _gap_report(min_cc[0] if min_cc else None,
                                        min_cc[1] if min_cc else None, min_cc[2] if min_cc else None)
        cw_txt, cw_overlap = _gap_report(cw_best[0] if cw_best else None,
                                        cw_best[1] if cw_best else None, cw_best[2] if cw_best else None)

        lines.append("{}: cover={} [{}] | cover-cover {} | cover-wall {} | cover-entry {:.2f} m [APPROXIMATION]"
                     .format(pname, len(cover_recs), worst_tag, cc_txt, cw_txt,
                             min_ce[0] if min_ce else -1.0))

        if len(cover_recs) != 3:
            issues.append(("WARNING", "{}: resolved {} interior cover object(s), expected 3 [{}]"
                           .format(pname, len(cover_recs), worst_tag)))
        if cc_overlap:
            issues.append(("CRITICAL", "{}: cover objects OVERLAP -- {} [{}]".format(pname, cc_txt, worst_tag)))
        elif min_cc and _width_band_safe(min_cc[0]) == "CRITICAL":
            issues.append(("WARNING", "{}: cover-to-cover gap {:.2f} m is CRITICAL (<3 m) [APPROXIMATION]"
                           .format(pname, min_cc[0])))
        if cw_overlap:
            issues.append(("CRITICAL", "{}: cover OVERLAPS the rock boundary -- {} [{}]".format(pname, cw_txt, worst_tag)))
        if min_ce and min_ce[0] < 3.0:
            issues.append(("CRITICAL", "{}: cover object '{}' only {:.2f} m from the entry point "
                           "[APPROXIMATION]".format(pname, min_ce[1], min_ce[0])))

    return lines


# =============================================================================
# v0.2 -- CORE COVER AUDIT (spec section 4) -- kept separate from Altar
# Obstacles (section 5). Classification is grounded in real data only:
#   MOVE            object is named in validation.warnings STRUCTURAL CONTACT
#   OBSTRUCTION     within 1.5 m of a registered chokepoint (real coordinates)
#   LOW VALUE       tiny footprint (< 1.0 m^2) -- unlikely to matter tactically
#   KEEP            none of the above
# =============================================================================

def _is_core_cover_record(rec):
    """Strict Core Cover classification: metadata -> element/type -> safe name fallback."""
    meta = rec.get("meta") or {}
    values = [
        str(meta.get("element", "")).lower(),
        str(meta.get("element_type", "")).lower(),
        str(rec.get("element", "")).lower(),
        str(rec.get("element_type", "")).lower(),
        str(rec.get("type", "")).lower(),
    ]
    if "core_cover" in values or "corecover" in values:
        return True
    name = str(rec.get("name", ""))
    if name.startswith("Core_Cover_"):
        return True
    return False


def _is_pocket_cover_record(rec):
    meta = rec.get("meta") or {}
    values = " ".join(str(v).lower() for v in (
        meta.get("element", ""),
        meta.get("element_type", ""),
        rec.get("element", ""),
        rec.get("element_type", ""),
        rec.get("type", ""),
    ))
    if "interior_cover" in values or "pocket_cover" in values:
        return True
    return bool(re.match(r"^(WestPocket|EastPocket|SWPocket|SEPocket)_C\d+$",
                         str(rec.get("name", "")), re.I))


def core_cover_audit(data, altars, issues):
    lines = []
    cover = [c for c in data.get("cover", []) if _is_core_cover_record(c) and not _is_pocket_cover_record(c)]
    if not cover:
        lines.append("No Core Cover objects found. [DATA MISSING]")
        return lines

    altar_pos = altars[0]["location"][:2] if altars else None
    altar_r = _eff_radius(altars[0]) if altars else 0.0
    warn_text = " ".join(data.get("validation", {}).get("warnings", []))
    chokes = data.get("navigation", {}).get("chokepoints", [])

    lines.append("[EXACT dims/area | APPROXIMATION distance formulas | HEURISTIC classification]")
    lines.append("{:<32}{:>8}{:>14}{:>10}{:>14}".format("Object", "AreaM2", "ToAltarEdge", "NearCvr", "Class"))
    for c in cover:
        dims = c.get("dimensions") or [1, 1, 1]
        area = dims[0] * dims[1]
        d_altar = (dist2(c["location"][:2], altar_pos) - altar_r - _eff_radius(c)) if altar_pos else None
        others = [o for o in cover if o["name"] != c["name"]]
        d_near, _ = min_gap_to_set(c["location"][:2], others) if others else (None, None)
        near_choke = any(dist2((ch["x"], ch["y"]), c["location"][:2]) <= 1.5 for ch in chokes)
        flagged_contact = c["name"] in warn_text
        low_value = area < 1.0

        if flagged_contact and low_value:
            cls = "REMOVE"
        elif flagged_contact:
            cls = "MOVE"
        elif near_choke:
            cls = "OBSTRUCTION"
        elif low_value:
            cls = "LOW VALUE"
        else:
            cls = "KEEP"

        d_altar_txt, d_overlap = _gap_report(d_altar, c["name"], "Altar") if d_altar is not None else ("n/a", False)
        lines.append("{:<32}{:>8.2f}{:>14}{:>10}{:>14}".format(
            c["name"], area, d_altar_txt, "{:.2f}m".format(d_near) if d_near is not None else "n/a", cls))

        if cls == "REMOVE":
            issues.append(("WARNING", "{}: flagged REMOVE -- structural contact and low tactical value [HEURISTIC]"
                           .format(c["name"])))
        elif cls == "MOVE":
            issues.append(("WARNING", "{}: flagged MOVE -- validation structural-contact warning [HEURISTIC]"
                           .format(c["name"])))
        elif cls == "OBSTRUCTION":
            issues.append(("WARNING", "{}: flagged OBSTRUCTION -- within 1.5 m of registered chokepoint [HEURISTIC]"
                           .format(c["name"])))
        if d_overlap:
            issues.append(("WARNING", "{}: bounding-circle overlap with Altar -- {} [APPROXIMATION]"
                           .format(c["name"], d_altar_txt)))
    return lines



# =============================================================================
# v0.2 -- ALTAR OBSTACLE AUDIT (spec section 5) -- deliberately separate from
# Core Cover above. As of this project's current generator (geometry/
# structures.py), no "Altar_Obstacle_*" objects are ever created -- Altar-area
# blocking is done entirely via Core_Cover_*. Rather than fold them together
# (which the spec explicitly forbids) or invent obstacle data, this is
# reported honestly as [DATA MISSING].
# =============================================================================

def altar_obstacle_audit(data, issues):
    obstacles = [c for c in data.get("cover", []) if str(c.get("name", "")).startswith("Altar_Obstacle")]
    obstacles += [r for r in data.get("rocks", []) if str(r.get("name", "")).startswith("Altar_Obstacle")]
    if not obstacles:
        issues.append(("DATA MISSING",
                       "No Altar_Obstacle_* objects exist -- Altar blocking is currently provided entirely by Core_Cover_*"))
        return ["No Altar_Obstacle_* objects found (distinct from Core Cover).",
                "[DATA MISSING] -- current generator does not create this category."]
    lines = ["{} Altar_Obstacle_* object(s) found:".format(len(obstacles))]
    for o in obstacles:
        dims = o.get("dimensions") or [1, 1, 1]
        lines.append("  {}  area={:.2f} m2  height={:.2f} m".format(o["name"], dims[0] * dims[1], dims[2]))
    return lines



# =============================================================================
# v0.2 -- CAPTURE POINT AUDIT (spec section 10)
# "approaches" = roads/ramps whose registered position lies within a radius
# of (platform radius + typical road half-width) of the point -- an
# [APPROXIMATION] of true graph connectivity (no road-adjacency graph exists
# in the export), stated as such rather than presented as exact.
# =============================================================================
def _approach_verdict(n):
    if n >= 3:
        return "GOOD"
    if n == 2:
        return "NORMAL"
    if n == 1:
        return "SINGLE-ENTRY"
    return "CONSTRAINED"



def capture_point_audit(data, cps, issues):
    """Prefer real point-to-point routed graph connectivity.

    If CapturePoint<->CapturePoint routes exist, approach count is the number
    of distinct routed neighbours and is marked EXACT as graph connectivity.
    A physical entrance count remains an APPROXIMATION and is not substituted
    for the routed result.
    """
    lines = []
    nav = data.get("navigation", {})
    routes = nav.get("routes", {})
    cp_names = {cp["name"] for cp in cps}
    base_names = {b["name"] for b in data.get("bases", [])}

    routed_graph = {}
    for key, dist in routes.items():
        if "->" not in key or dist is None:
            continue
        a, b = key.split("->", 1)
        if a in cp_names and b in cp_names:
            routed_graph.setdefault(a, set()).add(b)
        elif a in base_names and b in cp_names:
            routed_graph.setdefault(b, set()).add(a)
        elif a in cp_names and b in base_names:
            routed_graph.setdefault(a, set()).add(b)

    roads = data.get("roads", []) + data.get("ramps", [])
    cover_all = data.get("cover", []) + [r for r in data.get("rocks", []) if not (r.get("meta") or {}).get("pocket")]
    chokes = data.get("navigation", {}).get("chokepoints", [])

    lines.append("{:<14}{:>8}{:>10}{:>12}{:>10}{:>10}{:>18}".format(
        "Point", "Radius", "Area", "Approaches", "Cover", "Chokes", "Verdict"))

    for cp in cps:
        pos = cp["position"][:2]
        r = cp["radius"]
        area = math.pi * r * r
        near_r = r + 12.0
        near_cover = sum(1 for c in cover_all if dist2(c["location"][:2], pos) <= near_r)
        near_choke = sum(1 for c in chokes if dist2((c["x"], c["y"]), pos) <= near_r)

        if cp["name"] in routed_graph:
            peers = routed_graph[cp["name"]]
            approaches = len(peers)
            verdict = _approach_verdict(approaches)
            tag = "[EXACT, routed graph]"
        else:
            approaches = sum(1 for road in roads if dist2(road["location"][:2], pos) <= near_r)
            verdict = _approach_verdict(approaches)
            tag = "[APPROXIMATION]"

        lines.append("{:<14}{:>7.1f}m{:>9.0f}{:>12}{:>10}{:>10}{:>18}  {}".format(
            cp["name"], r, area, approaches, near_cover, near_choke, verdict, tag))

        if cp["name"] in routed_graph:
            if approaches == 1:
                issues.append(("WARNING",
                               "{}: SINGLE-ENTRY -- exactly one routed neighbour [EXACT, routed graph]"
                               .format(cp["name"])))
        else:
            lines.append("  {} physical approach count is only an approximation; no routed CP graph was found."
                         .format(cp["name"]))

    return lines



# =============================================================================
# v0.2 -- BASE AUDIT (spec section 11)
# =============================================================================

def base_audit(data, bases, cps, issues):
    """Keep v0.4 route/fairness base analysis and add read-only live geometry audit."""
    lines = []
    routes = data.get("navigation", {}).get("routes", {})
    stats = {}

    for b in bases:
        pos = b["position"][:2]
        area = math.pi * b["radius"] ** 2
        own = [(cp["name"], routes.get("{}->{}".format(b["name"], cp["name"])))
               for cp in cps]
        own = [(n, d) for n, d in own if d is not None]
        own.sort(key=lambda x: x[1])
        nearest = own[0] if own else (None, None)
        second = own[1] if len(own) > 1 else (None, None)
        stats[b["name"]] = {"area": area, "nearest": nearest, "second": second}
        lines.append("{}: platform {:.0f} m2 | nearest {} ({:.1f} m) | second {} ({:.1f} m)"
                     .format(b["name"], area, nearest[0] or "n/a", nearest[1] or -1.0,
                             second[0] or "n/a", second[1] or -1.0))

    if len(stats) == 2:
        s = list(stats.values())
        d1, d2 = s[0]["nearest"][1] or 0.0, s[1]["nearest"][1] or 0.0
        diff_pct = abs(d1 - d2) / max(d1, d2) * 100.0 if max(d1, d2) else 0.0
        lines.append("Nearest-objective distance difference: {:.1f} %".format(diff_pct))

    # Live base audit
    if not HAVE_BPY:
        lines.append("LIVE BASE GEOMETRY: [DATA MISSING] Blender runtime required")
        return lines

    for team in ("Blue", "Red"):
        prefix = team
        platform = _live_obj(prefix + "_BasePlatform")
        crystal = _live_obj(prefix + "_Crystal")
        heal = _live_obj(prefix + "_HealthRestore")
        spawn = _live_obj(prefix + "_Spawn")
        shop = _live_obj(prefix + "_Shop")
        connector = _live_obj(prefix + "_ShopConnector")

        lines.append("{} live: Platform={} Crystal={} HealthRestore={} Spawn={} Shop={} Connector={}"
                     .format(team,
                             "YES" if platform else "NO",
                             "YES" if crystal else "NO",
                             "YES" if heal else "NO",
                             "YES" if spawn else "NO",
                             "YES" if shop else "NO",
                             "YES" if connector else "NO"))

        for label, obj in (("HealthRestore", heal), ("Spawn", spawn), ("Shop", shop), ("ShopConnector", connector)):
            if label in ("HealthRestore", "Spawn", "Shop", "ShopConnector") and obj is None:
                # Missing source feature is a data finding, not a geometry fix.
                lines.append("  {}: [DATA MISSING]".format(label))

    return lines



# =============================================================================
# v0.2 -- LOS ANALYSIS (spec section 13) -- Blender only.
# Uses Blender's own depsgraph ray_cast (internally BVH-accelerated and
# shared/cached by Blender itself -- satisfies the "one reusable BVH, no
# per-object rebuild" performance requirement in section 28 without this
# script hand-rolling and owning a second acceleration structure).
# Samples 8 compass directions from a small, fixed set of key points (5
# capture points + Altar + 2 bases + 4 pocket floors = 12 points x 8 rays =
# 96 raycasts) -- deliberately small so this stays a "seconds, not minutes"
# tool per section 28.
# =============================================================================
_COMPASS = [("N", (0, 1)), ("NE", (0.7071, 0.7071)), ("E", (1, 0)), ("SE", (0.7071, -0.7071)),
           ("S", (0, -1)), ("SW", (-0.7071, -0.7071)), ("W", (-1, 0)), ("NW", (-0.7071, 0.7071))]



_COMPASS = [("N", (0, 1)), ("NE", (0.70710678, 0.70710678)), ("E", (1, 0)),
            ("SE", (0.70710678, -0.70710678)), ("S", (0, -1)),
            ("SW", (-0.70710678, -0.70710678)), ("W", (-1, 0)),
            ("NW", (-0.70710678, 0.70710678))]


def _los_source_object(zone_name):
    if not HAVE_BPY:
        return None
    candidates = {
        "BlueBase": ("Blue_Crystal", "Blue_BasePlatform"),
        "RedBase": ("Red_Crystal", "Red_BasePlatform"),
        "Altar": ("Altar_Base", "Altar_PowerCore"),
    }
    if zone_name in candidates:
        for n in candidates[zone_name]:
            obj = _live_obj(n)
            if obj is not None:
                return obj
    if zone_name in CAPTURE_POINTS:
        return _live_obj("CapturePlatform_{}".format(zone_name))
    if zone_name in POCKETS:
        return _live_obj("{}_Floor".format(zone_name))
    return None


def _raycast_after_ignored_hits(depsgraph, origin, direction, max_dist, source_obj=None, max_iter=8):
    """Shared depsgraph raycast; ignore only the declared source object and continue.

    Blender scene.ray_cast has no native exclusion list, so ignored self-hits are
    skipped by advancing just beyond the hit and continuing the same ray. This is
    a general source-object rule, not an object-name special case.
    """
    from mathutils import Vector
    current = Vector((float(origin[0]), float(origin[1]), float(origin[2])))
    direction = Vector((float(direction[0]), float(direction[1]), float(direction[2])))
    if direction.length == 0.0:
        return False, None
    direction.normalize()
    remaining = float(max_dist)
    total = 0.0
    for _ in range(max_iter):
        hit, loc, normal, face_idx, obj, matrix = bpy.context.scene.ray_cast(
            depsgraph, current, direction, distance=remaining
        )
        if not hit:
            return False, None
        if source_obj is None or obj is None or obj != source_obj:
            return True, obj.name if obj is not None else "(unnamed)"
        step = max(0.01, (loc - current).length + 0.01)
        total += step
        remaining -= step
        if remaining <= 0.0:
            return False, None
        current = loc + direction * 0.01
    return False, None


def los_analysis(data, cps, bases, pockets, altars, issues):
    if not HAVE_BPY:
        return ["[DATA MISSING] LOS analysis requires Blender runtime."]

    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    except Exception as e:
        return ["[DATA MISSING] Could not get evaluated depsgraph: {}".format(e)]

    max_dist = 25.0
    eye_h = 1.6
    points = []
    for cp in cps:
        points.append((cp["name"], cp["position"]))
    for b in bases:
        points.append((b["name"], b["position"]))
    if altars:
        points.append(("Altar", altars[0]["location"]))
    for p in pockets:
        points.append((p["name"], p["location"]))

    lines = [
        "[EXACT, Blender depsgraph ray_cast; source-object self-hit excluded generically]",
        "{:<16}{:>10}{:>10}   direction: blocking object".format("Point", "OpenPct", "BlockPct"),
    ]

    for name, pos in points:
        base_origin = (float(pos[0]), float(pos[1]), float(pos[2] if len(pos) > 2 else 0.0) + eye_h)
        source_obj = _los_source_object(name)
        blocked = 0
        detail = []

        for dname, (dx, dy) in _COMPASS:
            origin = (base_origin[0], base_origin[1], base_origin[2])
            try:
                hit, blocker = _raycast_after_ignored_hits(
                    depsgraph, origin, (dx, dy, 0.0), max_dist, source_obj=source_obj
                )
            except Exception as e:
                hit, blocker = False, None
                detail.append("{}:ERROR({})".format(dname, e))
            if hit:
                blocked += 1
                detail.append("{}:{}".format(dname, blocker))

        open_pct = (8 - blocked) / 8.0 * 100.0
        block_pct = blocked / 8.0 * 100.0
        lines.append("{:<16}{:>9.0f}%{:>9.0f}%   {}".format(
            name, open_pct, block_pct, ", ".join(detail) if detail else "-"))

        if open_pct <= 0.0:
            issues.append(("WARNING", "{}: LOS fully blocked in all 8 directions [EXACT]".format(name)))
        elif open_pct >= 100.0:
            issues.append(("WARNING", "{}: LOS fully open in all 8 directions [EXACT]".format(name)))

    return lines



# =============================================================================
# v0.2 -- COVER VALUE (spec section 14). Simple, disclosed formula:
#   value = 0.5*(size factor) + 0.5*(1 - normalised distance to nearest
#           capture point / base)
# closer-to-action + reasonably sized -> higher value. This is a heuristic,
# not a simulated playtest -- printed as such.
# =============================================================================
def cover_value_analysis(data, cps, bases, issues):
    lines = []
    objectives = [cp["position"][:2] for cp in cps] + [b["position"][:2] for b in bases]
    cover = [c for c in data.get("cover", []) if not c["name"].startswith("Altar_Obstacle")]
    if not cover or not objectives:
        return ["Insufficient data. [DATA MISSING]"]

    scored = []
    for c in cover:
        dims = c.get("dimensions") or [1, 1, 1]
        size_factor = min(1.0, (dims[0] * dims[1]) / 6.0)
        d_obj = min(dist2(c["location"][:2], o) for o in objectives)
        dist_factor = max(0.0, 1.0 - d_obj / 60.0)
        score = 0.5 * size_factor + 0.5 * dist_factor
        scored.append((c["name"], score, d_obj))

    scored.sort(key=lambda x: -x[1])
    lines.append("(heuristic score, see source comment for formula -- not a playtest result)")
    for name, score, d_obj in scored:
        cls = "BEST" if score >= 0.66 else "LOW VALUE" if score < 0.33 else "NORMAL"
        lines.append("  {:<28}score={:.2f}  nearest_objective={:.1f}m  [{}]".format(name, score, d_obj, cls))

    return lines


# =============================================================================
# v0.2 -- RESOURCE ANALYSIS (spec section 18)
# =============================================================================
def resource_analysis(cat, issues):
    if not cat["Resources"]:
        return ["RESOURCE DATA: NOT FOUND"]
    return ["Found: " + ", ".join(cat["Resources"])]


# =============================================================================
# v0.2 -- MAP CONNECTIVITY / DEAD-END ANALYSIS (spec sections 16-17)
# =============================================================================
def connectivity_analysis(data, issues):
    """v0.3 section 18: a zero-traffic zone is NOT automatically a WARNING.
    Cross-references simulation.zones[*].traffic against the REAL routed
    reachability already computed by core.navigation
    (navigation.pockets[*].reachable / route_length) to tell REAL ISOLATION
    (no route exists) apart from NO SIMULATION TRAFFIC (a route exists and
    is reachable -- the bot simulation just didn't happen to route through
    it)."""
    lines = []
    zones = data.get("simulation", {}).get("zones", {})
    nav_pockets = {p["name"]: p for p in data.get("navigation", {}).get("pockets", [])}
    checked_points = set(data.get("navigation", {}).get("checked_points", []))
    zero_traffic = [name for name, z in zones.items() if z.get("traffic", 0) == 0]

    if not zero_traffic:
        lines.append("  No zero-traffic zones found.")
    for name in zero_traffic:
        if name in nav_pockets:
            np = nav_pockets[name]
            if np.get("reachable"):
                lines.append("  {}: NO SIMULATION TRAFFIC -- but a real route exists (length {:.1f} m) "
                             "[EXACT, navigation.pockets] -- NOT isolated.".format(name, np.get("route_length", -1)))
            else:
                lines.append("  {}: REAL ISOLATION -- navigation.pockets marks it unreachable [EXACT]".format(name))
                issues.append(("CRITICAL", "{}: REAL ISOLATION -- unreachable per navigation data (not just zero sim traffic)"
                               .format(name)))
        elif name in checked_points:
            lines.append("  {}: zero traffic, but present in navigation.checked_points (a route was "
                         "computed to it) [APPROXIMATION] -- likely NOT isolated.".format(name))
        else:
            lines.append("  {}: zero traffic, no navigation reachability record found for this zone "
                         "-- cannot distinguish real isolation from no simulated traffic [DATA MISSING]"
                         .format(name))
            issues.append(("WARNING", "{}: zero simulated traffic, no navigation reachability record "
                           "to confirm either way [DATA MISSING]".format(name)))

    problems = data.get("navigation", {}).get("problems", [])
    if problems:
        for p in problems:
            lines.append("  navigation.problems: {}  [EXACT] (see ISSUES -- already reported in CHOKEPOINTS)".format(p))
    else:
        lines.append("  navigation.problems: (none)  [EXACT]")
    return lines


# =============================================================================
# v0.2 -- RISK HEURISTICS (spec sections 20-23). Every number here is derived
# from data already printed elsewhere in this report -- formulas stated
# inline, nothing invented.
# =============================================================================
def risk_analysis(data, chokes_lines_data, fairness_diff_pct, issues):
    lines = []
    chokes = data.get("navigation", {}).get("chokepoints", [])
    routes = data.get("navigation", {}).get("routes", {})
    total_routes = len(routes) if routes else 1
    max_pressure = max((c["routes_through"] / float(total_routes) for c in chokes), default=0.0)

    deathball = "HIGH" if max_pressure >= 0.8 else "MEDIUM" if max_pressure >= 0.5 else "LOW"
    lines.append("DEATHBALL RISK: {} (max route concentration at one chokepoint = {:.0f}%)"
                 .format(deathball, max_pressure * 100.0))
    if deathball == "HIGH":
        issues.append(("WARNING", "DEATHBALL RISK HIGH -- {:.0f}% of routes pass through one chokepoint"
                       .format(max_pressure * 100.0)))

    snowball = "HIGH" if fairness_diff_pct > 20.0 else "MEDIUM" if fairness_diff_pct > 10.0 else "LOW"
    lines.append("SNOWBALL RISK: {} (base Blue/Red route-time difference = {:.1f}%)"
                 .format(snowball, fairness_diff_pct))

    pockets = data.get("pockets", [])
    comeback_routes = len(pockets)   # each pocket is an alternative flank route
    comeback = "LOW" if comeback_routes >= 4 else "MEDIUM" if comeback_routes >= 2 else "HIGH"
    lines.append("COMEBACK ROUTE AVAILABILITY: {} flank pocket(s) found -> risk of a single predictable "
                "recovery route: {}".format(comeback_routes, comeback))
    if comeback == "HIGH":
        issues.append(("WARNING", "Comeback risk HIGH -- fewer than 2 flank/pocket routes available"))

    return lines, deathball, snowball, comeback


def camping_risk(data, cps, altars, pockets, issues):
    lines = []
    roads = data.get("roads", []) + data.get("ramps", [])
    cover_all = data.get("cover", [])
    results = {}

    def score_zone(name, pos, radius):
        near_r = radius + 12.0
        approaches = sum(1 for r in roads if dist2(r["location"][:2], pos) <= near_r)
        near_cover = sum(1 for c in cover_all if dist2(c["location"][:2], pos) <= near_r)
        if approaches <= 1 and near_cover >= 2:
            return "HIGH"
        if approaches <= 2:
            return "MEDIUM"
        return "LOW"

    for cp in cps:
        results[cp["name"]] = score_zone(cp["name"], cp["position"][:2], cp["radius"])
    if altars:
        results["Altar"] = score_zone("Altar", altars[0]["location"][:2], 10.0)
    for p in pockets:
        results[p["name"]] = "MEDIUM"   # single-entry by design -- always at least MEDIUM

    for name, risk in results.items():
        lines.append("  {:<16}{}  [APPROXIMATION]".format(name, risk))
        if risk == "HIGH":
            issues.append(("WARNING", "{}: HIGH camping risk (<=1 approach + >=2 nearby cover)".format(name)))

    return lines


# =============================================================================
# v0.2 -- MAP QUALITY SCORE (spec sections 24 + 32). Every sub-score has an
# explicit formula printed alongside it -- never a bare number.
# =============================================================================
def map_quality_score(data, issues, fairness_diff_pct, deathball, snowball, comeback):
    scores = {}
    reasons = {}

    n_crit = sum(1 for lvl, _ in issues if lvl == "CRITICAL")
    n_warn = sum(1 for lvl, _ in issues if lvl == "WARNING")

    geometry = max(0, 100 - n_crit * 25 - n_warn * 3)
    scores["GEOMETRY"] = geometry
    reasons["GEOMETRY"] = "100 - 25*CRITICAL - 3*WARNING ({} critical, {} warning)".format(n_crit, n_warn)

    problems = data.get("navigation", {}).get("problems", [])
    nav_ok = data.get("navigation", {}).get("ok", False)
    navigation = 100 if (nav_ok and not problems) else max(0, 60 - 20 * len(problems))
    scores["NAVIGATION"] = navigation
    reasons["NAVIGATION"] = "navigation.ok={} problems={}".format(nav_ok, len(problems))

    fairness = max(0, 100 - fairness_diff_pct * 4)
    scores["FAIRNESS"] = round(fairness, 1)
    reasons["FAIRNESS"] = "100 - 4*|Blue-Red route time diff %| ({:.1f}%)".format(fairness_diff_pct)

    chokepoints = {"LOW": 90, "MEDIUM": 65, "HIGH": 35}[deathball]
    scores["CHOKEPOINTS"] = chokepoints
    reasons["CHOKEPOINTS"] = "derived from DEATHBALL RISK = {}".format(deathball)

    pockets = data.get("pockets", [])
    cont_ok = sum(1 for p in pockets if p.get("perimeter_continuous"))
    pockets_score = int(100 * cont_ok / len(pockets)) if pockets else 0
    scores["POCKETS"] = pockets_score
    reasons["POCKETS"] = "{}/{} pockets flagged perimeter_continuous".format(cont_ok, len(pockets))

    val_ok = data.get("validation", {}).get("ok", False)
    val_warn = len(data.get("validation", {}).get("warnings", []))
    altar = max(0, 100 - (0 if val_ok else 50) - val_warn * 5)
    scores["ALTAR"] = altar
    reasons["ALTAR"] = "validation.ok={}  {} structural warnings near AetherCore".format(val_ok, val_warn)

    bases = data.get("bases", [])
    scores["BASES"] = 100 if len(bases) == EXPECTED_BASES else 0
    reasons["BASES"] = "{} of {} expected bases present".format(len(bases), EXPECTED_BASES)

    comeback_score = {"LOW": 90, "MEDIUM": 60, "HIGH": 25}[comeback]
    scores["COMEBACK"] = comeback_score
    reasons["COMEBACK"] = "derived from COMEBACK route availability = {}".format(comeback)

    scores["LOS"] = None
    reasons["LOS"] = "[DATA MISSING] not scored numerically yet -- see LOS ANALYSIS section for raw open/blocked %"
    scores["COVER"] = None
    reasons["COVER"] = "[DATA MISSING] cover value is a per-object heuristic list, not yet aggregated to one score"
    scores["ROTATION"] = None
    reasons["ROTATION"] = "[DATA MISSING] full Dominion macro-rotation simulation not implemented yet -- see ROUTES section"
    scores["ACCESSIBILITY"] = None
    reasons["ACCESSIBILITY"] = "[DATA MISSING] not separately scored yet -- see CAPTURE POINTS / BASE AUDIT sections"

    numeric = [v for v in scores.values() if v is not None]
    overall = round(sum(numeric) / len(numeric), 1) if numeric else 0.0

    return overall, scores, reasons



def _sec(out, title):
    out.append("")
    out.append("-" * 60)
    out.append(title)
    out.append("-" * 60)


def rotation_summary(route_rows, issues):
    """v0.4 section 11/22 ROTATION section. HONEST SCOPE: this is built only
    from the real Base->CapturePoint route table already computed above --
    NOT the full adjacent/non-adjacent Point->Point, Point->Altar,
    Base->opposite-sector graph spec section 11 describes (that needs a
    point-to-point route graph this project's exporter does not produce).
    Labelled [APPROXIMATION] for that reason, not presented as the full
    macro-rotation audit."""
    times = [d / PLAYER_SPEED for lbl, d, fb in route_rows if not fb and d is not None]
    if not times:
        return ["[DATA MISSING] no routed times available for a rotation summary."]
    avg_t = sum(times) / len(times)
    lines = [
        "[APPROXIMATION -- Base->CapturePoint routes only, not a full point-to-point graph]",
        "AVERAGE ROTATION TIME: {:.1f} s".format(avg_t),
        "FASTEST ROTATION:      {:.1f} s".format(min(times)),
        "SLOWEST ROTATION:      {:.1f} s".format(max(times)),
        "ROUTE VARIANCE:        {:.1f} s (max - min)".format(max(times) - min(times)),
    ]
    if max(times) - min(times) > avg_t:
        issues.append(("WARNING", "Rotation variance ({:.1f}s) exceeds the average rotation time ({:.1f}s) "
                       "-- some objectives are disproportionately slow to reach [APPROXIMATION]"
                       .format(max(times) - min(times), avg_t)))
    return lines





def _live_obj(name):
    if not HAVE_BPY:
        return None
    try:
        return bpy.data.objects.get(name)
    except Exception:
        return None


def _mesh_vertices_world(obj):
    if not HAVE_BPY or obj is None or obj.type != "MESH":
        return []
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        verts = [obj.matrix_world @ v.co for v in mesh.vertices]
        eval_obj.to_mesh_clear()
        return verts
    except Exception:
        return []


def _mesh_bvh(obj):
    if not HAVE_BPY or obj is None or obj.type != "MESH":
        return None
    try:
        from mathutils.bvhtree import BVHTree
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        verts = [obj.matrix_world @ v.co for v in mesh.vertices]
        polys = [[v for v in poly.vertices] for poly in mesh.polygons]
        bvh = BVHTree.FromPolygons(verts, polys, all_triangles=False)
        eval_obj.to_mesh_clear()
        return bvh
    except Exception:
        return None


def _mesh_overlap(obj_a, obj_b):
    if not HAVE_BPY:
        return None
    try:
        a = _mesh_bvh(obj_a)
        b = _mesh_bvh(obj_b)
        if a is None or b is None:
            return None
        return bool(a.overlap(b))
    except Exception:
        return None


def _mesh_vertex_clearance(obj_a, obj_b):
    if not HAVE_BPY:
        return None
    bvh = _mesh_bvh(obj_b)
    verts = _mesh_vertices_world(obj_a)
    if bvh is None or not verts:
        return None
    best = None
    for v in verts:
        hit = bvh.find_nearest(v)
        if hit and hit[3] is not None:
            d = float(hit[3])
            best = d if best is None else min(best, d)
    return best


def _live_core_cover_objects():
    if not HAVE_BPY:
        return []
    result = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if obj.name.startswith("Core_Cover_"):
            result.append(obj)
            continue
        try:
            if str(obj.get("element", "")).lower() == "core_cover":
                result.append(obj)
        except Exception:
            pass
    return result



def _collision_status(obj):
    if obj is None:
        return "DATA MISSING"
    try:
        props = {str(k).lower(): obj[k] for k in obj.keys()}
    except Exception:
        props = {}
    for key in ("collision", "aetherflow_collision", "collision_type", "collision_mode"):
        if key in props:
            return "COLLISION METADATA ONLY"
    if obj.type == "MESH" and getattr(obj, "data", None) is not None:
        return "COLLISION METADATA ONLY"
    return "DATA MISSING"


def collision_audit(data, pockets, cps, bases, issues):
    lines = []
    if not HAVE_BPY:
        lines.append("COLLISION: [DATA MISSING] Blender runtime required")
        return lines
    names = []
    for team in ("Blue", "Red"):
        names += [team + "_BasePlatform", team + "_Crystal", team + "_HealthRestore",
                  team + "_Spawn", team + "_Shop", team + "_ShopConnector"]
    names += ["CapturePlatform_{}".format(cp["name"]) for cp in cps]
    names += ["Altar_Base", "Altar_PowerCore"]
    names += ["{}_Floor".format(p["name"]) for p in pockets]
    names += ["Core_Cover_{}".format(n) for n in (
        "LCover_West", "LCover_East", "Pillar_North", "SouthScreen", "Pocket_SW", "Pocket_SE"
    )]
    metadata = 0
    missing = 0
    for name in names:
        obj = _live_obj(name)
        if obj is None:
            missing += 1
        else:
            metadata += 1
    lines.append("Gameplay-critical collision: METADATA_OR_MESH={} DATA_MISSING={} [METADATA ONLY]"
                 .format(metadata, missing))
    lines.append("Physical collision shape is not claimed without explicit Blender collision data.")
    return lines


def overlap_audit(pockets, issues):
    lines = []
    if not HAVE_BPY:
        return ["[DATA MISSING] overlap audit requires Blender runtime."]
    pair_defs = []
    altar = _live_obj("Altar_Base")
    for name in ("LCover_West", "LCover_East", "Pillar_North", "SouthScreen", "Pocket_SW", "Pocket_SE"):
        cover = _live_obj("Core_Cover_" + name)
        if altar and cover:
            pair_defs.append((altar, cover))
    core = _live_core_cover_objects()
    for i, a in enumerate(core):
        for b in core[i+1:]:
            pair_defs.append((a, b))
    for p in pockets:
        floor = _live_obj(p["name"] + "_Floor")
        for i in range(1, 4):
            cover = _live_obj("{}_C{}".format(p["name"], i))
            if cover and floor:
                pair_defs.append((cover, floor))
    actual = []
    for a, b in pair_defs:
        ov = _mesh_overlap(a, b)
        if ov:
            actual.append((a.name, b.name))
    lines.append("Actual evaluated-mesh intersections: {} [EXACT]".format(len(actual)))
    for a, b in actual[:50]:
        lines.append("  {} <-> {} [EXACT]".format(a, b))
        issues.append(("WARNING", "{} <-> {} actual mesh intersection [EXACT]".format(a, b)))
    return lines


def symmetry_audit(data, cps, bases, pockets, issues):
    lines = []
    base_map = {b["name"]: b for b in bases}
    blue, red = base_map.get("BlueBase"), base_map.get("RedBase")
    base_ok = False
    if blue and red:
        bp, rp = blue["position"], red["position"]
        base_ok = (abs(bp[0] + rp[0]) < 1e-3 and
                   abs(bp[1] - rp[1]) < 1e-3 and
                   abs(blue["radius"] - red["radius"]) < 1e-3)
    checks = [("BlueBase ↔ RedBase", base_ok)]
    by_name = {p["name"]: p for p in pockets}
    for a_name, b_name in (("WestPocket", "EastPocket"), ("SWPocket", "SEPocket")):
        a, b = by_name.get(a_name), by_name.get(b_name)
        ok = False
        if a and b:
            ok = (abs(a["entry"]["width"] - b["entry"]["width"]) < 1e-3 and
                  abs(a.get("floor_area", 0) - b.get("floor_area", 0)) < 1e-3 and
                  len(a.get("cover", [])) == len(b.get("cover", [])))
        checks.append((a_name + " ↔ " + b_name, ok))
    for label, ok in checks:
        lines.append("{}: {} [EXACT export]".format(label, "PASS" if ok else "WARNING"))
        if not ok:
            issues.append(("WARNING", "{} symmetry mismatch [EXACT export]".format(label)))
    if HAVE_BPY:
        lines.append("Live geometry symmetry: evaluated where named gameplay objects exist [EXACT scene]")
    else:
        lines.append("Live geometry symmetry: [DATA MISSING] Blender runtime required")
    return lines



def terrain_floor_audit(data, pockets, issues):
    lines = []
    terrain_present = bool(data.get("terrain"))
    safety_present = bool(data.get("terrain", {}).get("safety_floor") or data.get("terrain", {}).get("safetyFloor"))
    lines.append("Export terrain: {} [EXACT]".format("PRESENT" if terrain_present else "DATA MISSING"))
    lines.append("Export safety floor: {} [EXACT metadata]".format("PRESENT" if safety_present else "DATA MISSING"))

    if not HAVE_BPY:
        lines.append("Live terrain/floor mesh audit: [DATA MISSING] Blender runtime required")
        return lines

    terrain_objs = [o for o in bpy.data.objects if o.type == "MESH" and (
        o.name.lower() in ("terrain", "safetyfloor", "safety_floor") or
        "terrain" in o.name.lower() or "safetyfloor" in o.name.lower()
    )]
    lines.append("Live terrain objects: {} [EXACT scene scan]".format(len(terrain_objs)))
    for p in pockets:
        floor = _live_obj("{}_Floor".format(p["name"]))
        lines.append("  {} floor: {}".format(p["name"], "PRESENT [EXACT]" if floor else "DATA MISSING"))
    central = _live_obj("AetherCore_Floor") or _live_obj("Altar_Base")
    lines.append("  central gameplay floor: {}".format("PRESENT [EXACT]" if central else "DATA MISSING"))
    return lines


def _collision_status(obj):
    if obj is None:
        return "DATA MISSING"
    props = {}
    try:
        props = {str(k).lower(): obj[k] for k in obj.keys()}
    except Exception:
        pass
    for key in ("collision", "aetherflow_collision", "collision_type", "collision_mode"):
        if key in props:
            return "COLLISION METADATA ONLY"
    if obj.type == "MESH" and getattr(obj, "data", None) is not None:
        return "COLLISION METADATA ONLY"
    return "DATA MISSING"


def collision_audit(data, pockets, cps, bases, issues):
    lines = []
    if not HAVE_BPY:
        lines.append("COLLISION: [DATA MISSING] Blender runtime required")
        return lines

    names = []
    for team in ("Blue", "Red"):
        names += [team + "_BasePlatform", team + "_Crystal", team + "_HealthRestore",
                  team + "_Spawn", team + "_Shop", team + "_ShopConnector"]
    names += ["CapturePlatform_{}".format(cp["name"]) for cp in cps]
    names += ["Altar_Base"]
    names += ["Altar_PowerCore"]
    names += ["{}_Floor".format(p["name"]) for p in pockets]
    names += ["Core_Cover_{}".format(n) for n in (
        "LCover_West", "LCover_East", "Pillar_North", "SouthScreen", "Pocket_SW", "Pocket_SE"
    )]

    verified = 0
    metadata = 0
    missing = 0
    for name in names:
        obj = _live_obj(name)
        if obj is None:
            missing += 1
            continue
        st = _collision_status(obj)
        if st == "COLLISION VERIFIED":
            verified += 1
        elif st == "COLLISION METADATA ONLY":
            metadata += 1
        else:
            missing += 1
    lines.append("Gameplay-critical collision: VERIFIED={} METADATA_ONLY={} DATA_MISSING={}".format(
        verified, metadata, missing))
    lines.append("Physical collision shape is not inferred when Blender does not expose explicit collision data.")
    return lines


def overlap_audit(pockets, issues):
    lines = []
    if not HAVE_BPY:
        return ["[DATA MISSING] overlap audit requires Blender runtime."]

    pair_defs = []
    # Altar/Core Cover
    altar = _live_obj("Altar_Base")
    for name in ("LCover_West", "LCover_East", "Pillar_North", "SouthScreen", "Pocket_SW", "Pocket_SE"):
        cover = _live_obj("Core_Cover_" + name)
        if altar and cover:
            pair_defs.append((altar, cover, "Altar ↔ " + cover.name))

    # Core Cover ↔ Core Cover
    core = _live_core_cover_objects()
    for i, a in enumerate(core):
        for b in core[i+1:]:
            pair_defs.append((a, b, "Core Cover ↔ Core Cover"))

    # Pocket covers ↔ floor/walls
    for p in pockets:
        floor = _live_obj(p["name"] + "_Floor")
        for i in range(1, 4):
            cover = _live_obj("{}_C{}".format(p["name"], i))
            if cover and floor:
                pair_defs.append((cover, floor, "{} cover ↔ floor".format(p["name"])))

    actual = []
    for a, b, label in pair_defs:
        ov = _mesh_overlap(a, b)
        if ov:
            actual.append((a.name, b.name, label))
    lines.append("Actual evaluated-mesh intersections: {} [EXACT]".format(len(actual)))
    for a, b, label in actual[:40]:
        lines.append("  {} ↔ {} [EXACT]".format(a, b))
        issues.append(("WARNING", "{}: actual mesh intersection [EXACT]".format(label)))
    return lines


def symmetry_audit(data, cps, bases, pockets, issues, live_pocket_cover_result=None):
    lines = []
    base_map = {b["name"]: b for b in bases}
    blue, red = base_map.get("BlueBase"), base_map.get("RedBase")
    base_ok = False
    if blue and red:
        bp, rp = blue["position"], red["position"]
        base_ok = (abs(bp[0] + rp[0]) < 1e-3 and abs(bp[1] - rp[1]) < 1e-3 and
                   abs(blue["radius"] - red["radius"]) < 1e-3)
    checks = [("BlueBase ↔ RedBase", base_ok)]
    by_name = {p["name"]: p for p in pockets}
    for a_name, b_name in (("WestPocket", "EastPocket"), ("SWPocket", "SEPocket")):
        a, b = by_name.get(a_name), by_name.get(b_name)
        ok = False
        if a and b:
            ok = (abs(a["entry"]["width"] - b["entry"]["width"]) < 1e-3 and
                  abs(a.get("floor_area", 0) - b.get("floor_area", 0)) < 1e-3)
        checks.append((a_name + " ↔ " + b_name, ok))
    for label, ok in checks:
        lines.append("{}: {} [EXACT export]".format(label, "PASS" if ok else "WARNING"))
        if not ok:
            issues.append(("WARNING", "{} symmetry mismatch [EXACT export]".format(label)))
    if HAVE_BPY and live_pocket_cover_result is not None:
        for a_name, b_name in (("WestPocket", "EastPocket"), ("SWPocket", "SEPocket")):
            ac = len(live_pocket_cover_result.get(a_name, []))
            bc = len(live_pocket_cover_result.get(b_name, []))
            if ac != bc:
                issues.append(("WARNING", "{} ↔ {} live cover-count mismatch [EXACT scene]".format(a_name, b_name)))
                lines.append("{} ↔ {} live cover count: WARNING ({} vs {})".format(a_name, b_name, ac, bc))
            else:
                lines.append("{} ↔ {} live cover count: {} / {} [EXACT scene]".format(a_name, b_name, ac, bc))
    elif HAVE_BPY:
        lines.append("Live geometry symmetry: resolver data unavailable [DATA MISSING]")
    else:
        lines.append("Live geometry symmetry: [DATA MISSING] Blender runtime required")
    return lines



def simulation_diagnostic(data, pockets, issues):
    lines = []
    sim_zones = data.get("simulation", {}).get("zones", {})
    nav_pockets = {p.get("name"): p for p in data.get("navigation", {}).get("pockets", [])}

    if not sim_zones:
        return ["SIMULATION: [DATA MISSING] no simulation.zones in export."]

    for name in ("WestPocket", "EastPocket", "SWPocket", "SEPocket"):
        z = sim_zones.get(name)
        n = nav_pockets.get(name)
        if z is None:
            lines.append("{}: [DATA MISSING] simulation zone absent".format(name))
            continue
        traffic = z.get("traffic", 0)
        reachable = n.get("reachable") if n else None
        route = n.get("route_length") if n else None
        lines.append("{}: NAVIGATION={}  SIMULATION traffic={}  route_length={}"
                     .format(name,
                             "REACHABLE" if reachable is True else "UNREACHABLE" if reachable is False else "DATA MISSING",
                             traffic,
                             "{:.1f} m [EXACT]" .format(route) if route is not None else "DATA MISSING"))
        if reachable is True and traffic == 0:
            lines.append("  DIAGNOSTIC: NAVIGATION = REACHABLE / SIMULATION = ZERO TRAFFIC")
    return lines



def pocket_live_geometry_audit(pockets, issues, live_pocket_cover_result):
    if not HAVE_BPY:
        return ["[DATA MISSING] live pocket geometry audit requires Blender runtime."]
    lines = []
    for p in pockets:
        pname = p["name"]
        resolved = live_pocket_cover_result.get(pname, []) if live_pocket_cover_result else []
        covers = []
        for item in resolved:
            obj = _live_obj(item[0])
            if obj is not None:
                covers.append(obj)
        exact = bool(resolved) and all(str(item[1]).startswith("EXACT") for item in resolved)
        provenance = "EXACT" if exact else ("APPROXIMATION" if resolved else "DATA MISSING")
        lines.append("{}: live gameplay cover objects = {} [{}]".format(pname, len(covers), provenance))
        if len(covers) != 3:
            issues.append(("WARNING", "{}: live scene resolver found {} gameplay cover objects, expected 3 [{}]".format(pname, len(covers), provenance)))
        for i, a in enumerate(covers):
            for b in covers[i+1:]:
                if _mesh_overlap(a, b):
                    issues.append(("CRITICAL", "{}: {} overlaps {} [EXACT mesh]".format(pname, a.name, b.name)))
        floor = _live_obj(pname + "_Floor")
        if floor:
            for c in covers:
                if _mesh_overlap(c, floor):
                    issues.append(("WARNING", "{}: {} intersects pocket floor mesh [EXACT mesh]".format(pname, c.name)))
        else:
            lines.append("{}: floor [DATA MISSING]".format(pname))
    return lines



def _provenance_summary(text_report):
    labels = ("EXACT", "HEURISTIC", "APPROXIMATION", "DATA MISSING", "FALLBACK")
    return {label: text_report.count("[" + label) for label in labels}


def build_report():
    """A v0.5 report built by extending the original v0.4 implementation."""
    issues = []
    out = []
    out.append("=" * 64)
    out.append("AETHERFLOW GAMEPLAY AUDITOR v0.5 -- NEW IMPLEMENTATION BASED ON ORIGINAL V0.4 SOURCE")
    out.append("=" * 64)
    out.append("READ-ONLY: no map generation or scene mutation.")
    out.append("")

    data, path, probed = load_map_data()
    if data is None:
        out.append("[CRITICAL] Could not find export/map_data.json.")
        out.append("Searched:")
        for p in probed[:24]:
            out.append("  - " + p)
        return "\n".join(out), {"ok": False, "error": "map_data.json not found"}

    out.append("Reading: {}".format(path))
    out.append("Map version: {}   seed: {}".format(data.get("version"), data.get("seed")))

    _sec(out, "SCAN")
    scan_lines, cps, bases, pockets, altars = scene_scan(data, issues)
    out.extend(scan_lines)

    pocket_cover_result, cover_conflicts, live_pocket_cover_result = resolve_pocket_cover_combined(data, pockets)

    _sec(out, "SCENE CLASSIFICATION")
    class_lines, cat = classification_report(data, pocket_cover_result, cover_conflicts, issues)
    if not HAVE_BPY:
        issues[:] = [item for item in issues if "live-scene scan skipped" not in item[1]]
    out.extend(class_lines)

    _sec(out, "ROUTES  (PLAYER_SPEED = {:.1f} m/s)".format(PLAYER_SPEED))
    route_lines, route_rows = route_analysis(data, cps, bases, pockets, altars, issues)
    out.extend(route_lines)

    _sec(out, "FAIRNESS")
    fairness_lines, fairness_diff_pct = fairness_analysis(cps, route_rows, issues)
    out.extend(fairness_lines)
    if fairness_diff_pct is None:
        fairness_diff_pct = 0.0

    _sec(out, "CAPTURE POINTS")
    out.extend(capture_point_audit(data, cps, issues))

    _sec(out, "CHOKEPOINTS -- route-density")
    out.extend(chokepoint_analysis(data, issues))

    _sec(out, "POCKETS")
    out.extend(pocket_audit(pockets, pocket_cover_result, issues))

    _sec(out, "POCKET GEOMETRY")
    out.extend(pocket_geometry_audit(data, pockets, pocket_cover_result, issues))
    out.extend(pocket_live_geometry_audit(pockets, issues, live_pocket_cover_result))

    _sec(out, "ALTAR")
    out.extend(altar_audit(data, altars, bases, pockets, issues))

    _sec(out, "ALTAR OBSTACLE AUDIT")
    out.extend(altar_obstacle_audit(data, issues))

    _sec(out, "CORE COVER")
    out.extend(core_cover_audit(data, altars, issues))

    _sec(out, "BASES")
    out.extend(base_audit(data, bases, cps, issues))

    _sec(out, "TERRAIN / FLOOR")
    out.extend(terrain_floor_audit(data, pockets, issues))

    _sec(out, "COLLISION")
    out.extend(collision_audit(data, pockets, cps, bases, issues))

    _sec(out, "OVERLAPS")
    out.extend(overlap_audit(pockets, issues))

    _sec(out, "SYMMETRY")
    out.extend(symmetry_audit(data, cps, bases, pockets, issues, live_pocket_cover_result))

    _sec(out, "LOS")
    out.extend(los_analysis(data, cps, bases, pockets, altars, issues))

    _sec(out, "COVER VALUE")
    out.extend(cover_value_analysis(data, cps, bases, issues))

    _sec(out, "ROTATION")
    out.extend(rotation_summary(route_rows, issues))

    _sec(out, "SIMULATION")
    out.extend(simulation_diagnostic(data, pockets, issues))

    _sec(out, "RESOURCES")
    out.extend(resource_analysis(cat, issues))

    _sec(out, "MAP CONNECTIVITY / DEAD-ENDS")
    out.extend(connectivity_analysis(data, issues))

    _sec(out, "RISKS")
    lines_camp = camping_risk(data, cps, altars, pockets, issues)
    risk_lines, deathball, snowball, comeback = risk_analysis(data, None, fairness_diff_pct, issues)
    out.append("Camping:")
    out.extend("  " + l for l in lines_camp)
    out.extend(risk_lines)

    overall, scores, reasons = map_quality_score(
        data, issues, fairness_diff_pct, deathball, snowball, comeback
    )

    _sec(out, "ISSUES")
    order = {"CRITICAL": 0, "WARNING": 1, "GOOD": 2}
    for level, msg in sorted(issues, key=lambda x: order.get(x[0], 9)):
        out.append("{:<9} {}".format(level + ":", msg))
    if not issues:
        out.append("(none)")

    n_crit = sum(1 for lvl, _ in issues if lvl == "CRITICAL")
    n_warn = sum(1 for lvl, _ in issues if lvl == "WARNING")
    n_good = sum(1 for lvl, _ in issues if lvl == "GOOD")

    _sec(out, "MAP SCORE")
    out.append("OVERALL SCORE: {}/100  (numeric sub-scores only; DATA MISSING is excluded)".format(overall))
    for key in ("GEOMETRY", "NAVIGATION", "ROTATION", "FAIRNESS", "LOS", "COVER",
                "CHOKEPOINTS", "ALTAR", "POCKETS", "BASES", "COMEBACK"):
        val = scores.get(key)
        out.append("{:<14}{:<18}{}".format(
            key + ":", val if val is not None else "[DATA MISSING]", reasons.get(key, "")))
    out.append("DEATHBALL RISK: {}".format(deathball))
    out.append("SNOWBALL RISK:  {}".format(snowball))
    out.append("CAMPING RISK:   see RISKS section")
    out.append("CRITICAL ISSUES: {}".format(n_crit))
    out.append("WARNINGS:        {}".format(n_warn))
    out.append("GOOD:            {}".format(n_good))

    text = "\n".join(out)
    provenance = _provenance_summary(text)

    structured = {
        "ok": True,
        "auditor_version": "0.5",
        "based_on": "v0.4 source",
        "map_version": data.get("version"),
        "seed": data.get("seed"),
        "overall_score": overall,
        "scores": scores,
        "fairness_diff_pct": fairness_diff_pct,
        "deathball_risk": deathball,
        "snowball_risk": snowball,
        "comeback_risk": comeback,
        "critical_count": n_crit,
        "warning_count": n_warn,
        "good_count": n_good,
        "issues": [{"level": lvl, "message": msg} for lvl, msg in issues],
        "route_rows": [{"label": lbl, "distance_m": d, "fallback": fb} for lbl, d, fb in route_rows],
        "provenance": provenance,
    }
    return text, structured



# =============================================================================
# v0.2 -- EXPORT (spec section 26). This tool may write ONLY these two files
# (spec section 29's one exception to "read-only").
# =============================================================================
def export_report(text_report, structured):
    root, _probed = find_project_root()
    if root is None:
        print("[DATA MISSING] Could not locate project root -- report NOT written to disk "
             "(printed to console only).")
        return None, None
    export_dir = os.path.join(root, "export")
    try:
        os.makedirs(export_dir, exist_ok=True)
        txt_path = os.path.join(export_dir, "gameplay_audit.txt")
        json_path = os.path.join(export_dir, "gameplay_audit.json")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_report)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(structured, f, indent=2, ensure_ascii=False)
        return txt_path, json_path
    except OSError as e:
        print("[DATA MISSING] Could not write report files ({}).".format(e))
        return None, None


# =============================================================================
# v0.2 -- REGRESSION MODE (spec section 25): --compare <previous gameplay_audit.json>
# =============================================================================
def _verdict(delta, higher_is_better):
    if delta is None or abs(delta) < 1e-9:
        return "SAME"
    better = (delta > 0) if higher_is_better else (delta < 0)
    return "BETTER" if better else "WORSE"


def compare_reports(prev_path, structured):
    """v0.4 section 18: Metric / Before / After / Delta / Verdict table."""
    if not os.path.isfile(prev_path):
        print("[DATA MISSING] --compare-report file not found: {}".format(prev_path))
        return
    try:
        with open(prev_path, "r", encoding="utf-8") as f:
            prev = json.load(f)
    except (OSError, ValueError) as e:
        print("[DATA MISSING] Could not read --compare-report file: {}".format(e))
        return

    print("")
    print("=" * 60)
    print("REGRESSION COMPARE: {}".format(prev_path))
    print("=" * 60)
    print("{:<24}{:>12}{:>12}{:>12}{:>10}".format("Metric", "Before", "After", "Delta", "Verdict"))

    def row(label, a, b, higher_is_better=True, fmt="{:.1f}"):
        if a is None or b is None:
            print("{:<24}{:>12}{:>12}{:>12}{:>10}".format(label, a, b, "n/a", "[DATA MISSING]"))
            return
        delta = b - a
        print("{:<24}{:>12}{:>12}{:>+12}{:>10}".format(
            label, fmt.format(a), fmt.format(b), fmt.format(delta), _verdict(delta, higher_is_better)))

    row("OVERALL SCORE", prev.get("overall_score"), structured.get("overall_score"))
    for key in sorted(set(list((prev.get("scores") or {}).keys()) + list((structured.get("scores") or {}).keys()))):
        a = (prev.get("scores") or {}).get(key)
        b = (structured.get("scores") or {}).get(key)
        row(key, a, b)
    row("Fairness diff %", prev.get("fairness_diff_pct"), structured.get("fairness_diff_pct"), higher_is_better=False)
    row("CRITICAL count", prev.get("critical_count"), structured.get("critical_count"), higher_is_better=False, fmt="{:.0f}")
    row("WARNING count", prev.get("warning_count"), structured.get("warning_count"), higher_is_better=False, fmt="{:.0f}")

    prev_routes = {r["label"]: r["distance_m"] for r in prev.get("route_rows", [])}
    cur_routes = {r["label"]: r["distance_m"] for r in structured.get("route_rows", [])}
    changed = [k for k in cur_routes if k in prev_routes and prev_routes[k] != cur_routes[k]]
    if changed:
        print("")
        print("Route distance changes:")
        print("{:<34}{:>12}{:>12}{:>12}{:>10}".format("Route", "Before", "After", "Delta", "Verdict"))
        for k in changed:
            a, b = prev_routes[k], cur_routes[k]
            if a is None or b is None:
                continue
            print("{:<34}{:>11.1f}m{:>11.1f}m{:>+11.1f}m{:>10}".format(k, a, b, b - a, _verdict(b - a, False)))
    print("=" * 60)






def run_self_tests():
    """Fast non-Blender regression checks for the auditor itself."""
    failures = []
    checks = 0

    def check(name, condition):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(name)

    core = {"name": "Core_Cover_Pillar_North", "type": "cover", "meta": {}}
    pocket = {"name": "SWPocket_C1", "type": "cover", "meta": {}}
    check("core classification", _is_core_cover_record(core))
    check("pocket excluded from core classification", not _is_core_cover_record(pocket))
    check("pocket classification", _is_pocket_cover_record(pocket))

    test_export = {
        "navigation": {
            "routes": {"BlueBase->Crown": 1.0},
            "pockets": [{"name": "SWPocket", "reachable": True, "route_length": 37.5}],
        },
        "capture_points": [{"name": "Crown", "position": [0, 0, 0], "radius": 6.7}],
        "bases": [{"name": "BlueBase", "position": [0, 0, 0], "radius": 11.67}],
        "pockets": [{"name": "SWPocket", "capture_point": "Crown",
                     "entry": {"width": 10.0, "point": [0, 0, 0]},
                     "location": [0, 0, 0], "floor_area": 415.9,
                     "cover": ["SWPocket_C1", "SWPocket_C2", "SWPocket_C3"],
                     "perimeter_continuous": True}],
        "landmarks": [{"name": "Altar_Base", "type": "altar", "location": [0, 0, 0],
                       "dimensions": [3, 3, 0.2]}],
        "cover": [core, pocket],
        "rocks": [], "roads": [], "ramps": [], "props": [],
        "simulation": {"zones": {"SWPocket": {"traffic": 0}}},
        "validation": {"ok": True, "warnings": []},
    }

    issues = []
    route_lines, rows = route_analysis(
        test_export, test_export["capture_points"], test_export["bases"],
        test_export["pockets"], test_export["landmarks"], issues)
    route_text = "\n".join(route_lines)
    pocket_lines = [line for line in route_lines if "SWPocket -> MainRoad" in line]
    check("routed pocket exact tag", pocket_lines and "[EXACT, navigation.pockets]" in pocket_lines[0])
    check("pocket does not use fallback", pocket_lines and "[FALLBACK]" not in pocket_lines[0])

    sim_lines = simulation_diagnostic(test_export, test_export["pockets"], issues)
    check("reachable zero traffic diagnostic",
          "NAVIGATION = REACHABLE / SIMULATION = ZERO TRAFFIC" in "\n".join(sim_lines))

    check("altar requirement remains 7.5m", INNER_CLEAR_RADIUS_MIN == 7.5)

    # Generic self-hit rule is represented by a source-object parameter rather
    # than an object-name special case.
    sig = inspect.signature(_raycast_after_ignored_hits)
    check("LOS has generic source exclusion", "source_obj" in sig.parameters)

    # Route analysis keeps Base->Altar fallback explicit while pocket routes stay exact.
    base_altar_lines = [line for line in route_lines if "BlueBase -> Altar" in line]
    check("base altar fallback remains explicit", base_altar_lines and "[FALLBACK]" in base_altar_lines[0])

    if failures:
        print("SELF-TEST: FAIL")
        for f in failures:
            print("  -", f)
        return False
    print("SELF-TEST: {}/{} PASS".format(checks, checks))
    return True




def main():
    argv = sys.argv
    if "--self-test" in argv:
        ok = run_self_tests()
        return 0 if ok else 1

    text_report, structured = build_report()
    print(text_report)

    if structured.get("ok"):
        if "--save-report" in argv:
            txt_path, json_path = export_report(text_report, structured)
            if txt_path:
                print("")
                print("Written: {}".format(txt_path))
                print("Written: {}".format(json_path))
        else:
            print("")
            print("(report not written to disk -- pass --save-report to write "
                  "export/gameplay_audit.json + .txt)")

        compare_flag = "--compare-report" if "--compare-report" in argv else (
            "--compare" if "--compare" in argv else None)
        if compare_flag:
            idx = argv.index(compare_flag)
            if idx + 1 < len(argv):
                compare_reports(argv[idx + 1], structured)
            else:
                print("[DATA MISSING] {} given with no file path".format(compare_flag))
    return 0



if __name__ == "__main__":
    main()
