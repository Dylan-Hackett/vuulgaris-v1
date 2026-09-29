"""The printed scrub scale on F.SilkS: under each pad, its ticks and crosses. Re-runnable.
Deterministic -- the strokes are the generator's scale_marks(), the SVG's own.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkscale.py

This is the usable scrub region, marked (ADR 0003, "Endpoint trim"). The copper runs past
the printed scale -- the generator's scale_inset_mm, 6mm at each end -- so a finger's
centroid never has to reach a mark it cannot, and the scale's first and last ticks are the
sample's start and end. 13 marks, 17mm apart, crosses on 1/4, 1/2 and 3/4 of the scale.

The SVG strokes have butt ends; KiCad's are round, so each segment is drawn half its width
short at both ends and the ink is the SVG's to the hundredth. The generator keeps the ink
0.25 clear of the pads' F.Mask openings, which fab would clip silk from.

Everything goes in one locked group, SCRUB_SCALE: the script removes it and redraws it,
and touches nothing else. tools/panelcheck.py checks the result against the generator.

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

GROUP = "SCRUB_SCALE"
mm = pcbnew.FromMM


def main():
    gen, g = pg.generator()
    marks = gen.scale_marks(dict(gen.CFG), g)
    b = pcbnew.LoadBoard(proj.P.pcb)
    old = [grp for grp in b.Groups() if grp.GetName() == GROUP]
    n_old = 0
    for grp in old:
        items = list(grp.GetItems())
        for it in items:
            grp.RemoveItem(it)
            b.Remove(it)
        n_old += len(items)
        b.Remove(grp)
    grp = pcbnew.PCB_GROUP(b)
    grp.SetName(GROUP)
    b.Add(grp)
    sheet = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))
    for _, x1, y1, x2, y2, w in marks:
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(mm(w))
        s.SetStart(sheet(x1 + ux * w / 2, y1 + uy * w / 2))
        s.SetEnd(sheet(x2 - ux * w / 2, y2 - uy * w / 2))
        b.Add(s)
        grp.AddItem(s)
    grp.SetLocked(True)
    pcbnew.SaveBoard(proj.P.pcb, b)
    print(f"scrub scale: {len(marks)} strokes on F.SilkS, {g['SCALE_L']:.0f}mm, "
          f"{gen.CFG['scale_inset_mm']:g}mm inside each copper end (replaced {n_old}). "
          f"File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
