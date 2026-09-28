#!/usr/bin/env python3
"""The faceplate's placement check: does the faceplate board agree with the panel,
and with the main board it bolts to?

    python3 tools/panelcheck.py --project faceplate            # FAIL on anything wrong
    python3 tools/panelcheck.py --project faceplate --strict   # ...and on anything missing
    python3 tools/panelcheck.py --project faceplate OTHER.kicad_pcb

The main board's equivalent is place.py --check. This one never writes.

Everything it compares against is derived (tools/panelgeo.py): the generator for
the outline, placement-panel-facing.txt for the holes, the MAIN BOARD ITSELF for
the connector -- its J12 footprint and the Edge.Cuts cutout beside it -- and the
two netmaps for the cable. So a change on either board shows up here.

  outline   Edge.Cuts is exactly the generator's panel, at FACE_ORG
  cable     faceplate J1 pin n carries main J12 pin n's net, for every n. The
            ribbon is straight through, so this is the whole interface.
  J1        on the back; pad centroid on the cutout centre; pad 1 in the same
            direction from its centre as J12's; body inside the cutout
  holes     every panel part with a known hole size has a hole of that size,
            centred on its panel coordinate (pots 0.17mm toward the top edge)

A part whose hole is not sized yet, or whose hole is not drawn yet, is a TODO,
not a failure -- the board is in progress. --strict makes TODOs fail; run it
that way before plotting the fab package.

Hole = an NPTH or PTH pad's drill, or a circle on Edge.Cuts. Either is fine.
"""
import json
import os
import subprocess
import sys

import proj
import panelgeo as pg

KPY = ("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework"
       "/Versions/3.9/bin/python3")
STRICT = "--strict" in sys.argv
if proj.KEY != "faceplate":
    sys.exit("panelcheck is the faceplate's check: pass --project faceplate "
             "(the main board's is place.py --check)")
_other = [a for a in sys.argv[1:] if not a.startswith("--")]
PCB = os.path.abspath(_other[0]) if _other else proj.P.pcb
MAIN = proj.PROJECTS["main"]

DUMP = r'''
import json, sys, pcbnew
T = pcbnew.ToMM
def pt(v): return [T(v.x), T(v.y)]
def board(path):
    b = pcbnew.LoadBoard(path)
    edges = []
    for d in b.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        s = d.GetShape()
        if s == pcbnew.SHAPE_T_CIRCLE:
            edges.append({"kind": "circle", "c": pt(d.GetCenter()), "r": T(d.GetRadius())})
        elif s == pcbnew.SHAPE_T_SEGMENT:
            edges.append({"kind": "seg", "pts": [pt(d.GetStart()), pt(d.GetEnd())]})
        elif s == pcbnew.SHAPE_T_ARC:
            edges.append({"kind": "seg", "pts": [pt(d.GetStart()), pt(d.GetEnd())],
                          "arc_c": pt(d.GetCenter()), "arc_r": T(d.GetRadius())})
        elif s == pcbnew.SHAPE_T_RECT:
            a, z = pt(d.GetStart()), pt(d.GetEnd())
            c = [a, [z[0], a[1]], z, [a[0], z[1]]]
            for i in range(4):
                edges.append({"kind": "seg", "pts": [c[i], c[(i + 1) % 4]]})
        else:
            q = d.GetBoundingBox()
            edges.append({"kind": "other", "pts": [[T(q.GetLeft()), T(q.GetTop())],
                                                   [T(q.GetRight()), T(q.GetBottom())]]})
    fps = {}
    for f in b.GetFootprints():
        fab = [d for d in f.GraphicalItems()
               if d.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab)]
        bb = None
        for d in fab:
            q = d.GetBoundingBox()
            box = [T(q.GetLeft()), T(q.GetTop()), T(q.GetRight()), T(q.GetBottom())]
            bb = box if bb is None else [min(bb[0], box[0]), min(bb[1], box[1]),
                                         max(bb[2], box[2]), max(bb[3], box[3])]
        cy = None
        for d in f.GraphicalItems():
            if d.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                q = d.GetBoundingBox()
                box = [T(q.GetLeft()), T(q.GetTop()), T(q.GetRight()), T(q.GetBottom())]
                cy = box if cy is None else [min(cy[0], box[0]), min(cy[1], box[1]),
                                             max(cy[2], box[2]), max(cy[3], box[3])]
        for p in f.Pads():
            q = p.GetBoundingBox()
            box = [T(q.GetLeft()), T(q.GetTop()), T(q.GetRight()), T(q.GetBottom())]
            cy = box if cy is None else [min(cy[0], box[0]), min(cy[1], box[1]),
                                         max(cy[2], box[2]), max(cy[3], box[3])]
        fps[f.GetReference()] = {
            "layer": f.GetLayerName(),
            "fab": bb,
            "extent": cy,
            "pads": [{"n": p.GetNumber(), "xy": pt(p.GetPosition()),
                      "net": p.GetNetname().lstrip("/"),
                      "size": [T(p.GetSize().x), T(p.GetSize().y)],
                      "bbox": [T(p.GetBoundingBox().GetLeft()), T(p.GetBoundingBox().GetTop()),
                               T(p.GetBoundingBox().GetRight()), T(p.GetBoundingBox().GetBottom())],
                      "layer": "F.Cu" if p.IsOnLayer(pcbnew.F_Cu) else "B.Cu",
                      "drill": T(p.GetDrillSize().x) if p.GetDrillSize().x else 0.0}
                     for p in f.Pads()],
        }
    ob = b.GetBoardEdgesBoundingBox()
    vias = [{"xy": pt(t.GetPosition()), "net": t.GetNetname().lstrip("/"),
             "d": T(t.GetWidth()), "drill": T(t.GetDrillValue())}
            for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    tracks = [{"a": pt(t.GetStart()), "b": pt(t.GetEnd()), "net": t.GetNetname().lstrip("/"),
               "layer": b.GetLayerName(t.GetLayer()), "w": T(t.GetWidth())}
              for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    zones = []
    for z in b.Zones():
        q = z.GetBoundingBox()
        zones.append({"net": z.GetNetname().lstrip("/"), "layer": b.GetLayerName(z.GetLayer()),
                      "bbox": [T(q.GetLeft()), T(q.GetTop()), T(q.GetRight()), T(q.GetBottom())]})
    return {"edges": edges, "fps": fps, "vias": vias, "tracks": tracks, "zones": zones,
            "outer": [T(ob.GetLeft()), T(ob.GetTop()), T(ob.GetRight()), T(ob.GetBottom())]}
print(json.dumps({"face": board(sys.argv[1]), "main": board(sys.argv[2])}))
'''


def dump():
    r = subprocess.run([KPY, "-c", DUMP, PCB, MAIN.pcb], capture_output=True, text=True)
    if r.returncode:
        sys.exit((r.stderr or r.stdout).strip() or "pcbnew dump failed")
    return json.loads(r.stdout.strip().splitlines()[-1])


fails, todos, oks = [], [], []


def row(ok, label, val):
    (oks if ok else fails).append(f"{label:40} {val}")


def main():
    d = dump()
    face, mainb = d["face"], d["main"]
    O = pg.FACE_ORG
    to_panel = lambda p: (p[0] - O[0], p[1] - O[1])

    # ---- outline
    _, g = pg.generator()
    W, H = g["PANEL_W"], g["PANEL_H"]
    segs = [p for e in face["edges"] if e["kind"] == "seg" for p in e["pts"]]
    if not segs:
        row(False, "outline", "no Edge.Cuts outline")
    else:
        x0, y0 = min(p[0] for p in segs), min(p[1] for p in segs)
        x1, y1 = max(p[0] for p in segs), max(p[1] for p in segs)
        want = (O[0], O[1], O[0] + W, O[1] + H)
        dev = max(abs(a - b) for a, b in zip((x0, y0, x1, y1), want))
        row(dev < 0.001, "outline is the generator's panel",
            f"{x1 - x0:.3f} x {y1 - y0:.3f} at ({x0:.3f}, {y0:.3f}), off by {dev:.4f}")
        # corners: one arc each, of the generator's radius, centred r in from both edges
        cr = pg.generator()[0].CFG["panel_corner_r_mm"]
        want_c = [(x0 + cr, y0 + cr), (x1 - cr, y0 + cr), (x1 - cr, y1 - cr), (x0 + cr, y1 - cr)]
        arcs = [e for e in face["edges"] if "arc_r" in e]
        hit = [any(abs(e["arc_c"][0] - cx) < 0.005 and abs(e["arc_c"][1] - cy) < 0.005
                   and abs(e["arc_r"] - cr) < 0.005 for e in arcs) for cx, cy in want_c]
        row(all(hit), "outline corners filleted to the generator's radius",
            f"r {cr:g}mm on all four" if all(hit) else f"{sum(hit)} of 4 corners at r {cr:g}mm")

    # ---- cable
    fn = json.load(open(proj.P.netmap)).get("J1", {})
    mn = json.load(open(MAIN.netmap)).get("J12", {})
    bad = [n for n in sorted(set(fn) | set(mn), key=int) if fn.get(n) != mn.get(n)]
    row(not bad and len(mn) == 10, "cable: J1 pin n == main J12 pin n",
        "10/10 pins" if not bad else "differ at pins " + ", ".join(
            f"{n} ({fn.get(n)} vs {mn.get(n)})" for n in bad))

    # ---- J1 over the cutout
    holes_main = pg.cutouts([e["pts"] for e in mainb["edges"] if e["kind"] == "seg"])
    j1, j12 = face["fps"].get("J1"), mainb["fps"].get("J12")
    if len(holes_main) != 1:
        row(False, "main board cutout", f"expected exactly one internal cutout, found {len(holes_main)}")
    elif not j1:
        row(False, "J1", "not on the faceplate board")
    else:
        m2p = pg.main_to_panel()
        k = holes_main[0]
        cut = [m2p(k[:2]), m2p(k[2:])]
        cc = ((cut[0][0] + cut[1][0]) / 2, (cut[0][1] + cut[1][1]) / 2)
        pads = j1["pads"]
        c1 = to_panel((sum(p["xy"][0] for p in pads) / len(pads),
                       sum(p["xy"][1] for p in pads) / len(pads)))
        dev = max(abs(c1[0] - cc[0]), abs(c1[1] - cc[1]))
        row(j1["layer"] == "B.Cu", "J1 on the back", j1["layer"])
        row(dev < 0.01, "J1 centred on the main-board cutout",
            f"pads at panel ({c1[0]:.3f}, {c1[1]:.3f}), cutout ({cc[0]:.3f}, {cc[1]:.3f})")

        def pin1_dir(fp):
            c = (sum(p["xy"][0] for p in fp["pads"]) / len(fp["pads"]),
                 sum(p["xy"][1] for p in fp["pads"]) / len(fp["pads"]))
            q = next(p for p in fp["pads"] if p["n"] == "1")["xy"]
            dx, dy = q[0] - c[0], q[1] - c[1]
            return ("+x" if dx > 0 else "-x") + (" end, " if abs(dx) > abs(dy) else " row, ") + \
                   ("+y" if dy > 0 else "-y") + (" row" if abs(dx) > abs(dy) else " end")
        a, b = pin1_dir(j1), pin1_dir(j12)
        row(a == b, "J1 pad 1 lies the way J12's does", f"J1 {a}; J12 {b}")
        # The key/pin-1 TODO that stood here was closed 2026-09-28 from both
        # manufacturer drawings (README section 5): hanxia and C5665 both put the
        # key on the pin-1 row, so J1 and J12 lying the same way (checked above)
        # means a straight cable, both sockets on one face, maps pin n to pin n.
        if j1["fab"]:
            fb = [to_panel(j1["fab"][:2]), to_panel(j1["fab"][2:])]
            m = min(fb[0][0] - cut[0][0], fb[0][1] - cut[0][1],
                    cut[1][0] - fb[1][0], cut[1][1] - fb[1][1])
            row(m >= 0.5, "J1 body inside the cutout, >= 0.5mm a side",
                f"{fb[1][0] - fb[0][0]:.2f} x {fb[1][1] - fb[0][1]:.2f} in "
                f"{cut[1][0] - cut[0][0]:.2f} x {cut[1][1] - cut[0][1]:.2f}, "
                f"tightest side {m:.2f}mm")
        else:
            row(False, "J1 body inside the cutout", "J1 has no Fab outline to measure")

    # ---- holes
    have = [(to_panel(e["c"]), 2 * e["r"]) for e in face["edges"] if e["kind"] == "circle"]
    have += [(to_panel(p["xy"]), p["drill"]) for f in face["fps"].values()
             for p in f["pads"] if p["drill"] > 1.0]
    n_ok = 0
    for ref, (wx, wy), dia, src in pg.holes():
        near = [(h, dd) for h, dd in have if abs(h[0] - wx) < 1.0 and abs(h[1] - wy) < 1.0]
        if dia is None:
            todos.append(f"{ref:5} hole not sized yet -- {src}"
                         + (" (one is drawn)" if near else ""))
            continue
        if not near:
            todos.append(f"{ref:5} {dia:.2f}mm hole not drawn yet at ({wx:.3f}, {wy:.3f}) -- {src}")
            continue
        (hx, hy), hd = min(near, key=lambda t: (t[0][0] - wx) ** 2 + (t[0][1] - wy) ** 2)
        off = max(abs(hx - wx), abs(hy - wy))
        good = off < 0.01 and abs(hd - dia) < 0.01
        n_ok += good
        if not good:
            row(False, f"{ref} hole", f"{hd:.3f}mm at ({hx:.3f}, {hy:.3f}); want {dia:.3f}mm "
                                      f"at ({wx:.3f}, {wy:.3f}) -- {src}")
    if n_ok:
        row(True, "panel holes on their parts", f"{n_ok} checked")

    # ---- back-side parts clear the enclosure walls. The faceplate rests on the wall tops
    # (generator enclosure_wall_mm all round, panel to the walls' outer faces), so anything
    # on its back must stay inside their inner faces: courtyard and pads, whichever is wider.
    gen_, _ = pg.generator()
    wall = gen_.CFG["enclosure_wall_mm"]
    over = []
    for ref, f in face["fps"].items():
        if f["layer"] != "B.Cu" or not f["extent"]:
            continue
        (x0_, y0_), (x1_, y1_) = to_panel(f["extent"][:2]), to_panel(f["extent"][2:])
        m = min(x0_ - wall, y0_ - wall, W - wall - x1_, H - wall - y1_)
        if m < 0:
            over.append(f"{ref} {-m:.2f}mm")
    row(not over, "back-side parts inside the walls",
        f"{wall:g}mm walls, inner faces x {wall:g}..{W - wall:.2f}" if not over
        else "over the wall top: " + ", ".join(sorted(over)))

    # ---- the routing fences (design/mkroute.py): nothing on F.Cu but the pads, and nothing
    # under a pad but that pad's own nets -- a trace under another pad couples to it and
    # breaks position sensing, and passes DRC. J1's own nets are allowed on B.Cu where its
    # pads reach under the pads' edges.
    nm_ = json.load(open(proj.P.netmap))
    prect = {p: (g["PAD_X0"], g["PAD_TOPS"][p - 1], g["PAD_X1"], g["PAD_TOPS"][p - 1] + g["PW"])
             for p in range(1, 5)}
    own = {p: set(nm_[f"E{p}"].values()) for p in range(1, 5)}
    j1n = set(nm_["J1"].values())
    j1box = None
    if j1:
        xs = [q for pp in j1["pads"] for q in (pp["bbox"][0], pp["bbox"][2])]
        ys = [q for pp in j1["pads"] for q in (pp["bbox"][1], pp["bbox"][3])]
        a0, a1 = to_panel((min(xs), min(ys))), to_panel((max(xs), max(ys)))
        j1box = (a0[0] - 0.5, a0[1] - 0.5, a1[0] + 0.5, a1[1] + 0.5)
    inside = lambda r, x, y: r[0] < x < r[2] and r[1] < y < r[3]

    def under_wrong_pad(pts, net, layer):
        for x, y in pts:
            for p, r in prect.items():
                if inside(r, x, y) and net not in own[p]:
                    if layer == "B.Cu" and net in j1n and j1box and inside(j1box, x, y):
                        continue
                    return p
        return None
    on_top = [t for t in face["tracks"] if t["layer"] == "F.Cu"]
    bad_u = []
    for t in face["tracks"]:
        a_, b_ = to_panel(t["a"]), to_panel(t["b"])
        n_ = max(2, int(max(abs(b_[0] - a_[0]), abs(b_[1] - a_[1])) / 0.5) + 1)
        pts = [(a_[0] + (b_[0] - a_[0]) * k / n_, a_[1] + (b_[1] - a_[1]) * k / n_) for k in range(n_ + 1)]
        p = under_wrong_pad(pts, t["net"], t["layer"])
        if p:
            bad_u.append(f"{t['net']} ({t['layer']}) under pad {p}")
    for v in face["vias"]:
        p = under_wrong_pad([to_panel(v["xy"])], v["net"], "*")
        if p:
            bad_u.append(f"{v['net']} via under pad {p}")
    for z in face["zones"]:
        zb = [*to_panel(z["bbox"][:2]), *to_panel(z["bbox"][2:])]
        for p, r in prect.items():
            if zb[0] < r[2] and zb[2] > r[0] and zb[1] < r[3] and zb[3] > r[1]:
                bad_u.append(f"{z['net']} zone on {z['layer']} under pad {p}")
    row(not on_top, "nothing routed on F.Cu", f"{len(face['tracks'])} tracks, none on the top layer"
        if not on_top else f"{len(on_top)} tracks on F.Cu")
    row(not bad_u, "nothing under a pad but its own nets",
        f"{len(face['tracks'])} tracks, {len(face['vias'])} vias, {len(face['zones'])} zones checked"
        if not bad_u else f"{len(bad_u)}: " + "; ".join(sorted(set(bad_u))[:4]))

    # ---- the panel screws, where the generator puts them
    sc, sd = pg.screws()
    circ = [(to_panel(e["c"]), 2 * e["r"]) for e in face["edges"] if e["kind"] == "circle"]
    miss = [(x, y) for x, y in sc
            if not any(abs(h[0] - x) < 0.005 and abs(h[1] - y) < 0.005 and abs(dd - sd) < 0.005
                       for h, dd in circ)]
    row(not miss, "panel screw holes where the generator puts them",
        f"{len(sc)} x {sd:g}mm" if not miss else f"{len(miss)} missing, first at ({miss[0][0]:.2f}, {miss[0][1]:.2f})")

    # ---- the OLED window: what the generator derives, where the main board has DS1
    wx0, wy0, wx1, wy1, _ = pg.oled_window()
    ox0, oy0, ox1, oy1 = face["outer"]
    inside = [to_panel(p) for e in face["edges"] if e["kind"] == "seg"
              if all(ox0 + 0.5 < q[0] < ox1 - 0.5 and oy0 + 0.5 < q[1] < oy1 - 0.5 for q in e["pts"])
              for p in e["pts"]]
    if not inside:
        todos.append("DS1   OLED window not drawn yet -- design/mkholes.py")
    else:
        bb = (min(p[0] for p in inside), min(p[1] for p in inside),
              max(p[0] for p in inside), max(p[1] for p in inside))
        dev = max(abs(a - b) for a, b in zip(bb, (wx0, wy0, wx1, wy1)))
        row(dev < 0.005, "OLED window == generator oled_window()",
            f"{bb[2] - bb[0]:.2f} x {bb[3] - bb[1]:.2f} at ({bb[0]:.3f}, {bb[1]:.3f}), off by {dev:.4f}")
    ds1 = mainb["fps"].get("DS1")
    holes4 = [p for p in (ds1 or {}).get("pads", []) if abs(p["drill"] - 3.3) < 0.05]
    if len(holes4) != 4:
        row(False, "OLED module where the window assumes", "main board DS1: expected 4 mounting holes")
    else:
        m2p = pg.main_to_panel()
        mc = m2p((sum(p["xy"][0] for p in holes4) / 4, sum(p["xy"][1] for p in holes4) / 4))
        gc = pg.oled_module_centre()
        dev = max(abs(mc[0] - gc[0]), abs(mc[1] - gc[1]))
        row(dev < 0.01, "OLED module where the window assumes",
            f"main-board DS1 holes centred at panel ({mc[0]:.3f}, {mc[1]:.3f}), "
            f"generator ({gc[0]:.3f}, {gc[1]:.3f})")

    # ---- scrub pads: the board's copper IS the generator's copper()
    gen, _ = pg.generator()
    cfg = dict(gen.CFG)
    nm = json.load(open(proj.P.netmap))
    q = lambda v: round(v, 4)
    missing = [f"E{p}" for p in range(1, 5) if f"E{p}" not in face["fps"]]
    if missing:
        row(False, "scrub pads on the board", "missing " + ", ".join(missing))
    else:
        bad_cu, bad_via, n_cu, n_via = [], [], 0, 0
        board_vias = {}
        for v in face["vias"]:
            if v["xy"][0] - O[0] > g["PAD_X1"]:      # the margin's are routing vias
                continue
            board_vias.setdefault(v["net"], set()).add((q(v["xy"][0] - O[0]), q(v["xy"][1] - O[1]),
                                                        q(v["d"]), q(v["drill"])))
        for p in range(1, 5):
            ref, cu = f"E{p}", gen.copper(cfg, g, g["PAD_TOPS"][p - 1])
            fp = face["fps"][ref]
            want = sorted((q(x + w / 2), q(y + h / 2), q(w), q(h), nm[ref]["1" if n == 0 else str(n + 1)])
                          for n, x, y, w, h in cu["bars"] + cu["bridges"])
            have = sorted((q(pp["xy"][0] - O[0]), q(pp["xy"][1] - O[1]), q(pp["size"][0]),
                           q(pp["size"][1]), pp["net"]) for pp in fp["pads"])
            # footprint coordinates are written to 0.1um, so compare within 1um
            close = lambda u, v: u[4] == v[4] and all(abs(i - j) <= 0.001 for i, j in zip(u[:4], v[:4]))
            if fp["layer"] != "F.Cu" or len(want) != len(have) or \
                    not all(close(u, v) for u, v in zip(want, have)):
                diff = [(u, v) for u, v in zip(want, have) if not close(u, v)]
                bad_cu.append(f"{ref}: {fp['layer']}, {len(have)} pads vs {len(want)}"
                              + (f", first difference {diff[0]}" if diff else ""))
            n_cu += len(want)
            for n, x, y in cu["vias"]:
                net = nm[ref]["1" if n == 0 else str(n + 1)]
                key = (q(x), q(y), q(cfg["via_dia_mm"]), q(cfg["via_drill_mm"]))
                if key not in board_vias.get(net, ()):
                    bad_via.append(f"{net} via at ({x:.3f}, {y:.3f})")
                else:
                    board_vias[net].discard(key)
                n_via += 1
        stray = [f"{n} ({len(s)})" for n, s in board_vias.items()
                 if n.startswith("PAD") and s]
        row(not bad_cu, "scrub pad copper == generator copper()",
            f"{n_cu} bars + bridges on E1-E4, F.Cu" if not bad_cu else bad_cu[0])
        row(not bad_via and not stray, "one via per bar, where the generator puts it",
            f"{n_via} vias on their bar's net" if not (bad_via or stray)
            else (bad_via[:1] + [f"extra vias on {', '.join(stray)}"])[0])
    # The generator's via keepouts must be exactly J1's pads, read off the board.
    if j1:
        rows_ = {}
        for pp in j1["pads"]:
            (x0_, y0_), (x1_, y1_) = to_panel(pp["bbox"][:2]), to_panel(pp["bbox"][2:])
            rows_.setdefault(round(to_panel(pp["xy"])[1], 2), []).append((x0_, y0_, x1_, y1_))
        derived = sorted(tuple(round(v, 3) for v in (min(r[0] for r in rs), min(r[1] for r in rs),
                                                     max(r[2] for r in rs), max(r[3] for r in rs)))
                         for rs in rows_.values())
        typed = sorted(tuple(round(v, 3) for v in k) for k in cfg["via_keepouts_mm"])
        row(derived == typed, "generator via keepouts == J1's pad rows",
            f"{len(typed)} rows" if derived == typed else f"J1 {derived} vs generator {typed}")

    for s in oks:
        print(f"  OK    {s}")
    for s in fails:
        print(f"  FAIL  {s}")
    if todos:
        print(f"\n  TODO ({len(todos)}):")
        for s in todos:
            print(f"    {s}")
    print()
    if fails or (STRICT and todos):
        print(f"  *** {len(fails)} FAIL" + (f", {len(todos)} TODO under --strict" if STRICT else "") + " ***")
        return 1
    print(f"  {len(oks)} OK, {len(todos)} TODO" + ("" if not todos else " -- not ready to fab (--strict)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
