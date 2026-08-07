# 0009 - IO plan: 12 ADC routed, no mux, 1-bit SD, no panel USB

**Status:** Accepted
**Date:** 2026-08-06
**Closes:** Q3 (two competing IO plans), Q4 (SD bus width), Q6 (4P3T availability), Q14 (USB pins)

## Decision

- **12 ADC pots plus one analog pot.** 2 per channel (8) on CV_1-CV_8, plus 4 on A2, A3, D8, D9.
- **13th knob, LPG offset: dual-gang analog, 0 pins.**
- **Spend A8/A9 on IO.** No panel-mounted USB jack.
- **No CV or gate jacks into the Daisy. No mux. 1-bit SD.**
- Encoder on the main PCB. CV_OUT_1 / CV_OUT_2 drive the LPG, one envelope per stereo side.

| Pot | Pin | Function |
|---|---|---|
| 9 | A2 | Envelope attack |
| 10 | A3 | Envelope release |
| 11 | D9 | CV amount, left |
| 12 | D8 | CV amount, right |
| 13 | **none** | LPG offset, dual-gang analog into the Bergman LPG |

**Revised 2026-08-06.** Was two envelopes with attack and release each. Now **one envelope**
with a per-side CV amount, plus an analog offset. Same 4 ADC pins, and the offset knob is free
because it never reaches the Daisy.

Full table: [../pin-allocation.md](../pin-allocation.md).

## What unlocked 12

An earlier revision of this ADR concluded 12 was impossible. That rested on a documentation
error about the USB pins, corrected 2026-08-06.

**Patch SM has two independent USB ports**, verified against the Rev3 schematic and libDaisy:

| Port | Peripheral | Pins | libDaisy role |
|---|---|---|---|
| Onboard Micro USB, on the module | USB_OTG_FS | PA11 / PA12 | `usbd` = **device**: DFU, USB MIDI |
| A8 / A9 on the header | USB_OTG_HS | PB14 / PB15 | `usbh` = **host**: USB drives |

**DFU flashing and USB MIDI never touch A8/A9.** They were reserved for a job they do not do.

Freeing them gave two pins, and the second one mattered more than its count. **PB15 (A9) is a
supported SPI2_MOSI pin**, listed in `libDaisy/src/per/spi.cpp:741`:

```cpp
static pin_alt_spi spi2_pins_mosi[] = {{Pin(PORTC, 1), GPIO_AF5_SPI2},
                                       {Pin(PORTB, 15), GPIO_AF5_SPI2},
                                       {Pin(PORTC, 3), GPIO_AF5_SPI2}};
```

Moving OLED MOSI from D9 to A9 freed **D9 for pot 11**. Relocating the MSP430 IRQ to A8 freed
**D8 for pot 12**. Without the MOSI move, D9 alone would still have capped the design at 11.

## The constraint that remains

Patch SM has **16 bidirectional GPIO** and this design uses all 16. The 8 pots on CV_1-CV_8
are free because those pins are input-only and can do nothing else. **Every pot past 8 costs a
bidirectional GPIO**, and there are exactly four ADC-capable ones: A2, A3, D8, D9.

**13 is impossible.** All 12 ADC-capable pins are in use, and a CD4051 would cost 3 GPIO for
its select lines, of which there are zero spare.

## What the budget closes on

Three functions sit on pins that are not bidirectional GPIO, which this design leaves idle
because there are no jacks:

| Function | Pin | Why it works |
|---|---|---|
| BSL RST | **B5** (GATE_OUT_1) | Plain `GPIO` in libDaisy, and RST is a Daisy-driven output |
| BSL TEST | **B6** (GATE_OUT_2) | Same |
| Encoder push | **B9** (GATE_IN_2) | Input-only is all a button needs |
| OLED RST | RC / pullup | No GPIO at all |

**B10** (GATE_IN_1) remains free. One spare input.

## What spending A8/A9 costs

| Given up | Kept |
|---|---|
| Panel-mounted USB jack | **DFU** over the module's onboard Micro USB |
| Bootloader firmware-from-USB-drive | **SD card firmware drop** |
| Future USB MIDI host | **USB MIDI device**, when the module is reachable |

**USB access means unscrewing the module from the rack.** Accepted: firmware ships via SD card,
and the SD path is already in the design.

**Build the bootloader without `DSY_DFU_USE_EXT_USB`.** That flag moves DFU to the external
port, which this board no longer wires.

## Why not a mux

CD4051 costs **3 GPIO** for select lines to save 8 ADC pins, but the 8 free pots are already on
input-only CV pins. It would spend 3 GPIO to save 4, and there are none to spend.

## Consequences

- **No CV, gate, or USB jacks on the panel, ever, without a respin.** All four gate pins and
  both USB pins are consumed.
- **RST and TEST need dividers.** Gate outputs are 0-5V; MSP430 I/O max is 3.6V. Four resistors.
  Bench-verify the edges: [Q13](../notes/open-questions.md).
- **Verify A9 drives the display cleanly.** The module may carry ESD or filtering on the USB_HS
  lines: [Q15](../notes/open-questions.md).
- **`GateIn` inverts by default.** Encoder push on B9 needs the polarity flipped in software.
- **Pot wiring differs by group.** Pots 1-8 to **5V (A6)**; pots 9-12 to **3V3 (A10)**.
- **Envelopes have no external trigger.** No gate or CV jacks means they fire internally, from
  touch onset, note events, or the sequencer. This shapes the voice architecture and should be
  decided before the envelope code. **B10 (GATE_IN_1) is still free** if an external trigger
  ever earns a jack.
- **Twelve pots plus an encoder, two switches, the screen and four pads does not fit
  219 x 110mm.** The panel is resized around the Salamis composition, and pad length is now
  derived from the inter-pad gap rather than chosen; see
  [../panel-budget.md](../panel-budget.md).
- Zero spare bidirectional GPIO.

## What would overturn this

Deciding a panel USB jack is worth two pots, or adding CV/gate jacks.
