"""
pose.py -- restore footprint LAYER and ROTATION after Pcbnew clobbers them.

place.py owns X/Y.  It does not own which side a part is on or how it is turned,
because those live only in the board file -- so every "Update PCB from Schematic"
(F8) that re-imports a footprint drops it back on F.Cu at 0 degrees, and the work
of flipping the whole analog block to the back is gone.  That has now happened
three times: the bypass caps, then the entire headphone block, twice.

    python3 tools/pose.py --save     snapshot the board's current poses
    python3 tools/pose.py --check    report what differs, write nothing
    python3 tools/pose.py            put every part back the way pose.json says

Order after an F8 is:  place.py  ->  pose.py  ->  place.py --check

Rotation carries the pad angles with it.  A pad angle in the file is absolute, so
turning a footprint means rewriting all of them; the relative angle is recovered
from the board's own current pose, not from the library, because the library lookup
is keyed on coordinates that do not always match and a miss there invents a rotation
out of nothing.  Circles are skipped -- rotating a circle means nothing.

Verify with place.py --check, whose "pad orientation vs library" pass is the
independent authority on whether the angles came out right.
"""
import re, sys, json, os, math

KI   = "/Users/dylanhackett/V1/hardware/kicad"
PCB  = f"{KI}/vuulgaris.kicad_pcb"
POSE = f"{KI}/tools/pose.json"

SAVE  = "--save"  in sys.argv
CHECK = "--check" in sys.argv

FRONT = ["F.Cu", "F.SilkS", "F.CrtYd", "F.Fab", "F.Adhes", "F.Paste", "F.Mask"]

def blocks(text):
    """Yield (ref, start, end, block) with the block ended at its BALANCED
    closing paren.

    It used to end each block where the next footprint began, with len(text) as
    the final sentinel -- which made the LAST footprint's "block" run to end of
    file and swallow everything after it: Edge.Cuts, the zone, the lot. The
    mirror transform then negated Y on the board outline, and the faceplate
    connector cutout came apart. The gr_arc corners survived only because the
    regex wanted (start ...) (end ...) adjacent and an arc carries a (mid ...)
    between them, which is the sort of luck that hides a bug rather than
    revealing it. place.py's fp_blocks had this right all along."""
    pos = 0
    while True:
        m = re.compile(r'\(footprint "').search(text, pos)
        if not m:
            return
        start = m.start()
        d, j = 0, start
        while j < len(text):
            if text[j] == '(':
                d += 1
            elif text[j] == ')':
                d -= 1
                if d == 0:
                    break
            j += 1
        blk = text[start:j + 1]
        pos = j + 1
        r = re.search(r'\(fp_text reference "([^"]+)"', blk)
        yield (r.group(1) if r else None), start, j + 1, blk

def layer_of(blk):
    m = re.match(r'\(footprint "[^"]*" \(layer "([^"]+)"', blk)
    return m.group(1) if m else "F.Cu"

def rot_of(blk):
    m = re.search(r'\n\s*\(at [-\d.]+ [-\d.]+(?: ([-\d.]+))?\)', blk)
    return float(m.group(1)) if (m and m.group(1)) else 0.0

# --------------------------------------------------------------- mirror
def mirror(blk, to_back):
    """Reflect a footprint block across its own X axis and swap F.* <-> B.*.

    An involution: applying it twice is the identity, so the same code flips
    both directions.  Only the layer-name swap has a direction."""
    own = re.search(r'\n\s*\(at [-\d.]+ [-\d.]+(?: [-\d.]+)?\)', blk)
    head, tail = blk[:own.end()], blk[own.end():]

    a, b = ("F.", "B.") if to_back else ("B.", "F.")
    head = head.replace('(layer "%sCu")' % a, '(layer "%sCu")' % b, 1)
    for L in FRONT:
        suf = L[2:]
        tail = tail.replace('(layer "%s%s")' % (a, suf), '(layer "%s%s")' % (b, suf))
    tail = tail.replace('(layers "%sCu" "%sPaste" "%sMask")' % (a, a, a),
                        '(layers "%sCu" "%sPaste" "%sMask")' % (b, b, b))
    tail = tail.replace('(layers "%sCu" "%sMask")' % (a, a),
                        '(layers "%sCu" "%sMask")' % (b, b))

    neg = lambda s: ('%g' % -float(s))
    tail = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+)\)',
                  lambda m: '(at %s %s)' % (m.group(1), neg(m.group(2))), tail)
    tail = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)\)',
                  lambda m: '(at %s %s %s)' % (m.group(1), neg(m.group(2)), m.group(3)), tail)
    tail = re.sub(r'\(start (-?[\d.]+) (-?[\d.]+)\) \(end (-?[\d.]+) (-?[\d.]+)\)',
                  lambda m: '(start %s %s) (end %s %s)' % (m.group(1), neg(m.group(2)),
                                                           m.group(3), neg(m.group(4))), tail)
    tail = re.sub(r'\(center (-?[\d.]+) (-?[\d.]+)\) \(end (-?[\d.]+) (-?[\d.]+)\)',
                  lambda m: '(center %s %s) (end %s %s)' % (m.group(1), neg(m.group(2)),
                                                            m.group(3), neg(m.group(4))), tail)
    # back-side text reads mirrored; front-side text must not
    if to_back:
        tail = re.sub(r'\(effects \(font \(size ([\d.]+) ([\d.]+)\) \(thickness ([\d.]+)\)\)\)',
                      r'(effects (font (size \1 \2) (thickness \3)) (justify mirror))', tail)
    else:
        tail = tail.replace(') (justify mirror))', '))')
    return head + tail

# --------------------------------------------------------------- rotate
def set_rot(blk, rot0, onback0, rot1, onback1):
    """Set the footprint angle and carry every pad angle with it.

    The pad angle in the file is ABSOLUTE -- the footprint rotation is already
    folded in, which is why turning a footprint means rewriting all of them.  The
    relative angle is recovered from the board rather than from the library: the
    board is self-consistent by construction, the library lookup is keyed on pad
    coordinates that do not always match, and a miss there silently invents a
    rotation.  That is what put 270 on J9's oval pads, which carry none.

    Mirroring negates the relative angle, so the sign flips with the side.  A pad
    with no angle field is angle 0; if the arithmetic lands back on 0 the field
    stays off, which makes a pose->clobber->pose round trip byte-exact.

    The footprint angle is written back verbatim, not normalised into [0,360).
    KiCad stores -90, and rewriting it as 270 is a no-op that shows up as a diff
    on every part it touches.
    """
    blk = re.sub(r'(\n\s*\(at )(-?[\d.]+) (-?[\d.]+)(?: -?[\d.]+)?(\))',
                 lambda m: m.group(1) + m.group(2) + ' ' + m.group(3) +
                           ('' if rot1 % 360 == 0 else ' %g' % rot1) + m.group(4),
                 blk, count=1)

    def padfix(m):
        head, num, typ, shape, x, y, ang = m.groups()
        if shape == "circle":
            return m.group(0)
        cur = float(ang) if ang else 0.0
        rel = (cur - rot0) * (-1 if onback0 else 1)
        a = (rot1 + (-rel if onback1 else rel)) % 360.0
        tail = '' if min(a, 360.0 - a) < 1e-6 else ' %g' % a
        return '%s"%s" %s %s (at %s %s%s)' % (head, num, typ, shape, x, y, tail)

    return re.sub(r'(\(pad )"([^"]*)" (\w+) (\w+) \(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)',
                  padfix, blk)

# --------------------------------------------------------------- main
src = open(PCB).read()

if SAVE:
    snap = {}
    for ref, a, b, blk in blocks(src):
        if ref:
            snap[ref] = [layer_of(blk), rot_of(blk)]
    json.dump(dict(sorted(snap.items())), open(POSE, "w"), indent=1)
    nd = sum(1 for v in snap.values() if v[0] != "F.Cu" or v[1])
    print(f"saved {len(snap)} poses to tools/pose.json  ({nd} not F.Cu/0)")
    sys.exit(0)

if not os.path.exists(POSE):
    sys.exit("no pose.json -- run  python3 tools/pose.py --save  first")
want_pose = json.load(open(POSE))

out, pos, log, missing = [], 0, [], []
for ref, a, b, blk in blocks(src):
    out.append(src[pos:a]); pos = b
    if ref not in want_pose:
        if ref:
            missing.append(ref)
        out.append(blk); continue
    wlay, wrot = want_pose[ref]
    cur_lay, cur_rot = layer_of(blk), rot_of(blk)
    back0, back1 = cur_lay != "F.Cu", wlay != "F.Cu"
    turned = abs((cur_rot - wrot + 180) % 360 - 180) > 0.01
    if back0 != back1:
        blk = mirror(blk, back1)
        log.append(f"{ref}:{'flip->B' if back1 else 'flip->F'}")
    if turned:
        log.append(f"{ref}:rot{wrot:g}")
    if turned or back0 != back1:
        # mirror() moves geometry; the pad ANGLES are absolute and are settled here
        blk = set_rot(blk, cur_rot, back0, wrot, back1)
    out.append(blk)
out.append(src[pos:])

if CHECK:
    print("MODE: --check, nothing written")
print(f"poses in pose.json : {len(want_pose)}")
print(f"restored           : {len(log)}  {log if log else ''}")
if missing:
    print(f"NOT in pose.json   : {missing}   <- run --save once they are posed")
if log and not CHECK:
    open(PCB, "w").write("".join(out))
