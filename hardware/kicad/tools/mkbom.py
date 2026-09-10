"""
mkbom.py -- build the JLC assembly BOM, preferring Basic parts.

    kicad-cli sch export python-bom --output fab/vuulgaris-bom.xml vuulgaris.kicad_sch
    python3 tools/mkbom.py

LCSC numbers come from four places, in order of confidence:

  1. CURATED below -- decisions made in this project and recorded in docs/,
     each one verified against the LCSC or JLCPCB product page.
  2. the footprint name, when it embeds the code (IDC-TH_10P-P2.54_C5665).
  3. the value string, when it embeds the code (RVT1E470M0505_C2977553).
  4. JLCPCB's Basic parts list, matched on value + package + dielectric.

Basic matters: JLC charges a per-part loading fee for every distinct Extended
part, so a board with 30 Extended passives pays that 30 times over. Everything
that can be Basic should be.

TP1-TP15 are excluded. They are bare 1.0mm pads -- drilled, never populated --
and were otherwise showing up as BOM lines named things like "SIGIN L".
"""
import xml.etree.ElementTree as ET, csv, re, json, collections, os, sys

K = "/Users/dylanhackett/V1/hardware/kicad"
BASIC = "/private/tmp/claude-501/-Users-dylanhackett-V1/4de9b9fa-a306-444b-94eb-965c3f912b9d/scratchpad/basic.json"

# Verified against the LCSC or JLCPCB product page during this project.
CURATED = {
    "EC11L1525G01":          "C2991196",   # ENC0, 30/15 detents, WITH push switch
    "EC12E2430803":          "C470684",    # ENC1-8, detentless 0/24
    "12x12 tactile":         "C54573007",  # TS1103S-12x12x14DIP, 14mm, 2.4mm proud
    "FACEPLATE 2x5 IDC":     "C5665",      # 2x5 2.54mm IDC box header
    "OPA1688_FLAT":          "C206212",
    "20k trim":              "C55071",     # 3224W-1-203E SMD multiturn
    "TL072_FLAT":            "C67473",
    "CD4046B":               "C2651237",
    "J113 / MMBFJ113":       "C891686",
    "DKM10E-12":             "C6934792",
    "TFPUSH":                "C393941",
    "HS242L01W4S01":         "C5139768",
    "TYPE-C-31-M-12":        "C165948",
    "ASMD1812-200":          "C135364",
    "BLM18PG121SN1D_C14709": "C14709",
    "AMS1117-3.3":           "C6186",
    "1N4148W":               "C81598",
    "0402WGF2201TCE":        "C25879",
    "PJ-376":                "C22355746",  # SOFNG 3.5mm right-angle TH, 571 stock
    "CUTOFF":                "C380211",    # ALPS RK09L1240A12 dual 10k, all six pots
    "RESONANCE":             "C380211",
    "FILTER CV AMT":         "C380211",
    "TIME":                  "C380211",
    "FEEDBACK":              "C380211",
    "WET/DRY":               "C380211",
    "MCP23017-E_SO":         "C47023",
    "TL074":                 "C12594",     # TL074CDR SOIC-14
    "TL084":                 "C8956",      # TL084CDR SOIC-14
    "1nF C0G":               "C163508",    # CL10C102JB8NNNC, 50V C0G
    "220pF C0G":             "C27675",     # CL10C221JB8NNNC, 50V C0G
    "3V9 zener":             "C213113",    # BZT52C3V9 SOD-123, 3.7-4.1V
}
# Placed but deliberately not populated, or with no LCSC source at all.
NOTE = {
    "V3205SD":               "no LCSC source -- hand solder",
    "VTL5C3":                "no LCSC source -- hand solder, Xvive reissue",
    "SW_DPDT_FLAT":          "no LCSC source -- hand solder",
    "ES_DAISY_PATCH_SM_REV1":"module, socketed or hand soldered",
}

def ohms(s):
    s = s.split("(")[0].strip()
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([kKMR]?)(\d*)", s)
    if not m:
        return None
    a, u, b = m.groups()
    v = float(f"{a}.{b}") if b else float(a)
    return v * {"k": 1e3, "K": 1e3, "M": 1e6, "R": 1, "": 1}[u]

def farads(s):
    m = re.search(r"([\d.]+)\s*(pF|nF|uF)", s)
    return float(m.group(1)) * {"pF": 1e-12, "nF": 1e-9, "uF": 1e-6}[m.group(2)] if m else None

def natkey(r):
    m = re.match(r"([A-Za-z]+)(\d+)", r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)

def harvest_symbols():
    """Symbol name -> LCSC, straight out of the symbol library.

    easyeda2kicad writes an "LCSC Part" property on every symbol it pulls, so
    for anything imported that way the number is already sitting in the file.
    This is the source that should have been read first -- it is authoritative
    for the part that was actually chosen, where a value string like
    "BEAD0805S601A20T" only says what it is called."""
    out = {}
    sym = f"{K}/lib/vuulgaris.kicad_sym"
    if not os.path.exists(sym):
        return out
    s = open(sym).read()
    pos = 0
    while True:
        m = re.compile(r'\n  \(symbol "([^"]+)"').search(s, pos)
        if not m:
            return out
        name = m.group(1); st = m.start() + 1; d = 0; j = st
        while j < len(s):
            if s[j] == "(": d += 1
            elif s[j] == ")":
                d -= 1
                if d == 0: break
            j += 1
        blk = s[st:j + 1]; pos = j + 1
        props = dict(re.findall(r'\(property\s*\n?\s*"([^"]*)"\s*\n?\s*"([^"]*)"', blk))
        code = props.get("LCSC Part", "").strip()
        if re.fullmatch(r"C\d{4,10}", code):
            out[name] = code

def harvest_docs():
    """Designator -> LCSC, from the tables in docs/.

    power-usbc-dkm.md maps the whole power stage by designator, which is a
    stronger key than the value string: C31 and C34 are both "100nF 0603" but
    the table names them individually."""
    import glob
    out = {}
    files = glob.glob("/Users/dylanhackett/V1/docs/*.md") + \
            glob.glob("/Users/dylanhackett/V1/hardware/*.md") + [f"{K}/README.md"]
    ref1 = re.compile(r"^[A-Z]{1,3}\d+(?:\s*[-,]\s*[A-Z]{1,3}?\d+)*$")
    for fn in files:
        for line in open(fn):
            if "|" not in line:
                continue
            cells = [c.strip().strip("`*") for c in line.split("|")]
            code = next((c for c in cells if re.fullmatch(r"C\d{5,8}", c)), None)
            if not code or len(cells) < 2:
                continue
            first = cells[1]
            if not ref1.match(first.replace(" ", "")):
                continue
            for tok in re.split(r"[,\s]+", first):
                m = re.fullmatch(r"([A-Z]{1,3})(\d+)-([A-Z]{1,3})?(\d+)", tok)
                if m:
                    for i in range(int(m.group(2)), int(m.group(4)) + 1):
                        out[f"{m.group(1)}{i}"] = code
                elif re.fullmatch(r"[A-Z]{1,3}\d+", tok):
                    out[tok] = code
    return out

def main():
    basic = {"R": {}, "C": {}}
    if os.path.exists(BASIC):
        b = json.load(open(BASIC))
        basic["R"] = {tuple(k.split("|")): v for k, v in b["R"].items()}
        basic["C"] = {tuple(k.split("|")): v for k, v in b["C"].items()}
    bympn = {}
    if os.path.exists(BASIC.replace("basic.json", "basic.csv")):
        for r in csv.DictReader(open(BASIC.replace("basic.json", "basic.csv"),
                                     encoding="latin-1")):
            mp = (r["MFR.Part #"] or "").strip()
            if mp:
                bympn.setdefault(mp, r["LCSC Part #"].strip())
    byref = harvest_docs()
    bysym = harvest_symbols()
    root = ET.parse(f"{K}/fab/vuulgaris-bom.xml").getroot()
    groups = collections.defaultdict(list)
    for c in root.find("components"):
        ref = c.get("ref")
        if re.fullmatch(r"TP\d+", ref):
            continue
        groups[((c.findtext("value") or "").strip(),
                (c.findtext("footprint") or "").split(":")[-1])].append(ref)

    rows, how = [], collections.Counter()
    for (val, fp), refs in sorted(groups.items()):
        code, why = "", ""
        codes = {byref[r] for r in refs if r in byref}
        if len(codes) == 1:
            code, why = codes.pop(), "designator"
        if not code and val in bysym:
            code, why = bysym[val], "symbol lib"
        if not code and val in bympn:
            code, why = bympn[val], "exact MPN"
        if not code and val in CURATED:
            code, why = CURATED[val], "curated"
        if not code:
            m = re.search(r"_(C\d{4,8})$", fp) or re.search(r"_(C\d{4,8})$", val)
            if m:
                code, why = m.group(1), "embedded"
        if not code:
            pk = re.match(r"[RC](\d{4})", fp)
            pk = pk.group(1) if pk else None
            if pk and fp.startswith("R0"):
                o = ohms(val)
                if o is not None and (pk, f"{o:g}") in basic["R"]:
                    code, why = basic["R"][(pk, f"{o:g}")][0], "basic"
            elif pk and fp.startswith("C0"):
                f = farads(val)
                if f is not None:
                    want = ["C0G"] if ("C0G" in val or "NP0" in val) else ["X7R", "X5R"]
                    for d in want:
                        k = (pk, f"{f:g}", d)
                        if k in basic["C"]:
                            code, why = basic["C"][k][0], "basic"
                            break
        how[why or "UNSOURCED"] += 1
        rows.append({"Comment": val, "Designator": ",".join(sorted(refs, key=natkey)),
                     "Footprint": fp, "LCSC Part #": code, "Qty": len(refs),
                     "Note": NOTE.get(val, "")})
    out = f"{K}/fab/vuulgaris-BOM.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Comment", "Designator", "Footprint",
                                          "LCSC Part #", "Qty", "Note"])
        w.writeheader(); w.writerows(rows)
    got = sum(1 for r in rows if r["LCSC Part #"])
    print(f"{len(rows)} lines / {sum(r['Qty'] for r in rows)} parts -> {out}")
    print(f"  sourced   : {got}   {dict(how)}")
    print(f"  unsourced : {len(rows)-got}")
    for r in sorted((r for r in rows if not r["LCSC Part #"]), key=lambda z: -z["Qty"]):
        print(f"     {r['Comment'][:30]:32}{r['Qty']:>3}x  {r['Note'] or r['Footprint'][:34]}")

if __name__ == "__main__":
    main()
