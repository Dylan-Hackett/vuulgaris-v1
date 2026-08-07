# 0007 - Stereo Buchla-style low pass gate, not Serge VCFQ

**Status:** Accepted
**Date:** pre-2026-08-05 (recorded retroactively from design state section 6)

## Decision

Stereo Buchla 292-style low pass gate, based on **Eddy Bergman's published design** (free,
he invites builds). Keeps the **VCA / VCF / both** mode switch so the sampler or synth
engine can run through an analog VCA and VCF.

Replaces an earlier plan for a stereo Serge variable-Q filter.

## Why the Serge VCFQ was dropped

The decisive reason is **calibration burden**: six gain cells means six trimmer-and-scope
passes per unit shipped, plus per-cell trims. That is unbounded labour on a build meant to
be cheap. LM13700 (3 packages, ~$6, no matching) or THAT2180 both eliminate it.

Supporting reasons, recorded because they took real work to establish:

- No fully public schematic exists for a true Serge VCFQ, by design.
- CGS112 (Ken Stone's DIY version) is published, but its BOM lists "CGS108 submodule x3" as
  a line item. The gain cells are daughterboards. The schematic is a complete drawing of a
  board that is two-thirds of a filter. Only one TL072 and one TL074 in the whole BOM; the
  voltage-controlled elements are all inside the submodules.
- CGS108 internals were never published, described only as essentially a voltage-controlled
  op amp. Ancestry is the Blackmer log-antilog VCA patent, expired.
- **Low-Gain Electronics publishes an LGE108 schematic** (public PDF) and sells
  pre-assembled SMD boards, a drop-in for the CGS108 in the same board position.
  whether LGE108 is topologically identical to CGS108 or an independent Blackmer-derived
  implementation was never settled. **Moot as of 2026-08-06**, see Q11.
- Modern equivalent: **THAT2180** per gain-cell position, what Random*Source uses in their
  licensed SMD VCFQ, no transistor matching required. Six for stereo, ~$36-45.

**Legal position (not legal advice):** copyright on a schematic covers the drawing, not the
circuit. Building and selling from a published schematic is not copyright infringement;
republishing the drawing or copying the PCB layout is. Blackmer's patent is expired.
Tcherepnin never patented the gain cell (trade secret, not IP). The real exposures are
trademark, so do not use "Serge" or "VCFQ" in marketing, and reputation.

## Problems this decision hands us

- **Vactrol count: four.** Bergman's design uses two vactrols for one channel, one VCA path
  and one filter path. Stereo doubles it.
- **Bergman rolls his own vactrols** from an LED plus LDR in heatshrink, and notes
  soldering an extra LED over one to dim it because it sounded better. That is a hand-tuned
  one-off. A stereo product needs four cells matched in **both on-resistance and decay**
  across L and R. Either buy Xvive VTL5C3s and match by measurement, or use **VTL5C3/2
  duals** so each stereo pair comes from one package.
- **Excelitas discontinued the Vactrol line.** Current source is the Xvive reissue, ~$5-8
  each. Reports say Xvive uses a brighter LED giving a longer release, so drive current
  needs trimming for consistency.
- **Vactrol bleed**, the LPG never fully closing. Prism Circuits' 4U version (also two
  VTL5C3s) adds circuitry specifically for this. Bergman's design may not address it.
  Solve deliberately rather than rediscovering it on assembled hardware.
- **RoHS / cadmium: closed 2026-08-06.** Vactrol supply is handled directly. No further
  action.
- Bergman's is a **stripboard layout**. Redraw in KiCad/EasyEDA, which is also the right
  move IP-wise.

Vactrols are **cost lever #1** at $20-32 for the set, second-biggest line after the Patch SM.

## Switching

**Two switches, not one.** One selects filter placement (pre/post); one selects source
(resample vs external input).

### Mode switch: two positions, not three

**RESOLVED 2026-08-06.** The mode switch is now **stereo VCF or stereo VCA**. The third
"both" position is dropped.

That makes it a **DPDT**, one pole per stereo side, which is a commodity panel part. The
previous plan needed 4P3T (or DP3T if reducible), and **4P3T panel-mount toggles are
uncommon** enough that it was a live risk to panel layout, with rotary as the likely
fallback. That risk is gone. Closes Q6.

### Source switch

Needs enough poles for **two stereo pairs**. DPDT is sufficient for two stereo sources into
one stereo destination: pole A carries L (throws resample-L / ext-L), pole B carries R.

**Break-before-make (non-shorting) is correct here.** A shorting switch would briefly tie two
low-impedance outputs together. Add a **100k-1M resistor to ground on the switch common** so
the node does not float during the open moment, plus **DC blocking caps on both sources**.

### Pinout, on both switches

Standard 6-pin DPDT: **middle pin of each row is the common** (pins 2 and 5; throws 1/3 and
4/6). **Lever direction is inverted relative to the pin it selects**, so flipping up connects
to the bottom throws.

**Verify the pinout with a multimeter on the actual part, and silkscreen the labels after
bench-confirming, not before.** PCB-mount slide switches differ between manufacturers.
