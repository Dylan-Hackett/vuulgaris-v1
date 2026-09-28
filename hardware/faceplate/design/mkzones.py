"""The faceplate's GND on L3: hatched, and never under a pad. Re-runnable.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkzones.py

Two areas, both In2.Cu, net GND (ADR 0003: L3 hatched ground, none under the electrodes):

  * the right margin, from just past the pad copper to the board edge -- under U1, the
    network grid and the corner group, so every ground there is one short via away;
  * a strip down the middle of the gap between pads 3 and 4, from J1 to the margin, under
    the UART and power lines (ADR 0003, "Route digital lines..."): 3mm wide, 2.5mm clear
    of both pads' copper, widened at J1's end to take its GND via.

Hatched, not solid: under the sensor lines crossing the margin on L2 a solid pour would
add more capacitance to them than it needs to shield them.
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
STRIP_CLEAR = 2.5
STRIP_X0 = 218.0                              # from J1's far end


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


AREAS = [
    rect(X_MARGIN, 0.0, G["PANEL_W"], G["PANEL_H"]),     # clipped to the outline by the fill
    rect(STRIP_X0, GAP_TOP + STRIP_CLEAR, X_MARGIN + 0.1, GAP_BOT - STRIP_CLEAR),
    # at J1's end, up to J1's GND row -- its via lands here (mkescape.py) -- still in the
    # gap, 0.25 clear of pad 3's edge, and past J1's pads, not under them
    rect(234.9, GAP_TOP + 0.25, 237.2, GAP_TOP + STRIP_CLEAR + 0.1),
    # under the test-pad row on the corridor's top edge, for TP4's via: 1mm clear of pad 3
    rect(240.0, GAP_TOP + 1.0, 270.0, GAP_TOP + STRIP_CLEAR + 0.1),
]


def main():
    b = pcbnew.LoadBoard(proj.P.pcb)
    gnd = b.FindNet("/GND")
    for z in [z for z in b.Zones() if z.GetLayer() == pcbnew.In2_Cu and z.GetNetname() == "/GND"]:
        b.Remove(z)
    for pts in AREAS:
        z = pcbnew.ZONE(b)
        z.SetLayer(pcbnew.In2_Cu)
        z.SetNet(gnd)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            sx, sy = pg.face_sheet((x, y))
            ol.Append(mm(sx), mm(sy))
        z.SetFillMode(pcbnew.ZONE_FILL_MODE_HATCH_PATTERN)
        z.SetHatchThickness(mm(0.25))
        z.SetHatchGap(mm(0.75))
        z.SetMinThickness(mm(0.2))
        z.SetLocalClearance(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"{len(AREAS)} GND zones on In2.Cu, hatched. File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
