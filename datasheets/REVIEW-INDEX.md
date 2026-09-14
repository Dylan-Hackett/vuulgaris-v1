# Review index — everything a second agent needs to check the netlist

One folder, one job: check that every pin in the Vuulgaris V1 schematic is wired
the way its datasheet and its source schematic say. Read
[`docs/review-packet.md`](../docs/review-packet.md) first — it says what has
already been verified, how, and what has not.

The thing under review is **`hardware/kicad/tools/netmap.json`** (309 refs, 942
connections, 219 nets). The schematic and board are machine-checked against it;
nothing checks it against the documents below. That gap is where U8 came from.

## Populate this folder

PDFs are gitignored. On a fresh checkout:

```bash
cd datasheets && ./fetch-datasheets.sh
```

```bash
cp "../docs/BBD_MANUAL_250228 (3).pdf" BBD-mki-manual-250228.pdf
```

```bash
cp ../docs/reference/V3.0.kicad_sch PSU-USBC-reference-V3.0.kicad_sch
```

```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export pdf --output vuulgaris-schematic.pdf ../hardware/kicad/vuulgaris.kicad_sch
```

```bash
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch export netlist --format kicadsexpr --output vuulgaris-netlist.net ../hardware/kicad/vuulgaris.kicad_sch
```

The last two are **generated** — regenerate them if the schematic has changed
since 2026-09-13. The netlist carries 219 named nets plus 51 `unconnected-`
single-pin nets; the 219 are the ones in `netmap.json`.

## Our design

| File | What it is |
|---|---|
| `vuulgaris-schematic.pdf` | the schematic, one sheet |
| `vuulgaris-netlist.net` | KiCad's own netlist of it |
| `../hardware/kicad/tools/netmap.json` | the intent: ref → pin → net |
| `../hardware/kicad/tools/kpins.json` | symbol pin number → pin name — **the layer that broke U8** |
| `extracts/patch-sm-v1.0.5-pinout.md` | Daisy Patch SM pin table, text |

## Source schematics — block by block

| Block | Source | Our intent doc | Refs |
|---|---|---|---|
| BBD delay, both channels | `BBD-mki-manual-250228.pdf` — BOM in text, schematic on p2 as a bitmap | `docs/bbd-mki.md` | U101–U104 + U106, U201–U204 + U206 (no U105/U205), R1xx/R2xx, C1xx/C2xx, D103–D107, D203–D207 |
| LPG, both channels | `LPG Schematic E Bergman (3) (1).jpg` | `docs/lpg-bergman.md` | U301/U302, U401/U402, VT301/VT302, VT401/VT402, R3xx/R4xx, C3xx/C4xx, D301/D401 |
| USB-C input + DKM | `V3.0.pdf` and `PSU-USBC-reference-V3.0.kicad_sch` | `docs/power-usbc-dkm.md` | J11, F1, U7, C28, R22/R23, D3 |
| ±12V filtering | **not in this folder** — `~/Documents/origin2.2.eprj`, the EasyEDA project. Check it with `python3 hardware/kicad/tools/edapower.py` (57/57 pin-nets on 2026-09-13) | `docs/power-usbc-dkm.md` | L1/L2, C29–C39, R24/R25, D1/D2 |
| Encoders, buttons, OLED, SD, Patch SM | no source schematic — datasheets only | `docs/pin-allocation.md` | U1, U3/U4, ENC0–ENC8, SW4–SW9, DS1, J1 |
| Headphone / EXT preamp | no source schematic — datasheets only | `docs/design-state.md` | U9/U10 |

**Decided, do not re-raise:** the LPG is BOTH + VCF only, no VCA (`R12`/`R16`
absent). The Bergman licensing question is closed — see `review-packet.md`.

## Datasheets — by reference designator

| Refs | Part | File |
|---|---|---|
| U1 | Daisy Patch SM | `Electrosmith-Patch-SM-v1.0.5.pdf` |
| U3, U4 | MCP23017 | `Microchip-MCP23017-datasheet.pdf` |
| U5, U6, U8 | AMS1117-3.3 / -5.0 | `AMS1117-datasheet.pdf` |
| U7 | DKM10E-12 | `MeanWell-SKM10-DKM10-spec.pdf` |
| U9, U10 | OPA1688 | `TI-OPA1688-datasheet.pdf` |
| U101, U201 | V3205SD | `Panasonic-MN3205-datasheet.pdf` (the original; image-only scan) + manual p25 |
| U102/U103/U106, U202/U203/U206 | TL072 | `TI-TL072-datasheet.pdf` |
| U104, U204 | CD4046B | `TI-CD4046B-datasheet.pdf` |
| U301, U401 | TL084 | `TI-TL084-datasheet.pdf` |
| U302, U402 | TL074 | `TI-TL074-datasheet.pdf` |
| VT301/VT302, VT401/VT402 | VTL5C3 | `Xvive-VTL5C3-datasheet.pdf` |
| Q1, Q2 | MMBFJ113 | `onsemi-MMBFJ113-datasheet.pdf` |
| J11 | TYPE-C-31-M-12 | `Korean-Hroparts-TYPE-C-31-M-12.pdf` — image-only drawing |
| J1 | TF PUSH microSD | `TF-PUSH-microSD.pdf` |
| DS1 | HS242L01W4S01 OLED module | `HS242L01W4S01-OLED.pdf` — pin table p7 |
| J2–J6 | PJ-376 | `PJ-376-jack.pdf` |
| J7–J10 | PJ-603 | `PJ-603-jack.pdf` — image-only drawing |
| ENC0 | EC11L1525G01 | `ALPS-EC11L1525G01.pdf` — scanned |
| ENC1–ENC8 | EC12E2430803 | `ALPS-EC12E2430803.pdf` |
| SW1, SW2 | Dailywell 2MD1T1B1M2QES (Thonk DW3) | `Dailywell-2MD1T1B1M2QES-DPDT.pdf` |
| SW4–SW9 | TS1103S 12×12 tactile | `TS1103S-12x12-tactile.pdf` |
| D3 | SMAJ6.0A | `SMAJ6.0A-TVS.pdf` |
| D103–D107, D203–D207 | 1N4148W | `1N4148W.pdf` |
| D301, D401 | BZT52C3V9 | `BZT52C3V9-zener.pdf` — image-only |
| D1, D2 | YLED0402Y | `YLED0402Y.pdf` |
| C29, C32, C33, C36, C37 | Lelon RVT electrolytic | `Lelon-RVT-electrolytic.pdf` |
| RV1–RV6 | RK09L1240A12 | `ALPS-RK09L1240A12-pot.pdf` |
| RT301, RT401, RT501–RT504 | 3224W | `Bourns-3224W-trimmer.pdf` |
| faceplate (not on this board) | MSP430FR2675 | `TI-MSP430FR2675-datasheet.pdf` + the SLAA/SLAU docs |

Every file above was opened on 2026-09-13 and confirmed to name its own part.

**No datasheet, by design:** resistors, MLCCs, ferrite beads FB1/FB2 and L1/L2,
the F1 PTC — no pin semantics. **No datasheet, gap:** J12 (2×5 IDC, C5665 —
pin 1 orientation only) and the CoolAudio V3205SD sheet itself (vendor 403s;
the MN3205 original and the manual cover the pinout).

## Worth a reviewer's attention

- **DS1 controller.** ADR 0006 and the firmware plan say SSD1309. The module
  datasheet names SSD1306 once, in a handling-precautions paragraph, and never
  in the electrical section. Its pin table is `1 GND, 2 VCC, 3 SCL, 4 SDA,
  5 RES, 6 DC, 7 CS1, 8 FS0, 9 CS2` — pins 8/9 are an on-module **font chip**,
  not the display. Logic inputs are rated **1.65–3.3V max**; module VCC 3–5V.
  Ours: `2 = P3V3_OLED`, `9 = OLED_FONTCS`, 8 open.
- **Jacks and switches.** Lug-to-function on PJ-376 / PJ-603 and the throw
  pairs on the DPDT (drawing: commons are 2 and 5; `POS.1` connects 2-3, 5-6)
  have never been checked against these drawings. `bbd-mki.md` records one
  switch bug already — `SW_DPDT_x2` shorting both channels' timing caps.
- **Tactile switches.** 4-pin 12×12 parts have internally shorted pairs; a
  switch wired across a shorted pair never switches.
- **Polarised parts** were checked against netmap semantics only, not against
  these package drawings.
