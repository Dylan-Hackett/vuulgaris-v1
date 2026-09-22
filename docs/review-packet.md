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
| BBD | V3205SD ×2, CD4046B ×2, TL072 ×6, 1N4148W ×10 | `bbd-mki.md` (814 lines, full net inventory) | `BBD_MANUAL_250228.pdf`, in repo | CD4046B, TL072 ✓ · V3205SD pinout from the manual |
| LPG | TL084 ×2, TL074 ×2, VTL5C3 ×4, 3V9 zener ×2 | `lpg-bergman.md` | Bergman drawing in `datasheets/` ✓ | TL074, TL084, VTL5C3 ✓ |
| PSU / USB-C | DKM10E-12, AMS1117 ×3, MMBFJ113 ×2, TYPE-C-31-M-12 | `power-usbc-dkm.md` | `reference/V3.0.kicad_sch` ✓ | DKM10, MMBFJ113, AMS1117 ✓ |
| Encoder / button IO | MCP23017 ×2 | `pin-allocation.md` | n/a | MCP23017 ✓ |
| Headphone / EXT preamp | OPA1688 ×2 | `design-state.md` | n/a | OPA1688 ✓ |
| Daisy Patch SM | U1 | `design-state.md` | n/a | Patch SM v1.0.5 ✓ + pinout extract |
| MSP430 touch | MSP430FR2675 | `design-state.md`, ADRs 0002–0005 | n/a | 5 docs ✓ |

PDFs live in `datasheets/` and are **gitignored** — run
`datasheets/fetch-datasheets.sh` to populate. 35 fetch cleanly; only the
CoolAudio V3205SD sheet 403s, and the MN3205 original covers that pinout.
`datasheets/REVIEW-INDEX.md` maps every reference designator to its datasheet
and every block to its source schematic.

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
| LPG vs Bergman's drawing, **both channels** | **one defect, since fixed** — the LED drive was inverted (see `lpg-bergman.md`). The rest is clean; `R12`/`R16` absent by decision, BOTH+VCF only | node-by-node diff 2026-09-11, drawing re-read at full resolution 2026-09-16 |
| 3.5mm jacks `J2`–`J6` | **clean** — the datasheet's plug gauge numbers the sections 1 sleeve, 2 ring, 3 tip, matching the contact numbers | SOFNG PJ-376 drawing |
| DPDT `SW1`/`SW2` | **clean** — commons on 2 and 5, throws 1/3 and 4/6 | Dailywell 2MDP0428 |
| `AMS1117` `U5`/`U6`/`U8` | **clean** — 1 = GND/ADJ, 2 = VOUT, 3 = VIN, tab = VOUT | Advanced Monolithic ds1117 |
| `U101`/`U201` V3205SD **footprint geometry** | **clean** — 2.54mm pitch, 7.62mm row spacing, 15.24mm pin 1 to pin 4, body 19.2 x 6.4mm, middle three DIP-14 positions omitted per side, pin 1 top-left counterclockwise, rect pad plus a silk notch at the pin-1 end | Panasonic MN3205 package drawing, p1 | 
| `U7` pad **coordinates** | **clean** — the irregular 0.3"/0.2" top row against a 0.4" bottom row is what the drawing specifies, and the pads match, 0.8" between rows | Mean Well mechanical spec p5 |
| Polarised parts vs package drawings | **clean** — silkscreen "+" lands on pad 1 on every electrolytic, read off a board render | 2026-09-16 |
| Encoders, trimmers | **clean** — ALPS A/common/B plus switch; Bourns 1 = CCW, 2 = wiper, 3 = CW | ALPS + Bourns drawings |
| BBD vs the manual's own BOM, **both channels** | **clean** — all 27 R and 22 C accounted for, channels symmetric, the three crossings unshorted | text extracted from `BBD_MANUAL_250228.pdf` |
| BBD vs the **schematic drawing** | **clean** — every value and node checked. The previously recorded `R120` 62k vs 56K mismatch is **withdrawn**: the manual's schematic is vector (p61, KiCad 5.1.5 export) and reads `R20 62k` at 10x | re-read from the vector source, 2026-09-16 |
| V3205SD, VTL5C3, MMBFJ113 pinouts | **all three clean** — see items 2-4 below | manual p25, Xvive package drawing, onsemi Rev 5 drawing |
| Polarity, all 14 polarised parts | **clean** — D103–D106 clamp pairs, zener shunts, D1/D2 bipolar indicator | inspection vs netmap |
| Board ↔ schematic parity | 942/942, 0 unintended | `netcheck.py`, `boardcheck.py` |

## Open defects — found 2026-09-16, must be fixed before ordering

1. **`SW4`–`SW9`, all six buttons are shorted out.** The TS1103S drawing joins
   pins 1–2 internally and 3–4 internally, with the contact between those pairs.
   The footprint's pads 1+2 are the 12.5mm-apart pair and 3+4 the other, which is
   forced by the hole pattern regardless of anyone's numbering convention. We
   wired BTN to 1+3 and GND to 2+4, so each terminal carries both nets. Every
   button reads permanently pressed. **Not yet fixed.**
2. **`RV1`–`RV6` are the wrong value.** The BOM buys `C380211` =
   `RK09L1240A12`, which the ALPS datasheet gives as **10kΩ**. The design needs
   **100kΩ**: `lpg-bergman.md` specifies 100K for OFFSET, RESONANCE and CV
   Level; the BBD manual specifies 100k for DRY/WET; and the TIME divider's own
   arithmetic in `bbd-mki.md` (10.17V at full CCW, 36k at centre) only comes out
   at 100k. At 10k the TIME knob's sweep collapses. **Needs a part that JLC
   stocks.**
3. **`J7`–`J10`, the 1/4" jacks — unresolved, needs a meter.** Neither
   manufacturer drawing labels the contacts. The cross-section implies pad 2 =
   sleeve, pad 3 = ring, pads 4/5 = tip and its normalling switch, which is how
   we wired it, but nothing rules out pad 3 being the tip. If it is, a mono plug
   shorts every output to ground. Beep out one physical jack before ordering.

### Connector and module pinouts — checked 2026-09-21

Four blocks had never been diffed against their datasheets. Three are clean;
the fourth cannot be checked yet because the thing it mates with does not exist.

**`U1` Daisy Patch SM, 28 of 40 pins — clean.** Diffed pin by pin against
Electrosmith Table 2 (Pin Functions), cross-checked against Table 3. 26 direct
matches. The SPI2 group is self-consistent — CS on D1, SCK on D10, MOSI on D9's
`SPI2_MOSI` alternate. UART direction is right: the MSP's TX lands on A2, whose
alternate is `UART4_RX`, and A3 (`UART4_TX`) drives the MSP's RX. Both CV
outputs sit on the only two output-capable CV pins, C1 and C10, and `CV_IN_JACK`
sits on C9, which is input-only.

Two pins are repurposed, both deliberate and both recorded in
[ADR 0009](decisions/0009-io-plan-12-adc.md):

| pin | datasheet | ours | depends on |
|---|---|---|---|
| A9 | `USB_DP` | `OLED_RES` | no panel USB, which ADR 0009 decides |
| D2 | `SDMMC1_D3` | `OLED_DC` | 1-bit SD, so D1/D2/D3 are free |

ADR 0009 carries a standing action on the first of these — *"verify A9 drives
the display cleanly, the module may carry ESD or filtering on the USB_HS
lines."* Still open, but the risk is much smaller than when it was written:
the ADR was contemplating putting **MOSI** on A9, and A9 now carries **RES**,
which is a static level toggled once at init rather than a clocked signal.

**`J1` microSD, 10 pins — clean.** The vendor drawing's own table gives
1 `DAT2`, 2 `CD/DAT3`, 3 `CMD`, 4 `VDD`, 5 `CLK`, and the rest follow the SD
standard. Ours uses 3/4/5/6/7 for CMD/VDD/CLK/VSS/DAT0 and leaves 1 (`DAT2`)
and 8 (`DAT1`) open, which is correct for 1-bit. `DAT3` is pulled up through
`R508` rather than driven — correct, it keeps the card out of SPI mode. Shell
tabs 10-13 to GND.

**`DS1` OLED, 8 pins — clean, and it was already documented.** Listing this as
unverified was wrong: [ADR 0006](decisions/0006-ssd1309-oled.md) carries the
full pin table and the FS0/CS2 reasoning, it just never made it into the table
above. `netmap.json` matches the datasheet's section 1.5 exactly, including the
two that are easy to get wrong: **pin 8 `FS0` is the font ROM's data OUTPUT and
is left open on purpose**, and **pin 9 `CS2` is held high through `R505`** so
the font die stays off the shared bus.

**`J12` faceplate IDC, 10 pins — cannot be verified yet.** A 2x5 IDC has no
vendor pinout to diff against; the pinout is ours to define. What is checkable
is checked: the footprint uses the standard convention (odd pins one row, even
the other, 2.54mm pitch, pin 1 at the end), and every signal on the odd row has
a ground directly opposite for its return. It becomes a real check only when the
faceplate board exists to mate with it. **Treat this table as the interface
contract and design the faceplate to it.**

## Not verified — what a second pass should cover

1. ~~**U7 pin coordinates**~~ — **done 2026-09-16.** The Mean Well drawing
   (p5, Bottom View) specifies the top row as 7.62mm then 5.08mm — 0.3" then
   0.2" — against a uniform 10.16mm bottom row, with 20.32mm between rows. The
   footprint matches all of it. The irregular spacing was the part, not a bug.
2. ~~**V3205SD pinout**~~ — **done 2026-09-11.** The manual states it in words on
   p25: *"5 V at pin 5 and ground at pin 1… VGG at pin 8 via a 4k7/56k divider…
   clock 1 into pin 6, clock 2 into pin 2, and our scaled and biased input into
   pin 7"*. All seven match `netmap.json`. The drawing leaves pin 3's stub
   unconnected, which ours does too — the p25 line about "pins 3 and 4" is the
   breadboard stage, the module uses one output. The `DIP-8_SPECIAL` footprint
   is confirmed as a DIP-14 body with the middle three positions omitted per
   side: pads sit on a 0.300" row pitch at 0.100" spacing with a 0.400" gap.
3. ~~**VTL5C3 pinout**~~ — **done 2026-09-11**, against the Xvive/PerkinElmer
   package drawing. Pins **1/2 are the LED** and **3/4 the photocell**, matching
   the footprint's two-leads-per-end geometry, and the drawing's "cathode
   identifier" plus the body's own `+ LED −` marking give **1 = anode,
   2 = cathode**. Our LED chain is forward biased: drive → `VT301`.1→.2 →
   `VT302`.1→.2 → GND. Note there is no manufacturer pin *numbering* on an axial
   part — orientation is by the body marking at assembly, so this is a
   soldering-time risk, not a netlist one.
4. ~~**MMBFJ113 pinout**~~ — **done 2026-09-11**, against the onsemi datasheet
   (Rev 5, 2023) package drawing. On both SOT-23 cases the **gate is the lone
   pin on its side, pin 3**, with D and S as the pair — which is what our symbol
   says (`1=D, 2=S, 3=G`) and how `Q1`/`Q2` are wired. The datasheet also states
   **"Source & Drain are Interchangeable"**, so the D/S order across pins 1 and 2
   is electrically immaterial. A web search had claimed pin 2 was the gate; the
   drawing disproves it.
5. ~~**AMS1117** (U5/U6)~~ — **done 2026-09-16** against the Advanced Monolithic
   datasheet: 3-pin fixed version is 1 = Ground/Adjust, 2 = VOUT, 3 = VIN, and
   "TAB IS OUTPUT". All three regulators match.
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
