# Mockups

## comb-pad-generator.html

**Parametric generator for the scrub pad copper.** Open in any browser, no build step.

Live-checks the geometry against fab limits and **exports SVG at true mm scale with one
`<g>` per net**, which imports into EasyEDA/KiCad as separate copper zones.

**The tool defaults to 175mm, which is not current.** Pad length is now **derived** from the
inter-pad gap via `pad length = 12 x pad pitch`
([ADR 0003](../docs/decisions/0003-comb-pad-rx0-wraparound.md)). Working value **216mm** at a
6mm gap, giving 54mm zones. **Do not regenerate until [Q17](../docs/notes/open-questions.md)
settles the gap**, since zone length, tooth pitch and tooth count all follow from the length.

Other geometry is unchanged: 12mm wide, 4 zones, minimum copper 0.15mm enforced.

> **Cross-check its output against TI's SLAA891 OpenSCAD scripts before committing copper.**
> Those generate TI's own validated pattern and export DXF. Two independent generators
> agreeing is worth the hour it costs.

## salamis-faceplate-reference.svg

**The agreed layout as supplied**, 2026-08-06. Full Salamis Tablet composition: an irregular
crack line dividing a five-rule control group above from four scrub pads below, vertical dividers, semicircles,
eleven tick divisions per pad with crosses at the third, sixth and ninth, Greek acrophonic
numerals in the left, right and bottom margins.

Measured proportions, which now drive the panel size:

| Element | Units | Ratio |
|---|---|---|
| Panel | 580 x 300 | 1.933 : 1 |
| Pad length | 420 | **12.0 x pad pitch** |
| Pad pitch | 35 | |

**`pad length = 12 x pad pitch` is the load-bearing relationship.** Pitch is 12mm of copper plus
the inter-pad gap, so the gap sets the size of the whole instrument. See
[../docs/panel-budget.md](../docs/panel-budget.md).

## generate-faceplate.py  <-  the one to use

**Parametric, true-scale faceplate generator.** Emits SVG in **real millimetres** (1 user unit
= 1mm), including the actual comb-tooth electrode geometry.

```bash
python3 generate-faceplate.py                          > faceplate-v1-298x154.svg
python3 generate-faceplate.py --check                  # verification report, no SVG
python3 generate-faceplate.py --set pad_length_mm=264  # one-off override
```

### How to change the layout

**Edit the `CFG` dict at the top of the file. That is the whole interface.** Every dimension,
every position and both placement flags live there. Nothing in the drawing code needs touching.

| Want to change | Edit |
|---|---|
| Panel size | `pad_length_mm` (panel derives from it) |
| Pad spacing | `pad_gap_mm` |
| Tick count, cross positions | `n_ticks`, `cross_at` |
| Knob size or spacing | `knob_r_mm`, `knob_pitch_mm`, `offset_knob_r_mm` |
| Switch openings | `switch_w_mm`, `switch_h_mm` |
| Encoder position | `encoder_lower_right` (True = beside pads, False = upper strip) |
| Divider style | `straight_divider` (False restores the irregular crack) |
| Tooth density | `teeth_per_zone` |
| Inscription | `inscription`, `inscription_h_mm`, `salamis_marks` |

### Always run `--check` after a change

It re-derives and asserts **14 properties**, each of which has gone wrong at least once during
design:

```
  OK  pads centred on panel width          margins 41.143 / 41.143mm
  OK  centre tick == pad divider           149.143 vs 149.143
  OK  tick spacing even                    [18.0] mm
  OK  crosses on clean fractions           [0.25, 0.5, 0.75]
  OK  pad block fits lower region          75.0 in 75.2mm
  OK  min copper bar >= fab floor          0.2360 vs 0.15mm
  OK  every tooth pair sums to pad width   11.80mm
  OK  upper assembly centred               content 266.00, margins 16.14mm
  OK  encoder clears pads / centred / within OLED span
  OK  switch slots vertical
  OK  OLED inside panel
```

Exit code is non-zero on failure, so it can gate a build.

### The copper it generates

Per [ADR 0003](../docs/decisions/0003-comb-pad-rx0-wraparound.md): **100 teeth per pad**
(25 per zone x 4 zones), 2.16mm pitch, 1.95mm tooth width. Each tooth splits into a top and a
bottom bar whose heights ramp complementarily from the presence functions, so **total copper per
tooth is constant along the pad**.

Output is grouped **one `<g>` per net** (`RX0`, `RX1`, `RX2`, `RX3`) for import as separate
copper zones.

**Minimum bar drawn is 0.236mm against the 0.15mm fab floor**, so no sliver ever needs dropping
at 100 teeth. Sampling at tooth centres rather than edges is what avoids it.

### The Salamis inscription

**Plain single letters, left margin only, below the divider rule.**

```
T P X F H F A N G F C T X
```

Codes in `CFG["inscription"]`: `T` tau, `P` rho, `X` chi, `F` digamma-like, `H` eta,
`A` alpha, `N` pi, `G` gamma, `C` lunate sigma.

### Two wrong turns, recorded so they are not repeated

**First pass** read the photo correctly as plain letters but drew them alongside an invented
Χ/Η/Δ/Π/Ι denomination ladder and a row of compound glyphs along the bottom.

**Second pass over-reasoned.** It theorised the F-like and gamma-like shapes were **compound
Attic numerals**, a Π nesting a smaller Χ, Η or Δ. That produced visually busy glyphs that did
not match the photo. The theory was plausible from the numeral system, but the photo shows a
few clean incised strokes per character, not nested forms. **Direct observation should have
outranked the theory.**

**Current version returns to the plain letters** and draws them with fewer, cleaner strokes.

**Still uncertain:** the F-shapes could be digamma, heta or a damaged gamma. All are drawn the
same rather than inventing a distinction the scan cannot support. Worth checking against a
high-resolution photograph before copper. `CFG["inscription"]` is a plain string.

**Drawn as strokes, not typeset.** The Ancient Greek codepoints have unreliable font coverage
and this file goes to a fab, where font substitution is a real risk.

**Placement.** `inscription_left_only` suppresses the right column. `inscription_below_divider`
keeps every letter under the divider rule. Both asserted in `--check`.

### Departures from the reference

- **The divider rule is straight**, not the irregular crack of the original tablet.
  `straight_divider = False` restores it.
- **The pads are centred.** The reference had 90 units of left margin against 70 of right.
- **The encoder sits in the lower region**, right margin beside the pads, below the OLED.
- **The two switch openings are vertical** (9 x 20mm), crossing rules 2 to 4.
- **13 tick divisions**, crosses at 4/7/10 rather than 3/6/9 of 11. Numerals are **generated
  from `cross_at`** via an `attic(n)` helper, so labels cannot drift out of sync with marks.

### What it is NOT, yet

**Do not send this to a fab as-is.** Three things stand between it and copper:

1. **Pad length is provisional** until [Q17](../docs/notes/open-questions.md) settles the gap.
2. **Cross-check against SLAA891.** TI's OpenSCAD scripts export DXF; two independent
   generators agreeing is the real validation.
3. **Electrode-to-pin assignment comes from Design Center first**, then the PCB is laid out to
   match. This file draws geometry, not net assignment.

No drill file, no board outline layer, no soldermask openings, no copper pour.

## salamis-faceplate-dimensioned.svg## salamis-faceplate-dimensioned.svg

**Schematic view**, pads drawn as plain bands rather than teeth. Easier to read for composition
review than the full generated file. Same 298 x 154mm working proposal.

**Control layout, decided 2026-08-06:** OLED at the right end, all 12 knobs grouped together
**standing on rules 2 and 4** of the five-rule group. The **vertical divider separates the 8
channel pots (left) from the 4 envelope pots (right)**, with the downward semicircle at its
foot as drawn.

Knobs on the rules is faithful rather than convenient: the Salamis Tablet is a counting board
and the rules are where the pebbles sat.

**Channel numerals I, II, III, IIII are silkscreened above the four knob columns**, matching the
pad numerals in the margins. Channels run as columns in the knob block but as rows in the pad
group, so without the numerals the mapping is not legible.

## faceplate-mockup.html

Faceplate rendering: the **Salamis Tablet** layout, drawn at 219 x 110mm.

> **Superseded** by `salamis-faceplate-reference.svg` above. This one draws the 3-zone /
> no-wraparound electrode ramp and a 219 x 110mm board, neither of which is current.

Four parallel pads as the line group, with the tablet's vertical divider, semicircles,
crosses at divisions 3/6/9, and Greek acrophonic numerals in the margins. Above an irregular
crack line sits a five-rule group with a vertical divider and downward semicircle for the
screen, encoder and switches. Below, four scrub pads with a vertical divider crossing all
four, capped by an upward semicircle.

> **This is out of date and must not drive layout.** It still draws the **3-zone /
> no-wraparound** electrode ramp (E1->E4, 60 teeth). It needs the **4-zone RX0-wraparound**
> pattern from [ADR 0003](../docs/decisions/0003-comb-pad-rx0-wraparound.md) first.
> Tracked as step 5 in [next-steps.md](../docs/notes/next-steps.md).

**Note:** this file is an HTML *fragment* (a `<div>` with inline SVG), not a full document.
Browsers render it fine on open. Wrap it in `<html><body>` if you need it to validate.

## Superseded layout, for the record

Two pads each side, two diagonal one way and two the other, forming a separated triangle in
the middle of a rectangular enclosure. If it is ever revisited:

- A 216mm pad at 45 degrees needs **~153mm per axis**, so the enclosure would need roughly
  300mm in the diagonal-spanning direction.
- Convergence points create **worst-case crosstalk exactly where RX0 sits on both pads.**
  Keep closest approach >=10mm with a grounded strip between.
