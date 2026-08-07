# Gerbers

One dated subfolder per fab order, so an order can always be reproduced exactly:

```
2026-08-05-faceplate-test-pad-v1/
  gerbers.zip
  bom.csv
  cpl.csv
  ORDER.md      fab, options chosen, price, lead time, what changed since last time
```

Never overwrite a folder that has been ordered. Make a new one.

## Standing fab options

| Option | Value | Why |
|---|---|---|
| Surface finish | **ENIG** | HASL feels wrong under a sliding finger and will not wear. Non-negotiable on the faceplate. |
| Layers | 4 (faceplate) | L1 electrodes / L2 traces / L3 hatched ground / L4 components |
| Min trace/space | 0.15mm enforced | Pad generator checks against this. Sub-0.127mm copper etches away. |

Flag on any order containing the microSD socket: **JLC needs an assembly fixture** to
support it during placement.

## First thing to order

Not the faceplate. **One cheap 2-layer board with two pads in final tooth geometry, ~216mm**,
roughly $50 and 2 weeks. Measures monotonicity, continuity and repeatability before the
faceplate exists, and the second pad answers the inter-pad gap question that gates the panel.
See [next-steps.md](../../docs/notes/next-steps.md) step 0.
