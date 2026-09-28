# Coupon: what the bench should read

From `sim/tb_coupon.py kicad` on the card's netlist, 5.00 V, a x10 probe (15 pF) on the loop being read and 3.3 nF clipped on DRV;
LO, TYP, HI are the transistor model's threshold corners (0.8, 2.0, 3.0 V, `lib/2N7000.lib`), MIX gives every transistor its own.
The band is the lowest to the highest value over all the runs; a bench reading outside it means the cell in copper is not the modelled one (docs/bring-up.md section 1).

| Measurement | Unit | TYP | LO | HI | MIX1 | MIX2 | MIX3 | Band |
|---|---|---|---|---|---|---|---|---|
| Ring period at RING (buffered) | us | 14.6 | 5.9 | 23.6 | 11.2 | 7.2 | 17.3 | 5.9 to 23.6 |
| Ring period at RING0 (the ring node) | us | 14.6 | 5.9 | 23.6 | 11.2 | 7.2 | 17.3 | 5.9 to 23.6 |
| RING0 peak (the ring's swing) | V | 3.2 | 1.6 | 4.1 | 3.0 | 2.0 | 3.2 | 1.6 to 4.1 |
| Rise 10-90 %, fan-out 1 (FO1) | us | 10.70 | 10.31 | 11.55 | 10.69 | 10.70 | 10.31 | 10.31 to 11.55 |
| Rise 10-90 %, fan-out 10 (FO10) | us | 70.08 | 66.84 | 77.22 | 70.28 | 73.77 | 72.36 | 66.84 to 77.22 |
| Fall 90-10 %, fan-out 1 (FO1) | us | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 to 0.06 |
| Fall 90-10 %, fan-out 10 (FO10) | us | 1.18 | 0.62 | 2.22 | 1.18 | 1.18 | 0.61 | 0.61 to 2.22 |
| Delay IN edge to FO1 half way (rising) | us | 6.34 | 5.89 | 4.75 | 6.34 | 6.41 | 5.96 | 4.75 to 6.41 |
| Delay IN edge to FO10 half way (rising) | us | 28.71 | 24.93 | 13.74 | 24.34 | 19.04 | 21.62 | 13.74 to 28.71 |
| NAND low, N1 N2 N3 = 111 | V | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 to 0.001 |
| NOR low, N1 N2 N3 = 111 | V | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 to 0.000 |
| BUS low, IN high (10k pull-up) | V | 0.001 | 0.001 | 0.002 | 0.001 | 0.001 | 0.001 | 0.001 to 0.002 |
| X lower trip point | V | 1.97 | 0.82 | 2.92 | 3.01 | 2.97 | 0.77 | 0.77 to 3.01 |
| X upper trip point | V | 2.39 | 1.23 | 3.34 | 3.43 | 3.39 | 1.19 | 1.19 to 3.43 |
| OSC period | ms | 1.64 | 2.48 | 1.72 | 1.79 | 1.77 | 2.55 | 1.64 to 2.55 |
| OSC duty (high fraction) |  | 0.55 | 0.79 | 0.36 | 0.34 | 0.35 | 0.80 | 0.34 to 0.80 |
| Q period | ms | 3.28 | 4.95 | 3.44 | 3.58 | 3.53 | 5.11 | 3.28 to 5.11 |
| Q edges per OSC rising edge |  | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 to 1.00 |
| Q while RST is high, away from clock edges | V | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 to 0.00 |
| Q pulse at a clock edge while RST is high: peak | V | 0.00 | 0.00 | 0.00 | 0.00 | 4.13 | 0.00 | 0.00 to 4.13 |
| That pulse: width above 1 V | us | 0 | 0 | 0 | 0 | 11 | 0 | 0 to 11 |
| DRV high (3.3 nF, 10k) | V | 4.02 | 4.02 | 4.02 | 4.02 | 4.02 | 4.02 | 4.02 to 4.02 |
| DRV rise 0.5 to 3.5 V | us | 6.6 | 6.6 | 6.6 | 6.6 | 6.6 | 6.6 | 6.6 to 6.6 |
| DRV fall 3.5 to 0.8 V | us | 49 | 49 | 49 | 49 | 49 | 49 | 49 to 49 |
| VTO | V | 2.05 | 0.88 | 3.02 | 3.02 | 2.05 | 0.88 | 0.88 to 3.02 |
| ROM high, IN low | V | 4.52 | 4.52 | 4.52 | 4.52 | 4.52 | 4.52 | 4.52 to 4.52 |
| ROM low, IN high | V | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 to 0.000 |
| Supply current, IN low (meter average) | mA | 5.7 | 7.4 | 4.7 | 4.6 | 4.8 | 7.5 | 4.6 to 7.5 |
| Supply current, IN high (the LED, the row) | mA | 12.3 | 13.8 | 10.7 | 10.9 | 11.2 | 13.6 | 10.7 to 13.8 |
| Supply current, peak | mA | 14.9 | 15.4 | 14.4 | 14.7 | 14.9 | 15.1 | 14.4 to 15.4 |
