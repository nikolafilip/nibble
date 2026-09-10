# Instruction set (v2)

An instruction is one or two 8-bit words. The first word is 4 bits of opcode
and 4 bits of operand. Jumps and calls carry a second word holding an 8-bit
address. Program memory is 256 words, addressed by the 8-bit program counter;
the switch boards provide 16 words each, one per page.

Opcode 0000 is a family: those instructions need no operand, so the operand
nibble selects which one. That leaves eight opcodes free for instructions that
do carry an operand, and blank memory (all switches open) reads as NOP.

| Opcode | Name | Words | Effect |
|---|---|---|---|
| 0000 nnnn | family | 1 | see the next table |
| 0001 nnnn | LDI n | 1 | A = n |
| 0010 | JMP a | 2 | PC = a |
| 0011 | JC a | 2 | PC = a if C is set |
| 0100 | JZ a | 2 | PC = a if Z is set |
| 0101 nnnn | LOAD n | 1 | A = data memory slot n |
| 0110 nnnn | STORE n | 1 | data memory slot n = A |
| 0111 | CALL a | 2 | RA = address of the next instruction; PC = a |
| 1000 to 1111 | | | Free |

| Word | Name | Effect |
|---|---|---|
| 0000 0000 | NOP | Nothing |
| 0000 0001 | MOV B,A | B = A |
| 0000 0010 | XCH | Swap A and B |
| 0000 0011 | ADD | A = A + B. C = carry out. Z = result is zero |
| 0000 0100 | SUB | A = A - B. C = no borrow (A >= B). Z = result is zero |
| 0000 0101 | OUT | OUT = A (the display LEDs) |
| 0000 0110 | HLT | Stop the clock |
| 0000 0111 | DEC | A = A - 1, flags as SUB |
| 0000 1000 | INC | A = A + 1, flags as ADD |
| 0000 1001 | LOAD [B] | A = data memory slot B |
| 0000 1010 | STORE [B] | data memory slot B = A |
| 0000 1011 | IN | A = the panel's data switches |
| 0000 1100 | RET | PC = RA |
| 0000 1101 | AND | A = A and B, bit by bit. C = 0, Z = result is zero |
| 0000 1110 | OR | A = A or B |
| 0000 1111 | XOR | A = A xor B |

Numbers are 4-bit two's complement when it suits the program (-8 to 7) or
unsigned (0 to 15); the hardware does not care, only the flags differ in
meaning. Wider results are built from nibbles with the carry flag and JC:
`sim/programs/mul.asm` makes an 8-bit product, `calc.asm` does it as a
subroutine on numbers typed on the switches.

Shift left is `MOV B,A` then `ADD`: the top bit lands in C. There is no shift
right; a 16-entry table in data memory read with `LOAD [B]` gives any function
of one nibble.

CALL saves one return address, in the return register RA. A subroutine cannot
call another (the second CALL would overwrite RA), which is how the early
microcontrollers worked. A stack would be a different machine.

## Control steps

The sequencer has five states. Every instruction runs S0 and S1; two-word
instructions run S2; every instruction runs S3; memory instructions run S4.
A "done" column in the control matrix returns the sequencer to S0 early, so
one-word instructions take 3 ticks, memory instructions 4, jumps and calls 5.

| Step | Lines | Effect |
|---|---|---|
| S0 | `II` | Instruction register loads the memory word the program counter points at |
| S1 | `PCE` | Program counter increments |
| S2 | `OPI` `PCE` | (two-word only) operand register loads the next word, counter increments |
| S3 | matrix row 1 | Execute, first tick |
| S4 | matrix row 2 | Execute, second tick (memory instructions) |

| Instruction | S3 | S4 |
|---|---|---|
| NOP | `DONE` | |
| MOV B,A | `BA` `DONE` | |
| XCH | `AB` `BA` `DONE` | |
| ADD | `EO` `AI` `FI` `DONE` | |
| SUB | `SUB` `EO` `AI` `FI` `DONE` | |
| OUT | `AO` `OI` `DONE` | |
| HLT | `HLT` | |
| DEC | `ONE` `SUB` `EO` `AI` `FI` `DONE` | |
| INC | `ONE` `EO` `AI` `FI` `DONE` | |
| LOAD [B] | `BO` `MAI` | `MO` `AI` `DONE` |
| STORE [B] | `BO` `MAI` | `AO` `MI` `DONE` |
| IN | `INP` `AI` `DONE` | |
| RET | `PCR` `DONE` | |
| AND | `F0` `EO` `AI` `FI` `DONE` | |
| OR | `F1` `EO` `AI` `FI` `DONE` | |
| XOR | `F0` `F1` `EO` `AI` `FI` `DONE` | |
| LDI | `IO` `AI` `DONE` | |
| JMP | `PCL` `DONE` | |
| JC | `PCL` if C, `DONE` | |
| JZ | `PCL` if Z, `DONE` | |
| LOAD n | `IO` `MAI` | `MO` `AI` `DONE` |
| STORE n | `IO` `MAI` | `AO` `MI` `DONE` |
| CALL | `RAI` `PCL` `DONE` | |

`PCL` copies the 8-bit operand register into the program counter, `PCR` copies
the return register, `RAI` copies the program counter into the return register;
all three are paths internal to the sequencer board, the 4-bit bus is not
involved. CALL does `RAI` and `PCL` on the same edge: the return register
captures the old program counter while the counter loads the target.

After S1 the step counter goes to S2 for a two-word instruction and straight to
S3 otherwise, so one-word instructions never spend a tick in S2.

## ALU control lines

| Lines | Result |
|---|---|
| none | A + B |
| `SUB` | A - B |
| `ONE` | the B input is replaced by 0001, so `ONE` alone is A + 1 and `ONE` `SUB` is A - 1 |
| `F0` | A and B |
| `F1` | A or B |
| `F0` `F1` | A xor B |

The carry flag is the adder's carry out; for the logic functions it reads 0.
The zero flag is 1 when the selected result is 0000.

## Registers on the sequencer

- **IR**, 4 bits: the opcode. `II` loads it from M7..M4.
- **OPR**, 8 bits: the operand. `II` loads its low nibble from M3..M0 at the
  same time as IR (that is the `n` of LDI, LOAD and STORE, and the family
  selector of opcode 0000); `OPI` loads all eight bits from M (the address
  word of a jump or call). `IO` drives OPR3..0 onto the bus, `PCL` copies all
  of OPR into the program counter.
- **PC**, 8 bits. `PCE` increments it, `PCL` and `PCR` load it. By the time an
  instruction executes (S3), PC already points at the next word.
- **RA**, 8 bits: the return address. `RAI` loads it from PC, `PCR` copies it
  back.
- **CF, ZF**: latched from the ALU's carry and zero outputs when `FI` is
  high, which only ADD, SUB, INC, DEC, AND, OR and XOR assert. No other
  instruction touches the flags: a LOAD of zero does not set Z, so loops test
  the result of a DEC, not the value they loaded.
- **RST** clears PC, IR, OPR, RA, the flags and the step counter. A, B, OUT
  and the data memory are not on the reset line and keep whatever they held.

Every register captures on the rising edge of CLK, from values present before
the edge: ADD latches A = A + B and the flags of that same sum on one edge.
`sim/emu.py` implements exactly this and is the reference for the machine
simulation.

## The control matrix

The sequencer board decodes the opcode into 16 lines and, for opcode 0000,
the operand nibble into 16 more. ANDed with S3 and S4 that gives 62 row wires
(15 opcodes plus 16 family members, two steps each). The control lines are
columns. A diode soldered at a crossing pulls that column when that row is
active. Every instruction above is populated at assembly; the free opcodes
take any future instruction that can be expressed with the lines on the
header. Columns have 1 Meg pull-downs.

## Worked program: Fibonacci on the LEDs

```
addr  word       instr      A   B   LEDs
0     0001 0001  LDI 1      1
1     0000 0001  MOV B,A    1   1
2     0001 0000  LDI 0      0   1
3     0000 0101  OUT        0   1   0
4     0000 0011  ADD        1   1
5     0000 0010  XCH        1   1
6     0011 0000  JC         (second word follows)
7     0000 1010    -> 10
8     0010 0000  JMP
9     0000 0011    -> 3
10    0000 0110  HLT
```

Eleven words. Slots 3 to 9 repeat. The LEDs show 0, 1, 1, 2, 3, 5, 8; the
next add (8 + 13) overflows 4 bits, sets C, and JC halts the machine. The
reference programs in `sim/programs/` go further: sorting four numbers typed
on the switches, a pseudo-random sequence with XOR, Euclid's algorithm, and
an interactive multiply with the multiply as a subroutine.
