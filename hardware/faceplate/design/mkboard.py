"""Bootstrap hardware/faceplate/vuulgaris-faceplate.kicad_pcb. ONE-SHOT.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkboard.py            # refuses if the board exists

Runs under KiCad's Python (it needs pcbnew). It writes the skeleton the
verification loop starts from, and after that the board is edited like the
main board's: scripted through pcbnew (LoadBoard -> edit -> SaveBoard) or by
hand in Pcbnew. It is not a generator to re-run, and it will not overwrite.

What it puts on the board, all derived rather than typed:

  * 4 copper layers, 1.6mm, ENIG (ADR 0004), the main board's stackup.
  * The outline: the generator's panel, W x H, at FACE_ORG. Square corners for
    now; the enclosure decides the rest.
  * J1 on the back, pad centroid on the main board's J12 cutout centre carried
    into panel coordinates, turned so its pad 1 sits in the same direction
    from its centre as J12's (pin 1 at +x, odd row toward +y). Nets from
    design/netmap.json.
  * J1's five GND pads joined on B.Cu, pad to pad along their row. Same net,
    one connector -- and without it the skeleton fails DRC on unconnected
    pads. Everything else is left for layout.
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

P = proj.P
MAIN = proj.PROJECTS["main"]
STOCK_FP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
mm = pcbnew.FromMM

if os.path.exists(P.pcb) and "--force" not in sys.argv:
    sys.exit(f"{P.pcb} exists. This is a one-shot bootstrap; edit the board instead.")

HEADER = """(kicad_pcb (version 20221018) (generator pcbnew)

  (general
    (thickness 1.6)
  )

  (paper "A3")
  (title_block
    (title "Vuulgaris V1 faceplate")
    (rev "0")
  )

  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" signal)
    (2 "In2.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )

  (setup
    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0152))
      (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )
    (pad_to_mask_clearance 0)
    (aux_axis_origin %(ox)s %(oy)s)
    (grid_origin %(ox)s %(oy)s)
  )

  (net 0 "")
)
""" % {"ox": pg.FACE_ORG[0], "oy": pg.FACE_ORG[1]}

open(P.pcb, "w").write(HEADER)
b = pcbnew.LoadBoard(P.pcb)

# ---- outline: the generator's panel
_, g = pg.generator()
W, H = g["PANEL_W"], g["PANEL_H"]
r = pcbnew.PCB_SHAPE(b)
r.SetShape(pcbnew.SHAPE_T_RECT)
x0, y0 = pg.face_sheet((0.0, 0.0))
x1, y1 = pg.face_sheet((W, H))
r.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
r.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
r.SetLayer(pcbnew.Edge_Cuts)
r.SetWidth(mm(0.1))
b.Add(r)

# ---- where J1 goes: the cutout centre, and J12's pin-1 direction
mb = pcbnew.LoadBoard(MAIN.pcb)
shapes = [((pcbnew.ToMM(d.GetStart().x), pcbnew.ToMM(d.GetStart().y)),
           (pcbnew.ToMM(d.GetEnd().x), pcbnew.ToMM(d.GetEnd().y)))
          for d in mb.GetDrawings()
          if d.GetLayer() == pcbnew.Edge_Cuts
          and d.GetShape() in (pcbnew.SHAPE_T_SEGMENT, pcbnew.SHAPE_T_ARC)]
cut = pg.cutouts(shapes)
if len(cut) != 1:
    sys.exit(f"main board: expected one internal cutout, found {len(cut)}")
cx, cy = (cut[0][0] + cut[0][2]) / 2, (cut[0][1] + cut[0][3]) / 2
target = pg.face_sheet(pg.main_to_panel()((cx, cy)))

j12 = mb.FindFootprintByReference("J12")
c12 = [sum(pcbnew.ToMM(getattr(p.GetPosition(), a)) for p in j12.Pads()) / 10 for a in "xy"]
p1 = next(p for p in j12.Pads() if p.GetNumber() == "1").GetPosition()
want = ((pcbnew.ToMM(p1.x) - c12[0]) > 0, (pcbnew.ToMM(p1.y) - c12[1]) > 0)

# ---- nets
NET = json.load(open(P.netmap))
nets = {}
for n in sorted({n for pins in NET.values() for n in pins.values()}):
    ni = pcbnew.NETINFO_ITEM(b, "/" + n)
    b.Add(ni)
    nets[n] = ni

# ---- J1
fp = pcbnew.FootprintLoad(f"{STOCK_FP}/Connector_IDC.pretty", "IDC-Header_2x05_P2.54mm_Vertical_SMD")
fp.SetFPID(pcbnew.LIB_ID("Connector_IDC", "IDC-Header_2x05_P2.54mm_Vertical_SMD"))
fp.SetReference("J1")
fp.SetValue(json.load(open(P.values)).get("J1", "J1"))
b.Add(fp)
fp.SetPosition(pcbnew.VECTOR2I(mm(target[0]), mm(target[1])))
fp.Flip(fp.GetPosition(), False)


def pad1_dir():
    c = [sum(pcbnew.ToMM(getattr(p.GetPosition(), a)) for p in fp.Pads()) / len(fp.Pads()) for a in "xy"]
    q = next(p for p in fp.Pads() if p.GetNumber() == "1").GetPosition()
    return ((pcbnew.ToMM(q.x) - c[0]) > 1.0, (pcbnew.ToMM(q.y) - c[1]) > 1.0), c


for rot in (0, 90, 180, 270):
    fp.SetOrientationDegrees(rot)
    got, c = pad1_dir()
    # pad 1 must be at the +x END (x offset the larger) and on the +y row
    q = next(p for p in fp.Pads() if p.GetNumber() == "1").GetPosition()
    along_x = abs(pcbnew.ToMM(q.x) - c[0]) > abs(pcbnew.ToMM(q.y) - c[1])
    if got == want and along_x:
        break
else:
    sys.exit("no rotation puts J1's pad 1 where J12's is")
# rotating about the origin moves the pad centroid if the origin is off-centre
got, c = pad1_dir()
fp.Move(pcbnew.VECTOR2I(mm(target[0] - c[0]), mm(target[1] - c[1])))

for pad in fp.Pads():
    n = NET["J1"].get(pad.GetNumber())
    if n:
        pad.SetNet(nets[n])

# ---- J1's GND pads joined along their row, pad centre to pad centre. One long
# track through all five satisfies KiCad, which counts a track crossing a pad,
# but boardcheck.py only counts track ENDPOINTS, so it is four segments.
gnd = sorted((p for p in fp.Pads() if NET["J1"].get(p.GetNumber()) == "GND"),
             key=lambda p: p.GetPosition().x)
assert len({p.GetPosition().y for p in gnd}) == 1, "GND pads not in one row"
glen = 0.0
for a_, z_ in zip(gnd, gnd[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(a_.GetPosition())
    t.SetEnd(z_.GetPosition())
    t.SetWidth(mm(0.5))
    t.SetLayer(pcbnew.B_Cu)
    t.SetNet(nets["GND"])
    b.Add(t)
    glen += pcbnew.ToMM(t.GetLength())

pcbnew.SaveBoard(P.pcb, b)
got, c = pad1_dir()
print(f"outline  {W:.3f} x {H:.3f} at sheet ({x0}, {y0})")
print(f"J1       rot {fp.GetOrientationDegrees():.0f} on {fp.GetLayerName()}, pad centroid "
      f"sheet ({c[0]:.3f}, {c[1]:.3f}) = panel ({c[0]-pg.FACE_ORG[0]:.3f}, {c[1]-pg.FACE_ORG[1]:.3f})")
print(f"nets     {len(nets)}; GND {len(gnd) - 1} segments, {glen:.2f}mm")
