"""
AetherFlow :: tools/aetherflow_gameplay_auditor.py  (v0.1)

READ-ONLY diagnostic tool. It answers: "how well does the current AetherFlow
map serve Dominion-style gameplay?" — SCAN -> ANALYZE -> REPORT.

GUARANTEE: this script never creates, deletes, or moves an object, never
touches materials/terrain/navigation/simulation/export, and never runs the
generation pipeline (main.py / core.pipeline are not imported or invoked).
It only READS the live Blender scene (bpy.data) and the last-exported
export/map_data.json next to the project.

HOW TO RUN
    Blender Text Editor -> Open... this file from disk (a pasted Text Block
    has no filepath and cannot locate the project) -> Run Script.
    Or headless: blender --background <file>.blend --python
    tools/aetherflow_gameplay_auditor.py

REQUIRES export/map_data.json to already exist (produced by a previous
main.py run). This tool does not generate it.

v0.1 SCOPE (spec "AETHERFLOW GAMEPLAY AUDITOR v0.1", section 16 -- first
minimal version only):
    1. scene scan             5. altar audit
    2. route distances + time 6. fairness
    3. chokepoints             7. report
    4. pocket audit
Deferred to a later version (NOT implemented here -- see spec sections in
parentheses): capture-point approach counting (5), BVH line-of-sight
analysis (8), per-object cover value scoring (9), Dominion rotation quality
(11), the 0-100 weighted map score (12).

NAVIGATION DATA POLICY (spec section 15): real route/chokepoint data already
computed by core.navigation and stored in map_data.json is used wherever it
exists. Where it does NOT exist (e.g. Base -> Altar, Pocket -> MainRoad --
the exported "navigation.routes" table only covers Base -> CapturePoint), a
straight-line estimate is computed instead and every such case is printed
with an explicit "NAVIGATION FALLBACK USED" tag -- it is never silently
presented as a real routed distance.
"""
import os
import sys
import json
import math

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
    lines = []
    routes = data.get("navigation", {}).get("routes", {})
    fallback_used = False

    rows = []   # (label, distance_or_None, is_fallback)

    for b in bases:
        for cp in cps:
            key = "{}->{}".format(b["name"], cp["name"])
            d = routes.get(key)
            rows.append(("{} -> {}".format(b["name"], cp["name"]), d, False))
            if d is None:
                issues.append(("WARNING", "No nav route for {}".format(key)))

    # Base -> Altar: NOT in navigation.routes (only Base->CapturePoint is
    # precomputed) -> explicit straight-line fallback.
    altar_pos = altars[0]["location"][:2] if altars else None
    for b in bases:
        if altar_pos is not None:
            d = dist2(b["position"][:2], altar_pos)
            rows.append(("{} -> Altar".format(b["name"]), d, True))
            fallback_used = True

    # Pocket routes are present in the current navigation export.  Consume
    # the routed CapturePoint -> PocketEntry length instead of replacing it
    # with a straight-line proxy.
    nav_pockets = {p["name"]: p for p in data.get("navigation", {}).get("pockets", [])}
    for p in pockets:
        nav_p = nav_pockets.get(p["name"])
        if nav_p is not None and nav_p.get("route_length") is not None:
            rows.append(("{} -> PocketEntry (via {})".format(
                p["name"], p.get("capture_point")), nav_p["route_length"], False))
            continue

        cp = cp_by_name.get(p.get("capture_point"))
        if cp is None:
            issues.append(("WARNING", "{}: capture_point '{}' not found for pocket fallback"
                           .format(p["name"], p.get("capture_point"))))
            continue
        d = dist2(p["entry"]["point"][:2], cp["position"][:2])
        rows.append(("{} -> PocketEntry (via {})".format(p["name"], cp["name"]), d, True))
        fallback_used = True

    lines.append("{:<32}{:>10}{:>10}".format("Route", "Distance", "Time"))
    for label, d, is_fb in rows:
        dtxt, ttxt = fmt_dt(d)
        tag = "  [FALLBACK]" if is_fb else ""
        lines.append("{:<32}{}{}{}".format(label, dtxt, ttxt, tag))

    if fallback_used:
        lines.append("")
        lines.append("NAVIGATION FALLBACK USED for routes marked [FALLBACK] above "
                     "(straight-line estimate -- no routed nav data exists for "
                     "Base->Altar or Pocket->MainRoad in the current export).")

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
        return lines

    blue_avg_d = sum(blue) / len(blue)
    red_avg_d = sum(red) / len(red)
    blue_avg_t = blue_avg_d / PLAYER_SPEED
    red_avg_t = red_avg_d / PLAYER_SPEED
    diff_pct = abs(blue_avg_t - red_avg_t) / max(blue_avg_t, red_avg_t) * 100.0 if max(blue_avg_t, red_avg_t) else 0.0

    lines.append("BLUE average: {:.1f} m / {:.1f} s ({} routes)".format(blue_avg_d, blue_avg_t, len(blue)))
    lines.append("RED  average: {:.1f} m / {:.1f} s ({} routes)".format(red_avg_d, red_avg_t, len(red)))
    lines.append("DIFFERENCE:   {:.1f} %".format(diff_pct))

    if diff_pct > 10.0:
        issues.append(("WARNING", "Blue/Red average route time differs by {:.1f}% (>10%)".format(diff_pct)))
    else:
        issues.append(("GOOD", "Blue/Red average route time within {:.1f}% -- gameplay-equivalent".format(diff_pct)))

    return lines


# =============================================================================
# 4) POCKET AUDIT
# =============================================================================
def pocket_audit(pockets, issues):
    lines = []
    lines.append("{:<12}{:>9}{:>7}{:>11}{:>12}".format("Pocket", "Entry", "Cover", "MinPass", "Continuous"))

    by_name = {p["name"]: p for p in pockets}
    for p in pockets:
        entry_w = p.get("entry", {}).get("width")
        cover_n = len(p.get("cover", []))
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
        if min_pass is not None and _width_band(min_pass) == "CRITICAL":
            issues.append(("CRITICAL", "{}: internal min passage {:.1f} m is CRITICAL (<3 m)"
                           .format(p["name"], min_pass)))
        if cover_n < 2:
            issues.append(("WARNING", "{}: only {} interior cover object(s) (expected 2-3)"
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
        cov_p = len(p.get("cover", []))
        cov_q = len(q.get("cover", []))
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
def altar_audit(data, altars, bases, pockets, issues):
    lines = []
    if not altars:
        issues.append(("CRITICAL", "Altar audit skipped -- no altar landmark in map_data.json"))
        return ["No altar landmark found -- CRITICAL (see CRITICAL ISSUES)."]

    altar_pos = altars[0]["location"][:2]
    zones = data.get("simulation", {}).get("zones", {})
    core = zones.get("AetherCore")

    if core is None:
        issues.append(("WARNING", "No 'AetherCore' zone in simulation data -- altar metrics limited"))
        lines.append("Position: ({:.1f}, {:.1f})".format(*altar_pos))
        lines.append("No simulation zone data available for the altar area.")
    else:
        obstacles = core.get("cover_objects_in_zone", 0)
        traffic = core.get("traffic", 0)
        exposure = core.get("exposure")
        covered_fraction = core.get("covered_fraction")
        lines.append("Position: ({:.1f}, {:.1f})".format(*altar_pos))
        lines.append("Cover anchors in analysis zone: {}".format(obstacles))
        lines.append("LOS exposure: {}   LOS covered fraction: {}".format(
            exposure, covered_fraction))
        lines.append("Traffic (sim): {}".format(traffic))
        lines.append("Reachable (traffic > 0): {}".format("YES" if traffic > 0 else "NO"))
        if traffic <= 0:
            issues.append(("CRITICAL", "AetherCore/Altar zone shows zero simulated traffic -- unreachable?"))

    # chokepoints near the altar (reuses real navigation.chokepoints, filtered
    # by distance -- no fabricated width, see CHOKEPOINT ANALYSIS note)
    chokes = data.get("navigation", {}).get("chokepoints", [])
    near = [c for c in chokes if dist2((c["x"], c["y"]), altar_pos) <= 20.0]
    lines.append("Chokepoints within 20 m: {}".format(len(near)))
    for c in near:
        lines.append("  ({:.1f}, {:.1f})  routes_through={}  cells={}"
                     .format(c["x"], c["y"], c["routes_through"], c["cells"]))

    # Base/Pocket -> Altar: no routed nav data for this -> fallback, disclosed.
    lines.append("")
    lines.append("Approach distances (straight-line -- NAVIGATION FALLBACK USED, "
                 "no routed nav data to the altar in the current export):")
    for b in bases:
        d = dist2(b["position"][:2], altar_pos)
        dtxt, ttxt = fmt_dt(d)
        lines.append("  {:<12} -> Altar   {}{}".format(b["name"], dtxt, ttxt))
    for pname in ("WestPocket", "EastPocket"):
        p = next((p for p in pockets if p["name"] == pname), None)
        if p is None:
            continue
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
# REPORT ASSEMBLY
# =============================================================================
def build_report():
    issues = []   # list of (level, message), level in CRITICAL/WARNING/GOOD

    out = []
    out.append("=" * 60)
    out.append("AETHERFLOW GAMEPLAY AUDITOR v0.1")
    out.append("=" * 60)

    data, path, probed = load_map_data()
    if data is None:
        out.append("")
        out.append("[CRITICAL] Could not find export/map_data.json.")
        out.append("This tool only reads an existing export -- run main.py once first.")
        out.append("Searched (each entry and all of its parents):")
        for p in probed[:24]:
            out.append("  - " + p)
        return "\n".join(out)

    out.append("")
    out.append("Reading: {}".format(path))
    out.append("Map version: {}   seed: {}".format(data.get("version"), data.get("seed")))
    out.append("")

    out.append("-" * 60)
    out.append("SCAN")
    out.append("-" * 60)
    scan_lines, cps, bases, pockets, altars = scene_scan(data, issues)
    out.extend(scan_lines)

    out.append("")
    out.append("-" * 60)
    out.append("ROUTES  (PLAYER_SPEED = {:.1f} m/s)".format(PLAYER_SPEED))
    out.append("-" * 60)
    route_lines, route_rows = route_analysis(data, cps, bases, pockets, altars, issues)
    out.extend(route_lines)

    out.append("")
    out.append("-" * 60)
    out.append("FAIRNESS")
    out.append("-" * 60)
    out.extend(fairness_analysis(cps, route_rows, issues))

    out.append("")
    out.append("-" * 60)
    out.append("CHOKEPOINTS")
    out.append("-" * 60)
    out.extend(chokepoint_analysis(data, issues))

    out.append("")
    out.append("-" * 60)
    out.append("POCKETS")
    out.append("-" * 60)
    out.extend(pocket_audit(pockets, issues))

    out.append("")
    out.append("-" * 60)
    out.append("ALTAR")
    out.append("-" * 60)
    out.extend(altar_audit(data, altars, bases, pockets, issues))

    out.append("")
    out.append("-" * 60)
    out.append("ISSUES")
    out.append("-" * 60)
    order = {"CRITICAL": 0, "WARNING": 1, "GOOD": 2}
    for level, msg in sorted(issues, key=lambda x: order.get(x[0], 9)):
        out.append("{:<9} {}".format(level + ":", msg))
    if not issues:
        out.append("(none)")

    out.append("")
    out.append("-" * 60)
    out.append("v0.1 SCOPE")
    out.append("-" * 60)
    out.append("Implemented: scene scan, route distances + time, chokepoints,")
    out.append("             pocket audit, altar audit, fairness, this report.")
    out.append("Deferred (planned v0.2): capture-point approach counting, BVH")
    out.append("             line-of-sight analysis, per-object cover value scoring,")
    out.append("             Dominion rotation quality, 0-100 weighted map score.")
    out.append("=" * 60)

    return "\n".join(out)


def main():
    report = build_report()
    print(report)
    return report


if __name__ == "__main__":
    main()
