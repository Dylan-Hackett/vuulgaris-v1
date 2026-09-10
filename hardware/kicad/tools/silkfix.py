"""
silkfix.py -- move reference designators off copper and off each other.

Silk that lands on a solder-mask opening is clipped away by the fab. On a
footprint outline crossing its own pads that is normal and everyone ships it.
On a REFERENCE DESIGNATOR it means the label you read at the bench comes out
chopped, which is the one silk problem worth spending time on.

    python3 tools/silkfix.py --check     report what it would move
    python3 tools/silkfix.py             move them

Only the reference text is touched, and only its position within its own
footprint -- no part moves, no copper changes, so this cannot affect
connectivity. A designator is moved only if its current spot is bad AND a
better one is found; anything that cannot be improved is left where it is and
named.

The text box is deliberately over-estimated (0.75 * size per character plus the
stroke thickness, and the full height plus thickness) so a near miss counts as a
hit. Better to move one that did not strictly need it than to leave one clipped.
"""
import re, sys, math

KI  = "/Users/dylanhackett/V1/hardware/kicad"
PCB = f"{KI}/vuulgaris.kicad_pcb"
CHECK = "--check" in sys.argv
CLEAR = 0.15          # silk-to-mask clearance this board is set to

def blocks(text):
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
        yield st, j + 1, text[st:j + 1]
        pos = j + 1

def xf(ax, ay, ang):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return lambda lx, ly: (ax + lx * ca + ly * sa, ay - lx * sa + ly * ca)

def textbox(s, cx, cy, sx, sy, th, ang=0.0):
    """Conservative extent of a stroke-font string.

    0.75 * size per character was too narrow -- KiCad's glyph cell is about a
    full size.x wide including inter-character spacing, and at 0.75 the tool
    declared pairs clear that DRC then flagged. Rotation is honoured because a
    designator turned 90 degrees is tall, not wide."""
    w = len(s) * sx + th
    h = sy + th
    if abs((ang % 180) - 90) < 45:
        w, h = h, w
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

def gap(A, B):
    return math.hypot(max(A[0]-B[2], B[0]-A[2], 0.0), max(A[1]-B[3], B[1]-A[3], 0.0))

def parse(text):
    """Pads, silk graphics, visible value text, and reference texts."""
    pads, refs, graphics, fixedtext = [], [], [], []
    for st, en, blk in blocks(text):
        a = re.search(r'\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)', blk)
        L = re.match(r'\(footprint "[^"]*" \(layer "([^"]+)"', blk)
        side = L.group(1) if L else "F.Cu"
        rm = re.search(r'\(fp_text reference "([^"]+)"', blk)
        if not (a and rm):
            continue
        ref = rm.group(1)
        ax, ay = float(a.group(1)), float(a.group(2))
        ang = float(a.group(3)) if a.group(3) else 0.0
        place = xf(ax, ay, ang)
        pi = 0
        while True:
            pm = re.compile(r'\(pad ').search(blk, pi)
            if not pm: break
            pst = pm.start(); d = 0; pj = pst
            while pj < len(blk):
                if blk[pj] == '(': d += 1
                elif blk[pj] == ')':
                    d -= 1
                    if d == 0: break
                pj += 1
            pb = blk[pst:pj + 1]; pi = pj + 1
            p = re.match(r'\(pad "?[^"\s]*"? (\w+) \w+ \(at ([-\d.]+) ([-\d.]+)[^)]*\)'
                         r' \(size ([\d.]+) ([\d.]+)\)', pb)
            if not p: continue
            px, py, sw, sh = map(float, p.groups()[1:5])
            prim = [(float(u), float(v)) for u, v in
                    re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', pb)]
            if prim:
                w_ = re.search(r'\(width ([\d.]+)\)', pb)
                w_ = float(w_.group(1)) if w_ else 0.0
                xs_ = [q[0] for q in prim]; ys_ = [q[1] for q in prim]
                sw = max(sw, max(xs_) - min(xs_) + w_)
                sh = max(sh, max(ys_) - min(ys_) + w_)
            cs = [place(u, v) for u in (px - sw/2, px + sw/2) for v in (py - sh/2, py + sh/2)]
            xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
            th_ = p.group(1).endswith("thru_hole")
            pads.append(((min(xs), min(ys), max(xs), max(ys)), side, th_))
        for gm in re.finditer(r'\(fp_(line|circle|arc) \(start ([-\d.]+) ([-\d.]+)\)'
                              r'(?:.|\n){0,120}?\(layer "([FB])\.SilkS"\)', blk):
            pass
        for gm in re.finditer(r'\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                              r'(?:.|\n){0,160}?\(layer "([FB])\.SilkS"\)', blk):
            g = list(map(float, gm.groups()[:4]))
            P = [place(g[0], g[1]), place(g[2], g[3])]
            xs_ = [q[0] for q in P]; ys_ = [q[1] for q in P]
            graphics.append(((min(xs_)-0.08, min(ys_)-0.08, max(xs_)+0.08, max(ys_)+0.08),
                             gm.group(5) + ".SilkS"))
        for gm in re.finditer(r'\(fp_circle \(center ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                              r'(?:.|\n){0,160}?\(layer "([FB])\.SilkS"\)', blk):
            g = list(map(float, gm.groups()[:4]))
            rr = math.hypot(g[2]-g[0], g[3]-g[1])
            P = [place(g[0]-rr, g[1]-rr), place(g[0]+rr, g[1]+rr),
                 place(g[0]-rr, g[1]+rr), place(g[0]+rr, g[1]-rr)]
            xs_ = [q[0] for q in P]; ys_ = [q[1] for q in P]
            graphics.append(((min(xs_), min(ys_), max(xs_), max(ys_)), gm.group(5) + ".SilkS"))
        for gm in re.finditer(r'\(fp_arc \(start ([-\d.]+) ([-\d.]+)\) \(mid ([-\d.]+) ([-\d.]+)\)'
                              r' \(end ([-\d.]+) ([-\d.]+)\)(?:.|\n){0,160}?\(layer "([FB])\.SilkS"\)', blk):
            g = list(map(float, gm.groups()[:6]))
            P = [place(g[0], g[1]), place(g[2], g[3]), place(g[4], g[5])]
            xs_ = [q[0] for q in P]; ys_ = [q[1] for q in P]
            graphics.append(((min(xs_)-0.08, min(ys_)-0.08, max(xs_)+0.08, max(ys_)+0.08),
                             gm.group(7) + ".SilkS"))
        vm = re.search(r'\(fp_text value "([^"]+)" \(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)'
                       r' \(layer "([FB]\.SilkS)"\)(?! hide)\s*\n?\s*\(effects \(font'
                       r' \(size ([\d.]+) ([\d.]+)\) \(thickness ([\d.]+)\)\)', blk)
        if vm:
            vx, vy = place(float(vm.group(2)), float(vm.group(3)))
            fixedtext.append((textbox(vm.group(1), vx, vy, float(vm.group(6)),
                                      float(vm.group(7)), float(vm.group(8)),
                                      float(vm.group(4) or 0)), vm.group(5)))
        tm = re.search(r'\(fp_text reference "([^"]+)" \(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)'
                       r' \(layer "([^"]+)"\)\s*\n?\s*\(effects \(font \(size ([\d.]+) ([\d.]+)\)'
                       r' \(thickness ([\d.]+)\)\)', blk)
        if tm:
            refs.append(dict(ref=ref, st=st, en=en, blk=blk, side=side, place=place,
                             lx=float(tm.group(2)), ly=float(tm.group(3)),
                             sx=float(tm.group(6)), sy=float(tm.group(7)),
                             th=float(tm.group(8)), silk=tm.group(5),
                             tang=float(tm.group(4) or 0)))
    return pads, refs, graphics, fixedtext

def main():
    text = open(PCB).read()
    pads, refs, graphics, fixedtext = parse(text)
    boxes = {}
    for r in refs:
        cx, cy = r["place"](r["lx"], r["ly"])
        boxes[r["ref"]] = (textbox(r["ref"], cx, cy, r["sx"], r["sy"], r["th"], r["tang"]), r["silk"])

    def bad(ref, box, silk, skip_self=True):
        side = "F.Cu" if silk.startswith("F") else "B.Cu"
        for prect, pside, pth in pads:
            if not (pside == side or pth):
                continue
            if gap(box, prect) < CLEAR:
                return True
        for other, (obox, osilk) in boxes.items():
            if other == ref or osilk != silk:
                continue
            if gap(box, obox) < CLEAR:
                return True
        for obox, osilk in fixedtext:
            if osilk == silk and gap(box, obox) < CLEAR:
                return True
        for gbox, gsilk in graphics:
            if gsilk == silk and gap(box, gbox) < CLEAR:
                return True
        return False

    moved, stuck, fine = [], [], 0
    for r in refs:
        cx, cy = r["place"](r["lx"], r["ly"])
        box = textbox(r["ref"], cx, cy, r["sx"], r["sy"], r["th"], r["tang"])
        if not bad(r["ref"], box, r["silk"]):
            fine += 1
            continue
        best = None
        for d in [x / 4.0 for x in range(4, 41)]:          # 1.0mm out to 10mm
            for adeg in range(0, 360, 15):
                nx = cx + d * math.cos(math.radians(adeg))
                ny = cy + d * math.sin(math.radians(adeg))
                nb = textbox(r["ref"], nx, ny, r["sx"], r["sy"], r["th"], r["tang"])
                if not bad(r["ref"], nb, r["silk"]):
                    best = (nx, ny, d, nb); break
            if best: break
        if not best:
            stuck.append(r["ref"]); continue
        nx, ny, d, nb = best
        boxes[r["ref"]] = (nb, r["silk"])
        moved.append((r, nx, ny, d))

    print(f"reference designators : {len(refs)}")
    print(f"  already clear       : {fine}")
    print(f"  moved               : {len(moved)}")
    print(f"  no clear spot found : {len(stuck)}  {stuck if stuck else ''}")
    if moved:
        dd = [m[3] for m in moved]
        print(f"  distance moved      : min {min(dd):.2f}  mean {sum(dd)/len(dd):.2f}  max {max(dd):.2f} mm")
    if CHECK:
        print("\nMODE: --check, nothing written")
        return
    if not moved:
        return
    # write new local coordinates back, footprint by footprint, last first
    out = text
    for r, nx, ny, d in sorted(moved, key=lambda z: -z[0]["st"]):
        ca = math.cos(math.radians(0))
        # invert the footprint transform to get local coords
        a = re.search(r'\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)', r["blk"])
        ax, ay = float(a.group(1)), float(a.group(2))
        ang = float(a.group(3)) if a.group(3) else 0.0
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        dx, dy = nx - ax, ny - ay
        lx =  dx * c - dy * s
        ly =  dx * s + dy * c
        nb = re.sub(r'(\(fp_text reference "%s" \(at )[-\d.]+ [-\d.]+' % re.escape(r["ref"]),
                    r'\g<1>%.4f %.4f' % (lx, ly), r["blk"], count=1)
        out = out[:r["st"]] + nb + out[r["en"]:]
    open(PCB, "w").write(out)
    print(f"\nwrote {len(moved)} new designator positions")

if __name__ == "__main__":
    main()
