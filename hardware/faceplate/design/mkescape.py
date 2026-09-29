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
  * The corridor's right end is TAIL: fixed geometry to every pad, as Dylan rerouted it by
    hand (2026-09-29). RXD and TXD hop to L2 under the via patch (ADR 0013) -- not in the
    gold between pads 3 and 4 -- and on to R3 and U1 pins 4 and 5; RST runs to R1, C4 and
    U1 pin 2, TEST to U1 pin 3, both through their own L2 hops; C4's GND gets its via under
    the patch. Past C4 that was the router's routing, which the reroute kept. So these four
    nets reach the router complete, and a rebuild gives this corner back.
  * J1's GND row, joined pad to pad along its centre line (mkboard.py drew that once; it
    lives here now), gets a via just past its end into the L3 GND strip (mkzones.py widens
    it there), and TP4 (SBW GND) a track to that via.

3V3 alone runs to CORR_END and the router takes it from there. Idempotent: removes, first,
every track and via on TXD, RXD, RST and TEST, 3V3's B.Cu inside J1's rows and the
corridor, C4's GND tail, and the J1 GND via and TP4's link.

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
# Where each corridor lane stops and TAIL takes over (CORR_END if not named). TEST's is its
# last tap, TP1, where it jogs down 0.6 to clear RXD's hop.
LANE_END = {"MSP430_TXD": 278.88213, "MSP430_RXD": 277.7745, "MSP_TEST": 258.4}
# The corridor's right end, Dylan's hand reroute (2026-09-29), absolute panel mm: per net,
# (layer, width, polyline); "REF.PIN" is that pad's centre. TAIL_VIAS: each net's vias, which
# its polylines start or end on. Checked by DRC, boardcheck and panelcheck like the rest.
TAIL = {
    "MSP430_TXD": [
        ("B", 0.25, [(278.88213, 111.675), (279.51895, 111.03818)]),
        ("L2", 0.25, [(279.51895, 111.03818), (276.2, 114.35713), (276.2, 115.425),
                      (285.7, 115.425), (285.7, 110.9)]),                  # under RXD's hop
        ("B", 0.25, [(285.7, 110.9), "U1.4"])],
    "MSP430_RXD": [
        ("B", 0.25, [(277.7745, 112.975), (279.55, 114.7505)]),
        ("L2", 0.25, [(279.55, 114.7505), (279.6995, 114.9), (284.2, 114.9), (284.2, 110.2)]),
        ("B", 0.25, [(284.2, 110.2), "R3.2"]),
        ("B", 0.25, [(284.2, 110.2), (285.2, 109.2), "U1.5"])],
    "MSP_RST": [
        ("B", 0.25, [(277.5, 114.275), (278.6, 115.375), (281.2, 115.375), (281.5873, 114.9877),
                     (281.5873, 114.108), (281.5873, 113.0891)]),
        ("B", 0.25, [(281.5873, 114.108), (281.8092, 114.3299), (283.3926, 114.3299),
                     (284.95, 112.7725), (284.95, 112.2595)]),
        ("L2", 0.25, [(284.95, 112.2595), (284.95, 110.7157), (285.8581, 109.8076),
                      (286.6804, 109.8076)]),
        ("B", 0.25, [(286.6804, 109.8076), (286.7, 109.788), "U1.2"]),
        ("B", 0.25, [(281.5873, 113.0891), (281.8465, 112.8299), (282.775, 112.8299), "R1.2"]),
        ("B", 0.25, [(281.5873, 113.0891), (281.4156, 112.9174)]),
        ("B", 0.1874, [(281.4156, 112.9174), (281.3174, 112.9174), (280.725, 112.325)]),  # necked
        ("B", 0.25, [(280.725, 112.325), "C4.1"])],
    "MSP_TEST": [
        ("B", 0.25, [(258.4, 115.575), (259.0, 116.175), (283.1205, 116.175), (287.1611, 112.1344)]),
        ("L2", 0.25, [(287.1611, 112.1344), (287.3338, 111.9617), (287.3338, 107.9196),
                      (286.2, 106.7858)]),
        ("B", 0.25, [(286.2, 106.7858), "U1.3"])],
    "GND": [                                                            # C4's ground
        ("B", 0.3, [(280.43702, 111.05864), (279.925, 111.57066), (279.925, 112.8), "C4.2"])],
}
TAIL_VIAS = {"MSP430_TXD": [(279.51895, 111.03818), (285.7, 110.9)],
             "MSP430_RXD": [(279.55, 114.7505), (284.2, 110.2)],
             "MSP_RST": [(284.95, 112.2595), (286.6804, 109.8076)],
             "MSP_TEST": [(287.1611, 112.1344), (286.2, 106.7858)],
             "GND": [(280.43702, 111.05864)]}   # 0.02 below the reroute: clear of TXD's via
TAIL_NETS = ("MSP430_TXD", "MSP430_RXD", "MSP_RST", "MSP_TEST")
GND_TAIL_BOX = (279.5, 110.7, 281.0, 113.7)   # C4's GND via and its run to C4 pin 2


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
    # TXD, RXD, RST and TEST are all this script's now, end to end; and C4's GND tail
    old += [t for t in b.GetTracks() if t.GetNetname().lstrip("/") in TAIL_NETS]
    # C4's GND tail: whatever GND via and B.Cu track lies in its box (nothing else does), so
    # a change to TAIL's numbers still clears the last build's
    x0, y0, x1, y1 = GND_TAIL_BOX
    inbox = lambda q: x0 <= q[0] <= x1 and y0 <= q[1] <= y1
    old += [t for t in b.GetTracks() if t.GetNetname() == "/GND"
            and ((isinstance(t, pcbnew.PCB_VIA) and inbox(ToP(t.GetPosition())))
                 or (not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu
                     and inbox(ToP(t.GetStart())) and inbox(ToP(t.GetEnd()))))]
    # once each: two proxies of one track are not ==, and removing it twice crashes pcbnew
    old = list({t.m_Uuid.AsString(): t for t in old}.values())
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
        """from (x, y) at ESC_X, fan out and run the corridor, split at every tap; a tap pad
        whose centre is off the line (R2's) gets a stub to its centre (stubs, below)"""
        yc = CORRIDOR_Y[net]
        # TXD bends 0.6 after 3V3, the line above it, so their corners never close up
        bend = ESC_X + (0.6 if net == "MSP430_TXD" else 0.0)
        # each stops where TAIL takes over (LANE_END), 3V3 at the margin
        end = LANE_END.get(net, CORR_END)
        pts = [(x, y), (bend, y), (FAN_X, yc)] + [(tx, yc) for tx in sorted(taps[net]) if tx < end]
        return pts + [(end, yc)]

    # the channel lanes, bottom up, each CLR clear of the row below it
    y = sig_top - CLR
    for n in LANES:
        w = width[nets[n]]
        y -= w / 2
        x = ToP(pad[n].GetPosition())[0]
        run(nets[n], [ToP(pad[n].GetPosition()), (x, sig_top + w / 2)] + corridor(nets[n], x, y))
        y -= w / 2 + CLR
    if y < gnd_bot:
        sys.exit(f"channel too narrow: lanes reach {y:.3f}, GND row ends at {gnd_bot:.3f}")
    # TEST straight out to the right of its pad, then down the corridor
    x1 = ToP(pad["1"].GetPosition())[0]
    run(nets["1"], [ToP(pad["1"].GetPosition())] +
        corridor(nets["1"], x1, sig_top + width[nets["1"]] / 2 + 0.3))
    # a tap pad off its line gets a stub from the line to its centre (R2 straddles two)
    for ref in ("TP1", "TP2", "TP3", "TP5", "TP6", "R2"):
        for p in fps[ref].Pads():
            n = p.GetNetname().lstrip("/")
            px, py = ToP(p.GetPosition())
            if n in taps and px < LANE_END.get(n, CORR_END) and abs(py - CORRIDOR_Y[n]) > 1e-6:
                seg(n, (px, CORRIDOR_Y[n]), (px, py), width[n])
    # the corridor's right end: TAIL, to every pad
    padxy = lambda name: next(ToP(p.GetPosition()) for p in fps[name.split(".")[0]].Pads()
                              if p.GetNumber() == name.split(".")[1])
    layer = {"B": pcbnew.B_Cu, "L2": pcbnew.In1_Cu}
    n_tail = 0
    for net, runs in TAIL.items():
        for ly, w, pl in runs:
            pts = [padxy(q) if isinstance(q, str) else q for q in pl]
            for a_, z_ in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b)
                b.Add(t)
                t.SetLayer(layer[ly])
                t.SetWidth(mm(w))
                t.SetNet(b.FindNet("/" + net))
                t.SetStart(sheet(*a_))
                t.SetEnd(sheet(*z_))
                n_tail += 1
        for xy in TAIL_VIAS[net]:
            vv = pcbnew.PCB_VIA(b)
            b.Add(vv)
            vv.SetViaType(pcbnew.VIATYPE_THROUGH)
            vv.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            vv.SetPosition(sheet(*xy))
            vv.SetWidth(mm(VIA_D))
            vv.SetDrill(mm(VIA_DRILL))
            vv.SetNet(b.FindNet("/" + net))
    # J1's GND row joined pad to pad along its centre line (mkboard.py drew this once)
    grow = sorted(ToP(pad[n].GetPosition()) for n in ("2", "4", "6", "8", "10"))
    for a_, z_ in zip(grow, grow[1:]):
        seg("GND", a_, z_, 0.5)
    # grounds: J1's row into the L3 strip, TP4 to the same via
    g2 = box(pad["2"])
    seg("GND", ToP(pad["2"].GetPosition()), GND_VIA, 0.3)
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
    print(f"J1 escape and corridor: 5 lines, {sum(len(v) for v in taps.values())} taps, the tail "
          f"({n_tail} tracks, {sum(len(v) for v in TAIL_VIAS.values())} vias), GND via + TP4 "
          f"(replaced {len(old)}). File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
