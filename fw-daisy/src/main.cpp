// Vuulgaris V1 - Daisy Patch SM firmware
//
// Skeleton. Brings up the Patch SM and an audio callback, and stubs the touch link.
// Nothing here is tuned; it exists so the toolchain can be proven before the hardware
// arrives. See docs/notes/next-steps.md.
//
// Build:  make libs   (once)
//         make
// Flash:  make program-dfu

#include "daisy_patch_sm.h"
#include "daisysp.h"

using namespace daisy;
using namespace patch_sm;
using namespace daisysp;

DaisyPatchSM hw;

// ---------------------------------------------------------------------------
// Sample buffer
//
// MUST live in SDRAM: scrubbing is arbitrary random access, so the whole sample has
// to be resident. SDRAM objects are declared globally with DSY_SDRAM_BSS and cannot
// have meaningful constructors, hence a plain static array.
//
// 64MB total. Four tracks. Sizing below is a placeholder: decide the advertised
// per-track length limit deliberately, since it is bounded by SDRAM, not card size.
// See docs/decisions/0008-boot-sram-not-qspi.md.
// ---------------------------------------------------------------------------
static constexpr size_t kNumTracks    = 4;
static constexpr size_t kMaxTrackLen  = 48000 * 20;  // 20s mono @48k, placeholder

float DSY_SDRAM_BSS sample_buf[kNumTracks][kMaxTrackLen];
static size_t       sample_len[kNumTracks] = {0, 0, 0, 0};

// ---------------------------------------------------------------------------
// Touch link
//
// The MSP430FR2675 on the faceplate reports one position per pad. Transport is UART
// (A2/A3) or I2C (B7/B8), which are alternate mappings of the same peripheral, plus an
// IRQ line signalling data-ready so we do not poll.
//
// Position is 0..resolution-1 across 175mm. Resolution is configurable in Design Center;
// 1000 gives 0.175mm per step. The real limit is jitter, not resolution: if the reported
// value wanders N counts at rest, usable points = 1000/N. Measure it.
// See docs/decisions/0003-comb-pad-rx0-wraparound.md.
// ---------------------------------------------------------------------------
struct TouchState
{
    float position[kNumTracks];  // 0.0 .. 1.0, normalised
    bool  touched[kNumTracks];
};

static TouchState touch;

static void TouchInit()
{
    for(size_t i = 0; i < kNumTracks; i++)
    {
        touch.position[i] = 0.f;
        touch.touched[i]  = false;
    }
    // TODO: bring up UART/I2C to the MSP430, and the IRQ pin.
    // TODO: BSL flashing path over RST + TEST. Wait ~300ms after entry invocation
    //       before the first command; this BSL version is slow to initialise and
    //       skipping the wait looks exactly like a hardware fault.
    //       See docs/decisions/0005-bsl-over-daisy-uart.md.
}

static void TouchPoll()
{
    // TODO: read from the MSP430 when IRQ asserts.
    //
    // Smoothing goes here, and it is a direct latency tradeoff: scrub position jitter
    // becomes audible warble, but filtering it costs responsiveness. Do not pick a
    // filter constant before measuring real jitter on real copper.
}

// ---------------------------------------------------------------------------
// Audio
// ---------------------------------------------------------------------------
void AudioCallback(AudioHandle::InputBuffer  in,
                   AudioHandle::OutputBuffer out,
                   size_t                    size)
{
    hw.ProcessAllControls();
    TouchPoll();

    for(size_t i = 0; i < size; i++)
    {
        float sig = 0.f;

        // TODO: per-track machine (sampler or synth). Plaits is the synth engine.
        // Sampler reads sample_buf[track] at touch.position[track] * sample_len[track],
        // interpolated, with the read head following the finger.

        out[0][i] = sig;
        out[1][i] = sig;
    }

    // CV outs drive the LPG vactrols. 12-bit, and they can run at audio rate if written
    // per-sample here, though the vactrol's own lag dominates anyway.
    // hw.WriteCvOut(CV_OUT_1, v1);
    // hw.WriteCvOut(CV_OUT_2, v2);
}

int main(void)
{
    hw.Init();
    hw.SetAudioBlockSize(48);
    hw.SetAudioSampleRate(SaiHandle::Config::SampleRate::SAI_48KHZ);

    TouchInit();

    hw.StartAudio(AudioCallback);

    while(1)
    {
        // Display refreshes belong HERE, never in the audio callback.
        // CV output timing is documented as degradable by OLED and MIDI activity.
        // No full-frame redraws during timing-sensitive CV.
        // See docs/decisions/0006-ssd1309-oled.md.
    }
}
