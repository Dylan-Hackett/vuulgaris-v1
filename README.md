# Vuulgaris V1

A 4-channel sample-scrubbing instrument. Long capacitive copper pads on a PCB faceplate
represent the length of a waveform; dragging a finger along a pad scrubs through the sample.
Each track carries a swappable machine that is either a sampler or a synth, with Plaits as
the synth engine.

```
[ FACEPLATE PCB ]
  4x capacitive pads, ~216mm (length follows the inter-pad gap, Q17)
  MSP430FR2675TPTR (CapTIvate touch MCU) on the back side
        |
        |  UART (primary) or I2C (fallback), + IRQ, + BSL entry lines
        v
[ MAIN PCB ]
  Daisy Patch SM (STM32H750) - audio engine, sample playback, UI
  microSD socket
  2.42" SSD1309 OLED (SPI)
  Rotary encoder
  Stereo Buchla-style low pass gate (analog)
```

## Layout

| Folder | Contents |
|---|---|
| [`docs/`](docs/) | `design-state.md` (source of truth), ADRs, open questions, pin allocation, panel budget |
| [`mockups/`](mockups/) | Parametric comb pad generator, Salamis faceplate reference + dimensioned |
| [`datasheets/`](datasheets/) | Manifest + fetch script. PDFs are not committed. |
| [`hardware/`](hardware/) | Faceplate and main PCB, gerbers, BOM spreadsheet |
| [`fw-daisy/`](fw-daisy/) | Daisy Patch SM firmware. libDaisy + DaisySP as submodules. |
| [`fw-touch/`](fw-touch/) | MSP430FR2675 firmware. CCS + CapTIvate Design Center. |

## Start here

1. **[docs/design-state.md](docs/design-state.md)** is authoritative. Everything else is
   derived from it.
2. **[docs/notes/next-steps.md](docs/notes/next-steps.md)** step 0 is the thing to do first,
   and it is deliberately cheap: one 2-layer board with **two pads in final tooth geometry**,
   roughly $50 and 2 weeks. It answers whether a moving finger reads and repeats cleanly, and
   the second pad settles the inter-pad gap, which sets the size of the whole instrument.
3. **[docs/pin-allocation.md](docs/pin-allocation.md)** is resolved and safe to lay out
   against. Zero spare bidirectional GPIO, so any addition means a removal.
4. **[docs/panel-budget.md](docs/panel-budget.md)** is **not** settled, and it hinges on one
   measurement. The Salamis composition locks `pad length = 12 x pad pitch`, so the inter-pad
   gap ([Q17](docs/notes/open-questions.md)) sets the size of the whole instrument: a 6mm gap
   gives a 298 x 154mm panel with 216mm pads, a 10mm gap gives 365 x 189mm with 264mm pads.
5. **[docs/notes/open-questions.md](docs/notes/open-questions.md)** lists what is still
   unverified. Only one is a real design risk: **Q1**, whether a moving finger on bare copper
   reads and repeats cleanly. **Q10, Q13, Q15, Q18** are bench or datasheet checks. **Q17**
   (inter-pad gap) sets the instrument size. **Q7** is a cash decision.

## Setup

```bash
# Firmware submodules
git -C fw-daisy submodule update --init --recursive
cd fw-daisy && make libs && make

# Datasheets (not committed)
cd datasheets && ./fetch-datasheets.sh
```

## The three facts that shape everything else

**The MCU is on the faceplate, not the main board.** TI's design guide says keep
MCU-to-electrode traces as short as possible and explicitly warns against routing capacitive
sensing lines through board-to-board connectors or cables. That is what forces the two-board
split, and only ~8-10 digital pins cross between them.

**Accuracy is not the requirement. Monotonicity and continuity are.** You scrub by listening
and adjusting, so the loop closes through your ears and absolute position error is inaudible.
A bent curve is a lookup table. What cannot be fixed downstream is a **momentary reversal**
(sample stutters backward) or a **dropout** (click). Scan rate and jitter at rest are both
settled, see [Q1](docs/notes/open-questions.md). This is where the Trautonium pivot changed
the requirements: there, position was pitch and a 2% error was a wrong note.

**Electrode order is generated first, then laid out.** `RX0->E00, RX1->E01, RX2->E02,
RX3->E03`, produced in Design Center **before** the PCB. A swapped pair gives garbage
interpolation on a board that passes every electrical check.

**Every pot past the eighth costs a bidirectional GPIO.** CV_1-CV_8 are input-only pins that
can do nothing else, so the first 8 are free. Pots 9-12, the envelope attack and release for
each stereo side, take A2, A3, D8 and D9, and that consumes all 16 bidirectional GPIO exactly.
A 13th is impossible.

**Patch SM has two USB ports, and only one of them is on the header.** DFU flashing and USB
MIDI run on the module's own onboard Micro USB (PA11/PA12). **A8/A9 are a separate USB host
port**, spent here on IO. The cost is that USB access means unscrewing the module from the
rack; firmware ships via SD card instead.

## Decisions already made

| # | Decision |
|---|---|
| [0001](docs/decisions/0001-pivot-to-capacitive-scrubbing.md) | Pivot from Trautonium analog to capacitive sample-scrubbing |
| [0002](docs/decisions/0002-msp430fr2675-for-touch.md) | MSP430FR2675 (CapTIvate) for touch sensing |
| [0003](docs/decisions/0003-comb-pad-rx0-wraparound.md) | Comb-tooth pads with RX0 wraparound |
| [0004](docs/decisions/0004-no-overlay-exposed-copper.md) | Exposed copper, no overlay, ENIG |
| [0005](docs/decisions/0005-bsl-over-daisy-uart.md) | Daisy flashes the MSP430 over BSL |
| [0006](docs/decisions/0006-ssd1309-oled.md) | 2.42" SSD1309 over SPI |
| [0007](docs/decisions/0007-buchla-lpg-over-serge-vcfq.md) | Buchla-style LPG, not Serge VCFQ |
| [0008](docs/decisions/0008-boot-sram-not-qspi.md) | BOOT_SRAM, QSPI reserved for samples |
| [0009](docs/decisions/0009-io-plan-12-adc.md) | IO plan: 12 ADC, no mux, 1-bit SD, no panel USB |

## Cost

**$162.40 at qty 1** per [the BOM](hardware/bom/vuulgaris-v1-bom.xlsx), of which **$48.76 is
confirmed** against real listings and the rest is estimated. Inside the $125-200 range in
design-state section 10.

**The enclosure is not in that number.** The prior design was CNC walnut. It is cost lever
number 3 and currently unbounded.

Stock warnings that matter: **MSP430FR2675 has 10 units at LCSC**, and the **SSD1309 has 27**.
Both are prototype quantities.
