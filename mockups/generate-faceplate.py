#!/usr/bin/env python3
"""
Vuulgaris V1 faceplate generator.

Emits a TRUE-SCALE SVG in millimetres (1 user unit = 1mm) of the Salamis Tablet
faceplate, including the real comb-tooth electrode geometry per ADR 0003.

    python3 generate-faceplate.py               > faceplate.svg   # fills the view
    python3 generate-faceplate.py --fab         > faceplate.svg   # exact mm, for the fab
    python3 generate-faceplate.py --check                  # verification report, no SVG
    python3 generate-faceplate.py --set pad_length_mm=264  # one-off override

Both outputs carry the SAME geometry in millimetre coordinates. The only
difference is the wrapper: the default emits width="100%" with a margin so it
displays large and centred, --fab emits explicit mm with flush edges.

EVERYTHING tweakable lives in CFG below. To change the layout, change a number
there. Do not go hunting through the drawing code.
"""
import math
import sys

# =============================================================================
# CFG - the only thing you should need to edit
# =============================================================================
CFG = {
    # ---- pads: the geometry everything else follows from --------------------
    # pad_length and pad_gap are INDEPENDENT. The 12:1 pad-length-to-pitch ratio
    # measured off the reference sketch was an artefact of that sketch drawing
    # pads as single strokes with no thickness. Discarded 2026-08-06.
    "pad_length_mm":     216.0,
    "pad_width_mm":       10.0,   # ADR 0003 says 10-12mm is the useful band
    # DO NOT REDUCE. design-state wants >=10mm closest approach for crosstalk,
    # and 9mm was already a compromise. Crosstalk between adjacent pads is the
    # untested failure mode in Q1, so this is the wrong place to buy millimetres.
    "pad_gap_mm":          9.0,
    # Depth override. None = the original Salamis 1.933:1 ratio (154.29mm).
    # 129 was chosen 2026-08-09 to shrink the footprint WITHOUT touching the gap.
    "panel_h_mm":        139.0,

    # ---- copper: comb teeth -------------------------------------------------
    "teeth_per_zone":       25,   # x4 zones = 100 teeth/pad
    "tooth_gap_mm":       0.21,
    "top_bottom_gap_mm":  0.20,
    "min_copper_mm":      0.15,   # fab floor; slivers are dropped, not drawn
    # Fillet on every tooth's OWN four corners. Softens the outline, including
    # the pad's four extreme corners, without shortening anything. Sharp
    # corners on exposed copper are where etch undercut starts, so this helps
    # the process as well as the look. Clamped per tooth at render time.
    "tooth_fillet_mm":     0.6,   # 0 restores hard corners; max useful = T_WIDTH/2

    # Fillets remove copper from every tooth, and position is read from the
    # AREA ratio between the top and bottom bars. A fixed area loss on both
    # bars therefore bends the position curve: at 0.6mm the worst error is
    # 2.33mm on a 216mm pad. Pre-compensating the bar HEIGHTS so the filleted
    # AREAS stay linear removes it, and costs nothing but this arithmetic.
    "compensate_fillet_area": True,

    # Taper the pad ENDS along an arc by shortening the teeth near them.
    # Different thing entirely, and off: it makes the last teeth shorter
    # rather than just softening their corners.
    "pad_corner_r_mm":     0.0,

    # ---- pad markings -------------------------------------------------------
    "n_ticks":              13,   # 13 marks = 12 intervals = a TRUE centre mark
    "cross_at":     (4, 7, 10),   # 1-indexed. Centre +/-3, lands on 1/4, 1/2, 3/4.

    # ---- upper region controls ----------------------------------------------
    "knob_r_mm":           8.0,   # 16mm knob
    "knob_pitch_mm":      22.0,
    "offset_knob_r_mm":   10.0,   # dual-gang ANALOG pot, deliberately larger
    # TWO switches, doing two DIFFERENT jobs. Both are DPDT, both are one pole
    # per stereo side ganged on one actuator, both are analog routing on the LPG
    # board, both cost zero Daisy pins.
    #   slot 1  LPG MODE    stereo VCF or stereo VCA
    #   slot 2  SOURCE      resample or external input
    # There is NOT a separate VCF/VCA switch per channel. The LPG is one stereo
    # unit, so mode is a single decision applied to both sides. Clarified
    # 2026-08-07 after that was described wrongly.
    "n_switches":            2,
    "switch_w_mm":         9.0,   # vertical slots
    "switch_h_mm":        20.0,
    "oled_w_mm":          70.0,
    "oled_h_mm":          42.0,
    "encoder_r_mm":        9.2,
    # Controls live in ONE column in the left margin: encoder, shift, then the
    # four channel buttons. Decided 2026-08-17. The pad block is pushed right to
    # open that margin; every panel-facing coordinate moves with it.
    "controls_left":      True,
    "pad_x_shift_mm":     20.0,
    "n_buttons":             4,
    "button_r_mm":         3.5,
    # Cherry MX keycaps in a 2x2 cluster. The four buttons are general UI keys,
    # not per-channel, so a cluster reads better than a column. Shift is gone.
    "mx_buttons":         True,
    "mx_cap_mm":          18.0,
    "mx_pitch_mm":        19.05,

    # Shift button, directly below the encoder in the right margin. Wired to
    # A9 (PB15) on the Daisy, not to the MSP430. Tactile switch on the MAIN
    # PCB with a tall plunger through the faceplate, same standoff as the
    # encoder. Deliberately smaller than the encoder so the hierarchy reads.
    "shift_button":      False,
    "shift_r_mm":          4.0,   # 8mm cap
    "shift_gap_mm":        5.0,   # clear space below the encoder
    # Centre the encoder + button as ONE group on the pad block, rather than
    # centring the encoder and letting the button hang below it.
    "center_encoder_pair": True,
    "group_gap_mm":        6.0,   # between upper-region groups

    # ---- Salamis inscription -----------------------------------------------
    # Read directly off the photographed inscription: PLAIN SINGLE LETTERS.
    # An earlier pass theorised these were compound PI-nesting numerals; that
    # was over-reading. They are simple incised letterforms, a few strokes each.
    #   T  tau     P rho    X chi     F digamma-like    H eta
    #   A  alpha   N pi     G gamma   C lunate sigma
    # LEFT MARGIN ONLY.
    # OFF 2026-08-09. The monoline stroke glyphs running down the left margin
    # did not read well at 4.4mm. The letterforms are kept here rather than
    # deleted, so turning this back on restores them unchanged.
    "salamis_marks":     False,
    "inscription":        "TPXFHFANGFCTX",
    "inscription_h_mm":    4.4,
    "inscription_below_divider": True,   # never in the control strip
    "inscription_left_only":     True,

    # ---- placement ----------------------------------------------------------
    "encoder_lower_right": True,  # False puts it back in the upper strip
    "straight_divider":    True,  # False restores the irregular crack line
    # Push the divider rule DOWN from where the reference composition puts it.
    # Also buys the OLED headroom, since the screen centres in the strip above.
    "divider_nudge_mm":    4.0,

    # ---- how the SVG presents itself ----------------------------------------
    # The panel geometry is IDENTICAL either way. This only changes the wrapper.
    # ---- enclosure -----------------------------------------------------------
    # The panel screws down ON TOP of the cheeks, so the cheeks sit UNDER the
    # panel's outer edge. Anything on the main PCB must clear them, and the main
    # PCB is therefore narrower than the panel by 2x this plus assembly slop.
    # At 15mm the upper assembly clears by only 1.14mm; at 20mm it collides.
    "enclosure_wall_mm":   6.0,
    "wall_clearance_mm":   2.0,   # minimum air between wall and nearest part
    # The composition is INSET from the panel edge by wall+clearance, so the
    # main PCB and everything on it lives inside the cavity. Without this the
    # OLED sat 4mm from the panel edge and the top wall went straight through
    # it. That bug predated the depth change; it was never caught because
    # nothing checked against an enclosure.
    "inset_composition": True,
    "panel_screw_inset_mm": 3.0,  # from panel edge, into the wall top

    "fab_output":        False,   # True = explicit mm size, flush edges
    "view_margin_mm":     10.0,   # breathing room around the panel on screen

    # ---- vertical margins in the lower region -------------------------------
    # True centres the pad block between the divider rule and the bottom edge.
    # The numeral row then sits in the space below rather than being reserved
    # out of the centring, which is what was pushing the pads high.
    "center_pads_in_region": True,
    "numeral_row_mm":      4.5,   # pad bottom to numeral baseline
    "bottom_margin_mm":    8.0,
    "below_divider_mm":    5.5,
}

NET_COLOR = {0: "#D85A30", 1: "#1D9E75", 2: "#378ADD", 3: "#7F77DD"}
NET_NAME = {0: "RX0", 1: "RX1", 2: "RX2", 3: "RX3"}
INK, INK2, INK3 = "#5F5E5A", "#888780", "#B4B2A9"
KNOB_INK, OFFSET_INK = "#534AB7", "#993C1D"


# =============================================================================
def derive(c):
    """All computed geometry, in mm. Pure function of CFG."""
    g = {}
    PL, PW, GAP = c["pad_length_mm"], c["pad_width_mm"], c["pad_gap_mm"]
    g["PL"], g["PW"], g["GAP"] = PL, PW, GAP
    g["PITCH"] = PW + GAP
    g["PANEL_W"] = PL * (580.0 / 420.0)          # pad is 420/580 of panel width
    # Height was locked to the Salamis 1.933:1 ratio. panel_h_mm now overrides it
    # so depth can be reduced independently of the pad length. X and Y therefore
    # need SEPARATE scales; using one for both is what tied them together.
    g["PANEL_H"] = c["panel_h_mm"] or g["PANEL_W"] * (300.0 / 580.0)
    g["S"] = g["PANEL_W"] / 580.0                # reference-unit -> mm, HORIZONTAL
    INSET = (c["enclosure_wall_mm"] + c["wall_clearance_mm"]) if c["inset_composition"] else 0.0
    g["INSET"] = INSET
    g["SY"] = (g["PANEL_H"] - 2.0 * INSET) / 300.0   # reference-unit -> mm, VERTICAL
    uy = lambda u: INSET + (u - 40.0) * g["SY"]
    g["uy"] = uy

    # pads: centred on the panel width
    g["PAD_X0"] = (g["PANEL_W"] - PL) / 2.0 + c.get("pad_x_shift_mm", 0.0)
    g["PAD_X1"] = g["PAD_X0"] + PL
    g["PAD_MID"] = g["PAD_X0"] + PL / 2.0

    # pads: distributed through the lower region
    # divider_nudge_mm pushes the rule DOWN, independently of the reference
    # composition. Every millimetre comes out of the lower region, so it is
    # bounded by the pad block plus the numeral row still fitting.
    g["DIV_Y"] = uy(150) + c["divider_nudge_mm"]
    block = 4 * PW + 3 * GAP
    avail = (g["PANEL_H"] - (g["DIV_Y"] + c["below_divider_mm"])
             - c["numeral_row_mm"] - c["bottom_margin_mm"])
    g["BLOCK_H"], g["AVAIL"] = block, avail
    if c["center_pads_in_region"]:
        # Centre the pad BLOCK in the whole region between the divider rule and
        # the bottom edge, and let the numeral row live in the space beneath.
        # The old behaviour subtracted the numeral row before centring, which
        # left the pads visibly high: 5.6mm above, 17.1mm below.
        g["PAD_Y0"] = g["DIV_Y"] + (g["PANEL_H"] - g["DIV_Y"] - block) / 2.0
    else:
        g["PAD_Y0"] = g["DIV_Y"] + c["below_divider_mm"] + max(0.0, (avail - block) / 2.0)
    g["PAD_TOPS"] = [g["PAD_Y0"] + i * g["PITCH"] for i in range(4)]

    # teeth
    g["N_TEETH"] = c["teeth_per_zone"] * 4
    g["T_PITCH"] = PL / g["N_TEETH"]
    g["T_WIDTH"] = g["T_PITCH"] - c["tooth_gap_mm"]

    # ticks
    g["TICK_X"] = [g["PAD_X0"] + k * (PL / (c["n_ticks"] - 1)) for k in range(c["n_ticks"])]

    # upper region: four groups, equal gaps, symmetric outer margins
    KR, KP, UG = c["knob_r_mm"], c["knob_pitch_mm"], c["group_gap_mm"]
    g["RULE_Y"] = [uy(r) for r in (54, 75, 96, 118, 139)]
    # OLED centred in the upper strip. Tying its top to rule 1 was what made it
    # collide with the top wall: rule 1 scales with the panel and sits near the edge.
    g["OLED_Y"] = INSET + ((g["DIV_Y"] - INSET) - c["oled_h_mm"]) / 2.0
    g["R2"], g["R3"], g["R4"] = g["RULE_Y"][1], g["RULE_Y"][2], g["RULE_Y"][3]
    ch_w = 3 * KP + 2 * KR
    env_w = 2 * KP + 2 * KR          # 3 columns x 2 rows: 2 encoders, 4 pots
    NSW = c["n_switches"]
    ui_w = NSW * c["switch_w_mm"] + max(0, NSW - 1) * 4.0 + 6.0
    if not c["encoder_lower_right"]:
        ui_w += 2 * c["encoder_r_mm"] + 6.0
    content = ch_w + UG + UG + env_w + UG + ui_w + UG + c["oled_w_mm"]
    g["UP_MARG"] = (g["PANEL_W"] - content) / 2.0
    g["UP_CONTENT"] = content
    g["ch_x0"] = g["UP_MARG"]
    g["UP_DIV"] = g["ch_x0"] + ch_w + UG
    g["env_x0"] = g["UP_DIV"] + UG
    g["ui_x0"] = g["env_x0"] + env_w + UG
    g["oled_x0"] = g["ui_x0"] + ui_w + UG
    g["CH_CX"] = [g["ch_x0"] + KR + i * KP for i in range(4)]
    g["EN_CX"] = [g["env_x0"] + KR + i * KP for i in range(3)]
    g["OFFSET_CX"] = g["EN_CX"][2]      # RV1 now sits in column 3, top row
    g["ENV_W"] = env_w

    # encoder
    if c["encoder_lower_right"]:
        # centre in the CAVITY margin: the panel edge is not the limit,
        # the inner wall face is. The encoder was overhanging it by 3mm.
        g["ENC_CX"] = (g["PAD_X1"] + g["PANEL_W"] - c["enclosure_wall_mm"]) / 2.0
        mid = (g["PAD_TOPS"][0] + g["PAD_TOPS"][3] + PW) / 2.0
        if c["shift_button"] and c["center_encoder_pair"]:
            # Centre the encoder AND button as one group on the pad block.
            # Centring the encoder alone and hanging the button off the bottom
            # left the pair sitting 6.5mm low.
            pair_h = 2 * c["encoder_r_mm"] + c["shift_gap_mm"] + 2 * c["shift_r_mm"]
            g["ENC_CY"] = mid - pair_h / 2.0 + c["encoder_r_mm"]
        else:
            g["ENC_CY"] = mid
    else:
        g["ENC_CX"] = g["ui_x0"] + c["encoder_r_mm"] + 2.0
        g["ENC_CY"] = g["R2"]

    # shift button: same axis as the encoder, directly below it
    g["SHIFT_CX"] = g["ENC_CX"]
    g["SHIFT_CY"] = (g["ENC_CY"] + c["encoder_r_mm"]
                     + c["shift_gap_mm"] + c["shift_r_mm"])

    # One control column in the left margin. Overrides encoder_lower_right.
    g["BTN_CX"], g["BTN_CY"] = None, []
    if c.get("controls_left"):
        col = (c["enclosure_wall_mm"] + g["PAD_X0"]) / 2.0
        g["ENC_CX"] = g["SHIFT_CX"] = g["BTN_CX"] = col
        if c.get("mx_buttons"):
            P, CAP, er = c["mx_pitch_mm"], c["mx_cap_mm"], c["encoder_r_mm"]
            pad_mid = (g["PAD_TOPS"][0] + g["PAD_TOPS"][3] + PW) / 2.0
            gap = 6.0
            top = pad_mid - (2 * er + gap + (P + CAP)) / 2.0
            g["ENC_CY"] = top + er
            g["SHIFT_CY"] = None
            g["MX_CX"] = [col - P / 2.0, col + P / 2.0]
            first = top + 2 * er + gap + CAP / 2.0
            g["MX_CY"] = [first, first + P]
            g["BTN_CY"] = []
        else:
            g["ENC_CY"] = 72.0
            g["SHIFT_CY"] = 87.0
            g["BTN_CY"] = [97.0, 106.0, 115.0, 124.0][:c.get("n_buttons", 4)]
    return g


def presences(t):
    return [max(0.0, 1 - t) + max(0.0, t - 3),
            max(0.0, 1 - abs(t - 1)),
            max(0.0, 1 - abs(t - 2)),
            max(0.0, 1 - abs(t - 3))]


def corner_inset(x, x0, x1, r):
    """Vertical inset of the pad outline at horizontal position x, for a pad
    with rounded ends of radius r. Zero outside the corner zones.

    Computed as real geometry rather than an SVG clip path, because this file
    becomes copper and a clip path may not survive the trip into a PCB tool."""
    if r <= 0.0:
        return 0.0
    d = min(x - x0, x1 - x)          # distance to the nearer end
    if d >= r:
        return 0.0
    d = max(d, 0.0)
    return r - (r * r - (r - d) ** 2) ** 0.5


def teeth(c, g, y_top):
    out, usable = [], g["PW"] - c["top_bottom_gap_mm"]
    x0, x1 = g["PAD_X0"], g["PAD_X1"]
    r = c["pad_corner_r_mm"]
    for i in range(g["N_TEETH"]):
        t = (i + 0.5) / g["N_TEETH"] * 4.0
        p = presences(t)
        tn = 0 if p[0] >= p[2] else 2
        bn = 1 if p[1] >= p[3] else 3
        frac = p[0] + p[2]                       # wanted TOP area fraction
        if c["compensate_fillet_area"] and c["tooth_fillet_mm"] > 0.0:
            # Solve for the height split whose FILLETED AREAS hit `frac`.
            # Closed form does not work: a short bar has its fillet clamped to
            # h/2, so the copper removed is not the same on both bars, and
            # assuming it is over-corrects exactly where the error is worst.
            # Fixed-point iteration handles the clamping and converges fast.
            W = g["T_WIDTH"]
            k = lambda h: (lambda rr: 4.0 * (rr * rr - math.pi * rr * rr / 4.0))(
                min(c["tooth_fillet_mm"], W / 2.0, max(h, 0.0) / 2.0))
            ht = frac * usable
            for _ in range(40):
                kt, kb = k(ht), k(usable - ht)
                nxt = (frac * (W * usable - kt - kb) + kt) / W
                nxt = min(max(nxt, 0.0), usable)
                if abs(nxt - ht) < 1e-12:
                    ht = nxt
                    break
                ht = nxt
            hb = usable - ht
        else:
            ht, hb = frac * usable, (1.0 - frac) * usable
        if ht < c["min_copper_mm"]:
            ht, hb = 0.0, g["PW"]
        elif hb < c["min_copper_mm"]:
            hb, ht = 0.0, g["PW"]
        x = g["PAD_X0"] + i * g["T_PITCH"]
        w = g["T_WIDTH"]
        # Worst-case inset across the tooth's own width, so no corner of the
        # rect pokes outside the rounded outline.
        ins = max(corner_inset(x, x0, x1, r), corner_inset(x + w, x0, x1, r))
        # Clamp each rect to the rounded envelope at BOTH edges. Doing it as a
        # general clamp rather than per-case arithmetic is what makes the
        # full-height teeth (where one bar fell below the fab floor) come out
        # right; an earlier version inset only one edge and they poked out.
        lim_top, lim_bot = y_top + ins, y_top + g["PW"] - ins
        for net, ry0, ry1 in ((tn, y_top, y_top + ht),
                              (bn, y_top + g["PW"] - hb, y_top + g["PW"])):
            if ry1 - ry0 <= 0:
                continue
            ry0, ry1 = max(ry0, lim_top), min(ry1, lim_bot)
            if ry1 - ry0 >= c["min_copper_mm"]:
                out.append((net, x, ry0, w, ry1 - ry0))
    return out


def attic_symbol(code, x, y, h):
    """One Attic denomination symbol as monoline strokes: simple letter, or a
    compound PI nesting a smaller letter (PD=50, PH=500, PX=5000). Drawn rather
    than typeset so it survives any font situation and matches incised marble."""
    if len(code) == 2 and code[0] == "P":
        return pi_compound(x, y, h, code[1])
    return archaic_glyph(code, x, y, h)


def archaic_glyph(ch, x, y, h):
    """Archaic Greek inscriptional letterform, monoline strokes, baseline y,
    centred on x, cap height h. Deliberately plain: a few clean strokes each,
    which is what the incised original actually looks like."""
    w = h * 0.58
    L, R, T, M = x - w / 2, x + w / 2, y - h, y - h * 0.52
    if ch == "T":   return f"M{L:.2f} {T:.2f}H{R:.2f}M{x:.2f} {T:.2f}V{y:.2f}"
    if ch == "P":   return (f"M{L:.2f} {y:.2f}V{T:.2f}H{x:.2f}"
                            f"A{w*0.5:.2f} {h*0.24:.2f} 0 0 1 {x:.2f} {y-h*0.52:.2f}H{L:.2f}")
    if ch == "X":   return f"M{L:.2f} {y:.2f}L{R:.2f} {T:.2f}M{R:.2f} {y:.2f}L{L:.2f} {T:.2f}"
    if ch == "F":   return f"M{L:.2f} {y:.2f}V{T:.2f}H{R:.2f}M{L:.2f} {M:.2f}H{x+w*0.22:.2f}"
    if ch == "H":   return (f"M{L:.2f} {y:.2f}V{T:.2f}M{R:.2f} {y:.2f}V{T:.2f}"
                            f"M{L:.2f} {y-h*0.5:.2f}H{R:.2f}")
    if ch == "A":   return (f"M{L:.2f} {y:.2f}L{x:.2f} {T:.2f}L{R:.2f} {y:.2f}"
                            f"M{x-w*0.26:.2f} {y-h*0.36:.2f}H{x+w*0.26:.2f}")
    if ch == "N":   return f"M{L:.2f} {y:.2f}V{T:.2f}H{R:.2f}V{y:.2f}"
    if ch == "G":   return f"M{L:.2f} {y:.2f}V{T:.2f}H{R:.2f}"
    if ch == "C":   return (f"M{R:.2f} {y-h*0.80:.2f}A{w*0.52:.2f} {h*0.42:.2f} 0 0 0 "
                            f"{R:.2f} {y-h*0.20:.2f}")
    if ch == "I":   return f"M{x:.2f} {y:.2f}V{T:.2f}"
    if ch == "D":   return f"M{L:.2f} {y:.2f}L{x:.2f} {T:.2f}L{R:.2f} {y:.2f}Z"
    return ""


def pi_compound(x, y, h, inner):
    """Attic compound glyph: PI nesting a smaller letter. PI+D=50, PI+H=500, PI+X=5000.
    Drawn as vector paths so it renders without an Ancient Greek Numbers font."""
    w = h * 0.78
    L, R, T = x - w / 2, x + w / 2, y - h
    d = f"M{L:.2f} {y:.2f}V{T:.2f}H{R:.2f}V{y:.2f}"          # the PI
    ih, iy = h * 0.46, y - h * 0.10                            # nested letter box
    il, ir = x - w * 0.26, x + w * 0.26
    it = iy - ih
    if inner == "D":                                            # delta, triangle
        d += f"M{il:.2f} {iy:.2f}L{x:.2f} {it:.2f}L{ir:.2f} {iy:.2f}Z"
    elif inner == "H":                                          # eta
        d += (f"M{il:.2f} {iy:.2f}V{it:.2f}M{ir:.2f} {iy:.2f}V{it:.2f}"
              f"M{il:.2f} {(iy+it)/2:.2f}H{ir:.2f}")
    elif inner == "X":                                          # chi
        d += f"M{il:.2f} {iy:.2f}L{ir:.2f} {it:.2f}M{ir:.2f} {iy:.2f}L{il:.2f} {it:.2f}"
    return d


def attic(n):
    """Attic acrophonic numeral. I=1, P(pente)=5, D(deka)=10."""
    s = "&#916;" * (n // 10)
    r = n % 10
    if r >= 5: s += "&#928;"; r -= 5
    return s + "&#921;" * r


def render(c, g):
    f = lambda v: f"{v:.3f}".rstrip("0").rstrip(".")
    L, A = [], None
    L_append = L.append
    A = L_append
    PW_, PH_ = g["PANEL_W"], g["PANEL_H"]

    # Display vs fabrication.
    #   default : width="100%" and a margin around the panel, so it FILLS the
    #             view and sits centred with breathing room, like the reference
    #             mockup. Coordinates are still millimetres, so it stays exact.
    #   --fab   : explicit mm width/height and zero margin, panel flush to the
    #             SVG edge, for the board house.
    M = 0.0 if c["fab_output"] else c["view_margin_mm"]
    if c["fab_output"]:
        size = f'width="{f(PW_)}mm" height="{f(PH_)}mm"'
    else:
        size = 'width="100%"'
    A(f'<svg xmlns="http://www.w3.org/2000/svg" {size} '
      f'viewBox="{f(-M if M else 0.0)} {f(-M if M else 0.0)} '
      f'{f(PW_ + 2*M)} {f(PH_ + 2*M)}" role="img">')
    A(f'<title>Vuulgaris V1 faceplate, {f(PW_)} x {f(PH_)}mm, true scale</title>')
    A(f'<desc>Salamis Tablet faceplate at true millimetre scale. Four capacitive scrub pads '
      f'{f(g["PL"])}mm long and {f(g["PW"])}mm wide at {f(g["PITCH"])}mm pitch '
      f'({f(g["GAP"])}mm gap), each drawn as {g["N_TEETH"]} comb teeth split into complementary '
      f'top and bottom bars across four interpolation zones in the order RX0 RX1 RX2 RX3 RX0. '
      f'Above a straight divider rule, eight channel knobs on rules 2 and 4, a vertical divider, '
      f'four envelope and CV amount knobs with the larger analog offset knob on rule 3, '
      f'{c["n_switches"]} vertical switch slots, LPG mode and source, '
      f'and the OLED at the right. {c["n_ticks"]} tick divisions per pad '
      f'with crosses at marks {", ".join(str(m) for m in c["cross_at"])}, Greek acrophonic '
      f'numerals in the margins, and the rotary encoder in the right margin beside the pads.</desc>')
    A(f'<rect x="0.4" y="0.4" width="{f(PW_-0.8)}" height="{f(PH_-0.8)}" rx="1.5" '
      f'fill="none" stroke="{INK2}" stroke-width="0.3"/>')

    # rules
    A(f'<g id="rules" stroke="{INK3}" stroke-width="0.18" fill="none">')
    for ry in g["RULE_Y"]:
        A(f'<line x1="{f(g["ch_x0"]-2)}" y1="{f(ry)}" x2="{f(g["env_x0"]+g["ENV_W"]+2)}" y2="{f(ry)}"/>')
    A('</g>')
    r12 = 12 * g["S"]
    A(f'<g id="upper-divider" stroke="{INK}" stroke-width="0.3" fill="none">'
      f'<line x1="{f(g["UP_DIV"])}" y1="{f(g["RULE_Y"][0]-3)}" x2="{f(g["UP_DIV"])}" y2="{f(g["RULE_Y"][4]+3)}"/>'
      f'<path d="M{f(g["UP_DIV"]-r12)} {f(g["RULE_Y"][4])} A{f(r12)} {f(r12)} 0 0 0 '
      f'{f(g["UP_DIV"]+r12)} {f(g["RULE_Y"][4])}"/></g>')

    # knobs
    A(f'<g id="knobs-channel" fill="none" stroke="{KNOB_INK}" stroke-width="0.3">')
    for cx in g["CH_CX"]:
        for cy in (g["R2"], g["R4"]):
            A(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(c["knob_r_mm"])}"/>')
    A('</g>')
    A(f'<g id="channel-numerals" font-family="sans-serif" font-size="3" fill="{INK}" text-anchor="middle">')
    for cx, n in zip(g["CH_CX"], range(1, 5)):
        A(f'<text x="{f(cx)}" y="{f(g["RULE_Y"][0]-1.5)}">{attic(n)}</text>')
    A('</g>')
    A(f'<g id="knobs-envelope" fill="none" stroke="{KNOB_INK}" stroke-width="0.3">')
    for cx in g["EN_CX"]:
        for cy in (g["R2"], g["R4"]):
            A(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(c["knob_r_mm"])}"/>')
    A('</g>')
    # RV1 (dual-gang offset) is column 3 top; drawn like the rest now that the
    # group is a uniform 2x2x2 block.

    # switches (vertical slots) + OLED
    sw_y = g["R3"] - c["switch_h_mm"] / 2.0
    A(f'<g id="switches" fill="none" stroke="{INK}" stroke-width="0.3">')
    for i in range(c["n_switches"]):
        A(f'<rect x="{f(g["ui_x0"]+3+i*(c["switch_w_mm"]+4))}" y="{f(sw_y)}" '
          f'width="{f(c["switch_w_mm"])}" height="{f(c["switch_h_mm"])}" rx="{f(c["switch_w_mm"]/2)}"/>')
    A('</g>')
    A(f'<g id="oled" fill="none" stroke="{INK}" stroke-width="0.3">'
      f'<rect x="{f(g["oled_x0"])}" y="{f(g["OLED_Y"])}" width="{f(c["oled_w_mm"])}" '
      f'height="{f(c["oled_h_mm"])}" rx="1"/></g>')

    # divider rule
    if c["straight_divider"]:
        A(f'<line id="divider-rule" x1="0" y1="{f(g["DIV_Y"])}" x2="{f(PW_)}" y2="{f(g["DIV_Y"])}" '
          f'stroke="{INK}" stroke-width="0.45"/>')
    else:
        ux = lambda u: (u - 42.0) * g["S"]
        pts = [(42,150),(112,146),(182,153),(247,147),(312,154),(382,148),(447,155),(512,149),(572,154),(622,148)]
        A('<path id="divider-rule" d="M' + ' L'.join(f'{f(ux(a))} {f(g["uy"](b))}' for a,b in pts) +
          f'" fill="none" stroke="{INK}" stroke-width="0.45"/>')

    # copper, one group per net
    bars = {0: [], 1: [], 2: [], 3: []}
    for y0 in g["PAD_TOPS"]:
        for net, x, y, w, h in teeth(c, g, y0):
            # Fillet each tooth's own corners. Clamped per tooth, because the
            # shortest bars are only 0.236mm tall and rx must not exceed half
            # the smaller dimension or the rect degenerates into a lozenge.
            rr = min(c["tooth_fillet_mm"], w / 2.0, h / 2.0)
            rx = f' rx="{f(rr)}"' if rr > 0.0 else ""
            bars[net].append(f'<rect x="{f(x)}" y="{f(y)}" '
                             f'width="{f(w)}" height="{f(h)}"{rx}/>')
    for net in (0, 1, 2, 3):
        A(f'<g id="{NET_NAME[net]}" fill="{NET_COLOR[net]}" stroke="none">')
        L.extend(bars[net])
        A('</g>')

    # encoder
    A(f'<g id="encoder" fill="none" stroke="{INK}" stroke-width="0.3">'
      f'<circle cx="{f(g["ENC_CX"])}" cy="{f(g["ENC_CY"])}" r="{f(c["encoder_r_mm"])}"/></g>')
    if c["shift_button"]:
        A(f'<g id="shift-button" fill="none" stroke="{INK}" stroke-width="0.3">'
          f'<circle cx="{f(g["SHIFT_CX"])}" cy="{f(g["SHIFT_CY"])}" '
          f'r="{f(c["shift_r_mm"])}"/></g>')

    # MX keycaps, 2x2 cluster
    if c.get("controls_left") and c.get("mx_buttons"):
        cap = c["mx_cap_mm"]
        A(f'<g id="mx-buttons" fill="none" stroke="{INK}" stroke-width="0.3">')
        for cy in g["MX_CY"]:
            for cx in g["MX_CX"]:
                A(f'<rect x="{f(cx-cap/2)}" y="{f(cy-cap/2)}" width="{f(cap)}" '
                  f'height="{f(cap)}" rx="1.6"/>')
        A('</g>')

    # the four channel buttons, in the left control column
    if c.get("controls_left") and g["BTN_CY"]:
        A(f'<g id="buttons" fill="none" stroke="{INK}" stroke-width="0.3">')
        for cy in g["BTN_CY"]:
            A(f'<circle cx="{f(g["BTN_CX"])}" cy="{f(cy)}" r="{f(c["button_r_mm"])}"/>')
        A('</g>')

    # pad divider + semicircle
    A(f'<g id="pad-marks" stroke="{INK}" stroke-width="0.3" fill="none">'
      f'<line x1="{f(g["PAD_MID"])}" y1="{f(g["PAD_TOPS"][0]-2.2)}" x2="{f(g["PAD_MID"])}" '
      f'y2="{f(g["PAD_TOPS"][3]+g["PW"]+2.2)}"/>'
      f'<path d="M{f(g["PAD_MID"]-r12)} {f(g["PAD_TOPS"][0])} A{f(r12)} {f(r12)} 0 0 1 '
      f'{f(g["PAD_MID"]+r12)} {f(g["PAD_TOPS"][0])}"/></g>')

    # ticks + crosses
    tk, cr = [], []
    for y0 in g["PAD_TOPS"]:
        yb = y0 + g["PW"]
        for k, x in enumerate(g["TICK_X"]):
            if (k + 1) in c["cross_at"]:
                cr.append(f'M{f(x-1.6)} {f(yb+1.4)}h3.2M{f(x)} {f(yb-0.2)}v3.2')
            else:
                tk.append(f'M{f(x)} {f(yb+0.3)}v1.4')
    A(f'<g id="ticks" stroke="{INK3}" stroke-width="0.2" fill="none"><path d="{"".join(tk)}"/></g>')
    A(f'<g id="crosses" stroke="{INK}" stroke-width="0.3" fill="none"><path d="{"".join(cr)}"/></g>')

    # numerals
    A(f'<g id="numerals" font-family="sans-serif" font-size="3.2" fill="{INK}">')
    for y0, n in zip(g["PAD_TOPS"], range(1, 5)):
        A(f'<text x="{f(g["PAD_X0"]-2)}" y="{f(y0+g["PW"]*0.72)}" text-anchor="end">{attic(n)}</text>')
        A(f'<text x="{f(g["PAD_X1"]+2)}" y="{f(y0+g["PW"]*0.72)}">{attic(n)}</text>')
    by = g["PAD_TOPS"][3] + g["PW"] + c["numeral_row_mm"]
    for m in c["cross_at"]:
        A(f'<text x="{f(g["TICK_X"][m-1])}" y="{f(by)}" text-anchor="middle">{attic(m)}</text>')
    A('</g>')

    # ---- Salamis authenticity marks (additive only) -------------------------
    if c["salamis_marks"]:
        # LEFT MARGIN ONLY, and confined below the divider rule.
        seq = list(c["inscription"])
        gh = c["inscription_h_mm"]
        y0 = (g["DIV_Y"] + 6.5) if c["inscription_below_divider"] else 12.0
        y1 = PH_ - 6.0
        step = (y1 - y0) / (len(seq) - 1)
        dl = [archaic_glyph(ch, 8.0, y0 + i * step, gh) for i, ch in enumerate(seq)]
        A(f'<g id="inscription-left" fill="none" stroke="{INK3}" stroke-width="0.32" '
          f'stroke-linecap="round" stroke-linejoin="round"><path d="{"".join(dl)}"/></g>')
        if not c["inscription_left_only"]:
            dr = [archaic_glyph(ch, PW_ - 7.0, y0 + i * step, gh)
                  for i, ch in enumerate(seq)
                  if abs(y0 + i * step - g["ENC_CY"]) > c["encoder_r_mm"] + 3.5]
            A(f'<g id="inscription-right" fill="none" stroke="{INK3}" stroke-width="0.32" '
              f'stroke-linecap="round" stroke-linejoin="round"><path d="{"".join(dr)}"/></g>')

    A('</svg>')
    return "\n".join(L)


def check(c, g):
    """Verification report. Every assertion that has bitten us at least once."""
    out, ok = [], True
    def row(label, val, good):
        nonlocal ok
        ok = ok and good
        out.append(f"  {'OK  ' if good else 'FAIL'}  {label:44} {val}")

    PW_, PL = g["PANEL_W"], g["PL"]
    out.append(f"panel {PW_:.2f} x {g['PANEL_H']:.2f}mm   pad {PL}x{g['PW']}mm   "
               f"gap {g['GAP']}mm   pitch {g['PITCH']}mm")
    out.append(f"teeth {g['N_TEETH']}/pad, pitch {g['T_PITCH']:.3f}mm, width {g['T_WIDTH']:.3f}mm")
    out.append("")

    lm, rm = g["PAD_X0"], PW_ - g["PAD_X1"]
    if c.get("controls_left"):
        # deliberately asymmetric: the left margin carries the control column
        row("pads clear both walls",
            f"margins {lm:.3f} / {rm:.3f}mm, wall {c['enclosure_wall_mm']}mm",
            lm > c["enclosure_wall_mm"] and rm > c["enclosure_wall_mm"])
        row("pad shift matches config", f"{c['pad_x_shift_mm']:.3f}mm right",
            abs((lm - rm) / 2.0 - c["pad_x_shift_mm"]) < 1e-6)
    else:
        row("pads centred on panel width", f"margins {lm:.3f} / {rm:.3f}mm", abs(lm - rm) < 1e-6)
    row("pad divider on pad midpoint", f"{g['PAD_MID']:.3f}mm", True)
    mid_tick = g["TICK_X"][c["n_ticks"] // 2]
    row("centre tick == pad divider", f"{mid_tick:.3f} vs {g['PAD_MID']:.3f}",
        abs(mid_tick - g["PAD_MID"]) < 0.01 and c["n_ticks"] % 2 == 1)
    sp = {round(g["TICK_X"][i+1] - g["TICK_X"][i], 6) for i in range(len(g["TICK_X"])-1)}
    row("tick spacing even", f"{sorted(sp)} mm", len(sp) == 1)
    fr = [round((g["TICK_X"][m-1] - g["PAD_X0"]) / PL, 4) for m in c["cross_at"]]
    row("crosses on clean fractions", f"{fr}", fr == [0.25, 0.5, 0.75])
    if c["center_pads_in_region"]:
        region = g["PANEL_H"] - g["DIV_Y"]
        need = g["BLOCK_H"] + c["numeral_row_mm"]
        row("pad block + numerals fit below the divider",
            f"{need:.1f} in {region:.1f}mm", need <= region + 0.01)
    else:
        row("pad block fits lower region", f"{g['BLOCK_H']:.1f} in {g['AVAIL']:.1f}mm",
            g["BLOCK_H"] <= g["AVAIL"] + 0.01)
    above = g["PAD_Y0"] - g["DIV_Y"]
    below = g["PANEL_H"] - (g["PAD_TOPS"][3] + g["PW"])
    row("pad block centred below the divider", f"{above:.2f} above / {below:.2f} below",
        abs(above - below) < 0.05)
    nb = g["PAD_TOPS"][3] + g["PW"] + c["numeral_row_mm"]
    row("bottom numerals inside the panel", f"baseline {nb:.2f} of {g['PANEL_H']:.2f}",
        nb < g["PANEL_H"] - 2.0)

    # copper: test the REAL emitted geometry, not the idealised presence
    # function. An earlier version recomputed from presences() and so never
    # looked at the rounded ends at all.
    usable = g["PW"] - c["top_bottom_gap_mm"]
    r = c["pad_corner_r_mm"]
    x0, x1 = g["PAD_X0"], g["PAD_X1"]
    y_top = g["PAD_TOPS"][0]
    rects = teeth(c, g, y_top)

    row("min copper bar >= fab floor",
        f"{min(h for _, _, _, _, h in rects):.4f} vs {c['min_copper_mm']}mm",
        min(h for _, _, _, _, h in rects) >= c["min_copper_mm"])

    # away from the corner zones a top/bottom pair must still fill the pad
    mids = {}
    for _, x, y, w, h in rects:
        if x - x0 > r and x1 - (x + w) > r:
            mids[round(x, 6)] = mids.get(round(x, 6), 0.0) + h
    bad = [x for x, s in mids.items() if abs(s - usable) > 1e-6]
    row("tooth pairs fill the pad, away from the ends",
        f"{len(mids)} columns, {usable:.2f}mm", not bad)

    # nothing may poke outside the rounded outline
    worst = 0.0
    for _, x, y, w, h in rects:
        for px in (x, x + w):
            ins = corner_inset(px, x0, x1, r)
            worst = max(worst, (y_top + ins) - y, (y + h) - (y_top + g["PW"] - ins))
    row("no copper outside the rounded outline", f"worst overhang {worst:.4f}mm",
        worst <= 1e-9)

    # tooth fillets: must never exceed half the smaller dimension
    tf = c["tooth_fillet_mm"]
    worst_rr, clamped = 0.0, 0
    for _, x, y, w, h in rects:
        rr = min(tf, w / 2.0, h / 2.0)
        if rr < tf - 1e-9:
            clamped += 1
        worst_rr = max(worst_rr, rr)
    row("tooth fillet within half the smaller side",
        f"r={tf}mm, {clamped} of {len(rects)} teeth clamped to fit",
        worst_rr <= tf + 1e-9)
    row("pad ends not tapered", f"pad_corner_r_mm = {r}", True)

    # THE ONE THAT MATTERS: position is read from the copper AREA ratio between
    # the top and bottom bars, so fillets bend the position curve unless the
    # heights are pre-compensated. Measure it on the emitted geometry.
    # Compare the emitted AREA ratio against the fraction the presence function
    # ASKED FOR. Comparing area against emitted height would be circular, since
    # compensation works precisely by making the heights non-linear.
    cols = {}
    for net, x, y, w, h in rects:
        rr = min(tf, w / 2.0, h / 2.0)
        area = w * h - 4.0 * (rr * rr - math.pi * rr * rr / 4.0)
        # Classify by NET, not by y. A tooth whose complement fell below the
        # fab floor takes the FULL pad height and therefore starts at y_top
        # whichever bar it is, so position is not a reliable classifier.
        # RX0/RX2 are the top bars, RX1/RX3 the bottom (ADR 0003).
        d = cols.setdefault(round(x, 6), [0.0, 0.0])
        d[0 if net in (0, 2) else 1] += area
    err = 0.0
    for i in range(g["N_TEETH"]):
        p = presences((i + 0.5) / g["N_TEETH"] * 4.0)
        want = p[0] + p[2]
        d = cols.get(round(g["PAD_X0"] + i * g["T_PITCH"], 6))
        if not d or d[0] + d[1] <= 0:
            continue
        err = max(err, abs(d[0] / (d[0] + d[1]) - want))
    row("fillet does not bend the position curve",
        f"worst {err*100:.3f}% of scale = {err*g['PL']:.2f}mm on a {g['PL']:.0f}mm pad",
        err * g["PL"] < 0.5)

    # upper region
    row("upper assembly centred", f"content {g['UP_CONTENT']:.2f}, margins {g['UP_MARG']:.2f}mm",
        g["UP_MARG"] > 0)
    er = c["encoder_r_mm"]
    if c["encoder_lower_right"]:
        if c.get("controls_left"):
            row("control column clears pads",
                f"{g['PAD_X0']-(g['ENC_CX']+er):.2f}mm",
                g["ENC_CX"] + er < g["PAD_X0"])
        else:
            row("encoder clears pads", f"{g['ENC_CX']-er-g['PAD_X1']:.2f}mm", g["ENC_CX"]-er > g["PAD_X1"])
        # measured against the INNER WALL FACE, not the panel edge
        _rlim = PW_ - c["enclosure_wall_mm"]
        if c.get("controls_left"):
            _llim = c["enclosure_wall_mm"]
            row("control column centred in the left margin",
                f"{(g['ENC_CX']-er)-_llim:.2f} / {g['PAD_X0']-(g['ENC_CX']+er):.2f}mm",
                abs(((g["ENC_CX"]-er)-_llim) - (g["PAD_X0"]-(g["ENC_CX"]+er))) < 2.0)
            btm = (g["MX_CY"][-1] + c["mx_cap_mm"]/2.0) if c.get("mx_buttons") else \
                  ((g["BTN_CY"][-1] + c["button_r_mm"]) if g["BTN_CY"] else g["SHIFT_CY"])
            row("control column inside the walls (vertical)",
                f"{g['ENC_CY']-er:.2f} .. {btm:.2f} of {c['enclosure_wall_mm']}..{g['PANEL_H']-c['enclosure_wall_mm']:.1f}",
                g["ENC_CY"]-er > c["enclosure_wall_mm"] and btm < g["PANEL_H"]-c["enclosure_wall_mm"])
            _bx = (g["MX_CX"][-1] + c["mx_cap_mm"]/2.0) if c.get("mx_buttons") \
                  else (g["BTN_CX"] + c["button_r_mm"])
            row("buttons clear the pads", f"{g['PAD_X0']-_bx:.2f}mm", _bx < g["PAD_X0"])
        else:
            row("encoder centred in the cavity margin",
                f"{g['ENC_CX']-er-g['PAD_X1']:.2f} / {_rlim-(g['ENC_CX']+er):.2f}mm",
                abs((g["ENC_CX"]-er-g["PAD_X1"]) - (_rlim-(g["ENC_CX"]+er))) < 0.01)
        if not c.get("controls_left"):
            ox0, ox1 = g["oled_x0"], g["oled_x0"] + c["oled_w_mm"]
            row("encoder within OLED span", f"{ox0:.1f} <= {g['ENC_CX']:.1f} <= {ox1:.1f}",
                ox0 <= g["ENC_CX"] <= ox1)
    if c["shift_button"]:
        sr = c["shift_r_mm"]
        row("shift on the encoder axis", f"x {g['SHIFT_CX']:.2f}",
            abs(g["SHIFT_CX"] - g["ENC_CX"]) < 1e-9)
        row("shift clears the encoder",
            f"{(g['SHIFT_CY']-sr)-(g['ENC_CY']+er):.2f}mm gap",
            (g["SHIFT_CY"] - sr) - (g["ENC_CY"] + er) >= 1.0)
        if c.get("controls_left"):
            row("shift clears the pads", f"{g['PAD_X0']-(g['SHIFT_CX']+sr):.2f}mm",
                g["SHIFT_CX"] + sr < g["PAD_X0"])
        else:
            row("shift clears the pads", f"{g['SHIFT_CX']-sr-g['PAD_X1']:.2f}mm",
                g["SHIFT_CX"] - sr > g["PAD_X1"])
        # Right-side pad numerals: x from PAD_X1+2, baseline pad_top + PW*0.72.
        # Only meaningful when the controls are on the right; the left column is
        # nowhere near them.
        if not c.get("controls_left"):
            num_x0 = g["PAD_X1"] + 2.0
            num_x1 = num_x0 + 4 * 0.45 * 3.2
            gapx = (g["SHIFT_CX"] - sr) - num_x1
            rows_near = [t + g["PW"] * 0.72 for t in g["PAD_TOPS"]
                         if abs(t + g["PW"] * 0.72 - g["SHIFT_CY"]) < sr + 3.4]
            row("shift clears right-side numerals",
                f"{gapx:.2f}mm horizontal" + (f", {len(rows_near)} row(s) alongside"
                                              if rows_near else ""),
                gapx > 2.0)
        pad_mid = (g["PAD_TOPS"][0] + g["PAD_TOPS"][3] + g["PW"]) / 2.0
        if c.get("controls_left"):
            # the whole column is what gets centred now, not the encoder+shift pair
            btm = (g["MX_CY"][-1] + c["mx_cap_mm"]/2.0) if c.get("mx_buttons") else \
                  ((g["BTN_CY"][-1] + c["button_r_mm"]) if g["BTN_CY"] else g["SHIFT_CY"] + sr)
            col_mid = ((g["ENC_CY"] - er) + btm) / 2.0
            row("control column centred on the pad block",
                f"column mid {col_mid:.2f} vs pads {pad_mid:.2f}",
                abs(col_mid - pad_mid) < 6.0)
        else:
            pair_mid = ((g["ENC_CY"] - er) + (g["SHIFT_CY"] + sr)) / 2.0
            row("encoder+shift centred on the pad block",
                f"pair mid {pair_mid:.2f} vs pads {pad_mid:.2f}",
                abs(pair_mid - pad_mid) < 0.05)
        row("shift inside panel",
            f"bottom {g['SHIFT_CY']+sr:.2f} of {g['PANEL_H']:.2f}",
            g["SHIFT_CY"] + sr < g["PANEL_H"] - c["bottom_margin_mm"])
    row("switch slots vertical", f"{c['switch_w_mm']} x {c['switch_h_mm']}mm",
        c["switch_h_mm"] > c["switch_w_mm"])
    row("switch count", f"{c['n_switches']} (LPG mode + source, both DPDT)",
        c["n_switches"] == 2)
    # At reduced panel depth the OLED is the VERTICAL floor of the upper strip:
    # 42mm of screen has to fit above the divider rule. This is the check that
    # decides how far the depth can be cut.
    _ot = g["OLED_Y"]
    row("OLED clears the divider rule",
        f"bottom {_ot+c['oled_h_mm']:.2f} vs divider {g['DIV_Y']:.2f} "
        f"({g['DIV_Y']-(_ot+c['oled_h_mm']):+.2f}mm)",
        _ot + c["oled_h_mm"] < g["DIV_Y"])
    # Channel knobs stand on rules 2 and 4, NOT 2 and 3. Rule 3 carries the
    # offset knob, which sits in a different group horizontally.
    row("knob rows do not overlap",
        f"{g['R4']-g['R2']-2*c['knob_r_mm']:+.2f}mm between rows",
        g["R4"] - g["R2"] > 2 * c["knob_r_mm"])
    row("knob rows inside the upper strip",
        f"top {g['R2']-c['knob_r_mm']:.2f}, bottom {g['R4']+c['knob_r_mm']:.2f} of {g['DIV_Y']:.2f}",
        g["R2"] - c["knob_r_mm"] > 0 and g["R4"] + c["knob_r_mm"] < g["DIV_Y"])
    # ---- enclosure fit: the main PCB lives INSIDE the cheeks ----------------
    wall, need = c["enclosure_wall_mm"], c["wall_clearance_mm"]
    lo, hi = g["UP_MARG"], g["oled_x0"] + c["oled_w_mm"]
    row("upper assembly clears the enclosure walls",
        f"{lo-wall:.2f} / {PW_-hi-wall:.2f}mm at {wall:.0f}mm cheeks",
        min(lo - wall, PW_ - hi - wall) >= need)
    # FOUR-SIDED cavity check. The earlier version only tested left and right,
    # which is why a 6mm top-wall collision with the OLED went unnoticed for the
    # whole life of the layout. Every object that lives INSIDE the box goes in.
    box = []
    for cx in g["CH_CX"]:
        for cy in (g["R2"], g["R4"]):
            box.append((cx-c["knob_r_mm"], cx+c["knob_r_mm"], cy-c["knob_r_mm"], cy+c["knob_r_mm"]))
    for cx in g["EN_CX"]:
        for cy in (g["R2"], g["R4"]):
            box.append((cx-c["knob_r_mm"], cx+c["knob_r_mm"], cy-c["knob_r_mm"], cy+c["knob_r_mm"]))

    box.append((g["oled_x0"], g["oled_x0"]+c["oled_w_mm"], g["OLED_Y"], g["OLED_Y"]+c["oled_h_mm"]))
    sy0 = g["R3"] - c["switch_h_mm"]/2.0
    for i in range(c["n_switches"]):
        sx = g["ui_x0"]+3+i*(c["switch_w_mm"]+4)
        box.append((sx, sx+c["switch_w_mm"], sy0, sy0+c["switch_h_mm"]))
    box.append((g["ENC_CX"]-er, g["ENC_CX"]+er, g["ENC_CY"]-er, g["ENC_CY"]+er))
    if c["shift_button"]:
        sr2 = c["shift_r_mm"]
        box.append((g["SHIFT_CX"]-sr2, g["SHIFT_CX"]+sr2, g["SHIFT_CY"]-sr2, g["SHIFT_CY"]+sr2))
    bx0, bx1 = min(b[0] for b in box), max(b[1] for b in box)
    by0, by1 = min(b[2] for b in box), max(b[3] for b in box)
    for nm, clr in (("LEFT", bx0-wall), ("RIGHT", (PW_-wall)-bx1),
                    ("TOP", by0-wall), ("BOTTOM", (g["PANEL_H"]-wall)-by1)):
        row(f"cavity clearance, {nm}", f"{clr:+.2f}mm", clr >= need)
    row("pads clear the enclosure walls",
        f"{g['PAD_X0']-wall:.2f}mm", g["PAD_X0"] - wall >= need)
    row("max main PCB width",
        f"{PW_-2*wall-2:.1f}mm inside {wall:.0f}mm cheeks", PW_ - 2*wall - 2 > 0)
    scr = c["panel_screw_inset_mm"]
    row("panel screws land on the cheek, not past it",
        f"screw at {scr:.1f}mm, cheek spans 0..{wall:.1f}mm", 1.5 <= scr <= wall - 1.5)
    row("OLED inside panel", f"right edge {g['oled_x0']+c['oled_w_mm']:.2f} of {PW_:.2f}",
        g["oled_x0"] + c["oled_w_mm"] <= PW_)
    if c["salamis_marks"]:
        seq = list(c["inscription"])
        gw = c["inscription_h_mm"] * 0.58
        y0 = (g["DIV_Y"] + 6.5) if c["inscription_below_divider"] else 12.0
        step = (g["PANEL_H"] - 6.0 - y0) / (len(seq) - 1)
        rows = [y0 + i * step for i in range(len(seq))]
        row("inscription letters", f"{len(seq)}, left margin only", len(seq) > 0)
        row("LEFT SIDE ONLY", "right column suppressed", c["inscription_left_only"])
        row("none above the divider rule",
            f"topmost {min(rows)-c['inscription_h_mm']:.2f} vs divider {g['DIV_Y']:.2f}",
            min(rows) - c["inscription_h_mm"] > g["DIV_Y"])
        row("clears the pads", f"{8.0+gw/2:.1f} vs pad x0 {g['PAD_X0']:.1f}",
            8.0 + gw / 2 < g["PAD_X0"])
        row("inside panel", f"bottom {max(rows):.1f} of {g['PANEL_H']:.1f}",
            max(rows) <= g["PANEL_H"] - 1.0)
        row("letters do not collide vertically", f"step {step:.2f} vs height "
            f"{c['inscription_h_mm']}mm", step > c["inscription_h_mm"] + 1.0)
    out.append("")
    out.append("  ALL CHECKS PASS" if ok else "  *** FAILURES ABOVE ***")
    return "\n".join(out), ok


def placement(c, g):
    """Emit hardware/placement-panel-facing.txt.

    This is the ONLY place these coordinates should come from. The file used to
    say it was generated here while actually being hand-maintained, which meant
    the panel artwork and the PCB placement could drift apart silently.
    """
    L = []
    A = L.append
    A("# Vuulgaris V1 panel-facing placement, generated from mockups/generate-faceplate.py")
    A("#   python3 mockups/generate-faceplate.py --placement > hardware/placement-panel-facing.txt")
    A("# ORIGIN: panel top-left corner. X right, Y DOWN. Millimetres.")
    A(f"# Panel {g['PANEL_W']:.3f} x {g['PANEL_H']:.3f}mm. All parts on the MAIN PCB,")
    A("# protruding through faceplate openings, EXCEPT the pads which are faceplate copper.")
    A("")
    A(f"{'REF':<7} {'PART':<42} {'X':>9} {'Y':>9}  NOTE")
    rows = []
    for i, cx in enumerate(g["CH_CX"]):
        for j, cy in enumerate((g["R2"], g["R4"])):
            n = i * 2 + j + 1
            rows.append((f"ENC{n}", f"encoder, ch{i+1} {'AB'[j]}", cx, cy, "-> MCP23017"))
    for j, cy in enumerate((g["R2"], g["R4"])):
        rows.append((f"ENC{9+j}", f"encoder, envelope {'ATTACK RELEASE'.split()[j]}",
                     g["EN_CX"][0], cy, "-> MCP23017"))
    rows.append(("RV2", "POT 9mm, CV amount L", g["EN_CX"][1], g["R2"], "ANALOG -> LPG"))
    rows.append(("RV3", "POT 9mm, CV amount R", g["EN_CX"][1], g["R4"], "ANALOG -> LPG"))
    rows.append(("RV1", "POT 9mm DUAL-GANG, LPG OFFSET", g["EN_CX"][2], g["R2"], "ANALOG -> LPG"))
    rows.append(("RV4", "POT 9mm, RESONANCE", g["EN_CX"][2], g["R4"], "ANALOG -> LPG"))
    for i in range(c["n_switches"]):
        sx = g["ui_x0"] + 3 + i * (c["switch_w_mm"] + 4.0) + c["switch_w_mm"] / 2.0
        rows.append((f"SW{1+i}",
                     "DPDT LPG mode VCF/VCA" if i == 0 else "DPDT SOURCE resample/ext",
                     sx, g["R3"], "ANALOG -> LPG"))
    rows.append(("DS1", "OLED 2.42in SSD1309 (TOP-LEFT)", g["oled_x0"], g["OLED_Y"], "SPI -> Daisy"))
    rows.append(("ENC0", "encoder + PUSH, main UI", g["ENC_CX"], g["ENC_CY"], "-> MCP23017 U4 GPB0-2"))
    if c.get("shift_button"):
        rows.append(("SW3", "tactile, SHIFT", g["SHIFT_CX"], g["SHIFT_CY"], "-> Daisy A9"))
    if c.get("mx_buttons"):
        n = 0
        for cy in g["MX_CY"]:
            for cx in g["MX_CX"]:
                rows.append((f"SW{4+n}", f"Cherry MX key {n+1} (general UI)", cx, cy,
                             f"-> MCP23017 U4 GPA{4+n}"))
                n += 1
    else:
        for k, cy in enumerate(g["BTN_CY"]):
            rows.append((f"SW{4+k}", f"tactile, UI button {k+1}", g["BTN_CX"], cy,
                         f"-> MCP23017 U4 GPA{4+k}"))
    for ref, part, x, y, note in rows:
        A(f"{ref:<7} {part:<42} {x:9.3f} {y:9.3f}  {note}")
    A("")
    A("# FACEPLATE COPPER (layer 1, exposed, no soldermask):")
    for i, t in enumerate(g["PAD_TOPS"], 1):
        A(f"#   pad{i}  x {g['PAD_X0']:.3f}..{g['PAD_X1']:.3f}   y {t:.3f}..{t + g['PW']:.3f}")
    A(f"#   {g['N_TEETH']} comb teeth per pad, pitch {g['T_PITCH']:.3f}mm, width {g['T_WIDTH']:.3f}mm")
    A("")
    A(f"# ENCLOSURE: {c['enclosure_wall_mm']:.0f}mm walls all round, panel screws onto the wall tops")
    cav_w = g["PANEL_W"] - 2 * c["enclosure_wall_mm"]
    cav_h = g["PANEL_H"] - 2 * c["enclosure_wall_mm"]
    A(f"#   cavity        {cav_w:.2f} x {cav_h:.2f}mm")
    A(f"#   MAIN PCB MAX  {cav_w - 2:.1f} x {cav_h - 2:.1f}mm")
    A("#   PCB ORIGIN sits at panel (%.3f, %.3f); pcb = panel - that offset"
      % (c["enclosure_wall_mm"] + 0.995, c["enclosure_wall_mm"] + 1.0))
    return "\n".join(L)


if __name__ == "__main__":
    cfg = dict(CFG)
    args = sys.argv[1:]
    for a in list(args):
        if a.startswith("--set"):
            i = args.index(a)
            kv = a.split("=", 1)[1] if "=" in a else args[i + 1]
            k, v = kv.split("=")
            cfg[k] = type(CFG[k])(float(v)) if not isinstance(CFG[k], tuple) else CFG[k]
    if "--fab" in args:
        cfg["fab_output"] = True
    geo = derive(cfg)
    if "--placement" in args:
        print(placement(cfg, geo))
        sys.exit(0)
    if "--check" in args:
        rep, ok = check(cfg, geo)
        print(rep)
        sys.exit(0 if ok else 1)
    sys.stdout.write(render(cfg, geo) + "\n")
    rep, ok = check(cfg, geo)
    sys.stderr.write(rep + "\n")
