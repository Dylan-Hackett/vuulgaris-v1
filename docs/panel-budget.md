# Panel budget

**Status: WORKING.** Not yet a decision. Feeds the faceplate layout before copper.

Opened 2026-08-06 when the control count reached 12 and the panel stopped closing.

## Superseded envelopes

Earlier working proposals (Envelope A ~285 x 155mm, Envelope B ~190 x 220mm) predated the
supplied Salamis composition. Both assumed a free hand with the layout. The composition now
fixes the ratios, so panel size follows from the inter-pad gap rather than from packing.

## The problem with 219 x 110mm

The size recorded in `design-state.md` section 11 does not fit the current design.

| Item | Height | Note |
|---|---|---|
| 4 pads at 12mm | 48mm | Pad width from [ADR 0003](decisions/0003-comb-pad-rx0-wraparound.md) |
| 3 inter-pad gaps at 10mm | 30mm | **Estimate.** See "Assumptions to confirm" below. |
| **Pad block subtotal** | **78mm** | of 110mm available |
| Remaining strip | **32mm** | for screen, 12 controls, encoder, 2 switches |
| 2.42" OLED module | ~40mm | **Estimate.** Exceeds the strip on its own. |

The display alone does not fit in what the pads leave, before a single control is placed.

## Decisions taken

- **Format: desktop / standalone.** Height and width are both free. Not Eurorack 3U, so the
  128.5mm panel constraint does not apply.
- **Layout: the full Salamis Tablet composition**, per
  `mockups/salamis-faceplate-reference.svg` (supplied 2026-08-06). A straight divider rule separating a
  five-rule control group above from four scrub pads below, vertical dividers, semicircles,
  tick divisions per pad with crosses, and Greek acrophonic numerals in the left, right and
  bottom margins. (The reference had 11 ticks with crosses at 3/6/9; now 13 with crosses at
  4/7/10, see below.)

## The composition locks the scale

Measured from the reference SVG:

| Element | Units | As a ratio |
|---|---|---|
| Panel | 580 x 300 | **1.933 : 1** |
| Pad length | 420 | 0.724 of panel width |
| Pad pitch (centre to centre) | 35 | **pad length = 12.0 x pitch** |
| Upper region (five-rule group) | 110 tall | 0.367 of panel height |
| Lower region (pads) | 190 tall | 0.633 of panel height |
| Tick divisions | 11 at 42 units | crosses at 3rd, 6th, 9th. **Now 13, see below.** |

### The 12:1 ratio was an artefact, and is discarded

Measuring the reference gave `pad length = 12 x pad pitch`, which briefly looked like a hard
constraint tying the inter-pad gap to the size of the whole instrument.

**It was not a design decision.** The reference sketch drew the pads as **single strokes with no
thickness**, so 420/35 was an accident of how the drawing was made. Once pads have a real 12mm
width and real spacing, nothing holds the ratio.

**Discarded 2026-08-06. Pad length and inter-pad gap are now independent parameters.**

Two consequences, both good:

1. **The gap no longer sets the product's size.** [Q17](notes/open-questions.md) drops back to
   being what it always should have been: a crosstalk question about vertical spacing inside a
   fixed lower region.
2. **The gap is free to be electrically generous.** It now costs nothing but blank panel.

**Settled: 216mm pads, 9mm gap, 298 x 154mm panel.**

### The pads are centred on the panel width

**Corrected 2026-08-06.** The reference sketch was asymmetric: **90 units of left margin against
70 of right**, which put the pads **5.143mm right of panel centre** (46.286mm left margin,
36.000mm right). Now **41.143mm both sides**.

The pad vertical divider and its upward semicircle now **derive from the pad midpoint**, so they
follow the pads rather than sitting at a fixed reference coordinate. That also guarantees the
divider always coincides with the centre tick.

**The upper region is left as drawn.** The rule group starts 5.1mm from the left edge and the
OLED ends 8.2mm from the right, so the control strip is mildly asymmetric too. That is a
composition question rather than a geometry error, and it has not been touched.

### The divider rule is straight

**Changed 2026-08-06.** The reference drew the upper/lower divider as an **irregular crack
line**, echoing the real Salamis Tablet, which is physically cracked. It is now a **single
straight rule** spanning the panel.

Worth noting for the record that this is the one place the layout departs from the artifact
rather than interpreting it. The crack was the most literal reference to the original object.

## Vertical spacing: pads fill the lower region

The pad block is **distributed through the lower region rather than packed at the top**.

| | |
|---|---|
| Lower region (divider rule to bottom, less margins and the numeral row) | **75.2mm** |
| 4 pads at 12mm | 48mm |
| 3 gaps at **9mm** | 27mm |
| **Block** | **75.0mm**, filling it with 0.2mm to spare |

**9mm is the maximum that fits**, and it is not a compromise. The design state's crosstalk
guidance was **>=10mm closest approach**, so spreading the pads for visual reasons moved the
geometry *toward* the electrical guidance rather than away from it. The earlier 6mm figure was
well under it.

## This reverses the 150mm pad decision

Pads were shortened from 175mm to 150mm to buy panel area. **The composition wants them
longer, not shorter**: 216mm at the working proposal.

That is fine electrically. TI demonstrated 300mm on four electrodes, so 216mm is well inside
the envelope, and a longer pad gives more scrub travel per unit of sample time. The earlier
reasoning was sound for a controls-above-pads layout; it does not apply once the pots move into
the side margins.

**ADR 0003 pad length should follow whatever gap Q17 returns**, not a fixed number chosen in
advance.

## Control layout in the upper region

**Decided 2026-08-06: OLED off to the right, all 12 knobs grouped together.**

The knobs **stand on the ruled lines**, on rules 2 and 4 of the five. This is not decoration
reused as a background: the Salamis Tablet is a **counting board**, and its rules are exactly
where the counting pebbles were placed. Knobs on the rules is what the object was for. An empty
rule group with controls elsewhere would be the less faithful option.

**The vertical divider does real work too.** In the original it separates number registers.
Here it separates the **8 channel pots** (left) from the **4 envelope pots** (right), with the
downward semicircle at its foot as drawn.

At 298 x 154mm, the upper band is 56mm tall and the full 298mm wide:

| Zone | Width | Contents |
|---|---|---|
| Channel knob block | 82mm | **8 channel pots**, 4 columns x 2 rows at 22mm centres. One column per channel. |
| Vertical divider | | With downward semicircle at rule 5 |
| Envelope knob block | 68mm | **2 x 2** on rules 2 and 4 (attack, release, CV amt L, CV amt R) plus the **offset** knob alone on rule 3 |
| **2 vertical switch slots** | 28mm | 9 x 20mm each, centred on rule 3 so each slot crosses rules 2 to 4 |
| **OLED** | 70mm | |

The whole upper assembly is **laid out in millimetres and centred**, with a uniform 6mm gap
between groups.

### The two switches do two different jobs

**Clarified 2026-08-07**, after they were described wrongly as a pair of VCF/VCA switches.

| Slot | Switch | Selects |
|---|---|---|
| 1 | **LPG mode** | stereo VCF or stereo VCA |
| 2 | **Source** | resample or external input |

**Neither is a per-channel switch.** The LPG is one **stereo** unit, so mode is a *single*
decision applied to both sides: a **DPDT toggle, one pole per channel, ganged on one actuator**,
exactly as [ADR 0007](decisions/0007-buchla-lpg-over-serge-vcfq.md) specifies. Two independent
mode switches would allow L in VCF while R is in VCA, which is not a mode, it is a fault. The
source switch is DPDT for the same reason: pole A carries L, pole B carries R.

Both are **analog routing on the LPG board and cost zero Daisy pins**, which is part of why the
16-GPIO budget closes.

### The encoder moved out of the upper strip

**Changed 2026-08-06.** It now sits in the **right margin beside the pads, directly below the
OLED**, in the lower region.

| | |
|---|---|
| Centre | 277.71, 99.68mm |
| Clearance right of the pads | 11.37mm |
| Margin to the panel edge | 11.37mm, so it is centred in the right margin |
| Clearance from the right-side pad numerals | 9.37mm |
| Vertically | centred on the pad block |

It also sits **horizontally within the OLED's span**, so screen and encoder read as a pair
despite being on opposite sides of the divider rule.

### The switch openings are vertical

**Changed 2026-08-06.** Two **9 x 20mm** slots, rounded to a stadium, centred on rule 3 so each
one **crosses rules 2, 3 and 4**. On a counting board that reads as a counter column, which is
a better fit than a horizontal opening cutting across the rules.

**The offset knob stands alone on the centre rule, larger than the others.** That is deliberate:
it is a **dual-gang analog pot** wired into the LPG and never read by the Daisy, so it is
architecturally different from every other control on the panel. Giving it its own position and
size says so without a label.

### Silkscreen the channel numerals on the knob columns

**The knob columns do not spatially correspond to the pads.** Channels run as *columns* in the
knob block but as *horizontal rows* in the pad group, so channel I's knobs are top-left while
channel I's pad is the top row. Nothing about the geometry makes that mapping obvious.

The composition already solves this: the Greek acrophonic numerals **I, II, III, IIII** label
the four pads in the margins. **Carry the same numerals above the four knob columns.** Free in
silkscreen, and it makes the mapping legible without adding any element foreign to the design.

### Tick divisions

**13 per pad**, crosses at the **fourth, seventh and tenth**. Settled 2026-08-06 after a brief
detour through 12.

Why 13 rather than 12: **13 marks gives 12 equal intervals, so there is a true centre mark.**
12 marks gives 11 intervals and no centre, which broke the pad's vertical divider alignment.

Verified on the generated output at 216mm:

| | |
|---|---|
| Marks | 13, evenly spaced at **exactly 18.00mm** |
| Intervals | 12 equal divisions of the sample |
| Centre mark (7th) | **154.286mm**, coincides exactly with the pad vertical divider |
| Crosses (4th, 7th, 10th) | **0.250, 0.500, 0.750** of pad length |

### The bottom numerals had to move with the crosses

**Corrected 2026-08-06.** They read **ΙΙΙ (3), ΠΙ (6), ΠΙΙΙΙ (9)**, which labelled the crosses
under the old 11-mark scheme. Once the crosses moved to marks 4/7/10 both the **values and the
positions** were wrong: they sat at 0.200 / 0.500 / 0.800 of the pad against crosses at
0.250 / 0.500 / 0.750.

Now **ΙΙΙΙ (4), ΠΙΙ (7), Δ (10)**, generated directly from `CROSS_AT` and placed on the cross
marks, so they cannot drift out of sync again.

Attic acrophonic system, verified: **Ι = 1, Π = 5** (from ΠΕΝΤΕ), **Δ = 10** (from ΔΕΚΑ). The
generator has an `attic(n)` helper rather than hardcoded glyph strings.

**The crosses moved from 3/6/9 to 4/7/10, and that is the faithful translation, not a change.**
The reference put crosses at centre and centre plus/minus 3 (marks 3, 6, 9 of 11, where 6 was
the centre). With 13 marks the centre is the 7th, so centre plus/minus 3 is 4, 7, 10. Same
relationship to the composition, and it happens to land them on clean quarters.

12 equal divisions is also the more useful number for a scrub instrument: **the divisions are
what [Q1](notes/open-questions.md) repeatability is measured against**, and quarters are the
positions a player will actually aim for.

### Drawings

| File | Use |
|---|---|
| `mockups/generate-faceplate.py` | **The one to use.** Parametric, true-scale mm, real comb teeth, one `<g>` per net. |
| `mockups/faceplate-v1-298x154.svg` | Generated output: 216mm pads, 9mm gap, 13 ticks. |
| `mockups/salamis-faceplate-dimensioned.svg` | Schematic view, pads as plain bands. Easier for composition review. |
| `mockups/salamis-faceplate-reference.svg` | The supplied layout, unmodified. |

## Faders vs rotary pots

**Faders cost panel area, they do not save it.** Asked and answered with real dimensions.

| Control | Body | Panel area each |
|---|---|---|
| 9mm rotary pot (Alpha RD901F) | ~10 x 12mm | ~18 x 18mm with knob = **324 mm2** |
| 30mm-travel slide pot | ~45 x 8mm | ~15 x 45mm = **675 mm2** |
| 45mm-travel slide pot | ~60 x 9mm | ~15 x 60mm = **900 mm2** |

12 faders at 45mm travel: one row is 180mm wide, or two rows of 6 is 90 x 120mm. **That 120mm
does not fit the 78mm lower band**, so faders push the panel roughly 40mm taller. 30mm-travel
versions reach 90 x 90mm, still over.

**Verdict:** faders are a deliberate aesthetic spend, not a space saver. The argument *for* them
is that vertical faders rhyme visually with the horizontal scrub pads, and they show state at a
glance. That is a real reason, but it costs panel height and roughly doubles the control BOM
line.

## Assumptions to confirm before layout

1. **Inter-pad gap.** [Q17](notes/open-questions.md), and it now sets the size of the whole
   instrument rather than just the panel height. The 10mm figure in the old budget above was
   extrapolated from the design state's ">=10mm closest approach" guidance, which was written
   for the *diagonal* layout where pads converge at a point. Parallel pads sit at closest
   approach along their whole length, so the real requirement may differ in either direction,
   and **a grounded guard strip between pads may allow a tighter gap.**
   **How to close:** lay out **two** pads on the test board at two or three candidate gaps,
   with and without a guard strip, and measure crosstalk. Nearly free.
2. **OLED module outline height.** [Q18](notes/open-questions.md). The design state records only
   the **active area**, 55.01 x 27.49mm. These are bare panels with an FPC tail and the glass
   outline is larger. The ~42mm used above is an estimate. It has to fit the 56mm rule-group
   band, so there is margin, but confirm before committing.
3. **22mm pot centres.** Comfortable for 9mm pots with small knobs. Tighter is possible with
   smaller knobs, at the cost of feel. At 22mm the six-pot blocks are 66 x 44mm and fit the side
   margins with room.
4. **Pad copper width 12mm.** From [ADR 0003](decisions/0003-comb-pad-rx0-wraparound.md). If
   this changed, every number in the scaling table moves with it, since pitch = width + gap.

## Knock-on effects

- **Pad length and gap are independent.** The 12:1 ratio is discarded. Changing the gap moves
  vertical spacing only; it does not resize the instrument.
- **Longer pads are a gain, not a cost.** 216mm gives more scrub travel than the 150mm that was
  briefly settled on, and is well inside TI's demonstrated 300mm.
- **Endpoint trim still eats a few mm at each end.** Copper extends past the printed scale per
  [ADR 0003](decisions/0003-comb-pad-rx0-wraparound.md), so the eleven printed divisions stay
  inside the well-behaved middle region. **The tick divisions are exactly what
  [Q1](notes/open-questions.md) repeatability is measured against.**
- **Resolution is unaffected.** Slider resolution is configurable and the real limit is jitter,
  not length.
- **`design-state.md` section 11 is stale** on board size (219 x 110mm) and pad length (175mm).
