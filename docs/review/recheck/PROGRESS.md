# Recheck progress, 2026-10

Runbook: `docs/notes/recheck-prompts.md`. One line per section, updated in each commit.

Branch: `claude/epic-lamport-gbvvd4` (the session's assigned branch; the runbook
names `recheck/2026-10`, which is not the branch this cloud session was assigned).

| section | status | defects | blocked | notes |
|---|---|---|---|---|
| 01 inventory and chain integrity | done | 2 doc | 2 | gate passed: 944/944 main, 145/145 faceplate (runbook's 942 is stale) |
| 02 power | done | 1 doc | 4 | +12 V vs DKM 416 mA per output is a QUESTION (potentially fatal); AMS1117 ceramic-cap stability QUESTION |
| 03 Patch SM | done | 1 silkscreen, 3 fw comment, 4 doc | 0 | header orientation clean (matches p15 and the KAD footprint); U1 silk letters A/B/C/D on the wrong headers |
| 04 digital IO | done | 2 doc | 1 | GPA7/GPB7 BLOCKED (3 inputs); ENC0 contact current under ALPS minimum; U4 has no local decoupling; buttons and encoders otherwise clean |
| 05 BBD | done | 1 (X7R where film specified), 1 doc | 1 | all 36 manual nets match channel 1; ch2 = ch1 exactly; CD4046 drive vs MN3205 clock spec is an inherited QUESTION |
| 06 LPG | done | 1 (vactrol LED reverse voltage), 1 doc | 0 | every node matches Bergman; 4xx = 3xx; ADR 0011 headroom quoted against the wrong limit |
| 07 audio IO | done | 1 naming | 0 | pots clean against the Alpha drawing; PJ-603 contacts settled by its own drawing; U9 thermal at 16 ohm full trim is a low QUESTION |
| 08 footprints | done | 2 land pattern (low), 3 doc | 3 | all 370 footprints match their libraries and every back-side part is a true flip; 24/24 panel parts on their holes; Patch SM seated height under the MSP430 BLOCKED (must stay under 7.9 mm) |
| 09 interconnect | done | 1 doc | 0 | pin n meets pin n (computed from both boards: same orientation, key on the same wall); TX into RX both ways; RST one driver, TEST undriven; power-down back-feed on MSP430_RXD is a QUESTION |
| 10 faceplate MCU | done | 6 doc (5 fw-touch, 1 Q22) | 1 | every U1 pin matches Figure 7-1 and Table 7-2; each pad spans all four CapTIvate blocks; crystal load and drive clean; only own-pad copper under each pad; TVS 12 pF against sensitivity is a QUESTION |
| 11 board level | | | | |
| 12 synthesis | | | | |
