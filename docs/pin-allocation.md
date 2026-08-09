# Pin allocation

**Status: CURRENT as of 2026-08-09.** Rewritten after a cascade of changes freed six pins
and added five jacks. Safe to lay out against.

## The IO plan

- **10 ADC pots.** 2 per channel (8) on CV_1-CV_8, plus **attack** (A2) and **release** (A3).
- **Three knobs are ANALOG and cost zero pins:** LPG offset (dual-gang), CV amount L, CV
  amount R. They act directly on the Bergman LPG and the Daisy never sees them.
- **Five jacks:** CV in (D8), CV out (C1), gate in / clock (B10), gate out x2 (B5, B6).
- **Shift button on A9.** Encoder on D3/D4 with push on B9.
- **No panel USB.** DFU runs over the module's own Micro USB. See "The USB decision".
- **No mux.** **1-bit SD.**
- **One spare bidirectional GPIO: A8**, and it is **reserved**, see below.

### The full header

| Pin | Use | | Pin | Use |
|---|---|---|---|---|
| A1 | -12V in | | B10 | **GATE IN / clock** |
| A2 | envelope attack | | C1 | **CV OUT jack** |
| A3 | envelope release | | C2-C9 | 8 channel pots |
| A4 | GND | | C10 | LPG envelope (one, splits analog) |
| A5 | +12V in | | D1 | OLED CS |
| A6 | 5V out | | D2 | OLED DC |
| A7 | GND | | D3, D4 | encoder A, B |
| **A8** | **RESERVED** | | D5, D6, D7 | SD 1-bit: D0, CLK, CMD |
| A9 | shift button | | **D8** | **CV IN** (needs conditioning) |
| A10 | 3V3 out | | D9 | OLED MOSI (native SPI2) |
| B1-B4 | audio out/in L/R | | D10 | OLED SCK |
| B5, B6 | **GATE OUT 1, 2** | | | |
| B7, B8 | MSP430 link | | | |
| B9 | encoder push | | | |

**Bidirectional GPIO 15 of 16. ADC 11 of 12 converting**, the twelfth (D9) on SPI.

---

## A8 is reserved for a delay in a later revision

**Decision 2026-08-09: build V1 without the analog delay, but do not spend A8.**

The delay work (see [workflow.md](workflow.md) and the BBD investigation) concluded that a
BBD's **two-phase clock can be generated from a 74HC74 divide-by-two fed by a single Daisy
timer pin**, which makes delay time a firmware parameter locked to the loop clock. That
needs exactly one pin, and **A8 is PB14, which has a hardware timer on it.**

Spending A8 on anything else closes that door. Nothing else currently needs it.

### What else to reserve now, while it is free

| Reserve | Cost now | Why |
|---|---|---|
| **A8** | 0 | the BBD clock, from a hardware timer |
| **0R links in the audio path** where a delay would insert | pennies | a later daughterboard taps in without cutting traces |
| **Board area** beside the LPG section | 0 | ~30 x 40mm is enough for a stereo BBD |
| **2-3 spare pins on the inter-board connector** | 0 | connector pins are free, Daisy pins are not |

### The one thing worth FITTING now rather than reserving

**A quad DAC (MCP4728, I2C, ~$2.50), driven by the MSP430.** It pays for itself immediately
by making the three analog knobs presettable, and leaves a channel for the delay later:

| DAC channel | V1 use | Later |
|---|---|---|
| 1 | LPG offset | unchanged |
| 2 | CV amount L | unchanged |
| 3 | CV amount R | unchanged |
| 4 | spare | **delay dry/wet** |

That converts the standing complaint about the analog controls, that they cannot be saved in
a preset or shown on the OLED, into a solved problem, and it costs **zero Daisy pins** because
the MSP430 owns the I2C bus and relays over the existing link.

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

### Bidirectional GPIO: 15 of 16 used, A8 reserved

| Function | Pins | Note |
|---|---|---|
| Envelope pots | **A2** attack, **A3** release | Wire to **3V3 (A10)**, not 5V |
| **CV IN** | **D8** (ADC_12) | **Needs conditioning and clamps. See below.** |
| SD 1-bit | **D5** (D0), **D6** (CLK), **D7** (CMD) | Fixed SDMMC1 pins |
| OLED SPI2 | **D1** (CS), **D9** (MOSI), **D10** (SCK) | D9 is the **native** SPI2_MOSI |
| OLED DC | **D2** | Any GPIO |
| MSP430 link | **B7**, **B8** | UART primary, I2C routed as fallback |
| Encoder A, B | **D3**, **D4** | |
| Shift button | **A9** | Internal pull-up, button to ground, `daisy::Switch` |
| **A8** | **RESERVED** | BBD clock in a later rev. Do not spend. |

### Two pins came back, and it is worth recording why

**The MSP430 IRQ line was redundant.** It existed so the Daisy would know when to poll, which
is an I2C requirement. **Over UART the MSP430 simply transmits and the Daisy's RX interrupt
fires by itself.** Dropping the wire freed **A8**. Keep the footprint in case of an I2C
fallback, but do not allocate the pin.

**BSL does not need RST and TEST from the Daisy.** SLAU550 section 3.3.1: the BSL can be
invoked by application software, by calling the Z-area at 0x1000. So the Daisy sends an
"enter BSL" command over the existing UART and reflashes over the same two wires.
**That freed B5 and B6 to be real 0-5V gate outputs.** The SBW pads stay on the board as the
recovery path for a touch chip too broken to receive the command.

**And CV amount moving to analog freed D8 and D9.** MOSI returned to its native D9, which in
turn freed **A9** for the shift button.

### Input-only and output-only pins

| Function | Pin | Note |
|---|---|---|
| Pots 1-8 (2 per channel) | **CV_1-CV_8** (C2-C9) | Input only. Wire to **5V (A6)**. Conditioned on-module for +/-5V. |
| **GATE OUT 1** | **B5** (GATE_OUT_1, PC14) | Native 0-5V, no buffer needed |
| **GATE OUT 2** | **B6** (GATE_OUT_2, PC13) | Same |
| **Encoder push** | **B9** (GATE_IN_2, PG14) | `GateIn` inverts by default; flip in software |
| **GATE IN / clock** | **B10** (GATE_IN_1, PG13) | Doubles as the external envelope trigger |
| LPG envelope out | **CV_OUT_1** (C10) | **One output.** Splits on the LPG board into the two analog CV-amount attenuators. |
| **CV OUT jack** | **CV_OUT_2** (C1) | Freed because one envelope needs one DAC |

### Not a GPIO

| Function | How |
|---|---|
| OLED RST | **RC / pullup, no GPIO.** |
| LPG offset, CV amt L, CV amt R | **Analog, on the LPG board.** |
| Mode switch, source switch | **Analog DPDT routing on the LPG board.** |

---

## D8 as a CV input will destroy the pin without a front end

**This is the one genuinely dangerous item in the plan.**

`CV_1` to `CV_8` are conditioned **on the module** for +/-5V. **D8 is not.** It is a bare
0 to 3.3V ADC pin. A CV jack wired straight to it dies the first time someone patches a
+/-10V LFO into it.

Required: a divider and offset mapping the incoming range into 0-3.3V, **plus clamp diodes to
the rails**, or an op-amp front end doing it properly. Not optional, not a later refinement.

---

## Why there is no analog headroom

**All 12 ADC-capable pins are allocated**: CV_1-CV_8 (8, input-only), ADC_9 (A2), ADC_10 (A3),
ADC_12 (D8 as CV in), and ADC_11 (D9) spent on SPI MOSI. **11 are converting.**

A second CV input would have to come out of a channel pot. A **CD4051 mux costs 3 GPIO** for
its select lines and only A8 is free, which is reserved.

---

## Pot wiring, by group

Two different references. Getting this wrong gives a control that reads full-scale at
two-thirds rotation.

| Pots | Pins | Wire top of pot to |
|---|---|---|
| 1-8 (channel, 2 per channel) | CV_1-CV_8 | **5V output (A6)**, +/-5V range |
| attack, release | ADC_9 (A2), ADC_10 (A3) | **3V3 output (A10)**, 0-3.3V range |

### Envelope and LPG control map

**One envelope, one DAC output.** The split into left and right happens in analog.

```
        [ one envelope, in firmware ]
                     |
              CV_OUT_1 (C10)          <- ONE output. CV_OUT_2 is now a jack.
                     |
        +------------+------------+
        |                         |
   x CV amt L                x CV amt R     <- ANALOG pots on the LPG board
        |                         |
        v                         v
   [ L LPG ]  <----  +  ---->  [ R LPG ]
        ^                         ^
        +-------- offset ---------+
              (dual-gang analog pot)
```

Each LPG control input is **analog offset + (envelope x CV amount)**.

**Attenuating after the DAC rather than in firmware is the better engineering**, not just the
cheaper wiring: the CV outputs are 12-bit, so scaling to 10% in software would leave you using
about 400 of 4096 codes. Attenuating in analog keeps the DAC at full scale at every setting.

**The mode switch is ONE switch, not one per channel.** The LPG is a single **stereo** unit, so
VCF-or-VCA is one decision applied to both sides at once: a **DPDT toggle, one pole per stereo
side, ganged on a single actuator**. The panel's second slot is the unrelated **source** switch
(resample or external input), also DPDT for the same L/R reason.

**Consequence of offset and CV amount being analog:** they cannot be stored in a preset or
shown on the OLED. **The quad DAC above fixes this**, and is the reason to fit it in V1.

**The envelope now has an external trigger: B10.** That was the open architectural question.
It can still fire internally from touch onset, note events or the sequencer, but the jack
exists.

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
| 3V3 | DVCC (pin 1) | **Its own LDO.** Not shared with the OLED or audio. |
| **GND x2-3** | DVSS (pin 48) | More than one. Cheapest noise mitigation there is. |
| UART TXD | pin 45 (P5.2) | B7 or B8 |
| UART RXD | pin 44 (P5.1) | B8 or B7 |
| I2C SDA | pin 14 (P1.2) | B8 (populate one interface, not both) |
| I2C SCL | pin 15 (P1.3) | B7 |
| IRQ | footprint only | **Do NOT wire to A8.** Redundant over UART. |
| **BSL RST** | pin 2 | **Test pad only.** Software BSL invocation instead. |
| **BSL TEST** | pin 3 | **Test pad only.** |

**Connector pins are cheap, Daisy pins are not.** Route all four serial wires and pick the
interface with jumpers rather than economising on the connector. Spend the saved positions on
extra grounds, since this cable carries digital edges into a capacitive sensing front end.

**SBW test pads** (TEST pin 3, RST pin 2, 3V3, GND) are now the *only* hardware BSL path, and
they are the recovery route for a touch chip whose firmware is too broken to accept the
software invocation. Put them on the board: free, and the difference between a repair and a
scrapped faceplate.

**Test points on all four signals** (UART Tx, Rx, RST, TEST). When BSL does not work first
time, you want a scope probe point that is not an LQFP pin.

**Regulate 3V3 on the main board and filter locally at the MSP430.** Do not share a rail with
audio circuitry. The LPG runs on +/-12V, so there is a regulator in the chain already.
