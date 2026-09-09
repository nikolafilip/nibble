# sim: generators and testbenches

| File | What |
|---|---|
| `nmos.py` | The cell family: INV/NAND/NOR/BUS/LED cells, XOR and D flip-flop macros, fan-out and floating-input checks, SPICE emitter |
| `ksch.py` | KiCad 10 schematic writer: draws a gate list as cells, plus header, decoupling, indicators, testbench sources |
| `bus.py` | The 50-pin header pinout |
| `alu.py` | Board 01 logic. `build_alu.py` turns it into `boards/01-alu/` |
| `tb_alu.py` | Board 01 testbench: demo or exhaustive cases, any threshold corner, on the dev netlist or a kicad-cli export |
| `plots_alu.py` | Transient plots from a testbench run |
| `out/` | Scratch (ignored by git). `out/cell.cir` characterises one cell |

Needs ngspice (`brew install ngspice`), numpy, matplotlib, and KiCad 10 for
`kicad-cli` and the shared symbol libraries.

Rules that the generator enforces are in `docs/gate-cell.md`. ngspice node
names are case-insensitive, so never create two nets that differ only by case.
