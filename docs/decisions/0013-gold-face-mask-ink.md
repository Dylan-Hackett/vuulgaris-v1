# 0013 - The faceplate's front is exposed gold on ground; the art is black soldermask

**Status:** Accepted
**Date:** 2026-09-29

## Decision

The whole front of the faceplate is **exposed ENIG on a grounded copper face**, not
soldermask. Dylan's call: an all-gold panel with the markings still showing, and the pads
separated from the surrounding copper.

- **The face:** one GND zone on F.Cu (`FACE_GOLD`), solid, over the whole outline less two
  things. Each pad's **2mm frame** of mask: the copper stops 1.9mm from the pad and the mask
  overlaps it by 0.1, so no bare laminate shows. And a **masked panel** right of the pads, from
  the divider rule down, which hides the 46 routing vias in the right margin.
- **The markings are black soldermask**, not silk. The fab prints no silk on bare copper. So
  every rule, divider, tick, cross and numeral is a line of mask left standing in the gold's
  mask opening. The only silk is the right-hand pad numerals, white on the masked panel.
- **Vias stay open**, not filled and capped. The pads' bar vias stay open as ADR 0003 has them.
  The four stitch vias show as open holes in the gold. The two signal vias that sit in the
  gold, the UART hops, are covered by a dot of mask.
- **The gold's only ground is four stitch vias** between the corridor's TXD and RXD lanes. The
  corridor between pads 3 and 4 is the one place the face lies over the L3 plane with room on
  B.Cu. The zone's island removal is "always", so if the stitches ever fail to connect, the
  gold fills to nothing rather than float.

The generator owns the layout (`face()`, `scale_marks()`, `panel_art()`, all in
`mockups/generate-faceplate.py`). `hardware/faceplate/design/mkface.py` builds it, last in the
pipeline. `tools/panelcheck.py` samples every mask stroke against the board's own mask
polygons.

## Why ground, and why a gap

**Floating copper is ruled out.** An unconnected face beside four self-capacitance electrodes
couples them to each other through it, and a finger on one pad reads on its neighbours.

**The gap is the one number that matters.** ADR 0003's rule was no ground pour **under** the
electrodes or their traces, since parallel-plate capacitance is the dominant parasitic, and
that still holds. Nothing of the gold is under a pad. The fan-in lines on L2 run in the right
margin, which is the masked panel with no gold. The pad buses run under their own pads. What
the pads do see is coplanar ground 1.9mm from their edges all round, which adds fringe
capacitance. Bare copper under a finger gives a large signal, so this is expected to cost
sensitivity rather than break it. It is not measured.

**The strip between pads is a grounded guard.** Q17 guessed that one might allow tighter pad
spacing. Here it sits in the 8mm gap anyway (4mm of gold between frames) and should cut
pad-to-pad crosstalk.

## What it moved

- **The scale** now hangs from each pad's frame: `scale_top_mm` 0.65 to 2.0. The crosses'
  uprights start on the frame's edge and the ticks start 0.5 below it. The generator checks
  every mark sits on the gold. The numeral row under pad 4 moved from 6.4 to 7.8.
- **The side numerals** moved from 2 to 2.8mm off the pad ends. That puts the left ones on the
  gold clear of the frame, and the right ones on the panel, clear of the diodes' ground vias
  at x 281.55.
- **The pad divider** stands 2.2mm proud of the frames, not the pads, so it still shows inside
  pad 1's dome.
- **Copper to edge** went from 0 to 0.3mm, in the faceplate's `.kicad_pro` rule. JLC wants
  0.2. Without it, the fill ran to every hole's edge. Now each hole and the board edge carry a
  thin black ring.
- The silk scale and silk art (`mkscale.py`, `mkart.py`, 2026-09-29) are gone. Their strokes
  are the same ones, now printed in mask.

## Consequences

- **Order black soldermask** (JLC, about +$8), white silk, ENIG, vias tented. Not POFV: it
  would cap the pads' vias too.
- **The knob, encoder and switch nuts and washers sit on the gold** and bond their bushings to
  GND. The panel screws bond to it too, into brass inserts in the printed case, which are
  isolated.
- **Mask ink minimums:** the thinnest stroke is 0.18 (the rules), above JLC's 0.13mm black
  mask dam. Openings narrower than 0.1 are closed rather than left as slivers.
- **The face is part of Q1.** If a pad reads short or noisy, widen `pad_frame_mm`. That is
  one number in the generator; `mkface.py` and the checks follow it. 3mm leaves 2mm of gold
  between frames.
