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


def pot(x, y, ref, val, vert=True, wiper_right=True, ganged=True, flip=False):
    """Panel pot. Terminals 1 (ccw end) 2 (wiper) 3 (cw end) -- 1 = CCW per
    Alpha's RD902F drawing, 2026-09-23; this said the reverse before anyone had
    read one. Drawn 1 on top; flip=True puts 3 on top instead."""
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
    top, bot = _t(x, y-L/2-22), _t(x, y+L/2+22)
    return body + wires + arrow + lab, {
        "1": bot if flip else top, "2": _t(x+d*(w/2+34), y), "3": top if flip else bot}


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


def chip(x, y, w, h, ref, part, left, right):
    """A rectangular IC. left/right are [(pin, name), ...] top to bottom."""
    box = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="fillwhite"/>'
    lab = (f'<text x="{x+w/2}" y="{y-26}" class="ref" text-anchor="middle">{ref}</text>'
           f'<text x="{x+w/2}" y="{y-8}" class="val" text-anchor="middle">{part}</text>')
    g, term = box + lab, {}
    def side(pins, isleft):
        nonlocal g
        step = h / (len(pins) + 1)
        for i, (pin, name) in enumerate(pins):
            py = y + step * (i + 1)
            if isleft:
                g += f'<line x1="{x-24}" y1="{py}" x2="{x}" y2="{py}" class="pin"/>'
                g += (f'<text x="{x-28}" y="{py-8}" class="pin-no" text-anchor="end">{pin}</text>'
                      f'<text x="{x+10}" y="{py+6}" class="note">{name}</text>')
                term[pin] = _t(x-24, py)
            else:
                g += f'<line x1="{x+w}" y1="{py}" x2="{x+w+24}" y2="{py}" class="pin"/>'
                g += (f'<text x="{x+w+28}" y="{py-8}" class="pin-no">{pin}</text>'
                      f'<text x="{x+w-10}" y="{py+6}" class="note" text-anchor="end">{name}</text>')
                term[pin] = _t(x+w+24, py)
    side(left, True)
    side(right, False)
    return g, term


def jfet(x, y, ref, part):
    """N-channel JFET, gate on the left. Terminals 1 = drain, 2 = source, 3 = gate."""
    ch = (f'<line x1="{x}" y1="{y-34}" x2="{x}" y2="{y+34}" class="body"/>'
          f'<line x1="{x}" y1="{y-34}" x2="{x}" y2="{y-60}" class="pin"/>'
          f'<line x1="{x}" y1="{y+34}" x2="{x}" y2="{y+60}" class="pin"/>')
    gate = (f'<line x1="{x-60}" y1="{y}" x2="{x-14}" y2="{y}" class="pin"/>'
            f'<polygon points="{x-14},{y-7} {x-14},{y+7} {x-2},{y}" class="fillbody"/>')
    lab = (f'<text x="{x+16}" y="{y-8}" class="ref">{ref}</text>'
           f'<text x="{x+16}" y="{y+10}" class="val">{part}</text>'
           f'<text x="{x-10}" y="{y-40}" class="note" text-anchor="end">D</text>'
           f'<text x="{x-10}" y="{y+50}" class="note" text-anchor="end">S</text>')
    return ch + gate + lab, {"1": _t(x, y-60), "2": _t(x, y+60), "3": _t(x-60, y)}


def diode(x, y, ref, val, cathode_up=True):
    """Vertical signal diode. Terminal 1 is the cathode (bar), 2 the anode."""
    s = 14
    if cathode_up:
        tri = f'<polygon points="{x-s},{y+s} {x+s},{y+s} {x},{y-2}" class="fillbody"/>'
        bar = f'<line x1="{x-s-4}" y1="{y-2}" x2="{x+s+4}" y2="{y-2}" class="body"/>'
        term = {"1": _t(x, y-44), "2": _t(x, y+44)}
        wires = (f'<line x1="{x}" y1="{y-44}" x2="{x}" y2="{y-2}" class="pin"/>'
                 f'<line x1="{x}" y1="{y+s}" x2="{x}" y2="{y+44}" class="pin"/>')
    else:
        tri = f'<polygon points="{x-s},{y-s} {x+s},{y-s} {x},{y+2}" class="fillbody"/>'
        bar = f'<line x1="{x-s-4}" y1="{y+2}" x2="{x+s+4}" y2="{y+2}" class="body"/>'
        term = {"1": _t(x, y+44), "2": _t(x, y-44)}
        wires = (f'<line x1="{x}" y1="{y-44}" x2="{x}" y2="{y-s}" class="pin"/>'
                 f'<line x1="{x}" y1="{y+2}" x2="{x}" y2="{y+44}" class="pin"/>')
    lab = (f'<text x="{x+24}" y="{y-6}" class="ref">{ref}</text>'
           f'<text x="{x+24}" y="{y+10}" class="val">{val}</text>')
    return tri + bar + wires + lab, term


def led(x, y, ref, val, anode="1", cathode="2", cathode_up=False):
    """Indicator LED. Pin names follow the part, so the same glyph serves a
    symbol numbered anode-first (YLED0402Y) and one numbered cathode-first."""
    s = 14
    if cathode_up:
        tri = f'<polygon points="{x-s},{y+s} {x+s},{y+s} {x},{y-2}" class="fillbody"/>'
        bar = f'<line x1="{x-s-4}" y1="{y-2}" x2="{x+s+4}" y2="{y-2}" class="body"/>'
        term = {cathode: _t(x, y-44), anode: _t(x, y+44)}
    else:
        tri = f'<polygon points="{x-s},{y-s} {x+s},{y-s} {x},{y+2}" class="fillbody"/>'
        bar = f'<line x1="{x-s-4}" y1="{y+2}" x2="{x+s+4}" y2="{y+2}" class="body"/>'
        term = {anode: _t(x, y-44), cathode: _t(x, y+44)}
    wires = (f'<line x1="{x}" y1="{y-44}" x2="{x}" y2="{y-s if not cathode_up else y-2}" class="pin"/>'
             f'<line x1="{x}" y1="{y+2 if not cathode_up else y+s}" x2="{x}" y2="{y+44}" class="pin"/>')
    rays = (f'<path d="M {x+s+6} {y-12} l 16 -12 M {x+s+6} {y+2} l 16 -12" class="ray"/>'
            f'<path d="M {x+s+20} {y-26} l 6 4 l -1 -7 z" class="fillbody"/>'
            f'<path d="M {x+s+20} {y-12} l 6 4 l -1 -7 z" class="fillbody"/>')
    lab = (f'<text x="{x-24}" y="{y-6}" class="ref" text-anchor="end">{ref}</text>'
           f'<text x="{x-24}" y="{y+10}" class="val" text-anchor="end">{val}</text>')
    return tri + bar + wires + rays + lab, term


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
    # flip: +12V is on terminal 3 so CUTOFF opens clockwise (2026-09-23)
    put("RV1", pot(170, 220, "RV1", "CUTOFF", wiper_right=True, flip=True))
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
    # R301/R302 mix the Daisy and EXT into C306; R312 (Bergman's R12) gives U301A
    # the gain of 2 that the passive mix takes back. Added 2026-09-25, ADR 0011.
    put("R310", resistor(220, 930, "R310", V("R310"), vert=True))
    put("R301", resistor(290, 860, "R301", V("R301")))
    put("R302", resistor(350, 790, "R302", V("R302"), vert=True))
    put("C306", cap(400, 860, "C306", V("C306")))
    put("R309", resistor(500, 930, "R309", V("R309"), vert=True))
    opamp_unit("U301", "A", 620, 860, ("1", "2", "3"))
    put("R311", resistor(680, 1000, "R311", V("R311"), swap=True, flip_label=True))
    put("R312", resistor(560, 1070, "R312", V("R312"), vert=True))

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
    put("C301", cap(430, 1230, "C301", V("C301"), vert=True))
    put("C302", cap(620, 1230, "C302", V("C302")))

    # --- CV chain, Bergman's U2: invert, attenuvert, two more inverters ---
    put("R323", resistor(330, 1600, "R323", V("R323")))
    opamp_unit("U302", "A", 520, 1600, ("1", "2", "3"))
    put("R320", resistor(580, 1700, "R320", V("R320"), flip_label=True))
    # flip: the uninverted envelope is on terminal 3, so clockwise is + (2026-09-23)
    put("RV3", pot(900, 1620, "RV3", "FILTER CV AMT", wiper_right=True, flip=True))
    put("R328", resistor(1060, 1620, "R328", V("R328")))
    opamp_unit("U302", "D", 1200, 1620, ("14", "13", "12"))
    put("R330", resistor(1260, 1740, "R330", V("R330"), flip_label=True))
    put("R331", resistor(1430, 1647, "R331", V("R331")))
    opamp_unit("U302", "C", 1560, 1620, ("8", "9", "10"))
    put("R333", resistor(1660, 1780, "R333", V("R333"), flip_label=True))
    opamp_unit("U302", "B", 1000, 1950, ("7", "6", "5"))
    put("U302pwr", power_pins(180, 1900, "U302", "TL074"))
    T["U302"].update(T.pop("U302pwr"))
    put("C303", cap(430, 1950, "C303", V("C303"), vert=True))
    put("C304", cap(620, 1950, "C304", V("C304")))
    put("U301pwr", power_pins(180, 1180, "U301", "TL084"))
    glyphs.append('<text x="46" y="140" class="ref" style="font-size:20px">'
                  'AUDIO PATH AND LED DRIVE</text>')
    glyphs.append('<line x1="46" y1="1400" x2="2014" y2="1400" class="dashbox"/>')
    glyphs.append('<text x="46" y="1462" class="ref" style="font-size:20px">'
                  'CV CHAIN &#8212; Bergman U2, one per channel</text>')
    T["U301"].update(T.pop("U301pwr"))
    return P, T, glyphs


def bbd_left(netmap, values):
    """BBD left channel, laid out like the mki manual: audio across the top,
    mix below it, the 4046 clock and the sample trigger underneath."""
    V = lambda r: values.get(r, "")
    P, T, glyphs = {}, {}, []

    def put(ref, res):
        svg, terms = res
        P[ref] = svg
        T[ref] = terms

    def opamp_unit(ref, unit, x, y, pins, plus_top=True):
        svg, tt = opamp(x, y, f"{ref}-{unit}", V(ref) or "TL072", plus_top, pins)
        P[f"{ref}{unit}"] = svg
        T[ref] = {**T.get(ref, {}), pins[0]: tt["out"], pins[1]: tt["-"], pins[2]: tt["+"]}

    # --- input buffer, summing amp, the BBD itself ----------------------
    put("R106", resistor(280, 380, "R106", V("R106"), vert=True))
    put("R107", resistor(400, 300, "R107", V("R107")))
    opamp_unit("U102", "A", 560, 300, ("1", "2", "3"))
    put("R104", resistor(860, 300, "R104", "0R  IN GAIN"))
    put("R114", resistor(1030, 300, "R114", V("R114")))
    put("R118", resistor(1280, 180, "R118", V("R118")))
    put("R113", resistor(1240, 470, "R113", V("R113"), vert=True, swap=True))
    opamp_unit("U103", "A", 1200, 300, ("1", "2", "3"), plus_top=False)
    put("U101", chip(1560, 240, 200, 300, "U101", "V3205SD",
                     [("7", "IN"), ("6", "CLK1"), ("2", "CLK2"), ("8", "VGG")],
                     [("4", "OUT"), ("5", "VDD"), ("1", "VSS")]))
    put("R119", resistor(1960, 700, "R119", V("R119"), vert=True))
    put("R120", resistor(1340, 650, "R120", V("R120"), vert=True))
    put("C110", cap(1260, 650, "C110", V("C110"), vert=True, flip_label=True))
    put("R122", resistor(1860, 405, "R122", V("R122"), vert=True))
    put("C113", cap(1960, 315, "C113", V("C113")))
    put("R124", resistor(2060, 405, "R124", V("R124"), vert=True))
    opamp_unit("U106", "A", 2140, 315, ("1", "2", "3"))

    # --- sample and hold ------------------------------------------------
    put("R128", resistor(2440, 420, "R128", V("R128"), vert=True))
    put("Q1", jfet(2560, 420, "Q1", "J113"))
    put("C119", cap(2560, 600, "C119", V("C119"), vert=True))
    put("D107", diode(2500, 760, "D107", V("D107"), cathode_up=False))
    opamp_unit("U106", "B", 2740, 480, ("7", "6", "5"))
    put("R129", resistor(2716, 760, "R129", V("R129"), vert=True))
    put("R130", resistor(2820, 700, "R130", V("R130"), flip_label=True))
    put("C120", cap(3040, 480, "C120", V("C120")))

    # --- mix, feedback, output -----------------------------------------
    put("RV5", pot(1300, 1100, "RV5", "FEEDBACK", wiper_right=False))
    put("R112", resistor(1160, 1100, "R112", V("R112"), swap=True))
    put("RV6", pot(1600, 1100, "RV6", "WET/DRY", wiper_right=True))
    opamp_unit("U103", "B", 1760, 1100, ("7", "6", "5"))
    put("R131", resistor(2060, 1100, "R131", V("R131")))
    put("R132", resistor(2900, 1300, "R132", V("R132"), vert=True))

    # --- 4046 clock -----------------------------------------------------
    put("R110", resistor(300, 1600, "R110", V("R110"), vert=True))
    put("RV4", pot(300, 1760, "RV4", "TIME", wiper_right=True))
    put("R111", resistor(300, 1900, "R111", V("R111"), vert=True))
    put("R115", resistor(460, 1760, "R115", V("R115")))
    put("R116", resistor(460, 1860, "R116", V("R116")))
    put("D103", diode(700, 1660, "D103", V("D103"), cathode_up=True))
    put("D105", diode(800, 1860, "D105", V("D105"), cathode_up=True))
    put("R117", resistor(460, 2060, "R117", V("R117")))
    put("D104", diode(640, 1980, "D104", V("D104"), cathode_up=True))
    put("D106", diode(720, 2120, "D106", V("D106"), cathode_up=True))
    put("C114", cap(760, 1810, "C114", V("C114"), vert=True, flip_label=True))
    put("R123", resistor(830, 2000, "R123", V("R123"), vert=True))
    put("R121", resistor(760, 2180, "R121", V("R121"), vert=True))
    put("U104", chip(900, 1600, 240, 420, "U104", "CD4046B",
                     [("9", "VCO_IN"), ("5", "INH"), ("6", "C1A"), ("7", "C1B"),
                      ("11", "R1"), ("12", "R2")],
                     [("4", "VCO_OUT"), ("3", "COMP_IN"), ("2", "PC1_OUT"),
                      ("14", "SIG_IN"), ("16", "VDD"), ("8", "VSS")]))

    # --- sample trigger comparator --------------------------------------
    put("C116", cap(1600, 1560, "C116", V("C116")))
    put("R127", resistor(1700, 1650, "R127", V("R127"), vert=True))
    put("R125", resistor(1620, 1760, "R125", V("R125"), vert=True))
    put("R126", resistor(1620, 1900, "R126", V("R126"), vert=True))
    opamp_unit("U102", "B", 1800, 1560, ("7", "6", "5"))

    # --- supplies and decoupling ----------------------------------------
    put("U102pwr", power_pins(300, 2330, "U102", "TL072", ("8", "4")))
    T["U102"].update(T.pop("U102pwr"))
    put("U103pwr", power_pins(700, 2330, "U103", "TL072", ("8", "4")))
    T["U103"].update(T.pop("U103pwr"))
    put("U106pwr", power_pins(1100, 2330, "U106", "TL072", ("8", "4")))
    T["U106"].update(T.pop("U106pwr"))
    for i, (ref, kind) in enumerate([("C105", "+"), ("C107", "+"), ("C121", "+"),
                                     ("C109", "5"), ("C111", "5")]):
        put(ref, cap(1560 + i*180, 2400, ref, V(ref), vert=True))
    for i, ref in enumerate(["C106", "C108", "C122"]):
        put(ref, cap(2540 + i*220, 2400, ref, V(ref)))

    glyphs.append('<text x="46" y="140" class="ref" style="font-size:20px">'
                  'AUDIO PATH \u2014 input, BBD, sample and hold</text>')
    glyphs.append('<line x1="46" y1="960" x2="3154" y2="960" class="dashbox"/>')
    glyphs.append('<text x="46" y="1010" class="ref" style="font-size:20px">'
                  'MIX \u2014 feedback, wet/dry, output</text>')
    glyphs.append('<line x1="46" y1="1440" x2="3154" y2="1440" class="dashbox"/>')
    # 1478, not 1500 like the other band headings: R110's +12V rail label hangs
    # at y=1510 and the two were printing through each other.
    glyphs.append('<text x="46" y="1478" class="ref" style="font-size:20px">'
                  'CLOCK \u2014 CD4046 VCO, TIME control, sample trigger</text>')
    glyphs.append('<line x1="46" y1="2260" x2="3154" y2="2260" class="dashbox"/>')
    glyphs.append('<text x="46" y="2310" class="ref" style="font-size:20px">'
                  'SUPPLIES</text>')
    return P, T, glyphs


def psu(netmap, values):
    """USB-C in, the DKM10 converter, the rail filters and the three linear
    regulators. Laid out like the V3.0 reference: input at the left, the
    converter in the middle, rails to the right, regulators underneath."""
    V = lambda r: values.get(r, "")
    P, T, glyphs = {}, {}, []

    def put(ref, res):
        svg, terms = res
        P[ref] = svg
        T[ref] = terms

    # --- USB-C input -----------------------------------------------------
    put("J11", chip(120, 200, 260, 420, "J11", "TYPE-C-31-M-12",
                    [("A1B12", "GND"), ("B1A12", "GND"), ("1", "SHELL"), ("2", "SHELL"),
                     ("3", "SHELL"), ("4", "SHELL")],
                    [("A4B9", "VBUS"), ("B4A9", "VBUS"), ("A5", "CC1"), ("B5", "CC2")]))
    put("R22", resistor(450, 640, "R22", V("R22") or "5k1", vert=True))
    put("R23", resistor(560, 640, "R23", V("R23") or "5k1", vert=True, swap=True))
    # 520, not 560: "SMAJ6.0A" is the longest value string on this row and at
    # 100px spacing it ran straight through C28's top plate.
    put("D3", zener(520, 420, "D3", V("D3"), anode_up=False))
    put("C28", cap(660, 420, "C28", V("C28") or "10nF", vert=True))
    put("C43", cap(760, 420, "C43", V("C43") or "100nF", vert=True))
    put("F1", resistor(870, 284, "F1", V("F1") or "PTC 3A"))

    # --- converter -------------------------------------------------------
    put("C29", cap(960, 420, "C29", V("C29") or "10uF", vert=True))
    put("C30", cap(1040, 420, "C30", V("C30") or "1uF", vert=True, swap=True))
    put("C31", cap(1120, 420, "C31", V("C31") or "100nF", vert=True, swap=True))
    put("U7", chip(1250, 200, 300, 420, "U7", "DKM10E-12",
                   [("1", "+Vin"), ("2", "-Vin")],
                   [("3", "+Vout"), ("4", "Common"), ("5", "-Vout"), ("6", "R.C. open")]))

    # --- positive rail ---------------------------------------------------
    # 47uF, not 470uF. These read RVT1E470M0505, and the "470" is an EIA
    # three-digit code -- 47 x 10^0 -- not a value in microfarads. Its sibling
    # RVT1H220M0605 carries its own descr, "22uF 50V", which settles the
    # reading; and 470uF at 25V is a 10mm can, not the 5.0mm one this footprint
    # is. The fallback here said 470uF for a week and was the only record in
    # the repo that did, which is why these now come from values.json instead.
    put("C32", cap(1680, 420, "C32", V("C32") or "47uF", vert=True))
    put("C34", cap(1780, 420, "C34", V("C34") or "100nF", vert=True, swap=True))
    put("L1", resistor(1880, 284, "L1", V("L1") or "bead"))
    put("C36", cap(1990, 420, "C36", V("C36") or "22uF", vert=True))
    put("C38", cap(2080, 420, "C38", V("C38") or "100nF", vert=True, swap=True))
    put("C40", cap(2170, 420, "C40", V("C40"), vert=True))
    put("R24", resistor(2300, 420, "R24", V("R24") or "2k2", vert=True, swap=True))
    put("D1", led(2300, 560, "D1", V("D1") or "green"))

    # --- negative rail ---------------------------------------------------
    put("C33", cap(1680, 800, "C33", V("C33") or "47uF", vert=True, swap=True))
    put("C35", cap(1780, 800, "C35", V("C35") or "100nF", vert=True))
    put("L2", resistor(1880, 700, "L2", V("L2") or "bead"))
    put("C37", cap(1990, 800, "C37", V("C37") or "22uF", vert=True, swap=True))
    put("C39", cap(2080, 800, "C39", V("C39") or "100nF", vert=True))
    put("R25", resistor(2300, 790, "R25", V("R25") or "2k2", vert=True, swap=True))
    put("D2", led(2300, 930, "D2", V("D2") or "red", cathode_up=True))

    # --- the BBD's 5V ----------------------------------------------------
    put("U8", chip(1700, 1040, 240, 180, "U8", "AMS1117-5.0",
                   [("3", "VIN"), ("1", "GND")], [("2", "VOUT"), ("4", "VOUT tab")]))
    put("C41", cap(2120, 1160, "C41", V("C41"), vert=True))
    put("C42", cap(2200, 1160, "C42", V("C42"), vert=True))

    # --- 3V3 rails off the Daisy's 5V ------------------------------------
    put("FB1", resistor(360, 1100, "FB1", V("FB1") or "bead"))
    put("C24", cap(480, 1220, "C24", V("C24") or "1uF", vert=True))
    put("U5", chip(600, 1010, 240, 180, "U5", "AMS1117-3.3",
                   [("3", "VIN"), ("1", "GND")], [("2", "VOUT"), ("4", "VOUT tab")]))
    put("C20", cap(1000, 1220, "C20", V("C20") or "1uF", vert=True))
    put("C21", cap(1080, 1220, "C21", V("C21") or "100nF", vert=True))
    put("FB2", resistor(360, 1520, "FB2", V("FB2") or "bead"))
    put("C25", cap(480, 1640, "C25", V("C25") or "1uF", vert=True))
    put("U6", chip(600, 1430, 240, 180, "U6", "AMS1117-3.3",
                   [("3", "VIN"), ("1", "GND")], [("2", "VOUT"), ("4", "VOUT tab")]))
    put("C22", cap(1000, 1640, "C22", V("C22") or "1uF", vert=True))
    put("C23", cap(1080, 1640, "C23", V("C23") or "100nF", vert=True))

    # --- the Daisy's 3V3 and the I2C pull-ups ----------------------------
    put("C26", cap(1500, 1640, "C26", V("C26") or "1uF", vert=True))
    put("C27", cap(1580, 1640, "C27", V("C27") or "100nF", vert=True))
    put("R20", resistor(1800, 1560, "R20", V("R20") or "2k2", swap=True))
    put("R21", resistor(1800, 1680, "R21", V("R21") or "2k2", swap=True))

    glyphs.append('<text x="46" y="140" class="ref" style="font-size:20px">'
                  'INPUT AND CONVERTER \u2014 check against V3.0.pdf</text>')
    glyphs.append('<line x1="46" y1="980" x2="2954" y2="980" class="dashbox"/>')
    glyphs.append('<text x="46" y="1030" class="ref" style="font-size:20px">'
                  'REGULATORS \u2014 the Daisy returns 5V and 3V3 on its own pins</text>')
    return P, T, glyphs


# ------------------------------------------------------------------ wires ---
# Each entry: (net, [waypoints]).  A waypoint is ("REF", "pin") or (x, y).
# Ground and rail glyphs are placed by ("GND", x, y) / ("RAIL", x, y, name, up).

def lpg_left_wires():
    return [
        # ---- LED drive, exactly Bergman's arrangement ----
        ("POS12V",      [("RAIL", 170, 160, "+12V", True), ("RV1", "3")]),
        ("GND",         [("RV1", "1"), ("GND", 170, 280)]),
        ("LPG_OFS_L",   [("RV1", "2"), ("R303", "1")]),
        ("LPG_SUM_L",   [("R303", "2"), (430, 220), (430, 247), ("U301", "6")]),
        ("LPG_SUM_L",   [(430, 220), (430, 400), (200, 400), (200, 620), ("C305", "1")]),
        ("LPG_SUM_L",   [(200, 520), ("R305", "1")]),
        ("LPG_SUM_L",   [(430, 270), (230, 270), (230, 330), ("RT301", "1")]),
        ("LPG_BP_L",    [("U301", "5"), (490, 193), ("R308", "1")]),
        ("GND",         [("R308", "2"), ("GND", 490, 450)]),
        ("LPG_C5_L",    [("C305", "2"), ("R304", "1")]),
        ("LPG_CV_L",    [(1780, 1620), (1780, 1440), (150, 1440), (150, 700),
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
        ("AUDIO_OUT_L", [("PORT", 200, 860, "AUDIO_OUT_L  ← Daisy out", False),
                         (220, 860), ("R301", "1")]),
        ("AUDIO_OUT_L", [(220, 860), ("R310", "1")]),
        ("GND",         [("R310", "2"), ("GND", 220, 980)]),
        ("EXT_AMP_OUT_L", [("PORT", 200, 740, "EXT_AMP_OUT_L  ← EXT in, U10", False),
                         ("R302", "1")]),
        ("LPG_MIX_L",   [("R301", "2"), (350, 860), ("C306", "1")]),
        ("LPG_MIX_L",   [(350, 860), ("R302", "2")]),
        ("LPG_INF_L",   [("C306", "2"), (500, 860), (560, 860), (560, 833), ("U301", "3")]),
        ("LPG_INF_L",   [(500, 860), ("R309", "1")]),
        ("GND",         [("R309", "2"), ("GND", 500, 980)]),
        ("LPG_AFB_L",   [("U301", "2"), (560, 887), (560, 1000), ("R311", "2")]),
        ("LPG_AFB_L",   [(560, 1000), ("R312", "1")]),
        ("GND",         [("R312", "2"), ("GND", 560, 1120)]),
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
        ("LPG_OUT_L",   [(1680, 900), (1680, 960), (1456, 960), (1456, 1003), ("U301", "12")]),
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
        ("POS12V",      [("RAIL", 430, 1190, "+12V", True), ("C301", "1")]),
        ("GND",         [("C301", "2"), ("GND", 430, 1270)]),
        ("NEG12V",      [("C302", "1"), (520, 1230), (520, 1330), ("RAIL", 520, 1330, "-12V", False)]),
        ("GND",         [("C302", "2"), (700, 1230), (700, 1330), ("GND", 700, 1330)]),

        # ---- CV chain: invert, attenuvert, invert, invert ----
        ("LPG_ENV",     [("PORT", 200, 1600, "LPG_ENV  ← Daisy CV_OUT_1", False),
                         ("R323", "1")]),
        ("LPG_ENV",     [(240, 1600), (240, 1500), (900, 1500), ("RV3", "3")]),
        ("LPG_CVI_L",   [("R323", "2"), (450, 1600), (450, 1627), ("U302", "2")]),
        ("LPG_CVI_L",   [("U302", "2"), (496, 1700), ("R320", "1")]),
        ("LPG_ENVN_L",  [("R320", "2"), (700, 1700), (700, 1600), ("U302", "1")]),
        ("LPG_ENVN_L",  [(700, 1600), (820, 1600), (820, 1680), ("RV3", "1")]),
        ("LPG_CVW_L",   [("RV3", "2"), ("R328", "1")]),
        ("LPG_SUMCV_L", [("R328", "2"), (1140, 1620), (1140, 1647), ("U302", "13")]),
        ("LPG_SUMCV_L", [("U302", "13"), (1176, 1740), ("R330", "1")]),
        ("LPG_CVD_L",   [("U302", "14"), (1380, 1620), ("R331", "1")]),
        ("LPG_CVD_L",   [("R330", "2"), (1380, 1740), (1380, 1647)]),
        ("LPG_CVC_L",   [("R331", "2"), ("U302", "9")]),
        ("LPG_CVC_L",   [("U302", "9"), (1536, 1780), ("R333", "1")]),
        ("LPG_CV_L",    [("R333", "2"), (1780, 1780), (1780, 1620), ("U302", "8")]),

        # ---- U302's ground bus, its unused section, its supply ----
        ("GND",         [("U302", "3"), (430, 1573), (430, 1820), (1490, 1820)]),
        ("GND",         [(990, 1820), ("GND", 990, 1820)]),
        ("GND",         [("U302", "12"), (1120, 1593), (1120, 1820)]),
        ("GND",         [("U302", "10"), (1490, 1593), (1490, 1820)]),
        ("GND",         [("U302", "5"), (900, 1923), (900, 2060), ("GND", 900, 2060)]),
        ("LPG_NC_L",    [("U302", "7"), (1180, 1950), (1180, 2010), (940, 2010),
                         (940, 1977), ("U302", "6")]),
        ("POS12V",      [("RAIL", 235, 1876, "+12V", True), ("U302", "4")]),
        ("NEG12V",      [("U302", "11"), ("RAIL", 315, 2020, "-12V", False)]),
        ("POS12V",      [("RAIL", 430, 1910, "+12V", True), ("C303", "1")]),
        ("GND",         [("C303", "2"), ("GND", 430, 1990)]),
        ("NEG12V",      [("C304", "1"), (520, 1950), (520, 2050), ("RAIL", 520, 2050, "-12V", False)]),
        ("GND",         [("C304", "2"), (760, 1950), (760, 2050), ("GND", 760, 2050)]),
    ]


def bbd_left_wires():
    return [
        # ---- input buffer -> summing amp -> BBD ----
        ("BBD_IN_L",    [("PORT", 180, 300, "BBD_IN_L  \u2190 LPG out", False), (280, 300),
                         ("R107", "1")]),
        ("BBD_IN_L",    [(280, 300), ("R106", "1")]),
        ("GND",         [("R106", "2"), ("GND", 280, 430)]),
        ("BBD_INF_L",   [("R107", "2"), (500, 300), (500, 273), ("U102", "3")]),
        ("BBD_DRY_L",   [("U102", "1"), (740, 300), ("R104", "1")]),
        ("BBD_DRY_L",   [(740, 300), (740, 380), (500, 380), (500, 327), ("U102", "2")]),
        ("BBD_DRY_L",   [(740, 380), (740, 1000), (1600, 1000), ("RV6", "1")]),
        ("BBD_GAIN_L",  [("R104", "2"), ("R114", "1")]),
        ("BBD_SUM_L",   [("R114", "2"), (1140, 300), (1140, 273), ("U103", "2")]),
        ("BBD_SUM_L",   [(1140, 300), (1140, 380), ("R113", "2")]),
        ("BBD_SUM_L",   [(1140, 273), (1140, 180), ("R118", "1")]),
        ("NEG12V",      [("R113", "1"), ("RAIL", 1240, 560, "-12V", False)]),
        ("GND",         [("U103", "3"), (1120, 327), (1120, 430), ("GND", 1120, 430)]),
        ("BBD_SIGIN_L", [("R118", "2"), (1400, 180), (1400, 300), ("U103", "1")]),
        ("BBD_SIGIN_L", [(1400, 300), (1440, 300), ("U101", "7")]),
        ("P5V_BBD",     [("RAIL", 1960, 650, "+5V BBD", True), ("R119", "1")]),
        ("BBD_VGG_L",   [("R119", "2"), (1960, 800), (1600, 800), (1600, 560),
                         (1400, 560), (1400, 480), ("U101", "8")]),
        ("BBD_VGG_L",   [(1400, 560), (1340, 560), ("R120", "1")]),
        ("BBD_VGG_L",   [(1340, 560), (1260, 560), ("C110", "1")]),
        ("GND",         [("R120", "2"), ("GND", 1340, 700)]),
        ("GND",         [("C110", "2"), ("GND", 1260, 686)]),
        ("P5V_BBD",     [("U101", "5"), (1820, 390), (1820, 200), ("RAIL", 1820, 200, "+5V BBD", True)]),
        ("GND",         [("U101", "1"), (1900, 465), (1900, 560), ("GND", 1900, 560)]),
        ("BBD_RAW_L",   [("U101", "4"), (1860, 315), ("C113", "1")]),
        ("BBD_RAW_L",   [(1860, 315), ("R122", "1")]),
        ("GND",         [("R122", "2"), ("GND", 1860, 455)]),
        ("BBD_AC_L",    [("C113", "2"), (2060, 315), (2060, 288), ("U106", "3")]),
        ("BBD_AC_L",    [(2060, 315), ("R124", "1")]),
        ("GND",         [("R124", "2"), ("GND", 2060, 455)]),

        # ---- sample and hold ----
        ("BBD_SH_IN_L", [("U106", "1"), (2284, 215), (2080, 215), (2080, 342), ("U106", "2")]),
        ("BBD_SH_IN_L", [("U106", "1"), (2560, 315), ("Q1", "1")]),
        ("BBD_SH_IN_L", [(2440, 315), ("R128", "1")]),
        ("BBD_SH_G_L",  [("R128", "2"), (2440, 500), (2500, 500), ("Q1", "3")]),
        ("BBD_SH_G_L",  [(2500, 500), (2500, 716)]),
        ("BBD_SH_G_L",  [(2500, 716), ("D107", "2")]),
        ("BBD_SH_HOLD_L", [("Q1", "2"), (2560, 540), ("C119", "1")]),
        ("BBD_SH_HOLD_L", [(2560, 540), (2660, 540), (2660, 453), ("U106", "5")]),
        ("GND",         [("C119", "2"), ("GND", 2560, 636)]),
        ("BBD_SH_FB_L", [("U106", "6"), (2716, 710), ("R129", "1")]),
        ("BBD_SH_FB_L", [(2716, 700), ("R130", "1")]),
        ("GND",         [("R129", "2"), ("GND", 2716, 810)]),
        ("BBD_WET_L",   [("R130", "2"), (2940, 700), (2940, 480), ("U106", "7")]),
        ("BBD_WET_L",   [(2940, 480), ("C120", "1")]),

        # ---- mix, feedback, output ----
        ("BBD_WETAC_L", [("C120", "2"), (3120, 480), (3120, 1220), (1300, 1220),
                         ("RV5", "3")]),
        ("BBD_WETAC_L", [(1600, 1220), ("RV6", "3")]),
        ("BBD_WETAC_L", [(2900, 1220), ("R132", "1")]),
        ("BBD_WETOUT_L", [("R132", "2"), (2900, 1350),
                          ("PORT", 3000, 1350, "BBD_WETOUT_L  \u2192 resample bus", True)]),
        ("GND",         [("RV5", "1"), (1240, 1040), (1240, 1320), ("GND", 1240, 1320)]),
        ("BBD_FB_L",    [("RV5", "2"), ("R112", "1")]),
        ("BBD_SUM_L",   [("R112", "2"), (1040, 1100), (1040, 380), (1140, 380)]),
        ("BBD_MIXW_L",  [("RV6", "2"), (1700, 1100), (1700, 1073), ("U103", "5")]),
        ("BBD_MIX_L",   [("U103", "7"), (1960, 1100), ("R131", "1")]),
        ("BBD_MIX_L",   [(1960, 1100), (1960, 1180), (1700, 1180), (1700, 1127),
                         ("U103", "6")]),
        ("BBD_OUT_L",   [("R131", "2"), ("PORT", 2220, 1100, "BBD_OUT_L  \u2192 J9 tip", True)]),

        # ---- TIME control into the 4046 ----
        ("POS12V",      [("RAIL", 300, 1550, "+12V", True), ("R110", "1")]),
        ("BBD_TIMEHI_L", [("R110", "2"), ("RV4", "1")]),
        ("BBD_TIMELO_L", [("RV4", "3"), ("R111", "1")]),
        ("GND",         [("R111", "2"), ("GND", 300, 1950)]),
        ("BBD_TIMEW_L", [("RV4", "2"), ("R115", "1")]),
        ("BBD_VCOCV_L", [("R115", "2"), (600, 1760), (830, 1760), (830, 1660),
                         ("U104", "9")]),
        ("TIME_CV",     [("PORT", 300, 1860, "TIME_CV  \u2190 Daisy CV_OUT_2", False),
                         ("R116", "1")]),
        ("BBD_VCOCV_L", [("R116", "2"), (600, 1860), (600, 1760)]),
        ("BBD_VCOCV_L", [(700, 1760), ("D103", "2")]),
        ("P5V_BBD",     [("D103", "1"), (700, 1580), ("RAIL", 700, 1580, "+5V BBD", True)]),
        ("BBD_VCOCV_L", [(800, 1760), ("D105", "1")]),
        ("GND",         [("D105", "2"), ("GND", 800, 1920)]),

        # ---- inhibit ----
        ("GATE_OUT_2",  [("PORT", 300, 2060, "GATE_OUT_2  \u2190 Daisy", False), ("R117", "1")]),
        ("BBD_INH_L",   [("R117", "2"), (560, 2060), (560, 1720), ("U104", "5")]),
        ("BBD_INH_L",   [(560, 2060), (640, 2060), ("D104", "2")]),
        ("P5V_BBD",     [("D104", "1"), (640, 1900), ("RAIL", 640, 1900, "+5V BBD", True)]),
        ("BBD_INH_L",   [(640, 2060), (720, 2060), ("D106", "1")]),
        ("GND",         [("D106", "2"), ("GND", 720, 2180)]),

        # ---- 4046 timing parts and supply ----
        ("BBD_C1A_L",   [("U104", "6"), (760, 1780), ("C114", "1")]),
        ("BBD_C1B_L",   [("U104", "7"), (760, 1840), ("C114", "2")]),
        ("BBD_VCOR1_L", [("U104", "11"), (830, 1900), ("R123", "1")]),
        ("GND",         [("R123", "2"), ("GND", 830, 2050)]),
        ("BBD_VCOR2_L", [("U104", "12"), (760, 1960), (760, 2080), ("R121", "1")]),
        ("GND",         [("R121", "2"), ("GND", 760, 2230)]),
        ("P5V_BBD",     [("U104", "14"), (1480, 1840), (1480, 1700),
                         ("RAIL", 1480, 1700, "+5V BBD", True)]),
        ("P5V_BBD",     [("U104", "16"), (1480, 1900), (1480, 1840)]),
        ("GND",         [("U104", "8"), (1240, 1960), (1240, 2060), ("GND", 1240, 2060)]),

        # ---- clock out to the BBD, and the complementary phase ----
        ("BBD_CLK_L",   [("U104", "4"), (1220, 1660), (1220, 1720), ("U104", "3")]),
        ("BBD_CLK_L",   [(1220, 1660), (1220, 360), ("U101", "6")]),
        ("BBD_CLKN_L",  [("U104", "2"), (1360, 1780), (1360, 420), ("U101", "2")]),

        # ---- sample trigger ----
        ("BBD_CLK_L",   [(1220, 1560), ("C116", "1")]),
        ("BBD_TRIGIN_L", [("C116", "2"), (1700, 1560), (1700, 1533), ("U102", "5")]),
        ("BBD_TRIGIN_L", [(1700, 1560), ("R127", "1")]),
        ("GND",         [("R127", "2"), ("GND", 1700, 1700)]),
        ("POS12V",      [("RAIL", 1620, 1710, "+12V", True), ("R125", "1")]),
        ("BBD_TRIGREF_L", [("R125", "2"), (1620, 1830), (1740, 1830), (1740, 1587),
                           ("U102", "6")]),
        ("BBD_TRIGREF_L", [(1620, 1830), ("R126", "1")]),
        ("GND",         [("R126", "2"), ("GND", 1620, 1950)]),
        ("BBD_TRIG_L",  [("U102", "7"), (2500, 1560), ("D107", "1")]),

        # ---- supplies ----
        ("POS12V",      [("RAIL", 375, 2306, "+12V", True), ("U102", "8")]),
        ("NEG12V",      [("U102", "4"), ("RAIL", 455, 2450, "-12V", False)]),
        ("POS12V",      [("RAIL", 775, 2306, "+12V", True), ("U103", "8")]),
        ("NEG12V",      [("U103", "4"), ("RAIL", 855, 2450, "-12V", False)]),
        ("POS12V",      [("RAIL", 1175, 2306, "+12V", True), ("U106", "8")]),
        ("NEG12V",      [("U106", "4"), ("RAIL", 1255, 2450, "-12V", False)]),
        ("POS12V",      [("RAIL", 1560, 2352, "+12V", True), ("C105", "1")]),
        ("GND",         [("C105", "2"), ("GND", 1560, 2448)]),
        ("POS12V",      [("RAIL", 1740, 2352, "+12V", True), ("C107", "1")]),
        ("GND",         [("C107", "2"), ("GND", 1740, 2448)]),
        ("POS12V",      [("RAIL", 1920, 2352, "+12V", True), ("C121", "1")]),
        ("GND",         [("C121", "2"), ("GND", 1920, 2448)]),
        ("P5V_BBD",     [("RAIL", 2100, 2352, "+5V BBD", True), ("C109", "1")]),
        ("GND",         [("C109", "2"), ("GND", 2100, 2448)]),
        ("P5V_BBD",     [("RAIL", 2280, 2352, "+5V BBD", True), ("C111", "1")]),
        ("GND",         [("C111", "2"), ("GND", 2280, 2448)]),
        ("NEG12V",      [("C106", "1"), (2440, 2400), (2440, 2480),
                         ("RAIL", 2440, 2480, "-12V", False)]),
        ("GND",         [("C106", "2"), (2620, 2400), (2620, 2480), ("GND", 2620, 2480)]),
        ("NEG12V",      [("C108", "1"), (2660, 2400), (2660, 2480),
                         ("RAIL", 2660, 2480, "-12V", False)]),
        ("GND",         [("C108", "2"), (2840, 2400), (2840, 2480), ("GND", 2840, 2480)]),
        ("NEG12V",      [("C122", "1"), (2880, 2400), (2880, 2480),
                         ("RAIL", 2880, 2480, "-12V", False)]),
        ("GND",         [("C122", "2"), (3060, 2400), (3060, 2480), ("GND", 3060, 2480)]),
    ]


def psu_wires():
    return [
        # ---- connector shells and shield to ground ----
        ("GND",   [("J11", "A1B12"), (60, 260), (60, 660), ("GND", 60, 660)]),
        ("GND",   [("J11", "B1A12"), (60, 320)]),
        ("GND",   [("J11", "1"), (60, 380)]),
        ("GND",   [("J11", "2"), (60, 440)]),
        ("GND",   [("J11", "3"), (60, 500)]),
        ("GND",   [("J11", "4"), (60, 560)]),

        # ---- VBUS: both pairs, CC pulldowns, TVS, bypass, fuse ----
        ("VBUS",  [("J11", "A4B9"), (470, 284), (520, 284), (660, 284), (760, 284),
                   ("F1", "1")]),
        ("VBUS",  [("J11", "B4A9"), (470, 368), (470, 284)]),
        ("VBUS",  [(520, 284), ("D3", "1")]),
        ("VBUS",  [(660, 284), ("C28", "1")]),
        ("VBUS",  [(760, 284), ("C43", "1")]),
        ("GND",   [("D3", "2"), ("GND", 520, 464)]),
        ("GND",   [("C28", "2"), ("GND", 660, 456)]),
        ("GND",   [("C43", "2"), ("GND", 760, 456)]),
        ("CC1",   [("J11", "A5"), (450, 452), ("R22", "1")]),
        ("GND",   [("R22", "2"), ("GND", 450, 690)]),
        ("CC2",   [("J11", "B5"), (560, 536), ("R23", "2")]),
        ("GND",   [("R23", "1"), ("GND", 560, 690)]),

        # ---- filtered VBUS into the converter ----
        ("VBUS_F", [("F1", "2"), (960, 284), (1040, 284), (1120, 284), (1180, 284),
                    (1180, 340), ("U7", "1")]),
        ("VBUS_F", [(960, 284), ("C29", "1")]),
        ("VBUS_F", [(1040, 284), ("C30", "2")]),
        ("VBUS_F", [(1120, 284), ("C31", "2")]),
        ("GND",   [("C29", "2"), ("GND", 960, 456)]),
        ("GND",   [("C30", "1"), ("GND", 1040, 456)]),
        ("GND",   [("C31", "1"), ("GND", 1120, 456)]),
        ("GND",   [("U7", "2"), (1180, 480), (1180, 640), ("GND", 1180, 640)]),
        ("GND",   [("U7", "4"), (1600, 368), (1600, 600), ("GND", 1600, 600)]),

        # ---- positive rail ----
        ("POS12V_RAW", [("U7", "3"), (1680, 284), (1780, 284), ("L1", "1")]),
        ("POS12V_RAW", [(1680, 284), ("C32", "1")]),
        ("POS12V_RAW", [(1780, 284), ("C34", "2")]),
        ("GND",   [("C32", "2"), ("GND", 1680, 456)]),
        ("GND",   [("C34", "1"), ("GND", 1780, 456)]),
        ("POS12V", [("L1", "2"), (1990, 284), (2080, 284), (2170, 284), (2300, 284),
                    (2600, 284), ("PORT", 2700, 284, "POS12V  \u2192 board", True)]),
        ("POS12V", [(1990, 284), ("C36", "1")]),
        ("POS12V", [(2080, 284), ("C38", "2")]),
        ("POS12V", [(2170, 284), ("C40", "1")]),
        ("POS12V", [(2300, 284), ("R24", "2")]),
        ("POS12V", [(2600, 284), (2600, 900), (1600, 900), (1600, 1100), ("U8", "3")]),
        ("GND",   [("C36", "2"), ("GND", 1990, 456)]),
        ("GND",   [("C38", "1"), ("GND", 2080, 456)]),
        ("GND",   [("C40", "2"), ("GND", 2150, 456)]),
        ("LED_POS", [("R24", "1"), ("D1", "1")]),
        ("GND",   [("D1", "2"), ("GND", 2300, 640)]),

        # ---- negative rail ----
        ("NEG12V_RAW", [("U7", "5"), (1650, 452), (1650, 700), (1680, 700), (1780, 700),
                        ("L2", "1")]),
        ("NEG12V_RAW", [(1680, 700), ("C33", "2")]),
        ("NEG12V_RAW", [(1780, 700), ("C35", "1")]),
        ("GND",   [("C33", "1"), ("GND", 1680, 836)]),
        ("GND",   [("C35", "2"), ("GND", 1780, 836)]),
        ("NEG12V", [("L2", "2"), (1990, 700), (2080, 700), (2300, 700),
                    ("PORT", 2700, 700, "NEG12V  \u2192 board", True)]),
        ("NEG12V", [(1990, 700), ("C37", "2")]),
        ("NEG12V", [(2080, 700), ("C39", "1")]),
        ("NEG12V", [(2300, 700), ("R25", "2")]),
        ("GND",   [("C37", "1"), ("GND", 1990, 836)]),
        ("GND",   [("C39", "2"), ("GND", 2080, 836)]),
        ("LED_NEG", [("R25", "1"), ("D2", "2")]),
        ("GND",   [("D2", "1"), (2300, 1010), (2400, 1010), ("GND", 2400, 1010)]),

        # ---- the BBD's 5V ----
        ("GND",   [("U8", "1"), (1640, 1160), (1640, 1230), ("GND", 1640, 1230)]),
        ("P5V_BBD", [("U8", "2"), (2040, 1100), (2120, 1100), (2200, 1100),
                     ("PORT", 2700, 1100, "P5V_BBD  \u2192 BBD", True)]),
        ("P5V_BBD", [("U8", "4"), (2040, 1160), (2040, 1100)]),
        ("P5V_BBD", [(2120, 1100), ("C41", "1")]),
        ("P5V_BBD", [(2200, 1100), ("C42", "1")]),
        ("GND",   [("C41", "2"), ("GND", 2120, 1196)]),
        ("GND",   [("C42", "2"), ("GND", 2200, 1196)]),

        # ---- OLED 3V3 ----
        ("P5V",   [("PORT", 200, 1100, "P5V  \u2190 Daisy pin A6", False), (260, 1100),
                   ("FB1", "1")]),
        ("P5V",   [(260, 1100), (260, 1520), ("FB2", "1")]),
        ("P5V_OLED", [("FB1", "2"), (480, 1100), ("U5", "3")]),
        ("P5V_OLED", [(480, 1100), ("C24", "1")]),
        ("GND",   [("C24", "2"), ("GND", 480, 1256)]),
        ("GND",   [("U5", "1"), (540, 1160), (540, 1300), ("GND", 540, 1300)]),
        ("P3V3_OLED", [("U5", "2"), (940, 1070), (1000, 1070), (1080, 1070),
                       ("PORT", 1300, 1070, "P3V3_OLED  \u2192 DS1", True)]),
        ("P3V3_OLED", [("U5", "4"), (940, 1130), (940, 1070)]),
        ("P3V3_OLED", [(1000, 1070), ("C20", "1")]),
        ("P3V3_OLED", [(1080, 1070), ("C21", "1")]),
        ("GND",   [("C20", "2"), ("GND", 1000, 1256)]),
        ("GND",   [("C21", "2"), ("GND", 1080, 1256)]),

        # ---- MSP430 3V3 ----
        ("P5V_MSP", [("FB2", "2"), (480, 1520), ("U6", "3")]),
        ("P5V_MSP", [(480, 1520), ("C25", "1")]),
        ("GND",   [("C25", "2"), ("GND", 480, 1676)]),
        ("GND",   [("U6", "1"), (540, 1580), (540, 1720), ("GND", 540, 1720)]),
        ("P3V3_MSP430", [("U6", "2"), (940, 1490), (1000, 1490), (1080, 1490),
                         ("PORT", 1300, 1490, "P3V3_MSP430  \u2192 faceplate", True)]),
        ("P3V3_MSP430", [("U6", "4"), (940, 1550), (940, 1490)]),
        ("P3V3_MSP430", [(1000, 1490), ("C22", "1")]),
        ("P3V3_MSP430", [(1080, 1490), ("C23", "1")]),
        ("GND",   [("C22", "2"), ("GND", 1000, 1676)]),
        ("GND",   [("C23", "2"), ("GND", 1080, 1676)]),

        # ---- the Daisy's own 3V3, and the I2C pull-ups ----
        ("P3V3_DAISY", [("PORT", 1400, 1300, "P3V3_DAISY  \u2190 Daisy pin A10", False),
                        (1500, 1300), (1580, 1300), (1700, 1300), (1700, 1560), ("R20", "2")]),
        ("P3V3_DAISY", [(1500, 1300), ("C26", "1")]),
        ("P3V3_DAISY", [(1580, 1300), ("C27", "1")]),
        ("P3V3_DAISY", [(1700, 1560), (1700, 1680), ("R21", "2")]),
        ("GND",   [("C26", "2"), ("GND", 1500, 1676)]),
        ("GND",   [("C27", "2"), ("GND", 1580, 1676)]),
        ("I2C_SCL", [("R20", "1"), ("PORT", 2100, 1560, "I2C_SCL  \u2192 U3/U4", True)]),
        ("I2C_SDA", [("R21", "1"), ("PORT", 2100, 1680, "I2C_SDA  \u2192 U3/U4", True)]),
    ]


# declared off-sheet: the right channel's gang, panel mounting lugs, the unused
# throw of the mode switch. Every other pin must be wired or the build fails.
OFF_SHEET = {("RV1", "4"), ("RV1", "5"), ("RV1", "6"), ("RV1", "7"), ("RV1", "8"),
             ("RV2", "4"), ("RV2", "5"), ("RV2", "6"), ("RV2", "7"), ("RV2", "8"),
             ("SW1", "4"), ("SW1", "5"),
             ("RV3", "4"), ("RV3", "5"), ("RV3", "6"), ("RV3", "7"), ("RV3", "8"),
             ("RV4", "4"), ("RV4", "5"), ("RV4", "6"), ("RV4", "7"), ("RV4", "8"),
             ("RV5", "4"), ("RV5", "5"), ("RV5", "6"), ("RV5", "7"), ("RV5", "8"),
             ("RV6", "4"), ("RV6", "5"), ("RV6", "6"), ("RV6", "7"), ("RV6", "8")}


# ------------------------------------------------------------------ build ---

def resolve(wires, T, glyphs):
    """waypoints -> polylines, placing ground/rail/port glyphs as it goes.

    Returns the polylines and the points where a ground or rail symbol attaches.
    Those symbols are connections to a global net, so a net drawn as several
    symbol-terminated pieces is not broken. Ports are not connectors: a port is
    one off-sheet link, and a net drawn in two pieces around one is a bug.
    """
    out, connectors = [], []
    for net, path in wires:
        pts = []
        for wp in path:
            if wp[0] == "GND":
                svg, p = gnd(wp[1], wp[2]); glyphs.append(svg); pts.append(p)
                connectors.append((net, p))
            elif wp[0] == "RAIL":
                svg, p = rail(wp[1], wp[2], wp[3], wp[4]); glyphs.append(svg); pts.append(p)
                connectors.append((net, p))
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
    return out, connectors


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


def continuity(polys, T, netmap, refs, connectors=()):
    """Every wire and pin on a net must form ONE connected thing.

    Without this, a wire can start in mid-air next to the net it belongs to and
    every per-pin check still passes -- which is how U301 pin 12 came to sit on
    a stub that reached nothing.
    """
    bad = []
    nets = collections.defaultdict(list)
    for net, poly in polys:
        for a, b in segments(poly):
            if a != b:
                nets[net].append((a, b))
    pins = collections.defaultdict(list)
    for ref in refs:
        for pin, net in netmap[ref].items():
            if (ref, pin) in OFF_SHEET or ref not in T or pin not in T[ref]:
                continue
            pins[net].append(((ref, pin), T[ref][pin]))
    conn = collections.defaultdict(list)
    for net, pt in connectors:
        conn[net].append(pt)
    for net, segs in nets.items():
        parent = {}
        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        def uni(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        for i, (a, b) in enumerate(segs):
            uni(("s", i), ("p", a)); uni(("s", i), ("p", b))
        for i, (a, b) in enumerate(segs):
            for j, (c, d) in enumerate(segs):
                if i >= j:
                    continue
                for q in (a, b):
                    if on_seg(q, c, d, tol=1.5):
                        uni(("s", i), ("s", j))
                for q in (c, d):
                    if on_seg(q, a, b, tol=1.5):
                        uni(("s", i), ("s", j))
        for (ref, pin), q in pins.get(net, []):
            for i, (a, b) in enumerate(segs):
                if on_seg(q, a, b, tol=1.5):
                    uni(("t", ref, pin), ("s", i))
        groups = collections.defaultdict(list)
        for i, (a, b) in enumerate(segs):
            groups[find(("s", i))].append(f"wire {a}->{b}")
        for (ref, pin), q in pins.get(net, []):
            key = ("t", ref, pin)
            if key in parent:
                groups[find(key)].append(f"{ref}.{pin}")
        if len(groups) > 1 and conn.get(net):
            # every piece that reaches a ground or rail symbol is one net
            joined = [k for k, v in groups.items()
                      if any(any(on_seg(pt, a, b, tol=1.5) for a, b in
                                 [(s[0], s[1]) for i2, s in enumerate(segs) if f"wire {s[0]}->{s[1]}" in v])
                             for pt in conn[net])]
            for k in joined[1:]:
                groups[joined[0]].extend(groups.pop(k))
        if len(groups) > 1:
            pieces = " | ".join(", ".join(sorted(v)[:3]) for v in groups.values())
            bad.append(f"{net} is drawn in {len(groups)} disconnected pieces: {pieces}")
    return bad


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


def text_overlaps(svg):
    """Report label text printed on top of other label text.

    Every other check in this file is about electrical truth. This one is about
    being able to READ the result, which is the whole point of drawing it: a
    wire that is right but illegible has not been checked by anyone.

    The five (bulk cap, 100nF) pairs on the power sheet sat 80px apart with the
    second label flipped back across the first, so "C29 10uF" and "C30 1uF"
    printed one over the other -- two smudges where the two values should be.
    It had been that way since the sheet was first drawn and nothing said so.

    The font is monospace, so a run is len * 0.6 * font-size wide. That is an
    estimate, but it is the same estimate everywhere and the collisions it
    finds are 15px deep. A part's own ref and value sit on consecutive lines
    and graze each other by a pixel at the box edges, which is not a collision
    -- hence the 4px floor on vertical overlap.
    """
    size = {c: int(s) for c, s in re.findall(r'\.([\w-]+)\{[^}]*font-size:(\d+)', STYLE)}
    boxes = []
    for m in re.finditer(r'<text x="([-\d.]+)" y="([-\d.]+)" class="([\w-]+)"([^>]*)>([^<]*)<',
                         svg):
        x, y, cls, rest, txt = (float(m.group(1)), float(m.group(2)),
                                m.group(3), m.group(4), m.group(5))
        if not txt.strip():
            continue
        inline = re.search(r'font-size:(\d+)', rest)
        fs = int(inline.group(1)) if inline else size.get(cls, 16)
        w = len(txt) * fs * 0.60
        anc = re.search(r'text-anchor="(\w+)"', rest)
        a = anc.group(1) if anc else "start"
        x0 = x if a == "start" else (x - w / 2 if a == "middle" else x - w)
        boxes.append((x0, y - fs * 0.76, x0 + w, y + fs * 0.19, txt))
    bad = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 1.0 and oy > 4.0:
                bad.append(f"{a[4]!r} and {b[4]!r} overlap by {ox:.0f}x{oy:.0f}px "
                           f"near x={max(a[0], b[0]):.0f} y={max(a[1], b[1]):.0f}")
    return bad


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
    parts.append(legend(1560, 2000))
    parts.append(f'<rect class="frame" x="18" y="18" width="{w-36}" height="{h-36}"/>')
    parts.append(f'<text class="title" x="46" y="66">{title}</text>')
    parts.append(f'<text class="subtitle" x="46" y="92">{subtitle}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


PAGE = """<title>__PAGETITLE__</title>
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
  #sheet{transform-origin:0 0;width:__W__px}
  #sheet svg{display:block;width:100%;height:auto;
             box-shadow:0 2px 10px rgba(0,0,0,.18);border-radius:3px}
</style>
<header>
  <h1>__TITLE__</h1>
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
    sheet.style.height=(__H__*z)+"px"; sheet.style.width="__W__px";};
  const fit=()=>{z=Math.min(1,(stage.clientWidth-32)/__W__); apply();};
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


def build(slug, title, subtitle, builder, wirer, w, h, pagetitle):
    netmap = json.load(open(f"{KI}/tools/netmap.json"))
    values = json.load(open(f"{KI}/tools/values.json"))
    P, T, glyphs = builder(netmap, values)
    refs = [r for r in T if r in netmap]
    polys, connectors = resolve(wirer(), T, glyphs)
    bad = (check(polys, T, netmap, refs) + wire_shorts(polys)
           + continuity(polys, T, netmap, refs, connectors))
    if bad:
        print(f"{slug}: drawing does not match netmap.json ({len(bad)}):")
        for b in bad:
            print("   ", b)
        sys.exit(1)
    leads, bodies = symbol_geometry(P, T, netmap)
    hits = body_hits(polys, bodies, T)
    if hits:
        print(f"{slug}: wires drawn across component bodies:")
        for h_ in hits:
            print("   ", h_)
        sys.exit(1)
    svg = render(title, subtitle, P, polys, glyphs, w, h, leads)
    smudged = text_overlaps(svg)
    if smudged:
        print(f"{slug}: labels printed over each other ({len(smudged)}):")
        for s_ in smudged:
            print("   ", s_)
        sys.exit(1)
    open(f"{ROOT}/docs/{slug}.svg", "w").write(svg)
    page = (PAGE.replace("<!--SVG-->", svg).replace("__PARTS__", str(len(refs)))
                .replace("__WIRES__", str(len(polys))).replace("__TITLE__", title)
                .replace("__W__", str(w)).replace("__H__", str(h))
                .replace("__PAGETITLE__", pagetitle))
    open(f"{ROOT}/docs/{slug}.html", "w").write(page)
    print(f"{slug}: {len(refs)} parts, {len(polys)} wires, all pins agree with netmap.json")


def main():
    build("sch-lpg-left", "LPG \u2014 left channel",
          "complete: audio path, LED drive and CV chain, drawn from netmap.json "
          "and checked against it \u00b7 compare with Bergman's sheet",
          lpg_left, lpg_left_wires, 2060, 2140, "LPG Left Sheet")
    build("sch-psu", "Power \u2014 USB-C, DKM10, regulators",
          "input, converter, rail filters and the three linear regulators, drawn from "
          "netmap.json and checked against it \u00b7 compare with V3.0.pdf",
          psu, psu_wires, 3000, 1800, "PSU Sheet")
    build("sch-bbd-left", "BBD \u2014 left channel",
          "complete: audio path, sample and hold, mix and CD4046 clock, drawn from "
          "netmap.json and checked against it \u00b7 compare with the mki manual",
          bbd_left, bbd_left_wires, 3200, 2560, "BBD Left Sheet")


if __name__ == "__main__":
    main()
