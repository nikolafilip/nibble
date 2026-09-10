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
| `docs/` | Architecture, instruction set, bus header, gate cell, build plan, decision ledger, known issues |
| `boards/00-origin-calculator/` | The hand-made 3-bit add/subtract calculator this started from, untouched |
| `boards/01-alu/` | 4-bit ALU: add, subtract, and, or, xor, increment, decrement, with flags |
| `boards/02-registers/` | A, B and OUT registers |
| `boards/03-sequencer/` | Step counter, instruction and operand registers, flags, decoders and the diode control matrix |
| `boards/04-program/` | Program memory: 16 words on DIP switches, one page of 256; build more for longer programs |
| `boards/05-clock/` | Clock with a speed knob, RUN/STEP, halt and power-on reset |
| `boards/06-panel/` | Front panel: switches for every line, LEDs on every line, the input port |
| `boards/07-hub/` | Bus hub: power, pull-ups, eight slots |
| `boards/08-memory/` | Data memory: 16 slots of 4 bits, every cell with an LED |
| `boards/09-counter/` | 8-bit program counter and return register |
| `coupon/` | Gate-cell test board: measure the real cell before trusting anything |
| `lib/` | Shared SPICE models and KiCad libraries |
| `sim/` | Generators, testbenches, the emulator and the whole-machine simulation |
| `experiments/muldiv/` | A multiplier/divider designed on the original RTL calculator. Simulated, not built |

## Start here

1. `docs/architecture.md` — what the machine is and how the boards fit together.
2. `docs/isa.md` — the instruction set (31 instructions in 16 opcodes) and a worked program.
3. `docs/bus-header.md` — the 64-pin ribbon header every board shares.
4. `docs/gate-cell.md` — the one logic cell everything is made of.
5. `docs/plan.md` — the gates every board passes before copper exists, and the whole-machine simulation.
6. `docs/DECISIONS.md` — why things are the way they are, in order.

## Status

See `docs/DECISIONS.md` for the latest entry and `docs/KNOWN-ISSUES.md` for what is wrong.

## Licence

CERN-OHL-P-2.0 for the hardware, MIT-equivalent terms for the scripts. See `LICENSE`.
