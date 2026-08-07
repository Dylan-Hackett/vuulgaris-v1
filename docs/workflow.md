# Performance workflow

**Status: WORKING.** Captured 2026-08-07 from the design intent. Not yet decided, not yet
firmware. Recorded now because it constrains hardware choices that are about to be locked.

## The intent, as stated

> Each channel will have a looper, possibly of different lengths but all synced to a divisible
> length, and that will be able to be resampled to one of the channels as a sample, if the
> resample switch is flipped, allowing for analog filtering.

Everything below is either that statement restated precisely, or a consequence of it. The
consequences are marked as such, because they are inference and have not been confirmed.

## The loop

```
   1. RECORD      four independent loopers, one per channel,
                  lengths locked to integer multiples of a base length

   2. PLAY        each channel's loop plays back; the capacitive pad
                  scrubs position within it

   3. MIX         channel outputs sum into the stereo LPG

   4. COLOUR      LPG applies envelope x CV amount + offset,
                  in stereo VCF or stereo VCA mode

   5. RESAMPLE    with the SOURCE switch on "resample", the LPG's
                  analog output returns to AUDIO_IN and is captured
                  into one channel as a new sample

   6. repeat from 2, now scrubbing the resampled material
```

Step 5 is the point of the whole instrument: **the capture happens after the analog stage, so
the filter and the gate are printed into the sample**, not applied to it at playback. Whatever
the LPG was doing at capture time is now permanent material that can itself be scrubbed and
resampled again.

## Loop sync: lengths are integer multiples of a base

**Confirmed intent.** Channels may hold loops of different lengths, but every length is a whole
multiple of one base length, so wrap points periodically coincide instead of drifting.

**Consequence worth knowing before choosing the allowed multipliers.** The whole four-channel
pattern only repeats at the **least common multiple** of the four multipliers:

| Allowed multipliers | Global repeat |
|---|---|
| 1, 2, 4, 8 (powers of two) | **8** base units |
| 1, 2, 3, 4 | **12** base units |
| 1, 2, 3, 5 | **30** base units |

Admitting a 3 nearly doubles the time before the pattern comes back around, and admitting a 5
makes it thirty. That is either the feature or the problem depending on what the instrument is
for. **Powers of two behave predictably; odd multipliers are where polymetric interest lives.**
This is a musical decision, not a technical one, and it should be made deliberately rather than
falling out of whatever the encoder happens to scroll through.

### The base length must be defined in samples, not BPM

**Consequence, and a real trap.** Sync only holds if the base length is an exact integer number
of samples. Derive it from a tempo and it usually is not:

| Tempo | 1 bar at 48kHz |
|---|---|
| 120 BPM | 96000 samples exactly |
| 90 BPM | 128000 samples exactly |
| **140 BPM** | **82285.714... samples** |

At 140 BPM the bar does not land on a sample boundary. Round it and every loop drifts by a
fraction of a sample per cycle, which accumulates. **Store the base length as an integer sample
count and display the resulting BPM, rather than storing BPM and computing samples.** The
displayed tempo is then quantised by the sample rate, which is invisible in practice and
removes the drift entirely.

## The resample path is analog, and that has three consequences

### 1. The Daisy does not know which source is selected, and does not need to

The **source switch is a DPDT analog switch on the LPG board** feeding `AUDIO_IN_L/R`. It picks
between the LPG return and the external input. The Daisy has **no pin on it** (see
[pin-allocation.md](pin-allocation.md)), so firmware simply records whatever arrives.

Functionally this is fine. **The cost is that the OLED cannot show the current source**, the
same trade already accepted for the analog offset pot. If showing it ever becomes important,
`B10 (GATE_IN_1)` is the only pin left.

### 2. The analog round trip adds latency, which offsets the loop start

Resampling leaves through the DAC, crosses the LPG, and returns through the ADC. That path has
a real, non-zero delay: codec group delay plus at least one audio block. **A resampled loop will
therefore start slightly late relative to the loop it was captured from**, and the offset is
constant, so it can be compensated in firmware once measured.

**The exact figure is not known and must be measured on the prototype.** It is not safe to
assume it is negligible, because the whole sync scheme is built on sample-accurate loop
boundaries. Opened as [Q19](notes/open-questions.md).

### 3. Resampling a channel into itself is a feedback loop

If the destination channel is still playing into the mix while being resampled, its output
returns through the analog path into its own input. **This is genuine acoustic feedback through
the LPG**, not a metaphor, and with the gate open it will run away.

Three ways to handle it, in increasing order of how much fun they preserve:

- **Forbid it.** Mute the destination channel during resample capture.
- **Allow it, with the LPG as the limiter.** The gate closing is what stops the runaway, which
  is arguably the correct Buchla-ish answer.
- **Allow it and warn.** Let it happen, but do not let the default state be a screaming board.

**Not decided.** Opened as [Q20](notes/open-questions.md).

## Memory budget

Loop buffers and sample buffers both live in **SDRAM, 64MB, volatile** (see
[design-state.md](design-state.md) section 5). Total record time across the whole instrument:

| Format | Whole 64MB | Split 4 ways | 4 ways, loop + sample each |
|---|---|---|---|
| int16 mono | 699s | 175s | 87s |
| int16 stereo | 350s | 87s | 44s |
| float32 mono | 350s | 87s | 44s |
| **float32 stereo** | **175s** | **44s** | **22s** |

**The rightmost column is the honest one**, because a channel that is being resampled into needs
somewhere to put the new material without destroying what is still playing.

Two things follow. **float32 stereo throughout costs 8x int16 mono** and buys about 22 seconds
per channel, which may or may not be enough. And **SDRAM is volatile**, so loops do not survive
power-off; anything worth keeping has to be written to the SD card deliberately.

## What this does not yet specify

- How the resample **destination channel** is chosen (encoder plus OLED is the obvious answer,
  but it is not decided)
- Whether a channel holds a loop and a sample **simultaneously** or whether resampling
  **overwrites** the channel
- What **fires the envelope**, still the open architectural question from
  [pin-allocation.md](pin-allocation.md): there is no external trigger, so it must come from
  touch onset, note events, or a sequencer
- Whether loop record is **quantised** to the base length or free-running and rounded
