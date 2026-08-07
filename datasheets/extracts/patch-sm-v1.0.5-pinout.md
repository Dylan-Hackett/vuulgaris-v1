# Daisy Patch SM v1.0.5 - pinout extract

Text extract from the Electrosmith Patch SM datasheet v1.0.5 (25/JAN/2023), retrieved during
project scaffolding. Tables reproduced verbatim. Figures, technical drawing and landing pattern
are **not** here: get the PDF via `../fetch-datasheets.sh` for those.

## Absolute maximum ratings (Table 1)

| Pin type | Min | Max | Unit |
|---|---|---|---|
| Positive power input | 6 | 17 | V |
| Negative power input | -6 | -17 | V |
| Ground | 0 | 0 | V |
| 5V output | | 800 | mA |
| 3V3 output | | 500* | mA |
| GPIO | -0.3 | 6** | V |
| Audio IO | neg power in | pos power in | V |
| Gate input | neg power in | pos power in | V |
| Gate output | 0 | 5 | V |
| CV input | neg power in | pos power in | V |
| CV output | 0 | 5 | V |

\* Maximum output current is firmware dependent.
\*\* To sustain a voltage higher than 4V the internal pull-up/pull-down resistors must be disabled.

## Pin functions (Table 2)

| Pin | Primary name | STM32 pin | Detail | Alt. function |
|---|---|---|---|---|
| A1 | -12V | N/A | Negative power input | N/A |
| A2 | ADC_9 | PA1 | GPIO | UART4_RX |
| A3 | ADC_10 | PA0 | GPIO | UART4_TX |
| A4 | GND | N/A | Ground | N/A |
| A5 | 12V | N/A | Positive power input | N/A |
| A6 | 5V | N/A | Positive power output | N/A |
| A7 | GND | N/A | Power | N/A |
| A8 | USB_DM | PB14 | GPIO | USART1_TX |
| A9 | USB_DP | PB15 | GPIO | USART1_RX |
| A10 | 3V3 | N/A | Power output | N/A |
| B1 | AUDIO_OUT_RIGHT | N/A | DC coupled audio | N/A |
| B2 | AUDIO_OUT_LEFT | N/A | DC coupled audio | N/A |
| B3 | AUDIO_IN_RIGHT | N/A | AC coupled audio | N/A |
| B4 | AUDIO_IN_LEFT | N/A | AC coupled audio | N/A |
| B5 | GATE_OUT_1 | PC14 | Output only | N/A |
| B6 | GATE_OUT_2 | PC13 | Output only | N/A |
| B7 | I2C1_SCL | PB8 | GPIO | UART4_RX, PWM (TIM4_CH3) |
| B8 | I2C1_SDA | PB9 | GPIO | UART4_TX, PWM (TIM4_CH4) |
| B9 | GATE_IN_2 | PG14 | **Input only** | N/A |
| B10 | GATE_IN_1 | PG13 | **Input only** | N/A |
| C1 | CV_OUT_2 | PA5 | Output only | N/A |
| C2 | CV_4 | PA7 | Input only | N/A |
| C3 | CV_3 | PA2 | Input only | N/A |
| C4 | CV_2 | PA6 | Input only | N/A |
| C5 | CV_1 | PA3 | Input only | N/A |
| C6 | CV_5 | PB1 | Input only | N/A |
| C7 | CV_6 | PC4 | Input only | N/A |
| C8 | CV_7 | PC0 | Input only | N/A |
| C9 | CV_8 | PC1 | Input only | N/A |
| C10 | CV_OUT_1 | PA4 | Output only | N/A |
| D1 | SPI2_CS | PB4 | GPIO | N/A |
| D2 | SDMMC1_D3 | PC11 | GPIO | USART3_RX* |
| D3 | SDMMC1_D2 | PC10 | GPIO | USART3_TX* |
| D4 | SDMMC1_D1 | PC9 | GPIO | N/A |
| D5 | SDMMC1_D0 | PC8 | GPIO | N/A |
| D6 | SDMMC1_CLK | PC12 | GPIO | UART5_TX* |
| D7 | SDMMC1_CMD | PD2 | GPIO | UART5_RX* |
| D8 | ADC_12 | PC2 | GPIO | SPI2_MISO |
| D9 | ADC_11 | PC3 | GPIO | SPI2_MOSI |
| D10 | SPI2_SCK | PD3 | GPIO | N/A |

\* **47K pullups are connected to this pin.** May affect behaviour when used as UART.
This is the D2 / D3 / D6 / D7 caveat in `docs/design-state.md` section 5. If freeing SD pins
for reuse, prefer D4 and D5.

## What this confirms for the V1 design

Cross-checked against the claims in `docs/design-state.md` section 5. All hold:

- **D8 and D9 are primarily ADC pins** (ADC_12/PC2, ADC_11/PC3). SPI2_MISO/MOSI are alternate.
- **A2 and A3 are primarily ADC_9 and ADC_10** (PA1, PA0), UART4 alternate.
- **B9/B10 are Input Only.** Not usable for an encoder.
- Everything on the C header is Input Only or Output Only. No bidirectional GPIO there.
- Bidirectional GPIO set: **A2, A3, A8, A9, B7, B8, D1-D10.**
- **A2/A3 and B7/B8 both reach UART4_RX/TX.** Alternate mappings of the same peripheral,
  so routing both and populating one is free insurance. Confirmed by the alt-function column.
- Pot wiring: CV_1-CV_8 take +/-5V (wire to 5V out, A6). ADC_9-ADC_12 are 0-3.3V and must
  wire to the 3V3 output (A10). Datasheet states this explicitly under Figure 1.2.
- microSD reference part: **PJS008U-3000-0**, no pullup resistors necessary.
- CV outputs are 0-5V, output impedance 100R.
- Gate/CV/audio input impedance: 100K.

## Other figures in the PDF (not extracted)

1.1 stereo audio input (jack 1 normals to jack 2) - 1.2 potentiometers - 1.3 CV input -
1.4 gate input - 1.5 tactile switch - 1.6 toggle switch - 1.7 micro SD - 1.8 stereo audio
output - 1.9 CV output - 1.10 gate output - 1.11 power (no bypass caps necessary) -
1.12 LED - 1.13 on-off-on toggle switch. Plus technical drawing and landing pattern in mm.

Example parts named by Electrosmith: Thonkiconn WQP-WQP518MA jacks, Alpha 9mm
RD901F-40-15F-B10K-00D70 pots, TL1105SPF250Q tactile, 2MS1T1B1M2QES toggle,
TS-4A-TECQ-H on-off-on toggle, WP132XND 3mm LED.

## Power note

Patch SM can be partially powered over USB for firmware updates without VIN, but the audio
codec will not function properly that way. Connecting USB while VIN is applied causes no damage.
