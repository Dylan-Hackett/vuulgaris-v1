#!/usr/bin/env python3
"""Set footprint positions in vuulgaris.kicad_pcb.

There are two kinds of position here and they are governed differently.

PANEL parts are DERIVED, not chosen: their coordinates come from
hardware/placement-panel-facing.txt, which is generated from the faceplate
artwork.  A knob has to come through its hole, so these are always enforced and
a move made in Pcbnew is reverted (and reported).  KiCad's board format is
Y-down and native millimetres, the same convention as that file, so the only
transform is the origin shift:

    pcb_mm = panel_mm - (6.995, 7.000)     # board sits inside the 6mm walls
    sheet  = BOARD_ORIGIN + pcb_mm

FREE parts are CHOSEN, and the board wins.  Move them in Pcbnew, save, and this
script keeps them there -- it re-reads their positions every run and records
them in tools/free-placement.json so the layout is reviewable in a diff.  A part
that is not yet in that file is new (just arrived via F8) and gets seeded once
from FREE_SEED below.

    python3 tools/place.py            # normal: enforce panel, keep free
    python3 tools/place.py --check    # report only, write NOTHING
    python3 tools/place.py --reset    # throw away free moves, back to FREE_SEED

--check is safe to run at any time, including with KiCad open, and is the thing
to run before plotting fab files.
"""
import re, sys, json, os, math

KI = "/Users/dylanhackett/V1/hardware/kicad"
PCB = f"{KI}/vuulgaris.kicad_pcb"
FREE_JSON = f"{KI}/tools/free-placement.json"
ORG = (100.0, 50.0)          # board top-left on the sheet
OX, OY = 6.995, 7.000        # panel -> pcb
W, H = 284.3, 125.0
RESET = "--reset" in sys.argv
CHECK = "--check" in sys.argv

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

# Starting positions ONLY. Once a part is in free-placement.json the board wins
# and these are ignored -- see the module docstring.
FREE_SEED = {
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
    "J2": (60, 117), "J3": (90, 117), "J4": (120, 117), "J5": (150, 117),
    # power input stage, left-edge pocket, clear of the touch electrodes (x54+)
    "J11": (261.0, 6.2),
    "D1": (272.0, 16.0),
    "L1": (265.0, 16.0),
    "C29": (260.0, 16.0),
    "C30": (256.0, 16.0),
    "D3": (251.0, 16.0),
    "C28": (246.0, 28.0),
    "U7": (262.0, 30.0),
    "L2": (250.0, 38.0),
    "C31": (245.0, 38.0),
    "C32": (241.0, 38.0),
    "D2": (256.0, 38.0),
    "R22": (264.0, 38.0),
    "R23": (267.0, 38.0),
    "R24": (270.0, 38.0),
    # 1/4" audio, rotated 270 so the barrel exits the TOP edge. y = 24.55 puts
    # the bushing at the board edge; the body runs 34mm inward on the back side,
    # under the OLED, which is on standoffs on the front.
    "J7": (170.50, 24.55), "J8": (188.50, 24.55),
    "J9": (213.00, 24.55), "J10": (231.00, 24.55),
}

# For a panel-facing part the thing that must line up with the faceplate hole is
# the SHAFT AXIS, which for these parts is not the footprint origin. Values are
# the local coordinate of that axis, read off the board geometry:
#   RK09L  bushing circle (0, -4.83) r 3.24, body y[-9.91, 1.52]
#   RK09D  bushing circle (0, -3.56) r 2.50, body y[-9.14, 2.03]
#   MX     centre post    (0.63, 3.81), also a 4.2mm pad
#   EC12   silk body centre AND both mounting lugs agree on (0, -3.75)
#   EC11L  bushing circle  (0, -0.20) r 4.00
ORIGIN_OFFSET = {
    "SW4": (0.63, 3.81), "SW5": (0.63, 3.81),   # Cherry MX: body centre is the
    "SW6": (0.63, 3.81), "SW7": (0.63, 3.81),   # centre post at local (0.63, 3.81)
    "RV1": (0.0, -4.83),                        # dual-gang, deeper body
    "RV2": (0.0, -3.56), "RV3": (0.0, -3.56), "RV4": (0.0, -3.56),
    "ENC0": (0.0, -0.20),
}
for _i in range(1, 11):                         # ENC1-ENC10 are all EC12
    ORIGIN_OFFSET[f"ENC{_i}"] = (0.0, -3.75)


def fp_blocks(text):
    """Yield (ref, block, start, end) for every footprint in a board file."""
    pos = 0
    while True:
        m = re.compile(r'\(footprint "').search(text, pos)
        if not m:
            return
        start = m.start()
        d, j = 0, start
        while j < len(text):
            if text[j] == '(':
                d += 1
            elif text[j] == ')':
                d -= 1
                if d == 0:
                    break
            j += 1
        block = text[start:j + 1]
        pos = j + 1
        r = re.search(r'\(property "Reference" "([^"]+)"', block) or \
            re.search(r'\(fp_text reference "([^"]+)"', block)
        yield (r.group(1) if r else None), block, start, j + 1


src = open(PCB).read()

# ------------------------------------------------------------ current board
current, angle = {}, {}
for ref, block, _, _ in fp_blocks(src):
    a = re.search(r'\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)', block)
    if ref and a:
        current[ref] = (float(a.group(1)) - ORG[0], float(a.group(2)) - ORG[1])
        angle[ref] = float(a.group(3)) if a.group(3) else 0.0

# ORIGIN_OFFSET is expressed in the footprint's own frame, so it is only valid
# while that frame is unrotated. A rotated panel part would need the offset
# rotated with it, and the sign convention there is worth confirming against
# KiCad rather than assuming -- so refuse to place it instead of guessing.
spun = [r for r in current if r in PANEL and angle[r] and ORIGIN_OFFSET.get(r, (0, 0)) != (0, 0)]

saved = {}
if os.path.exists(FREE_JSON) and not RESET:
    saved = json.load(open(FREE_JSON))
first_run = not saved

# ------------------------------------------------------------ decide targets
targets, seeded, kept, reverted, unknown = {}, [], [], [], []
for ref in current:
    if ref in PANEL:
        px, py = PANEL[ref]
        ox, oy = ORIGIN_OFFSET.get(ref, (0.0, 0.0))
        t = (px - OX - ox, py - OY - oy)
        targets[ref] = t
        cx, cy = current[ref]
        if abs(cx - t[0]) > 0.05 or abs(cy - t[1]) > 0.05:
            reverted.append((ref, round(cx - t[0], 2), round(cy - t[1], 2)))
    elif ref in saved:
        targets[ref] = current[ref]      # board wins
        kept.append(ref)
    elif first_run:
        targets[ref] = current[ref]      # adopt the layout that already exists
        kept.append(ref)
    elif ref in FREE_SEED:
        targets[ref] = FREE_SEED[ref]
        seeded.append(ref)
    else:
        targets[ref] = current[ref]
        unknown.append(ref)

if spun:
    head = "ROTATED PANEL PART" if CHECK else "REFUSING TO PLACE -- rotated panel part"
    print(f"{head}, and the shaft offset is frame-relative:")
    for r in spun:
        print(f"   {r:6} rotated {angle[r]}deg, shaft offset {ORIGIN_OFFSET[r]}")
    print("   rotate it back to 0, or tell me and I will verify the rotated math.\n")
    if not CHECK:
        sys.exit(1)      # --check reports everything; a write must not guess

# ------------------------------------------------------------ write
out, pos = [], 0
for ref, block, start, end in fp_blocks(src):
    if ref in targets:
        x, y = targets[ref]
        sx, sy = round(ORG[0] + x, 3), round(ORG[1] + y, 3)
        block = re.sub(r'\(at [-\d.]+ [-\d.]+( [-\d.]+)?\)',
                       lambda mm: f'(at {sx} {sy}{mm.group(1) or ""})', block, count=1)
    out.append(src[pos:start])
    out.append(block)
    pos = end
out.append(src[pos:])

if not CHECK:
    open(PCB, "w").write("".join(out))
    json.dump({r: [round(v[0], 3), round(v[1], 3)]
               for r, v in sorted(targets.items()) if r not in PANEL},
              open(FREE_JSON, "w"), indent=2)

print("MODE: --check, nothing written\n" if CHECK else "")
print(f"panel (derived) : {sum(1 for r in targets if r in PANEL)}")
print(f"free  (yours)   : {len(kept)}" + ("   [adopted from the board]" if first_run else ""))
if seeded:
    print(f"free  (seeded)  : {len(seeded)}  {seeded}")
if unknown:
    print(f"NEW, unplaced   : {unknown}   <- add to FREE_SEED or move them yourself")
if reverted:
    verb = "OFF THE FACEPLATE" if CHECK else "reverted to the faceplate"
    print(f"{verb} ({len(reverted)}):")
    for ref, dx, dy in reverted:
        print(f"   {ref:6} moved by ({dx:+}, {dy:+}) mm from its hole")
    if CHECK:
        print("   run without --check to snap them back")
else:
    print("panel parts on their holes: all 20")
oob = [r for r, (x, y) in targets.items() if not (0 <= x <= W and 0 <= y <= H)]
print(f"outside board outline (origins): {oob or 'none'}")

# ------------------------------------------------- shaft offset, independently
# ORIGIN_OFFSET is the one input nothing else can check: comparing board
# positions back to the panel file uses the same table, so a wrong value passes
# both ways. Here the shaft is inferred from the footprint's OWN geometry --
# the bushing circle, the silkscreen body centre, the largest pad -- and any
# disagreement is reported. This is what caught ENC1-ENC10 sitting 3.75mm high.
src = open(PCB).read()
print("\nshaft offset vs footprint geometry:")
bad_shaft = 0
for ref, block, _, _ in fp_blocks(src):
    if ref not in PANEL or ref == "DS1":
        continue
    cands = []
    big = []
    for c in re.finditer(r'\(fp_circle \(center ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)', block):
        cx, cy, ex, ey = map(float, c.groups())
        rad = ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5
        if rad > 1.5:                      # below this they are pad drill markers
            big.append((rad, cx, cy))
    if big:
        rad, cx, cy = max(big)
        cands.append((f"bushing r{rad:.2f}", cx, cy))
    silk = []
    for l in re.finditer(r'\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)((?:.|\n){0,200}?)\)\n', block):
        if '"F.SilkS"' in l.group(5):
            g = list(map(float, l.groups()[:4]))
            silk += [(g[0], g[1]), (g[2], g[3])]
    if silk:
        xs, ys = [p[0] for p in silk], [p[1] for p in silk]
        cands.append(("silk body", (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2))
    pads = [(float(m.group(3)) * float(m.group(4)), float(m.group(1)), float(m.group(2)))
            for m in re.finditer(r'\(pad "[^"]*" \w+ \w+ \(at ([-\d.]+) ([-\d.]+)[^)]*\) \(size ([\d.]+) ([\d.]+)\)', block)]
    if pads:
        area, px_, py_ = max(pads)
        if area > 10:
            cands.append(("big pad", px_, py_))
    cfg = ORIGIN_OFFSET.get(ref, (0.0, 0.0))
    if not any(abs(cx - cfg[0]) < 0.5 and abs(cy - cfg[1]) < 0.5 for _, cx, cy in cands):
        bad_shaft += 1
        detail = "  ".join(f"{n}({cx:.2f},{cy:.2f})" for n, cx, cy in cands)
        print(f"   MISMATCH {ref:6} configured ({cfg[0]:.2f},{cfg[1]:.2f})   geometry: {detail}")
print(f"   {bad_shaft} mismatches")

# ------------------------------------------------- pad orientation vs library
# KiCad stores a pad's rotation ABSOLUTELY: footprint angle + the pad's own
# angle from the library. Rotating a footprint by editing its (at x y angle)
# moves the pad POSITIONS but leaves every pad SHAPE unrotated, which is silent
# and catastrophic -- it turned J1's 0.7 x 1.6mm SD contacts into 1.6mm-tall
# pads on a 1.1mm pitch and fused nine of them into one bar of copper.
# Neither ERC, DRC-by-eye, nor the overlap check above catches it, because both
# sides of the arithmetic are consistently wrong. So compare against the
# library, which is the only place the intended relative angle survives.
print("\npad orientation vs library:")
LIBDIR = f"{KI}/lib/vuulgaris.pretty"
def lib_pads(fpname):
    path = f"{LIBDIR}/{fpname}.kicad_mod"
    if not os.path.exists(path):
        return None
    txt = open(path).read()
    out = {}
    for m in re.finditer(r'\(pad\s+"?([^"\s]+)"?\s+\w+\s+(\w+)\s+\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', txt):
        num, shape, x, y, ang = m.groups()
        out[(round(float(x), 3), round(float(y), 3))] = (shape, float(ang) if ang else 0.0)
    return out

bad_ang, checked, skipped = 0, 0, []
for ref, block, _, _ in fp_blocks(src):
    if not ref:
        continue
    fpm = re.match(r'\(footprint "([^"]+)"', block)
    a = re.search(r'\(at [-\d.]+ [-\d.]+( [-\d.]+)?\)', block)
    fang = float(a.group(1)) if (a and a.group(1)) else 0.0
    Lm = re.match(r'\(footprint "[^"]*" \(layer "([^"]+)"', block)
    onback = (Lm.group(1) if Lm else "F.Cu") != "F.Cu"
    lp = lib_pads(fpm.group(1).split(":")[-1]) if fpm else None
    if lp is None:
        skipped.append(ref); continue
    for m in re.finditer(r'\(pad "([^"]*)" \w+ (\w+) \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', block):
        num, shape, x, y, ang = m.groups()
        if shape == "circle":
            continue                      # rotation is meaningless on a circle
        cur = float(ang) if ang else 0.0
        want_rel = lp.get((round(float(x), 3), round(float(y), 3)))
        if want_rel is None:
            continue
        # Mirroring negates the pad's relative angle, so a back-side footprint
        # is fp_angle MINUS the library angle, not plus.
        rel = -want_rel[1] if onback else want_rel[1]
        want = (fang + rel) % 360.0
        checked += 1
        if abs((cur - want + 180) % 360 - 180) > 0.01:
            bad_ang += 1
            print(f"   {ref:5} pad {num:>4} {shape:9} angle {cur:6.1f}, expected {want:6.1f} "
                  f"(footprint {fang:+.0f} {'-' if onback else '+'} library "
                  f"{abs(want_rel[1]):.0f}{', BACK' if onback else ''}) -- SHAPE NOT ROTATED")
print(f"   {checked} non-circular pads checked, {bad_ang} wrong"
      + (f"; {len(skipped)} footprints not in the local library" if skipped else ""))

# ---------------------------------------------------------------- overlap
# Bound each footprint by its own geometry. No ERC or DRC catches a part sitting
# on another at this stage, and it already caught U5 landing on ENC6.
# A hole goes through the board, so PADS conflict no matter which face a part is
# mounted on. Bodies only conflict with parts on the SAME face -- the 1/4" jacks
# sit on the back, under an OLED that stands off the front, and that is fine.
box, padbox, side = {}, {}, {}
for ref, block, _, _ in fp_blocks(src):
    a = re.search(r'\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)', block)
    if not (ref and a):
        continue
    L = re.match(r'\(footprint "[^"]*" \(layer "([^"]+)"', block)
    side[ref] = L.group(1) if L else "F.Cu"
    ax, ay = float(a.group(1)), float(a.group(2))
    ang = float(a.group(3)) if a.group(3) else 0.0
    # KiCad's footprint rotation, confirmed against a rendered board:
    #   x' = lx*cos + ly*sin ;  y' = -lx*sin + ly*cos
    # Bounding a rotated part with its unrotated extents silently swaps its
    # width and height, which is wrong by 28mm on the Daisy alone.
    # A BACK-side footprint is mirrored: KiCad negates the local Y before
    # rotating, so back = front(lx, -ly). Verified against Gerber flash positions
    # for J7 and J11. Without this the box is mirrored in X for every part on
    # B.Cu, and since the same arithmetic placed those parts, the check agreed
    # with the mistake -- J11's pad sat 0.40mm over the outline and passed.
    mir = -1.0 if (Lm.group(1) if Lm else "F.Cu") != "F.Cu" else 1.0
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def place(lx, ly):
        ly = ly * mir
        return ax + lx * ca + ly * sa, ay - lx * sa + ly * ca
    pts, ppts, prects = [], [], []
    for p in re.finditer(r'\(pad "[^"]*" \w+ \w+ \(at ([-\d.]+) ([-\d.]+)[^)]*\) \(size ([\d.]+) ([\d.]+)\)', block):
        px, py, sw, sh = map(float, p.groups())
        corners = [place(cx_, cy_) for cx_ in (px - sw / 2, px + sw / 2)
                                   for cy_ in (py - sh / 2, py + sh / 2)]
        ppts += corners
        xs_, ys_ = [c[0] for c in corners], [c[1] for c in corners]
        prects.append((min(xs_), min(ys_), max(xs_), max(ys_)))
    pts += ppts
    for l in re.finditer(r'\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)', block):
        g = list(map(float, l.groups()))
        pts += [place(g[0], g[1]), place(g[2], g[3])]
    if pts:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        box[ref] = (min(xs), min(ys), max(xs), max(ys))
    if prects:
        padbox[ref] = prects        # individual pads, NOT their bounding box:
                                    # DS1's pads sit only at its edges, so a box
                                    # would falsely span the whole OLED module

def ov(A, B):
    ax0, ay0, ax1, ay1 = A
    bx0, by0, bx1, by1 = B
    dx = min(ax1, bx1) - max(ax0, bx0)
    dy = min(ay1, by1) - max(ay0, by0)
    return (dx, dy) if dx > 0 and dy > 0 else None

# A footprint's ORIGIN can sit inside the outline while its BODY hangs off the
# edge -- that is how J11 ended up 3.5mm over the right edge and passed. Bound by
# geometry, not by origin.
# These deliberately overhang: their barrels pass through the enclosure wall,
# which sits 1mm beyond the board edge and is 6mm thick.
EDGE_OK = {"J2", "J3", "J4", "J5", "J7", "J8", "J9", "J10", "J11"}
edge = []
for ref, (x0, y0, x1, y1) in box.items():
    if ref in EDGE_OK:
        continue
    # box{} is in SHEET coordinates; the outline is board coordinates
    x0, y0, x1, y1 = x0 - ORG[0], y0 - ORG[1], x1 - ORG[0], y1 - ORG[1]
    over = max(0 - x0, 0 - y0, x1 - W, y1 - H)
    if over > 0.01:
        edge.append((ref, round(over, 2)))
if edge:
    print(f"BODY OVER THE BOARD EDGE ({len(edge)}):")
    for ref, o in sorted(edge, key=lambda t: -t[1]):
        print(f"   {ref:5} by {o} mm")
else:
    print("bodies inside the outline: all")

padedge = []
for ref, rects in padbox.items():
    for (x0, y0, x1, y1) in rects:
        x0, y0, x1, y1 = x0 - ORG[0], y0 - ORG[1], x1 - ORG[0], y1 - ORG[1]
        over = max(0 - x0, 0 - y0, x1 - W, y1 - H)
        if over > 0.005:
            padedge.append((ref, round(over, 2)))
            break
if padedge:
    print(f"PADS OVER THE BOARD EDGE ({len(padedge)}) -- these get milled through:")
    for ref, o in sorted(padedge, key=lambda t: -t[1]):
        print(f"   {ref:5} by {o} mm")
else:
    print("pads inside the outline: all")

hard, soft = [], []
refs = sorted(box)
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        if a in padbox and b in padbox:
            worst = None
            for ra in padbox[a]:
                for rb in padbox[b]:
                    h = ov(ra, rb)
                    if h and (worst is None or h[0] * h[1] > worst[0] * worst[1]):
                        worst = h
            if worst:                               # holes clash through the board
                hard.append((a, b, round(worst[0], 2), round(worst[1], 2)))
                continue
        if side.get(a) == side.get(b):
            sft = ov(box[a], box[b])
            if sft:
                soft.append((a, b, round(sft[0], 2), round(sft[1], 2), side.get(a)))
if hard:
    print(f"\nPAD OVERLAPS ({len(hard)}) -- holes clash regardless of mounting face:")
    for a, b, dx, dy in hard:
        print(f"   {a:5} x {b:5}  {dx} x {dy} mm")
else:
    print("pad overlaps: none")
if soft:
    print(f"body overlaps, SAME face ({len(soft)}):")
    for a, b, dx, dy, ly in soft:
        print(f"   {a:5} x {b:5}  {dx} x {dy} mm  both on {ly}")
else:
    print("body overlaps (same face): none")
cross = [(a, b) for a in refs for b in refs if a < b
         and side.get(a) != side.get(b) and ov(box[a], box[b])]
if cross:
    print(f"body overlaps across faces ({len(cross)}) -- OK if clearance allows:")
    for a, b in cross:
        print(f"   {a:5} ({side[a]}) under/over {b:5} ({side[b]})")
