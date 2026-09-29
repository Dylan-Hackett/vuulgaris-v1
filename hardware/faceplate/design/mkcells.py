"""Wire each network cell's electrode side: the via the line comes up on, to the TVS, to the
470R. Re-runnable. Deterministic -- the positions are the grid's, from design/mkplace.py.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkcells.py

For every pad p and RX index n (README "Layout"): a 0.5/0.3 via at VIA_X / VIA_LEVEL --
between the TVS and the R above, inside its own cell -- then B.Cu down to TVS pin 1 and on
to R pin 1. Run after mkbuses.py and
before mkroute.py: left to the router, these sixteen layer changes never found room in the
packed grid, and with them fixed its job on the electrode side is a single-layer one, each
bus exit to its via on L2.

Also each TVS's ground: a GND via beside its ground pin, into the L3 plane (GND_SKIP says
where not). Idempotent: removes, first, every via and B.Cu track on a PADp_RXn net or GND
inside the grid.

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
TVS_DY, R1_DY = -2.0, -0.75
# Each cell's via: on its column line (column 0's 0.4 right, to open a fourth slot in the
# fan-in's left strip) at its own height in the cell band, in the order that pad's lines
# arrive (design/mkfanin.py): pads 1-3 come in from the left as RX0, RX2, RX1, RX3 from the
# top, pad 4 from the right, so reversed.
VIA_X = {0: COL_X[0] + 0.4, 1: COL_X[1], 2: COL_X[2], 3: COL_X[3]}
_LEFT = {0: -4.3, 2: -3.8, 1: -3.3, 3: -2.8}
VIA_LEVEL = {1: _LEFT, 2: _LEFT, 3: _LEFT, 4: {3: -4.3, 1: -3.8, 2: -3.3, 0: -2.8}}
VIA_D, VIA_DRILL, W = 0.5, 0.3, 0.15          # CapTIvate netclass
# Each TVS's ground: a GND via just right of its ground pin, at the TVS's own height -- L2
# there is clear of the fan-in lanes, which all run above it -- into the L3 plane. Not in
# row 4 of columns 0, 2, 3: their channels carry three traces past it there, and column 3's
# would sit on pad 4's right-hand fan-in strip; the router grounds those three.
GND_DX, GND_D, GND_W = 0.55, 0.6, 0.3
GND_SKIP = {(4, 0), (4, 3)}
# Row 4, column 2 has no room beside its pin: its via goes up into the gap between rows 3
# and 4 (pad 4's RX3 lane stops short of it; 0.29 off row 3's R corner, 0.23 off the RX1
# lane, 1.14 of column 3's channel left for its three traces), stub down to the pin.
GND_UP = {(4, 2): (0.15, -2.4)}
# C3's ground (VREG) takes a track to the via beside row 4, column 1's TVS, 1.8 away.
C3_TO = (4, 1)
mm = pcbnew.FromMM


def main():
    nm = json.load(open(proj.P.netmap))
    b = pcbnew.LoadBoard(proj.P.pcb)
    net = lambda p, n: b.FindNet("/" + nm[f"E{p}"]["1" if n == 0 else str(n + 1)])
    padnets = {"/" + v for p in range(1, 5) for v in nm[f"E{p}"].values()}
    gx0, gx1 = min(COL_X) - 1.5, max(COL_X) + 1.5
    gy0, gy1 = min(ROW_Y.values()) - 5.0, max(ROW_Y.values()) + 1.5   # the highest via is 4.3 up
    P = lambda t: tuple(round(v, 3) for v in (pcbnew.ToMM(t.x) - pg.FACE_ORG[0], pcbnew.ToMM(t.y) - pg.FACE_ORG[1]))
    inside = lambda q: gx0 <= q[0] <= gx1 and gy0 <= q[1] <= gy1
    old = [t for t in b.GetTracks() if t.GetNetname() in padnets | {"/GND"} and (
        (isinstance(t, pcbnew.PCB_VIA) and inside(P(t.GetPosition()))) or
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
            vx, vy = VIA_X[n], y + VIA_LEVEL[p][n]
            v.SetPosition(sheet(vx, vy))
            v.SetWidth(mm(VIA_D))
            v.SetDrill(mm(VIA_DRILL))
            v.SetNet(net(p, n))
            nv += 1
            for a, z in (((vx, vy), (x, y + TVS_DY)), ((x, y + TVS_DY), (x, y + R1_DY))):
                t = pcbnew.PCB_TRACK(b)
                b.Add(t)
                t.SetLayer(pcbnew.B_Cu)
                t.SetWidth(mm(W))
                t.SetNet(net(p, n))
                t.SetStart(sheet(*a))
                t.SetEnd(sheet(*z))
                nt += 1
    # TVS grounds
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    gnd = b.FindNet("/GND")
    ng = 0
    for p, y in ROW_Y.items():
        for n in range(4):
            if (p, n) in GND_SKIP:
                continue
            pin2 = next(q for q in fps[f"D{p}{n + 1}"].Pads() if q.GetNumber() == "2")
            px, py = P(pin2.GetPosition())
            dx, dy = GND_UP.get((p, n), (GND_DX, 0.0))
            v = pcbnew.PCB_VIA(b)
            b.Add(v)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetPosition(sheet(px + dx, py + dy))
            v.SetWidth(mm(GND_D))
            v.SetDrill(mm(VIA_DRILL))
            v.SetNet(gnd)
            t = pcbnew.PCB_TRACK(b)
            b.Add(t)
            t.SetLayer(pcbnew.B_Cu)
            t.SetWidth(mm(GND_W))
            t.SetNet(gnd)
            t.SetStart(sheet(px, py))
            t.SetEnd(sheet(px + dx, py + dy))
            ng += 1
            if (p, n) == C3_TO:
                c3g = next(q for q in fps["C3"].Pads() if q.GetNumber() == "2")
                t = pcbnew.PCB_TRACK(b)
                b.Add(t)
                t.SetLayer(pcbnew.B_Cu)
                t.SetWidth(mm(GND_W))
                t.SetNet(gnd)
                t.SetStart(c3g.GetPosition())
                t.SetEnd(sheet(px + dx, py + dy))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())      # the GND plane clears round new vias
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"{nv} cell vias, {nt} cell tracks, {ng} TVS grounds (replaced {len(old)}). "
          f"File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
