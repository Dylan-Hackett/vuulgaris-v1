# Datasheets

Canonical documents for Vuulgaris V1. PDFs are **not committed** (TI redistribution terms,
and they are large). Run `./fetch-datasheets.sh` on your own machine to populate this folder.

Text extracts of what could be pulled during scaffolding live in `extracts/`. They are
searchable but lose all tables, figures and pinout drawings. Treat them as a grep index,
never as the authority. Pull the real PDF before any number drives a layout decision.

## Required

| File | Doc # | Title | Why it is here |
|---|---|---|---|
| `TI-MSP430FR2675-datasheet.pdf` | SLASES4 | MSP430FR2675 mixed-signal MCU | **Pin function table for the PT/LQFP-48 package.** Settles the eUSCI_A vs eUSCI_B muxing question that blocks faceplate layout. |
| `SLAU550-MSP430-FRAM-BSL.pdf` | SLAU550 | MSP430 FRAM Devices Bootloader (BSL) User's Guide | BSL entry sequence, password rules, device table. Confirms FR2675 = BSL 00.09.36.B5, UART on eUSCI_A + I2C on eUSCI_B. |
| `SLAA891-OpenSCAD-CapTouch-Scripts.pdf` | SLAA891 | Automating Capacitive Touch Sensor Design using OpenSCAD | TI's validated slider pattern generator. Cross-check the comb pad generator against this before committing copper. |
| `Electrosmith-Patch-SM-v1.0.5.pdf` | v1.0.5 | Daisy Patch Submodule datasheet | Pin functions, electrical characteristics, typical application circuits. |

## Supporting

| File | Doc # | Title | Why it is here |
|---|---|---|---|
| `SLAA843-Sensitivity-SNR.pdf` | SLAA843 | Sensitivity, SNR, and Design Margin in Capacitive Touch | Retuning for the no-overlay case. TI's guidance assumes 1.5-4mm of plastic; this is the doc that tells you how to move off that. |
| `SLAA685-Code-Protection.pdf` | SLAA685 | MSP Code Protection Features | The brick-risk doc. Read section on JTAG lock + BSL disable before touching any security setting. |
| `SLAA842-CapTIvate-Selection.pdf` | SLAA842 | CapTIvate device selection | Source for "FR2675 has 4 parallel measurement blocks". |

## Web-only references

The CapTIvate Design Guide is HTML, not a PDF:
<https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/CapTIvate_Design_Center/latest/exports/docs/users_guide/html/CapTIvate_Technology_Guide_html/markdown/ch_design_guide.html>

Layout rules quoted in `docs/design-state.md` section 3 come from here.

## Open items these documents resolve

1. **eUSCI_A / eUSCI_B pin muxing on PT package** -> FR2675 datasheet, pin function table.
   Blocks: faceplate routing, whether 0R jumpers are needed. See `docs/notes/open-questions.md` Q2.
2. **BSL entry timing** -> SLAU550. Note the documented doc bug: page 18, I2C unlock example
   shows length field `0x33` where it should be `33` decimal.
3. **Slider pattern validation** -> SLAA891 OpenSCAD scripts, export DXF and diff against
   `mockups/comb-pad-generator.html` SVG output.
