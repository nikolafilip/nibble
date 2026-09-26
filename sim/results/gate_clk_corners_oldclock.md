# Machine gate: boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc, the FIRST clock and memctl cards (before D053/D054)
Survey run 2026-09-22/23 by sim/gate.py, killed once the cause was found; `sim/out/gate_clk_corners_oldclock.log`. Corners: LO, HI, MIX seeds [1, 2]. "From the ledger" rows were run earlier in the same gate.

| program | corner | result |
|---|---|---|
| fib.asm | LO | pass: 127 ticks, 0 mismatches |
| fib.asm | HI | pass: 127 ticks, 0 mismatches |
| fib.asm | MIX1 | pass: 127 ticks, 0 mismatches |
| fib.asm | MIX2 | pass: 127 ticks, 0 mismatches (ladder rung 2) |
| alu.asm | LO | pass: 75 ticks, 0 mismatches (ladder rung 2) |
| alu.asm | HI | pass: 75 ticks, 0 mismatches |
| alu.asm | MIX1 | pass: 75 ticks, 0 mismatches |
| alu.asm | MIX2 | pass: 75 ticks, 0 mismatches |
| gcd.asm | LO | pass: 160 ticks, 0 mismatches |
| gcd.asm | HI | pass: 160 ticks, 0 mismatches (ladder rung 2) |
| gcd.asm | MIX1 | pass: 160 ticks, 0 mismatches |
| gcd.asm | MIX2 | **FAIL: 160 ticks, 886 mismatches** (a store landed in the wrong slot, D054) |
| list.asm | LO | pass: 210 ticks, 0 mismatches |
| list.asm | HI | pass: 210 ticks, 0 mismatches |
| list.asm | MIX1 | pass: 210 ticks, 0 mismatches |
| list.asm | MIX2 | **FAIL: 210 ticks, 652 mismatches** (same) |
| logic.asm | LO | pass: 986 ticks, 0 mismatches |
| logic.asm | HI | pass: 986 ticks, 0 mismatches |
| logic.asm | MIX2 | **FAIL: 986 ticks, 7850 mismatches** (same) |
| call.asm | LO | pass: 84 ticks, 0 mismatches |
| call.asm | HI | pass: 84 ticks, 0 mismatches |

logic MIX1 and call MIX1/MIX2 were never run on the first cards. The three failures are the address-latch race: the memory card's latch opened on PH1 while the sequencer, reading the 35 us clock edge with its own transistors, had already stepped and put the next word's data on the bus (D053 for the edge, D054 for the latch).
