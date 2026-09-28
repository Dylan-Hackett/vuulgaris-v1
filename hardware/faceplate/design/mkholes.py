"""Draw the faceplate's panel holes and the OLED window on Edge.Cuts. Re-runnable.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkholes.py

Every hole that panelgeo sizes (each row there says which drawing it came from) becomes an
Edge.Cuts circle at its panel centre; unsized ones are left for panelcheck to list as TODO.
The OLED window is a rounded rectangle from panelgeo.oled_window() (the generator derives
it from the module drawing and the stack-up). Idempotent: removes every Edge.Cuts circle,
and every Edge.Cuts line or arc that does not touch the board outline, first.
tools/panelcheck.py checks each hole and the window against the same sources.

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
ob = b.GetBoardEdgesBoundingBox()
edge = (pcbnew.ToMM(ob.GetLeft()), pcbnew.ToMM(ob.GetTop()),
        pcbnew.ToMM(ob.GetRight()), pcbnew.ToMM(ob.GetBottom()))


def inner(d):
    """an Edge.Cuts item that is not part of the outline: nowhere near its edges"""
    q = d.GetBoundingBox()
    x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (q.GetLeft(), q.GetTop(), q.GetRight(), q.GetBottom()))
    return x0 > edge[0] + 0.5 and y0 > edge[1] + 0.5 and x1 < edge[2] - 0.5 and y1 < edge[3] - 0.5


for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts and (d.GetShape() == pcbnew.SHAPE_T_CIRCLE or inner(d)):
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


def shape(kind):
    d = pcbnew.PCB_SHAPE(b)
    d.SetShape(kind)
    d.SetLayer(pcbnew.Edge_Cuts)
    d.SetWidth(mm(0.1))
    b.Add(d)
    return d


P = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))
x0, y0, x1, y1, r = pg.oled_window()
for (ax, ay), (bx, by) in (((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)),
                           ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))):
    s = shape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(ax, ay))
    s.SetEnd(P(bx, by))
h = r * 2 ** -0.5
for (cx, cy), (mx, my), start, end in (
        ((x0 + r, y0 + r), (-1, -1), (x0, y0 + r), (x0 + r, y0)),
        ((x1 - r, y0 + r), (1, -1), (x1 - r, y0), (x1, y0 + r)),
        ((x1 - r, y1 - r), (1, 1), (x1, y1 - r), (x1 - r, y1)),
        ((x0 + r, y1 - r), (-1, 1), (x0 + r, y1), (x0, y1 - r))):
    a = shape(pcbnew.SHAPE_T_ARC)
    a.SetArcGeometry(P(*start), P(cx + mx * h, cy + my * h), P(*end))
pcbnew.SaveBoard(proj.P.pcb, b)
print(f"{n} holes and the OLED window ({x1 - x0:.2f} x {y1 - y0:.2f}) drawn. "
      f"File -> Revert in Pcbnew before touching it.")
