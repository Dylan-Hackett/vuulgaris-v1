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
  dominant channel at that point. The position ramp is unaffected.
- **Pin assignment order is not arbitrary: RX0->E00, RX1->E01, RX2->E02, RX3->E03.**
  Generate the assignment in Design Center **first**, then lay out the PCB to match.
  Swapped pins produce garbage interpolation.

## Working dimensions

| | |
|---|---|
| Pad length | **Derived, not fixed.** The Salamis composition locks `pad length = 12 x pad pitch`, and pitch = 12mm copper + inter-pad gap. Working value **216mm** at a 6mm gap. Settle [Q17](../notes/open-questions.md) first. Was 175mm, then 150mm; both superseded. Inside TI's demonstrated 300mm. |
| Pad width | 12mm (10-12mm is the useful band) |
| Zone length | pad length / 4. **54mm** at the 216mm working value. |
| Teeth per zone | 20, so 80 total (15/zone, 60 total, also fine) |
| Tooth pitch | 2.19mm @ 80 teeth |
| Tooth width | 1.98mm |
| Tooth-to-tooth gap | 0.21mm |
| Top-to-bottom gap | 0.20mm |
| Min copper width | 0.15mm, enforced |

Wider than 12mm raises base capacitance without helping a lengthwise scrub.

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

- `mockups/comb-pad-generator.html` - parametric, live checks against fab limits, exports
  SVG at true mm scale with one `<g>` per net.
- TI **SLAA891** OpenSCAD scripts generate TI's own validated pattern and export DXF.
  **Use these to cross-check the generator's output before committing copper.**

## Layout rules (TI design guide)

- Keep MCU-to-electrode traces short. Trace length adds parasitic capacitance and noise
  susceptibility. This is why the MCU is on the faceplate.
- **Do not ground-pour under electrodes or their traces.** Parallel-plate capacitance to a
  nearby pour is the dominant parasitic contributor. Hatched ground at distance if needed.
- Decoupling caps and ESD parts right at the MCU.
- Route digital lines to the main board away from electrodes, ideally exiting the opposite edge.
- Stackup: L1 electrodes, L2 traces, L3 hatched ground, L4 MCU + components. RX0's
  full-length return cannot run under the electrodes on the same layer.
- MCU placement: centre of the pad group, to equalise trace length across all four pads.
  Unequal lengths give unequal baselines.
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
