# 0002 - MSP430FR2675 (CapTIvate) for touch sensing

**Status:** Accepted
**Date:** pre-2026-08-05 (recorded retroactively from design state section 3)

## Decision

Use **TI MSP430FR2675TPTR**, 48-pin LQFP (PT package), LCSC **C2052972**, at $4.49 qty 1.
Mount it on the **back of the faceplate PCB**, not the main board.

Verified specs: 16 self-cap touch IO / 64 mutual-cap sensors, **4 parallel measurement
blocks**, 32KB FRAM, 6KB SRAM, 43 GPIO, 12-bit ADC.

## Why this part

Four parallel measurement blocks is the deciding spec. TI states that devices with fewer
than four are generally not recommended for sliders, because elements measured in separate
cycles sit at ground potential and degrade their neighbours' linearity. The four-block
count for this exact part number is confirmed in TI SLAA842.

32KB/6KB is ample. Four sliders plus a serial link is nowhere near the limit.

## Why not MPR121

- 12 channels, 16 needed, so two chips.
- No slider algorithm at all. Per-channel filtered data only; centroid math and endpoint
  correction land on us.
- 10-bit ADC, and the baseline registers expose only the top 8 bits.
- Measures **one electrode at a time**: 16 sequential measurements against CapTIvate's 4
  grouped ones. On a moving finger, sequential sampling smears the centroid. This is the
  real killer, not the channel count.

MPR121's only advantage is toolchain simplicity, meaning no CCS, no Design Center, no
second firmware. That is a real cost, paid once, in exchange for a defect that would be
present in every gesture.

## Why not SoftPot

- Needs pressure (membrane switch). Light lateral scrubbing drops out.
- +/-3% linearity is +/-6.5mm absolute error over a 216mm pad.
- $8.95 (50mm) to $27.50 (500mm) each, recurring per unit.
- Kills the exposed-copper faceplate concept outright.
- Finite mechanical cycle life.

Still useful as a **bench prototyping stand-in** to settle firmware and scrubbing feel
before cap-touch hardware exists. Keep one around.

## Consequences

- **MCU goes on the faceplate.** TI's layout guide says keep MCU-to-electrode traces as
  short as possible, and explicitly warns against routing capacitive sensing lines through
  board-to-board connectors or cables. That decides the board split, not aesthetics.
- Second firmware image and second toolchain. See `fw-touch/`.
- CCS + CapTIvate Design Center required. Design Center is at 1.83.00.08, dated May 2020.
- **There is no FR2675 dev board.** TI's own evaluation recommendation is
  CAPTIVATE-FR2676 + CAPTIVATE-PGMR. Same silicon for touch purposes; the FR2676 just has
  64KB/8KB against 32KB/6KB.
- **Stock is a prototype quantity: 10 at LCSC.** Reels of 1000 exist. See
  `../notes/open-questions.md` Q7.

## What would overturn this

Measured scan time across four sliders bad enough to make per-pad update rate unusable,
with noise immunity already traded away. See `../notes/open-questions.md` Q1.
