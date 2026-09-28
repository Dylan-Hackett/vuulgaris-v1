# Faceplate PCB — next session: the schematic

Paste everything below the line into a **new** Claude Code session opened in
`/Users/dylanhackett/V1`. `CLAUDE.md` loads by itself. (The previous kickoff — settle the
four questions, the +2mm offset, the project setup — is in git history, done 2026-09-27.)

---

We're doing the faceplate schematic for Vuulgaris V1. The KiCad project and its
verification loop exist and pass on a skeleton (outline + the cable header `J1`). The main
board is finished; don't change it unless a faceplate constraint forces it, and tell me
before you do.

**Read first:**

1. `hardware/faceplate/README.md` — status, **the loop** (every tool takes
   `--project faceplate`), then the handoff from the main board. §1–§7 are constraints.
2. ADRs `0002`–`0005` and `0012` in `docs/decisions/`; `docs/pin-allocation.md`
   (CapTIvate blocks, UART, system pins); `docs/notes/open-questions.md` Q1, Q7, Q17, Q22.
3. `hardware/faceplate/design/design.py` and `netmap.json`, and
   `hardware/kicad/tools/proj.py` / `panelcheck.py`, so you know what the loop checks.

**Rule for this phase:** build every IC's support circuit from the manufacturer's
reference circuit, never from first principles. Datasheets are in `datasheets/`
(`fetch-datasheets.sh`; ask before downloading anything new). Check pin numbers against
the datasheet's own table, not a KiCad or LCSC symbol. Say explicitly in the commit which
parts came from a reference circuit and which did not.

**Settle with me first, one at a time, each with your recommendation:**

a. **ESD count: 16 or 20** series resistors and TVS diodes? ADR 0004 and the README say
   20 (5 electrode segments x 4 pads); `design-state.md` §3 says 16 (4 nets per pad, since
   RX0's two ends are one net). It turns on where RX0's two ends join relative to the
   resistor and the TVS. TI's no-overlay guidance (SLAA843, the CapTIvate design guide) is
   the source.
b. **`J1`'s real part.** It must be an SMD 2x5 2.54mm shrouded box header (a through-hole
   one puts pins through the front face between pads 3 and 4). JLC-stocked, Basic if
   possible, checked in JLC's parts library in the browser; footprint from the
   manufacturer drawing. Its key/pin-1 orientation gets confirmed with a real ribbon
   (README §5); I'll do the mock-up.
c. **The CAPTIVATE-PGMR connector**: which connector and pinout TI's PGMR expects on the
   target, from TI's own user guide.

**Then the schematic**, into `design/netmap.json` + `design/design.py`, with
`mksch → netcheck` green after each step:

- MSP430FR2675TPT (LCSC C2052972): symbol + footprint into the shared library, pinout
  checked against SLASEO5D Figure 7-1 / Table 7-2 (PT), footprint against TI's PT package
  drawing.
- Its supply, decoupling, VREG, RST/TEST network (SBW needs a specific RST pull-up and
  cap — TI's hardware tools guide), from TI's reference schematics.
- 47k pull-ups on P1.4/P1.5 (README §6). The 32.768kHz crystal on pins 46/47 with its
  load caps (Q22).
- The 16 CapTIvate lines, one block per pad, `RX0→E00 … RX3→E03`, through the ESD network
  from (a). The electrodes themselves as a symbol per pad for now; their copper comes from
  the generator in the layout phase.
- SBW pads (TEST, RST, 3V3, GND) and test points on TX, RX, RST, TEST.

Every part on the faceplate goes on the **back** and must be **SMD**: the front is exposed
ENIG copper under the player's hand. Mind the 10mm gap's height limits (README §2).

**Rules:** `CLAUDE.md` applies throughout. Commit per logical step, no AI co-author
trailer. Split into a new session before layout.
