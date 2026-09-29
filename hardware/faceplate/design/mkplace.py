"""Place the faceplate's parts (everything but J1 and E1-E4) on the back. ONE-SHOT.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkplace.py          # refuses once U1 is on the board's back
    $KPY hardware/faceplate/design/mkplace.py --force  # re-place, discarding hand moves

The placement settled 2026-09-28 (README, "Layout"): U1 and its sixteen networks in the
RIGHT MARGIN, not the centre, so every pad's lines run to the right end under their own pad
and nothing runs under another pad; the UART and power arrive from J1 along the gap between
pads 3 and 4. After Dylan starts routing, Pcbnew is the source of truth and this file only
records where things started.

Coordinates are PANEL mm (front view, y down from the jack edge), sheet = panel + FACE_ORG.
Every part is on B.Cu, so pin order reads mirrored from the front; U1 is turned so its CAP
pins (23-39) face UP, towards the networks, and its digital corner (46-5) faces down-right,
towards the UART's entry. The strip is panel x 277.14 (pad copper ends) to 292.29 (wall's
inner face); parts keep inside 277.6-291.3. Under it is the Daisy, ~3mm clear, and nothing
here is over 1.6mm.

After this writes the board, File -> Revert in Pcbnew before touching it.
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
mm, T = pcbnew.FromMM, pcbnew.ToMM
_, G = pg.generator()
TOPS = G["PAD_TOPS"]
PW = G["PW"]

U1_XY = (284.45, 104.0)

# ---- the networks: a 4 x 4 grid of cells, one COLUMN per CapTIvate block (CAP0..CAP3 =
# RX0..RX3), one ROW per pad (1 at the top). A cell is the line's TVS directly on top of its
# 470R, TVS pin 1 over R pin 1: electrode, clamp, resistor, pin, in that order and within
# 2mm (ADR 0004: with bare copper there is no entry point, so both sit by the MCU and what
# matters is the order and a short ground). Each column stands over its own pins (CAP0 over
# 23-26 at U1's top-left corner ... CAP3 over 36-39 at the top-right), and every column runs
# its four pin traces down its LEFT side: that order reaches 23-39 round both corners with
# no crossing. So every TVS has its ground pin on the right, and every cell is the same.
# Pitches from the silk (R0603's box is 1.47 x 2.93), not the courtyards: rows 4.0 apart,
# columns wide enough for three traces (0.15 / 0.2) beside the next column's TVS, and the
# middle channel wider again for C3 over pin 31.
# Dylan moved the grid +1.25 / -0.25 in Pcbnew (2026-09-28, widening the left channel);
# RX3's column then came back 0.73 so its TVS clear the wall (panelcheck), and columns
# 0-2 went 0.45 left again so RX3's channel holds its three traces past the TVS (1.57mm).
# Rows are 6.0 apart (5.0 until the autorouter needed room to cross each pad's RX1 and RX2
# lines between rows; 4.0 before that): that leaves a via spot in every cell, on the column line
# 2.9 above the R's centre -- between the TVS and the R above -- where the line comes up
# from L2 without entering any trace channel. Row 4 stays put: the fan-out into U1 is
# unchanged; the grid grows upward into empty margin.
COL_X = (280.30, 283.50, 288.00, 290.92)  # RX0..RX3 = CAP0..CAP3
ROW_Y = {1: 77.15, 2: 83.15, 3: 89.15, 4: 95.15}
VIA_DY = -2.9                             # the electrode's via spot, from the R's centre
TVS_DY = -2.0                             # TVS centre above its R's centre
TVS_PIN_DX = 0.35                         # X1SON-2 pads at +-0.35: pin 1 over the R


def cell(p, n):
    """pad p (1..4), RX index n (0..3) -> (R centre, TVS centre), panel mm."""
    x, y = COL_X[n], ROW_Y[p]
    return (x, y), (x + TVS_PIN_DX, y + TVS_DY)


PLACE = {
    # ref: (panel x, panel y, pad that must point, direction)  -- direction of that pad
    # from the part's centre: "up" / "down" / "left" / "right"
    "U1": (*U1_XY, "31", "up"),
    # 1uF VREG in the middle channel, over pin 31 -- left of the channel's centre, which
    # leaves RX2's three traces their 1.25mm past R43
    "C3": (285.25, 95.875, "1", "down"),
    # Under the digital corner. Pins 1-5 (DVCC, RST, TEST, TXD, RXD) run right to left
    # along U1's bottom and 46-48 (XOUT, XIN, GND) up its right side, so C2 goes straight
    # under pin 1 and the channel under pins 2-5 stays open for the lines to J1.
    # 100nF DVCC across the corner, pin 1 by U1 pin 1 (DVCC), pin 2 by pin 48 (GND).
    "C2": (288.35, 111.175, "1", "left"),
    # XT1: XIN / XOUT drop down U1's right side past C2 to Y1, stood on end against the
    # edge (XOUT takes the outside, over the wall band: copper only, nothing tall). C5 on
    # XIN and C6 on XOUT lie beside Y1's two pads (SLASEO5D Figure 10-2).
    "Y1": (290.9, 114.25, "1", "up"),      # FC-135, pin 1 XIN; courtyard 0.24 inside the wall
    "C5": (288.05, 113.4, "1", "right"),   # 22pF XIN
    "C6": (288.05, 115.9, "1", "right"),   # 22pF XOUT
    # Where 3V3 and RST arrive from J1 along the gap: bulk first, then the RST RC. RST is a
    # slow net; TI's Figure 10-4 gives the RC no distance.
    # 10uF DVCC bulk: above the corridor's mouth, not in it -- there it blocked RST, TXD
    # and RXD in turn -- 0.6 clear of U1's left pins; 3V3 reaches it from the top line
    "C1": (278.3, 106.2, "1", "down"),
    "C4": (280.725, 112.9, "1", "up"),     # 1nF C0G on RST
    "R1": (282.775, 112.85, "2", "up"),    # 47k RST pull-up
    # UART pull-ups (SLAU550 3.3.2.1: on the TCK / TMS nets, no distance given). R2 stands
    # across the corridor's 3V3 and TXD lines, which run side by side; R3 cannot -- TXD runs
    # between 3V3 and RXD -- so it sits in the margin under U1, beside RXD's pin (5).
    "R2": (262.0, 111.025, "1", "up"),     # 47k TXD: pin 1 on the 3V3 line, pin 2 on TXD
    "R3": (282.5, 110.2, "1", "left"),     # 47k RXD: pin 1 3V3, pin 2 toward pin 5
}
# Test pads in the gap between pads 3 and 4, beside J1, where TEST, RST, 3V3, GND and the
# UART all arrive anyway: one row along the corridor's top edge, so J1's lines run clear
# underneath, labelled on silk by signal (the main board's rule: the silk carries what it
# is, not TPn). The UART pull-ups lie at the end of the row.
TP_LABEL = {"TP1": "TEST", "TP2": "RST", "TP3": "3V3", "TP4": "GND", "TP5": "TX", "TP6": "RX"}
# The corridor's lines (design/mkescape.py draws them): out of J1's channel they fan out
# to these heights, 1.3 apart, and run straight to the margin. Each test pad sits ON its
# own line -- a tap, not a detour -- staggered along x so no pad reaches the next line.
# RXD keeps the height it leaves J1's channel at and the others fan away from it, so every
# neighbouring pair diverges (fanned about a common point, RXD bent up toward TXD's corner
# and came 0.197mm off it).
CORRIDOR_Y = {"P3V3_MSP430": 110.375, "MSP430_TXD": 111.675, "MSP430_RXD": 112.975,
              "MSP_RST": 114.275, "MSP_TEST": 115.575}
for ref, x, lane in (("TP3", 244.0, "P3V3_MSP430"), ("TP5", 247.6, "MSP430_TXD"),
                     ("TP6", 251.2, "MSP430_RXD"), ("TP2", 254.8, "MSP_RST"),
                     ("TP1", 258.4, "MSP_TEST")):
    PLACE[ref] = (x, CORRIDOR_Y[lane], None, None)
# SBW GND, above the lines, tracked to J1's GND via; clear of J1's courtyard (to 239.5)
PLACE["TP4"] = (240.9, 109.25, None, None)

# Silk: where each reference goes (panel mm, and whether it stands on end), placed by the
# silk's real extents so no reference lands on a body. None = off the silk, onto B.Fab.
REF_AT = {
    "C3": (285.25, 92.6, False),
    "C2": (285.55, 111.475, False),
    "Y1": (290.9, 117.45, False),
    "C5": (285.55, 113.4, False), "C6": (285.55, 115.9, False),
    "C1": (278.3, 103.6, False), "C4": (280.725, 115.7, False), "R1": (282.775, 115.65, False),
    "R2": (263.6, 111.025, False), "R3": (280.0, 110.2, False),
}
REF_AT.update({ref: None for ref in TP_LABEL})
for _p in range(1, 5):
    for _n in range(4):
        # a 470R's reference stands on end just LEFT of it, in the column's trace gap
        REF_AT[f"R{_p}{_n + 1}"] = (COL_X[_n] - 1.2, ROW_Y[_p], True)
        REF_AT[f"D{_p}{_n + 1}"] = None   # its cell names it; assembly goes by the CPL

CAP_PINS = [str(p) for p in range(23, 40) if p != 31]


def direction(fp, pad):
    c = fp.GetPosition()
    q = next(p for p in fp.Pads() if p.GetNumber() == pad).GetPosition()
    dx, dy = q.x - c.x, q.y - c.y
    if abs(dx) >= abs(dy):
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"


def put(fp, x, y, pad, want):
    sx, sy = pg.face_sheet((x, y))
    fp.SetPosition(pcbnew.VECTOR2I(mm(sx), mm(sy)))
    if not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), True)
    if pad is None:                     # one round pad: nothing to point
        fp.SetOrientationDegrees(0)
        return
    for a in (0, 90, 180, 270):
        fp.SetOrientationDegrees(a)
        if direction(fp, pad) == want:
            return
    raise SystemExit(f"{fp.GetReference()}: no rotation puts pad {pad} {want}")


def text_at(t, x, y, on_end):
    """Put a footprint text at panel (x, y), 0.8mm, reading along x or standing on end.
    The angle KiCad stores is relative to the (flipped, turned) footprint, so try each and
    keep the one whose box has the wanted shape."""
    t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    t.SetTextThickness(mm(0.12))
    sx, sy = pg.face_sheet((x, y))
    for a in (0, 90, 180, 270):
        t.SetTextAngle(pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T))
        t.SetPosition(pcbnew.VECTOR2I(mm(sx), mm(sy)))
        bb = t.GetBoundingBox()
        if (bb.GetHeight() > bb.GetWidth()) == on_end:
            return
    raise SystemExit(f"cannot turn {t.GetText()}")


def silk(fp, at):
    ref = fp.Reference()
    if at is None:
        ref.SetLayer(pcbnew.B_Fab)
        return
    ref.SetLayer(pcbnew.B_SilkS)
    text_at(ref, *at)


def main():
    b = pcbnew.LoadBoard(P.pcb)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    if fps["U1"].IsFlipped() and "--force" not in sys.argv:
        sys.exit("U1 is already on the back: this is one-shot. --force re-places and "
                 "discards any hand moves.")
    for ref, (x, y, pad, want) in PLACE.items():
        put(fps[ref], x, y, pad, want)
    # U1's CAP pins must read 23..39 left to right (block-major), or the columns are wrong
    u1 = fps["U1"]
    order = sorted(CAP_PINS, key=lambda n: next(p for p in u1.Pads() if p.GetNumber() == n)
                   .GetPosition().x)
    if order != CAP_PINS:
        sys.exit(f"U1's CAP pins read {order} left to right, not 23..39")
    for p in range(1, 5):
        for n in range(4):
            (rx, ry), (tx, ty) = cell(p, n)
            put(fps[f"R{p}{n + 1}"], rx, ry, "1", "up")
            put(fps[f"D{p}{n + 1}"], tx, ty, "1", "left")
    for ref, at in REF_AT.items():
        silk(fps[ref], at)
    for ref, label in TP_LABEL.items():
        tp = fps[ref]
        for t in [t for t in tp.GraphicalItems() if isinstance(t, pcbnew.FP_TEXT)
                  and t.GetType() == pcbnew.FP_TEXT.TEXT_is_DIVERS]:
            tp.Remove(t)
        t = pcbnew.FP_TEXT(tp)
        t.SetText(label)
        t.SetLayer(pcbnew.B_SilkS)
        t.SetMirrored(True)
        x, y = PLACE[ref][:2]
        # to its right, a touch high: clear of the next pad's circle, 1.3 lower
        text_at(t, x + 1.3 + 0.31 * len(label), y - 0.35, False)
        tp.Add(t)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(P.pcb, b)
    print("U1 CAP pins left to right: " + " ".join(order))
    print(f"placed {len(PLACE) + 32} parts. File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
