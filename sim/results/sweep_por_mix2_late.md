# Reset-release sweep: fib, 12 ticks, the whole card deck

Generated 2026-09-29 06:42 by sim/sweep_por.py. Boards aluc,hubc,regc,seq,ctrc,memc,progc,pnl,clkc. VDD 5 V.
The release is pulled to about 35 ms with POR_V0 (see the docstring); "edge" is where the nearest clock edge fell against the release as the scorer measured it,
positive after. The cards let go of their resets over the 45 us after the release, so an edge at 0 to +45 us is the straddle.

## MIX2: calibration release 22.325 ms, edge -1111 us, period 2.476 ms (pass); second calibration edge +327 us (pass), an asked shift arrives x1.1616

| wanted us | POR_V0 V | release ms | edge us | period ms | result | time |
|---|---|---|---|---|---|---|
| -40 | 3.0034 | 21.257 | -41 | 2.477 | pass: 12 ticks, 0 mismatches | 1078 s |
| -30 | 3.0034 | 21.247 | -31 | 2.476 | pass: 12 ticks, 0 mismatches | 1076 s |
| -20 | 3.0035 | 21.237 | -21 | 2.477 | pass: 12 ticks, 0 mismatches | 1076 s |
| -10 | 3.0036 | 21.228 | -12 | 2.477 | pass: 12 ticks, 0 mismatches | 1080 s |
| +0 | 3.0037 | 21.218 | -2 | 2.477 | pass: 12 ticks, 0 mismatches | 1073 s |
| +10 | 3.0038 | 21.207 | +9 | 2.477 | FAIL: 12 ticks, 64 mismatches | 1108 s |
| +20 | 3.0038 | 21.197 | +20 | 2.477 | pass: 12 ticks, 0 mismatches | 1080 s |
| +30 | 3.0039 | 21.186 | +29 | 2.477 | pass: 12 ticks, 0 mismatches | 1079 s |
| +40 | 3.0040 | 21.176 | +40 | 2.477 | pass: 12 ticks, 0 mismatches | 1090 s |
| +50 | 3.0041 | 21.167 | +49 | 2.477 | pass: 12 ticks, 0 mismatches | 1087 s |
| +60 | 3.0042 | 21.157 | +59 | 2.477 | pass: 12 ticks, 0 mismatches | 1076 s |
| +70 | 3.0042 | 21.147 | +70 | 2.477 | pass: 12 ticks, 0 mismatches | 1080 s |
| +80 | 3.0043 | 21.137 | +80 | 2.477 | pass: 12 ticks, 0 mismatches | 989 s |

12 of 13 sweep runs pass; calibrations 2 of 2.
