# Code Composer Studio project

`vuulgaris-touch/` is the CCS project for the MSP430FR2675TPTR.

Import into CCS with **Project > Import CCS Projects**, pointing at this directory.

Build output (`Debug/`, `Release/`) is gitignored. `.settings/` and `.metadata/` are too,
because they carry absolute paths from whichever machine generated them.

## What belongs where

| | |
|---|---|
| `src/main.c` | Hand-written. Link to the Daisy, IRQ, reporting. |
| `../captivate/generated/` | Design Center output. **Regenerated, never hand-edited.** |

Keep those two separate in commits so a regeneration diff stays readable.
