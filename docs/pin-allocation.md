# Pin allocation

**Status: RESOLVED.** Supersedes the two competing IO plans. Safe to lay out against.

Two IO plans previously existed and conflicted on pin count. This is the reconciled one.

## The IO plan

- **12 ADC pots plus one analog pot.** 2 per channel (8) on CV_1-CV_8, plus 4 on A2, A3, D8, D9:
  **envelope attack, envelope release, CV amount L, CV amount R.**
- **13th knob: LPG offset.** A **dual-gang analog pot** wired into the Bergman LPG, summing into
  both L and R control inputs. **Never read by the Daisy, costs 0 pins.**
- **No CV or gate jacks into the Daisy.** All controls are panel pots.
- **No USB on the panel.** A8/A9 are spent on IO. See "The USB decision" below.
- **Encoder on the main PCB.** CV_OUT_1 / CV_OUT_2 drive the LPG, one envelope per stereo side.
- **No mux.** **1-bit SD.**

---

## The USB decision

**Patch SM has two independent USB ports**, verified against the Rev3 schematic
(`ES_Daisy_Patch_SM_Schematic.pdf`) and libDaisy source. This was originally documented wrong
and it cost two usable pins.

| Port | Peripheral | Pins | On the header? | libDaisy role |
|---|---|---|---|---|
| **Onboard Micro USB** | USB_OTG_FS | PA11 / PA12 (+PA9 VBUS) | **No.** On the module itself. | `usbd` = **device**: DFU flashing, USB MIDI |
| **A8 / A9** | USB_OTG_HS | PB14 / PB15 | Yes | `usbh` = **host**: USB drives, future USB MIDI host |

**DFU flashing and USB MIDI never touch A8/A9.** They run on the module's own connector. The
schematic notes it "allows for powering of the MCU from just USB (allowing for pre-flashing,
etc. without having to have it powered by eurorack)."

**Decision: spend A8/A9 on IO.**

| Given up | Kept |
|---|---|
| Panel-mounted USB jack | **DFU** over the module's onboard Micro USB |
| Bootloader firmware-from-USB-drive | **SD card firmware drop** |
| Future USB MIDI host (plug in a keyboard) | **USB MIDI device**, when the module is reachable |

The practical cost: **USB access means unscrewing the module from the rack.** Accepted, because
firmware ships via SD card and the SD path is already in the design.

**Build the bootloader with the default config**, i.e. **without** `DSY_DFU_USE_EXT_USB`. That
flag moves DFU to the external port, which no longer exists on this board.

---

## Daisy Patch SM

### Bidirectional GPIO: 16 of 16 used, zero spare

| Function | Pins | Note |
|---|---|---|
| Pots 9-12 | **A2** env attack, **A3** env release, **D9** CV amt L, **D8** CV amt R | All wire to **3V3 (A10)**, not 5V |
| SD 1-bit | **D5** (D0), **D6** (CLK), **D7** (CMD) | Fixed SDMMC1 pins |
| OLED SPI2 | **D1** (CS), **A9** (MOSI), **D10** (SCK) | **MOSI moved off D9 to A9 (PB15).** See below. |
| OLED DC | **D2** | Any GPIO |
| MSP430 UART | **B7**, **B8** | UART4 alt mapping |
| Encoder A, B | **D3**, **D4** | |
| MSP430 IRQ (data ready) | **A8** | Freed by dropping USB host |

### Why MOSI can move to A9

`libDaisy/src/per/spi.cpp:741` lists the SPI2 MOSI alternates:

```cpp
static pin_alt_spi spi2_pins_mosi[] = {{Pin(PORTC, 1), GPIO_AF5_SPI2},
                                       {Pin(PORTB, 15), GPIO_AF5_SPI2},
                                       {Pin(PORTC, 3), GPIO_AF5_SPI2}};
```

**PB15 is A9.** It is in libDaisy's own alternate-function table, so `SpiHandle` accepts it
with no custom code. PC3 is D9, the original choice; PC1 is CV_8 and input-only on this module,
so unusable.

That one move frees **D9 for pot 11**, and D8 follows as **pot 12** once the IRQ relocates to
A8. This is what makes 12 ADC reachable at all.

### Input-only and output-only pins doing real work

Not bidirectional GPIO, and idle in this design because there are no jacks.

| Function | Pin | Note |
|---|---|---|
| Pots 1-8 (2 per channel) | **CV_1-CV_8** (C2-C9) | Input only. Wire to **5V (A6)**. |
| **BSL RST** | **B5** (GATE_OUT_1, PC14) | Plain `GPIO` in libDaisy. **Needs a 5V to 3.3V divider.** |
| **BSL TEST** | **B6** (GATE_OUT_2, PC13) | Same. |
| **Encoder push** | **B9** (GATE_IN_2, PG14) | `GateIn` inverts by default; flip in software. |
| LPG envelope out, L | **CV_OUT_1** (C10) | Output only, 0-5V, 100R |
| LPG envelope out, R | **CV_OUT_2** (C1) | Output only, 0-5V, 100R |

Still idle: **B10** (GATE_IN_1). One spare input.

### Not a GPIO

| Function | How |
|---|---|
| OLED RST | **RC / pullup, no GPIO.** Required: the budget does not close otherwise. |

---

## Verify on the first prototype

1. **BSL dividers.** Gate outputs are 0-5V, MSP430 I/O absolute max is DVCC+0.3V = 3.6V. Two
   resistors per line. **Scope the edges**, because BSL entry needs two clean rising edges on
   TEST and mushy edges look exactly like a protocol bug.
   See [Q13](notes/open-questions.md).
2. **A9 as SPI MOSI.** The module may carry ESD protection or filtering on the USB_HS lines
   whose capacitance could affect SPI edges. At SSD1309 clock rates this should be a non-issue,
   but confirm the display drives cleanly. See [Q15](notes/open-questions.md).
3. **`GateIn` polarity** on the encoder push (B9) is inverted by default.

---

## Why not 13+

**All 12 ADC-capable pins are now in use**: CV_1-CV_8 (8, input-only) plus ADC_9, ADC_10,
ADC_11, ADC_12. There is no 13th analog input without a mux, and a **CD4051 costs 3 GPIO for
its select lines**, of which there are now zero spare.

---

## Pot wiring, by group

Two different references. Getting this wrong gives a control that reads full-scale at
two-thirds rotation.

| Pots | Pins | Wire top of pot to |
|---|---|---|
| 1-8 (channel, 2 per channel) | CV_1-CV_8 | **5V output (A6)**, +/-5V range |
| 9-12 (envelope A/R, per side) | ADC_9 (A2), ADC_10 (A3), ADC_11 (D9), ADC_12 (D8) | **3V3 output (A10)**, 0-3.3V range |

### Envelope and LPG control map

**One envelope**, shared, with separate CV amount per stereo side.

| Pot | Pin | Function |
|---|---|---|
| 9 | A2 (ADC_9) | Envelope **attack** |
| 10 | A3 (ADC_10) | Envelope **release** |
| 11 | D9 (ADC_11) | **CV amount, left** |
| 12 | D8 (ADC_12) | **CV amount, right** |
| 13 | **none** | **LPG offset**, dual-gang analog, both channels |

Signal flow:

```
        [ one envelope, in firmware ]
                 |
        +--------+--------+
        |                 |
   x CV amt L         x CV amt R
        |                 |
   CV_OUT_1 (C10)    CV_OUT_2 (C1)
        |                 |
        v                 v
   [ L LPG ] <-- + --> [ R LPG ]
        ^                 ^
        +---- offset -----+
          (dual-gang analog pot,
           summed into both control
           inputs on the analog board)
```

Each LPG control input is therefore **analog offset + (envelope x CV amount)**. The offset sets
where the gate rests with no envelope; the envelope opens it from there.

**The mode switch is ONE switch, not one per channel.** The LPG is a single **stereo** unit, so
VCF-or-VCA is one decision applied to both sides at once: a **DPDT toggle, one pole per stereo
side, ganged on a single actuator**. The panel's second slot is the unrelated **source** switch
(resample or external input), also DPDT for the same L/R reason.

Both switches are **analog routing on the LPG board and cost zero Daisy pins**, alongside the
offset pot and the RC OLED reset. Pull any of those into the Daisy and the 16-GPIO budget
stops closing.

**Consequence of the offset being analog:** it cannot be stored in a preset or shown on the
OLED, because the Daisy never sees it. That is the price of the pin it saves.

**There is no external trigger.** With no gate or CV jacks into the Daisy, the envelopes must be
fired **internally**: from touch onset on a pad, from note events in the machine, or from the
sequencer. Decide this before writing the envelope code, because it shapes the whole voice
architecture. Note that **B10 (GATE_IN_1) is still free** if an external trigger ever becomes
worth a jack.

---

## MSP430FR2675 (PT / LQFP-48)

**Verified against the datasheet**, SLASEO5D revised September 2021. Pin numbers are the PT
column of Table 7-2.

### CapTIvate electrodes: all 16 used

4 pads x 4 electrodes. This consumes the entire self-cap capacity, and it constrains
everything else.

| Block | Signals | PT pins |
|---|---|---|
| CAP0 | CAP0.0-0.3 | 23, 24, 25, 26 |
| CAP1 | CAP1.0-1.3 | 27, 28, 29, 30 |
| CAP2 | CAP2.0-2.3 | 32, 33, 34, 35 |
| CAP3 | CAP3.0-3.3 | 36, 37, 38, 39 |

Put **each pad's four electrodes in one block** so they are measured in parallel. The part has
exactly four blocks, one per pad. Element order within a pad is `RX0->E00, RX1->E01, RX2->E02,
RX3->E03`.

### Serial link: eUSCI_A and eUSCI_B do NOT share pins

**Q2 is resolved. No 0R jumpers needed.** Route both UART and I2C; select in software.

| Interface | Module + mapping | PT pins | Verdict |
|---|---|---|---|
| **UART** | UCA0 remapped (P5.2 TXD / P5.1 RXD) | **45 / 44** | **Use this.** No conflicts. |
| UART | UCA0 default (P1.4 TXD / P1.5 RXD) | 4 / 5 | Works, but pin 4 also carries VREF+ and TCK. |
| UART | UCA1 (P2.6 TXD / P2.5 RXD) | 30 / 29 | **Unusable. Collides with CAP1.3 and CAP1.2.** |
| **I2C** | UCB0 default (P1.2 SDA / P1.3 SCL) | **14 / 15** | **Use this.** No conflicts. |
| I2C | UCB0 remapped (P4.6 SDA / P4.5 SCL) | 18 / 17 | Also fine. |
| I2C | UCB1 default (P3.2 SDA / P3.6 SCL) | 38 / 39 | **Unusable. Collides with CAP3.2 and CAP3.3.** |
| I2C | UCB1 remapped (P4.4 SDA / P4.3 SCL) | 9 / 8 | Fine. |

**The two traps are UCA1 UART and default UCB1 I2C.** Both land on CapTIvate electrode pins.
With all 16 electrodes in use they are simply not available, and picking one by habit gives a
board that cannot talk and cannot sense.

Mapping is selected by the **`USCIA0RMP` / `USCIBxRMP` bits** in `SYSCFG2` / `SYSCFG3`.
Datasheet footnotes 3 and 4: **only one selected port is valid at any time.**

### System pins

| Function | PT pin |
|---|---|
| DVCC | 1 |
| DVSS | 48 |
| **RST / NMI / SBWTDIO** | **2** |
| **TEST / SBWTCK** | **3** |
| VREG (CapTIvate regulator decoupling cap) | 31 |
| VREF+ | 4 |

**VREG on pin 31 needs an external decoupling cap.** It is the CapTIvate regulator output, not
a supply input. Easy to miss.

---

## Inter-board interface

| Signal | Faceplate side | Main board side |
|---|---|---|
| 3V3 | DVCC (pin 1) | Regulated on main board, filtered locally at the MSP430 |
| GND | DVSS (pin 48) | |
| UART TXD | pin 45 (P5.2) | B7 or B8 |
| UART RXD | pin 44 (P5.1) | B8 or B7 |
| I2C SDA | pin 14 (P1.2) | B8 (populate one interface, not both) |
| I2C SCL | pin 15 (P1.3) | B7 |
| IRQ | any free GPIO | A8 |
| BSL RST | pin 2 | **B5 via divider** |
| BSL TEST | pin 3 | **B6 via divider** |

**SBW test pads** (TEST pin 3, RST pin 2, 3V3, GND) share the BSL lines. Put the pads on the
board regardless: free, and the recovery path.

**Test points on all four signals** (UART Tx, Rx, RST, TEST). When BSL does not work first
time, you want a scope probe point that is not an LQFP pin.

**Regulate 3V3 on the main board and filter locally at the MSP430.** Do not share a rail with
audio circuitry. The LPG runs on +/-12V, so there is a regulator in the chain already.
