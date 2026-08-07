# Faceplate PCB

4-layer, **size not yet settled** (see [../../docs/panel-budget.md](../../docs/panel-budget.md); working proposal ~285 x 155mm), **ENIG**. Carries the four capacitive scrub pads on L1
and the MSP430FR2675 on the back.

## Contents (expected)

```
vuulgaris-faceplate.kicad_pro / .kicad_sch / .kicad_pcb
pads.svg          exported from ../../mockups/comb-pad-generator.html, true mm scale
pads-ti.dxf       SLAA891 OpenSCAD output, for cross-checking pads.svg
```

## Pad geometry

Authoritative spec is [ADR 0003](../../docs/decisions/0003-comb-pad-rx0-wraparound.md).
Summary: 4 channels, 5 segments, 4 zones, order `RX0 RX1 RX2 RX3 RX0`, 12mm wide. **Length is
derived, not chosen:** the Salamis composition locks `pad length = 12 x pad pitch`, so it
follows the inter-pad gap ([Q17](../../docs/notes/open-questions.md)). Working value **216mm**
at a 6mm gap, 80 teeth at 2.19mm pitch, minimum copper 0.15mm enforced.

Generate with `../../mockups/comb-pad-generator.html`. It exports SVG at true mm scale with
one `<g>` per net, which imports cleanly as separate copper zones.

**Cross-check against TI's own SLAA891 OpenSCAD output before committing copper.**

## Pin order is load-bearing

`RX0->E00, RX1->E01, RX2->E02, RX3->E03`. Generate the assignment in Design Center **first**,
then lay out to match. A swapped pair produces garbage interpolation on a board that passes
every electrical check.

## Per-electrode ESD network

5 electrodes x 4 pads = **20 of each**:
- 470R-1k series resistor per electrode
- TPD1E10B06 TVS between electrode and ground, on the **electrode side** of the resistor

Place near the MCU with a low-impedance ground path.

## Layout checklist

- [ ] No ground pour under electrodes or their traces
- [ ] RX0 end groups connected as one net, return on L2, not under electrodes
- [ ] MCU centred on the pad group, trace lengths equalised
- [ ] No electrode within the edge keepout
- [ ] Digital lines exit the opposite edge from the electrodes
- [ ] Minimum copper 0.15mm everywhere, no slivers at ramp ends
- [ ] CAPTIVATE-PGMR connector present
- [ ] 4 SBW test pads present (TEST, RST, 3V3, GND)
- [ ] Test points on UART Tx/Rx, IRQ, RST, TEST
- [ ] Soldermask opening over all pad copper
- [ ] Usable scrub region marked inside the copper, or copper extended past the printed scale
      (endpoint trim eats a few mm at each end)
