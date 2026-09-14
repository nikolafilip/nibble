# Bring-up: the whole machine, one card at a time

Rewritten 2026-09-11 for the cards (D042, `cards.md`). The order of testing
and the tests carry over from the nine-board plan: a register bit card is
tested the way the register board was, one bit at a time, and a machine
that already works gets one more card at each step, so a failure points at
one card.

The order (docs/order-1.md) brings the gate coupon, the sequencer board and
the cards: 25 designs, most in fives. Solder and test them in the order
below. The panel cards are the test fixture for every other card: a switch
on every control line, an LED on every bus line, buttons for CLK and RST.
Until the clock card is in, the CLK button is the clock. Until the
sequencer is in, the switches are the sequencer.

## Tools you need before the cards arrive

- Bench supply with current limit (5.0 V, limit 300 mA for the first power-on of each board) or the USB supply through the hub once the hub is trusted.
- Multimeter with a continuity beeper.
- 8-channel USB logic analyser (any Saleae-compatible clone) and Sigrok/PulseView, or a scope.
- Temperature-controlled iron, 0.6 mm solder, flux, brass wool, wick.
- Anti-static wrist strap: 2N7000 gates are static-sensitive until soldered.
- Flush cutters, tweezers, a board holder, a lead-bending jig for TO-92 (the footprint is the 2.54 mm wide inline one).
- The frame (docs/mounting.md) can wait; cards test fine flat on the bench on a short ribbon with a few sockets crimped on.

## Soldering, every card

Resistors first (all lying flat on the tile, the body over pad 1), then
diodes, then capacitors, headers, jumpers and switches, then LEDs (long leg
is the anode, the square pad), transistors last with the strap on. Before
the transistors go in, power the card and check that no pull-up is
shorted: with the resistors and LEDs only, the current is under 1 mA.
After the transistors: about 0.1 mA per gate that is on, so tens of mA for
a full card, never hundreds. If it is more than 30 mA above the number in
the table, power off and look for a bridge between the three TO-92 pads.

| Card | Transistors | Expected current (5 V) | Soldering time |
|---|---|---|---|
| coupon | 26 | under 3 mA | 1 h |
| hub | 0 | under 5 mA (the LED) | 1 h (the headers, the USB socket) |
| panel A, B, C | 28, 20, 32 | 5 to 40 mA depending on the LEDs lit | 2 h each |
| register bit | 99 | 5 to 12 mA | 2.5 h each |
| ALU bit | 66 to 73 | 4 to 9 mA | 2 h each |
| counter bit | 62 | 4 to 8 mA | 2 h each |
| memory control | 59 | 3 to 7 mA | 1.5 h |
| memory slots | 91 | 5 to 12 mA | 2.5 h each |
| program | 41 + 32 diodes | 3 to 6 mA | 1.5 h each |
| clock | 16 | under 5 mA | 1 h |
| sequencer | 592 + 87 diodes | 30 to 70 mA | 12 h |

## 1. Coupon

One of every cell, with test loops, plus a ring oscillator: it measures
the transistor and the cell in copper, which the simulation only assumed.
Power it from the bus header (pins 1-2 +5 V, 3-4 ground) on the bench
supply, or from the hub once the hub is trusted. Expected current under
3 mA.

| Measure | Where | Simulated | Write it in `gate-cell.md` |
|---|---|---|---|
| Ring period | RING | about 14 us (70 kHz) | gate delay = period / 10 |
| Rise time, fan-out 1 vs 10 | FO1, FO10 | 1 us vs 3 us | the 47k pull-up against the gate capacitance |
| NAND and NOR output low, all inputs high | NAND, NOR | under 0.2 V | three transistors in series still pull low |
| Bus driver low with the 10k pull-up | BUS | under 0.1 V | |
| Supply current, all inputs low | the supply | under 3 mA | |

If the ring is slower than 30 us or an output low is above 0.5 V, stop:
the cell is not what the simulation modelled, and every card depends on
it.

## 2. Hub

No logic. Check with the meter, USB unplugged: no short between +5V and
ground on either header; every one of the 64 pins of the top header beeps
to the same pin of the bottom header; the four BUS pull-ups read 10k to
+5V; the eight M pull-downs read 220k to ground. Plug the USB in: the
power LED lights, the current is under 5 mA. Crimp the first ribbon: a
short piece with three sockets for the bench, then the long ones for the
column.

## 3. Panel A, B, C

Plug the three onto the ribbon with the hub. Every level switch up puts a
1 on its line: the LED of that line lights on card A or B, and the meter
reads 5 V on the header pin. Switch down: 0 V (the 1 Meg pull-down). Card
C: the CLK and RST buttons each give one clean edge per press on the
header (scope or logic analyser: no bounce after the Schmitt trigger); the
DATA switches show on the D3..D0 LEDs of card A only while INP is up
(card B's switch): that is the input port driving the bus. PC and M LEDs
follow the PC and M lines, which nothing drives yet.

## 4. Register bit cards

One card at a time, on the ribbon with the hub and the panel. The panel's
A and B switches sit on the registers' output lines, so leave them down
and drive the bus instead: DATA switch <i> on card C with INP up puts the
bit on the bus; raise AI, press CLK: the A<i> LED lights (the card's own
and panel A's). AO puts A back on the bus: the D<i> LED. Same
for B with BI, BO; BA copies A into B, AB copies B into A; OI loads OUT.
All four cards on the ribbon: any value through A and B, in both
directions. This is the register testbench's script done by hand; the
simulation ran it 113 steps at six corners.

## 5. ALU bit cards

The four cards side by side, the 2x3 links between them (IN of bit i+1 to
OUT of bit i), on the ribbon with the hub, panel and registers. Load A and
B through the panel, set F1 F0 (00 add, 01 and, 10 or, 11 xor), SUB, ONE;
raise EO: the result on the bus is on the D3..D0 LEDs, CF and ZF on card
A. Try 3 + 5, 9 + 9 (carry), 7 - 7 (zero), 0 - 1 (borrow, CF = 0). The
simulation did all 2304 cases at four corners.

## 6. Counter bit cards

Eight cards in a row, the 2x3 carry links between neighbours, the 2x6
ribbon from the sequencer's link header along all eight (not connected
yet: the sequencer is later). RST: all PC LEDs off. PCE up, press CLK: bit
0 lights; again: bit 1; the carry runs through the links. PCL with the
bus data switches (OPR comes from the sequencer later; for now the panel's
switches on the link ribbon's OPR lines): loads a jump target. RAI then
PCR: the return register. call.asm on the eight cards in the simulation
passed; the machine gate proves the rest.

## 7. Memory control and slot cards

Memory control on the ribbon, the 2x6 link ribbon from it along the eight
slot cards, each slot card's jumpers set to its pair (A3 A2 A1 = the
pair number 0..7 in binary, the centre pin to '1' where the bit is 1).
MAI with an address on the data switches, then MI with a value: the cell
LEDs of that slot show the value. Change the address, MO: the value comes
back on the bus. Fill all sixteen, read all sixteen (the testbench's
script). A slot that always reads another slot's value is a jumper on the
wrong side.

## 8. Program cards

Set a card's jumpers: P7..P4 the page, G3 G2 the word group, the centre pin
to '1' where the address bit is 1; card c holds words 4c..4c+3. Set the
switches of a short program (`sim/programs/count.asm` assembled by
`sim/emu.py` gives the words; switch up = 1, bit 7 at the top). With the
counter on the bus, PCE up and the CLK button: each press moves PC by one,
the card's R<n> LED shows the row, and the M LEDs on panel C show the word.
A blank word (all down) reads 0000 0000, NOP.

## 9. Clock card

RUN switch off, STEP: the panel's CLK button owns the line. RUN: the OSC
LED blinks and the CLK line runs at the pot's speed (500 Hz down to 40 Hz,
the SLOW jumper 10 Hz to 0.8 Hz); HLT high stops it a quarter of a
millisecond later, after the pulse in flight (D050). Power-on: RST high
for a tenth of a second, then low.

## 10. Sequencer

The big board last, on the ribbon, its link ribbon to the counter cards.
Its own LEDs show the step and the instruction register. With the whole
machine on the bus and a program card set to count.asm, single-step with
the CLK button and compare every tick with the emulator's trace
(`python3 emu.py programs/count.asm --trace`): PC, the M word, the step,
the control lines on the panel B LEDs, A and B. Then RUN. Then every
program in `sim/programs`, which the machine gate ran at every corner
before the boards were ordered.

## When something is wrong

- A card draws too much: a bridge on a TO-92, or a transistor in
  backwards (the flat face is on the silk outline's flat side).
- A line reads 2 to 3 V: two cards driving it; one has a switch or a
  jumper wrong, or a link ribbon is one row off.
- A card works alone and fails on the ribbon: a socket crimped one row
  off, or pin 1 (the red edge) at the wrong end.
- The simulation numbers are the reference for every measurement here:
  `cards/README.md` says which run proved which card.
