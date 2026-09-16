#!/usr/bin/env python3
"""Draw a real schematic -- symbols and orthogonal wires -- from netmap.json.

    python3 tools/schdraw.py            # -> docs/sch-lpg-left.svg

Why this exists: the KiCad schematic is a stub and a net label on every pin, and
a graph of nets is not a schematic either. Both are unreadable, which is how the
LED drive and the input stage shipped inverted. This draws the block the way
Bergman draws it -- same arrangement, same left-to-right signal flow -- so the
two can sit side by side and be compared by eye.

The drawing cannot lie about the circuit. Placement and wire paths are authored
here, but every wire carries a net name, and `check()` refuses to emit the file
unless every pin of every net in this block is touched by a wire of that net,
and no wire touches a pin that is not on its net. Get a wire wrong and the
build fails rather than producing a pretty picture of the wrong thing.
"""
import json, os, re, sys, collections

KI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(KI))

GRID = 10
W, H = 1720, 1180

# ---------------------------------------------------------------- symbols ---
# Every symbol returns (svg, {terminal: (x, y)}). Terminals are on-grid so the
# wires meet them exactly, which is what makes the check below meaningful.

def _t(x, y):
    return (round(x), round(y))


def resistor(x, y, ref, val, vert=False, flip_label=False, swap=False):
    """IEC box, 60 long, terminals 1 and 2 at the ends."""
    L, w = 60, 20
    if vert:
        body = f'<rect x="{x-w/2}" y="{y-L/2}" width="{w}" height="{L}" class="body"/>'
        wires = (f'<line x1="{x}" y1="{y-L/2-20}" x2="{x}" y2="{y-L/2}" class="pin"/>'
                 f'<line x1="{x}" y1="{y+L/2}" x2="{x}" y2="{y+L/2+20}" class="pin"/>')
        tx = x + (-16 if flip_label else 16)
        anchor = "end" if flip_label else "start"
        lab = (f'<text x="{tx}" y="{y-4}" class="ref" text-anchor="{anchor}">{ref}</text>'
               f'<text x="{tx}" y="{y+12}" class="val" text-anchor="{anchor}">{val}</text>')
        a, b = _t(x, y-L/2-20), _t(x, y+L/2+20)
        return body + wires + lab, ({"2": a, "1": b} if swap else {"1": a, "2": b})
    body = f'<rect x="{x-L/2}" y="{y-w/2}" width="{L}" height="{w}" class="body"/>'
    wires = (f'<line x1="{x-L/2-20}" y1="{y}" x2="{x-L/2}" y2="{y}" class="pin"/>'
             f'<line x1="{x+L/2}" y1="{y}" x2="{x+L/2+20}" y2="{y}" class="pin"/>')
    ty = y + (34 if flip_label else -30)
    lab = (f'<text x="{x}" y="{ty}" class="ref" text-anchor="middle">{ref}</text>'
           f'<text x="{x}" y="{ty+14}" class="val" text-anchor="middle">{val}</text>')
    a, b = _t(x-L/2-20, y), _t(x+L/2+20, y)
    return body + wires + lab, ({"2": a, "1": b} if swap else {"1": a, "2": b})


def cap(x, y, ref, val, vert=False, flip_label=False, swap=False):
    g, half = 8, 18
    if vert:
        plates = (f'<line x1="{x-half}" y1="{y-g/2}" x2="{x+half}" y2="{y-g/2}" class="body"/>'
                  f'<line x1="{x-half}" y1="{y+g/2}" x2="{x+half}" y2="{y+g/2}" class="body"/>')
        wires = (f'<line x1="{x}" y1="{y-g/2-32}" x2="{x}" y2="{y-g/2}" class="pin"/>'
                 f'<line x1="{x}" y1="{y+g/2}" x2="{x}" y2="{y+g/2+32}" class="pin"/>')
        tx = x + (-24 if flip_label else 24)
        anchor = "end" if flip_label else "start"
        lab = (f'<text x="{tx}" y="{y-4}" class="ref" text-anchor="{anchor}">{ref}</text>'
               f'<text x="{tx}" y="{y+12}" class="val" text-anchor="{anchor}">{val}</text>')
        a, b = _t(x, y-g/2-32), _t(x, y+g/2+32)
        return plates + wires + lab, ({"2": a, "1": b} if swap else {"1": a, "2": b})
    plates = (f'<line x1="{x-g/2}" y1="{y-half}" x2="{x-g/2}" y2="{y+half}" class="body"/>'
              f'<line x1="{x+g/2}" y1="{y-half}" x2="{x+g/2}" y2="{y+half}" class="body"/>')
    wires = (f'<line x1="{x-g/2-32}" y1="{y}" x2="{x-g/2}" y2="{y}" class="pin"/>'
             f'<line x1="{x+g/2}" y1="{y}" x2="{x+g/2+32}" y2="{y}" class="pin"/>')
    ty = y + (40 if flip_label else -32)
    lab = (f'<text x="{x}" y="{ty}" class="ref" text-anchor="middle">{ref}</text>'
           f'<text x="{x}" y="{ty+14}" class="val" text-anchor="middle">{val}</text>')
    a, b = _t(x-g/2-32, y), _t(x+g/2+32, y)
    return plates + wires + lab, ({"2": a, "1": b} if swap else {"1": a, "2": b})


def zener(x, y, ref, val, anode_up=True):
    """Vertical zener. Terminal 1 is the cathode (bar), 2 the anode (triangle)."""
    s = 14
    if anode_up:                      # anode on top, cathode (bar) at the bottom
        tri = f'<polygon points="{x-s},{y-s} {x+s},{y-s} {x},{y+2}" class="fillbody"/>'
        bar = (f'<path d="M {x-s-4} {y+2} L {x+s+4} {y+2} M {x-s-4} {y+2} l -6 7 '
               f'M {x+s+4} {y+2} l 6 -7" class="body"/>')
        term = {"2": _t(x, y-s-30), "1": _t(x, y+32)}
        wires = (f'<line x1="{x}" y1="{y-s-30}" x2="{x}" y2="{y-s}" class="pin"/>'
                 f'<line x1="{x}" y1="{y+2}" x2="{x}" y2="{y+32}" class="pin"/>')
    else:
        tri = f'<polygon points="{x-s},{y+s} {x+s},{y+s} {x},{y-2}" class="fillbody"/>'
        bar = (f'<path d="M {x-s-4} {y-2} L {x+s+4} {y-2} M {x-s-4} {y-2} l -6 -7 '
               f'M {x+s+4} {y-2} l 6 7" class="body"/>')
        term = {"1": _t(x, y-32), "2": _t(x, y+s+30)}
        wires = (f'<line x1="{x}" y1="{y-32}" x2="{x}" y2="{y-2}" class="pin"/>'
                 f'<line x1="{x}" y1="{y+s}" x2="{x}" y2="{y+s+30}" class="pin"/>')
    lab = (f'<text x="{x+26}" y="{y-6}" class="ref">{ref}</text>'
           f'<text x="{x+26}" y="{y+10}" class="val">{val}</text>')
    return tri + bar + wires + lab, term


def opamp(x, y, ref, part, plus_on_top=False, pins=("1", "2", "3")):
    """Triangle, apex right. x,y is the left edge, vertical centre.
    pins = (out, in-, in+). Terminals: 'out', '-', '+'."""
    w, h = 120, 108
    tri = f'<polygon points="{x},{y-h/2} {x},{y+h/2} {x+w},{y}" class="fillwhite"/>'
    y_top, y_bot = y - h/4, y + h/4
    y_minus, y_plus = (y_bot, y_top) if plus_on_top else (y_top, y_bot)
    sym = (f'<text x="{x+16}" y="{y_minus+6}" class="sign">−</text>'
           f'<text x="{x+16}" y="{y_plus+7}" class="sign">+</text>')
    wires = (f'<line x1="{x-24}" y1="{y_minus}" x2="{x}" y2="{y_minus}" class="pin"/>'
             f'<line x1="{x-24}" y1="{y_plus}" x2="{x}" y2="{y_plus}" class="pin"/>'
             f'<line x1="{x+w}" y1="{y}" x2="{x+w+24}" y2="{y}" class="pin"/>')
    nums = (f'<text x="{x-6}" y="{y_minus-7}" class="pin-no" text-anchor="end">{pins[1]}</text>'
            f'<text x="{x-6}" y="{y_plus-7}" class="pin-no" text-anchor="end">{pins[2]}</text>'
            f'<text x="{x+w+6}" y="{y-7}" class="pin-no">{pins[0]}</text>')
    lab = (f'<text x="{x+30}" y="{y-6}" class="ref">{ref}</text>'
           f'<text x="{x+30}" y="{y+12}" class="val">{part}</text>')
    return tri + sym + wires + nums + lab, {
        "out": _t(x+w+24, y), "-": _t(x-24, y_minus), "+": _t(x-24, y_plus)}


def vactrol(x, y, ref, part="VTL5C3"):
    """Bergman's box: LED across the top, LDR across the bottom.
    Terminals 1 (LED anode, left) 2 (LED cathode, right) 3/4 (LDR, left/right)."""
    bw, bh = 150, 130
    box = f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" class="dashbox"/>'
    ly = y + 42
    cx = x + bw/2
    led = (f'<polygon points="{cx-16},{ly-14} {cx-16},{ly+14} {cx+8},{ly}" class="fillbody"/>'
           f'<line x1="{cx+8}" y1="{ly-16}" x2="{cx+8}" y2="{ly+16}" class="body"/>'
           f'<path d="M {cx-4} {ly+20} l 14 14 M {cx+8} {ly+20} l 14 14" class="ray"/>'
           f'<path d="M {cx+6} {ly+30} l 6 6 l -8 1 z" class="fillbody"/>'
           f'<path d="M {cx+18} {ly+30} l 6 6 l -8 1 z" class="fillbody"/>')
    led_w = (f'<line x1="{x-24}" y1="{ly}" x2="{cx-16}" y2="{ly}" class="pin"/>'
             f'<line x1="{cx+8}" y1="{ly}" x2="{x+bw+24}" y2="{ly}" class="pin"/>')
    ry = y + bh - 32
    ldr = (f'<rect x="{cx-30}" y="{ry-11}" width="60" height="22" class="body"/>'
           f'<line x1="{x-24}" y1="{ry}" x2="{cx-30}" y2="{ry}" class="pin"/>'
           f'<line x1="{cx+30}" y1="{ry}" x2="{x+bw+24}" y2="{ry}" class="pin"/>')
    lab = (f'<text x="{x+bw/2}" y="{y-10}" class="ref" text-anchor="middle">{ref}</text>'
           f'<text x="{x+bw/2}" y="{y+22}" class="val" text-anchor="middle">{part}</text>')
    return box + led + led_w + ldr + lab, {
        "1": _t(x-24, ly), "2": _t(x+bw+24, ly), "3": _t(x-24, ry), "4": _t(x+bw+24, ry)}


def pot(x, y, ref, val, vert=True, wiper_right=True, ganged=True):
    """Panel pot. Terminals 1 (cw end) 2 (wiper) 3 (ccw end)."""
    L, w = 76, 22
    body = f'<rect x="{x-w/2}" y="{y-L/2}" width="{w}" height="{L}" class="body"/>'
    wires = (f'<line x1="{x}" y1="{y-L/2-22}" x2="{x}" y2="{y-L/2}" class="pin"/>'
             f'<line x1="{x}" y1="{y+L/2}" x2="{x}" y2="{y+L/2+22}" class="pin"/>')
    d = 1 if wiper_right else -1
    arrow = (f'<line x1="{x+d*(w/2+34)}" y1="{y}" x2="{x+d*(w/2+4)}" y2="{y}" class="pin"/>'
             f'<polygon points="{x+d*(w/2+4)},{y} {x+d*(w/2+16)},{y-7} {x+d*(w/2+16)},{y+7}" class="fillbody"/>')
    tx = x - d*(w/2+12)
    anchor = "end" if wiper_right else "start"
    lab = (f'<text x="{tx}" y="{y-6}" class="ref" text-anchor="{anchor}">{ref}</text>'
           f'<text x="{tx}" y="{y+10}" class="val" text-anchor="{anchor}">{val}</text>'
           + (f'<text x="{tx}" y="{y+26}" class="note" text-anchor="{anchor}">dual gang</text>' if ganged else ""))
    return body + wires + arrow + lab, {
        "1": _t(x, y-L/2-22), "2": _t(x+d*(w/2+34), y), "3": _t(x, y+L/2+22)}


def trimmer(x, y, ref, val):
    """Trimmer wired as a rheostat: 2 and 3 tied, drawn as one terminal."""
    L, w = 60, 20
    body = f'<rect x="{x-L/2}" y="{y-w/2}" width="{L}" height="{w}" class="body"/>'
    wires = (f'<line x1="{x-L/2-20}" y1="{y}" x2="{x-L/2}" y2="{y}" class="pin"/>'
             f'<line x1="{x+L/2}" y1="{y}" x2="{x+L/2+20}" y2="{y}" class="pin"/>')
    arrow = (f'<line x1="{x}" y1="{y+26}" x2="{x}" y2="{y+w/2}" class="pin"/>'
             f'<polygon points="{x},{y+w/2} {x-6},{y+16} {x+6},{y+16}" class="fillbody"/>'
             f'<path d="M {x} {y+26} L {x+L/2+20} {y+26} L {x+L/2+20} {y}" class="wire"/>')
    lab = (f'<text x="{x}" y="{y-30}" class="ref" text-anchor="middle">{ref}</text>'
           f'<text x="{x}" y="{y-14}" class="val" text-anchor="middle">{val}</text>')
    return body + wires + arrow + lab, {"1": _t(x-L/2-20, y), "2": _t(x+L/2+20, y),
                                        "3": _t(x+L/2+20, y)}


def spdt(x, y, ref, note=""):
    """One pole of the mode switch. Terminals: com, nc (up), no (down)."""
    com = _t(x-30, y)
    nc, no = _t(x+40, y-40), _t(x+40, y+40)
    g = (f'<line x1="{x-30}" y1="{y}" x2="{x-6}" y2="{y}" class="pin"/>'
         f'<circle cx="{x-4}" cy="{y}" r="4" class="body"/>'
         f'<circle cx="{x+30}" cy="{y-40}" r="4" class="body"/>'
         f'<circle cx="{x+30}" cy="{y+40}" r="4" class="body"/>'
         f'<line x1="{x-2}" y1="{y-2}" x2="{x+28}" y2="{y-36}" class="body"/>'
         f'<line x1="{x+30}" y1="{y-40}" x2="{x+40}" y2="{y-40}" class="pin"/>'
         f'<line x1="{x+30}" y1="{y+40}" x2="{x+40}" y2="{y+40}" class="pin"/>'
         f'<text x="{x-8}" y="{y+26}" class="ref" text-anchor="end">{ref}</text>')
    if note:
        g += f'<text x="{x-8}" y="{y+42}" class="note" text-anchor="end">{note}</text>'
    return g, {"com": com, "nc": nc, "no": no}


def gnd(x, y):
    return (f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y+16}" class="wire"/>'
            f'<line x1="{x-16}" y1="{y+16}" x2="{x+16}" y2="{y+16}" class="body"/>'
            f'<line x1="{x-10}" y1="{y+22}" x2="{x+10}" y2="{y+22}" class="body"/>'
            f'<line x1="{x-4}" y1="{y+28}" x2="{x+4}" y2="{y+28}" class="body"/>'), _t(x, y)


def rail(x, y, name, up=True):
    d = -1 if up else 1
    return (f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y+d*18}" class="wire"/>'
            f'<polygon points="{x},{y+d*30} {x-9},{y+d*16} {x+9},{y+d*16}" class="fillbody"/>'
            f'<text x="{x}" y="{y+d*40+(0 if up else 12)}" class="rail-label" '
            f'text-anchor="middle">{name}</text>'), _t(x, y)


def port(x, y, name, left=True):
    """Off-block signal, drawn as a flag."""
    w = 12 + 8.2*len(name)
    if left:
        pts = f'{x},{y} {x+14},{y-15} {x+w},{y-15} {x+w},{y+15} {x+14},{y+15}'
        tx, anchor = x + 22, "start"
    else:
        pts = f'{x},{y} {x-14},{y-15} {x-w},{y-15} {x-w},{y+15} {x-14},{y+15}'
        tx, anchor = x - 22, "end"
    return (f'<polygon points="{pts}" class="port"/>'
            f'<text x="{tx}" y="{y+5}" class="port-label" text-anchor="{anchor}">{name}</text>'), _t(x, y)


def power_pins(x, y, ref, part, pins=("4", "11")):
    """The op-amp's supply pins, drawn once for the whole chip."""
    w, h = 150, 96
    box = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="fillwhite"/>'
    lab = (f'<text x="{x+w/2}" y="{y+38}" class="ref" text-anchor="middle">{ref}</text>'
           f'<text x="{x+w/2}" y="{y+56}" class="val" text-anchor="middle">{part} supply</text>')
    wires = (f'<line x1="{x+w/2-40}" y1="{y}" x2="{x+w/2-40}" y2="{y-24}" class="pin"/>'
             f'<line x1="{x+w/2+40}" y1="{y+h}" x2="{x+w/2+40}" y2="{y+h+24}" class="pin"/>')
    nums = (f'<text x="{x+w/2-34}" y="{y-8}" class="pin-no">{pins[0]}</text>'
            f'<text x="{x+w/2+46}" y="{y+h+18}" class="pin-no">{pins[1]}</text>')
    return box + lab + wires + nums, {pins[0]: _t(x+w/2-40, y-24), pins[1]: _t(x+w/2+40, y+h+24)}


# ------------------------------------------------------------------ sheet ---

def lpg_left(netmap, values):
    """LPG left channel, audio path and LED drive, arranged like Bergman's."""
    V = lambda r: values.get(r, "")
    P, T, glyphs = {}, {}, []          # placement svg, terminals, loose glyphs

    def put(ref, res):
        svg, terms = res
        P[ref] = svg
        T[ref] = terms

    def opamp_unit(ref, unit, x, y, pins, plus_top=True):
        svg, t = opamp(x, y, f"{ref}-{unit}", V(ref) or "TL084", plus_top, pins)
        P[f"{ref}{unit}"] = svg
        T[ref] = {**T.get(ref, {}), pins[0]: t["out"], pins[1]: t["-"], pins[2]: t["+"]}

    # --- LED drive -----------------------------------------------------
    put("RV1", pot(170, 220, "RV1", "CUTOFF", wiper_right=True))
    put("R303", resistor(330, 220, "R303", V("R303")))
    opamp_unit("U301", "B", 540, 220, ("7", "6", "5"))
    put("R308", resistor(490, 400, "R308", V("R308"), vert=True))
    put("R305", resistor(330, 520, "R305", V("R305")))
    put("C305", cap(291, 620, "C305", V("C305"), flip_label=True))
    put("R304", resistor(430, 620, "R304", V("R304"), flip_label=True))
    put("RT301", trimmer(280, 330, "RT301", V("RT301")))
    put("R307", resistor(390, 330, "R307", V("R307")))
    put("R317", resistor(620, 430, "R317", V("R317"), vert=True, flip_label=True))
    put("D301", zener(790, 504, "D301", V("D301"), anode_up=True))
    put("R306", resistor(840, 220, "R306", V("R306")))
    put("VT301", vactrol(820, 560, "VT301"))
    put("VT302", vactrol(1120, 560, "VT302"))

    # --- audio in ------------------------------------------------------
    put("R310", resistor(280, 930, "R310", V("R310"), vert=True))
    put("C306", cap(400, 860, "C306", V("C306")))
    put("R309", resistor(500, 930, "R309", V("R309"), vert=True))
    opamp_unit("U301", "A", 620, 860, ("1", "2", "3"))
    put("R311", resistor(680, 1000, "R311", V("R311"), swap=True, flip_label=True))

    # --- filter network and output ------------------------------------
    put("C307", cap(1020, 770, "C307", V("C307"), vert=True))
    put("C308", cap(1060, 940, "C308", V("C308"), vert=True))
    sw, swt = spdt(1160, 1030, "SW1", "VCF position")
    P["SW1"] = sw
    T["SW1"] = {"2": swt["com"], "1": swt["nc"], "3": swt["no"]}   # commons are 2 and 5
    put("C309", cap(1340, 760, "C309", V("C309"), vert=True, flip_label=True))
    put("R313", resistor(1400, 830, "R313", V("R313"), vert=True))
    opamp_unit("U301", "C", 1480, 740, ("8", "9", "10"))
    put("R314", resistor(1560, 900, "R314", V("R314"), flip_label=True))
    put("R315", resistor(1770, 740, "R315", V("R315")))
    opamp_unit("U301", "D", 1480, 1030, ("14", "13", "12"))
    put("C310", cap(1381, 1080, "C310", V("C310")))
    put("RV2", pot(1300, 1180, "RV2", "RESONANCE", wiper_right=True))
    put("R318", resistor(1300, 1310, "R318", V("R318"), vert=True))
    put("U301pwr", power_pins(180, 1180, "U301", "TL084"))
    T["U301"].update(T.pop("U301pwr"))
    P["U301pwr"] = P["U301pwr"]
    return P, T, glyphs


# ------------------------------------------------------------------ wires ---
# Each entry: (net, [waypoints]).  A waypoint is ("REF", "pin") or (x, y).
# Ground and rail glyphs are placed by ("GND", x, y) / ("RAIL", x, y, name, up).

def lpg_left_wires():
    return [
        # ---- LED drive, exactly Bergman's arrangement ----
        ("POS12V",      [("RAIL", 170, 160, "+12V", True), ("RV1", "1")]),
        ("GND",         [("RV1", "3"), ("GND", 170, 280)]),
        ("LPG_OFS_L",   [("RV1", "2"), ("R303", "1")]),
        ("LPG_SUM_L",   [("R303", "2"), (430, 220), (430, 247), ("U301", "6")]),
        ("LPG_SUM_L",   [(430, 220), (430, 400), (200, 400), (200, 620), ("C305", "1")]),
        ("LPG_SUM_L",   [(200, 520), ("R305", "1")]),
        ("LPG_SUM_L",   [(430, 270), (230, 270), (230, 330), ("RT301", "1")]),
        ("LPG_BP_L",    [("U301", "5"), (490, 193), ("R308", "1")]),
        ("GND",         [("R308", "2"), ("GND", 490, 450)]),
        ("LPG_C5_L",    [("C305", "2"), ("R304", "1")]),
        ("LPG_CV_L",    [("PORT", 200, 700, "LPG_CV_L  ← CV chain", False),
                         (600, 700), (600, 620), ("R304", "2")]),
        ("LPG_CV_L",    [(600, 620), (600, 520), ("R305", "2")]),
        ("LPG_T1_L",    [("RT301", "2"), ("R307", "1")]),
        ("LPG_LED_L",   [("R307", "2"), (700, 330), (700, 602), ("VT301", "1")]),
        ("LPG_LED_L",   [(700, 380), ("R317", "1")]),
        ("LPG_LED_L",   [(700, 460), ("D301", "2")]),
        ("GND",         [("R317", "2"), ("GND", 620, 480)]),
        ("GND",         [("D301", "1"), ("GND", 790, 536)]),
        ("LPG_BOUT_L",  [("U301", "7"), ("R306", "1")]),
        ("LPG_LEDK_L",  [("R306", "2"), (1420, 220), (1420, 602), ("VT302", "2")]),
        ("LPG_LEDM_L",  [("VT301", "2"), ("VT302", "1")]),

        # ---- audio in ----
        ("AUDIO_OUT_L", [("PORT", 200, 860, "AUDIO_OUT_L  ← source select", False),
                         (280, 860), ("C306", "1")]),
        ("AUDIO_OUT_L", [(280, 860), ("R310", "1")]),
        ("GND",         [("R310", "2"), ("GND", 280, 980)]),
        ("LPG_INF_L",   [("C306", "2"), (500, 860), (560, 860), (560, 833), ("U301", "3")]),
        ("LPG_INF_L",   [(500, 860), ("R309", "1")]),
        ("GND",         [("R309", "2"), ("GND", 500, 980)]),
        ("LPG_AFB_L",   [("U301", "2"), (560, 887), (560, 1000), ("R311", "2")]),
        ("LPG_ABUF_L",  [("U301", "1"), (796, 860), (796, 658), ("VT301", "3")]),
        ("LPG_ABUF_L",  [("R311", "1"), (790, 1000), (796, 1000), (796, 860)]),

        # ---- LDR chain, filter network ----
        ("LPG_MID_L",   [("VT301", "4"), ("VT302", "3")]),
        ("LPG_MID_L",   [(1020, 658), ("C307", "1")]),
        ("LPG_MID_L",   [(1060, 658), ("C308", "1")]),
        ("GND",         [("C307", "2"), ("GND", 1020, 810)]),
        ("LPG_VCFSW_L", [("C308", "2"), (1060, 1030), ("SW1", "2")]),
        ("LPG_LDR_L",   [("VT302", "4"), (1400, 658), (1400, 713), ("U301", "10")]),
        ("LPG_LDR_L",   [(1340, 658), ("C309", "1")]),
        ("LPG_LDR_L",   [(1400, 713), (1400, 780), ("R313", "1")]),
        ("GND",         [("C309", "2"), ("GND", 1340, 800)]),
        ("GND",         [("R313", "2"), ("GND", 1400, 880)]),
        ("LPG_CFB_L",   [("U301", "9"), (1456, 900), ("R314", "1")]),
        ("LPG_OUT_L",   [("U301", "8"), (1680, 740), (1720, 740), ("R315", "1")]),
        ("LPG_OUT_L",   [("R314", "2"), (1680, 900), (1680, 740)]),
        ("LPG_OUT_L",   [(1680, 960), (1456, 960), (1456, 1003), ("U301", "12")]),
        ("BBD_IN_L",    [("R315", "2"), ("PORT", 1880, 740, "BBD_IN_L  → delay", True)]),

        # ---- resonance ----
        ("LPG_RES_L",   [("U301", "14"), (1680, 1030), (1680, 1120), (1200, 1120),
                         (1200, 990), ("SW1", "1")]),
        ("LPG_RES_L",   [(1300, 1120), ("RV2", "1")]),
        ("LPG_RES_L",   [(1417, 1120), ("C310", "2")]),
        ("LPG_RESW_L",  [("RV2", "2"), (1345, 1080), (1345, 1057), ("U301", "13")]),
        ("LPG_RESW_L",  [(1345, 1080), ("C310", "1")]),
        ("LPG_RESL_L",  [("RV2", "3"), ("R318", "1")]),
        ("GND",         [("R318", "2"), ("GND", 1300, 1360)]),

        # ---- chip supply ----
        ("POS12V",      [("RAIL", 255, 1156, "+12V", True), ("U301", "4")]),
        ("NEG12V",      [("U301", "11"), ("RAIL", 335, 1300, "-12V", False)]),
    ]


# declared off-sheet: the right channel's gang, panel mounting lugs, the unused
# throw of the mode switch. Every other pin must be wired or the build fails.
OFF_SHEET = {("RV1", "4"), ("RV1", "5"), ("RV1", "6"), ("RV1", "7"), ("RV1", "8"),
             ("RV2", "4"), ("RV2", "5"), ("RV2", "6"), ("RV2", "7"), ("RV2", "8"),
             ("SW1", "4"), ("SW1", "5")}


# ------------------------------------------------------------------ build ---

def resolve(wires, T, glyphs):
    """waypoints -> polylines, placing ground/rail/port glyphs as it goes."""
    out = []
    for net, path in wires:
        pts = []
        for wp in path:
            if wp[0] == "GND":
                svg, p = gnd(wp[1], wp[2]); glyphs.append(svg); pts.append(p)
            elif wp[0] == "RAIL":
                svg, p = rail(wp[1], wp[2], wp[3], wp[4]); glyphs.append(svg); pts.append(p)
            elif wp[0] == "PORT":
                svg, p = port(wp[1], wp[2], wp[3], wp[4]); glyphs.append(svg); pts.append(p)
            elif isinstance(wp[0], str):
                ref, pin = wp
                if ref not in T or pin not in T[ref]:
                    sys.exit(f"wire on {net}: no terminal {ref}.{pin}")
                pts.append(T[ref][pin])
            else:
                pts.append(_t(*wp))
        out.append((net, pts))
    return out


def segments(poly):
    return [(poly[i], poly[i+1]) for i in range(len(poly)-1)]


def on_seg(p, a, b, tol=1.5):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if ax == bx:
        return abs(px-ax) <= tol and min(ay, by)-tol <= py <= max(ay, by)+tol
    if ay == by:
        return abs(py-ay) <= tol and min(ax, bx)-tol <= px <= max(ax, bx)+tol
    dx, dy = bx-ax, by-ay
    L = (dx*dx+dy*dy) ** .5
    if not L:
        return abs(px-ax) <= tol and abs(py-ay) <= tol
    t = max(0, min(1, ((px-ax)*dx + (py-ay)*dy)/L**2))
    return ((px-(ax+t*dx))**2 + (py-(ay+t*dy))**2) ** .5 <= tol


def check(polys, T, netmap, refs):
    """The drawing has to agree with netmap.json, both ways."""
    bad = []
    touch = collections.defaultdict(set)          # (ref,pin) -> nets drawn on it
    for net, poly in polys:
        for ref in refs:
            for pin, p in T.get(ref, {}).items():
                if any(on_seg(p, a, b) for a, b in segments(poly)):
                    touch[(ref, pin)].add(net)
    for ref in refs:
        for pin, net in netmap[ref].items():
            if (ref, pin) in OFF_SHEET:
                continue
            got = touch.get((ref, pin), set())
            if net not in got:
                bad.append(f"{ref}.{pin} is {net} but the drawing wires it to "
                           f"{sorted(got) or 'nothing'}")
        for pin in T.get(ref, {}):
            if pin not in netmap[ref]:
                continue
            wrong = touch.get((ref, pin), set()) - {netmap[ref][pin]}
            if wrong:
                bad.append(f"{ref}.{pin} ({netmap[ref][pin]}) is also touched by {sorted(wrong)}")
    return bad


def symbol_geometry(P, T, netmap):
    """Pin leads and body outlines, read back out of the symbols' own SVG."""
    leads, bodies = [], []
    for ref, svg in P.items():
        base = ref.rstrip("ABCD") if ref.startswith("U") else ref
        for m in re.finditer(r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" '
                             r'y2="([-\d.]+)" class="pin"', svg):
            x1, y1, x2, y2 = (float(v) for v in m.groups())
            net = None
            for pin, pt in T.get(base, {}).items():
                if abs(pt[0]-x1) + abs(pt[1]-y1) < 2 or abs(pt[0]-x2) + abs(pt[1]-y2) < 2:
                    net = netmap.get(base, {}).get(pin)
                    break
            leads.append((net, (round(x1), round(y1)), (round(x2), round(y2))))
        for m in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" '
                             r'height="([-\d.]+)" class="(body|fillwhite)"', svg):
            x, y, w, h = (float(v) for v in m.groups()[:4])
            bodies.append((ref, x, y, x+w, y+h))
        for m in re.finditer(r'<polygon points="([^"]+)" class="(fillwhite|fillbody)"', svg):
            pts = [tuple(float(v) for v in pair.split(",")) for pair in m.group(1).split()]
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            bodies.append((ref, min(xs), min(ys), max(xs), max(ys)))
    return leads, bodies


def body_hits(polys, bodies, T):
    """A wire drawn across a component body. Always a layout bug."""
    bad = []
    for net, poly in polys:
        for a, b in segments(poly):
            for ref, x0, y0, x1, y1 in bodies:
                if any(on_seg(pt, a, b, tol=0) for pt in T.get(ref, {}).values()):
                    pass
                (ax, ay), (bx, by) = a, b
                inset = 3
                if ay == by and y0+inset < ay < y1-inset and min(ax, bx) < x1-inset and max(ax, bx) > x0+inset:
                    bad.append(f"{net} runs across {ref}'s body at y={ay}")
                if ax == bx and x0+inset < ax < x1-inset and min(ay, by) < y1-inset and max(ay, by) > y0+inset:
                    bad.append(f"{net} runs across {ref}'s body at x={ax}")
    return sorted(set(bad))


def crossings(polys, leads=()):
    """Where a horizontal wire crosses a vertical wire of a DIFFERENT net.

    A crossing with no dot only means "not connected" by convention, which is
    exactly the ambiguity that makes a schematic hard to trust. The horizontal
    wire hops over the vertical one instead, so a connection is a dot and a
    crossing is a bridge, and neither can be mistaken for the other.
    """
    hor, ver = [], []
    for net, poly in polys:
        for a, b in segments(poly):
            (ax, ay), (bx, by) = a, b
            if ay == by and ax != bx:
                hor.append((net, min(ax, bx), max(ax, bx), ay))
            elif ax == bx and ay != by:
                ver.append((net, min(ay, by), max(ay, by), ax))
    for net, a, b in leads:               # a symbol's own pin leads count too
        (ax, ay), (bx, by) = a, b
        if ay == by and ax != bx:
            hor.append((net, min(ax, bx), max(ax, bx), ay))
        elif ax == bx and ay != by:
            ver.append((net, min(ay, by), max(ay, by), ax))
    out = collections.defaultdict(list)
    for net, x0, x1, y in hor:
        for net2, y0, y1, x in ver:
            if net2 == net:
                continue
            if x0 + 6 < x < x1 - 6 and y0 + 6 < y < y1 - 6:
                out[(x0, x1, y)].append(x)
    return out


def hop_path(a, b, cross):
    """One segment as an SVG path, with a little bridge at every crossing."""
    (ax, ay), (bx, by) = a, b
    key = (min(ax, bx), max(ax, bx), ay) if ay == by else None
    xs = sorted(cross.get(key, [])) if key else []
    if not xs:
        return f"M {ax} {ay} L {bx} {by}"
    if bx < ax:
        xs = list(reversed(xs))
    r, d = 8, (1 if bx > ax else -1)
    parts = [f"M {ax} {ay}"]
    for x in xs:
        parts.append(f"L {x - d*r} {ay}")
        parts.append(f"A {r} {r} 0 0 1 {x + d*r} {ay}")
    parts.append(f"L {bx} {by}")
    return " ".join(parts)


def wire_shorts(polys):
    """A wire ending on another net's wire reads as a T-junction. It is a bug."""
    bad = []
    for net, poly in polys:
        for end in (poly[0], poly[-1]):
            for net2, poly2 in polys:
                if net2 == net:
                    continue
                for a, b in segments(poly2):
                    if on_seg(end, a, b, tol=2.0):
                        bad.append(f"{net} ends at {end}, which sits on {net2}")
    return sorted(set(bad))


def junctions(polys):
    """A dot means three or more wires join, or one wire lands on another.

    It deliberately does not appear where a wire simply ends on a pin, or where
    two segments turn a corner -- those are connections by construction, and
    dotting them would make the real branch points harder to pick out.
    """
    ends = collections.Counter()
    real = [(net, a, b) for net, poly in polys for a, b in segments(poly) if a != b]
    for net, a, b in real:
        ends[(net, a)] += 1
        ends[(net, b)] += 1
    dots = {p for (net, p), n in ends.items() if n >= 3}
    for net, a, b in real:
        for p in (a, b):
            for net2, c, d in real:
                if net2 != net or (c, d) == (a, b):
                    continue
                if p not in (c, d) and on_seg(p, c, d, tol=1.0):
                    dots.add(p)
    return dots


def legend(x, y):
    return (f'<g><path class="wire" d="M {x} {y} L {x+30} {y} '
            f'A 8 8 0 0 1 {x+46} {y} L {x+76} {y}"/>'
            f'<path class="wire" d="M {x+38} {y-26} L {x+38} {y+26}"/>'
            f'<text x="{x+90}" y="{y+6}" class="note">wires cross, not connected</text>'
            f'<path class="wire" d="M {x} {y+52} L {x+76} {y+52}"/>'
            f'<path class="wire" d="M {x+38} {y+52} L {x+38} {y+78}"/>'
            f'<circle class="dot" cx="{x+38}" cy="{y+52}" r="6"/>'
            f'<text x="{x+90}" y="{y+58}" class="note">wires joined</text>'
            f'<text x="{x}" y="{y-44}" class="note">A wire ending on a pin is '
            f'connected; corners are not dotted.</text></g>')


STYLE = """
<style>
  .sheet-bg{fill:#fbfaf7}
  .body,.pin,.wire{stroke:#1a1a1a;fill:none;stroke-linecap:square}
  .body{stroke-width:2.4} .pin{stroke-width:2} .wire{stroke-width:2}
  .fillbody{fill:#1a1a1a;stroke:#1a1a1a;stroke-width:2}
  .fillwhite{fill:#fbfaf7;stroke:#1a1a1a;stroke-width:2.4}
  .dashbox{fill:none;stroke:#1a1a1a;stroke-width:1.6;stroke-dasharray:7 5}
  .ray{stroke:#1a1a1a;stroke-width:1.6;fill:none}
  .dot{fill:#1a1a1a}
  .port{fill:#fff3e3;stroke:#a85a26;stroke-width:2}
  text{font-family:"IBM Plex Mono","DejaVu Sans Mono",monospace;fill:#1a1a1a}
  .ref{font-size:17px;font-weight:600}
  .val{font-size:16px;fill:#8a5a2b}
  .note{font-size:13px;fill:#6b6b6b}
  .sign{font-size:20px;font-weight:700}
  .pin-no{font-size:13px;fill:#6b6b6b}
  .rail-label{font-size:15px;font-weight:600}
  .port-label{font-size:15px;font-weight:600;fill:#7a3f16}
  .net-label{font-size:13px;fill:#3060a0}
  .title{font-size:30px;font-weight:700}
  .subtitle{font-size:16px;fill:#5b5b5b}
  .frame{fill:none;stroke:#1a1a1a;stroke-width:2}
  @media (prefers-color-scheme: dark){
    .sheet-bg{fill:#14181d}
    .body,.pin,.wire,.ray{stroke:#e8eaed} .fillbody{fill:#e8eaed;stroke:#e8eaed}
    .fillwhite{fill:#14181d;stroke:#e8eaed} .dashbox{stroke:#e8eaed} .dot{fill:#e8eaed}
    text{fill:#e8eaed} .val{fill:#e0a56a} .note,.pin-no{fill:#9aa3ad}
    .port{fill:#3a2413;stroke:#dd8f55} .port-label{fill:#e8b184}
    .subtitle{fill:#9aa3ad} .frame{stroke:#e8eaed} .net-label{fill:#8ab4f8}
  }
</style>"""


def render(title, subtitle, P, polys, glyphs, w, h, leads=()):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
             f'height="{h}" font-size="16">', STYLE,
             f'<rect class="sheet-bg" x="0" y="0" width="{w}" height="{h}"/>']
    cross = crossings(polys, leads)
    for net, poly in polys:
        for a, b in segments(poly):
            if a == b:
                continue
            parts.append(f'<path class="wire" d="{hop_path(a, b, cross)}"/>')
    parts += glyphs
    parts += list(P.values())
    for (x, y) in junctions(polys):
        parts.append(f'<circle class="dot" cx="{x}" cy="{y}" r="6"/>')
    # net names on the longer runs, so a wire can be followed without tracing it
    seen = set()
    for net, poly in polys:
        if net in ("GND", "POS12V", "NEG12V") or net in seen:
            continue
        for (ax, ay), (bx, by) in segments(poly):
            if abs(bx-ax) >= 150 and ay == by:
                parts.append(f'<text class="net-label" x="{(ax+bx)/2}" y="{ay-9}" '
                             f'text-anchor="middle">{net}</text>')
                seen.add(net)
                break
    parts.append(legend(1700, 1310))
    parts.append(f'<rect class="frame" x="18" y="18" width="{w-36}" height="{h-36}"/>')
    parts.append(f'<text class="title" x="46" y="66">{title}</text>')
    parts.append(f'<text class="subtitle" x="46" y="92">{subtitle}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


PAGE = """<title>LPG Left Sheet</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  :root{--ground:#e9e6df;--panel:#fbfaf7;--ink:#1a1a1a;--muted:#6b6b6b;--line:#cfcabf;--copper:#a85a26}
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --ground:#0e1116;--panel:#14181d;--ink:#e8eaed;--muted:#9aa3ad;--line:#2b323b;--copper:#dd8f55}}
  :root[data-theme="dark"]{--ground:#0e1116;--panel:#14181d;--ink:#e8eaed;--muted:#9aa3ad;
    --line:#2b323b;--copper:#dd8f55}
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);
       font-family:"IBM Plex Sans",system-ui,sans-serif;height:100vh;display:flex;flex-direction:column}
  header{padding-block:10px;padding-inline:16px;border-bottom:1px solid var(--line);
         background:var(--panel);display:flex;gap:8px 20px;align-items:baseline;flex-wrap:wrap}
  h1{margin:0;font-size:17px;font-weight:600;letter-spacing:.01em}
  .sub{color:var(--muted);font-size:13px;flex:1 1 240px}
  .facts{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted)}
  .facts b{color:var(--ink);font-weight:600}
  .bar{display:flex;gap:6px}
  button{font:inherit;font-size:13px;padding:5px 11px;border:1px solid var(--line);
         background:var(--panel);color:var(--ink);border-radius:3px;cursor:pointer}
  button:hover{border-color:var(--copper)}
  button:focus-visible{outline:2px solid var(--copper);outline-offset:1px}
  #stage{flex:1;overflow:auto;padding:16px;cursor:grab}
  #stage.drag{cursor:grabbing}
  #sheet{transform-origin:0 0;width:2060px}
  #sheet svg{display:block;width:100%;height:auto;
             box-shadow:0 2px 10px rgba(0,0,0,.18);border-radius:3px}
</style>
<header>
  <h1>LPG left channel</h1>
  <p class="sub">Drawn from <code>netmap.json</code>. Every wire is checked against the netlist
     at build time, so this is the circuit on the board — not what the notes claim.</p>
  <span class="facts"><b>__PARTS__</b> parts · <b>__WIRES__</b> wires · pins verified</span>
  <span class="bar">
    <button id="out" type="button">&minus;</button>
    <button id="in" type="button">+</button>
    <button id="fit" type="button">Fit</button>
    <button id="full" type="button">100%</button>
  </span>
</header>
<div id="stage"><div id="sheet"><!--SVG--></div></div>
<script>
  const stage=document.getElementById("stage"), sheet=document.getElementById("sheet");
  let z=1;
  const apply=()=>{sheet.style.transform="scale("+z+")";
    sheet.style.height=(1440*z)+"px"; sheet.style.width="2060px";};
  const fit=()=>{z=Math.min(1,(stage.clientWidth-32)/2060); apply();};
  document.getElementById("in").onclick=()=>{z=Math.min(4,z*1.25); apply();};
  document.getElementById("out").onclick=()=>{z=Math.max(.1,z/1.25); apply();};
  document.getElementById("fit").onclick=fit;
  document.getElementById("full").onclick=()=>{z=1; apply();};
  let drag=null;
  stage.addEventListener("pointerdown",e=>{drag={x:e.clientX,y:e.clientY,
    l:stage.scrollLeft,t:stage.scrollTop}; stage.classList.add("drag"); stage.setPointerCapture(e.pointerId);});
  stage.addEventListener("pointermove",e=>{if(!drag)return;
    stage.scrollLeft=drag.l-(e.clientX-drag.x); stage.scrollTop=drag.t-(e.clientY-drag.y);});
  const stop=()=>{drag=null; stage.classList.remove("drag");};
  stage.addEventListener("pointerup",stop); stage.addEventListener("pointercancel",stop);
  window.addEventListener("resize",()=>{if(z<1)fit();});
  fit();
</script>
"""


def main():
    netmap = json.load(open(f"{KI}/tools/netmap.json"))
    values = json.load(open(f"{KI}/tools/values.json"))
    P, T, glyphs = lpg_left(netmap, values)
    refs = [r for r in T if r in netmap]
    polys = resolve(lpg_left_wires(), T, glyphs)
    bad = check(polys, T, netmap, refs) + wire_shorts(polys)
    if bad:
        print(f"drawing does not match netmap.json ({len(bad)}):")
        for b in bad:
            print("   ", b)
        sys.exit(1)
    leads, bodies = symbol_geometry(P, T, netmap)
    hits = body_hits(polys, bodies, T)
    if hits:
        print("wires drawn across component bodies:")
        for h in hits:
            print("   ", h)
        sys.exit(1)
    svg = render("LPG — left channel", "audio path and LED drive, drawn from netmap.json · "
                 "compare with Bergman's sheet · CV chain on its own sheet",
                 P, polys, glyphs, 2060, 1440, leads)
    out = f"{ROOT}/docs/sch-lpg-left.svg"
    open(out, "w").write(svg)
    page = PAGE.replace("<!--SVG-->", svg).replace("__PARTS__", str(len(refs))) \
               .replace("__WIRES__", str(len(polys)))
    open(f"{ROOT}/docs/sch-lpg-left.html", "w").write(page)
    print(f"{len(refs)} parts, {len(polys)} wires, all pins agree with netmap.json")
    print(f"-> {out}\n-> {ROOT}/docs/sch-lpg-left.html")


if __name__ == "__main__":
    main()
