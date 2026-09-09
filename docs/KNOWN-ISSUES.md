# Known issues

Tracked as GitHub issues; this file is the index so it survives without GitHub.

## Origin calculator (`boards/00-origin-calculator/`)

These are in the hand-made design and are left there on purpose. They are
fixed by the two's-complement redesign of board one (D006), not by editing the origin.

| # | Issue | Symptom | Cause |
|---|---|---|---|
| 1 | Converter XOR keyed on SUB instead of the result sign | 7 - 5 stores 13; every subtraction with A >= B is wrong | The sign-magnitude converter inverts the sum whenever SUB is set, not when the result is negative |
| 2 | Adder carry-out leaks into result bit 3 in subtract mode | 6 - 6 stores 8 | Carry-out of the 3-bit adder feeds bit 3 of the register unmasked |
| 3 | Memory bits OUT_B0/OUT_B1 sit at 1.2 V high | Marginal decode; one bad transistor away from a wrong digit | Each drives 13 decoder inputs through a 4.7k pull-up; RTL fan-out is about 3 |
| 4 | Simulation clock is a 100 ns pulse | The sim stimulus is far faster than the gates can switch | Value chosen before gate delay was understood |

The fixed versions of 1 and 2 (and a 2.2k pull-up for 3) exist in
`experiments/muldiv/Untitled.kicad_sch`, which is the origin sheet as modified
during the multiply/divide experiment.
