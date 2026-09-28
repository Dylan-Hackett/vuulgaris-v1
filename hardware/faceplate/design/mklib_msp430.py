#!/usr/bin/env python3
"""Write the MSP430FR2675TPT symbol and its PT0048A footprint into the shared
library (hardware/kicad/lib). Re-runnable: it replaces its own symbol block and
footprint file, and touches nothing else.

    python3 hardware/faceplate/design/mklib_msp430.py

The pinout is transcribed TWICE from TI SLASEO5D (Sept 2021), from two different
presentations, and the script refuses to write unless they agree pin for pin:

  FIG_7_1    Figure 7-1, "48-Pin PT Package (Top View)": the full pin names
  TABLE_7_1  Table 7-1, "Pin Attributes", PT column: pin number -> the reset
             default signal, the one marked (RD) (or the power/system name)

Both were read from the datasheet rendered as images, not from its text layer
and not from any KiCad or LCSC symbol (CLAUDE.md, "check the source").

The footprint is TI's own land pattern, PT0048A (drawing 4215159/B, datasheet
p. 119, "EXAMPLE BOARD LAYOUT"): 48 pads 1.6 x 0.3, 0.5 pitch, opposite rows
8.2 apart centre to centre, R0.05 corners, non-solder-mask-defined with 0.05
mask clearance. Body 7 x 7 (6.8-7.2), lead tips 9 x 9 (8.8-9.2), 1.6 max high
(p. 118, "PACKAGE OUTLINE").
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(os.path.dirname(HERE)), "kicad", "lib")
SYM_LIB = os.path.join(LIB, "vuulgaris.kicad_sym")
FP_NAME = "LQFP-48_7x7mm_P0.5mm_PT0048A"
FP_FILE = os.path.join(LIB, "vuulgaris.pretty", FP_NAME + ".kicad_mod")
SYM_NAME = "MSP430FR2675TPT"

FIG_7_1 = {
    1: "DVCC", 2: "~{RST}/NMI/SBWTDIO", 3: "TEST/SBWTCK",
    4: "P1.4/UCA0TXD/UCA0SIMO/TA1.2/TCK/A4/VREF+",
    5: "P1.5/UCA0RXD/UCA0SOMI/TA1.1/TMS/A5",
    6: "P1.6/UCA0CLK/TA1CLK/TDI/TCLK/A6",
    7: "P1.7/UCA0STE/SMCLK/TDO/A7",
    8: "P4.3/UCB1SOMI/UCB1SCL/TB0.5/A8",
    9: "P4.4/UCB1SIMO/UCB1SDA/TB0.6/A9",
    10: "P5.3/UCB1CLK/TA3.0/A10",
    11: "P5.4/UCB1STE/TA3CLK/A11",
    12: "P1.0/UCB0STE/TA0CLK/A0/Veref+",
    13: "P1.1/UCB0CLK/TA0.1/COMP0.0/A1",
    14: "P1.2/UCB0SIMO/UCB0SDA/TA0.2/A2/Veref-",
    15: "P1.3/UCB0SOMI/UCB0SCL/MCLK/A3",
    16: "P2.2/SYNC/ACLK/COMP0.1",
    17: "P4.5/UCB0SOMI/UCB0SCL/TA3.2",
    18: "P4.6/UCB0SIMO/UCB0SDA/TA3.1",
    19: "P5.5/UCB0CLK/TA2CLK",
    20: "P5.6/UCB0STE/TA2.0",
    21: "P5.7/TA2.1/COMP0.2",
    22: "P6.0/TA2.2/COMP0.3",
    23: "P3.0/TA2.2/CAP0.0",
    24: "P3.3/TA2.1/CAP0.1",
    25: "P2.3/TA2.0/CAP0.2",
    26: "P3.4/TA2CLK/COMP0OUT/CAP0.3",
    27: "P3.1/UCA1STE/CAP1.0",
    28: "P2.4/UCA1CLK/CAP1.1",
    29: "P2.5/UCA1RXD/UCA1SOMI/CAP1.2",
    30: "P2.6/UCA1TXD/UCA1SIMO/CAP1.3",
    31: "VREG",
    32: "P3.7/TA3.2/CAP2.0",
    33: "P4.0/TA3.1/CAP2.1",
    34: "P4.1/TA3.0/CAP2.2",
    35: "P4.2/TA3CLK/CAP2.3",
    36: "P2.7/UCB1STE/CAP3.0",
    37: "P3.5/UCB1CLK/TB0TRG/CAP3.1",
    38: "P3.2/UCB1SIMO/UCB1SDA/CAP3.2",
    39: "P3.6/UCB1SOMI/UCB1SCL/CAP3.3",
    40: "P6.1/TB0CLK",
    41: "P6.2/TB0.0",
    42: "P4.7/UCA0STE/TB0.1",
    43: "P5.0/UCA0CLK/TB0.2",
    44: "P5.1/UCA0RXD/UCA0SOMI/TB0.3",
    45: "P5.2/UCA0TXD/UCA0SIMO/TB0.4",
    46: "P2.0/XOUT",
    47: "P2.1/XIN",
    48: "DVSS",
}

TABLE_7_1 = {
    1: "DVCC", 2: "RST", 3: "TEST", 4: "P1.4", 5: "P1.5", 6: "P1.6", 7: "P1.7",
    8: "P4.3", 9: "P4.4", 10: "P5.3", 11: "P5.4", 12: "P1.0", 13: "P1.1",
    14: "P1.2", 15: "P1.3", 16: "P2.2", 17: "P4.5", 18: "P4.6", 19: "P5.5",
    20: "P5.6", 21: "P5.7", 22: "P6.0", 23: "P3.0", 24: "P3.3", 25: "P2.3",
    26: "P3.4", 27: "P3.1", 28: "P2.4", 29: "P2.5", 30: "P2.6", 31: "VREG",
    32: "P3.7", 33: "P4.0", 34: "P4.1", 35: "P4.2", 36: "P2.7", 37: "P3.5",
    38: "P3.2", 39: "P3.6", 40: "P6.1", 41: "P6.2", 42: "P4.7", 43: "P5.0",
    44: "P5.1", 45: "P5.2", 46: "P2.0", 47: "P2.1", 48: "DVSS",
}

# Table 7-1's CapTIvate rows, PT column -- checked separately because the
# electrode wiring hangs on exactly these sixteen.
CAP_7_1 = {
    "CAP0.0": 23, "CAP0.1": 24, "CAP0.2": 25, "CAP0.3": 26,
    "CAP1.0": 27, "CAP1.1": 28, "CAP1.2": 29, "CAP1.3": 30,
    "CAP2.0": 32, "CAP2.1": 33, "CAP2.2": 34, "CAP2.3": 35,
    "CAP3.0": 36, "CAP3.1": 37, "CAP3.2": 38, "CAP3.3": 39,
}


def check():
    assert sorted(FIG_7_1) == list(range(1, 49)), "Figure 7-1 is not pins 1..48"
    assert sorted(TABLE_7_1) == list(range(1, 49)), "Table 7-1 is not pins 1..48"
    for n in range(1, 49):
        first = FIG_7_1[n].split("/")[0].replace("~{RST}", "RST")
        assert first == TABLE_7_1[n], f"pin {n}: Figure 7-1 {FIG_7_1[n]!r} vs Table 7-1 {TABLE_7_1[n]!r}"
    for sig, n in CAP_7_1.items():
        assert FIG_7_1[n].endswith("/" + sig), f"{sig}: Table 7-1 says pin {n}, Figure 7-1 says {FIG_7_1[n]!r}"
    names = [s for v in FIG_7_1.values() for s in v.split("/")]
    for sig in CAP_7_1:
        assert names.count(sig) == 1, f"{sig} appears {names.count(sig)} times in Figure 7-1"


# ------------------------------------------------------------------ symbol
# Functional grouping, not package order: supply and system pins, then the
# ports, on the left; the sixteen CapTIvate pins by block on the right.
# None is a one-row gap.
LEFT = [1, 48, 31, 2, 3, 47, 46, None,
        4, 5, 6, 7, 12, 13, 14, 15, None,
        16, 8, 9, 17, 18, 42, None,
        22, 40, 41]
RIGHT = [23, 24, 25, 26, None, 27, 28, 29, 30, None, 32, 33, 34, 35, None,
         36, 37, 38, 39, None,
         43, 44, 45, 10, 11, 19, 20, 21]
TYPE = {1: "power_in", 48: "power_in", 31: "passive", 2: "bidirectional", 3: "input"}
G = 2.54
X_BODY, X_PIN, PIN_LEN = 45.72, 50.8, 5.08


def symbol():
    assert sorted(p for p in LEFT + RIGHT if p) == list(range(1, 49))
    rows = max(len(LEFT), len(RIGHT))
    top = G * 14
    assert top - G * (rows - 1) >= -G * 14, "symbol taller than planned"
    y_hi, y_lo = top + G, top - G * rows
    f = "(effects (font (size 1.27 1.27)))"
    out = [f'  (symbol "{SYM_NAME}" (in_bom yes) (on_board yes)',
           f'    (property "Reference" "U" (id 0) (at {-X_BODY} {y_hi + G:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))',
           f'    (property "Value" "{SYM_NAME}" (id 1) (at {-X_BODY} {y_lo - G:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))',
           f'    (property "Footprint" "vuulgaris:{FP_NAME}" (id 2) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '    (property "Datasheet" "https://www.ti.com/lit/gpn/msp430fr2675" (id 3) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '    (property "LCSC Part" "C2052972" (id 4) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '    (property "ki_description" "MSP430FR2675 CapTIvate MCU, LQFP-48 (PT). Pins from SLASEO5D Figure 7-1, cross-checked against Table 7-1 by hardware/faceplate/design/mklib_msp430.py" (id 5) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (symbol "{SYM_NAME}_0_1"',
           f'      (rectangle (start {-X_BODY} {y_hi:.2f}) (end {X_BODY} {y_lo:.2f})',
           '        (stroke (width 0.254) (type default)) (fill (type background)))',
           '    )',
           f'    (symbol "{SYM_NAME}_1_1"']
    for side, pins, x, ang in (("L", LEFT, -X_PIN, 0), ("R", RIGHT, X_PIN, 180)):
        for i, n in enumerate(pins):
            if n is None:
                continue
            y = top - G * i
            t = TYPE.get(n, "bidirectional")
            out.append(f'      (pin {t} line (at {x:.2f} {y:.2f} {ang}) (length {PIN_LEN}) '
                       f'(name "{FIG_7_1[n]}" {f}) (number "{n}" {f}))')
    out += ['    )', '  )']
    return "\n".join(out) + "\n"


def write_symbol():
    s = open(SYM_LIB).read()
    block = symbol()
    m = re.search(r'\n  \(symbol "%s".*?\n  \)\n' % re.escape(SYM_NAME), s, re.S)
    if m:
        s = s[:m.start() + 1] + block + s[m.end():]
    else:
        end = s.rstrip().rfind(")")
        s = s[:end].rstrip("\n") + "\n" + block + ")\n"
    open(SYM_LIB, "w").write(s)


# ------------------------------------------------------------------ footprint
def pad_xy(n):
    """TI PT0048A, top view: 1-12 down the left, 13-24 left to right along the
    bottom, 25-36 up the right, 37-48 right to left along the top (Figure 7-1)."""
    k, side = (n - 1) % 12, (n - 1) // 12
    off = -2.75 + 0.5 * k
    return [(-4.1, off, 0), (off, 4.1, 90), (4.1, -off, 0), (-off, -4.1, 90)][side]


def footprint():
    L = [f'(footprint "{FP_NAME}" (version 20221018) (generator pcbnew)',
         '  (layer "F.Cu")',
         '  (descr "TI PT0048A LQFP-48 7x7mm 0.5mm pitch, land pattern from TI drawing 4215159/B '
         '(MSP430FR2675 datasheet SLASEO5D p.119): pads 1.6 x 0.3, rows 8.2 apart, R0.05, NSMD 0.05")',
         '  (tags "LQFP-48 PT0048A MSP430FR2675")',
         '  (attr smd)',
         '  (fp_text reference "REF**" (at 0 -6) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
         f'  (fp_text value "{FP_NAME}" (at 0 6) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
         '  (fp_text user "${REFERENCE}" (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    w = '(stroke (width 0.1) (type solid))'
    body = [(-2.5, -3.5), (3.5, -3.5), (3.5, 3.5), (-3.5, 3.5), (-3.5, -2.5), (-2.5, -3.5)]
    for a, b in zip(body, body[1:]):
        L.append(f'  (fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) {w} (layer "F.Fab"))')
    # silk: the body's corners only, clear of the pad rows (pads end at +-2.9)
    s, e = 3.61, 3.2
    ws = '(stroke (width 0.12) (type solid))'
    for sx in (-1, 1):
        for sy in (-1, 1):
            if sx < 0 and sy < 0:
                continue
            L.append(f'  (fp_line (start {sx*s} {sy*s}) (end {sx*e} {sy*s}) {ws} (layer "F.SilkS"))')
            L.append(f'  (fp_line (start {sx*s} {sy*s}) (end {sx*s} {sy*e}) {ws} (layer "F.SilkS"))')
    L.append(f'  (fp_line (start -3.2 -3.61) (end -3.61 -3.2) {ws} (layer "F.SilkS"))')
    L.append(f'  (fp_circle (center -4.1 -3.55) (end -3.95 -3.55) {ws} (fill solid) (layer "F.SilkS"))')
    L.append('  (fp_rect (start -5.15 -5.15) (end 5.15 5.15) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')
    for n in range(1, 49):
        x, y, rot = pad_xy(n)
        L.append(f'  (pad "{n}" smd roundrect (at {x:g} {y:g} {rot}) (size 1.6 0.3) '
                 f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1667) (solder_mask_margin 0.05))')
    L.append(')')
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    check()
    write_symbol()
    open(FP_FILE, "w").write(footprint())
    print(f"{SYM_NAME}: 48 pins, Figure 7-1 == Table 7-1 on every pin, 16 CAP pins checked")
    print(f"wrote {os.path.relpath(SYM_LIB)} ({SYM_NAME}) and {os.path.relpath(FP_FILE)}")
