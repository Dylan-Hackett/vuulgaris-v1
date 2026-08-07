# Tuning logs

One dated file per session. The point is to be able to answer "did that get better or worse"
six months from now.

Template:

```markdown
# 2026-MM-DD - <board rev> - <what changed>

Hardware:  single-pad test board rev A / faceplate rev A
Overlay:   none (exposed copper, ENIG)
Env:       bench / in enclosure / in enclosure with PSU running

## Measured
Scan time, 4 sliders:     ___ ms      (Design Center reports directly)
Scan time, 1 slider:      ___ ms
Noise immunity:           on / off
Jitter at rest:           ___ counts  @ resolution ___
  -> usable positions:    ___         (resolution / jitter)
Linearity, worst dev:     ___ mm over 175mm
Lower_Trim / Upper_Trim:  ___ / ___
Dead zone measured:       ___ mm at each end

## Conclusion
Does it sound like an instrument when driving sample position? y/n
What to change next:
```

**The number that matters most is jitter in counts**, because usable resolution is
`resolution / jitter` and smoothing only trades it against latency, which is audible as lag.
