# Vuulgaris V1 — Design State

Handoff document. Current as of this writing. Items marked **[unverified]** need checking before they drive a decision.

---

## 1. What the instrument is

A 4-channel sample-scrubbing instrument. Long capacitive copper pads on a PCB faceplate represent the length of a waveform; dragging a finger along a pad scrubs through the sample.

This is a pivot away from the original Trautonium-style analog design, made to cut cost and part count. The Trautonium design (MPR121 pitch pads + LDC1612 inductive pressure sensing + sprung compliance layer) is shelved.

Each track has a swappable "machine" that can be either a sampler or a synth. Plaits is the synth engine.

**Each channel also has a looper.** Loop lengths may differ but are integer multiples of a shared base length, so they stay in sync. The mix passes through the stereo LPG, and with the source switch on "resample" that analog output returns to `AUDIO_IN` and can be captured into a channel as new material. **The filter and gate are printed into the sample rather than applied at playback.** See **[workflow.md](workflow.md)**.

---

## 2. Architecture

```
[ FACEPLATE PCB ]
  4x 175mm capacitive pads (exposed copper, no overlay)
  MSP430FR2675TPTR (CapTIvate touch MCU) mounted on back side
        |
        |  UART (primary) or I2C (fallback), + IRQ, + BSL entry lines
        v
[ MAIN PCB ]
  Daisy Patch SM (STM32H750) — audio engine, sample playback, UI
  microSD socket
  2.42" SSD1309 OLED (SPI)
  Rotary encoder
  Stereo Buchla-style low pass gate (analog)
```

---

## 3. Capacitive sensing

### Part
**TI MSP430FR2675TPTR** — 48-pin LQFP (PT package). LCSC part **C2052972**.

Verified specs:
- 16 self-cap touch IO / 64 mutual-cap sensors
- 4 parallel measurement blocks (confirmed by exact part number in TI SLAA842)
- 32KB FRAM, 6KB SRAM (ample; 4 sliders + serial link is nowhere near this)
- 43 GPIO, 12-bit ADC

Why 4 measurement blocks matters: TI states devices with fewer than 4 are generally not recommended for sliders, because elements measured in separate cycles sit at ground potential and degrade their neighbours' linearity.

### Pad geometry — comb teeth with RX0 wraparound

**Topology:** vertical comb teeth, not a horizontal zigzag boundary. Each tooth is split into a **top bar and a bottom bar** whose heights ramp complementarily. Position is encoded by the copper ratio between the two halves, which is linear by construction rather than approximated. A finger always spans many teeth, so tooth quantisation doesn't reach the position value.

**Structure:** 4 channels, **5 segments**, **4 interpolation zones**. Order along the axis: RX0, RX1, RX2, RX3, RX0.

Presence functions, `t` running 0→4 across the pad:

```
RX0 = max(0, 1-t) + max(0, t-3)     <- appears at BOTH ends
RX1 = max(0, 1-|t-1|)
RX2 = max(0, 1-|t-2|)
RX3 = max(0, 1-|t-3|)
```

These sum to 1 everywhere, so total copper per tooth is constant along the pad.

**Vertical placement alternates** so a strip never stacks the same channel:
- top half → RX0 or RX2
- bottom half → RX1 or RX3

This puts RX0 on top in *both* end zones, keeping the pattern consistent across the wrap.

**RX0 is one net.** Both end groups must be connected on the board. TI requires this for the default slider algorithm to work. Route the return on the layer below, never under the electrodes.

**Minimum copper enforcement.** Near a ramp end one bar's computed height falls below the fab limit. Do **not** draw it as a sliver — sub-0.127mm copper etches away or comes out fragile. Instead drop the bar and hand its height to the surviving bar, which is already the dominant channel at that point. The position ramp is unaffected.

**Working dimensions:**

| | |
|---|---|
| Pad length | 175mm (inside TI's demonstrated 300mm on four electrodes) |
| Pad width | 12mm (10–12mm is the useful band; wider raises base capacitance without helping a lengthwise scrub) |
| Zone length | 43.75mm |
| Teeth per zone | 20 → 80 total (15/zone → 60 total also fine) |
| Tooth pitch | 2.19mm @ 80 teeth |
| Tooth width | 1.98mm |
| Tooth-to-tooth gap | 0.21mm |
| Top-to-bottom gap | 0.20mm |
| Min copper width | 0.15mm, enforced |

**Pin assignment order is not arbitrary:** RX0→E00, RX1→E01, RX2→E02, RX3→E03. Generate the assignment in Design Center *first*, then lay out the PCB to match. Swapped pins produce garbage interpolation.

**Tools:**
- `vuulgaris-comb-pad-generator.html` (this project) — parametric, live checks against fab limits, exports SVG at true mm scale with one `<g>` per net.
- TI **SLAA891** OpenSCAD scripts generate TI's own validated pattern and export DXF. Use these to cross-check the generator's output before committing copper.

### Resolution
Configurable. TI: number of discrete positions = the configured resolution. Set 1000 and you get positions 0–999 across 175mm (0.175mm per step). Well beyond 10-bit.

The real limit is **jitter, not resolution.** If reported position wanders N counts at rest, usable points = 1000/N. This is the number to measure. Smoothing fixes it at the cost of latency — a direct tradeoff, since scrub position jitter becomes audible warble.

### Endpoint trim
TI documents that most slider layouts can't reach 0 and max at the physical extremes, because a finger's centroid doesn't align with the slider endpoint. `Lower_Trim` / `Upper_Trim` parameters correct this, tuned by touching each end and observing. **Plan for a few dead millimetres at each end** — mark the usable scrub region inside the copper, or extend copper past the printed scale.

### No overlay — consequences
Direct finger-to-copper contact. This is outside TI's design assumptions (all their tuning guidance assumes 1.5–4mm of plastic).

- **Larger signal delta** than TI's reference designs. Retune for lower conversion counts. Buys margin on latency and filtering.
- **ESD is now on you.** TI's fallback for no-overlay: 470R–1k series resistor per electrode + TVS clamp (they name TPD1E10B06) between electrode and ground, on the electrode side of the resistor. 5 electrodes × 4 pads = 20 of each. Place near the MCU with a low-impedance ground path.
- **Specify ENIG, not HASL.** HASL leaves uneven solder — looks bad, feels worse under a sliding finger, and won't wear well. ENIG is flat and won't tarnish.
- Upside: no bubble-induced dead spots, uniform sensitivity along the whole pad.

### Layout rules (from TI design guide)
- Keep MCU-to-electrode traces as short as possible; trace length adds parasitic capacitance and noise susceptibility. **This is why the MCU goes on the faceplate.**
- TI explicitly says to avoid routing capacitive sensing lines through board-to-board connectors or cables — connectors are significant noise receptors.
- Do **not** ground-pour under electrodes or their traces. Parallel-plate capacitance to a nearby pour is the dominant parasitic contributor. Hatched ground at distance if needed.
- Decoupling caps and ESD parts right at the MCU.
- Route digital lines to the main board away from electrodes, ideally exiting the opposite edge.
- Suggested stackup: L1 electrodes, L2 traces, L3 hatched ground, L4 MCU + components. RX0's full-length return trace can't run under the electrodes on the same layer.
- MCU placement: centre of the pad group, to equalise trace length across all four pads (unequal lengths = unequal baselines).
- Avoid electrodes at PCB edges (weakens ground shielding).

### Open concerns
- **Scan rate across 4 sliders.** 4 blocks × 4 pins each = each slider's own elements scan in parallel (good for linearity), but the four sliders scan in four sequential cycles. Effective per-pad update rate is 1/4 of a single-slider design. **[unverified]** — no published number for this config. Design Center reports measured scan time directly; get it early.
- Enabling noise immunity turns on frequency hopping, aggregating four conversion frequencies. That multiplies scan time ×4 *on top of* the four sequential sliders. First knob to trade if latency is tight — against being next to switching supplies and audio circuitry.
- Two fingers on one pad reads as a single averaged position. No palm rejection with exposed copper.

### Why not MPR121
- 12 channels; 16 needed → two chips.
- No slider algorithm. Gives per-channel filtered data only; centroid math and endpoint correction are on you.
- 10-bit ADC, baseline registers expose only the top 8 bits.
- Measures **one electrode at a time** — 16 sequential measurements vs CapTIvate's 4 grouped ones. On a moving finger, sequential sampling smears the centroid.
- MPR121's only advantage is toolchain simplicity (no CCS, no Design Center, no second firmware).

### Why not SoftPot
- Requires pressure (membrane switch); light lateral scrubbing drops out.
- ±3% linearity = ±5mm absolute error over 175mm.
- $8.95 (50mm) to $27.50 (500mm) each, recurring per unit.
- Kills the exposed-copper faceplate concept entirely.
- Finite mechanical cycle life.
- Still useful as a **bench prototyping stand-in** to nail firmware and scrubbing feel before cap-touch hardware exists.

---

## 4. Development & programming (MSP430)

### Tuning requires the PGMR — buy one, once
The Design Center cannot talk to an MSP-FET or a LaunchPad eZ-FET. **CAPTIVATE-PGMR** carries a separate MSP430F5528 running HID Bridge firmware that streams live sensor data to the PC as a USB HID device. That live data view is the entire point: jitter, scan time, linearity, trim.

**Put the CAPTIVATE-PGMR connector on the faceplate PCB.** TI's recommended workflow: build your custom sensing board, integrate while keeping the PGMR connector so Design Center works against real hardware, remove after testing. Tuning against the actual pads in the actual enclosure next to the actual switching supply is the only tuning that counts. Leave unpopulated on production units.

There is **no FR2675 dev board.** TI's own recommendation for evaluating the FR2675 is CAPTIVATE-FR2676 + CAPTIVATE-PGMR. Same silicon for touch purposes (FR2676 just has 64KB/8KB vs 32KB/6KB). CAPTIVATE-BSWP is listed as required for evaluating self-cap designs and gives a reference slider baseline. The FR2676 board has a 48-pin sensor panel connector for plugging in your own test pad.

Design Center version is 1.83.00.08, dated May 2020. Stale toolchain; release notes say to re-create projects made in earlier versions.

**Migration note:** Design Center projects target a specific device. Regenerate for FR2675 (PT/LQFP-48) when moving to your own board. CAP pin *naming* carries over; physical pins don't.

### Production programming — no programmer per unit
BSL (bootstrap loader) lives in **secure ROM** and works on a virgin chip from the reel.

**Verified in TI SLAU550, device table:** MSP430FR2675, BSL version 00.09.36.B5, UART on eUSCI_A, I2C on eUSCI_B. Both interfaces supported.

Plan: JLC solders a blank chip; the Daisy flashes it over the UART already routed.

Requirements and gotchas:
- **2 extra wires** from Daisy: RST and TEST (BSL entry sequence). This is the hardware cost.
- Entry sequence: RST/NMI held low while pulling TEST high and applying the next two edges (falling, rising); BSL starts after TEST is held low and RST released. TI documents failure modes — the common one is fewer than two rising edges on TEST while RST is low. **Expect to lose a day here with a logic analyzer.**
- **Wait ~300ms** after entry invocation before the first command. This BSL version is slow to initialise. Skipping the wait looks like a hardware fault.
- Password = contents of the interrupt vector table (FFE0h–FFFFh). All FFs on a fresh chip; becomes your vectors after flashing. Wrong password with mass erase enabled → chip wipes and you start over. Recoverable.
- **Known doc bug:** SLAU550 page 18, I2C unlock example shows length field `0x33` where it should be `33` decimal. If I2C won't unlock, check this first.

### Brick risk: essentially zero if you don't go looking for it
BSL code is in secure ROM and cannot be overwritten. TI: even if the device is secured by disabling JTAG, the BSL still works.

**The one permanent brick:** deliberately disabling BSL *and* locking JTAG. TI's forum confirms that with BSL disabled completely you cannot regain access. **Leave JTAG/SBW unlocked and BSL enabled — i.e. don't touch the security settings.**

**Put 4 SBW test pads on the board regardless** (TEST, RST, 3V3, GND). Free, and it's the recovery path. A $12 MSP430 LaunchPad's eZ-FET can flash through them.

### Alternative production options (if BSL-over-Daisy proves painful)
- Distributor pre-programming (Digi-Key / Mouser / Arrow) — setup fee + cents per part; standard at volume.
- Pogo-pin test fixture + LaunchPad eZ-FET during board test — cheapest for small batches.
- Gang programmer (MSP-GANG, Elprotronic GangPro430) — 8 at a time, worth it in the hundreds.

---

## 5. Daisy Patch SM

Datasheet v1.0.5 reviewed. Key corrections to common assumptions:

- **D8 and D9 are primarily ADC pins** (ADC_12/PC2 and ADC_11/PC3). SPI2_MISO/MOSI are the *alternate* function.
- **A2 and A3 are primarily ADC_9 and ADC_10**, with UART4 as alternate.
- **B9/B10 (gate ins) are Input Only, not GPIO.** They carry Eurorack conditioning: negative-to-positive rail tolerance, 100K input impedance, typical 0–5V. libDaisy defaults `GateIn` to inverted because of the suggested BJT input circuit. **Do not use these for an encoder.**
- Everything on the C header is Input Only or Output Only.
- Actual bidirectional GPIO: **A2, A3, A8, A9, B7, B8, D1–D10**.
- **D2, D3, D6, D7 have 47K pullups fitted.** Electrosmith notes this may affect UART behaviour on those pins. If freeing SD pins, prefer D4 and D5 for reuse.
- **A2/A3 and B7/B8 both map to UART4_RX/TX** — alternate pin mappings for the same peripheral. Route both as a fallback, populate one.
- Pot wiring differs by group: CV_1–CV_8 take ±5V and wire to the 5V output; ADC_9–ADC_12 are 0–3.3V and must wire to the 3V3 output (A10).
- CV outputs are 12-bit and **can run at audio rate** (Electrosmith ships an example), but that requires writing the DAC per-sample inside the audio callback, not the default block rate (~1ms at 48-sample blocks). Fine for vactrol drive since the vactrol's lag dominates.
- **CV output timing can be degraded by OLED and MIDI activity.** Keep display refreshes off the audio callback; no full-frame redraws during timing-sensitive CV.
- microSD reference part in the datasheet: PJS008U-3000-0. No pullups needed (already fitted).

### Memory tiers
| Tier | Size | Volatile | Use |
|---|---|---|---|
| SDRAM | 64MB | yes | **Playback buffer.** Samples resident here; scrubbing does arbitrary random access, so this is mandatory. |
| QSPI flash | 7936 KB region | no | Firmware (at 256KB offset) + factory samples |
| SD card | unlimited | no | User samples |

SDRAM objects must be declared globally with `DSY_SDRAM_BSS` and can't have meaningful constructors. Plan buffers as static arrays.

**Compile `APP_TYPE=BOOT_SRAM`, not `BOOT_QSPI`.** BOOT_QSPI runs the program from QSPI and can grow to ~7.75MB, eating your sample space. SRAM execution is also faster (max ~480–512KB with a custom linker script).

### QSPI-only sample capacity (no SD card)
~7.2MB usable after firmware:

| Format | Total | Per track (÷4) |
|---|---|---|
| 48k 16-bit mono | 75 sec | 19 sec |
| 44.1k 16-bit mono | 81 sec | 20 sec |
| 32k 16-bit mono | 112 sec | 28 sec |
| 22k 16-bit mono | 163 sec | 40 sec |
| 48k 16-bit stereo | 37 sec | 9 sec |

Tool: `DADDesign-Projects/Daisy_QSPI_Flasher` on GitHub loads sample files into QSPI over USB.

### SD bus width
- 4-bit = 6 pins (CLK, CMD, D0–D3). 1-bit = 3 pins (CLK, CMD, D0). ~4× bandwidth difference.
- `Config::Defaults()` is 4-bit @ 50MHz.
- Community threads skew toward 1-bit: multiple people got SD working only after setting `BusWidth::BITS_1`. **But those were breadboard/flying-wire setups** — three extra high-speed lines on jumper wires is where signal integrity dies. On a real PCB, 4-bit should behave.
- Electrosmith testing: smooth playback at 4-bit down to 400kHz, or 1-bit at 12.5MHz. 1-bit at 400kHz is too slow to stream audio.
- **For this build, 1-bit is probably right** — samples load into SDRAM at boot rather than streaming, so bandwidth only affects a boot-time delay of a second or two.
- **Recommendation: route all 6 pins anyway.** Copper is free; choose the width in software.
- **[unverified]** Whether the Daisy bootloader hardcodes 4-bit for SD-card firmware updates. Grep DaisyBootloader before committing to 3-pin wiring.

### Firmware update paths
Bootloader lives in internal 128KB flash; the application always lives in QSPI at a 256KB offset. Bootloader offers USB DFU **or** dropping a `.bin` on SD/USB media. Grace period is 2.5s on startup with sinusoidal LED blinks.

- **USB DFU** — works, zero effort, requires a cable.
- **SD card drop** — much nicer for a product; check the 4-bit question above.
- **Audio (QPSK)** — possible. Electrosmith's open-source announcement names QPSK-encoded audio as an example of what forks can add. Reference implementation is Mutable Instruments' `stm_audio_bootloader`. **Not recommended:** a documented user account of the MI process reports hundreds of failed attempts across volumes and playback devices. You'd also fork and maintain a bootloader and bring up the codec before it can listen.
- **MIDI SysEx** — better target than audio if you want a no-cable path. Digital transport, no level dependence, and `SonBonAudio/DaisySeedMidiBoot` already exists (forked from OpenWare).

---

## 6. Analog section — stereo low pass gate

**Decision:** stereo Buchla 292-style low pass gate, based on **Eddy Bergman's published design** (free, he invites builds). Replaced an earlier plan for a stereo Serge variable-Q filter.

Keeps the **VCA / VCF / both** mode switch so the sampler/synth engine can run through an analog VCA and VCF.

### Vactrol count
Bergman's design uses **two vactrols for one channel** (one VCA path, one filter path). **Stereo needs four.**

### Problems to solve
- **Bergman rolls his own vactrols** from an LED + LDR in heatshrink, and notes soldering an extra LED over one to dim it because it sounded better. That's a hand-tuned one-off. For a stereo product you need four cells matched in both on-resistance and decay across L and R. Buy Xvive VTL5C3s and match by measurement, or use **VTL5C3/2 duals** so each stereo pair comes from one package.
- **Excelitas discontinued the Vactrol line.** Current source is the Xvive reissue, ~$5–8 each. Reports say Xvive uses a brighter LED giving a longer release, so drive current needs trimming for consistency.
- **Vactrol bleed** — the LPG never fully closing. Prism Circuits' 4U version (also two VTL5C3s) adds circuitry specifically for this. Bergman's design may not address it. Solve deliberately rather than rediscovering it on assembled hardware.
- **[unverified] RoHS / cadmium.** Vactrols use cadmium sulfide photocells; cadmium is restricted. Verify current exemption status before designing in, especially for JLC assembly and any EU sales. This surfaces late and expensively.
- Bergman's is a **stripboard layout**. Redraw in KiCad/EasyEDA — also the right move IP-wise.

### Switching
- **Two switches**, not one. One selects filter placement (pre/post); one selects source (resample vs external input).
- The source switch needs enough poles for **two stereo pairs**. DPDT is sufficient for two stereo sources → one stereo destination: pole A carries L (throws resample-L / ext-L), pole B carries R.
- **Break-before-make (non-shorting)** is correct here. A shorting switch would briefly tie two low-impedance outputs together. Add a 100k–1M resistor to ground on the switch common so the node doesn't float during the open moment, plus DC blocking caps on both sources.
- Standard 6-pin DPDT: **middle pin of each row is the common** (pins 2 and 5; throws 1/3 and 4/6). Lever direction is inverted relative to the pin it selects — flipping up connects to the bottom throws. **Silkscreen labels after bench-confirming, not before.** Verify pinout with a multimeter on the actual part; PCB-mount slide switches can differ.
- Mode switch (VCF/VCA/both) needs both channels ganged. That's 4P3T, or DP3T if switching can be reduced to two poles per channel. **4P3T panel-mount toggles are uncommon — check availability before committing panel layout.** Rotary may be the answer.

### Serge VCFQ — why it was dropped (for the record)
- No fully public schematic exists for a true Serge VCFQ, by design.
- CGS112 (Ken Stone's DIY version) is published, but its BOM lists "CGS108 submodule ×3" as a line item. The gain cells are daughterboards. The schematic is a complete drawing of a board that is two-thirds of a filter. (Only one TL072 + one TL074 in the whole BOM — the voltage-controlled elements are all inside the submodules.)
- CGS108 internals were never published; described only as essentially a voltage-controlled op amp. Ancestry is the Blackmer log-antilog VCA patent (expired).
- **Low-Gain Electronics publishes an LGE108 schematic** (public PDF) and sells pre-assembled SMD boards — a drop-in replacement for the CGS108 in the same board position. **[unverified]** whether the LGE108 circuit is topologically identical to the CGS108 or an independent Blackmer-derived implementation. It's SMD and the CGS108 was through-hole BC547/BC557, so not a literal copy at minimum. Ask Low-Gain directly.
- Modern equivalent: **THAT2180** per gain-cell position (what Random*Source uses in their licensed SMD VCFQ — no transistor matching required). Six for stereo, ~$36–45.
- **Killer for a product: calibration burden.** Six gain cells = six trimmer-and-scope passes per unit shipped, plus per-cell trims. Unbounded labour on a build meant to be cheap. LM13700 (3 packages, ~$6, no matching) or THAT2180 both eliminate it.
- Legal position (not legal advice): copyright on a schematic covers the *drawing*, not the circuit. Building and selling from a published schematic isn't copyright infringement; republishing the drawing or copying the PCB layout is. Blackmer's patent is expired; Tcherepnin never patented the gain cell (trade secret, not IP). The real exposures are trademark (don't use "Serge" or "VCFQ" in marketing) and reputational.

---

## 7. Display

**Part:** 2.42" SSD1309, 128×64, **SPI**. LCSC **C5139768** (HS242L01W4S01). Active area 55.01 × 27.49mm, supply 1.65–3.3V.

Why this one:
- **Only display family with a shipped libDaisy driver.** `OledDisplay` uses the SSD130x driver; libDaisy issue #166 confirms SSD1309 in SPI mode. No ST7789 / ILI9341 / SSD1322 driver exists — those mean writing your own transport, which is exactly where audio glitches come from.
- **1KB per full frame.** SSD1322 (256×64, 4-bit grey) is 8KB. A 320×240 TFT at 16bpp is 150KB — 150× the bus traffic and 150× the window competing with audio and CV timing.
- 3.3V supply matches Patch SM's 3V3 rail directly. No level shifting.
- No backlight; better off-angle legibility than TFT.
- 2.5× the diagonal of a 0.96" panel at the same pixel count.

Interference ranking, worst → best: I2C anything → TFT over SPI → SSD1322 → SSD1309.

**Stock warning: 27 units.** Second SPI option C5139769 has 8. I2C versions are better stocked (C7466000 blue 67, C7466001 white 22) but I2C is the interference-worst choice. 2.42" SSD1309 SPI is a commodity format widely available outside LCSC — plan on second-sourcing for production.

Cheaper fallback: **C5139767**, 1.54" SPI, 49 in stock, $7.21@1 / $5.06@100.

Notes:
- These are **bare panels with an FPC tail**, not breakout boards. Board needs an FPC connector, not a 2.54mm header. Check pin count and pitch on the datasheet.
- SSD1309 panels usually need external charge-pump caps and an IREF resistor.
- **[unverified]** Whether MISO (D8) is truly free — depends on the panel being write-only. Usually yes for SSD130x; confirm.
- libDaisy SPI DMA is documented as non-blocking, and IRQ handlers exist for SPI2–SPI5. `OneBitGraphicsDisplay::Update()` returns true when finished, described as being for chained DMA transfers. **[unverified]** — the `SendDataDma` line in SSD130x source appears commented out, so the shipped `Update()` may still be blocking. At 1KB it doesn't matter much either way.
- DMA buffers must be in the DMA memory section and at **global scope**.
- **Known issue to test early:** a 2022 report on Daisy Patch showed audio working but the OLED dead under both `BOOT_QSPI` and `BOOT_SRAM`. May be fixed. Since this design has both a display and the bootloader, verify that path before it's load-bearing.

---

## 8. Pin allocation (Daisy Patch SM)

**Note:** memory records a later IO plan of *three ADC inputs per channel (12 total), all panel pots, no CV jacks into the Daisy*, with the encoder on the main PCB and the two CV outputs generating LPG cutoff envelopes shaped by two of the 12 pots. **Reconcile that against the allocation below before layout — they may conflict on pin count.**

| Function | Pins | Notes |
|---|---|---|
| SD card (SDMMC) | D2–D7 | 6 pins for 4-bit; 3 for 1-bit (frees D4, D5 — avoid D2/D3/D6/D7 for reuse, 47K pullups) |
| Display SPI2 | D1 (CS), D9 (MOSI), D10 (SCK) | + DC and RST GPIO on top of these |
| MSP430 link | B7/B8 (I2C1) **or** A2/A3 (UART4) | Same peripheral, alternate mappings — populate one |
| MSP430 IRQ | 1 GPIO | Signals data-ready; avoids polling |
| MSP430 BSL entry | RST + TEST = 2 GPIO | Required for the Daisy-flashes-MSP430 plan |
| Encoder A, B, push | 3 pins | D8 + whichever pair the MSP430 link didn't take |
| Pots | CV_1–CV_8 (C2–C9), ADC_9–12 | 12 ADC total |
| CV outs → LPG | CV_OUT_1, CV_OUT_2 | One per channel (mode switch routes to VCA/VCF/both within a channel) |

**This is tight.** Release valve: a **CD4051 mux** on one ADC pin — libDaisy has `InitMux` built into `AdcChannelConfig` for exactly this, turning one pin into eight pot reads. **Design the footprint in now even if left unpopulated.**

Also: display DC and RST are two GPIO not counted in early estimates. Some modules tie RST to a pullup, saving one.

---

## 9. Inter-board interface

Only ~8–10 pins cross from faceplate to main board:
- 3V3, GND
- UART Tx/Rx (and I2C SCL/SDA if both routed)
- IRQ
- BSL: RST, TEST
- SBW test pads: TEST, RST, 3V3, GND (shared with above)

**Do this:**
- Route both UART and I2C. Check the FR2675 datasheet pin function table for the PT package — eUSCI_A and eUSCI_B may share physical port pins, in which case use 0R jumpers to select. **[unverified]**
- **Test points on all four signals.** When this doesn't work first time, you want a scope probe point that isn't a QFN/LQFP pin.
- Bring MSP430 SBW pins out to a header. You'll reflash constantly during sensor tuning.
- **Regulate 3V3 on the main board and filter locally at the MSP430.** Don't share a rail with audio circuitry — cap touch does not love switching noise. The LPG is on ±12V, so there's a regulator in the chain somewhere.

---

## 10. BOM so far

Confirmed prices, qty 1:

| Part | Source | Price |
|---|---|---|
| Daisy Patch SM | Electrosmith direct | $31.99 |
| MSP430FR2675TPTR | LCSC C2052972 | $4.49 |
| 2.42" SSD1309 SPI | LCSC C5139768 | $12.22 |
| microSD socket | LCSC C393941 | $0.06 |
| **Subtotal** | | **$48.76** |

Buy the Patch SM direct — resellers are ~$51.

Estimated remainder (not verified):
- 4× vactrols: $20–32 ← second-biggest line after the Patch SM
- Op amps (LPG): $3–6
- Discretes + passives: $14–24
- 12 pots: $5–12 (revise upward if 12 panel pots is the final plan)
- Encoder: <$1
- Two switches (one 4P3T or rotary): $2–6
- Jacks: $6–12
- ESD (20× TVS + 20× resistors): $3
- PCBs (4-layer faceplate + main), low qty: $20–50
- Board-to-board connectors, power regulation: $4–7

**Realistic total: $125–200 per unit at prototype quantity.** Enclosure not included (prior design was CNC walnut).

### Stock warnings
| Part | LCSC stock |
|---|---|
| MSP430FR2675TPTR (C2052972) | **10** — reels of 1000 available |
| 2.42" SSD1309 SPI (C5139768) | **27** |
| microSD socket (C393941) | 205,170 + 600k at 6–8 day lead |

The first two are prototype quantities, not production quantities. LCSC-Reels is the production path on the MSP430 but is a real cash commitment.

Note: JLCPCB flags that microSD sockets need an assembly fixture for support during placement — not a trivial placement.

### Cost levers
1. Vactrols
2. Display (1.54" saves ~$5)
3. Enclosure (not in the list at all)

---

## 11. Faceplate

**Current layout: Salamis Tablet.** Four parallel pads as the line group, with the tablet's vertical divider, semicircles, crosses at divisions 3/6/9, and Greek acrophonic numerals in the margins. Board approx **219 × 110mm**. Above an irregular crack line sits a five-rule group with a vertical divider and downward semicircle for the screen, encoder and switches. Below, four scrub pads with a vertical divider crossing all four, capped by an upward semicircle.

See `vuulgaris-faceplate-mockup.html` for the current rendering. Note that mockup still draws the **3-zone / no-wraparound** electrode ramp (E1→E4). It needs updating to the 4-zone RX0-wraparound pattern in §3 before it drives layout.

**Earlier arrangement (superseded):** two pads each side, two diagonal one way and two the other, forming a separated triangle in the middle of the rectangular enclosure. If revisited, note: 175mm at 45° needs ~124mm per axis, so the enclosure needs ~250mm in the diagonal-spanning direction. Convergence points create worst-case crosstalk exactly where RX0 sits on both pads — keep closest approach ≥10mm with a grounded strip between.

Decoration and instructions in silkscreen. Exposed copper pads, ENIG finish.

**LCSC does not stock display modules usefully**, and JLCPCB does not do overlay lamination (that's a membrane-switch/graphic-overlay industry — vendors like JRPanel). Not needed given the no-overlay decision, but noted for the record.

---

## 12. Immediate next steps

1. **Validate the sensing concept cheaply before committing.** Buy CAPTIVATE-PGMR (+ FR2676 board + BSWP) and make one cheap 2-layer JLC board with a **single 175mm pad in final geometry**. ~$50, ~2 weeks. Measure scan time, jitter, linearity; hear what it sounds like driving sample position. This tells you whether the interaction works before the faceplate exists. If one pad works, the remaining unknown is arithmetic on the measured number.
2. Pull the FR2675 datasheet pin function table for the PT package — settle the eUSCI_A / eUSCI_B pin muxing question. **This changes the layout.**
3. Confirm the FR2675 symbol/footprint exists in the LCSC/EasyEDA library. If not, LQFP-48 is standard and TI publishes the pinout (~20 min to draw).
4. Grep DaisyBootloader for the SD bus-width question.
5. Verify RoHS/cadmium status on vactrols.
6. Reconcile the two IO plans (§8) before panel layout.
7. Check 4P3T panel-mount availability before committing panel layout.
8. Generate the slider electrode assignment in Design Center **first**, then lay out to match.
9. Decide sample-storage strategy: factory samples in QSPI so the instrument makes sound with no card, user samples on SD. Both stream into SDRAM at load; playback always from SDRAM so scrubbing has no latency. Decide the advertised per-track length limit early — it's bounded by SDRAM, not card size.

---

## 13. Reference links

- CapTIvate Design Guide: https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/CapTIvate_Design_Center/latest/exports/docs/users_guide/html/CapTIvate_Technology_Guide_html/markdown/ch_design_guide.html
- SLAA891 — Automating Capacitive Touch Sensor Design using OpenSCAD Scripts: https://www.ti.com/lit/slaa891
- SLAA843 — Sensitivity, SNR, and Design Margin in Capacitive Touch: https://www.ti.com/lit/slaa843
- SLAU550 — MSP430 FRAM Devices Bootloader (BSL) User's Guide: https://www.ti.com/lit/pdf/slau550
- SLAA685 — MSP Code Protection Features: https://www.ti.com/lit/pdf/slaa685
- CAPTIVATE-FR2676: https://www.ti.com/tool/CAPTIVATE-FR2676
- Patch SM datasheet v1.0.5: https://daisy.nyc3.cdn.digitaloceanspaces.com/products/patch-sm/ES_Patch_SM_datasheet_v1.0.5.pdf
- Daisy Bootloader: https://github.com/electro-smith/DaisyBootloader
- Daisy QSPI Flasher: https://github.com/DADDesign-Projects/Daisy_QSPI_Flasher
- Daisy MIDI bootloader: https://github.com/SonBonAudio/DaisySeedMidiBoot
- libDaisy SDMMC DMA PR (bus width discussion): https://github.com/electro-smith/libDaisy/pull/311
