# fw-touch

Firmware for the **MSP430FR2675TPTR** on the faceplate. Reads four capacitive scrub pads and
reports position to the Daisy over UART (or I2C).

## Toolchain

| Tool | Version | Note |
|---|---|---|
| Code Composer Studio | current | The IDE and compiler |
| **CapTIvate Design Center** | **1.83.00.08 (May 2020)** | Generates the sensor config. Stale, and its release notes say to re-create projects made in earlier versions. |
| **CAPTIVATE-PGMR** | hardware | **Required.** Not optional, see below. |

### The PGMR is not optional

The Design Center **cannot talk to an MSP-FET or a LaunchPad eZ-FET.** The PGMR carries a
separate MSP430F5528 running HID Bridge firmware that streams live sensor data to the PC as
a USB HID device. That live view is the entire point: jitter, scan time, linearity, trim.

There is **no FR2675 dev board.** TI's own evaluation recommendation is
**CAPTIVATE-FR2676 + CAPTIVATE-PGMR**, plus **CAPTIVATE-BSWP** which is listed as required
for self-cap designs and gives a reference slider baseline. FR2676 is the same silicon for
touch purposes, just 64KB/8KB against the FR2675's 32KB/6KB. The FR2676 board has a 48-pin
sensor panel connector for plugging in your own test pad.

**Migration note:** Design Center projects target a specific device. Regenerate for
**FR2675 (PT/LQFP-48)** when moving to your own board. CAP pin *naming* carries over;
physical pins do not.

## Layout

```
ccs/vuulgaris-touch/   CCS project
design-center/         .captivate project files
captivate/generated/   Design Center output, REGENERATED not hand-edited
tuning/                Measurement logs: scan time, jitter, linearity, trim values
docs/                  pin-assignment.md, bsl-protocol.md
```

## Order of operations, and it matters

1. **Generate the slider electrode assignment in Design Center FIRST.**
2. **Then lay out the PCB to match.**

`RX0->E00, RX1->E01, RX2->E02, RX3->E03`. Swapped pins produce garbage interpolation on a
board that passes every electrical check. See [docs/pin-assignment.md](docs/pin-assignment.md).

## Sensor configuration

Four sliders, four electrodes each, 5 segments / 4 interpolation zones with **RX0 appearing
at both ends** as a single net. Full geometry in
[ADR 0003](../docs/decisions/0003-comb-pad-rx0-wraparound.md).

**No overlay.** Direct finger-to-copper contact, which is outside TI's design assumptions
since all their tuning guidance assumes 1.5-4mm of plastic. Expect a **larger signal delta**
than the reference designs and **retune for lower conversion counts.** That is a gain, not a
problem: it buys margin on latency and filtering. See SLAA843.

### What to measure first

| Measurement | Where | Why |
|---|---|---|
| **Scan time across 4 sliders** | Design Center reports it directly | 4 blocks x 4 pins means each slider's elements scan in parallel, but the four sliders scan in **four sequential cycles**. Effective per-pad rate is 1/4 of a single-slider design. No published number exists for this config. |
| **Jitter at rest, in counts** | Design Center live view | Usable resolution is `configured_resolution / jitter_counts`. Set 1000 and measure N; the answer is 1000/N. **This is the number that decides whether scrubbing sounds like an instrument.** |
| **Linearity** | drag a finger, log position | Validates the ratio-encoded comb geometry. |
| **Lower_Trim / Upper_Trim** | touch each end, observe | A finger's centroid does not align with the slider endpoint, so most layouts cannot reach 0 and max. Plan for a few dead millimetres at each end. |

Log results in `tuning/`, dated, with the board revision noted.

### Noise immunity is a trade, not a free win

Enabling it turns on frequency hopping, aggregating four conversion frequencies. That
multiplies scan time **x4 on top of** the four sequential sliders. It is the first knob to
trade if latency is tight, weighed against sitting next to switching supplies and audio
circuitry.

## Do not touch the security settings

BSL code is in secure ROM and cannot be overwritten. Even with JTAG disabled, the BSL still
works. **The one permanent brick is deliberately disabling BSL *and* locking JTAG.**

**Rule: leave JTAG/SBW unlocked and BSL enabled.**

The 4 SBW test pads on the faceplate (TEST, RST, 3V3, GND) are the recovery path. A $12
MSP430 LaunchPad's eZ-FET flashes through them.

See [docs/bsl-protocol.md](docs/bsl-protocol.md) and
[ADR 0005](../docs/decisions/0005-bsl-over-daisy-uart.md).

## Bench stand-in

A SoftPot is a bad product part (needs pressure, +/-3% linearity, $9-27 each, finite cycle
life) and a fine **development** stand-in. Use one to settle firmware and scrubbing feel on
the Daisy side before cap-touch hardware exists.
