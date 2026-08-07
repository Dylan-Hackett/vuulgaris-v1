# Hardware

```
faceplate/   Faceplate PCB: 4x capacitive pads + MSP430FR2675 on the back
main/        Main PCB: Patch SM, microSD, OLED, encoder, stereo LPG
gerbers/     Fab outputs, one dated subfolder per order
bom/         vuulgaris-v1-bom.xlsx
```

## Two boards, and why

The MSP430 lives on the **faceplate**, not the main board. This is not a packaging
preference. TI's design guide says keep MCU-to-electrode traces as short as possible, and
explicitly warns against routing capacitive sensing lines through board-to-board connectors
or cables, which are significant noise receptors. Only ~8-10 digital pins cross between
boards. See [ADR 0002](../docs/decisions/0002-msp430fr2675-for-touch.md).

## Before you draw anything

1. **Generate the slider electrode assignment in CapTIvate Design Center first**, then lay
   out the PCB to match. `RX0->E00, RX1->E01, RX2->E02, RX3->E03`. Swapped pins produce
   garbage interpolation and the board will look fine.
2. **Cross-check the pad geometry against SLAA891's OpenSCAD output** before committing copper.
3. **Verify the LCSC C2052972 footprint against the datasheet PT package drawing.**

Q2 and Q3 are closed. [../docs/pin-allocation.md](../docs/pin-allocation.md) is resolved and
safe to build against.

**UART and I2C do not share pins on the PT package**, so route both and select in software. Two
mappings are traps: **UCA1 UART (pins 30/29)** and **default UCB1 I2C (pins 38/39)** both land
on CapTIvate electrode pins, which are all in use.

## Faceplate rules that are easy to violate silently

- **Do not ground-pour under electrodes or their traces.** Parallel-plate capacitance to a
  nearby pour is the dominant parasitic contributor. Hatched ground at a distance if needed.
- **RX0 is one net.** Both end groups connected, return routed on the layer below, never
  under the electrodes.
- **MCU at the centre of the pad group** so trace lengths are equal across all four pads.
  Unequal lengths give unequal baselines.
- **No electrodes at PCB edges.** Weakens ground shielding.
- **Route digital lines away from electrodes**, ideally exiting the opposite edge.
- ESD parts and decoupling caps right at the MCU, low-impedance ground path.
- **Minimum copper 0.15mm, enforced.** Where a ramp would go thinner, drop the bar and give
  its height to the surviving bar. Never draw a sliver.

Suggested stackup: **L1 electrodes, L2 traces, L3 hatched ground, L4 MCU + components.**

## Fab notes

- **ENIG, not HASL.** HASL leaves uneven solder that feels wrong under a sliding finger and
  will not wear well. [ADR 0004](../docs/decisions/0004-no-overlay-exposed-copper.md)
- **Faceplate size is not settled, and it follows from one measurement.** The Salamis
  composition locks `pad length = 12 x pad pitch`, so the inter-pad gap sets the whole
  instrument: 6mm gives **298 x 154mm with 216mm pads**, 10mm gives 365 x 189mm with 264mm
  pads. Settle [Q17](../docs/notes/open-questions.md) before drawing an outline. See
  [../docs/panel-budget.md](../docs/panel-budget.md).
- Exposed copper on the pads: no soldermask over the electrodes. Decoration and instructions
  in silkscreen.
- JLCPCB **does not do overlay lamination**, which is fine given the no-overlay decision.
- microSD sockets need an **assembly fixture** at JLC for support during placement. Not a
  trivial placement, flag it on the order.

## Things to put on the board even though they seem optional

| Item | Why |
|---|---|
| **CAPTIVATE-PGMR connector** (faceplate) | Design Center cannot talk to an MSP-FET or eZ-FET. No PGMR means no live sensor data, which means no real tuning. DNP on production units. |
| **4 SBW test pads** (TEST, RST, 3V3, GND) | Free, and it is the recovery path. A $12 LaunchPad eZ-FET flashes through them. |
| **Both UART and I2C to the faceplate** | Separate pins on the PT package, so both are free to route. Populate one. |
| **Dividers on BSL RST/TEST** | Gate outs are 0-5V, MSP430 max is 3.6V. Four resistors. |
| **VREG decoupling cap, MSP430 pin 31** | CapTIvate regulator output, not a supply input. Easy to miss, and it will not work without it. |
| **Test points on all 4 inter-board signals** | When BSL does not work first time you want a scope probe point that is not an LQFP pin. |
