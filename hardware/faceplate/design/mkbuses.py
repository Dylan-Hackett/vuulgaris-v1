"""The scrub pads' buses: every bar's via joined to its net, and each net brought out to the
right margin. Re-runnable. Deterministic -- geometry from the generator, not a router.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkbuses.py

Per pad (ADR 0003, "Connecting the bars"; README "Layout"), all at the CapTIvate netclass
width, and every track under its OWN pad -- nothing here runs under another pad:

  top edge, L2      RX0 (zone 1) | RX2 | RX0 (zone 4), each a straight track through its
                    stretch's vias, TOP_IN below the edge. RX0 zone 4 runs on to the margin.
  RX2 out, L2       from its last via, down to DEEP_TOP and along under zone 4's RX0 to the
                    margin.
  RX0 join, L3      zone 1's last via to zone 4's first, DEEP_TOP under the edge, under RX2.
                    On L3 because on L2 it would enclose RX2 (the edge reads RX0|RX2|RX0),
                    and it is the full-length return ADR 0003 wanted on the layer below.
  bottom edge, L2   RX1 | RX3, BOT_IN above the edge. RX3 runs on to the margin.
  RX1 out, L2       from its last via, up to DEEP_BOT and along under RX3 to the margin --
                    deep enough to pass under pad 3's RX3 vias, walked ~2.2mm in to clear J1.

A via off its stretch's line (the J1-walked ones) gets a short stub. Every margin exit ends at
x = EXIT, just past the pad copper, where the rest of the routing picks it up.

Idempotent: removes, first, every track on a PADp_RXn net lying wholly at x <= EXIT (the pad
region), which is exactly what this draws. Tracks in the margin are left alone.
tools/boardcheck.py proves the result: every bar of every net in one piece with its exit.

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

TOP_IN, DEEP_TOP = 0.5, 1.3       # below the pad's top edge
BOT_IN, DEEP_BOT = 0.5, 3.0       # above its bottom edge
W = 0.15                          # CapTIvate netclass track
mm = pcbnew.FromMM
gen, G = pg.generator()
C = dict(gen.CFG)
EXIT = G["PAD_X1"] + 0.65         # just past the copper, into the margin


def main():
    nm = json.load(open(proj.P.netmap))
    b = pcbnew.LoadBoard(proj.P.pcb)
    padnets = {"/" + n for p in range(1, 5) for n in nm[f"E{p}"].values()}
    old = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)
           and t.GetNetname() in padnets
           and max(pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetEnd().x)) - pg.FACE_ORG[0] <= EXIT + 1e-6]
    for t in old:
        b.Remove(t)

    def seg(net, layer, a, z):
        t = pcbnew.PCB_TRACK(b)
        b.Add(t)
        t.SetLayer(layer)
        t.SetWidth(mm(W))
        t.SetNet(b.FindNet(net))
        t.SetStart(pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet(a))))
        t.SetEnd(pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet(z))))
        return 1

    n = 0
    for p in range(1, 5):
        yt = G["PAD_TOPS"][p - 1]
        yb = yt + G["PW"]
        net = lambda rx: "/" + nm[f"E{p}"]["1" if rx == 0 else str(rx + 1)]
        vias = gen.copper(C, G, yt)["vias"]
        V = lambda rx, pick=lambda x: True: sorted((x, y) for r, x, y in vias if r == rx and pick(x))
        mid = G["PAD_MID"]
        top_line, top_deep = yt + TOP_IN, yt + DEEP_TOP
        bot_line, bot_deep = yb - BOT_IN, yb - DEEP_BOT
        stretches = (  # (rx, vias, line, runs on to the margin)
            (0, V(0, lambda x: x < mid), top_line, False),
            (2, V(2), top_line, False),
            (0, V(0, lambda x: x > mid), top_line, True),
            (1, V(1), bot_line, False),
            (3, V(3), bot_line, True))
        # Via to via, never through: every via must sit on a segment END. KiCad counts a
        # track that merely passes over a via as connected; Freerouting does not, and saw
        # every intermediate via as an island it had to reach under the fenced-off pads.
        for rx, vs, line, out in stretches:
            nodes = []
            for x, y in vs:
                if abs(y - line) <= 0.25:           # on the line (short bars sit a hair in)
                    nodes.append((x, y))
                else:                               # walked in to clear J1: stub to it
                    nodes.append((x, line))
                    n += seg(net(rx), pcbnew.In1_Cu, (x, line), (x, y))
            if out:          # the last run into the margin dead level on the line,
                nodes.append((G["PAD_X1"] - 0.5, line))   # where the router's stub lies
                nodes.append((EXIT, line))
            for a, z in zip(nodes, nodes[1:]):
                n += seg(net(rx), pcbnew.In1_Cu, a, z)
        # RX2 out, under zone 4's RX0, from its last via's centre
        xa, ya = V(2)[-1]
        n += seg(net(2), pcbnew.In1_Cu, (xa, ya), (xa, top_deep))
        n += seg(net(2), pcbnew.In1_Cu, (xa, top_deep), (EXIT, top_deep))
        # RX1 out, under RX3
        xc, yc = V(1)[-1]
        n += seg(net(1), pcbnew.In1_Cu, (xc, yc), (xc, bot_deep))
        n += seg(net(1), pcbnew.In1_Cu, (xc, bot_deep), (EXIT, bot_deep))
        # RX0 join on L3, under RX2, via centre to via centre
        (xz1, yz1), (xz4, yz4) = V(0, lambda x: x < mid)[-1], V(0, lambda x: x > mid)[0]
        n += seg(net(0), pcbnew.In2_Cu, (xz1, yz1), (xz1, top_deep))
        n += seg(net(0), pcbnew.In2_Cu, (xz1, top_deep), (xz4, top_deep))
        n += seg(net(0), pcbnew.In2_Cu, (xz4, top_deep), (xz4, yz4))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())      # the GND plane clears round new vias
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"{n} bus tracks on E1-E4 (replaced {len(old)}). File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
