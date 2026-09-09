"""
gndvias.py -- give every ground pad its own short drop to the In2.Cu plane.

Run AFTER importing a GND-free Specctra session. Handed the GND net, Freerouting
daisy-chains ground: the first attempt on this board produced 267 trace segments
and only 66 vias, so ground wandered across the card looking for other ground
pads instead of going straight down. That turns a solid plane into a shared
return path, which is the thing the plane exists to prevent.

Per pad:
  through-hole GND pad -> nothing, the barrel already passes through In2.Cu
  SMD GND pad          -> one via as close as it will legally sit, plus a stub
                          from pad to via on the pad's own layer

Via size, drill, clearance and stub width come from the GND net class in
vuulgaris.kicad_pro, so this follows the design rules rather than inventing them.

    python3 tools/gndvias.py --check     report what it would add
    python3 tools/gndvias.py             write them into the board

Spots are searched outward in 15-degree steps and accepted only when clear of
every pad, via and track already on the board -- including what the autorouter
just imported. Idempotent: a pad that already has a via within 1.8mm is left
alone, so it is safe to re-run after hand edits.
"""
import re, sys, json, math, uuid

KI  = "/Users/dylanhackett/V1/hardware/kicad"
PCB = f"{KI}/vuulgaris.kicad_pcb"
PRO = f"{KI}/vuulgaris.kicad_pro"
PLANE_LAYER = "In2.Cu"
CHECK = "--check" in sys.argv

def netclass_gnd():
    for c in json.load(open(PRO))["net_settings"]["classes"]:
        if c["name"] == "GND":
            return c["via_diameter"], c["via_drill"], c["clearance"], c["track_width"]
    return 0.8, 0.4, 0.2, 0.5

VIA_D, VIA_DRILL, CLEAR, TRACK_W = netclass_gnd()

def fp_blocks(text):
    pos = 0
    while True:
        m = re.compile(r'\(footprint "').search(text, pos)
        if not m:
            return
        st = m.start(); d = 0; j = st
        while j < len(text):
            if text[j] == '(': d += 1
            elif text[j] == ')':
                d -= 1
                if d == 0: break
            j += 1
        yield text[st:j + 1]
        pos = j + 1

def board_geometry(text):
    pads, gnd_smd = [], []
    for blk in fp_blocks(text):
        a = re.search(r'\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)', blk)
        L = re.match(r'\(footprint "[^"]*" \(layer "([^"]+)"', blk)
        side = L.group(1) if L else "F.Cu"
        rm = re.search(r'\(fp_text reference "([^"]+)"', blk)
        ref = rm.group(1) if rm else "?"
        ax, ay = float(a.group(1)), float(a.group(2))
        ang = float(a.group(3)) if a.group(3) else 0.0
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        place = lambda lx, ly: (ax + lx * ca + ly * sa, ay - lx * sa + ly * ca)
        # Pad sub-blocks are taken with a balanced-paren walk. A bounded
        # "(?:.|\n){0,500}?\n    )" tail looks equivalent and is not: it silently
        # skips any pad whose block runs long, which here found 15 ground pads
        # out of 140 and reported success.
        pi = 0
        while True:
            pm = re.compile(r'\(pad "').search(blk, pi)
            if not pm:
                break
            pst = pm.start(); pd = 0; pj = pst
            while pj < len(blk):
                if blk[pj] == '(': pd += 1
                elif blk[pj] == ')':
                    pd -= 1
                    if pd == 0: break
                pj += 1
            pblk = blk[pst:pj + 1]; pi = pj + 1
            p = re.match(r'\(pad "([^"]*)" (\w+) \w+ \(at ([-\d.]+) ([-\d.]+)[^)]*\)'
                         r' \(size ([\d.]+) ([\d.]+)\)', pblk)
            if not p:
                continue
            num, ptype = p.group(1), p.group(2)
            px, py, sw, sh = map(float, p.groups()[2:6])
            netm = re.search(r'\(net (\d+) "([^"]*)"\)', pblk)
            net = (int(netm.group(1)), netm.group(2)) if netm else None
            cs = [place(cx, cy) for cx in (px - sw/2, px + sw/2)
                                for cy in (py - sh/2, py + sh/2)]
            xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
            rect = (min(xs), min(ys), max(xs), max(ys))
            th = ptype.endswith("thru_hole")
            pads.append((rect, side, th))
            if net and net[1] == "/GND" and not th:
                gnd_smd.append((ref, num, place(px, py), rect, side, net[0]))
    vias = [(float(m.group(1)), float(m.group(2)), float(m.group(3)))
            for m in re.finditer(r'\(via \(at ([-\d.]+) ([-\d.]+)\) \(size ([\d.]+)\)', text)]
    segs = []
    for m in re.finditer(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                         r' \(width ([\d.]+)\) \(layer "([^"]+)"\)', text):
        v = list(map(float, m.groups()[:5]))
        segs.append((v[0], v[1], v[2], v[3], v[4], m.group(6)))
    return pads, gnd_smd, vias, segs

def gap_rect(A, B):
    return math.hypot(max(A[0]-B[2], B[0]-A[2], 0.0), max(A[1]-B[3], B[1]-A[3], 0.0))

def seg_dist(px, py, s):
    x1, y1, x2, y2 = s[0], s[1], s[2], s[3]
    dx, dy = x2-x1, y2-y1
    L2 = dx*dx + dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy)/L2))
    return math.hypot(px - (x1+t*dx), py - (y1+t*dy)) - s[4]/2.0

def main():
    text = open(PCB).read()
    pads, gnd_smd, vias, segs = board_geometry(text)
    R = VIA_D/2.0 + CLEAR
    print(f"GND net class: via {VIA_D}/{VIA_DRILL}mm, clearance {CLEAR}mm, stub {TRACK_W}mm")
    print(f"{len(gnd_smd)} SMD ground pads; board already has {len(vias)} vias, {len(segs)} segments")
    placed, failed, skipped, newvias = [], [], 0, []
    for ref, num, (cx, cy), rect, side, netno in gnd_smd:
        if any(math.hypot(cx-v[0], cy-v[1]) < 1.8 for v in vias):
            skipped += 1
            continue
        spot = None
        for d in [x/20.0 for x in range(16, 41)]:
            for adeg in range(0, 360, 15):
                x = cx + d*math.cos(math.radians(adeg))
                y = cy + d*math.sin(math.radians(adeg))
                box = (x-R, y-R, x+R, y+R)
                ok = True
                for prect, pside, pth in pads:
                    if prect == rect: continue
                    if (pside == side or pth) and gap_rect(box, prect) <= 0:
                        ok = False; break
                if ok:
                    for v in vias + newvias:
                        if math.hypot(x-v[0], y-v[1]) < (VIA_D+v[2])/2.0 + CLEAR:
                            ok = False; break
                if ok:
                    for s in segs:
                        if s[5] in (side, PLANE_LAYER) and seg_dist(x, y, s) < R:
                            ok = False; break
                if ok:
                    spot = (x, y, d); break
            if spot: break
        if spot:
            placed.append((ref, num, cx, cy, spot[0], spot[1], spot[2], side, netno))
            newvias.append((spot[0], spot[1], VIA_D))
        else:
            failed.append((ref, num, cx, cy, side))
    print(f"\n  vias to add            : {len(placed)}")
    print(f"  already had one nearby : {skipped}")
    print(f"  NO ROOM                : {len(failed)}")
    for ref, num, cx, cy, side in failed[:12]:
        print(f"     {ref}.{num} at ({cx:.1f}, {cy:.1f}) {side}")
    if placed:
        d = [p[6] for p in placed]
        print(f"  stub length: min {min(d):.2f}  mean {sum(d)/len(d):.2f}  max {max(d):.2f} mm")
    if CHECK:
        print("\nMODE: --check, nothing written"); return
    if not placed:
        print("nothing to do"); return
    add = []
    for ref, num, cx, cy, vx, vy, _d, side, netno in placed:
        add.append(f'  (segment (start {cx:.4f} {cy:.4f}) (end {vx:.4f} {vy:.4f})'
                   f' (width {TRACK_W}) (layer "{side}") (net {netno}) (tstamp {uuid.uuid4()}))')
        add.append(f'  (via (at {vx:.4f} {vy:.4f}) (size {VIA_D}) (drill {VIA_DRILL})'
                   f' (layers "F.Cu" "B.Cu") (net {netno}) (tstamp {uuid.uuid4()}))')
    k = text.rstrip().rfind(')')
    open(PCB, "w").write(text[:k] + "\n".join(add) + "\n" + text[k:])
    print(f"\nwrote {len(placed)} vias and {len(placed)} stubs")

if __name__ == "__main__":
    main()
