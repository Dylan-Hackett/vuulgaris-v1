# 02: Power

Block: J11, F1, D3, R22/R23, U7, U5/U6/U8, L1/L2, C20-C43, R24/R25, D1/D2,
Q1/Q2, FB1/FB2. Pin tables were built from the drawings first, then diffed
against `netmap.json`.

Sources read for this section:

- `MeanWell-SKM10-DKM10-spec.pdf` (File Name SKM10,DKM10-SPEC 2024-04-30): p2 model table, p3 specification, p5 mechanical and plug assignment.
- `AMS1117-datasheet.pdf` (Advanced Monolithic Systems): p1 pin connections, p2 absolute maximum and electrical characteristics, p3-p4 application hints.
- `SMAJ6.0A-TVS.pdf` (Littelfuse SMAJ series): electrical table, row SMAJ6.0A.
- `onsemi-MMBFJ113-datasheet.pdf` (Rev 5, March 2023): p1 maximum ratings and SOT-23 pinout, p2 electrical characteristics.
- `Korean-Hroparts-TYPE-C-31-M-12.pdf`: the single-sheet drawing, rendered at 300 dpi and read as an image.
- `Lelon-RVT-electrolytic.pdf`: voltage code table.
- `Xvive-VTL5C3-datasheet.pdf`, `YLED0402Y.pdf`, `HS242L01W4S01-OLED.pdf` p7-p11, `Panasonic-MN3205-datasheet.pdf` p1-p2 (rendered), `TI-TL072`/`TL084`/`OPA1688`, `Microchip-MCP23017` (DS20001952C) for supply currents.
- `V3.0.pdf`, the reference PSU schematic.

## Pinouts

### J11, TYPE-C-31-M-12 (drawing: pin table and "recommend PCB layout, component side")

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| J11.A1B12 | GND | A1 GND, B12 GND (one pad) | GND | CLEAN |
| J11.A4B9 | VBUS | A4 VBUS, B9 VBUS | VBUS | CLEAN |
| J11.B4A9 | VBUS | B4 VBUS, A9 VBUS | VBUS | CLEAN |
| J11.B1A12 | GND | B1 GND, A12 GND | GND | CLEAN |
| J11.A5 | CC1 | A5 CC1 | CC1 -> R22 5.1k -> GND | CLEAN |
| J11.B5 | CC2 | B5 CC2 | CC2 -> R23 5.1k -> GND | CLEAN |
| J11.A6/A7/B6/B7 | NC | DP1, DN1, DP2, DN2 | open | CLEAN (power-only sink, ADR 0010) |
| J11.A8/B8 | NC | SBU1, SBU2 | open | CLEAN |
| J11.1-4 | GND | shell tabs | GND | CLEAN |

Both plug orientations: an unflipped plug presents its CC on A5, a flipped one
on B5. Each has its own 5.1k (`R22`, `R23`), neither shares a resistor, and both
VBUS pairs and both GND pairs are joined. Shield goes straight to GND, as in the
`V3.0.pdf` reference.

Pad order of the footprint, read from the `.kicad_pcb` in footprint-local
coordinates on F.Cu (unmirrored, so it is the component-side view):
A1B12, A4B9, B8, A5, B7, A6, A7, B6, A8, B5, B4A9, B1A12, the same sequence as
the drawing's land pattern. Spans match the drawing: A5-A8 2.50, B8-B5 3.50,
A4B9-B4A9 4.80, A1B12-B1A12 6.40, shell tabs 8.65 apart and 4.18 between rows,
locating holes 5.78 apart. Drawing rating: 5A, 20V. **CLEAN.**

### U7, DKM10E-12 (spec p5 "Plug Assignment", DKM10 column)

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| U7.1 | VBUS_F | +Vin | VBUS_F | CLEAN |
| U7.2 | GND | -Vin | GND | CLEAN |
| U7.3 | POS12V_RAW | +Vout | POS12V_RAW | CLEAN |
| U7.4 | GND | Common | GND | CLEAN |
| U7.5 | NEG12V_RAW | -Vout | NEG12V_RAW | CLEAN |
| U7.6 | (open) | R.C.: "Power ON: R.C. ~ -Vin >5.5~75Vdc or open circuit" (p3) | open | CLEAN |

Input and output share GND here, which defeats the 1.5kV isolation. That is
fine for this use: the spec does not require isolation to be kept.

### U5, U6, U8, AMS1117 (p1, "3 PIN FIXED/ADJUSTABLE VERSION", SOT-223)

1 = Ground/Adjust, 2 = VOUT, 3 = VIN, "TAB IS OUTPUT".

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| U5.1/2/3/4 | GND / P3V3_OLED / P5V_OLED / P3V3_OLED | GND, VOUT, VIN, tab=VOUT | same | CLEAN |
| U6.1/2/3/4 | GND / P3V3_MSP430 / P5V_MSP / P3V3_MSP430 | GND, VOUT, VIN, tab=VOUT | same | CLEAN |
| U8.1/2/3/4 | GND / P5V_BBD / POS12V / P5V_BBD | GND, VOUT, VIN, tab=VOUT | same | CLEAN |

The U8 fix of 2026-09-10 holds.

### D3, SMAJ6.0A; D1/D2, YLED0402Y; Q1/Q2, MMBFJ113

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| D3.1 (C) | VBUS | cathode to the positive line, as the V3.0 reference draws its TVS | VBUS | CLEAN (pad 1 = cathode band: section 8) |
| D3.2 (A) | GND | anode | GND | CLEAN |
| D1.1 (A) / D1.2 (K) | LED_POS / GND | forward from +12V via R24 | A on LED_POS, K on GND | CLEAN |
| D2.1 (A) / D2.2 (K) | GND / LED_NEG | forward into -12V via R25 | A on GND, K on LED_NEG | CLEAN |
| Q1.1/2/3 | BBD_SH_IN_L / BBD_SH_HOLD_L / BBD_SH_G_L | SOT-23: gate is the lone pin 3; "Source & Drain are Interchangeable" | D, S, G | CLEAN |
| Q2.1/2/3 | ..._R | same | same | CLEAN |

## The numbers

### Supply currents, from the datasheets

| part | figure used | source |
|---|---|---|
| TL072 / TL074 / TL084, per amplifier | 1.4 mA typ, 2.5 mA max | SLOS080W 5.8 and SLOS081O, C-grade rows (the TL074/TL084 are `...CDR` per mkbom CURATED; the TL072's grade is not recorded, so the C row) |
| OPA1688, per amplifier | 1.6 typ, 1.8 max, 2.0 max over -40..85C; short-circuit +-75 mA | SBOS724A 7.5 |
| AMS1117 quiescent | 5 typ, 11 max mA | p2 |
| MCP23017 IDD | 1 mA max | DS20001952C D004 |
| MN3205 clock pin capacitance | 2800 pF max per pin; fcp 10-100 kHz | p2 operating conditions. **No supply current is published** (p2 electrical table has none). |
| VTL5C3 LED | 40 mA max (derate 0.9 mA/C above 30C), VF 1.65 typ / 2.0 max at 20 mA, **reverse breakdown 3.0 V** | Xvive p1 |
| YLED0402Y | IF 20 mA max, VF 1.8-2.4 V at 20 mA | p2-p3 |
| OLED module | VCC (module input) 3-5 V abs max; panel ICC 31.7 mA at a 13 V panel rail, 100% on | p9, p10. **The module's current at its own 3-5 V input is not stated.** |
| Daisy Patch SM | 5V out 800 mA max, 3V3 out 500 mA max | Table 1. **Its own consumption is not stated anywhere in the sheet.** |

### Rail budget

Known worst-case loads, everything except the Patch SM's own draw:

| rail | load | mA, max case | arithmetic |
|---|---|---|---|
| +12 V | 28 TL07x/TL08x amplifiers | 70.0 | 28 x 2.5 |
| | 4 OPA1688 amplifiers | 8.0 | 4 x 2.0 |
| | U8 in: quiescent + P5V_BBD | 11 + ~7 + BBD IDD | clock drive 4 pins x 2800 pF x 5 V x 100 kHz = 5.6; VGG dividers 2 x 5/(4.7k+62k) = 0.15; CD4046 VCO about 1 |
| | R24 + D1 | 4.8 | (12.3 - 1.8)/2.2k |
| | R110/R210, R125/R225, RV1 | 1.6 | 2 x 12.3/22k + 2 x 12.3/110k + 2 x 12.3/100k |
| | headphones, both channels, RT501/502 fully up | 45 peak, 14.5 average | Patch SM out +-5 V typ (Table 3) x 20k/120k = 0.83 V peak into 4.7 + 32 ohm = 22.7 mA per channel |
| | **subtotal** | **~145 peak** | |
| -12 V | op-amps (quiescent flows rail to rail) | 78.0 | |
| | R25 + D2 | 4.8 | |
| | R113/R213 | 0.5 | 2 x 12.3/47k |
| | vactrol LEDs, both channels fully on | ~15 | U301B/U401B sink through the LEDs toward V-: (10.5 - 3.7 - 2 x 1.65)/470 = 7.4 mA per channel, zener at its 3.7 V minimum |
| | headphones | 45 peak | |
| | **subtotal** | **~145 peak** | |

Then the Patch SM, on +12 V and -12 V, plus everything it re-exports on +12 V:
the OLED via FB1/U5, the faceplate via FB2/U6 (11 mA quiescent plus the MSP430),
both MCP23017s (2 mA), the microSD card (card dependent, no figure in the repo),
I2C pullups (3 mA with both lines low).

None of that is published. `power-usbc-dkm.md` estimates 250-300 mA for the
Patch SM including its exports. **Summed with its own table, that document puts
the +12 V rail at 353-433 mA**, and with the datasheet maxima above, 395-445 mA.
The DKM10E-12 is rated **"+-0~416mA"** per output (p2). The document compared
the total, about 6 W, against the 10 W rating and stopped there; the per-output
limit was never checked, and the +12 V rail carries nearly all the digital load
because the Patch SM makes its 5 V and 3.3 V from +12 V. The -12 V rail sits
near 150-250 mA, so the converter runs well inside 10 W but with one output at
or past its rating, and the spec gives load regulation (+-1%) only for 10-100%
loading, with no cross-regulation figure for an unbalanced dual output.

How much the OLED and the card cost on +12 V depends on how the Patch SM
regulates, which its sheet does not say. Inference, not a datasheet fact: an
800 mA rating on a 5 V output from a 12 V input would dissipate 5.6 W in a linear
regulator, so it is very likely a switcher, in which case the exports cost
roughly half their 5 V current at 12 V. That makes the low end of the range the
likely one. It does not close the question.

**Verdict: QUESTION, potentially fatal.** Measure +12 V current on the bench
with the OLED full white, an SD write in progress and the headphone trims up,
before ordering more than the first board. Over about 350 mA, the converter
choice has to change.

### Input side

- Full load in: the spec's full-load input current is 2295 mA at 5 V
  (p2). Our estimate of 5-7 W out at 87% efficiency is 1.2-1.6 A at 5 V, within a
  3 A source.
- USB VBUS standoff: D3 VR 6.0 V, VBR 6.67 V min, so it does not conduct on a
  5 V bus; IR 800 uA max at 6.0 V. Clamp VC 10.3 V at IPP 38.8 A, under the
  DKM10E's "SURGE VOLTAGE (100ms max.) 5Vin models: 12Vdc" and under the 25 V
  rating of every capacitor on VBUS/VBUS_F. **CLEAN.**
- U7 input range is 4.7-9 V, UVLO start 4.4 V and shutdown 4.2 V. At 1.4 A a
  cable and fuse that drop 0.3 V leave 4.7 V from a 5.0 V source. This is the
  margin ADR 0010 already decided to manage by specifying the source and cable.
  No datasheet limit says it cannot work. Not re-raised.
- **F1 hold and trip: BLOCKED.** No ASMD1812-300 sheet in the repo. The 3 A hold
  / 5 A trip / 40 mohm figures in `power-usbc-dkm.md` are uncited. Mean Well
  recommends "5A delay time Type" (p3, Protection) for the 5 V-input models,
  which a 3 A-hold PTC plausibly approximates, but that needs the PTC's own
  curve and its derating with temperature.
- **L1/L2 (BLM18PG121SN1D) and FB1/FB2 current rating: BLOCKED.** These are
  in series with every milliamp of their rails (L1 with the whole +12 V rail,
  up to ~420 mA by the estimate above). The inventory treated beads as
  datasheet-free, which is right for pin semantics but not for current. The
  only rating in the repo is a code comment in `mkbom.py` (500 mA for FB1/FB2).

### U7 output capacitance and start-up

Per output (p2 "CAPACITOR LOAD (MAX.) *440uF, *For each output"):

- +12 V: C32 47 uF + C36 22 uF + C34/C38/C40 and twelve 0603 100 nF = 70.5 uF,
  84 uF at +20% tolerance, plus whatever bulk sits on the Patch SM's input.
- -12 V: C33 47 + C37 22 + 1.3 = 70.3 uF, 84 uF at +20%.

Both are under a fifth of the limit. Start-up into this load is inside the
converter's spec; no minimum load is required ("No minimum load required", p1).
R.C. open = on. **CLEAN.**

### AMS1117s

| check | U5 (3.3 V, OLED) | U6 (3.3 V, faceplate) | U8 (5 V, BBD) |
|---|---|---|---|
| VIN vs 15 V abs max | ~5 V | ~5 V | 12.3 V max (12 V +-1.5% accuracy, +-1% load reg.) -> 2.7 V margin |
| headroom vs dropout (1.3 V max at 0.8 A, less at lower load) | ~1.65 V after FB1 | ~1.65 V | ~7 V |
| dissipation, (VIN - VOUT) x IOUT + VIN x IQ | (1.7 x 0.16) + (5 x 0.011) = 0.33 W at an assumed 160 mA OLED draw | < 0.1 W | (7.3 x 0.02) + (12.3 x 0.011) = 0.28 W at 20 mA; 0.65 W at 70 mA |
| Tj at 40 C ambient, 90 C/W (p2, SOT-223 on copper) | 70 C | ~49 C | 65 C; 98 C at 70 mA |
| output cap fitted | C20 10 uF X5R 0805 + C21 100 nF | C22 10 uF + C23 100 nF | C42 10 uF + C41 100 nF |

All inside 125 C. The OLED current is an assumption: the module sheet gives the
panel's 31.7 mA at 13 V but not what the module draws at its 3.3 V input; 160 mA
assumes an 80%-efficient on-module boost.

**Output capacitor: QUESTION.** The datasheet's only stability statement is
"The addition of 22uF solid tantalum on the output will ensure stability for all
operating conditions" and that smaller capacitors work "without bypassing the
adjustment terminal" (p3, Stability). It gives no ESR window and says nothing
about ceramic capacitors. All three regulators run on a 10 uF X5R MLCC, which
at 3.3-5 V bias is nearer 6-7 uF with milliohm ESR. That is outside anything
this sheet guarantees. Bench-check each rail for oscillation at light and full
load; if it rings, a 22 uF tantalum or 1 ohm in series with the MLCC is the fix.

### Capacitor voltage ratings and polarity

Every capacitor on the board, rating from the part number in the BOM line
(Yageo `...8BB...` = 25 V, `...9BB...` = 50 V; Samsung `CL21A..KA..` = 25 V,
`CL05B..KO..` = 16 V, `CL10C..JB8..` = 50 V; Lelon `RVT1E` = 25 V, `RVT1H` = 50 V,
per the Lelon voltage-code table):

- 25 V parts sit on +-12.3 V at most: 49% of rating. 16 V parts sit on 3.3 V.
  No rail capacitor exceeds half its rating.
- The only sub-50 V parts off a rail are C110/C210, 10 uF 25 V on VGG (about
  4.6 V). Fine.
- C310/C410 (22 pF C0G, `C1653`): rating not recorded in the repo. They sit in
  an op-amp feedback path, so at most about 11 V. Every C0G 0603 at that value
  is 25 V or more in practice; not checkable from the repo. Low risk.

Electrolytics, symbol pin 1 against the more positive net:

| ref | pin 1 | pin 2 | verdict |
|---|---|---|---|
| C32 47 uF 25 V | POS12V_RAW | GND | CLEAN |
| C33 47 uF 25 V | GND | NEG12V_RAW | CLEAN |
| C36 22 uF 50 V | POS12V | GND | CLEAN |
| C37 22 uF 50 V | GND | NEG12V | CLEAN |

The symbol pins are named `1`/`2`, not `+`/`-`, so this holds only if footprint
pad 1 is the + terminal. Section 8 checks the silkscreen and the Lelon drawing.

### Q1/Q2 across the J113 spread

Q1 is the sample switch of the BBD's sample-and-hold: drain on U106A's output
(`BBD_SH_IN`), source on the 10 nF hold cap C119 and U106B's input, gate tied to
the drain through R128 100k and pulled down through D107 by the comparator
U102B.

- **On** (U102B output high, D107 reverse biased): VGS = 0 through R128.
  rDS(on) is 100 ohm max at VGS = 0 (p2). Time constant 100 ohm x 10 nF = 1 us
  worst case.
- **Off** (U102B output low, about -10.5 V on a +-12 V TL072): gate at about
  -9.8 V. VGS(off) for the J113 spans -0.5 V to -3.0 V (p2). The switch stays off
  while the more negative channel terminal is above -9.8 + 3.0 = **-6.8 V**. The
  signal here is the BBD's AC-coupled output, a few volts peak at most. 6.8 V of
  margin at the worst-case device.
- VGS worst case about -16 V against -35 V (p1). Gate leakage via D107 reverse
  current into 100k is millivolts.

**CLEAN** across the full datasheet range. (Acquisition time against the sample
pulse width is section 5's.)

### Power sequencing

All rails come from one converter: +-12 V together, then P5V_BBD (U8 from +12 V),
the Patch SM's 5 V and 3.3 V, then U5/U6 from the Patch SM's 5 V.

| interface | during ramp | verdict |
|---|---|---|
| U103A output (+-12 V op-amp) -> U101.7 BBD IN | U103A's DC bias is +10k x 12/47k = **+2.55 V** from R113 to NEG12V, present before P5V_BBD rises. MN3205 absolute maximum is "-0.3~+11 V" per terminal, referred to GND (p2), with no VDD-relative limit stated. | CLEAN (clipping behaviour is section 5's) |
| TIME pot and TIME_CV -> U104.9 VCO IN | can sit above a not-yet-up P5V_BBD; D103 clamps into the rail through 100k, under 0.1 mA. CD4046B allows +-10 mA per input (p1). | CLEAN |
| GATE_OUT_2 -> U104.5 INHIBIT | 0-5 V through R117 100k, clamped by D104/D106 | CLEAN |
| Patch SM 3.3 V GPIO -> OLED logic | OLED logic max 3.3 V (p9). The GPIOs are high-impedance until firmware runs, which is long after U5 is up. | CLEAN |
| Patch SM UART TX -> MSP430 RXD | MSP430 on U6, which rises from the same 5 V within milliseconds; the Daisy boots in hundreds. | CLEAN |
| MSP430 TXD -> Patch SM A2 | Patch SM GPIO absolute max -0.3 to 6 V (Table 1) | CLEAN |
| U4 GPB3 -> MSP_RST | MCP23017 resets to all-input | CLEAN |
| op-amp outputs -> Patch SM audio and CV inputs | the Patch SM's +-12 V are POS12V/NEG12V, so its input ratings ("Negative Power In" to "Positive Power In", Table 1) rise with the op-amps' rails | CLEAN |

### +-12 V filter, internal sanity (source diff BLOCKED-LOCAL)

The EasyEDA source (`~/Documents/origin2.2.eprj`) is not in this checkout, so
`edapower.py` cannot run. Internally: each rail is raw bulk (47 uF) and 100 nF at
the converter, a 120-ohm-at-100-MHz bead, then 22 uF and 100 nF. Both
electrolytics are polarised correctly. The bead and the 22 uF can resonate in
the tens of kHz, damped by the electrolytic's ESR; nothing in the repo
quantifies the bead's inductance. Topology matches `power-usbc-dkm.md`. Same
structure on both rails, with L1 on +12 V and L2 on -12 V as the doc says.

## Verdicts

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| J11 all 16 pins + shell | | drawing pin table | as table above | CLEAN |
| U7.1-6 | | Mean Well p5 | as table above | CLEAN |
| U5/U6/U8 | | AMS p1 | as table above | CLEAN |
| D3, D1, D2, Q1, Q2 | | each drawing | as table above | CLEAN |
| C32/C33/C36/C37 polarity | | pin 1 = + assumed | correct for that | CLEAN pending section 8 |
| U7 +12 V output current | POS12V | 416 mA per output | 395-445 mA estimated, unmeasured | QUESTION (potentially fatal) |
| U5/U6/U8 output cap | P3V3_OLED, P3V3_MSP430, P5V_BBD | 22 uF tantalum guaranteed | 10 uF MLCC | QUESTION |
| F1 | VBUS/VBUS_F | needs its own sheet | none in repo | BLOCKED |
| L1/L2/FB1/FB2 rating | | needs their own sheets | none in repo | BLOCKED |
| Patch SM, OLED, MN3205 currents | | not published | | BLOCKED (bench) |
| +-12 V filter vs EasyEDA | | `origin2.2.eprj` | | BLOCKED-LOCAL |
| D3 standoff and clamp | VBUS | 6.0 V / 10.3 V | vs 5 V bus, 12 V surge | CLEAN |
| U7 capacitive load | | 440 uF per output | ~84 uF | CLEAN |
| capacitor ratings | | part codes | all at or under 49% | CLEAN |
| Q1/Q2 VGS(off) spread | | -0.5 to -3.0 V | gate at -9.8 V | CLEAN |

## Defects and questions, ranked

1. **QUESTION, could kill the board: +12 V load against the DKM10E-12's
   416 mA per output.** The existing budget, summed per rail, lands on the
   rating. The unknown is the Patch SM's draw. Measure before a production
   order; nothing on the board changes unless the number is over.
2. **QUESTION, degrades: AMS1117 stability on all-ceramic outputs.** Not
   covered by its datasheet. Bench check; tantalum or a series resistor if it
   rings.
3. **BLOCKED: F1, L1/L2, FB1/FB2 ratings.** Add the four datasheets.
4. **Doc (cosmetic):** `power-usbc-dkm.md` puts the vactrol LED drive on
   +12 V. U301B/U401B sink the LED current toward V-, so it is a -12 V load.
   The same table never sums the +12 V column against the per-output rating.
