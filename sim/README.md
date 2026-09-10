# sim: generators and testbenches

| File | What |
|---|---|
| `nmos.py` | The cell family: INV/NAND/NOR/BUS/LED cells, XOR and D flip-flop macros, fan-out, floating-input and node-name checks, SPICE emitter |
| `ksch.py`, `frame.py`, `knet.py` | KiCad 10 schematic writer (gate lists as cells, header, decoupling, indicators, testbench sources), the common board frame, netlist parser |
| `bus.py` | The 64-pin header pinout (docs/bus-header.md) |
| `alu.py`, `build_alu.py`, `tb_alu.py` | Board 01: logic, generator for `boards/01-alu/`, testbench (demo or exhaustive cases, TYP/LO/HI/MIX corners, dev netlist or kicad-cli export) |
| `registers.py`, `build_registers.py`, `tb_registers.py` | Board 02: logic, generator, testbench (a clocked script through every register path) |
| `panel.py`, `build_panel.py` | Board 06: switches, buttons, LEDs, input port |
| `build_hub.py`, `coupon.py`, `build_coupon.py` | Board 07 (hub) and the gate coupon |
| `plots_alu.py` | Transient plots from a testbench run |
| `emu.py` | Tick-accurate ISA emulator; the reference for the whole-machine simulation |
| `asm.py` | Assembler; `programs/*.asm` are the reference programs, `test_emu.py` runs them on the emulator |
| `machine.py` | The whole-machine deck: every existing board's export plus emulator stand-ins for the rest, one program, compared tick for tick |
| `gate.py` | The machine gate: every program, every corner, one summary table (`out/gate_<boards>.md`) |
| `pcb.py` | Placement, power rails, freerouting, DRC, fab outputs (run with KiCad's python) |
| `bom.py` | Sums the fab BOMs of every routed board into one parts table (`--per` for a column per board); `docs/order-1.md` quotes it |
| `spicedat.py` | Fast reader for ngspice `wrdata` files |
| `out/` | Scratch (ignored by git). `out/cell.cir` characterises one cell |

Needs ngspice (`brew install ngspice`), numpy, matplotlib, and KiCad 10 for
`kicad-cli` and the shared symbol libraries.

Rules that the generator enforces are in `docs/gate-cell.md`. ngspice node
names are case-insensitive, so never create two nets that differ only by case.

## PCB flow

`pcb.py` (run with KiCad's bundled python, see the docstring) takes a project's
schematic and its `<name>.plan.json` (placements, silkscreen labels, power
rails; written by the `build_*.py` generators) and produces the `.kicad_pcb`:
footprints placed, power pre-routed, signals routed by freerouting (headless,
retried until DRC reports zero unconnected), a ground pour on the back, DRC, and
`fab/` outputs (gerbers, drill, BOM, position file, renders).

    <kicad>/python3 pcb.py ../boards/01-alu alu

Gerbers are regenerated, not committed; the renders and BOM are.

## Whole-machine simulation

    python3 machine.py programs/fib.asm --boards alu,hub,reg,panel [--corner MIX --seed 2] [--ticks 40]
    python3 gate.py --boards alu,hub,reg,panel -j 4          # all programs, all corners

A board named `x@dev` is taken from its gate list instead of the schematic
export, for trying a design before drawing it. The deck runs the clock at
1 ms per tick; a 130-tick program with three boards takes two to three
minutes per corner. Registers that have no reset (A, B, OUT) are compared only
from the tick after the program first writes them.

Things ngspice taught us, so nobody learns them twice: `pwl()` in a B-source
extrapolates outside its points; a B-source with a `?:` step inside it fails
with "timestep too small" sooner or later, use the `SW` switch model for an
ideal driver; a net named `PWL` cannot be probed.
