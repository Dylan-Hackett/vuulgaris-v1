"""The front face (ADR 0013): exposed ENIG on a grounded copper face, every printed mark in
black soldermask on it, the right-hand numerals in silk. Re-runnable. Deterministic -- the
generator owns the layout (face(), scale_marks(), panel_art()); this builds it.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkface.py

Run last, after mkroute.py: the gold clears every via, so the vias come first.

  gold    One GND zone on F.Cu, FACE_GOLD, solid: the whole outline less each pad's frame,
          its corners filleted with the mask's (generator mask_block()). Its copper stops
          UNDER 0.1 short of the frame, so the mask overlaps the copper's edge and no bare
          laminate shows. 0.3 from every cut (the board's copper-to-edge
          rule) and from every other net's via. It runs on under the via patch, where it
          screens the fan-in lines from a hand resting there, and it is grounded there: the
          margin's GND vias (the TVS grounds among them) join it. Island removal is "always",
          so if they ever did not, it would fill to nothing rather than float.
  mask    F.Mask openings = the gold's fill, UNDER in, less the mask block (the frames and
          the via patch as one filleted outline, generator mask_block()), less a DOT over
          every via outside the pads and the patch, less every mask stroke -- so the art is
          where the mask stays -- less any sliver of gold narrower than 2 x SLIVER. A board
          polygon cannot hold holes, so the openings are fractured into plain outlines.
  silk    The right-hand numerals, white on the via patch.

Each part is its own locked group -- FACE_MASK, FACE_SILK -- and the zone is named
FACE_GOLD; the script removes all three and rebuilds them, and touches nothing else.
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
DOT = CLEAR + UNDER    # a via's mask dot, beyond its copper: 0.4, past JLC's 0.35 for plugging
GROUPS = ("FACE_MASK", "FACE_SILK")
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
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.F_Cu)
    z.SetNet(gnd)
    z.SetZoneName("FACE_GOLD")
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((-1, -1), (W + 1, -1), (W + 1, H + 1), (-1, H + 1)):   # clipped by the fill
        ol.Append(*P(x, y))
    R = gen.CFG["mask_fillet_mm"]
    for x0, y0, x1, y1 in fc["frames"]:          # each frame, UNDER in, filleted to match
        h = ol.NewHole()
        for x, y in gen.round_rect(x0 + UNDER, y0 + UNDER, x1 - UNDER, y1 - UNDER, R - UNDER, 2.0):
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

    def poly(pts):
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in pts:
            ch.Append(*P(x, y))
        ch.SetClosed(True)
        return ch
    covers = pcbnew.SHAPE_POLY_SET()
    covers.AddOutline(poly(gen.mask_block(dict(gen.CFG), G, 2.0)))
    inside = lambda r, x, y: r[0] <= x <= r[2] and r[1] <= y <= r[3]
    n_dots = 0
    for v in b.GetTracks():
        if not isinstance(v, pcbnew.PCB_VIA):
            continue
        vx, vy = (pcbnew.ToMM(c) - o for c, o in zip((v.GetPosition().x, v.GetPosition().y), pg.FACE_ORG))
        if any(inside(r, vx, vy) for r in fc["frames"] + [fc["patch"]]):
            continue
        rd = pcbnew.ToMM(v.GetWidth()) / 2 + DOT
        covers.AddOutline(poly([(vx + rd * math.cos(k * math.pi / 16), vy + rd * math.sin(k * math.pi / 16))
                                for k in range(32)]))
        n_dots += 1
    covers.Simplify(pcbnew.SHAPE_POLY_SET.PM_FAST)
    op.BooleanSubtract(covers, pcbnew.SHAPE_POLY_SET.PM_STRICTLY_SIMPLE)
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

    # ---- the silk: what prints on the via patch
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
    for g in (mask, silk):
        g.SetLocked(True)
    z.SetLocked(True)
    pcbnew.SaveBoard(proj.P.pcb, b)
    area = sum(op.Outline(i).Area() for i in range(op.OutlineCount())) / 1e12
    print(f"face: gold {fill.OutlineCount()} piece(s); {n_dots} via dots; {op.OutlineCount()} mask openings, "
          f"{area:.0f} mm2 of gold showing, {sum(s['on'] == 'mask' for s in ink)} strokes of "
          f"mask ink; {n_silk} silk strokes (replaced {len(items)} items). "
          f"File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
