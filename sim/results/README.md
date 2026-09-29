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
| `coupon_expected.md` | The coupon card, 2026-09-28 (D056): what the bench should read at each test loop, from `tb_coupon.py kicad --all` on the routed card's export at TYP, LO, HI and MIX seeds 1..3 (written by the testbench, not by `gate.py`) |
| `sweep_por.md` | The reset-release sweep, 2026-09-28/29 (`sweep_por.py`): fib for 12 ticks on the whole card deck with the clock card's power-on reset released at 13 places against the clock edge, 10 us apart, at TYP and MIX seeds 1 and 2. 37 of 39 pass. The two that fail are the mixed corners with the clock edge 9 and 10 us after the release; the runs on either side of them, at 0 and 20 us, pass. Scored again from the saved data: at MIX1 the first opcode is not latched and the first instruction runs as another one; at MIX2 the step ring starts with two steps active and never recovers. At TYP every card lets go at the same voltage and nothing fails. MIX2 released 3.8 ms after power-on, a period and a half of its clock, not the 20 ms asked for: that corner is run again with a later release |
| `rst_neighbour.md` | The reset line beside BUS1#, 2026-09-28 (D062): with the bus header on the back RST has one ground neighbour on the ribbon, not two; the bump it picks up when BUS1# is released, with every gate the routed boards hang on the two lines, against the coupling and a capacitor at the hub (written by `tb_rst_neighbour.py`) |
| `crowbar.md` | The hub's crowbar and reverse diode, 2026-09-28 (D061): the models against their datasheets, which zener and gate resistor, and the rail in every way the voltage can arrive (turned up, switched on at 30 V, plugged in live, leads crossed), with the heat in the SCR (written by `tb_crowbar.py`). The parts are not on the hub yet |

The four stages before `gate25_vdd425.md` ran on the scorer before 1480db7.
At 5 V its fixed levels were the same fractions of VDD, so the tables stand.
At 4.5 V the switch counter's reset bridge (3.5/4.0 V, against a reset high
of 3.7 V) never read high, so the counter was not cleared by the card's reset
and started from its flip-flops' initial state, 0, the same state; the switch
sequence those runs saw is the one they were scored against.
