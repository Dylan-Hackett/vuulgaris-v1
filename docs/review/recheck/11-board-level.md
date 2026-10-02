# 11: Board level: DRC, fab rules, power copper, planes, BOM and CPL

Both boards. Sources: `hardware/kicad/DRC.rpt`, `hardware/faceplate/DRC.rpt`,
both `.kicad_pcb` and `.kicad_pro`, `hardware/kicad/fab/`,
`hardware/faceplate/fab/`, the two fab packages, `tools/mkcpl.py`,
`tools/mkbom.py`, the section 2 rail budget, ADR 0013. Geometry was measured
with a scratch script (shapely) over pads, tracks, vias, zone fills and
Edge.Cuts read straight from the board files; custom-shape pads (J11's VBUS
and shell pads) are not modelled, so KiCad's DRC stays the authority there.

**JLCPCB's published capabilities could not be read:** `jlcpcb.com` is
blocked by this environment's network policy. Every "against JLC" column
below is therefore BLOCKED except where the project itself records a JLC
figure (ADR 0013: copper to edge 0.2 mm, black mask dam 0.13 mm). The
tightest instance of each rule is measured either way, ready to compare.

## 1. DRC reports

| board | report created | last board commit | errors | unconnected | warnings by type | verdict |
|---|---|---|---|---|---|---|
| main | 2026-10-02 12:23:08 | 2026-09-26 22:56 (5cf3909) | 0 | 0 | 199 silk_over_copper, 27 silk_overlap, 24 silk_edge_clearance, 6 lib_footprint_mismatch (U1, D3, U101, U201, J1, C30) | CLEAN: every bucket is silk or library override |
| faceplate | 2026-10-02 12:23:09 | 2026-09-29 14:55 (2d764e5) | 0 | 0 | 31 silk_over_copper | CLEAN |

Both reports are newer than their boards, so they are trusted. The six
library mismatches are not pad changes: section 8 found every board pad
identical to its library copy.

## 2. Design rules and the tightest instance on the board

| rule | main `.kicad_pro` | main, tightest found | faceplate `.kicad_pro` | faceplate, tightest found | JLC |
|---|---|---|---|---|---|
| copper clearance | 0.2 (all classes) | 0.1995, track to via, In1 (ENC1_B / ENC2_A); 0.200 track to track, pad to pad | 0.2; CapTIvate class 0.15 | 0.150 track to track (In1, CapTIvate); 0.152 pad to track; 0.200 between comb teeth | BLOCKED |
| track width | class 0.25 to 1.5 | 0.1874 (`BBD_AC_R`, `EXT_AMP_IN_L`, B.Cu) | class 0.15 to 0.3 | **0.1124** (`CAP3.3`, B.Cu, 2 x 2 mm near U1), under its own class | BLOCKED |
| via | 0.8 / 0.4 | all 486 are 0.8 / 0.4, annular 0.20 | 0.6 / 0.3; CapTIvate 0.5 / 0.3 | 781 at 0.5 / 0.3 (annular **0.10**), 31 at 0.6 / 0.3 | BLOCKED |
| PTH annular | | 0.20 (J11 shell slots 0.8 x 1.2-1.5 in 1.2 pads) | | none (no PTH) | BLOCKED |
| hole to hole | 0.25 | 0.60 edge to edge, different nets (two vias at sheet 163.8, 99.1); 0.60 same net | 0.25 | 0.62, different nets | BLOCKED |
| copper to edge | **0.0** | **0.0005**: the In2 GND plane, along 874 mm of outline; next is a track at 0.227 (`CV_IN_JACK`, In1) | 0.3 | 0.2975 (In2 GND) | ADR 0013: 0.2. Main board **DEFECT** |
| hole to edge | | 1.0 (J2 pin) | | 4.96 | BLOCKED |
| mask dam | 0 expansion | no dam under 0.2 between pad openings | per-pad | **0.10** between U1's LQFP pads (44 places, NSMD 0.05 per TI) | ADR 0013: black 0.13. Faceplate QUESTION |
| silk stroke | 0.15 default | 0.06 (easyeda2kicad's pin-1 dots, e.g. C105) | | 0.06 (same dots) | BLOCKED |
| silk text | min 0.8 | 0.9 high, 0.15 stroke (TP labels) | min 0.8 | 0.8 high, 0.12 stroke (reference designators) | BLOCKED |

Outline: the main board's Edge.Cuts polygonises into one closed outline
(33,582.6 mm2) and one closed inner cutout (286.1 mm2: 24 x 12 less four 1.5
mm corner radii). The faceplate's gives the outline, the OLED window (2,036
mm2) and 27 closed holes. CLEAN.

**The main board's GND plane runs to the routed edge.** `vuulgaris.kicad_pro`
sets `min_copper_edge_clearance` to 0, so the In2 fill was poured right up to
Edge.Cuts: within 0.2 mm of the outline for 874 mm, which is the whole
perimeter and the J12 cutout. The faceplate's file carries 0.3 for exactly
this reason (ADR 0013: "JLC wants 0.2. Without it, the fill ran to every
hole's edge"). Expect JLC's CAM to query it or pull the plane back on its
own; built as drawn, plane copper is exposed along every edge. Setting the
rule and refilling is a board change, so it is the user's (CLAUDE.md:
scripted refill or Pcbnew, then regenerate the fab package).

## 3. Power copper against the rail budget

Rail currents from section 2: input 1.2-1.6 A at 5 V (2.3 A at the DKM10's
full load, its spec p2), +12 V up to about 445 mA, -12 V 150-250 mA, `P5V`
about 200 mA (OLED and MSP430 regulators), the rest tens of mA. Capacities
are IPC-2221 at 10 C rise, 1 oz outer; the fab README does not state the
inner copper weight, so inner layers are taken at 0.5 oz, the worst case.

| net | narrowest | where | carries | capacity of the neck | vias | verdict |
|---|---|---|---|---|---|---|
| `VBUS` | **0.25 mm, F.Cu** | 2.7 mm from `J11.B4A9` down to the 0.6 mm run, and a 0.25 mm loop (about 6 mm) joining `J11.A4B9` to it | all of the input current | 0.88 A; about 40 C rise at 1.6 A by IPC-2221, which overstates a short stub tied to the connector | 1 x 0.4 drill | **DEFECT**: the net class asks 1.5 mm; the whole input runs through 0.25 mm and one via |
| `VBUS_F` | 0.8 B.Cu, then 1.5 In1 | F1 to U7: 59.5 mm on In1 | all of the input | 0.97 A at 1.5 mm inner, 0.5 oz | **1** x 0.4 drill | QUESTION: one 0.4 mm via and an inner run for up to 2.3 A |
| `POS12V_RAW` | 0.6 | 39 mm on In1 | up to ~445 mA | 0.50 A inner | 1 | CLEAN, close |
| `NEG12V_RAW` | 0.6 | 21 mm on In1 | 150-250 mA | 0.50 A inner | 2 | CLEAN |
| `POS12V` | 0.45 (0.6 elsewhere) | stubs into the SOIC-14 supply pins | distributed, 445 mA total | 1.34 A outer; 0.6 inner 0.50 A | 23 | CLEAN |
| `NEG12V` | 0.36 for 0.5 mm | into U401.11 | distributed | 1.14 A | 19 | CLEAN |
| `P5V` | 0.5 | 269 mm on In1 | about 200 mA | 0.44 A inner | 2 | CLEAN for heat; about 0.1 V drop at 0.5 oz, inside the LDOs' headroom (section 2) |
| `P5V_BBD`, `P3V3_DAISY` | 0.375 | short necks at C41 and R508 | tens of mA | 1.17 A | 7, 8 | CLEAN |
| `P3V3_OLED`, `P3V3_MSP430`, `P5V_OLED`, `P5V_MSP` | 0.5 | | up to 160 mA | 0.44 A inner, 1.45 A outer | 1-2 | CLEAN |

## 4. Planes and return paths

Stack-up (fab README; gerber X2 FileFunction): L1 `F.Cu` signal; L2 `In1.Cu`
signal and power (most of ±12 V, `P5V`); L3 `In2.Cu`, filed as
`vuulgaris-GND.gbr`, "Copper,L3,Inr"; L4 `B.Cu` signal.

- **In2 is one plane**: one island of 30,724 mm2, 91.5% of the board, plus
  eight 1.5-2.1 mm2 slabs that are not floating (each sits between two GND
  pins of U1, RV1, RV5 or J12 and joins them).
- **Its holes** are merged antipads around through-hole pin rows: the Patch SM
  header rows (up to 64 mm2), J12, the pots, the DIP BBDs, the test points.
  Nothing cuts across the board.
- **Sensitive runs**: the BBD clocks cross only the antipads of their own
  MN3205, CD4046 or test point, at most 1.9 mm at a time. Audio and CV nets
  (`AUDIO_IN_*`, `GATE_IN`, `TIME_CV`) cross the Patch SM's header slots on
  their way to its pins; `TIME_CV` runs 9.7 mm along one. CLEAN, with that note.
- **Converter return**: U7's -Vin (2) and Common (4) are through-hole into the
  plane. Its input caps C29-C31 sit at the USB-C, 55-69 mm away; the DKM10 has
  its own Pi input filter (spec p3, "INPUT FILTER Pi type"), so this is
  CLEAN, but the input loop's inductance is the 59.5 mm inner run above.

## 5. Decoupling distance

Nearest capacitor on the same rail to each IC supply pin, main board:

| IC pins | nearest | verdict |
|---|---|---|
| every TL07x/TL08x, OPA1688, CD4046, MN3205 supply pin | 2.4-4.9 mm, a 100 nF each | CLEAN |
| U3 VDD (pin 9) | C26, 4.0 mm | CLEAN |
| U4 VDD (pin 9) | C26, 33.7 mm | QUESTION, already section 4 |
| U5 out / tab | C21, 9.3 / 3.6 mm | CLEAN |
| U6 in, out | 7.9, 6.3-7.1 mm | CLEAN |
| U8 (AMS1117-5.0) out / tab | C41 100 nF 10.3 / 16.2 mm; C42 10 uF 13.9 / 19.8 mm | note: far for the cap the regulator's stability depends on (section 2's QUESTION) |
| U1 Patch SM A5 (+12 V), A1 (-12 V), A10 (3V3) | 56.9, 47.7, 21.9 mm | note: Electrosmith's power application example (Figure 1.11) says "No bypass caps necessary" |
| U7 in / +out / -out | 56.6 / 38.7 / 16.4 mm | note: internal Pi filter; output caps are the LC filter's |

Faceplate: section 10 (C2 3.1 mm, C1 9.0 mm, C3 3.1 mm).

## 6. Analog hygiene

- **BBD clock beside audio**: the longest close run is `BBD_CLK_L` within 1 mm
  of `BBD_IN_L` for 6.0 mm on F.Cu, at the MN3205's own pins; everything else
  is under 3 mm. CLEAN.
- **Clocks under the faceplate**: the electrodes have no ground under them by
  design (ADR 0013) and look down 11.6 mm at the main board's top. Of the
  BBD clocks, 15.8 mm (`BBD_CLK_L`), 26.7 mm (`BBD_CLK_R`) and 7.4 mm
  (`BBD_CLKN_R`) run on F.Cu or In1 under the pad block, unshielded from it;
  the rest is on B.Cu behind the In2 plane. Also there: `I2C_SCL` 78 mm,
  `MSP430_RXD`/`TXD` 64/57 mm, `I2C_SDA` 42 mm, `OLED_MOSI` 38 mm, `SD_CLK` 10
  mm. Note for Q1/Q17: on the bench, compare touch counts with the BBD clocks
  running and stopped (`GATE_OUT_2` drives the inhibit).

## 7. Gerber packages

| item | main | faceplate | verdict |
|---|---|---|---|
| files in the gerber zip | 15: F/B Cu, In1, GND (In2), F/B Mask, F/B Paste, F/B Silkscreen, Edge_Cuts, PTH.drl, NPTH.drl, two drill maps | 15, same set with In2_Cu | CLEAN |
| layer identification | X2 FileFunction L1 Top, L2 Inr, L3 Inr (`GND.gbr`), L4 Bot; job file agrees | same | CLEAN |
| drills | plated and non-plated separate | same | CLEAN |
| generated after the last board change | gerbers 2026-09-26 22:56:27, in the board's own commit 5cf3909 | package 3ef52f1 at 15:26, after the board's 2d764e5 at 14:55 | CLEAN |
| package zip vs `fab/` zip | byte-identical | byte-identical | CLEAN |

The main fab README names 744f16b, the parent of 5cf3909: `mkfab.py` records
HEAD before the commit it lands in. Harmless.

## 8. BOM against board

| check | main | faceplate | verdict |
|---|---|---|---|
| every fitted ref once | 301 refs on 72 lines, no duplicates; the 15 TH test points are bare holes and rightly absent | 44 refs on 11 lines; TP1-TP6 and E1-E4 are copper | CLEAN |
| footprint per ref | all 301 match the board | all 44 | CLEAN |
| value per ref against `values.json` | all match (RV2/3/4/6 share one line whose comment lists their labels) | all match | CLEAN |
| LCSC package against footprint | settled per ref in section 1 | section 1 | CLEAN |
| hand-fit parts blank | RV1-RV6, U1, SW1/SW2, U101/U201, VT301-VT402 blank with notes | none | CLEAN for those |
| hand-fit parts blank | **U7 (C6934792) and DS1 (C5139768) carry LCSC numbers in the uploaded `vuulgaris-BOM-jlc.csv`**, though the fab README says to source U7 elsewhere and fit DS1 by hand, and the notes that say so are not in the file JLC reads | | DEFECT, low (CLAUDE.md: hand-fit parts get a blank LCSC number) |

## 9. CPL

Both CPLs were recomputed from the boards with `mkcpl.py`'s stated rule
(top: t + d; bottom: 180 - t + d; d = -90 for `SOIC-14_3.9x8.7mm_P1.27mm`,
0 otherwise) and every row agrees: 316 of 316 main, 44 of 44 faceplate,
sides and positions included (Y negated, the same frame as the gerbers).
The algebra of the bottom rule checks: with KiCad's flip a mirror about X
and JLC reading bottom rotations mirrored about Y, M_y R(t) M_x R(d) = R(180
- t + d).

What cannot be proven here is the premise underneath: that each footprint's
zero matches the model JLC holds for its LCSC part, and that JLC reads bottom
rotations that way. The SOIC-14 offset and the faceplate's d = 0 were
checked by the author against EasyEDA's API (`mkcpl.py` docstring), which
this environment cannot reach either. So pin 1 is unproven, until JLC's
placement preview shows it, for every JLC-placed polarised part:

- main: U3, U4, U5, U6, U8, U9, U10, U102, U103, U104, U106, U202, U203,
  U204, U206, U301, U302, U401, U402, Q1, Q2, D1, D2, D3, D103-D107,
  D203-D207, D301, D401, C32, C33, C36, C37, J1 (microSD), J11, J12 (key);
- faceplate: U1 (MSP430), J1 (key). D11-D44 are bidirectional and Y1 is
  not polarised.

## Verdicts

| item | verdict |
|---|---|
| DRC reports fresh, 0 errors, 0 unconnected, warnings all silk or library | CLEAN |
| main-board GND plane to the board edge | DEFECT |
| rules against JLC's published limits | BLOCKED (jlcpcb.com unreachable) |
| faceplate LQFP mask dams 0.10 under black 0.13 | QUESTION, low |
| faceplate 0.1124 mm `CAP3.3` track, 0.10 via annular | QUESTION, low |
| VBUS 0.25 mm neck and single via | DEFECT |
| VBUS_F single via, inner run | QUESTION |
| other rails | CLEAN |
| planes and return paths | CLEAN |
| decoupling | CLEAN, with notes (U4 is section 4's) |
| analog hygiene | CLEAN, with a bench note |
| gerber packages | CLEAN |
| BOM: U7 and DS1 carry LCSC numbers | DEFECT, low |
| CPL against the board and its rule | CLEAN |
| CPL pin 1 against JLC's models | BLOCKED until JLC's preview |

## Defects, ranked

Nothing here would kill the board outright.

1. **DEFECT, could hold the order:** the main board's In2 GND plane is poured
   to the routed edge all round, because its copper-to-edge rule is 0. Set it
   (0.3, as the faceplate has), refill, rerun DRC, regenerate the fab package.
2. **DEFECT, runs hot under load:** every amp of USB input leaves `J11` through
   2.7 mm of 0.25 mm track (and the second VBUS pad joins through more 0.25),
   then crosses layers through one 0.4 mm via, against a 1.5 mm net class.
   Widen after the pad row and add vias; this is hand-routing, the user's.
3. **QUESTION:** `VBUS_F` reaches U7 through one 0.4 mm via and 59.5 mm of
   inner copper of unstated weight. Add vias at F1; confirm the stack-up
   ordered (inner 0.5 or 1 oz).
4. **DEFECT, low:** U7 and DS1 carry LCSC numbers in the JLC BOM though both
   are hand-fit; blank them or deselect them at order time.
5. **QUESTION, low:** the faceplate's LQFP mask dams (0.10) are under the
   black-mask minimum the project records (0.13); JLC will likely open each
   side as one gang. Its 0.1124 mm `CAP3.3` segment and 0.10 mm via rings
   need JLC's live limits, which this environment cannot read.
6. **BLOCKED:** pin 1 of every JLC-placed polarised part against JLC's own
   models; check each in the placement preview before paying.
