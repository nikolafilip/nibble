# Instruction set (v2)

An instruction is one or two 8-bit words. The first word is 4 bits of opcode
and 4 bits of operand. Jumps carry a second word holding an 8-bit address.
Program memory is 256 words, addressed by the 8-bit program counter; today's
switch boards provide 16 words each, one per page.

| Opcode | Name | Words | Effect |
|---|---|---|---|
| 0000 | NOP | 1 | Nothing |
| 0001 | LDI n | 1 | A = n |
| 0010 | MOV B,A | 1 | B = A |
| 0011 | XCH | 1 | Swap A and B |
| 0100 | ADD | 1 | A = A + B. C = carry out. Z = result is zero |
| 0101 | SUB | 1 | A = A - B. C = no borrow (A >= B). Z = result is zero |
| 0110 | OUT | 1 | OUT = A (the display LEDs) |
| 0111 | JMP a | 2 | PC = a (8-bit address in the second word) |
| 1000 | JC a | 2 | PC = a if C is set |
| 1001 | JZ a | 2 | PC = a if Z is set |
| 1010 | HLT | 1 | Stop the clock |
| 1011 | LOAD n | 1 | A = data memory slot n (reserved; needs the data memory board) |
| 1100 | STORE n | 1 | data memory slot n = A (reserved; needs the data memory board) |
| 1101 to 1111 | | | Unused. Candidates: LOAD from the address in B, STORE to the address in B, subtract 1 |

Numbers are 4-bit two's complement when it suits the program (-8 to 7) or
unsigned (0 to 15); the hardware does not care, only the flags differ in
meaning. Wider results are built from nibbles with the carry flag and JC.

## Control steps

The sequencer has five states. Every instruction runs S0 and S1; two-word
instructions run S2; every instruction runs S3; memory instructions run S4.
A "done" column in the control matrix returns the sequencer to S0 early, so
one-word instructions take 3 ticks, memory instructions 4, jumps 5.

| Step | Lines | Effect |
|---|---|---|
| S0 | `II` | Instruction register loads the memory word the program counter points at |
| S1 | `PCE` | Program counter increments |
| S2 | `OPI` `PCE` | (two-word only) operand register loads the next word, counter increments |
| S3 | matrix row 1 | Execute, first tick |
| S4 | matrix row 2 | Execute, second tick (memory instructions) |

| Instruction | S3 | S4 |
|---|---|---|
| LDI | `IO` `AI` `DONE` | |
| MOV B,A | `BA` `DONE` | |
| XCH | `AB` `BA` `DONE` | |
| ADD | `EO` `AI` `FI` `DONE` | |
| SUB | `SUB` `EO` `AI` `FI` `DONE` | |
| OUT | `AO` `OI` `DONE` | |
| JMP | `PCL` `DONE` | |
| JC | `PCL` if C, `DONE` | |
| JZ | `PCL` if Z, `DONE` | |
| HLT | `HLT` | |
| LOAD n | `IO` `MAI` | `MO` `AI` `DONE` |
| STORE n | `IO` `MAI` | `AO` `MI` `DONE` |

`PCL` copies the 8-bit operand register into the program counter over a path
internal to the sequencer board; the 4-bit bus is not involved.

After S1 the step counter goes to S2 for a two-word opcode and straight to S3
otherwise, so one-word instructions never spend a tick in S2.

## Registers on the sequencer

- **IR**, 4 bits: the opcode. `II` loads it from M7..M4.
- **OPR**, 8 bits: the operand. `II` loads its low nibble from M3..M0 at the
  same time as IR (that is the `n` of LDI, LOAD and STORE); `OPI` loads all
  eight bits from M (the address word of a jump). `IO` drives OPR3..0 onto the
  bus, `PCL` copies all of OPR into the program counter.
- **PC**, 8 bits. `PCE` increments it, `PCL` loads it. By the time an
  instruction executes (S3), PC already points at the next word.
- **CF, ZF**: latched from the ALU's carry and zero outputs when `FI` is
  high, which only ADD and SUB assert. No other instruction touches the flags:
  a LOAD of zero does not set Z, so loops test the result of a SUB, not the
  value they loaded (see `sim/programs/mul.asm`).
- **RST** clears PC, IR, OPR, the flags and the step counter. A, B and OUT are
  not on the reset line and keep whatever they held.

Every register captures on the rising edge of CLK, from values present before
the edge: ADD latches A = A + B and the flags of that same sum on one edge.
`sim/emu.py` implements exactly this and is the reference for the machine
simulation.

## The control matrix

The sequencer board decodes all sixteen opcodes and ANDs each with S3 and S4,
giving 32 row wires. The control lines are columns. A diode soldered at a
crossing pulls that column when that row is active. The ten instructions above
are populated at assembly; LOAD and STORE are two diodes each, added when the
data memory board exists; the free rows take any future instruction that can be
expressed with the lines on the header. Columns have 1 Meg pull-downs.

## Worked program: Fibonacci on the LEDs

```
addr  word       instr      A   B   LEDs
0     0001 0001  LDI 1      1
1     0010 0000  MOV B,A    1   1
2     0001 0000  LDI 0      0   1
3     0110 0000  OUT        0   1   0
4     0100 0000  ADD        1   1
5     0011 0000  XCH        1   1
6     1000 0000  JC         (second word follows)
7     0000 1010    -> 10
8     0111 0000  JMP
9     0000 0011    -> 3
10    1010 0000  HLT
```

Eleven words. Slots 3 to 9 repeat. The LEDs show 0, 1, 1, 2, 3, 5, 8; the
next add (8 + 13) overflows 4 bits, sets C, and JC halts the machine.
