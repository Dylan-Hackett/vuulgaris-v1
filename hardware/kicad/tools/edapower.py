#!/usr/bin/env python3
"""Read the USB-C power stage out of the EasyEDA project, as data.

The point of choosing this circuit over the barrel one was that it has been
built and works. That argument only holds if what is in netmap.json is what is
on that board -- so this reads it rather than trusting a transcription. The
first hand-typed version had nine two-terminal parts with pins 1 and 2 swapped;
harmless, all non-polar, but not what was claimed.

An .eprj is a SQLite database. documents.dataStr is base64 (with a literal
"base64" prefix) wrapping gzip. The PCB document stores PAD_NET records --
component id, pad number, net -- which is EasyEDA's OWN resolved connectivity
for the board that was routed, not a re-reading of the schematic drawing.

    python3 tools/edapower.py            # check netmap.json against the board
    python3 tools/edapower.py --write    # rewrite the power block from it

Nothing else in the repo depends on the .eprj; if it moves, only this breaks.
"""
import sqlite3, gzip, base64, zlib, json, re, sys, os, collections

EPRJ = os.path.expanduser("~/Documents/origin2.2.eprj")
DOC = "postpcb"
KI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_PATH = f"{KI}/tools/netmap.json"

# EasyEDA designator -> ours. Odd-numbered rail parts are +12V, even are -12V,
# which is why L1/L2 come across swapped.
REF = {"USBC1": "J11", "F1": "F1", "C105": "C28", "R438": "R22", "R439": "R23",
       "C81": "C29", "C82": "C30", "C100": "C31", "U44": "U7",
       "U50": "C32", "U49": "C33", "C102": "C34", "C104": "C35",
       "L2": "L1", "L1": "L2", "C110": "C36", "C111": "C37",
       "C113": "C38", "C112": "C39", "R440": "R24", "R441": "R25",
       "LED20": "D1", "U43": "D2"}

# EasyEDA net -> ours. The $1N... names are auto-generated: those nodes were
# never labelled, so the names carry no meaning and are assigned here by role.
NET = {"DKM5V": "VBUS", "$1N339035": "VBUS_F",
       "$1N364806": "POS12V_RAW", "$1N362061": "NEG12V_RAW",
       "V+": "POS12V", "VEE": "NEG12V",
       "$1N338891": "CC1", "$1N338930": "CC2",
       "$1N339498": "LED_POS", "$1N339496": "LED_NEG", "GND": "GND"}


def decode(s):
    s = re.sub(r"^\s*base64\s*", "", s)
    b = base64.b64decode(s)
    for fn in (gzip.decompress, zlib.decompress, lambda x: zlib.decompress(x, -15)):
        try:
            return fn(b).decode("utf8", "replace")
        except Exception:
            pass
    return b.decode("utf8", "replace")


def extract(path=EPRJ, doc=DOC):
    """-> {our_ref: {pad: our_net}} for the power block."""
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    row = db.execute("select dataStr from documents where docType=3 and title=?",
                     (doc,)).fetchone()
    if not row:
        sys.exit(f"no PCB document named {doc!r} in {path}")
    desig, padnet = {}, collections.defaultdict(dict)
    for line in decode(row[0]).split("\n"):
        line = line.strip().rstrip(",")
        if not line.startswith("["):
            continue
        try:
            a = json.loads(line)
        except Exception:
            continue
        if a[0] == "ATTR" and len(a) > 8 and a[7] == "Designator":
            desig[a[3]] = a[8]
        elif a[0] == "PAD_NET":
            padnet[a[1]][str(a[2])] = a[3]
    out = {}
    for cid, pads in padnet.items():
        r = REF.get(desig.get(cid))
        if not r:
            continue
        out[r] = {pad: NET[n] for pad, n in sorted(pads.items()) if n}
    missing = set(REF.values()) - set(out)
    if missing:
        sys.exit(f"not found on the board: {sorted(missing)}")
    return out


def main():
    board = extract()
    m = json.load(open(MAP_PATH))
    diff = []
    n = 0
    for ref, pads in sorted(board.items()):
        for pad in sorted(set(pads) | set(m.get(ref, {}))):
            n += 1
            a, b = m.get(ref, {}).get(pad), pads.get(pad)
            if a != b:
                diff.append(f"  {ref}.{pad}: netmap {a!r}, board {b!r}")
    if "--write" in sys.argv:
        m.update(board)
        json.dump(collections.OrderedDict(
            sorted(m.items(), key=lambda kv: (kv[0][0], len(kv[0]), kv[0]))),
            open(MAP_PATH, "w"), indent=1)
        open(MAP_PATH, "a").write("\n")
        print(f"wrote {len(board)} parts, {sum(len(v) for v in board.values())} "
              f"pin-nets into netmap.json ({len(diff)} changed)")
        return 0
    print("\n".join(diff))
    print(f"\n{n - len(diff)}/{n} pin-nets match the EasyEDA board"
          + ("" if not diff else f"   {len(diff)} DIFFER"))
    return 1 if diff else 0


if __name__ == "__main__":
    sys.exit(main())
