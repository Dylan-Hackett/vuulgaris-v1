# Stereo BBD delay — SSI2100

Transcribed from the **SSI2100 datasheet Rev 2.5 (June 2026), Figure 1 "Typical
Application Circuit"**, read from the rendered PDF rather than from the text
layer, which interleaves the drawing labels and cannot be trusted for topology.

## The part

| | |
|---|---|
| stages | 512 |
| supply | single **5V** (4.75–5.25V), 0.4–0.6mA |
| clock | 1kHz to >2MHz, **on-chip driver**, TTL/CMOS, **3.3V and 5V** compatible |
| bias | on-chip VTBIAS (14/15 of V+), no legacy 14/15V VGG rail |
| package | SOP-8 |
| SNR | 70dB bare, 108dB with SSI's compandor application |
| THD | 0.4% (compandor out) at fCLK 250kHz, VIN 20mV RMS |
| response | 20Hz – 15kHz |

### Pinout (datasheet page 3, authoritative)

| pin | name | note |
|---|---|---|
| 1 | GND | short, low-inductance trace to analog ground |
| 2 | GCAP | **GND = low gain**; V+ = high gain when daisy-chaining |
| 3 | SIGNAL IN | needs **3.20V DC bias** and a low-impedance source |
| 4 | VTBIAS | internally generated; **3.3µF to GND** |
| 5 | SIG OUT 2 | output when CLK IN is high, source follower |
| 6 | SIG OUT 1 | output when CLK IN is low, source follower |
| 7 | V+ | +5V, **100nF local** + 10µF bulk |
| 8 | CLK IN | clock in, 3.3V/5V logic |

## Figure 1, per channel

Both filters are set to **15kHz for fCLK >= 30kHz**.

```
AUDIO IN ─┬─ 100k ─ GND
          └─ 3.3uF ─ 47k ─┬─ 56k ─┬─ 33k ─┬───────┐
                        470p     470p     │       │  TL072
                         │        │       └─(−)───┤>─┬─ 100R ─┬─→ pin 3 SIGNAL IN
                        GND      GND    (+)       │  │        │
                                        │  100k fb ┘  │      1nF
                                        │  47pF  fb ┘  │       │
                                    V_DCB               │      GND
                                                        │
  V_DCB:  +5V ─ 18.2k ─┬─ 32.4k ─ GND      = 3.20V      │
                       └─ 4.7uF ─ GND                   │

  pin 5 SIG OUT 2 ─┐                                    pin 4 ─ 3.3uF ─ GND
                   ├─ VR1 5k trim ─ wiper ─┬─ 49.9k ─ GND
  pin 6 SIG OUT 1 ─┘                       │
                                           └─ 4.7uF ─ 43k ─┬─ 39k ─┬─ 39k ─┬─ 33k ─┬──────┐
                                                         330p    390p    470p     │      │ TL072
                                                           │       │       │      └─(−)──┤>─→ AUDIO OUT
                                                          GND     GND     GND   (+)=GND  │
                                                                              120k fb ───┘
                                                                              33pF fb ───┘
```

VR1 trims the balance between the two source-follower outputs. The datasheet
marks it optional but says it gives best audio performance, **particularly at
low clock frequencies** — which is exactly where long delays live, so populate it.

## Supply split

The SSI2100 is 5V-only; the TL072s are not. The input filter's op-amp sits with
its non-inverting input at 3.20V so its output biases the BBD input, and the
output filter's op-amp has its non-inverting input at **ground**, so its output
is ground-referenced. That only works on a **split supply** — the op-amps run on
**+/-12V**, the SSI2100 on **+5V**. Both rails already exist on this board.

## Component count

Per channel: 14 resistors, 13 capacitors, 1 trimmer, 2 op-amp sections, 1
SSI2100. Stereo is roughly double, less the V_DCB divider (18.2k / 32.4k /
4.7uF), which is a DC reference and is shared. Four op-amp sections = one TL074,
or two TL072.

## OPEN — gain staging depends on the LPG

Optimal input is **20mV RMS**. That is far below line level, and Figure 1 has no
compandor in it — the compandor is a separate application circuit, and it is
what buys the 70dB -> 108dB SNR and the input range.

The BBD sits after the LPG in the chain, and **the LPG is not designed yet**, so
the attenuation into the BBD and the make-up gain out of it cannot be fixed
until its output level is known. Build the block with the reference values, keep
the input scaling on parts that are easy to change, and bring test points out.

---

# Wet/dry VCA — SSI2164

**Rebuilt 2026-08-27 from the SSI2164 datasheet.** The first version of this
section was invented from general principles about current-mode VCAs and was
wrong in most of its numbers. Recorded here so the mistake is not repeated.

## What the datasheet actually says

| | |
|---|---|
| control port input impedance | **9–11kΩ** (typ 10k) — *not* high impedance |
| gain constant | **−33 mV/dB** |
| control law | **positive VC attenuates, negative amplifies; unity at VC = 0.0V** |
| max attenuation / gain | −100dB / +20dB |
| R_IN | **20kΩ recommended**, range 7.5k–100k; lower = better noise, more THD |
| R_OUT (feedback) | equal to R_IN gives unity gain |
| feedback cap | **100pF** preserves phase margin |
| MODE | **resistor R_M to V−**, not a short to ground |
| control port | optional **series 10µF** improves control feedthrough |

Class A mode resistor: `R_M = (|V−| − 0.65) / (2·I_M)`. At ±12V with I_M = 1mA
that is 5.675k, so **5.6kΩ**. The datasheet's own worked example (9V → 3.9k)
confirms the formula uses the supply magnitude.

## Figure 10: 0–5V exponential control

An inverting summing amp turns a positive control voltage into the negative-going
swing the port wants, with an offset resistor from the negative rail and a PNP
clamp limiting attenuation:

```
control 0-5V ── 100kΩ ──┬── 100kΩ ──┬── op-amp out ── to VC
                        │           │
              −12V ── 270kΩ      100pF
                        │           │
                     op-amp (−) ────┘        Q1 PNP clamp, base at V_CLAMP
                     op-amp (+) ── GND       V_CLAMP = +2.7V (3k:10k off +12V)
                                             1kΩ in series stabilises the loop
```

V_CLAMP of +2.7V gives the maximum 100dB attenuation. Q1 is a small-signal high
gain PNP — BC557 / 2N2907 or equivalent.

## What was wrong the first time

| | first attempt | correct |
|---|---|---|
| DAC → VC | 100kΩ straight into the port | Figure 10 summing amp |
| effective range | **~9dB** (100k into a 10k port is a 10:1 divider) | 100dB |
| R_IN / R_OUT | 100kΩ | 20kΩ |
| MODE | shorted to GND | 5.6kΩ to V− |
| control feedthrough cap | absent | 10µF in series |
| clamp | absent | PNP + 2.7V reference |

## Still to check

Q1's pin mapping was taken as base/emitter/collector = 1/2/3 from KiCad's
`Q_PNP_BEC`. The orientation against Figure 10 has **not** been verified against
the drawing — confirm before fab.

## Decided: delay LEVEL, not a wet/dry crossfade

**2026-08-27.** U9 is an inverting summing amp holding its (−) input at virtual
ground. The VCA's output current (wet) and the dry current through R41 both land
on that node and R42 turns the sum back into a voltage — 20k/20k/20k, so unity
throughout.

Dry is therefore **fixed at unity and always present**; the VCA only sets how
much wet is added. **Wet-only is unreachable.** That is the right control for a
delay and it is what most delays do. It is *not* right for vibrato, which needs
100% wet.

**Upgrade path if that ever matters.** The SSI2164 has four cells and only two
are used — channels 3 and 4 (pins 10/11/12 and 15/14/13) are idle. The MCP4728
has two spare outputs. Route dry through VCAs 3 and 4, drive them from DAC_C/D
with the complementary curve computed on the Daisy, and it becomes a true
crossfade — constant-power rather than linear, since software is generating both
sides. Costs one more TL074 (U8 and U9 are both full at four sections), two more
PNP clamps and about eight passives.

Until then those two VCA cells and two DAC channels are spare capacity for
anything else that wants voltage control.
