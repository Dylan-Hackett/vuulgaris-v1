"""The faceplate's schematic design: which symbol each ref uses, where it sits on
the sheet, and which footprint it gets. Drawn by hardware/kicad/tools/mksch.py
--project faceplate; netmap.json beside this file is the intent it is checked
against (tools/netcheck.py --project faceplate).

Rule for this board: every IC's support circuit comes from the manufacturer's
reference circuit, never from first principles. Each block below says which
figure it came from; a part that did not come from one says so.

Symbols come from the main board's library plus KiCad's generic ones. Footprints
are named "lib:name"; a bare name means the shared vuulgaris.pretty. Every part
goes on the BACK and is SMD: the front is bare ENIG under the player's hand.
Passives follow the main board: 0603, with 0805 for 1uF and up.
"""
import json
import proj

MAIN = proj.PROJECTS["main"]
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

# Must match ksym.py's argument list for this project (faceplate README):
# stock libraries first, the project library last.
LIBS = [
    f"{STOCK}/Connector_Generic.kicad_sym",
    f"{STOCK}/Device.kicad_sym",
    f"{MAIN.dir}/lib/vuulgaris.kicad_sym",
]

NET = json.load(open(proj.P.netmap))

SYM, POS, FPMAP = {}, {}, {}


def part(ref, sym, fp, xy):
    SYM[ref], FPMAP[ref], POS[ref] = sym, fp, xy


# ---------------------------------------------------------------- the cable
# J1 pin n carries main-board J12 pin n's net (the ribbon is straight through),
# and tools/panelcheck.py fails if the two netmaps ever disagree.
# hanxia HX JN2.54-2x5P TP H8.9, LCSC C41376028 (Extended: JLC has no Basic
# SMD 2x5 box header). SMD because a through-hole header here puts ten pins
# through the FRONT face, in the 8mm gap between pads 3 and 4. Footprint from
# hanxia's drawing; 9.60mm seated, under the 10mm gap. Pin 1 is on the
# key-side row at the triangle end -- confirm with a real ribbon before
# ordering (hardware/faceplate/README.md, section 5). It is also the
# CAPTIVATE-PGMR connection (ADR 0005).
part("J1", "Conn_02x05_Odd_Even", "IDC-SMD_10P-P2.54_C41376028", (100, 100))

# ---------------------------------------------------------------- the MCU
# MSP430FR2675TPT, LCSC C2052972. Symbol and PT0048A footprint from
# design/mklib_faceplate.py (SLASEO5D Figure 7-1 == Table 7-1, TI land pattern).
part("U1", "MSP430FR2675TPT", "LQFP-48_7x7mm_P0.5mm_PT0048A", (330, 220))

# Supply, from SLASEO5D section 10.1.1, Figure 10-1: "a combination of a 10-uF
# plus a 100-nF low-ESR ceramic decoupling capacitor to the DVCC and DVSS pins",
# within a few millimetres of them. DVCC is P3V3_MSP430 straight off the cable:
# U6 on the main board is this MCU's own AMS1117 (ADR 0012), and TI's figure
# has nothing between supply and pin but the two capacitors.
part("C1", "C", "C0805", (160, 300))       # 10uF  DVCC bulk
part("C2", "C", "C0603", (185, 300))       # 100nF DVCC
# VREG, pin 31: the CapTIvate regulator's output. SLASEO5D section 4, the notes
# under Figure 4-1: "The recommended value for the required decoupling
# capacitor is 1 uF, with a maximum ESR of <=200 mohm" (CREG in 8.12.10.1
# likewise). A ceramic MLCC is far under that.
part("C3", "C", "C0805", (210, 300))       # 1uF   VREG
# RST/NMI/SBWTDIO, pin 2: SLASEO5D Figure 10-4 (2-wire JTAG, Spy-Bi-Wire):
# R1 47k to VCC and C1 1nF to ground, "The upper limit for C1 is 1.1 nF when
# using current TI tools." Required here, not just good practice: MSP_RST is
# driven by the main board's MCP23017 U4, whose GPIO power up high-Z
# (pin-allocation.md, "MSP430 reset on U4 GPB3").
part("R1", "R", "R0603", (240, 300))       # 47k   RST pull-up
part("C4", "C", "C0603", (265, 300))       # 1nF   RST
# TEST/SBWTCK, pin 3: nothing. Figure 10-4 wires it straight to the tool, and
# Table 7-4 says an unused TEST is left "Open. This pin always has an internal
# pulldown enabled" (Table 7-1: reset state PD). MSP_TEST is undriven at J12.

# UART on UCA0 at its default pins, P1.4 TXD (4) / P1.5 RXD (5): the runtime
# link and the UART BSL are the same two wires (SLASEO5D Table 9-4;
# pin-allocation.md). 47k pull-ups on both, from SLAU550 section 3.3.2.1:
# "Add a 47-kohm pullup resistor and a 1-nF pulldown capacitor on TCK and TMS"
# -- P1.4 is TCK and P1.5 is TMS. The 1nF capacitors are left off by decision
# (README section 6): they serve the hardware BSL entry sequence, which
# production never uses (blank-device detection, then software invocation).
# The pull-ups also hold RXD high while the Daisy boots.
part("R2", "R", "R0603", (290, 300))       # 47k   P1.4 TXD / TCK
part("R3", "R", "R0603", (315, 300))       # 47k   P1.5 RXD / TMS

# XT1, 32.768kHz, on P2.1/XIN (47) and P2.0/XOUT (46). Topology from SLASEO5D
# section 10.1.2, Figure 10-2: crystal across XIN/XOUT, one capacitor from each
# to ground ("External bypass capacitors for the crystal oscillator pins are
# required"). Q22: the FLL locks to it, so baud accuracy is not a question.
# Y1: Epson FC-135 12.5pF (C32346, JLC Basic); C0 1pF against TI's 1.6pF max
# shunt (8.12.3.1 note 7). NOT from a reference circuit: the capacitor VALUE.
# TI gives no number, only "meet the effective load capacitance specified by
# crystal manufacturers" with CL,eff 1pF integrated (8.12.3.1). 12.5pF =
# C/2 + 1 + board stray puts C near 20pF; 22pF is the nearest Basic C0G 0603
# (C1653, already on the main board) and lands a pF or so high, which pulls a
# few ppm -- irrelevant to a UART that needs percent. Q22: fit the footprint;
# populating it is decided later.
part("Y1", "Crystal", "XTAL-SMD_FC-135_3.2x1.5mm", (360, 300))
part("C5", "C", "C0603", (390, 300))       # 22pF C0G  XIN
part("C6", "C", "C0603", (415, 300))       # 22pF C0G  XOUT

# ---------------------------------------------------------------- the pads
# Sixteen CapTIvate lines, four per pad, each pad ONE PIN FROM EACH BLOCK:
# RXn of pad p on CAPn.(p-1), so a pad's four elements are measured in one
# cycle, in parallel (SLASEO5D 9.10.14, "one electrode per block"; the
# CapTIvate Technology Guide's 4-element slider figure; pin-allocation.md).
# Pads are numbered 1-4 from the jack edge.
#
# Per line, from the CapTIvate Technology Guide, Design Guide, "Electrostatic
# Discharge (ESD)": "Populate a 470-1k ohm resistor in series with the
# electrode ... with a protection clamp such as a TVS diode placed between the
# electrode and ground (return) on the electrode side of the resistor"; the
# guide names TPD1E10B06. So: electrode net PADp_RXn -- TVS Dpn to GND --
# series R Rpn -- pin net CAPn.(p-1). 470R, the low end of TI's range and the
# value TI gives for its RX series resistors. 16 of each (ADR 0004): RX0's two
# ends are pins 1 and 5 of Ep, both on PADp_RX0, joined ahead of the TVS.
# Both TVS pins are "ESD Protected I/O. Connect other pin ground": pin 1 goes
# to the electrode, pin 2 to GND.
for _p in range(1, 5):
    _y = 360 + (_p - 1) * 65
    part(f"E{_p}", "SCRUB_PAD_5SEG", "", (90, _y))
    for _n in range(4):
        part(f"D{_p}{_n + 1}", "D_TVS", "X1SON-2_DPY0002A", (180 + _n * 55, _y))
        part(f"R{_p}{_n + 1}", "R", "R0603", (420 + _n * 25, _y))
