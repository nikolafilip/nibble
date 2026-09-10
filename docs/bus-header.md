# Bus header (v2, 64 pins)

One 2x32 (64-pin) box header per board, 2.54 mm pitch, connected to the hub
board with a 64-way IDC ribbon cable. Pin 1 is marked on every board. Clock and
reset each sit next to a ground pin.

All lines are 0 V / 5 V. Everything is active-high except the four `BUS#`
lines, which are open-drain and active-low (pulled up to 5 V on the hub; a
board pulls low to assert a 1), and the eight `M` lines, which are diode-OR
outputs of the program memory boards (pulled down on the hub; a selected memory
board pulls high). A board that does not use a line leaves it unconnected.
Inputs on a board are MOSFET gates and must never float: every input a board
uses is either driven from the header or tied to a rail on the board.

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
| 25 | PC4 | 26 | PC5 |
| 27 | PC6 | 28 | PC7 |
| 29 | M0 | 30 | M1 |
| 31 | M2 | 32 | M3 |
| 33 | M4 | 34 | M5 |
| 35 | M6 | 36 | M7 |
| 37 | CF | 38 | ZF |
| 39 | SUB | 40 | EO |
| 41 | AI | 42 | AO |
| 43 | BI | 44 | BO |
| 45 | BA | 46 | AB |
| 47 | OI | 48 | IO |
| 49 | II | 50 | PCE |
| 51 | PCL | 52 | FI |
| 53 | HLT | 54 | MAI |
| 55 | MI | 56 | MO |
| 57 | PWL | 58 | PWH |
| 59 | SP0 | 60 | SP1 |
| 61 | SP2 | 62 | SP3 |
| 63 | +5V | 64 | GND |

| Signal | Direction | Meaning |
|---|---|---|
| CLK | clock board -> all | Rising edge is the active edge for every register |
| RST | clock board -> all | High clears PC, IR, flags and the step counter |
| BUS0#..3# | shared | Data bus, active-low, open-drain |
| A0..3, B0..3 | registers -> ALU, panel | Register contents, plain logic levels |
| PC0..7 | sequencer -> memory, panel | Program counter. PC0..3 select the row on a program memory board, PC4..7 select which board (page) |
| M0..7 | program memory -> sequencer | The selected instruction word (M7..4 opcode, M3..0 operand). Diode-OR across memory boards |
| CF, ZF | ALU -> sequencer, panel | Carry and zero, combinational from the ALU; latched on the sequencer when `FI` is high |
| SUB | sequencer -> ALU | 1 = subtract |
| EO | sequencer -> ALU | ALU drives its result onto the bus |
| AI, BI, OI | sequencer -> registers | Register loads from the bus on the next clock edge |
| AO, BO | sequencer -> registers | A / B drives the bus |
| BA, AB | sequencer -> registers | B loads from A / A loads from B directly (both = XCH) |
| IO | sequencer (internal) | Low 4 bits of the operand register drive the bus |
| II | sequencer (internal) | Instruction register loads from M0..7 |
| PCE, PCL | sequencer (internal) | Counter enable / load from the 8-bit operand register (jump) |
| FI | sequencer (internal) | Flags latch |
| HLT | sequencer -> clock | Stops the clock |
| MAI | sequencer -> data memory | Data memory address register loads from the bus |
| MI, MO | sequencer -> data memory | Data memory writes the bus into / drives the bus from the addressed slot |
| PWL, PWH | panel -> writable program memory | Write the bus into the low / high nibble of the word at the PC address |
| SP0..3 | spare | Unassigned |

Lines marked internal still cross the header so the front panel can drive
them by hand while the sequencer board does not exist yet. MAI, MI, MO, PWL,
PWH and BO are reserved for boards that do not exist yet (see `plan.md`).
