# Fab order 1: what to buy

Four boards, all 2-layer, 1.6 mm FR4, HASL is fine (hand soldering). Sizes:

| Board | Size (mm) | Parts | Solder joints (approx.) |
|---|---|---|---|
| Coupon | 112 × 94 | 65 | 160 |
| Hub | 130 × 98 | 28 | 460 (the headers) |
| Front panel | 150 × 222 | 229 | 560 |
| ALU | 126 × 210 | 228 | 640 |

Gerbers come from `sim/pcb.py` (`fab/` under each board). Order 5 of each; the
minimum quantity at most fabs is 5 anyway and you will want spares of the coupon.

## Parts (totals for one set, buy with margin)

| Part | Qty | Buy | Notes |
|---|---|---|---|
| 2N7000, TO-92 | 213 | 500 | Bend the leads to 2.54 mm pitch (wide footprint). Onsemi or Diodes Inc.; keep them in the anti-static bag until soldering |
| 47k, 1/4 W axial | 100 | 200 | pull-ups |
| 1k | 50 | 100 | LED series |
| 1 Meg | 44 | 100 | panel pull-downs |
| 10k | 31 | 100 | panel switch series, hub bus pull-ups, debounce |
| 220k, 100k | 2 each | 10 each | debounce |
| LED 3 mm red | 50 | 100 | any 2 mA-bright type; one colour for now |
| 100 nF ceramic disc, 2.5 mm pitch | 4 | 20 | |
| 10 µF and 1 µF electrolytic, 5 mm, 2 mm pitch | 3 + 2 | 10 each | |
| 100 µF electrolytic, 5 mm | 1 | 5 | hub bulk |
| 1N4148 | 2 | 20 | |
| 2×25 IDC box header, 2.54 mm | 10 | 12 | 8 on the hub, one per board |
| 50-way ribbon cable with 2×25 IDC sockets both ends, 30 cm | 3 | 4 | one per board that plugs into the hub |
| DIP switch, 8 position | 3 | 4 | |
| DIP switch, 4 position | 1 | 2 | |
| Tactile button 6 mm | 2 | 10 | |
| USB-B receptacle, through-hole, horizontal | 1 | 2 | |
| Polyfuse 750 mA hold, radial | 1 | 5 | Bel 0ZRE0075FF or similar |
| Test loop, 2.5 mm | 12 | 20 | or bare wire loops |
| Pin header 1×2, 1×4 | 1 each | strip | coupon |
| M3 standoffs and screws | 14 holes | a kit | |

Everything is through-hole. Rough cost: boards 40 to 70 USD including shipping,
parts about 60 USD, cables and headers about 20 USD.

## Before pressing order

1. `sim/pcb.py` reports zero DRC errors and zero unconnected for every board.
2. The exhaustive ALU simulation on the export (`boards/01-alu/sim_results/`) is current for the committed schematic.
3. Look at the renders in each `fab/` folder for 30 seconds each: header on the edge, pin 1 marked, LEDs on the visible side.
4. Nikola's gate: `docs/bring-up.md` read once, so the test plan is known before the boards exist.
