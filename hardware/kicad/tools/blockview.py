#!/usr/bin/env python3
"""Draw netmap.json as one readable diagram per circuit block.

    python3 tools/blockview.py          # -> docs/blockview.html

The schematic KiCad holds is a stub and a net label on every one of 942 pins.
It is correct and it is unreadable, so nobody can check it against Bergman's
drawing or the mki manual by eye -- which is exactly how the LED drive and the
input stage shipped inverted. This renders the same data as a graph per block:
nets are nodes, two-pin parts are labelled edges, op-amp sections are boxes with
their pin names on the edges. Rails get a leaf node per connection so GND does
not collapse the whole drawing into a hub.

It reads netmap.json, so it shows what the board was built from -- not what the
documentation claims. That is the point.
"""
import json, re, os, html, collections

KI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(KI))
OUT = f"{ROOT}/docs/blockview.html"

RAIL = re.compile(r'^(GND|POS12V|NEG12V|P5V|P3V3|VBUS|VDD|VSS)')

BLOCKS = [
    ("lpg-l", "LPG left",  "Bergman Buchla 292, left channel",
     "datasheets/LPG Schematic E Bergman (3) (1).jpg", lambda r, n: n and 300 <= n < 400),
    ("lpg-r", "LPG right", "Bergman Buchla 292, right channel",
     "datasheets/LPG Schematic E Bergman (3) (1).jpg", lambda r, n: n and 400 <= n < 500),
    ("bbd-l", "BBD left",  "mki x es.edu BBD delay, left channel",
     "datasheets/BBD-mki-manual-250228.pdf", lambda r, n: n and 100 <= n < 200),
    ("bbd-r", "BBD right", "mki x es.edu BBD delay, right channel",
     "datasheets/BBD-mki-manual-250228.pdf", lambda r, n: n and 200 <= n < 300),
    ("out",   "Output stage", "Headphone, line out and EXT in, both channels",
     "OPA1688 datasheet", lambda r, n: (n and 500 <= n < 600) or r in ("U9", "U10")
                                        or r in ("J6", "J7", "J8", "J9", "J10")),
    ("psu",   "Power",    "USB-C in, DKM10 converter, the three regulators",
     "datasheets/V3.0.pdf", lambda r, n: (n is not None and n < 100 and r[0] in "RCLFD")
                                          or r in ("U5", "U6", "U7", "U8", "J11", "FB1", "FB2",
                                                   "Q1", "Q2")),
    ("io",    "Control IO", "Daisy, port expanders, encoders, buttons, display, card",
     "docs/pin-allocation.md", lambda r, n: r in ("U1", "U3", "U4", "J1", "J12", "DS1",
                                                 "J2", "J3", "J4", "J5")
                                             or r.startswith(("ENC", "SW", "RV", "TP"))),
]


def load():
    j = lambda f: json.load(open(f"{KI}/tools/{f}"))
    return j("netmap.json"), j("values.json"), j("kpins.json")


def symbols():
    """ref -> symbol name, straight out of the generated schematic."""
    t = open(f"{KI}/vuulgaris.kicad_sch").read()
    out = {}
    for m in re.finditer(r'\(lib_id "([^"]+)"\)', t):
        lib = m.group(1).split(":")[-1]
        nxt = t.find('(property "Reference" "', m.start())
        out[re.match(r'\(property "Reference" "([^"]+)"', t[nxt:]).group(1)] = lib
    return out


def section_of(pin_name):
    """('B', '-') for IN_B-, ('1', 'out') for 1OUT. None if not an op-amp pin."""
    m = re.match(r'(IN|OUT)_?([A-D])([+-])?$', pin_name)
    if m:
        return m.group(2), ("out" if m.group(1) == "OUT" else m.group(3))
    m = re.match(r'([1-4])(IN|OUT)([+-])?$', pin_name)
    if m:
        return m.group(1), ("out" if m.group(2) == "OUT" else m.group(3))
    return None


def mermaid(refs, netmap, values, kpins, syms):
    """flowchart source for one block."""
    lines = ["flowchart LR"]
    nets = collections.defaultdict(list)
    for r in refs:
        for p, n in netmap[r].items():
            nets[n].append((r, p))
    seen_net, rails, edges = set(), 0, []

    def nid(n):
        return "n_" + re.sub(r'\W', '_', n)

    def net_node(n):
        if n not in seen_net:
            seen_net.add(n)
            lines.append(f'  {nid(n)}(["{n}"])')
        return nid(n)

    def rail_node(n, tag):
        nonlocal rails
        rails += 1
        i = f"r{rails}"
        lines.append(f'  {i}[/"{n}"/]')
        lines.append(f'  class {i} rail')
        return i

    def endpoint(n, tag):
        return rail_node(n, tag) if RAIL.match(n) else net_node(n)

    for r in sorted(refs, key=lambda x: (x[0], int(re.sub(r'\D', '', x) or 0))):
        pins = netmap[r]
        sym = syms.get(r, "")
        names = {p: kpins.get(sym, {}).get(p, {}).get("name", p) for p in pins}
        val = values.get(r, "")
        secs = collections.defaultdict(dict)
        for p, name in names.items():
            s = section_of(name)
            if s:
                secs[s[0]][s[1]] = p
        if len(pins) == 2 and not secs:                      # R, C, L, D, switch leg
            (p1, n1), (p2, n2) = list(pins.items())
            a, b = endpoint(n1, r), endpoint(n2, r)
            label = f"{r} {val}" if val else r
            if r[0] == "D":                                   # polarity is the whole point
                k = "1" if names.get("1", "").upper() in ("K", "C") else "2"
                lines.append(f'  {a} ---|"{label}  ▸{names.get(p1,p1)}/{names.get(p2,p2)}"| {b}')
            else:
                lines.append(f'  {a} ---|"{label}"| {b}')
        elif secs:                                            # op-amp, one box per section
            for s in sorted(secs):
                box = f"u_{r}_{s}"
                lines.append(f'  {box}["{r}-{s}<br/>{val or sym}"]')
                lines.append(f'  class {box} chip')
                for role, p in sorted(secs[s].items()):
                    n = pins.get(p)
                    if not n:
                        continue
                    if role == "out":
                        lines.append(f'  {box} -->|"pin {p}"| {endpoint(n, r)}')
                    else:
                        lines.append(f'  {endpoint(n, r)} -->|"pin {p} {role}"| {box}')
            for p, n in pins.items():
                if RAIL.match(n) and not section_of(names.get(p, "")):
                    lines.append(f'  {rail_node(n, r)} -.-|"pin {p}"| u_{r}_{sorted(secs)[0]}')
        else:                                                 # everything else: one box
            box = f"u_{re.sub(chr(92)+'W','_',r)}"
            lines.append(f'  {box}["{r}<br/>{val or sym}"]')
            lines.append(f'  class {box} chip')
            for p, n in sorted(pins.items(), key=lambda x: (len(x[0]), x[0])):
                nm = names.get(p, p)
                lab = f"{p} {nm}" if nm != p else f"pin {p}"
                lines.append(f'  {box} ---|"{lab}"| {endpoint(n, r)}')
    lines += ["  classDef rail fill:none,stroke:none,color:#8a8378,font-size:11px",
              "  classDef chip fill:#2f3b47,stroke:#1d252d,color:#f4f1ea,font-weight:600"]
    return "\n".join(lines), nets


def main():
    netmap, values, kpins = load()
    syms = symbols()
    nums = {r: (int(re.sub(r'\D', '', r)) if re.search(r'\d', r) else None) for r in netmap}
    assigned, blocks = set(), []
    for slug, name, sub, src, pred in BLOCKS:
        refs = [r for r in netmap if r not in assigned and pred(r, nums[r])]
        assigned |= set(refs)
        code, nets = mermaid(refs, netmap, values, kpins, syms)
        blocks.append(dict(slug=slug, name=name, sub=sub, src=src, refs=sorted(refs),
                           code=code, nets={k: v for k, v in sorted(nets.items())}))
    leftover = sorted(set(netmap) - assigned)
    print(f"{len(blocks)} blocks, {len(assigned)} refs placed, {len(leftover)} unplaced: {leftover[:12]}")
    payload = json.dumps(blocks, separators=(",", ":"))
    tpl = open(f"{KI}/tools/blockview.tpl.html").read()
    open(OUT, "w").write(tpl.replace("/*__DATA__*/null", payload))
    print(f"-> {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
