# Stereo low pass gate — Eddy Bergman's Buchla 292

Transcribed 2026-09-04 from **"RESONANT LOPASS GATE (BASED ON BUCHLA 292)",
schematic redrawn by Eddy Bergman**, 4500 x 4500 JPEG from
[eddybergman.com part 35](https://www.eddybergman.com/2020/10/synthesizer-build-part-35-resonant.html).
Raster, not vector — so unlike the BBD there is a hard resolution floor, but at
4500px the values and junctions read cleanly at 60% zoom.

## Licensing — read before this goes anywhere near a product

The drawing carries **"not for commercial use!"** in its own bottom-right corner.
`design-state.md:248` records the design as "free, he invites builds", which is
true of DIY, and §6 already notes that redrawing it is "the right move IP-wise".
Those are not the same permission. This repo also contains plans for JLC
assembly and EU sales. If this is ever sold, work from the **modularsynthesis.com
Buchla 292 source Bergman says he redrew from**, not from his drawing.

## What it is

Two vactrols per channel whose LDRs sit in the audio path, driven by a common
LED string. A 3-position mode switch reconfigures the same LDR pair as a VCA, a
2-pole resonant low pass, or both at once. `U1` is a TL084 (four sections),
`U2` a TL074 doing the CV mixing.

## Audio path, one channel

```
AUDIO IN ─ C6 1uF ─┬─ R9 100K ─ GND
                   ├─ R10 100K ─ GND
                   └─ U1-A pin 3 (+)
    U1-A pin 2 (−) ─┬─ R11 15K ─ pin 1 (out)
                    └─ R12 15K ─ [S1/S2] ─ GND     gain 2 with the contact made,
                                                    1 with it open
    pin 1 ─ LDR1 ─┬─ LDR2 ─┬─ R16 10K ─ [S3/S4] ─ GND
                  │        └─ U1-C pin 10 (+) ─┬─ C9 1nF ─ GND
                  │                            └─ R13 4M7 ─ GND
                  ├─ C7 220pF ─ GND
                  └─ C8 4.7nF ─ [S5/S6] ─ U1-D pin 14 (out)

    U1-C pin 9 (−) ─ R14 10K ─ pin 8 (out)         unity buffer
    pin 8 ─ R15 1K ─ AUDIO OUT
    pin 8 ─ U1-D pin 12 (+)
    U1-D pin 13 (−) ─ C10 22pF / RESONANCE 100K / R18 100K
```

**`U1-C` is the output buffer and `U1-D` is the resonance amplifier** — not the
other way round, which is the easy misreading. The LDR chain feeds `U1-C`'s
**non-inverting** input directly; `C9` 1nF and `R13` 4M7 sit on that node. `U1-C`
buffers to the output *and* drives `U1-D`, whose output returns through `C8` into
the **junction between the two LDRs** — the mid-node of the two-pole filter,
which is where resonance feedback belongs. RESONANCE sets how much comes back.

### Careful: the drawing uses "S1" for two different things

Bergman labels the **mode switch's first lug** `S1` (the red dot by `R12`) *and*
the **DEEP toggle** `S1 DEEP on/off`. They are unrelated parts. Everywhere below,
`S1`-`S6` mean mode-switch lugs only; the DEEP toggle is not fitted (see LED
drive).

### The mode switch is the whole trick

The table on the drawing is captioned **"Bottom view of toggle switch"** — it is a
**lug map, not a list of closed contacts**, and misreading it that way inverts the
whole circuit. In a 3PDT toggle the middle row of lugs is the three commons, so
**S2, S4 and S5 are commons**, and on an ON-OFF-ON the centre lever position
connects them to nothing.

| lever | contacts made | circuit |
|---|---|---|
| **VCA** | S2-S1, S4-S3 | `R12` grounded (gain 2), `R16` grounded. LDRs plus `R16` are a defined divider, response stays flat. `C8` open |
| **BOTH** (middle = OFF) | **none** | `R12`, `R16` and `C8` all open. The LDRs feed only `C7`, so the series photoresistance drops level and corner frequency **together** |
| **VCF** | S5-S6 | `C8` into the LDR1/LDR2 junction — 2-pole resonant lowpass |

**BOTH is not a combination of the other two.** It is the bare behaviour of a
photoresistor in series with a capacitor, with the switch removed from the
circuit entirely — which is the actual Buchla lowpass-gate character. VCA and VCF
are each a *modification* of it: `R16` pins the response flat, `C8` plus
resonance makes it a filter.

**Consequence for the switch part.** Poles 1 and 2 always act together, so there
are only **two** control signals — "ground `R12` and `R16`" and "connect `C8`" —
not three, and the middle position switches nothing. Stereo therefore needs
**four switched connections**, which is a quad analog switch, not the 6P3T panel
toggle this otherwise implies.

## LED drive — verified 2026-09-04 at 1.7x

`U1-B` is an **inverting** amp: pin 5 (+) runs left and straight down to `R8` 10K
to ground, **crossing `R5`'s line with no junction dot** — checked at high zoom,
and reading that crossing as a connection would turn the stage into a follower.

Its inverting input is the summing node, and OFFSET and CV arrive there
differently:

```
OFFSET pot wiper ─ R3 150K ─┬──────────── U1-B pin 6 (−)      [same node]
                            ├─ R5 100K ──────────┐
                            └─ C5 2nF ─ R4 470K ─┴─ CV in (U2-C output)
```

`C5` and `R4` are in **series with each other** and that pair is in **parallel
with `R5`** — both between the summing node and the CV node. At DC `C5` blocks,
so the CV sees 100K. Above about 170Hz it shorts and the branch becomes `R4`
470K in parallel with `R5`, i.e. 82.5K, giving the CV path roughly **1.2x more
gain at high frequency**. That is deliberate: it sharpens envelope transients to
compensate for how slow a vactrol is.

### Two feedback paths, not one

```
pin 6 ─┬─ Tp2 500K trim ──────────────────────────── pin 7 (out)   [S1 removed]
       └─ Tp1 20K trim ─ R7 33K ─┬─ LED node
                                 ├─ R17 100K ─ GND
                                 └─ D1 3.9V zener ─ GND
   pin 7 ─ R6 470R ─ LED node ─ the two vactrol LEDs in series
```

The main loop closes from the **LED anode node, after `R6`** — so the amp
regulates the voltage across the LED string rather than its own output, which is
what makes the drive behave consistently as the LEDs warm. `Tp1` sets that
depth. `Tp2` adds a second feedback path taken straight from the output,
changing overall gain.

**Neither `S1` "DEEP" nor `Tp2` is fitted — decided 2026-09-04.** Bergman
describes DEEP as making the sound "deeper with less high tones… the effect of
turning the Offset knob counterclockwise, amount set by `Tp2`". Mechanically it
adds a second feedback path from pin 7 straight to the summing node, bypassing
the LEDs, so part of the feedback stops depending on the LED node and the LED
node has to move less to balance. Less light, gate sits more closed — an
operating-point shift, not a filter change.

With the switch permanently open that path never exists, so **`Tp2` has nothing
to do and is not fitted either.** `RT302`/`RT402` removed. `Tp1` (`RT301`/`RT401`)
stays: it is in the main loop and is still the LED-drive depth trim.

## CV section — `U2` TL074

`CV1 IN` through a **Level 100K** pot into `R27`/`R28` 100K; `CV2 IN` through a
**Level + Invert 100K** pot into `R23` 100K at `U2-A` (`R20` 100K feedback).
`U2-D` (12/13/14, `R30` 100K feedback) sums, `R31` 100K feeds `U2-C` (10/9/8,
`R33` 100K feedback), whose output runs back to the `R4`/`R5` summing node in the
LED driver. **`U2-B` is unused.**

## Adaptation — decided 2026-09-04

**Rails: ±12V, unchanged.** Bergman runs ±15V. Accepted as-is; the LED drive
range, the `D1` 3.9V clamp point and the `R6` 470R current all shift slightly and
the trimmers (`Tp1` depth, `Tp2` gain) absorb it. Set them on the bench.

**Three panel pots, dual-gang, one knob per stereo pair:**

| | Bergman | here |
|---|---|---|
| `RV1` **CUTOFF** | OFFSET 100K | sets the standing LED drive — how open the gate rests |
| `RV2` **RESONANCE** | RESONANCE 100K | unchanged |
| `RV3` **CV AMOUNT** | CV2 "Level + Invert" 100K | bipolar attenuverter on `LPG_ENV` |

This settles the `values.json` vs `pin-allocation.md:408-410` disagreement in
favour of `values.json`. **`pin-allocation.md` is now stale** and should be
updated to match.

**CV1 is dropped entirely** — its jack, its Level pot, and `R27`. `LPG_ENV` from
the Daisy's CV_OUT_1 is the only control voltage.

### Dropping CV1 frees a whole op-amp package

With `R27` gone, `U2-D` has a single input, so `U2-D` + `U2-C` are two cascaded
unity inverters — a buffer. Per channel `U2` needs only **`U2-A`** (the
attenuverter's inverter) and **one summing/buffer stage**, so:

- 2 sections per channel, 4 for stereo
- **one TL074 covers both channels** instead of two
- `U2-B` was already marked "not used" on the drawing

### Mode switch

Mechanically a 3PDT ON-OFF-ON, and `SW1` here is a DPDT which cannot do it. Per
the switch reading above the circuit needs only **two control signals** and
**four switched connections** for stereo, so a quad analog switch would cover it
from one plain panel toggle — `DG419DY-T1-E3` is in `lib/vuulgaris.kicad_sym`
and commit 6724750 took that route once.

**Superseded 2026-09-11: VCA was dropped, so this is moot.** Two modes need two
switched connections, one per channel, and the DPDT does that directly. See
*VCA mode is deliberately not implemented* above.

### Vactrols — still open

Four needed, matched in on-resistance and decay across L and R. Excelitas
discontinued the line; the Xvive reissue reportedly has a brighter LED and longer
release. `design-state` §6 also carries an **unverified RoHS/cadmium** question.
No symbol or footprint in `lib/` yet.

## Checked against the drawing — 2026-09-11, both channels

`datasheets/` now holds Bergman's schematic image. `netmap.json` was diffed
against it node by node, L and R. **The two channels are structurally identical**
— every node below has the same membership on both sides, so nothing is a
one-channel typo.

Matching, and including the three things this drawing is easy to get wrong:

| node | agrees |
|---|---|
| input | `C6` → `R9`‖`R10`‖`U1-A` pin 3 |
| `U1-A` | `R11` 15K feedback |
| vactrols | LEDs in series off `R6`; LDRs in series in the audio path |
| LDR mid-node | `C7` 220pF to GND |
| **`C8` 4.7nF** | mid-node → switch → **`U1-D` output**, not to ground — the resonance injection |
| LDR2 out | `C9` 1nF and `R13` 4M7 to GND, into `U1-C` pin 10 **(+)** |
| `U1-C` | `R14` unity buffer, `R15` to output, and it drives `U1-D` pin 12 |
| `U1-D` | `C10` 22pF, RESONANCE, `R18` |
| **LED drive** | `Tp1`→`R7` to the LED node, `R17`+`D1` there, and the loop closes **after `R6`** |
| **offset/CV sum** | `R5` 100K in parallel with the `C5`+`R4` *series* pair |
| CV chain | `U2-A` inverter, `RV3` attenuverter, `U2-D`→`U2-C` cascade |
| `U2-B` | unused, pin 5 to GND, pins 6/7 tied — as drawn |

Zero dangling nets anywhere in the block.

Deviations that are deliberate and recorded above: CV1 and `R27` dropped, `Tp2`
and the DEEP switch not fitted, ±12V rails instead of ±15V.

### VCA mode is deliberately not implemented — decided, do not re-raise

**This instrument ships BOTH and VCF only.** Confirmed 2026-09-11. `R12` and
`R16` are on Bergman's drawing and on neither channel here, and that is the
intended design, not an omission:

- `R12` 15K, `U1-A` pin 2 → [S1/S2] → GND. Omitted, so `U1-A` is a unity
  follower. Bergman would get **gain 2** from it in VCA.
- `R16` 10K, LDR2 output → [S3/S4] → GND. Omitted, so nothing pins the response
  flat — which is the whole point of VCA mode.

`SW1` compounds it. It is a DPDT using pins 1/2 and 4/5 only, so each pole is
ON-OFF rather than ON-ON, and the one thing it switches is `C8`:

| `SW1` | result | Bergman equivalent |
|---|---|---|
| closed | `C8` → `U1-D` out | **VCF** — resonant 2-pole |
| open | `C8` floating | **BOTH** — bare LDR + `C7` |

That is exactly the wanted behaviour. **BOTH is the actual Buchla lowpass-gate
character** — series photoresistance dropping level and corner frequency
together — and VCF is the resonant variant. VCA, the mode that pins the response
flat and turns the thing into a plain amplifier, is the one worth losing.

Dropping it also simplifies the hardware rather than compromising it. The
three-mode circuit needs four switched connections for stereo, which is why
*Mode switch* below reached for a `DG419DY-T1-E3` quad analog switch. Two modes
need **two** connections — one per channel — so a plain DPDT panel toggle is not
a compromise here, it is the correct part. `SW1` is already wired that way,
using pins 1/2 and 4/5 so each pole is ON-OFF.

**The DG419 proposal is therefore moot and should not be implemented.** Anyone
restoring VCA would need the quad analog switch *and* four resistors
(`R312`/`R412`, `R316`/`R416`), and that is not on the roadmap.

## Interface this has to present

| net | direction | currently |
|---|---|---|
| `AUDIO_OUT_L` / `_R` | Daisy → LPG in | only on `U1.B2`/`U1.B1` |
| `BBD_IN_L` / `_R` | LPG out → delay | only on `R106`/`R107`, `R206`/`R207` |
| `LPG_ENV` | Daisy CV_OUT_1 → LED drive | only on `U1.C10` |
| `RV1` `RV2` `RV3` | panel, dual-gang | **placed, zero pins wired** |
| `SW1` `SW2` | panel | **placed, zero pins wired** |

## Status — in netmap and VERIFIED 2026-09-04

**748/748 connections verified, 0 unintended, 189 nets, `netcheck` exits 0.**
netmap went 169 refs / 524 connections -> **245 / 748**.

**Built exactly as the drawing shows, per channel, with CV1 removed and nothing
else reasoned away.** 14 op-amp sections, four packages:

| | |
|---|---|
| `U301` / `U401` | Bergman `U1`. A input buffer, B LED driver, C output buffer, D resonance |
| `U302` / `U402` | Bergman `U2`. A attenuverter inverter, D summer, C output inverter, **B unused with pin 5 to GND and 6 tied to 7, as drawn** |
| `VT301/302`, `VT401/402` | four VTL5C3 |
| `RT301` / `RT401` | `Tp1` 20K LED-drive depth trim, one per channel. `Tp2` not fitted |

`RV1` CUTOFF, `RV2` RESONANCE, `RV3` CV AMOUNT and `SW1` had **zero pins wired**
before this and are now connected. `SW1` pole A switches `C308`, pole B `C408` —
open is BOTH, closed is VCF.

**Removed, all by explicit decision and not by inference:** the CV1 jack, its
Level pot and `R27`; the DEEP switch and `Tp2` with it; and
`R12`/`R16`, because only BOTH and VCF modes are wanted so the VCA contact is
never made.

### Still to do

- **F8** to pull the footprints onto the board, then place.
- The **3V9 zener** is a generic `Device:D_Zener` on a SOD-123 land — pick a real
  part before ordering.
- **Vactrol pair-to-pair spacing** in `VACTROL-TH_VTL5C3` is 12.7mm, a layout
  choice not a package dimension; the 5.08mm within each pair is from the
  datasheet and is fixed.
- **Match the four vactrols** on on-resistance and decay, L against R.
- With `R16` unfitted the LDRs work into `R13` 4M7, so at full dark the gate
  reaches about **-14dB**, not silence — the "vactrol bleed" of `design-state` §6.
