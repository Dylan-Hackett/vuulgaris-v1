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
| F1 | `ASMD1812-200` | 2.0A resettable PTC, 1812 |
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

1. **No reverse-polarity diode and no TVS.** Correct — a USB-C receptacle cannot
   be reverse-polarised, so the Schottky the barrel design needs is not needed
   here. That also removes its 0.4V drop.
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

Transcribed into `hardware/kicad/tools/netmap.json` and verified 217/217 by
`tools/netcheck.py` against `kicad-cli`'s netlist. Designators are renumbered to
fit this project's sequence:

| here | EasyEDA | part | LCSC |
|---|---|---|---|
| J11 | USBC1 | TYPE-C-31-M-12 | C165948 |
| F1 | F1 | ASMD1812-200 PTC 2A | C135364 |
| C28 | C105 | 10nF 0603 NP0 | C389113 |
| R22, R23 | R438, R439 | 5.1k 0603 | C122969 |
| C29 | C81 | 22uF 50V SMD can | C72505 |
| C30 | C82 | 1uF 0805 | C91185 |
| C31 | C100 | 100nF 0603 | C327087 |
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

### Open, and not yet checked

- **U7 is 25.4mm square and about 10mm tall**, mounted on the back. That is a
  much bigger part than the B1212S it replaces. Its footprint is placed but the
  enclosure clearance underneath is not verified.
- **C29/C32/C33/C36/C37 are SMD aluminium cans**, 5.3 and 6.6mm square, standing
  5.4 and 6.0mm. Same unverified-height family as the OLED standoff question.
- **The USB-C mouth must reach the top edge.** Seed position only; the rotation
  and the overhang need `gerbercheck.py` and a render, not arithmetic. That
  exact class of reasoning has been wrong here three times.
