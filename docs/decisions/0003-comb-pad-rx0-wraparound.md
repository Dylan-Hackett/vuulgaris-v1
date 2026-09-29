# 0003 - Comb-tooth pads with RX0 wraparound

**Status:** Accepted
**Date:** pre-2026-08-05 (recorded retroactively from design state section 3)

## Decision

Vertical **comb teeth**, not a horizontal zigzag boundary. Each tooth splits into a **top
bar and a bottom bar** whose heights ramp complementarily. Position is encoded by the
copper ratio between the two halves.

**4 channels, 5 segments, 4 interpolation zones.** Order along the axis:
`RX0, RX1, RX2, RX3, RX0`.

Presence functions, `t` running 0 to 4 across the pad:

```
RX0 = max(0, 1-t) + max(0, t-3)     <- appears at BOTH ends
RX1 = max(0, 1-|t-1|)
RX2 = max(0, 1-|t-2|)
RX3 = max(0, 1-|t-3|)
```

These sum to 1 everywhere, so total copper per tooth is constant along the pad.

## Why ratio-encoded comb teeth

Position comes out **linear by construction** rather than approximated. A finger always
spans many teeth, so tooth quantisation never reaches the reported position value.

## Rules that are not optional

- **RX0 is one net.** Both end groups must be connected on the board. TI requires this for
  the default slider algorithm to work. Route the return on the layer below, **never under
  the electrodes.**
- **Vertical placement alternates** so a strip never stacks the same channel: top half gets
  RX0 or RX2, bottom half gets RX1 or RX3. This puts RX0 on top in *both* end zones, which
  keeps the pattern consistent across the wrap.
- **Minimum copper enforcement.** Near a ramp end, one bar's computed height falls below
  the fab limit. Do **not** draw it as a sliver: sub-0.127mm copper etches away or comes
  out fragile. Drop the bar and hand its height to the surviving bar, which is already the
  dominant channel at that point. The position ramp is unaffected. (At 100 teeth no bar
  falls below the floor; the thinnest, 0.197mm, are bridged — see "Connecting the bars".)
- **Pin assignment order is not arbitrary: RX0->E00, RX1->E01, RX2->E02, RX3->E03.**
  Generate the assignment in Design Center **first**, then lay out the PCB to match.
  Swapped pins produce garbage interpolation.

## Working dimensions

**Settled 2026-09-27** for the faceplate PCB. `mockups/generate-faceplate.py` draws exactly
this; the table used to carry 12mm / 6mm gap / 80 teeth at 2.19mm, which were the 175mm
pad's numbers.

| | |
|---|---|
| Pad length | **216mm.** Independent of the gap: the `12 x pad pitch` lock measured off the reference sketch was an artefact of pads drawn as zero-width strokes ([Q17](../notes/open-questions.md)). Was 175mm, then 150mm; both superseded. Inside TI's demonstrated 300mm. |
| Pad width | **10mm** (10-12mm is the useful band) |
| Inter-pad gap | **8mm**, so an 18mm pitch |
| Zone length | pad length / 4 = **54mm** |
| Teeth per zone | **25, so 100 total** |
| Tooth pitch | **2.160mm** |
| Tooth width | **1.950mm** |
| Tooth-to-tooth gap | 0.21mm |
| Top-to-bottom gap | 0.20mm |
| Tooth fillet | 0.6mm, bar heights area-compensated so the fillet does not bend the position curve |
| Min copper width | 0.15mm, enforced; thinnest bar drawn is 0.197mm |

Wider than 12mm raises base capacitance without helping a lengthwise scrub.

**Why 10mm and not 12.** The pitch is 18mm either way, so width and gap trade one for one.
The gap is the untested crosstalk variable (Q17) and wants every millimetre. Bare copper
already gives a larger signal delta than TI's overlay designs (ADR 0004), so the extra
width buys sensitivity that is not needed and costs base capacitance. And ratio encoding has
a weak spot across the pad: top bars are RX0/RX2 and bottom bars RX1/RX3, so a finger
riding high or low reads as a position error, alternating in sign zone by zone. It is
continuous, so it does not break monotonicity, but it varies with where each player's
finger lands, which is the repeatability term Q1 cares about. A pad closer to a fingertip's
width keeps it smaller. That last point is reasoning about the geometry, not a TI figure.

## Connecting the bars — decided 2026-09-28

The generator draws every bar as its own island: 200 per pad, 800 on the board, nothing
joining them on L1. TI's SLAA891 slider elements (Figure 4) are each one continuous body,
so there was no TI pattern to cross-check this against; the question was how each island
reaches its net. Two options were weighed: a spine along each long edge (a true comb, 5
pieces per pad, 20 vias outside the scrub surface) or **one via per bar**. Chosen: **one
via per bar**, keeping the settled geometry.

- **Open through vias**, 0.3mm drill / 0.5mm pad, **not filled or capped** (Dylan's call),
  and open on the back too — a via open at one end only traps plating chemistry. They show
  as 0.3mm dots in the copper.
- Via centre 0.5mm in from the bar's **outer** edge (the pad edge), capped at mid-bar, so a
  net's vias line up for a straight L2 bus. The hole is copper the finger does not see; it
  goes into the same area compensation as the fillets.
- A bar too short for the via pad (the 0.197mm slivers, two either side of each zone
  boundary) is **bridged** along the pad edge to its same-net neighbour, and shortened to
  pay for the bridge's copper.
- **Keepout:** through vias come out on the back, and `J1` sits there over the edges of
  pads 3 and 4. Inside `J1`'s pad rows a via walks inward along its bar until it clears;
  the thin RX0 bars at the start of pad 4's zone 4 cannot, and are chain-bridged to the
  first bar past `J1`.
- `--check` measures the emitted area ratio with fillets, holes and bridges all counted:
  0.00mm worst error. Uncompensated, holes alone cost 0.72mm and bridges 2.02mm.

Totals: 763 vias, 37 bridges. The copper enters KiCad as four generated footprints
(`hardware/faceplate/design/mkpads.py`), one per pad.

**The L2 buses run under their own net's bars**, so they add almost nothing: a net's bus
is shielded above by its own electrode, and there is no ground under the pads. Where a bus
has to continue past its own stretch (RX1 under RX3, RX2 under zone-4 RX0, RX0's join under
RX2) it runs under elements of the same pad, which are scanned in the same cycle with the
same waveform: close to a driven shield. That reasoning still needs confirming against the
CapTIvate Technology Guide. It is what makes the right-margin MCU placement work (Layout rules).

## Resolution and the thing that actually limits it

Resolution is configurable: set 1000 and you get positions 0-999 across the pad, which at the
216mm working length is 0.22mm per step, well beyond 10-bit.

**The real limit is jitter, not resolution.** If reported position wanders N counts at
rest, usable points = 1000/N. That is the number to measure. Smoothing fixes it at the cost
of latency, a direct tradeoff, since scrub position jitter becomes audible warble.

## Endpoint trim

Most slider layouts cannot reach 0 and max at the physical extremes, because a finger's
centroid does not align with the slider endpoint. `Lower_Trim` / `Upper_Trim` correct this,
tuned by touching each end and observing.

**Plan for a few dead millimetres at each end.**

**Decided 2026-08-06: extend copper past the printed scale.** The design originally offered
two options, the other being to mark the usable region inside the copper. The Salamis Tablet
faceplate carries printed division marks (crosses at 3/6/9, Greek numerals in the margins),
and a finger on a printed mark is expected to land at the corresponding point in the sample.
Extending the copper keeps **every printed division inside the well-behaved middle region**
and out of the trim zone.

That matters more than it first appears: trim at the ends is **finger-size dependent**,
because a large finger's centroid cannot reach as close to the pad edge as a small one. It is
the one error term that does not cancel in the ratio and cannot be calibrated away for all
players at once. Keep the marks away from it.

## Tools

- `mockups/generate-faceplate.py` - **the source of the copper.** Draws the pads in place on
  the panel, true mm scale, one `<g>` per net, and `--check` asserts the fab floor and the
  fillet compensation on the emitted geometry.
- `mockups/comb-pad-generator.html` - the earlier single-pad tool, live checks against fab
  limits. Its defaults are the superseded 175mm / 12mm pad.
- TI **SLAA891** OpenSCAD scripts generate TI's own validated pattern and export DXF.
  **Use these to cross-check the generator's output before committing copper.**

## Layout rules (TI design guide)

- Keep MCU-to-electrode traces short. Trace length adds parasitic capacitance and noise
  susceptibility. This is why the MCU is on the faceplate.
- **Do not ground-pour under electrodes or their traces.** Parallel-plate capacitance to a
  nearby pour is the dominant parasitic contributor. Hatched ground at distance if needed.
- Decoupling caps and ESD parts right at the MCU.
- Route digital lines to the main board away from electrodes, ideally exiting the opposite edge.
  **Not possible here (2026-09-28):** `J1` is fixed by the main board in the gap between pads
  3 and 4. The UART, 3V3, RST and TEST run from it along that gap on L4, fanned 1.3mm apart
  with the test pads on them, over an L3 ground strip under all five lines, 0.75mm clear of
  both pads' copper (it was to be ~3mm wide and 2.5mm clear, before the lines spread to take
  the test pads), into the right margin. The gap carries nothing else. Firmware keeps the UART
  quiet during scans ([Q23](../notes/open-questions.md)).
- Stackup: L1 electrodes, L2 traces, L3 ground, L4 MCU + components. RX0's
  full-length return cannot run under the electrodes on the same layer.
  **As built (2026-09-28):** L3 is a **solid** GND plane in the margin and the pad 3–4
  corridor only, never under a pad; under the pads L3 carries only the RX0 joins. Hatched
  first, but a via in a hatch hole touches nothing; L2 is ~1.1mm above L3, so solid adds
  under 1pF to a fan-in line.
- MCU placement: centre of the pad group, to equalise trace length across all four pads.
  Unequal lengths give unequal baselines.
  **Superseded for this board (2026-09-28): the MCU is in the right margin.** The rule assumes
  pads arranged around a chip. Ours are four long strips stacked on top of each other: at the
  centre, pads 1 and 4 would reach it only by running four lines each under pads 2 and 3
  (measured in other cycles, so they really couple), and the MCU, crystal and UART would sit
  behind the centre printed mark of pads 2 and 3. From the right margin every pad's lines run
  to the right end under their own pad and nothing runs under another pad. Every pad's route
  has the same shape, which is what equal lengths were for; within a pad the lengths differ
  (RX3 short, RX1 long), and CapTIvate calibrates each element on its own.
- Avoid electrodes at PCB edges, which weakens ground shielding.

## Why ratio encoding matters more than expected

It was chosen for linearity, but it also delivers **repeatability**, which became a hard
requirement once the faceplate gained printed division marks.

Position is the **ratio of copper between the top and bottom bars**, not an absolute
capacitance. Skin moisture, contact pressure and contact patch area all scale both bars
together, so they **largely cancel in the ratio**. Those are precisely the terms that vary
between players and across a session, and an absolute-capacitance design would have had to
fight every one of them.

The exception is the pad ends, see the endpoint trim section above.

## Known limitation

Two fingers on one pad reads as a single averaged position. No palm rejection with exposed
copper. Accepted.
