#!/usr/bin/env python3
"""Connectivity, parity and clearance check on the board -- no KiCad needed.

KiCad 7's kicad-cli has no `drc` subcommand, and this used to stand in for it.
It no longer does: `tools/drc.py` runs KiCad's own engine through pcbnew and is
the authority on clearance. This is the fast pass, and the only one that checks
parity against netmap.json, which DRC knows nothing about. Run both.

The demotion was earned. This file's track-to-track test measured from segment
ENDPOINTS, which is exact for two segments that do not meet and wrong for an X
crossing, whose closest point is the intersection. /LPG_LED and /LPG_LEDK lay
directly across each other on both channels and measured 0.6mm apart. See
seg_seg() below, and tools/drc.py's docstring for what that nearly cost.

Three more mistakes cost real time building it, all recorded here so they are
not repeated:

  * A custom pad's (size ...) is a 0.005mm ANCHOR. The copper is in
    (primitives (gr_poly ...)). J11's VBUS pads read as points and the net
    looked broken.
  * A track reaching a via lands anywhere inside its annular ring, not on its
    centre. VBUS's B.Cu track ends 0.056mm off the via and is connected.
  * Clearance is PER NETCLASS, and between two nets it is the LARGER of the
    two. Hardcoding 0.2 missed all 23 real errors on Power_5V_IN (0.3) and
    Rails_12V (0.25) and reported the board clean.

Circles and ovals are also measured as circles and ovals; treating them as
their bounding box invents ~0.35mm of copper at each corner and manufactured
113 violations that did not exist.
"""
import re, math, json, collections, sys, os, fnmatch
import proj                     # takes --project NAME out of argv; see tools/proj.py

PCB = sys.argv[1] if len(sys.argv) > 1 else proj.P.pcb
PRO = proj.P.pro
MAP = proj.P.netmap


def blocks(t, kind='footprint'):
    pos = 0
    while True:
        m = re.compile(r'\(%s ' % kind).search(t, pos)
        if not m:
            return
        st = m.start(); d = 0; j = st
        while j < len(t):
            if t[j] == '(':
                d += 1
            elif t[j] == ')':
                d -= 1
                if d == 0:
                    break
            j += 1
        yield t[st:j + 1]; pos = j + 1


T = open(PCB).read()
nets = {int(m.group(1)): m.group(2) for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', T)}
P = json.loads(open(PRO).read())
CLS = {c['name']: c.get('clearance', 0.2) for c in P['net_settings']['classes']}
NC = {}
for pat in P['net_settings'].get('netclass_patterns', []):
    NC[pat['pattern']] = pat['netclass']
DEFAULT = CLS.get('Default', 0.2)


def clr(n):
    # KiCad's netclass patterns are wildcards (the faceplate's "/PAD*", "/CAP*");
    # an exact-name lookup silently gave those nets the Default clearance.
    name = nets.get(n, '')
    cls = NC.get(name) or next((c for pat, c in NC.items() if fnmatch.fnmatchcase(name, pat)), 'Default')
    return CLS.get(cls, DEFAULT)


def pair_clr(a, b):
    return max(clr(a), clr(b))


PADS = []
for blk in blocks(T):
    a = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    ax, ay, ang = float(a.group(1)), float(a.group(2)), float(a.group(3) or 0)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    ref = (re.search(r'\(fp_text reference "([^"]+)"', blk) or [None, '?'])[1]
    for pm in re.finditer(r'\(pad "([^"]+)" (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)'
                          r' \(size ([\d.]+) ([\d.]+)\)[\s\S]*?(?=\n    \(pad "|\n  \)|\n    \(model)', blk):
        pin, typ, shape = pm.group(1), pm.group(2), pm.group(3)
        lx, ly = float(pm.group(4)), float(pm.group(5))
        # A pad's angle in the file is its ABSOLUTE orientation (footprint's included),
        # and absent when that is 0 -- not "absent, so use the footprint's". Taking the
        # footprint's stood the faceplate U1's pins on end (flipped, turned 90) and
        # reported 27 overlaps with the neighbouring pins' tracks that were not there.
        prot = float(pm.group(6) or 0)
        w, h = float(pm.group(7)), float(pm.group(8))
        if shape == 'custom':
            pts = [(float(x), float(y)) for x, y in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', pm.group(0))]
            if pts:
                w = max(p[0] for p in pts) - min(p[0] for p in pts)
                h = max(p[1] for p in pts) - min(p[1] for p in pts)
            shape = 'rect'
        rr = re.search(r'\(roundrect_rratio ([\d.]+)\)', pm.group(0))
        rad = float(rr.group(1)) * min(w, h) if rr else 0.0
        nm = re.search(r'\(net (\d+)', pm.group(0))
        thru = typ in ('thru_hole', 'np_thru_hole')
        PADS.append(dict(x=ax + lx * ca + ly * sa, y=ay - lx * sa + ly * ca, w=w, h=h,
                         shape=shape, rad=rad, rot=prot, ref=ref, pin=pin,
                         net=int(nm.group(1)) if nm else 0, thru=thru,
                         lay='*' if thru else ('B.Cu' if '"B.Cu"' in pm.group(0).split('(net')[0] else 'F.Cu')))
SEG = [dict(x1=float(m.group(1)), y1=float(m.group(2)), x2=float(m.group(3)), y2=float(m.group(4)),
            w=float(m.group(5)), lay=m.group(6), net=int(m.group(7)))
       for m in re.finditer(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                            r' \(width ([\d.]+)\) \(layer "([^"]+)"\) \(net (\d+)\)', T)]
VIA = [dict(x=float(m.group(1)), y=float(m.group(2)), r=float(m.group(3)) / 2, net=int(m.group(4)))
       for m in re.finditer(r'\(via \(at ([-\d.]+) ([-\d.]+)\) \(size ([\d.]+)\)[\s\S]{0,120}?\(net (\d+)\)', T)]

# Every In2.Cu zone is a plane: a node of its own, joined to any other zone of its net it
# overlaps. This took only the FIRST In2 zone, which was all the main board ever had; the
# faceplate's GND is three (margin, corridor strip, the patch at J1), and every ground
# reaching the plane through the one it skipped read as an island.
ZONES = []
for zb in blocks(T, 'zone'):
    if '"In2.Cu"' in zb[:200]:
        head = zb[:zb.find('(filled_polygon')] if '(filled_polygon' in zb else zb
        ZONES.append((int(re.search(r'\(zone \(net (\d+)\)', zb).group(1)),
                      [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', head)]))


def inpoly(poly, px, py):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            c = not c
    return c


def p2s(px, py, s):
    dx, dy = s['x2'] - s['x1'], s['y2'] - s['y1']; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - s['x1']) * dx + (py - s['y1']) * dy) / L))
    return math.hypot(px - (s['x1'] + t * dx), py - (s['y1'] + t * dy))


def pad_pt(p, qx, qy):
    """distance from pad copper edge to a point, honouring the pad's real shape"""
    dx, dy = qx - p['x'], qy - p['y']
    if p['rot']:
        c, s = math.cos(math.radians(-p['rot'])), math.sin(math.radians(-p['rot']))
        dx, dy = dx * c - dy * s, dx * s + dy * c
    if p['shape'] == 'circle':
        return max(math.hypot(dx, dy) - p['w'] / 2, 0.0)
    if p['shape'] == 'oval':
        a, b = p['w'] / 2, p['h'] / 2
        if a >= b:
            cx = max(-(a - b), min(a - b, dx)); return max(math.hypot(dx - cx, dy) - b, 0.0)
        cy = max(-(b - a), min(b - a, dy)); return max(math.hypot(dx, dy - cy) - a, 0.0)
    r = p.get('rad', 0.0)
    ex = max(abs(dx) - (p['w'] / 2 - r), 0.0); ey = max(abs(dy) - (p['h'] / 2 - r), 0.0)
    return max(math.hypot(ex, ey) - r, 0.0)


def pad_samples(p):
    """centre, edge midpoints and corners of a pad, a hair inside its copper, board coords"""
    out = []
    for fx, fy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        r = p.get('rad', 0.0)
        dx, dy = fx * (p['w'] / 2 - 1e-3), fy * (p['h'] / 2 - 1e-3)
        if fx and fy and r:                                  # pull corners onto the fillet
            dx -= fx * r * (1 - 2 ** -0.5)
            dy -= fy * r * (1 - 2 ** -0.5)
        if p['rot']:
            c, s_ = math.cos(math.radians(p['rot'])), math.sin(math.radians(p['rot']))
            dx, dy = dx * c + dy * s_, -dx * s_ + dy * c
        out.append((p['x'] + dx, p['y'] + dy))
    return out


def pads_touch(a, b):
    return any(pad_pt(b, x, y) <= 0 for x, y in pad_samples(a)) or \
           any(pad_pt(a, x, y) <= 0 for x, y in pad_samples(b))


def pad_seg(p, s, N=64):
    return min(pad_pt(p, s['x1'] + i / N * (s['x2'] - s['x1']),
                      s['y1'] + i / N * (s['y2'] - s['y1'])) for i in range(N + 1)) - s['w'] / 2


# ---------------- connectivity ----------------
byn = collections.defaultdict(lambda: dict(p=[], s=[], v=[]))
for p in PADS: byn[p['net']]['p'].append(p)
for s in SEG: byn[s['net']]['s'].append(s)
for v in VIA: byn[v['net']]['v'].append(v)
broken = []
for net, g in byn.items():
    if net == 0 or 'unconnected-' in nets.get(net, '') or len(g['p']) < 2:
        continue
    items = [('p', x) for x in g['p']] + [('s', x) for x in g['s']] + [('v', x) for x in g['v']]
    zones = [poly for zn, poly in ZONES if zn == net]
    par = list(range(len(items) + len(zones))); PLANE = len(items)
    def find(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    def uni(a, b):
        a, b = find(a), find(b)
        if a != b: par[a] = b
    def inpad(p, x, y, m=0.0): return pad_pt(p, x, y) <= m
    for i, (ti, a) in enumerate(items):
        for j in range(i + 1, len(items)):
            tj, b = items[j]; h = False
            if ti == 'p' and tj == 'p':
                # Overlapping pads of one net are one piece of copper, as KiCad counts
                # them. The faceplate's scrub pads depend on it: a sliver bar reaches
                # its via only through a bridge pad laid over it and its neighbour.
                # Without this every bridge chain read as a separate island.
                h = a['lay'] in ('*', b['lay']) or b['lay'] == '*'
                h = h and abs(a['x'] - b['x']) <= (a['w'] + b['w']) / 2 + 1e-6 \
                    and abs(a['y'] - b['y']) <= (a['h'] + b['h']) / 2 + 1e-6 and pads_touch(a, b)
            elif ti == 's' and tj == 's':
                h = a['lay'] == b['lay'] and min(p2s(a['x1'], a['y1'], b), p2s(a['x2'], a['y2'], b),
                                                 p2s(b['x1'], b['y1'], a), p2s(b['x2'], b['y2'], a)) <= (a['w'] + b['w']) / 2
            elif ti == 's' and tj == 'v': h = p2s(b['x'], b['y'], a) <= b['r'] + a['w'] / 2
            elif ti == 'v' and tj == 's': h = p2s(a['x'], a['y'], b) <= a['r'] + b['w'] / 2
            elif ti == 'p' and tj == 's': h = a['lay'] in ('*', b['lay']) and any(inpad(a, b['x' + e], b['y' + e], b['w'] / 2) for e in '12')
            elif ti == 's' and tj == 'p': h = b['lay'] in ('*', a['lay']) and any(inpad(b, a['x' + e], a['y' + e], a['w'] / 2) for e in '12')
            elif ti == 'p' and tj == 'v': h = inpad(a, b['x'], b['y'], b['r'])
            elif ti == 'v' and tj == 'p': h = inpad(b, a['x'], a['y'], a['r'])
            if h: uni(i, j)
    for k, poly in enumerate(zones):
        for i, (ti, a) in enumerate(items):
            if (ti == 'v' or (ti == 'p' and a['thru'])) and inpoly(poly, a['x'], a['y']): uni(i, PLANE + k)
        for k2 in range(k + 1, len(zones)):             # overlapping zones of one net join
            if any(inpoly(zones[k2], x, y) for x, y in poly) or any(inpoly(poly, x, y) for x, y in zones[k2]):
                uni(PLANE + k, PLANE + k2)
    grp = collections.defaultdict(list)
    for i, (ti, a) in enumerate(items):
        if ti == 'p': grp[find(i)].append(f"{a['ref']}.{a['pin']}")
    if len(grp) > 1: broken.append((nets[net], list(grp.values())))

def seg_seg(s, o):
    """Distance between two segment CENTRELINES -- zero when they cross.

    This used to be the minimum of the four endpoint-to-segment distances,
    which is exact for two segments that do not meet and wrong in the one case
    that matters most: an X crossing. The closest point of a crossing is the
    intersection, which is not an endpoint of either segment, so the endpoint
    formula returns a comfortable positive gap for two tracks that are lying
    on top of each other.

    It missed a dead short on both channels. /LPG_LED_L crossed /LPG_LEDK_L at
    (229.42, 121.895) and /LPG_LED_R crossed /LPG_LEDK_R at (231.675, 155.0),
    both on F.Cu, and this file reported "clearance violations: 0" for days.
    KiCad's own DRC found them in a second. The nets either side of that short
    are the two ends of the vactrol LED string, so it shorted out both LEDs --
    it would have undone the LED-drive fix entirely and the gates would never
    have opened.

    Orientation test first, endpoint distances only if they do not cross.
    """
    def ccw(ax, ay, bx, by, cx, cy):
        return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    d1 = ccw(s['x1'], s['y1'], s['x2'], s['y2'], o['x1'], o['y1'])
    d2 = ccw(s['x1'], s['y1'], s['x2'], s['y2'], o['x2'], o['y2'])
    d3 = ccw(o['x1'], o['y1'], o['x2'], o['y2'], s['x1'], s['y1'])
    d4 = ccw(o['x1'], o['y1'], o['x2'], o['y2'], s['x2'], s['y2'])
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(p2s(s['x1'], s['y1'], o), p2s(s['x2'], s['y2'], o),
               p2s(o['x1'], o['y1'], s), p2s(o['x2'], o['y2'], s))


# ---------------- clearance ----------------
G = collections.defaultdict(list); C = 3.0
for i, s in enumerate(SEG):
    x0, x1 = sorted((s['x1'], s['x2'])); y0, y1 = sorted((s['y1'], s['y2']))
    for gx in range(int(x0 // C), int(x1 // C) + 1):
        for gy in range(int(y0 // C), int(y1 // C) + 1): G[(gx, gy)].append(i)
viol = []
for i, s in enumerate(SEG):
    x0, x1 = sorted((s['x1'], s['x2'])); y0, y1 = sorted((s['y1'], s['y2']))
    cand = set()
    for gx in range(int(x0 // C) - 1, int(x1 // C) + 2):
        for gy in range(int(y0 // C) - 1, int(y1 // C) + 2): cand |= set(G.get((gx, gy), []))
    for j in cand:
        if j <= i: continue
        o = SEG[j]
        if o['lay'] != s['lay'] or o['net'] == s['net']: continue
        req = pair_clr(s['net'], o['net'])
        g = seg_seg(s, o) - s['w'] / 2 - o['w'] / 2
        if g < req - 5e-4: viol.append(('track/track', nets.get(s['net']), nets.get(o['net']), s['lay'], round(g, 4), req))
for p in PADS:
    for s in SEG:
        if s['net'] == p['net'] or p['lay'] not in ('*', s['lay']): continue
        if abs((s['x1'] + s['x2']) / 2 - p['x']) > 15 or abs((s['y1'] + s['y2']) / 2 - p['y']) > 15: continue
        req = pair_clr(p['net'], s['net'])
        g = pad_seg(p, s)
        if g < req - 5e-4: viol.append(('track/pad', f"{p['ref']}.{p['pin']}", nets.get(s['net']), s['lay'], round(g, 4), req))
    for v in VIA:
        if v['net'] == p['net']: continue
        req = pair_clr(p['net'], v['net'])
        g = pad_pt(p, v['x'], v['y']) - v['r']
        if g < req - 5e-4: viol.append(('via/pad', f"{p['ref']}.{p['pin']}", nets.get(v['net']), '-', round(g, 4), req))
for v in VIA:
    for s in SEG:
        if s['net'] == v['net']: continue
        req = pair_clr(v['net'], s['net'])
        g = p2s(v['x'], v['y'], s) - v['r'] - s['w'] / 2
        if g < req - 5e-4: viol.append(('via/track', nets.get(v['net']), nets.get(s['net']), s['lay'], round(g, 4), req))

# ---------------- parity ----------------
nm = json.load(open(MAP))
board = collections.defaultdict(dict)
for blk in blocks(T):
    r = (re.search(r'\(fp_text reference "([^"]+)"', blk) or [None, None])[1]
    if not r: continue
    # Bound each pad to ITSELF, the same way the clearance parser above does.
    # This used to search up to 600 characters ahead for the next "(net ...)",
    # which is only safe if every pad has one. A pad with no net then borrowed
    # the NEXT pad's net and swallowed that pad whole, so it was never recorded
    # at all. It surfaced on 2026-09-22 when SW4-SW9 each lost a diagonal pair
    # of connections: pad 1 on SW4 read as GND and pad 2 -- genuinely on GND --
    # read as missing, six parity "mismatches" on a board that was correct.
    # Empty-named pads (NPTH holes) still do not match [^"]+ and are skipped.
    for pm in re.finditer(r'\(pad "([^"]+)"([\s\S]*?)(?=\n    \(pad "|\n  \)|\n    \(model)', blk):
        nn = re.search(r'\(net (\d+) "([^"]*)"\)', pm.group(2))
        board[r][pm.group(1)] = nn.group(2) if nn else None
par = [(r, p, n, board.get(r, {}).get(p)) for r, pins in nm.items() for p, n in pins.items()
       if board.get(r, {}).get(p) != '/' + n]
# The other direction. Parity above asks "is every pin netmap names on the net
# it names?" -- it never asks "is any pad on a net netmap did NOT ask for?".
# That is the direction that would let a deliberately disconnected pad stay
# quietly on GND. On 2026-09-22 twelve pads across SW4-SW9 were taken off their
# nets to un-short the buttons, and nothing here would have noticed if one had
# been missed. KiCad's own "unconnected-(...)" nets and net-less pads are fine.
extra = [(r, p, n) for r, pins in board.items() for p, n in pins.items()
         if n and not n.startswith('unconnected-') and p not in nm.get(r, {})]
degen = [1 for s in SEG if math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']) < 0.01]

print(f"netclass clearances: { {k: v for k, v in sorted(CLS.items())} }")
print(f"pads {len(PADS)}  segments {len(SEG)}  vias {len(VIA)}")
print(f"\nnets not fully connected : {len(broken)}")
for n, gs in broken: print(f"   {n}: " + " | ".join(str(x[:6]) for x in gs))
print(f"clearance violations     : {len(viol)}")
for v in sorted(viol, key=lambda z: z[4])[:20]: print(f"   {v}")
print(f"board/schematic parity   : {len(par)} mismatches over {sum(len(v) for v in nm.values())} connections")
for x in par[:10]: print(f"   {x}")
print(f"pads on nets netmap never asked for: {len(extra)}")
for x in extra[:10]: print(f"   {x}")
print(f"degenerate (zero-length) segments: {sum(degen)}")
