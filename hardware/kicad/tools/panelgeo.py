"""Faceplate geometry that the two boards have to agree on, read from its sources.

Nothing here is a number typed from a doc when a file can supply it:

    panel size, pad copper     mockups/generate-faceplate.py (imported, derive())
    panel-part centres         hardware/placement-panel-facing.txt (generated)
    main board <-> panel       that file's footer line, "PCB ORG (sheet X, Y) sits
                               at panel (OX, OY)" -- the same pair as place.py's
                               ORG and (OX, OY), printed by the generator
    faceplate board <-> panel  FACE_ORG below: faceplate sheet = FACE_ORG + panel

The exceptions are the hole sizes in HOLES, which come from manufacturer
drawings; each row says which.

Pure Python, no pcbnew, so it imports under both the system interpreter and
KiCad's (design/mkboard.py runs under the latter).
"""
import importlib.util
import os
import re

import proj

REPO = os.path.dirname(proj.HW)
GENERATOR = os.path.join(REPO, "mockups", "generate-faceplate.py")
PANEL_FILE = os.path.join(proj.HW, "placement-panel-facing.txt")

# The faceplate board is drawn in panel coordinates, shifted onto the sheet.
FACE_ORG = (100.0, 50.0)


def face_sheet(p):
    """panel (x, y) -> faceplate board sheet (x, y)"""
    return (FACE_ORG[0] + p[0], FACE_ORG[1] + p[1])


def generator():
    """-> (module, derived geometry) for the CURRENT generator config."""
    spec = importlib.util.spec_from_file_location("generate_faceplate", GENERATOR)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, m.derive(dict(m.CFG))


def panel_rows():
    """-> {ref: (x, y)} from the placement file, panel coordinates."""
    out = {}
    for line in open(PANEL_FILE):
        if line.startswith("#") or not line.strip():
            continue
        # Same pattern as place.py: X and Y must be decimals, or a description
        # ending in a digit ("UI button 1") parses as a coordinate.
        m = re.match(r'(\w+)\s+.*?(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*(?:#|\S.*)?$', line.rstrip())
        if m and m.group(1) != "REF":
            out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out


def main_to_panel():
    """-> function mapping a MAIN board sheet (x, y) to panel (x, y)."""
    txt = open(PANEL_FILE).read()
    m = re.search(r'PCB ORG \(sheet ([\d.]+), ([\d.]+)\) sits at panel \(([\d.]+), ([\d.]+)\)', txt)
    if not m:
        raise SystemExit(f"{PANEL_FILE}: no 'PCB ORG ... sits at panel' footer -- regenerate it")
    sx, sy, ox, oy = map(float, m.groups())
    return lambda p: (p[0] - sx + ox, p[1] - sy + oy)


def holes():
    """-> [(ref, want_centre_panel, diameter_or_None, source)] for every panel
    part in the placement file. diameter None = not sized yet."""
    cfg = generator()[0].CFG
    out = []
    for ref, (x, y) in sorted(panel_rows().items()):
        if re.fullmatch(r"RV[1-6]", ref):
            # Alpha RD902F: M7 x 0.75 bushing, washer ID 7.2. The shafts sit
            # 0.17mm toward the top edge of their panel coordinate (place.py
            # ORIGIN_OFFSET: placed at -4.83, true shaft at -5.00).
            out.append((ref, (x, y - 0.17), 7.5, "Alpha RD902F drawing; place.py shaft offset"))
        elif re.fullmatch(r"SW[4-9]", ref):
            out.append((ref, (x, y), cfg["mx_cut_d_mm"], "generator mx_cut_d_mm (6.2 +-0.2 plunger, TS1103S)"))
        elif re.fullmatch(r"SW[12]", ref):
            out.append((ref, (x, y), cfg["switch_hole_d_mm"], "generator switch_hole_d_mm (10-48 bushing, Dailywell)"))
        elif ref == "ENC0":
            # ALPS EC11L1525G01 drawing (LE2115L02G): no thread. A 7mm bushing ends
            # 9.5mm above the board, then a KNURLED 9.03mm shaft from 10 to 18mm --
            # so what passes the faceplate (10-11.6mm) turns, and pushes 1.5mm.
            # Running clearance, not a bushing fit: 10.0mm.
            out.append((ref, (x, y), 10.0, "ALPS EC11L drawing: knurled 9.03mm shaft turns in it"))
        elif re.fullmatch(r"ENC[1-8]", ref):
            # ALPS EC12E2430803 (bushing type): body 5.5mm, then 7mm of M9 x 0.75,
            # ending 0.9mm above the outer face. The static thread passes the
            # faceplate: M9 + 0.5, the pots' margin (M7 -> 7.5).
            out.append((ref, (x, y), 9.5, "ALPS EC12E drawing: M9 x 0.75 bushing"))
        elif ref == "DS1":
            continue            # a rectangle, not a hole: oled_window() below
        else:
            out.append((ref, (x, y), None, "no rule for this ref"))
    return out


def cutouts(shapes):
    """Internal cutouts of a board outline, as [(x0, y0, x1, y1)] bounding boxes.

    shapes: the endpoints of every Edge.Cuts segment and arc, [((x0, y0), (x1, y1))].
    Endpoints that coincide join shapes into loops; the loop with the largest
    extent is the board's outer edge and every other loop is a cutout.

    This replaced an "inside the outer bounding box" filter, which the main
    board's USB tab defeats: the outline is not a rectangle, so pieces of the
    OUTER edge sit well inside its bounding box and were read as cutout.
    """
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in shapes:
        ra, rb = find(key(a)), find(key(b))
        parent[ra] = rb
    groups = {}
    for p in list(parent):
        groups.setdefault(find(p), []).append(p)
    boxes = [(min(x for x, _ in g), min(y for _, y in g), max(x for x, _ in g), max(y for _, y in g))
             for g in groups.values()]
    boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    return boxes[1:]


def oled_window():
    """-> (x0, y0, x1, y1, corner_r) of the OLED window, panel mm, from the
    generator's oled_window() (HS242L01 drawing + stack-up; see its CFG)."""
    m, g = generator()
    return tuple(g["OLED_WIN"]) + (m.CFG["oled_window_r_mm"],)


def oled_module_centre():
    """-> the module's centre, panel mm, as the generator places it: the four
    mounting holes are centred on it (drawing: 68 x 39 on a 72 x 43 board)."""
    m, g = generator()
    c = m.CFG
    return (g["oled_x0"] - c["oled_hdr_to_edge_mm"] + 36.0, g["OLED_Y"] + 21.5)


def screws():
    """-> ([(x, y)], diameter): the panel screw holes, panel mm, from the generator."""
    m, g = generator()
    return list(g["SCREWS"]), m.CFG["panel_screw_d_mm"]


# ---- the silkscreen -----------------------------------------------------------------------
PAD_MASK_MARGIN = 0.25  # each pad's one F.Mask opening, beyond its copper (design/mkpads.py)
SILK_TO_CUT = 0.3       # silk to the board edge or any hole: the fab trims it anyway
SILK_TO_MASK = 0.2      # silk to a mask opening: none is printed on bare copper


def panel_silk():
    """-> (strokes, clipped): the generator's panel_art() as the fab can print it, panel mm.

    strokes: [{"id", "w", and "seg": (x1, y1, x2, y2) or "arc": (cx, cy, r, a0, a1)}], arc
    angles in degrees, y down, swept a0 -> a1 increasing (the generator's convention).
    Each art stroke loses whatever lies within SILK_TO_CUT (plus its half-width) of the board
    edge or a hole -- panel holes, screws, the OLED window -- or within SILK_TO_MASK of a
    pad's mask opening. The rules lose the pots' holes; the pad divider breaks at each pad.
    The art's own free ends are drawn half a width short, so KiCad's round caps end where the
    SVG's butt ends do; a clipped end keeps its clearance to the cap's edge.
    clipped: {art id: mm of centreline removed}."""
    import math
    m, g = generator()
    c = dict(m.CFG)
    W, H, R = g["PANEL_W"], g["PANEL_H"], c["panel_corner_r_mm"]
    sc, sd = screws()
    circles = [(x, y, d / 2) for _, (x, y), d, _ in holes() if d] + [(x, y, sd / 2) for x, y in sc]
    cuts = [oled_window()[:4]]
    masks = []
    for yt in g["PAD_TOPS"]:
        cu = m.copper(c, g, yt)
        r = cu["bars"] + cu["bridges"]
        pm = PAD_MASK_MARGIN
        masks.append((min(x for _, x, _, _, _ in r) - pm, min(y for _, _, y, _, _ in r) - pm,
                      max(x + w for _, x, _, w, _ in r) + pm, max(y + h for _, _, y, _, h in r) + pm))

    def blocked(x, y, w):
        d = SILK_TO_CUT + w / 2
        cx, cy = min(max(x, R), W - R), min(max(y, R), H - R)      # the outline, corners too
        if not (d <= x <= W - d and d <= y <= H - d) or math.hypot(x - cx, y - cy) > R - d:
            return True
        if any(math.hypot(x - hx, y - hy) < hr + d for hx, hy, hr in circles):
            return True
        if any(r[0] - d < x < r[2] + d and r[1] - d < y < r[3] + d for r in cuts):
            return True
        dm = SILK_TO_MASK + w / 2
        return any(r[0] - dm < x < r[2] + dm and r[1] - dm < y < r[3] + dm for r in masks)

    def kept(P, L, w):
        """[(t0, t1)] of t in [0, 1] where P(t) is printable, boundaries to 1e-9"""
        n = max(2, int(math.ceil(L / 0.02)))
        ok = [not blocked(*P(i / n), w) for i in range(n + 1)]

        def edge(ta, tb):             # ok(ta) != ok(tb): bisect to the boundary
            oa = not blocked(*P(ta), w)
            for _ in range(40):
                tm = (ta + tb) / 2
                if (not blocked(*P(tm), w)) == oa:
                    ta = tm
                else:
                    tb = tm
            return (ta + tb) / 2
        out, t0 = [], 0.0 if ok[0] else None
        for i in range(n):
            if ok[i] != ok[i + 1]:
                t = edge(i / n, (i + 1) / n)
                if ok[i]:
                    out.append((t0, t))
                else:
                    t0 = t
        if ok[n]:
            out.append((t0, 1.0))
        return out

    strokes, clipped = [], {}
    for a in m.panel_art(c, g):
        w, gid = a["w"], a["id"]
        if "arc" in a:
            cx, cy, r, a0, a1 = a["arc"]
            P = lambda t: (cx + r * math.cos(math.radians(a0 + t * (a1 - a0))),
                           cy + r * math.sin(math.radians(a0 + t * (a1 - a0))))
            parts = [(P, r * math.radians(a1 - a0), True, True,
                      lambda t0, t1: {"arc": (cx, cy, r, a0 + t0 * (a1 - a0), a0 + t1 * (a1 - a0))})]
        else:
            pts = a["pts"]
            closed = len(pts) > 2 and pts[0] == pts[-1]
            parts = []
            for i, ((x1, y1), (x2, y2)) in enumerate(zip(pts, pts[1:])):
                P = (lambda x1, y1, x2, y2: lambda t: (x1 + t * (x2 - x1), y1 + t * (y2 - y1)))(x1, y1, x2, y2)
                mk = (lambda P: lambda t0, t1: {"seg": (*P(t0), *P(t1))})(P)
                parts.append((P, math.hypot(x2 - x1, y2 - y1),
                              i == 0 and not closed, i == len(pts) - 2 and not closed, mk))
        for P, L, free0, free1, mk in parts:
            ks = kept(P, L, w)
            got = 0.0
            for t0, t1 in ks:
                if free0 and t0 == 0.0:
                    t0 = (w / 2) / L
                if free1 and t1 == 1.0:
                    t1 = 1.0 - (w / 2) / L
                if (t1 - t0) * L < 0.1:          # a sliver is not art
                    continue
                strokes.append({"id": gid, "w": w, **mk(t0, t1)})
                got += (t1 - t0) * L
            lost = L - got - (w / 2 if free0 else 0) - (w / 2 if free1 else 0)
            if lost > 1e-6:
                clipped[gid] = clipped.get(gid, 0.0) + lost
    return strokes, clipped
