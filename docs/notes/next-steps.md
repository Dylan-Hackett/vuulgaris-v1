# Next steps

From `../design-state.md` section 12, reordered so the cheap thing that could invalidate
everything else comes first.

---

## 0. The one that gates the rest

**Validate the sensing concept cheaply before committing.**

Buy CAPTIVATE-PGMR, plus the FR2676 board and CAPTIVATE-BSWP. Make one cheap 2-layer JLC
board with **two pads in final tooth geometry, ~216mm long**. Roughly $50 and 2 weeks.

Measure: **scan time, jitter in counts at rest, linearity.** Then hear what it sounds like
driving sample position.

This tells you whether the interaction works before the faceplate exists. **If one pad
works, the remaining unknown is arithmetic on the measured number.** If it does not, you
have spent $50 instead of a faceplate spin.

**Lay out TWO pads on that board, not one.** The second pad costs almost nothing and answers
[Q17](open-questions.md) (how tight the inter-pad gap can be), which currently gates the panel
layout to the tune of up to 30mm of height. Include two or three candidate gap widths, with and
without a grounded guard strip.

Notes on the kit:
- CAPTIVATE-BSWP is listed as required for evaluating self-cap designs and gives a
  reference slider baseline worth having for comparison.
- The FR2676 board has a 48-pin sensor panel connector for plugging in your own test pad.
- FR2676 is the same silicon for touch purposes, just 64KB/8KB against the FR2675's 32KB/6KB.
- Design Center projects target a specific device. **Regenerate for FR2675 (PT/LQFP-48)**
  when moving to your own board. CAP pin *naming* carries over; physical pins do not.
- Design Center is 1.83.00.08, dated May 2020. Stale toolchain, and the release notes say
  to re-create projects made in earlier versions.

---

## Blocking layout

**Q2, Q3, Q4, Q6 are closed.** What is left before copper:

1. **Generate the slider electrode assignment in Design Center first**, then lay out the PCB
   to match. `RX0->E00, RX1->E01, RX2->E02, RX3->E03`. Swapped pins give garbage
   interpolation on a board that passes every electrical check.
2. **Cross-check the comb pad generator against SLAA891's OpenSCAD output.** Export DXF from
   TI's scripts, diff against the generator's SVG, before committing copper.
3. **Update `mockups/faceplate-mockup.html`.** It still draws the **3-zone / no-wraparound**
   electrode ramp (E1->E4). It needs the 4-zone RX0-wraparound pattern from
   [ADR 0003](../decisions/0003-comb-pad-rx0-wraparound.md) before it drives layout.
4. **Verify the LCSC C2052972 footprint against the datasheet PT package drawing.**
   A 10-minute check that prevents a dead board.
5. **Lay out per [../pin-allocation.md](../pin-allocation.md).** It is resolved and safe to
   build against. Do not forget **VREG on pin 31 needs an external decoupling cap** (it is the
   CapTIvate regulator output, not a supply input), and the **dividers on BSL RST/TEST**.

---

## Blocking BOM

6. **Second-source the display.** 27 units at LCSC is not a production quantity.
   [Q7](open-questions.md#q7-production-quantity-sourcing)
7. **Order the DPDT switches and bench-confirm their pinout with a multimeter** before
   silkscreening labels. Lever direction is inverted relative to the pin it selects.

---

## Firmware, can proceed in parallel

8. **Scope B5/B6 through the BSL dividers before writing any BSL code.**
   [Q13](open-questions.md#q13-do-the-gate-outputs-drive-bsl-cleanly-through-a-divider)
9. **Test the OLED + bootloader combination early.**
   [Q10](open-questions.md#q10-oled-dead-under-bootloader)
10. **Decide the sample-storage strategy concretely.** Factory samples in QSPI so the
    instrument makes sound with no card; user samples on SD; both into SDRAM at load; playback
    always from SDRAM. **Decide the advertised per-track length limit**, which is bounded by
    SDRAM, not card size.
11. **Use a SoftPot as a bench stand-in** to develop scrubbing feel and the sampler engine
    before cap-touch hardware exists. It is a bad product part and a fine dev tool.

---

## Not yet on any list

- **Enclosure.** Not in the BOM at all. The prior design was CNC walnut. This is cost lever #3
  and currently an unbounded number.
- **Vactrol bleed.** Solve it deliberately in the schematic rather than rediscovering it on
  assembled hardware.
- **Vactrol matching procedure.** Four cells matched in on-resistance *and* decay across L
  and R. Either a measurement-and-bin process, or VTL5C3/2 duals so each stereo pair comes
  from one package.
- **No CV or gate jacks, ever, without a respin.** All four gate pins are consumed by internal
  functions under [ADR 0009](../decisions/0009-io-plan-12-adc.md). Worth being sure about
  before the panel is drawn.
