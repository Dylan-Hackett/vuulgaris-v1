# 09: Main board to faceplate interconnect

Block: main-board `J12` (BOOMELE C5665, through-hole, B.Cu) to faceplate `J1`
(hanxia HX JN2.54-2x5P TP H8.9, SMD, B.Cu), the ribbon between them, the
nets on both ends, BSL entry, power across the connector, and the spacing.

Sources: `BOOMELE-C5665-2x5-box-header.pdf` (side elevation and "P.C.B
Layout", rendered); `hanxia-HX-JN2.54-2x5P-TP-H8.9.pdf` (all views and the
specification block, rendered); `TI-MSP430FR2675-datasheet.pdf` (SLASEO5D:
Figure 7-1 p10, Table 7-2 p22, Table 7-4 p23, 8.1 p24, 8.4 p25, Table 9-4
p53); `SLAU550-MSP430-FRAM-BSL.pdf` (Rev AB: §3.1.1 p4, §3.3.2.1, §3.3.3 and
§3.4 p7); `Electrosmith-Patch-SM-v1.0.5.pdf` (pin table, power outputs);
`AMS1117-datasheet.pdf` p2; both netmaps (`hardware/kicad/tools/netmap.json`,
`hardware/faceplate/design/netmap.json`) and both `.kicad_pcb` files;
`hardware/faceplate/README.md` §5; ADR 0005; open questions Q13, Q21, Q22,
Q23.

## 1. Pin for pin

Nets read from both netmaps and from the pads in both boards (section 1
proved netmap = schematic = board on each). Positions are pad centres
converted to the panel frame (main: pcb + (6.995, 9.000), sheet = pcb +
(100, 50); faceplate: sheet = panel + (100, 50)). `J1`'s SMD pads sit 2.155
outboard of its pins, so its pin rows are at y 111.23 / 113.77; the table
gives the pads.

| pin | `J12` net | `J12` pad, panel | `J1` net | `J1` pad, panel | verdict |
|---|---|---|---|---|---|
| 1 | `MSP_TEST` | (234.075, 101.770) | `MSP_TEST` | (234.075, 115.925) | CLEAN |
| 2 | `GND` | (234.075, 99.230) | `GND` | (234.075, 109.075) | CLEAN |
| 3 | `MSP_RST` | (231.535, 101.770) | `MSP_RST` | (231.535, 115.925) | CLEAN |
| 4 | `GND` | (231.535, 99.230) | `GND` | (231.535, 109.075) | CLEAN |
| 5 | `MSP430_RXD` | (228.995, 101.770) | `MSP430_RXD` | (228.995, 115.925) | CLEAN |
| 6 | `GND` | (228.995, 99.230) | `GND` | (228.995, 109.075) | CLEAN |
| 7 | `MSP430_TXD` | (226.455, 101.770) | `MSP430_TXD` | (226.455, 115.925) | CLEAN |
| 8 | `GND` | (226.455, 99.230) | `GND` | (226.455, 109.075) | CLEAN |
| 9 | `P3V3_MSP430` | (223.915, 101.770) | `P3V3_MSP430` | (223.915, 115.925) | CLEAN |
| 10 | `GND` | (223.915, 99.230) | `GND` | (223.915, 109.075) | CLEAN |

Every signal wire in the ribbon has a ground wire on each side (1 and 3, 5,
7, 9 between the even grounds).

## 2. Physical mapping

Computed from the pads, not taken from the README:

| | `J12` | `J1` |
|---|---|---|
| board side | main B.Cu, rot 180 | faceplate B.Cu, rot 180 |
| faces | down, away from the faceplate | down, toward the main board |
| centre, panel | (228.995, 100.5) | (228.995, 112.5) |
| pin 1 | +x end | +x end |
| odd row | +y | +y |
| key wall | +y: silk notch on the odd-row wall in the library (y +4.40), flipped and turned to +y | +y: Fab notch 4.5 wide on the odd-row wall in the library (y +4.45), flipped and turned to +y |

The two headers differ by a pure translation of 12.0 mm in y (and their
heights). Both drawings put the pin-1 triangle on the keyed wall at one end
(C5665 side elevation: the triangle and the 4.5 key window on the same face;
hanxia side elevation: the triangle at one end of the face that carries the
4.50 key), and both footprints put pin 1 at that end of the key-wall row. A
box header's ten posts are symmetric under a half turn; the key is the only
thing that fixes a socket's orientation. With the key on the same wall of
two identically oriented headers, a straight IDC cable with both sockets
crimped on the same face puts socket contact k over the same post at both
ends, whatever the socket's own numbering convention, so **pin n meets pin n
with no row swap**. The cable leaves `J12` toward +y (the cutout), drops
under the main board and rises into `J1` from its -y side: a bend about the
cable's width, never a twist. CLEAN.

What this needs at assembly, and nothing on paper can check: `J12` is
through-hole and symmetric, so it must be soldered with its key on the
silkscreen notch; `J1` is placed by JLC, so the CPL rotation has to put
hanxia's key where the footprint expects it (section 11 checks the CPL).

## 3. Direction of every line

| pin | net | driven by | received by | verdict |
|---|---|---|---|---|
| 5 | `MSP430_RXD` | main `U1.A3`, Patch SM PA0, alt UART4_TX (section 3) | faceplate `U1.5`, P1.5/UCA0RXD, input (Fig 7-1 p10; Table 7-2 p22) | CLEAN: TX into RX |
| 7 | `MSP430_TXD` | faceplate `U1.4`, P1.4/UCA0TXD, output (same) | main `U1.A2`, PA1, alt UART4_RX | CLEAN: TX into RX |
| 3 | `MSP_RST` | main `U4.4` (MCP23017 GPB3, on `P3V3_DAISY`); nothing else on the main board | faceplate `U1.2` RST/NMI/SBWTDIO, with R1 47k to `P3V3_MSP430`, C4 1 nF C0G to GND, TP2 | CLEAN: one driver |
| 1 | `MSP_TEST` | nobody: `J12.1` has no track on the main board | faceplate `U1.3` TEST/SBWTCK, TP1; "This pin always has an internal pulldown enabled" (Table 7-4 p23) | CLEAN: undriven, held low inside the MSP |
| 9 | `P3V3_MSP430` | main `U6` (AMS1117-3.3) | faceplate C1 10 uF, C2 100 nF, U1 DVCC | CLEAN |

Idle levels: R2 and R3 (47k to `P3V3_MSP430`, faceplate) hold both UART
lines high while either end is in reset, so the Daisy never sees a false
start bit from a resetting MSP430 and the MSP430's RX does not float while
the Daisy boots. They are also the TCK/TMS termination SLAU550 §3.3.2.1 (p7)
asks for; its 1 nF pull-downs are left off (Q21, accepted there).

`U4` powers up with every pin an input (section 2), so `MSP_RST` follows R1
up with the MSP rail. When `U4` drives it high, it drives `P3V3_DAISY` into a
pin whose absolute maximum is DVCC + 0.3 V (8.1, p24); the two 3.3 V rails
are separate regulators, AMS1117-3.3 at 3.235-3.365 V over line, load and
temperature (p2), the Patch SM's 3V3 unpublished. Inside the limit while
both are in regulation.

### Power-down back-feed (QUESTION)

`P3V3_MSP430` is `U6`, an AMS1117 fed from the Daisy's 5 V (`P5V`, Patch SM
A6). It falls out of regulation once `P5V` drops below about 4.4 V. The
Daisy's own 3V3 (A10) comes from a regulator Electrosmith does not describe.
If that 3V3 outlasts `U6` on the way down, the Daisy's UART TX, idling high,
drives `MSP430_RXD` into an unpowered MSP430 through its input clamp. There
is no series resistance anywhere on that line, and SLASEO5D 8.1 (p24) caps
the diode current at any pin at +-2 mA, which an STM32 push-pull output can
exceed. Power-up is safe: PA0 is not a driven output until firmware runs,
and `U4` starts as inputs. This needs a scope at bring-up (`P3V3_DAISY`,
`P3V3_MSP430` and `MSP430_RXD` on a power-off). If the window exists, a
2.2k series resistor on `MSP430_RXD` caps the current near 1.4 mA and costs
nothing at 9600 or 115200 baud; the same reasoning applies to `MSP_RST` if
firmware ever drives GPB3 high rather than leaving it an input.

## 4. BSL entry

| requirement | source | what this hardware does | verdict |
|---|---|---|---|
| UART BSL pins: P1.4 transmit, P1.5 receive, plus RST and TEST for the entry sequence | SLASEO5D Table 9-4 (p53) | P1.4/P1.5 are PT pins 4/5 (Fig 7-1), on `MSP430_TXD`/`MSP430_RXD`, the runtime UART (Q21) | CLEAN |
| hardware entry sequence on RST and TEST | Table 9-4; SLAU550 §3.3 | RST is drivable (U4 GPB3); TEST is not connected on the main board | not available, by design (ADR 0005) |
| blank device: "jumps directly to the BSL and bypasses the entry sequence only when the reset vector has a value of 0xFFFF" | SLAU550 §3.3.3 (p7) | a reel part is blank, so the first flash needs no entry sequence | CLEAN |
| "If no communication has been established within ten seconds, the device enters LPM4 ... a reset or NMI must be received" | SLAU550 §3.4 (p7) | `U4` can pulse `MSP_RST`, which gives the Daisy a fresh ten seconds without a power cycle | CLEAN |
| 9600 baud to start; 8 data bits, even parity, 1 stop; half duplex; 1.2 ms before a new character | SLAU550 §3.1.1 (p4) | firmware only; the Daisy's UART4 must be set to 8E1 for the flash and back to the runtime framing after | note for `fw-daisy` |
| levels | Patch SM pin table: A2/A3 0 to 3V3 | 3.3 V logic both ends; no divider anywhere; Q13 closed by deletion and the gate-output path it covered no longer exists | CLEAN |

After the first flash the reset vector is no longer 0xFFFF, so a later
reflash over this connector depends on the MSP430 application jumping to its
own BSL on command. If an image cannot do that, recovery is Spy-Bi-Wire: pull
the ribbon from `J12` and drive TP1-TP4 or the ribbon socket from a LaunchPad
or CAPTIVATE-PGMR (ADR 0005, revised 2026-09-28). With the ribbon still in,
`U4` would fight the tool on RST if it is driving. That is a documented
trade, not a defect; adding a spare `U4` pin to `J12.1` at a later spin
would make the full hardware entry sequence available from the Daisy.

## 5. Power across the connector

| item | value | source | verdict |
|---|---|---|---|
| rail | `P3V3_MSP430`, one pin (9), from main `U6` | netmaps | CLEAN |
| load | MSP430 at 16 MHz, 0% FRAM cache hit, 105 C: 3.75 mA max; plus three 47k pull-ups (0.2 mA) and CapTIvate conversion current | SLASEO5D 8.4 (p25) | well under 10 mA |
| pin rating | C5665 1 A; hanxia 3 A | both drawings' specification blocks | CLEAN |
| grounds | 5 of 10 (2, 4, 6, 8, 10) | | CLEAN |
| main-board run | `U6.2` to `J12.9`: 56.6 mm of 0.5 mm track, F.Cu and In1.Cu, 2 vias; C22 10 uF and C23 100 nF 7 mm from `U6` | board | CLEAN |
| faceplate run | `J1.9` to the MSP430: 79.4 mm of 0.225-0.3 mm track on B.Cu, about 0.17 ohm, under 1 mV at 5 mA | board | CLEAN |
| faceplate decoupling | C2 100 nF 3.1 mm from DVCC (`U1.1`), C1 10 uF 9.0 mm | board | CLEAN here; distances against TI's layout guidance are section 10 |

## 6. Mechanical

The board-to-board spacing is not set by this connector: the cable takes up
any gap. It is set by the Alpha pot shoulder, 10 +-0.5 (section 8), and
nothing else in the stack touches both boards. Against that range:

- `J1` stands 9.60 +-0.25 off the faceplate. At the tightest stack (9.5 gap,
  9.85 header) its body reaches 0.35 mm below the main board's top surface,
  which is fine only because it sits over the cutout: Edge.Cuts gives the
  hole as panel x 216.995-240.995, y 106.5-118.5, 1.5 mm corner radius, and
  `J1`'s 20.30 x 8.90 body centred on (228.995, 112.5) clears it by 1.85 in x
  and 1.55 in y. The faceplate floats +-0.25 (faceplate README §3). CLEAN.
- `J12`'s 8.8 mm body hangs from the main board's back and ends 1.6 mm short
  of the cutout's edge in y. Its 3.3 mm tails come 1.7 mm through the top,
  under nothing on the faceplate taller than 1.6. CLEAN.
- Both mated sockets hang below the main board, so the case floor needs room
  for `J12` (8.8) plus a socket and the ribbon's fold; the faceplate README
  asks for about 15 mm there. Enclosure note, no defect.

## Verdicts

| item | verdict |
|---|---|
| pin-for-pin nets, both netmaps and both boards | CLEAN |
| physical mapping: pin n to pin n, no row swap | CLEAN |
| UART direction, TX into RX both ways | CLEAN |
| RST: one driver; TEST: undriven, internal pull-down | CLEAN |
| BSL pins and blank-device entry | CLEAN |
| hardware BSL entry sequence from the Daisy | not available, documented (ADR 0005) |
| power-down back-feed on `MSP430_RXD` | QUESTION |
| power across the connector | CLEAN |
| spacing and cutout clearance | CLEAN |
| ADR 0005: "nothing on the main board drives RST any more" | DEFECT, doc |

## Defects, ranked

Nothing here would kill the board.

1. **QUESTION, degrades the MSP430 over time if real:** on power-down the
   Daisy's UART TX may back-feed the MSP430 through `MSP430_RXD` with no
   series resistance, past the +-2 mA pin limit, if the Daisy's 3V3 outlasts
   `U6`. Scope it at bring-up; a 2.2k series resistor closes it.
2. **Doc:** ADR 0005's superseded block says the 10 s time-out recovery is a
   power cycle "because nothing on the main board drives RST any more".
   `U4` GPB3 drives `MSP_RST` now (main netmap `U4.4`), so a reset recovers
   it. The BSL TODO in `fw-daisy` that still plans RST + TEST was reported in
   section 3; the `fw-touch` notes are section 10's.
3. **Note:** the Daisy's UART must run 9600 8E1 while flashing (SLAU550
   §3.1.1). Nothing in `fw-daisy` does BSL yet.
