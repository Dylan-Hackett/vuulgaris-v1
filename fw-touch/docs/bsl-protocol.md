# BSL protocol notes

How the Daisy flashes the MSP430 with no per-unit programmer. Plan:
**JLC solders a blank chip from the reel; the Daisy flashes it over the already-routed UART.**

Verified in TI **SLAU550** device table: MSP430FR2675, BSL version **00.09.36.B5**,
UART on eUSCI_A, I2C on eUSCI_B. Both interfaces supported. BSL lives in **secure ROM** and
works on a virgin chip from the reel.

## Hardware cost: two wires

**RST and TEST** from the Daisy. That is the entire hardware cost of this approach.

## Entry sequence

RST/NMI held low while pulling TEST high and applying the next two edges (falling, rising).
BSL starts after TEST is held low and RST is released.

```
RST   ‾‾‾\________________________/‾‾‾‾
TEST  ____/‾‾‾\___/‾‾‾\____________
           ^1st   ^2nd  <- TWO rising edges while RST is low
```

**The common failure is fewer than two rising edges on TEST while RST is low.**
Budget a day here with a logic analyzer. That is not pessimism, it is the documented
experience.

## Then wait

**Wait ~300ms after entry invocation before the first command.** This BSL version is slow to
initialise. Skipping the wait looks exactly like a hardware fault, and you will go looking
for one.

## Password

Password = **contents of the interrupt vector table (FFE0h-FFFFh)**.

- All `FF`s on a fresh chip.
- Becomes your vectors after flashing, so the flashing tool must track it.
- Wrong password **with mass erase enabled** wipes the chip and you start over. Recoverable,
  but it costs a cycle.

## Known documentation bug

**SLAU550 page 18**, the I2C unlock example shows length field `0x33` where it should be
**`33` decimal**. If I2C will not unlock, check this before anything else.

## Do not brick it

BSL code is in secure ROM and cannot be overwritten. TI states that even if the device is
secured by disabling JTAG, the BSL still works.

**The one permanent brick: deliberately disabling BSL *and* locking JTAG.** TI's forum
confirms that with BSL disabled completely you cannot regain access.

> **Leave JTAG/SBW unlocked and BSL enabled. Do not touch the security settings.**

Recovery path if BSL somehow fails: the 4 SBW test pads (TEST, RST, 3V3, GND) and a $12
MSP430 LaunchPad eZ-FET.

## Fallbacks if this proves painful

| Option | When it makes sense |
|---|---|
| Distributor pre-programming (Digi-Key / Mouser / Arrow) | At volume. Setup fee plus cents per part, standard practice. |
| Pogo-pin fixture + LaunchPad eZ-FET at board test | Cheapest for small batches. |
| Gang programmer (MSP-GANG, Elprotronic GangPro430) | 8 at a time. Worth it in the hundreds. |

Reference: **SLAU550** (MSP430 FRAM Devices Bootloader User's Guide), **SLAA685**
(MSP Code Protection Features). Both listed in `datasheets/MANIFEST.md`.
