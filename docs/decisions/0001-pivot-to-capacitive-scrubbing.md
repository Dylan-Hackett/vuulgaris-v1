# 0001 - Pivot from Trautonium analog to capacitive sample-scrubbing

**Status:** Accepted
**Date:** pre-2026-08-05 (recorded retroactively from design state section 1)

## Decision

Vuulgaris V1 is a 4-channel sample-scrubbing instrument. Long capacitive copper pads on a
PCB faceplate represent the length of a waveform; dragging a finger along a pad scrubs
through the sample. Each track carries a swappable "machine" that is either a sampler or a
synth, with Plaits as the synth engine.

## What this rules out

The original Trautonium-style analog design is shelved: MPR121 pitch pads, LDC1612
inductive pressure sensing, and the sprung compliance layer all go with it.

## Why

Cost and part count. The compliance layer in particular was mechanical work that had to be
right on every unit, and inductive pressure sensing added a second sensing modality with
its own tuning burden.

## Consequences

- Position sensing is now the whole interaction. Jitter and latency in the touch path are
  directly audible as scrub warble, so they are product-defining rather than incidental.
  See [0003](0003-comb-pad-rx0-wraparound.md) and `../notes/open-questions.md` Q1.
- No pressure axis. Anything the compliance layer would have expressed has to come from
  elsewhere: panel pots, or gesture derived from position over time.
- Playback is random-access by nature, which forces samples into SDRAM.
  See [0008](0008-boot-sram-not-qspi.md).

## What would overturn this

Measured jitter on a real full-length pad bad enough that scrubbing is unusable even with
smoothing that keeps latency acceptable. That is exactly what the single-pad test board in
`../notes/next-steps.md` step 1 exists to find out, and it is cheap on purpose.
