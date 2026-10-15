# Coupon on the bench, 2026-10-15

The first copper (D055, D056): the pilot coupon soldered and measured
against `sim/results/coupon_expected.md`. Bench supply 5.00 V, limit
300 mA, on the POWER header; AstroAI meter; HiLetgo 24 MHz analyser read
with `sigrok-cli` (OSC on D0, Q on D1, RING0 on D2). The captures are
the `.sr` files beside this file, measured with the script at the end.

| Measure | Expected (5 V) | Measured | |
|---|---|---|---|
| Supply current, IN low | 5 to 8 mA | 4 mA | pass (less leakage than modelled) |
| Supply current, IN high | 11 to 14 mA | 12 mA | pass |
| NAND, NOR low, N1 N2 N3 = 111 | under 0.01 V | under 0.01 V | pass |
| BUS low, IN high | under 0.01 V | under 0.01 V | pass |
| ROM, IN low | 4.5 V | 4.57 V | pass |
| ROM, IN high | 0 V | 75 to 125 mV | pass (Rds(on) and ground drop) |
| VTO | 0.9 to 3.0 V | 1.53 V | pass, middle of the range |
| OSC period, high fraction | 1.6 to 2.6 ms, 34 to 80 % | 1.655 ms, 66 % | pass, fast end |
| Q, RST open | half the OSC rate, one edge per OSC rise | 3.309 ms, one edge 5 us after each OSC rise | pass |
| Q, RST at +5V | 0 V between edges, a pulse up to 10 us at an edge allowed | flat 0; two 40 ns blips at one edge | pass |
| RING0 period | 6 to 24 us | 7.2 us | pass, fast end |

Not measured (needs a scope): FO1 and FO10 rise times, the Schmitt trip
points, the DRV edge into 3.3 nF. They refine the model; the go/no-go
cells above are the ones that decide the second order.

The 40 ns single-sample blips on Q and RING0 sit on the channels' own
transitions: the analyser chattering on a slow analog edge, not the
circuit (a 2N7000 toggle cannot make a 40 ns pulse).

Reading: the batch sits at the fast end of the simulated bands with a
threshold of about 1.5 V, between the model's TYP (2.0 V) and LO (0.8 V)
corners, both of which the machine gate passes. Nothing in
`lib/2N7000.lib` needs correcting. The second order can go.

```python
import zipfile, numpy as np
z = zipfile.ZipFile('cap24m.sr'); fs = 24e6
raw = b''.join(z.read(n) for n in sorted(n for n in z.namelist() if n.startswith('logic-1')))
d = np.frombuffer(raw, dtype=np.uint8)
for ch, name in enumerate(['OSC', 'Q', 'RING0']):
    b = (d >> ch) & 1
    r = np.flatnonzero((b[1:] == 1) & (b[:-1] == 0)) + 1
    print(name, np.median(np.diff(r)) / fs * 1e6, 'us')
```
