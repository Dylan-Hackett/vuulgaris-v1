# 07: Audio IO: headphone, EXT input, jacks, pots

Block: U9/U10, R501-R522 and C501-C512 (the audio ones), RT501-RT504, J2-J10,
RV1-RV6.

Sources: `TI-OPA1688-datasheet.pdf` (SBOS724A: Table 6-1, 7.1, 7.4, 7.5,
8.3.2, 8.3.3 with Figures 8-3/8-4 rendered), `PJ-376-jack.pdf` (SOFNG, rendered),
`PJ-603-jack.pdf` (Haoyu/Legion, image-only, rendered at 500 dpi),
`Alpha-RD902F-40-15R1-dual-9mm-pot.pdf` (drawing RD902F-40-(L)R1-XXX-00D70 and
the spec sheets, all rendered), `ALPS-RK09L1240A12-pot.pdf`,
`Bourns-3224W-trimmer.pdf`, the BOM, and the Patch SM sheet for levels.

## Which pot is on the BOM

The BOM line for RV1-RV4 and RV6 (`fab/vuulgaris-BOM.csv`) has **no LCSC
number** and the note "NOT FROM JLC -- FIT BY HAND. Alpha
RD902F-40-15R1-B100K ... Tayda A-5440"; RV5 likewise with B10K, Tayda A-6433.
The footprint is still named `RES-ADJ-TH_RK09L1240A12`, but the fitted part
is the Alpha, so the check is against **Alpha's drawing**.

Alpha RD902F-40-(L)R1-XXX-00D70, rev -0057 (p2), with the spec sheet (p3-p4)
and taper chart (p5):

- "SHAFT SHOWN IN FULL C.C.W. POSITION". The front view, from the shaft end
  with the pins down, numbers the terminals **1 2 3 left to right**.
- p5 plots "TERM.1-2 OUTPUT VOLTAGE / TERM.1-3 INPUT VOLTAGE" rising from 0 as
  rotation travel goes from "TERM 1" to "TERM 3": **terminal 1 is the CCW end**.
- P.C.B. mounting hole detail: six Ø1.0 holes at 2.5 mm pitch in two rows 2.5
  mm apart, the near row 7.5 mm from the shaft; two tab slots **1.8 x 1.1**,
  11.3 mm over the outside, long side along the line joining them.
- L = 15 for the -15 shaft; M7 x 0.75 bushing; Ø6.35 shaft.

Our footprint, F.Cu, read from the board (RV1 and RV5 identical): tab slots 7/8
at (+-4.75, -5.00), drill 1.8 x 1.1 with the 1.8 along x (the line joining
them), so 4.75 x 2 + 1.8 = 11.3 over the outside; pin rows at y = 2.5
(pads 4, 5, 6) and y = 5.0 (pads 1, 2, 3), i.e. 7.5 and 10.0 from the tab line;
x = -2.5 / 0 / +2.5; Ø1.0 holes. Seen from above, as the front view is, the
shaft is at (0, -5) with the pins below it, and **pads 1 and 4 are on the left:
terminal 1, the CCW end, for both gangs.** **CLEAN.** The drawing does not
say which row is the front gang, and does not need to: both gangs are the same
value and taper and each carries one stereo channel.

Ratings: B taper 0.05 W (p3 1.2). RV1 across 12 V: 1.4 mW. RV5 (10k) with the
wet signal at up to +-9 V: 4 mW rms. Fine. Tracking error is specified only as a
volume control (-40 to 0 dB within 3 dB, p3 1.9), which is what a stereo knob
gets.

## Jacks

### J2-J6, PJ-376 (SOFNG)

Circuit diagram: **#1** is the sleeve (the hooked contact), **#2** the ring
contact, **#3** the tip contact; the plug gauge numbers the plug 1 sleeve,
2 ring, 3 tip. No switch contacts on this part. P.C.B. layout: 1, 2, 3 in line at
3.5 mm pitch, pin 1 nearest the mouth (3.5 / 7 / 10.5 mm from the body face).

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| J2-J5 .1 | GND | sleeve | GND | CLEAN |
| J2-J5 .2 | GND | ring | GND | CLEAN: a mono jack; a TRS plug's ring is grounded, which is harmless for these signals |
| J2.3 / J3.3 / J4.3 / J5.3 | CVOUT_JACK / GATEOUT_JACK / CV_IN_JACK / GATE_IN | tip | | CLEAN |
| J6.1 / .2 / .3 | GND / HP_OUT_R / HP_OUT_L | sleeve / ring / tip | | CLEAN: tip = left, ring = right |

Library footprint: pads 1/2/3 at x = -3.5 / 0 / +3.5, outline x -12.0 to +4.5,
so the mouth is at -x beyond pad 1, as drawn. Rating 0.5 A, 24 V DC.

### J7-J10, PJ-603 (Haoyu)

The drawing's own SCHEMATIC box settles it without the variant argument:
contact **2** is the sleeve (the line from the barrel), **5** the ring (V
spring), **4** the tip (^ spring), and **3 ends in an arrow resting on 4's
spring**, the normally-closed tip switch. PJ-603-3 (mono) keeps 2, 3, 4; PJ-603-2
(no switch) keeps 2, 5, 4. P.C.B. layout, top view, mouth to the left: 2# on the
centre line 7.6 mm from the face; 3# and 4# on one side at 15.1 and 22.5 mm;
5# opposite 4#, 5 mm away.

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| J7.2 / J8.2 | GND | sleeve | | CLEAN |
| J7.4 / J8.4 | EXT_IN_L/R | tip | | CLEAN |
| J7.3 / J8.3 | GND | tip switch, closed with no plug | GND | CLEAN: unplugged, the tip (and U10's input) is grounded; a plug lifts the spring off 3 |
| J7.5 / J8.5 | GND | ring | GND | CLEAN for unbalanced sources; a balanced source's cold leg is grounded, which balanced outputs tolerate |
| J9.2 / J10.2 | GND | sleeve | | CLEAN |
| J9.4 / J10.4 | LINE_OUT_L/R | tip | | CLEAN |
| J9.3 / J10.3 | open | tip switch | open | CLEAN |
| J9.5 / J10.5 | GND | ring | | CLEAN |

Library footprint: 3 (0.05, 2.5), 4 (7.45, 2.5), 5 (7.45, -2.5), 2 (-7.45, 0),
outline to x = -24.05 (9 mm barrel + 7.6 mm to pin 2). Spacing 7.5 / 7.4 / 14.9
and 5.0 against the drawing's 7.6->15.1->22.5 and 5: matches the top view.
J7-J10 are on B.Cu and the board copies have local y negated, a genuine flip.
This supersedes review-packet item 3's "beep one jack" caveat: the drawing in
the repo states the contact functions directly.

## OPA1688 (U9, U10)

Table 6-1, D (SOIC): 1 OUT A, 2 -IN A, 3 +IN A, 4 V-, 5 +IN B, 6 -IN B, 7 OUT B,
8 V+. Our symbol and nets: U9 1/2 `HP_BUF_L`, 3 `HP_W_L`, 4 NEG12V, 5 `HP_W_R`,
6/7 `HP_BUF_R`, 8 POS12V; U10 1 `EXT_AMP_OUT_L`, 2 `EXT_FB_L`, 3 `EXT_AMP_IN_L`,
5/6/7 the R side. **CLEAN.** Supply 24.6 V against 36 V recommended, 40 V
absolute (7.1/7.3).

| stage | gain from fitted values | notes |
|---|---|---|
| U9A/B headphone buffer | 1 (follower), driven from `BBD_OUT` through C505, R509 100k and RT501 20k to GND | wiper fraction 0 to 20/120 = **0.167** |
| U10A/B EXT preamp | 1 + RT503/R521 = 1 + (0..20k)/2.2k = **1 to 10.1** | RT503 is a rheostat, wiper tied to 3 |

- **Common-mode range** (7.5): (V-) - 0.1 V to (V+) - 2 V, about -12.4 to
  +10.3 V. U9 sees at most +-1.24 V. U10's input is the EXT jack through C511:
  inside the range for anything up to +18 dBu (9.75 V peak). And 8.3.2: "The
  input of the OPA1688 prevents phase reversal", so beyond it the output limits
  instead of reversing.
- **Input protection.** 7.1 limits signal-input current to **+-10 mA** and the
  **differential** input to **+-0.5 V** (back-to-back diodes, 8.4.2). When U10
  clips at gain 10, the inputs separate and the diodes conduct from the jack
  through R517 1k and C511: at +18 dBu with RT503 at 20k, (9.75 - 1.18 - 0.7) V
  over about 3k = **2.6 mA**. A +24 dBu pro-level peak (17.4 V) pushes +IN past
  V+, clamped through R517: (17.4 - 12.3 - 0.7)/1k = **4.4 mA**. Both under
  10 mA. CLEAN.
- **Output current into headphones.** Maximum at the trim's top, with U103B at
  its guaranteed +-9 V swing: `BBD_OUT` = 9 x 2.2k/(2.2k + 0.47k) = +-7.4 V,
  wiper +-1.24 V, into R511 4.7 + 32 ohm = **34 mA** peak; into 16 ohm,
  **60 mA**. ISC is 75 mA typical, not a minimum (7.5). Inside, but a 16 ohm
  headphone at full trim uses most of it.
- **Thermal, 16 ohm worst case.** Per channel, a continuous full-scale sine at
  60 mA peak draws 2 x 12.3 V x 60 mA / pi = 0.47 W from the rails and puts
  37 mW in the load: 0.43 W dissipated, **0.87 W** for the package. RthetaJA
  116.1 C/W (SOIC, 7.4) gives a 101 C rise: about 140 C at 40 C ambient,
  under the 150 C absolute maximum but past the 125 C operating limit. With
  32 ohm phones it is 0.49 W and 97 C. Music's crest factor makes the
  continuous-sine case pessimistic, and RT501/RT502 are set at bring-up.
  QUESTION, low: set the headphone trims with a 16 ohm load in mind.
- **Stability with R511 4.7 ohm and cable capacitance.** 8.3.3 recommends
  isolating heavy capacitive loads with a series resistor, "for example,
  ROUT = 50 ohm". Figure 8-4 (G = 1): with ROUT = 0 overshoot reaches about 50%
  at 200 pF, with 25 ohm about 28%, with 50 ohm about 20%. 4.7 ohm sits near the
  0 ohm curve. With headphones connected the 32 ohm load damps the capacitance;
  with a long cable into a high-impedance input, expect about 50% overshoot,
  not oscillation. QUESTION, low; 4.7 ohm buys damping factor for headphones.

## Levels end to end

0 dBu = 0.775 V rms. Patch SM audio output: "Typical -5V to 5V" (Table 3), and
the SNR plot uses 9.5 Vpp, so +-5 V is taken as full scale.

| path | arithmetic | level | against |
|---|---|---|---|
| Daisy out | +-5 V | 3.54 V rms, **+13.2 dBu** | |
| -> LPG, gate open | x 0.95 (section 6) | +-4.75 V | U301A input +-2.4 V, fine |
| -> `BBD_IN` -> U102A | x 100k/101k | +-4.7 V | BBD window needs at most 6.6 Vpp at R104 = 0R: **over by about 3 dB** (section 5, bbd-mki.md OPEN 1) |
| -> dry -> U103B -> R131 -> `BBD_OUT` | x 2.2k/2.67k loading = 0.824 | +-3.9 V, **+11.0 dBu** | |
| -> line out J9/J10 | x 1k/2.2k | +-1.77 V, **+4.2 dBu**, source 625 ohm | pro line level, as review-packet says |
| -> headphone | x 0..0.167 | up to +-0.65 V | U9 range, fine |
| -> resample (SW2) -> Daisy in | AC coupled, x1 | +-3.9 V | Daisy input typ +-5 V, abs = rails |
| EXT in -> U10 -> Daisy in (SW2 = EXT) | x 1..10.1, rail-to-rail | up to +-11.9 V when clipping | Daisy audio in abs max = its rails (Table 1), +-12.3 V: **inside, with 0.4 V to spare** |
| EXT -> LPG mix (ADR 0011) | x 0.95 | with both sources full scale, +-9 V | section 6: past the TL08xC/TL07xC guaranteed common-mode range |

## AC coupling

All coupling capacitors are 1 uF X7R (`CC0805KKX7R9BB105`), non-polarised, so
there is no polarity to get wrong.

| cap | from -> to | load | corner |
|---|---|---|---|
| C501/C502 | EXT amp out -> SW2 -> Daisy in | Daisy 100k parallel R501 1M = 91k | 1.75 Hz |
| C503/C504 | `BBD_OUT` -> SW2 -> Daisy in | 91k | 1.75 Hz |
| C505/C506 | `BBD_OUT` -> headphone divider | R509 100k + RT501 20k | 1.3 Hz |
| C511/C512 | jack (via R517 1k) -> U10 + | R519 100k | 1.6 Hz |

DC across them is op-amp offset only, millivolts; their loads are 90k and up,
so the audio voltage across each is a small fraction of the signal and X7R's
voltage coefficient does not matter here (unlike C120 in section 5).

## Trimmers, Bourns 3224W

Drawing (p1-p2): top-adjust 3224W, terminals 1 and 3 on one side 2.5 mm apart,
wiper 2 opposite, 2.9 mm between rows, wiper pad 2.0 wide; circuit "CCW 1 ...
3 CW". Footprint: 1 (-1.25,-1.45), 3 (1.25,-1.45), 2 (0, 1.45), pads 1.3/2.0 x
1.6. Matches. `C55071` is 3224W-1-203E per mkbom CURATED (20k).

| trim | 1 (CCW) | 2 | 3 (CW) | clockwise does |
|---|---|---|---|---|
| RT301/RT401 | `LPG_SUM` | `LPG_T1` | `LPG_T1` | more resistance in series with R307 (the gate-open threshold rises toward its top, section 6) |
| RT501/RT502 | `HP_DIV` | `HP_W` | GND | **less** headphone level |
| RT503/RT504 | `EXT_AMP_OUT` | `EXT_FB` | `EXT_FB` | more resistance: more EXT gain |

RT501/RT502 turn the opposite way to the other trims (CW = quieter). Harmless,
worth a line in the bring-up notes. Power 0.25 W at 85 C; nothing here comes
near it.

## Verdicts

| item | verdict |
|---|---|
| RV1-RV6 against the Alpha drawing: pins, CCW end, tabs, both gangs | CLEAN |
| J2-J6 PJ-376 contacts and footprint | CLEAN |
| J7-J10 PJ-603 contacts, normalling and footprint | CLEAN |
| U9/U10 pinout and supply | CLEAN |
| U10 input protection, phase reversal | CLEAN |
| headphone current and package dissipation at 16 ohm, full trim | QUESTION, low |
| 4.7 ohm isolation vs cable capacitance | QUESTION, low |
| levels: line out +4.2 dBu, Daisy input inside its maximum | CLEAN |
| Daisy -> BBD level at R104 = 0R | already OPEN in bbd-mki.md |
| AC coupling corners and polarity | CLEAN |
| RT501/RT502 direction | note |
| footprint name `RES-ADJ-TH_RK09L1240A12` on an Alpha part | DEFECT (doc/naming) |

## Defects, ranked

Nothing here would kill the board.

1. **QUESTION, degrades:** at full headphone trim into 16 ohm, U9 dissipates
   enough to approach 140 C on a continuous sine. Set the trims with that in
   mind; 32 ohm phones are comfortable.
2. **Naming:** the pot footprint and the REVIEW-INDEX datasheet row still name
   the ALPS RK09L. The pads are right for the Alpha; the name invites the
   C380211 substitution the BOM note warns against.
3. **Note:** RT501/RT502 are reversed relative to the other trims.
