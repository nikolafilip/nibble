# Gate cell

Everything in Nibble is built from one cell: an N-channel MOSFET (2N7000,
TO-92) pulling an output down, and one resistor pulling it up to 5 V.

```
        +5V
         |
        [R]  pull-up (47k, to be confirmed by the coupon)
         |
   out --+
         |
  in --|| 2N7000
         |
        GND
```

- One transistor with a pull-up is an inverter.
- Transistors in parallel sharing one pull-up make a NOR: any input high pulls the output low.
- Transistors in series (at most 3) sharing one pull-up make a NAND: all inputs high pull the output low.
- AND and OR are a NAND or NOR followed by an inverter.
- A bus driver is a transistor whose gate is `data AND enable`, drain on the bus line, no pull-up on the board (the hub has it).
- An LED indicator is a transistor with an LED and a 1k resistor in its drain. It costs nothing to drive because a gate draws no current.

## Why this works

A MOSFET gate is a capacitor, not a resistor. It draws no steady current, so
one output can drive as many inputs as you like; the only cost is that the
pull-up has to charge all those gates, which makes the rising edge slower.
Output high is the full 5 V, output low is a few tens of millivolts. The
2N7000 turns on somewhere between 0.8 V and 3 V depending on the individual
part, and both of those are comfortably between the two output levels.

## Numbers to confirm on the coupon

Simulated with the VDMOS 2N7000 model in `lib/2N7000.lib` on the routed
coupon card's own netlist (`sim/tb_coupon.py`, 2026-09-28), 47k pull-ups,
5 V, a x10 probe (15 pF) on the loop being read. The band is over the
model's three threshold corners (0.8, 2.0, 3.0 V) and three mixed seeds;
the full table with every column is `sim/results/coupon_expected.md`, and
what each number stands for is in `bring-up.md` section 1. The old table
here (a hand-run `out/cell.cir`) said 12 us for the ring and 68 us for the
fan-out-10 rise; those were the typical corner and stand.

| Quantity | Simulated (band over the corners) | Measured |
|---|---|---|
| Delay low-to-high, 1 load, to half way | 4.8 to 6.4 us | |
| Delay low-to-high, 10 loads, to half way | 14 to 29 us | |
| 10 %-90 % rise, 1 load | 10 to 12 us | |
| 10 %-90 % rise, 10 loads | 67 to 77 us | |
| 90 %-10 % fall, 1 load / 10 loads | 0.06 us / 0.6 to 2.2 us | |
| Output low, 1 transistor (the bus driver on 10k) | under 2 mV | |
| Output low, 3 in series | 1 mV | |
| Ring oscillator, 5 inverters, period | 6 to 24 us (14.6 us typical); the ring node swings 1.6 to 4.1 V | |
| Threshold fixture (diode-connected, 4.7k) | 0.9 to 3.0 V | |
| Schmitt trip points, hysteresis | 0.4 V, both points 0.15 and 0.55 V above the threshold | |
| Supply current per gate that is on | 0.1 mA | |

With 22k the delays halve and the current doubles; with 100k the reverse. 47k
is the default; the generator picks 22k, 10k, 4.7k, 3.3k or 1k for a heavily
loaded net (`nmos.MAX_LOADS`). The rising edge is what sets the clock: a
control line into ten gates takes about 30 us to half way, and the
machine's clock is a few hundred hertz.

## Rules the generator enforces

1. No input is ever left floating. Unused inputs tie to GND.
2. At most 3 transistors in series.
3. Every board has a 100 nF ceramic and a 10 uF electrolytic across the supply at the header.
4. Bus lines are driven only by open-drain transistors and pulled up only on the hub.

## On the PCB

Every cell is the same tile: on the cards (D045) the pull-up lying along the
row above its stack of transistors, one TO-92 per 5.08 mm row in 7.68 mm
columns; on the nine boards the pull-up standing at the top of a 10.16 mm
column. Ground and +5 V run as pre-routed rails on the back between the
columns with a short stub to each pad, joined by two trunks above the tiles,
so the autorouter only ever handles signals. The tiles on the board are in
the same order as the cells on the schematic.
