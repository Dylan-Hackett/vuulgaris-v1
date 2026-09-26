# Faceplate PCB — session kickoff

Paste everything below the line into a **new** Claude Code session opened in
`/Users/dylanhackett/V1`. `CLAUDE.md` loads by itself; this points the session at the rest.

---

We're starting the faceplate PCB for Vuulgaris V1. The main board is finished and ready to
order. Don't change it unless a faceplate constraint forces it, and tell me before you do.

**Read first, in this order:**

1. `hardware/faceplate/README.md` — it opens with the handoff from the main board. Treat
   §1–§7 as constraints, not suggestions.
2. ADRs `0002` (MSP430FR2675), `0003` (comb pads, RX0 wraparound), `0004` (exposed copper,
   ENIG, no overlay), `0005` (BSL over the Daisy UART) in `docs/decisions/`.
3. `docs/notes/open-questions.md` — Q1, Q17, Q21, Q22.
4. `mockups/generate-faceplate.py` and `hardware/placement-panel-facing.txt`.
5. `docs/design-state.md` §3 (capacitive sensing) and §4 (MSP430 programming); §9 is
   superseded where the handoff says so.

**Before any layout, settle these with me, one at a time, each with your recommendation:**

a. **Panel height** — 132.81mm (board + 14, 1mm behind the board) or 137.81mm (the 6mm the
   board needs to slide in)? Handoff §1.
b. **Pad geometry** — the README says 12mm wide, 80 teeth, 6mm gap; the generator's SVG says
   10mm at 18mm pitch, 100 teeth. Which, and why (ADR 0003, Q17)?
c. **Close Q21** against SLAU550: is the runtime UART on the default UCA0 pins the same pair
   the BSL uses?
d. **LEDs, yes or no** (handoff §7). White or RGB would need a 5V pin on `J12`, which is a
   main-board change — so this one decides whether the main board waits.

**First engineering task after that:** the +2mm offset at the jack edge (handoff §1). A pure
offset — the regenerated placement file must differ from the old one by +2.000 in y and
nothing else — with `OY` in `hardware/kicad/tools/place.py` going 7.000 → 9.000 in the same
commit, and `place.py --check` still reporting all 24 panel parts on their holes.

**Then** set `hardware/faceplate/` up as its own KiCad 7 project with the same verification
loop the main board uses: a `netmap.json` as the intent, a generated schematic, netcheck
both ways, KiCad's own DRC through pcbnew, a placement check. The main board's tools in
`hardware/kicad/tools/` hardcode their paths — parametrize them rather than forking copies.

**Rules:** `CLAUDE.md` applies throughout. TI's documents and manufacturer drawings over
KiCad library parts and anything summarised. Check the source, not the doc describing it.
Commit per logical step, with no AI co-author trailer. Split into a new session at the next
phase boundary rather than letting this one run long.
