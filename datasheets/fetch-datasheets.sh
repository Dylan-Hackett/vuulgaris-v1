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

# ---- will not fetch: these vendors 403 every scripted request ------------
# Download by hand into this directory, keeping these filenames:
#   AMS1117-datasheet.pdf            http://www.advanced-monolithic.com/pdf/ds1117.pdf
#   CoolAudio-V3205SD-datasheet.pdf  https://coolaudio.com  (BBD, U101/U201)
#     -- but the pinout is settled: the mki manual states it in words on p25,
#        and Panasonic-MN3205-datasheet.pdf (fetched above) is the original.
#        Note the MN3205 scan is CCITT fax-coded with no text layer.
echo
echo "Four datasheets cannot be fetched -- see the comment at the end of this script."
