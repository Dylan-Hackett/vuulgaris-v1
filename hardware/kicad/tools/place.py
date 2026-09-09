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
W, H = 284.3, 116.81      # board shrunk 2026-08-26; H was 125.0
RESET = "--reset" in sys.argv
CHECK = "--check" in sys.argv

# READ from the generated placement file, NOT transcribed. This used to be a
# hardcoded copy of generate-faceplate.py's output, which meant regenerating the
# faceplate silently changed nothing here -- the two drifted apart and place.py
# went on enforcing coordinates from a panel that no longer existed. That cost a
# whole shrink cycle to notice, because every delta it reported was measured
# against the old panel.
PANEL_FILE = "/Users/dylanhackett/V1/hardware/placement-panel-facing.txt"

_BOARD_REFS = set(re.findall(r'\(fp_text reference "([^"]+)"', open(PCB).read()))

def _read_panel(path):
    out = {}
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        # X and Y must be DECIMALS. The old pattern allowed bare integers with a
        # non-greedy middle, so a description ending in a digit -- "UI button 1"
        # -- parsed as x=1, y=<the real x>, silently, and every button would
        # have been snapped to a garbage coordinate. The previous descriptions
        # only survived because their trailing digit was followed by "(".
        m = re.match(r'(\w+)\s+.*?(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*(?:#|\S.*)?$',
                     line.rstrip())
        if not m:
            continue
        ref, x, y = m.group(1), float(m.group(2)), float(m.group(3))
        if ref == "REF":
            continue
        if not (0.0 <= x <= 400.0 and 0.0 <= y <= 200.0):
            raise SystemExit(f"panel file: {ref} parsed as ({x}, {y}), outside the "
                             f"panel. The description column probably confused the "
                             f"coordinate match.")
        out[ref] = (x, y)
    # DS1's origin is the 9-pin HEADER; the panel file gives the module TOP-LEFT,
    # header on that left edge, vertically centred on the 43mm body.
    if "DS1" in out:
        out["DS1"] = (out["DS1"][0], out["DS1"][1] + 21.5)
    # SW1/SW2 are LPG panel controls. They are dropped only while they have no
    # footprint on this PCB; once they exist they are panel parts like any other
    # and must line up with their faceplate slots.
    for k in ("SW1", "SW2"):
        if k not in _BOARD_REFS:
            out.pop(k, None)
    return out

PANEL = _read_panel(PANEL_FILE)

# Starting positions ONLY. Once a part is in free-placement.json the board wins
# and these are ignored -- see the module docstring.
FREE_SEED = {
    # Daisy. No longer needs an edge -- MIDI was dropped 2026-08-25 and firmware
    # goes on by opening the box, so the micro-USB does not have to reach a wall.
    # Placed instead where the SIGNALS want it: directly under the four 1/4"
    # jacks, so the analog audio runs are ~30mm instead of ~100mm across the
    # board. Audio is the one thing here that cannot be cleaned up afterwards.
    # 37mm clear of U7, which is an encapsulated module with two-stage LC on
    # both rails, so that is enough. Rotation is now free -- nothing depends
    # on where the USB points.
    "U1": (120.0, 105.0),                  # 68 x 40, spans x[86,154] y[85,125] -- BOTTOM EDGE for USB
    # SD. Slot mouth is local +y, so the card ejects toward the bottom edge.
    # U1 is on the BACK now, same face as this, so it needs clearance in front
    # of the mouth, not merely no overlap: 15.3mm to the board edge, 12.2mm back
    # to the Daisy.
    "J1": (100.0, 75.0),   # rot -90, set by hand 2026-09-09 -- card ejects toward the edge
    "FB1": (196, 53), "U5": (207, 53), "C24": (196, 59),
    "C20": (217, 53), "C21": (223, 59),    # OLED rail, at the OLED
    # MSP430 rail: moved again to clear the MX cluster. Still far from the OLED
    # rail, which is what §5.5 actually requires.
    "FB2": (55, 95), "U6": (67, 95), "C25": (55, 102),
    "C22": (78, 95), "C23": (78, 102),
    "J2": (60, 117), "J3": (90, 117), "J4": (120, 117), "J5": (150, 117),
    # Power stage: USB-C -> DKM10E-12 -> +/-12V, down the right edge.
    #
    # Only TWO parts here are through-hole: U7 and the USB-C's shell legs. The
    # other 21 are SMD on the back, and the OLED is on the front, so the board
    # itself separates them -- they sit under the screen and nothing touches.
    # It is the through-hole pins that could not stay there.
    #
    # U7 is 25.4mm SQUARE. There is no 25.4mm slot in the band above the
    # capacitive pads (y < 57.5) that is not already the OLED, so it goes below
    # them, pushed as far right as it fits: the pads stop at x 270, so its right
    # third is outside the electrode area entirely.
    "J11": (279.2, 4.0),                     # USB-C at the top edge, right of DS1
    # input side, along the right edge under the OLED -- all SMD
    "R22": (267.0, 10.0), "R23": (267.0, 13.0),
    "C28": (272.0, 10.0), "F1": (277.0, 14.0),
    "C29": (272.0, 20.0), "C30": (278.0, 26.0), "C31": (278.0, 30.0),
    "U7":  (270.0, 62.0),                    # spans x[257.3,282.7] y[49.3,74.7]
    # raw rails, left of the module
    "C32": (247.0, 52.0), "C34": (247.0, 57.0), "L1": (247.0, 61.0),
    "C33": (247.0, 66.0), "C35": (247.0, 70.0), "L2": (247.0, 74.0),
    # filtered rails, below it, in space the Daisy vacated
    "C36": (255.0, 80.0), "C38": (255.0, 85.0),
    "R24": (262.0, 80.0), "D1": (266.0, 80.0),
    "C37": (255.0, 90.0), "C39": (255.0, 95.0),
    "R25": (262.0, 90.0), "D2": (266.0, 90.0),
    # 1/4" audio, rotated 270 so the barrel exits the TOP edge. y = 24.55 puts
    # the bushing at the board edge; the body runs 34mm inward on the back side,
    # under the OLED, which is on standoffs on the front.
    "J7": (170.50, 24.55), "J8": (188.50, 24.55),
    "J9": (213.00, 24.55), "J10": (231.00, 24.55),
    # 5xx: the SOURCE interconnect. SW2 sits at (186.6, 30.6) with the audio
    # jacks directly above it, so the DC blocking caps go in that gap -- the ext
    # pair beside their own jack, the resample pair below on the BBD side -- and
    # the two common pulldowns to the right, on the way to U1.
    # The clear band is y 38..46, x 165..193: SW1/SW2 stop at y 35.19, DS1 starts
    # at x 195.55, and the jacks' bodies stop at y 25. An earlier seed put C501
    # on SW1's through-hole pads and R501/R502 inside the OLED.
    "C501": (172.0, 39.0), "C503": (172.0, 43.0),   # L: ext, resample
    "R501": (178.0, 39.0), "R502": (178.0, 43.0),   # common pulldowns
    "C502": (190.0, 39.0), "C504": (190.0, 43.0),   # R: ext, resample
    # --- bypass caps, hugging their own chip -------------------------------
    # Moved 2026-09-08. They were 6.5-12.1mm from the power pin they decouple
    # (mean 9.3), which is far enough that the trace inductance undoes most of
    # what a 100nF is for. Now 2.1-3.1mm. Each sits beside the pad it feeds, on
    # the same face as its chip, so there is no via in the path. Positions are
    # a nearest-free-spot search around the power pad, not hand-placed, with a
    # 2.0mm pad-to-pad floor so a hot-air nozzle or an iron tip actually fits
    # beside the chip -- 1.0mm was still too tight to work in --
    # "bypass caps hug their chip" below is what keeps them honest.
    "C105": (125.859, 58.647), "C106": (132.137, 49.76),   # U102
    "C107": (57.886, 52.922), "C108": (64.157, 43.813),   # U103
    "C121": (106.249, 58.77), "C122": (109.127, 46.283),   # U106
    "C205": (125.787, 96.177), "C206": (132.065, 87.29),   # U202
    "C207": (57.886, 92.922), "C208": (64.157, 83.813),   # U203
    "C221": (107.109, 96.177), "C222": (109.055, 83.813),   # U206
    "C301": (114.606, 72.819), "C302": (127.875, 72.0),   # U301
    "C303": (137.606, 85.819), "C304": (150.875, 85.0),   # U302
    "C401": (114.606, 96.819), "C402": (127.875, 96.0),   # U401
    "C403": (137.606, 109.819), "C404": (150.275, 109.0),   # U402
    "C111": (91.778, 43.52), "C109": (80.855, 73.984),   # U101 V3205, U104 4046
    "C211": (87.266, 78.467), "C209": (80.855, 113.984),   # U201 V3205, U204 4046
    # Series protection on the two output jacks, beside J3/J2 on the top edge.
    # Below the encoder block: the top strip is full -- ENC columns at x 18.15,
    # 40.15, 62.15, 84.15 and the jacks' bodies run 12mm inward between them.
    "R503": (29.15, 45.0), "R504": (51.15, 45.0),
    "R505": (208.0, 48.0),                   # font-chip CS pullup, clear of DS1
    # The two LPG trimmers live on B.Cu, not with the rest of the LPG on F.Cu.
    # They set vactrol LED drive depth and have to be adjusted by hand; F.Cu is
    # under the faceplate, so a top-adjust part there is only reachable with the
    # panel off. Vactrols age, so re-trimming is a real event, not a one-off.
    "RT301": (120.445, 65.493), "RT401": (120.418, 100.938),
    # --- headphone monitor out, added 2026-09-08 ---------------------------
    # J6 goes on the top wall immediately right of J10, tucked under the OLED
    # on B.Cu exactly as J9/J10 already are. The driver and its parts follow it
    # onto B.Cu; the whole block sits in the gap between the 1/4" jacks and the
    # power-input cluster. RT501/RT502 are on the back for the same reason the
    # LPG trimmers are: they are set by hand and the front is under the panel.
    "J6": (240.5, 5.0),
    "U9": (243.964, 15.0),
    "RT501": (237.672, 15.828),
    "RT502": (237.554, 23.680),   # pushed 7.5mm off U9.8 so C507 gets the pocket
    "C505": (251.326, 7.446),   # turned 90 so the 0805 body clears J6
    "C506": (243.725, 21.402),
    "R509": (249.41, 17.54),
    "R510": (247.423, 4.451),
    "R511": (251.325, 6.75),
    "R512": (242.768, 27.321),
    "C507": (239.154, 19.530),   # U9 V+ bypass, 3.44mm to pin 8 -- was 15.5mm
    "C508": (248.214, 12.170),   # U9 V- bypass, 2.35mm to pin 4 -- was 15.0mm
    # Line-output attenuators. The 1/4" jacks used to sit straight on BBD_OUT at
    # Eurorack level (9.5Vpp, +12.7dBu); these drop them to +3.8dBu full scale.
    # They sit DOWNSTREAM of the C503/C505 taps, so the internal resample loop
    # and the headphone feed keep the Eurorack level they were designed around.
    # Tucked in beside their own jacks on the back, with the rest of the 5xx block.
    # EXT input preamp, under its own jacks on the back. U10 lands first and the
    # rest hangs off it: C509/C510 are pinned to the rail pins they decouple, the
    # signal parts to the U10 pin they serve.
    "U10": (178.000, 38.500),   # EXT preamp, placed first; the cluster hangs off it
    "C509": (180.630, 42.860),   # U10 V+ bypass, 2.45mm to pin 8
    "C510": (172.270, 36.550),   # U10 V- bypass, 3.05mm to pin 4
    "C511": (171.500, 44.000),   # L input DC block, 2.06mm off U10 at 0805
    "C512": (180.430, 34.100),   # R input DC block
    "R519": (173.820, 33.370),   # L input bias, 100k = the input impedance
    "R520": (183.680, 36.600),   # R input bias
    "R521": (175.320, 43.130),   # L gain-set leg, 2k2
    "R522": (183.680, 40.370),   # R gain-set leg
    "RT503": (168.820, 39.130),   # L gain trim, 1x-10.1x
    "RT504": (187.180, 37.870),   # R gain trim
    "R517": (167.700, 28.500),   # series protection off J7
    "R518": (186.700, 28.500),   # ... and J8
    "R513": (210.500, 26.000),   # J9 series, 1k3
    "R514": (207.000, 26.000),   # J9 shunt, 1k
    "R515": (225.500, 26.000),   # J10 series
    "R516": (222.000, 26.000),   # J10 shunt
    # SD pull-ups. There is very little room here -- DS1 runs to x 267.55 and U1
    # starts at y 47.27, so the only pocket near J1 is the strip above the Daisy
    # and right of the OLED.
    "R506": (272.0, 25.0), "R507": (276.0, 25.0), "R508": (280.0, 25.0),
    # Power test points, top-left corner: the one part of the board with nothing
    # near it, at an edge, and through-hole so they can be probed from EITHER
    # face -- which matters because the front is under the faceplate. Deliberately
    # at the far end from the power stage: what you want to know at bring-up is
    # what the far end of the board actually receives, not what the regulator
    # makes. 4.5mm pitch, GND in the row so probe loops stay short.
    "TP1": (4.0, 4.0), "TP2": (8.5, 4.0), "TP3": (13.0, 4.0),
    "TP4": (17.5, 4.0), "TP5": (22.0, 4.0),
    # Signal test points sit next to the node they probe, not in a row --
    # Tidied into one row along the bottom 2026-09-08 -- scattered singletons
    # wedged into gaps between parts were a mess to find and to look at. The
    # LABEL is what makes a test point findable, not proximity, so a labelled row
    # loses nothing.
    #
    # TP12/TP13 are the exception and stay beside their own 4046. They carry the
    # BBD CLOCK, and running a 100kHz square wave 100mm across the board to a
    # probe pad is a noise injector sitting next to the audio, not a debugging
    # aid. Everything else in the row is a driven, slow node that does not care.
    "TP6": (165.5, 104.0),   # BBD_DRY_L
    "TP7": (181.5, 104.0),    # BBD_DRY_R
    "TP8": (173.5, 104.0),    # BBD_SIGIN_L
    "TP9": (189.5, 104.0),    # BBD_SIGIN_R
    "TP10": (197.5, 104.0),  # LPG_LED_L
    "TP11": (205.5, 104.0),  # LPG_LED_R
    "TP12": (76.326, 60.433),   # BBD_CLK_L
    "TP13": (77.516, 106.925),  # BBD_CLK_R
    "TP14": (213.5, 104.0),   # TIME_CV
    "TP15": (221.5, 104.0),  # LPG_ENV
    # U8's decoupling. Shifted right and down 2026-09-07 when U8 went from SOT-89
    # to SOT-223 and grew into C40.
    "C40": (58.0, 113.5), "C41": (62.0, 113.5), "C42": (66.0, 113.5),
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
    # SW4-SW9 are 12x12 tactiles as of 2026-09-06 and their pads are symmetric
    # about the origin, so the button centre IS the origin -- no offset. The old
    # (0.63, 3.81) was the Cherry MX centre post and would now push every button
    # off its hole by that much.
    # All six pots are RK09L1240A12 dual-gang now, so they share one offset.
    "RV1": (0.0, -4.83), "RV5": (0.0, -4.83), "RV6": (0.0, -4.83),                        # dual-gang, deeper body
    "RV2": (0.0, -4.83), "RV3": (0.0, -4.83), "RV4": (0.0, -4.83),
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
    # count, not a literal -- "all 20" stayed on screen after SW1/SW2 made it 22
    print(f"panel parts on their holes: all {sum(1 for r in targets if r in PANEL)}")
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
padpos = {}          # ref -> {pad number: (x, y)}, for the bypass-distance check
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
    # side[ref], NOT Lm -- Lm belongs to the pad-orientation loop above. Reading
    # it here gave every part the mirror flag of whichever footprint that loop
    # happened to end on, so every box in this check was mirrored together or
    # not at all. It invented a 3.18mm RV3/RV4-vs-U1 collision and, worse, would
    # hide a real one just as silently. Third mirror bug in this file.
    # NO mirror. Proven 2026-09-09 with kicad-cli: a pad at footprint-local
    # (0,+3) plots to the SAME absolute place whether its footprint is on F.Cu or
    # B.Cu -- KiCad renders stored coordinates as-is and applies no implicit
    # mirror for the back. The flip therefore has to be BAKED INTO the stored
    # coordinates, and this line was applying a second one on top of it.
    #
    # The old comment claimed Gerber verification against J7 and J11. J7 is a
    # correctly-mirrored part and J11 is on the front, so that check compared a
    # double mirror against a single one and read the agreement as confirmation.
    # Note the pad-ANGLE check in this same file already assumed baked-in
    # mirroring (rel = -lib when onback) -- the two halves of place.py disagreed
    # with each other for months.
    mir = 1.0
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def place(lx, ly):
        ly = ly * mir
        return ax + lx * ca + ly * sa, ay - lx * sa + ly * ca
    pts, ppts, prects = [], [], []
    # The pad TYPE is captured, not skipped. Without it every pad counted as
    # through-going, so an 0805 on B.Cu "clashed" with a SOIC on F.Cu and the
    # hard-collision list filled with ten pairs that cannot touch -- which is
    # exactly how a real through-hole collision would get lost.
    for p in re.finditer(r'\(pad "[^"]*" (\w+) \w+ \(at ([-\d.]+) ([-\d.]+)[^)]*\) \(size ([\d.]+) ([\d.]+)\)', block):
        ptype = p.group(1)
        px, py, sw, sh = map(float, p.groups()[1:])
        corners = [place(cx_, cy_) for cx_ in (px - sw / 2, px + sw / 2)
                                   for cy_ in (py - sh / 2, py + sh / 2)]
        ppts += corners
        xs_, ys_ = [c[0] for c in corners], [c[1] for c in corners]
        prects.append((min(xs_), min(ys_), max(xs_), max(ys_),
                       ptype.endswith("thru_hole")))
        padpos.setdefault(ref, {})[p.group(0).split('"')[1]] = place(px, py)
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
    for (x0, y0, x1, y1, _th) in rects:
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

# --- the board has HOLES in it, and "inside the outline" does not mean "on copper"
# The faceplate-header cutout is a 24 x 12mm slot in the middle of the board. The
# outline check above only bounds the board RECTANGLE, so a part placed in the
# slot passes it -- which is how two test points ended up hanging over the hole on
# 2026-09-08, found by eye and not by this file.
#
# Cutouts are read from Edge.Cuts rather than hardcoded: any edge geometry that
# does not touch the outer boundary is an interior loop.
_edge = []
for _m in re.finditer(r'\(gr_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                      r'.{0,160}?\(layer "Edge\.Cuts"\)', src, re.S):
    _edge.append(tuple(map(float, _m.groups())))
for _m in re.finditer(r'\(gr_arc \(start ([-\d.]+) ([-\d.]+)\) \(mid ([-\d.]+) ([-\d.]+)\)'
                      r' \(end ([-\d.]+) ([-\d.]+)\).{0,160}?\(layer "Edge\.Cuts"\)', src, re.S):
    _g = list(map(float, _m.groups()))
    _edge.append((_g[0], _g[1], _g[4], _g[5]))
    _edge.append((_g[2], _g[3], _g[2], _g[3]))
_cuts = []
if _edge:
    _xs = [v for e in _edge for v in (e[0], e[2])]
    _ys = [v for e in _edge for v in (e[1], e[3])]
    _ox0, _oy0, _ox1, _oy1 = min(_xs), min(_ys), max(_xs), max(_ys)
    def _onedge(x, y, t=0.05):
        return (abs(x-_ox0) < t or abs(x-_ox1) < t or abs(y-_oy0) < t or abs(y-_oy1) < t)
    _pts = [(e[i], e[i+1]) for e in _edge for i in (0, 2)
            if not _onedge(e[i], e[i+1])]
    while _pts:                          # cluster interior points into loops
        _grp = [_pts.pop()]
        _grew = True
        while _grew:
            _grew = False
            for _q in list(_pts):
                if any(math.hypot(_q[0]-r[0], _q[1]-r[1]) < 30.0 for r in _grp):
                    _grp.append(_q); _pts.remove(_q); _grew = True
        _gx = [q[0] for q in _grp]; _gy = [q[1] for q in _grp]
        _cuts.append((min(_gx), min(_gy), max(_gx), max(_gy)))
# The outline itself is checked before anything is measured against it. A board
# whose Edge.Cuts does not enclose its own parts is not a board, and every other
# check in this file quietly becomes meaningless -- "pads inside the outline"
# passes trivially when the outline is somewhere else entirely.
#
# This exists because a mirror transform negated Y on all eight Edge.Cuts
# gr_lines and left the four gr_arcs alone, so the connector cutout kept its
# rounded corners and lost its straight edges. Nothing here noticed; Dylan did,
# by looking at the board. It then came BACK, because Pcbnew was still holding
# the pre-fix board in memory and wrote its snapshot over the repaired file on
# the next save.
_ex = [v for e in _edge for v in (e[0], e[2])]
_ey = [v for e in _edge for v in (e[1], e[3])]
if _ex:
    _bad = []
    if min(_ey) < 0 or min(_ex) < 0:
        _bad.append(f"negative coordinates (x from {min(_ex)}, y from {min(_ey)})")
    _px = [v for r in box.values() for v in (r[0], r[2])]
    _py = [v for r in box.values() for v in (r[1], r[3])]
    if _px:
        _out = sum(1 for _r, _b in box.items()
                   if _b[0] < min(_ex) - 1 or _b[2] > max(_ex) + 1
                   or _b[1] < min(_ey) - 1 or _b[3] > max(_ey) + 1)
        if _out > len(box) // 2:
            _bad.append(f"{_out} of {len(box)} footprints fall outside it")
    if _bad:
        print("\nBOARD OUTLINE IS WRONG:")
        for _l in _bad:
            print(f"   {_l}")
        print(f"   Edge.Cuts spans x {min(_ex)}..{max(_ex)}  y {min(_ey)}..{max(_ey)}")
        print("   every check below this line is measured against it -- fix it first")
    else:
        print(f"board outline: x {min(_ex)}..{max(_ex)}  y {min(_ey)}..{max(_ey)}, "
              f"{len(_cuts)} interior cutout(s)")

CUT_CLEAR = 0.30
_incut = []
for _ref in sorted(set(box) | set(padbox)):
    for _cx0, _cy0, _cx1, _cy1 in _cuts:
        _c = (_cx0 - CUT_CLEAR, _cy0 - CUT_CLEAR, _cx1 + CUT_CLEAR, _cy1 + CUT_CLEAR)
        _hit = ov(box[_ref], _c) if _ref in box else None
        _pad = any(ov(tuple(r[:4]), _c) for r in padbox.get(_ref, []))
        if _hit or _pad:
            _incut.append((_ref, "PAD" if _pad else "body",
                           round(_cx0-ORG[0], 1), round(_cy0-ORG[1], 1)))
if _cuts:
    if _incut:
        print(f"\nIN A BOARD CUTOUT ({len(_incut)}) -- there is no board there:")
        for _r, _w, _x, _y in _incut:
            print(f"   {_r:6} ({_w}) in the cutout at board ({_x}, {_y})")
    else:
        print(f"clear of all {len(_cuts)} board cutout(s)")

hard, soft = [], []
refs = sorted(box)
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        if a in padbox and b in padbox:
            worst = None
            for *ra, tha in padbox[a]:
                for *rb, thb in padbox[b]:
                    # A pad pair collides through the board only if at least one
                    # of them actually goes through it. Two SMD pads on opposite
                    # faces are separated by 1.6mm of FR4.
                    if not (tha or thb) and side.get(a) != side.get(b):
                        continue
                    h = ov(tuple(ra), tuple(rb))
                    if h and (worst is None or h[0] * h[1] > worst[0] * worst[1]):
                        worst = h
            if worst:                               # copper clashes
                hard.append((a, b, round(worst[0], 2), round(worst[1], 2)))
                continue
        if side.get(a) == side.get(b):
            sft = ov(box[a], box[b])
            if sft:
                soft.append((a, b, round(sft[0], 2), round(sft[1], 2), side.get(a)))
# --- crowding: parts need room around them, connected or not ---------------
# Overlap is not the only failure. A 0603 sitting 0.3mm off a SOIC pin passes
# every overlap check and still cannot be reworked -- you cannot get hot air or an
# iron on the chip without lifting the neighbour. Being on the same NET does not
# earn a part the right to crowd: the connection is made by copper, not proximity.
#
# JLC's floor for assembly is ~0.2mm. That is a fabrication limit, not a working
# clearance, so WARN well above it and only FAIL near it.
CROWD_WARN, CROWD_FAIL = 1.00, 0.45

def _pgap(A, B):
    dx = max(B[0] - A[2], A[0] - B[2])
    dy = max(B[1] - A[3], A[1] - B[3])
    return -1.0 if (dx < 0 and dy < 0) else math.hypot(max(dx, 0), max(dy, 0))

_crowd = []
_crefs = sorted(padbox)
for _i, _a in enumerate(_crefs):
    for _b in _crefs[_i + 1:]:
        _same = side.get(_a) == side.get(_b)
        _worst = None
        for *_ra, _tha in padbox[_a]:
            for *_rb, _thb in padbox[_b]:
                # across faces only a through-going pad can crowd anything
                if not _same and not (_tha or _thb):
                    continue
                _g = _pgap(tuple(_ra), tuple(_rb))
                if _worst is None or _g < _worst:
                    _worst = _g
        if _worst is not None and 0 <= _worst < CROWD_WARN:
            _crowd.append((round(_worst, 2), _a, _b))
_crowd.sort()
_bad = [c for c in _crowd if c[0] < CROWD_FAIL]
if _bad:
    print(f"\nPADS TOO CLOSE TO WORK WITH ({len(_bad)} pairs, under {CROWD_FAIL}mm):")
    for _g, _a, _b in _bad:
        print(f"   {_g:5.2f}mm  {_a:6} x {_b:6}")
if _crowd:
    print(f"tightest pad-to-pad clearance: {_crowd[0][0]:.2f}mm "
          f"({_crowd[0][1]} x {_crowd[0][2]}); {len(_crowd)} pairs under {CROWD_WARN}mm"
          + (f", {len(_bad)} under {CROWD_FAIL}" if _bad else ""))
    for _g, _a, _b in _crowd[:8]:
        print(f"   {_g:5.2f}mm  {_a:6} x {_b:6}")
else:
    print(f"pad-to-pad clearance: everything is at least {CROWD_WARN}mm apart")

# Chips get their own line. A 0603 crowding another 0603 is untidy; a 0603
# crowding a SOIC is a part you cannot rework, because the iron has to reach the
# chip's pins with the neighbour still on the board.
CHIP_MIN = 1.50
_chip = []
for _c in sorted(padbox):
    if not re.match(r"^U\d+$", _c):
        continue
    for _o in padbox:
        if _o == _c or re.match(r"^U\d+$", _o):
            continue
        _same = side.get(_c) == side.get(_o)
        _g = min((_pgap(tuple(_x[:4]), tuple(_y[:4]))
                  for _x in padbox[_c] for _y in padbox[_o]
                  if _same or _x[4] or _y[4]), default=None)
        if _g is not None and 0 <= _g < CHIP_MIN:
            _chip.append((round(_g, 2), _c, _o))
_chip.sort()
if _chip:
    print(f"TOO CLOSE TO A CHIP ({len(_chip)} pairs under {CHIP_MIN}mm):")
    for _g, _c, _o in _chip[:12]:
        print(f"   {_g:5.2f}mm  {_c:6} x {_o:6}")
else:
    print(f"nothing within {CHIP_MIN}mm of a chip pad")

# --- a B.Cu footprint must be MIRRORED, not merely relabelled ---------------
# KiCad applies no implicit mirror (proven with kicad-cli: a pad at local (0,+3)
# plots to the same absolute place on either layer), so a part on the back has to
# carry mirrored coordinates in the file. A "flip" that only rewrites the layer
# names leaves the FRONT land pattern on the BACK: pin 1 lands where pin 8 should
# be, and the chip is soldered mirror-image. Thirteen parts were in that state on
# 2026-09-09 -- Q1/Q2 and the whole BBD block, U101-U106 and U201-U206 -- and
# nothing in this file noticed, because the position maths was applying its own
# mirror on top and the two errors cancelled in the checks.
_mir = []
for _ref, _block, _, _ in fp_blocks(src):
    if not _ref or side.get(_ref) == "F.Cu":
        continue
    _fpm = re.match(r'\(footprint "([^"]+)"', _block)
    _lp = lib_pads(_fpm.group(1).split(":")[-1]) if _fpm else None
    if _lp is None:
        continue
    _ly = {round(_y, 3): _n for (_x, _y), _n in
           ((k, v) for k, v in _lp.items())}
    _asym = [(_x, _y) for (_x, _y) in _lp if abs(_y) > 0.001]
    if not _asym:
        continue                       # symmetric: the mirror is a no-op
    _hit = _miss = 0
    for _m in re.finditer(r'\(pad "[^"]*" \w+ \w+ \(at ([-\d.]+) ([-\d.]+)', _block):
        _bx, _by = round(float(_m.group(1)), 3), round(float(_m.group(2)), 3)
        if (_bx, -_by) in _lp: _hit += 1
        elif (_bx, _by) in _lp: _miss += 1
    if _miss and not _hit:
        _mir.append(_ref)
if _mir:
    print(f"\nNOT MIRRORED, front land pattern on the back ({len(_mir)}):")
    print("   " + ", ".join(sorted(_mir)))
    print("   these would be soldered mirror-image -- pin 1 in the wrong corner")
else:
    print("every B.Cu footprint is mirrored, not just relabelled")

# --- bypass caps have to be NEXT TO the pin they decouple -------------------
# A 100nF 10mm from its power pin is decoration: the trace inductance in series
# with it undoes most of what it is for. Nothing noticed this until it was
# measured by hand on 2026-09-08, when the mean was 9.3mm and the worst 12.1mm.
# (chip, power pin, cap) -- the cap must also be on the SAME FACE, or the path
# picks up a via and the point is lost again.
BYPASS = [("U102", "8", "C105"), ("U102", "4", "C106"),
          ("U103", "8", "C107"), ("U103", "4", "C108"),
          ("U106", "8", "C121"), ("U106", "4", "C122"),
          ("U202", "8", "C205"), ("U202", "4", "C206"),
          ("U203", "8", "C207"), ("U203", "4", "C208"),
          ("U206", "8", "C221"), ("U206", "4", "C222"),
          ("U301", "4", "C301"), ("U301", "11", "C302"),
          ("U302", "4", "C303"), ("U302", "11", "C304"),
          ("U401", "4", "C401"), ("U401", "11", "C402"),
          ("U402", "4", "C403"), ("U402", "11", "C404"),
          ("U101", "5", "C111"), ("U104", "16", "C109"),
          ("U201", "5", "C211"), ("U204", "16", "C209"),
          # U9/U10 were never in this table -- the headphone driver and the EXT
          # preamp both got bypass caps that nothing was checking.
          ("U9", "8", "C507"), ("U9", "4", "C508"),
          ("U10", "8", "C509"), ("U10", "4", "C510")]
BYPASS_MAX_MM = 5.0

_byp = []
for _chip, _pin, _cap in BYPASS:
    if _chip not in padpos or _pin not in padpos[_chip] or _cap not in box:
        _byp.append(f"   {_cap:6} -> {_chip}.{_pin}  MISSING from the board")
        continue
    _px, _py = padpos[_chip][_pin]
    _cx, _cy = (box[_cap][0] + box[_cap][2]) / 2.0, (box[_cap][1] + box[_cap][3]) / 2.0
    _d = math.hypot(_cx - _px, _cy - _py)
    if side.get(_cap) != side.get(_chip):
        _byp.append(f"   {_cap:6} -> {_chip}.{_pin}  {_d:5.1f}mm but on {side.get(_cap)}, "
                    f"chip is on {side.get(_chip)} -- via in the path")
    elif _d > BYPASS_MAX_MM:
        _byp.append(f"   {_cap:6} -> {_chip}.{_pin}  {_d:5.1f}mm  (max {BYPASS_MAX_MM})")
if _byp:
    print(f"\nBYPASS CAPS TOO FAR FROM THEIR CHIP ({len(_byp)}):")
    for _l in _byp:
        print(_l)
else:
    print(f"bypass caps hug their chip: all {len(BYPASS)} within {BYPASS_MAX_MM}mm, same face")

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
