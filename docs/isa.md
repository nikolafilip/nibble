# Instruction set

Each instruction is one 8-bit word: 4 bits of opcode, 4 bits of operand.
Program memory holds 16 words, addressed 0 to 15 by the program counter.
A program is up to 16 instructions long; each is one of the ten below.

| Opcode | Name | Operand | Effect |
|---|---|---|---|
| 0000 | NOP | | Nothing |
| 0001 | LDI n | 4-bit number | A = n |
| 0010 | MOV B,A | | B = A |
| 0011 | XCH | | Swap A and B |
| 0100 | ADD | | A = A + B. C = carry out. Z = result is zero |
| 0101 | SUB | | A = A - B. C = no borrow (A >= B). Z = result is zero |
| 0110 | OUT | | OUT = A (the display LEDs) |
| 0111 | JMP a | 4-bit address | PC = a |
| 1000 | JC a | address | PC = a if C is set |
| 1001 | JZ a | address | PC = a if Z is set |
| 1010 | HLT | | Stop the clock |
| 1011 to 1111 | | | Unused. Room for AND, OR, shifts later |

Numbers are 4-bit two's complement when it suits the program (-8 to 7) or
unsigned (0 to 15); the hardware does not care, only the flags differ in meaning.

## Control steps

Every instruction takes three clock steps. Steps 0 and 1 are the same for all:

| Step | Lines | Effect |
|---|---|---|
| 0 | `II` | Instruction register loads the memory word the program counter points at |
| 1 | `PCE` | Program counter increments |
| 2 | depends on opcode | Execute (see below) |

| Instruction | Step 2 lines |
|---|---|
| LDI | `IO` `AI` |
| MOV B,A | `BA` |
| XCH | `AB` `BA` |
| ADD | `EO` `AI` `FI` |
| SUB | `SUB` `EO` `AI` `FI` |
| OUT | `AO` `OI` |
| JMP | `IO` `PCL` |
| JC | `IO` `PCL` if C |
| JZ | `IO` `PCL` if Z |
| HLT | `HLT` |

## Worked program: Fibonacci on the LEDs

```
addr  word       instr      A   B   LEDs
0     0001 0001  LDI 1      1
1     0010 0000  MOV B,A    1   1
2     0001 0000  LDI 0      0   1
3     0110 0000  OUT        0   1   0
4     0100 0000  ADD        1   1
5     0011 0000  XCH        1   1
6     1000 1000  JC 8
7     0111 0011  JMP 3
8     1010 0000  HLT
```

Slots 3 to 7 repeat. The LEDs show 0, 1, 1, 2, 3, 5, 8; the next add (8 + 13)
overflows 4 bits, sets C, and `JC 8` halts the machine.
