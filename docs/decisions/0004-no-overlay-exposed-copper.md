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
  the electrode side of the resistor. **5 electrodes x 4 pads = 20 of each.** Place near the
  MCU with a low-impedance ground path.
- No palm rejection.

## What this buys

- No bubble-induced dead spots.
- Uniform sensitivity along the whole pad.
- Cheaper: JLCPCB does not do overlay lamination anyway. That is a membrane-switch and
  graphic-overlay industry, vendors like JRPanel, and a separate supply chain.

## What would overturn this

Field failures traced to ESD despite the resistor + TVS network, or wear on the ENIG that
shows up in accelerated testing.
