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

| Quantity | Simulated | Measured |
|---|---|---|
| Rise time, 1 load | | |
| Rise time, 10 loads | | |
| Fall time | | |
| Output low with 1 transistor | | |
| Output low with 3 in series | | |
| Ring oscillator frequency, 5 inverters | | |
| Supply current, all outputs low | | |

## Rules the generator enforces

1. No input is ever left floating. Unused inputs tie to GND.
2. At most 3 transistors in series.
3. Every board has a 100 nF ceramic and a 10 uF electrolytic across the supply at the header.
4. Bus lines are driven only by open-drain transistors and pulled up only on the hub.
