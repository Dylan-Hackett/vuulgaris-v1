# Docs

- **[design-state.md](design-state.md)** - the handoff document. The single source of truth
  for the whole project. Everything else in this folder is derived from it.
- **[pin-allocation.md](pin-allocation.md)** - **resolved.** Safe to lay out against.
- **[panel-budget.md](panel-budget.md)** - faceplate area arithmetic. **Working, not decided.**
  The 219 x 110mm in design-state section 11 does not fit the current design.
- **[decisions/](decisions/)** - ADRs for choices already made and expensive to revisit.
- **[notes/](notes/)** - open questions and the worklist. Expected to change.

## How these relate

`design-state.md` is authoritative and should be updated as things change. The ADRs pull
the *decided* parts out of it into one-file-per-decision form so that a decision and its
reasoning can be cited from a schematic comment or a commit message. The notes pull the
*undecided* parts out into a worklist.

If a fact appears in both design-state.md and an ADR and they disagree, design-state.md
wins and the ADR needs updating.
