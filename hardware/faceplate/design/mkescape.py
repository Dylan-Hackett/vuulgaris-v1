"""J1's escape and the corridor to the margin: exact geometry, before the router. Re-runnable.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkescape.py

J1 sits in the gap between pads 3 and 4 with its signal row (odd pins: TEST, RST, RXD,
TXD, 3V3) reaching under pad 4's edge and its GND row under pad 3's. Nothing may leave it
downward (pad 4) or upward (pad 3), and the router, left to it, never got the five lines
out and along the corridor past the test pads. So all of it is drawn here, on B.Cu:

  * RST, RXD, TXD, 3V3 (pins 3, 5, 7, 9) rise off their pads into lanes of the 2.2mm
    channel between J1's rows -- pin 3 lowest, pin 9 highest, so nothing crosses -- and
    run right to ESC_X. TEST (pin 1, the rightmost) leaves straight to the right.
  * Past J1 the five fan out to mkplace.CORRIDOR_Y, 1.3 apart, and run straight down the
    corridor to CORR_END, just inside the margin. Each test pad sits ON its own line and
    R2 stands across the 3V3 and TXD lines; every line is split at those pads, so each
    pad is on a track end.
  * J1's GND row, joined pad to pad along its centre line (mkboard.py drew that once; it
    lives here now), gets a via just past its end into the L3 GND strip (mkzones.py widens
    it there), and TP4 (SBW GND) a track to that via.

From CORR_END on, the router takes over: into the margin and U1, whose pins run in another
order. Idempotent: removes, first, every B.Cu track on those nets inside J1's rows and the
corridor, and the GND via and TP4's link.

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
from mkplace import CORRIDOR_Y  # noqa: E402

mm = pcbnew.FromMM
ESC_X = 236.0                 # the channel lanes end here (J1's pads end at 234.585)
FAN_X = 239.5                 # ... and are at their corridor heights by here
CORR_END = 277.5              # just inside the margin (pad copper ends at 277.14)
CLR = 0.2                     # Default / Power / GND netclass clearance
LANES = ("3", "5", "7", "9")  # channel lanes, bottom (nearest the signal row) first
GND_VIA = (235.9, 109.075)    # just past the GND row's end (pin 2), on its centre line
VIA_D, VIA_DRILL = 0.6, 0.3


def main():
    nm = json.load(open(proj.P.netmap))
    b = pcbnew.LoadBoard(proj.P.pcb)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    ToP = lambda v: (pcbnew.ToMM(v.x) - pg.FACE_ORG[0], pcbnew.ToMM(v.y) - pg.FACE_ORG[1])
    pad = {p.GetNumber(): p for p in fps["J1"].Pads()}

    def box(p):
        q = p.GetBoundingBox()
        a = ToP(pcbnew.VECTOR2I(q.GetLeft(), q.GetTop()))
        z = ToP(pcbnew.VECTOR2I(q.GetRight(), q.GetBottom()))
        return a + z
    sig_top = min(box(pad[n])[1] for n in ("1", "3", "5", "7", "9"))       # signal row's top edge
    gnd_bot = max(box(pad[n])[3] for n in ("2", "4", "6", "8", "10"))      # GND row's bottom edge
    nets = {n: nm["J1"][n] for n in pad}                                   # without the "/"
    sig = [nets[n] for n in ("1", "3", "5", "7", "9")]

    # taps on each line: test pads, and R2's two pads
    taps = {n: [] for n in sig}
    for ref in ("TP1", "TP2", "TP3", "TP5", "TP6", "R2"):
        for p in fps[ref].Pads():
            n = p.GetNetname().lstrip("/")
            if n in taps:
                taps[n].append(ToP(p.GetPosition())[0])
    tp4 = ToP(fps["TP4"].GetPosition())

    # remove what this script drew before
    x_lo = box(pad["9"])[0] - 0.5
    inside = lambda q: x_lo <= q[0] <= CORR_END + 0.01 and 108.4 <= q[1] <= sig_top + 5.0
    old = [t for t in b.GetTracks()
           if (not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu
               and t.GetNetname().lstrip("/") in sig
               and inside(ToP(t.GetStart())) and inside(ToP(t.GetEnd())))
           or (isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "/GND"
               and abs(ToP(t.GetPosition())[0] - GND_VIA[0]) < 0.01
               and abs(ToP(t.GetPosition())[1] - GND_VIA[1]) < 0.01)
           or (not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "/GND"
               and t.GetLayer() == pcbnew.B_Cu
               and all(box(pad["10"])[0] <= ToP(q)[0] <= box(pad["2"])[2]
                       and abs(ToP(q)[1] - ToP(pad["2"].GetPosition())[1]) < 0.01
                       for q in (t.GetStart(), t.GetEnd())))
           or (not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "/GND"
               and t.GetLayer() == pcbnew.B_Cu
               and all(box(pad["2"])[2] - 0.6 <= ToP(q)[0] <= tp4[0] + 0.01
                       and 108.4 <= ToP(q)[1] <= 110.5 for q in (t.GetStart(), t.GetEnd())))]
    for t in old:
        b.Remove(t)

    # each net's width, from the project (KiCad 7's bindings hand GetNetClass() back opaque)
    ns = json.load(open(proj.P.pro))["net_settings"]
    cw = {c["name"]: c["track_width"] for c in ns["classes"]}
    pat = {q["pattern"].lstrip("/"): q["netclass"] for q in ns["netclass_patterns"]}
    width = {n: cw.get(pat.get(n, "Default"), cw["Default"]) for n in sig}

    sheet = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))

    def seg(net, a, z, w):
        if a == z:
            return
        t = pcbnew.PCB_TRACK(b)
        b.Add(t)
        t.SetLayer(pcbnew.B_Cu)
        t.SetWidth(mm(w))
        t.SetNet(b.FindNet("/" + net))
        t.SetStart(sheet(*a))
        t.SetEnd(sheet(*z))

    def run(net, pts):
        for a, z in zip(pts, pts[1:]):
            seg(net, a, z, width[net])

    def corridor(net, x, y):
        """from (x, y) at ESC_X, fan out and run the corridor, split at every tap"""
        yc = CORRIDOR_Y[net]
        # TXD bends 0.6 after 3V3, the line above it, so their corners never close up
        bend = ESC_X + (0.6 if net == "MSP430_TXD" else 0.0)
        pts = [(x, y), (bend, y), (FAN_X, yc)] + [(tx, yc) for tx in sorted(taps[net])] + [(CORR_END, yc)]
        return pts

    # the channel lanes, bottom up, each CLR clear of the row below it
    y = sig_top - CLR
    for n in LANES:
        w = width[nets[n]]
        y -= w / 2
        x = ToP(pad[n].GetPosition())[0]
        run(nets[n], [(x, sig_top + w / 2)] + corridor(nets[n], x, y))
        y -= w / 2 + CLR
    if y < gnd_bot:
        sys.exit(f"channel too narrow: lanes reach {y:.3f}, GND row ends at {gnd_bot:.3f}")
    # TEST straight out to the right of its pad, then down the corridor
    x1 = ToP(pad["1"].GetPosition())[0]
    run(nets["1"], corridor(nets["1"], x1, sig_top + width[nets["1"]] / 2 + 0.3))
    # J1's GND row joined pad to pad along its centre line (mkboard.py drew this once)
    grow = sorted(ToP(pad[n].GetPosition()) for n in ("2", "4", "6", "8", "10"))
    for a_, z_ in zip(grow, grow[1:]):
        seg("GND", a_, z_, 0.5)
    # grounds: J1's row into the L3 strip, TP4 to the same via
    g2 = box(pad["2"])
    seg("GND", (g2[2] - 0.5, GND_VIA[1]), GND_VIA, 0.3)
    seg("GND", GND_VIA, tp4, 0.3)
    v = pcbnew.PCB_VIA(b)
    b.Add(v)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetPosition(sheet(*GND_VIA))
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNet(b.FindNet("/GND"))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"J1 escape and corridor: 5 lines to x {CORR_END}, {sum(len(v) for v in taps.values())} taps, "
          f"GND via + TP4 (replaced {len(old)}). File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
