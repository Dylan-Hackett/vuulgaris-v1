"""The panel art on F.SilkS: rules, dividers, their semicircles, the Attic numerals.
Re-runnable. Deterministic -- the strokes are the generator's panel_art(), the SVG's own,
less what the fab cannot print (tools/panelgeo.py panel_silk()).

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkart.py

The scrub scale is design/mkscale.py's, a group of its own. The SVG's knob circles, button
outlines, switch and OLED outlines and screw heads are drawings of parts, not art, and are
not printed.

What the silk loses against the SVG, and why (panel_silk()):
  * the rules through the knob rows break at every knob hole -- the knob covers the gap;
  * the pad divider breaks at each pad: nothing prints on bare copper, so it shows in the
    gaps between the pads, and the dome's feet stop short of pad 1;
  * the divider rule stops short of the board edge.
All at SILK_TO_CUT (0.3) from a cut and SILK_TO_MASK (0.2) from a mask opening, clear of
the stroke's round cap. The art's own ends are drawn half a width short so KiCad's round
caps end where the SVG's butt ends do. Numerals are never clipped: if one would be, this
stops.

Everything goes in one locked group, PANEL_ART: the script removes it and redraws it, and
touches nothing else. tools/panelcheck.py checks the result against panel_silk() and for
clearance to every via.

After this writes the board, File -> Revert in Pcbnew before touching it.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FACE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(FACE), "kicad", "tools"))
sys.argv[1:1] = ["--project", "faceplate"]
import proj            # noqa: E402
import panelgeo as pg  # noqa: E402
import pcbnew          # noqa: E402

GROUP = "PANEL_ART"
mm = pcbnew.FromMM


def main():
    strokes, clipped = pg.panel_silk()
    bad = [k for k in clipped if "numeral" in k]
    if bad:
        sys.exit(f"mkart: {', '.join(bad)} would lose ink to a hole, the edge or a pad -- "
                 f"move them in the generator, do not print half a numeral")
    b = pcbnew.LoadBoard(proj.P.pcb)
    n_old = 0
    for grp in [grp for grp in b.Groups() if grp.GetName() == GROUP]:
        items = list(grp.GetItems())
        for it in items:
            grp.RemoveItem(it)
            b.Remove(it)
        n_old += len(items)
        b.Remove(grp)
    grp = pcbnew.PCB_GROUP(b)
    grp.SetName(GROUP)
    b.Add(grp)
    P = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))
    for s in strokes:
        d = pcbnew.PCB_SHAPE(b)
        if "seg" in s:
            x1, y1, x2, y2 = s["seg"]
            d.SetShape(pcbnew.SHAPE_T_SEGMENT)
            d.SetStart(P(x1, y1))
            d.SetEnd(P(x2, y2))
        else:
            cx, cy, r, a0, a1 = s["arc"]
            at = lambda a: P(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
            d.SetShape(pcbnew.SHAPE_T_ARC)
            d.SetArcGeometry(at(a0), at((a0 + a1) / 2), at(a1))
        d.SetLayer(pcbnew.F_SilkS)
        d.SetWidth(mm(s["w"]))
        b.Add(d)
        grp.AddItem(d)
    grp.SetLocked(True)
    pcbnew.SaveBoard(proj.P.pcb, b)
    lost = ", ".join(f"{k} {v:.1f}mm" for k, v in sorted(clipped.items()))
    print(f"panel art: {len(strokes)} strokes on F.SilkS (replaced {n_old}); clipped for the "
          f"fab: {lost or 'nothing'}. File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
