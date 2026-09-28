# Faceplate PCB — next session: layout

Paste everything below the line into a **new** Claude Code session opened in
`/Users/dylanhackett/V1`. `CLAUDE.md` loads by itself. (The schematic kickoff is in git
history; that session ran 2026-09-27/28, commits `d6ba15b`..`9ed8f22`.)

---

We're laying out the faceplate PCB for Vuulgaris V1. The schematic is complete and
verified (`mksch → netcheck` 145/145, 41 nets); the board is still the skeleton — outline
and `J1` only. The main board is finished; don't change it unless a faceplate constraint
forces it, and tell me before you do.

**Read first:**

1. `hardware/faceplate/README.md` — status, **the loop** (`--project faceplate` on every
   tool), §1–§7 constraints (§2's height table matters now), the layout checklist.
2. `hardware/faceplate/design/design.py` — every block and the TI figure it came from.
   `netmap.json` is the intent.
3. ADRs `0003` (pad geometry, stackup, layout rules), `0004` (ESD network and where it
   goes), `0005` (PGMR via `J1`, SBW pads); `docs/pin-allocation.md` (the corrected
   one-pin-per-block CapTIvate table).
4. `mockups/generate-faceplate.py` — the source of the pad copper.

**Settle with me first, one at a time, each with your recommendation:**

a. **How the pad copper enters the board.** `E1`–`E4` are symbols with no footprint.
   The generator's copper has to land on `PADp_RXn` nets so boardcheck and DRC see it:
   one generated footprint per pad (custom pads), zones, or something else. Cross-check
   the geometry against TI's SLAA891 OpenSCAD output before committing copper.
b. **Where `U1` and its sixteen networks sit.** ADR 0003 says centre the MCU on the pad
   group and equalise trace lengths; each pad's four lines now come from four different
   blocks around the package. TVS on the electrode side with a short ground, 470R near the
   pin, decoupling within millimetres. Mind §2: nothing over the main board's tall parts
   that does not fit (every faceplate part except `J1` is ≤1.6mm -- `U1`'s LQFP max;
   the 10µF 0805 is ≤1.45, the crystal 0.9, the TVS 0.45).
c. **The UART's exit.** ADR 0003 wants digital lines to leave by the edge away from the
   electrodes, but `J1` is fixed by the main board at panel (228.995, 112.5), in the gap
   between pads 3 and 4. Say how `MSP430_TXD`/`RXD` get there without running under pads.

**Then place, then stop for me to route.** Hand-routing is mine: place the parts, leave the
ratsnest, and say what to route. The board is edited by pcbnew script or by me in Pcbnew;
after a script writes, I File → Revert before touching it. Loop green after each step;
panelcheck's hole TODOs are for this phase too.

**Open, not blocking layout:** `J1`'s pin 1 / key with a real ribbon (I'm doing the
mock-up); there is no faceplate BOM/CPL tooling yet
(`mkbom.py` is main-board only) — chosen so far: U1 C2052972, J1 C41376028, Y1 C32346,
TVS C48260, 22pF C1653, 470R C23179, 47k C25819, 100nF C14663, 10µF C15850, 1µF C28323,
1nF C0G C163508 (not the Basic X7R C1588 -- see design.py).
Q1 and Q17 are still open; the faceplate lives with them.

**Rules:** `CLAUDE.md` applies throughout. Commit per logical step, no AI co-author
trailer. Never commit a board that fails DRC.
