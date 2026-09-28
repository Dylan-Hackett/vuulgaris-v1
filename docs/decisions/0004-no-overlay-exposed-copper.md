# 0004 - Exposed copper, no overlay, ENIG finish

**Status:** Accepted
**Date:** pre-2026-08-05 (recorded retroactively from design state section 3)

## Decision

Direct finger-to-copper contact. No plastic overlay, no lamination. **Specify ENIG, not HASL.**

## Why

It is the instrument. The faceplate is the interface, and the Salamis Tablet layout
([0009 pending, see section 11](../design-state.md)) depends on visible copper as
decoration. An overlay would also reintroduce the bubble-induced dead spots that laminated
panels are prone to.

ENIG over HASL is not cosmetic preference: HASL leaves uneven solder, which looks bad,
feels worse under a sliding finger, and will not wear well. ENIG is flat and will not tarnish.

## What this costs

**This is outside TI's design assumptions.** All their tuning guidance assumes 1.5-4mm of
plastic between finger and copper.

- **Larger signal delta** than TI's reference designs. Retune for lower conversion counts.
  This is actually a gain: it buys margin on latency and filtering. See SLAA843.
- **ESD is now on you.** TI's fallback for the no-overlay case: 470R-1k series resistor per
  electrode, plus a TVS clamp (they name **TPD1E10B06**) between electrode and ground, on
  the electrode side of the resistor. **4 CapTIvate lines x 4 pads = 16 of each** (corrected
  2026-09-28 from 20, "5 electrodes x 4 pads"). The pad has five segments but four nets: TI's
  4-element slider figure says "Connect RX0 elements together" on the sensor side and runs one
  line to one pin, and its ESD rule is per electrode. So RX0's two ends join first, the TVS
  clamps the joined net, and one resistor runs from it to the pin. Twenty would put two
  resistors in parallel on RX0 (half the series resistance of the other three elements) and
  two TVS diodes on it -- TPD1E10B06 is 12pF (TI product page) -- making one element unlike its
  neighbours for nothing.
- **Where they go.** TI's text: series resistors "as close as possible to the
  microcontroller"; the TVS "close to the electrode where an electrostatic discharge is likely
  to enter the system", with a low-impedance path to ground. With bare copper a discharge can
  land anywhere on a 216mm pad, so there is no entry point to sit beside. What protects the pin
  is the order -- electrode, TVS to ground, resistor, pin -- with the TVS's ground short. Both
  go near the MCU. TI also asks for "low-capacitance" TVS clamps; its own named part adds 12pF
  to every element, equally with 16. Whether a lower-capacitance part is worth it is a BOM
  question for later, not a count question.
- No palm rejection.

## What this buys

- No bubble-induced dead spots.
- Uniform sensitivity along the whole pad.
- Cheaper: JLCPCB does not do overlay lamination anyway. That is a membrane-switch and
  graphic-overlay industry, vendors like JRPanel, and a separate supply chain.

## What would overturn this

Field failures traced to ESD despite the resistor + TVS network, or wear on the ENIG that
shows up in accelerated testing.
