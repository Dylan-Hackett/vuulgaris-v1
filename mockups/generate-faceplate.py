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
    "pad_gap_mm":          8.0,   # was 9.0; 1mm off each of 3 gaps to fit
                                  # the shorter panel. Width stays 10.0 --
                                  # that is the sensitivity number, ADR 0003 floor.
    # Depth. The COMPOSITION is laid out in this frame and every panel part's y
    # comes out of it, scaled, so changing it RE-FLOWS the panel and moves all
    # 24 panel parts on a routed main board. None = the original Salamis 1.933:1
    # ratio (154.29mm). 129 was chosen 2026-08-09 to shrink the footprint without
    # touching the gap; 130.81 on 2026-08-26 as board + 14 (board then 116.81).
    "composition_h_mm":  130.81,
    # Size changes since then go on OUTSIDE the frame, as pure extensions.
    # +2 at the top (jack) edge, 2026-09-27: the main board's top edge and the
    # wall moved out 2mm on 2026-09-23. Every panel y grows by exactly this, and
    # place.py's OY is 7.000 + this. --check proves the offset is pure.
    "panel_top_extra_mm":    2.0,
    # +5 at the bottom (back) edge, 2026-09-27: the board slides 6mm along y to
    # clear the jacks, so the cavity is 1 + 118.81 + 6 = 125.81, not board + 2,
    # and the panel covers the box to both outer faces. Moves nothing.
    "panel_bottom_extra_mm": 5.0,

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

    # ---- connecting the bars ------------------------------------------------
    # Every bar is its own island of copper: nothing joins them on L1. Each
    # one takes an open through-via (decided 2026-09-28, not filled or capped)
    # down to its net's bus on L2. The project's minimum via, JLC standard.
    # The hole is copper the finger does not see, so it goes into the same
    # area compensation as the fillets. A bar too short to hold the via's pad
    # (only the 0.197mm slivers beside each zone boundary) instead gets a
    # BRIDGE across the tooth gap to its same-net neighbour, at the pad edge,
    # and gives back the bridge's copper by shortening. See connections().
    "via_drill_mm":        0.3,
    "via_dia_mm":          0.5,
    "via_inset_mm":        0.5,   # via centre from the bar's OUTER edge (pad edge)
    "bridge_h_mm":         0.3,   # bridge strip height, or the thinner bar's if less
    # Through vias come out on the BACK, so they must clear whatever sits
    # there over the pads. Only J1 does: the hanxia 2x5's pads at panel
    # (228.995, 112.5), rows over the edges of pads 3 and 4 (hanxia drawing;
    # mkboard.py placed it). tools/panelcheck.py derives these rectangles
    # from J1's real pads on the board and fails if they differ.
    "via_keepouts_mm": ((223.405, 106.75, 234.585, 111.4),
                        (223.405, 113.6, 234.585, 118.25)),
    "via_keepout_clear_mm": 0.2,  # project Default clearance

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
    "switch_reserve_slots":  2,   # hold the row where it was; see ui_w
    # Dailywell 2MD1T1B1M2QES (Thonk DW3): the panel opening is a ROUND 4.95mm
    # bushing hole, not a slot. switch_w/h stay as the LAYOUT footprint the
    # switch occupies in the row; switch_hole_d_mm is what actually gets cut.
    "switch_hole_d_mm":    4.95,
    # Drop the switch pair below rule 3. Centred on R3 their through-holes land
    # inside the 1/4" jack footprints, and J8's pad 5 sits BETWEEN SW2's two pad
    # columns -- nowhere to nudge it, J7 blocks left and DS1/J9 block right.
    # 8.2mm puts them clear of the jacks (which end at pcb y 25) and level with
    # the lower pot row, which reads fine.
    "switch_y_shift_mm":   8.2,
    # Nudge the pair LEFT. At 0 SW2's body sits 0.33mm off the OLED.
    "switch_x_shift_mm":  -4.0,
    "switch_w_mm":         9.0,
    "switch_h_mm":        20.0,
    "oled_w_mm":          70.0,
    # Nudge the OLED left of where the composition flow puts it. At 0 its pads
    # collide with the SD socket and the USB-C, which live in the top-right
    # corner of the board -- a board-side constraint the composition cannot see.
    "oled_x_shift_mm":    -6.1,
    "oled_h_mm":          42.0,
    # ---- the OLED WINDOW (2026-09-28) ---------------------------------------
    # The cut is sized from the module, not from the oled_w/h box above -- that
    # box is a layout stand-in anchored on the header column. HS242L01W4S01
    # drawing (datasheets/HS242L01W4S01-OLED.pdf, section 1.4): PCB 72 x 43
    # (the spec table's "68 x 43" is the hole pitch), the 9-pin header 2.5mm in
    # from the left edge. Along the long axis the glass (FRAME 62.1), VA (57)
    # and AA (55.01) are centred, at 4.95 / 7.5 / 8.5 from each end. Across it
    # they are not: AA 5.11 below the top edge and 10.4 above the bottom, glass
    # 2.1 from the top and 1.05 from the bottom. The wide black band -- where
    # the flex bonds -- is on the player's side, which is the side that needs
    # the viewing margin. The main board's DS1 matches: holes 68 x 39 apart,
    # header at the left edge, pin 1 at the bottom.
    "oled_hdr_to_edge_mm":  2.5,
    "oled_aa_mm":    (8.5, 5.11, 55.01, 27.49),    # x from left edge, y from top edge, w, h
    "oled_glass_mm": (4.95, 2.1, 62.1, 39.85),
    # Stack-up: the pots are the datum, outer face 11.6mm above the main board;
    # the display face at lift + 4.2 (module height). The lift is not chosen yet
    # -- 3-5mm on a 1x9 socket and nylon standoffs (hardware/faceplate/README.md
    # section 4) -- so the window is sized at the DEEPEST, 3mm, and only gets
    # better if the module ends up higher.
    "panel_outer_mm":       11.6,
    "oled_module_h_mm":      4.2,
    "oled_lift_min_mm":      3.0,
    # How far past the active area the window opens, at that depth. The window
    # never opens nearer the glass edge than oled_glass_margin_mm (placement:
    # the faceplate locates on 7.5mm holes round M7 pots, +-0.25), so beyond the
    # AA it shows black glass, never the module's PCB.
    "oled_view_player_deg": 45.0,   # toward the player (+y): whole AA seen at 45 deg
    "oled_view_side_deg":   30.0,   # left, right and far, as far as the black glass allows
    "oled_glass_margin_mm":  1.0,
    "oled_window_r_mm":      1.0,   # corner radius: JLC routes internal corners round anyway
    "encoder_r_mm":        9.2,
    # Controls live in ONE column in the left margin: encoder, shift, then the
    # four channel buttons. Decided 2026-08-17. The pad block is pushed right to
    # open that margin; every panel-facing coordinate moves with it.
    "controls_left":      True,
    "pad_x_shift_mm":     20.0,
    "n_buttons":             4,
    "button_r_mm":         3.5,
    # Six UI buttons, 12x12 through-hole tactile, 2 wide x 3 tall. Was four
    # Cherry MX until 2026-09-06: six MX at 18mm caps on 19.05 pitch will not fit
    # the same panel area. The tactile's pads splay to 14.7mm, so the COLUMNS
    # keep the 19.05 pitch and only the ROWS tighten, to 12.7mm. Net effect on
    # the cluster envelope is 0.2mm, so ENC0 above it does not move.
    # 2026-09-08: no cap. TS1103S-12X12X14DIP (LCSC C54573007) is 14.0mm tall
    # against a panel outer face at 11.6mm, so its plunger stands 2.4mm proud and
    # IS the button face. A separate snap-on cap was only ever needed because the
    # old 7.3mm part could not reach the panel at all.
    "mx_buttons":         True,
    "mx_plunger_mm":       6.2,      # the plunger IS the button; nothing sits on the panel
    "mx_pitch_mm":        15.50,     # column pitch; floor is ~15.0, the TH pads collide below that
    "mx_row_pitch_mm":    12.7,      # bodies are 12.0 square, so 0.7mm between them
    "mx_rows":               3,
    # Clearance hole for the plunger. Was 2.25 (4.5mm) when a 3.8mm SQUARE stem
    # was assumed -- which never fitted anyway, its diagonal is 5.37mm.
    "mx_hole_r_mm":        3.30,     # 6.6mm, clearing the 6.2mm round plunger

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
    # What the cavity has to hold along y (design-state "Assembly"): the jack
    # wall's 1mm assembly gap, the main board, and the travel it slides to put
    # its jacks through that wall. --check asserts the panel covers exactly this.
    "front_gap_mm":        1.0,
    "main_pcb_h_mm":     118.81,  # 2026-09-23, after the 2mm top-edge extension
    "slide_travel_mm":     6.0,

    "fab_output":        False,   # True = explicit mm size, flush edges
    "view_margin_mm":     10.0,   # breathing room around the panel on screen

    # ---- vertical margins in the lower region -------------------------------
    # True centres the pad block between the divider rule and the bottom edge.
    # The numeral row then sits in the space below rather than being reserved
    # out of the centring, which is what was pushing the pads high.
    "center_pads_in_region": True,
    "numeral_row_mm":      3.6,   # pad bottom to numeral baseline (was 4.5)
    "numeral_pt_mm":       2.7,   # glyph size (was a hardcoded 3.2)
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
    # Height was locked to the Salamis 1.933:1 ratio. composition_h_mm now
    # overrides it so depth can be reduced independently of the pad length. X and
    # Y therefore need SEPARATE scales; using one for both is what tied them.
    COMP_H = c["composition_h_mm"] or g["PANEL_W"] * (300.0 / 580.0)
    TOP, BOT = c["panel_top_extra_mm"], c["panel_bottom_extra_mm"]
    # The composition frame runs COMP_Y0..COMP_Y1 inside a panel that is TOP
    # taller above it and BOT taller below. Nothing below reads PANEL_H to place
    # a part: that is what keeps the extensions from re-flowing anything.
    g["COMP_H"], g["TOP_X"], g["BOT_X"] = COMP_H, TOP, BOT
    g["COMP_Y0"], g["COMP_Y1"] = TOP, TOP + COMP_H
    g["PANEL_H"] = TOP + COMP_H + BOT
    g["S"] = g["PANEL_W"] / 580.0                # reference-unit -> mm, HORIZONTAL
    INSET = (c["enclosure_wall_mm"] + c["wall_clearance_mm"]) if c["inset_composition"] else 0.0
    g["INSET"] = INSET
    g["SY"] = (COMP_H - 2.0 * INSET) / 300.0     # reference-unit -> mm, VERTICAL
    uy = lambda u: TOP + INSET + (u - 40.0) * g["SY"]
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
    avail = (g["COMP_Y1"] - (g["DIV_Y"] + c["below_divider_mm"])
             - c["numeral_row_mm"] - c["bottom_margin_mm"])
    g["BLOCK_H"], g["AVAIL"] = block, avail
    if c["center_pads_in_region"]:
        # Centre the pad BLOCK in the whole region between the divider rule and
        # the bottom edge, and let the numeral row live in the space beneath.
        # The old behaviour subtracted the numeral row before centring, which
        # left the pads visibly high: 5.6mm above, 17.1mm below.
        g["PAD_Y0"] = g["DIV_Y"] + (g["COMP_Y1"] - g["DIV_Y"] - block) / 2.0
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
    g["OLED_Y"] = TOP + INSET + ((g["DIV_Y"] - TOP - INSET) - c["oled_h_mm"]) / 2.0
    g["R2"], g["R3"], g["R4"] = g["RULE_Y"][1], g["RULE_Y"][2], g["RULE_Y"][3]
    # Switch centre-line. Computed ONCE here: the SVG, the validation box and
    # the placement rows all read it. They used to each recompute from R3,
    # which is how a y-shift reached the drawing but not the placement file.
    g["SW_CY"] = g["R3"] + c.get("switch_y_shift_mm", 0.0)
    ch_w = 3 * KP + 2 * KR
    env_w = 2 * KP + 2 * KR          # 3 columns x 2 rows: 2 encoders, 4 pots
    NSW = c["n_switches"]
    # Reserve the width the switches used to occupy even when none are drawn.
    # Letting the row re-centre when they went away moved every encoder and pot
    # 11mm right and drove RV1's pads through J7's -- a cosmetic change breaking
    # a verified layout. Set to 0 to genuinely reclaim the space.
    RSV = c.get("switch_reserve_slots", NSW)
    ui_w = RSV * c["switch_w_mm"] + max(0, RSV - 1) * 4.0 + 6.0
    if not c["encoder_lower_right"]:
        ui_w += 2 * c["encoder_r_mm"] + 6.0
    content = ch_w + UG + UG + env_w + UG + ui_w + UG + c["oled_w_mm"]
    g["UP_MARG"] = (g["PANEL_W"] - content) / 2.0
    g["UP_CONTENT"] = content
    g["ch_x0"] = g["UP_MARG"]
    g["UP_DIV"] = g["ch_x0"] + ch_w + UG
    g["env_x0"] = g["UP_DIV"] + UG
    g["ui_x0"] = g["env_x0"] + env_w + UG
    # Switch group left edge. Computed ONCE, like SW_CY. The SVG used to read
    # a g["sw_x0"] that was never assigned, so render() raised KeyError and
    # emitted NOTHING -- while --check and --placement, which skip render(),
    # both passed. A generator that crashes only on its main output.
    g["SW_X0"] = g["ui_x0"] + 3 + c.get("switch_x_shift_mm", 0.0)
    g["oled_x0"] = g["ui_x0"] + ui_w + UG + c.get("oled_x_shift_mm", 0.0)
    oled_window(c, g)
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
            P, CAP, er = c["mx_pitch_mm"], 2 * c["mx_hole_r_mm"], c["encoder_r_mm"]
            RP, NR = c["mx_row_pitch_mm"], c["mx_rows"]
            pad_mid = (g["PAD_TOPS"][0] + g["PAD_TOPS"][3] + PW) / 2.0
            gap = 6.0
            block = (NR - 1) * RP + CAP
            top = pad_mid - (2 * er + gap + block) / 2.0
            g["ENC_CY"] = top + er
            g["SHIFT_CY"] = None
            g["MX_CX"] = [col - P / 2.0, col + P / 2.0]
            first = top + 2 * er + gap + CAP / 2.0
            g["MX_CY"] = [first + i * RP for i in range(NR)]
            g["BTN_CY"] = []
        else:
            g["ENC_CY"] = TOP + 72.0
            g["SHIFT_CY"] = TOP + 87.0
            g["BTN_CY"] = [TOP + y for y in (97.0, 106.0, 115.0, 124.0)][:c.get("n_buttons", 4)]
    return g


def oled_window(c, g):
    """The OLED window, from the module drawing and the stack-up (CFG comments).
    Sets OLED_AA / OLED_GLASS / OLED_WIN as (x0, y0, x1, y1) panel mm, and
    OLED_DEPTH, the display face below the outer face at the deepest mount."""
    mx0 = g["oled_x0"] - c["oled_hdr_to_edge_mm"]     # module left edge
    my0 = g["OLED_Y"]                                 # module top edge (DS1's row)
    box = lambda r: (mx0 + r[0], my0 + r[1], mx0 + r[0] + r[2], my0 + r[1] + r[3])
    aa, gl = box(c["oled_aa_mm"]), box(c["oled_glass_mm"])
    d = c["panel_outer_mm"] - (c["oled_lift_min_mm"] + c["oled_module_h_mm"])
    t = lambda deg: d * math.tan(math.radians(deg))
    m = c["oled_glass_margin_mm"]
    g["OLED_AA"], g["OLED_GLASS"], g["OLED_DEPTH"] = aa, gl, d
    g["OLED_WIN"] = (aa[0] - min(t(c["oled_view_side_deg"]), aa[0] - gl[0] - m),
                     aa[1] - min(t(c["oled_view_side_deg"]), aa[1] - gl[1] - m),
                     aa[2] + min(t(c["oled_view_side_deg"]), gl[2] - m - aa[2]),
                     aa[3] + min(t(c["oled_view_player_deg"]), gl[3] - m - aa[3]))


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


def hole_area(c, h):
    """Copper a bar of height h loses to its via hole (none if it is too
    short to take a via and is bridged instead)."""
    if c.get("via_drill_mm", 0.0) <= 0.0 or h < c["via_dia_mm"]:
        return 0.0
    return math.pi * (c["via_drill_mm"] / 2.0) ** 2


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
                min(c["tooth_fillet_mm"], W / 2.0, max(h, 0.0) / 2.0)) + hole_area(c, h)
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


def in_rrect(px, py, x, y, w, h, r):
    """Point inside a rounded rectangle (corner radius r)."""
    if px < x or px > x + w or py < y or py > y + h:
        return False
    cx = min(max(px, x + r), x + w - r)
    cy = min(max(py, y + r), y + h - r)
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r + 1e-12


def bar_r(c, w, h):
    return min(c["tooth_fillet_mm"], w / 2.0, h / 2.0)


def rr_span(x, bx, by, bw, bh, r):
    """Vertical extent [y0, y1] of a rounded rectangle at abscissa x, or None."""
    if x < bx or x > bx + bw:
        return None
    d = min(x - bx, bx + bw - x)
    ins = 0.0 if d >= r else r - math.sqrt(max(r * r - (r - d) ** 2, 0.0))
    return by + ins, by + bh - ins


def bridge_extra(c, bridge, a, b, n=4000):
    """Copper a bridge ADDS: its area outside both rounded bars it joins.
    Integrated column by column; the bars are disjoint, so their overlaps
    with the bridge just subtract."""
    bx, by, bw, bh = bridge
    dx = bw / n
    tot = 0.0
    for i in range(n):
        x = bx + (i + 0.5) * dx
        cov = 0.0
        for q in (a, b):
            sp = rr_span(x, *q, bar_r(c, q[2], q[3]))
            if sp:
                cov += max(0.0, min(sp[1], by + bh) - max(sp[0], by))
        tot += max(0.0, bh - cov) * dx
    return tot


def bar_area(c, w, h):
    return w * h - 4.0 * (bar_r(c, w, h) ** 2 * (1 - math.pi / 4))


def via_clear(c, x, y):
    """A via at panel (x, y) clears every via keepout (the back-side parts
    over the pads): its pad plus via_keepout_clear_mm outside each rect."""
    m = c["via_dia_mm"] / 2.0 + c["via_keepout_clear_mm"]
    return all(not (k[0] - m < x < k[2] + m and k[1] - m < y < k[3] + m)
               for k in c["via_keepouts_mm"])


_COPPER = {}


def copper(c, g, y_top):
    """One pad's final copper: bars, bridges and vias, in panel mm.

    Returns dict(bars=[(net, x, y, w, h)], bridges=[(net, x, y, w, h)],
    vias=[(net, x, y)], charge=[(bridge_index, charged_bar_x, other_bar_x)]).

    Every bar tall enough to hold the via pad gets one via, centred across the
    tooth and via_inset_mm in from its OUTER edge (the pad edge), capped at
    mid-bar, so each net's vias line up for a straight L2 bus. Inside a via
    keepout the via walks inward along the bar until it clears; a bar that
    cannot hold a via anywhere clear -- the 0.197mm slivers beside each zone
    boundary, and the thin bars behind J1 -- is bridged along the pad edge,
    tooth to tooth, to the nearest same-net bar on the same side that has one.
    Each bridge's own copper is paid for by shortening the THINNER bar it
    joins from its inner edge, so every column's area ratio still matches the
    presence function (--check measures it).
    """
    key = (tuple(sorted((k, repr(v)) for k, v in c.items())), g["PAD_X0"], g["PW"], y_top)
    if key in _COPPER:
        return _COPPER[key]
    bars = [list(b) for b in teeth(c, g, y_top)]
    top = lambda b: b[0] in (0, 2)
    idx = lambda b: round((b[1] - g["PAD_X0"]) / g["T_PITCH"])
    side = {(idx(b), top(b)): k for k, b in enumerate(bars)}

    def via_for(b):
        net, x, y, w, h = b
        if h < c["via_dia_mm"]:
            return None
        k = min(c["via_inset_mm"], h / 2.0)
        cx = x + w / 2.0
        while k <= h - c["via_dia_mm"] / 2.0 + 1e-9:
            vy = y + k if top(b) else y + h - k
            if via_clear(c, cx, vy):
                return (net, cx, vy)
            k += 0.05
        return None

    vias = {k: via_for(b) for k, b in enumerate(bars)}
    # chains: each via-less bar walks to the nearest via bar of its net, same side
    links = set()
    for k, b in enumerate(bars):
        if vias[k]:
            continue
        best = None
        for step in (-1, 1):
            path, j = [k], idx(b)
            while True:
                j += step
                q = side.get((j, top(b)))
                if q is None or bars[q][0] != b[0]:
                    break
                path.append(q)
                if vias[q]:
                    if best is None or len(path) < len(best):
                        best = path
                    break
        if best is None:
            raise SystemExit(f"tooth {idx(b)} at y {y_top}: no via and no same-net bar with one")
        for u, v in zip(best, best[1:]):
            links.add(tuple(sorted((u, v))))
    # Every bar's copper budget is what teeth() gave it: its filleted area less
    # the via hole it was compensated for. A bar that ended up with no via has
    # that hole's worth too much copper; a bar that pays for a bridge has the
    # bridge's worth too much. Both are taken off by shortening the bar from
    # its inner edge. Each bridge is paid for by the THINNER bar it joins.
    # Iterate: a short bar's fillet shrinks with it, and the bridge on its thin
    # side is measured against it.
    orig = {k: tuple(b) for k, b in enumerate(bars)}
    hole = math.pi * (c["via_drill_mm"] / 2.0) ** 2
    for _ in range(12):
        bridges, charge, extra = [], [], {}
        for u, v in sorted(links):
            thin, thick = (u, v) if orig[u][4] <= orig[v][4] else (v, u)
            tb, kb = bars[thin], bars[thick]
            bx0, bx1 = sorted((tb[1] + tb[3] / 2.0, kb[1] + kb[3] / 2.0))
            bh = min(tb[4], c["bridge_h_mm"])
            yb = tb[2] if top(tb) else tb[2] + tb[4] - bh
            br = (bx0, yb, bx1 - bx0, bh)
            extra[thin] = extra.get(thin, 0.0) + bridge_extra(c, br, tuple(tb[1:]), tuple(kb[1:]))
            bridges.append((tb[0],) + br)
            charge.append((len(bridges) - 1, tb[1], kb[1]))
        moved = 0.0
        for k, b in enumerate(bars):
            net, x, y, w, h0 = orig[k]
            target = bar_area(c, w, h0) - hole_area(c, h0) - extra.get(k, 0.0)
            mine = hole if vias[k] else 0.0
            if abs(bar_area(c, w, b[4]) - mine - target) < 1e-12:
                continue
            lo, hi = c["min_copper_mm"], h0
            for _ in range(60):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if bar_area(c, w, mid) - mine < target else (lo, mid)
            if lo < c["min_copper_mm"] + 1e-9:
                raise SystemExit(f"tooth {idx(b)}: paying for its bridge takes it below the fab floor")
            moved = max(moved, abs(lo - b[4]))
            b[2], b[4] = (y if top(b) else y + h0 - lo), lo
        if moved < 1e-9:
            break
    else:
        raise SystemExit("bridge compensation did not settle")
    for k, v in vias.items():
        if v:
            b = bars[k]
            r = c["via_dia_mm"] / 2.0
            assert b[2] + r - 1e-9 <= v[2] <= b[2] + b[4] - r + 1e-9, f"via off its bar at tooth {idx(b)}"
    out = dict(bars=[tuple(b) for b in bars], bridges=bridges, charge=charge,
               vias=[vias[k] for k in range(len(bars)) if vias[k]])
    _COPPER[key] = out
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
      f'six dual-gang analog knobs for the filter and delay, '
      f'{c["n_switches"]} round toggle bushing holes, LPG mode and source, '
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

    # switch bushing holes + OLED
    A(f'<g id="switches" fill="none" stroke="{INK}" stroke-width="0.3">')
    for i in range(c["n_switches"]):
        sx = g["SW_X0"] + i * (c["switch_w_mm"] + 4.0)
        A(f'<circle cx="{f(sx + c["switch_w_mm"]/2)}" cy="{f(g["SW_CY"])}" '
          f'r="{f(c["switch_hole_d_mm"]/2)}"/>')
    A('</g>')
    # the OLED window: a cut, drawn where the board routes it (oled_window())
    w = g["OLED_WIN"]
    A(f'<g id="oled" fill="none" stroke="{INK}" stroke-width="0.3">'
      f'<rect x="{f(w[0])}" y="{f(w[1])}" width="{f(w[2] - w[0])}" '
      f'height="{f(w[3] - w[1])}" rx="{f(c["oled_window_r_mm"])}"/></g>')

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
    holes = []
    for y0 in g["PAD_TOPS"]:
        cu = copper(c, g, y0)
        for net, x, y, w, h in cu["bridges"]:
            bars[net].append(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"/>')
        holes += cu["vias"]
        for net, x, y, w, h in cu["bars"]:
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
    # open via holes, one per bar: what the finger sees of them
    A(f'<g id="via-holes" fill="#FFFFFF" stroke="none">')
    for _, x, y in holes:
        A(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(c["via_drill_mm"] / 2.0)}"/>')
    A('</g>')

    # encoder
    A(f'<g id="encoder" fill="none" stroke="{INK}" stroke-width="0.3">'
      f'<circle cx="{f(g["ENC_CX"])}" cy="{f(g["ENC_CY"])}" r="{f(c["encoder_r_mm"])}"/></g>')
    if c["shift_button"]:
        A(f'<g id="shift-button" fill="none" stroke="{INK}" stroke-width="0.3">'
          f'<circle cx="{f(g["SHIFT_CX"])}" cy="{f(g["SHIFT_CY"])}" '
          f'r="{f(c["shift_r_mm"])}"/></g>')

    # UI buttons, 2 wide x 3 tall. Two things are drawn per button: the CAP
    # outline, which sits on the panel surface, and the actual HOLE, which only
    # has to pass the stem.
    if c.get("controls_left") and c.get("mx_buttons"):
        hr, pl = c["mx_hole_r_mm"], c["mx_plunger_mm"]
        A(f'<g id="ui-buttons" fill="none" stroke="{INK}" stroke-width="0.3">')
        for cy in g["MX_CY"]:
            for cx in g["MX_CX"]:
                A(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(hr)}"/>')
                A(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(pl/2)}" '
                  f'stroke-dasharray="0.8 0.8"/>')
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
    A(f'<g id="numerals" font-family="sans-serif" font-size="{c["numeral_pt_mm"]}" fill="{INK}">')
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
        y0 = (g["DIV_Y"] + 6.5) if c["inscription_below_divider"] else g["COMP_Y0"] + 12.0
        y1 = g["COMP_Y1"] - 6.0
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
    out.append(f"composition {g['COMP_H']:.2f}mm, +{g['TOP_X']:.2f} at the jack edge, "
               f"+{g['BOT_X']:.2f} at the back")
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
        region = g["COMP_Y1"] - g["DIV_Y"]
        need = g["BLOCK_H"] + c["numeral_row_mm"]
        row("pad block + numerals fit below the divider",
            f"{need:.1f} in {region:.1f}mm", need <= region + 0.01)
    else:
        row("pad block fits lower region", f"{g['BLOCK_H']:.1f} in {g['AVAIL']:.1f}mm",
            g["BLOCK_H"] <= g["AVAIL"] + 0.01)
    # Centred in the COMPOSITION frame. The back-edge extension adds to the space
    # below on purpose: re-centring would move ENC0 and SW4-SW9 with the pads.
    above = g["PAD_Y0"] - g["DIV_Y"]
    below = g["COMP_Y1"] - (g["PAD_TOPS"][3] + g["PW"])
    row("pad block centred below the divider", f"{above:.2f} above / {below:.2f} below"
        f" (+{g['BOT_X']:.2f} to the back edge)", abs(above - below) < 0.05)
    nb = g["PAD_TOPS"][3] + g["PW"] + c["numeral_row_mm"]
    row("bottom numerals inside the panel", f"baseline {nb:.2f} of {g['PANEL_H']:.2f}",
        nb < g["PANEL_H"] - 2.0)

    # copper: test the REAL emitted geometry, not the idealised presence
    # function. An earlier version recomputed from presences() and so never
    # looked at the rounded ends at all.
    usable = g["PW"] - c["top_bottom_gap_mm"]
    r = c["pad_corner_r_mm"]
    x0, x1 = g["PAD_X0"], g["PAD_X1"]
    tf = c["tooth_fillet_mm"]
    hole = math.pi * (c["via_drill_mm"] / 2.0) ** 2
    worst = worst_rr = err = 0.0
    clamped = nbars = nvias = nbr = nshort = ncols = 0
    minh, bad, conn_bad = 9e9, [], []
    for y_top in g["PAD_TOPS"]:
        cu = copper(c, g, y_top)
        rects = cu["bars"]
        nbars += len(rects); nvias += len(cu["vias"]); nbr += len(cu["bridges"])
        minh = min(minh, min(h for *_, h in rects))
        find = lambda net, x: next(i for i, b in enumerate(rects) if b[0] == net and abs(b[1] - x) < 1e-6)
        via_at = set()
        for net, vx, vy in cu["vias"]:
            k = next((i for i, b in enumerate(rects) if b[0] == net and b[1] <= vx <= b[1] + b[3]
                      and b[2] <= vy <= b[2] + b[4]), None)
            if k is None:
                conn_bad.append(f"via at ({vx:.3f}, {vy:.3f}) is on no bar of its net")
            via_at.add(k)
        # Every column must fill the pad, except where a bar was shortened to
        # pay for a bridge, or for the via hole it was compensated for and did
        # not get.
        short = {round(cx, 6) for _, cx, _ in cu["charge"]} | \
                {round(b[1], 6) for i, b in enumerate(rects) if i not in via_at}
        mids = {}
        for _, x, y, w, h in rects:
            if x - x0 > r and x1 - (x + w) > r:
                mids[round(x, 6)] = mids.get(round(x, 6), 0.0) + h
        bad += [x for x, sm in mids.items() if abs(sm - usable) > 1e-6 and x not in short]
        ncols += len(mids); nshort += len(short & set(mids))
        # every bar: a via, or a bridge chain to a bar that has one
        linked = {}
        for bi, cx, ox in cu["charge"]:
            net = cu["bridges"][bi][0]
            u, v = find(net, cx), find(net, ox)
            linked.setdefault(u, set()).add(v); linked.setdefault(v, set()).add(u)
        for i in range(len(rects)):
            seen, todo = {i}, [i]
            while todo:
                for q in linked.get(todo.pop(), ()):
                    if q not in seen:
                        seen.add(q); todo.append(q)
            if not seen & via_at:
                conn_bad.append(f"bar at x {rects[i][1]:.3f}, pad y {y_top:.2f} reaches no via")
        # nothing may poke outside the rounded outline; fillets in range
        for _, x, y, w, h in rects:
            for px in (x, x + w):
                ins = corner_inset(px, x0, x1, r)
                worst = max(worst, (y_top + ins) - y, (y + h) - (y_top + g["PW"] - ins))
            rr = min(tf, w / 2.0, h / 2.0)
            clamped += rr < tf - 1e-9
            worst_rr = max(worst_rr, rr)
        # THE ONE THAT MATTERS: position is read from the copper AREA ratio
        # between the top and bottom bars. Compare the emitted area ratio --
        # fillets, via holes and bridges all counted -- against the fraction
        # the presence function ASKED FOR. Comparing against emitted height
        # would be circular, since compensation works by making the heights
        # non-linear. A bridge's own copper counts in the column of the bar
        # that paid for it. Classify by NET, not by y: RX0/RX2 are the top
        # bars, RX1/RX3 the bottom (ADR 0003).
        cols = {}
        for bi, cx, ox in cu["charge"]:
            net = cu["bridges"][bi][0]
            d = cols.setdefault(round(cx, 6), [0.0, 0.0])
            d[0 if net in (0, 2) else 1] += bridge_extra(
                c, cu["bridges"][bi][1:], rects[find(net, cx)][1:], rects[find(net, ox)][1:])
        for i, (net, x, y, w, h) in enumerate(rects):
            d = cols.setdefault(round(x, 6), [0.0, 0.0])
            d[0 if net in (0, 2) else 1] += bar_area(c, w, h) - (hole if i in via_at else 0.0)
        for i in range(g["N_TEETH"]):
            p = presences((i + 0.5) / g["N_TEETH"] * 4.0)
            d = cols.get(round(g["PAD_X0"] + i * g["T_PITCH"], 6))
            if d and d[0] + d[1] > 0:
                err = max(err, abs(d[0] / (d[0] + d[1]) - (p[0] + p[2])))

    row("min copper bar >= fab floor", f"{minh:.4f} vs {c['min_copper_mm']}mm",
        minh >= c["min_copper_mm"])
    row("tooth pairs fill the pad, away from the ends",
        f"{ncols - nshort} of {ncols} columns, {usable:.2f}mm; {nshort} short by their bridge or hole",
        not bad)
    row("no copper outside the rounded outline", f"worst overhang {worst:.4f}mm", worst <= 1e-9)
    row("tooth fillet within half the smaller side",
        f"r={tf}mm, {clamped} of {nbars} bars clamped to fit", worst_rr <= tf + 1e-9)
    row("pad ends not tapered", f"pad_corner_r_mm = {r}", True)
    row("every bar reaches a via, all 4 pads",
        f"{nvias} vias, {nbr} bridges, {nbars} bars" + ("" if not conn_bad else "; " + conn_bad[0]),
        not conn_bad)
    row("no via in a keepout (J1's pads)", f"{len(c['via_keepouts_mm'])} keepouts, "
        f"{c['via_keepout_clear_mm']}mm clear",
        all(via_clear(c, vx, vy) for y_top in g["PAD_TOPS"] for _, vx, vy in copper(c, g, y_top)["vias"]))
    row("fillets, holes, bridges do not bend the position curve",
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
            btm = (g["MX_CY"][-1] + c["mx_hole_r_mm"]) if c.get("mx_buttons") else \
                  ((g["BTN_CY"][-1] + c["button_r_mm"]) if g["BTN_CY"] else g["SHIFT_CY"])
            row("control column inside the walls (vertical)",
                f"{g['ENC_CY']-er:.2f} .. {btm:.2f} of {c['enclosure_wall_mm']}..{g['PANEL_H']-c['enclosure_wall_mm']:.1f}",
                g["ENC_CY"]-er > c["enclosure_wall_mm"] and btm < g["PANEL_H"]-c["enclosure_wall_mm"])
            _bx = (g["MX_CX"][-1] + c["mx_hole_r_mm"]) if c.get("mx_buttons") \
                  else (g["BTN_CX"] + c["button_r_mm"])
            row("buttons clear the pads", f"{g['PAD_X0']-_bx:.2f}mm", _bx < g["PAD_X0"])
            if c.get("mx_buttons"):
                # KEY-TH_4P-L12.0-W12.0-P5.00-LS12.5 puts its through-hole pads
                # at x = +/-6.25, 2.2mm of copper on a 1.5mm drill -- OUTSIDE the
                # 12mm courtyard. Two columns side by side short below 14.7mm
                # pitch and lose fab clearance before that, so the column pitch
                # is limited by the PCB, not by the caps.
                _pgap = c["mx_pitch_mm"] - 2 * 6.25 - 2.2
                row("button columns clear each other's pads",
                    f"{_pgap:.2f}mm copper at {c['mx_pitch_mm']:.2f}mm pitch",
                    _pgap >= 0.5)
                # The two facts that were wrong before 2026-09-08, now checked.
                # The panel Z-stack is fixed by design-state "Panel mounting":
                # the pots are the datum, faceplate underside at 10mm above the
                # main PCB and the outer face at 11.6mm.
                _PANEL_OUTER_MM = 11.6
                _SW_H_MM        = 14.0      # TS1103S-12X12X14DIP, LCSC C54573007
                _proud = _SW_H_MM - _PANEL_OUTER_MM
                row("button reaches through the panel",
                    f"{_proud:.2f}mm proud of the {_PANEL_OUTER_MM}mm outer face",
                    1.5 <= _proud <= 5.0)
                _hgap = 2 * c["mx_hole_r_mm"] - c["mx_plunger_mm"]
                row("plunger clears its panel hole",
                    f"{_hgap:.2f}mm on dia, {c['mx_plunger_mm']}mm in "
                    f"{2*c['mx_hole_r_mm']:.1f}mm",
                    _hgap >= 0.2)
                # Bodies are 12.0 square and sit BEHIND the panel, so this is a
                # PCB-side fit, not a panel one.
                _bodygap = c["mx_row_pitch_mm"] - 12.0
                row("switch bodies clear each other, row to row",
                    f"{_bodygap:.2f}mm at {c['mx_row_pitch_mm']}mm rows",
                    _bodygap >= 0.5)
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
            btm = (g["MX_CY"][-1] + c["mx_hole_r_mm"]) if c.get("mx_buttons") else \
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
    row("switch bushing hole fits its slot",
        f'dia {c["switch_hole_d_mm"]}mm in a {c["switch_w_mm"]}mm column',
        c["switch_hole_d_mm"] < c["switch_w_mm"])
    row("switch count", f'{c["n_switches"]} (LPG mode + source, both DPDT '
        f'Dailywell 2MD1T1B1M2QES / Thonk DW3)', c["n_switches"] == 2)
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
    sy0 = g["SW_CY"] - c["switch_h_mm"]/2.0
    for i in range(c["n_switches"]):
        sx = g["SW_X0"]+i*(c["switch_w_mm"]+4)
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
    w, aa, gl, d = g["OLED_WIN"], g["OLED_AA"], g["OLED_GLASS"], g["OLED_DEPTH"]
    gm = min(w[0] - gl[0], w[1] - gl[1], gl[2] - w[2], gl[3] - w[3])
    row("OLED window shows only black glass", f"{gm:.2f}mm from the glass edge at the nearest",
        gm >= c["oled_glass_margin_mm"] - 1e-9 and w[0] <= aa[0] and w[1] <= aa[1]
        and w[2] >= aa[2] and w[3] >= aa[3])
    ang = lambda e: math.degrees(math.atan2(e, d))
    row("OLED active area in view at the deepest mount",
        f"{d:.1f}mm deep: player {ang(w[3] - aa[3]):.0f} deg, sides {ang(aa[0] - w[0]):.0f} / "
        f"{ang(w[2] - aa[2]):.0f}, far {ang(aa[1] - w[1]):.0f}",
        ang(w[3] - aa[3]) >= c["oled_view_player_deg"] - 1e-6 and
        min(aa[0] - w[0], w[2] - aa[2], aa[1] - w[1]) >= 0.5)
    row("OLED window clears the divider", f"bottom {w[3]:.2f} vs divider {g['DIV_Y']:.2f}",
        w[3] < g["DIV_Y"] - 2.0)
    if c["salamis_marks"]:
        seq = list(c["inscription"])
        gw = c["inscription_h_mm"] * 0.58
        y0 = (g["DIV_Y"] + 6.5) if c["inscription_below_divider"] else g["COMP_Y0"] + 12.0
        step = (g["COMP_Y1"] - 6.0 - y0) / (len(seq) - 1)
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
    # ---- the panel extensions ------------------------------------------------
    # The +2 at the jack edge must be a PURE offset: place.py enforces these
    # rows on a routed board, and anything that re-flows moves real parts.
    # Re-derive with both extensions zeroed and compare every placement row.
    c0 = dict(c, panel_top_extra_mm=0.0, panel_bottom_extra_mm=0.0)
    now = {r[0]: r[2:4] for r in panel_rows(c, g)}
    base = {r[0]: r[2:4] for r in panel_rows(c0, derive(c0))}
    dev = max(max(abs(now[k][0] - base[k][0]), abs(now[k][1] - base[k][1] - g["TOP_X"]))
              for k in base)
    pad_dev = max(abs(a - b - g["TOP_X"]) for a, b in zip(g["PAD_TOPS"], derive(c0)["PAD_TOPS"]))
    row("panel extensions move nothing but y += top",
        f"{len(now)} parts + 4 pads, worst {max(dev, pad_dev):.2e}mm off +{g['TOP_X']:.3f}",
        sorted(now) == sorted(base) and max(dev, pad_dev) < 1e-9)
    cav = g["PANEL_H"] - 2 * c["enclosure_wall_mm"]
    cav_need = c["front_gap_mm"] + c["main_pcb_h_mm"] + c["slide_travel_mm"]
    row("panel covers the box the board slides into",
        f"cavity {cav:.2f} = {c['front_gap_mm']:g} gap + {c['main_pcb_h_mm']:g} board"
        f" + {c['slide_travel_mm']:g} travel", abs(cav - cav_need) < 1e-6)

    # --- check the OUTPUT, not just the geometry -----------------------------
    # Everything above reads `g` and `c`. None of it had ever looked at what
    # render() actually emits, so the two shared no code path: render() spent a
    # day raising KeyError and emitting nothing while these rows all reported
    # ALL CHECKS PASS, and later emitted an orphaned </g> that no check could
    # see. A validator that cannot observe its own product is decoration.
    import xml.etree.ElementTree as _ET
    import re as _re
    try:
        _svg = render(c, g)
        _ET.fromstring(_svg)
        row("rendered SVG is well-formed XML", f"{len(_svg)} chars parsed", True)
    except Exception as _e:
        _svg = ""
        row("rendered SVG is well-formed XML", f"{type(_e).__name__}: {_e}", False)
    if _svg and c["n_switches"]:
        _drawn = _re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" '
                            r'r="%s"/>' % _re.escape(f'{c["switch_hole_d_mm"]/2:g}'), _svg)
        _want = [(g["SW_X0"] + i * (c["switch_w_mm"] + 4.0) + c["switch_w_mm"] / 2.0,
                  g["SW_CY"]) for i in range(c["n_switches"])]
        _okxy = (len(_drawn) == c["n_switches"] and
                 all(abs(float(a) - wx) < 0.01 and abs(float(b) - wy) < 0.01
                     for (a, b), (wx, wy) in zip(_drawn, _want)))
        row("drawn switch holes match the placement file",
            f"{len(_drawn)} drawn at {_drawn}", _okxy)
    out.append("")
    out.append("  ALL CHECKS PASS" if ok else "  *** FAILURES ABOVE ***")
    return "\n".join(out), ok


def panel_rows(c, g):
    """(ref, part, x, y, note) for every main-board part that comes through the
    panel. placement() prints these and check() diffs them, so the file and the
    purity check can never be looking at different lists."""
    rows = []
    for i, cx in enumerate(g["CH_CX"]):
        for j, cy in enumerate((g["R2"], g["R4"])):
            n = i * 2 + j + 1
            rows.append((f"ENC{n}", f"encoder, ch{i+1} {'AB'[j]}", cx, cy, "-> MCP23017"))
    # Six ANALOG pots, all DUAL-GANG so one knob moves both stereo sides.
    # Columns left to right: filter, filter, delay. ENC9/ENC10 (envelope
    # attack/release) were removed 2026-09-01 and column 0 became pots -- the
    # group was already 3 columns x 2 rows, so no geometry moved.
    POTS = [("RV1", "CUTOFF"),        ("RV2", "RESONANCE"),
            ("RV3", "FILTER CV AMT"), ("RV4", "TIME"),
            ("RV5", "FEEDBACK"),      ("RV6", "WET/DRY")]
    for k, (ref, label) in enumerate(POTS):
        cx = g["EN_CX"][k // 2]
        cy = (g["R2"], g["R4"])[k % 2]
        dest = "ANALOG -> LPG" if k < 3 else "ANALOG -> BBD"
        rows.append((ref, f"POT 9mm DUAL-GANG, {label}", cx, cy, dest))
    for i in range(c["n_switches"]):
        sx = g["SW_X0"] + i * (c["switch_w_mm"] + 4.0) + c["switch_w_mm"] / 2.0
        rows.append((f"SW{1+i}",
                     "DPDT LPG mode VCF/VCA" if i == 0 else "DPDT SOURCE resample/ext",
                     sx, g["SW_CY"], "ANALOG -> LPG"))
    rows.append(("DS1", "OLED 2.42in SSD1309 (TOP-LEFT)", g["oled_x0"], g["OLED_Y"], "SPI -> Daisy"))
    rows.append(("ENC0", "encoder + PUSH, main UI", g["ENC_CX"], g["ENC_CY"], "-> MCP23017 U4 GPB0-2"))
    if c.get("shift_button"):
        rows.append(("SW3", "tactile, SHIFT", g["SHIFT_CX"], g["SHIFT_CY"], "-> Daisy A9"))
    if c.get("mx_buttons"):
        # GPA4-7 were the original four; BTN5/BTN6 went onto U4's spare GPA0/GPA1.
        GPIO = ["GPA4", "GPA5", "GPA6", "GPA7", "GPA0", "GPA1"]
        n = 0
        for cy in g["MX_CY"]:
            for cx in g["MX_CX"]:
                rows.append((f"SW{4+n}", f"12x12 tactile, UI button {n+1}", cx, cy,
                             f"-> MCP23017 U4 {GPIO[n]}"))
                n += 1
    else:
        for k, cy in enumerate(g["BTN_CY"]):
            rows.append((f"SW{4+k}", f"tactile, UI button {k+1}", g["BTN_CX"], cy,
                         f"-> MCP23017 U4 GPA{4+k}"))
    return rows


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
    for ref, part, x, y, note in panel_rows(c, g):
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
    A(f"#   cavity        {cav_w:.2f} x {cav_h:.2f}mm = {c['front_gap_mm']:g} gap + "
      f"{c['main_pcb_h_mm']:g} board + {c['slide_travel_mm']:g} slide travel")
    A(f"#   MAIN PCB MAX  {cav_w - 2:.1f}mm wide")
    # ORG is sheet (100, 50) in vuulgaris.kicad_pcb, the board's top-left corner
    # until its top edge moved out 2mm on 2026-09-23. The panel grew the same
    # 2mm at the same edge (panel_top_extra_mm), so ORG sits that far below the
    # board's edge, which sits the front gap inside the wall.
    wall = c["enclosure_wall_mm"]
    A("#   PCB ORG (sheet 100, 50) sits at panel (%.3f, %.3f); pcb = panel - that offset"
      % (wall + 0.995, wall + c["front_gap_mm"] + g["TOP_X"]))
    A("#   (place.py OX, OY). The board's top edge is at panel y %.3f, %gmm inside the wall."
      % (wall + c["front_gap_mm"], c["front_gap_mm"]))
    return "\n".join(L)


if __name__ == "__main__":
    cfg = dict(CFG)
    args = sys.argv[1:]
    # Every --set counts. This used args.index(a), which finds the FIRST --set
    # each time, so a second or third override silently re-applied the first.
    for i, a in enumerate(args):
        if a == "--set" or a.startswith("--set="):
            kv = a.split("=", 1)[1] if a.startswith("--set=") else args[i + 1]
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
