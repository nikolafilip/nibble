# Decision ledger

Append-only. One row per decision, newest at the bottom. `Story` says what it
changes for the public log (the X account brain lives in a separate repo and
reads this file). IDs never change; a reversed decision gets a new row.

| ID | Date | Decision | Why | Story |
|---|---|---|---|---|
| D001 | 2026-08-17 | Hand-build a 3-bit sign-magnitude add/subtract calculator in RTL (2N3904, 10k/22k/4.7k) as a learning exercise. | Relearning electronics from nothing. | The origin. Posted as-is, bugs and all. |
| D002 | 2026-09-09 | Extend the calculator with a sequential multiplier/divider, simulation only. | Test whether an AI can work at schematic level. | 480 extra transistors, 256/256 exhaustive pass. Not built. See `experiments/muldiv/`. |
| D003 | 2026-09-09 | The goal is a 4-bit CPU, built as separate boards, in public. Multiply/divide dropped from the roadmap. | 4-bit CPUs multiply in software; the experiment served its purpose. | "Nibble". |
| D004 | 2026-09-09 | Logic family: NMOS with 2N7000 and one pull-up resistor per gate. The 2N3904 RTL cell is retired. | MOSFET gates draw no current: fan-out limited only by speed, no base resistors, 20x less supply current, rail-to-rail levels. RTL was limited to 3 loads and sagged to 1.2 V on the memory bits. | The 419-transistor count restarts. "I threw away 419 bipolar transistors" is the post. |
| D005 | 2026-09-09 | Through-hole parts, hand-soldered, board size unconstrained. | Nikola wants to solder every joint. | Joint count is a recurring number. |
| D006 | 2026-09-09 | Number representation: 4-bit two's complement. The sign-magnitude converter is gone. | Subtraction becomes "invert B, add 1". Both known bugs of the origin lived in the converter. | Educational post: why computers use two's complement. |
| D007 | 2026-09-09 | Accumulator architecture: registers A, B, OUT, IR, PC; flags C and Z; ten instructions (see `isa.md`). Program memory is 16 words of 8 bits. | Smallest design that can loop and branch. Same shape as SAP-1, scaled to 4 bits. | The Fibonacci program is the first-program milestone. |
| D008 | 2026-09-09 | Program memory is a grid of DIP switches with one diode per bit. The CPU cannot write it. | Zero transistors instead of about 1,500 for flip-flop RAM. Reprogrammed by flipping switches. Filmable. | Altair-style front panel. |
| D009 | 2026-09-09 | Boards connect with 50-way ribbon cables to a bus hub board and sit in a rack, not stacked on headers. | A stack of pass-through headers gets wobbly past 4 boards; a rack looks better on camera. | The rack shot. |
| D010 | 2026-09-09 | Bus lines are open-drain, active-low, pulled up on the hub. | NMOS gives a shared bus for free; no tri-state logic needed. | One sentence on wired-OR buses. |
| D011 | 2026-09-09 | Fab order 1 = gate coupon + ALU board + front panel board. Nothing is ordered before the whole board passes an exhaustive ngspice sweep at both 2N7000 threshold corners. | The coupon measures the cell; the front panel tests every later board too. | Two cliffhangers: order and power-on. |
| D012 | 2026-09-09 | Decision ledger lives here. The X repo's own ledger points at IDs from this table. | One source of truth for engineering; the story repo reads, never rewrites. | |
