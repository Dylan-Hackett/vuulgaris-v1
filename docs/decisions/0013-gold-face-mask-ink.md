# 0013 - The faceplate's front is exposed gold on ground; the art is black soldermask

**Status:** Accepted
**Date:** 2026-09-29 (revised the same day: the masked right panel shrank to a small via
patch, and the corridor stitch vias went)

## Decision

The whole front of the faceplate is **exposed ENIG on a grounded copper face**, not
soldermask. Dylan's call: an all-gold panel with the markings still showing, and the pads
separated from the surrounding copper.

- **The face:** one GND zone on F.Cu (`FACE_GOLD`), solid, over the whole outline less each
  pad's **2mm frame** of mask. The copper stops 1.9mm from the pad, and the mask overlaps it
  by 0.1 so no bare laminate shows.
- **The markings are black soldermask**, not silk. The fab prints no silk on bare copper. So
  every rule, divider, tick, cross and numeral is a line of mask left standing in the gold's
  mask opening.
- **A small via patch:** one mask rectangle right of the pads covers the 44 routing vias of
  the right margin. It is flush with the frames, from the top of pad 1's to the bottom of pad
  4's, and runs to x 294.5, just past the network grid's last vias. The right-hand pad
  numerals print on it in **white silk**, the only silk on the face. Gold shows above it,
  below it and past its right edge. (It was a panel from the divider rule to the board's
  bottom and right edges. Dylan: too much of a block.)
- **Every other via outside the pads gets a black dot** of mask, 0.4 beyond its copper.
  That covers three vias, all at the right end of the gap between pads 3 and 4: the two UART
  hops and one GND via. The pads' own bar vias stay open, as ADR 0003 has them, and no via is
  filled and capped.
- **The gold runs on under the patch** and is grounded there, by the margin's GND vias; the
  TVS grounds are among them. Island removal is "always", so the gold fills to nothing rather
  than float if they ever fail to join it.

The generator owns the layout (`face()`, `scale_marks()`, `panel_art()`, all in
`mockups/generate-faceplate.py`). `hardware/faceplate/design/mkface.py` builds it, last in
the pipeline. `tools/panelcheck.py` samples every mask stroke against the board's own mask
polygons.

## Why ground, and why a gap

**Floating copper is ruled out.** An unconnected face beside four self-capacitance electrodes
couples them to each other through it, and a finger on one pad reads on its neighbours.

**The gap is the one number that matters.** Nothing of the gold is under a pad, and the pad
buses run under their own pads. What the pads see is coplanar ground 1.9mm from their edges
all round, which adds fringe capacitance. Bare copper under a finger gives a large signal, so
this is expected to cost sensitivity rather than break it. It is not measured.

**Under the patch the gold is over the fan-in lines, on purpose.** ADR 0003 says no pour
under electrodes or their traces, because parallel-plate capacitance is the dominant
parasitic. Here that costs roughly 70pF/m: gold about 0.2mm above a 0.15mm line, on JLC's
standard stack-up. Over fan-in runs of 35mm or less, that is 1–2.5pF a line. That is small
next to the 12pF the TVS already puts on every electrode (24pF on RX0, which has two; ADR
0004). CapTIvate calibrates each element against its own baseline. What it buys is a
**screen**: without it, a hand resting on the margin couples through 0.2mm of laminate into
whichever pad's lines run beneath it. That would bias the position of a pad being played.

**The strip between pads is a grounded guard.** Q17 guessed that one might allow tighter pad
spacing. Here it sits in the 8mm gap anyway (4mm of gold between frames) and should cut
pad-to-pad crosstalk.

## What it moved

- **The scale** now hangs from each pad's frame: `scale_top_mm` 0.65 to 2.0. The crosses'
  uprights start on the frame's edge and the ticks start 0.5 below it. The generator checks
  every mark sits on the gold. The numeral row under pad 4 moved from 6.4 to 7.8.
- **The side numerals** moved from 2 to 2.8mm off the pad ends. The left ones sit on the gold
  clear of the frame; the right ones, in silk, clear of the vias under them. On the gold the
  right ones could not work: the grid's column 0 vias (x 280.7 and 281.55) sit exactly where
  they go, and a dot beside a numeral reads as one blob. That is what the patch is for.
- **The pad divider** stands 2.2mm proud of the frames, not the pads, so it still shows inside
  pad 1's dome.
- **Copper to edge** went from 0 to 0.3mm, in the faceplate's `.kicad_pro` rule. JLC wants
  0.2. Without it, the fill ran to every hole's edge. Now each hole and the board edge carry a
  thin black ring.
- The silk scale and silk art (`mkscale.py`, `mkart.py`, 2026-09-29) are gone. Their strokes
  are the same ones, now printed in mask.

## Consequences

- **Order black soldermask** (JLC, about +$8), white silk, ENIG, vias tented. JLC's "plugged"
  default should also do: every dot is 0.4 beyond its via, past the 0.35 its plugging needs,
  and it leaves vias with openings (the pads') open. Not POFV: that would cap the pads' vias.
- **The knob, encoder and switch nuts and washers sit on the gold** and bond their bushings to
  GND. The panel screws bond to it too, into brass inserts in the printed case, which are
  isolated.
- **Mask ink minimums:** the thinnest stroke is 0.18 (the rules), above JLC's 0.13mm black
  mask dam. Openings narrower than 0.1 are closed rather than left as slivers.
- **The face is part of Q1.** If a pad reads short or noisy, widen `pad_frame_mm`. That is
  one number in the generator; `mkface.py` and the checks follow it. 3mm leaves 2mm of gold
  between frames.
