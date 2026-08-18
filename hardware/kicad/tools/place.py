#!/usr/bin/env python3
"""Set footprint positions in vuulgaris.kicad_pcb.

Panel-facing parts are DERIVED, not chosen: their coordinates come from
hardware/placement-panel-facing.txt, which is generated from the faceplate
artwork.  KiCad's board format is Y-down and native millimetres, the same
convention as that file, so the only transform is the origin shift:

    pcb_mm = panel_mm - (6.995, 7.000)     # board sits inside the 6mm walls
    sheet  = BOARD_ORIGIN + pcb_mm

Everything else is free placement, grouped so signals stay short.
"""
import re, sys

PCB = "/Users/dylanhackett/V1/hardware/kicad/vuulgaris.kicad_pcb"
ORG = (100.0, 50.0)          # board top-left on the sheet
OX, OY = 6.995, 7.000        # panel -> pcb
W, H = 284.3, 125.0

PANEL = {
    # GENERATED coordinates, from:
    #   python3 mockups/generate-faceplate.py --placement
    "ENC1": (25.143, 22.35),
    "ENC2": (25.143, 39.98),
    "ENC3": (47.143, 22.35),
    "ENC4": (47.143, 39.98),
    "ENC5": (69.143, 22.35),
    "ENC6": (69.143, 39.98),
    "ENC7": (91.143, 22.35),
    "ENC8": (91.143, 39.98),
    "ENC9": (119.143, 22.35),
    "ENC10": (119.143, 39.98),
    "ENC0": (33.571, 76.525),
    "SW4": (24.046, 100.725),
    "SW5": (43.096, 100.725),
    "SW6": (24.046, 119.775),
    "SW7": (43.096, 119.775),
    # LPG analog controls, 2x2x2 group
    "RV1": (163.143, 22.35),
    "RV2": (141.143, 22.35),
    "RV3": (141.143, 39.98),
    "RV4": (163.143, 39.98),
    # DS1 origin is the 9-pin HEADER; panel file gives the module TOP-LEFT,
    # header on that left edge, vertically centred on the 43mm body.
    "DS1": (211.143, 11.55 + 21.5),
}
FREE = {
    "U1": (120, 90),                       # Daisy, centre of the board
    "U3": (45, 52), "U4": (90, 52),        # expanders under the encoder rows
    "C26": (45, 61), "C27": (90, 61),      # their decoupling
    "R20": (122, 48), "R21": (128, 48),    # I2C pull-ups, on the bus
    "J1": (172, 84),                       # SD hard against the Daisy
    "FB1": (196, 53), "U5": (207, 53), "C24": (196, 59),
    "C20": (217, 53), "C21": (223, 59),    # OLED rail, at the OLED
    # MSP430 rail: moved again to clear the MX cluster. Still far from the OLED
    # rail, which is what §5.5 actually requires.
    "FB2": (55, 95), "U6": (67, 95), "C25": (55, 102),
    "C22": (78, 95), "C23": (78, 102),
    "J2": (60, 117), "J3": (90, 117), "J4": (120, 117),
    "J5": (150, 117), "J6": (180, 117),    # INVENTED - jacks are not in the panel file
}

# Footprints whose origin is NOT the part's physical centre. Placing by origin
# would offset the part on the panel -- the same trap the OLED footprint sets.
# For a panel-facing part the thing that must line up with the faceplate hole is
# the SHAFT AXIS, which for these parts is not the footprint origin. Values are
# the local coordinate of that axis, read off the board geometry:
#   RK09L  bushing circle (0, -4.83) r 3.24, body y[-9.91, 1.52]
#   RK09D  bushing circle (0, -3.56) r 2.50, body y[-9.14, 2.03]
#   MX     centre post    (0.63, 3.81), also a 4.2mm pad
ORIGIN_OFFSET = {
    "SW4": (0.63, 3.81), "SW5": (0.63, 3.81),   # Cherry MX: body centre is the
    "SW6": (0.63, 3.81), "SW7": (0.63, 3.81),   # centre post at local (0.63, 3.81)
    "RV1": (0.0, -4.83),                        # dual-gang, deeper body
    "RV2": (0.0, -3.56), "RV3": (0.0, -3.56), "RV4": (0.0, -3.56),
}


def target(ref):
    if ref in PANEL:
        px, py = PANEL[ref]
        ox, oy = ORIGIN_OFFSET.get(ref, (0.0, 0.0))
        return px - OX - ox, py - OY - oy
    return FREE[ref]

src = open(PCB).read()
out, pos, i = [], 0, 0
placed, missing = {}, []

# walk footprint blocks, rewriting the first (at ...) of each
while True:
    m = re.compile(r'\(footprint "').search(src, pos)
    if not m:
        out.append(src[pos:]); break
    start = m.start()
    d, j = 0, start
    while j < len(src):
        if src[j] == '(': d += 1
        elif src[j] == ')':
            d -= 1
            if d == 0: break
        j += 1
    block = src[start:j + 1]
    r = re.search(r'\(property "Reference" "([^"]+)"', block) or \
        re.search(r'\(fp_text reference "([^"]+)"', block)
    ref = r.group(1) if r else None
    if ref and (ref in PANEL or ref in FREE):
        x, y = target(ref)
        sx, sy = round(ORG[0] + x, 3), round(ORG[1] + y, 3)
        block = re.sub(r'\(at [-\d.]+ [-\d.]+( [-\d.]+)?\)',
                       lambda mm: f'(at {sx} {sy}{mm.group(1) or ""})', block, count=1)
        placed[ref] = (x, y)
    elif ref:
        missing.append(ref)
    out.append(src[pos:start]); out.append(block)
    pos = j + 1

open(PCB, "w").write("".join(out))

print(f"placed  : {len(placed)}")
print(f"skipped : {missing or 'none'}")
oob = [r for r, (x, y) in placed.items() if not (0 <= x <= W and 0 <= y <= H)]
print(f"outside board outline: {oob or 'none'}")

# ---------------------------------------------------------------- overlap
# Read the board back and bound each footprint by its own geometry. No ERC or
# DRC catches a part sitting on top of another at this stage, and the panel
# coordinates are derived rather than chosen -- so this is the only check that
# a derived position is physically possible.
src = open(PCB).read()
box, pos = {}, 0
while True:
    m = re.compile(r'\(footprint "').search(src, pos)
    if not m: break
    st = m.start(); d, j = 0, st
    while j < len(src):
        if src[j] == '(': d += 1
        elif src[j] == ')':
            d -= 1
            if d == 0: break
        j += 1
    block, pos = src[st:j + 1], j + 1
    r = re.search(r'\(property "Reference" "([^"]+)"', block) or \
        re.search(r'\(fp_text reference "([^"]+)"', block)
    a = re.search(r'\(at ([-\d.]+) ([-\d.]+)', block)
    if not (r and a): continue
    ax, ay = float(a.group(1)), float(a.group(2))
    pts = []
    for p in re.finditer(r'\(pad "[^"]*" \w+ \w+ \(at ([-\d.]+) ([-\d.]+)[^)]*\) \(size ([\d.]+) ([\d.]+)\)', block):
        px, py, sw, sh = map(float, p.groups())
        pts += [(px - sw / 2, py - sh / 2), (px + sw / 2, py + sh / 2)]
    for l in re.finditer(r'\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)', block):
        g = list(map(float, l.groups())); pts += [(g[0], g[1]), (g[2], g[3])]
    if not pts: continue
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    box[r.group(1)] = (ax + min(xs), ay + min(ys), ax + max(xs), ay + max(ys))

hits = []
refs = sorted(box)
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        ax0, ay0, ax1, ay1 = box[a]; bx0, by0, bx1, by1 = box[b]
        ox = min(ax1, bx1) - max(ax0, bx0)
        oy = min(ay1, by1) - max(ay0, by0)
        if ox > 0 and oy > 0:
            hits.append((round(ox * oy, 2), a, b, round(ox, 2), round(oy, 2)))
print(f"bounded : {len(box)}")
if hits:
    print(f"OVERLAPS: {len(hits)}")
    for area, a, b, ox, oy in sorted(hits, reverse=True):
        print(f"   {a:5} x {b:5}  {ox} x {oy} mm  ({area} mm2)")
else:
    print("overlaps: none")
