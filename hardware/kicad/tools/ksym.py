#!/usr/bin/env python3
"""Parse KiCad .kicad_sym libraries: extract each symbol's body and pin geometry.

RUN IT LIKE THIS, and not with a glob over lib/:

    python3 tools/ksym.py \
        /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/*.kicad_sym \
        hardware/kicad/lib/daisy_es.kicad_sym \
        hardware/kicad/lib/vuulgaris.kicad_sym

Later paths win, so the project libraries must come LAST and the argument list
must match `sym-lib-table` -- which names only `vuulgaris` and `daisy_es`. The
KiCad stock libraries are there for the generic `R` and `C` symbols.

There used to be a third file, `lib/daisy_patch_sm.kicad_sym`, not in the lib
table, holding a SECOND and DIFFERENT `ES_DAISY_PATCH_SM_REV1` -- A6 at x -5.08
instead of -1.27, A10 at -7.62 instead of -6.35. Passing it to this script moved
the pin stubs mksch.py draws, two power pins quietly stopped connecting, and
netcheck reported `unconnected-(U1-+5V-PadA6)` for a schematic that looked fine.
**Deleted 2026-09-07** (it was committed in 398a1f2 and referenced by nothing).
If it ever comes back out of git history, it does not belong in this argument
list -- and the real reason to keep the list explicit is that any duplicate
symbol name does this, not just that one.

Running this with NO arguments writes an EMPTY kpins.json and mksch.py then dies
on a KeyError. kpins.json is generated, not tracked; rebuild it here.

A pin's (at x y angle) is its CONNECTION point in symbol space, where Y is
up-positive.  Schematic space is Y down-positive, so placing an instance at
(ix, iy) with rotation 0 puts the pin at (ix + px, iy - py).
"""
import re, sys, json, os

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
    # The docstring above has warned about this since the file was written,
    # and the warning is not a guard: run it bare and it writes an empty
    # kpins.json, after which mksch.py dies on KeyError: 'C' several steps
    # away from the cause. Refuse instead.
    if not sys.argv[1:]:
        sys.exit(__doc__.strip().split('\n\n')[1])
    libs = {}
    for path in sys.argv[1:]:
        libs.update(load(path))
    for k, v in libs.items():
        xs = [p['x'] for p in v.values()]
        ys = [p['y'] for p in v.values()]
        print(f'{k:32} {len(v):3} pins  x[{min(xs):7.2f},{max(xs):7.2f}] y[{min(ys):7.2f},{max(ys):7.2f}]')
    json.dump(libs, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kpins.json'), 'w'))
