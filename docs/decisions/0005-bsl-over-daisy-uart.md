# 0005 - Daisy flashes the MSP430 over BSL, no per-unit programmer

**Status:** Accepted
**Date:** pre-2026-08-05 (recorded retroactively from design state section 4)

## Decision

JLC solders a blank MSP430FR2675 from the reel. The **Daisy flashes it over the UART that
is already routed** between the boards, using the BSL in secure ROM.

Verified in TI SLAU550 device table: MSP430FR2675, BSL version **00.09.36.B5**, UART on
eUSCI_A, I2C on eUSCI_B. Both interfaces supported.

## Hardware cost

**Two extra wires from the Daisy: RST and TEST**, plus a **5V to 3.3V divider on each**.

**Updated 2026-08-06:** these live on **B5 (GATE_OUT_1)** and **B6 (GATE_OUT_2)**, not on
bidirectional GPIO. Gate outputs are plain `GPIO` in libDaisy and RST/TEST are Daisy-driven
outputs, so they fit there, and this design leaves the gate pins idle. That is what kept this
decision affordable when the pin budget tightened. See
[ADR 0009](0009-io-plan-12-adc.md).

**Gate outputs are 0-5V** and the **MSP430 I/O absolute max is DVCC+0.3V = 3.6V**, so each
line needs a divider (two resistors, four total). **Bench-verify the edges before writing BSL
code:** entry depends on two clean rising edges on TEST, and mushy edges from the divider
present identically to a protocol bug. See `../notes/open-questions.md` Q13.

## Gotchas, in the order you will hit them

- **Entry sequence:** RST/NMI held low while pulling TEST high and applying the next two
  edges (falling, rising). BSL starts after TEST is held low and RST is released. TI
  documents the failure modes; the common one is **fewer than two rising edges on TEST
  while RST is low**. Expect to lose a day here with a logic analyzer.
- **Wait ~300ms after entry invocation before the first command.** This BSL version is slow
  to initialise. Skipping the wait looks exactly like a hardware fault.
- **Password = contents of the interrupt vector table (FFE0h-FFFFh).** All FFs on a fresh
  chip; becomes your vectors after flashing. Wrong password with mass erase enabled wipes
  the chip and you start over. Recoverable.
- **Known doc bug:** SLAU550 page 18, the I2C unlock example shows length field `0x33`
  where it should be `33` decimal. If I2C will not unlock, check this first.

## Brick risk: essentially zero if you do not go looking for it

BSL code is in secure ROM and cannot be overwritten. TI states that even if the device is
secured by disabling JTAG, the BSL still works.

**The one permanent brick is deliberately disabling BSL *and* locking JTAG.** TI's forum
confirms that with BSL disabled completely you cannot regain access.

**Rule: leave JTAG/SBW unlocked and BSL enabled. Do not touch the security settings.**

**Put 4 SBW test pads on the board regardless** (TEST, RST, 3V3, GND). Free, and it is the
recovery path: a $12 MSP430 LaunchPad's eZ-FET can flash through them.

## Also on the board: the PGMR connector

**Put the CAPTIVATE-PGMR connector on the faceplate PCB.** The Design Center cannot talk to
an MSP-FET or a LaunchPad eZ-FET; the PGMR carries a separate MSP430F5528 running HID
Bridge firmware that streams live sensor data to the PC. That live data view is the entire
point: jitter, scan time, linearity, trim.

TI's recommended workflow is exactly this: build the custom sensing board, integrate while
keeping the PGMR connector so Design Center works against real hardware, remove after
testing. Tuning against the actual pads, in the actual enclosure, next to the actual
switching supply is the only tuning that counts. Leave unpopulated on production units.

## Fallbacks if BSL-over-Daisy proves painful

- Distributor pre-programming (Digi-Key / Mouser / Arrow): setup fee plus cents per part,
  standard at volume.
- Pogo-pin test fixture + LaunchPad eZ-FET during board test: cheapest for small batches.
- Gang programmer (MSP-GANG, Elprotronic GangPro430): 8 at a time, worth it in the hundreds.
