# The reset release against the clock: the hold-off on the clock card alone

Generated 2026-09-29 10:48 by sim/tb_reset_release.py. 24 cases, 504 releases.

The two parts on trial: 100 ohm and a 2N7000 from the timing node X to ground, gate on RST. They are in the deck, not on the card yet.
Each case: power-on, then 20 presses of the panel's RST button (8 ms each), walked across the clock period; the same without the two parts.

| corner | speed | period ms | first edge after the release ms | CLK while held V | RST up to CLK down us | first high / usual | first period / usual | phases of 20 | period without ms | without: nearest edge us | without: releases with an edge inside 1 ms | result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TYP | the pot at its least, 47 nF | 1.64 | 3.174 to 3.175 | 0.01 | 8 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 1.638 | 45 | 14 of 21 | pass |
| LO | the pot at its least, 47 nF | 2.476 | 1.402 to 1.402 | 0.01 | 2 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 2.474 | 3 | 13 of 21 | pass |
| HI | the pot at its least, 47 nF | 1.719 | 5.395 to 5.397 | 0.02 | 17 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 1.718 | 43 | 12 of 21 | pass |
| MIX1 | the pot at its least, 47 nF | 1.629 | 3.116 to 3.116 | 0.01 | 9 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 1.628 | 31 | 14 of 21 | pass |
| MIX2 | the pot at its least, 47 nF | 2.552 | 1.304 to 1.304 | 0.01 | 11 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 2.55 | 1 | 8 of 21 | pass |
| MIX3 | the pot at its least, 47 nF | 2.475 | 1.376 to 1.376 | 0.01 | 8 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 2.474 | 41 | 6 of 21 | pass |
| TYP | the pot at 1 M, 47 nF | 17.45 | 33.67 to 33.69 | 0.01 | 8 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 17.43 | 15 | 1 of 21 | pass |
| LO | the pot at 1 M, 47 nF | 26.69 | 14.73 to 14.74 | 0.01 | 2 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 26.68 | 50 | 0 of 21 | pass |
| HI | the pot at 1 M, 47 nF | 18.09 | 57.16 to 57.19 | 0.02 | 17 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 18.08 | 56 | 0 of 21 | pass |
| MIX1 | the pot at 1 M, 47 nF | 17.3 | 32.76 to 32.78 | 0.01 | 9 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 17.29 | 226 | 0 of 21 | pass |
| MIX2 | the pot at 1 M, 47 nF | 27.52 | 14.06 to 14.06 | 0.01 | 11 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 27.52 | 245 | 0 of 21 | pass |
| MIX3 | the pot at 1 M, 47 nF | 26.68 | 14.69 to 14.72 | 0.01 | 8 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 26.64 | 802 | 0 of 21 | pass |
| TYP | the pot at its least, SLOW jumper on (2.2 uF more) | 77.03 | 152.1 to 152.2 | 0.01 | 51 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 77.01 | 259 | 0 of 21 | pass |
| LO | the pot at its least, SLOW jumper on (2.2 uF more) | 116.7 | 66.3 to 66.34 | 0.01 | 95 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 116.8 | 377 | 1 of 21 | pass |
| HI | the pot at its least, SLOW jumper on (2.2 uF more) | 80.5 | 258.4 to 258.5 | 0.02 | 47 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 80.49 | 6 | 0 of 21 | pass |
| MIX1 | the pot at its least, SLOW jumper on (2.2 uF more) | 76.31 | 147.9 to 148 | 0.01 | 50 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 76.32 | 705 | 0 of 21 | pass |
| MIX2 | the pot at its least, SLOW jumper on (2.2 uF more) | 120.3 | 63.33 to 63.37 | 0.01 | 111 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 120.3 | 39 | 0 of 21 | pass |
| MIX3 | the pot at its least, SLOW jumper on (2.2 uF more) | 116.7 | 66.23 to 66.32 | 0.01 | 101 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 116.7 | 2442 | 0 of 21 | pass |
| TYP | the pot at 1 M, SLOW jumper on | 831.1 | 1608 to 1608 | 0.01 | 51 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 831.1 | 1183 | 0 of 21 | pass |
| LO | the pot at 1 M, SLOW jumper on | 1272 | 701.9 to 702 | 0.01 | 95 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 1272 | 7448 | 0 of 21 | pass |
| HI | the pot at 1 M, SLOW jumper on | 861.5 | 2729 to 2729 | 0.02 | 47 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 861.5 | 8411 | 0 of 21 | pass |
| MIX1 | the pot at 1 M, SLOW jumper on | 823.6 | 1563 to 1563 | 0.01 | 50 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 823.6 | 8987 | 0 of 21 | pass |
| MIX2 | the pot at 1 M, SLOW jumper on | 1311 | 671.1 to 671.1 | 0.01 | 111 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 1311 | 14648 | 0 of 21 | pass |
| MIX3 | the pot at 1 M, SLOW jumper on | 1272 | 702 to 702 | 0.01 | 101 | 1.00 to 1.00 | 1.00 to 1.00 | 20 | 1273 | 2454 | 0 of 21 | pass |

24 of 24 cases pass.
