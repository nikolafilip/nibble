# Build plan and end-to-end verification

Written 2026-09-10 after the design v2 decisions (D017 to D026). This is the
order of work and the tests that gate each step, so nothing is fabricated that
has not been shown to work in simulation, first alone, then as a whole machine.

## The rule

Every board passes three gates before its gerbers are trusted:

1. **Schematic gate.** ERC clean. The kicad-cli SPICE export of the exact
   committed schematic is simulated exhaustively, or over every reachable
   state, at all three 2N7000 threshold corners (0.8 V, 2.0 V, 3.0 V).
2. **Board gate.** PCB routed by `sim/pcb.py`, DRC zero errors, zero
   unconnected. The netlist of the routed PCB matches the schematic export.
3. **Machine gate.** The board's netlist is dropped into the whole-machine
   simulation and the reference programs still run correctly.

## The whole-machine simulation

`sim/machine.py` (to be written) assembles one SPICE deck from the exported
netlists of every board plus the hub (supply, bus pull-ups, M pull-downs) and a
model of the switch program memory holding a program. The clock is a pulse
source. The deck is run with ngspice and the OUT register, the flags and the
program counter are sampled at every clock edge.

The expected values come from `sim/emu.py`, a tick-accurate Python emulator
of the instruction set, running the same program (`sim/test_emu.py` checks
every program's `; expect:` line on the emulator alone). The test passes when the ngspice
trace and the emulator trace are identical, tick for tick.

Reference programs, in `sim/programs/`, assembled by `sim/asm.py`:

- `fib.asm`: Fibonacci to 8, halts on carry. Exercises LDI, MOV, XCH, ADD, OUT, JC, JMP, HLT and the two-word jump.
- `count.asm`: count 0..15, wrap on carry, count back down with SUB and JZ.
- `alu.asm`: every ADD/SUB result and flag pattern reachable from a short program.
- `mul.asm`: 8-bit product of two nibbles using LOAD/STORE, DEC, INC and the carry flag.
- `list.asm`: maximum of four numbers in data memory, walked with B as the pointer (LOAD [B]).
- `calc.asm`: two numbers typed on the switches (IN), multiplied by a subroutine (CALL/RET), product shown as two nibbles.
- `sort.asm`: four numbers from the switches sorted in memory with STORE [B] and shown in order.
- `lfsr.asm`: a pseudo-random sequence from a 4-bit shift register, using AND, OR, XOR.
- `gcd.asm`: Euclid's algorithm on two numbers from the switches.

Boards that do not exist yet are absent from the deck; the front panel model
drives their lines to 0. As each board is designed, it is added and the
programs that need it are enabled.

Speed: the ALU settles in 89 us worst case; the machine deck runs its clock at
1 ms per tick. Measured: about 10 s of ngspice per tick with 1,600 transistors
in the deck, so the nine programs (4,400 ticks) are half a day per corner.
`sim/gate.py` runs them as a batch, four corners in parallel; during design,
`--ticks` runs the first part of a program in minutes.

## Order of work

| Step | What | Gate | Notes |
|---|---|---|---|
| 1 | Regenerate ALU, panel, hub, coupon with the 64-pin header (D017) and the D031 lines | schematic + board gates | hub gains M pull-downs (D021); panel gains the control switches and LEDs for every line and the input port (IN); ALU gains ONE, F0, F1 |
| 2 | `emu.py`, `asm.py`, reference programs | emulator runs all programs with the expected output | pure Python, no hardware |
| 3 | Register board (A, B, OUT, with BO, BA, AB) | all three gates: the ALU and registers run `fib.asm` with the emulator playing the sequencer | about 370 transistors |
| 4 | Sequencer board (IR, 8-bit operand register, 5-state counter, two decoders, diode matrix, flags) and the counter board (8-bit PC, return register) joined by a link cable (D035) | all three gates: every program that needs no memory passes on the machine deck | 524 + 416 transistors; the diode matrix is diodes, not transistors |
| 5 | Data memory board (16 x 4, address register, MAI, MI, MO) | machine gate: `mul.asm`, `list.asm`, `sort.asm`, `lfsr.asm`, `calc.asm` | 746 transistors, one LED per cell |
| 6 | Program memory board (16 words, page jumpers, diode-OR outputs) | machine gate with the program held in the switch model replaced by the real board netlist | zero transistors plus page compare |
| 7 | Clock board (Schmitt RC oscillator, RUN/STEP, power-on reset, halt) | machine gate with the real clock instead of the pulse source, on programs that take no input (the switch stimulus is timed to the pulse clock) | 16 transistors |
| 8 | Fab: every board in one order | Nikola's review: renders, bring-up doc, order doc | one order (D032); the coupon is on the same order, so the corner and mixed-threshold simulations are what stands in for its measurements |
| 9 | Bring-up per `bring-up.md`, one board at a time on the panel; measured gate delay replaces the simulated one in every testbench | physical | first program runs on hardware |

Every board passes the machine gate before the order is placed, so the header,
the control lines and the instruction set are proven as a whole before any
copper exists.

## What "won't work" looks like, and where it is caught

| Failure | Caught by |
|---|---|
| A gate cell that is too slow or has bad margins in copper | the three threshold corners and the mixed-threshold runs of every board; then coupon measurements at bring-up |
| A latch that only works when all transistors match | corner MIX of the machine deck: every transistor gets a random threshold model (D033) |
| A wiring mistake on a board | schematic gate (exhaustive sim of the export) |
| A routing mistake | board gate (DRC + netlist compare) |
| Two boards disagreeing about a control line's meaning or timing | machine gate |
| An instruction recipe that is wrong | machine gate against the emulator, per program |
| A header pin assignment that a later board needs changed | D017 reserved them; the machine deck uses the same pin table as every board |
