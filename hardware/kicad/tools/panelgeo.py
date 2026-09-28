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
            out.append((ref, (x, y), 2 * cfg["mx_hole_r_mm"], "generator mx_hole_r_mm (6.2mm plunger)"))
        elif re.fullmatch(r"SW[12]", ref):
            out.append((ref, (x, y), cfg["switch_hole_d_mm"], "generator switch_hole_d_mm (Dailywell DW3)"))
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
            out.append((ref, (x, y), None, "OLED window: size to the active area at the final height"))
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
