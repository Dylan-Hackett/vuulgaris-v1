# Open questions

Every `[unverified]` flag and unresolved conflict from `../design-state.md`, ordered by what
it blocks. **Nothing open here should drive a decision until it is closed.**

**Resolved: Q2, Q3, Q4, Q5, Q6, Q8, Q9, Q11, Q12, Q14.** Kept below with their answers, because
the reasoning is usually the useful part. **Still open: Q1, Q7, Q10, Q13, Q15, Q17, Q18.**

---

## Q1. Does a moving finger on bare copper read cleanly?

**Blocks:** committing a faceplate. **Status: OPEN, and narrower than originally written.**

**Revised 2026-08-06.** This was originally "scan rate and jitter across 4 sliders" and flagged
as blocking everything. Two thirds of it closed on arithmetic. What is left is a different and
more specific question.

### Closed: scan rate

TI's CapTIvate guide gives conversion as **2 clock cycles per count at a 2 MHz effective rate,
so 0.5 us per count**. A sensor at 250 conversion counts takes **125 us**. Reference designs
agree: the CAPTIVATE-METAL panel measures everything in **920 us**, another design in under
**2.4 ms**.

Our case, with each pad's 4 elements measured in parallel as one block and 4 pads sequential:

| | |
|---|---|
| 4 pads x 125 us @ 250 counts | **~500 us** |
| x4 for frequency hopping (noise immunity on) | **~2 ms worst case** |
| No overlay allows retuning to fewer counts | **better than both** |

That is a **500 Hz to 2 kHz update rate**, against an audio block rate of 1 kHz (48 samples
@ 48k) and a human gesture bandwidth of roughly 10 Hz. Latency of 2 ms sits far below the
10-20 ms where lag becomes perceptible.

**The 20-33 ms scan periods in TI's demo designs are not measurement limits.** They are power
optimizations for battery-powered buttons that sleep between scans. This instrument is wall
powered and scans back to back.

**[unverified, minor]** The 125 us figure assumes a 4-element pad resolves in one parallel
cycle, which is the entire point of the 4-block architecture. Design Center reports measured
scan time directly, so confirm rather than assume. Also assumed: frequency hopping is 4
sequential passes rather than something overlapped.

### Closed: jitter at rest

Filterable, with room to spare. **Gesture lives at ~10 Hz, jitter lives at hundreds of Hz**,
and the fast scan rate is what creates that separation. An ordinary filter removes the jitter
without touching the gesture, and there are 8+ ms of latency budget to spend on it.

Worth noting *why* the scan rate matters, since it is not the obvious reason: not latency, but
**signal and noise bandwidth separation**. At TI's 30 Hz demo default, gesture and noise would
overlap and no filter could separate them.

### Still open: monotonicity and continuity under a moving finger

**Narrowed 2026-08-06.** The earlier framing of this asked whether the pad reads *accurately*
under a moving finger. Wrong question for this instrument.

**Absolute accuracy is not directly required.** You scrub by listening and adjusting, so the
loop closes through your ears. A smooth nonlinearity reads as a mildly nonlinear scrub and is
indistinguishable from an intentional design choice.

**But the faceplate has printed marks.** The layout puts **13 tick divisions per pad at 18.00mm
spacing**, with crosses on the quarter, half and three-quarter points, plus Greek acrophonic
numerals in the margins. If a finger on a printed cross should land
at the corresponding point in the sample, then **accuracy against those marks is a
requirement**, and that makes **repeatability** a pass criterion.

The distinction matters because only one of the two is fixable:

- **Accuracy** (reading matches the printed mark) is a **lookup table**. Measure once, correct
  forever.
- **Repeatability** (the same physical spot reads the same tomorrow, with a damp finger, played
  by someone else) **cannot be fixed downstream.** There is nothing to calibrate against if the
  target moves.

This is a direct consequence of the pivot in [ADR 0001](../decisions/0001-pivot-to-capacitive-scrubbing.md).
In the shelved Trautonium design **position was pitch**, and a 2% error is a wrong note, which
is instantly audible. **Scrubbing has no equivalent of a wrong note.**

So only three properties matter:

| Property | Why | If it fails |
|---|---|---|
| **Monotonicity** | Forward finger movement must never report backward, even briefly | Sample stutters backward mid-gesture. Audible. |
| **Continuity** | No dropouts or sudden jumps | Discontinuity in the read pointer is a click. |
| **Stability within a stroke** | No sudden change of character mid-drag | Scrub audibly changes behaviour halfway along. |
| **Repeatability** | Printed marks on the faceplate must correspond to fixed points in the sample | Marks drift against the sound. Not correctable. |

**Everything else is inaudible or calibratable.** Linearity and endpoint offset are both
lookup-table problems: a repeatable error, however large, is correctable.

### Why the geometry helps here

**Position comes from the ratio of copper between the top and bottom bars, not from absolute
capacitance** ([ADR 0003](../decisions/0003-comb-pad-rx0-wraparound.md)). Skin moisture,
contact pressure and contact patch area all scale both bars together, so they **largely cancel
in the ratio.** The ratiometric encoding was chosen for linearity, but it happens to buy
exactly the robustness that repeatability needs.

**The ends are the weak spot.** A large finger's centroid physically cannot reach as close to
the pad edge as a small one, so endpoint trim is **finger-size dependent** in a way the middle
region is not. This is the one genuinely person-varying term.

**If the OLED draws a waveform with a playhead**, a positional bow makes the visual disagree
with what you hear. Same lookup table fixes it.

### Consequences for the faceplate

1. **Extend copper past the printed scale.** The design state offered two options: mark the
   usable region inside the copper, or extend copper past the printed scale. **Printed marks
   settle it: extend the copper**, so every division sits in the well-behaved middle region and
   none land in the finger-size-dependent trim zone at the ends.
2. **Multi-point calibration, not just `Lower_Trim` / `Upper_Trim`.** Two-point trim corrects
   the ends and leaves the middle free to bow. If the centre cross must land on the halfway
   point of the sample, calibrate against several known marks and interpolate between them.
   **The three crosses at 1/4, 1/2 and 3/4 are the natural calibration points**, and they are
   also what a player aims for, so they are where accuracy matters most.
3. **Do not chase better than ~2mm.** Placing a finger on a printed cross, a player's own
   contact centroid is a couple of millimetres from where they think it is. Sensor precision
   beyond that is invisible.

### Why this is still worth testing

Bare copper sits outside TI's validated envelope. **Every TI reference design assumes 1.5-4mm
of plastic** between finger and copper. Direct ENIG contact changes things their tuning
guidance does not cover:

- Contact patch area changes with pressure and drag speed
- Skin moisture varies the coupling, between people and across a session
- Partial galvanic contact rather than clean capacitive coupling through a dielectric

Any of those could in principle produce **momentary reversals or dropouts**, which are the two
things that cannot be fixed downstream. Smoothing cannot help: an artifact that moves with the
finger sits inside the gesture band, and a filter wide enough to remove it also removes the
gesture. Averaging harder only adds lag while keeping the error.

**How to close.** Single-pad test board, [next-steps.md](next-steps.md) step 0. **Do not
measure linearity.** Drag a finger and log position against time, then check:

1. Is the sequence ever non-monotonic during a steady forward drag?
2. Are there dropouts or jumps rather than a continuous trace?
3. Does either get worse with a damp finger, light pressure, or a fast drag?

Then the **repeatability** test, which is now a pass criterion because of the printed marks:

4. Mark a fixed physical spot mid-pad. Touch it 20 times and record the **spread** of readings.
5. Repeat with a damp finger, with light and firm pressure, and with **at least two different
   people** (finger size is the variable that does not cancel in the ratio).
6. Repeat near each end, where trim is finger-size dependent, to find how much of the pad has
   to be excluded from the printed scale.

**Pass:** spread under ~2mm mid-pad, and monotonic and continuous throughout. Bend in the
curve does not matter; scatter does.

**Expected outcome: fine, or fixable with a calibration table.** TI demonstrated 300mm on four
electrodes, and no overlay gives a *larger* signal delta than their reference designs. The
argument for spending $50 first is not that failure is likely, it is that this is the only
open question where a bad answer costs a faceplate respin instead of a firmware commit.

---

## Q7. Production quantity sourcing

**Blocks:** any run beyond prototypes.
**Status: OPEN, deferred by decision.** A cash question, not a technical one.

| Part | LCSC stock |
|---|---|
| MSP430FR2675TPTR (C2052972) | **10** |
| 2.42" SSD1309 SPI (C5139768) | **27** |

Both are prototype quantities. LCSC-Reels (1000) is the production path on the MSP430 but is a
real cash commitment. The display is a commodity format widely available outside LCSC, so
second-source it.

---

## Q10. OLED dead under bootloader

**Blocks:** nothing yet. **Test before it is load-bearing.**
**Status: OPEN.**

A 2022 report on Daisy Patch showed audio working but the OLED dead under both `BOOT_QSPI` and
`BOOT_SRAM`. May be fixed. This design has both a display and the bootloader, so verify that
combination early rather than discovering it late.

---
---

# Resolved

## Q2. eUSCI_A / eUSCI_B pin muxing on the FR2675 PT package

**RESOLVED 2026-08-06.** Datasheet SLASEO5D (revised September 2021), Table 7-2, PT column.

**They do not share pins. No 0R jumpers needed.** Route both UART and I2C, select in software
via the `USCIA0RMP` / `USCIBxRMP` bits in `SYSCFG2` / `SYSCFG3`.

| Interface | Mapping | PT pins |
|---|---|---|
| **UART (use this)** | UCA0 remapped, P5.2 / P5.1 | **45 / 44** |
| **I2C (use this)** | UCB0 default, P1.2 / P1.3 | **14 / 15** |

**Two traps found while checking.** CapTIvate electrodes occupy pins 23-30 and 32-39, and all
16 are used by our four pads. That makes two obvious-looking mappings unusable:

- **UCA1 UART** (pins 30 / 29) collides with **CAP1.3 and CAP1.2**
- **UCB1 default I2C** (pins 38 / 39) collides with **CAP3.2 and CAP3.3**

Picking either by habit gives a board that can neither talk nor sense.

Full table in [../pin-allocation.md](../pin-allocation.md).

---

## Q3. Reconcile the two IO plans

**RESOLVED 2026-08-06, then reopened and re-resolved the same day.** Settled as **12 ADC
routed, 10 populated, no mux**:

- 2 pots per channel (8 total) on **CV_1-CV_8**
- 4 more on **A2, A3, D8, D9**. Populate 2 of them now, leave 2 as stuff options.
- No CV or gate jacks into the Daisy, and **no panel USB**
- Encoder on the main PCB
- CV_OUT_1 / CV_OUT_2 drive the LPG, one envelope per stereo side

**The first answer here was 10 pots, and it was wrong.** It rested on two claims that did not
survive checking, both corrected under [Q14](#q14-are-a8a9-really-reserved-for-dfu-and-usb-midi):
that A8/A9 were needed for DFU and USB MIDI, and that D9 was the only SPI2_MOSI pin available.
PB15 (A9) is also SPI2_MOSI, so moving the OLED there freed D9, and relocating the IRQ to A8
freed D8.

**13 is impossible.** All 12 ADC-capable pins are in use, and a CD4051 costs 3 GPIO for its
select lines, of which there are zero spare.

**The budget closes because three functions moved off bidirectional GPIO.** This design leaves
the gate pins idle, since there are no jacks:

- **BSL RST and TEST -> B5 and B6** (GATE_OUT_1/2). Plain `GPIO` in libDaisy, and these are
  Daisy-driven outputs. **Needs a 5V to 3.3V divider**, see Q13 below.
- **Encoder push -> B9** (GATE_IN_2). Input-only is all a button needs.
- **OLED RST -> RC/pullup**, no GPIO.

Result: 14 of 14 bidirectional GPIO used, BSL retained, and the data-ready IRQ retained on D8.
Keeping the IRQ matters: polling costs latency in the touch path.

**A mux does not help.** CD4051 spends 3 GPIO on select lines to save 8 ADC pins, but the pots
that cost nothing are already on CV_1-8 (input-only pins that can do nothing else). Only pots
9+ cost GPIO, and there are two. It would spend 3 to save 2.

---

## Q4. Does the Daisy bootloader hardcode 4-bit SD?

**RESOLVED 2026-08-05.** No, and the concern was backwards.

`DaisyBootloader/shared/bootloader.cpp:164` (HEAD `8b279a8`):

```cpp
sd_cfg.width = SdmmcHandler::BusWidth::BITS_1;
```

It is libDaisy's `Config::Defaults()` that is 4-bit @ 50MHz; the bootloader explicitly
overrides to 1-bit. **SD-card firmware drops work on 3-pin wiring.**

**Decision: use 1-bit.** Saves 3 GPIO (D2, D3, D4 freed), and samples load into SDRAM at boot
rather than streaming, so bandwidth only affects a boot-time delay of a second or two.

---

## Q5. RoHS / cadmium status on vactrols

**CLOSED 2026-08-06.** Vactrol supply handled directly. No further action.

---

## Q6. 4P3T panel-mount toggle availability

**RESOLVED 2026-08-06.** Moot: the mode switch is now **two positions**, stereo VCF or stereo
VCA, not three.

That is a **DPDT** (one pole per stereo side), which is a commodity part. No 4P3T hunt, no
rotary fallback, no panel-layout risk. See
[ADR 0007](../decisions/0007-buchla-lpg-over-serge-vcfq.md).

---

## Q8. Is Patch SM D8 (MISO) actually free?

**RESOLVED 2026-08-05.** Yes. `libDaisy/src/dev/oled_ssd130x.h` sets the SPI transport to:

```cpp
spi_config.periph_direction = SpiHandle::Config::Direction::TWO_LINES_TX_ONLY;
spi_config.pin_config.miso  = Pin(PORTX, 0);   // unused-pin sentinel
```

Write-only confirmed, MISO explicitly unused. **D8 is free**, and after the Q14 correction it
carries **pot 12** (the MSP430 data-ready IRQ moved to A8).

---

## Q9. libDaisy SSD130x `Update()`, blocking or not?

**RESOLVED 2026-08-05.** The DMA path is live. The design state's concern is stale for this
revision.

`Update()` branches on `useDma_` and calls `TransferPageDma(0)`, which calls
`transport_.SendDataDma(...)` at line 646 with `SpiPageCompleteCallback` chaining page to page.
The commented-out line at 650 is a leftover debug variant two lines below the real call.

At 1KB per frame it barely mattered either way.

---

## Q11. LGE108 vs CGS108 topology

**CLOSED 2026-08-06.** Moot. The analog section is **Eddy Bergman's Buchla-style LPG, doubled
for stereo**. Serge VCFQ is not being revisited, so the CGS108 / LGE108 question is academic.
Reasoning retained in [ADR 0007](../decisions/0007-buchla-lpg-over-serge-vcfq.md).

---

## Q12. FR2675 symbol and footprint in EasyEDA/LCSC library

**RESOLVED 2026-08-06.** Using the **LCSC part C2052972 (MSP430FR2675TPTR)** schematic symbol
and footprint. Verify the footprint against the datasheet PT package drawing before ordering,
which is a 10-minute check that prevents a dead board.

---

## Q14. Are A8/A9 really reserved for DFU and USB MIDI?

**RESOLVED 2026-08-06. No, and the original documentation was wrong.** This cost two usable
pins and capped the design at 10 pots until corrected.

**Patch SM has two independent USB ports.** Verified against the Rev3 schematic
(`ES_Daisy_Patch_SM_Schematic.pdf`, 2024-02-08) and libDaisy source:

| Port | Peripheral | Pins | On the header? | libDaisy role |
|---|---|---|---|---|
| **Onboard Micro USB** | USB_OTG_FS | PA11 / PA12 (+PA9 VBUS) | **No.** On the module. | `usbd` = **device**: DFU, USB MIDI |
| **A8 / A9** | USB_OTG_HS | PB14 / PB15 | Yes | `usbh` = **host**: USB drives |

Evidence:

- The schematic shows a **Micro USB connector on the module**, netted `USB_OTG_FS_D_+/-`,
  `USB_OTG_FS_VBUS`, `USB_OTG_FS_ID`, with the note that it "allows for powering of the MCU
  from just USB (allowing for pre-flashing, etc. without having to have it powered by
  eurorack)". The header separately carries `USB_HS_DP` / `USB_HS_DM`.
- `libDaisy/src/usbd/usbd_conf.c` (device mode) configures `USB_OTG_FS` on `GPIOA`
  `GPIO_PIN_11 | GPIO_PIN_12`, plus PA9 for VBUS.
- `libDaisy/src/usbh/usbh_conf.c` (host mode) configures `GPIOB` `GPIO_PIN_14 | GPIO_PIN_15`
  with `GPIO_AF12_OTG2_FS`.
- `DaisyBootloader` default (`#if !DSY_DFU_USE_EXT_USB`) runs DFU on FS and initialises USB
  **host** on the external port to read firmware from a drive.

**Decision: spend A8/A9 on IO.** Given up: panel USB jack, firmware-from-USB-drive, future USB
MIDI host. Kept: DFU over the onboard Micro USB, SD card firmware drop, USB MIDI device.
The practical cost is that **USB access means unscrewing the module from the rack.**

**Build the bootloader without `DSY_DFU_USE_EXT_USB`**, which would move DFU to a port this
board no longer wires.

---
---

# New, opened by the pin allocation work

## Q13. Do the gate outputs drive BSL cleanly through a divider?

**Blocks:** the BSL-over-Daisy plan, which is now on B5/B6.
**Status: OPEN.** Prototype bench check.

Gate outputs are **0-5V** (Patch SM datasheet Table 3) and the **MSP430 I/O absolute max is
DVCC+0.3V = 3.6V**. RST and TEST each need a **5V to 3.3V divider**, two resistors per line.

The datasheet gives output impedance (100R) but **not the internal topology of the gate output
stage**. Confirm on the bench that B5/B6 toggle cleanly as GPIO through the divider.

**Why this matters more than it looks:** BSL entry needs **two clean rising edges on TEST while
RST is held low**, and the single most common BSL entry failure is exactly "fewer than two
rising edges". Mushy edges from the divider would present identically to a protocol bug, and
you would chase it in the wrong place.

**How to close:** scope B5/B6 at the MSP430 pin with the divider fitted, before writing any BSL
code.

## Q15. Does A9 drive the OLED cleanly as SPI MOSI?

**Blocks:** the display, and with it pots 11-12.
**Status: OPEN.** Prototype bench check.

**PB15 (A9) is a supported SPI2_MOSI pin**, confirmed in `libDaisy/src/per/spi.cpp:741`
alongside PC1 and PC3, all `GPIO_AF5_SPI2`. `SpiHandle` accepts it with no custom code.

The open part is analog, not software. **A9 is normally USB_HS_DP**, and the module may carry
ESD protection or common-mode filtering on those lines whose capacitance could soften SPI
edges. At SSD1309 clock rates this should be a non-issue, but it is worth ten minutes.

**How to close:** drive the display from A9 on the first prototype and scope MOSI at the panel
connector. If the edges are poor, drop the SPI clock first, since 1KB per frame leaves plenty
of headroom.

**If it fails:** MOSI returns to D9 and the design falls back to 11 pots, with pot 11 on D8.
No respin required if the pot footprints are already there, which is the argument for routing
all 12 and populating 10.

---

## Q17. How tight can the inter-pad gap be?

**Blocks:** crosstalk between adjacent pads. Vertical spacing only.
**Status: OPEN**, but **de-risked**, and cheap to answer alongside the test board.

**Promoted then demoted, both on 2026-08-06.** It was briefly the highest-leverage hardware
question, because the reference composition appeared to lock `pad length = 12 x pad pitch`,
which would have made the gap set the size of the whole instrument.

**That ratio turned out to be an artefact.** The reference sketch drew pads as single strokes
with no thickness, so the 420/35 measurement described the drawing, not a design intent. Pad
length and gap are now independent, and the gap costs nothing but blank panel.

**The layout now uses a 9mm gap**, the maximum that fits the lower region. That is close to the
design state's **>=10mm closest approach** guidance, where the earlier 6mm was well under it.
So the geometry moved toward the guidance, and a bad answer here is much less expensive than it
looked.

**Still worth measuring**, because a grounded guard strip might permit tighter spacing if the
layout ever wants it back, and because nobody has confirmed the >=10mm figure applies to
parallel pads at all (it was written for the diagonal layout where pads converge at a point).
See [../panel-budget.md](../panel-budget.md).

Four pads at 12mm plus three gaps at 10mm consume **78mm** of panel height. **The 10mm figure
is an extrapolation**, taken from the design state's ">=10mm closest approach" guidance which
was written for the *diagonal* layout, where pads converge at a point. Parallel pads sit at
closest approach along their whole length, so the requirement may differ in either direction.

**A grounded guard strip between pads may allow a tighter gap.** Across three gaps this is worth
up to 30mm of panel height, which is the difference between a comfortable layout and a cramped
one.

**How to close:** lay out **two** pads on the single-pad test board instead of one, at two or
three candidate gap widths, with and without a guard strip. Measure crosstalk. Nearly free,
since the board is already being fabricated for [Q1](#q1-does-a-moving-finger-on-bare-copper-read-cleanly).

See [../panel-budget.md](../panel-budget.md).

---

## Q18. What is the OLED module's outline height?

**Blocks:** the upper strip of the panel budget.
**Status: OPEN.** Datasheet check, ten minutes.

The design state records only the **active area**: 55.01 x 27.49mm. These are **bare panels with
an FPC tail**, so the glass outline is larger. The panel budget currently assumes **~40mm**,
which is an estimate and exceeds the entire strip left by the pads on the old 219 x 110mm board.

**How to close:** pull the mechanical drawing for LCSC C5139768 (HS242L01W4S01) and record the
glass outline plus the FPC tail's bend radius and connector position.

---

## Q16. Does the SSD1309 need CS toggling?

**Blocks:** nothing. Recorded as a known fallback.
**Status: OPEN, not currently needed.**

The budget closes with CS on D1, so this is not on the critical path. But if a pin is ever
needed, SSD1309 in 4-wire SPI generally tolerates **CS tied permanently low** when it is the
only device on the bus. Some SSD130x controllers use CS edges to resync the command/data state
machine. Test before relying on it.
