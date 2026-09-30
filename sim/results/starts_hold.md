# The machine's starts with the hold-off: fib, 12 ticks, the whole card deck

Generated 2026-09-29 20:07 by sim/starts_hold.py. Boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc. The two parts of D064 are in the deck (`HOLD=1`), not on the card.
A run passes when the emulator agrees on all 12 ticks and the first clock edge came 1 ms or more after RST fell under 0.7 VDD.

## The starts of the reset sweep again, each at the POR_V0 it had: 46 of 46

| corner | POR_V0 V | release ms | first edge after it us | period ms | result | without the hold-off | time |
|---|---|---|---|---|---|---|---|
| TYP | 1.864759 | 17.347 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +615 us | 803 s |
| MIX1 | 0.399645 | 19.929 | +1421 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge -1159 us | 817 s |
| MIX2 | 3.127134 | 4.808 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge -927 us | 915 s |
| TYP | 1.876423 | 16.48 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge -158 us | 809 s |
| MIX1 | 0.425502 | 18.678 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +91 us | 831 s |
| MIX2 | 3.137644 | 3.347 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +534 us | 931 s |
| TYP | 1.878007 | 16.362 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge -39 us | 803 s |
| TYP | 1.878141 | 16.352 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge -29 us | 798 s |
| TYP | 1.878276 | 16.341 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge -20 us | 807 s |
| TYP | 1.878410 | 16.332 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge -9 us | 804 s |
| TYP | 1.878544 | 16.322 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +1 us | 807 s |
| TYP | 1.878678 | 16.312 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +11 us | 807 s |
| TYP | 1.878812 | 16.302 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +21 us | 808 s |
| TYP | 1.878947 | 16.291 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +31 us | 806 s |
| TYP | 1.879081 | 16.282 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +41 us | 804 s |
| TYP | 1.879215 | 16.271 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +51 us | 808 s |
| TYP | 1.879349 | 16.262 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +61 us | 807 s |
| TYP | 1.879483 | 16.252 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +71 us | 810 s |
| TYP | 1.879617 | 16.242 | +3210 | 1.641 | pass: 12 ticks, 0 mismatches | pass, edge +81 us | 811 s |
| MIX1 | 0.422799 | 18.809 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge -40 us | 824 s |
| MIX1 | 0.423005 | 18.799 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge -31 us | 832 s |
| MIX1 | 0.423212 | 18.789 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge -21 us | 833 s |
| MIX1 | 0.423418 | 18.779 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge -11 us | 834 s |
| MIX1 | 0.423624 | 18.769 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +0 us | 834 s |
| MIX1 | 0.423831 | 18.759 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | FAIL, edge +9 us | 833 s |
| MIX1 | 0.424037 | 18.749 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +20 us | 833 s |
| MIX1 | 0.424243 | 18.739 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +31 us | 835 s |
| MIX1 | 0.424450 | 18.73 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +40 us | 831 s |
| MIX1 | 0.424656 | 18.719 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +50 us | 832 s |
| MIX1 | 0.424862 | 18.709 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +60 us | 837 s |
| MIX1 | 0.425069 | 18.699 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +70 us | 834 s |
| MIX1 | 0.425275 | 18.689 | +1420 | 2.482 | pass: 12 ticks, 0 mismatches | pass, edge +80 us | 835 s |
| MIX2 | 3.133522 | 3.921 | +1404 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge -40 us | 935 s |
| MIX2 | 3.133594 | 3.911 | +1404 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge -31 us | 936 s |
| MIX2 | 3.133666 | 3.9 | +1404 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge -20 us | 933 s |
| MIX2 | 3.133738 | 3.89 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge -10 us | 928 s |
| MIX2 | 3.133809 | 3.881 | +1404 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge -1 us | 931 s |
| MIX2 | 3.133881 | 3.871 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | FAIL, edge +10 us | 933 s |
| MIX2 | 3.133953 | 3.861 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +19 us | 933 s |
| MIX2 | 3.134025 | 3.851 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +29 us | 931 s |
| MIX2 | 3.134097 | 3.84 | +1404 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +40 us | 934 s |
| MIX2 | 3.134169 | 3.83 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +50 us | 931 s |
| MIX2 | 3.134241 | 3.821 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +60 us | 935 s |
| MIX2 | 3.134312 | 3.811 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +70 us | 935 s |
| MIX2 | 3.134384 | 3.801 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | pass, edge +80 us | 942 s |
| MIX2 | 3.003761 | 21.207 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | FAIL, edge +9 us | 975 s |

## Other corners, the reset left to its own length: 4 of 4

| corner | POR_V0 V | release ms | first edge after it us | period ms | result | time |
|---|---|---|---|---|---|---|
| LO | 0 | 38.326 | +1418 | 2.476 | pass: 12 ticks, 0 mismatches | 473 s |
| HI | 0 | 236.035 | +5440 | 1.72 | pass: 12 ticks, 0 mismatches | 1232 s |
| MIX3 | 0 | 35.608 | +5735 | 1.788 | pass: 12 ticks, 0 mismatches | 822 s |
| MIX4 | 0 | 120.492 | +5597 | 1.765 | pass: 12 ticks, 0 mismatches | 1025 s |

## The panel's RST button pressed while the machine runs: 12 of 12

| corner | finger down, up s | release ms | first edge after it us | period ms | result | time |
|---|---|---|---|---|---|---|
| TYP | 0.035000, 0.055000 | 307.443 | +3212 | 1.64 | pass: 12 ticks, 0 mismatches | 1536 s |
| TYP | 0.035410, 0.055410 | 307.853 | +3212 | 1.641 | pass: 12 ticks, 0 mismatches | 1549 s |
| TYP | 0.035820, 0.055820 | 308.263 | +3212 | 1.641 | pass: 12 ticks, 0 mismatches | 1554 s |
| TYP | 0.036230, 0.056230 | 308.673 | +3212 | 1.641 | pass: 12 ticks, 0 mismatches | 1556 s |
| MIX1 | 0.035000, 0.055000 | 302.889 | +1422 | 2.482 | pass: 12 ticks, 0 mismatches | 1669 s |
| MIX1 | 0.035620, 0.055620 | 303.509 | +1422 | 2.482 | pass: 12 ticks, 0 mismatches | 1684 s |
| MIX1 | 0.036240, 0.056240 | 304.129 | +1422 | 2.482 | pass: 12 ticks, 0 mismatches | 1680 s |
| MIX1 | 0.036860, 0.056860 | 304.749 | +1422 | 2.482 | pass: 12 ticks, 0 mismatches | 1679 s |
| MIX2 | 0.035000, 0.055000 | 312.728 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | 1750 s |
| MIX2 | 0.035619, 0.055619 | 313.347 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | 1776 s |
| MIX2 | 0.036238, 0.056238 | 313.966 | +1405 | 2.478 | pass: 12 ticks, 0 mismatches | 1780 s |
| MIX2 | 0.036857, 0.056857 | 314.585 | +1406 | 2.478 | pass: 12 ticks, 0 mismatches | 1696 s |

62 of 62 starts pass.
