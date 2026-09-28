"""Draw the faceplate's whole Edge.Cuts layer from its sources. Re-runnable.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkholes.py

  * The outline: the generator's panel, PANEL_W x PANEL_H at FACE_ORG, its corners
    filleted to panel_corner_r_mm (2026-09-28; the enclosure's outer corners match it).
  * The panel holes: every hole panelgeo sizes becomes a circle at its panel centre (each
    row there says which drawing it came from); unsized ones are left for panelcheck to
    list as TODO.
  * The panel screws: M3 clearance holes from panelgeo.screws() (generator).
  * The OLED window: a rounded rectangle from panelgeo.oled_window() (the generator
    derives it from the module drawing and the stack-up).

Idempotent: removes every Edge.Cuts item first. tools/panelcheck.py checks the outline,
its corners, each hole and the window against the same sources.

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
gen, G = pg.generator()

# Collect everything to remove before removing any of it: in KiCad 7's bindings
# b.Drawings() stops being iterable once an item has been removed.
for d in [d for d in list(b.GetDrawings()) if d.GetLayer() == pcbnew.Edge_Cuts]:
    b.Remove(d)


def shape(kind):
    d = pcbnew.PCB_SHAPE(b)
    d.SetShape(kind)
    d.SetLayer(pcbnew.Edge_Cuts)
    d.SetWidth(mm(0.1))
    b.Add(d)
    return d


P = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))


def rounded_rect(x0, y0, x1, y1, r):
    """Four lines and four quarter arcs, panel mm."""
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


# ---- the outline
rounded_rect(0.0, 0.0, G["PANEL_W"], G["PANEL_H"], gen.CFG["panel_corner_r_mm"])

# ---- the panel holes
n = 0
for ref, (x, y), dia, src in pg.holes():
    if dia is None:
        continue
    c = shape(pcbnew.SHAPE_T_CIRCLE)
    c.SetCenter(P(x, y))
    c.SetEnd(P(x + dia / 2.0, y))
    n += 1

# ---- the panel screws
sc, sd = pg.screws()
for x, y in sc:
    c = shape(pcbnew.SHAPE_T_CIRCLE)
    c.SetCenter(P(x, y))
    c.SetEnd(P(x + sd / 2.0, y))

# ---- the OLED window
x0, y0, x1, y1, r = pg.oled_window()
rounded_rect(x0, y0, x1, y1, r)

pcbnew.SaveBoard(proj.P.pcb, b)
print(f"outline ({G['PANEL_W']:.3f} x {G['PANEL_H']:.3f}, r {gen.CFG['panel_corner_r_mm']:g}), "
      f"{n} holes, {len(sc)} screws and the OLED window ({x1 - x0:.2f} x {y1 - y0:.2f}) drawn. "
      f"File -> Revert in Pcbnew before touching it.")
