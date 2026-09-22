#!/usr/bin/env python3
"""Run KiCad's OWN DRC and fail on anything it calls an error.

    python3 tools/drc.py            # regenerate DRC.rpt and judge it
    python3 tools/drc.py --keep     # judge the existing DRC.rpt, run nothing
    python3 tools/drc.py OTHER.kicad_pcb    # judge some other board

The third form is how this gets tested: point it at a board with a known
short and it must fail. A checker nobody has watched fail is a checker
nobody should trust -- which is the whole reason this file exists.

Why this exists, and it is the most expensive lesson in this repo:

boardcheck.py was written because `kicad-cli` in 7.0.8 has no `drc`
subcommand, so it reimplements the parts of DRC this board needs. A
reimplementation has its own bugs, and one of them was load-bearing. Its
track-to-track test took the minimum of the four endpoint-to-segment
distances -- exact for two segments that do not meet, and wrong for the one
case that matters most. The closest point of an X crossing is the
intersection, which is not an endpoint of either segment, so two tracks lying
directly across each other measured 0.6mm apart and boardcheck printed
"clearance violations: 0" for days.

What it was hiding: /LPG_LED_L crossing /LPG_LEDK_L at (229.420, 121.895) and
/LPG_LED_R crossing /LPG_LEDK_R at (231.675, 155.000), both on F.Cu, both
0.0000mm. Those nets are the two ends of the vactrol LED string, so the short
bypassed both LEDs and the gates would never have opened. Dylan opened Pcbnew,
pressed DRC, and it found them in a second.

boardcheck.py is still worth running -- it checks parity against netmap.json,
which DRC knows nothing about, and it is fast. But it is no longer allowed to
be the last word on clearance. This is.

`kicad-cli` cannot do it, but pcbnew's Python module can: WriteDRCReport()
runs the real engine, connectivity included. It needs KiCad's own interpreter,
not the system one, so this shells out to it and parses what comes back.

On severity: everything in the report carries one, and the split is the
project's own setting in vuulgaris.kicad_pro. ERROR fails this script.
WARNING is counted and shown but does not. That is not laziness -- this board
carries ~270 silkscreen warnings (silk over pads, silk near the edge, silk
over silk) which JLC clips at plot time and which nobody is going to fix by
hand. Burying two real shorts in that pile is exactly how they survived.
If a silk warning ever needs to be an error, change it in the project file
and this will start failing on it.
"""
import os, re, sys, subprocess, collections

KI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = f"{KI}/vuulgaris.kicad_pcb"
RPT = f"{KI}/DRC.rpt"
KPY = ("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework"
       "/Versions/3.9/bin/python3")

GEN = '''
import pcbnew
b = pcbnew.LoadBoard(%r)
ok = pcbnew.WriteDRCReport(b, %r, pcbnew.EDA_UNITS_MILLIMETRES, True)
raise SystemExit(0 if ok else 1)
'''


def generate():
    if not os.path.exists(KPY):
        sys.exit(f"KiCad's Python is not at {KPY} -- pcbnew is the only way to "
                 f"run DRC headlessly in 7.0.8, so this cannot run without it")
    r = subprocess.run([KPY, "-c", GEN % (PCB, RPT)], capture_output=True, text=True)
    # pcbnew grumbles "create wxApp before calling this" on a headless load and
    # then works fine. Only a non-zero exit means anything.
    if r.returncode:
        sys.exit((r.stderr or r.stdout).strip() or "WriteDRCReport failed")


def main():
    global PCB, RPT
    other = [a for a in sys.argv[1:] if not a.startswith("--")]
    if other:
        PCB = os.path.abspath(other[0])
        RPT = os.path.splitext(PCB)[0] + ".DRC.rpt"
    if "--keep" not in sys.argv:
        generate()
    if not os.path.exists(RPT):
        sys.exit(f"no {RPT}")
    txt = open(RPT, encoding="utf-8", errors="replace").read()
    lines = txt.split("\n")

    seen = collections.Counter()
    errors = []
    for i, ln in enumerate(lines):
        m = re.match(r"^\[([a-z_]+)\]", ln)
        if not m:
            continue
        sev, detail = "?", []
        for j in range(i + 1, min(i + 4, len(lines))):
            if re.match(r"^\[", lines[j]) or not lines[j].strip():
                break
            s = re.search(r"Severity:\s*(\w+)", lines[j])
            if s:
                sev = s.group(1)
            else:
                detail.append(lines[j].strip())
        seen[(m.group(1), sev)] += 1
        if sev == "error":
            errors.append((m.group(1), ln.strip(), detail))

    # the report footer carries two counts of its own
    extra = []
    for label, pat in (("unconnected pads", r"Found (\d+) unconnected pads"),
                       ("footprint errors", r"Found (\d+) Footprint errors")):
        f = re.search(pat, txt)
        if f and int(f.group(1)):
            extra.append(f"{f.group(1)} {label}")

    total = sum(seen.values())
    print(f"KiCad DRC: {total} violations in {os.path.basename(RPT)}")
    for (kind, sev), n in sorted(seen.items(), key=lambda kv: (kv[0][1] != "error", -kv[1])):
        print(f"   {n:5}  {kind:26} {sev}")
    if not total:
        print("   (none)")

    if errors or extra:
        print()
        for kind, head, detail in errors:
            print(f"ERROR {head}")
            for d in detail:
                print(f"        {d}")
        for e in extra:
            print(f"ERROR {e}")
        print(f"\n{len(errors) + len(extra)} DRC ERROR(S) -- these are real")
        return 1
    warn = sum(n for (k, s), n in seen.items() if s == "warning")
    print(f"\n0 errors. {warn} warnings, none fatal "
          f"(silkscreen and library overrides -- see this file's docstring).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
