"""The electrode fan-in on L2: every bus exit to its cell's via. Re-runnable. Deterministic.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkfanin.py

Run after mkbuses.py and mkcells.py (which places each cell's via at the height given by
VIA_LEVEL here), before mkroute.py. Left to Freerouting, a third of these lines never
connected and the rest meandered; they are the sensor lines, so they are drawn exactly.

The problem it solves: each pad's lines leave its bus in the order RX0, RX2, RX1, RX3 (top
to bottom, set by the bus geometry), while the grid's columns run RX0, RX1, RX2, RX3 (set
by U1's pin order, which keeps the B.Cu fan-out crossing-free). Crossing-free anyway:

  * every cell's via sits at its own height inside the cell band (VIA_LEVEL, 0.5 apart),
    in the SAME order as the lines arrive, so each line runs horizontally at its own
    height to its own column and passes the other columns' vias at >= 0.5 -- never another
    line;
  * pads 1-3 come in from the left strip (between the pad copper's end and column 0):
    pad 1 turns down onto row 1, pads 2 and 3 turn up; the vertical runs take x slots
    ordered so no vertical crosses another line's horizontal, and pad 3's sit right of
    pad 2's (column 0's via steps 0.4 right in mkcells.py to make room for the fourth);
  * pad 4's lines would jam that strip, so they run right under the corner group, up a
    strip beside the right edge, and in from the right -- its via order reversed to match.

All 0.15mm (CapTIvate), all In1.Cu, nothing under a pad. Idempotent: removes, first, every
In1.Cu track on a PADp_RXn net that lies wholly in the margin (x > the pad copper's end).

After this writes the board, File -> Revert in Pcbnew before touching it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FACE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(FACE), "kicad", "tools"))
sys.argv[1:1] = ["--project", "faceplate"]
import proj            # noqa: E402
import panelgeo as pg  # noqa: E402
import pcbnew          # noqa: E402
import mkbuses as bus  # noqa: E402
from mkcells import COL_X, ROW_Y, VIA_X, VIA_LEVEL  # noqa: E402

mm = pcbnew.FromMM
W = 0.15
G = bus.G
X_M = G["PAD_X1"]
# vertical slots: left strip (x rising away from the pad copper) and right strip
LEFT = (278.0, 278.3, 278.6, 278.9, 279.2, 279.5, 279.8, 280.1)
RIGHT = (291.6, 291.9, 292.2, 292.5)
# Pad 4's RX0 runs this low, jogged 45 degrees off its bus exit (Dylan's reroute of the
# corridor's end, 2026-09-29, mkescape.py TAIL)
PAD4_RX0_Y = 117.15


def exits(p):
    """{rx: exit y} of pad p's bus, in panel mm (mkbuses.py)"""
    yt = G["PAD_TOPS"][p - 1]
    yb = yt + G["PW"]
    return {0: yt + bus.TOP_IN, 2: yt + bus.DEEP_TOP, 1: yb - bus.DEEP_BOT, 3: yb - bus.BOT_IN}


def target(p, rx):
    return VIA_X[rx], ROW_Y[p] + VIA_LEVEL[p][rx]


def paths():
    """{(p, rx): [points]} from the bus exit to the cell via"""
    out = {}
    order = lambda p: sorted(exits(p), key=lambda rx: exits(p)[rx])        # top to bottom
    # pad 1: down onto row 1 -- a lower exit turns down further LEFT
    for k, rx in enumerate(order(1)):
        x = LEFT[3 - k]
        (tx, ty), ey = target(1, rx), exits(1)[rx]
        out[(1, rx)] = [(bus.EXIT, ey), (x, ey), (x, ty), (tx, ty)]
    # pads 2 and 3: up onto their rows -- a lower exit turns up further RIGHT; pad 3 right of 2
    for p, slots in ((2, LEFT[0:4]), (3, LEFT[4:8])):
        for k, rx in enumerate(order(p)):
            x = slots[k]
            (tx, ty), ey = target(p, rx), exits(p)[rx]
            out[(p, rx)] = [(bus.EXIT, ey), (x, ey), (x, ty), (tx, ty)]
    # pad 4: right under the corner group, up the right strip, in from the right -- the
    # top exit turns up innermost
    for k, rx in enumerate(order(4)):
        x = RIGHT[k]
        (tx, ty), ey = target(4, rx), exits(4)[rx]
        if rx == 0:
            y = PAD4_RX0_Y
            out[(4, rx)] = [(bus.EXIT, ey), (bus.EXIT + (y - ey), y), (x, y), (x, ty), (tx, ty)]
        else:
            out[(4, rx)] = [(bus.EXIT, ey), (x, ey), (x, ty), (tx, ty)]
    return out


def main():
    nm = json.load(open(proj.P.netmap))
    b = pcbnew.LoadBoard(proj.P.pcb)
    padnets = {"/" + v for p in range(1, 5) for v in nm[f"E{p}"].values()}
    ToX = lambda v: pcbnew.ToMM(v.x) - pg.FACE_ORG[0]
    old = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)
           and t.GetLayer() == pcbnew.In1_Cu and t.GetNetname() in padnets
           and min(ToX(t.GetStart()), ToX(t.GetEnd())) >= bus.EXIT - 1e-6]
    for t in old:
        b.Remove(t)
    sheet = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))
    n = 0
    for (p, rx), pts in paths().items():
        net = b.FindNet("/" + nm[f"E{p}"]["1" if rx == 0 else str(rx + 1)])
        for a, z in zip(pts, pts[1:]):
            if a == z:
                continue
            t = pcbnew.PCB_TRACK(b)
            b.Add(t)
            t.SetLayer(pcbnew.In1_Cu)
            t.SetWidth(mm(W))
            t.SetNet(net)
            t.SetStart(sheet(*a))
            t.SetEnd(sheet(*z))
            n += 1
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"L2 fan-in: 16 lines, {n} tracks (replaced {len(old)}). "
          f"File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
