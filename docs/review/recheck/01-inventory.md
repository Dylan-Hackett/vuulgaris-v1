# 01: Inventory and chain integrity

Recheck of 2026-10-02, section 1 of `docs/notes/recheck-prompts.md`. Report only:
nothing in netmap, values, design.py, the KiCad files or the fab packages was touched.

## Method

No KiCad in this container, so the repo's own checkers (`netcheck.py`,
`boardcheck.py`) were not run. Instead, a fresh reader was written outside the
repo (scratch dir, never committed) that parses the files directly:

- **Schematic.** Reads the embedded `lib_symbols` for every pin's number, name,
  type and position per unit, applies each instance's position, rotation and
  mirror, then joins wire endpoints, labels (same name = same net) and
  `no_connect` markers by coordinate. Self-test: every one of the 944 wire
  endpoints on the main sheet and 145 on the faceplate sheet lands exactly on a
  pin or a label, every `no_connect` sits on a pin, and no point lies in the
  middle of a wire (there are no junctions to honour). A wrong transform would
  have left endpoints hanging, so the geometry is proven, not assumed.
- **Board.** Reads every footprint's pads with their net, converts pad
  positions to board coordinates. Self-test: 982 track ends fall on a pad
  centre and all 982 carry that pad's net.
- **Pin-name layer.** `tools/kpins.json` is absent, as expected. The pin
  number to pin name map was rebuilt from the schematic's own `lib_symbols`.

## Result: the gate holds, but the number it was gated on is stale

| check | main board | faceplate |
|---|---|---|
| netmap refs / connections / nets | 316 / **944** / 223 | 54 / 145 / 41 |
| netmap vs schematic, both directions | 944 / 944, 0 extra | 145 / 145, 0 extra |
| netmap vs board pad nets, both directions | 944 / 944, 0 extra | 145 / 145, 0 extra |
| schematic pins with `no_connect` | 63 | 23 |
| board pads outside netmap | 66 = the 63 NC pins + 3 unnumbered mechanical pads | 23 = the 23 NC pins |
| refs on board vs netmap | identical sets, no duplicates | identical sets |

The runbook, `review-packet.md`, `REVIEW-INDEX.md` and `tools/blockview.py`
expect **942 connections, 309 refs, 219 nets**. That figure is from
`87e5df6` (2026-09-10). netmap history since:

| commit | date | refs / conns / nets | change |
|---|---|---|---|
| `87e5df6` | 09-10 | 309 / 942 / 219 | D3 TVS added (the quoted figure) |
| `30da82a` | 09-16 | 309 / 942 / 221 | LPG LED drive fix |
| `b6f0c0a` | 09-18 | 310 / 944 / 221 | C29 to ceramic, 100nF added at the connector |
| `cf63396` | 09-22 | 310 / 932 / 221 | SW4-SW9 un-shorted, one diagonal per switch net-less |
| `9aa2c7b` | 09-25 | 316 / 944 / 223 | ADR 0011 EXT feed into the LPG |

So 944 is the right number for today's intent, and an independent parse
reproduces it three ways with zero disagreement. The gate is treated as passed.

## Inventory

Every fitted ref with its BOM line. TP1-TP15 (main) and TP1-TP6, E1-E4
(faceplate) are bare copper and correctly absent from both BOMs. BOM ref sets
equal netmap ref sets minus those.


### Main board

| refs | part (BOM comment) | LCSC | footprint | datasheet |
|---|---|---|---|---|
| R20, R21 | 0402WGF2201TCE | C25879 | R0402 | none: fine (R/C) |
| R104, R204 | 0R  (IN GAIN -- OPEN, see docs/bbd-mki.md) | C21189 | R0603 | none: fine (R/C) |
| R106, R115, R116, R117, R122, R124, R125, R128, R130, R206, R215, R216, R217, R222, R224, R225, R228, R230, R305, R309, R310, R317, R318, R320, R323, R328, R330, R331, R333, R405, R409, R410, R417, R418, R420, R423, R428, R430, R431, R433, R509, R510, R519, R520 | 100k | C25803 | R0603 | none: fine (R/C) |
| C31, C34, C35, C38, C39, C40, C41, C43, C105, C106, C107, C108, C109, C111, C121, C122, C205, C206, C207, C208, C209, C211, C221, C222, C301, C302, C303, C304, C401, C402, C403, C404, C507, C508, C509, C510 | 100nF / CC0603JRX7R8BB104 | C14663 | C0603 | none: fine (R/C) |
| R118, R126, R218, R226, R301, R302, R308, R314, R401, R402, R408, R414, R505 | 10k | C25804 | R0603 | none: fine (R/C) |
| C119, C219 | 10nF C0G 0805 | C237168 | C0805 | none: fine (R/C) |
| C20, C22, C24, C25, C29, C42, C110, C210 | 10uF / CL21A106KAYNNNE | C15850 | C0805 | none: fine (R/C) |
| SW4, SW5, SW6, SW7, SW8, SW9 | 12x12 tactile | C54573007 | KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5 | `TS1103S-12x12-tactile.pdf` |
| R303, R403 | 150k | C22807 | R0603 | none: fine (R/C) |
| R311, R312, R411, R412 | 15k | C22809 | R0603 | none: fine (R/C) |
| R501, R502 | 1M | C22935 | R0603 | none: fine (R/C) |
| D103, D104, D105, D106, D107, D203, D204, D205, D206, D207 | 1N4148W | C81598 | SOD-123_L2.8-W1.8-LS3.7-RD | `1N4148W.pdf` |
| R107, R207, R315, R415, R503, R504, R514, R516, R517, R518 | 1k | C21190 | R0603 | none: fine (R/C) |
| R513, R515 | 1k2 | C22765 | R0603 | none: fine (R/C) |
| C114, C214, C309, C409 | 1nF C0G | C163508 | C0603 | none: fine (R/C) |
| C30, C113, C120, C213, C220, C306, C406, C501, C502, C503, C504, C505, C506, C511, C512 | 1uF X7R 50V / CC0805KKX7R9BB105 | C28323 | C0805 | none: fine (R/C) |
| R121, R221 | 2.2M | C22938 | R0603 | none: fine (R/C) |
| RT301, RT401, RT501, RT502, RT503, RT504 | 20k trim | C55071 | RES-ADJ-SMD_3224W | `Bourns-3224W-trimmer.pdf` |
| C116, C216, C307, C407 | 220pF C0G | C27675 | C0603 | none: fine (R/C) |
| R110, R111, R129, R210, R211, R229 | 22k | C31850 | R0603 | none: fine (R/C) |
| C310, C410 | 22pF C0G | C1653 | C0603 | none: fine (R/C) |
| R521, R522 | 2k2 | C4190 | R0603 | none: fine (R/C) |
| C305, C405 | 2nF C0G | C296055 | C0603 | none: fine (R/C) |
| R307, R407 | 33k | C4216 | R0603 | none: fine (R/C) |
| R123, R223 | 39k | C23153 | R0603 | none: fine (R/C) |
| D301, D401 | 3V9 zener | C213113 | SOD-123_L2.7-W1.6-LS3.7-RD-1 | `BZT52C3V9-zener.pdf` |
| R119, R219 | 4.7k | C23162 | R0603 | none: fine (R/C) |
| C308, C408 | 4.7nF C0G | C576818 | C0603 | none: fine (R/C) |
| R131, R132, R231, R232, R306, R406 | 470R | C23179 | R0603 | none: fine (R/C) |
| R304, R404 | 470k | C23178 | R0603 | none: fine (R/C) |
| R113, R213, R506, R507, R508 | 47k | C25819 | R0603 | none: fine (R/C) |
| R313, R413 | 4M7 | C23163 | R0603 | none: fine (R/C) |
| R511, R512 | 4R7 | C23164 | R0603 | none: fine (R/C) |
| R114, R214 | 51k | C23196 | R0603 | none: fine (R/C) |
| R127, R227 | 6.2k | C4260 | R0603 | none: fine (R/C) |
| R120, R220 | 62k | C23221 | R0603 | none: fine (R/C) |
| R112, R212 | 82k | C23254 | R0603 | none: fine (R/C) |
| U5, U6 | AMS1117-3.3 | C6186 | SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR | `AMS1117-datasheet.pdf` |
| U8 | AMS1117-5.0 | C6187 | SOT-223-3_L6.5-W3.4-P2.30-LS7.0-BR | `AMS1117-datasheet.pdf` |
| F1 | ASMD1812-300 | C135366 | F1812 | none: GAP for section 2: PTC, no pin semantics, but hold/trip numbers needed and no sheet in repo |
| FB1, FB2 | BEAD0805S601A20T | C1017 | R0805 | none: fine (2-pin bead, no polarity) |
| L1, L2 | BLM18PG121SN1D_C14709 | C14709 | L0603 | none: fine (2-pin bead) |
| C28 | CC0603JRNPO9BN103 | C57112 | C0603 | none: fine (R/C) |
| U104, U204 | CD4046B | C2651237 | SO-16_L10.3-W5.3-P1.27-LS7.8-BL | `TI-CD4046B-datasheet.pdf` |
| C21, C23, C26, C27 | CL05B104KO5NNNC | C1525 | C0402 | none: fine (R/C) |
| RV1, RV2, RV3, RV4, RV6 | CUTOFF / FILTER CV AMT / RESONANCE / TIME / WET/DRY | (blank, hand-fit) | RES-ADJ-TH_RK09L1240A12 | `Alpha-RD902F-40-15R1-dual-9mm-pot.pdf` |
| U7 | DKM10E-12 | C6934792 | PWRM-TH_DKMW30F-12 | `MeanWell-SKM10-DKM10-spec.pdf` |
| ENC0 | EC11L1525G01 | C2991196 | SW-TH_ALPS_EC11L1525G01 | `ALPS-EC11L1525G01.pdf` |
| ENC1, ENC2, ENC3, ENC4, ENC5, ENC6, ENC7, ENC8 | EC12E2430803 | C470684 | SW-TH_EC12EXXXX | `ALPS-EC12E2430803.pdf` |
| U1 | ES_DAISY_PATCH_SM_REV1 | (blank, hand-fit) | DAISY_PATCH_SM | `Electrosmith-Patch-SM-v1.0.5.pdf` |
| J12 | FACEPLATE 2x5 IDC | C5665 | IDC-TH_10P-P2.54_C5665 | `BOOMELE-C5665-2x5-box-header.pdf` |
| RV5 | FEEDBACK | (blank, hand-fit) | RES-ADJ-TH_RK09L1240A12 | `Alpha-RD902F-40-15R1-dual-9mm-pot.pdf` |
| DS1 | HS242L01W4S01 | C5139768 | LCD-TH_HS242L01W4S01 | `HS242L01W4S01-OLED.pdf` |
| Q1, Q2 | J113 / MMBFJ113 | C891686 | SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR | `onsemi-MMBFJ113-datasheet.pdf` |
| U3, U4 | MCP23017-E_SO | C47023 | SOIC-28_L18.0-W7.5-P1.27-LS10.3-BL | `Microchip-MCP23017-datasheet.pdf` |
| U9, U10 | OPA1688_FLAT | C206212 | SOP-8_L4.9-W3.9-P1.27-LS6.0-BL | `TI-OPA1688-datasheet.pdf` |
| J2, J3, J4, J5, J6 | PJ-376 | C22355746 | AUDIO-TH_PJ-376 | `PJ-376-jack.pdf` |
| J7, J8, J9, J10 | PJ-603_C41409498 | C41409498 | AUDIO-TH_PJ-603 | `PJ-603-jack.pdf` |
| R24, R25 | RT0603BRD072K2L | C861295 | R0603 | none: fine (R/C) |
| R22, R23 | RT0603BRD075K1L | C122969 | R0603 | none: fine (R/C) |
| C32, C33 | RVT1E470M0505_C2977553 | C2977553 | CAP-SMD_BD5.0-L5.3-W5.3-LS6.3-FD | `Lelon-RVT-electrolytic.pdf` |
| C36, C37 | RVT1H220M0605 | C72505 | CAP-SMD_BD6.3-L6.6-W6.6-FD | `Lelon-RVT-electrolytic.pdf` |
| D3 | SMAJ6.0A | C223993 | SMA_L4.3-W2.6-LS5.2-RD | `SMAJ6.0A-TVS.pdf` |
| SW1, SW2 | SW_DPDT_FLAT | (blank, hand-fit) | SW-TH_DW3_DPDT_2MD1T1B1M2QES | `Dailywell-2MD1T1B1M2QES-DPDT.pdf` |
| J1 | TFPUSH | C393941 | TF-SMD_TF-PUSH | `TF-PUSH-microSD.pdf` |
| U102, U103, U106, U202, U203, U206 | TL072_FLAT | C67473 | SOIC-8_L4.9-W3.9-P1.27-LS6.1-BL | `TI-TL072-datasheet.pdf` |
| U302, U402 | TL074 | C12594 | SOIC-14_3.9x8.7mm_P1.27mm | `TI-TL074-datasheet.pdf` |
| U301, U401 | TL084 | C8956 | SOIC-14_3.9x8.7mm_P1.27mm | `TI-TL084-datasheet.pdf` |
| J11 | TYPE-C-31-M-12 | C165948 | USB-C_SMD-TYPE-C-31-M-12_1 | `Korean-Hroparts-TYPE-C-31-M-12.pdf` |
| U101, U201 | V3205SD | (blank, hand-fit) | DIP-8_SPECIAL_V3205SD | `Panasonic-MN3205-datasheet.pdf` (+ BBD manual p25) |
| VT301, VT302, VT401, VT402 | VTL5C3 | (blank, hand-fit) | VACTROL-TH_VTL5C3 | `Xvive-VTL5C3-datasheet.pdf` |
| D1, D2 | YLED0402Y | C20608782 | LED0402-R-RD | `YLED0402Y.pdf` |

### Faceplate

| refs | part (BOM comment) | LCSC | footprint | datasheet |
|---|---|---|---|---|
| C2 | 100nF | C14663 | C0603 | none: fine (R/C) |
| C1 | 10uF | C15850 | C0805 | none: fine (R/C) |
| C4 | 1nF C0G | C163508 | C0603 | none: fine (R/C) |
| C3 | 1uF | C28323 | C0805 | none: fine (R/C) |
| C5, C6 | 22pF C0G | C1653 | C0603 | none: fine (R/C) |
| Y1 | 32.768kHz FC-135 12.5pF | C32346 | XTAL-SMD_FC-135_3.2x1.5mm | `Epson-FC-135-32.768kHz.pdf` |
| R11, R12, R13, R14, R21, R22, R23, R24, R31, R32, R33, R34, R41, R42, R43, R44 | 470 | C23179 | R0603 | none: fine (R/C) |
| R1, R2, R3 | 47k | C25819 | R0603 | none: fine (R/C) |
| J1 | HX JN2.54-2x5P TP H8.9 | C41376028 | IDC-SMD_10P-P2.54_C41376028 | `hanxia-HX-JN2.54-2x5P-TP-H8.9.pdf` |
| U1 | MSP430FR2675TPT | C2052972 | LQFP-48_7x7mm_P0.5mm_PT0048A | `TI-MSP430FR2675-datasheet.pdf` |
| D11, D12, D13, D14, D21, D22, D23, D24, D31, D32, D33, D34, D41, D42, D43, D44 | TPD1E10B06DPYR | C48260 | X1SON-2_DPY0002A | `TI-TPD1E10B06-datasheet.pdf` |


**Refs with no datasheet:**

- R, C, FB1/FB2, L1/L2: fine, no pin semantics.
- **F1 (ASMD1812-300): gap.** No pin semantics, so no wiring risk, but section 2
  needs its hold and trip current and there is no sheet in the repo.
- **MCP23017: revision gap.** The committed sheet is **DS20001952C (July 2016)**,
  whose Table 2-1 calls GPA7 and GPB7 "Bidirectional I/O". The runbook itself
  refers to an output-only caveat on GPA7/GPB7 "in the current datasheet
  revision"; that revision is not in the repo. Three inputs sit on those pins
  (section 4 takes this up). **Closed 2026-10-04:** the committed sheet is now
  DS20001952E (July 2026), which says output only for both.
- CoolAudio V3205SD: never obtained, known; MN3205 original plus manual p25.

**Doc drift found here:** `REVIEW-INDEX.md` maps `C29` to the Lelon RVT
electrolytic (it is a 10uF 0805 MLCC, CL21A106KAYNNNE, since `b6f0c0a`) and `RV1`-`RV6`
to the ALPS RK09L sheet (the fitted part is the Alpha RD902F; the RK09L sheet
now only documents the footprint's origin). The BOM footprint name
`PWRM-TH_DKMW30F-12` on U7 names a different Mean Well module (DKMW30F); a
footprint name is not evidence either way, so section 8 checks the pads.

## Pins whose name implies a function

Every symbol pin named as a supply, ground, reset or control pin, both boards,
against the net it sits on. "CLEAN" here means name and net agree; whether the
**name** is right for that pin number is each block's datasheet check.

| board | ref.pin | pin name | net | name implies | verdict |
|---|---|---|---|---|---|
| main | DS1.1 | GND | GND | GND | CLEAN |
| main | DS1.2 | VCC | P3V3_OLED | +supply | CLEAN |
| main | ENC0.6 | EH | GND | GND | CLEAN |
| main | ENC0.7 | EH | GND | GND | CLEAN |
| main | J1.4 | VDD | P3V3_DAISY | +supply | CLEAN |
| main | J1.6 | VSS | GND | GND | CLEAN |
| main | J11.1 | EH | GND | GND | CLEAN |
| main | J11.2 | EH | GND | GND | CLEAN |
| main | J11.3 | EH | GND | GND | CLEAN |
| main | J11.4 | EH | GND | GND | CLEAN |
| main | J11.A1B12 | GND | GND | GND | CLEAN |
| main | J11.A4B9 | VBUS | VBUS | +supply | CLEAN |
| main | J11.B1A12 | GND | GND | GND | CLEAN |
| main | J11.B4A9 | VBUS | VBUS | +supply | CLEAN |
| main | U1.A1 | -12V | NEG12V | -supply | CLEAN |
| main | U1.A10 | +3V3 | P3V3_DAISY | +supply | CLEAN |
| main | U1.A4 | GND | GND | GND | CLEAN |
| main | U1.A5 | +12V | POS12V | +supply | CLEAN |
| main | U1.A6 | +5V | P5V | +supply | CLEAN |
| main | U1.A7 | GND | GND | GND | CLEAN |
| main | U10.4 | V- | NEG12V | -supply | CLEAN |
| main | U10.8 | V+ | POS12V | +supply | CLEAN |
| main | U101.1 | GND | GND | GND | CLEAN |
| main | U101.5 | VDD | P5V_BBD | +supply | CLEAN |
| main | U102.4 | V- | NEG12V | -supply | CLEAN |
| main | U102.8 | V+ | POS12V | +supply | CLEAN |
| main | U103.4 | V- | NEG12V | -supply | CLEAN |
| main | U103.8 | V+ | POS12V | +supply | CLEAN |
| main | U104.16 | VDD | P5V_BBD | +supply | CLEAN |
| main | U104.8 | VSS | GND | GND | CLEAN |
| main | U106.4 | V- | NEG12V | -supply | CLEAN |
| main | U106.8 | V+ | POS12V | +supply | CLEAN |
| main | U201.1 | GND | GND | GND | CLEAN |
| main | U201.5 | VDD | P5V_BBD | +supply | CLEAN |
| main | U202.4 | V- | NEG12V | -supply | CLEAN |
| main | U202.8 | V+ | POS12V | +supply | CLEAN |
| main | U203.4 | V- | NEG12V | -supply | CLEAN |
| main | U203.8 | V+ | POS12V | +supply | CLEAN |
| main | U204.16 | VDD | P5V_BBD | +supply | CLEAN |
| main | U204.8 | VSS | GND | GND | CLEAN |
| main | U206.4 | V- | NEG12V | -supply | CLEAN |
| main | U206.8 | V+ | POS12V | +supply | CLEAN |
| main | U3.10 | VSS | GND | GND | CLEAN |
| main | U3.18 | ~{RESET} | P3V3_DAISY | reset (pulled/driven) | CHECK |
| main | U3.9 | VDD | P3V3_DAISY | +supply | CLEAN |
| main | U301.11 | V- | NEG12V | -supply | CLEAN |
| main | U301.4 | V+ | POS12V | +supply | CLEAN |
| main | U302.11 | V- | NEG12V | -supply | CLEAN |
| main | U302.4 | V+ | POS12V | +supply | CLEAN |
| main | U4.10 | VSS | GND | GND | CLEAN |
| main | U4.18 | ~{RESET} | P3V3_DAISY | reset (pulled/driven) | CHECK |
| main | U4.9 | VDD | P3V3_DAISY | +supply | CLEAN |
| main | U401.11 | V- | NEG12V | -supply | CLEAN |
| main | U401.4 | V+ | POS12V | +supply | CLEAN |
| main | U402.11 | V- | NEG12V | -supply | CLEAN |
| main | U402.4 | V+ | POS12V | +supply | CLEAN |
| main | U5.1 | GND | GND | GND | CLEAN |
| main | U5.2 | VOUT | P3V3_OLED | +supply (driven) | CLEAN |
| main | U5.3 | VIN | P5V_OLED | +supply | CLEAN |
| main | U5.4 | VOUT | P3V3_OLED | +supply (driven) | CLEAN |
| main | U6.1 | GND | GND | GND | CLEAN |
| main | U6.2 | VOUT | P3V3_MSP430 | +supply (driven) | CLEAN |
| main | U6.3 | VIN | P5V_MSP | +supply | CLEAN |
| main | U6.4 | VOUT | P3V3_MSP430 | +supply (driven) | CLEAN |
| main | U7.1 | +Vin | VBUS_F | +supply | CLEAN |
| main | U7.2 | -Vin | GND | GND | CLEAN |
| main | U7.3 | +Vout | POS12V_RAW | +supply (driven) | CLEAN |
| main | U7.4 | Common | GND | GND | CLEAN |
| main | U7.5 | -Vout | NEG12V_RAW | -supply | CLEAN |
| main | U7.6 | R.C. | None | control | CHECK |
| main | U8.1 | GND | GND | GND | CLEAN |
| main | U8.2 | VOUT | P5V_BBD | +supply (driven) | CLEAN |
| main | U8.3 | VIN | POS12V | +supply | CLEAN |
| main | U8.4 | VOUT | P5V_BBD | +supply (driven) | CLEAN |
| main | U9.4 | V- | NEG12V | -supply | CLEAN |
| main | U9.8 | V+ | POS12V | +supply | CLEAN |
| face | U1.1 | DVCC | P3V3_MSP430 | +supply | CLEAN |
| face | U1.2 | ~{RST}/NMI/SBWTDIO | MSP_RST | reset (pulled/driven) | CHECK |
| face | U1.3 | TEST/SBWTCK | MSP_TEST | control | CHECK |
| face | U1.48 | DVSS | GND | GND | CLEAN |


The five `CHECK` rows, resolved:

- `U3.18`, `U4.18` `~RESET` on `P3V3_DAISY`: DS20001952C Table 2-1, RESET
  "Hardware reset. Must be externally biased." Held inactive-high. CLEAN.
- `U7.6` R.C. open: section 2 reads the Mean Well spec.
- Faceplate `U1.2` RST/NMI and `U1.3` TEST: section 10 (Table 7-4 of SLASEO5D
  wants RST/NMI pulled up with a 47k and 1.1nF-to-10nF; TEST may be left open,
  it has an internal pulldown).

No supply pin on a signal net, no ground pin on a supply, and no net with two
pins named as outputs (op-amp `OUT`, regulator `VOUT` excepted as one source).

## Single-pin nets and unconnected pins

### Single-pin nets (main board 3, faceplate 0)

| net | pin | justification | verdict |
|---|---|---|---|
| `MSP_TEST` | `J12.1` | ADR 0005 (superseded 2026-09-06): blank FR26xx devices enter BSL without the TEST/RST sequence (SLAU550 3.3.3 quoted there), so nothing on the main board drives TEST. The pin exists for the CAPTIVATE-PGMR / SBW path with the ribbon pulled (ADR 0005, 2026-09-28 revision). The faceplate side has TEST's internal pulldown. | CLEAN, by decision; section 9 checks the BSL claim against SLAU550 |
| `BBD_WETOUT_L` | `R132.2` | `bbd-mki.md` XS4, closed 2026-09-08: R132 taps `BBD_WETAC` in parallel with R131 and ends on nothing. A 470R with one end open draws no current and loads nothing. | CLEAN, by decision (a part that does nothing, costs one placement) |
| `BBD_WETOUT_R` | `R232.2` | as above | CLEAN, by decision |

### Unconnected pins, main board (63 `no_connect` + 3 unnumbered pads)

| ref.pin | name | may it float? source | verdict |
|---|---|---|---|
| `U1.A8` | USB_DM (PB14) | Patch SM Table 2: plain GPIO. A floating STM32 pin left in its reset state is harmless. | CLEAN |
| `U1.B9` | GATE_IN_2 | Table 2 "Input Only", Fig 1.4: 100k input network on the module. | CLEAN |
| `U1.C2`-`C8` | CV_1..CV_7 | Table 2 "Input Only", Fig 1.3: 100k input impedance on the module, biased there. | CLEAN |
| `U1.D3`, `U1.D4` | SDMMC1_D2, D1 (PC10, PC9) | GPIO; D3 carries a module 47k pullup (Table 2 footnote), D4 does not. Unused in 1-bit SD. | CLEAN |
| `U1.D8` | ADC_12 / SPI2_MISO | GPIO; display is write-only. | CLEAN |
| `U3.11`, `U3.14`, `U4.11`, `U4.14` | NC | DS20001952C Table 2-1: NC on MCP23017. | CLEAN |
| `U3.19`/`20`, `U4.19`/`20` | INTB, INTA | outputs (Table 2-1). Float allowed. Consequence: no interrupt, the Daisy must poll; section 4. | CLEAN |
| `U4.5`-`8`, `U4.23`, `U4.24` | GPB4-GPB7, GPA2, GPA3 | inputs at power-on (IODIR resets to all-input) with no external bias. Rev C gives no unused-pin rule. A floating CMOS input is legal but can draw shoot-through current; firmware should enable GPPU or set them as outputs. fw-daisy is a skeleton with no MCP23017 code yet. | QUESTION (firmware requirement) |
| `DS1.8` | FS0 | font-ROM data output (module sheet, ADR 0006). | CLEAN |
| `J1.1`, `J1.8` | DAT2, DAT1 | unused in 1-bit mode. No host pullup on either. Patch SM Fig 1.7 says "No pullup resistors necessary" but that refers to its own SDMMC pins, and DAT2/DAT1 are not connected to the module at all here. The SD Physical Layer spec (not in repo) is the authority on floating card DAT lines. | QUESTION, section 4 |
| `J1.CD` | card detect | switch contact, unused. | CLEAN |
| `J11.A6`/`A7`/`B6`/`B7` | D+/D- | power-only sink, ADR 0010. | CLEAN |
| `J11.A8`, `J11.B8` | SBU1/2 | unused sideband, power-only sink. | CLEAN |
| `SW1.3`, `SW1.6` | A_NO, B_NO | VCF switch uses one throw; open throw is the off position. Section 5/6. | CLEAN |
| `SW4`-`SW6`, `SW8` pads 1, 4; `SW7`, `SW9` pads 2, 3 | tactile | the un-shorting fix of 2026-09-22 leaves one terminal per internal bar unconnected. Floating is correct **if** the pairs are as claimed; section 4 re-reads the TS1103S drawing. | CLEAN pending 4 |
| `U104`/`U204` pins 1, 13 | phase pulses, PC II out | outputs (CD4046B p1 terminal assignment and Fig 1). | CLEAN |
| `U104`/`U204` pin 10 | demodulator out | CD4046B p1: "If unused this terminal should be left open." | CLEAN |
| `U104`/`U204` pin 15 | zener | an optional regulator zener to VSS (Fig 1). Open is unused. | CLEAN |
| `U101.3`, `U201.3` | OUT1 | review-packet item 2: the manual's module uses one output. Section 5 re-reads it. | CLEAN pending 5 |
| `U7.6` | R.C. | section 2 | pending 2 |
| `J9.3`, `J10.3` | tip switch | outputs; the normalling contact is unused. Section 7. | CLEAN pending 7 |
| `DS1`, `J1`, `J11` unnumbered pads | mounting pegs | no electrical function. | CLEAN |

### Unconnected pins, faceplate (23)

`U1` pins 6-22 and 40-45: all are Px.y GPIO (pin names list `P1.6` ... `P6.2`).
SLASEO5D section 7.6, Table 7-4: unused Px.0-Px.7 are left **open** and
"switched to port function, output direction (PxDIR.n = 1)". Open is correct
in hardware; the firmware half goes to section 10. **CLEAN** (firmware
requirement noted).

## Symbol pins vs footprint pads vs datasheet pin count

Symbol pin set equals footprint pad set, with no duplicate numbering, on every
part except these, all explained:

| ref | symbol pins | pads | difference |
|---|---|---|---|
| `DS1` | 9 | 13 | 4 unnumbered mounting pads |
| `J1` | 13 | 15 | 2 unnumbered locating pegs. Note **no pin 9**: pads are 1-8, 10-13 and `CD`. Section 4 checks that against the TF-PUSH drawing. |
| `J11` | 16 | 18 | 2 unnumbered locating pegs |
| faceplate `E1`-`E4` | 5 | 208-213 | the comb electrodes: many copper pads per element number, by design |

Datasheet pin counts, per block section, as each part is derived from its
drawing.

## Verdicts

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| all 944 main-board connections | | netmap | schematic and board agree | CLEAN |
| all 145 faceplate connections | | netmap | schematic and board agree | CLEAN |
| connection count | | runbook/docs: 942 | 944 | DEFECT (doc) |
| `U3.28`, `U3.8`, `U4.28` | ENC4_B, ENC8_B, BTN4 | current MCP23017 revision (not in repo) | inputs on GPA7/GPB7 | BLOCKED |
| `U4` GPB4-7, GPA2-3 | none | no rule in Rev C | floating inputs | QUESTION |
| `J1.1`, `J1.8` | none | SD spec (not in repo) | floating DAT2/DAT1 | QUESTION |
| `F1` | VBUS/VBUS_F | needs its own sheet | none in repo | BLOCKED |
| `REVIEW-INDEX.md` rows for C29 and RV1-RV6 | | BOM | stale part mapping | DEFECT (doc) |

## Defects, ranked

Nothing in section 1 would kill the board. The bookkeeping chain from netmap
through the schematic to the copper is intact on both boards.

1. **Doc (cosmetic):** the 942/309/219 figure is stale in the runbook,
   `docs/review-packet.md`, `datasheets/REVIEW-INDEX.md` and the
   `tools/blockview.py` docstring. Today: 944/316/223.
2. **Doc (cosmetic):** `REVIEW-INDEX.md` datasheet mapping for `C29` and
   `RV1`-`RV6` predates the C29 and pot changes.

Carried forward: GPA7/GPB7 (section 4, potentially a functional defect on two
encoders and one button), F1's ratings (section 2), floating SD DAT1/DAT2
(section 4), firmware termination of unused MCP23017 and MSP430 pins.
