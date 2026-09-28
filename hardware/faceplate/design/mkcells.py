"""Wire each network cell's electrode side: the via the line comes up on, to the TVS, to the
470R. Re-runnable. Deterministic -- the positions are the grid's, from design/mkplace.py.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkcells.py

For every pad p and RX index n (README "Layout"): a 0.5/0.3 via on the column line, VIA_DY
from the R's centre -- between the TVS and the R above, inside its own cell -- then B.Cu
straight down the column line to TVS pin 1 and on to R pin 1. Run after mkbuses.py and
before mkroute.py: left to the router, these sixteen layer changes never found room in the
packed grid, and with them fixed its job on the electrode side is a single-layer one, each
bus exit to its via on L2.

Idempotent: removes, first, every via on a PADp_RXn net at a cell spot and every B.Cu track
on a PADp_RXn net inside the grid.

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

# the grid, as design/mkplace.py placed it
COL_X = (280.30, 283.50, 288.00, 290.92)
ROW_Y = {1: 77.15, 2: 83.15, 3: 89.15, 4: 95.15}
VIA_DY, TVS_DY, R1_DY = -2.9, -2.0, -0.75
VIA_D, VIA_DRILL, W = 0.5, 0.3, 0.15          # CapTIvate netclass
mm = pcbnew.FromMM


def main():
    nm = json.load(open(proj.P.netmap))
    b = pcbnew.LoadBoard(proj.P.pcb)
    net = lambda p, n: b.FindNet("/" + nm[f"E{p}"]["1" if n == 0 else str(n + 1)])
    padnets = {"/" + v for p in range(1, 5) for v in nm[f"E{p}"].values()}
    spots = {(round(COL_X[n], 3), round(ROW_Y[p] + VIA_DY, 3)) for p in ROW_Y for n in range(4)}
    gx0, gx1 = min(COL_X) - 1.5, max(COL_X) + 1.5
    gy0, gy1 = min(ROW_Y.values()) - 3.5, max(ROW_Y.values()) + 1.5
    P = lambda t: tuple(round(v, 3) for v in (pcbnew.ToMM(t.x) - pg.FACE_ORG[0], pcbnew.ToMM(t.y) - pg.FACE_ORG[1]))
    inside = lambda q: gx0 <= q[0] <= gx1 and gy0 <= q[1] <= gy1
    old = [t for t in b.GetTracks() if t.GetNetname() in padnets and (
        (isinstance(t, pcbnew.PCB_VIA) and P(t.GetPosition()) in spots) or
        (not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu
         and inside(P(t.GetStart())) and inside(P(t.GetEnd()))))]
    for t in old:
        b.Remove(t)
    sheet = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))
    nv = nt = 0
    for p, y in ROW_Y.items():
        for n, x in enumerate(COL_X):
            v = pcbnew.PCB_VIA(b)
            b.Add(v)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetPosition(sheet(x, y + VIA_DY))
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_DRILL))
            v.SetNet(net(p, n))
            nv += 1
            for a, z in ((y + VIA_DY, y + TVS_DY), (y + TVS_DY, y + R1_DY)):
                t = pcbnew.PCB_TRACK(b)
                b.Add(t)
                t.SetLayer(pcbnew.B_Cu)
                t.SetWidth(mm(W))
                t.SetNet(net(p, n))
                t.SetStart(sheet(x, a))
                t.SetEnd(sheet(x, z))
                nt += 1
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())      # the GND plane clears round new vias
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"{nv} cell vias, {nt} cell tracks (replaced {len(old)}). "
          f"File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
