# 08: Footprints against manufacturer drawings

Block: every non-passive footprint on both boards, read from the two
`.kicad_pcb` files; the 24 panel parts; part heights against the 10 mm gap
between the boards.

Sources (all in `datasheets/`, rendered with pdftoppm where image-only):
`AMS1117-datasheet.pdf` p7 ("3 LEAD SOT-223 PLASTIC PACKAGE");
`onsemi-MMBFJ113-datasheet.pdf` p1 (package figures), p7-p8 (outlines);
`1N4148W.pdf` p1 (pinning), p3 (SOD-123 outline); `BZT52C3V9-zener.pdf` p1, p4
("Pinning information", "Suggested solder pad layout"); `SMAJ6.0A-TVS.pdf` p5
("Dimensions, DO-214AC (SMA)" with the solder pad figure); `YLED0402Y.pdf` p1
(section 2, "Package Profile & Soldering PAD Suggested"); `Lelon-RVT-electrolytic.pdf`
p2 (size code table and dimension table); `TI-TL072-datasheet.pdf` p77 (D0008A);
`TI-TL074-datasheet.pdf` p59 and `TI-TL084-datasheet.pdf` p52 (D0014A);
`TI-OPA1688-datasheet.pdf` p40 (D0008A); `TI-CD4046B-datasheet.pdf` p12-p13
(NS0016A); `Microchip-MCP23017-datasheet.pdf` p31-p32 (SO 28, 7.50 mm);
`MeanWell-SKM10-DKM10-spec.pdf` p5 (mechanical, bottom view);
`Xvive-VTL5C3-datasheet.pdf` p1 (package dimensions); `Dailywell-2MD1T1B1M2QES-DPDT.pdf`
(drawing 2MD1T1B1M2QES-5, "P.C. MOUNTING"); `BOOMELE-C5665-2x5-box-header.pdf`
("P.C.B Layout"); `hanxia-HX-JN2.54-2x5P-TP-H8.9.pdf` ("RECOMMEND P.C.B LAYOUT
(TOP VIEW)"); `Epson-FC-135-32.768kHz.pdf` p1 (sections 3 and 4);
`TI-TPD1E10B06-datasheet.pdf` p19-p20 (DPY0002A); `TI-MSP430FR2675-datasheet.pdf`
p118-p120 (PT0048A); `PJ-603-jack.pdf`, `PJ-376-jack.pdf` (heights only); the BOM;
`docs/design-state.md` ("Panel part heights"); `hardware/faceplate/README.md` §2, §4, §5.

Footprints already settled against their drawings in earlier sections, and not
repeated here: U1 Patch SM (03), J11 USB-C (02), DS1, J1 microSD, ENC0-ENC8,
SW4-SW9 (04), U101/U201 V3205SD DIP (05), RV1-RV6, J2-J10, RT301-RT504 (07).

## 1. Board copy against library copy, both boards

A script compared every footprint's pads in the `.kicad_pcb` with its library
`.kicad_mod` (front-side parts must match exactly; back-side parts must be the
exact mirror, local y negated, which is what KiCad's own flip produces).

| board | footprints | on B.Cu | pads differing from library | verdict |
|---|---|---|---|---|
| main | 316 | 167 | none | CLEAN |
| faceplate | 54 | 50 | none | CLEAN |

No pad on either board was hand-edited, and every back-side part is a true
flip, not a front-side copy dragged to the back. The one difference the sweep
found anywhere is U1's four user silk letters (A/B/C/D), which sit at the
library positions with y negated on a front-side part: the section 3 defect,
reconfirmed.

All 24 panel parts are on F.Cu at rotation 0, so none of them can carry the
through-hole mirror-image failure. Their footprints were checked against
their drawings in the top view in sections 4 and 7.

## 2. Main board, part by part

Pad coordinates are the library frame (component side, y down). "Span" is the
distance of a pad's inner and outer edges from the footprint centre along the
lead axis.

| ref (footprint) | check | source says | ours | verdict |
|---|---|---|---|---|
| U5, U6 (F.Cu), U8 (B.Cu) AMS1117, SOT-223 | numbering | AMS p1: 1 GND/ADJ, 2 VOUT, 3 VIN, tab = VOUT; p7 top view: three leads in a row, tab opposite | pads 1/2/3 in a row at x +2.97, tab pad 4 at x -2.97; with the tab turned up, pad 1 is on the left (a rotation, not a mirror) | CLEAN |
| " | land | p7: pitch 2.29 nom, lead width 0.64-0.84, tab width 2.95-3.15, overall 6.71-7.29, body 3.30-3.71 | pitch 2.30, pin pads 1.1 x 2.5 spanning 1.72-4.22, tab pad 3.6 x 2.34 spanning 1.80-4.14 | CLEAN: lead tips at 3.36-3.65 land on the pads |
| Q1, Q2 (B.Cu) MMBFJ113, SOT-23 | numbering | onsemi p1 figure, SOT-23 (TO-236) case 318-08: G alone on one side, D and S on the other | pad 3 alone, on `BBD_SH_G_*`; pads 1/2 drain and source (interchangeable, section 2) | CLEAN |
| " | land | no SOT-23 outline or soldering footprint in the committed file (p7-p8 are the TO-92 outlines) | 1.0 x 0.65 pads, rows 2.0 apart, pitch 1.90 | BLOCKED |
| D103-D107, D203-D207 (B.Cu) 1N4148W, SOD-123 | polarity | p1 pinning: pin 1 = cathode; p3 outline D 2.6-2.7, HE 3.55-3.85, bp 0.5-0.6 | pad 1 = K; silk double bar at x -0.83/-0.97, the pad-1 end | CLEAN |
| " | land | no land pattern in the file | 0.95 x 1.15 pads, span 1.22-2.17; the lead runs from 1.30 to 1.78-1.93 | CLEAN |
| D301, D401 (F.Cu) BZT52C3V9, SOD-123 | polarity | p4 pinning: pin 1 = cathode | pad 1 = K; silk bar and triangle apex at the pad-1 end | CLEAN |
| " | land | p4 suggested pad: A 1.22 across, B 0.91 along, C 2.36 gap (span 1.18-2.09) | 1.2 along x 0.95 across, gap 2.2 (span 1.10-2.30) | CLEAN: longer and narrower than suggested, still 0.35 wider than the lead |
| D3 (B.Cu) SMAJ6.0A, SMA | polarity | p5: cathode band, unidirectional | pad 1 = K on `VBUS`; silk band at x -0.88, the pad-1 end | CLEAN |
| " | land | p5 solder pads: I (width) 1.80 min, J/L (length) 2.10 min, K (gap) 2.30 max; package G 4.80-5.28, E 0.78-1.52 | 2.0 x 2.0 pads at +-2.2: width 2.0, length **2.0**, gap **2.40** | DEFECT, low: length 0.10 under J/L min, gap 0.10 over K max; at G max with E max, 0.08 mm of terminal falls inside the pad's inner edge |
| D1, D2 (F.Cu) YLED0402Y, 0402 | polarity | p1 symbol: ① = +, ② = cathode | pad 1 = A (`LED_POS` on D1, `GND` on D2), silk bar beyond pad 2 | CLEAN |
| " | land | p1 suggested: 0.65 across x 0.50 along, gap 0.50 (outer 1.50); body 1.1 x 0.5, 0.25 terminations | 0.54 across x 0.50 along, gap 0.34 (outer 1.34) | CLEAN: terminations (0.30-0.55 from centre, +-0.1) land fully; narrower and closer than suggested |
| C32, C33 (F.Cu) Lelon RVT 5 x 5.4 | polarity | p2: negative band on the can, chamfered base at the + terminal | pad 1 = + (section 2); silk chamfer and "+" at pad 1 | CLEAN |
| " | land | p2 table, D5: C 6.1, W 0.5-0.8, P 1.3 (terminals 0.65-3.05 from centre); no land pattern given | 2.7 x 0.91 at +-2.4 (span 1.05-3.75) | CLEAN |
| C36, C37 (F.Cu) Lelon RVT1H220M0605 | land, polarity | p2 size code 0605 = 6.3 x 5.4; D6.3: C 7.4, W 0.5-0.8, P 2.2 (terminals 1.1-3.7) | 3.5 x 1.2 at +-2.67 (span 0.92-4.42); polarity as C32 | CLEAN |
| U102, U103, U106, U202, U203, U206 (B.Cu) TL072, SOIC-8 | land, order | TL072 p77, D0008A: 8X 1.55 x 0.6, pitch 1.27, rows (5.4) centre to centre; pin 1 top left, counter-clockwise | 1.95 x 0.568 at 5.41 (span 1.74-3.69 against TI's 1.93-3.48); pin 1 corner, counter-clockwise; silk dot at pad 1 | CLEAN |
| U9, U10 (B.Cu) OPA1688, SOIC-8 | land, order | OPA1688 p40, D0008A as above | 1.865 x 0.63 at 5.36; order and dot as above | CLEAN |
| U301, U302, U401, U402 (F.Cu) TL084/TL074, SOIC-14 | land, order | TL074 p59 / TL084 p52, D0014A: 14X 1.55 x 0.6, pitch 1.27, rows (5.4) | 1.95 x 0.6 at 4.95 (span 1.50-3.45 against 1.93-3.48): same toe, 0.43 further under the body; pin-1 mark is the top silk line run out over pad 1 | CLEAN |
| U104, U204 (B.Cu) CD4046BNSR, SO-16 5.3 mm | package | `bbd-mki.md` part table: CD4046BNSR, the NS (SOP) body | footprint body 10.3 x 5.3 | CLEAN |
| " | land | p12 NS0016A: tip to tip 7.4-8.2, body 5.2-5.4, L 0.55-1.05; p13: 16X 1.85 x 0.6, rows (7) | 1.598 x 0.595 at **7.4** (span 2.90-4.50 against TI's 2.58-4.43) | QUESTION, low: at tip-to-tip 7.4 with L 1.05 the foot runs 2.65-3.70 and its innermost 0.25 mm misses the pad (no heel fillet); TI's pad covers every corner |
| U3, U4 (F.Cu) MCP23017, SO-28 7.50 mm | land | p32: E 1.27, C 9.40, X 0.60 max, Y **2.00 max**, Gx 0.67 min, G 7.40 min; p31: E 10.30 BSC, L 0.40-1.27 | 0.6 x **2.3** at C 10.12: G 7.82, Gx 0.67 | DEFECT, low: Y 0.30 over Microchip's maximum and C 0.72 over nominal; the foot (3.88-5.15 at L max) lands on 3.91-6.21, 0.03 mm short at the heel |
| " | order | pin 1 corner, counter-clockwise | pin 1 at (-8.25, +5.06), 1-14 along one row, 15-28 back; silk dot at pad 1 | CLEAN |
| U7 (B.Cu) DKM10E-12 | pins, flip | p5 bottom view: upper row 6, 2, 1 (6-2 7.62, 2-1 5.08), lower row 5, 4, 3 at 10.16, rows 20.32 apart; pin dia 1.0 +-0.1 | board, seen from the front (through the board, which is the pin side of a back-mounted module): upper row 6, 2, 1, lower row 5, 4, 3, same spacings | CLEAN |
| " | hole | pin 1.1 max | drill 1.4, pad 2.4 | CLEAN: 0.3 min clearance |
| VT301, VT302, VT401, VT402 (F.Cu) VTL5C3 | pins | p1: LED leads 1/2 at one end, LDR 3/4 at the other, 0.200 (5.08) within a pair; internal schematic puts "-" on lead 2 | pairs at x +-6.35, 5.08 within each; pad 1 square, silk dot by pad 1 | CLEAN |
| " | hole | p1: LED leads .010-.025 (0.25-0.64) SQ, LDR leads .020 (0.51) dia | drill 0.9 for all four | QUESTION, low: a 0.64 square lead has a 0.905 diagonal |
| " | body | p1 end view: 7.62-8.13 one way, 9.40-9.91 the other (the axis the lead pair spreads along), body 9.1-9.9 long, potting up to 1.52 past each end "not controlled" | silk and footprint description 9.9 x 8.13 | DEFECT, doc: lying flat the part is 9.40-9.91 across the board and 7.62-8.13 tall; the silk understates its board footprint by up to 1.8 mm (no clash: 1.64 mm to the nearest courtyard at full width) |
| " | fit | lead pairs 12.7 apart leave 1.4 mm a side between a 9.9 body and the hole centre | | QUESTION, low: potting up to 1.52 a side puts the lead bend at the potting edge |
| SW1, SW2 (F.Cu) Dailywell 2MD1T1B1M2QES | holes, order | "P.C. MOUNTING": Ø1.09 (.048), 2.54 within a column, 5.08 between; 1-2-3 one column, 4-5-6 the other | drill 1.1; 1-3 at x -2.54 (1 at +y), 4-6 at +2.54 | CLEAN |
| " | orientation mark | the body is symmetric; pin numbers are what fix the lever sense | silk is a centre circle only, nothing marks pin 1 | QUESTION, low: a 180 degree fit swaps the poles and reverses the lever sense |
| J12 (B.Cu) BOOMELE C5665 | holes | "P.C.B Layout": 2xn Ø1.0 on 2.54, terminal 0.64 sq, body 8.8 x (n x 2.54 + 7.6) | drill 1.0, pad 1.524, 2.54 grid, silk mark at the pad-1 corner | CLEAN (key and mating: section 9) |
| F1 (B.Cu) ASMD1812-300 | land | no datasheet in `datasheets/` | 1.407 x 3.499 pads at +-1.85 | BLOCKED |

## 3. Faceplate, part by part

| ref (footprint) | check | source says | ours | verdict |
|---|---|---|---|---|
| U1 (B.Cu) MSP430FR2675TPT, LQFP-48 | land | p119 PT0048A: 48X 1.6 x 0.3, pitch 0.5, rows (8.2) both ways, non-solder-mask-defined, 0.05 min opening; p120 stencil 1.6 x 0.3, 0.1 mm | 1.6 x 0.3 at +-4.1, mask margin +0.05; fab gerbers: B_Mask 1.7 x 0.4, B_Paste 1.6 x 0.3 | CLEAN |
| " | order | p119: pin 1 top left, counter-clockwise | pin 1 (-4.1, -2.75), 1-12 down, 13-24 along, 25-36 up, 37-48 back; silk dot at pad 1 | CLEAN |
| D11-D44, 16 (B.Cu) TPD1E10B06DPYR, X1SON-2 | land | p20 DPY0002A: openings 0.3 x 0.5 at (0.7) centres; "SOLDER MASK DEFINED (PREFERRED)", metal 0.07 min under the mask all round; p19 terminals 0.2-0.3 x 0.45-0.55 at 0.65 | copper 0.44 x 0.64 at +-0.35, mask and paste margin -0.07; fab gerbers: B_Mask and B_Paste openings 0.3 x 0.5 | CLEAN: TI's preferred variant exactly |
| " | polarity | p1: bidirectional | no mark | CLEAN |
| Y1 (B.Cu) Epson FC-135 | land | p1 section 4: 1.0 x 1.8 pads, 2.5 centre to centre; "Do not design any circuit patterns in the shaded area" (between the pads) | 1.0 x 1.8 at +-1.25 | CLEAN (the keep-out is section 10) |
| J1 (B.Cu) hanxia HX JN2.54-2x5P TP H8.9 | land | recommended layout (top view): pads 1.02 x 4.65, pitch 2.54, 11.50 overall, A 10.16 for 10 pins; body 20.30 x 8.80-8.90, seated 9.60 +-0.25 | 1.02 x 4.65 at +-3.425 (11.50 overall), 2.54 pitch; silk triangle at the pad-1 end | CLEAN (key and mating: section 9) |
| TP1-TP6 (B.Cu) | | bare 1.5 mm pads, no part on the BOM | | n/a |
| E1-E4 (F.Cu) | | generated electrode copper | | section 10 |

## 4. Panel parts, position logic of `place.py --check` by hand

From `hardware/placement-panel-facing.txt` (24 parts), DS1 moved from its
top-left to its header (+21.5 in y), pcb = panel - (6.995, 9.000), sheet =
pcb + (100, 50), less each part's shaft offset in its own frame.

| parts | against place.py's offsets | against the drawings' shaft | verdict |
|---|---|---|---|
| all 24 | 0.000 mm worst; all F.Cu, rotation 0 | | CLEAN: all 24 on their holes |
| RV1-RV6 | | 0.17 mm toward the jack edge (place.py uses -4.83; the Alpha and ALPS drawings put the shaft at -5.00) | CLEAN: known and documented; the faceplate drills its six pot holes at the true shaft |
| ENC0 | | 0.05 mm: the footprint's own lug slots sit at y -0.25 and -0.20; place.py takes -0.20 | CLEAN: drafting asymmetry, far inside the hole |

## 5. Heights

The gap is set by the Alpha pot shoulder: faceplate underside 10.0 mm above
the main board (`design-state.md`, "Panel part heights"), and that shoulder is
10 +-0.5, so the gap is 9.5 to 10.5. The faceplate is 1.6 mm.

Tallest parts in the gap, from their drawings:

| side | part | height | source |
|---|---|---|---|
| main board, top | VT301-VT402 lying flat | 7.62-8.13 | Xvive p1 end view |
| main board, top | C32/C33, C36/C37 | 5.4 +-0.5 | Lelon p2: codes 0505 and 0605 are both 5.4 long |
| main board, top | U3/U4 | 2.65 max | Microchip p31, A |
| main board, top | U5/U6 | 1.80 max | AMS p7 |
| main board, top | DS1 module | 4.2 on a 3-5 mm lift | faceplate README §4 |
| main board, top | U1 Patch SM | **not given** | Electrosmith's sheet has no seated height |
| faceplate, back | J1 | 9.60 +-0.25 | hanxia side view |
| faceplate, back | U1 LQFP-48 | 1.6 max | MSP430 p118 |
| faceplate, back | Y1 | 0.8 +-0.1 | Epson p1 section 3 |

Overlap of the two boards in the panel frame (main pcb = panel - (6.995, 9);
faceplate sheet = panel + (100, 50)), by courtyard:

- **J1** sits over the 24 x 12 cutout and over no main-board part. Its 9.6 mm
  does not stack with anything. CLEAN.
- **VT301-VT402, C32/C33/C36/C37, DS1:** no faceplate part above any of them.
  Worst case 8.13 under an empty 9.5 gap. CLEAN. DS1 at its planned 5 mm lift
  tops out at 9.2, 0.3 under the faceplate at the gap's low corner.
- **U1, the Daisy**, is the only main-board part with faceplate parts above it:
  its courtyard (panel x 251.8-289.9, y 57.3-120.5) lies under the MSP430,
  the crystal, all 16 TVS, the series resistors and C1-C6. The module's top
  must stay under 9.5 - 1.6 = **7.9 mm**. The faceplate README carries "~7mm
  soldered direct (no 3D model)", which is not from a drawing. BLOCKED: no
  height in the manufacturer's sheet. Soldered direct it very likely fits;
  on standard 8.5 mm sockets it cannot (the README says so too).

Behind the main board (back-side parts, toward the case floor): PJ-603 12.7
(Haoyu front view, 6.2 + 6.5), PJ-376 10.7 (SOFNG title block, H10.7), DKM10
10.2 (Mean Well p5 side view; its pins are 5.6 min and come through the top
by about 4 mm, under nothing taller than 1.6 on the faceplate). The faceplate
README asks for about 15 mm of floor at `J12`; along the jack edge the floor
has to clear 12.7. Note for the enclosure, no defect.

## Verdicts

| item | verdict |
|---|---|
| board pads vs library, both boards; every B.Cu part a true flip | CLEAN |
| U1 user silk letters (section 3) | DEFECT, reconfirmed |
| SOT-223, SOIC-8, SOP-8, SOIC-14, LQFP-48, X1SON-2, FC-135, both 2x5 headers, DKM10, DPDT holes | CLEAN |
| SOD-123 (both), SMA, LED0402, electrolytics: polarity in pad and silk | CLEAN |
| D3 SMA land | DEFECT, low |
| U3/U4 SO-28 land | DEFECT, low |
| U104/U204 SO-16 heel coverage | QUESTION, low |
| VTL5C3 hole for a 0.64 square lead; lead bend room | QUESTION, low |
| VTL5C3 silk and description: body width | DEFECT, doc |
| SW1/SW2 no orientation mark | QUESTION, low |
| Q1/Q2 SOT-23 land pattern | BLOCKED |
| F1 1812 land pattern | BLOCKED |
| U1 Patch SM seated height under the MSP430 | BLOCKED |
| panel parts: 24 on their holes | CLEAN |
| heights: vactrols, electrolytics, DS1, J1 | CLEAN |
| faceplate README C36/C37 height | DEFECT, doc |
| `place.py` FREE_SEED comment on U1's side | DEFECT, doc |

## Defects, ranked

Nothing here would kill the board.

1. **BLOCKED, could stop assembly:** the Patch SM's seated height. It sits
   under the faceplate's MSP430 cluster and has to stay under 7.9 mm at the
   pot shoulder's low tolerance. Measure a soldered module before the
   faceplate goes on; do not socket it.
2. **DEFECT, low (yield):** D3's SMA pads are 0.10 shorter and 0.10 further
   apart than Littelfuse's limits (p5). Every termination still lands except
   0.08 mm at the worst corner. Hand-touch-up, not a respin.
3. **DEFECT, low (yield):** U3/U4 pads are 2.3 long where Microchip's SO-28
   land pattern caps them at 2.00, and the rows sit 0.36 mm further out per
   side than its 9.40 spacing. The feet land; the heel fillet is thin at long
   leads.
4. **QUESTION, low:** U104/U204 rows at 7.4 against TI's 7.0. One tolerance
   corner leaves 0.25 mm of foot inboard of the pad.
5. **QUESTION, low:** VTL5C3 LED leads may be up to 0.64 square (0.905
   diagonal) in a 0.9 hole, and the 12.7 lead-pair spacing bends the leads at
   the potting edge. Hand-fit, so a builder can cope; widen the LED holes to
   1.0 and the pair spacing to 15.24 at the next spin. Check the LED's
   polarity with a meter at fit: the drawing's "cathode identifier" is drawn
   at the lead-1 corner while its own schematic marks lead 2 "-".
6. **QUESTION, low:** SW1/SW2 silk has no pin-1 mark; fitted 180 degrees
   round, the lever works backwards against the panel legend.
7. **Doc:** the VTL5C3 footprint description and silk give 9.9 x 8.13; on the
   board the part is 9.9 long, up to 9.91 across and 8.13 tall.
8. **Doc:** `hardware/faceplate/README.md` §2 lists C36/C37 at 7.8 mm. The BOM
   part is RVT1H220M0605, which Lelon's size code makes 6.3 x 5.4 (5.9 max).
   The error is on the safe side.
9. **Doc:** `hardware/kicad/tools/place.py` line 110 says "U1 is on the BACK
   now"; U1 is on F.Cu, under the faceplate.
