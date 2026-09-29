"""The front face (ADR 0013): exposed ENIG on a grounded copper face, every printed mark in
black soldermask on it, the right-hand numerals in silk. Re-runnable. Deterministic -- the
generator owns the layout (face(), scale_marks(), panel_art()); this builds it.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkface.py

Run last, after mkroute.py: the gold clears every via, so the vias come first.

  gold    One GND zone on F.Cu, FACE_GOLD, solid: the whole outline less each pad's frame
          and the masked right panel. Its copper stops UNDER 0.1 short of the frame and the
          panel, so the mask overlaps the copper's edge and no bare laminate shows. 0.3 from
          every cut (the board's copper-to-edge rule) and from every other net's via, which
          the mask then covers as a dot.
  ground  STITCH vias: the gold's only way to GND. The one place it lies over the L3 plane
          with room on B.Cu is the corridor between pads 3 and 4, between the TXD and RXD
          lanes (mkescape.py); a scan along that line takes the first free spot past each
          STITCH_X. Open, like every via (ADR 0013).
  mask    F.Mask openings = the gold's fill, UNDER in, less every mask stroke -- so the art is
          where the mask stays -- less any sliver of gold narrower than 2 x SLIVER. A board
          polygon cannot hold holes, so the openings are fractured into plain outlines.
  silk    The right-hand numerals, white on the masked panel.

Each part is its own locked group -- FACE_MASK, FACE_SILK, FACE_STITCH -- and the zone is
named FACE_GOLD; the script removes all four and rebuilds them, and touches nothing else.
tools/panelcheck.py checks the result against the generator.

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

mm = pcbnew.FromMM
UNDER = 0.1            # gold copper runs this far under the mask at each of its edges
EDGE = 0.3             # copper to any cut: the board's rule (.kicad_pro), JLC wants 0.2
CLEAR = 0.3            # the gold to another net
SLIVER = 0.05          # openings narrower than 2 x this close up
STITCH_Y = 112.325     # between the corridor's TXD (111.675) and RXD (112.975) lanes
STITCH_X = (242.0, 252.0, 262.0, 270.0)
STITCH_D, STITCH_DRILL = 0.6, 0.3
GROUPS = ("FACE_MASK", "FACE_SILK", "FACE_STITCH")
ARC_STEP = 5.0         # degrees per point on an arc stroke's outline


def stroke_outline(s):
    """a stroke's ink as a closed point list, panel mm: a band with round ends"""
    w2 = s["w"] / 2
    cap = lambda cx, cy, a0: [(cx + w2 * math.cos(a0 + math.pi * i / 12),
                               cy + w2 * math.sin(a0 + math.pi * i / 12)) for i in range(13)]
    if "seg" in s:
        x1, y1, x2, y2 = s["seg"]
        a = math.atan2(y2 - y1, x2 - x1)
        return cap(x2, y2, a - math.pi / 2) + cap(x1, y1, a + math.pi / 2)
    cx, cy, r, a0, a1 = s["arc"]
    n = max(2, int(math.ceil((a1 - a0) / ARC_STEP)))
    at = lambda rr, t: (cx + rr * math.cos(math.radians(t)), cy + rr * math.sin(math.radians(t)))
    outer = [at(r + w2, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    inner = [at(r - w2, a1 - (a1 - a0) * i / n) for i in range(n + 1)]
    ex, ey = at(r, a1)
    sx, sy = at(r, a0)
    return (outer + cap(ex, ey, math.radians(a1)) + inner +
            cap(sx, sy, math.radians(a0) + math.pi))


def main():
    gen, G = pg.generator()
    fc = pg.face()
    ink = pg.panel_ink()
    b = pcbnew.LoadBoard(proj.P.pcb)
    b.GetDesignSettings().m_CopperEdgeClearance = mm(EDGE)
    gnd = b.FindNet("/GND")
    P = lambda x, y: pcbnew.VECTOR2I(*(mm(v) for v in pg.face_sheet((x, y))))

    # ---- clear the last build: collect everything first (KiCad 7's bindings)
    groups = [g for g in b.Groups() if g.GetName() in GROUPS]
    items = [(g, it) for g in groups for it in list(g.GetItems())]
    old_zones = [z for z in b.Zones() if z.GetZoneName() == "FACE_GOLD"]

    # ---- the gold: made before anything is removed (a ZONE made after a removal hands
    # back an opaque Outline(); mkzones.py)
    W, H = G["PANEL_W"], G["PANEL_H"]
    px, py = fc["panel"][0], fc["panel"][1]
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.F_Cu)
    z.SetNet(gnd)
    z.SetZoneName("FACE_GOLD")
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((-1, -1), (W + 1, -1), (W + 1, py + UNDER), (px + UNDER, py + UNDER),
                 (px + UNDER, H + 1), (-1, H + 1)):       # the fill clips it to the outline
        ol.Append(*P(x, y))
    for x0, y0, x1, y1 in fc["frames"]:
        h = ol.NewHole()
        for x, y in ((x0 + UNDER, y0 + UNDER), (x1 - UNDER, y0 + UNDER),
                     (x1 - UNDER, y1 - UNDER), (x0 + UNDER, y1 - UNDER)):
            ol.Append(*P(x, y), 0, h)
    z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
    z.SetMinThickness(mm(0.25))
    z.SetLocalClearance(mm(CLEAR))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)   # no floating copper
    b.Add(z)
    for g, it in items:
        g.RemoveItem(it)
        b.Remove(it)
    for g in groups:
        b.Remove(g)
    for oz in old_zones:
        b.Remove(oz)

    # ---- ground it: stitch vias in the corridor, each at the first free spot
    stitch = pcbnew.PCB_GROUP(b)
    stitch.SetName("FACE_STITCH")
    b.Add(stitch)
    others = [t for t in b.GetTracks() if t.GetNetname() != "/GND"] + \
             [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() != "/GND"]
    placed = []
    for x0 in STITCH_X:
        x = x0
        while x < x0 + 6.0:
            v = pcbnew.PCB_VIA(b)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetPosition(P(x, STITCH_Y))
            v.SetWidth(mm(STITCH_D))
            v.SetDrill(mm(STITCH_DRILL))
            v.SetNet(gnd)
            vs = v.GetEffectiveShape()
            hit = any(o.GetEffectiveShape(ly).Collide(vs, mm(0.2))
                      for o in others for ly in (pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu)
                      if o.IsOnLayer(ly))
            if not hit:
                b.Add(v)
                stitch.AddItem(v)
                placed.append(x)
                break
            x += 0.25
    if len(placed) < 2:
        sys.exit(f"mkface: only {len(placed)} stitch vias found room -- the gold needs a ground")

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    fill = z.GetFilledPolysList(pcbnew.F_Cu)
    if fill.OutlineCount() == 0:
        sys.exit("mkface: the gold filled to nothing -- is it grounded?")

    # ---- the mask: openings are the gold, less the ink
    op = fill.CloneDropTriangulation()
    # A zone's fill comes back fractured: each hole joined to the outline by a zero-width
    # cut. Deflated as it is, every cut opens into a gap -- a line of mask from each hole to
    # the edge. A union first turns the cuts back into holes.
    op.Simplify(pcbnew.SHAPE_POLY_SET.PM_STRICTLY_SIMPLE)
    op.Deflate(mm(UNDER), 32)
    marks = pcbnew.SHAPE_POLY_SET()
    for s in ink:
        if s["on"] != "mask":
            continue
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in stroke_outline(s):
            ch.Append(*P(x, y))
        ch.SetClosed(True)
        marks.AddOutline(ch)
    marks.Simplify(pcbnew.SHAPE_POLY_SET.PM_FAST)
    op.BooleanSubtract(marks, pcbnew.SHAPE_POLY_SET.PM_STRICTLY_SIMPLE)
    op.Deflate(mm(SLIVER), 16)
    op.Inflate(mm(SLIVER), 16)
    op.Fracture(pcbnew.SHAPE_POLY_SET.PM_STRICTLY_SIMPLE)
    mask = pcbnew.PCB_GROUP(b)
    mask.SetName("FACE_MASK")
    b.Add(mask)
    for i in range(op.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(op.Outline(i))
        d = pcbnew.PCB_SHAPE(b)
        d.SetShape(pcbnew.SHAPE_T_POLY)
        d.SetPolyShape(one)
        d.SetFilled(True)
        d.SetWidth(0)
        d.SetLayer(pcbnew.F_Mask)
        b.Add(d)
        mask.AddItem(d)

    # ---- the silk: what prints on the masked panel
    silk = pcbnew.PCB_GROUP(b)
    silk.SetName("FACE_SILK")
    b.Add(silk)
    n_silk = 0
    for s in ink:
        if s["on"] != "silk":
            continue
        d = pcbnew.PCB_SHAPE(b)
        d.SetShape(pcbnew.SHAPE_T_SEGMENT)
        x1, y1, x2, y2 = s["seg"]
        d.SetStart(P(x1, y1))
        d.SetEnd(P(x2, y2))
        d.SetWidth(mm(s["w"]))
        d.SetLayer(pcbnew.F_SilkS)
        b.Add(d)
        silk.AddItem(d)
        n_silk += 1
    for g in (stitch, mask, silk):
        g.SetLocked(True)
    z.SetLocked(True)
    pcbnew.SaveBoard(proj.P.pcb, b)
    area = sum(op.Outline(i).Area() for i in range(op.OutlineCount())) / 1e12
    print(f"face: gold {fill.OutlineCount()} piece(s), {len(placed)} stitch vias at x "
          f"{', '.join(f'{x:.2f}' for x in placed)}; {op.OutlineCount()} mask openings, "
          f"{area:.0f} mm2 of gold showing, {sum(s['on'] == 'mask' for s in ink)} strokes of "
          f"mask ink; {n_silk} silk strokes (replaced {len(items)} items). "
          f"File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
