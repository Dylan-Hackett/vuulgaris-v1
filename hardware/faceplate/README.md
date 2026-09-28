# Faceplate PCB

4-layer, **ENIG**. Carries the four capacitive scrub pads on L1 and the MSP430FR2675 on
the back. Panel geometry comes from `../../mockups/generate-faceplate.py` — see the
handoff below for the size, which is not what older docs say.

## Status — 2026-09-28: placed, ready for routing

**Schematic done**, `mksch → netcheck` 145/145 over 41 nets, every block traced to a TI or
manufacturer figure in `design/design.py`. 54 parts: `U1` MSP430FR2675TPT; `C1`/`C2`
10µF + 100nF on DVCC, `C3` 1µF on VREG, `R1`/`C4` 47k + 1nF on RST (SLASEO5D Figures
10-1, 10-4); `R2`/`R3` 47k on P1.4/P1.5 (SLAU550 §3.3.2.1); `Y1` FC-135 + `C5`/`C6` 22pF
(Figure 10-2); the sixteen CapTIvate lines, **one pin from each block per pad**, each
through a TPD1E10B06 to GND on the electrode side and a 470R series resistor (`D11`–`D44`,
`R11`–`R44`, CapTIvate design guide); `E1`–`E4` the pads as symbols (RX0 on pins 1 and 5,
one net); `TP1`–`TP6` SBW and UART pads; `J1`.

**Pad copper is on the board** (2026-09-28): `E1`–`E4` are generated footprints, one via
per bar (763 vias, 37 bridges), from `design/mkpads.py`; ADR 0003, "Connecting the bars".
boardcheck parity is 0 over 145. **Every part is placed** (`design/mkplace.py`, one-shot; see
"Layout" below) and DRC is 0 errors apart from the ratsnest (`drc.py --unrouted`). **Routing
is Dylan's.**

**`J1` is the hanxia HX JN2.54-2x5P TP H8.9, LCSC C41376028** (chosen 2026-09-28).
It has to be SMD: `J12`'s through-hole C5665 here would put ten pins through the **front
face**, in the 8mm gap between pads 3 and 4. It is Extended: JLC's Basic filter returns no
SMD 2x5 box header at all. Footprint `IDC-SMD_10P-P2.54_C41376028` is from hanxia's
drawing (`datasheets/hanxia-HX-JN2.54-2x5P-TP-H8.9.pdf`): pads 1.02 x 4.65 on 2.54mm,
11.50 overall; body 20.30 x 8.90, **9.60mm seated**, under the 10mm gap. The runner-up,
XFCN BH254VS-10P (C492446), is 10.5mm tall. The drawing marks pin 1 only by a triangle
on the key wall, so the footprint puts pin 1 on the key-side row at that end, as KiCad's
DIN 41651 footprint and `J12` both do. **Pin 1 and the key are settled from both
manufacturer drawings** (2026-09-28, §5).

## The loop

Same tools as the main board, with `--project faceplate` (`../kicad/tools/proj.py`).
From `hardware/kicad/`, with `set -o pipefail` whenever output is piped:

```bash
python3 tools/mksch.py --project faceplate && python3 tools/netcheck.py --project faceplate
python3 tools/boardcheck.py --project faceplate   # board pads vs netmap parity
python3 tools/drc.py --project faceplate          # KiCad's own DRC -- the clearance authority
python3 tools/drc.py --project faceplate --unrouted   # while placed but not routed: the ratsnest is not a failure
python3 tools/panelcheck.py --project faceplate   # outline, holes, OLED window, J1, the cable, pad copper, vias, walls
```

**Pad copper** is regenerated, never hand-edited: change `mockups/generate-faceplate.py`
(its `--check` must pass), then, under KiCad's Python,
`hardware/faceplate/design/mkpads.py` rewrites the four `SCRUB_PAD_216x10_Pn` footprints
and replaces `E1`–`E4` and every via on a `PADp_RXn` net. panelcheck fails if the board's
pads or vias differ from `copper()` by more than 1µm, or if the generator's via keepouts are
not exactly `J1`'s pad rows.

- **Intent** is `design/netmap.json`; **symbols, sheet positions, footprints** are
  `design/design.py`; values `design/values.json`. Never hand-edit the `.kicad_sch`.
  `J1`'s netmap was derived from the main board's `J12`, pin for pin — the ribbon is
  straight through — and `panelcheck` fails if the two ever disagree.
- **`panelcheck`** is this board's `place.py --check`. It derives everything from the
  generator, the placement file, and the main board itself (its `J12` and the Edge.Cuts
  cutout). Parts not placed or not yet sized are **TODO**, not failures; run it with
  `--strict` before plotting a fab package and every TODO fails.
- **Pin cache:** `design/kpins.json` is untracked. Rebuild it, from the repo root, with
  exactly this argument list (stock libraries first, the shared project library last):

  ```bash
  python3 hardware/kicad/tools/ksym.py --project faceplate /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/*.kicad_sym hardware/kicad/lib/vuulgaris.kicad_sym
  ```
- **The board** was bootstrapped once by `design/mkboard.py` (KiCad's Python; it refuses
  to overwrite). From here it is edited like the main board's: scripted through pcbnew,
  or by hand in Pcbnew — and after a script writes, **File → Revert** before touching it.
- **Coordinates:** the faceplate board is drawn in panel coordinates, sheet = panel +
  (100, 50) (`panelgeo.FACE_ORG`). Panel y runs from the jack edge.
- The library is **shared** with the main board (`../kicad/lib/`, via this project's
  `sym-lib-table` / `fp-lib-table`). Footprints named `lib:name` in `design.py` come
  from elsewhere; a bare name means `vuulgaris.pretty`.
- DRC ran with one warning while `J1` was KiCad's stock footprint, which does not
  resolve in headless pcbnew. With the real part in the project library it is 0 and 0.
- Every check has been watched failing: a swapped netmap pin (netcheck, panelcheck), a
  track shorting pins 1 and 3 (DRC, boardcheck), `J1` moved 0.5mm or turned 180°, a pot
  hole 0.5mm undersize or 0.3mm off (panelcheck).

## Handoff from the main board — 2026-09-24

The main board is finished: DRC clean, fab package at `../vuulgaris-v1-fab.zip`. What
follows is fixed by it. The faceplate works around these, not the other way round.

### 1. Size: the generator is the source of truth — DONE 2026-09-27, 298.286 x 137.81mm

`generate-faceplate.py` gives **298.286 x 137.81mm**: the 130.81mm composition frame
(`composition_h_mm`, "board + 14" as of 2026-08-26) plus `panel_top_extra_mm` 2.0 and
`panel_bottom_extra_mm` 5.0, both pure extensions. `--check` re-derives with the extras
zeroed and fails if any placement row moves other than y += 2, and asserts the cavity is
1 + 118.81 + 6. Numbers still in circulation that are **superseded**: 130.81, "~285 x 155",
"298 x 154" (`panel-budget.md`). The mockup SVGs are now `mockups/faceplate-v1.svg` and
`faceplate-v1-FAB.svg`; they were `-298x139`, which was never their size.

- **+2mm at the top (jack) edge — DONE 2026-09-27.** Every one of the 24 rows in
  `../placement-panel-facing.txt` moved +2.000 in y and nothing else (compared in integer
  thousandths), `OY` went 7.000 → 9.000 in the same commit, and `place.py --check` reports
  all 24 on their holes with output identical to before; with the old `OY` it reports all
  24 off by 2.0. What the requirement was: The main board's top edge moved out 2mm on
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
| encoders `ENC1`–`ENC8` (EC12E) | **9.5mm** | ALPS EC12E2430803 drawing: body 5.5, then 7mm of M9x0.75 -- the static thread passes the faceplate; M9 + 0.5, the pots' margin |
| encoder `ENC0` (EC11L) | **10.0mm** | ALPS EC11L1525G01 drawing (LE2115L02G): **no thread** -- a 7mm bushing ends 9.5mm up, then a knurled 9.03mm shaft that turns and pushes 1.5mm passes the faceplate. Running clearance |
| OLED `DS1` | **window, 60.09 × 33.90mm**, r 1.0 corners, panel (208.50, 15.15)–(268.59, 49.05) | §4; the generator's `oled_window()` |

The generator draws **no pot or encoder holes at all** — the r=8 and r=9.2 circles in the FAB
SVG are knob outlines, not cuts. The board's holes are drawn by `design/mkholes.py` from
`panelgeo.holes()`, and the OLED window from `panelgeo.oled_window()` (2026-09-28).
panelcheck `--strict` has no TODO left.

### 4. OLED

The module is **68 x 43mm on its own PCB, 4.2mm tall**, active area 55.01 x 27.49mm. It will
be raised **3–5mm** on a 1x9 socket plus four M3 standoffs in the corner holes already on
the main board. **Nylon standoffs, not metal:** the lower-left hole (297.55, 94.05) has a
`POS12V` trace on F.Cu 2.2mm from its centre, under the standoff's hex base, and a metal
one would put +12V a scratch of soldermask away from the module's mounting hole. The
other three holes have no copper within 3mm on either side. Its face then sits about **2.4–4.4mm** behind the
outer surface; at 5.8mm of lift it hits the faceplate. This answers Q18.

**The window — sized 2026-09-28** by the generator's `oled_window()`, from the HS242L01
drawing (datasheets/, section 1.4: PCB **72** × 43 — the spec table's "68 × 43" is the hole
pitch; AA 55.01 × 27.49 centred along the long axis, **5.11mm below the top edge and 10.4mm
above the bottom**; glass 62.1 × 39.85) and the stack-up. The lift is not chosen, so it is
sized at the **deepest**, 3mm: face 4.4mm below the outer surface.

| | |
|---|---|
| active area, panel | x 211.04–266.05, y 17.16–44.65 |
| window | x 208.50–268.59, y 15.15–49.05 (60.09 × 33.90), r 1.0 |
| AA in view, at 4.4mm deep | 45° from the player's side, 30° from the sides, 25° from the back |
| never nearer the glass edge than | 1.0mm, so past the pixels you see black glass, not the module PCB |

It is lopsided on purpose: the wide black band on the glass, where the flex bonds, is on
the player's side, which is the side that needs the margin. panelcheck checks the drawn
window against the generator, and the generator's module centre against the main board's
four `DS1` holes. **No chamfer:** JLC cannot bevel an internal cutout in FR4; the walls are
straight 1.6mm, and a hand bevel is optional.

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
  cutout.** Orient the faceplate header so the ribbon takes pin 1 to pin 1 — the two plugs
  sit at different depths, so it is easy to get backwards on paper. Done below.

  **Paper mock-up, 2026-09-28** (both boards read through pcbnew, panel coordinates):

  | | centre | pin 1 | odd row | key (slot) | faces |
  |---|---|---|---|---|---|
  | main `J12` (C5665) | (228.995, 100.5) | +x end | +y | +y wall (footprint silk) | down, from the main board's back |
  | faceplate `J1` (hanxia) | (228.995, 112.5) | +x end | +y | +y wall (hanxia drawing) | down, from the faceplate's back |

  The two headers are the **same orientation**, 12mm apart in y and at different heights;
  the cutout is on `J12`'s +y side, `U7` on its −y side (y 82). So the cable is a plain
  straight 10-way IDC ribbon, both sockets pressed on the **same face**, red stripe at the
  triangle on both. It leaves `J12`'s socket toward +y (the cutout, away from `U7`), sags
  under the main board, and rises into `J1`'s socket from its −y side: no fold, no twist.
  Pin mapping then does not depend on the sockets at all -- each is keyed into an
  identically oriented header, so wire n lands on pin n at both ends, whatever the socket's
  own convention.

  That argument needs both headers to carry the key on the same side of pin 1 -- were
  C5665's on the other wall, a keyed socket would sit 180° round at `J12` and the cable would
  map pin n to 11−n, `P3V3_MSP430` onto `GND`. **Closed from both manufacturer drawings,
  2026-09-28:** hanxia's (`datasheets/hanxia-HX-JN2.54-2x5P-TP-H8.9.pdf`) and BOOMELE's for
  C5665 (`datasheets/BOOMELE-C5665-2x5-box-header.pdf`, from JLC's part page -- LCSC's link
  is dead) both mould the pin-1 triangle on the **keyed wall**, at one end. So the key is on
  the pin-1 row on both parts, which is what both footprints assume (`J12`'s silkscreen,
  `J1`'s Fab notch). C5665's drawing also confirms `J12`'s 1.0mm holes on the 2.54 grid.
  What is left is assembly, not design: use a straight cable, both sockets on the same face,
  red stripe to the triangle. Plugging in the first real cable is still a free sanity check.
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

## Contents

```
vuulgaris-faceplate.kicad_pro / .kicad_sch / .kicad_pcb
sym-lib-table, fp-lib-table   point at ../kicad/lib, shared with the main board
design/netmap.json            the intent
design/design.py              symbols, sheet positions, footprints (read by mksch.py)
design/values.json            Value fields
design/mkboard.py             the one-shot board bootstrap
design/mkpads.py              pad footprints + E1-E4 + their vias, from the generator's copper()
design/mkplace.py             the one-shot placement of everything else (the table above)
design/mkholes.py             the panel holes on Edge.Cuts, from panelgeo.holes()
design/mklib_faceplate.py     the faceplate's own library parts (U1, Y1, the TVS, the pad symbol);
                              the pin table twice (Figure 7-1, Table 7-1), checked equal
DRC.rpt                       from tools/drc.py --project faceplate
```

The SLAA891 cross-check came back as a connectivity finding, not a geometry one: TI's
elements are single bodies and ours are ratio-encoded islands, so there is no TI pattern to
diff against (ADR 0003, "Connecting the bars").

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

## Layout — placed 2026-09-28

Settled with Dylan, in order: (a) one open via per bar (ADR 0003, "Connecting the bars");
(b) `U1` and its networks in the **right margin**, not the centre (ADR 0003, layout rules);
(c) the UART, 3V3, RST and TEST from `J1` along the **gap between pads 3 and 4**.

All parts on B.Cu. The margin strip is panel x 277.14 (copper ends) to 292.29 (the wall's
inner face, where the faceplate rests on the wall top — panelcheck fails any back-side part
past it), over the Daisy (~3mm clear; nothing here is over 1.6mm). Positions are Dylan's
Pcbnew adjustments of 2026-09-28 (grid +1.25 / −0.25, the corner group lowered), with RX3's
column, `Y1` and `C3` brought back in; `design/mkplace.py` records them.

| where (panel) | what |
|---|---|
| `U1` (284.45, 104.0) | CAP pins 23–39 face **up**, digital corner (46–5) down-right. Pins 1–5 run right to left along the bottom, 46–48 up the right side |
| the 4 × 4 grid over the CAP pins, rows y 83.15–95.15 | the 16 networks. **Column = CapTIvate block** (RX0–RX3 at x 280.75 / 283.95 / 288.45 / 290.92, each over its own pins: CAP0 = 23–26 … CAP3 = 36–39), **row = pad** (1 at the top). Each cell is the TVS directly on top of its 470R, TVS pin 1 over R pin 1, ground pin to the right (ADR 0004: the order and a short ground are what count, and both sit by the MCU) |
| middle channel, over pin 31 | `C3` 1µF VREG |
| across the corner by pins 1 / 48 | `C2` 100nF |
| right edge, y ~112–115 | `Y1` stood on end, `C5` (XIN) / `C6` (XOUT) lying beside its two pads |
| where the lines from `J1` enter the margin | `C1` 10µF, then `C4` / `R1` (RST RC) |
| in the gap by `J1`, x 242–265 | `TP1`–`TP6` in one row, silk-labelled `TEST RST 3V3 GND TX RX`; then `R2` / `R3` (UART pull-ups) |

Pitches come from the silk (R0603's box is 1.47 × 2.93), not the library's small courtyards,
so no reference or body overlaps another: 0 silk overlaps. The 31 silk-over-copper warnings
are the library's R/C pin-1 dots, clipped by the mask, as on the main board. The 470Rs'
references stand on end beside them; the TVS and test pad references are on B.Fab.

**What to route:**

1. **Pads → margin, on L2.** Each net's vias are collinear: top-bar vias 0.5mm below the pad's
   top edge, bottom-bar vias 0.5mm above its bottom edge (shorter bars at mid-bar). Run each net's
   bus straight under its own bars, then carry it on to the pad's right end under the same pad:
   top edge RX0 (zone 1) → under RX2 → joins RX0 (zone 4); RX2 → under zone-4 RX0; bottom edge
   RX1 → under RX3. Nothing crosses under another pad ([Q24](../../docs/notes/open-questions.md)).
   Pad 3's bottom vias under `J1` sit ~2.2mm in from the edge; pad 4's first five zone-4 RX0 bars
   have no via (bridged along the edge). No ground under any of it.
2. **The grid:** each line lands on its cell's TVS pin 1 / R pin 1 (a via from L2), TVS pin 2
   takes a short GND via on its right, and the R's pin 2 runs **down the left side of its column**
   to the pin. Every column does the same, and that order reaches 23–39 round both corners with no
   crossing: the outermost trace in each column goes to the farthest pin.
3. **The gap between pads 3 and 4, on L4:** `MSP430_TXD`, `MSP430_RXD`, `MSP_RST`, `MSP_TEST`,
   `P3V3_MSP430` from `J1` past the test pads to the margin, over an L3 GND strip ~3mm wide on
   the gap's centreline.
4. **Crystal:** XIN (47) and XOUT (46) down `U1`'s right side, XOUT on the outside (over the wall
   band is fine: copper only).
5. GND: L3, hatched in the margin, and **not under the pads**.

## Pin order is load-bearing

`RX0->E00, RX1->E01, RX2->E02, RX3->E03`. Generate the assignment in Design Center **first**,
then lay out to match. A swapped pair produces garbage interpolation on a board that passes
every electrical check.

## Per-electrode ESD network

4 CapTIvate lines x 4 pads = **16 of each** (settled 2026-09-28; was 20, see ADR 0004):
- RX0's two end groups join on the electrode side, first
- TPD1E10B06 TVS between that electrode net and ground
- 470R-1k series resistor from there to the CapTIvate pin

Place near the MCU with a low-impedance ground path.

Each pad takes **one pin from each CapTIvate block** (`RXn` of pad `p` to `CAPn.(p-1)`), not
one block; `../../docs/pin-allocation.md` has the table and TI's source.

## Layout checklist

- [ ] No ground pour under electrodes or their traces
- [ ] RX0 end groups connected as one net, return on L2, not under electrodes
- [x] MCU placement: right margin, not centred (ADR 0003, layout rules, 2026-09-28)
- [ ] No electrode within the edge keepout
- [x] Digital lines: along the gap between pads 3 and 4 to `J1`, which the main board fixes
      (ADR 0003); UART quiet during scans ([Q23](../../docs/notes/open-questions.md))
- [x] Minimum copper 0.15mm everywhere, no slivers at ramp ends (0.165mm, bridged)
- [x] CAPTIVATE-PGMR connection: `J1` itself, by jumpering the ribbon's `J12` end to the
      PGMR (ADR 0005, revised 2026-09-28). No separate connector.
- [x] 4 SBW test pads present (TEST, RST, 3V3, GND): `TP1`–`TP4`, beside `J1`
- [x] Test points on UART Tx/Rx, RST, TEST (there is no IRQ line — `pin-allocation.md`): `TP5`, `TP6`
- [x] Soldermask opening over all pad copper (one opening per pad; vias open both sides)
- [ ] Usable scrub region marked inside the copper, or copper extended past the printed scale
      (endpoint trim eats a few mm at each end)
