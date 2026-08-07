# fw-daisy

Firmware for the Daisy Patch SM: audio engine, sample playback, UI, and the link to the
touch MCU on the faceplate.

## Setup

```bash
git clone --recurse-submodules <this repo>
# or, if already cloned:
git submodule update --init --recursive

make libs     # build libDaisy + DaisySP, once
make          # build the application
make program-dfu   # flash over USB DFU
```

Requires `arm-none-eabi-gcc` and `dfu-util`.

## Submodules

| Path | Repo | Pinned at |
|---|---|---|
| `libDaisy/` | electro-smith/libDaisy | `c02245d` |
| `DaisySP/` | electro-smith/DaisySP | see `git submodule status` |

Both are shallow clones. To move to a newer libDaisy:
`cd libDaisy && git fetch --unshallow && git checkout <ref>`, then commit the pointer.

## Build type is not the default

`APP_TYPE = BOOT_SRAM`, deliberately. `BOOT_QSPI` runs the program from QSPI and can grow
to ~7.75MB, which eats the sample space. SRAM execution is also faster, with a ceiling of
roughly 480-512KB using a custom linker script.

See [ADR 0008](../docs/decisions/0008-boot-sram-not-qspi.md).

## Memory model

| Tier | Size | Volatile | Use |
|---|---|---|---|
| SDRAM | 64MB | yes | **Playback buffer.** Scrubbing is arbitrary random access, so samples must be resident. |
| QSPI | 7936 KB | no | Firmware (256KB offset) + factory samples |
| SD | unlimited | no | User samples |

SDRAM buffers are declared with `DSY_SDRAM_BSS` at global scope and cannot have meaningful
constructors. They are plain static arrays in `src/main.cpp`.

## Rules that will bite you

- **Display refreshes stay out of the audio callback.** CV output timing is documented as
  degradable by OLED and MIDI activity. No full-frame redraws during timing-sensitive CV.
- **DMA buffers must be in the DMA memory section and at global scope.**
- **Do not use B9/B10 for the encoder.** They are Input Only, and libDaisy defaults `GateIn`
  to inverted because of the suggested BJT input circuit.
- **ADC_9-ADC_12 pots wire to 3V3 (A10), CV_1-CV_8 pots wire to 5V (A6).** Different groups,
  different reference.

## Findings from the submodule source

Two open questions from `docs/notes/open-questions.md` were closed by reading the pinned
source. Recorded here because the design state still carries the old concern.

### Q4: the bootloader uses 1-bit SD, not 4-bit

`DaisyBootloader/shared/bootloader.cpp:164` (HEAD `8b279a8`):

```cpp
SdmmcHandler::Config sd_cfg;
sd_cfg.Defaults();
sd_cfg.speed = SdmmcHandler::Speed::MEDIUM_SLOW;
sd_cfg.width = SdmmcHandler::BusWidth::BITS_1;
```

So SD-card firmware drops work on 3-pin wiring. The worry was backwards: it is `libDaisy`'s
`Config::Defaults()` that is 4-bit @ 50MHz, and the bootloader explicitly overrides it.
**Route all 6 pins anyway** and pick the width in software.

### Q9: the SSD130x DMA path is live

`libDaisy/src/dev/oled_ssd130x.h`. `Update()` branches on `useDma_` and calls
`TransferPageDma(0)`, which calls `transport_.SendDataDma(...)` at line 646 with
`SpiPageCompleteCallback` chaining page to page. The commented-out line at 650 is a leftover
debug variant, not the real call.

The design state's concern that `SendDataDma` "appears commented out" is stale for this
revision. At 1KB per frame it barely mattered either way.

## TODO

- Touch link over UART/I2C + IRQ, and the BSL flashing path over RST + TEST
- Sampler engine: interpolated read from SDRAM at the finger position
- Plaits synth machine
- Position smoothing, tuned against **measured** jitter, not guessed
- SSD1309 UI
- Sample loading from QSPI and SD into SDRAM at boot
