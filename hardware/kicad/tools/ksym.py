#!/usr/bin/env python3
"""Parse KiCad .kicad_sym libraries: extract each symbol's body and pin geometry.

A pin's (at x y angle) is its CONNECTION point in symbol space, where Y is
up-positive.  Schematic space is Y down-positive, so placing an instance at
(ix, iy) with rotation 0 puts the pin at (ix + px, iy - py).
"""
import re, sys, json

def sexp(text):
    """Minimal S-expression reader -> nested lists of tokens."""
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack, cur = [], []
    for t in toks:
        if t == '(':
            new = []
            cur.append(new)
            stack.append(cur)
            cur = new
        elif t == ')':
            cur = stack.pop()
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    return cur

def walk(node, tag):
    """Yield every sub-list whose head is `tag`."""
    if isinstance(node, list):
        if node and node[0] == tag:
            yield node
        for c in node:
            yield from walk(c, tag)

def load(path):
    root = sexp(open(path).read())
    lib = root[0]
    out = {}
    for sym in lib[1:]:
        if not (isinstance(sym, list) and sym and sym[0] == 'symbol'):
            continue
        name = sym[1]
        if re.search(r'_\d+_\d+$', name):      # unit sub-symbol, handled below
            continue
        pins = {}
        for p in walk(sym, 'pin'):
            at = next((x for x in p if isinstance(x, list) and x and x[0] == 'at'), None)
            num = next((x for x in p if isinstance(x, list) and x and x[0] == 'number'), None)
            nam = next((x for x in p if isinstance(x, list) and x and x[0] == 'name'), None)
            ln = next((x for x in p if isinstance(x, list) and x and x[0] == 'length'), None)
            if at and num:
                pins[num[1]] = {
                    'x': float(at[1]), 'y': float(at[2]),
                    'angle': float(at[3]) if len(at) > 3 else 0.0,
                    'len': float(ln[1]) if ln else 2.54,
                    'name': nam[1] if nam else '',
                }
        if pins:
            out[name] = pins
    return out

if __name__ == '__main__':
    libs = {}
    for path in sys.argv[1:]:
        libs.update(load(path))
    for k, v in libs.items():
        xs = [p['x'] for p in v.values()]
        ys = [p['y'] for p in v.values()]
        print(f'{k:32} {len(v):3} pins  x[{min(xs):7.2f},{max(xs):7.2f}] y[{min(ys):7.2f},{max(ys):7.2f}]')
    json.dump(libs, open('/private/tmp/claude-501/-Users-dylanhackett-V1/4d61871d-02f0-409c-8779-744109130e35/scratchpad/kpins.json', 'w'))
