# The origin: a hand-made 3-bit calculator

This is the KiCad project the whole thing started from, exactly as it was on
2026-08-17. Nothing in this directory is edited, ever.

Built by hand, from scratch, while relearning electronics: a keypad encoder, a
3-bit sign-magnitude adder/subtractor built from 2N3904 RTL gates, a result
register, a 4-to-16 decoder for a display, and a reference NOR/NAND pair.
419 transistors, 1,087 resistors. Simulated in KiCad's ngspice integration.

It has bugs. They are listed in `docs/KNOWN-ISSUES.md` and are fixed by the
redesign in `boards/01-alu`, not here.

The SPICE model path inside the schematic points at the Desktop location the
original used; the model is in `lib/2N3904.lib`. The PCB has 747 of about 1,500
footprints placed and no tracks: routing is where the original run stopped.
