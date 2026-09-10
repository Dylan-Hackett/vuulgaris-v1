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
PCB = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--pcb=")),
           f"{KI}/vuulgaris.kicad_pcb")
PRO = f"{KI}/vuulgaris.kicad_pro"
PLANE_LAYER = "In2.Cu"
# How far a stub may reach. 0.80mm is the tight fit against a 0603 pad; past
# about 2mm the stub inductance starts undoing the point of a local drop, so
# anything long is reported rather than hidden.
REACH_MM = float(next((a.split("=")[1] for a in sys.argv if a.startswith("--reach=")), 3.0))
CHECK = "--check" in sys.argv

def netclass_gnd():
    for c in json.load(open(PRO))["net_settings"]["classes"]:
        if c["name"] == "GND":
            return c["via_diameter"], c["via_drill"], c["clearance"], c["track_width"]
    return 0.8, 0.4, 0.2, 0.5

VIA_D, VIA_DRILL, CLEAR, TRACK_W = netclass_gnd()
# KiCad checks hole-to-copper and hole-to-hole separately from copper-to-copper,
# with its own board-setup minimum. 0.25mm is what this board is set to.
HOLE_R = VIA_DRILL / 2.0
HOLE_CLEAR = 0.25

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
            # A CUSTOM pad's (size ...) is only its anchor. J11's four merged
            # USB-C pads declare 0.005x0.005 -- five microns -- while the real
            # copper is a 0.6x1.3mm gr_poly primitive. Reading (size) alone made
            # them invisible, and a ground stub got routed 0.0148mm from VBUS.
            prim = [(float(a), float(b)) for a, b in
                    re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', pblk)]
            if prim:
                pw = re.search(r'\(width ([\d.]+)\)', pblk)
                pw = float(pw.group(1)) if pw else 0.0
                xs_ = [q[0] for q in prim]; ys_ = [q[1] for q in prim]
                sw = max(sw, (max(xs_) - min(xs_)) + pw)
                sh = max(sh, (max(ys_) - min(ys_)) + pw)
                px += (max(xs_) + min(xs_)) / 2.0
                py += (max(ys_) + min(ys_)) / 2.0
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
    # Net is captured, not just position. The idempotence check below asks "does
    # this pad already have a drop to the plane", and a via belonging to some
    # other net sitting 1mm away answers that question wrongly -- it connects
    # nothing. Counting those marked 27 of 140 ground pads as already done.
    vias = []
    for m in re.finditer(r'\(via \(at ([-\d.]+) ([-\d.]+)\) \(size ([\d.]+)\)'
                         r'(?:[^\n]*?\(net (\d+)\))?', text):
        vias.append((float(m.group(1)), float(m.group(2)), float(m.group(3)),
                     int(m.group(4)) if m.group(4) else -1))
    segs = []
    for m in re.finditer(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                         r' \(width ([\d.]+)\) \(layer "([^"]+)"\)', text):
        v = list(map(float, m.groups()[:5]))
        segs.append((v[0], v[1], v[2], v[3], v[4], m.group(6)))
    return pads, gnd_smd, vias, segs

def gap_rect(A, B):
    return math.hypot(max(A[0]-B[2], B[0]-A[2], 0.0), max(A[1]-B[3], B[1]-A[3], 0.0))

def seg_seg(a, b):
    """Minimum distance between two segments; negative when they cross."""
    def d_pt(px, py, s):
        x1, y1, x2, y2 = s[0], s[1], s[2], s[3]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx*dx + dy*dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy)/L2))
        return math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))
    den = (a[2]-a[0])*(b[3]-b[1]) - (a[3]-a[1])*(b[2]-b[0])
    if abs(den) > 1e-12:
        t = ((b[0]-a[0])*(b[3]-b[1]) - (b[1]-a[1])*(b[2]-b[0])) / den
        u = ((b[0]-a[0])*(a[3]-a[1]) - (b[1]-a[1])*(a[2]-a[0])) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return -1.0
    return min(d_pt(a[0], a[1], b), d_pt(a[2], a[3], b),
               d_pt(b[0], b[1], a), d_pt(b[2], b[3], a))

def seg_rect(seg, r):
    """Distance from a segment to an axis-aligned rectangle; 0 if it enters it.

    The first version approximated the pad with its circumscribed circle, which
    for a 1.5x0.5mm SOIC pad is a 0.79mm radius -- so a stub leaving one pin was
    judged to be colliding with its neighbours and 23 of 140 pads became
    unplaceable for no real reason."""
    x0, y0, x1, y1 = r
    edges = [(x0, y0, x1, y0), (x1, y0, x1, y1),
             (x1, y1, x0, y1), (x0, y1, x0, y0)]
    for e in edges:
        if seg_seg(seg, (e[0], e[1], e[2], e[3])) <= 0.0:
            return 0.0
    return min(seg_seg(seg, (e[0], e[1], e[2], e[3])) for e in edges)

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
        if any(v[3] == netno and math.hypot(cx-v[0], cy-v[1]) < 1.8 for v in vias):
            skipped += 1
            continue
        spot = None
        for d in [x/20.0 for x in range(16, int(REACH_MM*20) + 1)]:
            for adeg in range(0, 360, 15):
                x = cx + d*math.cos(math.radians(adeg))
                y = cy + d*math.sin(math.radians(adeg))
                box = (x-R, y-R, x+R, y+R)
                hole = (x-HOLE_R, y-HOLE_R, x+HOLE_R, y+HOLE_R)
                ok = True
                # EVERY pad on EVERY layer. The via is a through-hole; filtering
                # these by the served pad's side is what put four vias exactly on
                # top of C509/POS12V, U4.7, C410/LPG_RES_R and U10.7 at 0.0000mm,
                # each of which then also tripped hole_clearance and
                # solder_mask_bridge -- 12 DRC errors from one wrong condition.
                for prect, pside, pth in pads:
                    if prect == rect: continue
                    if gap_rect(box, prect) <= 0:
                        ok = False; break
                    if gap_rect(hole, prect) < HOLE_CLEAR:
                        ok = False; break
                if ok:
                    for v in vias + newvias:
                        if math.hypot(x-v[0], y-v[1]) < (VIA_D+v[2])/2.0 + CLEAR:
                            ok = False; break
                if ok:
                    # A via is a through-hole: it passes F.Cu to B.Cu and so has
                    # to clear tracks on EVERY copper layer, not just the pad's
                    # own and the plane. Filtering by layer here let 134 of 140
                    # vias land on foreign traces, one of them 0.525mm INSIDE a
                    # BBD_CLK_L track.
                    for s in segs:
                        if seg_dist(x, y, s) < R:
                            ok = False; break
                if ok:
                    # And the STUB. Where the via lands says nothing about the
                    # path taken to get there: the first version drove 15 of 139
                    # stubs straight through foreign traces, one 1.375mm inside a
                    # NEG12V track. The stub is single-layer, so only its own
                    # side matters.
                    stub = (cx, cy, x, y, TRACK_W)
                    for s in segs:
                        if s[5] != side:
                            continue
                        if seg_seg(stub, s) - (TRACK_W + s[4])/2.0 < CLEAR:
                            ok = False; break
                if ok:
                    # The stub against foreign VIAS and PADS, not just traces.
                    # Checking it against traces alone still let a stub pass
                    # 0.126mm through someone else's via. A via is a through-hole
                    # so it counts on every layer; pads count on the stub's own
                    # layer, plus any through-hole pad.
                    for v in vias:
                        if v[3] == netno:
                            continue
                        if seg_dist(v[0], v[1], (cx, cy, x, y, TRACK_W)) \
                           - v[2]/2.0 < CLEAR:
                            ok = False; break
                if ok:
                    for prect, pside, pth in pads:
                        if prect == rect or not (pside == side or pth):
                            continue
                        if seg_rect((cx, cy, x, y), prect) - TRACK_W/2.0 < CLEAR:
                            ok = False; break
                if ok:
                    spot = (x, y, d); break
            if spot: break
        if spot:
            placed.append((ref, num, cx, cy, spot[0], spot[1], spot[2], side, netno))
            newvias.append((spot[0], spot[1], VIA_D, netno))
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
        longs = [(p[0], p[1], p[6]) for p in placed if p[6] > 2.0]
        if longs:
            print(f"  stubs over 2.0mm ({len(longs)}) -- local drop is compromised, consider"
                  f" ripping up a neighbour:")
            for ref, num, dd in sorted(longs, key=lambda z: -z[2]):
                print(f"     {ref}.{num}  {dd:.2f}mm")
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
