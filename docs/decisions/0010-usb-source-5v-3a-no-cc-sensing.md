# 0010 - USB source is a stated requirement: 5V/3A and a data-grade cable, no CC sensing

**Status:** Accepted
**Date:** 2026-09-20

## Decision

The instrument requires a USB-C source that offers **5V at 3A** (or at least 1.5A), and a
**data-grade USB-C cable**, not a charge-only or thin one. This is a published requirement
of the instrument, the same way a Eurorack module requires a ±12V bus.

The board does **not** read CC. `J11`'s CC1 and CC2 go to `R22`/`R23`, 5.1kΩ to ground, and
nowhere else. That is the minimum a Type-C sink must present to make a source turn VBUS on;
it declares "I am a sink" and nothing more.

## Why it comes up

The current budget in [`power-usbc-dkm.md`](../power-usbc-dkm.md) is about **1.4A at 5V**.
Nothing on the board limits itself to what the source advertises, so on a port offering
*default* USB power (500mA, or 900mA on USB3) the port may current-limit or shut down. The
symptom is a board that will not start from a laptop but is fine from a charger.

The cable half is separate and just as real. The DKM10E-12 needs **4.4V to start** and 4.7V
minimum to run. At 1.4A a thin 1m USB-C cable drops 0.4–0.6V before the board sees anything,
which can put the converter input under its start-up threshold. A board that boots on one
cable and not another is a miserable thing to debug in the field, so the cable is specified
rather than assumed.

## What we are not doing, and what it would cost

Reading CC properly means a Type-C sink controller or an MCU ADC on each CC line plus the
firmware to interpret Rp, back off to 500mA when that is all that is offered, and tell the
user why the instrument is in a degraded mode. That is a part, two nets, firmware, and a
user-facing failure state — all to make the instrument *politely* not work on a port that
cannot run it anyway.

The instrument cannot do its job on 500mA. There is no useful degraded mode to fall back to:
the Daisy, the OLED, both BBDs and twelve op-amp packages are not optional. So the honest
engineering is to state the supply requirement and meet it, not to negotiate down to a power
budget that cannot run the product.

## Consequences

- The requirement has to appear wherever a user meets the instrument: the manual, the
  product page, and ideally silkscreen or a label near the USB-C jack.
- If the enclosure ever ships with a supply, it is a 5V/3A one and the cable is captive or
  included.
- If the design later grows a battery, a barrel jack or a PD sink, this ADR is the thing to
  revisit — the 5.1k pulldowns stay correct in all of those cases, but the reasoning above
  stops applying.
- Nothing about this is a board change. It is recorded because it is a decision that looks
  like an omission, and the next person reading the schematic will otherwise ask why CC goes
  nowhere.
