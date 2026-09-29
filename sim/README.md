# sim: generators and testbenches

| File | What |
|---|---|
| `nmos.py` | The cell family: INV/NAND/NOR/BUS/LED cells, XOR and D flip-flop macros, fan-out, floating-input and node-name checks, SPICE emitter |
| `ksch.py`, `frame.py`, `knet.py` | KiCad 10 schematic writer (gate lists as cells, header, decoupling, indicators, testbench sources), the common board frame, netlist parser |
| `bus.py` | The 64-pin header pinout (docs/bus-header.md) |
| `alu.py`, `build_alu.py`, `tb_alu.py` | Board 01: logic, generator for `boards/01-alu/`, testbench (demo or exhaustive cases, TYP/LO/HI/MIX corners, dev netlist or kicad-cli export) |
| `registers.py`, `build_registers.py`, `tb_registers.py` | Board 02: logic, generator, testbench (a clocked script through every register path; `cards` runs it on the four bit cards) |
| `build_reg_card.py` | Register bit cards `cards/reg<i>/` (docs/cards.md) from `registers.build_bit`, on the dense tile (`ksch.DenseWriter`) in the 100 x 100 card frame (`frame.card_frame`) |
| `panel.py`, `build_panel.py` | Board 06: switches, buttons, LEDs, input port |
| `build_hub.py`, `coupon.py`, `build_coupon.py` | Board 07 (hub) and the gate coupon (`build_coupon_card.py`, `tb_coupon.py`: the coupon card and its expected readings, D056) |
| `plots_alu.py` | Transient plots from a testbench run |
| `emu.py` | Tick-accurate ISA emulator; the reference for the whole-machine simulation |
| `asm.py` | Assembler; `programs/*.asm` are the reference programs, `test_emu.py` runs them on the emulator |
| `machine.py` | The whole-machine deck: every existing board's export plus emulator stand-ins for the rest, one program, compared tick for tick |
| `gate.py` | The machine gate: every program, every corner, one summary table (`out/gate_<boards>.md`) |
| `pcb.py` | Placement, power rails, freerouting, DRC, fab outputs (run with KiCad's python) |
| `bom.py` | Sums the fab BOMs of every routed board into one parts table (`--per` for a column per board); `docs/order-1.md` quotes it |
| `sweep_por.py` | The reset-release sweep: fib for 12 ticks on the whole card deck with the clock card's power-on reset released at 13 phases against the clock (`POR_V0`, `RESET_S` in `machine.py`), TYP and MIX seeds 1, 2; writes `out/sweep_por.md` |
| `assembly.py` | The assembly drawing, `cards/<card>/fab/<card>-assembly.svg`: the front as the silk shows it, every part that is not the card's commonest resistor or a 2N7000 coloured and labelled with its value (the cards print none); written by `pcb.py` with the fab outputs (plain python3) |
| `order_check.py` | The order gate on a card's committed files: clean tree, routed rules in the project file, ERC, DRC with parity, JLCPCB minimums (`jlcpcb.kicad_dru`), fab files and zip equal the board, 100 x 100 outline and holes, every part's pads and polarity, the assembly drawing is the board's, no copper of another net where a socket's nut or a standoff clamps; `docs/order-1.md` section 5 (plain python3) |
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

The `fab/` outputs (gerbers, drill, BOM, position file, renders) are committed with the board, as built.

## Whole-machine simulation

    python3 machine.py programs/fib.asm --boards alu,hub,reg,panel [--corner MIX --seed 2] [--ticks 40]
    python3 gate.py --boards alu,hub,reg,panel -j 2          # all programs, all corners (two decks at a time on a 36 GB machine)
    python3 gate.py --boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl --corners TYP -j 2     # the machine as cards
    python3 gate.py --boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc --corners TYP -j 2 --ticks 12     # the smoke gate: first twelve ticks of every program, about three hours; run it before every long queue and after every harness change
    python3 gate.py --boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc --corners LO,HI,MIX --seeds 1,2 -j 2 --resume out/ledger.jsonl     # a long gate keeps a ledger of finished runs: cut short, the same line picks up at the first run without a passing row

Board names: the nine boards (`alu`, `hub`, `reg`, `seq`, `ctr`, `mem`,
`prog`, `panel`, `clk`) and the cards (`reg0..3` or the group `regc`,
`alu0..3` / `aluc`, `ctr0..7` / `ctrc`, `memctl` + `memslot` / `memc`
(eight slot copies with their jumpers), `progc` (one program card per
four words, jumpered and switched from the program), `panela..c` / `pnl`,
`clkc`, `hubc`). A board named `x@dev` is taken from its gate list instead
of the schematic export, for trying a design before drawing it. The deck runs the clock at
1 ms per tick; a 130-tick program with three boards takes two to three
minutes per corner. Registers that have no reset (A, B, OUT) are compared only
from the tick after the program first writes them.

Things ngspice taught us, so nobody learns them twice: `pwl()` in a B-source
extrapolates outside its points; a B-source with a `?:` step inside it fails
with "timestep too small" sooner or later, use the `SW` switch model for an
ideal driver; a net named `PWL` cannot be probed.
