# 10: Faceplate MSP430FR2675 and electrodes

Block: everything in `hardware/faceplate/design/netmap.json`: U1, C1-C6, R1-R3,
R11-R44, D11-D44, Y1, E1-E4, TP1-TP6, J1 (its interconnect side is section 9).

Sources: `TI-MSP430FR2675-datasheet.pdf` (SLASEO5D, the PT package: Figure
7-1 p10, Table 7-1 p13-p17, Table 7-2 p18-p22, Table 7-4 p23, 8.1 and
recommended operating conditions p24, 8.12.3.1 p32, 8.12.3.4, 10.1.1 and
10.1.2 p91, Figure 10-2); `SLAA842-CapTIvate-Selection.pdf` (Rev B: Table 8
p9, Table 10 p11, Step 4a.3 p12, Step 4c.3 p19); `SLAA843-Sensitivity-SNR.pdf`
(Rev A: Table 1 p7); `SLAU550-MSP430-FRAM-BSL.pdf`; `TI-TPD1E10B06-datasheet.pdf`
(features p1, electrical characteristics p5); `Epson-FC-135-32.768kHz.pdf` p1;
ADRs 0002, 0003, 0004, 0005, 0012, 0013; Q1, Q17, Q22, Q24; the faceplate
board, BOM and fab gerbers; `fw-touch/`.

## 1. U1, every pin

Fitted part: MSP430FR2675TPT (BOM, LCSC C2052972), LQFP-48 PT. Pin numbers
and functions from Figure 7-1 and the PT column of Table 7-2; "symbol" is
the pin name the board's own pads carry.

| PT pin | function used (datasheet) | symbol pin name | net | verdict |
|---|---|---|---|---|
| 1 | DVCC | DVCC | `P3V3_MSP430` | CLEAN |
| 2 | RST/NMI/SBWTDIO | ~RST/NMI/SBWTDIO | `MSP_RST` | CLEAN |
| 3 | TEST/SBWTCK | TEST/SBWTCK | `MSP_TEST` | CLEAN |
| 4 | P1.4/UCA0TXD (BSL transmit, Table 9-4) | P1.4/UCA0TXD/... | `MSP430_TXD` | CLEAN |
| 5 | P1.5/UCA0RXD (BSL receive) | P1.5/UCA0RXD/... | `MSP430_RXD` | CLEAN |
| 23, 24, 25, 26 | CAP0.0-0.3 (P3.0, P3.3, P2.3, P3.4) | same | `CAP0.0`-`CAP0.3` | CLEAN |
| 27, 28, 29, 30 | CAP1.0-1.3 (P3.1, P2.4, P2.5, P2.6) | same | `CAP1.0`-`CAP1.3` | CLEAN |
| 31 | VREG | VREG | `MSP_VREG` | CLEAN |
| 32, 33, 34, 35 | CAP2.0-2.3 (P3.7, P4.0, P4.1, P4.2) | same | `CAP2.0`-`CAP2.3` | CLEAN |
| 36, 37, 38, 39 | CAP3.0-3.3 (P2.7, P3.5, P3.2, P3.6) | same | `CAP3.0`-`CAP3.3` | CLEAN |
| 46 | XOUT (P2.0) | P2.0/XOUT | `MSP_XOUT` | CLEAN |
| 47 | XIN (P2.1) | P2.1/XIN | `MSP_XIN` | CLEAN |
| 48 | DVSS | DVSS | `GND` | CLEAN |
| 6-22, 40-45 (23 pins) | general I/O, unused | names match Table 7-1 (e.g. 6 P1.6/UCA0CLK/TA1CLK/TDI/TCLK/A6) | `unconnected-*`, no copper | CLEAN in hardware |

The PT package has one supply pair, DVCC/DVSS (Table 7-2); there is no AVCC
or exposed pad. Unused pins: Table 7-4 (p23) says "Px.0 to Px.7: Open,
switched to port function, output direction (PxDIR.n = 1)". The board leaves
them open, which is the hardware half; the other half is firmware, and
`fw-touch` does not do it yet (section 7 below).

## 2. CapTIvate

Each pad's four lines land on four different blocks at the same element
index (`PADp_RXn` to `CAPn.(p-1)` through R*pn*):

| pad | RX0 | RX1 | RX2 | RX3 |
|---|---|---|---|---|
| E1 | CAP0.0 (23) | CAP1.0 (27) | CAP2.0 (32) | CAP3.0 (36) |
| E2 | CAP0.1 (24) | CAP1.1 (28) | CAP2.1 (33) | CAP3.1 (37) |
| E3 | CAP0.2 (25) | CAP1.2 (29) | CAP2.2 (34) | CAP3.2 (38) |
| E4 | CAP0.3 (26) | CAP1.3 (30) | CAP2.3 (35) | CAP3.3 (39) |

A block measures one element at a time, so a pad's four elements are
measured together in one cycle, one per block, which is what ADR 0002 chose
the part for. This agrees with `docs/pin-allocation.md` and
`fw-touch/docs/pin-assignment.md`. CLEAN.

Along each pad, from the board's own copper, the elements run RX0 (x
62-114), RX1 (62-168), RX2 (116-222), RX3 (170-276), RX0 (224-276): five
segments, four complementary zones, RX0 at both ends as one net (ADR 0003).
Same on all four pads. CLEAN.

| item | source | ours | verdict |
|---|---|---|---|
| VREG capacitor | SLASEO5D §4 and SLAA842 Table 10 row 1: 1 uF, ESR at most 200 mohm, next to VREG | C3 1 uF 0805 MLCC (C28323), 3.07 mm from pin 31 | CLEAN (an MLCC of this size is far under 200 mohm; no datasheet for C28323 is committed) |
| series resistors | SLAA842 Table 10 row 3: 470 ohm; Step 4a.3: works with a TPD1E10B06 | R11-R44, 470 ohm, 16 | CLEAN |
| network order | SLAA842 Figure 4; ADR 0004 | electrode, TVS to GND, then R, then pin; TVS pin 1 1.2 mm from its R on every line | CLEAN |
| resistor to pin | TI: "as close as possible to the microcontroller" (ADR 0004) | 4.1 to 23.9 mm | note: the network sits in a grid in the right margin |
| total electrode capacitance | SLAA842 Table 8: 300 pF at a 4 MHz conversion | a few tens of pF per element (estimate below) | CLEAN |
| MCU on the sensor board, only power and comms through the connector | SLAA842 Step 4c.3 | yes | CLEAN |

### TVS capacitance against sensitivity (QUESTION)

The TPD1E10B06 adds 12 pF typ to every element (p5, CIO at 2.5 V, 1 MHz).
SLAA843 Table 1 (p7) defines sensitivity as S = Ct / Cp, so whatever an
element's capacitance is without the TVS, call it Cp0, the TVS scales the
signal by Cp0 / (Cp0 + 12). The faceplate puts no ground plane under a pad
(L3 is kept out; README "Layout") and the gold face stops 1.9 mm from each
pad (ADR 0013), so Cp0 is the pad's coplanar fringe to the face, its own L2
bus, the run to the network and the pin. None of that is measured. At Cp0 =
10 pF the TVS takes 55% of the signal; at 20 pF, 37%; at 40 pF, 23%. All
16 elements carry it equally (ADR 0004), so it costs sensitivity, not
linearity, and bare copper under a finger gives a large Ct. Measure on the
first board: counts on one element with its TVS lifted against its
neighbours. If the margin is thin, a lower-capacitance clamp is a BOM
change, not a respin.

## 3. Crystal (Q22)

| item | source | ours | verdict |
|---|---|---|---|
| crystal | Epson p1: 32.768 kHz, CL 12.5 pF, R1 (ESR) 70 kohm max, C0 1 pF typ | Y1 FC-135 12.5 pF, on the BOM (C32346) | fitted, so Q22's "whether it is populated is still open" is stale |
| supported load | 8.12.3.1 (p32) note 7: 3.7, 6, 9 and 12.5 pF supported; shunt C0 at most 1.6 pF | 12.5 pF; C0 1 pF | CLEAN |
| load caps | CL = C5 C6 / (C5 + C6) + CL,eff (1 pF integrated, 8.12.3.1) + stray | 22 pF C0G each: 11 + 1 = 12.0 pF, plus about 0.5 pF of trace stray, about 12.5 | CLEAN |
| drive margin | 8.12.3.1: oscillation allowance 200 kohm at LFXTDRIVE 3, CL,eff 12.5 pF (already a factor of 5 below the oscillator, note 5) | ESR 70 kohm max | CLEAN; firmware must set LFXTDRIVE = 3 |
| footprint keep-out | Epson p1 §4: "Do not design any circuit patterns in the shaded area" | nothing on B.Cu between the pads; one L2 line (`PAD4_RX0`) passes under the crystal with the L3 ground plane between | CLEAN, with that note |
| trace length | 8.12.3.1 note 1: keep XIN/XOUT traces short, nothing under or beside the pins | Y1 7.2 mm from XIN, 10.0 mm from XOUT; only GND copper within 1 mm of either pin | note: longer than ideal, inside the load-cap budget above |
| is it needed | REFO 32768 Hz +-3.5% over -40 to 105 C (8.12.3.4); the DCO with FLL is +-1% at room temperature (p1) | the UART link runs from the FLL | an 8E1 frame is sampled 10.5 bit times after its start edge, so the two clocks may differ by under 4.8% in theory, less after edge and sampling error; +-3.5% from one end leaves little, so the crystal earns its place; CLEAN |

## 4. Decoupling, reset, programming access

| item | source | ours | verdict |
|---|---|---|---|
| DVCC | 10.1.1 (p91): 10 uF + 100 nF low-ESR ceramic, "within a few millimeters"; CDVCC 4.7-10 uF (p24) | C2 100 nF 3.1 mm from pin 1 (GND end 4.5 mm from pin 48); C1 10 uF 9.0 mm | CLEAN for C2; C1 is further than "a few millimeters", low |
| reset | Table 7-4: 47k pull-up with 10 nF, or 1.1 nF max when Spy-Bi-Wire is used; SLAA842 Table 10 row 5: 47k + 1 nF | R1 47k, C4 1 nF C0G +-5% (1.05 nF max) | CLEAN |
| TEST | Table 7-4: open, internal pull-down always on | open (TP1 only) | CLEAN |
| BSL | Table 9-4 and SLAU550, section 9 | P1.4/P1.5 on the runtime UART; blank-device entry | CLEAN (section 9) |
| Spy-Bi-Wire pads | ADR 0005: TEST, RST, 3V3, GND | TP1 `MSP_TEST`, TP2 `MSP_RST`, TP3 `P3V3_MSP430`, TP4 `GND`; TP5/TP6 on the UART | CLEAN; reachable only with the faceplate off |
| CAPTIVATE-PGMR through `J1` | ADR 0005 maps ribbon pins to PGMR 20-pin positions 7, 8, 9, 10, 18, 19 | not checkable: the CapTIvate Technology Guide's PGMR chapter is not in `datasheets/` | BLOCKED |

## 5. Exposed gold, ESD and Q24

- **Electrode strike.** Electrode, then the TVS to ground, then 470 ohm, then
  the pin: TI's own scheme (SLAA842 Step 4a.3). The TVS is bidirectional
  (p1), rated IEC 61000-4-2 level 4, +-30 kV contact (p1, p4), with VRWM 5.5
  V above any CapTIvate electrode voltage. CLEAN.
- **Face strike.** The face is one GND zone on F.Cu, joined to L3 and the TVS
  grounds by the margin's vias (ADR 0013). It returns to the main board two
  ways: the five ribbon grounds, and the six pot nuts, which sit on the gold
  and clamp it to the pot bushings (ADR 0013, Consequences), whose frame
  tabs are `GND` on the main board (netmap `RVn.7`, `RVn.8`). That second
  path is short and six-fold. It assumes the Alpha bushing is continuous with
  its tabs; beep one at bring-up. CLEAN pending that.
- **Q24.** Every track and via under the four pads was sorted by net: under
  pad *p* there is only `PADp_*` copper (L2 buses, the L3 RX0 return, the bar
  vias), nothing from another pad, no ground fill, no part. The nearest
  foreign copper is TP4 (GND, B.Cu) 0.05 mm outside pad 3's lower edge and TP1
  0.13 mm outside pad 4's upper edge, both on the back. So the board is what
  Q24 assumes; whether same-cycle shielding works is Q24's own measurement.

## 6. ADRs 0002-0004, 0012, 0013 against the board

| ADR | claim | board | verdict |
|---|---|---|---|
| 0002 | four parallel blocks, 16 self-cap IO | 16 electrode lines, four blocks, one pin each per pad | CLEAN |
| 0003 | 5 segments, 4 zones, RX0 both ends as one net | as measured above | CLEAN |
| 0004 | 16 TVS and 16 resistors, TVS on the electrode side, both near the MCU | as built | CLEAN |
| 0012 | no LEDs, no 5 V on the cable | none on the BOM; `J1` as section 9 | CLEAN |
| 0013 | gold face on GND, 1.9 mm from each pad, nuts on the gold | F.Cu GND fill never enters a pad rectangle; nuts per ADR | CLEAN |

## 7. `fw-touch` against the netmap

`fw-touch` is a skeleton: no Design Center output exists in
`captivate/generated/`, so there is no generated pin or sensor
configuration to diff. What the hand-written files say:

| file | says | board | verdict |
|---|---|---|---|
| `docs/pin-assignment.md` | RX*n* to E0*n*, pad *p* on `CAP0.(p-1)`-`CAP3.(p-1)`, one pin per block | matches | CLEAN |
| `design-center/README.md` | "Put each slider's four elements in **one measurement block** ... exactly one per slider" | each slider spans all four blocks | DEFECT, doc: the opposite of the board, and of `pin-assignment.md` (corrected there 2026-09-28) |
| `README.md`, `design-center/README.md` | generate the electrode assignment in Design Center first, then lay the PCB out to match | the PCB is finished | DEFECT, doc: Design Center must now be set to the board's assignment, not left to auto-assign |
| `docs/pin-assignment.md` serial table; `src/main.c` `LinkInit`, `IrqInit` | UART or I2C, an IRQ GPIO, BSL by RST + TEST GPIOs; the eUSCI sharing question "UNVERIFIED, blocks layout" (Q2) | UART only (P1.4/P1.5), no I2C, no IRQ line, TEST not driven from the Daisy; Q2 is resolved | DEFECT, doc |
| `docs/bsl-protocol.md` | "Hardware cost: two wires, RST and TEST from the Daisy" | blank-device entry, no TEST wire (section 9) | DEFECT, doc |
| `README.md`, `src/main.c` | resolution over 175 mm | pads are 216 mm (ADR 0003) | DEFECT, doc |
| `src/main.c` | no unused-pin setup, no XT1 setup | Table 7-4 wants the 23 unused pins as outputs; Y1 needs P2.0/P2.1 as XOUT/XIN and LFXTDRIVE 3 | note for the firmware |

## Verdicts

| item | verdict |
|---|---|
| U1 every pin against Figure 7-1, Table 7-2 and the symbol | CLEAN |
| unused pins open in hardware | CLEAN |
| CapTIvate block and element assignment | CLEAN |
| electrode order along each pad | CLEAN |
| VREG, DVCC, reset, TEST | CLEAN |
| C1 10 uF at 9 mm | note, low |
| series resistors, ESD network order | CLEAN |
| TVS capacitance against sensitivity | QUESTION |
| crystal: part, load caps, drive, keep-out | CLEAN |
| Q22 "populated still open" | DEFECT, doc |
| gold face ESD return through the pot nuts | CLEAN, continuity to check |
| Q24 precondition: only own-pad copper under each pad | CLEAN |
| PGMR pin map through `J1` | BLOCKED |
| `fw-touch` docs and comments | 5 DEFECT, doc |

## Defects, ranked

Nothing here would kill the board.

1. **QUESTION, could cost sensitivity:** the TVS's 12 pF on every element may
   be a large share of each element's capacitance, cutting signal by a
   quarter to a half (SLAA843 Table 1). Measure with one TVS lifted.
2. **Doc, could break the firmware build:** `fw-touch/design-center/README.md`
   tells whoever builds the Design Center project to put each slider in one
   block, and both READMEs still say the PCB follows Design Center. A sensor
   configured that way will not match the board. The board's assignment is
   the table in section 2; Design Center has to be set to it.
3. **Doc:** `fw-touch` still describes I2C, an IRQ line, RST + TEST BSL wires,
   the eUSCI sharing question as open, and a 175 mm pad.
4. **Doc:** Q22 says population of Y1 is open; the BOM fits it.
5. **Note:** C1 sits 9 mm from DVCC where TI asks for a few millimetres; C2,
   the one that matters at high frequency, is at 3 mm.
6. **Note:** firmware must set the 23 unused pins as outputs and run XT1 at
   LFXTDRIVE 3.
