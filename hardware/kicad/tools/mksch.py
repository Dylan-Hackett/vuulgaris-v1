#!/usr/bin/env python3
"""Generate hardware/kicad/vuulgaris.kicad_sch from the verified netlist.

Every pin that carries a net gets a short wire stub plus a GLOBAL LABEL at the
far end.  Global labels are first-class net declarations in KiCad, so net
identity does not depend on stubs happening to touch each other -- which is the
failure mode that broke the EasyEDA version repeatedly.

Coordinate note: symbol-library space is Y-up, schematic space is Y-down.  An
instance placed at (ix,iy) puts a pin whose symbol-space position is (px,py) at
(ix+px, iy-py).  A pin's `angle` points INTO the body, so the stub runs at
angle+180.
"""
import json, re, math, uuid, sys, os

SCRATCH = "/private/tmp/claude-501/-Users-dylanhackett-V1/4d61871d-02f0-409c-8779-744109130e35/scratchpad"
KI = "/Users/dylanhackett/V1/hardware/kicad"
LIBS = [f"{KI}/lib/vuulgaris.kicad_sym", f"{KI}/lib/daisy_es.kicad_sym"]
STUB = 10.16                     # 8 grid units - keeps labels clear of bodies
SHEET = str(uuid.uuid4())

# ---------------------------------------------------------------- symbol text
def symbol_blocks(path):
    """Return {name: raw s-expression text} for each top-level symbol."""
    s = open(path).read()
    out = {}
    for m in re.finditer(r'\(symbol "([^"]+)"', s):
        name = m.group(1)
        if re.search(r'_\d+_\d+$', name):
            continue
        i = m.start()
        depth, j = 0, i
        while j < len(s):
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out[name] = s[i:j + 1]
    return out

blocks, footprints = {}, {}
for p in LIBS:
    blocks.update(symbol_blocks(p))
for name, txt in blocks.items():
    m = re.search(r'\(property "Footprint" "([^"]*)"', txt)
    footprints[name] = m.group(1) if m else ""

pins = json.load(open(f"{SCRATCH}/kpins.json"))

# ---------------------------------------------------------------- the design
SYM = {
    "U1": "ES_DAISY_PATCH_SM_REV1", "U3": "MCP23017-E_SO", "U4": "MCP23017-E_SO",
    "DS1": "HS242L01W4S01", "J1": "TFPUSH",
    "ENC0": "EC11L1525G01",
    "U5": "AMS1117-3.3", "U6": "AMS1117-3.3",
    "FB1": "BEAD0805S601A20T", "FB2": "BEAD0805S601A20T",
    "R20": "0402WGF2201TCE", "R21": "0402WGF2201TCE",
    # LPG analog controls. Placed for the panel; pins intentionally unwired
    # until Bergman's circuit is in the repo (see design-state §6).
    "RV1": "RK09L1240A12",                       # dual-gang, LPG offset
    "RV2": "RK09D117000C", "RV3": "RK09D117000C", "RV4": "RK09D117000C",
    "SW4": "CPG151101S03", "SW5": "CPG151101S03",
    "SW6": "CPG151101S03", "SW7": "CPG151101S03",
    "C20": "CL21A106KAYNNNE", "C21": "CL05B104KO5NNNC",
    "C22": "CL21A106KAYNNNE", "C23": "CL05B104KO5NNNC",
    "C24": "CL21A106KAYNNNE", "C25": "CL21A106KAYNNNE",
    "C26": "CL05B104KO5NNNC", "C27": "CL05B104KO5NNNC",
    # ---- power input stage: USB-C 5V -> DKM10E-12 -> +/-12V.
    # Transcribed pad-for-pad from the routed EasyEDA board `postpcb` in
    # origin2.2.eprj -- see docs/power-usbc-dkm.md. The parts are the same LCSC
    # ones, so pin numbering carries over with no translation.
    "J11": "TYPE-C-31-M-12",           # USB-C receptacle, power only
    "F1":  "ASMD1812-200",             # resettable PTC, 2A hold
    "R22": "RT0603BRD075K1L", "R23": "RT0603BRD075K1L",   # CC1/CC2 5k1
    "C28": "CC0603JRNPO9BN103",        # 10nF at the connector
    "C29": "RVT1H220M0605",            # 22uF 50V, input bulk
    "C30": "CC0805KKX7R9BB105",        # 1uF
    "C31": "CC0603JRX7R8BB104",        # 100nF
    "U7":  "DKM10E-12",
    "C32": "RVT1E470M0505_C2977553", "C33": "RVT1E470M0505_C2977553",  # 47uF raw
    "C34": "CC0603JRX7R8BB104", "C35": "CC0603JRX7R8BB104",            # 100nF raw
    "L1":  "BLM18PG121SN1D_C14709", "L2": "BLM18PG121SN1D_C14709",     # 120R beads
    "C36": "RVT1H220M0605", "C37": "RVT1H220M0605",                    # 22uF rail
    "C38": "CC0603JRX7R8BB104", "C39": "CC0603JRX7R8BB104",            # 100nF rail
    "R24": "RT0603BRD072K2L", "R25": "RT0603BRD072K2L",                # 2k2 LED ballast
    # Rail-present LEDs. They are also the permanent minimum load on each rail,
    # ~4.5mA, which is why the -12V rail behaves with the LPG unpopulated.
    "D1":  "YLED0402Y", "D2": "YLED0402Y",
}
for i in range(1, 11):
    SYM[f"ENC{i}"] = "EC12E2430803"
# J2-J5: 3.5mm CV/gate. Four, not five -- CV out, gate out, CV in, gate in.
# PJ-376 is RIGHT ANGLE: barrel parallel to the board, exiting the top edge, the
# same as the 1/4" jacks. The old WQP-PJ398SM was a vertical Thonkiconn whose
# plug axis is perpendicular to the board -- it cannot exit an edge at all.
for j in range(2, 6):
    SYM[f"J{j}"] = "PJ-376"
# J7-J10: 1/4" audio, L/R in and L/R out. PJ-603 is a horizontal jack -- the
# barrel runs parallel to the board and exits the top edge. Four contacts
# (2,3,4,5); which is tip/sleeve/switch is NOT yet established, see netmap.
for j in range(7, 11):
    SYM[f"J{j}"] = "PJ-603_C41409498"

POS = {
    # --- top band: the digital core -------------------------------------
    "U1":  (150, 170),
    "U3":  (340,  95), "U4":  (340, 235),
    "C26": (430,  95), "C27": (430, 235),
    "R20": (500,  60), "R21": (570,  60),
    "DS1": (660, 110), "J1":  (660, 230),
    # --- left column: UI ------------------------------------------------
    "ENC0": (70, 310),
    "RV1": (300, 430), "RV2": (370, 430), "RV3": (300, 490), "RV4": (370, 490),
    "SW4": (70, 430), "SW5": (150, 430), "SW6": (70, 490), "SW7": (150, 490),
    # --- right: the two 3V3 rails, kept apart from each other ------------
    "FB1": (600, 330), "U5": (690, 330), "C24": (600, 400), "C20": (690, 400), "C21": (770, 400),
    "FB2": (600, 480), "U6": (690, 480), "C25": (600, 550), "C22": (690, 550), "C23": (770, 550),
}
for i in range(1, 11):
    col, row = (i - 1) % 5, (i - 1) // 5
    POS[f"ENC{i}"] = (180 + col * 85, 310 + row * 110)
for j in range(2, 6):
    POS[f"J{j}"] = (180 + (j - 2) * 95, 545)
for j in range(7, 11):
    POS[f"J{j}"] = (180 + (j - 7) * 95, 630)
# power input stage, its own band on the sheet
POS.update({
    # inlet row
    "J11": (80, 760), "C28": (170, 760), "F1": (240, 760),
    "R22": (100, 850), "R23": (170, 850),
    "C29": (310, 760), "C30": (375, 760), "C31": (440, 760),
    "U7":  (530, 800),
    # +12V rail, above the converter
    "C32": (620, 720), "C34": (685, 720), "L1": (755, 720),
    "C36": (830, 720), "C38": (895, 720), "R24": (965, 720), "D1": (1035, 720),
    # -12V rail, below it
    "C33": (620, 880), "C35": (685, 880), "L2": (755, 880),
    "C37": (830, 880), "C39": (895, 880), "R25": (965, 880), "D2": (1035, 880),
})


# footprint per reference; nickname must match fp-lib-table, name must match the
# .kicad_mod filename in lib/vuulgaris.pretty/
FPMAP = {
    "U1": "DAISY_PATCH_SM",
    "U3": "SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL", "U4": "SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL",
    "DS1": "LCD-TH_HS242L01W4S01", "J1": "TF-SMD_TF-PUSH",
    "ENC0": "SW-TH_ALPS_EC11L1525G01",
    "U5": "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR", "U6": "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
    "R20": "R0402", "R21": "R0402",
    "RV1": "RES-ADJ-TH_RK09L1240A12",
    "RV2": "RES-ADJ-TH_RK09D1130C4G", "RV3": "RES-ADJ-TH_RK09D1130C4G",
    "RV4": "RES-ADJ-TH_RK09D1130C4G",
    "SW4": "KEY-TH_CPG1511F01S0X", "SW5": "KEY-TH_CPG1511F01S0X",
    "SW6": "KEY-TH_CPG1511F01S0X", "SW7": "KEY-TH_CPG1511F01S0X",
    "C20": "C0805", "C22": "C0805", "C24": "C0805", "C25": "C0805",
    "C21": "C0402", "C23": "C0402", "C26": "C0402", "C27": "C0402",
    "FB1": "R0805", "FB2": "R0805",
}
for _i in range(1, 11):
    FPMAP[f"ENC{_i}"] = "SW-TH_EC12EXXXX"
for _j in range(2, 6):
    FPMAP[f"J{_j}"] = "AUDIO-TH_PJ-376"
for _j in range(7, 11):
    FPMAP[f"J{_j}"] = "AUDIO-TH_PJ-603"
FPMAP.update({
    "J11": "USB-C_SMD-TYPE-C-31-M-12_1",
    "F1":  "F1812",
    "R22": "R0603", "R23": "R0603", "R24": "R0603", "R25": "R0603",
    "C28": "C0603", "C30": "C0805", "C31": "C0603",
    "C34": "C0603", "C35": "C0603", "C38": "C0603", "C39": "C0603",
    # SMD aluminium cans -- 6.6mm square / 5.3mm square footprints, and they
    # stand 6.0mm and 5.4mm tall. Height matters near the OLED standoff.
    "C29": "CAP-SMD_BD6.3-L6.6-W6.6-FD", "C36": "CAP-SMD_BD6.3-L6.6-W6.6-FD",
    "C37": "CAP-SMD_BD6.3-L6.6-W6.6-FD",
    "C32": "CAP-SMD_BD5.0-L5.3-W5.3-LS6.3-FD",
    "C33": "CAP-SMD_BD5.0-L5.3-W5.3-LS6.3-FD",
    "L1": "L0603", "L2": "L0603",
    "D1": "LED0402-R-RD", "D2": "LED0402-R-RD",
    "U7": "PWRM-TH_DKMW30F-12",
})

NET = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "netmap.json")))

# ---------------------------------------------------------------- emit
def U():
    return str(uuid.uuid4())

def pin_xy(ref, pin):
    sym = SYM[ref]
    p = pins[sym][pin]
    ix, iy = POS[ref]
    return ix + p['x'], iy - p['y'], p['angle']

out = []
A = out.append
A('(kicad_sch (version 20221206) (generator eeschema)')
A(f'  (uuid {U()})')
A('  (paper "A1")')
A('  (lib_symbols')
for name in sorted({SYM[r] for r in SYM}):
    txt = blocks[name].replace(f'(symbol "{name}"', f'(symbol "vuulgaris:{name}"', 1)
    A(txt)
A('  )')

wires, labels, ncs = [], [], []
for ref in sorted(SYM):
    name = SYM[ref]
    x, y = POS[ref]
    A(f'  (symbol (lib_id "vuulgaris:{name}") (at {x} {y} 0) (unit 1)')
    A('    (in_bom yes) (on_board yes) (dnp no)')
    A(f'    (uuid {U()})')
    A(f'    (property "Reference" "{ref}" (at {x} {y - 12} 0) (effects (font (size 1.27 1.27))))')
    A(f'    (property "Value" "{name}" (at {x} {y - 9} 0) (effects (font (size 1.27 1.27))))')
    A(f'    (property "Footprint" "vuulgaris:{FPMAP[ref]}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    A(f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    for pn in pins[name]:
        A(f'    (pin "{pn}" (uuid {U()}))')
    A('  )')

    # every pin gets explicit treatment: a net label, or a no-connect marker
    for pn in pins[name]:
        if pn not in NET.get(ref, {}):
            px, py, _ = pin_xy(ref, pn)
            ncs.append((round(px, 2), round(py, 2)))

    for pn, net in NET.get(ref, {}).items():
        if pn not in pins[name]:
            print(f"MISSING PIN {ref}.{pn}", file=sys.stderr)
            continue
        px, py, ang = pin_xy(ref, pn)
        a = math.radians(ang + 180.0)
        ex = round(px + STUB * math.cos(a), 2)
        ey = round(py - STUB * math.sin(a), 2)
        wires.append((round(px, 2), round(py, 2), ex, ey))
        labels.append((ex, ey, net, (ang + 180) % 360))

for x1, y1, x2, y2 in wires:
    A(f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type solid)) (uuid {U()}))')
for x, y, net, ang in labels:
    A(f'  (label "{net}" (at {x} {y} {int(ang)}) (fields_autoplaced)')
    A('    (effects (font (size 1.27 1.27)) (justify left bottom))')
    A(f'    (uuid {U()})')
    A('  )')

for x, y in ncs:
    A(f'  (no_connect (at {x} {y}) (uuid {U()}))')

A('  (sheet_instances (path "/" (page "1")))')
A(')')

os.makedirs(KI, exist_ok=True)
open(f"{KI}/vuulgaris.kicad_sch", "w").write("\n".join(out) + "\n")
print("components:", len(SYM))
print("wires     :", len(wires))
print("labels    :", len(labels))
print("nets      :", len({l[2] for l in labels}))
print("no-connect:", len(ncs))
