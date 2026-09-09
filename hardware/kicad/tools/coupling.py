"""
coupling.py -- find where an aggressor track runs alongside a victim track.

An autorouter optimises for completion. It has no idea that BBD_CLK is a 100kHz
square wave with fast edges sitting two millimetres from BBD_SIGIN, which is the
classic bucket-brigade failure: clock whine riding on the output. This turns that
from an opinion into a number -- for every aggressor/victim pair, how far they run
parallel and how close.

    python3 tools/coupling.py                 # after importing the .ses
    python3 tools/coupling.py --min 3.0       # only runs longer than 3mm

Coupling is checked on the same layer AND broadside between F.Cu and In1.Cu,
which this stackup puts 0.2104mm apart -- closer than most side-by-side spacing,
and easy to miss because the tracks do not look near each other in 2D. B.Cu is
not paired with F.Cu or In1.Cu: In2.Cu is a solid ground plane and shields it.
"""
import re, sys, math

KI  = "/Users/dylanhackett/V1/hardware/kicad"
PCB = f"{KI}/vuulgaris.kicad_pcb"

AGGRESSOR = re.compile(r'BBD_CLK|BBD_CLKN|CLK_|OLED_(SCK|MOSI|CS|DC)|I2C_|SD_CLK|SD_CMD|SD_D0')
VICTIM    = re.compile(r'AUDIO_|BBD_(SIGIN|RAW|DRY|WET|MIX|SUM|OUT|AC|IN)|LPG_|HP_|EXT_|SRC_|CV_|LINE_OUT')

PARALLEL_DEG = 25.0
MAX_GAP_MM   = 2.0
ADJACENT     = {frozenset(("F.Cu", "In1.Cu"))}

def segments(text):
    nets = {int(m.group(1)): m.group(2)
            for m in re.finditer(r'\n  \(net (\d+) "([^"]*)"\)', text)}
    out = []
    for m in re.finditer(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                         r' \(width ([\d.]+)\) \(layer "([^"]+)"\) \(net (\d+)\)', text):
        x1, y1, x2, y2, w = map(float, m.groups()[:5])
        out.append((x1, y1, x2, y2, w, m.group(6), nets.get(int(m.group(7)), "?")))
    return out

def overlap(a, b):
    ax, ay = a[2] - a[0], a[3] - a[1]
    bx, by = b[2] - b[0], b[3] - b[1]
    la, lb = math.hypot(ax, ay), math.hypot(bx, by)
    if la < 0.05 or lb < 0.05:
        return None
    cosang = min(1.0, abs((ax * bx + ay * by) / (la * lb)))
    if math.degrees(math.acos(cosang)) > PARALLEL_DEG:
        return None
    ux, uy = ax / la, ay / la
    t = [((b[0] - a[0]) * ux + (b[1] - a[1]) * uy),
         ((b[2] - a[0]) * ux + (b[3] - a[1]) * uy)]
    t0, t1 = max(0.0, min(t)), min(la, max(t))
    if t1 - t0 <= 0.05:
        return None
    perp = lambda px, py: abs((px - a[0]) * (-uy) + (py - a[1]) * ux)
    gap = (perp(b[0], b[1]) + perp(b[2], b[3])) / 2.0 - (a[4] + b[4]) / 2.0
    return t1 - t0, max(0.0, gap)

def main():
    minlen = 1.0
    if "--min" in sys.argv:
        minlen = float(sys.argv[sys.argv.index("--min") + 1])
    segs = segments(open(PCB).read())
    if not segs:
        print("no track segments in the board -- nothing routed yet")
        return
    agg = [s for s in segs if AGGRESSOR.search(s[6])]
    vic = [s for s in segs if VICTIM.search(s[6])]
    print(f"{len(segs)} segments, {len(agg)} aggressor, {len(vic)} victim")
    if not agg or not vic:
        print("nothing to compare")
        return
    pairs = {}
    for a in agg:
        for b in vic:
            if a[6] == b[6]:
                continue
            same = a[5] == b[5]
            if not (same or frozenset((a[5], b[5])) in ADJACENT):
                continue
            r = overlap(a, b)
            if not r or r[1] > MAX_GAP_MM:
                continue
            key = (a[6], b[6], a[5] if same else f"{a[5]}/{b[5]}")
            if key not in pairs or r[0] > pairs[key][0]:
                pairs[key] = r
    rows = sorted(((v[0], v[1], k) for k, v in pairs.items()), reverse=True)
    rows = [r for r in rows if r[0] >= minlen]
    if not rows:
        print(f"no aggressor/victim pair runs parallel for {minlen}mm within {MAX_GAP_MM}mm")
        return
    print(f"\n{len(rows)} coupled runs over {minlen}mm:\n")
    print(f"  {'length':>9} {'gap':>8}  {'layer':<14} aggressor x victim")
    for length, gap, (an, bn, lay) in rows:
        flag = "   <-- FIX" if (length > 10 and gap < 0.5) else ""
        print(f"  {length:8.1f}mm {gap:7.2f}mm  {lay:<14} {an} x {bn}{flag}")

if __name__ == "__main__":
    main()
