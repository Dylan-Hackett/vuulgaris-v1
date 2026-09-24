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
- **ESD is now on you.** TI's fallback for no-overlay: 470R–1k series resistor per electrode + TVS clamp (they name TPD1E10B06) between electrode and ground, on the electrode side of the resistor. **4 electrodes × 4 pads = 16 of each** — the pad has 5 *segments* but only 4 *nets*, because RX0 appears at both ends and is one net. Place near the MCU with a low-impedance ground path.
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

### Signal levels — the LPG interface is Eurorack level, and that comes from the module

**Verified 2026-08-16 from the Patch SM datasheet v1.0.5.** Patch SM lists "Stereo
**Eurorack Level** Audio Input / Outputs" as a feature and benchmarks SNR against a
**9.5Vpp** reference sine (±4.75V). Bergman's LPG is a Eurorack design and expects the
same, so `AUDIO_OUT_L/R` → LPG → `AUDIO_IN_L/R` is level-matched as designed. Nothing
to do.

**The catch: that level shifting is on the Patch SM, not in the codec.** It is listed as
a distinguishing feature of the module, so a bare **Daisy Seed does not have it** — Seed
is the AK4556 at line level. Any migration to Seed (see the EOL note below) therefore
needs **~5x gain on both audio outputs and ~5x attenuation on both inputs**, on top of
the CV conditioning and power stage. That is an extra quad op-amp sitting directly in
the audio path.

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

#### SOURCE (SW2) — wired 2026-09-06

`AUDIO_IN_L/R` used to be the Daisy's only dead pins on the audio side. The path now exists:

```
J7 tip ──── EXT_IN_L ──── C501 ──── SRC_EXT_L ───→ SW2.1 (A_NC)
                                                     SW2.2 (A_COM) ── AUDIO_IN_L ──→ U1.B4
BBD_OUT_L ─────────────── C503 ──── SRC_RSMP_L ──→ SW2.3 (A_NO)        │
     └────────────────────────────→ J9 tip                            R501 1M
                                                                       └─ GND
```

R channel identical on `SW2.4/5/6` with `J8`, `C502`, `C504`, `R502`, `J10`.

Three things this section already called for, all present:

- **DC blocking on both sources.** `C501`–`C504`, 1uF. Without them, flipping SOURCE
  steps the common by whatever the two sources' DC offsets differ by, and that is
  a thump straight into the codec.
- **A resistor to ground on the common.** `R501`/`R502`, 1M. The switch is
  break-before-make, so the common is genuinely open for a moment; this holds it at 0V
  instead of letting it float. In parallel with the module's own input impedance it is
  far too big to shift the level.
- **Break-before-make.** Still needs confirming on the actual DW3 part with a meter —
  it is assumed, not measured.

**Nothing else is in the path, deliberately.** Patch SM is Eurorack level in *and* out
(see "Signal levels" above) and `BBD_OUT` is Eurorack level, so both legs are already
matched. No dividers, no buffers.

**The resample tap is `BBD_OUT`, the same node as the output jack** — what you resample
is exactly what the module sends out, including the 470R series resistor. The tap adds a
1uF into 1M beside a jack load; negligible.

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
- **CORRECTED 2026-08-12 from the datasheet.** This is **not** a bare panel with an FPC
  tail — C5139768 is a **module on its own 68.00 x 43.00 x 4.2mm PCB** with a **9-pin**
  interface, which is why the EasyEDA footprint is `LCD-TH_HS242L01W4S01` (through-hole).
  Pins: `1 GND, 2 VCC, 3 SCL, 4 SDA, 5 RES, 6 DC, 7 CS1, 8 FS0, 9 CS2`. **Pins 8 and 9 are
  a separate on-board font chip** (`FS0` data out, `CS2` chip select) — nothing in libDaisy
  uses it, so leave both unconnected, but the footprint has to carry them.
  **The 68 x 43mm module outline is a placement constraint** on a main PCB limited to
  284.3 x 125.0mm, and it is 4.2mm tall behind the panel.
- SSD1309 panels usually need external charge-pump caps and an IREF resistor.
- **[unverified]** Whether MISO (D8) is truly free — depends on the panel being write-only. Usually yes for SSD130x; confirm.
- libDaisy SPI DMA is documented as non-blocking, and IRQ handlers exist for SPI2–SPI5. `OneBitGraphicsDisplay::Update()` returns true when finished, described as being for chained DMA transfers. **[unverified]** — the `SendDataDma` line in SSD130x source appears commented out, so the shipped `Update()` may still be blocking. At 1KB it doesn't matter much either way.
- DMA buffers must be in the DMA memory section and at **global scope**.
- **Known issue to test early:** a 2022 report on Daisy Patch showed audio working but the OLED dead under both `BOOT_QSPI` and `BOOT_SRAM`. May be fixed. Since this design has both a display and the bootloader, verify that path before it's load-bearing.

---

## 8. Pin allocation (Daisy Patch SM)

> **SUPERSEDED 2026-08-09 by [pin-allocation.md](pin-allocation.md). Do not lay out
> against this section.** The knobs became encoders on two I2C expanders, the MSP430
> IRQ line was dropped, BSL moved to software invocation, and the CV jack moved to
> CV_8. Kept only as the record of what the plan was before those changes.

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

> **SUPERSEDED 2026-08-09 by [pin-allocation.md](pin-allocation.md) "Inter-board
> interface".** Three things below are now wrong: **no I2C crosses this cable**
> (the expanders are local to the main PCB), **there is no IRQ wire** (redundant
> over UART — that is what freed A8), and **RST/TEST are test pads, not Daisy
> pins** (BSL is invoked in software). The UART pin question it calls unverified
> is also settled: default UCA0, pins 4/5.

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
- ESD (16× TVS + 16× resistors): $3
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

### Power: USB-C 5V in, +/-12V from a DKM10E-12

**Decided 2026-08-23, reversing the 2026-08-20 barrel decision.** USB-C to a
Mean Well DKM10E-12, which makes both rails. Full circuit, part numbers and
designator mapping in [power-usbc-dkm.md](power-usbc-dkm.md).

**Why the reversal.** The barrel stage was cheaper -- about $1.39 against $15.36 --
and smaller, 70mm2 against 645mm2. It was also **entirely untested**, invented here
from a datasheet and an adaptation of someone else's topology, with a
minimum-load problem serious enough that it needed a bleeder network that no
single 0402 could legally dissipate. The USB-C design is a circuit Dylan has
already built and run. It was read back **pad by pad out of the routed EasyEDA
board**, not re-derived, so the thing in this repo is the thing that works.

Beyond "it's tested", three real advantages:

- **No reverse-polarity diode and no TVS**, because a USB-C receptacle cannot be
  plugged in backwards. That also removes the barrel design's 0.35V drop, so
  +12V is actually 12V and the rails are symmetric. The dropout-headroom worry
  that forced "the supply must be regulated" is gone with it.
- **The minimum-load problem is gone.** The DKM is regulated, and the two
  indicator LEDs put ~4.5mA permanently on each rail through their 2k2 ballast.
  The -12V rail behaves whether or not the LPG is populated. Compare the barrel
  stage, which needed a purpose-built bleeder and still sat near the boundary.
- **A USB-C powered instrument is unusual**, and it ships without a wall wart.

**Consequences accepted:**

- **Cost.** ~$15 of converter, against ~$1.39. On a one-off this is noise; it
  would matter at volume.
- **Board area.** U7 is a 25.4mm square through-hole module standing ~10mm, in
  the right-edge pocket on the back. The B1212S it replaces was 11.5 x 6.1mm.
- **Two USB ports on one instrument.** The Daisy's own port is **micro USB**, not
  USB-C, so they are not confusable by cable. Label them anyway.
- **Stock.** DKM10E-12 was out of stock at LCSC when the barrel decision was
  made. It is through-hole, so hand-fitting it after assembly is easy, but
  **confirm availability before the fab order** -- from Mouser if not LCSC.

**Untested in THIS layout.** The circuit is proven; its placement here is not.
Two checks, and it is worth being precise about what each one buys:
`tools/edapower.py` regenerates the power block straight out of the `.eprj` and
reports 57/57 against the routed board, so `netmap.json` IS the working circuit
rather than a retyping of it. `tools/netcheck.py` reports 217/217, so the KiCad
schematic is what `netmap.json` says. Neither says the parts physically fit.

### Layout: where the Daisy goes, and why not next to the power

**2026-08-25.** MIDI was dropped -- firmware goes on by opening the box -- so the
Daisy's micro-USB no longer has to reach a wall and its placement is free. It
went to **x[125.5,193.5] y[42.5,82.5], rot 0**, in the dead band between the pot
row and the electrodes.

**Not** next to the power stage, which is the intuitive answer and the wrong one.
Weighted total wire length, audio x10, CV x5, SD x3, SPI x1.5, I2C x1, power
x0.15:

| placement | score | AUDIO | CV | SD | SPI | I2C | PWR |
|---|---|---|---|---|---|---|---|
| **centre, rot 0** | **5611** | 161 | 594 | 51 | 480 | 106 | 355 |
| centre, rot 180 | 6127 | 318 | 392 | 190 | 209 | 68 | 226 |
| bottom-right by the power, rot 0 | 11875 | 405 | 1245 | 313 | 352 | 118 | 109 |
| bottom wall, rot 0 | 9114 | 405 | 579 | 254 | 837 | 73 | 566 |

Sitting on the power stage does buy the shortest rails -- 109mm against 355mm --
and it is worth almost nothing. Those are DC rails; widen the trace and the loss
is millivolts. It costs 244mm of extra analog audio and 651mm of extra CV, run
straight over the capacitive electrodes. **Length barely touches power and is the
whole game for analog.** Roughly twice the weighted cost, for a rail nobody can
measure.

Caveat on those numbers: J2-J5 and J7-J10 are placed but still unwired, so the
scorer cannot see the audio and CV destinations from `netmap.json` -- they are
supplied by hand in the scoring run. Redo this once the jacks are wired.

### place.py: the mirror flag was read from the wrong loop

`Lm` is assigned inside the pad-orientation loop and was then read again inside
the overlap loop, where it is a leftover holding whatever footprint the earlier
loop happened to finish on. **Every box in the overlap and edge checks therefore
got the same arbitrary mirror flag.** It invented a 3.18mm RV3/RV4-vs-U1
collision -- RV4's local y is [-9.14,+4.4], and mirrored that is [-4.4,+9.14],
which moves its bottom edge from 40.94 to 45.68. It would hide a real collision
exactly as quietly. Third mirror-related bug in this file; the other two are
recorded in `gerbercheck.py`'s docstring.

---

### The USB-C sits on a tab through the wall — decided 2026-09-20

**The problem, found by looking at the board.** Every panel connector on the top
edge presents a different face to the wall, because the parts are different
shapes. A right-angle jack's working face is the *nut face* at the end of a 7mm
barrel. An SMD USB-C's working face is its *mouth*, level with its own pads.

```
  outside                                              inside
  ─────────|#####  6mm wall  #####|· gap ·|board edge
         -7.00                  -1.00    0.00
  1/4"  ●                                              tip -9.00, 2mm proud
  3.5mm          ●                                     tip -7.00, flush
  USB-C                                        ●       mouth -0.33   <-- 6.67mm behind
```

The mouth did not even reach the wall's *inner* face. A plug would have needed
about 13.7mm of exposed shell to seat; a real USB-C cable has 7 to 7.5mm.
**It could not have been plugged in.** This was on the open list as "the USB-C
mouth must reach the top edge, seed position only, needs a render not
arithmetic" — the arithmetic was never done, and the render is what settled it.

**Why it is not fixed by moving J11.** Its shield legs sit 2.29mm inside the
edge, so it can move forward maybe 2mm before they walk off the board. The same
constraint that pins the PJ-376 at exactly flush. 6.5mm was needed.

**The fix: a tab.** The top edge steps out over the USB-C:

| | |
|---|---|
| tab | x 366.8 – 379.8 (13.00mm wide), out to y 41.00 (7.00mm deep) — was 43.00 before the 2026-09-23 extension below |
| J11 | moved forward 7.00mm, then 2.00mm more with the extension — now at (373.27, 45.76) |
| mouth | −7.33 in the wall frame — 0.33mm proud of the wall's outer face |

All three connector types now present one plane, so the wall is flat with plain
holes instead of a shaped pocket, and its position is a single number rather
than a set of exceptions. **That was not quite true until 2026-09-23** — the
1/4" jacks stood 2mm proud of it. See "Top edge extended 2mm" below.

**What the enclosure has to provide.** The tab passes *through* the wall, so the
wall needs a slot about **13.5mm wide × 5.5mm tall** (1.6mm board + ~3.2mm
connector body + clearance) at the tab's x range, cut the full 6mm depth. The
plug then mates at the outer face with its overmold entirely outside.

**The tab stops 4.5mm short of the right edge on purpose.** It was widened to
run out to the corner on 2026-09-20 — squarer board outline, two fewer edge
segments — and put back the same day once it was clear the case is **3D
printed**, not milled.

Milled, the wide version was slightly nicer: no inside corner for a router to
pick at. Printed, it is worse, and in the one place a box can least afford it.
Running the slot out to the board's right edge leaves the slot stopping an
assembly gap short of the right wall, so what remains at the top-right corner
is a **~1mm-wide tongue** of wall — two or three perimeters at a 0.4mm nozzle,
which a slicer may thin or drop outright, sitting exactly where the top and
right walls brace each other. That corner is where the box gets its rigidity.

The notch costs nothing to fab: JLC routes a 4.5mm-wide slot with its 2mm bit
without comment, and the quote is on the bounding envelope either way, so the
notch is paid for as solid board regardless. A closed **window** in the wall,
on the other hand, is the same class of feature as the nine jack holes already
needed — bridged across the top, wall material continuous around it, corner
untouched.

Printing also makes the CV-jack counterbore below a non-issue: a locally
thinner wall is modelled, not machined, so it costs nothing. The same is worth
revisiting for the 1/4" jacks, whose thread problem is recorded further down —
printing removes the machining objection to thinning the wall at that row,
though it does not remove the strength one.

**Assembly, which this does not change.** The board already could not drop into
the cavity vertically — nine panel-mount jack barrels cannot enter round holes
that way. It has always had to slide in along y, and the travel is set by the
1/4" jacks:

| | protrudes past the board edge | travel to clear the wall's inner face |
|---|---|---|
| J7–J10, 1/4" | 7.00mm (9.00mm before 2026-09-23) | 6.00mm |
| J2–J6, 3.5mm | 7.00mm | 6.00mm |
| the tab | 7.00mm | 6.00mm |

Since the 2026-09-23 extension every connector needs the same 6mm. **The cavity
must run 125.81mm** from the front wall's inner face to the back wall: the 1mm
gap, the 118.81mm board, and **6mm of air behind it when seated**. (This read
124.81mm with 8mm of air before the extension — 1mm short either way, the front
gap had been left out.) That gap cannot be permanently filled; it is also how
the board comes out for service. It is somewhere to put a cable coil.

Order of assembly: slide the board forward until the jacks are through the wall →
nuts onto the **3.5mm** jack threads from outside (the 1/4" jacks take none, see
below) → faceplate on over the 24 panel parts → nut the six pots → screw the
faceplate to the case. The board never moves vertically.

> **Corrected 2026-09-24.** This used to say "screws down into bosses to locate
> it", and the paragraph above offered the air gap for "retaining bosses". Both
> were wrong: the main board has **no mounting holes, by decision** ("Panel
> mounting", 2026-09-05, and `hardware/kicad/README.md`). It is located by the six
> pot nuts to the faceplate and the 3.5mm jack nuts to the wall; once the pots
> are nutted it cannot slide. The case needs no bosses under the main board.

**Cost on the fab side:** the outline is no longer a rectangle. The envelope is
284.30 × 125.81mm (123.81 before the extension) and JLC quotes on the envelope,
so the 13 × 7mm tab is paid for as if it were the full strip.

### Top edge extended 2mm — 2026-09-23

PJ-603's barrel reaches 9mm past its body where PJ-376 and the USB-C tab reach
7mm. With all three bodies on the board edge, the 3.5mm jacks and USB-C ended
exactly at the wall's outer face and the 1/4" collars stood 2mm proud of it.

**Fix: the whole top edge moved out 2mm** (y 50.00 → 48.00, tab 43.00 → 41.00,
GND zone with it), and **J2–J6 and J11 moved forward 2mm onto it**. J7–J10 did
not move, so their bodies now sit 2mm behind the edge and every connector
reaches the same 7mm past it. The wall stays a flat 6mm, and the 1/4" collars
get 4.5mm of it to sit in instead of 2.5mm — which matters now that they are
PCB-held. Board 284.30 × 118.81mm, envelope 125.81mm.

Two alternatives were tried on scratch copies first: moving only J7–J10 back
2mm (20 DRC errors, five traces behind them plus `R513`), and a 2mm raised band
on the case over the 1/4" row (no board change, but a stepped wall). This one
was chosen for the flat wall.

**Rerouted by hand.** Moving the six connectors dragged their track ends with
them, so nothing was disconnected (0 unconnected, parity 932/932), but it left
55 clearance errors: 27 in the J11 fan-out, 19 where long In1.Cu trunks —
`P5V`, `NEG12V`, `GATE_OUT_1` — thread between the J2–J5 pins, and 9 at J6.
Rerouted in Pcbnew the same day: DRC 0 errors, no net narrower than before, no
net more than 2mm longer except GND (+9mm), no vias added, zone fill current.
The one electrical change worth knowing is the 0.25mm `VBUS` neck from J11's
A4/B9 pads to the wide feed, stretched 0.7 → 2.7mm — about 5mΩ, 7mV at the
1.4A budget.

**Still owed: the faceplate.** The enclosure's front wall moved 2mm outward
relative to the board, so the faceplate needs 2mm more at the jack edge and
every panel y grows by 2. The knobs themselves do not move. `place.py`'s `OY`
goes 7.000 → 9.000 in the same commit as the regenerated
`placement-panel-facing.txt`, or it will move all 24 panel parts 2mm. Nothing
on the main board changes.

---

### Enclosure TODO: counterbore the top wall at the four CV jacks

**Decided 2026-08-18. Do this when the enclosure is built.** Pocket the **outside** face of the top wall from 6.0mm down to ~3.0mm at four spots, so the 3.5mm CV/gate jacks have enough thread proud of the wall to take a nut.

| | board x | panel x |
|---|---|---|
| J2 | 29.15 | 36.145 |
| J3 | 51.15 | 58.145 |
| J4 | 73.15 | 80.145 |
| J5 | 95.15 | 102.145 |

The geometry, all in board coordinates (board edge y = 0):

```
board edge        y   0.00
wall inner face   y  -1.00     1.0mm assembly gap
wall outer face   y  -7.00     6.0mm wall
```

**PJ-376 lands exactly flush at y −7.00 and cannot go further.** Its barrel is 12.00mm from origin to tip while its pads reach 4.30mm the other way, so pushing it forward any more walks the pads off the board edge. Counterboring to 3mm gains ~3mm of exposed thread, which is a real nut.

Two alternatives were considered and rejected. **Closing the 1.0mm board-to-wall gap** buys only 1mm — not enough for a nut — and spends the entire fit tolerance doing it; JLC holds board outline to about ±0.2mm, so at zero designed clearance an oversize board will not go into the cavity. **Accepting PCB-held jacks** works and is normal for right-angle parts, but a hard pull on a patch cable then loads the solder joints instead of the enclosure.

~~**The four 1/4" jacks need none of this.** PJ-603 sits 2.00mm proud already and can reach 8.20mm, so those nut to the wall normally and will take the abuse.~~

**Wrong, corrected 2026-09-20 — it is the 1/4" jacks that cannot be nutted, not the 3.5mm ones.** The 2.00mm protruding is the **smooth Ø10.3 collar**, not thread. That figure came off the silk outline, which is the whole barrel; the datasheets were never read.

Both drawings, now read:

| | barrel | threaded portion | nut |
|---|---|---|---|
| PJ-376, 3.5mm | 4.6mm projection, Ø7.5 flange behind | ØM6 over the 4.6mm | M6 |
| PJ-603, 1/4" | 9.0mm, front 4.5mm smooth Ø10.3 | **M12 over the REAR 4.5mm**, against the body | M12, 14mm A/F, 3.0mm thick |

**Both threads are ~4.5mm and the wall is 6mm.** The thread is shorter than the wall on both parts.

In board coordinates, with the wall spanning y 43.00 (outer) to 49.00 (inner) — **pre-extension**; since 2026-09-23 subtract 2.00 from every y here for the wall, the PJ-376 and J11, but not the PJ-603:

- **PJ-376** — thread runs 43.00 → 47.60, so it exactly reaches the outer face and protrudes by nothing. **The 3.0mm counterbore fixes it**: 3.0mm of M6 thread proud, enough for a panel nut. The hole has to be stepped, Ø7.6 for the first 1.4mm to clear the flange, then Ø6.2. The pocket also has to be wide enough to turn an M6 nut in, ~11mm.
- **PJ-603** — the body face sits on the board edge at 50.00 and the thread runs 45.50 → 50.00, so it **ends 2.50mm inside the wall**. A 3.0mm counterbore exposes 0.5mm. Since the wall must clear the body by the 1.0mm assembly gap, at most 3.5mm of thread is ever available past its inner face, and a 3.0mm M12 nut would need the wall down to about 0.5mm. **Moving the jack forward makes it worse — the thread is at the back of the barrel.**

So the 1/4" jacks cannot be nutted to this wall at any position. Three ways out — **option 1 chosen 2026-09-23**, see below:

1. **PCB-held.** Normal for right-angle parts, and the option already rejected for the 3.5mm jacks because a hard cable pull loads the solder joints instead of the enclosure. Four 1/4" jacks on an instrument is where that matters most.
2. **Thin the wall to ~1.5mm across the 1/4" row.** Gets a nut on, but a 1.5mm wall under four jacks being yanked is its own problem.
3. **A different 1/4" jack with a longer threaded bushing.** Cleanest if one exists in the same footprint that JLC stocks. Not yet searched.

**Decided 2026-09-23: option 1, PCB-held — no nut on the 1/4" jacks.** Option 3
was the only one that touched the board, and it would have meant a new part and
footprint days before fab. The objection to PCB-held is weaker than it reads:
a **sideways** yank is what hurts, and that load goes into the wall, because the
smooth Ø10.3 collar sits in a close-fitting hole. Only a **straight** pull
loads the joints, and pulling a plug out is a small force. Most gear with
right-angle jacks is built this way.

What it asks of the printed case:

- **A stepped hole per jack, small at the outside.** With the top edge
  extended (below), the wall spans y 41.00 → 47.00. The collar fills 41.00 →
  45.50 and the M12 thread starts at 45.50, so: Ø10.5 around the collar, then
  Ø12.2 for the last 1.5mm of wall. Put the step ~0.3mm in front of the thread
  shoulder so it never touches it: the board's locating screws set where the
  board sits, not four jack threads.
- **The collars are flush with the wall**, and 4.5mm of each sits inside it —
  see "Top edge extended 2mm" above.

This is the item the section below used to list as "still unverified: the split between threaded bushing and shoulder". It is verified now, and the answer was worse than the worry.

---

### Panel mounting: one datum family, the rest located but unclamped

**Decided 2026-09-05.** The main PCB has no standoffs of its own — it hangs off
the panel hardware. The faceplate goes on the bushings of the parts that pass
through it and is held by their nuts, so the load path is enclosure -> faceplate
-> nuts -> bushings -> part bodies -> **solder joints** -> main PCB.

**The jacks are not part of this.** `PJ-376` and `PJ-603` are right-angle, barrel
parallel to the board, exiting the **top edge through the enclosure wall** — see
`hardware/kicad/README.md` and the counterbore TODO in §11. Their mounting is a
separate problem with its own open question (whether a nut fits in the
board-to-wall gap at all, above).

What actually passes through the faceplate:

| family | qty | load it takes |
|---|---|---|
| `EC12E2430803` encoder | 8 | rotation **and** push — the most abused parts on the panel |
| Alpha `RD902F-40-15R1` pot, dual-gang (in the `RK09L1240A12` footprint) | 6 | rotation |
| `EC11L1525G01` encoder + push | 1 | rotation and push |
| DPDT toggle | 2 | flick |
| UI buttons | 4 (going to 6) | push only |
| OLED | 1 | none |

These do not share a shoulder height. The panel physically rests on whichever
shoulders are **tallest**, and every nut done up on a shorter part then tries to
close a gap that exists: the faceplate bows, or the tall parts get levered
against their joints, or the short bushing has no thread through the panel for
the nut to catch.

**So: nut one family only. The rest locate the panel and stop it sliding, and
carry no load.** Normal in DIY builds.

**The datum should be the EC12 encoders.** They are both the most numerous (8)
and the most mechanically abused — an encoder takes torque *and* an axial shove,
and an unclamped part transfers all of that into its solder joints. The pots take
torque only, the toggles and buttons almost nothing, and the OLED nothing at all.
Being most numerous is a tiebreak, not the reason.

### Panel part heights — RESOLVED from the ALPS drawings, 2026-09-06

Body height means PCB seating plane to **mounting surface** (the shoulder the
panel rests on).

| part | body | bushing | thread | cross-check |
|---|---|---|---|---|
| Alpha `RD902F-40-15R1` pot | **10mm** ±0.5 | 5mm | M7 x 0.75 | Alpha drawing `RD902F-40-(L)R1-XXX-00D70`: body 10, thread 5.0, L 15, Ø6.35; agrees with Tayda's "10mm+5mm" |
| `EC12E2430803` encoder | **5.5mm** | 7mm | M9 x 0.75 | "With bushing" style, confirms the §11 rejection of `C470602` |
| `EC11L1525G01` | not read | — | — | 13.1mm square body, 11mm size — will not exceed the pot |

**The pots are the datum, not the encoders.** They stand 4.5mm proud of the
EC12s, so the faceplate underside sits **10mm** above the main PCB and 11.6mm to
its outer face.

**Pot swap, 2026-09-22.** This table used to carry the ALPS `RK09L1240A12`
(10mm body, 7mm M9 bushing, 20mm flatted shaft). That part is 10k and the
design needs 100k, so the pots are now hand-fit Alpha `RD902F` duals — see
`review-packet.md`, open defect 2. Same 10mm body, so the datum and every
height below are unchanged. What did change, for whoever lays out the
faceplate PCB:

- **Pot holes are 7.5mm, not 9.5mm.** M7 x 0.75 bushing.
- **Drill them 0.17mm toward the top (jack) edge of the panel coordinate.**
  The shafts really sit there: `place.py` carried a 0.17mm error in the
  shaft offset, and moving the six pots to fix it broke 21 clearances. All
  six are off by the same amount in the same direction, so drilling at the true
  shaft puts every hole dead on. The encoders are unaffected.
- **3.4mm of thread above the panel** (bushing tip at 15mm, outer face at
  11.6mm), down from 5.4mm on the ALPS. Enough for the supplied nut (1.8mm per Alpha's drawing) and
  washer. There's no room for a thicker panel, a spacer or a lock washer.
- **Knobs take a 6.35mm (1/4") round shaft**, set-screw type, not 6mm
  D-shaft. 13.4mm of shaft stands above the panel. Thonk sells a D-shaft
  RD902F, but not in B100K.

### Consequence 1: the encoder nuts cannot bite

EC12 shoulder at 5.5mm + 7mm bushing = tip at **12.5mm**. The faceplate occupies
10 to 11.6mm, so the bushing clears the panel by **0.9mm** — nowhere near enough
thread for an M9 nut.

This is consistent with the datum decision (nut one family, locate the rest) and
it does **not** re-open the §11 side-load worry: the bushing still passes through
the panel hole, so lateral support is intact. Only axial clamping is lost. But it
should be explicit that **no encoder will ever be nutted on this build.**

### Consequence 2: the display sits 7.4mm behind the panel — socket it

DS1 is 4.2mm tall, so with a 10mm gap the display face is **7.4mm behind the
faceplate's outer surface**. For a 55.01 x 27.49mm active area that is a deep
well: at a 45 degree viewing angle it shadows about 7.4mm, roughly a quarter of
the display height.

**This reverses the earlier "do not socket the OLED" note.** That was written
assuming a 5.5mm gap, where a header would have crushed it. At 10mm there is
5.8mm of clearance, and putting the module on a ~2.5mm header *reduces* the
recess to 4.9mm and makes it serviceable. Chamfering the window edges is worth
doing either way.

### Consequence 3: six UI buttons replace four Cherry MX — DONE 2026-09-06

PCB top to faceplate top is 10 + 1.6 = **11.6mm**, so the switch has to be taller
than that before it is a button at all.

**Corrected 2026-09-08.** This paragraph used to end "use the 16mm height", from a
family list of 4.3 / 5.6 / 7.5 / 8.6 / 9.5 / 12 / 16mm. That list was wrong and so
was the conclusion — see §11. There is no 16mm TC-1212 at LCSC (it stops at
12.0H), and 12.0mm stands 0.4mm proud, which is not a button.

**Settled: `TS1103S-12X12X14DIP`, LCSC C54573007.** 14.0mm → **2.4mm proud**, with
a ∅6.2 round plunger through a 6.6mm panel hole. **No cap** — the plunger is the
button face, and the cap only ever existed to bridge a gap a 7.3mm switch could
not reach. Same 12×12 body and the same 4 × ∅1.2 at 12.5 × 5.0 pattern, so the
footprint and placement did not move.

**`SW4`-`SW9`, 12x12 through-hole tactile, 2 wide x 3 tall.** Six MX will not fit
the panel area; six tactiles do, because the panel hole only has to clear the
**4mm stem** — the cap snaps on from the front and sits on the panel surface, so
it can be wider than its own hole.

| | |
|---|---|
| Columns | 15.50mm — the pads splay to 14.7mm, which is the hard floor; 19.05 until 2026-09-06 |
| Rows | 12.7mm, tightened from 19.05 |
| Cluster | 22.1 x 32.0mm to the holes; the 12.0mm bodies behind it span 27.5 x 37.4mm |
| ENC0 | moved to y 73.453 on 2026-09-08 when the caps went away and the column re-centred on a 6.6mm hole instead of a 12mm cap |
| GPIO | `BTN5`/`BTN6` onto U4's spare GPA0/GPA1; 7 pins still free |
| Land pattern | `KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5`, 14.70 x 12.00mm, **identical at every height in the family** |

### CLOSED 2026-09-08: `TS1103S-12X12X14DIP`, LCSC **C54573007**

The old note here said to swap `C2845239` for "the 16mm variant" and that *"not the
panel hole"* would change. **Both halves were wrong.**

- **There is no 16mm TC-1212 at LCSC.** That family stops at 12.0H
  (`TC-1212DR-12.0H-250`, C17702632). The faceplate outer face is at 11.6mm, so
  even the tallest one would have stood **0.4mm** proud — not a button.
- **The panel hole was wrong too.** It was 4.5mm, sized for a "4mm stem". The
  HCTL part's stem is **3.8mm SQUARE**, whose diagonal is **5.37mm** — it would
  never have passed, at any height.

`TS1103S-12X12X14DIP` (CAX) fixes both. **14.0mm tall → 2.4mm proud** of the panel,
and a **∅6.2 round plunger** through a hole now widened to **6.6mm**. Its PCB
pattern is `4 x ∅1.2 at 12.5 x 5.0`, which is what
`KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5` already is — so the footprint, the netlist and
the button placement really are unchanged. The series runs 4.3mm to 20mm if the
stack ever moves.

**The snap-on cap is gone.** It only existed because a 7.3mm switch could not reach
the panel; the plunger is the button face now. That also retires the 0.7mm
cap-to-cap gap the 12.7mm rows used to imply — the 0.7mm that remains is between
the 12.0mm switch *bodies*, behind the panel, and `generate-faceplate.py` now
checks it along with the proud height and the plunger/hole fit.

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

### RESOLVED: J1 mirroring

**Checked on the hardware 2026-09-01 and it is fine.** J1 was flagged because its
local pad coordinates were stored identical to the library while J7's were stored
with local Y negated, which looked like it had been relabelled to B.Cu rather
than genuinely flipped. That reading was wrong. No change needed.

Keeping the note because the *check* is still worth running on any back-side
footprint whose layer was changed by editing the file rather than by KiCad: select
it in Pcbnew and press F twice. If the stored coordinates change, it was wrong.

