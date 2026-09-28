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
        elif s in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_ARC):
            edges.append({"kind": "seg", "pts": [pt(d.GetStart()), pt(d.GetEnd())]})
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
        fps[f.GetReference()] = {
            "layer": f.GetLayerName(),
            "fab": bb,
            "pads": [{"n": p.GetNumber(), "xy": pt(p.GetPosition()),
                      "net": p.GetNetname().lstrip("/"),
                      "drill": T(p.GetDrillSize().x) if p.GetDrillSize().x else 0.0}
                     for p in f.Pads()],
        }
    ob = b.GetBoardEdgesBoundingBox()
    return {"edges": edges, "fps": fps,
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

    todos.append("scrub pad copper: not on the board yet (generator PAD_TOPS / PAD_X0..X1)")

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
