#!/usr/bin/env python3
"""Assemble hardware/vuulgaris-v1-fab.zip -- the single file handed to JLCPCB.

Everything in it already exists under fab/; this only packages it. It is a
script rather than a hand-built zip because a generated artifact that cannot be
regenerated goes stale without saying so -- which is precisely what happened to
the JLC BOM, which was derived by hand and went a line out of date the moment a
part was added.

Run it after mkbom.py / mkcpl.py / the gerber export. It refuses to build if
the gerber zip is older than the board, because a stale package is worse than
no package.

    python3 tools/mkfab.py
"""
import os, sys, re, time, zipfile, subprocess

KI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.dirname(KI)
FAB = f"{KI}/fab"
PCB = f"{KI}/vuulgaris.kicad_pcb"
OUT = f"{HW}/vuulgaris-v1-fab.zip"

GERBERS = f"{FAB}/vuulgaris-gerbers.zip"
BOM = f"{FAB}/vuulgaris-BOM-jlc.csv"
CPL = f"{FAB}/vuulgaris-CPL-jlc.csv"

README = """Vuulgaris V1 -- JLCPCB fab package
Generated {stamp} from hardware/kicad/vuulgaris.kicad_pcb ({commit})

No known board defects as of 2026-09-22 -- docs/review-packet.md.

  (SW4-SW9, the six shorted buttons, were fixed 2026-09-22.)
  (RV1-RV6, 10k where the design needs 100k, came off the JLC BOM
   2026-09-22 -- hand-fit Alpha pots, see BEFORE YOU ORDER.)
  (J7-J10, the 1/4" jack pinout, was settled from the drawing and LCSC's
   symbol rather than a meter, since there is no jack to meter before the
   order. Beep one on the first assembled board before patching into it.)

WHAT TO UPLOAD WHERE
--------------------
  vuulgaris-gerbers.zip          -> PCB tab, "Add gerber file"
  assembly/vuulgaris-BOM-jlc.csv -> Assembly, BOM file
  assembly/vuulgaris-CPL-jlc.csv -> Assembly, CPL / pick-and-place file

Upload the gerber zip AS-IS. Do not unzip and re-zip it: it is already in the
flat layout JLC expects, 13 gerbers plus 2 Excellon drill files.

BOARD
-----
  {size}, 4 layer (F.Cu / In1.Cu / In2.Cu = GND plane / B.Cu)
  {placements} placements
  Absolute origin throughout -- gerbers, drills and CPL share it.

BEFORE YOU ORDER
----------------
1. U7, DKM10E-12 (C6934792) -- JLC has ZERO stock, pre-order only at $15.10.
   This is the +/-12V converter the whole board runs on. Source it from
   Mouser / Digi-Key / Arrow and hand-fit. Through-hole 1"x1" module.

2. DS1, HS242L01W4S01 (C5139768) -- not in JLC's assembly library at all.
   Buy from LCSC (~$12.22) and fit by hand.

3. RV1-RV6 -- the BOM line is deliberately blank, so JLC places nothing.
   Buy from Tayda and hand-fit:
     5x Alpha RD902F-40-15R1-B100K  (Tayda A-5440)  RV1-RV4, RV6
     1x Alpha RD902F-40-15R1-B10K   (Tayda A-6433)  RV5 FEEDBACK
   Do not let JLC "helpfully" match the line to C380211 -- that is the 10k
   ALPS these replace, and it fits the same holes.

4. These BOM lines have no source anywhere. All through-hole, all hand-solder:
{unsourced}
5. J7-J10 (PJ-603, C41409498) had 64 in stock on 2026-09-11 -- 16 boards'
   worth. The only line thin enough to cap a run.

NOTES
-----
The CPL carries rotation corrections. Bottom-side parts are sent as
180 - angle, because KiCad's flip mirrors about X while JLC reads a bottom
rotation mirrored about Y; the four SOIC-14s carry a further -90 because their
footprint is KiCad-library rather than LCSC. Do not "fix" these by hand.
"""


def main():
    for f in (GERBERS, BOM, CPL):
        if not os.path.exists(f):
            sys.exit(f"missing {f} -- run the gerber export, mkbom.py and mkcpl.py first")
    if os.path.getmtime(GERBERS) < os.path.getmtime(PCB):
        sys.exit("gerbers are older than the board. Re-export them; a stale "
                 "package is worse than no package.")

    commit = subprocess.run(["git", "-C", HW, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "uncommitted"
    placements = sum(1 for _ in open(CPL)) - 1
    uns = []
    import csv
    for r in csv.DictReader(open(f"{FAB}/vuulgaris-BOM.csv")):
        if not r["LCSC Part #"] and not r["Note"].startswith("NOT FROM JLC"):
            uns.append(f"     {r['Designator']:26}{r['Comment']}")
    # Derived, not typed. It read "284.30 x 116.81 mm" for a day after the top
    # edge was stepped out 7mm over the USB-C, which is the exact failure this
    # script's docstring is about: a generated artefact carrying a hand-kept
    # fact goes stale without saying so.
    _pcb = open(PCB).read()
    _e = re.findall(r'\(gr_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) '
                    r'([-\d.]+)\).{0,160}?\(layer "Edge\.Cuts"\)', _pcb, re.S)
    _e += [(g[0], g[1], g[4], g[5]) for g in
           re.findall(r'\(gr_arc \(start ([-\d.]+) ([-\d.]+)\) \(mid ([-\d.]+) '
                      r'([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\).{0,160}?'
                      r'\(layer "Edge\.Cuts"\)', _pcb, re.S)]
    _x = [float(v) for g in _e for v in (g[0], g[2])]
    _y = [float(v) for g in _e for v in (g[1], g[3])]
    size = (f"{max(_x)-min(_x):.2f} x {max(_y)-min(_y):.2f} mm overall envelope "
            f"-- NOT a rectangle, the top edge steps out at the USB-C; JLC quotes "
            f"on the envelope")
    readme = README.format(stamp=time.strftime("%Y-%m-%d"), commit=commit, size=size,
                           placements=placements, unsourced="\n".join(uns) + "\n")

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(GERBERS, "vuulgaris-gerbers.zip")
        z.write(BOM, "assembly/vuulgaris-BOM-jlc.csv")
        z.write(CPL, "assembly/vuulgaris-CPL-jlc.csv")
        z.writestr("README.txt", readme)
    print(f"{OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")
    print(f"  {placements} placements, {len(uns)} unsourced BOM lines, board at {commit}")


if __name__ == "__main__":
    main()
