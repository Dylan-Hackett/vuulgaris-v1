# 03: Daisy Patch SM (U1)

Sources: `Electrosmith-Patch-SM-v1.0.5.pdf`, read directly: p4 pinout figure
(rendered at 400 dpi, header silkscreen read off the module photo), p5 Table 1,
p6 Table 2, p7 Table 3, p9-p13 typical applications, p14 technical drawing, p15
landing pattern. Then `datasheets/extracts/patch-sm-v1.0.5-pinout.md`,
`docs/pin-allocation.md`, ADRs 0005, 0008, 0009, open-questions Q8/Q10/Q14/Q15,
`fw-daisy/src/main.cpp` and `fw-daisy/README.md`. The board was read from
`vuulgaris.kicad_pcb`; the silkscreen claim below was confirmed in
`fab/vuulgaris-F_Silkscreen.gbr`.

Not available: Electrosmith's Patch SM schematic (`ES_Daisy_Patch_SM_Schematic.pdf`,
cited by ADR 0009 and Q14, not in the repo) and libDaisy / DaisyBootloader
source (the `fw-daisy` submodules are empty in this checkout).

## Header orientation and row order

The p15 landing pattern gives geometry only, no pin numbers. Numbers come from
the p4 photo, whose module silkscreen prints, beside each header, a two-line key:
`10 9 8 7 6` over `1 2 3 4 5`. Read against the photo: on A and D (vertical
blocks) pin 1 is top of the left column with 10 beside it; on B and C
(horizontal blocks) 1 is the left end of the lower row with 10 above it. Table 2
and the p4 tables agree.

Which face meets the carrier: p14's side view has the male pins rising from the
same face as the header bodies and the large ICs, with the Micro USB on the other
face. The photo shows header bodies, so it is the pin face. The module is
therefore flipped onto the carrier, and the carrier's top view is the photo
rotated 90 degrees and mirrored, which is the transpose of the photo. Applied to
every header:

| header | carrier top view, derived | our footprint (local, F.Cu) |
|---|---|---|
| A | top-left, horizontal; upper row A1..A5 left to right, A10..A6 below | A1 (-32.08,-15.27) to A5 (-21.92,-15.27); A10 below A1 |
| D | bottom-left, horizontal; upper row D1..D5, D10..D6 below | D1 (-32.08, 12.73); D10 (-32.08, 15.27) |
| B | top-right, vertical; outer column B1 (top)..B5, inner B10..B6 | B1 (29.27,-18.08), B5 (29.27,-7.92), B10 (26.73,-18.08) |
| C | bottom-right, vertical; outer C1 (top)..C5, inner C10..C6 | C1 (29.27, 7.92), C5 (29.27, 18.08), C10 (26.73, 7.92) |

Geometry against p15, both figures: left-header centres 7 from the left edge
and 28 apart, 6 from top and bottom edges; right-header centres 26 apart and 7
from the bottom; first left column 1.92 from the edge; 58.81 from it to the
right header's inner column; 7.27 from that column to the right edge; holes
1.016. Every dimension matches the footprint to 0.01 mm.

Independent check: the library also carries `KAD_ES_DAISY_PATCH_SM_V1`, a
separately authored footprint whose comments say it corrects the Electrosmith
Eagle part for top-side mounting. Ours is exactly that footprint rotated
180 degrees (A1 (-32.08,-15.27) against KAD (32.09, 15.26), and so on for all
16 corner pins). **Header orientation: CLEAN.**

### Silkscreen header letters: DEFECT

The library footprint `DAISY_PATCH_SM.kicad_mod` puts `A` at (-15.748, -13.462),
beside the A pads. **On the board, U1's four letters have their local y
negated**: `A` (-15.748, 13.462), `D` (-16.002, -13.97), `B` (20.828, 13.462),
`C` (20.828, -13.716), while the pads are unchanged. Every letter sits beside
the wrong header: A by D, D by A, B by C, C by B. Confirmed in the fabricated
artwork: `vuulgaris-F_Silkscreen.gbr` draws an `A` glyph at board
(350.4, 115.6), just past the end of the D header's column (D pads at
x 348.6-351.1, y 99.2-109.4). Introduced in `4467882` (2026-08-27).

Consequence: the module still only fits one way (two horizontal and two
vertical 2x5 blocks), so assembly is safe. Bring-up is not: probing what the
board calls A1 for -12 V lands on D1, `OLED_CS`. Fix: restore the four
`fp_text user` positions to the library's, in the board file.

## Pin table

Pin names and classes from Table 2; operating range from Table 3; absolute
maxima from Table 1 (GPIO -0.3 to 6 V, "to sustain a voltage higher than 4V the
internal pull-up/pull-down resistors must be disabled"; audio, gate and CV
inputs "Negative Power In" to "Positive Power In"; gate and CV outputs 0-5 V).
"Worst on pin" is the most extreme voltage our circuit can put there.

| ref.pin | net | source says | ours / worst on pin | verdict |
|---|---|---|---|---|
| U1.A1 | NEG12V | -12V input, abs -6 to -17 | -12.3 V | CLEAN |
| U1.A2 | MSP430_TXD | ADC_9 / PA1, GPIO, alt UART4_RX | driven by the MSP430's TX at its DVCC, 3.4 V max (U6) | CLEAN: TX into RX |
| U1.A3 | MSP430_RXD | ADC_10 / PA0, alt UART4_TX | drives the MSP430's RX | CLEAN |
| U1.A4, A7 | GND | GND | GND | CLEAN |
| U1.A5 | POS12V | 12V input, 6 to 17 | 12.3 V | CLEAN |
| U1.A6 | P5V | 5V output, 800 mA max | FB1/FB2 to U5/U6, about 180 mA estimated | CLEAN |
| U1.A8 | (open) | USB_DM / PB14 | open | CLEAN |
| U1.A9 | OLED_RES | USB_DP / PB15, GPIO 0-3V3 | drives DS1.5 | CLEAN (see Q10/Q15 below) |
| U1.A10 | P3V3_DAISY | 3V3 output, 500 mA max, "firmware dependent" | U3/U4, J1, R20/R21, R506-R508; about 110 mA with an SD card writing (card figure not in repo) | CLEAN |
| U1.B1, B2 | AUDIO_OUT_R/L | DC-coupled out, 100R | 10k (R301/R401) into the LPG mix + 100k (R310/R410) to GND | CLEAN |
| U1.B3, B4 | AUDIO_IN_R/L | AC-coupled in, 100k; abs = the power rails | SW2 common: EXT amp (OPA1688, rail to rail, +-11.8 V) via C501/C502, or BBD out via C503/C504; R501/R502 1M bias | CLEAN: inside +-12 V |
| U1.B5 | GATE_OUT_1 | output only, 0-5 V | R504 1k to J3 | CLEAN |
| U1.B6 | GATE_OUT_2 | output only | R117/R217 100k to the 4046 inhibits, clamped by D104/D106 | CLEAN |
| U1.B7, B8 | I2C_SCL/SDA | I2C1 PB8/PB9, GPIO 0-3V3, no module pullup marked | R20/R21 2.2k to P3V3_DAISY, the only pullups on the bus | CLEAN |
| U1.B9 | (open) | GATE_IN_2, input only | open | CLEAN |
| U1.B10 | GATE_IN | GATE_IN_1, input only, 100k, abs = rails | J5 tip direct, whatever a patch cable brings | CLEAN for +-12 V sources; no series protection beyond the module's |
| U1.C1 | TIME_CV | CV_OUT_2, output only, 0-5 V | R116/R216 100k to the 4046 VCO inputs (clamped) | CLEAN |
| U1.C2-C8 | (open) | CV_1..CV_7, input only | open | CLEAN |
| U1.C9 | CV_IN_JACK | CV_8, input only, 100k, typ +-5 V, abs = rails | J4 tip direct | CLEAN, same note as B10 |
| U1.C10 | LPG_ENV | CV_OUT_1, output only, 0-5 V, 100R | R323/R423 100k to virtual grounds, RV3 both gangs (100k each, across +V and -V: 0.1 mA each at 5 V), R503 1k to J2 | CLEAN: about 0.3 mA internal |
| U1.D1 | OLED_CS | SPI2_CS / PB4 | DS1.7 | CLEAN |
| U1.D2 | OLED_DC | SDMMC1_D3 / PC11, 47k module pullup | DS1.6 | CLEAN (needs 1-bit SD, below) |
| U1.D3, D4 | (open) | SDMMC1_D2, D1 | open | CLEAN |
| U1.D5 | SD_D0 | SDMMC1_D0 / PC8 | J1.7, R507 47k pullup | CLEAN |
| U1.D6 | SD_CLK | SDMMC1_CLK / PC12, 47k module pullup | J1.5 | CLEAN |
| U1.D7 | SD_CMD | SDMMC1_CMD / PD2, 47k module pullup | J1.3, R506 47k (23.5k with the module's) | CLEAN |
| U1.D8 | (open) | ADC_12 / PC2, alt SPI2_MISO | open | CLEAN |
| U1.D9 | OLED_MOSI | ADC_11 / PC3, alt SPI2_MOSI | DS1.4 | CLEAN |
| U1.D10 | OLED_SCK | SPI2_SCK / PD3 | DS1.3 | CLEAN |

No GPIO on this board sees more than 3.4 V: everything that drives one (MSP430,
MCP23017, SD card) runs from a 3.3 V rail, so the 4 V pull-up caveat never
applies. No CV or ADC input is fed from a +-12 V op-amp stage; the only analog
inputs in use are C9 and B10, straight from jacks, and B3/B4, which are rated to
the rails.

## Peripherals exist on the pins used

| function | pins | Table 2 | verdict |
|---|---|---|---|
| SPI2 for the OLED | D10 SCK (PD3), D9 MOSI (PC3, alt SPI2_MOSI), D1 CS (PB4) | all three named SPI2 | CLEAN |
| SDMMC1, 1-bit | D6 CLK (PC12), D7 CMD (PD2), D5 D0 (PC8) | named SDMMC1 | CLEAN |
| UART4 to the faceplate | A2 RX (PA1), A3 TX (PA0) | alt UART4_RX/TX | CLEAN |
| I2C1 to U3/U4 | B7 SCL (PB8), B8 SDA (PB9) | I2C1 | CLEAN |
| CV out x2 | C10, C1 | the only two output-capable CV pins | CLEAN |

**ADR 0009's ADC count no longer describes the board.** It allocates twelve
ADC pots (CV_1-CV_8 plus A2, A3, D8, D9), puts OLED MOSI on A9, says "No CV or
gate jacks into the Daisy", and puts BSL RST/TEST on B5/B6 and the encoder push
on B9. The board has one ADC input in use (C9), MOSI on D9, RES on A9, four
jacks, encoders on the MCP23017s, and B5/B6 as a gate out and the BBD inhibit.
`pin-allocation.md` (current as of 2026-08-09) supersedes it, and ADR 0005's
2026-09-06 note supersedes its BSL rows, but ADR 0009 itself still reads
"Accepted" with no superseded marker. Doc defect, not a board defect.

Datasheet internal inconsistency, for the record: p4's figure labels D6
`SDMMC_CLK` with `UART_RX` and D7 `SDMMC_CMD` with `UART_TX`; Table 2 has
D6 alt `UART5_TX*` and D7 alt `UART5_RX*`. Not used here.

## Boot and special pins

- **QSPI, BOOT, SWD, USB device:** none is on the A-D headers (Table 2). The
  module's debug and Micro USB are on the module.
- **USB_HS on A8/A9 (Q14):** A9 carries `OLED_RES`. Q14's own record (from the
  Rev3 schematic, not in repo) says the DaisyBootloader by default
  "initialises USB host on the external port". A USB host holds D+/D- low
  through its pull-downs, so during the bootloader `OLED_RES` is probably held
  low and the display stays dark until the application drives A9. That fits
  Q10 ("OLED dead under bootloader") and is harmless. **QUESTION**, closable
  only with the module schematic or a scope.
- **Q15** is stale: it asks whether A9 can carry MOSI and says it blocks
  "pots 11-12". A9 carries RES, a static level; there are no pots. Whatever
  ESD part the module has on PB15 is irrelevant to a reset line. Doc defect.
- **Q8** is resolved and still true (D8 free), but its text says D8 "carries
  pot 12"; it carries nothing. Doc defect.
- **SDMMC width:** D2 (`SDMMC1_D3`) is spent on `OLED_DC`. Any code that brings
  SDMMC1 up 4-bit will drive PC11 and fight the display's DC line (no damage,
  `DC` is an input, but the display corrupts and the card fails). Per
  `fw-daisy/README.md`, libDaisy's `SdmmcHandler::Config::Defaults()` is
  4-bit, and the DaisyBootloader overrides it to 1-bit. **Firmware requirement:
  set `BusWidth::BITS_1` explicitly.** README's "Route all 6 pins anyway and
  pick the width in software" is stale against ADR 0009 and the board.

## Firmware cross-check

`fw-daisy/src/main.cpp` is a skeleton and names no pins in code. Its comments do
make three hardware claims, and all three disagree with the board:

| firmware says | board | verdict |
|---|---|---|
| "CV outs drive the LPG vactrols" (both `CV_OUT_1` and `CV_OUT_2`) | `CV_OUT_1` (C10) is `LPG_ENV` for both channels; `CV_OUT_2` (C1) is `TIME_CV`, the BBD delay time | DEFECT (comment) |
| touch link is "UART (A2/A3) or I2C (B7/B8) ... plus an IRQ line signalling data-ready" | UART only; `J12` carries TEST, RST, RX, TX, 3V3 and grounds, **no IRQ** | DEFECT (comment) |
| "BSL flashing path over RST + TEST" | TEST is not driven from the main board (ADR 0005, 2026-09-06); RST is on U4 GPB3 | DEFECT (comment) |

`fw-daisy/README.md` "Do not use B9/B10 for the encoder" agrees with the board
(the encoders are on U3/U4). Nothing the firmware drives is wired elsewhere,
because the firmware drives nothing yet.

## Verdicts

| item | verdict |
|---|---|
| all 40 pins, name and net | CLEAN |
| header placement and in-header order, against p4 and p15 | CLEAN |
| U1 silkscreen letters | **DEFECT** |
| peripherals on their pins | CLEAN |
| worst-case voltage on every pin | CLEAN |
| extract `patch-sm-v1.0.5-pinout.md` vs Table 2 | CLEAN: every row matches |
| ADR 0009, Q8, Q15, fw README SD note | DEFECT (doc, stale) |
| fw `main.cpp` comments | DEFECT (comment, 3) |
| OLED_RES under the bootloader | QUESTION |
| 4-bit SDMMC would fight OLED_DC | firmware requirement |

## Defects, ranked

1. **Degrades bring-up: U1 silkscreen A/B/C/D letters are on the wrong
   headers** (A by D, B by C). Board file, U1's four `fp_text user` positions.
2. **Firmware comments (3)** that would mislead the first person to write the
   touch link and CV code. `fw-daisy/src/main.cpp`.
3. **Doc, stale:** ADR 0009 needs a superseded marker pointing at
   `pin-allocation.md`; Q8 and Q15 describe pots that no longer exist;
   `fw-daisy/README.md`'s "route all 6 SD pins" line.
