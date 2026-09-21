# USB-C + DKM10E-12 power stage — extracted from EasyEDA

Source: `~/Documents/origin2.2.eprj` (SQLite), PCB document `postpcb` (rowid 33).
Read from the **`PAD_NET` records of the routed board**, so this is EasyEDA's own
resolved connectivity, not a reading of the drawing. Designators below are the
EasyEDA ones; they get renumbered on the way into `netmap.json`.

Caveat: this is the board file, which is authoritative about what was *drawn*.
Whether this specific board is the one Dylan built and verified is his call —
the extraction cannot tell.

## Nets

| EasyEDA net | meaning |
|---|---|
| `DKM5V` | VBUS off the USB-C connector |
| `$1N339035` | 5V after the PTC fuse — DKM input |
| `$1N364806` | +12V raw, DKM pin 3, before the ferrite |
| `$1N362061` | -12V raw, DKM pin 5, before the ferrite |
| `V+` | +12V rail |
| `VEE` | -12V rail |
| `$1N338891` / `$1N338930` | CC1 / CC2 |

## Topology

```
USB-C  A4/B9,B4/A9 ── DKM5V ──┬── C105 10nF ── GND
                              │
                              └── F1 (PTC 2A) ── 5V_F ──┬── C81  22uF/50V ── GND
   A5 (CC1) ── R438 5k1 ── GND                          ├── C82  1uF 0805  ── GND
   B5 (CC2) ── R439 5k1 ── GND                          ├── C100 100nF     ── GND
   shell 1-4, A1/B12, B1/A12 ── GND                     │
                                                        └── U44 pin 1 (+Vin)
                                        U44 pin 2 (-Vin) ── GND
                                        U44 pin 4 (COM)  ── GND
                                        U44 pin 6        ── NC

 U44 pin 3 (+Vout) ── +12V_RAW ──┬── U50 47uF/25V ── GND
                                 ├── C102 100nF     ── GND
                                 └── L2 (BLM18PG121, 120R) ── V+  ──┬── C110 22uF/50V ── GND
                                                                    ├── C113 100nF    ── GND
                                                                    └── R440 2k2 ── LED20 (red) ── GND

 U44 pin 5 (-Vout) ── -12V_RAW ──┬── U49 47uF/25V ── GND
                                 ├── C104 100nF     ── GND
                                 └── L1 (BLM18PG121, 120R) ── VEE ──┬── C111 22uF/50V ── GND
                                                                    ├── C112 100nF    ── GND
                                                                    └── GND ── U43 (yellow LED) ── R441 2k2 ── VEE
```

## Bill of materials

| Ref | Part | Function |
|---|---|---|
| USBC1 | `TYPE-C-31-M-12` | 16-pin USB-C receptacle, power-only (D+/D-/SBU floated) |
| F1 | `ASMD1812-300` | 3.0A hold / 5.0A trip resettable PTC, 1812 (was `-200`, 2.0A/4.0A, until 2026-09-20) |
| R438, R439 | `RT0603BRD075K1L` | 5.1k CC1/CC2 pulldowns |
| C105 | `CC0603JRNPO9BN103` | 10nF NP0, at the connector |
| C81 | `RVT1H220M0605` | 22uF 50V electrolytic, input bulk |
| C82 | `CC0805KKX7R9BB105` | 1uF X7R 0805 |
| C100 | `CC0603JRX7R8BB104` | 100nF X7R |
| U44 | `DKM10E-12` | 5V -> +/-12V, 10W regulated |
| U50, U49 | `RVT1E470M0505` | 47uF 25V, output bulk, one per rail |
| C102, C104 | `CC0603JRX7R8BB104` | 100nF, one per raw rail |
| L2, L1 | `BLM18PG121SN1D` (C14709) | ferrite bead 120R@100MHz, one per rail |
| C110, C111 | `RVT1H220M0605` | 22uF 50V, post-ferrite |
| C113, C112 | `CC0603JRX7R8BB104` | 100nF, post-ferrite |
| R440, R441 | `RT0603BRD072K2L` | 2.2k LED series |
| LED20 | `FC-2012HRK-620D` | red, +12V present |
| U43 | `YLED0402Y` | yellow, -12V present |

## Things worth noticing about this design

1. **No reverse-polarity diode and no TVS.** Half right, and the half that was
   wrong stood here until 2026-09-10. A USB-C receptacle cannot be
   reverse-polarised, so the Schottky the barrel design needs is genuinely not
   needed, and its 0.4V drop goes with it. But that argument says nothing about a
   TVS, which answers a different question — transients, not polarity — and the
   two got conflated into one bullet and waved through together. The EasyEDA board
   this section describes has no TVS; the later `reference/V3.0.kicad_sch` does.
   One is now fitted as `D3`; see *Checked against the source schematic* below.
2. **LED indicators double as a minimum load.** `(12 - 2) / 2k2` is about 4.5mA
   permanently on *each* rail. The minimum-load problem that dogged the B1212S
   barrel design is much less of an issue here: the DKM is regulated, and there is
   already a bleed path on both rails whether or not the LPG is populated.
3. **Two-stage filtering per rail** — bulk, then ferrite, then bulk+HF again.
   That is more filtering than the barrel stage currently has.
4. **The PTC is 2A** at 5V, ~10W in, which is above the DKM's 10W rating; the
   converter's own limit is the tighter one.
5. **Pin numbering for U44 comes from the board, not from the datasheet.** Pulling
   `DKM10E-12` in through `easyeda2kicad` from the same LCSC part carries the same
   pad numbering, so the mapping above transfers directly.

## As built into this repo

**Generated** into `hardware/kicad/tools/netmap.json` by `tools/edapower.py`,
which reads the `.eprj` directly -- not hand-transcribed. Re-run it to check:

```bash
python3 tools/edapower.py          # 57/57 pin-nets match the EasyEDA board
```

The first version of this WAS hand-typed, and nine two-terminal parts came
across with pins 1 and 2 swapped -- six ceramics and three resistors, all
non-polar, so electrically identical, but not what the board says. Every
polarised part was right. Generating it removes the question.

Designators are renumbered to fit this project's sequence:

| here | EasyEDA | part | LCSC |
|---|---|---|---|
| J11 | USBC1 | TYPE-C-31-M-12 | C165948 |
| F1 | F1 | ASMD1812-300 PTC 3A | C135366 |
| C28 | C105 | 10nF 0603 NP0 | C389113 |
| R22, R23 | R438, R439 | 5.1k 0603 | C122969 |
| C29 | C81 | 10uF 25V X5R 0805 | C15850 |
| C30 | C82 | 1uF 0805 | C91185 |
| C31 | C100 | 100nF 0603 | C327087 |
| C43 | — | 100nF 0603, at the connector; new 2026-09-18 | C14663 |
| U7 | U44 | DKM10E-12 | C6934792 |
| C32, C33 | U50, U49 | 47uF 25V SMD can | C2977553 |
| C34, C35 | C102, C104 | 100nF 0603 | C327087 |
| L1, L2 | L2, L1 | BLM18PG121SN1D ferrite | C14709 |
| C36, C37 | C110, C111 | 22uF 50V SMD can | C72505 |
| C38, C39 | C113, C112 | 100nF 0603 | C327087 |
| R24, R25 | R440, R441 | 2.2k 0603 | C861295 |
| D1, D2 | LED20, U43 | LED 0402 | C20608782 |

Here L1 is the +12V bead and L2 the -12V one; EasyEDA had them the other way
round. Odd-numbered rail parts are +12V, even-numbered are -12V throughout.

Nets: `VBUS`, `VBUS_F`, `CC1`, `CC2`, `POS12V_RAW`, `NEG12V_RAW`, `POS12V`,
`NEG12V`, `LED_POS`, `LED_NEG`. `POS12V`/`NEG12V` already existed — they feed
the Daisy at U1.A5 and U1.A1 — so the stage drops straight in.

### Deltas from the EasyEDA original

1. **Both indicator LEDs are the same part** (`YLED0402Y`, yellow). The original
   used a red `FC-2012HRK-620D` on +12V, which is not in the EasyEDA project's
   device table and could not be resolved to an LCSC number. Same 0402 footprint,
   so making them different colours later is a BOM edit, not a layout change —
   and worth doing, because "+12 lit, -12 dark" is the fastest bring-up
   diagnostic there is.
2. **U7 pin 6 (`R.C.`) is left open**, as it was on the working board.

### U8: 78L05 (SOT-89) -> AMS1117-5.0 (SOT-223), 2026-09-07

**The 78L05 had no defensible thermal margin, because the load current is not a
knowable number.** U8 drops **12V to 5V** for the BBD's digital side -- two
V3205SD and two CD4046. In SOT-89 the part is **500mW at roughly 250 C/W**:

| load | dissipation | rise | T_j at 40C inside the box |
|---|---|---|---|
| 35mA (estimate) | 245mW | 61C | **101C** — 24C of margin |
| 50mA | 350mW | 87C | **127C** — over the 125C limit |
| 100mA (its own rating) | 700mW | — | **exceeds P_D outright** |

The problem is not the estimate, it is that **the estimate cannot be checked.**
Panasonic never published an I_DD for the MN3205 -- the datasheet's electrical
table has delay, insertion loss, THD, S/N and no supply current at all. The only
hard number is **C_CP = 2800pF per clock pin**, which by itself puts
`4 x 2800pF x 5V x 100kHz` = **5.6mA** of clock-drive current on this rail before
the BBDs' own consumption. So the answer sat between "fine" and "destroyed" with
no way to close it on paper.

**AMS1117-5.0 in SOT-223 removes the question rather than answering it.** Same
part family and the same footprint as `U5`/`U6`, LCSC **C6187** against C6186.
SOT-223 runs about **100-160 C/W** with its pad, and the part is good for **1A**
instead of 100mA:

| load | dissipation (incl. ~6mA quiescent x 12V) | rise | T_j at 40C |
|---|---|---|---|
| 35mA | 317mW | 32-51C | 72-91C |
| 70mA (double the estimate) | 562mW | 56-90C | 96-130C |

At the estimate it is comfortable, and at **twice** the estimate it is still
alive where the 78L05 was already destroyed. That is the property worth buying.

`C42` goes **3.3uF -> 10uF** with it: the AMS1117 needs a real output capacitor
for loop stability, and 10uF ceramic is what `U5`/`U6` already use.

**Still open:** the actual rail current is unmeasured. Put a meter on `P5V_BBD`
at bring-up. The point of the swap is that the number stopped being load-bearing,
not that it stopped mattering.

### Checked against the source schematic — 2026-09-10

The source finally arrived: `reference/V3.0.kicad_sch`, "Mini - USB-C power
supply" rev 3, Nanas Sound OÜ, 2026-01-15. Its netlist was extracted with
[`schnet.py`](../hardware/kicad/tools/schnet.py) (the file is KiCad 10 format,
which KiCad 7's CLI refuses, and it carries connectivity as bare wires and
junctions with almost no labels) and diffed against `netmap.json`.

**U7 matches the reference pin for pin**, and independently matches the Mean Well
SKM10/DKM10 spec: `1=+Vin 2=-Vin 3=+Vout 4=Common 5=-Vout 6=R.C.`, with R.C.
left open in both, which the datasheet confirms means ON. The 5.1k CC pulldowns
and the 2A fuse match too. Our input caps sit *after* the fuse where the
reference puts them before it; that feeds the converter directly and is the
better of the two. **See the 2026-09-18 section below** — that comparison was
apples to oranges, and reading it properly changed two parts.

One genuine omission, since fixed:

- **No transient suppressor on VBUS.** The reference carries `D1`, an SMBJ5.0A
  5V TVS, cathode to +5V and anode to GND, right at the connector. Our `/VBUS`
  held only `C28` (10nF), `F1` and the two `J11` VBUS pads. `F1` is an
  resettable polyfuse — it limits *current* and does nothing about a
  *voltage* transient, and the datasheet gives the DKM10E-12 4.7–9Vdc continuous
  with 12Vdc tolerated for 100ms only. A hot-plug inductive kick into our 22uF
  of input bulk rings toward 2x supply, which is already past continuous spec
  before anything has gone wrong.

  **Added 2026-09-10 as `D3`, an SMAJ6.0A**, cathode to `/VBUS` and anode to a
  GND via, on the back at (366.5, 66.0) inside the existing at-the-connector
  cluster beside `C28`.

  6.0A rather than the reference's 5.0A: USB VBUS is spec'd 4.75–5.25V, and a
  5.0V standoff sits *under* that ceiling where the part leaks (800uA spec).
  6.0A stands off 6.0V, clear of 5.25V, and clamps at 10.3V — inside the 12V
  window. 6.5A would clamp at 11.2V, too close to it.

  What this does **not** do is survive sustained overvoltage. Fed 12V through a
  USB-C-to-barrel adapter the TVS conducts hard and cooks long before a 2A PTC
  trips, because PTCs take seconds. That needs a real OVP circuit — a load
  switch with an overvoltage cutoff, or a series FET and comparator. The TVS
  covers transients and ESD, which is what the reference uses it for.

### Sink capacitance and the missing 100nF — 2026-09-18

Re-read the reference's input stage properly, tracing its netlist rather than
its picture, and the earlier "ours is the better of the two" was comparing
different things.

**The reference's pre-fuse caps are not input caps.** Its `+5V` node is
exported: it lands on pins 5 and 6 of both 16-pin Eurorack headers. So `C1`
(10uF), `C2` (100nF), `C3` (10nF) and the `D1` TVS are the bulk and bypass for
a rail that leaves the board, and the fuse is on a *branch* off that rail
feeding only the converter — whose input pin has no local capacitor at all. We
export no 5V (`P5V` comes off the Daisy's A6, `P5V_BBD` off `U8`), so `VBUS_F`
reaches exactly one thing, `U7` pin 1, and our caps belong where they are.

Three things came out of it:

- **`C29` 22uF → 10uF, and ceramic.** A fuse is a DC short, so everything on
  `VBUS` *and* `VBUS_F` counts as sink capacitance at the port, and the USB
  limit on a device's VBUS bypass is 10uF — there to bound hot-plug inrush.
  22uF + 1uF + 100nF + 10nF was 23uF, and the reference sits deliberately *on*
  the limit with a 10uF can.

  Ceramic rather than a smaller can because the DKM10 spec gives **no minimum
  external input capacitance** and lists its own input filter as "Pi type", so
  this bulk is a courtesy. A 10uF X5R gives up roughly a quarter of its value
  to DC bias at 5V, which puts the real total under 10uF instead of level with
  it. `CL21A106KAYNNNE` (C15850) is JLC Basic and already on this board seven
  times, so the swap adds no BOM line and removes one part from the 22uF can
  line. On the board it is the same spot, 6.6mm square down to 0805.

  The one thing the can bought was ESR, which damps the ring when a cable is
  plugged into an all-ceramic input. `D3` covers it: an SMAJ6.0A breaks down at
  6.67V minimum, well under the DKM10's 9V continuous ceiling.

- **`C43`, a 100nF at the connector.** The reference pairs 100nF with its 10nF
  on raw VBUS; we had the 10nF alone. `C30`/`C31` cannot do this job because
  they are on the converter side of the fuse. Placed on the back at
  (366.895, 63.12), 2.8mm right of `C28`, tapping the same `VBUS` track with
  its own GND via at (367.595, 64.2).

- **Rail bulk is inside the converter's capacitive-load limit.** `U7`'s
  maximum capacitive load is 440uF, footnoted "for each output" (spec page 2).
  Per rail: `C32` 47uF + `C36` 22uF + about 1.3uF of 100nFs = roughly **70uF**,
  well inside it, and below the reference's 100uF per output. The ferrite beads
  are DC shorts, so everything downstream counts, and nothing downstream is
  bulk. Worth having written down because exceeding this limit is a *start-up*
  failure rather than a running one — the converter cannot charge the bulk
  inside its soft-start window, so it hiccups and retries — which presents as
  a board that simply never powers up. Recheck it if any rail cap grows.

  `C32`/`C33` are **47uF**, not 470uF: `RVT1E470M0505` carries an EIA
  three-digit code, 47 × 10^0. Its sibling `RVT1H220M0605` has its own descr in
  the footprint, "22uF 50V", which settles the reading, and 470uF at 25V is a
  10mm can rather than the 5.0mm one this footprint is. `schdraw.py` had a
  hardcoded fallback string saying 470uF and was the only record in the repo
  that did; it is fixed, and it is the reason to distrust display fallbacks.

### Current budget — 2026-09-20

Nobody had added this up. The working assumption was "well under an amp"; it is
about **1.4A at 5V**, roughly three times that. Written down here so the next
person does not have to guess, and because three separate decisions depend on it.

| rail | load | mA |
|---|---|---|
| **+12V** | Daisy Patch SM, including the 5V and 3V3 it returns to the OLED, MSP430, both MCP23017s and the microSD | 250–300 |
| | 28 TL07x/TL08x channels (6 x TL072 dual, 2 x TL074 quad, 2 x TL084 quad) at 1.4mA typ / 2.5mA max per amplifier | 40–70 |
| | vactrol LED drive, both channels fully open | ~30 |
| | `U8` AMS1117-5.0 feeding two V3205SDs and two CD4046s | ~23 |
| | `D1` rail LED through `R24`, bias and dividers | ~10 |
| **−12V** | the same op-amp quiescent current (it flows rail to rail), the Daisy's analog section, `D2` | 75–120 |

That is about **6W out**, so **1.3–1.4A in at 5V** after the DKM10's 87%, plus
its own 40mA no-load draw.

**Caveat, and it is the dominant term:** Electrosmith's Patch SM datasheet gives
absolute maximum ratings and what the module can *supply* (5V out 800mA, 3V3 out
500mA) but never states what it *consumes*. The 250–300mA is an estimate. This
whole table wants a bench-supply measurement before anything is ordered in
quantity.

Three things depend on the number:

- **The fuse, since changed.** A PPTC's hold current derates with ambient --
  roughly 0.7x at 60C, which a closed enclosure dissipating 6W will reach. The
  old `ASMD1812-200` was therefore holding about 1.4A against a 1.4A draw. That
  is a *warm-up* trip, not a start-up one: it would run for ten minutes and then
  the rails would sag. `ASMD1812-300` holds 3A and trips at 5A, so derated it
  still holds about 2.1A -- 50% margin -- and it is closer to Mean Well's own
  "5A delay time Type" recommendation for the 5V-input models. Same 1812
  footprint, same 8V rating, so no layout change.

- **Input voltage headroom, which is the tighter constraint.** The DKM10E-12
  needs **4.4V to start** and 4.7V minimum to run. At 1.4A a thin 1m USB-C cable
  (0.3–0.4 ohm round trip) drops 0.4–0.6V before the board sees anything. The
  fuse change helps here too: `R1max` goes 100mohm -> 40mohm, worth 85mV. From a
  5.0V source on a good cable that lands near 4.65V; on a cheap charge-only cable
  it can land under 4.4V and simply not start. **The instrument needs a
  data-grade cable, and that is a spec, not a suggestion.**

- **USB current advertisement.** `J11`'s CC1 and CC2 go to `R22`/`R23`, 5.1k to
  ground, and nowhere else -- nothing on the board reads what the source is
  advertising. A 5.1k pulldown says only "I am a sink". A host advertising
  *default* USB power offers 500mA (900mA on USB3); we would take 1.4A, and many
  ports will current-limit or shut down.

  **Decided 2026-09-20, [ADR 0010](decisions/0010-usb-source-5v-3a-no-cc-sensing.md):
  the 5V/3A source and a data-grade cable are a stated requirement of the
  instrument, and CC sensing is NOT being added.** The instrument cannot do its
  job on 500mA -- the Daisy, the OLED, both BBDs and twelve op-amp packages are
  none of them optional -- so there is no useful degraded mode to negotiate down
  to. The requirement has to reach the user: manual, product page, and ideally a
  label at the jack. No board change.

### Open, and not yet checked

- **U7 is 25.4mm square and about 10mm tall**, mounted on the back. That is a
  much bigger part than the B1212S it replaces. Its footprint is placed but the
  enclosure clearance underneath is not verified.
- **C32/C33/C36/C37 are SMD aluminium cans**, 5.3 and 6.6mm square, standing
  5.4 and 6.0mm. (`C29` was one of these until 2026-09-18 and is now an 0805.) Same unverified-height family as the OLED standoff question.
- ~~**The USB-C mouth must reach the top edge.**~~ **Settled 2026-09-20, and it
  did not** — the mouth sat 6.67mm behind the wall's outer face and no cable
  could have reached it. The top edge now steps out 7.00mm over J11 on a
  17.50mm step out to the right edge, and the mouth is 0.33mm proud of the wall. Geometry, the slot the
  wall needs and the assembly order are in `design-state.md`. The render, not
  the arithmetic, is what settled it.
