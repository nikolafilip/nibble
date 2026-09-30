# Machine gate 26, crosstalk: boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc, CROSS_PF=100, the hold-off in the deck (HOLD=1)
Generated 2026-09-30 07:00 by sim/gate.py. 100 pF between the lines that are neighbours on the ribbon with the header on the back (D062: RST beside BUS1#, BUS1# beside BUS0#, ...). The clock card carries the two parts of D064 as HOLD=1 puts them into the deck; the deck of the card with the parts on it is the same, element for element (machine.py, mix_order.json). Corners: TYP, HI; MIX seeds [1].

| program | corner | result | time |
|---|---|---|---|
| fib.asm | TYP | pass: 127 ticks, 0 mismatches | 2619 s |
| fib.asm | HI | pass: 127 ticks, 0 mismatches | 3022 s |
| alu.asm | TYP | pass: 75 ticks, 0 mismatches | 2006 s |
| alu.asm | HI | pass: 75 ticks, 0 mismatches | 2414 s |
| gcd.asm | TYP | pass: 160 ticks, 0 mismatches | 5433 s |
| gcd.asm | HI | pass: 160 ticks, 0 mismatches | 6015 s |
| list.asm | TYP | pass: 210 ticks, 0 mismatches | 4676 s |
| list.asm | HI | pass: 210 ticks, 0 mismatches | 5123 s |
| logic.asm | TYP | pass: 986 ticks, 0 mismatches | 20022 s |
| logic.asm | HI | pass: 986 ticks, 0 mismatches | 20831 s |
| call.asm | TYP | pass: 84 ticks, 0 mismatches | 2089 s |
| call.asm | HI | pass: 84 ticks, 0 mismatches | 2292 s |
