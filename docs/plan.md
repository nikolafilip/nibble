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
- `mul.asm` (after the data memory board): 8-bit product of two nibbles using LOAD/STORE and the carry flag.
- `list.asm` (after the data memory board): maximum of four numbers held in data memory, compared with SUB and JC.

Boards that do not exist yet are absent from the deck; the front panel model
drives their lines to 0. As each board is designed, it is added and the
programs that need it are enabled.

Speed: the ALU settles in 73 us worst case; the machine deck runs its clock at
2 ms per tick, so a 60-tick program is a 120 ms transient. With about 1,300
transistors that is on the order of an hour of ngspice per corner. Acceptable,
run in the background, three corners in parallel.

## Order of work

| Step | What | Gate | Notes |
|---|---|---|---|
| 1 | Regenerate ALU, panel, hub, coupon with the 64-pin header (D017) | schematic + board gates | hub gains M pull-downs (D021); panel gains BO, MAI, MI, MO, PWL, PWH switches and LEDs |
| 2 | `emu.py`, `asm.py`, reference programs | emulator runs all programs with the expected output | pure Python, no hardware |
| 3 | Register board (A, B, OUT, with BO, BA, AB) | all three gates: panel + ALU + registers run every register transfer | about 300 transistors |
| 4 | Sequencer board (8-bit PC, IR, 8-bit operand register, 5-state counter, diode matrix, flags) | all three gates: `fib.asm`, `count.asm`, `alu.asm` pass on the machine deck | about 750 transistors; the diode matrix is diodes, not transistors |
| 5 | Program memory board (16 words, page jumpers, diode-OR outputs) | machine gate with the program held in the switch model replaced by the real board netlist | zero transistors plus page compare |
| 6 | Clock board (astable, single-step, reset, halt) | machine gate with the real clock instead of the pulse source | about 20 transistors |
| 7 | Fab order 1: coupon, hub, panel, ALU | Nikola's review: renders, bring-up doc, order-1 doc | boards 1 to 4 only; the later boards' netlists already pass the machine gate |
| 8 | Bring-up per `bring-up.md`; measured gate delay replaces the simulated one in every testbench | physical | |
| 9 | Fab order 2: registers, sequencer, program memory, clock | machine gate re-run with measured delays | first program runs on hardware |
| 10 | Data memory board (16 x 4, MAI, MI, MO); LOAD/STORE diodes | machine gate: `mul.asm`, `list.asm` | first board added to a working machine |

Steps 3 to 6 are designed before order 1 is placed, even though they ship in
order 2. That way the header, the control lines and the whole-machine test are
proven before any copper exists, and order 1 cannot be invalidated by a
discovery made while designing the sequencer.

## What "won't work" looks like, and where it is caught

| Failure | Caught by |
|---|---|
| A gate cell that is too slow or has bad margins in copper | coupon measurements, step 8; every testbench then re-runs with measured numbers |
| A wiring mistake on a board | schematic gate (exhaustive sim of the export) |
| A routing mistake | board gate (DRC + netlist compare) |
| Two boards disagreeing about a control line's meaning or timing | machine gate |
| An instruction recipe that is wrong | machine gate against the emulator, per program |
| A header pin assignment that a later board needs changed | D017 reserved them; the machine deck uses the same pin table as every board |
