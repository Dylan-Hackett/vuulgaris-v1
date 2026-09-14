#!/usr/bin/env bash
# Populate datasheets/ with the real PDFs. Run from this directory.
# These are public documents; not committed to keep the repo light and
# to avoid redistributing TI literature.
set -u
cd "$(dirname "$0")"

fetch() {
  local url="$1" out="$2"
  if [ -s "$out" ]; then echo "skip  $out (already present)"; return; fi
  printf 'get   %-46s' "$out"
  if curl -fsSL -A "Mozilla/5.0" --max-time 90 -o "$out" "$url"; then
    if head -c 4 "$out" | grep -q '%PDF'; then
      echo "ok ($(du -h "$out" | cut -f1))"
    else
      echo "NOT A PDF (likely an interstitial page) - download by hand: $url"
      rm -f "$out"
    fi
  else
    echo "FAILED - download by hand: $url"
    rm -f "$out"
  fi
}

fetch "https://www.ti.com/lit/gpn/msp430fr2675" TI-MSP430FR2675-datasheet.pdf
fetch "https://www.ti.com/lit/pdf/slau550"      SLAU550-MSP430-FRAM-BSL.pdf
fetch "https://www.ti.com/lit/pdf/slaa891"      SLAA891-OpenSCAD-CapTouch-Scripts.pdf
fetch "https://www.ti.com/lit/pdf/slaa843"      SLAA843-Sensitivity-SNR.pdf
fetch "https://www.ti.com/lit/pdf/slaa685"      SLAA685-Code-Protection.pdf
fetch "https://www.ti.com/lit/pdf/slaa842"      SLAA842-CapTIvate-Selection.pdf
fetch "https://daisy.nyc3.cdn.digitaloceanspaces.com/products/patch-sm/ES_Patch_SM_datasheet_v1.0.5.pdf" Electrosmith-Patch-SM-v1.0.5.pdf

# ---- analog / power / IO, added 2026-09-10 -------------------------------
# Every one of these backs a block that netmap.json asserts a pinout for and
# nothing verifies. U8 was wired to the 78L05's pinout while carrying an
# AMS1117; that is the failure these exist to catch.
fetch "https://www.ti.com/lit/gpn/cd4046b"       TI-CD4046B-datasheet.pdf
fetch "https://www.ti.com/lit/gpn/tl072"         TI-TL072-datasheet.pdf
fetch "https://www.ti.com/lit/gpn/tl074"         TI-TL074-datasheet.pdf
fetch "https://www.ti.com/lit/gpn/tl084"         TI-TL084-datasheet.pdf
fetch "https://www.ti.com/lit/gpn/opa1688"       TI-OPA1688-datasheet.pdf
fetch "https://ww1.microchip.com/downloads/en/devicedoc/20001952c.pdf" Microchip-MCP23017-datasheet.pdf
fetch "http://www.meanwelljapan.com/upload/pdf/DKM10/SKM10,DKM10-spec.pdf" MeanWell-SKM10-DKM10-spec.pdf

echo
echo "TI sometimes serves an interstitial instead of the PDF. If a fetch says NOT A PDF,"
echo "open the URL in a browser once, then re-run."

# ---- found 2026-09-11, these DO fetch ------------------------------------
fetch "https://datasheets.b-cdn.net/files/J113.-Fairchild-datasheet-7564731.pdf" onsemi-MMBFJ113-datasheet.pdf
fetch "https://store.synthrotek.com/assets/images/XVIVE-VTL5C3-VTL5C4-Vactrol-Data-Sheet.pdf" Xvive-VTL5C3-datasheet.pdf
fetch "https://aionfx.com/app/files/datasheets/panasonic-mn3205.pdf" Panasonic-MN3205-datasheet.pdf

# ---- added 2026-09-13: everything else with a pin that can be wired wrong --
# Connectors, switches, encoders, the OLED module, and every polarised part.
# Resistors, MLCCs, beads and the PTC have no pin semantics and are omitted.
# URLs are the pdfUrl on each part's LCSC product page; the query string is
# LCSC's own and harmless.
LCSC=https://datasheet.lcsc.com/datasheet/pdf
fetch "$LCSC/e6935943fc6b1bbf350a1a0f3e90dc4a.pdf?productCode=C6186"     AMS1117-datasheet.pdf            # U5 U6 U8, -3.3 and -5.0 share it
fetch "$LCSC/9e56b777c022540fcce7c7f67825f55e.pdf?productCode=C165948"   Korean-Hroparts-TYPE-C-31-M-12.pdf   # J11
fetch "$LCSC/dc83ceb7bc09989eab2815b685da60e4.pdf?productCode=C393941"   TF-PUSH-microSD.pdf              # J1
fetch "$LCSC/52e4c1ee9763681502a3f052e7089c2a.pdf?productCode=C5139768"  HS242L01W4S01-OLED.pdf           # DS1
fetch "$LCSC/4cc3bd21dcba170c16b2674827fd1e2e.pdf?productCode=C22355746" PJ-376-jack.pdf                  # J2-J6
fetch "$LCSC/419fcba410f3701f7ab3fcab4bb673fc.pdf?productCode=C41409498" PJ-603-jack.pdf                  # J7-J10
fetch "$LCSC/e0a93036a66b5d2cacdda7d8f30bdea7.pdf?productCode=C2991196"  ALPS-EC11L1525G01.pdf            # ENC0
fetch "$LCSC/16cc0e471f78796867b3e08d7e332037.pdf?productCode=C470684"   ALPS-EC12E2430803.pdf            # ENC1-8
fetch "$LCSC/ddf46495c8b24beaa26ef652e1180b55.pdf?productCode=C54573007" TS1103S-12x12-tactile.pdf        # SW4-SW9
fetch "http://www.thonk.co.uk/wp-content/uploads/2017/05/DW3-DPDT-ON-ON-2MD1T1B1M2QES.pdf" Dailywell-2MD1T1B1M2QES-DPDT.pdf  # SW1 SW2, not on LCSC
fetch "$LCSC/bf298e2c0542e0172af23908598fa548.pdf?productCode=C223993"   SMAJ6.0A-TVS.pdf                 # D3
fetch "$LCSC/8abd7fc00ebe41ffb03ad1383c10753b.pdf?productCode=C81598"    1N4148W.pdf                      # D103-D107 D203-D207
fetch "$LCSC/2fab253063cdc61bc764f9393a362f63.pdf?productCode=C213113"   BZT52C3V9-zener.pdf              # D301 D401
fetch "$LCSC/bb373f7e3048e04274f44a753d40be09.pdf?productCode=C20608782" YLED0402Y.pdf                    # D1 D2
fetch "$LCSC/28b7f65130241c48e650f325ce318c84.pdf?productCode=C2977553"  Lelon-RVT-electrolytic.pdf       # C29 C32 C33 C36 C37, both series
fetch "$LCSC/72d5cba536460b3f2bac2dc6342f8983.pdf?productCode=C380211"   ALPS-RK09L1240A12-pot.pdf        # RV1-RV6
fetch "$LCSC/3e8e97a55d8a459d9476aee8c031bb82.pdf?productCode=C55071"    Bourns-3224W-trimmer.pdf         # RT301 RT401 RT501-RT504

# ---- will not fetch: these vendors 403 every scripted request ------------
# Download by hand into this directory, keeping these filenames:
#   CoolAudio-V3205SD-datasheet.pdf  https://coolaudio.com  (BBD, U101/U201)
#     -- but the pinout is settled: the mki manual states it in words on p25,
#        and Panasonic-MN3205-datasheet.pdf (fetched above) is the original.
#        Note the MN3205 scan is CCITT fax-coded with no text layer.
echo
echo "One datasheet (CoolAudio V3205SD) cannot be fetched -- see the comment at the end of this script."
