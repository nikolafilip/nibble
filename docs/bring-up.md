# Bring-up: the whole machine, one card at a time

Rewritten 2026-09-11 for the cards (D042, `cards.md`). The order of testing
and the tests carry over from the nine-board plan: a register bit card is
tested the way the register board was, one bit at a time, and a machine
that already works gets one more card at each step, so a failure points at
one card.

The pilot order (docs/order-1.md, D055) brings the coupon, one register
bit card and the hub: sections 1, 2 and 4 below, with a short ribbon and
the bench supply in place of the panel. Without the panel nothing pulls
the control lines down (its 1 Meg pull-downs), so on the hub's second
header jumper the register's control lines and CLK and RST to ground, raise
one at a time through 1k from +5V, and read the bus bit and the A, B, OUT
LEDs; the card's currents are the table's. The
second order brings the sequencer board and the other cards: 25 designs,
most in fives. Solder and test them in the order below. The panel cards are the test fixture for every other card: a switch
on every control line, an LED on every bus line, buttons for CLK and RST.
Until the clock card is in, the CLK button is the clock. Until the
sequencer is in, the switches are the sequencer.

## Tools you need before the cards arrive

- Bench supply with current limit (5.0 V, limit 300 mA for the first power-on of each board; 1.5 A for the whole machine into the hub's banana sockets, D052, D058) with a pair of banana-to-banana leads. The machine has no other power entry (D057).
- Multimeter with a continuity beeper.
- 8-channel USB logic analyser (any Saleae-compatible clone) and Sigrok/PulseView, or a scope.
- Temperature-controlled iron, 0.6 mm solder, flux, brass wool, wick.
- Anti-static wrist strap: 2N7000 gates are static-sensitive until soldered, and the bus lines of a finished card go straight to gates: strap on whenever a card or a ribbon is handled.
- Flush cutters, tweezers, a board holder, a lead-bending jig for TO-92 (the footprint is the 2.54 mm wide inline one).
- The frame (docs/mounting.md) can wait; cards test fine flat on the bench on a short ribbon with a few sockets crimped on.

## Soldering, every card

Every card has a drawing, `fab/<card>-assembly.svg`: which resistor is not
the common value, which way round each diode, LED and capacitor goes. The
boards print no values.

Resistors first (all standing upright on 5.08 mm, the body on one pad, the
bare lead bent over to the other), then diodes, then capacitors, link
headers, jumpers and switches, then LEDs (the short leg, the cathode, in the
square pad), transistors last with the strap on.

**The 64-pin bus header goes on the back of the board** (D059), with its
notch toward the top edge (on the hub both headers, the lower one too): the
front says `HEADER ON THE BACK`, the back has the header's outline with
`HEADER HERE` and `NOTCH TO TOP`. Its pins are soldered on the front. The link
headers (2x3, 2x6) and the jumpers stay on the front. A header on the wrong
face puts every signal on the wrong conductor of the ribbon. Before
the transistors go in, power the card and check that no pull-up is
shorted: with the resistors and LEDs only, the current is under 1 mA.
After the transistors: about 0.1 mA per gate that is on, so tens of mA for
a full card, never hundreds. If it is more than 30 mA above the number in
the table, power off and look for a bridge between the three TO-92 pads.

| Card | Transistors | Expected current (5 V) | Soldering time |
|---|---|---|---|
| coupon | 57 | 5 to 8 mA with IN low, 11 to 14 mA with IN high (the oscillator's 1k driver runs always; the LED and the row when IN is up) | 1.5 h |
| hub | 0 | under 6 mA (the LED, and half a milliamp in the crowbar's zener) | 1 h (the headers, the two sockets, the crowbar) |
| panel A, B, C | 28, 20, 32 | 5 to 40 mA depending on the LEDs lit; B 10 mA more, its two button drivers idle low through 1k (D053) | 2 h each |
| register bit | 99 | 5 to 12 mA | 2.5 h each |
| ALU bit | 66 to 73 | 4 to 9 mA | 2 h each |
| counter bit | 62 | 4 to 8 mA | 2 h each |
| memory control | 57 | 3 to 7 mA | 1.5 h |
| memory slots | 91 | 5 to 12 mA | 2.5 h each |
| program | 41 + 32 diodes | 3 to 6 mA | 1.5 h each |
| clock | 17 | 5 to 12 mA in RUN (the 1k CLK and RST drivers, D053) | 1 h |
| sequencer | 592 + 87 diodes | 30 to 70 mA | 12 h |

## 1. Coupon

Every cell the machine is built from, with a test loop on each (D056): it
measures the transistor and the cells in copper, which the simulation only
assumed. Power it from the bench supply on the 2-pin POWER header (5.00 V,
limit 300 mA), or from the bus header (pins 1-2 +5 V, 3-4 ground) once the
hub is trusted. Drive the inputs from the 6-pin INPUTS header: each has a
1 Meg pull-down, so an open pin is 0; a wire from the +5V loop is a 1. RST
open lets the flip-flop run. Clip a 3.3 nF capacitor from the DRV loop to
GND (the ribbon and seventeen cards' gates, as the clock card sees them)
and use a x10 probe: the expected numbers assume both.

The numbers to expect are in `sim/results/coupon_expected.md`, from
`sim/tb_coupon.py` on the routed card's own netlist at the model's three
threshold corners (0.8, 2.0, 3.0 V) and three mixed-threshold seeds; the
band is the lowest to the highest over those runs. What each loop stands
for and what a reading outside its band would mean:

| Measure | Loop | Expected (5 V, x10 probe) | What it stands for |
|---|---|---|---|
| Ring period | RING0 (the ring node), RING (buffered) | 6 to 24 us; a low-threshold ring swings only 1.6 to 3 V, and RING may then show nothing while RING0 runs | the gate delay of the 47k cell: the corner this batch of transistors sits at. Slower than the band: the cell is slower than any corner simulated |
| Rise 10-90 %, fan-out 1 and 10 | FO1, FO10 (IN toggled by hand or a 1 kHz square) | 10 to 12 us and 67 to 77 us | the pull-up against the gate capacitance with its Miller part: what every control line's rising edge costs. Slower than the band: the input capacitance is above the model's |
| Delay IN edge to FO1 / FO10 half way | FO1, FO10 | 5 to 6.5 us / 14 to 29 us | the same, as a delay |
| NAND and NOR output low, N1 N2 N3 = 111 | NAND, NOR | under 0.01 V | three transistors in series still pull low: every decoder's stack. Above 0.5 V: stop |
| Bus driver low, IN high | BUS | under 0.01 V (10k pull-up) | the register and ALU drivers against the hub's pull-up |
| Schmitt trip points | X | lower 0.8 to 3.0 V, upper 0.4 V above it | the clock card's Schmitt pair (the same parts): the hysteresis is 0.4 V whatever the threshold. No oscillation, or X stuck: the pair's dead point the design was meant to exclude |
| Oscillator period and duty | OSC | 1.6 to 2.6 ms, high 34 to 80 % | the clock card at its fastest setting (100k + 47 nF, the pot at zero) |
| Toggle flip-flop | Q with RST open | half the OSC rate, one Q edge per OSC rising edge | the master-slave cell of the counters and the sequencer, clocked by a real edge |
| Reset | Q with RST wired to +5V | 0 V between clock edges; at a rising clock edge a pulse of up to 4 V and 10 us can appear at some threshold mixes (the master's release racing the slave's copy; the machine's masters are closed at that moment) | the asynchronous reset of the counter and sequencer flops |
| Line driver edge into 3.3 nF | DRV (clip the capacitor on) | high 4.0 V (5 V less a diode, through 1.1k against 10k); rise 0.5 to 3.5 V in 6 to 8 us; fall 3.5 to 0.8 V in 45 to 55 us | the CLK edge every card sees and the RST release (D053); the capacitor's tolerance moves both by its own percentage |
| Threshold | VTO (a meter) | 0.9 to 3.0 V: about 0.1 V above this one transistor's threshold | Vgs(th) of one 2N7000 at 0.6 mA. Also measure twenty loose ones on a component tester or with a 4.7k and the meter: the spread of the batch is what MIX simulated |
| Program row | ROM | 4.5 V with IN low, 0 V with IN high | the M-line high through a row's diode into the hub's 220k (D048) |
| Supply current | the supply | 5 to 8 mA with IN low, 11 to 14 mA with IN high | about 0.1 mA per gate that is on, the oscillator's 1k driver half the time, the LED and the 3.3k row when IN is up |

A reading outside its band means the cell in copper is not the cell the
whole machine was simulated with. Stop there: the second order waits until
the model in `lib/2N7000.lib` is corrected to the measurement and the
machine gate (docs/cards.md step 9) is rerun on it. A low ring peak or a
blind RING loop is not a failure (read RING0); the reset pulse at a clock
edge is not a failure.

## 2. Hub

No logic. Check with the meter, nothing connected: no short between +5V
and ground on either header; every one of the 64 pins of the top header
beeps to the same pin of the bottom header; the four BUS pull-ups read 10k
to +5V; the eight M pull-downs read 220k to ground; the red banana
socket beeps to the fuse's first pad and, through the fuse, to header
pin 1; the black one to header pin 3. Plug the bench supply's leads into
the sockets (red +5V, black GND; 5.0 V, limit 300 mA): the power LED
lights, the current is under 6 mA. The sockets stand on four solder joints:
push a plug in with a finger behind the board.

The crowbar, once, before any card is on the ribbon: supply at 5.0 V, limit
at 0.5 A, nothing plugged into the hub's headers. Turn the voltage up
slowly. Somewhere between 6.3 and 7.8 V the supply drops into its current
limit and the rail reads about 0.8 V: the SCR has fired. Switch the output
off, set 5.0 V, switch on: 5 V again. If the rail follows the knob past
8 V, switch off: the zener or the SCR is in the wrong way round (the
assembly drawing has the square pads). With the machine running and the
limit at 1.5 A the supply cannot lift the rail above 7.5 V and the crowbar
may not fire at all: that is the limit doing the same job. Keep the limit
at 1.5 A; with it at 3 A or more a fired SCR overheats unless it has a
clip-on heatsink. Crimp the first ribbon: a short piece with three sockets for the
bench, then the long ones for the column.

Every ribbon, before it sees power: with nothing plugged into it but the
hub, beep each socket's pin 1 to the hub's pin 1 and its pin 64 to the
hub's pin 64, and check that pin 1 does not beep to pin 3. A socket
crimped the other way round, or a ribbon turned over at a fold, puts +5V
on a ground pin of every card after it (pins 1, 2 and 64 are +5V; 3, 4, 5,
7 and 63 ground, `bus-header.md`).

Plugging a 64-way socket takes 60 to 100 N and a card hangs on two screws
at mid-height: hold the card from the front, behind the header, with the
other hand. The same when pulling one off.

## 3. Panel A, B, C

Plug the three onto the ribbon with the hub. Every level switch that is ON
(slid to the right, toward its name; the boards print `ON >`) puts a 1 on
its line: the LED of that line lights on card A or B, and the meter reads
5 V on the header pin. Switch off: 0 V (the 1 Meg pull-down; 10k on CLK
and RST, D053). Card B: the CLK and RST buttons each give one clean
edge per press on the header (scope or logic analyser: no bounce after the
Schmitt trigger; the rise into the ribbon's few nF takes microseconds, the
fall through the 10k about 30 us); card C's DATA switches show on the
D3..D0 LEDs of card A only while INP is on (card B's switch): that is the
input port driving the bus. PC and M LEDs follow the PC and M lines, which
nothing drives yet.

## 4. Register bit cards

One card at a time, on the ribbon with the hub and the panel. The panel's
A and B switches sit on the registers' output lines, so leave them off
and drive the bus instead: DATA switch <i> on card C with INP on puts the
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
yet: the sequencer is later). RST: all PC LEDs off. PCE on, press CLK: bit
0 lights; again: bit 1; the carry runs through the links. PCL with the
bus data switches (OPR comes from the sequencer later; for now the panel's
switches on the link ribbon's OPR lines): loads a jump target. RAI then
PCR: the return register. call.asm on the eight cards in the simulation
passed; the machine gate proves the rest.

## 7. Memory control and slot cards

Memory control on the ribbon, the 2x6 link ribbon from it along the eight
slot cards, each slot card's jumpers set to its pair (A3 A2 A1 = the
pair number 0..7 in binary, the centre pin to '1' where the bit is 1).
On the scope, probe CLKD (the top of the control card's 2.2 nF) and MPH
(the output of the NOR that reads CLK and CLKD): a pulse from each falling
edge of CLK, 60 to 350 us long (D054); the address latch and the write
happen inside it, in the middle of the tick, never at an edge. MAI with an address on the data
switches, then MI with a value: the cell LEDs of that slot show the value. Change the address, MO: the value comes
back on the bus. Fill all sixteen, read all sixteen (the testbench's
script). A slot that always reads another slot's value is a jumper on the
wrong side.

## 8. Program cards

Set a card's jumpers: P7..P4 the page, G3 G2 the word group, the centre pin
to '1' where the address bit is 1; card c holds words 4c..4c+3. Set the
switches of a short program (`sim/programs/count.asm` assembled by
`sim/emu.py` gives the words; a switch that is ON, to the right, is a 1,
bit 7 at the top). With the counter on the bus, PCE on and the CLK button:
each press moves PC by one, the card's R<n> LED shows the row, and the M
LEDs on panel C show the word. A blank word (all off) reads 0000 0000, NOP.

## 9. Clock card

RUN switch off, STEP: the panel's CLK button owns the line. RUN: the OSC
LED blinks and the CLK line runs at the pot's speed (500 Hz down to 40 Hz,
the SLOW jumper 10 Hz to 0.8 Hz); HLT high stops it a quarter of a
millisecond later, after the pulse in flight (D050). Power-on: RST high
for a tenth of a second, then low. On the scope, with the ribbon and the
cards on it (about 3 nF): CLK rises 0.5 to 3.5 V in under 10 us, RST falls
3.5 to 0.8 V in under 100 us (D053; the simulation says 6 and 45 us). RST
lets go wherever the free-running clock happens to be, so on a few
power-ups in a hundred the machine may start a step off: press RST.

With the whole machine running a program, RST on the scope at the far end
of the ribbon (its neighbour on the ribbon is BUS1# since the headers went
to the back, D062): bumps of up to half a volt each time the bus is
released are what the simulation says (0.28 to 0.43 V,
`sim/results/rst_neighbour.md`). Above 0.6 V, fit a capacitor from RST to
ground at the hub (2.2 nF halves the bump and RST then releases in 50 us
instead of 20).

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
