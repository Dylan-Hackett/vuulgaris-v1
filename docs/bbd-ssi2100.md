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
