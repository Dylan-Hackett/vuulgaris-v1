# Full recheck — prompts for a cloud session

A second, independent pass over the netlist, the pinouts and the electrical
decisions, both boards. Paste prompt 0 first, then 1–12 in order, one at a time.
They also work as parallel sessions: prompt 0 plus one block each.

## Before starting — on the Mac, not in the cloud

The cloud session clones GitHub and has no KiCad. The datasheet PDFs are
committed, so it needs no network for them. Three things it cannot make for
itself:

1. **Push.** A session only sees what is on `origin/main`.
2. **Fresh evidence.** Run the loop from `CLAUDE.md` on both boards so the
   tracked `hardware/kicad/DRC.rpt` and `hardware/faceplate/DRC.rpt` are current,
   and commit them. The cloud reads DRC, it cannot run it.
3. **The CoolAudio V3205SD sheet** (never obtained; the MN3205 original and the
   mki manual cover it) and `~/Documents/origin2.2.eprj` do not exist there.
   The ±12V filter's source check (`edapower.py`) stays a local job; prompt 2
   says so.

---

## 0. Ground rules (paste first, every session)

```
You are doing an independent recheck of the Vuulgaris V1 hardware: main board
(hardware/kicad/) and faceplate (hardware/faceplate/). Read CLAUDE.md,
docs/review-packet.md and datasheets/REVIEW-INDEX.md first.

The datasheet PDFs are committed in datasheets/ (the mki BBD manual is at
"docs/BBD_MANUAL_250228 (3).pdf"). Setup, which I authorise now: apt-get
install poppler-utils so scanned drawings can be rendered with pdftoppm at
4-6x and read as images. If a manufacturer drawing you need is not in the
repo, do not substitute a distributor page or a web search -- mark the check
BLOCKED instead.

There is no KiCad here. Do not run mksch/netcheck/drc/boardcheck (they hardcode
/Applications/KiCad). Instead parse the files directly: the .kicad_sch embeds
lib_symbols (pin number -> pin name), the .kicad_pcb has every pad's number, net
and position. tools/kpins.json is untracked and absent; rebuild the pin-name
layer from lib_symbols. Write any parser to a scratch dir, not into tools/.

Rules:
- This is report-only. Do not edit netmap.json, values.json, design.py, any
  .kicad_* file or the fab packages. Fixes happen on my machine.
- Derive first, compare second. For each part, build the pin table from the
  manufacturer datasheet for the exact ordered part number and package (LCSC
  number from tools/mkbom.py CURATED) BEFORE looking at netmap.json. Then diff.
- "Already verified" in review-packet.md is a claim to retest, not evidence.
  Where your result disagrees with a doc, say which one is wrong and why.
- Every finding cites its source: file, page, figure/table, and the netmap
  ref.pin -> net it concerns. No finding from memory of what a part "usually" is.
- ADRs in docs/decisions/ are decided. Flag an ADR only if a datasheet limit
  shows it cannot work, not because you would have chosen differently.
- Follow the chain end to end for every pin: datasheet pin number -> footprint
  pad number -> symbol pin number -> symbol pin name -> net. A break anywhere
  in that chain is a defect even if netmap looks right.

Output: one file per prompt at docs/review/recheck/NN-<block>.md with a table
(ref.pin | net | source says | ours | verdict CLEAN/DEFECT/BLOCKED/QUESTION),
then defects ranked by "would this kill the board". Commit to branch
recheck/2026-10, subject "review: <block> recheck", no co-author trailer.
```

## 1. Inventory and chain integrity

```
Before any datasheet work, prove the bookkeeping. For both boards:
- Every ref in netmap.json: part number, LCSC number, footprint, datasheet file.
  List refs with no datasheet and say whether that is fine (R, C, FB) or a gap.
- Parse the .kicad_sch and the .kicad_pcb yourself and re-derive parity:
  netmap ref.pin->net vs schematic vs board pad nets. Expect 942/942 on the
  main board. This is an independent reimplementation of netcheck/boardcheck;
  if you disagree with them, that is the finding.
- Every symbol pin whose NAME implies a function (VCC, VDD, VSS, GND, V+, V-,
  OUT, IN+, IN-, ADJ, EN, RESET) against the net it sits on. This is the check
  that caught U8.
- Every single-pin net, every unconnected pin and every pin absent from
  netmap: list them all and justify each from the datasheet (may this pin
  float?). Unused op-amp sections, unused CMOS inputs and unused MCP23017 /
  MSP430 pins especially.
- Symbol pin count vs footprint pad count vs datasheet pin count for every
  multi-pin part. Thermal tabs and shield/mounting pads included.
```

## 2. Power

```
Block: J11, F1, D3, R22/R23, U7 (DKM10E-12), U5/U6/U8 (AMS1117), L1/L2,
C28-C39, R24/R25, D1/D2, Q1/Q2, FB1/FB2. Sources: Mean Well spec, AMS1117,
SMAJ6.0A, MMBFJ113, the Type-C connector drawing, docs/reference/V3.0.kicad_sch,
ADR 0010, docs/power-usbc-dkm.md.

Pinouts: every pin of J11, U7, each regulator, Q1/Q2, D3 against the drawing.
For J11 check both plug orientations (A and B rows), CC1/CC2 pulldowns each on
its own resistor, shield termination.

Then the numbers, from the datasheets, with arithmetic shown:
- Rail budget. Sum worst-case current per rail (+12, -12, +5, +3V3, each
  sub-rail) from each IC's datasheet supply current, the Patch SM's stated
  draw, OLED, vactrol LEDs, headphone load. Compare with DKM10E-12 rated
  output, its minimum-load requirement, and 5V/3A at the input after
  converter efficiency.
- Each AMS1117: input voltage vs absolute max, dropout at load, dissipation
  and junction temperature for the package, required output cap type/ESR.
- U7: input cap and output cap limits (max capacitive load), start-up into
  the fitted bulk capacitance, R.C. pin.
- Every capacitor's voltage rating vs the rail it sits on, with derating.
  Every electrolytic's polarity vs net.
- F1 hold/trip vs budget; D3 standoff and clamp vs VBUS and vs U7's input max.
- What Q1/Q2 are doing and whether Vgs(off) spread across the J113 datasheet
  range still gives the intended behaviour.
- Power sequencing: can any IC see an input above its own rail during ramp
  (3V3 logic driven from 5V parts, op-amp outputs into unpowered Patch SM)?

The ±12V filter's own source (the EasyEDA project) is not in this checkout.
Check that block for internal sanity and mark the source diff BLOCKED-LOCAL.
```

## 3. Daisy Patch SM (U1)

```
Block: U1 and every net touching it. Sources: Electrosmith Patch SM v1.0.5
datasheet (re-derive the pin table from the PDF; then diff
datasheets/extracts/patch-sm-v1.0.5-pinout.md against it too),
docs/pin-allocation.md, ADRs 0005, 0008, 0009.

- All pins, both headers: pin number -> name -> function -> our net. Header
  orientation and row order on the footprint vs the mechanical drawing, viewed
  from the side the module mounts on.
- Per pin electrical class: 3V3 GPIO, 5V-tolerant or not, ADC range, bipolar
  CV in, CV out range, gate in/out levels, audio in/out level and coupling.
  For every net, the worst voltage our circuit can put on that pin vs its
  absolute max. The CV and ADC inputs fed from ±12V op-amp stages matter most.
- Each peripheral actually exists on the pin we use it on: I2C (and where the
  pullups are, to which rail, one set only), SPI for the OLED, SDMMC for J1,
  UART to the faceplate, the ADC count in ADR 0009.
- Boot and special pins: anything shared with BOOT, DFU, USB, QSPI, the SD
  card or the debug header (open-questions Q8, Q14, Q15).
- Cross-check firmware: every pin named in fw-daisy/ against netmap. A pin the
  firmware drives that the board wires elsewhere is a defect either way.
```

## 4. Digital IO: expanders, encoders, buttons, OLED, SD

```
Block: U3/U4 (MCP23017), ENC0-ENC8, SW4-SW9, DS1, J1 (microSD), their R/C.
Sources: Microchip DS20001952, both ALPS encoder drawings, TS1103S drawing,
HS242L01W4S01 module datasheet, TF-PUSH drawing, ADR 0006.

- MCP23017: full pinout for the ordered package, address straps, RESET, INTA/
  INTB wiring and whether they need pullups (open-drain config), the GPA7/GPB7
  output-only caveat in the current datasheet revision, decoupling.
- Encoders: A/B/common and switch pins per drawing, for EC11 and EC12
  separately (they are different parts). Mounting lugs: grounded or floating?
  Pullups: internal or fitted, and to which rail.
- Tactile switches: which pins are internally shorted pairs. Prove each switch
  is wired across the switching pair and not along a shorted one.
- DS1: every module pin, logic level limit (the sheet says 3.3V max on logic),
  what drives each pin and from which rail, the font-chip pins (8/9), reset
  timing/RC, SSD1306 vs SSD1309 ambiguity and whether it changes any wiring.
- J1 microSD: pin numbering on the footprint vs the drawing, card-detect and
  shell pins, pullups, 1-bit vs 4-bit vs what the Patch SM exposes.
```

## 5. BBD delay, both channels

```
Block: U101-U104, U106 and 2xx, R1xx/R2xx, C1xx/C2xx, D103-D107/D203-D207,
SW1/SW2. Sources: "docs/BBD_MANUAL_250228 (3).pdf" -- the schematic page is
vector, render it at 10x; the BOM is text. MN3205, CD4046B, TL072 datasheets.
docs/bbd-mki.md is the thing being checked, not a source.

- Node by node against the drawing: build a netlist of the manual's schematic
  from the rendered page, then diff against channel 1 of netmap. Every R and C
  value against both the drawing and the BOM text; where those two disagree
  with each other, say so.
- Channel 2 against channel 1: structural diff with 1xx->2xx renaming. Any
  asymmetry is either documented or a defect.
- Every deviation from the manual that bbd-mki.md declares: is each one
  actually implemented as described, and does anything undeclared differ?
- V3205/MN3205: supply, VGG divider value vs the datasheet's VGG ratio, clock
  amplitude and the capacitive load CD4046 has to drive, input bias point,
  signal level vs the datasheet's max input for stated THD.
- CD4046B: VDD, VCO R1/R2/C1 against the datasheet's frequency equations and
  graphs -- compute the clock range and the resulting delay range; inhibit
  and unused phase-comparator pins tied off.
- TL072 stages: gain and corner frequency of each from the fitted values,
  input common-mode range vs actual signal (phase reversal near V-), output
  swing into the next stage's limits, especially into the BBD and the Patch SM.
- SW1/SW2 against the Dailywell drawing: commons, throw pairs per position,
  and that neither position shorts the two channels (a previous bug).
- Diode orientation on every clamp.
```

## 6. Low pass gate, both channels

```
Block: U301/U302, U401/U402, VT301/VT302, VT401/VT402, R3xx/R4xx, C3xx/C4xx,
D301/D401, RT301/RT401, the RV pots on this block. Sources:
"datasheets/LPG Schematic E Bergman (3) (1).jpg" at full resolution, TL074,
TL084, VTL5C3, BZT52C3V9 datasheets, ADRs 0007 and 0011.
docs/lpg-bergman.md is under review, not a source.

- Build the drawing's netlist from the image yourself, every node, then diff
  against channel 3xx. Then 4xx against 3xx. R12/R16 absent is decided.
- ADR 0011's input mix (R301/R302/R312 and 4xx) is not on the drawing: check
  it as a circuit -- gain, source impedances, what happens with nothing
  patched, headroom at the summing node.
- Vactrol LED drive: polarity through both LEDs in series, worst-case current
  with the control at maximum vs the VTL5C3's max LED current, zener
  direction and what it clamps.
- Op-amp section assignment: which physical section (A-D, pin numbers) does
  each job, and that +/- inputs are not swapped anywhere.
- Pot and trimmer wiring vs the pot drawings: which end is CW, that clockwise
  does what the panel legend says, both gangs of any dual pot.
- Control-voltage range arriving from the Patch SM / jacks vs what the
  circuit expects.
```

## 7. Audio IO: headphone, EXT input, jacks, pots

```
Block: U9/U10, R5xx/C5xx, RT501-RT504, J2-J10, RV1-RV6. Sources: OPA1688,
PJ-376 and PJ-603 drawings (image-only: render and read), pot and trimmer
drawings.

- First settle which pot is on the BOM (ALPS RK09L vs Alpha RD902F both have
  datasheets here) and check the footprint against THAT drawing: pin
  numbering of both gangs, pin 1, tab slot orientation, shaft side.
- Each jack: tip/ring/sleeve and every switch lug per the drawing, and that
  normalled connections break the way the design intends when a plug goes in.
  PJ-376 and PJ-603 are different parts with different numbering.
- OPA1688: pinout, gain of each stage from fitted values, output current into
  the lowest headphone impedance it should drive, stability with the series
  output resistor and cable capacitance, input protection current.
- Levels end to end: Patch SM out -> headphone, EXT in -> Patch SM in and ->
  the analog chain (ADR 0011). Compute each in dBu/Vpp and compare with every
  downstream absolute max.
- AC coupling: each cap's corner frequency with its load, and the polarity of
  any polarised coupling cap vs the DC on each side.
```

## 8. Footprints against manufacturer drawings

```
Every non-passive footprint on both boards, from the .kicad_pcb directly.
For each: pad count, pad numbering order, pitch, row spacing, pad/hole size vs
the drawing's recommended land pattern, pin-1 marker, body outline, and
mounting pegs/lugs. Do not trust a KiCad library footprint name as evidence.

Extra attention:
- Anything on the back copper side: confirm the flip is right by computing
  pad positions in board coordinates and comparing with the part's drawing
  viewed from the correct side. Through-hole panel parts are the classic
  mirror-image failure.
- SOT-23, SOT-223, SOD-123 parts: pad numbering vs each manufacturer's own
  numbering (they differ between vendors for the same package name).
- Polarised parts: pad 1 vs anode/cathode/+ per the drawing AND per the silk.
- Hole sizes vs lead diameter + tolerance for every through-hole part.
- Panel parts: run the position logic of tools/place.py --check by hand from
  hardware/placement-panel-facing.txt if the script will not run -- all 24
  must sit on their faceplate holes.
- Heights: tallest parts on each board vs the gap between the two boards and
  behind the panel (OLED module, DKM10, electrolytics, the header stack).
```

## 9. Main board to faceplate interconnect

```
Main-board J12 (C5665 box header) to faceplate J1 (HX-JN2.54-2x5P).
Sources: both connector drawings, both netmaps, hardware/faceplate/README.md,
ADR 0005, open-questions Q21/Q22/Q23.

- Pin-for-pin table: J12.n net <-> J1.n net. Then prove the physical mapping:
  which board side each connector is on, how they mate (direct stack or
  ribbon), and whether pin 1 meets pin 1 or the rows swap. Compute it from pad
  coordinates in both .kicad_pcb files, not from the docs.
- Direction of every signal on both ends: TX lands on an RX, not TX-to-TX.
  Reset and TEST/SBW lines driven by exactly one side.
- BSL entry: the pins and sequence SLAU550 requires for the FR2675 vs what the
  Daisy can actually drive over this connector, including levels and any
  divider (Q13).
- Power across the connector: rail, current vs pin rating, ground pin count,
  and where the faceplate's rail is decoupled.
- Mechanical: board-to-board spacing set by this connector vs the pot/jack/
  encoder seating heights that also set it.
```

## 10. Faceplate: MSP430FR2675 and electrodes

```
Block: everything in hardware/faceplate/design/netmap.json. Sources:
TI MSP430FR2675 datasheet (the exact package fitted), SLAA842, SLAA843,
SLAU550, TPD1E10B06, Epson FC-135, ADRs 0002-0004, 0012, 0013.

- U1 every pin: package pin number -> pin name -> the function we use, and
  that the function is available on that pin in that package (CapTIvate CAPx.y
  block/element, eUSCI, XIN/XOUT, RST/NMI/SBWTDIO, TEST/SBWTCK, VREG, DVCC/
  DVSS/AVCC). Unused pins: how are they terminated vs TI's guidance.
- CapTIvate: which electrodes are on which block and element, that elements
  meant to scan in the same cycle are on different blocks, VREG capacitor
  value/type per the datasheet, series resistors per electrode.
- TVS on electrodes: its capacitance vs the electrode capacitance and what
  that does to sensitivity per SLAA843.
- Crystal: load caps for FC-135's CL including pin and stray capacitance;
  whether it is needed at all (Q22).
- Decoupling, reset RC and the BSL/programming access path.
- Cross-check fw-touch/ pin and sensor configuration against the netmap.
- Exposed gold electrodes (ADR 0004/0013): ESD path, and that no trace under
  a pad violates what Q24 assumed.
```

## 11. Board-level: DRC, fab rules, BOM and CPL

```
Both boards. Sources: the tracked DRC.rpt files, the .kicad_pcb/.kicad_pro,
hardware/kicad/fab/ and hardware/faceplate/fab/, JLCPCB's published
capabilities for the stackup ordered.

- DRC.rpt: confirm its timestamp is newer than the last board commit (if not,
  say so and stop trusting it). Zero errors, zero unconnected. Bucket the
  warnings by type and flag any bucket that is not silk or library override.
- Design rules in .kicad_pro vs JLC's limits for this layer count: track/
  space, via drill and annular ring, hole-to-hole, copper-to-edge, mask
  sliver, min silk. Then scan the actual board for the tightest instance of
  each and report margin.
- Track width vs current on every power net, using the rail budget from
  prompt 2. Via count on power transitions. Narrowest neck on each rail.
- Plane integrity: layer stack, what each inner layer is, splits under fast
  or sensitive nets (BBD clocks, CapTIvate lines, audio inputs), return path
  for the converter.
- Decoupling placement: distance from each IC supply pin to its capacitor.
- Analog hygiene: BBD clock nets vs audio and touch nets, parallel-run length.
- Gerber zip: the 15 expected files, layer set, drill files plated/non-plated,
  outline closed.
- BOM vs board: every fitted ref present once, LCSC part's package matches
  the footprint, value matches values.json, hand-fit parts have blank LCSC.
- CPL: rotation and side for every polarised part and IC against JLC's
  rotation convention for that package. This is where a clean board still
  comes back wrong. List anything whose pin 1 you cannot prove.
```

## 12. Synthesis

```
Read every file in docs/review/recheck/. Produce 00-summary.md:
- All DEFECTs, deduplicated, ranked: kills the board / degrades it / cosmetic.
  For each: the one-line fix and which file it lands in (netmap, values,
  design.py, a footprint, a doc).
- All BLOCKED items and what unblocks each (a missing PDF, KiCad on the Mac,
  the EasyEDA project, a bench measurement).
- Every place a repo doc disagreed with its source, even where the board is
  right.
- Coverage: refs and nets no prompt touched. That list should be empty or
  explained.
- What you could not check from documents at all and only a bench will settle.
Do not soften anything and do not pad it. If a block came back clean, one
line.
```
