# Design Center generated output

**Do not hand-edit anything in this folder.** CapTIvate Design Center regenerates it, and
your edits are gone the next time you press Generate.

Expected files once the project exists:

```
CAPT_App.c / .h
CAPT_UserConfig.c / .h    <- sensor definitions, electrode assignment, tuning parameters
CAPT_BSP.c / .h
CAPT_Manager.c / .h
```

Tuning parameters that end up here, and are worth reviewing in every diff:

- Conversion count per electrode (**retune lower** for the no-overlay case)
- `Lower_Trim` / `Upper_Trim` per slider
- Slider resolution (1000 gives 0.175mm per step over 175mm)
- Noise immunity / frequency hopping on or off (**x4 scan time when on**)
- Filter coefficients (direct latency tradeoff against jitter)

Commit regenerated output as its own commit, separate from hand-written code, so the diff is
readable.
