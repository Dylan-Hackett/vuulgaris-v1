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

echo
echo "TI sometimes serves an interstitial instead of the PDF. If a fetch says NOT A PDF,"
echo "open the URL in a browser once, then re-run."
