#!/usr/bin/env python3
"""Prove the right channel is the left channel, pin for pin.

    python3 tools/mirrorcheck.py

Both stereo blocks are drawn once and duplicated by hand in netmap.json, so a
one-channel typo is invisible to every other check: the schematic matches the
netlist, the board matches the schematic, and one channel is quietly wrong.

This maps 3xx -> 4xx and 1xx -> 2xx, maps every net's _L suffix to _R, and
compares. The panel pots and the mode switch are single parts with a gang per
channel, so their pins 1-3 are compared against 4-6.

What it does NOT prove: that either channel is right. A value wrong in both
channels mirrors perfectly -- RV1-RV6 are 10k in both and both are wrong.
"""
import json, re, os, sys

KI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# a shared part's left-gang pin -> its right-gang pin
GANGS = {"RV1": {"1": "4", "2": "5", "3": "6"},
         "RV2": {"1": "4", "2": "5", "3": "6"},
         "RV3": {"1": "4", "2": "5", "3": "6"},
         "RV4": {"1": "4", "2": "5", "3": "6"},
         "RV5": {"1": "4", "2": "5", "3": "6"},
         "RV6": {"1": "4", "2": "5", "3": "6"},
         "SW1": {"1": "4", "2": "5", "3": "6"},
         "SW2": {"1": "4", "2": "5", "3": "6"}}

BLOCKS = [("LPG", "3", "4"), ("BBD", "1", "2")]


def mirror_net(n):
    return n[:-2] + "_R" if n.endswith("_L") else n


def main():
    netmap = json.load(open(f"{KI}/tools/netmap.json"))
    values = json.load(open(f"{KI}/tools/values.json"))
    bad, checked, pairs = [], 0, 0

    for name, left, right in BLOCKS:
        for r, pins in sorted(netmap.items()):
            m = re.match(r"([A-Z]+)(\d)(\d\d)$", r)
            if not m or m.group(2) != left:
                continue
            mr = f"{m.group(1)}{right}{m.group(3)}"
            if mr not in netmap:
                bad.append(f"[{name}] {r} has no counterpart {mr}")
                continue
            pairs += 1
            if values.get(r) != values.get(mr):
                bad.append(f"[{name}] {r} is {values.get(r)!r}, {mr} is {values.get(mr)!r}")
            for pin, net in pins.items():
                checked += 1
                want, got = mirror_net(net), netmap[mr].get(pin)
                if got != want:
                    bad.append(f"[{name}] {r}.{pin} is {net}; {mr}.{pin} should be "
                               f"{want} but is {got}")

    for ref, gang in GANGS.items():
        if ref not in netmap:
            continue
        for lp, rp in gang.items():
            if lp not in netmap[ref]:
                continue
            checked += 1
            want, got = mirror_net(netmap[ref][lp]), netmap[ref].get(rp)
            if got != want:
                bad.append(f"[gang] {ref}.{lp} is {netmap[ref][lp]}; pin {rp} should be "
                           f"{want} but is {got}")

    print(f"{pairs} mirrored parts, {checked} pins compared")
    if bad:
        print(f"{len(bad)} differences:")
        for b in bad:
            print("   ", b)
        sys.exit(1)
    print("both channels are identical")


if __name__ == "__main__":
    main()
