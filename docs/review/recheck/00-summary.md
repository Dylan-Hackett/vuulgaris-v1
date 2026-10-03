# 00: Recheck summary, October 2026

Sections 01-11 in this directory; `PROGRESS.md` has one line each. Branch
`claude/epic-lamport-gbvvd4` (the runbook names `recheck/2026-10`; this cloud
session was assigned the other name). Report only: nothing in `netmap.json`,
`values.json`, `design.py`, any `.kicad_*` file or the fab packages was
touched.

Gate (section 1): netmap = schematic = board on both boards, 944/944 main
(316 refs, 223 nets) and 145/145 faceplate.

**No DEFECT kills either board. Two open items could:** the +12 V load
against the DKM10E-12's per-output rating (bench), and three inputs on
MCP23017 GPA7/GPB7 (a missing datasheet).

## 1. Defects, deduplicated

### Kills the board

None found.

### Degrades it

| # | defect | section | one-line fix | lands in |
|---|---|---|---|---|
| D1 | VTL5C3 LED pairs are reverse-biased about 10 V in normal use (inverted CV, CUTOFF low) against a 3.0 V absolute maximum per LED | 06 | a 1N4148W in series with each channel's LED string | netmap, values, design.py, then the board (routing is the user's) |
| D2 | main-board In2 GND plane is poured to the routed edge all round, 874 mm within 0.2 mm (copper-to-edge rule is 0) | 11 | set `min_copper_edge_clearance` 0.3, refill, DRC, regenerate fab | `hardware/kicad/vuulgaris.kicad_pro`, board, fab |
| D3 | all USB input current leaves J11 through 2.7 mm of 0.25 mm track (the second VBUS pad joins through more 0.25 mm), then one 0.4 mm via, against a 1.5 mm net class | 11 | widen VBUS once clear of J11's pad row; add vias on VBUS and at F1 on VBUS_F | board (hand-routing, the user's) |
| D4 | U1 silkscreen letters A/B/C/D sit on the wrong headers (A by D, B by C), since commit 4467882 | 03, 08 | restore the four `fp_text user` positions from the library footprint | board |
| D5 | C113/C120/C213/C220 are 1 uF X7R in the wet path where `bbd-mki.md` says film and "should not be substituted with X7R" | 05 | fit film (hand-fit, blank LCSC) or C0G-class parts, or change `bbd-mki.md` to accept X7R with a reason | values, `mkbom.py` CURATED, or a doc |
| D6 | D3's SMA land: pads 2.0 long and 2.4 apart against Littelfuse's 2.10 min and 2.30 max | 08 | pads 2.1 long or longer, gap at most 2.3 | footprint `SMA_L4.3-W2.6-LS5.2-RD` |
| D7 | U3/U4 SO-28 land: pads 2.3 long against Microchip's 2.00 max, rows at 10.12 against 9.40 | 08 | Microchip's pattern: 0.6 x 2.0 at C 9.40 | footprint `SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL` |
| D8 | U7 (C6934792) and DS1 (C5139768) carry LCSC numbers in the uploaded `vuulgaris-BOM-jlc.csv` though both are hand-fit | 11 | blank them with a NOTE, as the pots are | `mkbom.py` |

### Cosmetic or doc

| # | defect | section | fix lands in |
|---|---|---|---|
| C1 | 942/309/219 connection, ref and net counts (today 944/316/223) | 01 | runbook, `review-packet.md`, `REVIEW-INDEX.md`, `tools/blockview.py` |
| C2 | `REVIEW-INDEX.md` datasheet rows for C29 and RV1-RV6 predate those parts | 01, 07 | `datasheets/REVIEW-INDEX.md` |
| C3 | vactrol LED drive listed as a +12 V load (it sinks to -12 V); +12 V never summed against the 416 mA per-output rating | 02 | `docs/power-usbc-dkm.md` |
| C4 | ADR 0009's ADC allocation no longer describes the board | 03 | ADR 0009 (superseded marker) |
| C5 | Q8 and Q15 describe pots and pin uses that no longer exist | 03 | `docs/notes/open-questions.md` |
| C6 | "route all 6 SD pins and pick the width in software" | 03 | `fw-daisy/README.md` |
| C7 | three comments: CV outs "drive the LPG vactrols", an IRQ line, BSL over RST + TEST | 03 | `fw-daisy/src/main.cpp` |
| C8 | four buttons and ten parameter encoders (the board has six and eight) | 04 | `docs/pin-allocation.md` |
| C9 | "RESOLVED: J1 mirroring" says J1 is stored identical to the library; it is y-negated (the conclusion holds) | 04 | `docs/design-state.md` |
| C10 | prose and diagram give C110 3.3 uF and C119 15 nF; its BOM table says 10 uF and 10 nF | 05 | `docs/bbd-mki.md` |
| C11 | SW1 described as "VCF/VCA"; VCA mode is not built | 06 | `mockups/generate-faceplate.py` |
| C12 | pot footprint named `RES-ADJ-TH_RK09L1240A12` on an Alpha RD902F | 07 | footprint name (and C2) |
| C13 | VTL5C3 footprint description and silk give 9.9 x 8.13; lying flat the part is up to 9.91 across and 8.13 tall | 08 | footprint `VACTROL-TH_VTL5C3` |
| C14 | C36/C37 listed at 7.8 mm tall; the part is 6.3 x 5.4 | 08 | `hardware/faceplate/README.md` §2 |
| C15 | "U1 is on the BACK now"; it is on F.Cu | 08 | `hardware/kicad/tools/place.py` comment |
| C16 | "nothing on the main board drives RST any more"; U4 GPB3 does | 09 | ADR 0005 |
| C17 | "put each slider's four elements in one measurement block"; the board spans four blocks per slider | 10 | `fw-touch/design-center/README.md` |
| C18 | "generate in Design Center first, then lay out the PCB"; the PCB is done, Design Center must follow it | 10 | `fw-touch/README.md`, `fw-touch/design-center/README.md` |
| C19 | I2C link, IRQ GPIO, RST + TEST BSL GPIOs, and the eUSCI sharing question marked "UNVERIFIED, blocks layout" | 10 | `fw-touch/docs/pin-assignment.md`, `fw-touch/ccs/.../main.c` |
| C20 | "hardware cost: two wires, RST and TEST" | 10 | `fw-touch/docs/bsl-protocol.md` |
| C21 | resolution "over 175 mm"; the pads are 216 mm | 10 | `fw-touch/README.md`, `main.c` |
| C22 | Q22 says Y1 population is open; the BOM fits it | 10 | `docs/notes/open-questions.md` |

Count: **0 kill, 8 degrade, 22 cosmetic/doc.**

## 2. Open questions, ranked

| # | question | section | how it closes |
|---|---|---|---|
| Q-A | +12 V load 395-445 mA against the DKM10E-12's 416 mA per output; the Patch SM's draw is unpublished | 02 | measure +12 V on the first board before a production order |
| Q-B | AMS1117 (U5, U6, U8) on all-ceramic outputs; the sheet guarantees 22 uF tantalum. U8's caps also sit 10-14 mm away | 02, 11 | scope each output under load step; tantalum or a series resistor if it rings |
| Q-C | CD4046B drive against the MN3205's 500 ns edge and cross-point limits; S&H trigger margin on the same edge | 05 | V3205 sheet, or scope CP1/CP2 and TP-F |
| Q-D | ENC0 contacts run at about a tenth of ALPS's minimum current | 04 | 3.3k pull-ups on `ENC0_A/B/PUSH` (netmap, values) |
| Q-E | U4 has no capacitor within 33 mm | 04, 11 | a 100 nF at U4 VDD (netmap, board) |
| Q-F | LPG common-mode: U301C/D and U102A exceed the TL07x/TL08x C-grade common-mode range on +-12 V when both sources run hot; ADR 0011 quotes output swing instead | 06, 05 | keep levels per ADR 0011 and correct its stated limit |
| Q-G | U101 pin 7 below -0.3 V with dry above 8.7 V peak at full feedback | 05 | level discipline, as Q-F |
| Q-H | `VBUS_F` reaches U7 through one 0.4 mm via and 59.5 mm of inner copper of unstated weight | 11 | add vias; confirm the stack-up ordered |
| Q-I | Daisy UART TX may back-feed the MSP430 through `MSP430_RXD` on power-down, no series resistance, past its +-2 mA pin limit | 09 | scope the power-off; 2.2k series if real |
| Q-J | TPD1E10B06's 12 pF per element against electrode capacitance: 23-55% of signal depending on the unmeasured Cp | 10 | counts on one element with its TVS lifted |
| Q-K | U9 near 140 C at full headphone trim into 16 ohm | 07 | trim with it in mind; thermal check |
| Q-L | OLED logic driven at its 3.3 V absolute maximum | 04 | accept or a series resistor |
| Q-M | CUTOFF alone needs RT301/RT401 near their top for full open | 06 | bench trim |
| Q-N | 4.7 ohm headphone isolation into long-cable capacitance | 07 | scope with a long cable |
| Q-O | U104/U204 rows at 7.4 against TI's 7.0; one tolerance corner loses 0.25 mm of heel | 08 | footprint, at the next spin |
| Q-P | VTL5C3 LED leads up to 0.64 square (0.905 diagonal) in 0.9 holes; 12.7 mm pair spacing bends at the potting | 08 | 1.0 holes, 15.24 spacing next spin; meter the LED at fit |
| Q-Q | SW1/SW2 silk has no pin-1 mark; a half turn reverses the lever | 08 | silk mark |
| Q-R | faceplate LQFP mask dams 0.10 under the black-mask 0.13 the repo records; 0.1124 mm `CAP3.3` segment; 0.10 via annular | 11 | JLC's live limits; expect gang relief at U1 |
| Q-S | U4 GPB4-7/GPA2-3 and SD DAT1/DAT2 left floating | 01, 04 | firmware sets the MCP23017 pins as outputs; SD spec for DAT1/DAT2 |
| Q-T | OLED_RES on A9 likely held low while the bootloader runs: display dark until the application drives it, harmless if so | 03 | module schematic or a scope at first boot |

## 3. Blocked, and what unblocks each

| item | section | unblocks it |
|---|---|---|
| MCP23017 GPA7/GPB7 as inputs (`ENC4_B`, `ENC8_B`, `BTN4`) | 01, 04 | the current MCP23017 datasheet revision (Rev D or later) in `datasheets/`. **Moved off those pins 2026-10-03** (`fix-mcp23017-gpa7-gpb7.md`), so the board no longer depends on the answer; the datasheet is still not in the repo |
| F1 ASMD1812-300 ratings and land | 02, 08 | its datasheet PDF |
| L1/L2 BLM18PG121SN1D and FB1/FB2 current ratings | 02 | their datasheet PDFs |
| Patch SM, OLED module and MN3205 supply currents | 02 | bench measurement (none published) |
| +-12 V filter against the EasyEDA source | 02 | `~/Documents/origin2.2.eprj` on the Mac |
| MN3205 clock edge and cross-point | 05 | the V3205 datasheet, or a scope |
| Q1/Q2 SOT-23 land pattern | 08 | onsemi's CASE 318-08 outline PDF |
| Patch SM seated height under the MSP430 (ceiling 7.9 mm at the pots' low tolerance) | 08 | calipers on a soldered module; do not socket it |
| CAPTIVATE-PGMR pin map through `J1` | 10 | the CapTIvate Technology Guide PGMR chapter |
| every rule against JLC's published limits | 11 | `jlcpcb.com` in this environment's allowed network hosts, or a saved copy of the capabilities page |
| pin 1 of every JLC-placed polarised part against JLC's own models | 11 | JLC's placement preview at order time (list in section 11 §9) |
| SD DAT1/DAT2 floating | 01, 04 | the SD Physical Layer Simplified Specification |

## 4. Where a repo doc disagreed with its source

Every row of section 1's cosmetic table (C1-C22) is one. The cases where
the board is right and only the doc is wrong: C1, C2, C3, C4, C5, C6, C7,
C8, C9, C10, C11, C12, C14, C15, C16, C17, C18, C19, C20, C21, C22. C13 is a
footprint description wrong about its own part. D5 is the one place a doc is
right and the board departs from it. In addition, three statements were
checked against their sources and found right: the faceplate README's pin 1
and key analysis (section 9, both drawings), ADR 0013's nut bonding (section
10), and `mkcpl.py`'s rotation algebra (section 11).

## 5. Coverage

Every ref on both boards fell inside some section's block except the main
board's fifteen test points, TP1-TP15. They are bare through-hole pads with
no part; their footprints were swept in section 8 and every silk label
matches its net (TP1 +12V on `POS12V` through TP15 LPG ENV on `LPG_ENV`).
No net touches only uncovered refs. Faceplate: every ref in section 10, J1
also in 9.

## 6. Only a bench will settle

- +12 V current at full load, against 416 mA (Q-A); the Patch SM's 5 V draw.
- LDO stability with ceramics (Q-B).
- MN3205 clock edges and S&H timing (Q-C).
- `J7`-`J10`: beep one 1/4" jack (fab README).
- Pot directions; one Alpha bushing beeped to its tabs (the faceplate's ESD
  return runs through the six nuts, section 10).
- U9 temperature at full trim into 16 ohm (Q-K); 4.7 ohm into a long cable.
- VBUS neck temperature at full load, if D3 is not fixed first.
- Power-off back-feed on `MSP430_RXD` (Q-I).
- Patch SM seated height with calipers, before the faceplate goes on.
- VTL5C3 LED polarity with a meter at fit.
- First MSP430 flash: blank-device BSL at 9600 8E1 within ten seconds.
- Touch: bare copper (Q1), pad gap (Q17), same-cycle shielding (Q24), the
  TVS's share of each element's capacitance (Q-J), touch counts with the BBD
  clocks running and inhibited (section 11 §6), UART quiet during scans (Q23).
- ENC0 contact reliability at its present current (Q-D) only shows over life.
