# Nibble

A 4-bit computer built from individual transistors, in public.

No integrated circuits anywhere. Transistors, resistors, diodes, capacitors,
LEDs, switches, connectors and wire. Every board is designed in KiCad,
simulated in ngspice, fabricated as a through-hole PCB and hand-soldered.

An AI (Claude) does the schematic generation, simulation and layout.
Nikola sets the constraints, reviews, orders, solders and measures.
The commit trailers say which is which.

## Layout

| Path | What |
|---|---|
| `docs/` | Architecture, instruction set, bus header, gate cell, decision ledger, known issues |
| `boards/00-origin-calculator/` | The hand-made 3-bit add/subtract calculator this started from, untouched |
| `boards/01-alu/` | Board one: 4-bit two's-complement adder/subtractor with flags |
| `coupon/` | Gate-cell test board: measure the real cell before trusting anything |
| `lib/` | Shared SPICE models and KiCad libraries |
| `sim/` | Generators, testbenches and simulation tooling |
| `experiments/muldiv/` | A multiplier/divider designed on the original RTL calculator. Simulated, not built |

## Start here

1. `docs/architecture.md` — what the machine is and how the boards fit together.
2. `docs/isa.md` — the ten instructions and a worked program.
3. `docs/bus-header.md` — the 50-pin ribbon header every board shares.
4. `docs/gate-cell.md` — the one logic cell everything is made of.
5. `docs/DECISIONS.md` — why things are the way they are, in order.

## Status

See `docs/DECISIONS.md` for the latest entry and `docs/KNOWN-ISSUES.md` for what is wrong.

## Licence

CERN-OHL-P-2.0 for the hardware, MIT-equivalent terms for the scripts. See `LICENSE`.
