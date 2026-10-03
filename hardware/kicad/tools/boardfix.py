#!/usr/bin/env python3
"""Two board edits from the October 2026 recheck, scripted through pcbnew.

    python3 tools/boardfix.py --check   # report what would change, write nothing
    python3 tools/boardfix.py           # apply, refill zones, save

1. U1's silkscreen header letters. The board carries the four `fp_text user`
   letters A/B/C/D at the library positions with Y negated, which puts A by
   the D header and B by C (recheck section 03; since commit 4467882). They
   are set back to lib/vuulgaris.pretty/DAISY_PATCH_SM.kicad_mod's positions,
   read from that file, not typed in here. The board's copies also carry
   `(justify mirror)` on F.SilkS, which the library does not, so they would
   print backwards; that is cleared too. Nothing else on U1 changes.

2. Copper to edge. vuulgaris.kicad_pro now sets min_copper_edge_clearance to
   0.3 (it was 0, and the In2 GND plane was poured onto the routed edge all
   round, recheck section 11). The rule is also set on the loaded board so
   the refill here honours it whether or not LoadBoard reads the project.

Close the board in KiCad first, or File -> Revert after this runs: Pcbnew
holds the design in memory and its next save would wipe the change.

--check first, then diff the saved board against HEAD: only U1's four texts
and the zone fills should move.
"""
import os, re, sys, subprocess
import proj

PCB = proj.P.pcb
LIBFP = os.path.join(proj.P.dir, "lib", "vuulgaris.pretty", "DAISY_PATCH_SM.kicad_mod")
KPY = ("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework"
       "/Versions/3.9/bin/python3")
CHECK = "--check" in sys.argv
EDGE_MM = 0.3

GEN = r'''
import pcbnew, sys
LETTERS = %r
CHECK = %r
b = pcbnew.LoadBoard(%r)
fp = b.FindFootprintByReference("U1")
if fp is None:
    sys.exit("no U1 on the board")
done = set()
for it in fp.GraphicalItems():
    if not isinstance(it, pcbnew.FP_TEXT) or it.GetText() not in LETTERS:
        continue
    t = it.GetText()
    x, y = LETTERS[t]
    p0 = it.GetPos0()
    now = (round(pcbnew.ToMM(p0.x), 3), round(pcbnew.ToMM(p0.y), 3))
    print(f"U1 {t}: local {now} -> {(x, y)}")
    if it.IsMirrored():
        print(f"U1 {t}: mirrored on {it.GetLayerName()} -> not mirrored")
    if not CHECK:
        # FromMM truncates: -16.002 came out as -16.001999
        it.SetPos0(pcbnew.VECTOR2I(round(x * 1e6), round(y * 1e6)))
        it.SetDrawCoord()
        it.SetMirrored(False)
    done.add(t)
missing = set(LETTERS) - done
if missing:
    sys.exit(f"U1 has no user text {sorted(missing)} -- nothing written")
ds = b.GetDesignSettings()
print(f"copper to edge: {pcbnew.ToMM(ds.m_CopperEdgeClearance):.3f} -> {%r:.3f} mm")
if CHECK:
    raise SystemExit(0)
ds.m_CopperEdgeClearance = pcbnew.FromMM(%r)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(%r, b)
print("saved")
'''


def library_letters():
    s = open(LIBFP).read()
    out = {}
    for t, x, y in re.findall(r'\(fp_text user "([ABCD])" \(at ([-\d.]+) ([-\d.]+)', s):
        out[t] = (float(x), float(y))
    if sorted(out) != ["A", "B", "C", "D"]:
        sys.exit(f"{LIBFP}: expected user texts A-D, found {sorted(out)}")
    return out


def main():
    if not os.path.exists(KPY):
        sys.exit(f"KiCad's Python is not at {KPY}")
    letters = library_letters()
    code = GEN % (letters, CHECK, PCB, EDGE_MM, EDGE_MM, PCB)
    r = subprocess.run([KPY, "-c", code], capture_output=True, text=True)
    print(r.stdout.strip())
    # pcbnew grumbles about wxApp on a headless load and works anyway; only the
    # exit code means anything.
    if r.returncode:
        sys.exit((r.stderr or r.stdout).strip() or "boardfix failed")
    if not CHECK:
        print("now: File -> Revert in Pcbnew if it is open, then rerun drc.py")


if __name__ == "__main__":
    main()
