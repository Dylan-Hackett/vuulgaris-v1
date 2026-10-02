# 06: Low pass gate, both channels

Block: U301/U302, U401/U402, VT301/VT302, VT401/VT402, R3xx/R4xx, C3xx/C4xx,
D301/D401, RT301/RT401, RV1/RV2/RV3, SW1.

Sources: `datasheets/LPG Schematic E Bergman (3) (1).jpg` (6000 x 6000), read in
six zoomed regions plus a separate crop of D1; `TI-TL084-datasheet.pdf`
(SLOS081O), `TI-TL074-datasheet.pdf` (identical file to the TL072 one,
SLOS080W), `Xvive-VTL5C3-datasheet.pdf`, `BZT52C3V9-zener.pdf` (Formosa, image
pages rendered), ADRs 0007 and 0011, `Dailywell-2MD1T1B1M2QES-DPDT.pdf`.
`lpg-bergman.md` was read only for what it declares, after the diff.

## Bergman's drawing, transcribed, against channel 3xx

Nets as drawn (one channel, his designators), then ours:

| drawing | ours | verdict |
|---|---|---|
| OFFSET 100K: +15V / GND, wiper - R3 150K | RV1 (3 = POS12V, 1 = GND), wiper `LPG_OFS_L` - R303 150k | CLEAN (+12 V rails, declared) |
| summing node: R3, C5 2nF, R5 100K, Tp1 (one end and its wiper), Tp2, U1-B pin 6 | `LPG_SUM_L`: R303, C305 2nF, R305, RT301.1, U301.6 | CLEAN; Tp2 not fitted (declared) |
| C5 - R4 470K | `LPG_C5_L`: C305, R304 | CLEAN |
| CV node: R4, R5, U2-C out pin 8, R33 | `LPG_CV_L`: R304, R305, U302.8, R333 | CLEAN |
| U1-B pin 5 - R8 10K - GND (the pin 5 wire crosses the R5 line without a dot) | `LPG_BP_L`: U301.5, R308 to GND | CLEAN |
| U1-B out pin 7 - R6 470R; (Tp2 + S1 DEEP back to pin 6) | `LPG_BOUT_L`: U301.7, R306 | CLEAN; DEEP not fitted (declared) |
| Tp1 20K rheostat - R7 33K | RT301 (1 on SUM, wiper tied to 3) - R307 | CLEAN. Bergman ties the wiper to the SUM end, ours to the R7 end: the same 0-20k rheostat, adjusted in the opposite sense |
| LED node: R7, R17 100K to GND, D1 anode, LED1 anode | `LPG_LED_L`: R307, R317, D301 A, VT301.1 (+TP10) | CLEAN |
| D1 3.9V: triangle points down, bar to GND (zoomed) | D301 C = GND, A = `LPG_LED_L` | CLEAN |
| LED1 K - LED2 A | `LPG_LEDM_L` | CLEAN |
| LED2 K - R6 | `LPG_LEDK_L`: VT302.2, R306 | CLEAN |
| AUDIO IN - R9 100K to GND - C6 1uF - R10 100K to GND - U1-A pin 3 | `AUDIO_OUT_L` - R310 100k (R9); mix node; C306; `LPG_INF_L`: R309 (R10), U301.3 | CLEAN plus the ADR 0011 mix (R301/R302 into `LPG_MIX_L` before C306) |
| U1-A pin 2: R11 15K from out, R12 15K to mode switch S1/S2 | `LPG_AFB_L`: R311, R312 15k **to GND permanently** | declared (ADR 0011) |
| U1-A out: R11, LDR1 | `LPG_ABUF_L`: U301.1, R311, VT301.3 | CLEAN |
| LDR1 - LDR2 midpoint: C7 220pF to GND, C8 4.7nF to S5 | `LPG_MID_L`: VT301.4, VT302.3, C307, C308 | CLEAN |
| LDR2 out: R16 10K to S3, C9 1nF, R13 4M7, U1-C pin 10 | `LPG_LDR_L`: VT302.4, C309, R313, U301.10 | CLEAN; R16 absent (declared, no VCA mode) |
| U1-C pin 9: R14 10K from out | `LPG_CFB_L` | CLEAN |
| U1-C out: R14, R15 1K (AUDIO OUT), U1-D pin 12 | `LPG_OUT_L`: U301.8, U301.12, R314, R315 (into `BBD_IN_L`) | CLEAN |
| U1-D: pin 13 = C10 22pF and RESONANCE wiper; out pin 14 = C10, RESONANCE top, S6 | `LPG_RESW_L`, `LPG_RES_L`: C310, RV2.2, RV2.1, SW1.1 | CLEAN |
| RESONANCE bottom - R18 100K - GND | `LPG_RESL_L`: RV2.3, R318 | CLEAN |
| S5/S6 (mode pole 3): C8 to U1-D out | SW1 pole A: 2 = `LPG_VCFSW_L` (C308), 1 = `LPG_RES_L`, 3 open | CLEAN |
| U2-A: + GND, - R23 100K from CV2 and R20 100K from out | U302.3 GND; `LPG_CVI_L`: R323 (from `LPG_ENV`), R320 | CLEAN |
| Level + Invert 100K: ends CV2 and U2-A out, wiper - R27 100K | RV3: 3 = `LPG_ENV`, 1 = `LPG_ENVN_L`, wiper - R328 | CLEAN (CV1 path and its R28 dropped, declared) |
| U2-D: + GND, - R27/R28/R30, out - R31 | `LPG_SUMCV_L`, `LPG_CVD_L` | CLEAN |
| U2-C: + GND, - R31 and R33, out = CV node | `LPG_CVC_L` | CLEAN |
| U2-B unused: + GND, - tied to out | U302.5 GND, `LPG_NC_L` = U302.6/.7 | CLEAN |

Values: every fitted part matches the drawing (R303 150k, R304 470k, R305 100k,
R306 470, R307 33k, R308 10k, R309/R310 100k, R311/R312 15k, R313 4M7, R314 10k,
R315 1k, R317/R318 100k, R320/R323/R328/R330/R331/R333 100k; C305 2nF, C306
1uF, C307 220pF, C308 4.7nF, C309 1nF, C310 22pF; RT301 20k). C306 is a
1 uF X7R where Bergman draws an electrolytic; at a 1.5 Hz corner it carries
almost no AC voltage, so X7R is fine there.

Mode switch: the drawing's table is a bottom view of a 3PDT ON-OFF-ON, so the
middle position connects nothing: VCA = S1-S2 and S3-S4 (R12, R16 grounded),
BOTH = all open, VCF = S5-S6 (C8 to U1-D). Our SW1 implements S5/S6 only, on a
2MD1 ON-NONE-ON (Dailywell: POS.1 joins 2-3, POS.3 joins 2-1). POS.3 = C8 in
= **VCF**, POS.1 = C8 out = **BOTH** (R12 and R16 open in both, apart from the
ADR 0011 R312). This is what `lpg-bergman.md` decides. **CLEAN.**

## Channel 4xx against 3xx

Renaming 3xx -> 4xx and `_L` -> `_R`: every pin and every value identical, no
4xx part without a 3xx twin. Shared nets: `LPG_ENV` (one envelope, both
sides), `POS12V`, `NEG12V`, `GND`. RV1/RV2/RV3 carry channel 3xx on pins 1-3 and
4xx on 4-6 in the same order. **CLEAN.**

## Electrical checks

### ADR 0011's input mix, as a circuit

- **Gain.** `LPG_MIX_L` is a passive average of `AUDIO_OUT_L` (Patch SM, 100R
  out, Fig 1.8) and `EXT_AMP_OUT_L` (OPA1688) through 10k each: source
  impedance 5k, loaded by R309 100k through C306, so each source arrives at
  0.5 x 100/105 = 0.476 and U301A (1 + 15k/15k = 2) returns **0.95x**. The
  ADR's 0.95 is right.
- **Nothing patched.** J7/J8's normalling contacts ground U10's input
  (section 7), so `EXT_AMP_OUT` sits at 0 V plus offset from a low impedance.
  The Daisy is then halved by R302 to ground and doubled by U301A: 0.95x,
  unchanged from before the ADR. With the Daisy idle its codec output is 0 V,
  and EXT passes alone at 0.95x.
- **DC.** C306 blocks both sources' offsets; R310 100k keeps `AUDIO_OUT_L`
  referenced. Corner 1/(2 pi x 1 uF x 105k) = 1.5 Hz.
- **Headroom: QUESTION, against a tighter limit than the ADR uses.** The ADR
  sums both sources at full scale to about +-9 V at U301A's output and compares
  that with a TL084 "swinging about +-10.5 V on +-12 V". The binding limit is
  not the output swing. With the gate open the same +-9 V appears at U301C's
  non-inverting input (pin 10, via the LDRs) and U301D's (pin 12), and then at
  the BBD's input buffer U102A pin 3. TL08xC and TL07xC guarantee a common-mode
  range of **+-11 V on +-15 V** (SLOS081O and SLOS080W, 5.8: "VCM +-11 min,
  -12 to 15 typ"), i.e. 4 V inside each rail: **about +-8 V on our +-12 V**.
  Only the H grades carry TI's "No Phase Reversal" figure. Negative peaks of
  -9 V are a volt past the guaranteed range, where a C-grade JFET input can
  phase-reverse and slam its output to the positive rail. Each source alone
  (+-4.75 V) is fine; the ADR's bring-up mitigation (trim RT503/RT504 for about
  -6 dB peaks, a firmware master level) covers it if followed. The ADR's
  arithmetic should quote the common-mode limit, not the output swing.

### Vactrol LED drive

- **Polarity: CLEAN.** `LPG_LED_L` -> VT301 A -> K -> VT302 A -> K -> R306 470R
  -> U301B out. Both LEDs forward from the LED node into the op-amp, which
  sinks. VTL5C3 pins 1/2 = LED anode/cathode, 3/4 = cell (Xvive p1 and section
  8).
- **Zener: CLEAN.** D301 anode on the LED node, cathode to ground, as drawn.
  When U301B pulls the string negative the node sits at -Vz (BZT52C3V9:
  **3.7 / 3.9 / 4.1 V** at 5 mA, Formosa p2) and D301 supplies the LED current
  from ground; the other way it clamps the node at about +0.7 V (VF 0.9 V max at
  10 mA, p1).
- **Worst-case LED current: CLEAN.** (|Vout| - Vz - 2 VF)/470. Taking U301B at
  -11 V (best case on +-12 V), Vz at its 3.7 V minimum and VF at 1.5 V:
  (11 - 3.7 - 3.0)/470 = **9.1 mA**. VTL5C3 absolute maximum 40 mA, derated
  0.9 mA/C above 30 C, so the limit stays above 9.1 mA up to about 64 C.
  Zener dissipation 9.1 mA x 4.1 V = 37 mW against 350 mW.
- **LED reverse voltage: DEFECT, inherited.** VTL5C3 absolute maximum: "LED
  Reverse Breakdown Voltage: 3.0 V" (Xvive p1, under ABSOLUTE MAXIMUM RATINGS).
  When the net current into the summing node is negative, U301B has nothing to
  balance it with (the LED node can rise only to the zener's +0.7 V) and
  saturates **positive**, about +9 to +10.5 V on +-12 V. The node sits near
  0 V through R317, so the two LEDs in series take roughly 10 V in reverse,
  against 3.0 V each. That happens in normal use: FILTER CV AMT (RV3) is a
  bipolar "Level + Invert" control, so an inverted envelope with CUTOFF low
  drives the sum negative (-50 uA from a -5 V CV through R305 against at most
  +80 uA from CUTOFF through R303). Bergman's circuit does the same with DEEP
  off; DEEP's Tp2 path from output to summing node is what would hold the
  output in, and it is not fitted. Fix (netmap, values): a 1N4148W in series
  with R306/R406, anode on `LPG_LEDK`, cathode toward U301B's output. It
  conducts the LED current and takes the reverse voltage (1N4148W: VR 75 V,
  `1N4148W.pdf`), and costs 0.7 V of LED drive, about 1.5 mA off the
  9.1 mA maximum.

### Op-amp section assignment

U301 (TL084) and U302 (TL074) use the same section and pin numbers as
Bergman's U1 and U2: A = pins 1-3, B = 5-7, C = 8-10, D = 12-14. Checked
input by input: U301.3 + `LPG_INF`, .2 - `LPG_AFB`; .5 + `LPG_BP`, .6 -
`LPG_SUM`; .10 + `LPG_LDR`, .9 - `LPG_CFB`; .12 + `LPG_OUT`, .13 -
`LPG_RESW`; U302.3/.5/.10/.12 + to GND, U302.2/.6/.9/.13 - as drawn. Supplies
on 4 (+12) and 11 (-12). No swapped inputs. **CLEAN.**

### Pots and trimmer

Assuming Alpha RD902F terminal 1 = CCW (section 7 re-reads the drawing):

| pot | pin 1 (CCW) | wiper | pin 3 (CW) | clockwise does |
|---|---|---|---|---|
| RV1 CUTOFF | GND | `LPG_OFS` | +12 V | more offset current, gate opens. Matches lpg-bergman.md's 2026-09-23 decision |
| RV2 RESONANCE | `LPG_RES` (U301D out) | `LPG_RESW` (U301D -) | `LPG_RESL` (R318 to GND) | more of the track above the wiper: gain 1 + R_upper/(R_lower + R318) rises from 1 toward 2, more resonance |
| RV3 FILTER CV AMT | `LPG_ENVN` (inverted envelope) | `LPG_CVW` | `LPG_ENV` | positive CV: the envelope opens the gate. Centre = no CV, CCW = inverted |

Both gangs of each pot are wired identically (pins 4-6 = 1-3 for the other
channel). RT301/RT401 are a 20k rheostat (Bourns 3224W: 1 = CCW, 2 = wiper,
3 = CW per the review packet; section 7 re-reads it), wiper tied to pin 3.
**Panel legend: nothing to check against.** The faceplate PCB carries no legend
text (no `gr_text` in `vuulgaris-faceplate.kicad_pcb`), and
`mockups/generate-faceplate.py` line 1633 still describes the switch as
"DPDT LPG mode VCF/VCA" while VCA mode is deliberately not built (doc drift).

### Control voltage arriving

`LPG_ENV` is the Patch SM's `CV_OUT_1`, 0-5 V (Table 1/3). U302A inverts it
(-5..0 V); RV3 picks anywhere between; U302D and U302C invert twice, so
`LPG_CV_L` spans **-5 to +5 V**: +-50 uA into the summing node through R305.
CUTOFF adds 0 to 12.0/150k = **80 uA** (Bergman's +15 V gave 100 uA).

The gate opens fully once the LED node reaches the zener knee, which takes
Vz/(R307 + RT301) of net current: 3.9/43k = 91 uA with RT301 mid-track,
74-124 uA across Vz and trim. CUTOFF alone (80 uA) only reaches the knee with
RT301 at least 15.8k (Vz 3.9 V) or 18.3k (Vz 4.1 V) of its 20k. So the +12 V
rails eat most of the trim's range on a high-Vz zener. Within adjustment, but
worth knowing at calibration: with CV added (up to 130 uA) the knee is always
reachable. QUESTION, low.

## Verdicts

| item | verdict |
|---|---|
| channel 3xx vs Bergman, every node and value | CLEAN (declared deviations only) |
| channel 4xx vs 3xx | CLEAN |
| ADR 0011 mix: gain, unpatched, DC | CLEAN |
| ADR 0011 headroom quoted against output swing instead of common-mode range | QUESTION |
| LED polarity, current, zener direction | CLEAN |
| **LED reverse voltage about 10 V vs 3.0 V absolute maximum** | **DEFECT** (inherited, DEEP not fitted) |
| op-amp sections and inputs | CLEAN |
| pot directions | CLEAN (pending section 7 on pin 1) |
| panel legend | not checkable; generator text says VCA (doc) |
| CUTOFF-alone full open needs RT301 near its top | QUESTION, low |

## Defects, ranked

1. **Degrades the vactrols over life: the LED pair is reverse-biased by about
   10 V in normal use** (inverted CV, CUTOFF low), against a 3.0 V absolute
   maximum per LED. Add a series 1N4148W per channel (netmap, values).
2. **QUESTION: common-mode headroom.** With both sources hot the signal at
   U301C/D and U102A exceeds the TL08xC/TL07xC guaranteed common-mode range on
   +-12 V. ADR 0011's mitigation works if followed; its stated limit is the
   wrong one.
3. **Doc:** `generate-faceplate.py` describes SW1 as "VCF/VCA".
