#!/usr/bin/env python3
"""Generate hardware/kicad/vuulgaris.kicad_pcb: board outline + placement + nets.

KiCad PCB space is Y-DOWN, the same convention as placement-panel-facing.txt, so
panel coordinates carry over with only the origin shift -- no axis flip and no
unit conversion (the file format is native millimetres).

    pcb_mm = panel_mm - (6.995, 7.000)      # PCB sits inside the 6mm walls
    sheet  = ORIGIN + pcb_mm
"""
import re, json, uuid, os

SCRATCH = "/private/tmp/claude-501/-Users-dylanhackett-V1/4d61871d-02f0-409c-8779-744109130e35/scratchpad"
KI = "/Users/dylanhackett/V1/hardware/kicad"
PRETTY = f"{KI}/lib/vuulgaris.pretty"
TEMPLATE = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/template/stm32f100-discovery-shield/stm32f100-discovery-shield.kicad_pcb"
ORIGIN = (100.0, 50.0)
W, H = 284.3, 125.0

FP = {
    "U1": "DAISY_PATCH_SM", "U3": "SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL",
    "U4": "SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL",
    "DS1": "LCD-TH_HS242L01W4S01", "J1": "TF-SMD_TF-PUSH",
    "ENC0": "SW-TH_ALPS_EC11L1525G01",
    "U5": "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR", "U6": "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
    "R20": "R0402", "R21": "R0402",
    "SW3": "SW-SMD_4P-L6.4-W6.3-P4.00-LS9.5",
    "C20": "C0805", "C22": "C0805", "C24": "C0805", "C25": "C0805",
    "C21": "C0402", "C23": "C0402", "C26": "C0402", "C27": "C0402",
}
for i in range(1, 11):
    FP[f"ENC{i}"] = "SW-TH_EC12EXXXX"
FP["FB1"] = FP["FB2"] = "R0805"
for j in range(2, 7):
    FP[f"J{j}"] = "CONN-TH_WQP-WQP518MA"

# panel-facing coordinates are DERIVED, not chosen -- see placement-panel-facing.txt
PANEL = {
    "ENC1": (24.143, 22.350), "ENC2": (24.143, 39.980), "ENC3": (46.143, 22.350),
    "ENC4": (46.143, 39.980), "ENC5": (68.143, 22.350), "ENC6": (68.143, 39.980),
    "ENC7": (90.143, 22.350), "ENC8": (90.143, 39.980), "ENC9": (118.143, 22.350),
    "ENC10": (118.143, 39.980), "ENC0": (274.714, 91.550), "SW3": (274.714, 109.750),
    "DS1": (212.143, 11.550),
}
# everything else is free placement inside the cavity, grouped by function
FREE = {
    "U1": (120, 90), "U3": (45, 52), "U4": (90, 52),
    "C26": (45, 61), "C27": (90, 61), "R20": (122, 48), "R21": (128, 48),
    "FB1": (196, 53), "U5": (207, 53), "C24": (196, 59), "C20": (217, 53), "C21": (223, 59),
    "FB2": (8, 58), "U6": (19, 58), "C25": (8, 65), "C22": (27, 58), "C23": (27, 65),
    "J1": (172, 84),
}
for j in range(2, 7):
    FREE[f"J{j}"] = (60 + (j - 2) * 30, 117)

def pcb_xy(ref):
    if ref in PANEL:
        px, py = PANEL[ref]
        return px - 6.995, py - 7.000
    return FREE[ref]

# ------------------------------------------------------------------ nets
s = open(f"{SCRATCH}/net.net").read()
body = s[s.index("(nets"):]
pad_net, cur = {}, None
for line in body.split("\n"):
    m = re.search(r'\(net \(code "[^"]+"\) \(name "([^"]+)"\)', line)
    if m:
        cur = m.group(1)
    for nd in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', line):
        pad_net[(nd.group(1), nd.group(2))] = cur

names = sorted({v for v in pad_net.values()})
netnum = {n: i + 1 for i, n in enumerate(names)}

# ------------------------------------------------------------------ boilerplate
tpl = open(TEMPLATE).read()
header = tpl[tpl.index("  (general"):tpl.index("  (net 0")]

# ------------------------------------------------------------------ emit
U = lambda: str(uuid.uuid4())
out = ['(kicad_pcb (version 20221018) (generator pcbnew)', '']
out.append(header.rstrip())
out.append('  (net 0 "")')
for n in names:
    out.append(f'  (net {netnum[n]} "{n}")')

missing_fp = []
for ref in sorted(FP):
    path = f"{PRETTY}/{FP[ref]}.kicad_mod"
    if not os.path.exists(path):
        missing_fp.append(f"{ref}:{FP[ref]}")
        continue
    txt = open(path).read().strip()
    # strip the standalone-file tokens; a pcb footprint carries at/tstamp instead
    txt = re.sub(r'\(version \d+\)\s*', '', txt, count=1)
    txt = re.sub(r'\(generator [^)]*\)\s*', '', txt, count=1)
    txt = txt.replace(f'(footprint "{FP[ref]}"', f'(footprint "vuulgaris:{FP[ref]}"', 1)
    x, y = pcb_xy(ref)
    sx, sy = round(ORIGIN[0] + x, 3), round(ORIGIN[1] + y, 3)
    txt = txt.replace('(layer "F.Cu")', f'(layer "F.Cu")\n    (tstamp {U()})\n    (at {sx} {sy})', 1)
    # reference designator
    txt = re.sub(r'\(fp_text reference "[^"]*"', f'(fp_text reference "{ref}"', txt, count=1)
    # assign nets to pads
    def addnet(m):
        pad = m.group(1)
        net = pad_net.get((ref, pad))
        if not net:
            return m.group(0)
        return m.group(0) + f' (net {netnum[net]} "{net}")'
    txt = re.sub(r'\(pad "([^"]+)"[^\n]*?(?=\)|\n)', lambda m: m.group(0), txt)
    # insert net just before each pad's closing: simpler -- after (layers ...) group
    def padfix(m):
        head, pad = m.group(0), m.group(1)
        net = pad_net.get((ref, pad))
        if not net:
            return head
        return head + f' (net {netnum[net]} "{net}")'
    txt = re.sub(r'\(pad "([^"]+)"(?:[^()]|\([^()]*\))*?\(layers[^)]*\)', padfix, txt)
    out.append(txt)

# board outline
for x1, y1, x2, y2 in [(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]:
    out.append(f'  (gr_line (start {ORIGIN[0]+x1} {ORIGIN[1]+y1}) (end {ORIGIN[0]+x2} {ORIGIN[1]+y2})'
               f' (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (tstamp {U()}))')
out.append(')')

open(f"{KI}/vuulgaris.kicad_pcb", "w").write("\n".join(out) + "\n")
print("footprints :", len(FP) - len(missing_fp), "of", len(FP))
print("missing fp :", missing_fp or "none")
print("nets       :", len(names))
print("outline    :", f"{W} x {H} mm")
