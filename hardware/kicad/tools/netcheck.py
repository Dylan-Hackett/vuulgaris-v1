#!/usr/bin/env python3
"""Diff the generated schematic against tools/netmap.json, using KiCad's netlister.

netmap.json is the INTENT: every (ref, pin) that is supposed to carry a net.
This exports the netlist with kicad-cli -- KiCad's own code, not a reimplementation
of it -- and reports three things:

    MISMATCH    a pin we intended is on the wrong net, or on none
    UNINTENDED  a pin KiCad bound to a real net that netmap.json never asked for
    (silence)   everything agrees

The UNINTENDED half is the one that matters. The EasyEDA board this project came
from had P3V3_DAISY shorted to I2C_SDA across nine pads, and no ERC anywhere will
flag that, because a short between two real nets is an electrically legal
connection. It is only visible by diffing against a declared intent.

Run after every mksch.py.
"""
import re, sys, os, json, subprocess, tempfile, collections

KI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = f"{KI}/vuulgaris.kicad_sch"
MAP = f"{KI}/tools/netmap.json"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


def export():
    fd, path = tempfile.mkstemp(suffix=".net")
    os.close(fd)
    r = subprocess.run([CLI, "sch", "export", "netlist", "--output", path, SCH],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr.strip() or r.stdout.strip() or "netlist export failed")
    return path


def parse(path):
    """-> {ref: {pin: net}}.  Net names are stripped of the sheet prefix."""
    s = open(path).read()
    out = collections.defaultdict(dict)
    net = None
    for line in s.split("\n"):
        m = re.search(r'\(net \(code "\d+"\) \(name "([^"]+)"\)', line)
        if m:
            net = m.group(1).lstrip("/")
        for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', line):
            out[r][p] = net
    return out


def main():
    path = export()
    try:
        got = parse(path)
    finally:
        os.unlink(path)
    want = json.load(open(MAP))

    bad = []
    n = 0
    for ref, pins in want.items():
        for pin, net in pins.items():
            n += 1
            g = got.get(ref, {}).get(pin)
            if g != net:
                bad.append(f"MISMATCH   {ref}.{pin}: want {net!r}, got {g!r}")
    extra = [f"UNINTENDED {r}.{p} -> {nt}"
             for r, ps in got.items() for p, nt in ps.items()
             if p not in want.get(r, {}) and nt and not nt.startswith("unconnected-")]

    for line in bad + extra:
        print("  " + line)
    print(f"\n{n - len(bad)}/{n} connections verified"
          f"   {len(extra)} unintended"
          f"   {len({v for p in want.values() for v in p.values()})} nets")
    return 1 if bad or extra else 0


if __name__ == "__main__":
    sys.exit(main())
