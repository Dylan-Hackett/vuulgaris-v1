"""Route the faceplate with Freerouting, headless, fenced in to what this board allows.

    KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY hardware/faceplate/design/mkroute.py [--passes N]
    $KPY hardware/faceplate/design/mkroute.py --ses PATH     # import a session, no re-run
    $KPY hardware/faceplate/design/mkroute.py --dsn-only PATH  # just the fenced DSN
    $KPY hardware/faceplate/design/mkroute.py --unroute    # strip every track and via
    $KPY hardware/faceplate/design/mkroute.py --stitch     # only close ungrounded GND pads

Run after mkbuses.py (the pad buses are deterministic and are NOT left to the router) and
mkzones.py (the L3 GND plane). Steps:

  1. Export the board to Specctra DSN (pcbnew.ExportSpecctraDSN).
  2. Fence it, by editing the DSN -- Freerouting knows clearances, not this board's rules:
       * no wires on F.Cu, anywhere: the top layer is the scrub pads and nothing else
         (declared a power layer, so the router treats it as a plane);
       * no wires or vias anywhere left of the right margin (under or between the pads, the
         upper panel, the left margin), EXCEPT the corridor between pads 3 and 4 that the
         UART, RST, TEST and 3V3 need from J1, and the pockets where J1's pads reach under
         the pads' edges;
       * in that corridor, wires on B.Cu only (ADR 0003: the digital lines on L4, over the
         L3 GND strip);
       * no new wires on In2.Cu at all (also a power layer): it is the GND plane in the
         margin and the corridor, and under the pads it carries only the RX0 joins;
       * every existing wire and via -- the buses, the pad vias, J1's GND link -- protected.
  3. Run Freerouting (~/tools/freerouting/freerouting-2.4.1.jar) without its GUI.
  4. Read its session file and add only NEW copper to the board (what was protected comes
     back too, and is skipped). pcbnew's own ImportSpecctraSES needs the GUI.
  5. Prune dangling copper, stitch every GND pad with no path to the L3 plane (its own via,
     placed clear of everything by pcbnew's shapes), refill the zones and save.

tools/panelcheck.py then checks the fences held: nothing on F.Cu but the pads, and nothing
under a pad but that pad's own nets. After this writes the board, File -> Revert in Pcbnew.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FACE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(FACE), "kicad", "tools"))
sys.argv[1:1] = ["--project", "faceplate"]
import proj            # noqa: E402
import panelgeo as pg  # noqa: E402
import pcbnew          # noqa: E402
sys.path.insert(0, HERE)
import mkbuses as bus  # noqa: E402  -- the exits' positions

JAR = os.path.expanduser("~/tools/freerouting/freerouting-2.4.1.jar")
PASSES = int(sys.argv[sys.argv.index("--passes") + 1]) if "--passes" in sys.argv else 60
mm = pcbnew.FromMM
gen, G = pg.generator()

# ---- the fences, panel mm
X_M = G["PAD_X1"]                                   # the margin starts where pad copper ends
GAP_TOP, GAP_BOT = G["PAD_TOPS"][2] + G["PW"], G["PAD_TOPS"][3]
J1_X0, J1_X1 = 222.9, 235.1                         # J1's pads, x, with clearance
J1_Y0, J1_Y1 = 106.2, 118.8                         # ... and y: they reach under both pads
BIG = (-5.0, -5.0, G["PANEL_W"] + 5.0, G["PANEL_H"] + 5.0)
NO_ROUTE = [                                        # all layers but F.Cu (fenced below)
    (BIG[0], BIG[1], X_M, J1_Y0),                   # everything above the corridor
    (BIG[0], J1_Y0, J1_X0, J1_Y1),                  # left of J1
    (J1_X1, J1_Y0, X_M, GAP_TOP),                   # pad 3's edge right of J1
    (J1_X1, GAP_BOT, X_M, J1_Y1),                   # pad 4's edge right of J1
    (BIG[0], J1_Y1, X_M, BIG[3]),                   # everything below the corridor
]
CORRIDOR = (J1_X0, J1_Y0, X_M, J1_Y1)               # wires on B.Cu only


def dsn_xy(x, y):
    """panel mm -> DSN um (y down is negative)"""
    sx, sy = pg.face_sheet((x, y))
    return sx * 1000.0, -sy * 1000.0


def rect(kind, layer, r):
    x0, y0 = dsn_xy(r[0], r[1])
    x1, y1 = dsn_xy(r[2], r[3])
    return f'    ({kind} "" (rect {layer} {x0:.0f} {min(y0, y1):.0f} {x1:.0f} {max(y0, y1):.0f}))\n'


def fence(dsn):
    # F.Cu and In2.Cu take no new traces at all: declare them power layers, which Freerouting
    # uses only as planes. (A wire_keepout over the whole of F.Cu did the same for traces but
    # also stopped every via, whose F.Cu copper it counts as a wire: the first run routed
    # B.Cu alone and could not change layer.)
    for L in ("F.Cu", "In2.Cu"):
        dsn = re.sub(r"(\(layer %s\s*\n\s*\(type )signal" % re.escape(L), r"\1power", dsn, count=1)
    k = []
    for r in NO_ROUTE:
        for L in ("In1.Cu", "In2.Cu", "B.Cu"):
            k.append(rect("keepout", L, r))
    k.append(rect("wire_keepout", "In1.Cu", CORRIDOR))
    i = dsn.index("    (via ")                        # first line after the boundary/keepouts
    dsn = dsn[:i] + "".join(k) + dsn[i:]
    # The scrub pads are not the router's business: every bar is already joined by its
    # via and bus (mkbuses.py), and the top layer is fenced off anyway. Left in, their 985
    # SMD pins read as ~870 unrouted connections it can never make. So drop E1-E4's
    # placements and their pins; each pad net is then its protected bus-and-via group plus
    # the TVS and R pins the router has to reach.
    dsn = re.sub(r"\n\s*\(place E[1-4] [^\n]*\)\)", "", dsn)
    dsn = re.sub(r"\n\s*\(component [^\s]+\s*\n\s*\)", "", dsn)       # now-empty blocks
    net0 = dsn.index("  (network")
    net1 = dsn.index("  (wiring")
    dsn = dsn[:net0] + re.sub(r"\s+E[1-4]-\d+(?:@\d+)?(?=[\s)])", "", dsn[net0:net1]) + dsn[net1:]
    # The buses, likewise: all of it lies in the no-route zone under the pads, and handed
    # over it reads as islands -- Freerouting merges collinear protected segments into one
    # polyline and loses the vias between, then spends every pass trying to rejoin them.
    # Drop every pad-net wire and via left of the margin and give it, instead, a short
    # protected stub at each bus exit: each electrode net is then that stub and its cell,
    # and the one connection to make is the real one.
    w0 = dsn.index("  (wiring")
    keep = []
    for line in dsn[w0:].split("\n"):
        m = re.search(r"\(net (/PAD\d_RX\d)\)", line)
        if m:
            xs = [float(v) / 1000.0 - pg.FACE_ORG[0]
                  for v in re.findall(r"\s(-?\d+(?:\.\d+)?)\s+-\d", line)]
            if xs and max(xs) <= X_M + 1.0:
                continue
        keep.append(line)
    stubs = []
    for p in range(1, 5):
        yt = G["PAD_TOPS"][p - 1]
        yb = yt + G["PW"]
        for rx, y in ((0, yt + bus.TOP_IN), (2, yt + bus.DEEP_TOP),
                      (1, yb - bus.DEEP_BOT), (3, yb - bus.BOT_IN)):
            (x0, y0), (x1, y1) = dsn_xy(X_M, y), dsn_xy(bus.EXIT, y)
            net = f"/PAD{p}_RX{rx}"
            stubs.append(f"    (wire (path In1.Cu 150  {x0:.0f} {y0:.0f}  {x1:.0f} {y1:.0f})"
                         f"(net {net})(type protect))")
    w = "\n".join(keep)
    w = w.replace("  (wiring\n", "  (wiring\n" + "\n".join(stubs) + "\n", 1)
    dsn = dsn[:w0] + w
    return dsn.replace("(type route)", "(type protect)")


# ---- a small s-expression reader for the session file
def sexp(txt):
    toks = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', txt)
    stack, cur = [], []
    for t in toks:
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done, cur = cur, stack.pop()
            cur.append(done)
        else:
            cur.append(t.strip('"'))
    return cur[0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def prune(b):
    """Remove every track segment with a free end, until none is left: on a sensor board a
    dangling stub is an antenna. An end is tied if it lies on a pad of its net, inside a via
    of its net, or on another segment of its net on its layer."""
    n = 0
    while True:
        tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
        vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
        pads = [p for f in b.GetFootprints() for p in f.Pads()]
        by_net = {}
        for t in tracks:
            by_net.setdefault((t.GetNetCode(), t.GetLayer()), []).append(t)

        def tied(t, pt):
            for v in vias:
                if v.GetNetCode() == t.GetNetCode() and (v.GetPosition() - pt).EuclideanNorm() <= v.GetWidth() / 2 + t.GetWidth() / 2:
                    return True
            for p in pads:
                if p.GetNetCode() == t.GetNetCode() and p.IsOnLayer(t.GetLayer()) and p.HitTest(pt):
                    return True
            for o in by_net.get((t.GetNetCode(), t.GetLayer()), []):
                if o is not t and o.HitTest(pt, t.GetWidth() // 2):
                    return True
            return False
        free = [t for t in tracks if not (tied(t, t.GetStart()) and tied(t, t.GetEnd()))
                or t.GetLength() < mm(0.02)]       # and slivers: a 10um join of two tied ends
        if not free:
            return n
        for t in free:
            b.Remove(t)
        n += len(free)


def stitch(b, radius=2.4, step=0.12):
    """Give every GND pad with no path to the L3 plane its own via: the nearest spot where a
    via and a straight B.Cu stub from the pad clear every other net at its netclass
    clearance (pcbnew's own shapes), inside the plane. Whatever the router did, the grounds
    it gave up on are then closed. Returns the number of stitches."""
    import fnmatch
    ns = __import__("json").load(open(proj.P.pro))["net_settings"]
    cl = {c["name"]: c["clearance"] for c in ns["classes"]}
    pats = [(q["pattern"], q["netclass"]) for q in ns["netclass_patterns"]]
    ncls = lambda n: next((c for pat, c in pats if fnmatch.fnmatchcase(n, pat)), "Default")
    req = lambda n: mm(max(cl["GND"], cl[ncls(n)]))
    gnd = b.FindNet("/GND")
    zones = [z for z in b.Zones() if z.GetNetname() == "/GND"]
    fills = [z.GetFilledPolysList(z.GetLayer()) for z in zones]
    outlines = [z.Outline() for z in zones]
    in_plane = lambda pt, r: any(f.Collide(pt, r) for f in fills)
    tracks = [t for t in b.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)]
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    pads = [p for f in b.GetFootprints() for p in f.Pads()]
    gtracks = [t for t in tracks if t.GetNetCode() == gnd.GetNetCode()]
    gvias = [v for v in vias if v.GetNetCode() == gnd.GetNetCode()]
    gpads = [p for p in pads if p.GetNetCode() == gnd.GetNetCode()]
    # which GND copper reaches the plane: from every via in it, through touching copper
    items = gtracks + gvias + gpads
    def touch(a, z):
        if isinstance(a, pcbnew.PAD) and isinstance(z, pcbnew.PAD):
            return False
        sa, sz = a.GetEffectiveShape(pcbnew.B_Cu), z.GetEffectiveShape(pcbnew.B_Cu)
        return sa.Collide(sz, 0)
    reached = {id(v) for v in gvias if in_plane(v.GetPosition(), v.GetWidth() // 2)}
    todo = [v for v in gvias if id(v) in reached]
    while todo:
        cur = todo.pop()
        for it in items:
            if id(it) not in reached and touch(cur, it):
                reached.add(id(it))
                todo.append(it)
    targets = [p for p in gpads if id(p) not in reached and p.IsOnLayer(pcbnew.B_Cu)]
    n = 0
    for pad in targets:
        c0 = pad.GetPosition()
        # everything whose BOX comes near -- a long track's position is only its start
        win = pcbnew.BOX2I(pcbnew.VECTOR2I(c0.x - mm(radius + 1), c0.y - mm(radius + 1)),
                           pcbnew.VECTOR2I(mm(2 * radius + 2), mm(2 * radius + 2)))
        others = [it for it in tracks + vias + pads if it.GetNetCode() != gnd.GetNetCode()
                  and it.GetBoundingBox().Intersects(win)]
        own_pads = [p for p in pads if p.GetNetCode() == gnd.GetNetCode() and p.IsOnLayer(pcbnew.B_Cu)
                    and p.GetBoundingBox().Intersects(win)]
        best = None
        k = int(radius / step)
        cands = sorted(((i, j) for i in range(-k, k + 1) for j in range(-k, k + 1)),
                       key=lambda ij: ij[0] * ij[0] + ij[1] * ij[1])
        for i, j in cands:
            pt = pcbnew.VECTOR2I(c0.x + mm(i * step), c0.y + mm(j * step))
            if not in_plane(pt, mm(0.1)) or pt.x - mm(pg.FACE_ORG[0]) < mm(X_M + 0.3):
                continue
            v = pcbnew.PCB_VIA(b)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetPosition(pt)
            v.SetWidth(mm(0.6))
            v.SetDrill(mm(0.3))
            t = pcbnew.PCB_TRACK(b)
            t.SetLayer(pcbnew.B_Cu)
            t.SetWidth(mm(0.3))
            t.SetStart(c0)
            t.SetEnd(pt)
            ok = True
            for o in others:
                for L in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
                    if not o.IsOnLayer(L):
                        continue
                    so = o.GetEffectiveShape(L)
                    if v.GetEffectiveShape(L).Collide(so, req(o.GetNetname())) or \
                       (L == pcbnew.B_Cu and t.GetEffectiveShape(L).Collide(so, req(o.GetNetname()))):
                        ok = False
                        break
                if not ok:
                    break
            # never in a pad, its own included: solder would wick down an open via
            if ok and any(v.GetEffectiveShape(pcbnew.B_Cu).Collide(p.GetEffectiveShape(pcbnew.B_Cu), mm(0.1))
                          for p in own_pads):
                ok = False
            # clear of every hole and the board edge (NPTH panel holes, screws, outline)
            if ok:
                for d in b.GetDrawings():
                    if d.GetLayer() == pcbnew.Edge_Cuts and d.GetEffectiveShape().Collide(
                            v.GetEffectiveShape(pcbnew.B_Cu), mm(0.3)):
                        ok = False
                        break
            if ok:
                best = (v, t)
                break
        if best is None:
            print(f"stitch: no room for a via near {pad.GetParent().GetReference()}.{pad.GetNumber()}")
            continue
        v, t = best
        b.Add(v)
        v.SetNet(gnd)
        b.Add(t)
        t.SetNet(gnd)
        others_added = [v, t]
        tracks.append(t)
        vias.append(v)
        n += 1
        print(f"stitch: {pad.GetParent().GetReference()}.{pad.GetNumber()} -> via at "
              f"({pcbnew.ToMM(v.GetPosition().x) - pg.FACE_ORG[0]:.2f}, "
              f"{pcbnew.ToMM(v.GetPosition().y) - pg.FACE_ORG[1]:.2f})")
    return n


def main():
    b = pcbnew.LoadBoard(proj.P.pcb)
    if "--stitch" in sys.argv:               # only close the grounds, on the board as it is
        n = stitch(b)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(proj.P.pcb, b)
        print(f"{n} GND stitches. File -> Revert in Pcbnew before touching it.")
        return
    if "--unroute" in sys.argv:              # every track and via off: the start of a rebuild
        gone = list(b.GetTracks())
        for t in gone:
            b.Remove(t)
        pcbnew.SaveBoard(proj.P.pcb, b)
        print(f"unrouted: {len(gone)} tracks and vias removed. Rebuild with mkpads, mkbuses, "
              f"mkcells, mkescape, mkzones, then mkroute.")
        return
    if "--dsn-only" in sys.argv:             # write the fenced DSN and stop (parallel runs)
        out = os.path.abspath(sys.argv[sys.argv.index("--dsn-only") + 1])
        if not pcbnew.ExportSpecctraDSN(b, out):
            sys.exit("DSN export failed")
        fenced = fence(open(out).read())
        open(out, "w").write(fenced)
        print(f"fenced DSN: {out}")
        return
    if "--ses" in sys.argv:                  # import a session already routed, no re-run
        ses = os.path.abspath(sys.argv[sys.argv.index("--ses") + 1])
        work, out = os.path.dirname(ses), ""
    else:
        work = tempfile.mkdtemp(prefix="faceplate-route-")
        dsn, ses = os.path.join(work, "fp.dsn"), os.path.join(work, "fp.ses")
        if not pcbnew.ExportSpecctraDSN(b, dsn):
            sys.exit("DSN export failed")
        fenced = fence(open(dsn).read())     # read it all before reopening for write
        open(dsn, "w").write(fenced)
        cmd = ["java", "-jar", JAR, "-de", dsn, "-do", ses, "-mp", str(PASSES), "--gui.enabled=false"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        out = r.stdout + r.stderr
        open(os.path.join(work, "freerouting.log"), "w").write(out)
        if not os.path.exists(ses):
            sys.exit(f"Freerouting wrote no session (exit {r.returncode}); log in {work}")

    s = sexp(open(ses).read())
    routes = find(s, "routes")[0]
    res = float(find(routes, "resolution")[0][2])     # units per um
    to_mm = lambda v: float(v) / res / 1000.0
    # What was protected comes back too -- merged into long polylines and re-rounded -- so
    # "new" means: not lying wholly on existing copper of the same net and layer. A via is
    # new if no existing via sits within 10um of it.
    old_seg = {}
    for t in b.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            old_seg.setdefault((t.GetNetname(), t.GetLayer()), []).append(
                ((pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)),
                 (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))))
    old_via = [(pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y))
               for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]

    def on(p, segs, tol=0.002):
        for (ax, ay), (zx, zy) in segs:
            dx, dy = zx - ax, zy - ay
            L = dx * dx + dy * dy
            u = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
            if (p[0] - ax - u * dx) ** 2 + (p[1] - ay - u * dy) ** 2 <= tol * tol:
                return True
        return False

    layer = {n: b.GetLayerID(n) for n in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")}
    nw = nv = 0
    for net in find(find(routes, "network_out")[0], "net"):
        ni = b.FindNet(net[1])
        for w in find(net, "wire"):
            path = find(w, "path")[0]
            L, width = layer[path[1]], to_mm(path[2])
            pts = [(to_mm(path[i]), -to_mm(path[i + 1])) for i in range(3, len(path) - 1, 2)]
            segs = old_seg.get((net[1], L), [])
            for a, z in zip(pts, pts[1:]):
                mid = ((a[0] + z[0]) / 2, (a[1] + z[1]) / 2)
                if a == z or (on(a, segs) and on(z, segs) and on(mid, segs)):
                    continue
                t = pcbnew.PCB_TRACK(b)
                b.Add(t)
                t.SetLayer(L)
                t.SetWidth(mm(width))
                t.SetNet(ni)
                t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
                t.SetEnd(pcbnew.VECTOR2I(mm(z[0]), mm(z[1])))
                nw += 1
        for v in find(net, "via"):
            x, y = to_mm(v[2]), -to_mm(v[3])
            if any(abs(x - ox) < 0.01 and abs(y - oy) < 0.01 for ox, oy in old_via):
                continue
            m = re.search(r"_(\d+):(\d+)_um", v[1])
            via = pcbnew.PCB_VIA(b)
            b.Add(via)
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            via.SetWidth(mm(int(m.group(1)) / 1000.0))
            via.SetDrill(mm(int(m.group(2)) / 1000.0))
            via.SetNet(ni)
            nv += 1
    pruned = prune(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    stitched = stitch(b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(proj.P.pcb, b)
    tail = [l for l in out.splitlines() if "INFO" in l][-3:]
    if pruned:
        print(f"pruned {pruned} dangling track segments")
    print("\n".join(tail))
    print(f"added {nw} track segments and {nv} vias from Freerouting ({work}). "
          f"File -> Revert in Pcbnew before touching it.")


if __name__ == "__main__":
    main()
