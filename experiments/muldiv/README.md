# Experiment: multiply and divide on the RTL calculator

Done on 2026-09-09 as a test of AI schematic-level design, before the CPU
direction was chosen. Not built, and not on the roadmap.

The origin sheet was extended with `muldiv.kicad_sch` (a 6-bit work register,
a five-state sequencer, shift-add multiply and restoring divide reusing the
origin's adder; 480 extra 2N3904s) and `testbench.kicad_sch` (clock, keypad and
op-code stimuli). The root sheet here is the origin sheet with the encoder
inverters moved, the register inputs muxed, and the two origin bugs fixed.

Proof: `sim_results/` holds the kicad-cli exported netlist, a 16-operation
transient test and an exhaustive 256-case sweep (all pass), the plots, and a
report. `tools/` regenerates everything from `logic.py`; read `tools/README.md`.
