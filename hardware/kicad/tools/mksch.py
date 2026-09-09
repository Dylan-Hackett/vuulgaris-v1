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

SCRATCH = os.path.dirname(os.path.abspath(__file__))   # kpins.json lives beside the tools
KI = "/Users/dylanhackett/V1/hardware/kicad"
LIBS = [f"{KI}/lib/vuulgaris.kicad_sym", f"{KI}/lib/daisy_es.kicad_sym"] + [
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Switch.kicad_sym",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Audio.kicad_sym",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Analog_DAC.kicad_sym",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Connector.kicad_sym",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Connector_Generic.kicad_sym",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym",
]
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
    # SW1 LPG MODE (stereo VCF / stereo VCA), SW2 SOURCE (resample / external).
    # Dailywell 2MD1T1B1M2QES DPDT ON-ON, PC pin -- Thonk sell it as DW3. Pins
    # 2 and 5 are the COMMONS, throws 1/3 and 4/6, per the manufacturer drawing.
    # Analog routing on the LPG, so unwired until Bergman's circuit lands.
    # Six ANALOG pots, ALL dual-gang so one knob controls both stereo sides:
    # CUTOFF, RESONANCE, FILTER CV AMT (filter) and TIME, FEEDBACK, WET/DRY
    # (delay). Placed for the panel; pins unwired until the LPG and the
    # Moritz Klein BBD land. RV5/RV6 sit where ENC9/ENC10 used to be.
    "RV1": "RK09L1240A12",
    "RV2": "RK09L1240A12",
    "RV3": "RK09L1240A12",
    "RV4": "RK09L1240A12",
    "RV5": "RK09L1240A12",
    "RV6": "RK09L1240A12",
    # SW_DPDT_x2 is a TWO-UNIT symbol: pins 1/4, 2/5 and 3/6 sit at identical
    # symbol coordinates, so this generator (one instance, unit 1) would stub
    # them onto each other the moment either switch is wired.  SW_DPDT_FLAT is
    # the same part with all six pins at distinct points -- same footprint.
    "SW1": "SW_DPDT_FLAT", "SW2": "SW_DPDT_FLAT",
    # Six UI buttons, 12x12 through-hole tactile, 2 wide x 3 tall. Replaced four
    # Cherry MX 2026-09-06: MX caps are 18mm on 19.05 pitch and six will not fit
    # the same panel area. The tactile's pads splay to 14.7mm so the columns keep
    # the 19.05 pitch and only the ROWS tighten, to 12.7mm.
    # TS1103S-12X12X14DIP (LCSC C54573007), swapped in 2026-09-08. The old
    # TC-1212-7.3-160G is 7.3mm tall and the panel's outer face is at 11.6mm, so
    # it could never have reached through -- and its 3.8mm SQUARE stem has a
    # 5.37mm diagonal, which would not have passed the 4.5mm hole either. Same
    # 12x12 body and the same 4-pin 12.5 x 5.0 pattern, so the FOOTPRINT is
    # unchanged; this is a part-number swap only.
    "SW4": "TS1103S-12X12X14DIP", "SW5": "TS1103S-12X12X14DIP",
    "SW6": "TS1103S-12X12X14DIP", "SW7": "TS1103S-12X12X14DIP",
    "SW8": "TS1103S-12X12X14DIP", "SW9": "TS1103S-12X12X14DIP",
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

    # ---- board-to-board to the faceplate.  THT here (both faces of this board
    # are hidden); the faceplate side is SMD so no solder shows on the front
    # face where the capacitive pads live.
    #
    # R26-R29 were two 5V->3.3V dividers carrying GATE_OUT_1/2 to the MSP430's
    # RST and TEST pins, for the HARDWARE BSL entry sequence in ADR 0005.  All
    # four are GONE as of 2026-09-06.  SLAU550 Rev AB section 3.3.3: the FR26xx
    # boot code does blank device detection and jumps straight into the BSL when
    # the reset vector reads 0xFFFF, which "eliminates the need for two
    # additional wires (TEST, RST)".  A chip fresh off the reel answers over the
    # UART on its own, so the entry sequence -- and both gate outputs with it --
    # was never needed.  J12 pins 7 and 9 still carry RST/TEST to the faceplate
    # as spare wires; nothing on this board drives them.
    "J12": "HDR-IDC-2.54-2X5P",

    # Power test points, through-hole so a probe can hook them or a wire loop can
    # be soldered in. TP5 is GND and sits with the others on purpose: a rail
    # measured against a ground 100mm away tells you about the ground.
    # Headphone monitor driver. OPA1688 (C206212): +/-18V, 75mA out, and TI
    # characterise its 0.00005% THD+N INTO 32 ohms -- it is a headphone part.
    # OPA1688_FLAT, not the LCSC symbol, which is multi-unit and would stub OUTA
    # onto OUTB in this generator. RT501/RT502 set max level and are set once.
    "U9": "OPA1688_FLAT",
    "RT501": "TRIMPOT_3T", "RT502": "TRIMPOT_3T",
    # EXT input preamp. The 1/4" jacks are a LINE input -- audio I/O is PJ-603,
    # CV is PJ-376 -- but they fed U1.B3/B4 at unity, and the Patch SM's full
    # scale is Eurorack 9.5Vpp. A receiver or phone lands 10-20dB down, and
    # software gain cannot recover that: it lifts the converter's noise floor
    # with the signal. RT503/RT504 set 1x to 10.1x once, on the back.
    "U10": "OPA1688_FLAT",
    "RT503": "TRIMPOT_3T", "RT504": "TRIMPOT_3T",
    "TP1": "TestPoint", "TP2": "TestPoint", "TP3": "TestPoint",
    "TP4": "TestPoint", "TP5": "TestPoint",
    # Signal test points. TP6-TP9 are the mki manual's TP1/TP3 equivalents, asked
    # for in docs/bbd-mki.md so R104's value can be chosen with a scope instead of
    # by ear. TP10/TP11 are the vactrol LED drive: RT301/RT401 have to be trimmed
    # by hand, and you cannot set a trimmer you cannot measure. TP12/TP13 are the
    # two 4046 clocks -- their mistracking IS the stereo width. TP14/TP15 are the
    # two DAC outputs, which split a fault into firmware or analog in one probe.
    "TP6": "TestPoint", "TP7": "TestPoint", "TP8": "TestPoint",
    "TP9": "TestPoint", "TP10": "TestPoint", "TP11": "TestPoint",
    "TP12": "TestPoint", "TP13": "TestPoint", "TP14": "TestPoint",
    "TP15": "TestPoint",

    # ---- stereo BBD delay, SSI2100. See docs/bbd-ssi2100.md.

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
# ENC9/ENC10 became analog pots 2026-09-01 -- eight encoders now.
for i in range(1, 9):
    SYM[f"ENC{i}"] = "EC12E2430803"
# J2-J5: 3.5mm CV/gate. Four, not five -- CV out, gate out, CV in, gate in.
# PJ-376 is RIGHT ANGLE: barrel parallel to the board, exiting the top edge, the
# same as the 1/4" jacks. The old WQP-PJ398SM was a vertical Thonkiconn whose
# plug axis is perpendicular to the board -- it cannot exit an edge at all.
for j in range(2, 6):
    SYM[f"J{j}"] = "PJ-376"
# J6 is the HEADPHONE jack, added 2026-09-08. Same PJ-376 as the CV jacks because
# it is already a stereo TRS -- 1 sleeve, 2 ring, 3 tip -- so tip/ring carry L/R.
# Reuses a part, a footprint and a pinout that are already established.
SYM["J6"] = "PJ-376"
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
    "TP1": (860, 60), "TP2": (920, 60), "TP3": (980, 60),
    "TP4": (1040, 60), "TP5": (1100, 60),
    "U9": (860, 300), "RT501": (960, 300), "RT502": (1060, 300), "J6": (1160, 300),
    "U10": (860, 370), "RT503": (960, 370), "RT504": (1060, 370),
    "TP6": (860, 130), "TP7": (920, 130), "TP8": (980, 130), "TP9": (1040, 130),
    "TP10": (1100, 130), "TP11": (860, 200), "TP12": (920, 200),
    "TP13": (980, 200), "TP14": (1040, 200), "TP15": (1100, 200),
    "DS1": (660, 110), "J1":  (660, 230),
    # --- left column: UI ------------------------------------------------
    "ENC0": (70, 310),
    "RV1": (300, 430), "RV2": (370, 430), "RV3": (440, 430),
    "RV4": (300, 490), "RV5": (370, 490), "RV6": (440, 490),
    # SW1/SW2 used to sit at (440,430)/(440,490) -- exactly on top of RV3/RV6.
    # SW_DPDT_x2 pin 1 is at symbol (5.08, 2.54), which is RK09L1240A12 pin 1;
    # pin 3 is at (5.08,-2.54), which is pot pin 4. Coincident pins bind to the
    # same net. Invisible while both parts were unwired; the moment RV6 got
    # nets, netcheck reported SW2.1 -> BBD_DRY_L and SW2.3 -> BBD_DRY_R, i.e.
    # the LPG SOURCE switch shorted onto the dry audio bus in both channels.
    # Sheet coordinates only -- POS is not read by place.py or mkpcb.py.
    "SW1": (530, 430), "SW2": (530, 490),
    "SW4": (70, 430), "SW5": (150, 430), "SW6": (70, 490),
    "SW7": (150, 490), "SW8": (230, 430), "SW9": (230, 490),
    # --- right: the two 3V3 rails, kept apart from each other ------------
    "FB1": (600, 330), "U5": (690, 330), "C24": (600, 400), "C20": (690, 400), "C21": (770, 400),
    "FB2": (600, 480), "U6": (690, 480), "C25": (600, 550), "C22": (690, 550), "C23": (770, 550),
}
for i in range(1, 9):
    col, row = (i - 1) % 4, (i - 1) // 4
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
    # faceplate interface, its own band between the power stage and the BBD
    "J12": (150, 950),
    "R26": (300, 930), "R27": (300, 990), "R28": (390, 930), "R29": (390, 990),
})


# footprint per reference; nickname must match fp-lib-table, name must match the
# .kicad_mod filename in lib/vuulgaris.pretty/
FPMAP = {
    "U1": "DAISY_PATCH_SM",
    "U3": "SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL", "U4": "SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL",
    "DS1": "LCD-TH_HS242L01W4S01", "J1": "TF-SMD_TF-PUSH",
    "ENC0": "SW-TH_ALPS_EC11L1525G01",
    "U5": "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR", "U6": "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
    "U9": "SOP-8_L4.9-W3.9-P1.27-LS6.0-BL",
    "RT501": "RES-ADJ-SMD_3224W", "RT502": "RES-ADJ-SMD_3224W",
    "U10": "SOP-8_L4.9-W3.9-P1.27-LS6.0-BL",
    "RT503": "RES-ADJ-SMD_3224W", "RT504": "RES-ADJ-SMD_3224W",
    "TP6": "TestPoint_TH_D1.0mm", "TP7": "TestPoint_TH_D1.0mm",
    "TP8": "TestPoint_TH_D1.0mm", "TP9": "TestPoint_TH_D1.0mm",
    "TP10": "TestPoint_TH_D1.0mm", "TP11": "TestPoint_TH_D1.0mm",
    "TP12": "TestPoint_TH_D1.0mm", "TP13": "TestPoint_TH_D1.0mm",
    "TP14": "TestPoint_TH_D1.0mm", "TP15": "TestPoint_TH_D1.0mm",
    "TP1": "TestPoint_TH_D1.0mm", "TP2": "TestPoint_TH_D1.0mm",
    "TP3": "TestPoint_TH_D1.0mm", "TP4": "TestPoint_TH_D1.0mm",
    "TP5": "TestPoint_TH_D1.0mm",
    "U8": "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
    "R20": "R0402", "R21": "R0402",
    "SW1": "SW-TH_DW3_DPDT_2MD1T1B1M2QES",
    "SW2": "SW-TH_DW3_DPDT_2MD1T1B1M2QES",
    "RV1": "RES-ADJ-TH_RK09L1240A12",
    "RV2": "RES-ADJ-TH_RK09L1240A12",
    "RV3": "RES-ADJ-TH_RK09L1240A12",
    "RV4": "RES-ADJ-TH_RK09L1240A12",
    "RV5": "RES-ADJ-TH_RK09L1240A12",
    "RV6": "RES-ADJ-TH_RK09L1240A12",
    "SW4": "KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5", "SW5": "KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5",
    "SW6": "KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5", "SW7": "KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5",
    "SW8": "KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5", "SW9": "KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5",
    "C20": "C0805", "C22": "C0805", "C24": "C0805", "C25": "C0805",
    "C21": "C0402", "C23": "C0402", "C26": "C0402", "C27": "C0402",
    "FB1": "R0805", "FB2": "R0805",


}
for _i in range(1, 9):
    FPMAP[f"ENC{_i}"] = "SW-TH_EC12EXXXX"
for _j in range(2, 6):
    FPMAP[f"J{_j}"] = "AUDIO-TH_PJ-376"
FPMAP["J6"] = "AUDIO-TH_PJ-376"          # headphone jack, same part as the CV jacks
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
    "J12": "IDC-TH_10P-P2.54_C5665",
    "R26": "R0603", "R27": "R0603", "R28": "R0603", "R29": "R0603",
})

VALUE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "values.json"))) if os.path.exists(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "values.json")) else {}

NET = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "netmap.json")))

# ---------------------------------------------------------------- stereo LPG
# Eddy Bergman's Buchla 292 lowpass gate, two channels. See docs/lpg-bergman.md.
# Deviations from the drawing, all deliberate: no CV1 path, no DEEP switch, and
# R12/R16 NOT FITTED because only BOTH and VCF modes are wanted -- the VCA
# contact is never made, so those two resistors have nothing to do.
LPG_SYM = {}
for _b, _S in ((300, "L"), (400, "R")):
    LPG_SYM[f"U{_b+1}"] = "TL074_FLAT"          # A in-buf, B LED drive, C out-buf, D resonance
    LPG_SYM[f"VT{_b+1}"] = "VTL5C3"
    LPG_SYM[f"VT{_b+2}"] = "VTL5C3"
    LPG_SYM[f"RT{_b+1}"] = "TRIMPOT_3T"          # Tp1 20K, LED drive depth.
    # Tp2 500K is NOT fitted: it only does anything with the DEEP switch closed,
    # and DEEP is not fitted either.
    LPG_SYM[f"D{_b+1}"]  = "BZT52C3V9_C2891408"  # 3V9 clamp on the LED node
    LPG_SYM[f"U{_b+2}"] = "TL074_FLAT"           # Bergman U2, CV chain, one per channel
LPG_FP = {"TL074_FLAT": "SOIC-14_3.9x8.7mm_P1.27mm",
          "VTL5C3":     "VACTROL-TH_VTL5C3",
          # 3224W-1-203E (LCSC C55071): the SMD sibling of the 3266W, same 4mm
          # square multiturn cermet, 12 turns. Swapped 2026-09-08 so JLC can
          # place it -- the through-hole 3266W had no LCSC number at all, which
          # made it one of the parts that had to be hand-fitted. Multiturn is
          # not negotiable here: this sets the vactrol LED drive depth by ear
          # against a scope, and a single-turn part puts 20k into 270 degrees.
          "TRIMPOT_3T": "RES-ADJ-SMD_3224W",
          "BZT52C3V9_C2891408": "SOD-123_L2.7-W1.6-LS3.7-RD-1"}

for _ref, _sym in LPG_SYM.items():
    if _ref in NET:
        SYM[_ref] = _sym
        FPMAP[_ref] = LPG_FP[_sym]

_LPG_BANDS = [([r for r in sorted(NET) if r not in SYM and re.match(r"^[RC]3\d\d$", r)], 3000),
              ([r for r in sorted(NET) if r not in SYM and re.match(r"^[RC]4\d\d$", r)], 3300),
              ([r for r in sorted(NET) if r not in SYM and re.match(r"^[RC]9\d$", r)], 3600),
              # 5xx: the I/O interconnect -- jacks -> SW2 SOURCE -> Daisy audio
              # in. Not part of the LPG; it just wants the same generic R/C
              # symbols and a band of its own to sit in.
              ([r for r in sorted(NET) if r not in SYM and re.match(r"^[RC]5\d\d$", r)], 3750)]
for _refs, _y0 in _LPG_BANDS:
    for _i, _r in enumerate(_refs):
        SYM[_r] = "R" if _r[0] == "R" else "C"
        FPMAP[_r] = "R0603" if _r[0] == "R" else "C0603"
        POS[_r] = (120 + (_i % 10) * 130, _y0 + (_i // 10) * 90)
for _i, _r in enumerate(sorted(LPG_SYM)):
    if _r in NET:
        POS[_r] = (120 + (_i % 6) * 200, 3900 + (_i // 6) * 120)

# ---------------------------------------------------------------- stereo BBD
# Moritz Klein's mki x es.edu BBD, two channels, TWO CD4046 clocks (one per
# channel -- the dual-gang TIME pot's mistracking IS the stereo width, see
# docs/bbd-ssi2100.md).  Topology transcribed from page 61 of the manual;
# docs/bbd-mki.md is the readable form and the thing to check this against.
#
# Passives are the generic Device:R / Device:C symbols rather than one LCSC
# symbol per exact part number: a resistor symbol carries nothing its value
# does not, Device.kicad_sym is already in LIBS above, and R0603/C0603 are
# already in the footprint library.  The ICs are real LCSC pulls because their
# PIN NUMBERING has to come from somewhere trustworthy.
BBD_SYM = {
    "U101": "V3205SD",    "U201": "V3205SD",
    "U102": "TL072_FLAT",  "U202": "TL072_FLAT",     # input buffer + S&H comparator
    "U103": "TL072_FLAT",  "U203": "TL072_FLAT",     # summing amp + mix buffer
    "U106": "TL072_FLAT",  "U206": "TL072_FLAT",     # S&H buffer + output amp
    "U104": "CD4046BNSR", "U204": "CD4046BNSR",   # one clock EACH, not shared
    "Q1":   "MMBFJ113",   "Q2":   "MMBFJ113",     # J113 equivalent, S&H switch
    # +5V for both channels.  Was a 78L05 in SOT-89 until 2026-09-07: 12V->5V is
    # a 7V drop, and that package is 500mW at ~250 C/W, so the margin depended
    # entirely on the BBD's supply current -- which Panasonic never specified for
    # the MN3205.  SOT-223 removes the guess.  Same part family and footprint as
    # U5/U6, and 1A instead of 100mA.
    "U8":   "AMS1117-5.0",
}
BBD_FP = {
    "V3205SD":       "DIP-8_SPECIAL_V3205SD",
    "TL072_FLAT":    "SOIC-8_L4.9-W3.9-P1.27-LS6.1-BL",
    "CD4046BNSR":    "SO-16_L10.3-W5.3-P1.27-LS7.8-BL",
    "MMBFJ113":      "SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR",
    "AMS1117-5.0":   "SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR",
    "1N4148WT4":     "SOD-123_L2.8-W1.8-LS3.7-RD",
    "SW_DPDT_FLAT":  "SW-TH_DW3_DPDT_2MD1T1B1M2QES",
}
# Caps that must NOT be 0603 X7R.  C_19 is the sample-and-hold storage cap on a
# high-impedance node -- X7R's voltage coefficient and piezoelectric response
# both land straight in the audio there, so it is 0805 C0G.  C_13 and C_20 are
# marked "Film" on the drawing, in the signal path.  C_10 and C42 are just too
# big for 0603 at a sane voltage rating.
BBD_C0805 = {"C110", "C113", "C119", "C120", "C210", "C213", "C219", "C220", "C42"}

for _ref in NET:
    if _ref in SYM:
        continue
    if _ref in BBD_SYM:
        SYM[_ref] = BBD_SYM[_ref]
    elif _ref.startswith("D"):
        SYM[_ref] = "1N4148WT4"
    elif _ref.startswith("R"):
        SYM[_ref] = "R"
    elif _ref.startswith("C"):
        SYM[_ref] = "C"
    else:
        raise SystemExit(f"BBD: no symbol for {_ref}")
    _sym = SYM[_ref]
    FPMAP[_ref] = ("C0805" if _ref in BBD_C0805 else
                   "C0603" if _sym == "C" else
                   "R0603" if _sym == "R" else BBD_FP[_sym])

# Sheet layout.  Generous spacing on purpose: every pin here gets a 10.16mm
# stub, and two stubs that happen to land on the same point are one net with
# nothing to show for it -- the SW1/RV3 failure above, in a new place.  netcheck
# is what actually proves this did not happen.
_BBD_BANDS = [
    ([r for r in sorted(NET) if r not in POS and r.endswith(("1", "2", "3", "4", "5",
      "6", "7", "8", "9", "0")) and re.match(r"^[A-Z]+1\d\d$", r)], 1000),   # left
    ([r for r in sorted(NET) if re.match(r"^[A-Z]+2\d\d$", r)], 1700),        # right
    (["Q1", "Q2", "U8", "C40", "C41", "C42"], 2400),                           # shared
]
for _refs, _y0 in _BBD_BANDS:
    for _i, _r in enumerate(_refs):
        if _r in POS:
            continue
        POS[_r] = (120 + (_i % 8) * 150, _y0 + (_i // 8) * 80)

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
    A(f'    (property "Value" "{VALUE.get(ref, name)}" (at {x} {y - 9} 0) (effects (font (size 1.27 1.27))))')
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
