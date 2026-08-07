# 0008 - Build APP_TYPE=BOOT_SRAM, reserve QSPI for samples

**Status:** Accepted
**Date:** pre-2026-08-05 (recorded retroactively from design state section 5)

## Decision

Compile **`APP_TYPE=BOOT_SRAM`**, not `BOOT_QSPI`.

## Why

`BOOT_QSPI` runs the program from QSPI and can grow to ~7.75MB, which eats the sample
space. SRAM execution is also faster. Ceiling is roughly 480-512KB with a custom linker
script, which is plenty for this application.

## Memory plan

| Tier | Size | Volatile | Use |
|---|---|---|---|
| SDRAM | 64MB | yes | **Playback buffer.** Samples resident here. Scrubbing is arbitrary random access, so this is mandatory, not an optimisation. |
| QSPI flash | 7936 KB region | no | Firmware (at 256KB offset) + factory samples |
| SD card | unlimited | no | User samples |

SDRAM objects must be declared globally with `DSY_SDRAM_BSS` and cannot have meaningful
constructors. **Plan buffers as static arrays.**

## QSPI-only sample capacity (no SD card), ~7.2MB usable after firmware

| Format | Total | Per track (/4) |
|---|---|---|
| 48k 16-bit mono | 75 sec | 19 sec |
| 44.1k 16-bit mono | 81 sec | 20 sec |
| 32k 16-bit mono | 112 sec | 28 sec |
| 22k 16-bit mono | 163 sec | 40 sec |
| 48k 16-bit stereo | 37 sec | 9 sec |

Tool for loading: `DADDesign-Projects/Daisy_QSPI_Flasher` on GitHub, over USB.

## Sample storage strategy

Factory samples in QSPI so the instrument makes sound with no card. User samples on SD.
Both stream into SDRAM at load; **playback always from SDRAM so scrubbing has no latency.**

**Decide the advertised per-track length limit early.** It is bounded by SDRAM, not card size.

## SD bus width: 1-bit, decided

**RESOLVED 2026-08-06. Use 1-bit.** Three pins (CLK, CMD, D0) on **D6, D7, D5**, freeing
D2, D3, D4. GPIO is the scarce resource in this design, and the pin budget does not close at
4-bit.

Bandwidth is not a real cost here: **samples load into SDRAM at boot rather than streaming**,
so bus width only affects a boot-time delay of a second or two.

### The bootloader question (Q4), answered

The worry was that the Daisy bootloader might hardcode 4-bit for SD-card firmware updates,
which would break 3-pin wiring. **It is the other way around.**
`DaisyBootloader/shared/bootloader.cpp:164` (HEAD `8b279a8`):

```cpp
sd_cfg.speed = SdmmcHandler::Speed::MEDIUM_SLOW;
sd_cfg.width = SdmmcHandler::BusWidth::BITS_1;
```

libDaisy's `Config::Defaults()` is 4-bit @ 50MHz; **the bootloader explicitly overrides to
1-bit.** SD-card firmware drops work fine on 3-pin wiring.

### Supporting data, for the record

- Electrosmith testing: smooth playback at 4-bit down to 400kHz, or **1-bit at 12.5MHz**.
  1-bit at 400kHz is too slow to stream audio.
- Community threads skew toward 1-bit, with several people getting SD working only after
  setting `BusWidth::BITS_1`. Those were breadboard and flying-wire setups, where three extra
  high-speed lines on jumper wires is exactly where signal integrity dies. On a real PCB
  4-bit should behave, but we are not using it anyway.

**Note on the old advice to "route all 6 pins anyway".** Superseded. D2, D3 and D4 are now
allocated to the OLED DC and the encoder. See `../pin-allocation.md`.

## Firmware update paths

Bootloader lives in internal 128KB flash; the application always lives in QSPI at a 256KB
offset. Grace period is 2.5s on startup with sinusoidal LED blinks.

- **USB DFU** - works, zero effort, requires a cable.
- **SD card drop** - much nicer for a product. Gated on the 4-bit question above.
- **MIDI SysEx** - the better no-cable path. Digital transport, no level dependence, and
  `SonBonAudio/DaisySeedMidiBoot` already exists, forked from OpenWare.
- **Audio (QPSK)** - **not recommended.** Electrosmith names it as an example of what forks
  can add, and the reference implementation is Mutable Instruments' `stm_audio_bootloader`,
  but a documented user account of the MI process reports hundreds of failed attempts
  across volumes and playback devices. You would also fork and maintain a bootloader and
  bring up the codec before it can listen.
