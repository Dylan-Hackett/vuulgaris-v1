# 0011 - The external input also feeds the analog chain

**Status:** Accepted
**Date:** 2026-09-25

## Decision

`EXT_AMP_OUT_L/R` — the 1/4" inputs after the `U10` preamp — is **mixed into the LPG input
alongside the Daisy's output, permanently**. The SOURCE switch (`SW2`) is unchanged: it
still gives the Daisy either the dry external input or the post-effects return.

```
EXT ─ U10 ─┬──────────────┐
           SW2 ─ Daisy in  │ R302/R402 10k
BBD out ───┘               │
Daisy out ── R301/R401 10k ┴── C306/C406 ── LPG ─ BBD ─ outs
```

Per channel: `R301`/`R401` 10k from `AUDIO_OUT`, `R302`/`R402` 10k from `EXT_AMP_OUT`, into
the node before the existing coupling cap (which now blocks DC from both). The passive mix
halves each source; **`R312`/`R412` 15k — Bergman's own `R12` — fitted permanently from
`U301A`/`U401A`'s inverting input to ground** gives that stage a gain of 2 and takes it back.
Each source reaches the LPG at 0.95x of today's level (the 100k `R309` loads the 5k mix);
DC from either source stops at `C306`/`C406`. `R310`/`R410` stay on `AUDIO_OUT` as before.

## Why

Before this, the only way into the analog effects was **through the Daisy**. External audio
could be *heard* through the LPG and delay only if firmware passed it through the codec, and
could not be *captured* after the effects in one pass: with SOURCE on RESAMPLE, the external
input was not connected to anything. The workaround was two passes — sample it dry, then play
it back through the effects and resample — which gives the same sound but not live.

With the mix:

- **Live external audio through the gate and delay, captured in one take.** SOURCE on
  RESAMPLE records Daisy playback plus EXT, through the analog chain.
- **A standalone effects box.** EXT reaches the LPG and BBD with no conversion and no
  latency, and works with the Daisy idle, booting or crashed.
- Nothing is lost that the old routing did: SOURCE on EXT still samples the input dry.

The cost is six Basic 0603 resistors of values already on the board, and a short reroute.

## Consequences

- **EXT is always in the effects when something is plugged in.** There is no mute on the
  instrument. Unplugged, the jacks' normalling contacts ground `U10`'s input, so it is
  silent. Closing the gate does **not** mute it — vactrol bleed leaves about −14dB at full
  dark (`lpg-bergman.md`) — and `RT503`/`RT504` bottom out at unity, not zero. The ways to
  silence it are unplugging and turning the source down. A firmware-controlled mute (a DG419
  per channel on a spare expander pin) and a build-time solder jumper were considered and
  declined, 2026-09-25: "plugged in means on" is normal for an effects input.
- **Anything on EXT is printed into every resample.** Deliberate when you want it, bleed when
  you forget a source plugged in.
- **Firmware must never pass `AUDIO_IN` through to `AUDIO_OUT`.** The Daisy cannot see
  `SW2`'s position (`workflow.md`, "The Daisy does not know which source is selected"), so
  "don't pass through when SOURCE is on EXT" is not implementable — the rule has to be
  unconditional. On EXT a passthrough would double the input; on RESAMPLE it would close a
  feedback loop around the analog chain. EXT is monitored through the analog path instead.
- **Headroom.** Each source alone swings exactly as before. A full-scale Daisy output and a
  hot EXT at the same time sum to about ±9V at `U301A`/`U401A` (2 x 4.75V x 0.95), against a
  TL084 swinging about ±10.5V on ±12V — close to clipping, and audible if it happens. It is
  managed at bring-up, not in hardware: trim `RT503`/`RT504` for about −6dB peaks, choose the
  BBD's `R104`/`R204` with both sources playing, and give the firmware a master output level
  (`design-state.md` §12, "Bring-up checklist", items 7–9).
- **It departs from Bergman's drawing.** `R12` is fitted permanently to ground rather than
  switched in for VCA mode; the input stage runs at gain 2 on a halved signal. VCA mode is
  still not implemented (`R16` is still absent). Recorded in `lpg-bergman.md`.

## Alternatives

- **Keep the old routing and resample in two passes.** Same sound, no live capture, and no
  effects-box use without firmware passthrough. Rejected for what it gives up, not for cost.
- **A switched version** (mute via DG419 + firmware, or a solder jumper). Declined above.
