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
import os, sys, time, zipfile, subprocess

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

WHAT TO UPLOAD WHERE
--------------------
  vuulgaris-gerbers.zip          -> PCB tab, "Add gerber file"
  assembly/vuulgaris-BOM-jlc.csv -> Assembly, BOM file
  assembly/vuulgaris-CPL-jlc.csv -> Assembly, CPL / pick-and-place file

Upload the gerber zip AS-IS. Do not unzip and re-zip it: it is already in the
flat layout JLC expects, 13 gerbers plus 2 Excellon drill files.

BOARD
-----
  284.30 x 116.81 mm, 4 layer (F.Cu / In1.Cu / In2.Cu = GND plane / B.Cu)
  {placements} placements
  Absolute origin throughout -- gerbers, drills and CPL share it.

BEFORE YOU ORDER
----------------
1. U7, DKM10E-12 (C6934792) -- JLC has ZERO stock, pre-order only at $15.10.
   This is the +/-12V converter the whole board runs on. Source it from
   Mouser / Digi-Key / Arrow and hand-fit. Through-hole 1"x1" module.

2. DS1, HS242L01W4S01 (C5139768) -- not in JLC's assembly library at all.
   Buy from LCSC (~$12.22) and fit by hand.

3. These BOM lines have no source anywhere. All through-hole, all hand-solder:
{unsourced}
4. J7-J10 (PJ-603, C41409498) had 64 in stock on 2026-09-11 -- 16 boards'
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
        if not r["LCSC Part #"]:
            uns.append(f"     {r['Designator']:26}{r['Comment']}")
    readme = README.format(stamp=time.strftime("%Y-%m-%d"), commit=commit,
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
