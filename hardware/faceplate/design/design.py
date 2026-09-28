"""The faceplate's schematic design: which symbol each ref uses, where it sits on
the sheet, and which footprint it gets. Drawn by hardware/kicad/tools/mksch.py
--project faceplate; netmap.json beside this file is the intent it is checked
against (tools/netcheck.py --project faceplate).

SKELETON, 2026-09-27. Only the cable header is in, because it is the one part
whose every pin is already fixed by the main board: the ribbon is straight
through, so J1 pin n carries J12 pin n's net, and tools/panelcheck.py fails if
the two netmaps ever disagree. The MSP430 and everything around it come next,
from TI's reference circuits, not from here.

Symbols come from the main board's library plus KiCad's generic ones. Footprints
are named "lib:name"; a bare name means the shared vuulgaris.pretty.
"""
import json
import proj

MAIN = proj.PROJECTS["main"]
STOCK = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

# Must match ksym.py's argument list for this project (faceplate README):
# stock libraries first, the project library last.
LIBS = [
    f"{STOCK}/Connector_Generic.kicad_sym",
    f"{STOCK}/Device.kicad_sym",
    f"{MAIN.dir}/lib/vuulgaris.kicad_sym",
]

NET = json.load(open(proj.P.netmap))

SYM = {
    "J1": "Conn_02x05_Odd_Even",
}

POS = {
    "J1": (100, 100),
}

FPMAP = {
    # hanxia HX JN2.54-2x5P TP H8.9, LCSC C41376028 (Extended: JLC has no Basic
    # SMD 2x5 box header). SMD because a through-hole header here puts ten pins
    # through the FRONT face, in the 8mm gap between pads 3 and 4. Footprint
    # from hanxia's drawing; 9.60mm seated, under the 10mm gap. Pin 1 is on the
    # key-side row at the triangle end -- confirm with a real ribbon before
    # ordering (hardware/faceplate/README.md, section 5).
    "J1": "IDC-SMD_10P-P2.54_C41376028",
}
