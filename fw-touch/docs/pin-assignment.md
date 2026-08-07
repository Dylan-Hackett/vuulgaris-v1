# Pin assignment - MSP430FR2675TPTR

> **Generate this in CapTIvate Design Center first, then lay out the PCB to match.**
> Not the other way around. A swapped pair produces garbage interpolation on a board that
> passes every electrical check.

## Electrode order per pad

| Net | CapTIvate element | Position along pad |
|---|---|---|
| RX0 | **E00** | segments 0 **and 4** (both ends, one net) |
| RX1 | **E01** | segment 1 |
| RX2 | **E02** | segment 2 |
| RX3 | **E03** | segment 3 |

Four pads, four electrodes each, **16 self-cap touch IO total**, which is exactly the part's
capacity. No spare electrodes.

**RX0 is one net.** Both end groups must be connected on the board. TI requires this for the
default slider algorithm to work. Route the return on the layer below, never under the
electrodes.

## Measurement blocks

The FR2675 has **4 parallel measurement blocks** (confirmed for this exact part number in TI
SLAA842). Each slider's four elements should sit in **one block** so they are measured in
parallel. This is what buys the linearity: elements measured in separate cycles sit at
ground potential and degrade their neighbours' linearity, which is why TI does not recommend
devices with fewer than four blocks for sliders.

Consequence: the four sliders scan in **four sequential cycles**, so per-pad update rate is
1/4 of a single-slider design. Measure it: see the tuning table in the README.

## Serial link to the Daisy

| Signal | MSP430 peripheral | Daisy side |
|---|---|---|
| UART Tx/Rx | eUSCI_A | A2/A3 (UART4) or B7/B8 (UART4 alt) |
| I2C SCL/SDA | eUSCI_B | B7/B8 (I2C1) |
| IRQ | any GPIO | 1 GPIO, data-ready, avoids polling |
| BSL entry | RST, TEST | 2 GPIO |

> **[UNVERIFIED - blocks layout]** eUSCI_A and eUSCI_B may share physical port pins on the
> 48-pin PT package. If they do, routing both UART and I2C needs **0R jumpers to select**
> rather than being free. Pull the FR2675 datasheet pin function table for the PT package.
> `docs/notes/open-questions.md` Q2.

## Programming and test connectors on the faceplate

| Connector | Populate on production? | Why it exists |
|---|---|---|
| CAPTIVATE-PGMR header | **No** (DNP) | Design Center live data. Tuning against the actual pads, in the actual enclosure, next to the actual switching supply is the only tuning that counts. |
| SBW test pads (TEST, RST, 3V3, GND) | pads only, no connector | Free, and the recovery path. |

## Per-electrode ESD

No overlay means ESD is on us. Per electrode: **470R-1k series resistor** plus a
**TPD1E10B06 TVS** to ground on the **electrode side** of the resistor.
**5 electrodes x 4 pads = 20 of each.** Place near the MCU with a low-impedance ground path.
