"""Draw the faceplate's panel holes on Edge.Cuts, from panelgeo.holes(). Re-runnable.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkholes.py

Every hole that panelgeo sizes (each row there says which drawing it came from) becomes an
Edge.Cuts circle at its panel centre; unsized ones are left for panelcheck to list as TODO.
Idempotent: removes every Edge.Cuts circle first (the outline is segments, so it is kept).
tools/panelcheck.py checks each hole's size and centre against the same table.

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
b = pcbnew.LoadBoard(proj.P.pcb)
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
        b.Remove(d)
n = 0
for ref, (x, y), dia, src in pg.holes():
    if dia is None:
        continue
    cx, cy = pg.face_sheet((x, y))
    c = pcbnew.PCB_SHAPE(b)
    c.SetShape(pcbnew.SHAPE_T_CIRCLE)
    c.SetLayer(pcbnew.Edge_Cuts)
    c.SetWidth(mm(0.1))
    c.SetCenter(pcbnew.VECTOR2I(mm(cx), mm(cy)))
    c.SetEnd(pcbnew.VECTOR2I(mm(cx + dia / 2.0), mm(cy)))
    b.Add(c)
    n += 1
pcbnew.SaveBoard(proj.P.pcb, b)
print(f"{n} holes drawn. File -> Revert in Pcbnew before touching it.")
