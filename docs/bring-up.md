# Bring-up: the whole machine, one board at a time

Ten boards arrive in one order (D032): the gate coupon, the hub and the nine
boards of the machine. Solder and test them in the order below. Every step
adds one board to a machine that already works, so a failure points at one
board. Everything below is a step you can film.

The panel is the test fixture for every other board: a switch on every
control line, an LED on every bus line, buttons for CLK and RST. Until the
clock board exists, the CLK button is the clock. Until the sequencer exists,
the switches are the sequencer.

## Tools you need before the boards arrive

- Bench supply with current limit (5.0 V, limit 300 mA for the first power-on of each board) or the USB supply through the hub once the hub is trusted.
- Multimeter with a continuity beeper.
- 8-channel USB logic analyser (any Saleae-compatible clone) and Sigrok/PulseView, or a scope.
- Temperature-controlled iron, 0.6 mm solder, flux, brass wool, wick.
- Anti-static wrist strap: 2N7000 gates are static-sensitive until soldered.
- Flush cutters, tweezers, a board holder, a lead-bending jig for TO-92 (the footprint is the 2.54 mm wide inline one).
- The frame (docs/mounting.md) can wait; boards test fine flat on the bench with the ribbons.

## Soldering, every board

Resistors first (all vertical, the body next to pad 1), then diodes, then
capacitors, headers and switches, then LEDs (long leg is the anode, the square
pad), transistors last with the strap on. Before the transistors go in, power
the board and check that no pull-up is shorted: with the resistors and LEDs
only, the current is under 1 mA. After the transistors: the expected current
is about 0.1 mA per gate that is on, so tens of mA for a big board, never
hundreds. If it is more than 50 mA above the number in the table, power off
and look for a bridge between the three TO-92 pads.

| Board | Transistors | Expected current (5 V) | Soldering time |
|---|---|---|---|
| Coupon | 26 | under 3 mA | 1 h |
| 07 hub | 0 | under 5 mA (the LED) | 1 h (the headers) |
| 06 panel | 80 | 5 to 60 mA depending on the LEDs lit | 4 h |
| 01 ALU | 233 | 10 to 25 mA | 5 h |
| 02 registers | 366 | 15 to 40 mA | 8 h |
| 09 counter | 416 | 20 to 45 mA | 9 h |
| 03 sequencer | 524 | 25 to 60 mA | 11 h |
| 04 program page | 112 | 5 to 15 mA | 4 h |
| 05 clock | 16 | under 5 mA | 1 h |
| 08 data memory | 747 | 30 to 80 mA | 15 h |

## 1. Coupon

One of every cell, with test loops, plus a ring oscillator. It measures the
transistor and the cell in copper, which the simulation only assumed.

Power J1 from the bench supply. Expected current under 3 mA.

| Measure | Where | Simulated | Write it in `gate-cell.md` |
|---|---|---|---|
| Ring period | TP_RING | about 14 µs (70 kHz) | gate delay = period / 10 |
| Rise time, 1 load | TP_FO1, drive IN low-to-high from J2 | 4 µs to 2.5 V | |
| Rise time, 10 loads | TP_FO10 | 28 µs to 2.5 V | |
| Fall time | TP_FO1 | well under 1 µs | |
| NAND output low | TP_NAND with N1=N2=N3 tied to +5 V | under 10 mV | |
| NOR output low | TP_NOR with any input high | under 10 mV | |
| Bus line low | TP_BUS with IN high | under 10 mV | |

The measured gate delay replaces the simulated one: the ALU settles in 89 µs
in the simulation, and the clock period must stay above 100 times the
fan-out-10 rise time. At the simulated numbers that is a 1 ms tick.
If the ring does not oscillate, or the low levels are above 100 mV, stop and
post it: the cell is wrong and every other board inherits it.

## 2. Hub

Solder the eight 64-way headers, the USB-B, the fuse, the LED, the
capacitors, the four 10k bus pull-ups and the eight 1 Meg M pull-downs. Plug
in USB: the power LED lights, current under 5 mA. Check 5 V between pins 1
and 3 of every slot. With the beeper, check that every signal pin reads the
same on slot 1 and slot 8: 64 pins, this is the boring video. Check that the
four BUS# test loops read 5 V (pulled up) and the eight M lines read 0 V
(pulled down).

## 3. Panel

Plug the panel alone into the hub. All LEDs off: every line reads 0 through
its 1 Meg pull-down.

- Flip a level switch on: its LED lights. 32 switches (A3..A0, B3..B0, the 24 control lines), 32 LEDs, one at a time.
- Close data switch D0 and flip INP on: the D0 LED lights, the BUS0# test loop on the hub reads 0 V (the panel pulled the line low, which is a 1). D1..D3 the same.
- Press CLK: the CLK LED lights while pressed, goes out about 0.15 s after release. Same for RST.
- With the logic analyser on the hub's CLK test loop: one press gives exactly one rising edge. Press it fifty times. Fifty edges. No other board can be trusted until this is true.

## 4. ALU

Hub + panel + ALU. The panel's A and B switches play the register board. Set
EO on (the ALU drives the bus), everything else off.

| A switches | B switches | SUB | Expected D3..D0 (panel data LEDs and the ALU's R LEDs) | CF | ZF |
|---|---|---|---|---|---|
| 0000 | 0000 | off | 0000 | off | on |
| 0011 (3) | 0100 (4) | off | 0111 (7) | off | off |
| 1111 (15) | 0001 (1) | off | 0000 | on | on |
| 0111 (7) | 0101 (5) | on | 0010 (2) | on | off |
| 0110 (6) | 0110 (6) | on | 0000 | on | on |
| 0010 (2) | 0101 (5) | on | 1101 (13, that is -3) | off | off |

Rows 4 and 5 are the two calculations the hand-made calculator got wrong.
Film those. Then the v2 lines: ONE on, A = 0101, SUB off: 0110 (INC). F0 on
(AND), A = 1100, B = 1010: 1000. F1 on, F0 off (OR): 1110. Both (XOR): 0110.
Flip EO off: the data LEDs go out (the ALU has let go of the bus) while its
own R LEDs still show the result.

The full check is all 2,048 combinations of A, B, SUB, ONE, F1, F0; the
simulation did them at every threshold corner, you do not have to. If a row
is wrong, note the output bit and the inputs; the cell tiles on the board are
in the same order as the schematic.

## 5. Registers

Hub + panel + ALU + registers. Now the A and B lines come from the register
board, so leave the panel's A and B switches off (a switch left on only
supplies a 1 where nothing drives, but it would confuse the reading).

- Load A: close data switches for 0110, INP on, AI on, press CLK. The register board's A LEDs and the panel's A LEDs show 0110. AI off.
- Load B the same way with BI: 0011.
- Read back: AO on: the data LEDs show 0110. AO off, BO on: 0011. Both off: the bus is empty (all data LEDs off).
- ADD: EO on: the data LEDs show 1001 (the ALU adds what the registers hold). OI on, press CLK: the OUT LEDs show 1001. Turn everything off: OUT still shows 1001.
- XCH: BA and AB on, press CLK: A and B have swapped. One edge, both registers.
- Hold: with nothing enabled, press CLK twenty times. Nothing changes.

The registers are not reset by RST; they power up in whatever state the
latches fall into. That is by design, and programs write before they read.

## 6. Sequencer and counter

The two boards share a 12-way link cable (OPR0..7, PCR, RAI) and neither
works alone: the counter's jump inputs come over the link, so plug the link
first, then both ribbons into the hub.

With no program board, every fetched word is 0000 0000 = NOP. Press RST once,
then CLK repeatedly:

- The step LEDs on the sequencer walk T0, T1, T3, T0 ... (S0, S1, S3 in `docs/isa.md`; NOP is a one-word instruction and skips S2 and S4).
- At T1 the PCE LED (panel and sequencer) is on and the counter's PC LEDs count up by one every three presses.
- IR stays 0000, the operand register stays 0.
- Press RST: PC back to 00000000, step back to T0.

## 7. Program page

Set the page jumpers to page 0 (all four on pins 2-3). Print the switch
pattern for `fib.asm`:

```
cd sim && python3 asm.py programs/fib.asm
```

and set the sixteen DIP-8 switches to it, bit 7 at the top of each word,
closed = 1. Plug it into the hub with everything else. Press RST, then press
CLK and watch: three to five presses per instruction, the row LED on the program board
shows the word being fetched, the sequencer's IR shows its opcode after T0,
the register LEDs change on the tick the ISA says. The OUT LEDs show 0, 1, 1,
2, 3, 5, 8 and the HLT LED comes on at `end`. That is the machine running its
first program, by hand, and the whole sequence is 127 presses (the simulation counts the same 127 ticks).

If it goes wrong, the trace is what to film: which instruction, which tick
(T0..T4), which line was not what `docs/isa.md` says. The simulation's trace
for the same program, tick for tick, is `sim/machine.py programs/fib.asm`.

## 8. Clock board

RUN switch off is STEP mode: the panel's CLK button still works and the
clock board only adds the power-on reset (RST is high for about a tenth of
a second after power) and the halt gate. Power-cycle the machine with fib on the
program page: PC and step counter start at 0 without pressing RST.

RUN on: the oscillator drives CLK. With the SLOW jumper on the pot spans
0.8 to 10 Hz, so the machine runs fib visibly. Jumper off: 40 to 500 Hz,
all slower than the 1 kHz the machine was simulated at (the measured gate
delay from the coupon says whether even that is safe: the tick must stay
above 100 times the fan-out-10 rise time). HLT stops the clock: the OUT LEDs
hold 8 and the CLK LED stays off. RST restarts.

## 9. Data memory

Hub + panel + memory, by hand first:

- Address: data switches 0101, INP on, MAI on: the MAR LEDs show 0101 (the latch is transparent while MAI). MAI off: they hold.
- Write: data switches 1001, MI on, press CLK: the four cell LEDs in row 5 show 1001. MI off.
- Read: data switches all open, INP off, MO on: the data LEDs show 1001. MO off.
- Write four different slots and read them back in a different order.

Then the whole machine with `list.asm` on the program page (it needs two
pages: set the second board's jumpers to page 1 and hop its ribbon from the
first page's right header). Expected OUT: 9, the maximum of the four numbers
it stores. Then `sort.asm` (five pages) if you have them: 2 5 9 14.

## 10. All boards, all programs

Every program in `sim/programs/` has an `; expect:` line: the OUT values in
order, then the label it halts at. With the clock board in RUN and the SLOW
jumper on, each one runs in under a minute. Film the OUT LEDs; compare with
the line. The eleven programs are the acceptance test; the simulation ran
them on the same netlists, so a difference is copper, solder or a part, not
the design.
