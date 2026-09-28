#!/usr/bin/env python3
"""Generate a project's .kicad_sch from its design module and netmap.json.

    python3 tools/mksch.py                          # main board -> hardware/kicad/vuulgaris.kicad_sch
    python3 tools/mksch.py --project faceplate      # -> hardware/faceplate/vuulgaris-faceplate.kicad_sch
    python3 tools/mksch.py --out /some/where.kicad_sch   # write elsewhere, touch nothing

This file is the ENGINE and holds no design. Which symbol each ref uses, where
it sits and which footprint it gets live in the project's design.py (see
tools/proj.py); the main board's is tools/design.py, moved out of here
2026-09-27 so the faceplate could share the engine instead of forking it.

Every pin that carries a net gets a short wire stub plus a GLOBAL LABEL at the
far end.  Global labels are first-class net declarations in KiCad, so net
identity does not depend on stubs happening to touch each other -- which is the
failure mode that broke the EasyEDA version repeatedly.

Coordinate note: symbol-library space is Y-up, schematic space is Y-down.  An
instance placed at (ix,iy) puts a pin whose symbol-space position is (px,py) at
(ix+px, iy-py).  A pin's `angle` points INTO the body, so the stub runs at
angle+180.
"""
import json, re, math, uuid, sys, os, importlib.util
import proj

P = proj.P
OUT = P.sch
if "--out" in sys.argv:
    OUT = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])

_spec = importlib.util.spec_from_file_location("design", P.design)
design = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(design)
LIBS, SYM, POS, FPMAP, NET = design.LIBS, design.SYM, design.POS, design.FPMAP, design.NET
VALUE = json.load(open(P.values)) if os.path.exists(P.values) else {}

STUB = 10.16                     # 8 grid units - keeps labels clear of bodies
SHEET = str(uuid.uuid4())

# ---------------------------------------------------------------- symbol text
def symbol_blocks(path):
    """Return {name: raw s-expression text} for each top-level symbol."""
    s = open(path).read()
    out = {}
    for m in re.finditer(r'\(symbol "([^"]+)"', s):
        name = m.group(1)
        if re.search(r'_\d+_\d+$', name):
            continue
        i = m.start()
        depth, j = 0, i
        while j < len(s):
            if s[j] == '(':
                depth += 1
            elif s[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out[name] = s[i:j + 1]
    return out

blocks, footprints = {}, {}
for p in LIBS:
    blocks.update(symbol_blocks(p))
for name, txt in blocks.items():
    m = re.search(r'\(property "Footprint" "([^"]*)"', txt)
    footprints[name] = m.group(1) if m else ""

if not os.path.exists(P.kpins):
    sys.exit(f"no {P.kpins} -- build it with tools/ksym.py --project {P.key}, "
             f"using the argument list in its docstring")
pins = json.load(open(P.kpins))

# ---------------------------------------------------------------- emit
def U():
    return str(uuid.uuid4())

def pin_xy(ref, pin):
    sym = SYM[ref]
    p = pins[sym][pin]
    ix, iy = POS[ref]
    return ix + p['x'], iy - p['y'], p['angle']

out = []
A = out.append
A('(kicad_sch (version 20221206) (generator eeschema)')
A(f'  (uuid {U()})')
A('  (paper "A1")')
A('  (lib_symbols')
for name in sorted({SYM[r] for r in SYM}):
    txt = blocks[name].replace(f'(symbol "{name}"', f'(symbol "vuulgaris:{name}"', 1)
    A(txt)
A('  )')

wires, labels, ncs = [], [], []
for ref in sorted(SYM):
    name = SYM[ref]
    x, y = POS[ref]
    A(f'  (symbol (lib_id "vuulgaris:{name}") (at {x} {y} 0) (unit 1)')
    A('    (in_bom yes) (on_board yes) (dnp no)')
    A(f'    (uuid {U()})')
    A(f'    (property "Reference" "{ref}" (at {x} {y - 12} 0) (effects (font (size 1.27 1.27))))')
    A(f'    (property "Value" "{VALUE.get(ref, name)}" (at {x} {y - 9} 0) (effects (font (size 1.27 1.27))))')
    A(f'    (property "Footprint" "vuulgaris:{FPMAP[ref]}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    A(f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))')
    for pn in pins[name]:
        A(f'    (pin "{pn}" (uuid {U()}))')
    A('  )')

    # every pin gets explicit treatment: a net label, or a no-connect marker
    for pn in pins[name]:
        if pn not in NET.get(ref, {}):
            px, py, _ = pin_xy(ref, pn)
            ncs.append((round(px, 2), round(py, 2)))

    for pn, net in NET.get(ref, {}).items():
        if pn not in pins[name]:
            print(f"MISSING PIN {ref}.{pn}", file=sys.stderr)
            continue
        px, py, ang = pin_xy(ref, pn)
        a = math.radians(ang + 180.0)
        ex = round(px + STUB * math.cos(a), 2)
        ey = round(py - STUB * math.sin(a), 2)
        wires.append((round(px, 2), round(py, 2), ex, ey))
        labels.append((ex, ey, net, (ang + 180) % 360))

for x1, y1, x2, y2 in wires:
    A(f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type solid)) (uuid {U()}))')
for x, y, net, ang in labels:
    A(f'  (label "{net}" (at {x} {y} {int(ang)}) (fields_autoplaced)')
    A('    (effects (font (size 1.27 1.27)) (justify left bottom))')
    A(f'    (uuid {U()})')
    A('  )')

for x, y in ncs:
    A(f'  (no_connect (at {x} {y}) (uuid {U()}))')

A('  (sheet_instances (path "/" (page "1")))')
A(')')

open(OUT, "w").write("\n".join(out) + "\n")
print("wrote     :", os.path.relpath(OUT, proj.HW) if OUT.startswith(proj.HW) else OUT)
print("components:", len(SYM))
print("wires     :", len(wires))
print("labels    :", len(labels))
print("nets      :", len({l[2] for l in labels}))
print("no-connect:", len(ncs))
