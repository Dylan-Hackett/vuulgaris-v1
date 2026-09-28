# 0012 - No LEDs on the faceplate, and no 5V on the faceplate cable

**Status:** Accepted
**Date:** 2026-09-27

## Decision

The faceplate PCB carries **no indicator LEDs**. `J12` stays as built: `MSP_TEST`, `MSP_RST`,
the two UART lines, `P3V3_MSP430` and five grounds. **No 5V pin is added**, so the main board
orders as it is.

## What was on the table

Discussed 2026-09-23 (`hardware/faceplate/README.md` §7): one LED per zone, 16 in all, lit
beside the zones through small windows, driven from the MSP430 through two 74HC595s or a
TLC59116, never PWM'd during a touch scan. Red, amber or yellow could run from the existing
3.3V pin at about 5mA each (80mA all on). White, blue or RGB needed a 5V pin, and `J12` has no
free position, so that meant a larger header and a reroute on a finished board.

## Why not

- **The faceplate's job is measuring tiny capacitance changes.** Sixteen switched LED lines
  would fan out alongside the electrodes, and windows beside the zones put LED copper into
  the 8mm inter-pad gaps, which are the one spacing nobody has measured yet (Q17). TI's layout
  guidance is to keep digital lines away from the electrodes and exit the opposite edge.
- **The current would come off the MSP430's own rail.** `U6` exists so the touch MCU does not
  share a supply with anything noisy; 80mA of LED switching on it undoes that.
- **Q1 is still open.** If bare copper misbehaves, the faceplate is the board that gets
  respun. Everything added to it is added risk with no sensing benefit.
- **The OLED already shows position.**
- **5V would have held the main board**, which is DRC-clean with a fab package ready.

## What would overturn this

A second faceplate revision after Q1 and Q17 are answered on real hardware, with a measured
noise margin that shows room for switched loads near the pads. At that point warm-colour LEDs
on 3.3V are still possible without touching the main board; anything needing 5V is not.
