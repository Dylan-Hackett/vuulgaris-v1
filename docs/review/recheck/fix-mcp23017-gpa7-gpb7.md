# Fix: MCP23017 GPA7/GPB7 used as inputs

**Severity: kills the main board's controls.** This supersedes section 04's
BLOCKED item (U3.28, U3.8, U4.28) and should count as a DEFECT in
`00-summary.md`.

## Status, 2026-10-03

Done: steps 2-6 and step 8's docs. The schematic is regenerated and checked
956/956 with KiCad's own netlister (`netcheck.py`); the board is routed, DRC
has 0 errors, `boardcheck.py` has 0 parity mismatches, and the fab package is
rebuilt. Step 1 was done on 2026-10-04: `datasheets/` now holds DS20001952E,
downloaded from Microchip, and the three places quoted below were read in that
PDF (p1 Features; Table 2-1 on p11, rows GPB7 and GPA7; the Revision D entry in
the history on p39). They say what this note says. Not done: step 7 (firmware).

How the board got there, since none of it was routed by hand in one sitting:

- `ENC4_A`, `ENC4_B`, `ENC8_A`, `ENC8_B`: Freerouting 2.4.1, headless, every
  other track protected. It could not get all four out of U4 with the board's
  0.8/0.4 vias (0.05 mm short between two vias under the north row), so these
  four nets use **0.6/0.3 vias**, eight of them. That is inside the board's
  own minimum (0.5/0.3) and the faceplate already uses 0.5 and 0.6. About
  1.5 mm of `ENC8_B` at U4.6 is necked to 0.1874 mm by the router.
- `BTN4`: placed by hand after the router failed it. South out of U4.7, a
  0.6/0.3 via, B.Cu west at y 127.3, a second via beside its old In1 trunk.
- Ground ties: U3.8 and U3.28 by `gndvias.py`. U4.8 by a track under pad 9 to
  U4.10's existing via. U4.28 by a track to a 0.8/0.4 via at (172.25, 116.5),
  3.1 mm out, just past `gndvias.py`'s 3.0 mm reach.
- ENC8 stayed on GPB4/GPB5 and ENC4 on GPA2/GPA3. The swap this note offers
  below was trial-routed and did no better.

## What is wrong

Microchip's current MCP23017 datasheet says GPA7 and GPB7 are **output only**
on the MCP23017 (I2C part; the SPI MCP23S17 is not affected):

- DS20001952E (July 2026), page 1, Features: "16-Bit Remote Bidirectional I/O
  Port (Pins GPA7, GPB7 are output only for MCP23017)".
- Table 2-1, rows GPA7 and GPB7: "Output only (MCP23017)".
- The change first appeared in Revision D (June 2022). Revision E keeps it.

The reason Microchip gave, as relayed in [Adafruit issue
#57](https://github.com/adafruit/Adafruit_CircuitPython_MCP230xx/issues/57)
and [Hackaday](https://hackaday.com/2023/02/03/mcp23017-went-through-shortage-hell-lost-two-inputs/):
transitions on these pins while they are inputs can corrupt the I2C **SDA**
signal. Microchip has published no detailed mechanism. The silicon
was not changed; only the document was. Every MCP23017 you can buy has the
problem.

The repo's copy, `datasheets/Microchip-MCP23017-datasheet.pdf`, was Revision C
until 2026-10-04 (`fetch-datasheets.sh` fetched `20001952c.pdf`), which
predates the note. That is why the design used these pins. It is Revision E
now.

## Why it is worse than three dead inputs

U3 and U4 share one I2C bus with nothing else on it but the Daisy (`U1.B7`
SCL, `U1.B8` SDA) and the pull-ups R20/R21. A corrupted SDA does not stay on
one pin: it can garble any transaction to either expander, so all eight
parameter encoders, ENC0 and all six buttons are at risk.

## The three affected signals today

| net | part | pin | port bit |
|---|---|---|---|
| `ENC4_B` | U3 (0x20) | 28 | GPA7 |
| `ENC8_B` | U3 (0x20) | 8 | GPB7 |
| `BTN4` (SW7) | U4 (0x21) | 28 | GPA7 |

U3 is full (16 encoder lines), so the fix has to go through U4. U4's free pins
are GPB4 (5), GPB5 (6), GPB6 (7), GPB7 (8, also output only, so unusable),
GPA2 (23) and GPA3 (24): five usable.

## The move

Move **both** lines of ENC4 and ENC8, not just their B lines, so each encoder
is read from one port in one I2C read. A quadrature pair split across two
chips is sampled in two transactions, and the skew between them can drop or
reverse steps on a fast turn. Five signals, five usable pins: an exact fit.

| net | from | to | why there |
|---|---|---|---|
| `ENC4_A` | U3.27 GPA6 | **U4.23 GPA2** | GPA row faces the encoders (north side of U4) |
| `ENC4_B` | U3.28 GPA7 | **U4.24 GPA3** | same port as `ENC4_A` |
| `ENC8_A` | U3.7 GPB6 | **U4.5 GPB4** | same port as `ENC8_B`; port B is already polled at 2 kHz for ENC0 |
| `ENC8_B` | U3.8 GPB7 | **U4.6 GPB5** | |
| `BTN4` | U4.28 GPA7 | **U4.7 GPB6** | GPB row faces SW7 (south side of U4) |

After the move, U3.7 and U3.27 are unconnected. The four GPA7/GPB7 pins
(U3.8, U3.28, U4.8 and U4.28) must **not** be left floating; tie them to
`GND`. The reported trigger is a *transition* on one of these pins while it is
an input, and every MCP23017 pin is an input from power-up until firmware
writes IODIR. A floating pin can toggle in that window, and later too if
firmware ever leaves it an input. Tied to ground it cannot move. U4.8 is
already floating on the current board, so this applies even to the pin
nothing uses today. U4 then has no free GPIO left.

Board geometry for the routing (sheet mm): U3 at (151.0, 105.0) and U4 at
(183.2, 120.0), both on F.Cu. ENC4 is at (140.1, 84.6) and ENC8 at (184.1,
84.6), north of both. SW7 is at (134.3, 147.7), south-west of U4. U4's
GPA2/GPA3 pads are at y 114.94 (north row) and GPB4-GPB6 at y 125.06 (south
row). The ENC8 lines have to come round U4 to its south row; if that routes
badly, swap the assignments (ENC8 on GPA2/GPA3, ENC4 on GPB4/GPB5).
Whichever way, each pair stays on one port.

## Steps

1. **Datasheet.** Replace `datasheets/Microchip-MCP23017-datasheet.pdf` with
   DS20001952E and update the URL in `datasheets/fetch-datasheets.sh` (ask
   before downloading, per CLAUDE.md).
2. **Netmap.** In `hardware/kicad/tools/netmap.json`, reassign the five nets
   per the table, remove U3.7 and U3.27 from their nets, and put U3.8, U3.28,
   U4.8 and U4.28 on `GND`.
3. **Schematic.** From `hardware/kicad/`, run
   `python3 tools/mksch.py && python3 tools/netcheck.py` (with `set -o
   pipefail` if piped). Then F8 in Pcbnew to pull the new nets in.
4. **Board.** The five old tracks become ratsnest. Delete them, then route
   the new connections by hand (hand-routing is yours, per CLAUDE.md). No
   parts move.
5. **Checks.** `boardcheck.py`, `drc.py` (0 errors, 0 unconnected),
   `place.py --check`, `schdraw.py`, `gerbercheck.py`. Diff against HEAD for
   anything DRC cannot see.
6. **Fab package.** Regenerate the BOM, CPL, gerbers, drill files and
   `hardware/vuulgaris-v1-fab.zip` in the same commit (CLAUDE.md's command
   list).
7. **Firmware**, when written:
   - Set U3 GPA7/GPB7 and U4 GPA7/GPB7 as **outputs driven low** (IODIR bit
     0, OLAT bit 0), matching their ground tie. **Never drive them high**: that
     would short a driven output to GND. Leaving them as inputs is also safe
     once they are tied, because a grounded input never transitions.
   - Read ENC4 from U4 port A, ENC8 and BTN4 from U4 port B.
   - Poll U4 port B at 2 kHz as before (it now carries ENC0, ENC8 and BTN4).
     U4 port A at 500 Hz is enough for ENC4, as for the other parameter
     encoders.
8. **Docs** in the same commit:
   - `docs/pin-allocation.md`: the button table (SW7 to GPB6), the encoder
     tables, the "free GPIO" counts, and a line on why GPA7/GPB7 are unused.
   - `mockups/generate-faceplate.py` (the `GPIO` list near line 1641), then
     regenerate `hardware/placement-panel-facing.txt` and confirm
     `place.py --check` still says all 24 are on their holes. Only the note
     column should change.
   - `docs/design-state.md` "GPIO ... 7 pins still free" becomes 0.
   - `docs/review/recheck/04-digital-io.md` and `00-summary.md`: BLOCKED
     becomes DEFECT (kills), fixed in the commit that lands this.

## If boards are already built

There is no fix without a rework.
- **Firmware only:** configure the three pins (and U4 GPB7) as outputs. The
  bus is then safe once firmware runs, though not during the power-up
  window before it does. ENC4 and ENC8 lose direction sensing and BTN4 is
  dead.
- **Bodge:** cut the three traces at U3.28, U3.8 and U4.28, and wire them to
  U4.24, U4.6 and U4.7 (GPA3, GPB5, GPB6). That leaves each encoder split
  across two chips: acceptable for slow turns, and it can miss steps on fast
  ones.

## Sources

- [MCP23017/MCP23S17 datasheet DS20001952E](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-MCP23S17-16-Bit-IO-Expander-with-Serial-Interface-DS20001952.pdf), page 1 and Table 2-1, revision history
- [Adafruit_CircuitPython_MCP230xx issue #57](https://github.com/adafruit/Adafruit_CircuitPython_MCP230xx/issues/57) (Microchip's SDA explanation, relayed)
- [RobTillaart/MCP23017_RT issue #40](https://github.com/RobTillaart/MCP23017_RT/issues/40)
- Board and netmap positions read from `hardware/kicad/vuulgaris.kicad_pcb` and `hardware/kicad/tools/netmap.json` at commit 95a5074.
