# Review packet — checking `netmap.json` against the sources

## Why this exists

`netcheck.py` proves the schematic matches `tools/netmap.json`. Nothing proves
`netmap.json` matches reality. The verified region of the toolchain starts at
`netmap.json` and runs rightward:

```
datasheet -> footprint pad numbers -> kpins.json (pin no. -> pin name) -> netmap.json
                                                                            |
                            [machine-verified from here] -> schematic + PCB -> fab
```

Everything left of `netmap.json` is a human assertion with no checker. On
2026-09-10 that gap produced a fatal defect: **U8 was wired to the 78L05's
pinout while carrying an AMS1117-5.0.** The part had been swapped on 2026-09-07
and the pin map never followed. The regulator's ground pin was driven by the 5V
rail, its output shorted to ground, and the tab — also VOUT, and the thermal
path — left floating. `P5V_BBD` would never have come up, taking U101/U201,
U104/U204 and the V3205SD pair with it. The schematic matched `netmap.json`
perfectly; both were wrong together.

This document is the index for a second pass over that gap.

## Licensing — decided 2026-09-10, do not reopen

The Bergman LPG drawing carries **"not for commercial use!"** in its own
bottom-right corner, and `lpg-bergman.md` records that "he invites builds"
covers DIY and is not the same permission as a repo planning JLC assembly and
EU sales.

**Dylan has assessed this and ruled the LPG block his own design**, on the
grounds that it is adapted to stereo and does not use the full both-mode
circuit. His drawing is therefore kept in `reference/` as a working source.
This is a settled call — a reviewer should not re-raise it. The
modularsynthesis.com Buchla 292 source Bergman redrew from remains the
fallback if the question is ever revisited.

## Coverage

| Block | Parts | Design intent | Source schematic | Datasheets |
|---|---|---|---|---|
| BBD | V3205SD ×2, CD4046B ×2, TL072 ×6, 1N4148W ×10 | `bbd-mki.md` (814 lines, full net inventory) | `BBD_MANUAL_250228.pdf`, in repo | CD4046B, TL072 ✓ · **V3205SD missing** |
| LPG | TL084 ×2, TL074 ×2, VTL5C3 ×4, 3V9 zener ×2 | `lpg-bergman.md` | Bergman drawing in `datasheets/` ✓ | TL074, TL084 ✓ · **VTL5C3 missing** |
| PSU / USB-C | DKM10E-12, AMS1117 ×3, MMBFJ113 ×2, TYPE-C-31-M-12 | `power-usbc-dkm.md` | `reference/V3.0.kicad_sch` ✓ | DKM10 ✓ · **AMS1117, MMBFJ113 missing** |
| Encoder / button IO | MCP23017 ×2 | `pin-allocation.md` | n/a | MCP23017 ✓ |
| Headphone / EXT preamp | OPA1688 ×2 | `design-state.md` | n/a | OPA1688 ✓ |
| Daisy Patch SM | U1 | `design-state.md` | n/a | Patch SM v1.0.5 ✓ + pinout extract |
| MSP430 touch | MSP430FR2675 | `design-state.md`, ADRs 0002–0005 | n/a | 5 docs ✓ |

PDFs live in `datasheets/` and are **gitignored** — run
`datasheets/fetch-datasheets.sh` to populate. Fourteen fetch cleanly; four
vendors 403 every scripted request and are listed at the end of that script for
manual download.

## Already verified

| What | Result | How |
|---|---|---|
| U7 DKM10E-12 pinout | **clean** — 1=+Vin, 2=−Vin, 3=+Vout, 4=Common, 5=−Vout, 6=R.C. | official Mean Well SKM10/DKM10 spec |
| U7 pin 6 left open | **correct** — "Power ON: R.C. ~ −Vin >5.5~75Vdc *or open circuit*" | same |
| U7 input range | **correct** — E suffix is 4.7~9Vdc, VBUS is 5V | same |
| U3/U4 MCP23017 pinout | **clean** — VDD/VSS/SCL/SDA/A0–A2/RESET all correct, GPA/GPB mapping correct | Microchip DS20001952C |
| U3/U4 I2C addresses | **distinct** — 0x20 and 0x21 | A0–A2 strapping |
| Power/ground pin semantics, all 309 parts | **1 defect found** (U8), since fixed | `boardcheck.py` pin-name vs net |
| PSU input stage vs its source | **clean** — DKM pinout, CC pulldowns, fuse all match; one omission (no TVS) since fixed as `D3` | `schnet.py` netlist of `V3.0.kicad_sch` |
| LPG vs Bergman's drawing, **both channels** | **clean** — channels structurally identical; `R12`/`R16` absent by decision, BOTH+VCF only | node-by-node diff, 2026-09-11 |
| Polarity, all 14 polarised parts | **clean** — D103–D106 clamp pairs, zener shunts, D1/D2 bipolar indicator | inspection vs netmap |
| Board ↔ schematic parity | 942/942, 0 unintended | `netcheck.py`, `boardcheck.py` |

## Not verified — what a second pass should cover

1. **U7 pin *coordinates*.** The pinout is confirmed but the footprint is named
   `PWRM-TH_DKMW30F-12` while the part is a DKM10E-12. Body outline is
   1.000"×1.000", which matches the datasheet's "1"x1" Package", and pads sit on
   a 0.800"×0.800" grid — but the per-pin x positions are irregular
   (−0.4/−0.1/+0.1 on one row, −0.4/0.0/+0.4 on the other) and the datasheet's
   mechanical drawing uses an embedded subset font whose dimension text will not
   extract. Check against the drawing by eye. Through-hole and hand-soldered, so
   a physical part can settle it.
2. **V3205SD pinout** (U101/U201) — the BBD itself, the core of the instrument.
   Datasheet not obtainable by script.
3. **VTL5C3 pinout** (VT301/VT302/VT401/VT402) — 4-pin vactrol, LED pair vs
   photoresistor pair orientation.
4. **MMBFJ113 pinout** (Q1/Q2) — SOT-23 JFET, gate/drain/source assignment.
5. **AMS1117** (U5/U6) — U8 is now verified by having been fixed; U5/U6 carry the
   same symbol and pass the semantic check, but confirm against the datasheet.
6. ~~**The LPG against its source**~~ — **done 2026-09-11.** Diffed node by node
   against Bergman's drawing, both channels, which are structurally identical.
   Everything matches including the three easy misreads (`C8` returning to
   `U1-D`'s output, the LED loop closing after `R6`, `R5` parallel with the
   `C5`+`R4` series pair). `R12`/`R16` are absent on both channels **by
   decision** — this build is BOTH and VCF only, no VCA. Do not re-raise it.
7. ~~**The PSU against its source**~~ — **done 2026-09-10.** `V3.0.kicad_sch`
   arrived and was diffed with `schnet.py`. U7 matches pin for pin and also
   matches the Mean Well spec independently. The one omission, a missing TVS on
   VBUS, is fitted as `D3`. Note the scope limit: that covers the **input**
   side. The ±12V output filtering has no counterpart in the reference, which
   drives Eurorack headers; it comes from the EasyEDA extraction instead,
   generated by `edapower.py` at 57/57 pin-nets.
8. **TL084 vs TL074** — U301/U401 are TL084, U302/U402 are TL074. Faithful to
   Bergman as-is; consolidating to TL074 is an open option, not a defect.

## Tooling available to a reviewer

- `hardware/kicad/tools/boardcheck.py` — connectivity, per-netclass clearance,
  board↔schematic parity. Calibrated against a real KiCad `DRC.rpt` and agrees
  with it exactly. Its docstring lists six ways this check was wrong before it
  was right; read it before trusting a new variant of it.
- `hardware/kicad/tools/netcheck.py` — schematic vs `netmap.json` via KiCad's
  own netlister. Proves consistency, **not** correctness.
- `hardware/kicad/tools/netmap.json` — 309 refs, 942 connections, 219 nets.
  The intent file. This is the thing under review.
- `hardware/kicad/tools/kpins.json` — symbol pin number → pin name. The layer
  that silently broke U8.
