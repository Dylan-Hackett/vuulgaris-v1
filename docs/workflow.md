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

Sizes taken from libDaisy's own linker script at the pinned submodule commit
(`core/STM32H750IB_sram.lds`), not from marketing copy:

```
SDRAM     (RWX) : ORIGIN = 0xc0000000, LENGTH = 64M
QSPIFLASH (RX)  : ORIGIN = 0x90040000, LENGTH = 7936K   <- after the 256K firmware offset
SRAM      (RWX) : ORIGIN = 0x24000000, LENGTH = 512K - 32K
```

Loop and sample buffers live in **SDRAM: 64MB, volatile**. Total record time, whole instrument,
at 48kHz:

| Format | Whole 64MB | Split 4 ways | 4 ways, loop + sample each | QSPI (persistent) |
|---|---|---|---|---|
| **int16 mono** | **11.7 min** | **175s** | **87s** | 85s |
| int16 stereo | 5.8 min | 87s | 44s | 42s |
| float32 mono | 5.8 min | 87s | 44s | 42s |
| float32 stereo | 2.9 min | 44s | 22s | 21s |
| int16 mono @32k | 17.5 min | 262s | 131s | 127s |
| int16 mono @22k | 25.4 min | 380s | 190s | 184s |

**The "loop + sample each" column is the honest one**, because a channel being resampled into
needs somewhere to put new material without destroying what is still playing.

**Storage format is an 8x lever and costs almost no CPU either way.** int16 mono against
float32 stereo is the difference between 87 and 22 seconds per channel. Process in float
internally, store in int16, convert at the buffer boundary.

**int16 storage is probably not where quality is lost here.** Every resample pass already
crosses the PCM3060 codec (confirmed as `Pcm3060 codec;` in `daisy_patch_sm.h`) and the analog
LPG, and that round trip contributes its own noise floor each time. That floor most likely
dominates 16-bit quantisation, which would make float32 storage an expensive way to preserve
headroom the analog path has already spent. **Worth confirming by measurement before it is
treated as settled.**

**SDRAM is volatile.** Loops do not survive power-off. Anything worth keeping has to be written
to the SD card deliberately, which is a UI feature that does not exist yet.

## CPU load

**Short version: the sampler path is cheap, and the synth path is where the budget goes.**

At 48kHz the CPU has **10,000 cycles per sample** at 480MHz, regardless of block size.

### The scrub and loop engine is not the problem

| Work, 4 channels stereo | Cycles/sample | Share of budget |
|---|---|---|
| Linear interpolation | 80 | **0.8%** |
| 4-point Hermite interpolation | 320 | **3.2%** |
| SDRAM misses, smooth scrub | 15 to 50 | **0.1 to 0.5%** |
| SDRAM misses, worst case every read | 240 to 800 | **2.4 to 8%** |

Recording is a plain write and rounds to nothing.

**Why the SDRAM figures are low even though SDRAM is slow.** The Cortex-M7 has a 32-byte cache
line, which holds 16 int16 samples. A finger scrubbing a pad moves *smoothly*, so consecutive
reads land in the same line and most of them hit cache. The miss cost is amortised roughly
16 to 1. The worst-case row assumes every single read misses, which is what a hard jump or a
very fast scrub looks like, and even that stays inside the budget.

**So the whole four-channel scrub-and-loop engine should land comfortably under 15%.**

### Four Plaits engines is the real load

Plaits ships on an **STM32F373, Cortex-M4 at 72MHz** (verified against ST's part page and
Mutable's own tech notes). The Daisy is a **Cortex-M7 at 480MHz**.

| | |
|---|---|
| Clock ratio | 6.67x |
| Times CoreMark/MHz, M7 5.0 against M4 3.4 | **~9.8x total throughput** |
| One Plaits engine | **~10% of the Daisy** |
| Four engines | **~41%** |

That leaves room, but it is the line item to watch, and it is **the synth machine, not the
sampler machine**. Four channels all running Plaits at once is the worst case; four channels
scrubbing samples is nearly free by comparison.

### These are estimates, and libDaisy ships the tool to replace them

Everything above is arithmetic from verified part specs, **not measurement**, and cache
behaviour in particular is the kind of thing that defies prediction.

**libDaisy has `CpuLoadMeter` at `src/util/CpuLoadMeter.h`.** Call `OnBlockStart()` and
`OnBlockEnd()` around the audio callback and read min, max and average. **Put it on the OLED
during development.** The max reading is the one that matters, because an average of 40% with
occasional 100% spikes is a clicking instrument.

## What this does not yet specify

- How the resample **destination channel** is chosen (encoder plus OLED is the obvious answer,
  but it is not decided)
- Whether a channel holds a loop and a sample **simultaneously** or whether resampling
  **overwrites** the channel
- What **fires the envelope**, still the open architectural question from
  [pin-allocation.md](pin-allocation.md): there is no external trigger, so it must come from
  touch onset, note events, or a sequencer
- Whether loop record is **quantised** to the base length or free-running and rounded
