"""The faceplate's GND on L3: solid, and never under a pad. Re-runnable.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkzones.py

Three areas, all In2.Cu, net GND (ADR 0003: L3 ground, none under the electrodes):

  * the right margin, from just past the pad copper to the board edge -- under U1, the
    network grid and the corner group, so every ground there is one short via away;
  * a strip down the gap between pads 3 and 4, from J1 to the margin, under all five of
    the corridor's lines (ADR 0003, "Route digital lines..."), 0.75 clear of both pads'
    copper, widened at J1's end to take its GND via.

Solid, not hatched (2026-09-28). Hatched first, to keep capacitance off the L2 sensor
lines crossing the margin; but a via that lands in a hatch hole touches nothing, and the
router takes the plane for solid, so grounds it thought done were open. L2 is ~1.1mm above
L3 (the 4-layer core), so solid adds under 1pF to a fan-in line against the tens of pF of
its pad, and it shields the digital lines on L4 properly. It is still never under a pad.
Idempotent: removes every GND zone on In2.Cu first.

After this writes the board, File -> Revert in Pcbnew before touching it.
"""
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
gen, G = pg.generator()
X_MARGIN = G["PAD_X1"] + 0.5                  # pad copper ends at PAD_X1
GAP_TOP = G["PAD_TOPS"][2] + G["PW"]          # pad 3's bottom edge
GAP_BOT = G["PAD_TOPS"][3]                    # pad 4's top edge
STRIP_CLEAR = 0.75
STRIP_X0 = 218.0                              # from J1's far end


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


AREAS = [
    rect(X_MARGIN, 0.0, G["PANEL_W"], G["PANEL_H"]),     # clipped to the outline by the fill
    # under all five of the corridor's lines (mkescape.py), 0.75 clear of both pads' copper
    rect(STRIP_X0, GAP_TOP + STRIP_CLEAR, X_MARGIN + 0.1, GAP_BOT - STRIP_CLEAR),
    # at J1's end, up to J1's GND row -- its via lands here -- 0.25 clear of pad 3's edge,
    # past J1's pads, not under them
    rect(234.9, GAP_TOP + 0.25, 237.2, GAP_TOP + STRIP_CLEAR + 0.1),
]


def main():
    b = pcbnew.LoadBoard(proj.P.pcb)
    gnd = b.FindNet("/GND")
    # New zones first, old ones out after: in KiCad 7's bindings a ZONE made after a
    # removal hands back an opaque Outline(), and a Python-built outline handed over
    # crashes pcbnew.
    old = [z for z in b.Zones() if z.GetLayer() == pcbnew.In2_Cu and z.GetNetname() == "/GND"]
    for pts in AREAS:
        z = pcbnew.ZONE(b)
        z.SetLayer(pcbnew.In2_Cu)
        z.SetNet(gnd)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            sx, sy = pg.face_sheet((x, y))
            ol.Append(mm(sx), mm(sy))
        z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)          # solid: see the docstring
        z.SetMinThickness(mm(0.2))
        z.SetLocalClearance(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        b.Add(z)
    for z in old:
        b.Remove(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"{len(AREAS)} GND zones on In2.Cu, solid. File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
