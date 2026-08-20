#!/usr/bin/env python3
"""Verify the board against KiCad's OWN Gerber output.

Why this exists, separately from place.py:

place.py reasons about geometry with its own transform -- rotation, and the
mirror that applies to back-side footprints. Those same transforms are what put
the parts where they are. So when the transform is wrong, the placement and the
check are wrong together and the check reports success. That has now happened
three times:

  * rotated parts were bounded with their UNROTATED extents (28mm out on U1)
  * the outline test compared only footprint ORIGINS, so J11 hung 3.5mm over
  * back-side pads were computed from the LIBRARY's local coordinates, but KiCad
    rewrites them on flip -- negating local Y and swinging pad angles 180. J11's
    pad sat 0.40mm past the milled outline and place.py called it clean.

Gerbers come out of KiCad, not out of this repo's arithmetic, so they cannot
share the mistake. Aperture definitions carry the true pad size and orientation;
flash coordinates carry the true position. This checks:

    1. no flash crosses the Edge.Cuts outline   (a pad there is milled through)
    2. no two flashes on a layer overlap        (a short no ERC can see)

Run it before plotting fab files, and after anything is flipped or rotated.
"""
import re, sys, os, glob, shutil, subprocess, tempfile

KI = "/Users/dylanhackett/V1/hardware/kicad"
PCB = f"{KI}/vuulgaris.kicad_pcb"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


def flashes(path):
    """Yield (x, y, w, h) in mm for every flashed pad in a Gerber."""
    s = open(path).read()
    aps = dict(re.findall(r'%ADD(\d+)([^*]+)\*%', s))
    cur = None
    for line in s.split("\n"):
        m = re.match(r'D(\d+)\*$', line.strip())
        if m:
            cur = m.group(1)
            continue
        m = re.match(r'X(-?\d+)Y(-?\d+)D0?3\*', line.strip())
        if not m:
            continue
        ap = aps.get(cur, "").strip()
        a = re.match(r'[ROC],([\d.]+)(?:X([\d.]+))?', ap)
        if not a:
            continue
        w = float(a.group(1))
        h = float(a.group(2)) if a.group(2) else w
        yield int(m.group(1)) / 1e6, int(m.group(2)) / 1e6, w, h


def main():
    out = tempfile.mkdtemp(prefix="gerbercheck-")
    try:
        r = subprocess.run([CLI, "pcb", "export", "gerbers", "--output", out + "/",
                            "--layers", "F.Cu,B.Cu,Edge.Cuts", PCB],
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stderr.strip() or r.stdout.strip())
            return 2
        edge = glob.glob(f"{out}/*Edge*")
        if not edge:
            print("no Edge.Cuts layer exported")
            return 2
        s = open(edge[0]).read()
        pts = [(int(m.group(1)) / 1e6, int(m.group(2)) / 1e6)
               for m in re.finditer(r'X(-?\d+)Y(-?\d+)D0?[12]\*', s)]
        bx0, bx1 = min(p[0] for p in pts), max(p[0] for p in pts)
        by0, by1 = min(p[1] for p in pts), max(p[1] for p in pts)
        print(f"outline  x[{bx0:.2f},{bx1:.2f}] y[{by0:.2f},{by1:.2f}]")

        bad = 0
        for f in sorted(glob.glob(f"{out}/*.gtl") + glob.glob(f"{out}/*.gbl")):
            fl = list(flashes(f))
            over = []
            for x, y, w, h in fl:
                d = max(bx0 - (x - w / 2), (x + w / 2) - bx1,
                        by0 - (y - h / 2), (y + h / 2) - by1)
                if d > 0.005:
                    over.append((round(d, 3), x, y, w, h))
            rects = [(x - w / 2, y - h / 2, x + w / 2, y + h / 2) for x, y, w, h in fl]
            clash = 0
            for i in range(len(rects)):
                for j in range(i + 1, len(rects)):
                    a, b = rects[i], rects[j]
                    if (max(b[0] - a[2], a[0] - b[2]) < 0
                            and max(b[1] - a[3], a[1] - b[3]) < 0):
                        clash += 1
            bad += len(over) + clash
            name = os.path.basename(f)
            print(f"  {name:26} {len(fl):4} flashes   over outline: {len(over)}   overlapping: {clash}")
            for d, x, y, w, h in sorted(over, reverse=True)[:8]:
                print(f"      ({x:9.3f},{y:9.3f}) {w}x{h}mm  over by {d}mm")
        print("CLEAN" if bad == 0 else f"{bad} PROBLEM(S)")
        return 0 if bad == 0 else 1
    finally:
        shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
