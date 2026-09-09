# Tooling used to build and verify the MUL/DIV extension

All new logic is described once, in `logic.py` (gate list in the schematic's RTL style),
and emitted twice from that description: as a SPICE netlist for fast iteration and as the
`muldiv.kicad_sch` sheet (`kigen.py`). `kiroot.py` applied the root-sheet edits **once**,
against the original `Untitled.kicad_sch`; do not run it again on the modified root.

Verification flow (this is what produced `../sim_results`):

    kicad-cli sch export netlist --format spice -o e2e.cir Untitled.kicad_sch
    python3 run_e2e.py e2e.cir out/        # simulate the exported netlist with ngspice, check every operation
    python3 plots.py out/                  # transient plots
    python3 run_exh.py MUL e2e_logic.cir x # exhaustive 8x8 sweep for one op (strip the V1xx sources and .tran/.ic first)

`tb.py` holds the stimulus sequence, expected values and the pass/fail decoder; `compare.py`
checks that the KiCad-exported netlist is gate-for-gate isomorphic to the development netlist.
Requires: ngspice (brew install ngspice), numpy, matplotlib; the 2N3904 model path is
`lib/2N3904.lib` at the repo root (the original project pointed at a Desktop path).
