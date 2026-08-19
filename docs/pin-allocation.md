# Pin allocation

**Status: CURRENT as of 2026-08-09.** Rewritten after a cascade of changes freed six pins
and added five jacks. Safe to lay out against.

## The IO plan

**Changed 2026-08-09: the ten Daisy-facing knobs are ENCODERS, not pots.**

- **10 rotary encoders** on **2x MCP23017 I2C expanders**, both on the MAIN PCB
  beside the encoders themselves. 20 lines into the expanders, **2 wires out**.
- **3 knobs stay ANALOG POTS wired straight to the Bergman LPG board**: offset
  (dual-gang), CV amount L, CV amount R. Zero pins, zero conversion, and the
  Daisy never sees them. **Deliberate: no DAC.**
- **The MSP430 link is UART on A2/A3**, point-to-point across the cable.
  **NOT on the I2C bus.** See "why the touch link is UART" below.
- **Five jacks:** CV in (C9 / CV_8), CV out (C1), gate in / clock (B10),
  gate out x2 (B5, B6).
- **Main encoder on U4 (GPB0-2), not the Daisy.** A9 is free (shift was dropped).
- **A8 reserved**, see below. **1-bit SD.** No panel USB.

### Four channel buttons — added 2026-08-16

**Four momentary buttons on U4's spare GPIO**, one per channel, sitting in the left
margin beside the pads. They cost **no Daisy pins**: U3 is full at 16 GPIO for eight
encoders, but U4 only used 4 of 16 for ENC9/ENC10, so the buttons take `GPA4`-`GPA7`
and eight of its GPIO are still free after them.

| Button | Net | U4 pin |
|---|---|---|
| SW4 | `BTN1` | 25 (GPA4) |
| SW5 | `BTN2` | 26 (GPA5) |
| SW6 | `BTN3` | 27 (GPA6) |
| SW7 | `BTN4` | 28 (GPA7) |

Wired **button to ground with the MCP23017's internal pull-ups enabled** — the same
arrangement as the encoders, so no external resistors. Polled with everything else at
500Hz, i.e. 2ms, which is irrelevant for a button.

**Placement, revised 2026-08-17:** the controls sit in the left margin centred on panel
**x 33.571** — the main encoder at y 76.525, then the four keys as a **2x2 Cherry MX
cluster** on 19.05mm pitch at x 24.046 / 43.096, y 100.725 / 119.775. The pad block moved
**20mm right** to open that margin, so the pads now run x 61.143-277.143. The encoder
used to sit in the RIGHT margin; it moved with the keys so the UI reads as one group.

**There is no shift button.** It was dropped 2026-08-16 — the four keys are general UI
keys, not per-channel modifiers, which is why they read better as a cluster than a
column. A9 came back with it.

Everything else on the panel is unchanged — the ten parameter encoders, three pots, two
DPDT switches and the OLED keep their coordinates, because the upper region is centred
independently of the pad block.

**This displaced the MSP430 power cluster**, which was in that left margin. It moved to
pcb (40-62, 98-105) — still nowhere near the OLED rail, which is the only thing §5.5
actually requires of it.

**`placement-panel-facing.txt` is now genuinely generated:**
`python3 mockups/generate-faceplate.py --placement > hardware/placement-panel-facing.txt`.
It previously claimed to be generated while being hand-maintained, which let the panel
artwork and the PCB placement drift apart with nothing to catch it.

**Net names are placeholders.** `BTN1`-`BTN4` should be renamed once the function is
decided (mute? solo? channel select? record-arm?).

### Two links, deliberately separate

| Link | Daisy pins | Devices | Crosses the cable? |
|---|---|---|---|
| **UART4** | **A2** (RX), **A3** (TX) | MSP430FR2675 | **yes**, point-to-point |
| **I2C1** | B7 (SCL), B8 (SDA) | MCP23017 x2 @ 0x20, 0x21 | **no**, main PCB only |

### Poll rates, and the arithmetic behind them

Quadrature edges per second is `rev/sec x PPR x 4`. For a 24-PPR encoder that is
**96 edges per revolution**, so:

| turn | rev/sec | edges/sec | at 500Hz | at 2kHz |
|---|---|---|---|---|
| deliberate parameter twist | ~1 | ~96 | 5 samples/edge | 21 |
| **fast menu flick** | 3-5 | **288-480** | **1-2 samples/edge** | 4-7 |

**ENC1-ENC10 stay at 500Hz** — about 24% of a 400kHz bus for both expanders. Parameter
knobs are turned deliberately and never flicked through a list.

**U4's Port B is polled at 2kHz** because ENC0 lives there and ENC0 is the one encoder
that does get spun hard. One GPIOB read is about 100us, so that is roughly 20% more bus.

*An earlier revision of this document claimed hands produce "20-30 transitions per
second". That is about 0.25 rev/sec — too slow even for a deliberate twist, and it is
what made 500Hz look sufficient everywhere. The table above supersedes it.*

**The encoders are DETENTLESS** (decided 2026-08-13, see the brief §4.1). The original
C202365 was an EC11E18244AU at 36 detents/18 pulses and is withdrawn — thirty-six
clicks per turn is wrong for ten continuously-variable parameters. The replacement part
is not yet chosen; it gates on stock, on shaft length (which waits on enclosure
height), and on ENC0 needing a push switch the other ten do not.

### Why the touch link is UART, not I2C

**TI's CapTIvate protocol is 2 wires over UART and 3 over I2C.** From the
CapTIvate Technology Guide: *"the UART operates in a full duplex mode using RX
and TX pins, and the I2C operates as an I2C Slave using SDA and SCL pins with an
additional pin P1.2/IRQ to generate interrupt requests."*

**That third wire would be A8**, the pin reserved for the BBD clock. I2C for the
touch chip costs the delay upgrade.

Four more reasons, on this board specifically:

| | |
|---|---|
| **Point-to-point** | a hung touch chip cannot take the encoders down with it |
| **Push-pull, not open-drain** | actively driven both ways, across a cable |
| **Self-resynchronising** | a glitch costs one frame. I2C can leave a slave stuck mid-byte holding SDA low, recoverable only by a deliberate routine |
| **Low impedance both states** | I2C idles high through a pull-up, and high-impedance nodes couple more into a capacitive front end |

**I2C's one real advantage was that the master supplies the clock**, so there is
no baud agreement and no exposure to oscillator drift. **That is retired by the
32.768kHz crystal** on pins 46/47, which cost about $0.20 and were already free.

Both interfaces are officially supported by CapTIvate, so this is not off-label
either way.

### Why encoders freed ten analog pins

The ten pots were the entire ADC budget. Moving them to expanders returns:

| Freed | Kind |
|---|---|
| **CV_1 to CV_7** | **conditioned, rated to the +/-12V rails** |
| D8 | bare 0-3.3V ADC |
| ~~A2, A3~~ | *spent again on the touch UART* |

**CV_8 already carries the CV in jack, so this makes eight conditioned CV
inputs available** on an instrument that had one. That is a larger change to
what the product *is* than the encoders themselves.

### What this costs

| | |
|---|---|
| 10x detentless encoder (part TBD; C202365 withdrawn) | +$12.12 **[stale — detentless parts cost more]** |
| less 10 pots no longer needed | -$7.00 |
| 2x MCP23017 | +$3.60 |
| **Net** | **+$8.72, about 5% of BOM** |

**The panel stops being readable at a glance.** No knob position to see. On a
Salamis counting board, whose visual logic is positions on lines, that is a
real loss and it was accepted knowingly.

**The three analog pots are the exception, and that reads as intentional.**
Pots with end stops for the analog domain, endless encoders for the digital
one. The offset knob is already drawn larger than the rest, so the distinction
is visible before it is felt.

**Consequence, accepted:** offset and CV amount L/R cannot be saved in a preset
or shown on the OLED, because nothing digital is in their path. Load a patch
and those three are wherever they were physically left.

---

## The full header

| Pin | Use | | Pin | Use |
|---|---|---|---|---|
| A1 | -12V in | | B10 | **GATE IN / clock** |
| **A2** | **MSP430 UART RX** | | C1 | **CV OUT jack** |
| **A3** | **MSP430 UART TX** | | **C2-C8** | **free** (CV_1-CV_7, conditioned) |
| A4 | GND | | **C9** | **CV IN jack** (CV_8) |
| A5 | +12V in | | C10 | LPG envelope (one, splits analog) |
| A6 | 5V out | | D1 | OLED CS |
| A7 | GND | | D2 | OLED DC |
| **A8** | **RESERVED** | | **D3, D4** | **FREE** (SDMMC_D2, SDMMC_D1) |
| A9 | **FREE** | | D5, D6, D7 | SD 1-bit: D0, CLK, CMD |
| A10 | 3V3 out | | **D8** | **free** (ADC) |
| B1-B4 | audio out/in L/R | | D9 | OLED MOSI (native SPI2) |
| B5, B6 | **GATE OUT 1, 2** | | D10 | OLED SCK |
| B7, B8 | **I2C** (2 expanders, local) | | | |
| **B9** | **FREE** (GATE_IN_2) | | | |

**Bidirectional GPIO 15 of 16. ADC 8 of 12 free** (CV_1-CV_7 and D8). A2 and A3
are now the touch UART, CV_8 is the CV in jack, D9 is SPI MOSI.

### The CV pins are NOT in ascending order

**Verified 2026-08-12 against the Patch SM symbol.** "C2-C8 = CV_1-CV_7" above is
shorthand for *which pins are free*, *not* a 1:1 map. The first four are reversed:

| Pin | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 |
|---|---|---|---|---|---|---|---|---|
| **Signal** | CV**4** | CV**3** | CV**2** | CV**1** | CV5 | CV6 | CV7 | CV8 |

Wire a jack to C2 expecting CV_1 and you get CV_4. This costs nothing if the jacks
are labelled from this table and a silkscreen respin if they are not.

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

### Explicitly NOT fitting: a DAC

An MCP4728 quad DAC on the I2C bus would make offset and CV amount L/R
presettable and OLED-visible. **Decided against 2026-08-09.** Those three
controls go straight to the Bergman board as analog pots, and that is the whole
point of them. Address 0x60 is left unused on the bus if that ever changes.

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

**Revised 2026-08-17: the module's connector is now exposed, so there is no practical cost.**
U1 sits rotated 90 degrees hard against the right wall, putting its USB-C at pcb (282.5, 85.2),
1.8mm inside the edge. Cut the enclosure for it there. This costs no pins — DFU and USB MIDI
device both run on that connector, and A8/A9 stay free for IO exactly as decided above.

The layout constraint that produced this: **USB, the D header and the C header are all on the
same long edge of the module**, so whichever wall the USB faces, the SD and CV face it too.
Only the right wall works — the left is blocked by ENC0 and the MX cluster (about 16mm clear
against the module's 68mm), and the top 47mm is entirely panel controls.

**The SD card is not user-accessible, and that is accepted.** The module occupies 68mm of the
77mm of clear height at that wall, so J1 cannot sit beside its own D header; it is parked to
the left at (234, 114), a 44mm run, with the module between. Swapping a card means opening the
case. Fine, because firmware ships over USB now and samples are written over the wire.

**Build the bootloader with the default config**, i.e. **without** `DSY_DFU_USE_EXT_USB`. That
flag moves DFU to the external port, which no longer exists on this board.

---

## Daisy Patch SM

### Bidirectional GPIO: 15 of 16 used, A8 reserved

| Function | Pins | Note |
|---|---|---|
| **I2C** | **B7** SCL, **B8** SDA | **2x MCP23017 only, both local.** Pull-ups once, on the main PCB. |
| **MSP430 UART4** | **A2** RX, **A3** TX | point-to-point across the cable |
| SD 1-bit | **D5** (D0), **D6** (CLK), **D7** (CMD) | Fixed SDMMC1 pins |
| OLED SPI2 | **D1** (CS), **D9** (MOSI), **D10** (SCK) | D9 is the **native** SPI2_MOSI |
| OLED DC | **D2** | Any GPIO |
| Main encoder A, B | **D3**, **D4** | The one beside the pads. The other ten are on expanders. |
| Shift button | **A9** | Internal pull-up, button to ground, `daisy::Switch` |
| **A8** | **RESERVED** | BBD clock in a later rev. Do not spend. |
| **D8** | **FREE** | ADC-capable, bare 0-3.3V |

### The main encoder moved to U4 — and poll Port B at 2kHz

**Revised 2026-08-19.** ENC0's A, B and push now go to **U4 GPB0, GPB1, GPB2**
instead of D3, D4 and B9. U4's Port B was completely unused; U3 is full at 16/16.

It was on the Daisy for latency. The reason it can move is that the real problem
was never latency, it was the **500Hz poll rate**:

```
realistic fast flick   3-5 rev/sec on a 24-detent encoder
                       = 72-120 detents/s = 288-480 quadrature transitions/s

 500 Hz  ->  1-2 samples per transition   marginal, drops steps
2 kHz    ->  4-7 samples per transition   comfortable
```

**So poll GPB on U4 at 2kHz.** One GPIOB read at 400kHz is about 100us, so 2kHz
costs ~20% of the bus. The ten parameter encoders can stay at 500Hz — knobs do not
get flicked through a menu.

**An interrupt line was considered and rejected.** U4's INTB (pin 19) is free and
could drive a freed Daisy pin, but the MCP23017's INT latches until GPIO or INTCAP
is read, and any code path that misses that clear leaves the encoder dead
intermittently. It also does not make the decode lossless -- the part queues
nothing, so a fast spin can still slip a transition between the interrupt and the
I2C read. Fixed-rate sampling is what a quadrature decoder wants anyway.

**What this bought:** about 508mm of trace (ENC0 sat 250mm from the Daisy's D
header and 75mm from U4), and **D3 and D4 back, both SDMMC data lines** -- 4-bit SD
now needs only D2, currently OLED DC.

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
| **CV_1 to CV_7** (C2-C8) | **FREE** | Input only, conditioned. Seven more CV jacks available. |
| **CV IN jack** | **CV_8** (C9) | **Conditioned on-module. Rated to the +/-12V rails.** |
| **GATE OUT 1** | **B5** (GATE_OUT_1, PC14) | Native 0-5V, no buffer needed |
| **GATE OUT 2** | **B6** (GATE_OUT_2, PC13) | Same |
| **GATE IN 2** | **B9** (GATE_IN_2, PG14) | **Free.** Was the main encoder push before it moved to U4. |
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

## Why the CV in moved off D8, and onto CV_8

**Corrected 2026-08-09.** The CV jack was briefly on D8, which would have needed a divider,
an offset and clamp diodes, and would have destroyed the pin without them. **Swapping it with
a channel pot removes the entire problem**, because the module already conditions CV_1-CV_8.

Straight from the Patch SM absolute maximum ratings:

| Pin type | Min | Max |
|---|---|---|
| **CV input** | **negative power in** | **positive power in** |
| GPIO | -0.3 V | 6 V |

**A CV input is rated to the power rails**, so at +/-12V it survives anything a modular can
patch into it, with 100K input impedance and the conditioning already on the module. **A GPIO
dies above 6V.**

And the swap is free in the other direction: **a pot is a benign 0-3.3V source**, so it is
perfectly happy on a bare ADC pin. Wire it to **3V3 (A10)**, not 5V.

| | Was | Now |
|---|---|---|
| CV jack | D8, bare 0-3.3V pin | **CV_8 (C9)**, conditioned, +/-12V tolerant |
| 8th channel pot | CV_8 | gone: it is an encoder now, D8 is free |
| External parts needed | divider + offset + 2 clamp diodes | **none** |

**The lesson worth keeping:** put the hostile signal on the pin that was built to survive it,
and the benign one on the pin that was not.

---

## Analog headroom: ten pins, and seven of them conditioned

Moving the knobs to encoders inverted this section. It used to read "all 12 ADC
pins are allocated, there is no headroom".

| Free | Kind | Good for |
|---|---|---|
| **CV_1 to CV_7** (C2-C8) | conditioned, rated to the rails | **CV input jacks** |
| D8 | bare 0-3.3V | a pot, a trimmer, anything benign |

Only **CV_8** (the CV in jack) and **ADC_11 / D9** (spent on SPI MOSI) are taken.

**Do not put a CV jack on D8.** Those are bare GPIO rated -0.3 to 6V.
See "Why the CV in moved off D8" above; the reasoning did not change just
because there are now spare pins.

## Pot wiring: only three pots remain

| Pot | Goes to | Note |
|---|---|---|
| LPG offset (dual-gang) | Bergman board | never seen by the Daisy |
| CV amount L | Bergman board | attenuates CV_OUT_1 |
| CV amount R | Bergman board | attenuates CV_OUT_1 |

The 5V-vs-3V3 reference trap that used to live here is **gone with the pots**.
Nothing analog reaches the Daisy any more except the CV in jack on CV_8, which
is conditioned on-module.

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
| **UART** | UCA0 default (P1.4 TXD / P1.5 RXD) | **4 / 5** | **Use this.** Runtime and BSL become the same two wires — see "Inter-board interface". Pin 4 also carries VREF+ and TCK, both idle here. |
| UART | UCA0 remapped (P5.2 TXD / P5.1 RXD) | 45 / 44 | **Route as a fallback.** No conflicts, but runtime and BSL stop being the same wires. |
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
| **UART TXD** | **pin 4 (P1.4), DEFAULT UCA0** | **A2** (UART4_RX) |
| **UART RXD** | **pin 5 (P1.5), DEFAULT UCA0** | **A3** (UART4_TX) |
| UART TXD alt | pin 45 (P5.2), remapped | route as a fallback |
| UART RXD alt | pin 44 (P5.1), remapped | route as a fallback |
| IRQ | footprint only | **Do NOT wire to A8.** Redundant over UART. |
| **BSL RST** | pin 2 | **Test pad only.** Software BSL invocation instead. |
| **BSL TEST** | pin 3 | **Test pad only.** |

**Use the DEFAULT UCA0 mapping, pins 4 and 5.** That is the change that probably
resolves [Q21](notes/open-questions.md): BSL pins are factory-fixed and are almost
certainly the defaults, so runtime UART and BSL UART become the same two wires.
Pin 4 also carries TCK and VREF+, but **SBW is 2-wire so TCK is idle**, and
CapTIvate does not use VREF+. Confirm on the bench, then close Q21.

**Route the remapped pins 44/45 as well.** Connector positions are free and a
respin is not. Spend the rest on extra grounds, since this cable carries digital
edges into a capacitive sensing front end.

**No I2C crosses this cable any more.** The expanders are local to the main PCB.

**SBW test pads** (TEST pin 3, RST pin 2, 3V3, GND) are now the *only* hardware BSL path, and
they are the recovery route for a touch chip whose firmware is too broken to accept the
software invocation. Put them on the board: free, and the difference between a repair and a
scrapped faceplate.

**Test points on all four signals** (UART Tx, Rx, RST, TEST). When BSL does not work first
time, you want a scope probe point that is not an LQFP pin.

**Regulate 3V3 on the main board and filter locally at the MSP430.** Do not share a rail with
audio circuitry. The LPG runs on +/-12V, so there is a regulator in the chain already.
