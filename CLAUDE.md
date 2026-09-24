# Vuulgaris V1 — project instructions

Four-channel capacitive sample-scrubbing instrument: Daisy Patch SM, a stereo
Buchla-style low pass gate (Bergman), a stereo BBD delay (Moritz Klein), and an
MSP430FR2675 touch faceplate. Two PCBs:

- **Main board** — `hardware/kicad/`, KiCad 7, 4-layer, JLC assembly. **Finished:**
  DRC clean, fab package at `hardware/vuulgaris-v1-fab.zip`.
- **Faceplate** — `hardware/faceplate/`. Not laid out yet. Its README opens with
  everything the main board has already fixed for it.

## Read first

| | |
|---|---|
| `docs/design-state.md` | the current state of everything — the handoff doc |
| `docs/review-packet.md` | what was verified against which source, and every defect found |
| `docs/decisions/` | ADRs 0001–0010. Read before relitigating anything |
| `docs/notes/open-questions.md` | open questions, with what each one blocks |
| `hardware/kicad/README.md` | the main-board process, and the lessons that cost real work |
| `hardware/faceplate/README.md` | faceplate constraints and the main-board handoff |
| `mockups/generate-faceplate.py` | source of truth for panel geometry and panel-part positions |

## Main board: the loop

`hardware/kicad/tools/netmap.json` is the intent. The schematic is **generated** —
never hand-edit `vuulgaris.kicad_sch`; change netmap / `values.json` / `mksch.py`
and regenerate. From `hardware/kicad/`, with `set -o pipefail` whenever output is
piped (a masked failure once let netcheck pass against a stale schematic):

```bash
python3 tools/mksch.py && python3 tools/netcheck.py   # schematic vs intent, both directions
python3 tools/boardcheck.py                           # board pads vs netmap parity
python3 tools/drc.py                                  # KiCad's own DRC -- the clearance authority
python3 tools/place.py --check                        # panel parts on their faceplate holes
python3 tools/pose.py --check && python3 tools/mirrorcheck.py
python3 tools/schdraw.py                              # doc schematics agree with netmap
python3 tools/gerbercheck.py                          # 9 known false positives; a 10th is real
```

DRC's ~256 warnings are silkscreen and library overrides; errors are what count.
gerbercheck's 9 are vias and one same-net pad whose square bounding boxes overlap
while the round copper does not (checked 2026-09-23).

Fab package, after any board change, in the same commit:

```bash
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
$CLI sch export python-bom --output fab/vuulgaris-bom.xml vuulgaris.kicad_sch && python3 tools/mkbom.py
python3 tools/mkcpl.py
$CLI pcb export gerbers --output fab/ --no-protel-ext --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts" vuulgaris.kicad_pcb
$CLI pcb export drill --output fab/ --format excellon --excellon-separate-th --generate-map --map-format gerberx2 vuulgaris.kicad_pcb
(cd fab && rm -f vuulgaris-gerbers.zip && zip -q -X vuulgaris-gerbers.zip vuulgaris-*.gbr vuulgaris-*.drl)   # must hold 15 files
python3 tools/mkfab.py
```

- KiCad's Python (has `pcbnew`): `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3`.
  `kicad-cli` 7.0.8 cannot run DRC; `drc.py` goes through `pcbnew.WriteDRCReport`.
- `tools/kpins.json` is untracked. Rebuild it with the exact argument list in
  `ksym.py`'s docstring — never bare, never a glob.
- **Board edits** are either scripted through pcbnew (`LoadBoard` → edit →
  `ZONE_FILLER(b).Fill(b.Zones())` → `SaveBoard`) or done by the user in Pcbnew.
  KiCad holds the design in memory: after a script writes, the user must
  **File → Revert** before touching it, or their next save wipes the change.
- **Hand-routing is the user's.** When a change needs rerouting, move the parts,
  drag track ends with them, leave the ratsnest, and say what to route. Do not
  script jogs through dense routing — it was tried and it makes a worse board.
- After any board change, diff against `HEAD` for what DRC cannot see: footprints
  that moved, nets that got narrower or much longer, vias added, stale zone fill.

## Rules that came from mistakes

- **Manufacturer drawings beat everything.** KiCad library footprints, product
  photos, distributor pages and this repo's own docs have each been wrong. On
  2026-09-22 all twelve pot tab slots were rotated on the strength of KiCad's
  library footprint and a photo; Alpha's drawing said the opposite.
- **Check the source, not the summary.** Diff netmap against the drawing or
  datasheet, never against a doc describing it — that is how two LPG rows shipped
  wrong. When a doc and its source disagree, fix the doc in the same commit.
- JLC and LCSC stock are different inventories; check JLC's parts library in the
  browser. Prefer Basic parts. LCSC numbers live in `mkbom.py` `CURATED`; hand-fit
  parts get a blank LCSC number and a `NOTE` so JLC cannot place them.
- **The main board fixes the panel.** Its 24 panel parts are placed from
  `hardware/placement-panel-facing.txt`. Any regeneration of that file must leave
  `place.py --check` at "all 24 on their holes".
- Datasheet PDFs are gitignored; `datasheets/fetch-datasheets.sh` fetches them.
  `pdftoppm` is not installed: render pages with macOS PDFKit (a short Swift
  script) or `brew install poppler`. Scanned drawings have no text layer — read
  them as images at 4–6x and crop to the detail.
- Ask before downloading anything. Don't read `~/Downloads` (TCC-blocked).
  `docs/reference/` is gitignored.

## Commits

`area: what changed` subject; the body says why and what was checked. **No AI
co-author trailer, ever.** Never commit a board that fails DRC.
