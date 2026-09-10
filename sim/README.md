# sim: generators and testbenches

| File | What |
|---|---|
| `nmos.py` | The cell family: INV/NAND/NOR/BUS/LED cells, XOR and D flip-flop macros, fan-out and floating-input checks, SPICE emitter |
| `ksch.py` | KiCad 10 schematic writer: draws a gate list as cells, plus header, decoupling, indicators, testbench sources |
| `bus.py` | The 64-pin header pinout (docs/bus-header.md) |
| `alu.py` | Board 01 logic. `build_alu.py` turns it into `boards/01-alu/` |
| `tb_alu.py` | Board 01 testbench: demo or exhaustive cases, any threshold corner, on the dev netlist or a kicad-cli export |
| `plots_alu.py` | Transient plots from a testbench run |
| `emu.py` | Tick-accurate ISA emulator; the reference for the whole-machine simulation |
| `asm.py` | Assembler; `programs/*.asm` are the reference programs, `test_emu.py` runs them |
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
