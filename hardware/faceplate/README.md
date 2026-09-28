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
- **+5mm more at the bottom (back) edge — DECIDED 2026-09-27: yes, 137.81mm.** "Board +
  14" leaves 1mm behind the board, but the board slides in along y and needs 6mm of
  travel to clear the jacks (`design-state.md`, "Assembly": cavity 125.81 = 1 + 118.81 +
  6), so the box is 137.81 outside. A 132.81 panel on that box stops 5mm short of the
  back wall's outer face: its back screws (3mm in) would land over the cavity, and pad 4
  would end 0.36mm from the wall's inner face. The 5mm goes on below pad 4 and **moves no
  coordinates**. The cost is look: the pad block now sits 6.36mm below the divider and
  11.36mm above the bottom edge. Re-centring it would move ENC0 and SW4–SW9, which are
  centred on the pad block, so it stays.

Pads — **RECONCILED 2026-09-27: the generator's geometry, 10mm wide, 8mm gap, 18mm
pitch, 100 teeth.** See "Pad geometry" below and ADR 0003. Both candidates sat on the
same 18mm pitch, so the pad centres (and ENC0, centred on them) come out identical
either way; this was a sensing decision, not a placement one.

### 2. Stack-up: the pots are the datum, and the faceplate is structural

- Faceplate underside **10.0mm** above the main board (the pots' mounting surface),
  **1.6mm** thick, outer face at 11.6mm.
- **Do not go thicker.** The pots (Alpha RD902F) have 3.4mm of M7x0.75 thread above the
  outer face, for a 1.8mm nut plus washer.
- The six pot nuts are the **only** clamp. Encoders (EC12, 0.9mm of bushing through),
  toggles, buttons and the OLED locate but carry nothing. The whole main board hangs off
  the faceplate through those six nuts (`design-state.md`, "Panel mounting").
- **The 10mm gap is shared.** Anything on the faceplate's back (the MSP430, the ESD network,
  LEDs, the connector) sits in the same 10mm as the main board's top-side parts beneath it.
  The tall ones, board coordinates (panel = board + (6.995, 9.000) once §1's offset is in):

  | main-board part | height | board bbox x0,y0 – x1,y1 | faceplate room above |
  |---|---|---|---|
  | `C36`, `C37` electrolytics | 7.8mm | 190–200, 72.8–90.9 | ~2.2mm |
  | `C32`, `C33` electrolytics | 5.4mm | 190–201, 50.1–68.3 | ~4.6mm |
  | `U1` Daisy Patch SM | ~7mm soldered direct (no 3D model) | 243.8–283.9, 47.2–115.4 | ~3mm |
  | `VT301`/`302`/`401`/`402` vactrols | unknown (no 3D model) | 132.6–165.3, 58.0–67.8 and 134.9–167.5, 91.1–100.9 | read the Xvive drawing |

  Everything else on the main board's top is under 3.5mm apart from the panel parts, which
  pass through. Keep faceplate back-side parts low over those areas, or put them elsewhere.
  **The Daisy must be soldered in or on low-profile sockets** — standard 8.5mm sockets put
  it near 13mm and into the faceplate.

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

- **Put the faceplate header over the cutout, centred on board (222.0, 103.5)** — panel
  (228.995, 112.5) once §1's offset is in. A 2x5 IDC plug is about 20.3 x 9mm; the hole is
  24 x 12, so 1.5–2mm clear per side. Checked 2026-09-26: `J12` is centred on the cutout
  in x (0.00mm), its body 1.44mm from the cutout's edge, nothing sits in the cutout, and
  nothing else is on the main board's back in the ribbon's path.
- **`J12`'s pin 1 is at its +x end (right, viewed from the top), on the row nearest the
  cutout.** Orient the faceplate header so the ribbon takes pin 1 to pin 1 — mock it up
  with a real cable before ordering; the two plugs sit at different depths, so it is easy
  to get backwards on paper.
- **`U7` (the DKM10, ~10mm tall, on the back) is 1.03mm from `J12`'s far side.** A plug
  sits inside the header's shroud, so it fits; run the ribbon out toward the cutout, not
  toward `U7`.
- **Leave the ribbon slack.** The faceplate end is plugged in with the faceplate lifted and
  then lowered onto the pots, so the cable folds under the main board rather than spanning
  the 12mm between the plugs taut.
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
There is **no 5V** on it, by decision (ADR 0012).

### 6. MSP430

- UART on UCA0 at its **default** pins (P1.4 TXD / P1.5 RXD, pins 4/5), per
  `pin-allocation.md`. UART and I2C do not share pins (Q2, resolved).
- **Q21 CLOSED 2026-09-27.** SLAU550 §3.1 defers the BSL pins to the device datasheet;
  SLASEO5D Table 9-4 gives the UART BSL as **P1.4 transmit / P1.5 receive**, PT pins 4/5
  (Figure 7-1). The runtime UART and the BSL are the same two wires. The remapped
  P5.1/P5.2 (44/45) fallback is **dropped**: it only ever covered the BSL being elsewhere,
  and `J12` has no free position to carry it.
- **47k pull-ups on P1.4 and P1.5.** They are also TCK/TMS, and SLAU550 §3.3.2.1 warns that
  floating TCK/TMS raise the odds of landing in JTAG mode; the pull-ups also stop RXD
  floating while the Daisy boots. SLAU550's 1nF pull-downs are left off: they target the
  hardware entry sequence, which production never uses (blank-device detection, then
  software invocation).
- Q22: plan the crystal. SBW pads (TEST, RST, 3V3, GND) and test points on TX/RX/RST/TEST.

### 7. LEDs — DECIDED 2026-09-27: none. See ADR 0012.

No LEDs on this faceplate, and no 5V on `J12`. The main board orders as it is. What was on
the table (2026-09-23): one LED per zone, 16 in all, red/amber on 3.3V or white/RGB on a
new 5V pin, driven from the MSP430 through shift registers, lit beside the zones through
small windows and never PWM'd during a touch scan.

## Contents (expected)

```
vuulgaris-faceplate.kicad_pro / .kicad_sch / .kicad_pcb
pads.svg          from ../../mockups/generate-faceplate.py, true mm scale
pads-ti.dxf       SLAA891 OpenSCAD output, for cross-checking pads.svg
```

## Pad geometry

Authoritative spec is [ADR 0003](../../docs/decisions/0003-comb-pad-rx0-wraparound.md).
Summary: 4 channels, 5 segments, 4 zones, order `RX0 RX1 RX2 RX3 RX0`.

**Settled 2026-09-27**, and what `../../mockups/generate-faceplate.py` draws:

| | |
|---|---|
| Pad length | 216mm, independent of the gap (the "12 x pitch" lock was an artefact — Q17) |
| Pad width | **10mm** |
| Gap / pitch | **8mm / 18mm** |
| Teeth | **100** (25 per zone), 2.160mm pitch, 1.950mm wide, 0.21mm apart |
| Top-to-bottom gap | 0.20mm |
| Tooth fillet | 0.6mm, with the bar heights area-compensated so it does not bend the position curve |
| Min copper | 0.15mm enforced; the thinnest bar drawn is 0.197mm |

Why 10/8 rather than the old 12/6: the gap is the untested crosstalk variable (Q17) and
wants to be as wide as the pitch allows; bare copper already gives more signal than TI's
overlay designs, so 12mm buys sensitivity that is not needed at the cost of base
capacitance; and ratio encoding reads a finger that rides high or low across the pad as a
position error (top bars are RX0/RX2, bottom RX1/RX3), which a pad closer to a fingertip's
width keeps smaller. The old "80 teeth at 2.19mm" was the 175mm pad's number; at 216mm, 80
teeth would be 2.70mm.

The copper comes from `generate-faceplate.py`, not `comb-pad-generator.html`, whose
defaults are the superseded 175mm / 12mm pad. Its SVG is true mm scale with one `<g>` per
net.

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
