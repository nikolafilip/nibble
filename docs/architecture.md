# Architecture

Nibble is a 4-bit accumulator machine. It runs one loop forever: read the
instruction at the address held in the program counter, decode it, execute it,
add one to the program counter. Jumps overwrite the program counter instead.

## Parts, and the board each one becomes

| Part | What it does | Board |
|---|---|---|
| ALU | Adds or subtracts A and B in two's complement, or ands, ors, xors them; can use 1 in place of B. Produces a 4-bit result, a carry flag and a zero flag. | `01-alu` |
| Registers A, B, OUT | A is the accumulator: every result lands here. B is the second operand and can drive the bus (BO) so it can serve as a memory pointer. OUT drives the display LEDs. | `02-registers` |
| Program counter, return register | 8-bit counter, loaded from the operand register for jumps and calls, or from the 8-bit return register for RET. Takes the operand and its load lines from the sequencer over a 12-pin link cable (D035). | `09-counter` |
| Instruction register, operand register, control | Holds the current instruction and its 8-bit operand; a five-state step counter, two decoders (opcode, and the operand nibble for the 0000 family) and a diode matrix (37 rows: every instruction's first execute step, the second step of the four memory accesses, the two conditional jumps) turn them into control-line pulses. New instructions are diodes. | `03-sequencer` |
| Program memory | 16 words of 8 bits per board as DIP switches with a diode per bit, selected by PC0..3; PC4..7 select the board (page jumpers). Build more copies for longer programs. | `04-program` |
| Data memory | 16 slots of 4 bits with its own address register (MAI) and MI/MO lines, addressed by an instruction operand or by B. Gives programs variables, lists and tables. | `08-memory` |
| Clock and reset | Schmitt-trigger RC oscillator with a speed pot, RUN/STEP switch, halt gate, power-on reset; single-step comes from the panel button. | `05-clock` |
| Front panel | Switches to force A, B and control lines by hand; LEDs on every bus line; the data switches double as the machine's input port (IN). Test fixture for every other board. | `06-panel` |
| Bus hub | Pull-ups for the bus, pull-downs for the M lines, power distribution, one 64-way header per board. | `07-hub` |

Boards connect to the hub with ribbon cables and sit in a rack. The hub is the
only place the bus pull-ups live, so a board can be unplugged without changing
the logic levels anywhere else.

## The bus

Four data lines, active-low, open-drain. Any board pulls a line low to put a
`1` on it; a resistor on the hub pulls it back to 5 V. Several sources may sit
on the bus at once because only the enabled one pulls. Sources: A (`AO`), B
(`BO`), the ALU result (`EO`), the instruction operand (`IO`), data memory
(`MO`), the panel switches (`INP`). Sinks: A (`AI`), B (`BI`), OUT (`OI`), the data memory address register
(`MAI`), data memory (`MI`), writable program memory (`WRL`, `WRH`). The
program counter loads from the operand register directly, not from the bus.

A and B also cross the header as plain 4-bit values, because the ALU reads them
continuously, and because `XCH` needs both registers to read each other in the
same clock without going through the bus.

## Levels and speed

Logic 0 is below 0.5 V, logic 1 is above 4 V, supply is 5 V. A gate output
rises through its pull-up resistor and falls through its transistor, so rising
edges are slow (microseconds) and falling edges are fast. The clock is expected
to run up to a few hundred hertz and be watched at a few hertz. The gate coupon
board measures the real numbers before anything else is ordered.
