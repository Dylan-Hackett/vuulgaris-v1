# Stereo BBD delay — mki x es.edu

Transcribed from **page 61 of `docs/BBD_MANUAL_250228 (3).pdf`** (PDF page index
60), the production schematic `EDUBBD2.sch`, rev v2.0, dated 2024-09-06.

That page is **vector line art with no text layer** — `get_text()` returns the
string `"61"` and nothing else. Everything below was read off renders: the page
rotated 90° (`page.set_rotation(90)`; `270` gives it upside down) and tiled at
500–2000 dpi with overlap, with every wire junction checked at high zoom for a
dot versus a hop. Where the drawing was ambiguous the region was re-rendered
larger rather than guessed; the three crossings that could have been shorts are
called out under **Junctions checked** below.

Every topology claim was then cross-checked against the manual's own prose,
which walks the same circuit block by block on pages 8–45 and 59–60. Page
citations are to the **printed** page number.

This supersedes nothing in [`bbd-ssi2100.md`](bbd-ssi2100.md) that is still
live — that file's SUPERSEDED section is the decision record that produced this
one, and its **two-CD4046 reasoning and layout rules are carried forward here**
verbatim in intent.

---

## Designator scheme

The manual numbers its parts R1–R32, C1–C22, DA1–DA5, DD1, VD1–VD7, VT1, SW1,
XS1–XS5, XP1. Those collide with this board, which already runs to C39, R25, D2,
L2, U7, J11, RV6, SW7, ENC8, FB2, F1.

**Rule: `<class><100·channel + manual number>`. Channel 1 = LEFT, channel 2 =
RIGHT.** The manual's number is always the last two digits, so any part on this
board maps back to page 61 by inspection.

| manual | LEFT | RIGHT | part |
|---|---|---|---|
| DD1 | `U101` | `U201` | V3205SD, 4096-stage BBD |
| DA1 | `U102` | `U202` | TL072 — input buffer (A) + S&H trigger comparator (B) |
| DA2 | `U103` | `U203` | TL072 — input summing amp (A) + mix buffer (B) |
| DA3 | `U104` | `U204` | CD4046BE — clock |
| DA5 | `U106` | `U206` | TL072 — S&H buffer (A) + output amp (B) |
| VT1 | `Q1` | `Q2` | J113 N-JFET, S&H switch |
| VD3–VD7 | `D103`–`D107` | `D203`–`D207` | 1N4148 |
| R6–R32 | `R106`–`R132` | `R206`–`R232` | fixed resistors |
| C5–C22 | `C105`–`C122` | `C205`–`C222` | see exceptions below |

Shared parts do **not** get a channel number; they take the next free reference
in the board's existing sequence:

| manual | this board | part |
|---|---|---|
| DA4 | `U8` | 78L05, +5V for both channels |
| C12 | `C40` | 100nF, 78L05 input |
| C17 | `C41` | 100nF, 78L05 output |
| C18 | `C42` | 3.3µF, 78L05 output bulk |
| SW1 | — | TIME RANGE, **not fitted**. Long mode is hardwired, see below |
| R1 / R3 / R5 | `RV4` / `RV5` / `RV6` | the existing dual-gang panel pots |

**`U105` and `U205` are deliberately never used** — DA4 is shared, so reserving
its slot would imply a part per channel that does not exist.

### Not transcribed, deliberately

**XP1, VD1, VD2, R8, R9, C1–C4.** That is the manual's Eurorack power inlet and
its reverse-polarity/RC filtering. This board does not have a Eurorack header —
it takes USB-C into a DKM10E-12 and already owns `J11`, `F1`, `U7`, `L1`, `L2`,
`C28`–`C39`, `R24`, `R25`, `D1`, `D2` for exactly that job (see
[`power-usbc-dkm.md`](power-usbc-dkm.md)). `POS12V` and `NEG12V` already exist
and are already filtered. Nothing from the manual's power page is needed.

**R2 (TIME CV pot) and XS1 (TIME CV jack).** Resolved — see *TIME CV* below.

**R4 (IN GAIN pot).** Replaced by a single stand-in resistor `R104`/`R204`. See
OPEN.

---

## Signal chain, one channel

```
BBD_IN ─ R107 1k ─ U102A(+) buffer ─┬──────────── BBD_DRY ─────────── RV6 ccw
   │                                │                                  (dry)
  R106                              └─ R104 (IN GAIN) ─ R114 51k ─┐
  100k                                                            │
   │                                       RV5 FEEDBACK ─ R112 82k┤ summing
  GND                                                             │  node
                                                    NEG12V ─ R113 47k
                                                                  │
                                                    R118 10k ─────┤
                                                            ┌─────┴── U103A(−)
                                                            │
                            U103A out ── BBD_SIGIN ── U101 pin 7 IN
                                                            │
        +5V ─ R119 4.7k ─┬─ R120 62k ─ GND     VGG = 4.65V   │
                         ├─ C110 3.3µF ─ GND ──── U101 pin 8 │
                                                             ▼
                                            ┌────────────────────────┐
                          CP1 ← CLK ────────┤ 6                    7 │
                          CP2 ← /CLK ───────┤ 2   U101  V3205SD    4 ├── BBD_RAW
                                            │ 5 = +5V   1 = GND    3 ├─ NC
                                            └────────────────────────┘
   BBD_RAW ─┬─ R122 100k ─ GND
            └─ C113 1µF film ─┬─ R124 100k ─ GND
                              └─ U106A(+) buffer ── BBD_SH_IN ─┬─ R128 100k ─┐
                                                               │             │
                                              Q1 J113  D ──────┘             │
                                                        G ───────────────────┤
                                                        S ── BBD_SH_HOLD ─┐  │
                                                                          │  │
                                          C119 15nF ─ GND ────────────────┤  │
                                                                          │  │
                                   U106B(+) ───────────────────────────────┘  │
                                   U106B(−) ─ R129 22k ─ GND                  │
                                            ─ R130 100k ─ out    gain 5.55    │
                                   U106B out ── BBD_WET ── C120 1µF film ──┐  │
                                                                           │  │
   BBD_WETAC ─┬─ R132 470 ─ WET OUT (no jack, see OPEN)                    │  │
              ├─ RV5 FEEDBACK cw                                            ◄─┘
              └─ RV6 DRY/WET cw ── wiper ── U103B buffer ─ R131 470 ─ BBD_OUT

   trigger:   CLK ─ C116 220pF ─┬─ R127 6.2k ─ GND
                                └─ U102B(+)                  D107 1N4148
              POS12V ─ R125 100k ─┬─ R126 10k ─ GND          anode = SH gate
                                  └─ U102B(−)  = 1.09V       cathode = TRIG
              U102B out ── BBD_TRIG ── D107 cathode ────────────────────────┘
```

### Input, scaling and biasing

`U102A` (DA1A) is a **unity-gain buffer**: pin 2 is tied directly to pin 1. Its
input comes through `R107` 1k from the block input, with `R106` 100k to ground.
Its output is the **dry bus** — it feeds the IN GAIN leg and the DRY/WET pot's
CCW end, and the manual says (p32) it exists precisely because current is drawn
from the input in two places.

`U103A` (DA2A) is an **inverting summing amplifier**, pin 3 at ground, feedback
`R118` 10k. Three inputs land on its virtual ground:

| through | from | what it does |
|---|---|---|
| `R114` 51k | IN GAIN | audio, gain −10k/51k = **−0.196** |
| `R112` 82k | FEEDBACK wiper | repeats, gain −10k/82k = **−0.122** |
| `R113` 47k | **NEG12V** | DC offset, +10k/47k × 12V = **+2.55V** |

The +2.55V is not decoration. Manual p24: the V3205's MOSFETs "only responded
well to signals swinging between around **1.9 and 3.2 V**" — centre 2.55V,
window 1.3Vpp. `R113` off the negative rail through an inverting stage is what
puts the signal there. A 10Vpp Eurorack input at full IN GAIN would be 1.96Vpp,
i.e. slightly over the window, which is why the manual has an IN GAIN control at
all (p25).

Loop gain around FEEDBACK at full CW = 0.122 × 5.55 (the output amp) ≈ 0.68
before the BBD's own loss, which is the manual's "feedback gain of about 1"
(p34) and the self-oscillation it promises.

### BBD and its bias

`U101` V3205SD, 8-pin. **Pinout confirmed twice** — off the drawing, and
independently from manual p26: *"supplied with 5 V at pin 5 and ground at pin 1
… VGG voltage at pin 8 via a 4k7/56k voltage divider … clock 1 into pin 6, clock
2 into pin 2, and our scaled and biased input into pin 7 … drive our output
reconstruction circuit from pins 3 and 4."*

| pin | name | net |
|---|---|---|
| 1 | GND | `GND` |
| 2 | CP2 | `BBD_CLKN` — inverted clock |
| 3 | OUT1 | **no-connect.** Marked with an X on the drawing |
| 4 | OUT2 | `BBD_RAW` |
| 5 | VDD | `P5V_BBD`, decoupled by `C111` 100nF |
| 6 | CP1 | `BBD_CLK` |
| 7 | IN | `BBD_SIGIN` |
| 8 | VGG | `BBD_VGG` |

**Only one output is used.** The breadboard chapter drives the reconstruction
from both pins 3 and 4; the production circuit does not, and p29 says why:
*"This means removing one output from the equation and killing the basic
low-pass filter."* The two-output summing trick is a low-pass substitute, and it
is replaced by the sample-and-hold.

**VGG is 4.65V**, from `R119` 4.7k / `R120` 62k off +5V with `C110` 3.3µF to
ground. The production divider is 4k7/62k where the breadboard chapter used
4k7/56k — the target is the "tetrode MOS structure" second-gate voltage, which
p25 gives as **14/15 of the supply**: 4.67V. 5 × 62/66.7 = 4.648V. The
production values hit it; the breadboard ones (4.60V) were close enough to
experiment with.

Output bias: `R122` 100k from pin 4 to ground sets the source-follower's
operating point, `C113` 1µF **film** AC-couples, `R124` 100k re-references the
result to ground for the ±12V buffer that follows. Both 1µF caps are specified
as film on the drawing, in the signal path — that is deliberate and should not
be substituted with X7R.

### Clock — CD4046BE, free-running VCO, and the inverter trick

`U104` CD4046BE on +5V/GND, `C109` 100nF at pin 16.

| pin | name | net | note |
|---|---|---|---|
| 16 | Vdd | `P5V_BBD` | |
| 8 | Vss | `GND` | |
| 9 | VCO_IN | `BBD_VCOCV` | the control node, TP2 "C" |
| 11 | R1 | `R123` 39k to GND | sets the top of the range |
| 12 | R2 | `R121` 2.2M to GND | frequency offset, ~800Hz floor (p10) |
| 6 | C1A | `C114` | timing cap, hardwired — no switch |
| 7 | C1B | `C114` far plate | |
| 4 | VCO_OUT | `BBD_CLK` | the clock |
| 14 | SIG_IN | **`P5V_BBD`** | tied high |
| 3 | COMP_IN | `BBD_CLK` | fed from VCO_OUT |
| 2 | PC1_OUT | `BBD_CLKN` | the inverted clock |
| 5 | INH | `BBD_INH` | |
| 1, 10, 13, 15 | PCP_OUT, SF_OUT, PC2_OUT, Z_OUT | no-connect | all marked X |

**Pins 2, 3 and 14 are the whole trick and they are easy to misread.** Phase
comparator I in a 4046 is an XOR. Tie `SIG_IN` (14) to Vdd and XOR(1, x) = NOT x,
so `PC1_OUT` (2) becomes an inverter of `COMP_IN` (3). Feed `COMP_IN` from
`VCO_OUT` and you get the BBD's second, anti-phase clock for free. Manual p14
states this outright: *"if we tie pin 14 on the 4046 chip to the high level
supply, pins 2 and 3 act as a simple inverter, with pin 3 as the input and pin 2
as the output."*

The wire from pin 3 crosses the pin-14-to-+5V wire on the way up to the clock
node. **That crossing has no junction dot** — checked at 2000 dpi. Reading it as
a junction would tie the clock to +5V and produce a module that does nothing.

**TIME RANGE — not fitted. Decided 2026-09-02: long mode only.**

On the drawing `SW1` is an SPDT selecting the timing cap: "long" = `C114` 1nF,
"short" = `C115` 220pF. Manual p36 is explicit about which is which — *"we can
shorten it by increasing the clock frequency. For that, all we have to do is swap
the 1 nF capacitor for a smaller one"* — and p37 confirms the short position is
the flanger one. (The manual's own figure for the 220pF, "4kHz to 112kHz … around
1s to just 35 ms", reads oddly against that; the prose, not the figure, is what
establishes which cap is which.)

**`C114` 1nF is wired straight across pins 6 and 7 and the switch is gone**,
along with `C115`/`C215` and the `BBD_CLONG`/`BBD_CSHORT` nets. What this costs
is **flanger mode**; what it buys is the third panel toggle nobody had budget
for, and two fewer caps per channel. p37 also notes 220pF is as small as this
circuit can usefully go — the sample window would exceed the valid part of the
BBD output and distort — so nothing smaller was ever on the table anyway.

### TIME control

```
POS12V ─ R110 22k ─ RV4 ccw ─┤wiper├─ RV4 cw ─ R111 22k ─ GND
                                │
                      R115 100k ┴───┬─── BBD_VCOCV ─ U104 pin 9
                                     │
       TIME_CV ─────── R116 100k ────┤
                                     ├── D103 anode, cathode → P5V_BBD
                                     └── D105 cathode, anode → GND
```

CCW is the +12V end, CW the ground end, so **clockwise = longer delay**.

`R115`/`R116` are a passive averager, not a summer, and the manual is explicit
that this is on purpose (p38): doubling the pot's output range and then halving
it in the averager means adding an idle-at-0V modulation source does not shift
the knob's setting. The Thévenin arithmetic, taking the pot's own wiper
impedance into account:

| TIME pot | V_oc | R_th | node, CV = 0V | CV coefficient |
|---|---|---|---|---|
| full CW (long) | 1.83V | 18.6k | **0.84V** | ×0.542 |
| centre | 6.00V | 36.0k | **2.54V** | ×0.576 |
| full CCW (short) | 10.17V | 18.6k | **4.65V** | ×0.542 |

So the knob alone sweeps roughly **0.84V to 4.65V** at `VCO_IN`, which is the
1V–5V the manual targets (p10: the 4046 has a CV dead zone of about 1V above the
lower supply, and the top is Vdd). The bottom of travel sits just inside that
dead zone, so the oscillator parks at the `R121` offset frequency — intended.

### TIME CV — from the Daisy, not a jack

**Resolved 2026-09-01.** There is no TIME CV jack on this build and no TIME CV
attenuator pot. The manual's `R2` (A100k) and `XS1` are both dropped; `R116`
100k in each channel connects straight to the Daisy.

```
U1 pin C1 (CV_OUT_2) ── TIME_CV ──┬── R116 100k ── BBD_VCOCV_L
                                  └── R216 100k ── BBD_VCOCV_R
```

**The net on U1 pin C1 is renamed `CV_OUT_JACK` → `TIME_CV`.** That pin was
allocated to a CV output jack ([`pin-allocation.md`](pin-allocation.md) line
345); the jack was never wired, so nothing is being ripped out, but **that line
of `pin-allocation.md` is now stale** and should be corrected.

**Does it need a buffer? No.** The Patch SM's CV outputs are **0–5V with 100Ω
output impedance** (`datasheets/extracts/patch-sm-v1.0.5-pinout.md` lines 21 and
89). Two 100k loads in parallel is 50kΩ:

- current at full scale: **100µA**. The pin is buffered on-module and this is
  nothing.
- error from source impedance: 100/(100k+... ) → **0.2%**. Irrelevant.
- inter-channel crosstalk, which is the reason to care about impedance and not
  current: L's control node reaches R's only through 100Ω sitting between two
  100k resistors, i.e. **≈ −66dB** before you account for the signal being a
  slow CV rather than audio. The two clocks do **not** talk to each other
  through this node.

**Level and polarity.** 0–5V into the averager contributes **0 to +2.7V** at
`VCO_IN` (coefficient 0.542–0.576 from the table above), on a knob span of
3.8V. So one DAC output sweeps about **70% of the full delay-time range**, in
one direction only: **CV up = VCO_IN up = clock faster = delay shorter.**
That lands usefully across the range with no scaling or offset needed.

**The clamp diodes are load-bearing in this configuration, not vestigial.** Knob
full CCW plus CV at 5V would put 4.65 + 2.71 = **7.36V** on pin 9, against a
CD4046 absolute maximum of Vdd + 0.5V. `D103` holds it to about 5.6V, sinking
roughly 33µA **into** `P5V_BBD` — trivial against the rail's ~10mA of load.
`D105` (anode GND, cathode node) cannot conduct from two non-negative sources;
it is fault protection against, say, the negative rail finding the TIME pot.
Both cost nothing. Keep both.

**Recommendation on the missing TIME CV attenuator: fit nothing, scale in
firmware.** Reasoning:

1. The manual's `R2` did two jobs (p39) — provide a path to ground when nothing
   is plugged in, and set modulation depth. Job one is gone: the Daisy drives
   the node at 100Ω whenever it is powered, so 0V is a real 0V.
2. Job two is now free. `pin-allocation.md` line 439 warns that scaling a 12-bit
   output to 10% leaves ~400 of 4096 codes. That argument does not bite here —
   at the depths anyone would actually use for delay-time modulation (25–100%)
   it is 1000–4096 codes, and full depth is already only 70% of the range.
3. **Do not fit a trimmer per channel.** Two independently-set trimmers make the
   two channels' modulation depths mistrack in an uncontrolled way. The stereo
   width in this design is supposed to come from *one* place — the dual-gang
   TIME pot's bounded few-percent mistracking. A drifting trimmer pair is a
   second, worse source of the same thing.

If bench testing says the range is too coarse, the fix is a fixed divider at the
block's CV entry with **the same two values in both channels**, not a trimmer.

*Unpowered-Daisy case:* if the CV output goes high-impedance while ±12V is up,
`R115` pulls `VCO_IN` toward the TIME pot's 10.17V, `D103` clamps it at 5.6V,
and the clock simply runs at maximum. Harmless. A 100k pull-down at the CV entry
would tidy it if that ever annoys; it costs one resistor and has zero effect
while the Daisy is driving.

### INHIBIT CV

`R117` 100k in series to pin 5, `D104` clamping to +5V, `D106` clamping to
ground — the same protection idiom as TIME CV, which is what the manual says it
is (p41: *"we can repurpose the diode-based limiting approach that we just came
up with"*). Pin 5 high stops the oscillator; a gate sequence into it gives the
rhythmic stutter the manual is after (p42). Source is OPEN — see below.

### Reconstruction sample-and-hold

This is the part of the circuit most likely to be mis-transcribed, because the
J113 symbol is drawn rotated: **drain and source enter from the top, gate leaves
from the bottom.**

`U106A` (DA5A) is a unity buffer on the AC-coupled BBD output. `Q1` is a series
switch from that buffer to `C119` 15nF, and `U106B` is a non-inverting amp of
**1 + 100k/22k = 5.55** on the held voltage. Manual p29–p30 names all three
differences from a textbook S&H, and every one is on the drawing:

| manual p29–30 | on page 61 |
|---|---|
| "100k resistor between the input and the JFET's gate terminal" | `R128` 100k, `BBD_SH_IN` → `BBD_SH_G`. Bootstraps V_GS ≈ 0 while on, so no biasing or scaling of the BBD output is needed |
| "a diode between the gate and the sampling trigger" | `D107`, **anode on the gate, cathode on the trigger**. Trigger low pulls the gate down and the switch off |
| "gate-to-trigger converter … turns the square wave clock into a super narrow pulse" | `C116` 220pF + `R127` 6.2k differentiating the clock (117kHz corner) into `U102B` used open-loop as a comparator against `R125`/`R126` = **1.09V** |
| "propagation delay … dodge the worst part of the clock spike" | the TL072's own slew and prop delay. Not a component |
| "a relatively big capacitor" | `C119` 15nF |
| "non-inverting amplifier … gain of around 5, plus another round of AC coupling" | `U106B` at 5.55, then `C120` 1µF film |

`U102B` — the comparator — shares a package with `U102A`, the input buffer.
That is the manual's own choice, not an artefact of packing; keep it if you keep
TL072s, and keep the local decoupling that goes with it.

### Dry/wet — a real crossfade

`RV6` DRY/WET is a **crossfade, not a delay-level control.** Wet (post-`C120`)
lands on the CW end, dry (`U102A`'s output, brought across the bottom of the
sheet) on the CCW end, wiper into `U103B` as a unity buffer. Manual p32:
*"sending the wet (delayed) and dry (unprocessed) signals to opposite sides of a
100k potentiometer"*, and p33 confirms full CW is wet-only.

**This is the opposite of what the scrapped SSI2164 block did**, where dry was
fixed at unity and the VCA only added wet ([`bbd-ssi2100.md`](bbd-ssi2100.md),
"Decided: delay LEVEL, not a wet/dry crossfade"). Wet-only *is* reachable here,
so vibrato and full-wet flanging work.

Two outputs: `R131` 470 from the mix buffer, `R132` 470 from the wet node
directly. Both 470Ω series resistors are short-circuit protection on Eurorack
outputs, not filters.

### Power

Per channel, from the existing ±12V rails: six 100nF (`C105`–`C108`, `C121`,
`C122`), two per TL072, one to each rail. The drawing places them as `DA1C`,
`DA2C`, `DA5C` — the power "units" of the three dual op-amps, pins 4 (V−) and
8 (V+).

Shared: `U8` 78L05 from +12V, `C40` 100nF in, `C41` 100nF + `C42` 3.3µF out,
feeding `P5V_BBD`. Pin numbering off the drawing is **1 = Vout, 2 = GND,
3 = Vin**, which is the TO-92 L78L05 pinout.

**`P5V_BBD` is a new net and is deliberately not the board's existing `P5V`**
(the Daisy's 5V output, which already feeds the OLED and the MSP430 through
`FB1`/`FB2`). Two free-running clocks do not belong on the rail that feeds a
display.

#### Does one 78L05 cover both channels?

**Yes, comfortably.** The arithmetic:

| load | each | ×2 |
|---|---|---|
| V3205SD | ~3mA typ, 10mA taken as worst case **[assumption — the Coolaudio datasheet is not in this repo]** | 20mA |
| CD4046BE VCO at 5V | R1/R2 currents are 5/39k + 5/2.2M = 130µA; internal switching dominates; ≤2mA | 4mA |
| clock drive into the BBD | C·V·f ≈ 50pF × 5V × 112kHz = **28µA** | negligible |
| **worst case** | | **~24mA** |
| **typical** | | **~8mA** |

- **Current:** the 78L05 is a 100mA part. Worst case is **under a quarter** of
  it.
- **Thermal:** drop is 12 − 5 = 7V. At 24mA that is 168mW. TO-92 θ_JA ≈
  200°C/W → **34°C rise**; at 50°C inside a closed desktop enclosure, Tj ≈ 84°C
  against a 125°C limit. SOT-89 (θ_JA ≈ 100°C/W) halves the rise.

So the answer is one regulator, and **the reason anyone would want a second is
isolation, not headroom** — which is better bought with layout than with silicon:

- **Star-route `P5V_BBD` from `C42` to each channel.** Do not daisy-chain L
  through to R; that puts L's clock transients across the trace impedance R sees.
- The per-channel 100nF at each 4046 (`C109`/`C209`) and each BBD
  (`C111`/`C211`) are already in the drawing and are already correct. Place them
  at the pins.
- **Consider more bulk.** `C42` 3.3µF is the only reservoir on a rail now
  feeding two clocks. 10µF, or a second 3.3µF at the far channel, is cheap
  insurance. *Not in the netmap — it is a change to the drawing, listed here as
  a recommendation.*

---

## Net inventory — LEFT channel

Generated from `netmap.json`, so this table and the netlist cannot drift. The
RIGHT channel is identical with `_L` → `_R` and the 1xx refs → 2xx. `GND`,
`POS12V` and `NEG12V` are omitted (118 / 23 / 19 pins).

| net | pins |
|---|---|
| `BBD_IN_L` | `R106.1 R107.1` — block input boundary, see OPEN |
| `BBD_INF_L` | `R107.2 U102.3` |
| `BBD_DRY_L` | `R104.1 RV6.1 U102.1 U102.2` |
| `BBD_GAIN_L` | `R104.2 R114.1` |
| `BBD_FB_L` | `R112.1 RV5.2` |
| `BBD_SUM_L` | `R112.2 R113.2 R114.2 R118.1 U103.2` |
| `BBD_SIGIN_L` | `R118.2 U101.7 U103.1` |
| `BBD_VGG_L` | `C110.1 R119.2 R120.1 U101.8` |
| `BBD_RAW_L` | `C113.1 R122.1 U101.4` |
| `BBD_AC_L` | `C113.2 R124.1 U106.3` |
| `BBD_SH_IN_L` | `Q1.1 R128.1 U106.1 U106.2` |
| `BBD_SH_G_L` | `D107.2 Q1.3 R128.2` |
| `BBD_SH_HOLD_L` | `C119.1 Q1.2 U106.5` |
| `BBD_SH_FB_L` | `R129.1 R130.1 U106.6` |
| `BBD_WET_L` | `C120.1 R130.2 U106.7` |
| `BBD_WETAC_L` | `C120.2 R132.1 RV5.3 RV6.3` |
| `BBD_MIXW_L` | `RV6.2 U103.5` |
| `BBD_MIX_L` | `R131.1 U103.6 U103.7` |
| `BBD_OUT_L` | `R131.2` — module output, jack pin not yet bound |
| `BBD_WETOUT_L` | `R132.2` — no jack, see OPEN |
| `BBD_CLK_L` | `C116.1 U101.6 U104.3 U104.4` |
| `BBD_CLKN_L` | `U101.2 U104.2` |
| `BBD_VCOCV_L` | `D103.2 D105.1 R115.2 R116.2 U104.9` |
| `BBD_TIMEHI_L` | `R110.2 RV4.1` |
| `BBD_TIMEW_L` | `R115.1 RV4.2` |
| `BBD_TIMELO_L` | `R111.1 RV4.3` |
| `BBD_INH_L` | `D104.2 D106.1 R117.2 U104.5` |
| `BBD_INHCV_L` | `R117.1` — no source yet, see OPEN |
| `BBD_C1A_L` | `C114.1 U104.6` |
| `BBD_C1B_L` | `C114.2 U104.7` |
| `BBD_VCOR1_L` | `R123.1 U104.11` |
| `BBD_VCOR2_L` | `R121.1 U104.12` |
| `BBD_TRIGIN_L` | `C116.2 R127.1 U102.5` |
| `BBD_TRIGREF_L` | `R125.2 R126.1 U102.6` |
| `BBD_TRIG_L` | `D107.1 U102.7` |

Shared, both channels:

| net | pins |
|---|---|
| `P5V_BBD` | `U8.1 C41.1 C42.1` + per channel `C109.1 C111.1 D103.1 D104.1 R119.1 U101.5 U104.14 U104.16` |
| `TIME_CV` | `U1.C1 R116.1 R216.1` |

## Junctions checked

Three crossings on this sheet would each produce a silent, working-looking short
if read as junctions. All three were re-rendered at 1800–2000 dpi and confirmed
to be **hops, not dots**:

| where | if misread |
|---|---|
| `U104` pin 3 (COMP_IN) riser crossing the pin 14 → +5V wire | clock tied to +5V; module silent |
| `U101` pin 2 (CP2) riser crossing the `C113` → `U106A` line | inverted clock shorted to the BBD's audio output |
| the dry bus running down the sheet, crossed by the TIME and INHIBIT rows | dry audio onto the 4046's control node |

Junction **dots** confirmed (not hops) at: the `BBD_CLK` node (three-way —
`U104.4`, `U104.3` via TP4, `C116`), the `U103A` summing node (four-way),
`BBD_SH_IN` (`U106.1`, `U106.2`, `Q1` D, `R128`), and `BBD_WETAC` (`C120`,
`RV5` CW, `RV6` CW, `R132`).

## Bill of materials cross-check

The manual's own parts list (p3–p4) was used as an independent check on the
transcription, and it reconciles exactly:

`2M2 ×1, 100k ×9, 82k, 62k, 51k, 47k, 39k, 22k ×3, 10k ×2, 6k2, 4k7, 1k, 470 ×2,
10 ×2` = 27 fixed resistors, which is R6–R32. The nine 100k are R6, R15, R16,
R17, R22, R24, R25, R28, R30 — all nine are accounted for above. Capacitors
`47µF ×2, 3.3µF ×2, 1µF ×2, 15nF, 100nF ×12, 1nF, 220pF ×2` = 22 = C1–C22. Five
1N4148, two 1N5819, one J113, one 78L05, three TL072, one V3205SD, one CD4046BE,
one SPDT (**not fitted here** — see TIME RANGE), five switched mono jacks, and pots `100k A104 ×1, 100k B104 ×3,
10k B103 ×1`. Nothing on the drawing is unaccounted for and nothing in the list
is missing from the drawing.

---

## Stereo, and what it demands of layout

Carried forward from [`bbd-ssi2100.md`](bbd-ssi2100.md) — the reasoning has not
changed, only the parts it applies to.

**Two CD4046s, one per channel, free-running.** `U104` and `U204` are
independent oscillators, both nominally set by `RV4`'s two gangs. A dual-gang
pot tracks to a few percent at best, the two clocks therefore never land on the
same frequency, and **that mismatch is the stereo width.** A single shared clock
would delay both channels identically, which sums to mono in the middle and has
no image.

The intermodulation worry is a **supply and layout problem, not a signal-path
one** — the two clocks never meet in the audio path, because each channel has
its own S&H, its own output amp and its own output.

- **Decouple each 4046 locally.** `C109`/`C209` at pin 16, at the pin.
- **Do not let the two share a rail impedance.** Star from `C42`, per above.
- **Keep the two clock traces apart**, and both away from both audio paths.
  `BBD_CLK` and `BBD_CLKN` also run to `C116` and to the BBD; those are the
  longest clock runs on the board.
- **Series damping resistors on the clock lines** to slow the edges. *Not in the
  netmap* — they are not on page 61. If fitted, 100–470Ω in series with
  `U104.4` → `U101.6` and `U104.2` → `U101.2`, right at the 4046.
- **Wet and dry sum within a channel and never across.** `RV6`'s two gangs are
  electrically independent and must stay that way; the only thing they share is
  the shaft.
- Measure at bring-up: scope one output with both channels running and sweep
  TIME, listening for a whistle that moves.

---

## Panel controls

All three are **existing dual-gang `RK09L1240A12` pots**, already placed for the
faceplate. One shaft, two independent sections, one knob per stereo pair — which
is exactly the arrangement the stereo argument above wants.

| pot | label | manual | gang A (L) | gang B (R) |
|---|---|---|---|---|
| `RV4` | TIME | R1 B100k | pins 1/2/3 | pins 4/5/6 |
| `RV5` | FEEDBACK | R3 B10k | pins 1/2/3 | pins 4/5/6 |
| `RV6` | WET/DRY | R5 B100k | pins 1/2/3 | pins 4/5/6 |

Symbol geometry (read out of `lib/vuulgaris.kicad_sym`): pins **2 and 5 are the
wipers**, 1/3 and 4/6 the ends, and **7/8 are the mounting lugs**, shorted to
each other inside the symbol and left unwired here. The two gangs are drawn with
matching orientation — pin 1 and pin 4 are on the same side, 3 and 6 on the
other — so the L and R sections cannot end up reversed relative to each other.

**UNVERIFIED: which end terminal is CCW.** The symbol names its pins "1".."8"
and carries no CW/CCW information; the netmap assumes the near-universal
**1 = CCW, 2 = wiper, 3 = CW** (and 4/5/6 likewise). If that is backwards, all
three knobs turn the wrong way *together*, nothing is damaged, and the fix is
swapping 1↔3 and 4↔6 in `netmap.json`. Confirm against the Alps RK09L drawing or
on the bench.

**UNVERIFIED and more consequential: what resistance these pots actually are.**
`values.json` records only the label and the symbol only the MPN
(`RK09L1240A12`, LCSC `C380211`). The manual needs **B100k** for TIME and
DRY/WET and **B10k** for FEEDBACK, and one part number cannot be both. What
happens in each case:

- **If the part is 100k:** TIME and DRY/WET are correct. FEEDBACK at 100k
  instead of 10k still works — it loads the wet node *less*, and the wiper's
  source impedance (up to 25k) adds to `R112` 82k, so mid-rotation feedback is
  about 23% lower than the drawing intends. A taper change, not a fault.
- **If the part is 10k:** FEEDBACK is correct and **TIME is broken.** In the
  +12V / 22k / pot / 22k string a 10k pot gives a wiper span of only 4.89–7.11V
  instead of 1.83–10.17V, collapsing the delay range to about a third. Fixable
  by rescaling `R110`/`R111` to 2k2, but it has to be caught first.

Check the LCSC page before ordering. This is the single most likely way for this
block to arrive wrong.

---

## OPEN

### 1. IN GAIN (manual R4, B100k) — no panel control, and none available

RV1–RV6 are all allocated (RV1–RV3 to the LPG, RV4–RV6 to this block) and the
panel has no seventh slot. The netmap therefore carries **`R104`/`R204`, a
single resistor standing in for the pot**, seeded at 0Ω (straight through).

**Recommendation: keep it a fixed part with the same value in both channels;
choose the value at bring-up; do not fit a trimmer.**

- Straight through is already −14dB into the summing node, and the BBD's window
  is 1.3Vpp centred on 2.55V, so the block accepts about **6.6Vpp** at
  `BBD_IN` before clipping the BBD. A 10Vpp Eurorack signal needs roughly 2/3.
- But the BBD's actual source is the **LPG output, whose level is not known
  because the LPG is not designed** — the same blocker
  [`bbd-ssi2100.md`](bbd-ssi2100.md) recorded against the SSI2100 version. So
  this cannot be fixed on paper.
- **Not a trimmer**, for the same reason as the TIME CV attenuator: two
  independently-set trimmers make the two channels' drive levels mismatch, and a
  level mismatch between L and R is an audible image shift — a defect, unlike
  the clock mistracking, which is the wanted effect.
- If a divider turns out to be needed, `R104` becomes the series leg and a shunt
  resistor to ground is added at `BBD_GAIN`. Give both a 0603 pad now.
- Bring `TP1`-equivalent (`BBD_DRY`) and `TP3`-equivalent (`BBD_SIGIN`) out as
  test pads so the setting can be found with a scope instead of by ear.

### 2. Jacks — XS1–XS5 onto the existing connectors

This module has **J7–J10** (1/4", `PJ-603`) for audio and **J2–J5** (3.5mm,
`PJ-376`) for CV/gate. All eight are placed and **all eight are still unwired**;
`hardware/kicad/README.md` records that which contact is tip/sleeve/switch on
`PJ-603` is *not established*. Nothing below binds a jack pin, and that
pre-existing open item is unchanged.

| manual | this board |
|---|---|
| **XS3 AUDIO IN** | **not a jack.** The BBD is an insert *after* the LPG, so its input is the LPG's output. The netmap calls it `BBD_IN_L`/`BBD_IN_R` and leaves it as the block boundary. J7/J8 feed `AUDIO_IN_L/R` into the Daisy and never touch this block. |
| **XS5 DRY/WET OUT** | the module's analog output. `BBD_OUT_L`/`BBD_OUT_R` → the two 1/4" output jacks of J7–J10. Which two, and which pin is tip, is the existing open item. |
| **XS4 WET OUT** | **no jack, and no slot for one.** `R132`/`R232` and `BBD_WETOUT_L/R` are transcribed and left terminating on nothing. Bring them out as pads/a 2-pin header for bring-up, or depopulate `R132`/`R232` and drop the nets. Do not add a panel jack without a panel-budget decision. |
| **XS1 TIME CV** | **resolved** — Daisy `CV_OUT_2` (U1 pin C1). See above. |
| **XS2 INHIBIT CV** | **OPEN.** J2–J5 are spoken for (CV out, gate out, CV in, gate in). `BBD_INHCV_L`/`_R` terminate on nothing in the netmap. |

**Recommendation for INHIBIT CV: drive it from a Daisy gate output.** `B5`
(`GATE_OUT_1`) and `B6` (`GATE_OUT_2`) are native 0–5V, exactly what a CD4046
INH pin wants, and both are free of any competing use in
[`pin-allocation.md`](pin-allocation.md). Either one gate to both channels
(rhythmic stutter applied to the pair, which is what you want musically) or one
each for independent L/R stutter. `R117`/`R217` and the clamps stay as drawn —
belt and braces for a source that already cannot leave 0–5V, and free. This
makes the stutter a sequencer-driven effect rather than a patch-cable one, which
suits an instrument with a looper in it.

Note that `GATE_OUT_1`/`GATE_OUT_2` are also nominally destined for J2–J5. If
INHIBIT takes one, that jack allocation needs revisiting. **Not decided here.**

### 3. TIME RANGE — CLOSED 2026-09-02

Resolved by deletion. It would have had to be DPDT rather than the manual's SPDT
(one pole per channel from one actuator), and the panel already carries two
toggles with no room for a third. Long mode is hardwired instead: `C114`/`C214`
1nF straight across each 4046's pins 6 and 7, `SW3` and the 220pF caps removed
from the netmap. Flanger mode is the thing given up.
### 4. Passive symbols — DECIDED 2026-09-02

Adopted: KiCad's generic `Device:R` / `Device:C` for the BBD block's passives,
with the value in `values.json` and the existing `R0603` / `C0603` / `C0805`
footprints. `Device.kicad_sym` was already in `mksch.py`'s `LIBS`, so it cost
nothing. A resistor symbol carries no information its value does not; what has to
be right is the footprint, and those already existed. The one thing it costs is
the LCSC part number in the BOM, which needs a value→part mapping at order time
either way.

The two 1µF **film** caps per channel (`C113`, `C120`) and the 15nF hold cap
(`C119`) are the exceptions, and they are handled by `BBD_C0805` in `mksch.py` —
see "Caps that are not 0603 X7R" below. Do not substitute plain X7R for any of
the three.

---

## Symbols — pulled 2026-09-02

All present in `lib/vuulgaris.kicad_sym` with `SYM` and `FPMAP` entries in
`mksch.py`, and every pin number checked against the real symbol.

| part | symbol | LCSC | footprint |
|---|---|---|---|
| CD4046B | `CD4046BNSR` | `C2651237` | `SO-16_L10.3-W5.3-P1.27-LS7.8-BL` |
| TL072 | `TL072_FLAT` | `C67473` | `SOIC-8_L4.9-W3.9-P1.27-LS6.1-BL` |
| 78L05 | `78L05_C181132` | `C181132` | `SOT-89-3_L4.5-W2.5-P1.50-LS4.2-BR` |
| J113 | `MMBFJ113` | `C891686` | `SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR` |
| 1N4148 | `1N4148WT4` | `C2099` | `SOD-123_L2.8-W1.8-LS3.7-RD` |
| V3205SD | `V3205SD` | — hand-built | `DIP-8_SPECIAL_V3205SD` |
| R, C | `Device:R`, `Device:C` | generic | `R0603`, `C0603` / `C0805` |

**The 1N4148 orientation risk is resolved.** `1N4148WT4` has **pin 1 = K,
pin 2 = A**, which is what `netmap.json` already assumed. `D103` anode on the CV
node with its cathode to +5V, `D105` anode to ground, `D107` anode on the S&H
gate — all three confirmed against the pulled symbol, not only the drawing.

`MMBFJ113` is **1 = D, 2 = S, 3 = G**, matching `Q1`/`Q2` in the netmap.

### The V3205SD footprint is not a DIP-8

The datasheet calls it a *"Special 8-Lead Dual-In-Line plastic Package"*, and the
mechanical drawing (V1.0, page 4) gives 2.54mm pitch, **7.62mm row spacing**, and
15.24mm from pin 1 to pin 4 — six pitches, i.e. a **DIP-14 lead pattern with the
middle three positions on each side omitted**. Body is 19.2 x 6.4mm.

```
chip pin   1   2   3   4    5   6    7    8
DIP-14     1   2   6   7    8   9   13   14
```

`DIP-8_SPECIAL_V3205SD.kicad_mod` puts the eight pads at those DIP-14 positions
and numbers them 1-8, so the netmap's pin numbers (taken off the drawing) bind to
the physically correct pads. A stock DIP-8 footprint would put every pad in the
wrong place; a stock DIP-14 would put them in the right places under the wrong
numbers. A 14-pin socket fits it.

### Caps that are not 0603 X7R

`BBD_C0805` in `mksch.py`. `C_19` is the sample-and-hold storage cap on a
high-impedance node — **15nF C0G in 0805**, because X7R's voltage coefficient and
piezoelectric response both land straight in the audio there. `C_13` and `C_20`
are the 1µF signal-path caps the drawing marks "Film", and `C_10` / `C42` are
simply too large for 0603 at a sane voltage rating.

## Verification status — VERIFIED 2026-09-02

**516/516 connections verified, 0 unintended, 137 nets, `netcheck` exits 0.**

```bash
cd hardware/kicad
python3 tools/mksch.py && python3 tools/netcheck.py
```

Every pin declared in `netmap.json` is instantiated on the schematic and agrees
with KiCad's own netlister in both directions. The reverse direction — pins KiCad
bound that `netmap.json` never asked for — is the one that matters, and it is
clean.

This replaces the earlier `225/516 … exits 1` state, which meant "not
instantiated yet", not "wired wrong": the BBD refs had no symbols, so there was
nothing on the schematic to compare their pins against.

### What the run caught before it went green

The generator emits **one symbol instance per reference, `(unit 1)`**. It cannot
express a multi-unit symbol, and two parts here are multi-unit with their units
drawn at *identical* symbol coordinates:

| symbol | what happened |
|---|---|
| `TL072CDR` (easyeda2kicad, 2 units) | pins 5, 6 and 7 live on unit 2 and were never instantiated — 18 `got None` mismatches across the six TL072s |
| `SW_DPDT_x2` (KiCad `Switch`, 2 units) | pins 1/4, 2/5 and 3/6 sit at the same coordinates, so `SW3`'s two poles stubbed onto each other and **`U204.6` bound to `BBD_C1A_L` instead of `BBD_C1A_R`** — the two channels' timing capacitors shorted together |

The second is the same defect class as the `SW1`-on-`RV3` short found on the way
in, in a new place. It would have tied the two clocks' TIME RANGE capacitors
across channels — audible, and invisible to ERC. (`SW3` has since been removed
entirely; the flat symbol still matters for `SW1`/`SW2`.)

Fixed by building flat single-unit symbols, which is what `TL074_FLAT` already
existed for: **`TL072_FLAT`** and **`SW_DPDT_FLAT`**, same footprints, all pins at
distinct coordinates. `SW1`/`SW2` moved to the flat symbol too — they are unwired
today, so the defect was latent there rather than live.

## Still to do

**The board.** The 109 new parts exist in the schematic and the netlist; none of
them are on the PCB yet. Update PCB from Schematic (F8) pulls the footprints in,
then `python3 tools/place.py` seeds and enforces positions. Layout constraints
are in "Stereo, and what it demands of layout" above — the sample-and-hold node
is the hard one.

**Still open:** IN GAIN (`R104`/`R204`, seeded 0Ω) and the jack mapping for WET
OUT and INHIBIT CV. TIME RANGE is closed — long mode hardwired, no switch.
