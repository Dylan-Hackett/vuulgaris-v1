# Decisions (ADRs)

One file per decision that has already been made and would be expensive to revisit.
Format is deliberately short: what was decided, what it rules out, why, and what would
overturn it.

Numbering is chronological, not priority. A decision stays in this folder even when
superseded: mark it `Status: superseded by NNNN` rather than deleting it, because the
reasoning is usually the useful part.

| # | Decision | Status |
|---|---|---|
| [0001](0001-pivot-to-capacitive-scrubbing.md) | Pivot from Trautonium analog to capacitive sample-scrubbing | Accepted |
| [0002](0002-msp430fr2675-for-touch.md) | MSP430FR2675 (CapTIvate) for touch sensing | Accepted |
| [0003](0003-comb-pad-rx0-wraparound.md) | Comb-tooth pads with RX0 wraparound, 5 segments / 4 zones | Accepted |
| [0004](0004-no-overlay-exposed-copper.md) | Exposed copper, no overlay, ENIG finish | Accepted |
| [0005](0005-bsl-over-daisy-uart.md) | Daisy flashes the MSP430 over BSL, no per-unit programmer | Accepted |
| [0006](0006-ssd1309-oled.md) | 2.42" SSD1309 over SPI for the display | Accepted |
| [0007](0007-buchla-lpg-over-serge-vcfq.md) | Buchla-style low pass gate, not Serge VCFQ | Accepted |
| [0008](0008-boot-sram-not-qspi.md) | Build APP_TYPE=BOOT_SRAM, reserve QSPI for samples | Accepted |
| [0009](0009-io-plan-12-adc.md) | IO plan: 12 ADC, no mux, 1-bit SD, no panel USB | Accepted |
