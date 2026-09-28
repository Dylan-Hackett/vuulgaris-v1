"""J1's escape and the corridor's grounds: exact geometry, before the router. Re-runnable.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkescape.py

J1 sits in the gap between pads 3 and 4 with its signal row (odd pins: TEST, RST, RXD,
TXD, 3V3) reaching under pad 4's edge and its GND row under pad 3's. Nothing may leave it
downward (pad 4) or upward (pad 3), so the four inner signals climb into the 2.2mm channel
between J1's two rows and run out along it; left to the router, two of them never did.

  * TEST (pin 1, the rightmost) leaves straight to the right, inside the corridor.
  * RST, RXD, TXD, 3V3 (pins 3, 5, 7, 9) each rise off their pad into a lane of the
    channel -- pin 3 lowest, pin 9 highest -- and run right to ESC_X. Rising in that order
    nothing crosses: every lane starts right of the risers of the pins left of it.
  * J1's GND row (already one piece on B.Cu) gets a via just past its end, and TP4 (SBW
    GND) one beside it, both into the L3 GND strip (mkzones.py extends it to J1's).

From ESC_X on, the router takes over. Idempotent: removes, first, every B.Cu track wholly
inside J1's escape box on those nets and the two GND vias at their spots.

After this writes the board, File -> Revert in Pcbnew before touching it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FACE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(FACE), "kicad", "tools"))
sys.argv[1:1] = ["--project", "faceplate"]
import proj            # noqa: E402
import panelgeo as pg  # noqa: E402
import pcbnew          # noqa: E402

mm = pcbnew.FromMM
ESC_X = 236.0                 # where the router picks the lanes up (J1's pads end at 234.585)
CLR = 0.2                     # Default / Power / GND netclass clearance
# pin -> lane order, bottom (nearest the signal row) first
LANES = ("3", "5", "7", "9")
GND_VIA = (235.9, 109.075)    # just past the GND row's end (pin 2), on its centre line
TP4_VIA_DX = 1.6              # TP4's via, to its right (TP5 is 3.6 along)
VIA_D, VIA_DRILL = 0.6, 0.3


def main():
    nm = json.load(open(proj.P.netmap))
    b = pcbnew.LoadBoard(proj.P.pcb)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    ToP = lambda v: (pcbnew.ToMM(v.x) - pg.FACE_ORG[0], pcbnew.ToMM(v.y) - pg.FACE_ORG[1])
    pad = {p.GetNumber(): p for p in fps["J1"].Pads()}
    box = lambda p: tuple(v for q in (ToP(pcbnew.VECTOR2I(p.GetBoundingBox().GetLeft(), p.GetBoundingBox().GetTop())),
                                      ToP(pcbnew.VECTOR2I(p.GetBoundingBox().GetRight(), p.GetBoundingBox().GetBottom())))
                          for v in q)
    sig_top = min(box(pad[n])[1] for n in ("1", "3", "5", "7", "9"))       # signal row's top edge
    gnd_bot = max(box(pad[n])[3] for n in ("2", "4", "6", "8", "10"))      # GND row's bottom edge
    nets = {n: "/" + nm["J1"][n] for n in pad}
    tp4 = ToP(fps["TP4"].GetPosition())
    tp4_via = (tp4[0] + TP4_VIA_DX, tp4[1])

    # remove what this script drew before
    esc_box = (box(pad["9"])[0] - 0.5, gnd_bot - 0.1, ESC_X + 0.01, box(pad["1"])[3])
    within = lambda q: esc_box[0] <= q[0] <= esc_box[2] and esc_box[1] <= q[1] <= esc_box[3]
    ours = set(nets[n] for n in ("1", "3", "5", "7", "9"))
    old = [t for t in b.GetTracks()
           if (not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu
               and t.GetNetname() in ours and within(ToP(t.GetStart())) and within(ToP(t.GetEnd())))
           or (isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "/GND"
               and any(abs(ToP(t.GetPosition())[0] - x) < 0.01 and abs(ToP(t.GetPosition())[1] - y) < 0.01
                       for x, y in (GND_VIA, tp4_via)))
           or (not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "/GND"
               and all(abs(ToP(q)[1] - GND_VIA[1]) < 0.01 and box(pad["2"])[2] - 0.6 <= ToP(q)[0] <= GND_VIA[0] + 0.01
                       for q in (t.GetStart(), t.GetEnd())))
           or (not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "/GND"
               and all(abs(ToP(q)[1] - tp4[1]) < 0.01 and tp4[0] - 0.01 <= ToP(q)[0] <= tp4_via[0] + 0.01
                       for q in (t.GetStart(), t.GetEnd())))]
    for t in old:
        b.Remove(t)

    sheet = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))
    # each net's netclass width, from the project (KiCad 7's bindings hand GetNetClass()
    # back as an opaque object)
    ns = json.load(open(proj.P.pro))["net_settings"]
    cw = {c["name"]: c["track_width"] for c in ns["classes"]}
    pat = {q["pattern"]: q["netclass"] for q in ns["netclass_patterns"]}
    width = {n: cw.get(pat.get(nets[n], "Default"), cw["Default"]) for n in ("1", "3", "5", "7", "9")}

    def seg(n_or_net, a, z, w):
        t = pcbnew.PCB_TRACK(b)
        b.Add(t)
        t.SetLayer(pcbnew.B_Cu)
        t.SetWidth(mm(w))
        t.SetNet(b.FindNet(n_or_net))
        t.SetStart(sheet(*a))
        t.SetEnd(sheet(*z))

    def via(net, xy):
        v = pcbnew.PCB_VIA(b)
        b.Add(v)
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetPosition(sheet(*xy))
        v.SetWidth(mm(VIA_D))
        v.SetDrill(mm(VIA_DRILL))
        v.SetNet(b.FindNet(net))

    # the lanes, bottom up, each CLR clear of the row below it
    y = sig_top - CLR
    for n in LANES:
        w = width[n]
        y -= w / 2
        x = ToP(pad[n].GetPosition())[0]
        seg(nets[n], (x, sig_top + w / 2), (x, y), w)      # off the pad's top edge, up
        seg(nets[n], (x, y), (ESC_X, y), w)                # out along the channel
        y -= w / 2 + CLR
    if y < gnd_bot:
        sys.exit(f"channel too narrow: lanes reach {y:.3f}, GND row ends at {gnd_bot:.3f}")
    # TEST straight out to the right, level with the lanes' corridor side
    x1 = ToP(pad["1"].GetPosition())[0]
    ty = sig_top + width["1"] / 2 + 0.3
    seg(nets["1"], (x1, ty), (ESC_X, ty), width["1"])
    # grounds into the L3 strip
    g2 = box(pad["2"])
    seg("/GND", (g2[2] - 0.5, GND_VIA[1]), GND_VIA, 0.3)
    via("/GND", GND_VIA)
    seg("/GND", tp4, tp4_via, 0.3)
    via("/GND", tp4_via)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"J1 escape: 4 lanes to x {ESC_X}, TEST out, 2 GND vias (replaced {len(old)}); "
          f"top lane {y + CLR:.3f} vs GND row {gnd_bot:.3f}. File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
