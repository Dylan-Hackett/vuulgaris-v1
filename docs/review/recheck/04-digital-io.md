# 04: Digital IO: expanders, encoders, buttons, OLED, SD

Block: U3/U4 (MCP23017), ENC0-ENC8, SW4-SW9, DS1, J1, R20/R21, R505-R508,
C26/C27. Sources, each read directly:

- `Microchip-MCP23017-datasheet.pdf`, **DS20001952C (July 2016)**: Table 2-1
  (p11), Section 3.3 and Figures 3-5/3-6 (p15), DC characteristics (p4-p5).
- `ALPS-EC12E2430803.pdf`: p1 product table, p3 drawing No. 4 (rendered at
  500 dpi).
- `ALPS-EC11L1525G01.pdf`: specification KK-2010-9648, 5LA211-LG2 (encoder),
  5LA2114-L1 (push switch), drawing LE2115L02G (rendered at 400 dpi).
- `TS1103S-12x12-tactile.pdf`: p2 drawing including the circuit diagram, p3
  ratings.
- `HS242L01W4S01-OLED.pdf`: p6 mechanical drawing (rendered at 400 dpi), p7 pin
  definition, p8 interface straps, p9 absolute maximum, p10 electrical, p14-p15
  power sequence.
- `TF-PUSH-microSD.pdf`: p1 drawing with pin table and land pattern.
- ADR 0006, `docs/pin-allocation.md`.

## U3, U4: MCP23017-E/SO

Pinout re-derived from Table 2-1, SOIC column, then diffed: GPB0-7 = 1-8,
VDD 9, VSS 10, NC 11, SCK 12, SDA 13, NC 14, A0-A2 15-17, RESET 18, INTB 19,
INTA 20, GPA0-7 21-28. Our symbol matches pin for pin (section 1 dump).

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| U3.9 / U4.9 | P3V3_DAISY | VDD, 1.8-5.5 V | 3.3 V | CLEAN |
| U3.10 / U4.10 | GND | VSS | GND | CLEAN |
| U3.12/13, U4.12/13 | I2C_SCL / I2C_SDA | SCK, SDA | R20/R21 2.2k to 3.3 V | CLEAN |
| U3.15/16/17 | GND/GND/GND | A0-A2, "Must be externally biased" | strapped | CLEAN, address 0100 000 = **0x20** |
| U4.15/16/17 | P3V3_DAISY/GND/GND | same | strapped | CLEAN, 0100 001 = **0x21** |
| U3.18 / U4.18 | P3V3_DAISY | RESET, "Must be externally biased" | tied high | CLEAN |
| U3.19/20, U4.19/20 | open | INTB/INTA outputs | open | CLEAN; firmware polls (pin-allocation.md: 500 Hz, 2 kHz for U4 port B) |
| U3.11/14, U4.11/14 | open | NC | open | CLEAN |
| U3.21-28 | ENC1_A ... ENC4_B | GPA0-7 | ENC1-ENC4 | CLEAN except pin 28, below |
| U3.1-8 | ENC5_A ... ENC8_B | GPB0-7 | ENC5-ENC8 | CLEAN except pin 8, below |
| U4.1/2/3 | ENC0_A/B/PUSH | GPB0-2 | | CLEAN |
| U4.4 | MSP_RST | GPB3 | | CLEAN (section 9 for the far end) |
| U4.21/22/25/26/27 | BTN5/BTN6/BTN1/BTN2/BTN3 | GPA0/1/4/5/6 | | CLEAN |
| U4.28 | BTN4 | GPA7 | input | see below |
| **U3.28, U3.8, U4.28** | **ENC4_B, ENC8_B, BTN4** | Rev C Table 2-1: "Bidirectional I/O". The runbook names an output-only caveat on GPA7/GPB7 in the current revision; that revision is not in the repo. | inputs | **BLOCKED** |

Address pins: Figure 3-6 gives the I2C control byte as `0 1 0 0 A2 A1 A0 R/W`,
and Figure 3-7's footnote ties IOCON.HAEN to the SPI part only, so the I2C
address pins are always live. The two addresses are distinct.

**GPA7/GPB7, BLOCKED and worth unblocking before the order.** If the current
datasheet does make GPA7/GPB7 output-only, two encoders lose their B phase and
one button is dead. The fix costs nothing on the expander side: U4 has six
unused GPIO (GPB4-GPB7 and GPA2/GPA3, all open), so `ENC4_B`, `ENC8_B` and
`BTN4` can move to U4 pins that are not bit 7. Unblock by committing
DS20001952 revision D or later and reading its Table 2-1 and revision history.

Pull-ups: no external pull-ups on any encoder or button line, so every one
depends on firmware setting GPPU. Weak pull-up current is 40-115 uA at
VDD = 5 V (D070); the sheet gives no 3.3 V figure, and the current will be lower
there.

Decoupling: the datasheet gives no bypass requirement. **C26 sits 4.0 mm from
U3.9; U4.9's nearest capacitor is C26 at 32.9 mm** (C27, the other P3V3_DAISY
cap, is 185 mm away by the J1 end). Not a datasheet violation; a 100 nF at U4 is
ordinary practice. QUESTION.

## Encoders

### ENC1-ENC8, EC12E2430803

p1 table: "带轴套型" (bushing type), shaft 25 mm, torque Heavy 25+-15, detent
"无" (none), 24 pulses, vertical, drawing **No. 4**. Rating "Each lead 0.5mA
5V DC, Common lead 1mA 5V DC".

Drawing No. 4, "PCB mounting hole dimensions, viewed from the insertion side":
three terminals **A C B** left to right, 5.0 over the outer two (2.5 pitch),
Ø1 holes; two locating-lug holes 2.0 x 2.1, **13.2 outer edge to outer edge**,
7.5 above the terminal row. No switch terminals on this part.

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| ENCn.A | ENCn_A | terminal A | footprint (-2.54, 3.75) | CLEAN |
| ENCn.C | GND | common, centre | (0, 3.75) | CLEAN |
| ENCn.B | ENCn_B | terminal B | (2.54, 3.75) | CLEAN |
| ENCn.D, ENCn.E | GND | locating lugs | (+-5.6, -3.75), slots 2.5 x 2.3 | CLEAN: lugs grounded; centres +-(13.2/2 - 1) = +-5.6, 7.5 above the terminals |

The footprint's 2.54 pitch against the drawing's 2.50 puts the outer leads
0.04 mm off, inside a 1.2 mm hole. The symbol's D/E are the lugs, not switch
pins, which is right for a part with no switch. F.Cu, so the footprint is the
insertion-side view the drawing shows. Lug thickness 0.4 (locating lug detail),
so the slot is generous.

### ENC0, EC11L1525G01

Drawing LE2115L02G, "P.W.B. mounting detail, viewed from mounting side":
D and E (push switch) 5 apart, 7 above the shaft centre; A C B 5 over the outer
two, 7.5 below; two lug slots 1.5 x 2.6 on the shaft line, **12.5 outer edge to
outer edge**; holes Ø1.0 +0.1.

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| ENC0.A / C / B | ENC0_A / GND / ENC0_B | A, common, B | (-2.5, 7.25), (0, 7.25), (2.5, 7.25) | CLEAN |
| ENC0.D / E | ENC0_PUSH / GND | push switch, SPST push-on, D-E | (-2.5, -7.25), (2.5, -7.25) | CLEAN |
| ENC0.6 / 7 | GND | lug slots | (-5.5, -0.25), (5.5, -0.20), slots 1.6 x 2.7 | CLEAN: centres +-(12.5/2 - 0.75) = +-5.5 |

Shaft centre falls at local (0, -0.25): 7 below D/E and 7.5 above A/C/B. Pad 7
is 0.05 mm off pad 6's line, which is nothing.

**Contact current: QUESTION.** ALPS rates the encoder "D.C. 5V 10mA (1mA MIN)"
(5LA211-LG2, 3-1) and the push switch "D.C. 5V 0.1A (MIN 500uA)" (5LA2114-L1,
1). Our only bias is the MCP23017 weak pull-up, under 115 uA even at 5 V and
less at 3.3 V: below both stated minimums by an order of magnitude. Below the
minimum the maker does not stand behind contact resistance or bounce over life.
The EC12E's p1 rating (0.5 mA per lead) states no minimum, so ENC1-ENC8 are less
clear-cut. A 3.3k pull-up on `ENC0_A`, `ENC0_B` and `ENC0_PUSH` (1 mA each)
meets the EC11L's numbers; whether the parameter encoders need the same is
worth asking ALPS or settling on the bench.

## SW4-SW9, TS1103S-12x12

p2 circuit diagram: **1-2 joined, 3-4 joined, the contact between the two
bars.** Top view: 1 top-left, 2 top-right, 3 bottom-left, 4 bottom-right, 12.5
across and 5.0 down. p3: 1 pole 1 throw, DC 12 V 50 mA max, no minimum.

Footprint (F.Cu, local): 1 (-6.25, -2.54), 2 (6.25, -2.54), 3 (-6.25, 2.54),
4 (6.25, 2.54). The 12.5 mm pairs are 1-2 and 3-4, the joined bars.

| switch | BTN on | GND on | across the contact? |
|---|---|---|---|
| SW4, SW5, SW6, SW8 | 3 (bar 3-4) | 2 (bar 1-2) | yes |
| SW7, SW9 | 1 (bar 1-2) | 4 (bar 3-4) | yes |

Every switch has its two nets on diagonal pads, one on each bar. The hole
pattern only admits the part at 0 or 180 degrees and a diagonal stays a
diagonal under either. The 2026-09-22 fix is correct. **CLEAN.** (Pitch: 5.08
in the footprint against the drawing's 5.0, in 1.5 mm holes for a part the
drawing gives Ø1.2 holes. Fine.)

## DS1, HS242L01W4S01

| ref.pin | net | source says (p7, p8 "4SPI+FONT") | ours | verdict |
|---|---|---|---|---|
| DS1.1 | GND | GND | GND | CLEAN |
| DS1.2 | P3V3_OLED | VCC, "Power Supply for OLED", 3-5 V abs (p9) | 3.3 V from U5 | CLEAN |
| DS1.3 | OLED_SCK | SCL, serial clock | Patch SM D10 | CLEAN |
| DS1.4 | OLED_MOSI | SDA, serial data | D9 | CLEAN |
| DS1.5 | OLED_RES | RES, low = initialise, "keep this pin pull high during normal operation" | A9, push-pull | CLEAN (firmware sequence, below) |
| DS1.6 | OLED_DC | DC | D2 | CLEAN |
| DS1.7 | OLED_CS | CS1, OLED chip select, low enable | D1 | CLEAN |
| DS1.8 | open | FS0, "Font Chip data output pin" | open | CLEAN |
| DS1.9 | OLED_FONTCS | CS2, font chip select, low enable | R505 10k to P3V3_OLED: font ROM held deselected | CLEAN |

- **Controller:** the p6 mechanical drawing prints "IC: SSD1309", and the p14
  initialisation flowchart uses `0xFD, 0x12` (command lock) and contains no
  charge-pump command. ADR 0006 is right. The single "SSD1306" (p23, handling
  precautions) is a leftover in the vendor's text. Either way the SPI wiring is
  the same.
- **Interface:** the p6 drawing note reads "出厂默认4SPI", factory default 4-wire
  SPI, which is the mode wired. CLEAN.
- **Logic level:** p9 gives "Supply Voltage for Logic, SCL/SDA/RES/DC/CS1/FS0/CS2,
  1.65 to 3.3 V" as an absolute maximum. The Patch SM drives 3.3 V CMOS, which
  sits exactly on that limit with no margin for its regulator's tolerance.
  Real exposure is low (the limit reads as conservative for an SSD1309 input),
  but the document gives no headroom. QUESTION, low.
- **Reset timing:** p14 requires VDD up with RES# low, then RES# high with at
  least 3 us, then initialise. Nothing on the board holds RES during power-up:
  A9 floats until firmware runs. **Firmware requirement:** drive A9 low after
  the rails are stable, hold it at least 3 us, release, then initialise. A9 may
  also be held low by the bootloader's USB host pull-downs (section 3), which
  is harmless.
- **Footprint against the p6 drawing:** pins 2.54 pitch, 20.32 over nine; the
  row is centred on the 43 mm side (11.34 from each edge) and sits 0.5 mm
  inboard of the hole line (2.5 against 2 from the edge); holes Ø3.1 at 39 x 68.
  Ours: pins at x = 0, y +-10.16; holes (-0.5, +-19.5) and (67.5, +-19.5).
  Matches. Pin 1: the drawing is the display-face view; rotated to our frame it
  puts pin 1 at +y, where ours has it (square pad). CLEAN.
- **Doc inconsistency in the vendor sheet:** p5 gives "PCB Size 68.00 x 43.00",
  while the p6 drawing shows PCB 72 with the holes 68 apart. The drawing is
  self-consistent (2 mm margins); p5 is wrong. Matters only for clearance
  (section 8).

## J1, TF-PUSH microSD

p1 pin table: 1 DAT2, 2 CD/DAT3, 3 CMD, 4 VDD, 5 CLX, 6 VSS, 7 DAT0, 8 DAT1.
Land pattern, component-side view: **Cd, 8, 7, ... 1** left to right at 1.10
pitch (8 x 1.10 = 8.80), with the contact row at the top; four shell pads; two
Ø1.00 locating holes 8.00 apart. There is no pin 9: the ninth contact is `Cd`.

| ref.pin | net | source says | ours | verdict |
|---|---|---|---|---|
| J1.1 | open | DAT2 | open | CLEAN (1-bit) |
| J1.2 | SD_DAT3 | CD/DAT3 | R508 47k to 3.3 V, not to the MCU | CLEAN: high at CMD0 keeps the card in SD mode |
| J1.3 | SD_CMD | CMD | D7, R506 47k (plus the module's 47k) | CLEAN |
| J1.4 | P3V3_DAISY | VDD | | CLEAN |
| J1.5 | SD_CLK | CLX | D6 | CLEAN |
| J1.6 | GND | VSS | | CLEAN |
| J1.7 | SD_D0 | DAT0 | D5, R507 47k | CLEAN |
| J1.8 | open | DAT1 | open | CLEAN, see below |
| J1.CD | open | card detect contact | open | CLEAN: no insertion detect, firmware must probe |
| J1.10-13 | GND | shell | GND | CLEAN |

- **Footprint:** the library copy matches the drawing's component-side view
  (contacts at local y -5.3, Cd at x -6.55, pin 1 at x 2.25, 8.80 apart; holes
  8.00 apart). J1 is on **B.Cu** and the board copy has local y negated, a
  genuine flip, so seen from the back it is the drawing. CLEAN. (The
  "RESOLVED: J1 mirroring" note in `design-state.md` says J1's coordinates were
  "stored identical to the library". Today they are y-negated. The note's
  conclusion holds; its description is stale.)
- **Floating DAT1/DAT2:** Electrosmith's own reference (Patch SM Table 2 and
  Fig 1.7, "No pullup resistors necessary") leaves DAT0 and DAT1 with no
  pull-up at all, so a floating DAT1 is no worse than the module maker's
  design. The SD Physical Layer spec, which would be the authority, is not in
  the repo. CLEAN on the evidence available.
- **Bus width:** the module exposes all four data lines (D2-D5) but D2 is spent
  on `OLED_DC`, so 1-bit is the only option. Firmware requirement (section 3).

## Verdicts

| item | verdict |
|---|---|
| U3/U4 pinout, addresses, RESET, INT, NC | CLEAN |
| U3.28 / U3.8 / U4.28 on GPA7/GPB7 | **BLOCKED** (Rev D not in repo) |
| U4 decoupling | QUESTION |
| ENC1-ENC8 pins and lugs | CLEAN |
| ENC0 pins, switch and lugs | CLEAN |
| ENC0 contact current vs ALPS minimum | **QUESTION** |
| SW4-SW9 across the contact | CLEAN |
| DS1 pins, controller, interface, footprint | CLEAN |
| DS1 3.3 V logic at its 3.3 V absolute max | QUESTION, low |
| J1 pins, footprint, flip | CLEAN |
| docs: pin-allocation.md button and encoder counts, design-state J1 note | DEFECT (doc) |

`pin-allocation.md` still describes four buttons (SW4-SW7 on GPA4-GPA7) and ten
parameter encoders "ENC1-ENC10" with U4 "only used 4 of 16 for ENC9/ENC10";
the netmap has six buttons (BTN5/BTN6 on GPA0/GPA1 added) and eight parameter
encoders plus ENC0.

## Defects and questions, ranked

1. **BLOCKED, could disable two encoders and a button:** three inputs on
   GPA7/GPB7. Get the current MCP23017 datasheet; if the caveat is real, move
   `ENC4_B`, `ENC8_B`, `BTN4` to U4's free GPIO (netmap).
2. **QUESTION, degrades over life:** ENC0's contacts run at roughly a tenth of
   ALPS's minimum current. Three 3.3k pull-ups (netmap, values) would satisfy
   the sheet.
3. **QUESTION, degrades:** no local decoupling at U4 (board).
4. **QUESTION, low:** OLED logic inputs driven at their absolute maximum.
5. **Doc:** pin-allocation.md counts; design-state.md J1 note.
