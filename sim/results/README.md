# Gate results kept on purpose

`sim/out/` is scratch and ignored by git; the tables that close a step of
`docs/cards.md` are copied here, unedited, from `out/gate_<boards>.md` as
`sim/gate.py` wrote them (the queue script copies each stage's table to
`out/<stage>.md`).

| File | What |
|---|---|
| `gate25_smoke_t12.md` | Step 9 smoke, 2026-09-23: the first 12 ticks of all thirteen programs at TYP on the whole card deck with the D053 clock card and the D054 memory control card, power-up start (`.tran ... uic`) |
| `gate25_TYP.md` | Step 9, 2026-09-23/24: all thirteen programs to their halt at TYP, same deck |
| `gate25_corners.md` | Step 9, 2026-09-24/26: fib, alu, gcd, list, logic, call at LO, HI, MIX seed 1 and MIX seed 2, same deck |
| `gate_clk_corners_oldclock.md` | The same corner gate on the cards before D053/D054, where gcd, list and logic failed at MIX seed 2 |
| `gate25_nop.md` | Added corners, 2026-09-26: nop at LO and HI, same deck |
| `gate25_500pF_HI.md` | Added corners, 2026-09-26: the six corner programs at HI with 500 pF on every bus line (`CABLE_PF=500`), same deck |
| `gate25_vdd45.md` | Added corners, 2026-09-26/27: the six corner programs at TYP and HI with the supply at 4.5 V (`VDD=4.5`), same deck |
| `gate25_cross.md` | Added corners, 2026-09-27: the six corner programs at TYP and HI with 100 pF between neighbouring bus lines (`CROSS_PF=100`), same deck |
| `gate25_vdd425.md` | Added corners, 2026-09-27: fib, logic and call at HI with the supply at 4.25 V (`VDD=4.25`), same deck. The first run of this stage failed fib on the scorer, not the machine: `machine.py` read CLK against a fixed 3.5 V and the card's CLK high is (VDD − a diode) × 10/11, 3.38 V at 4.25 V; every level in the scorer and the switch counter's bridges is a fraction of VDD since commit 1480db7, and the stage was rerun on the fixed scorer |
| `gate25_mix34.md` | Added corners, 2026-09-27/28: the six corner programs at MIX seeds 3 and 4, same deck |

The four stages before `gate25_vdd425.md` ran on the scorer before 1480db7.
At 5 V its fixed levels were the same fractions of VDD, so the tables stand.
At 4.5 V the switch counter's reset bridge (3.5/4.0 V, against a reset high
of 3.7 V) never read high, so the counter was not cleared by the card's reset
and started from its flip-flops' initial state, 0, the same state; the switch
sequence those runs saw is the one they were scored against.
