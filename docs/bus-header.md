# Bus header

One 2x25 (50-pin) box header per board, 2.54 mm pitch, connected to the hub
board with a 50-way IDC ribbon cable. Pin 1 is marked on every board. Clock and
reset each sit next to a ground pin.

All lines are 0 V / 5 V. Everything is active-high except the four `BUS#`
lines, which are open-drain and active-low (pulled up to 5 V on the hub; a
board pulls low to assert a 1). A board that does not use a line leaves it
unconnected. Inputs on a board are MOSFET gates and must never float: every
input a board uses is either driven from the header or tied to a rail on the board.

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | +5V | 2 | +5V |
| 3 | GND | 4 | GND |
| 5 | CLK | 6 | GND |
| 7 | RST | 8 | GND |
| 9 | BUS0# | 10 | BUS1# |
| 11 | BUS2# | 12 | BUS3# |
| 13 | A0 | 14 | A1 |
| 15 | A2 | 16 | A3 |
| 17 | B0 | 18 | B1 |
| 19 | B2 | 20 | B3 |
| 21 | PC0 | 22 | PC1 |
| 23 | PC2 | 24 | PC3 |
| 25 | M0 | 26 | M1 |
| 27 | M2 | 28 | M3 |
| 29 | M4 | 30 | M5 |
| 31 | M6 | 32 | M7 |
| 33 | CF | 34 | ZF |
| 35 | SUB | 36 | EO |
| 37 | AI | 38 | AO |
| 39 | BI | 40 | BA |
| 41 | AB | 42 | OI |
| 43 | IO | 44 | II |
| 45 | PCE | 46 | PCL |
| 47 | FI | 48 | HLT |
| 49 | +5V | 50 | GND |

| Signal | Direction | Meaning |
|---|---|---|
| CLK | clock board -> all | Rising edge is the active edge for every register |
| RST | clock board -> all | High clears PC, IR, flags and the step counter |
| BUS0#..3# | shared | Data bus, active-low, open-drain |
| A0..3, B0..3 | registers -> ALU, panel | Register contents, plain logic levels |
| PC0..3 | sequencer -> memory, panel | Program counter, selects the memory row |
| M0..7 | memory -> sequencer | The selected instruction word (M7..4 opcode, M3..0 operand) |
| CF, ZF | ALU -> sequencer, panel | Carry and zero, combinational from the ALU; latched on the sequencer when `FI` is high |
| SUB | sequencer -> ALU | 1 = subtract |
| EO | sequencer -> ALU | ALU drives its result onto the bus |
| AI, BI, OI | sequencer -> registers | Register loads from the bus on the next clock edge |
| AO | sequencer -> registers | A drives the bus |
| BA, AB | sequencer -> registers | B loads from A / A loads from B directly (both = XCH) |
| IO | sequencer (internal) | IR operand drives the bus |
| II | sequencer (internal) | IR loads from M0..7 |
| PCE, PCL | sequencer (internal) | Counter enable / load from bus |
| FI | sequencer (internal) | Flags latch |
| HLT | sequencer -> clock | Stops the clock |

Lines marked internal still cross the header so the front panel can drive
them by hand while the sequencer board does not exist yet.
