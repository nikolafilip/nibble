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
