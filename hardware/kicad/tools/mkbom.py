"""
mkbom.py -- build the JLC assembly BOM, preferring Basic parts.

    kicad-cli sch export python-bom --output fab/vuulgaris-bom.xml vuulgaris.kicad_sch
    python3 tools/mkbom.py

LCSC numbers come from four places, in order of confidence:

  1. CURATED below -- decisions made in this project and recorded in docs/,
     each one verified against the LCSC or JLCPCB product page.
  2. the footprint name, when it embeds the code (IDC-TH_10P-P2.54_C5665).
  3. the value string, when it embeds the code (RVT1E470M0505_C2977553).
  4. JLCPCB's Basic parts list, matched on value + package + dielectric --
     tools/jlc-basic.json, a snapshot of the entries this board uses.

Basic matters: JLC charges a per-part loading fee for every distinct Extended
part, so a board with 30 Extended passives pays that 30 times over. Everything
that can be Basic should be.

TP1-TP15 are excluded. They are bare 1.0mm pads -- drilled, never populated --
and were otherwise showing up as BOM lines named things like "SIGIN L".
"""
import xml.etree.ElementTree as ET, csv, re, json, collections, os, sys

K = "/Users/dylanhackett/V1/hardware/kicad"
# In the repo, not fetched. This used to point at a download in a scratch
# directory, and when that was wiped the script still ran -- and silently
# emitted a BOM with 40 lines' LCSC numbers blank. Missing is now fatal.
BASIC = f"{K}/tools/jlc-basic.json"

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
    "ASMD1812-300":          "C135366",   # 3A hold, was -200/C135364 until 2026-09-20
    "BLM18PG121SN1D_C14709": "C14709",
    "AMS1117-3.3":           "C6186",
    "1N4148W":               "C81598",
    "0402WGF2201TCE":        "C25879",
    # --- swapped away from parts JLC was short on, 2026-09-10 ---
    # was C9900013479, no JLC stock. GZ2012D601TF is Basic, 162k in stock, same
    # 600R at 100MHz in 0805. 500mA rated against ~50mA and ~20mA actual loads,
    # 300mohm DCR so 15mV of drop.
    "BEAD0805S601A20T":      "C1017",
    # was C389113 with 14 in stock against 20 needed. C57112 is Basic with 935k.
    # C28 is VBUS decoupling, so the original NP0 buys nothing over X7R here.
    "CC0603JRNPO9BN103":     "C57112",
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
    # TVS across VBUS. Checked in JLC's assembly library 2026-09-11: all 85
    # SMAJ6.0A entries are Extended, none Basic, so the per-part fee applies
    # whichever is picked and the choice comes down to stock and pedigree.
    # Littelfuse, 37k in stock, and one of the few whose JLC listing carries
    # IEC 61000-4-2 and 61000-4-4 -- the ESD and EFT immunity standards this
    # part exists to satisfy on a CE-marked product.
    #
    # DO NOT swap to C132934 (ST, "SMAJ6.0A-TR"). Same MPN prefix, but it is
    # the 2.3kW variant and clamps at 13.7V -- ABOVE the DKM10E-12's 12V/100ms
    # surge limit, so it would pass a transient straight into the converter.
    # Cheaper equivalents if stock ever fails: C364284 (MDD, 106k),
    # C353434 (Jingdao, 62k), C726732 (TWGMC, 10k). All 10.3V clamping.
    "SMAJ6.0A":              "C223993",    # Littelfuse SMAJ6.0A, SMA/DO-214AC
    # --- resolved in JLC's parts library 2026-09-11, browser not guesswork ---
    # 4R7 was carried as "EXTENDED: Basic has nothing under 10ohm but 0R".
    # That was wrong. C23164 is BASIC, 1% , 1.04M in stock, and it has been
    # costing an Extended loading fee for nothing.
    "4R7":                   "C23164",     # 0603WAF470KT5E UNI-ROYAL, 4.7ohm 1% 0603, BASIC
    # Both C0G 0603s are Extended -- no Basic C0G exists at these values -- so
    # these are picked on stock depth.
    "2nF C0G":               "C296055",    # 0603N222J500CT Walsin, 2.2nF 50V NP0 5%, 106k
    "4.7nF C0G":             "C576818",    # CC0603JRNPO9BN472 YAGEO, 4.7nF 50V NP0 5%, 424k
    # BBD sample-and-hold hold cap, C119/C219. Was 15nF, which JLC cannot supply
    # in ANY SMD package (checked 2026-09-11: 15nF C0G/NP0 is 0-stock pre-order
    # everywhere, and 18nF/22nF in 0805 do not exist either -- C0G is a low-K
    # dielectric and 10nF is the practical ceiling for this package).
    #
    # The manual asks for "a relatively big capacitor" in C0G, not for 15nF
    # exactly, and the DIELECTRIC is the real requirement: X7R dielectric
    # absorption relaxes the held voltage between samples and smears the
    # reconstruction. 10nF keeps C0G. Acquisition (Ron_J113 x C) gets 1.5x
    # faster, which helps inside the narrow sample pulse; droop and JFET charge
    # injection get 1.5x worse, about 9mV at the output after U106B's x5.55 at
    # typical J113 off-leakage. Fine on a lo-fi BBD delay.
    "10nF C0G 0805":         "C237168",    # 0805N103J500CT Walsin, 10nF 50V NP0 5%, 149k
}
# Placed but deliberately not populated, or with no LCSC source at all.
# The four values with no LCSC entry anywhere -- generic R/C symbols, so nothing
# was ever chosen. Each is an Extended part rather than Basic; JLC charges a
# small per-part fee for those, which is the right trade here because all four
# are in signal paths where the dielectric or the value actually matters.
NOTE = {
    # Stock and placeability below were read off JLC's parts library in a
    # browser on 2026-09-11, not inferred from LCSC. The two are different
    # inventories and this project has already been caught by that once.
    "DKM10E-12":     "NOT PLACEABLE -- PRE-ORDER ONLY. JLC returns 'No Result Found' for "
                     "C6934792 in the in-stock library: 0 stock, pre-order at $15.10, "
                     "MOQ 1. This is the power converter for the entire board, so it is "
                     "the one shortage that stops a build. Source it outside LCSC "
                     "(Mouser/Digi-Key/Arrow all list it) and hand-fit -- it is a "
                     "through-hole 1x1in module, trivial to solder.",
    "V3205SD":               "no LCSC source -- hand solder",
    "VTL5C3":                "no LCSC source -- hand solder, Xvive reissue",
    "SW_DPDT_FLAT":          "no LCSC source -- hand solder",
    "ES_DAISY_PATCH_SM_REV1":"module, socketed or hand soldered",
    "HS242L01W4S01":         "BUY FROM LCSC, FIT BY HAND -- C5139768, 27 in stock at $12.22. "
                             "Not in JLC's assembly library, and it is a display module on its "
                             "own 68x43mm PCB with a glass panel: do not reflow or wave solder it",
}

def decode_mlcc(mpn):
    """(farads, package, dielectric) from a YAGEO CC / Samsung CL part number.

    The power stage came in from EasyEDA with MPNs as values, so C31 reads
    "CC0603JRX7R8BB104" rather than "100nF". Those lines then missed the Basic
    matcher and kept whatever Extended part the old project happened to use --
    which is how five 100nF caps ended up on a part with 1 in JLC stock while
    the other thirty sat on a Basic part with millions."""
    m = re.match(r"CC(\d{4})[A-Z]+(X7R|NPO|C0G|X5R|Y5V)\w*?(\d{3})$", mpn)
    if m:
        pkg, diel, code = m.group(1), m.group(2), m.group(3)
    else:
        m = re.match(r"CL(\d\d)([ABC])(\d{3})[A-Z]", mpn)
        if not m:
            return None
        pkg = {"05": "0402", "10": "0603", "21": "0805", "31": "1206"}.get(m.group(1))
        diel = {"A": "X5R", "B": "X7R", "C": "C0G"}[m.group(2)]
        code = m.group(3)
    if not pkg:
        return None
    val = float(code[:2]) * (10 ** int(code[2])) * 1e-12
    return val, pkg, ("C0G" if diel == "NPO" else diel)

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
    if not os.path.exists(BASIC):
        sys.exit(f"missing {BASIC} -- without it every commodity R and C comes out unsourced")
    b = json.load(open(BASIC))
    basic = {"R": {tuple(k.split("|")): v for k, v in b["R"].items()},
             "C": {tuple(k.split("|")): v for k, v in b["C"].items()}}
    bympn = b.get("MPN", {})
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
        # CURATED first, always. These are explicit, verified decisions -- a part
        # checked on its LCSC or JLCPCB page, or chosen to get off something JLC
        # was short on. It has to outrank a table in docs/, which records what
        # some earlier version of the design happened to use.
        if val in CURATED:
            code, why = CURATED[val], "curated"
        # Commodity R and C get the Basic match first. Anything else keeps the
        # specific part someone chose.
        pk0 = re.match(r"[RC](\d{4})", fp)
        if not code and pk0:
            pk0 = pk0.group(1)
            if fp.startswith("R0"):
                o = ohms(val)
                if o is not None and (pk0, f"{o:g}") in basic["R"]:
                    code, why = basic["R"][(pk0, f"{o:g}")][0], "basic"
            else:
                f_ = farads(val)
                d_ = ["C0G"] if ("C0G" in val or "NP0" in val) else ["X7R", "X5R"]
                dec = decode_mlcc(val)
                if f_ is None and dec:
                    f_, pk0, d_ = dec[0], dec[1], [dec[2]] + ["X7R", "X5R"]
                if f_ is not None:
                    for d in d_:
                        k = (pk0, f"{f_:g}", d)
                        if k in basic["C"]:
                            code, why = basic["C"][k][0], "basic"
                            break
        codes = {byref[r] for r in refs if r in byref}
        if not code and len(codes) == 1:
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
    # Merge lines that resolved to the same LCSC part. The power stage arrived
    # from EasyEDA with MPNs as values, so five 100nF caps read
    # "CC0603JRX7R8BB104" and thirty read "100nF" -- same part, two lines, and
    # JLC prices the reel twice.
    merged = {}
    for r in rows:
        key = (r["LCSC Part #"], r["Footprint"]) if r["LCSC Part #"] else id(r)
        if key in merged:
            m = merged[key]
            m["Designator"] = ",".join(sorted(
                m["Designator"].split(",") + r["Designator"].split(","), key=natkey))
            m["Qty"] += r["Qty"]
            if r["Comment"] not in m["Comment"]:
                m["Comment"] = f"{m['Comment']} / {r['Comment']}"
        else:
            merged[key] = dict(r)
    before = len(rows)
    rows = sorted(merged.values(), key=lambda z: z["Comment"])
    if before != len(rows):
        print(f"merged {before - len(rows)} duplicate part lines")
    out = f"{K}/fab/vuulgaris-BOM.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Comment", "Designator", "Footprint",
                                          "LCSC Part #", "Qty", "Note"])
        w.writeheader(); w.writerows(rows)
    # JLC's upload wants exactly these four columns; Qty it derives from the
    # designators and Note it has nowhere to put. Derived here rather than by
    # hand, because doing it by hand is how the JLC copy went one line stale the
    # moment D3 was added.
    jlc = f"{K}/fab/vuulgaris-BOM-jlc.csv"
    with open(jlc, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Comment", "Designator", "Footprint",
                                          "LCSC Part #"], extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} lines -> {jlc}")

    got = sum(1 for r in rows if r["LCSC Part #"])
    print(f"{len(rows)} lines / {sum(r['Qty'] for r in rows)} parts -> {out}")
    print(f"  sourced   : {got}   {dict(how)}")
    print(f"  unsourced : {len(rows)-got}")
    for r in sorted((r for r in rows if not r["LCSC Part #"]), key=lambda z: -z["Qty"]):
        print(f"     {r['Comment'][:30]:32}{r['Qty']:>3}x  {r['Note'] or r['Footprint'][:34]}")

if __name__ == "__main__":
    main()
