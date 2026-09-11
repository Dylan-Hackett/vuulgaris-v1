#!/usr/bin/env python3
"""Extract a netlist from a KiCad schematic by tracing wires, no KiCad needed.

Reference schematics arrive in whatever KiCad version drew them. KiCad 7's
kicad-cli refuses a 20260306 (KiCad 10) file outright, and those files carry
their connectivity geometrically -- wires and junctions, barely any labels -- so
there is nothing to grep. This walks the geometry instead.

The symbol placement transform is not assumed. Candidate transforms are scored
by how many symbol pins land on a wire, and the winner is used. Getting that
convention wrong by a sign is the single most repeated mistake in this repo's
history, so it is measured rather than believed.

Usage:  schnet.py <file.kicad_sch> [--json out.json]
"""
import re, sys, math, json, collections

TOL = 0.02


def sexp_blocks(t, head):
    """Yield balanced-paren blocks starting with '(<head>' at any depth."""
    pat = re.compile(r'\(' + head + r'[\s\n]')
    pos = 0
    while True:
        m = pat.search(t, pos)
        if not m:
            return
        st = m.start(); d = 0; j = st
        while j < len(t):
            c = t[j]
            if c == '"':                      # skip strings
                j += 1
                while j < len(t) and t[j] != '"':
                    j += 2 if t[j] == '\\' else 1
            elif c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    break
            j += 1
        yield t[st:j + 1]
        pos = j + 1


def parse(path):
    T = open(path).read()

    # ---- library pin geometry, per lib_id ------------------------------
    libpins = {}
    libsec = T[T.find('(lib_symbols'):]
    for blk in sexp_blocks(libsec, 'symbol'):
        m = re.match(r'\(symbol\s+"([^"]+)"', blk)
        if not m or ':' not in m.group(1):
            continue
        lib_id = m.group(1)
        if lib_id in libpins:
            continue
        pins = {}
        for pb in sexp_blocks(blk, 'pin'):
            a = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', pb)
            num = re.search(r'\(number "([^"]*)"', pb)
            nam = re.search(r'\(name "([^"]*)"', pb)
            if a and num:
                pins[num.group(1)] = (float(a.group(1)), float(a.group(2)),
                                      nam.group(1) if nam else '')
        if pins:
            libpins[lib_id] = pins

    # ---- instances -----------------------------------------------------
    insts = []
    body = T[:T.find('(lib_symbols')] + T[T.find('\n\t(symbol\n'):] if False else T
    for blk in sexp_blocks(T, 'symbol'):
        lid = re.match(r'\(symbol\s*\n?\s*\(lib_id "([^"]+)"\)', blk)
        if not lid:
            continue
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
        if not at:
            continue
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk)
        val = re.search(r'\(property "Value" "([^"]*)"', blk)
        mir = re.search(r'\(mirror (\w+)\)', blk)
        insts.append(dict(lib_id=lid.group(1),
                          x=float(at.group(1)), y=float(at.group(2)),
                          ang=float(at.group(3) or 0),
                          mirror=mir.group(1) if mir else None,
                          ref=ref.group(1) if ref else '?',
                          val=val.group(1) if val else ''))

    wires = []
    for blk in sexp_blocks(T, 'wire'):
        p = re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', blk)
        if len(p) >= 2:
            wires.append((float(p[0][0]), float(p[0][1]), float(p[1][0]), float(p[1][1])))
    labels = []
    for head in ('label', 'global_label', 'hierarchical_label'):
        for blk in sexp_blocks(T, head):
            m = re.match(r'\(' + head + r'\s+"([^"]*)"', blk)
            a = re.search(r'\(at ([-\d.]+) ([-\d.]+)', blk)
            if m and a:
                labels.append((float(a.group(1)), float(a.group(2)), m.group(1)))
    return libpins, insts, wires, labels


def transforms():
    """Candidate (name, fn) where fn(px,py,ang,mirror) -> schematic offset."""
    def mk(rot_sign, ymul):
        def f(px, py, ang, mirror):
            if mirror == 'x':
                py = -py
            elif mirror == 'y':
                px = -px
            a = math.radians(rot_sign * ang)
            c, s = math.cos(a), math.sin(a)
            rx, ry = px * c - py * s, px * s + py * c
            return rx, ymul * ry
        return f
    return [(f"rot{rs:+d} y{ym:+d}", mk(rs, ym)) for rs in (1, -1) for ym in (1, -1)]


def pin_on_wire(px, py, w):
    x1, y1, x2, y2 = w
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)) <= TOL


def build(path, verbose=True):
    libpins, insts, wires, labels = parse(path)
    # choose the transform that puts the most pins on wires
    best = None
    for name, f in transforms():
        hits = 0; total = 0
        for s in insts:
            for num, (px, py, _) in libpins.get(s['lib_id'], {}).items():
                ox, oy = f(px, py, s['ang'], s['mirror'])
                ax, ay = s['x'] + ox, s['y'] - oy
                total += 1
                if any(pin_on_wire(ax, ay, w) for w in wires):
                    hits += 1
        if best is None or hits > best[1]:
            best = (name, hits, total, f)
    name, hits, total, f = best
    if verbose:
        print(f"transform: {name}  ({hits}/{total} pins land on a wire)")

    # absolute pin positions
    pins = []
    for s in insts:
        for num, (px, py, pname) in sorted(libpins.get(s['lib_id'], {}).items()):
            ox, oy = f(px, py, s['ang'], s['mirror'])
            pins.append(dict(ref=s['ref'], num=num, name=pname, val=s['val'],
                             lib=s['lib_id'], x=s['x'] + ox, y=s['y'] - oy))

    # union-find over wires, pins, labels
    nodes = []
    for w in wires:
        nodes.append(('wire', w))
    for p in pins:
        nodes.append(('pin', p))
    for l in labels:
        nodes.append(('label', l))
    par = list(range(len(nodes)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a

    def uni(a, b):
        a, b = find(a), find(b)
        if a != b:
            par[a] = b

    def pts(n):
        k, v = n
        if k == 'wire':
            return [(v[0], v[1]), (v[2], v[3])]
        if k == 'pin':
            return [(v['x'], v['y'])]
        return [(v[0], v[1])]

    for i, ni in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            nj = nodes[j]
            joined = False
            if ni[0] == 'wire' and nj[0] == 'wire':
                joined = any(math.hypot(a[0] - b[0], a[1] - b[1]) <= TOL
                             for a in pts(ni) for b in pts(nj))
            elif ni[0] == 'wire':
                joined = any(pin_on_wire(b[0], b[1], ni[1]) for b in pts(nj))
            elif nj[0] == 'wire':
                joined = any(pin_on_wire(a[0], a[1], nj[1]) for a in pts(ni))
            else:
                joined = any(math.hypot(a[0] - b[0], a[1] - b[1]) <= TOL
                             for a in pts(ni) for b in pts(nj))
            if joined:
                uni(i, j)

    # name the nets: a power symbol's value wins, then a label, else auto
    groups = collections.defaultdict(list)
    for i, n in enumerate(nodes):
        groups[find(i)].append(n)
    nets = {}
    auto = 0
    for root, mem in groups.items():
        nm = None
        for k, v in mem:
            if k == 'pin' and v['lib'].startswith('power:'):
                nm = v['val']; break
        if not nm:
            for k, v in mem:
                if k == 'label':
                    nm = v[2]; break
        if not nm:
            auto += 1; nm = f"N${auto:03d}"
        members = [(v['ref'], v['num'], v['name']) for k, v in mem
                   if k == 'pin' and not v['lib'].startswith('power:')]
        if members:
            nets.setdefault(nm, []).extend(members)
    return nets, insts, pins


if __name__ == '__main__':
    path = sys.argv[1]
    nets, insts, pins = build(path)
    print(f"symbols {len(insts)}  pins {len(pins)}  nets {len(nets)}\n")
    for nm in sorted(nets):
        mem = sorted(set(nets[nm]))
        print(f"{nm:16} " + "  ".join(f"{r}.{n}" + (f"({pn})" if pn and pn != '~' else '')
                                      for r, n, pn in mem))
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        json.dump({k: sorted(set(map(list, v))) if False else sorted({f"{r}.{n}" for r, n, _ in v})
                   for k, v in nets.items()}, open(out, 'w'), indent=1, sort_keys=True)
        print(f"\nwrote {out}")
