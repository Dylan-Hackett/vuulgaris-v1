# 05: BBD delay, both channels

Block: U101-U104, U106 and the 2xx twins, R1xx/R2xx, C1xx/C2xx, D103-D107 and
D203-D207. SW1/SW2 are checked here too, as the runbook asks.

Sources:

- `docs/BBD_MANUAL_250228 (3).pdf`: p61, the production schematic (KiCad 5.1.5
  vector export, no text layer). Rendered at 500 dpi, rotated upright, read in
  twelve tiles. p3-p5 the kit BOM (text). p59-p60 and p74-p76 for the module's
  description and test points.
- `Panasonic-MN3205-datasheet.pdf` p1-p2 (rendered), `TI-CD4046B-datasheet.pdf`
  (SCHS043B, image pages rendered: p1 terminal assignment, p2 design
  information, p3-p5 electrical characteristics, Fig 4/6/8 zoomed),
  `TI-TL072-datasheet.pdf` (SLOS080W), `Dailywell-2MD1T1B1M2QES-DPDT.pdf` p1.
- `docs/bbd-mki.md` was read only to list what it declares, after the diff.

## Netlist of the manual's schematic, diffed against channel 1

The p61 drawing was transcribed into 36 nets (manual designators), then mapped
onto ours with R*n* -> R1*nn*, C*n* -> C1*nn*, VD*n* -> D1*nn*, VT1 -> Q1,
DA1 -> U102, DA2 -> U103, DA5 -> U106, DA3 -> U104, DD1 -> U101, pots R1/R3/R5 ->
RV4/RV5/RV6 gang A (1 = CCW, 2 = wiper, 3 = CW). A script then asked, for each
manual net, whether all its members sit on one net of ours, and for each of our
`BBD_*_L` nets, whether anything sits on it that the manual does not have.

| manual net (members) | ours | verdict |
|---|---|---|
| input: XS3 tip, R6 100k to GND, R7 1k | `BBD_IN_L`: R106, R107, plus R315 (LPG output) | CLEAN, input source is the LPG by design |
| R7 -> DA1A + | `BBD_INF_L` -> U102.3 | CLEAN |
| node A: DA1A out and -, R4 CW, R5 CCW | `BBD_DRY_L`: U102.1/2, R104, RV6.1 | CLEAN (R4 -> R104, below) |
| R4 wiper -> R14 51k | `BBD_GAIN_L`: R104.2, R114 | CLEAN |
| summing node: R12 82k, R13 47k, R14 51k, R18 10k, DA2A - | `BBD_SUM_L` | CLEAN |
| R13 from -12V | R113 from `NEG12V` | CLEAN |
| DA2A out, R18, DD1 pin 7 (TP3) | `BBD_SIGIN_L` | CLEAN |
| R3 FEEDBACK wiper -> R12; CW = wet, CCW = GND | `BBD_FB_L`: RV5.2; RV5.3 `BBD_WETAC_L`; RV5.1 GND | CLEAN |
| VGG: R19 4.7k from +5V, R20 62k to GND, C10, DD1 pin 8 | `BBD_VGG_L` | CLEAN |
| DD1: 1 GND, 5 +5V, 3 X (open) | U101.1, .5, .3 | CLEAN |
| OUT2 pin 4, R22 100k, C13 | `BBD_RAW_L` | CLEAN |
| C13, R24 100k, DA5A + | `BBD_AC_L` | CLEAN |
| DA5A out and -, VT1, R28 (TP5) | `BBD_SH_IN_L`, Q1.1 | CLEAN |
| R28, VT1 gate, VD7 anode | `BBD_SH_G_L` | CLEAN |
| VT1, C19, DA5B + | `BBD_SH_HOLD_L` | CLEAN |
| DA5B -, R29 22k to GND, R30 100k | `BBD_SH_FB_L` | CLEAN |
| DA5B out, R30, C20 (TP7) | `BBD_WET_L` | CLEAN |
| C20, R32 470 (WET OUT), R3 CW, R5 CW | `BBD_WETAC_L` | CLEAN |
| R5 wiper -> DA2B +; DA2B follower -> R31 470 -> XS5 | `BBD_MIXW_L`, `BBD_MIX_L`, R131 -> `BBD_OUT_L` | CLEAN |
| R25 100k from +12V, R26 10k to GND, DA1B - | `BBD_TRIGREF_L` | CLEAN |
| C16 220pF, R27 6.2k to GND, DA1B + | `BBD_TRIGIN_L` | CLEAN |
| DA1B out (TP6), VD7 cathode | `BBD_TRIG_L` | CLEAN |
| TIME: +12V - R10 22k - R1 CCW; R1 CW - R11 22k - GND; wiper - R15 100k | `BBD_TIMEHI/LO/W_L` | CLEAN |
| VCO in: R15, R16, VD3 (to +5V), VD5 (from GND), DA3 pin 9 (TP2) | `BBD_VCOCV_L` | CLEAN |
| INH: R17 100k, VD4, VD6, DA3 pin 5 | `BBD_INH_L` | CLEAN |
| DA3 pins 4 and 3, DD1 pin 6, C16 (TP4) | `BBD_CLK_L` | CLEAN |
| DA3 pin 2 (PC1 out), DD1 pin 2 | `BBD_CLKN_L` | CLEAN |
| DA3 pin 11 - R23 39k - GND; pin 12 - R21 2.2M - GND | `BBD_VCOR1_L`, `BBD_VCOR2_L` | CLEAN |
| DA3 pins 6/7 via SW1 to C14 1nF (long) or C15 220pF (short) | C114 1nF straight across | CLEAN, declared (long hardwired) |
| DA3 14 and 16 to +5V, 8 GND; 1, 10, 13, 15 X | same | CLEAN |

All 36 manual nets map onto exactly one of ours. The only members on our nets
that the manual does not have: test points TP6/TP8/TP12, R315 (the LPG feeding
`BBD_IN_L`), and three taps on `BBD_OUT_L` (C503 to the resample switch, C505
to the headphone amp, R513 to the line out). Decoupling C105-C108, C121/C122 are
the manual's C5-C8, C21/C22.

### Values against the drawing and the BOM text

The drawing and the manual's own kit BOM (p3-p5) agree with each other: 27
resistors (2M2, 100k x9, 82k, 62k, 51k, 47k, 39k, 22k x3, 10k x2, 6k2, 4k7, 1k,
470 x2, 10 x2) and 22 capacitors (47u x2, 3.3u x2, 1u x2, 15n, 100n x12, 1n,
220p x2), and pots 100k A (R2), 100k B x3 (R1, R4, R5), 10k B (R3). Every
resistor in channels 1 and 2 matches its drawing value (R106-R132, R206-R232).
Capacitors:

| manual | value on drawing | ours (both channels) | status |
|---|---|---|---|
| C9, C11, C5-C8, C21, C22 | 0.1 uF | 100 nF X7R | CLEAN |
| C10 | 3.3 uF x 16 V, polarised | C110/C210 **10 uF** X5R 0805 | declared (bbd-mki.md BOM table); harmless, a bigger VGG reservoir |
| C13, C20 | **1 uF, Film** | C113/C120/C213/C220 **1 uF X7R** (`CC0805KKX7R9BB105`) | **DEFECT** against bbd-mki.md, below |
| C14 | 1 nF | C114/C214 1 nF C0G | CLEAN |
| C16 | 220 pF | C116/C216 220 pF C0G | CLEAN |
| C19 | 15 nF, Film | C119/C219 **10 nF C0G** | declared (mkbom CURATED; stock) |

## Channel 2 against channel 1

Every 1xx ref has a 2xx twin and vice versa. Renaming 1xx -> 2xx and `_L` ->
`_R`, all pins land on the corresponding net and all values match: **zero
differences**. The only nets BBD parts share across channels are `POS12V`,
`NEG12V`, `P5V_BBD`, `GND`, `TIME_CV` (one time CV for both, by design) and
`GATE_OUT_2` (one inhibit for both). No signal net crosses channels. The pots
put channel 1 on pins 1-3 and channel 2 on 4-6 of RV4/RV5/RV6, consistently.
**CLEAN.**

## Deviations bbd-mki.md declares, checked as built

| declared | as built | verdict |
|---|---|---|
| R4 IN GAIN pot -> fixed `R104`/`R204`, seeded 0R, "OPEN" | 0R, DRY to GAIN | implemented. Still open (level unknown) |
| TIME CV jack and A100k attenuator -> Daisy `CV_OUT_2` | R116/R216 from `TIME_CV` | implemented |
| INHIBIT jack -> Daisy `GATE_OUT_2` | R117/R217 from `GATE_OUT_2` | implemented |
| TIME RANGE switch removed, long mode hardwired | C114/C214 1 nF on pins 6-7 | implemented |
| WET OUT: R132/R232 kept, no jack | single-pin nets (section 1) | implemented |
| 78L05 -> AMS1117-5.0 | U8 | implemented (section 2) |
| C10 3.3 uF -> 10 uF | 10 uF | implemented; but bbd-mki.md's prose (line 95 diagram, line 181) still says "C110 3.3uF" |
| C19 15 nF film -> C0G | **10 nF** C0G | implemented as 10 nF per mkbom; bbd-mki.md lines 110, 357, 367, 839 still say 15 nF |
| C13/C20 "film ... deliberate and should not be substituted with X7R" (bbd-mki.md line 189-192, 789-791) | **X7R** | **not implemented** |

Undeclared differences: none found beyond the above.

## Electrical checks

### MN3205 / V3205

- Supply: VDD = 5 V from U8; MN3205 operating 4-9 V, absolute -0.3 to +11 V
  (p2). CLEAN.
- VGG: 5 x 62/(4.7 + 62) = **4.648 V** against "VGG = 14/15 VDD" = 4.667 V
  (p2 electrical-characteristics conditions). 0.4% low. CLEAN.
- Clock amplitude: CD4046B outputs 0.05 V max low, 4.95 V min high driving CMOS
  (p3), against VCPH = VDD and VCPL 0-0.5 V. CLEAN on amplitude.
- **Clock edges into the clock capacitance: QUESTION, inherited.** MN3205 p2:
  clock input capacitance up to **2800 pF**, rise and fall times **500 ns max**,
  cross point Vx 0 to 0.3 VCPH. CD4046B p3: VCO-section output sink 0.51 mA min
  at 0.4 V (about 780 ohm), 1 mA typ (about 400 ohm). Into 2800 pF that is a
  time constant of 1.1-2.2 us and a 10-90% edge of 2.5-4.8 us, five to ten
  times the MN3205 limit, and CP2 is an XOR-inverted copy of CP1, so the edges
  cross near VDD/2, not under 0.3 VCPH. The mki module does exactly the same
  (DA3 pins 4 and 2 straight to DD1 pins 6 and 2), it is a shipping product, and
  the part fitted is the CoolAudio V3205, whose own clock capacitance is not in
  the repo. So this is a datasheet conflict in the source design, not a
  transcription error. BLOCKED on the V3205 sheet to say more.
  Knock-on: the sample pulse is made by differentiating the same slow edge
  (C116 220 pF into R127 6.2 k, time constant 1.36 us). With a fast edge the pulse
  is 1.36 us x ln(5/1.09) = **2.1 us** above the 1.09 V reference (12 x 10k/110k).
  With a 4.8 us edge the differentiator's peak is only about 1.36 us x 5 V /
  4.8 us = 1.4 V, barely over the reference. At the MN3205 worst case the
  sample-and-hold trigger is marginal.
- Signal level: MN3205 p2 gives input signal swing 0.36 Vrms min at THD 2.5%.
  Manual p24 (quoted in bbd-mki.md): the usable window is about 1.9-3.2 V.
  U103A's bias is +10k x 12.0/47k = **+2.55 V** (2.62 V at 12.3 V), centred.
  With R104 at 0R the dry path gain is -10k/51k = -0.196, so `BBD_IN` above about
  6.6 Vpp leaves the window. That is bbd-mki.md OPEN item 1, correctly recorded
  as unknown until the LPG output level is known.
- **Absolute maximum at pin 7.** U103A drives the BBD input directly from +-12 V,
  as in the manual. With FEEDBACK fully up the wet path adds -10k/82k x 1.09 of
  the dry level, so pin 7 sits at 2.55 - 0.329 x (dry peak). It goes below the
  MN3205's -0.3 V absolute maximum once the dry signal at `BBD_IN` exceeds about
  **8.7 V peak** with feedback at maximum, and never with feedback at zero
  (2.85/0.196 = 14.5 V). A 10 Vpp Eurorack signal (5 V peak) stays inside.
  QUESTION, tied to the LPG output level (section 6).

### CD4046B

- VDD 5 V, inside 3-18 V for the VCO (p2, recommended operating). Pins 14 and
  3 are inputs tied to VDD and VCO out, inside VSS-VDD. 1, 10, 13, 15 open:
  outputs or the zener, "If unused this terminal should be left open" (p1, pin
  10). INHIBIT driven 0-5 V through 100k with D104/D106 clamps. CLEAN.
- The "inverter trick": with SIG IN held high, phase comparator I (exclusive-OR,
  p1) outputs NOT(VCO), the second clock phase. Matches the manual.
- **VCO range.** Fig 4 (p4, zoomed): at VCO_IN = VDD/2, R2 = infinity, VDD =
  5 V, the R1 = 10 k and 100 k curves cross C1 = 1 nF at about 1e5 and 1e4 Hz,
  i.e. f0 is close to 1/(R1 C1). For R1 = 39 k (R123) and C1 = 1 nF (C114):
  f0 about **26 kHz** at VCO_IN = 2.5 V, so roughly 51 kHz at 5 V. Fig 6: the
  offset from R2 = 2.2 M (R121) is several hundred Hz. Unit-to-unit spread at
  5 V: **+-50%** for f0 and +-25% for fmin (tables in Fig 4 and Fig 6).
  VCO_IN is the average of the TIME wiper and `TIME_CV` through two 100k
  resistors: wiper span 12 x 22/144 = 1.83 V to 12 x 122/144 = 10.17 V, so with
  `TIME_CV` = 0 VCO_IN runs **0.92 V to 5 V** (clamped by D103 at about 5.6 V).
  Clock range roughly **10 kHz to 51 kHz**, delay 2048/f = **about 200 ms to
  40 ms** (MN3205: 204.8 ms at 10 kHz, p1). The low end sits on the MN3205's
  10 kHz minimum clock (p2), and with +-50% spread some units will clock below
  it at full CW. Same values and same arithmetic as the mki module (its TIME CV
  attenuator grounds the other 100k when nothing is patched), so this is the
  source's behaviour, not ours. Noted, not a defect.

### TL072 stages (SLOS080W, TL07xC rows at +-15 V: VCM +-11 V min, -12 to 15 typ; VOM +-12 min at 10k)

On +-12 V rails that is a guaranteed common-mode range of about +-8 V and a
guaranteed swing of about +-9 V. The TL072's grade is not recorded (C67473);
the C row is the conservative one, and only the H grade carries the "No Phase
Reversal" figure (Fig 5-26).

| stage | function | gain / corner | input common mode | output | verdict |
|---|---|---|---|---|---|
| U102A | input buffer | 1 | = `BBD_IN`, the LPG output | to the summer and the dry bus | **QUESTION**: if the LPG output exceeds about -8 V, the C-grade input is outside its guaranteed range and may phase-reverse. Section 6 owns the level. |
| U102B | sample-pulse comparator | open loop; threshold 1.09 V | TRIGIN spans about -5 V to +5 V | +-10.5 V into D107 | CLEAN |
| U103A | inverting summer | -0.196 dry, -0.122 feedback, +2.55 V bias | IN+ at GND | 0.2-4.9 V into the BBD at sane levels | see pin 7 above |
| U106A | S&H input buffer | 1 | BBD output AC-coupled, C113 x R124 corner 1.6 Hz | J113 drain | CLEAN |
| U106B | reconstruction gain | 1 + 100k/22k = **5.55** | the hold cap | `BBD_WET`; overall dry-to-wet about 0.196 x 5.55 = 1.09 | CLEAN |
| U103B | mix buffer | 1 | DRY/WET wiper | R131 470 to `BBD_OUT` | CLEAN |

C120's corner: 1 uF into RV5 (10k) parallel RV6 (100k) = 9.1k, about **17.5 Hz**,
the same as the manual's. Feedback loop gain at full FEEDBACK:
0.122 x 5.55 = **0.68** before the BBD's insertion loss (0 +-4 dB, MN3205 p2),
which can reach 1.07 at +4 dB, so the manual's promised self-oscillation at
the top of the knob depends on the part. Same as source.

Op-amp section assignment, every input checked against the drawing: U102A
(DA1A) follower on pins 1-3; U102B (DA1B) + on pin 5 from C116, - on pin 6
from the divider; U103A (DA2A) - on pin 2, + grounded; U103B (DA2B) follower;
U106A (DA5A) follower; U106B (DA5B) + on pin 5 from the hold cap. No swapped
inputs. CLEAN.

### Clamps and the switch

| ref | drawing | ours | verdict |
|---|---|---|---|
| D103 / D203 | VD3: anode on VCO in, cathode to +5 V | K = `P5V_BBD`, A = `BBD_VCOCV` | CLEAN |
| D105 / D205 | VD5: cathode on VCO in, anode to GND | K = VCOCV, A = GND | CLEAN |
| D104 / D204 | VD4: anode on INH, cathode to +5 V | K = P5V_BBD, A = INH | CLEAN |
| D106 / D206 | VD6: cathode on INH, anode to GND | K = INH, A = GND | CLEAN |
| D107 / D207 | VD7: anode on J113 gate, cathode on DA1B out | A = `BBD_SH_G`, K = `BBD_TRIG` | CLEAN |

The clamps hold the 4046 inputs within a diode drop of the rails through 100k,
well inside CD4046B's +-10 mA input current limit (p1). Section 8 checks pad 1
= cathode on the SOD-123.

**SW1/SW2 against the Dailywell drawing (2MD1, ON-NONE-ON):** POS.1 joins 2-3
and 5-6, POS.3 joins 2-1 and 5-4; commons are 2 and 5. P.C. mounting view:
left column 3, 2, 1 top to bottom, right column 6, 5, 4, 5.08 mm between columns,
2.54 mm pitch, Ø1.09 holes. Our footprint (F.Cu): 3 (-2.54,-2.54), 2 (-2.54,0),
1 (-2.54,2.54), 6/5/4 likewise at +2.54, drill 1.1. Matches.

| switch | pole A (1, 2 com, 3) | pole B (4, 5 com, 6) | channels shorted in any position? |
|---|---|---|---|
| SW1 (LPG VCF) | RES_L / VCFSW_L / open | RES_R / VCFSW_R / open | no: each pole carries one channel |
| SW2 (source) | SRC_EXT_L / AUDIO_IN_L / SRC_RSMP_L | SRC_EXT_R / AUDIO_IN_R / SRC_RSMP_R | no |

The old `SW_DPDT_x2` bug (both channels' timing caps shorted) cannot recur: the
part is a single 6-pin symbol and each pole's three pins are one channel's.
**CLEAN.** Which lever position matches the panel legend is section 6/7.

## Verdicts

| item | verdict |
|---|---|
| channel 1 vs the manual's drawing, all 36 nets | CLEAN |
| all R values both channels; C values except declared substitutions | CLEAN |
| channel 2 vs channel 1 | CLEAN (zero differences) |
| C113/C120/C213/C220 X7R where bbd-mki.md says film, "should not be substituted with X7R" | **DEFECT** |
| bbd-mki.md prose: C110 3.3 uF, C119 15 nF | DEFECT (doc) |
| MN3205 clock edge and cross point vs CD4046B drive | QUESTION (inherited; BLOCKED on V3205 sheet) |
| S&H trigger margin at the MN3205 worst-case clock capacitance | QUESTION (same) |
| U102A common mode vs LPG output level | QUESTION (section 6) |
| U101.7 below -0.3 V at dry > 8.7 V peak with full feedback | QUESTION (section 6/7 levels) |
| VCO bottom end at the MN3205 10 kHz minimum | inherited, noted |
| VGG, clamps, op-amp sections, SW1/SW2 | CLEAN |

## Defects, ranked

1. **Degrades the audio, small: four 1 uF X7R caps in the wet signal path**
   where the design doc says film and says not to use X7R. Either fit film or
   C0G-equivalent parts (values, mkbom CURATED) or change bbd-mki.md to accept
   X7R with a reason. At 17.5 Hz corner C120 carries real audio voltage at low
   frequencies, which is where X7R's voltage coefficient shows.
2. **Doc:** bbd-mki.md still describes C110 as 3.3 uF and C119 as 15 nF in its
   prose and diagram, while its own BOM table and the BOM say 10 uF and 10 nF.
3. **QUESTION, inherited from the mki design:** CD4046B into the BBD clock pins
   breaks the MN3205's 500 ns edge and 0.3 VCPH cross-point limits on paper,
   and the S&H trigger rides on the same edge. Works in the mki kit. A V3205
   datasheet would settle it; a bench scope of CP1/CP2 and TP-F on the first
   board will too.
4. **QUESTION, level-dependent:** U102A's guaranteed common-mode range and
   U101 pin 7's absolute maximum both depend on how hot the LPG output runs.
