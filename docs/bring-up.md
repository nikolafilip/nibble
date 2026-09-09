# Bring-up: fab order 1

Four boards: gate coupon, bus hub, front panel, ALU. Solder in that order.
Everything below is a step you can film.

## Tools you need before the boards arrive

- Bench supply with current limit (set 5.0 V, limit 300 mA for the first power-on of each board).
- Multimeter.
- 8-channel USB logic analyser (any Saleae-compatible clone) and Sigrok/PulseView, or a scope.
- Temperature-controlled iron, 0.6 mm solder, flux, brass wool, wick.
- Anti-static wrist strap: 2N7000 gates are static-sensitive until soldered.
- Flush cutters, tweezers, a board holder.

## 1. Coupon (26 transistors, about 1 hour of soldering)

Solder resistors first (all flat against the board, they are vertical-mount), then test loops, then LEDs, then transistors last with the strap on. Check for solder bridges between the three TO-92 pads before power.

Power on J1 through the bench supply. Expected current: under 3 mA. If it is more than 20 mA, power off and look for a bridge.

| Measure | Where | Expected (simulated) | Write it in `gate-cell.md` |
|---|---|---|---|
| Ring period | TP_RING | about 14 µs (70 kHz) | gate delay = period / 10 |
| Rise time, 1 load | TP_FO1, drive IN low-to-high from J2 | 4 µs to 2.5 V | |
| Rise time, 10 loads | TP_FO10 | 28 µs to 2.5 V | |
| Fall time | TP_FO1 | well under 1 µs | |
| NAND output low | TP_NAND with N1=N2=N3 tied to +5 V | under 10 mV | |
| NOR output low | TP_NOR with any input high | under 10 mV | |
| Bus line low | TP_BUS with IN high | under 10 mV | |
| Supply current | bench supply, IN low | about 0.1 mA per gate that is on | |

The gate delay sets the clock: keep the clock period at least 100 times the fan-out-10 rise time.

If the ring does not oscillate, or the low levels are above 100 mV, stop and post it: the cell is wrong and every other board inherits it.

## 2. Hub (no transistors)

Solder the headers, the USB-B, the fuse, the LED, the capacitors, the four pull-ups. Plug in USB: the power LED lights, current under 5 mA. Check 5 V between pins 1 and 3 of every slot. Check that every one of the 42 signal pins reads the same on slot 1 and slot 8 with the meter's continuity beeper (there are 42 of them, this is the boring video).

## 3. Front panel (50 transistors, 42 LEDs)

Solder order: resistors (there are 88), diodes, capacitors, switches, buttons, LEDs (long leg is the anode, the square pad), transistors last.

Plug the panel alone into the hub. All LEDs off. Now:

- Flip A0 on: the A0 LED lights. Same for every level switch, one at a time. 22 switches, 22 LEDs.
- Close DATA switch D0: the D0 LED lights (the bus line went low, the inverter turned it into a 1).
- Press CLK: the CLK LED lights while pressed, goes out about 0.15 s after release. Same for RST.
- With the logic analyser on the hub's CLK test loop: one press gives exactly one rising edge. Press it fifty times. Fifty edges.

## 4. ALU (137 transistors)

Solder order: resistors, LEDs, capacitors, header, transistors. Before soldering the transistors, power it and check that no pull-up is shorted (current under 1 mA with the resistors only).

Plug hub + panel + ALU together. Set EO on (the ALU drives the bus). Everything else off.

| A switches | B switches | SUB | Expected D3..D0 | CF | ZF |
|---|---|---|---|---|---|
| 0000 | 0000 | off | 0000 | off | on |
| 0011 (3) | 0100 (4) | off | 0111 (7) | off | off |
| 1111 (15) | 0001 (1) | off | 0000 | on | on |
| 0111 (7) | 0101 (5) | on | 0010 (2) | on | off |
| 0110 (6) | 0110 (6) | on | 0000 | on | on |
| 0010 (2) | 0101 (5) | on | 1101 (13, that is -3) | off | off |

Rows 4 and 5 are the two calculations the hand-made calculator got wrong. Film those.

Then flip EO off: the D LEDs go out (the ALU has let go of the bus) while the ALU's own S LEDs still show the result.

The full check is all 512 combinations; the simulation did them, you do not have to. A dozen is plenty for the video. If any row is wrong, note which output bit and which inputs, and compare with `boards/01-alu/sim_results/`: the schematic tells you which cell to probe, and the cell tiles on the board are in the same order as the schematic.
