# Main PCB

Carries the Daisy Patch SM, microSD socket, SSD1309 OLED, rotary encoder, and the stereo
Buchla-style low pass gate.

## Contents (expected)

```
vuulgaris-main.kicad_pro / .kicad_sch / .kicad_pcb
lpg/          stereo LPG subsheet, redrawn from Bergman's stripboard layout
```

## Pin allocation is resolved

Build against **[../../docs/pin-allocation.md](../../docs/pin-allocation.md)**. It is settled
and there is **zero spare bidirectional GPIO**, so any addition means a removal.

Three things there are easy to miss:

- **BSL RST and TEST are on B5/B6 (gate outs), each through a 5V to 3.3V divider.** Gate outs
  are 0-5V; MSP430 I/O absolute max is 3.6V. Four resistors total.
- **Encoder push is on B9 (gate in)**, not a bidirectional GPIO.
- **OLED RST is an RC/pullup, not a GPIO.** The budget does not close otherwise.
- **OLED MOSI is on A9 (PB15), not D9.** PB15 is a supported SPI2_MOSI alternate. This is what
  frees D9 and D8 for pots 11-12.
- **No USB jack on the panel.** A8/A9 are spent on IO. DFU uses the module's onboard Micro USB.

## Analog section

Stereo Buchla 292-style LPG per
[ADR 0007](../../docs/decisions/0007-buchla-lpg-over-serge-vcfq.md).

- **Four vactrols.** Two per channel: one VCA path, one filter path.
- **Match them.** On-resistance *and* decay, across L and R. Either measure and bin, or use
  VTL5C3/2 duals so each stereo pair comes from one package.
- **Solve vactrol bleed deliberately** in the schematic. Bergman's design may not address
  it; Prism Circuits' 4U version adds circuitry specifically for this. Do not rediscover it
  on assembled hardware.
- **Redraw from the stripboard layout**, do not copy it. Also the right move IP-wise.
- Driven from CV_OUT_1 and CV_OUT_2. 12-bit, and they can run at audio rate if written
  per-sample in the audio callback, though the vactrol's own lag dominates anyway.

## Switching

Two switches, not one:

| Switch | Function | Type |
|---|---|---|
| SW1 | Mode: **stereo VCF or stereo VCA** | **DPDT**, one pole per stereo side |
| SW2 | Source: resample vs external input | DPDT, **break-before-make** |

The mode switch dropped from three positions to two, so it is a commodity DPDT rather than an
uncommon 4P3T. That removed a live risk to panel layout.

SW2 detail: pole A carries L (throws resample-L / ext-L), pole B carries R.
Break-before-make is correct, since a shorting switch would briefly tie two low-impedance
outputs together. Add a **100k-1M resistor to ground on the switch common** so the node does
not float during the open moment, plus **DC blocking caps on both sources**.

Standard 6-pin DPDT: middle pin of each row is the common (pins 2 and 5; throws 1/3 and 4/6).
**Lever direction is inverted relative to the pin it selects.** Verify the pinout with a
multimeter on the actual part and **silkscreen the labels after bench-confirming, not before.**

## Power

- **Regulate 3V3 on this board and filter locally at the MSP430.** Do not share a rail with
  audio circuitry; cap touch does not love switching noise.
- LPG runs on +/-12V, so there is a regulator in the chain already.
- Patch SM: no bypass caps necessary on the power header. 3V3 out is 500mA max (firmware
  dependent), 5V out is 800mA max.

## Display

SSD1309 is a **bare panel with an FPC tail**, not a breakout board. This board needs an
**FPC connector**, not a 2.54mm header. Check pin count and pitch against the panel
datasheet. Panels usually need external charge-pump caps and an IREF resistor.

## Checklist

- [ ] No CD4051 mux footprint (ADR 0009: it would spend 3 GPIO to save 2)
- [ ] SD wired 1-bit: D5 (D0), D6 (CLK), D7 (CMD) only
- [ ] 5V to 3.3V dividers fitted on BSL RST (B5) and TEST (B6)
- [ ] Test points on B5/B6 at the MSP430 side of the dividers, for scoping BSL edges
- [ ] OLED RST RC/pullup fitted, no GPIO
- [ ] Pots 1-8 wired to 5V (A6); pots 9-10 wired to 3V3 (A10)
- [ ] Both UART and I2C routed to the faceplate connector on B7/B8, one populated
- [ ] A2/A3 are POTS, not the MSP430 link
- [ ] IRQ line from MSP430 on **A8**
- [ ] OLED MOSI on **A9**, not D9
- [ ] All 12 pot footprints routed; 10 populated, 2 stuff options
- [ ] No USB connector on the panel
- [ ] FPC connector matches the actual panel, verified against its datasheet
- [ ] Encoder is NOT on B9/B10 (input only)
- [ ] ADC_9-12 pots wired to 3V3 (A10), CV_1-8 pots wired to 5V (A6)
