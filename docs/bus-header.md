# Bus header (v2, 64 pins)

One 2x32 (64-pin) box header per board, 2.54 mm pitch, connected to the hub
board with a 64-way IDC ribbon cable. Clock and reset each sit next to a
ground pin.

**The header is soldered on the back of the board (D059, D062), with its
notch toward the top edge.** The ribbon runs behind the cards. The boards
print `HEADER ON THE BACK` on the front and the header's outline on the
back; on the front, `1`, `2`, `63` and `64` stand at the corners of the two
rows of solder joints, and the square pad is pin 1.

2x32 is the largest standard IDC size (2x34 and 2x40 are not stocked
anywhere). Checked 2026-09-10: shrouded headers (XFCN BH254V-64P, LCSC
C48603668) and crimp sockets (ZHOURI FC-2.54-64P, LCSC C49261185) are cheap
and thousands deep; assembled 64-way cables are thin (Amazon, DigiKey Assmann
H3BBH-6406M), so cables are crimped from sockets and 64-way ribbon if needed.

All lines are 0 V / 5 V. Everything is active-high except the four `BUS#`
lines, which are open-drain and active-low (pulled up to 5 V on the hub; a
board pulls low to assert a 1), and the eight `M` lines, which are diode-OR
outputs of the program memory boards (pulled down on the hub; a selected memory
board pulls high). A board that does not use a line leaves it unconnected.
Inputs on a board are MOSFET gates and must never float: every input a board
uses is either driven from the header or tied to a rail on the board.

## The pins

This is the table to wire or probe by: the number is the header's own pin
number, which is also the ribbon's conductor. It is `PINS` in `sim/bus.py`,
and `python3 sim/order_check.py --machine` holds every pad of every header
on every board to it.

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | +5V | 2 | +5V |
| 3 | GND | 4 | GND |
| 5 | GND | 6 | CLK |
| 7 | GND | 8 | RST |
| 9 | BUS1# | 10 | BUS0# |
| 11 | BUS3# | 12 | BUS2# |
| 13 | A1 | 14 | A0 |
| 15 | A3 | 16 | A2 |
| 17 | B1 | 18 | B0 |
| 19 | B3 | 20 | B2 |
| 21 | PC1 | 22 | PC0 |
| 23 | PC3 | 24 | PC2 |
| 25 | PC5 | 26 | PC4 |
| 27 | PC7 | 28 | PC6 |
| 29 | M1 | 30 | M0 |
| 31 | M3 | 32 | M2 |
| 33 | M5 | 34 | M4 |
| 35 | M7 | 36 | M6 |
| 37 | ZF | 38 | CF |
| 39 | EO | 40 | SUB |
| 41 | AO | 42 | AI |
| 43 | BO | 44 | BI |
| 45 | AB | 46 | BA |
| 47 | IO | 48 | OI |
| 49 | PCE | 50 | II |
| 51 | FI | 52 | PCL |
| 53 | MAI | 54 | HLT |
| 55 | MO | 56 | MI |
| 57 | WRH | 58 | WRL |
| 59 | F0 | 60 | ONE |
| 61 | INP | 62 | F1 |
| 63 | GND | 64 | +5V |

Until 2026-09-28 the header was on the front, and the two signals of every
pair of pins were the other way round (CLK on 5, RST on 7, BUS0# on 9, +5V
on 63). The boards were routed to that table and no track has moved: a
header turned over onto the back in the same holes, notch toward the top
edge, has its odd row where its even row was. So every hole carries what it
always carried, and every pin carries what its neighbour across the header
used to. Pins 1 to 4 are unchanged (+5V, +5V, GND, GND). `HOLES` in
`sim/bus.py` is the old table, kept because the copper was routed to it.

What the move cost (D062). On the ribbon a conductor's neighbours are the
pins one below and one above its own number. CLK (6) still lies between two
grounds (5 and 7). RST (8) had two grounds as well; now it has one (7) and
BUS1# (9). Reset is the one line every card obeys by level, not on a clock
edge, so a bump on it matters. `sim/tb_rst_neighbour.py` puts the two lines
on the bench with every gate the routed boards hang on them: when BUS1# is
released RST rises 0.28 to 0.43 V for some tens of microseconds, against a
lowest transistor threshold of 0.8 V (typical 2.1 V), and a card's reset
input stage dips a quarter of a volt (`sim/results/rst_neighbour.md`).
`docs/bring-up.md` has the measurement to make on the real ribbon. The
machine deck's crosstalk option (`CROSS_PF`) couples RST to BUS1# since
this change.

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
| ONE | sequencer -> ALU | The ALU uses 0001 in place of B (INC, DEC) |
| F0, F1 | sequencer -> ALU | Result select: 00 add/subtract, 01 and, 10 or, 11 xor |
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
| WRL, WRH | panel -> writable program memory | Write the bus into the low / high nibble of the word at the PC address |
| INP | sequencer -> panel | The panel's data switches drive the bus (IN) |

Lines marked internal still cross the header so the front panel can drive
them by hand while the sequencer board does not exist yet. WRL and WRH are
reserved for a writable program memory board that is not designed yet. There
are no spare pins left (D031).
