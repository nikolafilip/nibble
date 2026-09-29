# Reset-release sweep: fib, 12 ticks, the whole card deck

Generated 2026-09-29 04:04 by sim/sweep_por.py. Boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc. VDD 5 V.
The release is pulled to about 20 ms with POR_V0 (see the docstring); "edge" is where the nearest clock edge fell against the release as the scorer measured it,
positive after. The cards let go of their resets over the 45 us after the release, so an edge at 0 to +45 us is the straddle.

## TYP: calibration release 17.347 ms, edge +615 us, period 1.64 ms (pass); second calibration edge -158 us (pass), an asked shift arrives x1.0573

| wanted us | POR_V0 V | release ms | edge us | period ms | result | time |
|---|---|---|---|---|---|---|
| -40 | 1.8780 | 16.361 | -39 | 1.64 | pass: 12 ticks, 0 mismatches | 1078 s |
| -30 | 1.8781 | 16.352 | -29 | 1.64 | pass: 12 ticks, 0 mismatches | 1088 s |
| -20 | 1.8783 | 16.342 | -20 | 1.64 | pass: 12 ticks, 0 mismatches | 1893 s |
| -10 | 1.8784 | 16.332 | -9 | 1.64 | pass: 12 ticks, 0 mismatches | 1889 s |
| +0 | 1.8785 | 16.322 | +1 | 1.64 | pass: 12 ticks, 0 mismatches | 1579 s |
| +10 | 1.8787 | 16.311 | +11 | 1.64 | pass: 12 ticks, 0 mismatches | 1600 s |
| +20 | 1.8788 | 16.302 | +21 | 1.64 | pass: 12 ticks, 0 mismatches | 1549 s |
| +30 | 1.8789 | 16.291 | +31 | 1.64 | pass: 12 ticks, 0 mismatches | 1534 s |
| +40 | 1.8791 | 16.282 | +41 | 1.64 | pass: 12 ticks, 0 mismatches | 1910 s |
| +50 | 1.8792 | 16.271 | +51 | 1.64 | pass: 12 ticks, 0 mismatches | 1908 s |
| +60 | 1.8793 | 16.262 | +61 | 1.64 | pass: 12 ticks, 0 mismatches | 1512 s |
| +70 | 1.8795 | 16.252 | +71 | 1.64 | pass: 12 ticks, 0 mismatches | 1503 s |
| +80 | 1.8796 | 16.241 | +81 | 1.64 | pass: 12 ticks, 0 mismatches | 928 s |

## MIX1: calibration release 19.928 ms, edge -1159 us, period 2.48 ms (pass); second calibration edge +91 us (pass), an asked shift arrives x1.0081

| wanted us | POR_V0 V | release ms | edge us | period ms | result | time |
|---|---|---|---|---|---|---|
| -40 | 0.4228 | 18.81 | -40 | 2.48 | pass: 12 ticks, 0 mismatches | 1060 s |
| -30 | 0.4230 | 18.8 | -31 | 2.48 | pass: 12 ticks, 0 mismatches | 1009 s |
| -20 | 0.4232 | 18.79 | -21 | 2.48 | pass: 12 ticks, 0 mismatches | 979 s |
| -10 | 0.4234 | 18.78 | -11 | 2.48 | pass: 12 ticks, 0 mismatches | 925 s |
| +0 | 0.4236 | 18.77 | +0 | 2.48 | pass: 12 ticks, 0 mismatches | 928 s |
| +10 | 0.4238 | 18.759 | +9 | 2.48 | FAIL: 12 ticks, 20 mismatches | 900 s |
| +20 | 0.4240 | 18.749 | +20 | 2.48 | pass: 12 ticks, 0 mismatches | 938 s |
| +30 | 0.4242 | 18.739 | +31 | 2.48 | pass: 12 ticks, 0 mismatches | 935 s |
| +40 | 0.4244 | 18.729 | +40 | 2.48 | pass: 12 ticks, 0 mismatches | 932 s |
| +50 | 0.4247 | 18.719 | +50 | 2.48 | pass: 12 ticks, 0 mismatches | 930 s |
| +60 | 0.4249 | 18.709 | +60 | 2.48 | pass: 12 ticks, 0 mismatches | 927 s |
| +70 | 0.4251 | 18.699 | +70 | 2.48 | pass: 12 ticks, 0 mismatches | 928 s |
| +80 | 0.4253 | 18.689 | +80 | 2.48 | pass: 12 ticks, 0 mismatches | 931 s |

## MIX2: calibration release 4.808 ms, edge -927 us, period 2.476 ms (pass); second calibration edge +534 us (pass), an asked shift arrives x1.1801

| wanted us | POR_V0 V | release ms | edge us | period ms | result | time |
|---|---|---|---|---|---|---|
| -40 | 3.1335 | 3.921 | -40 | 2.476 | pass: 12 ticks, 0 mismatches | 930 s |
| -30 | 3.1336 | 3.911 | -31 | 2.477 | pass: 12 ticks, 0 mismatches | 932 s |
| -20 | 3.1337 | 3.901 | -20 | 2.477 | pass: 12 ticks, 0 mismatches | 929 s |
| -10 | 3.1337 | 3.891 | -10 | 2.477 | pass: 12 ticks, 0 mismatches | 934 s |
| +0 | 3.1338 | 3.881 | -1 | 2.477 | pass: 12 ticks, 0 mismatches | 939 s |
| +10 | 3.1339 | 3.871 | +10 | 2.477 | FAIL: 12 ticks, 64 mismatches | 968 s |
| +20 | 3.1340 | 3.861 | +19 | 2.476 | pass: 12 ticks, 0 mismatches | 944 s |
| +30 | 3.1340 | 3.851 | +29 | 2.476 | pass: 12 ticks, 0 mismatches | 944 s |
| +40 | 3.1341 | 3.84 | +40 | 2.476 | pass: 12 ticks, 0 mismatches | 936 s |
| +50 | 3.1342 | 3.83 | +50 | 2.477 | pass: 12 ticks, 0 mismatches | 937 s |
| +60 | 3.1342 | 3.821 | +60 | 2.476 | pass: 12 ticks, 0 mismatches | 947 s |
| +70 | 3.1343 | 3.811 | +70 | 2.477 | pass: 12 ticks, 0 mismatches | 946 s |
| +80 | 3.1344 | 3.801 | +80 | 2.476 | pass: 12 ticks, 0 mismatches | 874 s |

37 of 39 sweep runs pass; calibrations 6 of 6.
