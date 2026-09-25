# Faceplate PCB

4-layer, **ENIG**. Carries the four capacitive scrub pads on L1 and the MSP430FR2675 on
the back. Panel geometry comes from `../../mockups/generate-faceplate.py` — see the
handoff below for the size, which is not what older docs say.

## Handoff from the main board — 2026-09-24

The main board is finished: DRC clean, fab package at `../vuulgaris-v1-fab.zip`. What
follows is fixed by it. The faceplate works around these, not the other way round.

### 1. Size: the generator is the source of truth, and it needs two changes

`generate-faceplate.py` currently gives **298.286 x 130.81mm** (`panel_h_mm`, "panel =
board + 14": a 6mm wall and 1mm gap at each end). Numbers still in circulation that are
**superseded**: "~285 x 155" (this file, until today), "298 x 154" (`panel-budget.md`),
and the filename `mockups/faceplate-v1-298x139.svg`, whose contents are 130.81.

- **+2mm at the top (jack) edge — required.** The main board's top edge moved out 2mm on
  2026-09-23 so every edge connector ends flush with the wall (`design-state.md`, "Top
  edge extended 2mm"); the board is now 118.81mm. The knobs did not move, so **every
  panel y grows by exactly 2.000 and nothing may re-flow.** The generator centres and
  scales parts of the composition, so do not just raise `panel_h_mm`: add a pure offset,
  regenerate `../placement-panel-facing.txt`, and diff it against the old one — every
  row +2.000 in y, nothing else. In the **same commit** set `OY` in
  `../kicad/tools/place.py` from 7.000 to 9.000 (the comment above `ORG` explains), and
  `place.py --check` must still report all 24 panel parts on their holes. Get this wrong
  and `place.py` moves 24 parts on a routed board.
- **+5mm more at the bottom (back) edge — a decision.** "Board + 14" leaves 1mm behind
  the board, but the board slides in along y and needs 6mm of travel to clear the
  jacks (`design-state.md`, "Assembly": cavity 125.81 = 1 + 118.81 + 6). A faceplate
  covering the box to both outer faces is therefore **137.81mm**. Extra height at the
  bottom edge moves no coordinates.

Pads: this file says 12mm wide, 80 teeth, 6mm gap; the generator's own SVG says 10mm
wide at 18mm pitch (8mm gap), 100 teeth. **Reconcile before any copper** (ADR 0003,
Q17).

### 2. Stack-up: the pots are the datum, and the faceplate is structural

- Faceplate underside **10.0mm** above the main board (the pots' mounting surface),
  **1.6mm** thick, outer face at 11.6mm.
- **Do not go thicker.** The pots (Alpha RD902F) have 3.4mm of M7x0.75 thread above the
  outer face, for a 1.8mm nut plus washer.
- The six pot nuts are the **only** clamp. Encoders (EC12, 0.9mm of bushing through),
  toggles, buttons and the OLED locate but carry nothing. The whole main board hangs off
  the faceplate through those six nuts (`design-state.md`, "Panel mounting").

### 3. Holes

| part | hole | source |
|---|---|---|
| pots `RV1`–`RV6` | **7.5mm**, centred **0.17mm toward the top edge** of the panel coordinate | M7x0.75, washer ID 7.2 (Alpha drawing); true shaft is (0, −5.00) from the footprint origin, placed at −4.83 — `place.py` |
| buttons `SW4`–`SW9` | 6.6mm | 6.2mm round plunger; generator `mx_hole_r_mm` |
| toggles `SW1`/`SW2` | 4.95mm | generator `switch_hole_d_mm` |
| encoders `ENC1`–`ENC8` (EC12E), `ENC0` (EC11L) | **not sized yet** | EC12 bushing M9x0.75 per `design-state.md`; read the ALPS drawings |
| OLED `DS1` | window, **not sized yet** | below |

The generator draws **no pot or encoder holes at all** yet — the r=8 and r=9.2 circles in
the FAB SVG are knob outlines, not cuts.

### 4. OLED

The module is **68 x 43mm on its own PCB, 4.2mm tall**, active area 55.01 x 27.49mm. It will
be raised **3–5mm** on a 1x9 socket plus four M3 standoffs in the corner holes already on
the main board. **Nylon standoffs, not metal:** the lower-left hole (297.55, 94.05) has a
`POS12V` trace on F.Cu 2.2mm from its centre, under the standoff's hex base, and a metal
one would put +12V a scratch of soldermask away from the module's mounting hole. The
other three holes have no copper within 3mm on either side. Its face then sits about **2.4–4.4mm** behind the
outer surface; at 5.8mm of lift it hits the faceplate. Size the window to the active area
at the final height and chamfer the edges (`design-state.md`, "Consequence 2"). This
answers Q18.

### 5. The connector

Main board `J12`: 2x5 2.54mm box header (LCSC C5665), **on the BACK of the main board,
facing down** (moved 2026-09-25), ribbon to the faceplate.

**The route.** The main board has a **24 x 12mm cutout** directly beside `J12`, at board
(210, 97.5)–(234, 109.5) — sheet (310, 147.5)–(334, 159.5) — made for exactly this. The
faceplate's connector sits **over that cutout, facing down**; its ribbon plug hangs through
the hole in the main board, and the ribbon runs underneath to `J12`. That is what makes the
10mm faceplate gap workable: neither mated plug has to fit inside it. So:

- **Put the faceplate header over the cutout.** A 2x5 IDC plug is about 20 x 9mm; the hole
  is 24 x 12.
- **The case floor needs about 15mm below the main board** around `J12` and the cutout: a
  9.2mm header plus the mated plug and the ribbon's fold.

| pin | net | |
|---|---|---|
| 1 | `MSP_TEST` | |
| 3 | `MSP_RST` | driven by MCP23017 `U4` |
| 5 | `MSP430_RXD` | Daisy A3 (UART4 TX) → MSP430 |
| 7 | `MSP430_TXD` | MSP430 **drives** → Daisy A2 (UART4 RX) |
| 9 | `P3V3_MSP430` | its own AMS1117 (`U6`) on the main board |
| 2,4,6,8,10 | GND | |

The order runs backwards from the original (pin 1 was 3V3) because flipping the header to
the back mirrors it; every net kept its hole and its routing. **Pin 1 is the ribbon's red
stripe** — check it end to end with the faceplate header's orientation before ordering
that board.

**No I2C and no IRQ cross the cable** (`pin-allocation.md`, superseding design-state §9).
There is **no 5V** on it unless someone adds it before the main board is ordered.

### 6. MSP430

- UART on UCA0 at its **default** pins (P1.4 TXD / P1.5 RXD, pins 4/5), per
  `pin-allocation.md`. UART and I2C do not share pins (Q2, resolved).
- **Q21 is still marked OPEN and blocks layout**: the BSL's factory-fixed pins must be the
  ones the runtime UART uses. Moving to the default mapping should have settled it —
  confirm against SLAU550 and close it first.
- Q22: plan the crystal. SBW pads (TEST, RST, 3V3, GND) and test points on TX/RX/RST/TEST.

### 7. Optional LEDs (discussed 2026-09-23, not decided)

One LED per zone, 16 in all. On the existing 3.3V pin they must be red, amber or yellow at
about 5mA each (80mA all on); white, blue or RGB need the 5V pin above. Drive from the
MSP430 (2x 74HC595, or a TLC59116 on its I2C). Put the light **beside** the zones through
small windows, not behind the electrodes, and **never PWM during a touch scan**.

## Contents (expected)

```
vuulgaris-faceplate.kicad_pro / .kicad_sch / .kicad_pcb
pads.svg          exported from ../../mockups/comb-pad-generator.html, true mm scale
pads-ti.dxf       SLAA891 OpenSCAD output, for cross-checking pads.svg
```

## Pad geometry

Authoritative spec is [ADR 0003](../../docs/decisions/0003-comb-pad-rx0-wraparound.md).
Summary: 4 channels, 5 segments, 4 zones, order `RX0 RX1 RX2 RX3 RX0`, 12mm wide. **Length is
derived, not chosen:** the Salamis composition locks `pad length = 12 x pad pitch`, so it
follows the inter-pad gap ([Q17](../../docs/notes/open-questions.md)). Working value **216mm**
at a 6mm gap, 80 teeth at 2.19mm pitch, minimum copper 0.15mm enforced.

Generate with `../../mockups/comb-pad-generator.html`. It exports SVG at true mm scale with
one `<g>` per net, which imports cleanly as separate copper zones.

**Cross-check against TI's own SLAA891 OpenSCAD output before committing copper.**

## Pin order is load-bearing

`RX0->E00, RX1->E01, RX2->E02, RX3->E03`. Generate the assignment in Design Center **first**,
then lay out to match. A swapped pair produces garbage interpolation on a board that passes
every electrical check.

## Per-electrode ESD network

5 electrodes x 4 pads = **20 of each**:
- 470R-1k series resistor per electrode
- TPD1E10B06 TVS between electrode and ground, on the **electrode side** of the resistor

Place near the MCU with a low-impedance ground path.

## Layout checklist

- [ ] No ground pour under electrodes or their traces
- [ ] RX0 end groups connected as one net, return on L2, not under electrodes
- [ ] MCU centred on the pad group, trace lengths equalised
- [ ] No electrode within the edge keepout
- [ ] Digital lines exit the opposite edge from the electrodes
- [ ] Minimum copper 0.15mm everywhere, no slivers at ramp ends
- [ ] CAPTIVATE-PGMR connector present
- [ ] 4 SBW test pads present (TEST, RST, 3V3, GND)
- [ ] Test points on UART Tx/Rx, RST, TEST (there is no IRQ line — `pin-allocation.md`)
- [ ] Soldermask opening over all pad copper
- [ ] Usable scrub region marked inside the copper, or copper extended past the printed scale
      (endpoint trim eats a few mm at each end)
