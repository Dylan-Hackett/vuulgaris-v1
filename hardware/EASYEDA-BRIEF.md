# Vuulgaris V1 — EasyEDA layout brief

**Hand this to Claude Code running natively on the Mac, with the
[easyeda-api-skill](https://github.com/easyeda/easyeda-api-skill) installed.**

You are laying out a two-board electronic instrument. Everything below is decided
and verified unless a line says otherwise. **Where something is marked UNRESOLVED,
stop and ask rather than guessing.**

---

## 0. Before you start

Confirm all of these, in this order, and stop if any fails:

1. `node --version` is 18 or higher
2. **EasyEDA Pro DESKTOP client** is running, and it is **version 3.2.x**. The
   browser version cannot load extensions and will not work. The version matters:
   `run-api-gateway` declares `"engines": {"eda": "~3.2.0"}`, and on a 2.x client
   it installs, shows its menu, and silently never connects, because the menu is
   declarative manifest data while the code that opens the socket never runs.
3. The `run-api-gateway` extension is installed from <https://jlc-ext.com/item/oshwhub/run-api-gateway>,
   **enabled, and granted its External Interactions permission** — without that
   permission it loads but never reaches the bridge.
4. The bridge is up: `node ~/.claude/skills/easyeda-api/scripts/bridge-server.mjs &`
   The server picks the first free port in **49620-49629**, so probe the range
   rather than assuming 49620. `/health` must report `"edaConnected": true` and
   `/eda-windows` must list at least one window.

Then read, in the repo root:

- `docs/pin-allocation.md` — the authority on every net. If this brief and that
  file disagree, **that file wins** and you should tell the user.
- `docs/design-state.md` §3 for the CapTIvate layout rules, §6 for the analog section
- `hardware/placement-panel-facing.txt` — exact mm coordinates, generated
- `mockups/faceplate-v1-298x139-FAB.svg` — the faceplate copper, true scale

---

## 1. What this is

A four-channel capacitive sample-scrubbing instrument. You drag a finger along a
long copper pad to scrub through a sample. Desktop format, wooden enclosure.

**Two PCBs:**

| Board | Size | Carries |
|---|---|---|
| **Faceplate** | 298.286 x 139.000mm | 4 capacitive pads (exposed copper), MSP430FR2675 on the BACK, ESD parts |
| **Main** | **max 284.3 x 125.0mm** | Daisy Patch SM, OLED, encoders, SD, I2C expanders, analog LPG, jacks, power |

They connect by one board-to-board cable. **The faceplate screws down onto the tops
of 6mm enclosure walls, so the main PCB must fit inside the cavity.** That is where
the 284.3 x 125.0 limit comes from and it is hard.

---

## 2. Do these in order

**Do NOT try to do it all in one pass.** Each step ends with something checkable.

1. **Project + two boards.** Create the project, two schematic sheets, two PCBs.
2. **Symbols and footprints.** Pull every part by LCSC part number (§4). EasyEDA and
   LCSC are the same company, so the footprint comes with the part. **Report any part
   you cannot find rather than substituting.**
3. **Faceplate schematic.** MSP430 + 16 electrodes + ESD + connector. Small, do it first.
4. **Main schematic.** Sections in §5.
5. **ERC on both.** Fix everything before touching the PCB.
6. **Faceplate PCB.** Import the copper geometry, place the MSP430 and ESD parts.
7. **Main PCB placement.** Use §6 coordinates for panel-facing parts. These are not
   suggestions, they must match the panel openings.
8. **Routing.** See §7. **You are not autorouting this board.**
9. **DRC.**

---

## 3. The rule that matters most

**This is a mixed-signal board.** Capacitive sensing, audio, a switching OLED supply,
and +/-12V analog all share it. A schematic that is electrically wrong looks exactly
like one that is right until it is powered up.

**So: after every section, state what you connected and what you are unsure about.**
Do not report success. Report what you did.

---

## 4. Parts

| Ref | Part | LCSC | Note |
|---|---|---|---|
| U1 | Daisy Patch SM | n/a | Electrosmith direct, $31.99. 2x 20-pin headers. |
| U2 | MSP430FR2675TPTR | **C2052972** | LQFP-48. **Faceplate, back side.** |
| DS1 | 2.42" SSD1309 OLED SPI | **C5139768** | |
| U3, U4 | MCP23017 I2C GPIO expander | search | SSOP-28 or SOIC-28 |
| ENC1-ENC10 | ALPS EC12E2430803, **DETENTLESS 0/24** | **C470684** | 10 parameter encoders. 3 pins, no switch. |
| ENC0 | ALPS EC11L1525G01, 30/15 detents, **with push** | **C2991196** | Main UI encoder only. Detents are wanted here. **25mm shaft, matches ENC1-10.** |
| RV1 | dual-gang 10K pot | search | LPG offset |
| RV2, RV3 | 10K pot | search | CV amount L / R |
| SW1, SW2 | DPDT toggle, break-before-make | search | **non-shorting** |
| SW3 | tactile switch, tall plunger | search | shift |
| J1 | microSD socket | **C393941** | |
| D1-D16 | TPD1E10B06 ESD diode | search | **one per electrode** |
| R1-R16 | 470R-1k 0402 | search | one per electrode, MCU side of the TVS |
| Y1 | 32.768kHz crystal | search | **footprint only, may go unpopulated** |
| VT1-VT4 | VTL5C3 vactrol | n/a | Xvive. LPG. |
| J2-J6 | 3.5mm jack, Thonkiconn | search | 5 jacks, §5.6 |

Also: TL07x op-amps for the LPG, 2x 3.3V LDO (§5.5), decoupling throughout.

---

## 5. Schematic, by section

### 5.1 Daisy Patch SM header

**The symbol in use is missing pin A7.** `Electrosmith-Boards_ES_DAISY_PATCH_SM_REV1`
has 39 pins, not 40; **A7 is GND** and has to be connected by hand. It lives in a
read-only community library, so it cannot be edited in place — the API refuses copy,
edit and open on it. Both KiCad sources
([Kad-Luka](https://github.com/Kad-Luka/ES-Patch-SM-KiCad-Footprint),
[GregBurns](https://github.com/GregBurns/sm_kicad)) carry all 40 with A7 = GND, if a
correct symbol is ever wanted. **A missing pin passes ERC silently** — there is no pin,
so there is nothing to report as unconnected. Check A7 by eye before fab.

**Transcribe `docs/pin-allocation.md` "The full header" table exactly.** Do not
infer pin functions from names. Notable:

- `A8` is **RESERVED and must be left unconnected.** It is for a BBD delay clock in
  a later revision. Do not use it for anything.
- `A2`, `A3`, `D8`, and `C2`-`C8` are **free**. Leave them as unconnected test pads.
- `C9` (CV_8) is the **CV input jack**. It is conditioned on-module.
- `B5`, `B6` are **gate outputs**, native 0-5V.
- `B10` is **gate in / clock**.
- `C1` is **CV out**, `C10` is the **LPG envelope** (one output, splits in analog).

### 5.2 Two separate links — do not merge them

| Link | Daisy pins | Devices | Crosses the cable? |
|---|---|---|---|
| **UART4** | **A2** RX, **A3** TX | MSP430FR2675 | **yes**, point-to-point |
| **I2C1** | B7 SCL, B8 SDA | MCP23017 x2 @ 0x20, 0x21 | **no**, main PCB only |

**The touch chip is NOT on the I2C bus.** TI's CapTIvate protocol needs a third
IRQ wire over I2C but only two over UART, and that third wire would be `A8`,
which is reserved. Putting them on one bus also means a hung touch chip takes the
encoders down with it.

**One pair of I2C pull-ups only**, on the main PCB, 2.2k to 3V3. Strap the
expander address pins A0/A1/A2 to ground or 3V3 accordingly.

**MSP430 UART goes on the DEFAULT UCA0 mapping, pins 4 (TXD) and 5 (RXD)**, not
the remapped 44/45, so that runtime and BSL share the same wires. **Route 44/45
to the connector as well** as a fallback.

### 5.3 Encoders

**10 encoders on the expanders.** Each needs 2 pins (A and B) plus a common to ground.
20 expander pins used of 32. Enable the MCP23017 internal pull-ups.

**ENC0, the main UI encoder, goes direct to the Daisy**: `D3`, `D4`, push on `B9`.
Deliberate, it wants lower latency than a 500Hz I2C poll.

### 5.4 MSP430 and the capacitive front end

**All 16 CapTIvate electrodes are used**, 4 pads x 4. Keep each pad's four electrodes
in ONE block so they measure in parallel:

| Block | Signals | LQFP-48 pins |
|---|---|---|
| CAP0 | CAP0.0-0.3 | 23, 24, 25, 26 |
| CAP1 | CAP1.0-1.3 | 27, 28, 29, 30 |
| CAP2 | CAP2.0-2.3 | 32, 33, 34, 35 |
| CAP3 | CAP3.0-3.3 | 36, 37, 38, 39 |

Element order within a pad: `RX0 -> E00, RX1 -> E01, RX2 -> E02, RX3 -> E03`.

**Every electrode gets a TVS to ground and a series resistor on the MCU side of it.**
Sixteen of each. This is the repetitive work worth scripting.

Other MSP430 pins:

| Function | Pin |
|---|---|
| DVCC | 1 |
| DVSS | 48 |
| RST / SBWTDIO | 2 |
| TEST / SBWTCK | 3 |
| **VREG** | **31** — needs an external decoupling cap. Easy to miss. |
| I2C SDA / SCL | 14 / 15 |
| XIN / XOUT | 47 / 46 — crystal footprint |

**Put SBW test pads on the faceplate**: TEST, RST, 3V3, GND. Four pads. They are the
only recovery path if the touch firmware breaks, and they cost nothing.

Also add the **CAPTIVATE-PGMR connector** footprint. Unpopulated on production, but
tuning is impossible without it.

### 5.5 Power — three separate 3V3 rails

**This is not optional and it is the thing most likely to be got wrong.**

The OLED module has an onboard DC-DC converter that dumps switching noise back onto
its supply. This is documented on the Daisy forums as audible on the outputs. It is a
power problem, not EMI.

```
Daisy 5V (A6) --[ferrite]--[LDO 3V3]--[470uF + 100nF]-- OLED
Daisy 5V (A6) --[ferrite]--[LDO 3V3]--[10uF + 100nF]--- MSP430
                            Daisy's own 3V3 -- untouched
```

**Do not share one LDO between the OLED and the MSP430.** Capacitive sensing is
supply-noise sensitive and the OLED is the noise source. **The 470uF at the OLED is
doing most of the work** and is not negotiable.

Star ground: the OLED's return goes to the supply ground point directly, not through
the analog section.

### 5.6 Jacks and the analog section

Five jacks: CV in (`C9`), CV out (`C1`), gate in (`B10`), gate out x2 (`B5`, `B6`).

The **Bergman stereo low pass gate** takes `AUDIO_OUT L/R` (`B2`, `B1`) and returns to
`AUDIO_IN L/R` (`B4`, `B3`) through SW2. `CV_OUT_1` (`C10`) carries **one** envelope
which splits in analog through RV2 and RV3, summed with RV1 as offset.

**RV1, RV2, RV3, SW1 and SW2 never touch the Daisy.** They are analog controls on the
LPG board. If you find yourself wiring them to a Daisy pin, something is wrong.

---

## 6. PCB placement

**Use `hardware/placement-panel-facing.txt` verbatim.** Origin is the panel top-left,
X right, Y **down**, millimetres. Those coordinates are generated from the faceplate
artwork and **must match the panel openings**. Do not round them or nudge them for
routing convenience.

Everything else (MSP430, expanders, LDOs, decoupling, LPG) is free placement inside
the cavity.

**Hard constraint: the main PCB must not exceed 284.3 x 125.0mm.**

---

## 7. Routing

**Do not autoroute this board.**

| Nets | How |
|---|---|
| 16 electrode traces | **Script it.** Repeating geometry, explicit rules, identical 16 times. Read `docs/design-state.md` §3 "Layout rules" FIRST. |
| Encoder fan-out to expanders | Script or autoroute, low stakes |
| SD, OLED SPI, I2C | Autoroute acceptable |
| **Analog: LPG, audio in/out, CV** | **Hand-route. Ask the user.** |
| **Power and ground** | **Hand-route. Ask the user.** |

On a board carrying capacitive sensing, audio, a switching OLED rail and +/-12V
analog, **the routing is the design**. An autorouter knows none of that.

**The faceplate is a 4-layer board**: L1 electrodes (exposed copper, NO soldermask),
L2 traces, L3 hatched ground, L4 MSP430 and support. ENIG finish, not HASL, because
the exposed copper is the touch surface.

---

### 4.1 The encoders must be DETENTLESS — decided 2026-08-13

**C202365 was wrong and is withdrawn.** It is an ALPS **EC11E18244AU**: LCSC lists it
as **36 detents / 18 pulses**. Thirty-six clicks per turn on ten continuously-variable
parameters is the opposite of what this instrument wants.

The replacement must be **smooth, no detents, no notches**. Bourns **PEC11R** is the
obvious family — the detent code sits in the part number (`S` = no detent, `N` =
detented, **confirm against the Bourns datasheet, not a distributor field**).
`PEC11R-4015K-S0024` is detentless at 24 PPR but reads **out of stock at LCSC**, which
matters if JLC is assembling.

**CHOSEN 2026-08-13 and fitted in the schematic: `C470684`, ALPS Alpine `EC12E2430803`.**
All eleven are placed and wired (A/B/C, plus D/E on ENC0). Dylan confirmed the faceplate
artwork can move to suit the part rather than the reverse.

**Consequence for the panel: `mockups/generate-faceplate.py` still cuts EC11 bushing
holes.** EC12 is a different body and bushing, so the generator has to be updated and
`hardware/placement-panel-facing.txt` regenerated before any fab output. The *positions*
in that file stay valid; the hole diameters do not.

| | |
|---|---|
| Detents / pulses | **0 / 24** — detentless, confirmed on LCSC's spec table |
| Stock | **1541** at LCSC, ~$0.50 |
| Mount | through hole, straight |
| Footprint | `SW-TH_EC12EXXXX` — **EC12, not EC11.** Different body, different footprint. |

**RESOLVED from the ALPS datasheets, 2026-08-13. Detentless and push-switch are
mutually exclusive in this family**, so the two roles take two part numbers:

| | ENC1-ENC10 | ENC0 |
|---|---|---|
| Part | `C470684` EC12E2430803 | `C2991196` EC11L1525G01 |
| Detents / pulses | **0 / 24** | 30 / 15 |
| Push switch | none (3-pin) | **yes** (A/B/C + D/E) |
| Shaft | **25mm** | **25mm — matched** |
| LCSC stock | 1541 | 3720 |

**Shaft lengths are matched at 25mm deliberately.** The first pick for ENC0 was
`C202365` EC11E18244AU, which has the switch but a **20mm** actuator — 5mm shorter than
the EC12E, so its knob would have sat visibly low. `C2991196` is the same idea at 25mm
and is better stocked. The alternative was moving all ten parameter encoders to a 20mm
part (`C470602`), but that one is the 标准型 body with **no threaded bushing**, leaving
the solder joints to carry side load from a knob next to a 175mm touch pad — rejected.

The datasheet evidence, so nobody re-opens this: ALPS lists switched EC12 parts only
under **EC12D** (`EC12D1524403`, `EC12D1564402`, `EC12D1524406`, `EC12D1564404`) and
**every one has 30 detents**. The detentless parts are all EC12E, which is a 3-pin body
with no switch section. The 5-pin EasyEDA symbol is a generic family symbol and is not
evidence of a switch. EC11E18244AU's own datasheet states `Push-on switch: With`.

Detents on ENC0 are **wanted**, not tolerated — it is the menu/UI encoder, where
discrete steps suit navigation. The ten parameter encoders stay smooth.

Still open: **shaft length**, which waits on the enclosure height (unresolved item 2).
It now has to be resolved for *two* different bodies, EC11 and EC12.

**Also note the pulses-per-detent trap** that made the old part wrong in a second way:
36 detents against 18 pulses is two detents per quadrature cycle. On a detentless part
this stops being a feel problem and becomes purely a counts-per-revolution decision,
but the firmware still has to know the number.

## 8. Unresolved — ask, do not guess

1. **Q21, BSL pin mapping.** The MSP430's bootloader pins are factory-fixed in TLV.
   Using the **default UCA0 mapping (pins 4/5)** for runtime UART should make
   runtime and BSL the same wires, which dissolves the question. Unconfirmed on
   hardware. **Route the remapped pins 44/45 as well**, as a fallback.
2. **Enclosure height.** Not yet determined. It sets the encoder shaft and shift
   plunger length. Do not choose part variants that depend on it.
3. **Q1, whether the pads work at all.** Untested. Everything else is contingent.
4. **Vactrol availability.** Excelitas discontinued the line; Xvive is the reissue.
5. The **32.768kHz crystal** may go unpopulated. Fit the footprint regardless.

---

## 8b. API behaviour worth knowing before you start

Learned the hard way on 2026-08-12. All three cost time.

| Trap | What actually happens |
|---|---|
| `sch_PrimitiveWire.getAll()` / `getAllPrimitiveId()` | **Under-reports.** Returned 1 when the document held 30 wires. **Verify against `sys_FileManager.getDocumentSource()`** and count `"type":"WIRE"` atoms. The source is the only truth. |
| `sch_PrimitiveAttribute.createNetLabel()` | **Hangs.** 30s timeout, creates nothing. Use `sch_PrimitiveWire.create([x,y,x2,y2], netName)` instead — a short stub off each pin carries the net and works reliably. |
| `lib_Symbol.get` / `openInEditor` / `copy` | **Throw on read-only community libraries**, and the error message is literally `[object Object]`. Symbols from imported libraries cannot be edited or copied through the API. |

Also: `createProject` silently returns `undefined` in **half-offline mode**, and
`deleteBoard` **orphans** its schematic and PCB rather than deleting them — clean
those up by uuid afterwards.

**The bridge enforces a 30-second server-side request timeout**, whatever the client
timeout says. One `/execute` call fits roughly 40 API round trips. Batch work into
chunks under that, and **cache pin lookups per component** — re-reading pins inside a
loop is what blows the budget. A timeout does **not** roll back: the work already done
persists, so re-query state before retrying or you will place everything twice.

`lib_Symbol.getRenderImage` and `lib_Device.searchByProperties` are also unreliable —
the first throws, the second returned an inductor when asked for a 470uF capacitor.

**Pin stubs connect by net name.** Two pins carrying the same net name are connected
whether or not a wire is drawn between them, which is what makes a 40-pin fan-out
tractable through the API.

## 9. When you are done

Report: parts you could not find, nets you were unsure about, any placement you had
to move and why, ERC and DRC output in full, and **anything in this brief that
contradicted `docs/pin-allocation.md`**.

Do not report that it is finished. Report what state it is in.
