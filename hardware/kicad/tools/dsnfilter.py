"""
dsnfilter.py -- strip nets and layers out of a Specctra .dsn before autorouting.

KiCad 7 has no autorouter and kicad-cli cannot export DSN, so the loop is:

    Pcbnew  File > Export > Specctra DSN        -> vuulgaris.dsn
    python3 tools/dsnfilter.py vuulgaris.dsn    -> vuulgaris-noGND.dsn
    freerouting                                  -> vuulgaris-noGND.ses
    Pcbnew  File > Import > Specctra Session

Two things get removed by default:

GND.  Dropping (net "/GND" ...) from the network section leaves every ground pad
with no net, so Freerouting treats it as a plain obstacle to keep clear of and
never tries to wire it. Ground then comes from the In2.Cu plane plus stitching
vias placed by hand, which is the point.

In2.Cu.  It is the ground plane, typed `power` in the board. If it stays in the
DSN's layer list the router will happily put signal traces on it and turn the
plane into swiss cheese -- the return path under every sensitive trace, gone.

Parsing is balanced-paren, not regex. A nested (pins ...) list inside (net ...)
is exactly the shape that makes a naive "cut to the next keyword" split eat the
rest of the file.
"""
import sys, os, re

def find_block(text, start):
    """Given the index of a '(', return the index just past its matching ')'."""
    d = 0
    i = start
    while i < len(text):
        if text[i] == '(':
            d += 1
        elif text[i] == ')':
            d -= 1
            if d == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced parentheses at %d" % start)

def drop_nets(dsn, names):
    """Remove (net "NAME" ...) blocks from the network section."""
    dropped = []
    for name in names:
        while True:
            m = re.search(r'\(\s*net\s+"?%s"?[\s)]' % re.escape(name), dsn)
            if not m:
                break
            end = find_block(dsn, m.start())
            dropped.append(name)
            dsn = dsn[:m.start()] + dsn[end:]
    return dsn, dropped

def scrub_classes(dsn, names):
    """Take dropped net names back out of every (class ...) member list.

    A KiCad DSN names every net twice: once as its own (net ...) block and again
    in the class it belongs to. Deleting only the block leaves the class quoting
    a net that no longer exists, and Freerouting either errors or invents an
    empty net for it."""
    hits = 0
    for m in list(re.finditer(r'\(\s*class\s', dsn)):
        pass
    out, i = [], 0
    while True:
        m = re.search(r'\(\s*class\s', dsn[i:])
        if not m:
            out.append(dsn[i:]); break
        st = i + m.start()
        en = find_block(dsn, st)
        blk = dsn[st:en]
        for name in names:
            new = re.sub(r'\s"%s"(?=[\s)])' % re.escape(name), '', blk)
            if new != blk:
                hits += 1
                blk = new
        out.append(dsn[i:st]); out.append(blk)
        i = en
    return "".join(out), hits

def drop_layers(dsn, names):
    """Remove (layer NAME ...) blocks from the structure section."""
    dropped = []
    for name in names:
        while True:
            m = re.search(r'\(\s*layer\s+"?%s"?[\s)]' % re.escape(name), dsn)
            if not m:
                break
            end = find_block(dsn, m.start())
            dropped.append(name)
            dsn = dsn[:m.start()] + dsn[end:]
    return dsn, dropped

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    nets = sys.argv[2].split(",") if len(sys.argv) > 2 else ["/GND", "GND"]
    layers = sys.argv[3].split(",") if len(sys.argv) > 3 else ["In2.Cu"]
    dsn = open(src).read()
    before = len(re.findall(r'\(\s*net\s+"', dsn))
    dsn, dn = drop_nets(dsn, nets)
    dsn, ch = scrub_classes(dsn, nets)
    dsn, dl = drop_layers(dsn, layers)
    after = len(re.findall(r'\(\s*net\s+"', dsn))
    out = os.path.splitext(src)[0] + "-noGND.dsn"
    open(out, "w").write(dsn)
    print(f"in  : {src}")
    print(f"out : {out}")
    print(f"nets   {before} -> {after}   dropped: {dn or 'none (check the name!)'}")
    print(f"class references scrubbed: {ch}")
    print(f"layers dropped: {dl or 'none (check the name!)'}")
    if not dn:
        print("\nNOTHING WAS DROPPED. Open the .dsn and look at how the net is")
        print("actually spelled -- KiCad writes the leading slash, so it is")
        print('usually "/GND". Pass it explicitly:')
        print(f"   python3 tools/dsnfilter.py {src} '/GND' In2.Cu")

if __name__ == "__main__":
    main()
