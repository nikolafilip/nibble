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
- An LED indicator is a transistor with an LED and a 1.5k resistor in its drain. It costs nothing to drive because a gate draws no current.

## Why this works

A MOSFET gate is a capacitor, not a resistor. It draws no steady current, so
one output can drive as many inputs as you like; the only cost is that the
pull-up has to charge all those gates, which makes the rising edge slower.
Output high is the full 5 V, output low is a few tens of millivolts. The
2N7000 turns on somewhere between 0.8 V and 3 V depending on the individual
part, and both of those are comfortably between the two output levels.

## Numbers to confirm on the coupon

Simulated with the VDMOS 2N7000 model in `lib/2N7000.lib` (`sim/out/cell.cir`), 47k pull-up, 5 V.

| Quantity | Simulated | Measured |
|---|---|---|
| Delay low-to-high, 1 load | 4 µs | |
| Delay low-to-high, 10 loads | 28 µs | |
| 10 %–90 % rise, 10 loads | 68 µs | |
| Delay high-to-low | 5 ns | |
| Output low, 1 transistor | under 1 mV | |
| Output low, 3 in series | 1 mV | |
| Ring oscillator, 5 inverters | 12 µs period (80 kHz) | |
| Supply current per gate that is on | 0.1 mA | |

With 22k the delays halve and the current doubles; with 100k the reverse. 47k
is the default; the generator can pick 22k or 10k for a heavily loaded net.
Board 01 settles in 73 µs worst case (slow threshold corner), so a clock of a
few hundred hertz is safe and a few hertz is watchable.

## Rules the generator enforces

1. No input is ever left floating. Unused inputs tie to GND.
2. At most 3 transistors in series.
3. Every board has a 100 nF ceramic and a 10 uF electrolytic across the supply at the header.
4. Bus lines are driven only by open-drain transistors and pulled up only on the hub.
