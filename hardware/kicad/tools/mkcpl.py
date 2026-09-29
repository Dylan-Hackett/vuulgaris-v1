#!/usr/bin/env python3
"""Build the JLC CPL from the board, correcting two rotation-frame mismatches.

kicad-cli's position export reports each footprint's rotation in KiCad's own
frame.  JLC places its parts using the LCSC/EasyEDA reference frame, so two
corrections are needed before the numbers mean the same thing.

1.  BOTTOM SIDE.  KiCad flips a footprint to B.Cu by mirroring it about the X
    axis (negating local Y) and leaving the stored rotation alone.  JLC reads a
    bottom-side rotation as counter-clockwise *seen from underneath the board*,
    which is a mirror about the Y axis.  Those two mirrors differ by a half
    turn.  Composing them:

        M_x . R(t) . M_y  ==  R(180 - t)

    so a bottom part stored at t must be sent as 180 - t.  Parts at +/-90 come
    out unchanged, which is why this hides: on this board 20 of the 154 bottom
    placements were already right and the other 134 were a half turn out.  It
    only becomes visible on a package whose body is asymmetric -- U8's SOT-223
    tab was the one that showed, while the SOIC-8s next to it looked fine
    rotated 180 and would have been assembled with pin 1 in the wrong corner.

2.  FOOTPRINT ZERO.  easyeda2kicad footprints are drawn in LCSC's frame and
    encode pin 1's corner in their name (-BL bottom-left, -BR bottom-right), so
    they need no correction.  Footprints taken from the KiCad standard library
    do not follow it.  SOIC-14_3.9x8.7mm_P1.27mm puts pin 1 top-left with the
    pitch running along Y; every LCSC SOIC/SOP here puts pin 1 bottom-left with
    the pitch along X.  Writing K for the KiCad drawing and L for the LCSC one,
    K = R(d).L, and the part is sent as t + d.  Measured from the pads, d = -90.

Composing both:   top     phi = t + d
                  bottom  phi = 180 - t + d

THE FACEPLATE (--project faceplate).  Every part is on the back, so every one takes
the bottom correction.  Its own footprints were checked, 2026-09-29, against the
EasyEDA footprint JLC holds for each part (easyeda.com/api/products/<LCSC>/components,
the source easyeda2kicad reads): U1's is LQFP-48_...-TL, pin 1 top-left with 1-12 down
the left side, exactly ours -- NOT the -90 the usual LQFP rule would give; J1's has pin 1
bottom-left, odd row along the bottom and the key on it, as ours; the TVS and the
crystal lie along X as ours.  So d = 0 for all of them.  The test pads and the scrub
pads are copper, not parts, and are left out.
"""
import csv, os, re, subprocess, sys

import proj

KI   = proj.P.dir
PCB  = proj.P.pcb
OUT  = os.path.join(KI, 'fab', f'{proj.P.name}-CPL-jlc.csv')
SKIP = re.compile(r'(TP|E)\d+') if proj.KEY == 'faceplate' else None
CLI  = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

# footprint -> degrees the KiCad drawing sits ahead of the LCSC reference.
# Only footprints NOT produced by easyeda2kicad can need an entry; verify any
# addition against the pads, not against the name.
FP_OFFSET = {
    'SOIC-14_3.9x8.7mm_P1.27mm': -90.0,   # pin 1 top-left / pitch Y vs LCSC bottom-left / pitch X
}


def raw_positions(tmp):
    subprocess.run([CLI, 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm',
                    '--side', 'both', '-o', tmp, PCB], check=True,
                   stdout=subprocess.DEVNULL)
    return list(csv.DictReader(open(tmp)))


def jlc_rotation(rot, side, package):
    d = FP_OFFSET.get(package, 0.0)
    phi = (rot + d) if side == 'top' else (180.0 - rot + d)
    return phi % 360.0


def main():
    tmp = os.path.join(KI, 'fab', '.pos-raw.csv')
    rows = raw_positions(tmp)
    os.remove(tmp)
    if SKIP:
        rows = [r for r in rows if not SKIP.fullmatch(r['Ref'])]
    changed = 0
    with open(OUT, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for r in sorted(rows, key=lambda z: z['Ref']):
            rot = float(r['Rot'])
            phi = jlc_rotation(rot, r['Side'], r['Package'])
            if abs(((phi - rot + 180) % 360) - 180) > 0.01:
                changed += 1
            w.writerow([r['Ref'],
                        f"{float(r['PosX']):.4f}mm",
                        f"{float(r['PosY']):.4f}mm",
                        r['Side'],
                        f"{phi:g}"])
    print(f"{OUT}: {len(rows)} placements, {changed} rotations corrected")


if __name__ == '__main__':
    main()
