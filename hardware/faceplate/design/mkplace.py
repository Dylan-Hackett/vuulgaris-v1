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

# ---- the R block: two interleaved rows right above the CAP pins, C3 in a slot over pin 31.
# Pins 23-39 read left to right across U1's top (block-major: CAP0 = RX0 of pads 1-4, then
# CAP1, VREG, CAP2, CAP3), so R x follows pin order and the fan-out never crosses. Same-row
# pitch 1.44 leaves 0.58mm between pads: room for the other row's trace at 0.15/0.2.
STEP, ROW_U, ROW_L = 0.72, 94.1, 96.7
GROUP_W = 7 * STEP + 0.864
SLOT = 1.35 + 0.4                                  # C0805 across, plus clearance each side
X0 = U1_XY[0] - (2 * GROUP_W + SLOT) / 2 + 0.432   # first R's centre


def r_xy(i):
    """i-th CAP pin in left-to-right order (0..15) -> R centre."""
    g, j = divmod(i, 8)
    x = X0 + g * (GROUP_W + SLOT) + j * STEP
    return (x, ROW_L if j % 2 == 0 else ROW_U)


# ---- TVS rows beside where each pad's lines come in (TI: the clamp near the entry, its
# ground short). Pads 1, 2 and 4 have their own band; pad 3's band holds U1, so its row
# sits just above the R block. Left to right RX0..RX3, the same order as the R block.
TVS_ROW_Y = {1: TOPS[0] + PW / 2, 2: TOPS[1] + PW / 2, 3: 91.8, 4: 120.5}
TVS_X = (279.3, 282.9, 286.5, 290.1)

PLACE = {
    # ref: (panel x, panel y, pad that must point, direction)  -- direction of that pad
    # from the part's centre: "up" / "down" / "left" / "right"
    "U1": (*U1_XY, "31", "up"),
    "C3": (U1_XY[0], (ROW_U + ROW_L) / 2, "1", "down"),   # 1uF VREG: pin 1 to pin 31
    # Under the digital corner. Pins 1-5 (DVCC, RST, TEST, TXD, RXD) run right to left
    # along U1's bottom and 46-48 (XOUT, XIN, GND) up its right side, so C2 goes straight
    # under pin 1 and the channel under pins 2-5 stays open for the lines to J1.
    "C2": (287.2, 110.6, "1", "up"),       # 100nF DVCC, under pin 1
    # XT1: XIN / XOUT drop down U1's right side to Y1, stood on end against the edge (XOUT
    # can take the outside, over the wall band: copper only, nothing tall). C5 on XIN
    # beside Y1's top pad, C6 on XOUT beside its bottom pad (SLASEO5D Figure 10-2).
    "Y1": (290.5, 111.8, "1", "up"),       # FC-135, pin 1 XIN
    "C5": (288.75, 110.55, "1", "up"),     # 22pF XIN
    "C6": (288.75, 113.05, "1", "down"),   # 22pF XOUT
    # Where 3V3 and RST arrive from J1 along the gap: bulk first, then the RST RC. RST is a
    # slow net; TI's Figure 10-4 gives the RC no distance.
    "C1": (278.3, 111.5, "1", "up"),       # 10uF DVCC bulk
    "C4": (280.1, 111.5, "1", "up"),       # 1nF C0G on RST
    "R1": (281.4, 111.5, "2", "up"),       # 47k RST pull-up
    # UART pull-ups (SLAU550 3.3.2.1: on the TCK / TMS nets, no distance given) beside J1,
    # where 3V3, TXD and RXD all come off the connector.
    "R2": (250.8, 111.1, "1", "left"),     # 47k TXD
    "R3": (250.8, 113.8, "1", "left"),     # 47k RXD
}
# Test pads in the gap between pads 3 and 4, beside J1, where TEST, RST, 3V3, GND and the
# UART all arrive anyway: two rows of three, clear of both pads' copper by 0.6mm.
for k, ref in enumerate(("TP1", "TP2", "TP3", "TP4", "TP5", "TP6")):
    PLACE[ref] = (242.0 + (k % 3) * 2.6, 111.1 + (k // 3) * 2.7, None, None)

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


def main():
    b = pcbnew.LoadBoard(P.pcb)
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    if fps["U1"].IsFlipped() and "--force" not in sys.argv:
        sys.exit("U1 is already on the back: this is one-shot. --force re-places and "
                 "discards any hand moves.")
    for ref, (x, y, pad, want) in PLACE.items():
        put(fps[ref], x, y, pad, want)
    # U1's CAP pins, left to right as the board has them, set the R order
    u1 = fps["U1"]
    order = sorted(CAP_PINS, key=lambda n: next(p for p in u1.Pads() if p.GetNumber() == n)
                   .GetPosition().x)
    nm = json.load(open(P.netmap))
    cap_to_r = {net: ref for ref, pins in nm.items() if ref.startswith("R") and len(ref) == 3
                for pin, net in pins.items() if pin == "2"}
    pin_net = nm["U1"]
    for i, pin in enumerate(order):
        r = cap_to_r[pin_net[pin]]
        put(fps[r], *r_xy(i), "1", "up")
        p, n = int(r[1]), int(r[2])
        put(fps[f"D{p}{n}"], TVS_X[n - 1], TVS_ROW_Y[p], "1", "left")
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(P.pcb, b)
    print("U1 CAP pins left to right: " + " ".join(order))
    print(f"placed {len(PLACE) + 32} parts. File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
