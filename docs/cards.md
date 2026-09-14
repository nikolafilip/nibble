# Cards: the machine as 100 x 100 mm boards on one ribbon

Decided 2026-09-10 evening (D042 to D045) after the first fab quotes: nine
boards of nine sizes came to about $1,300 for a machine we need one of. This
page is the plan that replaces the board list in `plan.md` step 1 to 7; the
three gates in `plan.md` still apply to every card.

## Why

JLCPCB (and every cheap fab) sells five of a design, and prices a board over
100 x 100 mm at three to six times more per square metre than the promo tier
under it ($2 to $4 for five). Cutting the boards along the bit and slot
structure the gate lists already have does two things at once: every card
lands on the cheap tier, and five-of stops being waste because a five-pack
is the four register bits plus a spare.

| | Nine boards (quoted) | Cards (estimated) |
|---|---|---|
| Boards | ~$700 for five of each | 12 designs on the promo tier plus the sequencer: $60 to $80 |
| Shipping | ~$300 in separate boxes | one package, $40 to $60 |
| Parts, cables, frame | ~$315 | ~$315 |
| **Machine** | **~$1,300** | **$400 to $450** |

## The cards

100 x 100 x 1.6 mm, 2-layer, one 2 x 32 shrouded header on the top edge
(the header is 91 mm long, so the two M3 holes sit mid-height on the left and
right edges). LEDs on the front. Below the header and its two power trunks
there is room for 11 tile columns of 82 mm (`sim/frame.py`, `ksch.DenseWriter`).

The dense tile (D045): a column is 7.68 mm wide and holds one TO-92 per 5.08 mm
row; the pull-up lies along the row above its stack, one pad on the source
column and one on the drain column. A gate of n transistors is 3.175 + 5.08 n
mm tall (8.3, 13.3, 18.4 mm for one, two, three), an LED cell 15.2 mm. The
power rails run on the back between the columns, alternately GND and +5V, each
shared by the two columns beside it (odd columns are mirrored so their sources
face the GND rail). The register bit card, 99 transistors and 54 pull-ups,
fills 10.3 of the 11 columns: about 66 mm2 per transistor all in, and
freerouting closes it in one pass with DRC zero.

| Card | Count | Designs | Transistors | Neighbour link | Notes |
|---|---|---|---|---|---|
| Register bit i: A, B, OUT flip-flops and muxes for one bit | 4 | 4 (bit baked in) | 99 (89 for the bit, 10 for the card's clock phases and hold decoders) | none | LEDs A, B, OUT |
| ALU bit i | 4 | 4 | 66 to 73 (bit 3 adds CF and ZF) | carry and zero-so-far to bit i+1 (2 x 3) | bit 3 carries CF and ZF to the bus |
| Counter bit i: PC bit and RA bit | 8 | 8 | 62 (59 for bit 7, no carry out) | count carry to bit i+1 (2 x 3); OPR i from the sequencer's link ribbon (2 x 6, chained) | |
| Memory control: MAR, write gate, PH1 | 1 | 1 | 59 | MAR0..3 and WR/RD to the slot cards (2 x 6, chained) | |
| Memory slots: two 4-bit slots with their decode | 8 | 1, slot pair by jumper | 91 | from memory control | 8 cell LEDs |
| Program: four words, page and word-group jumpers | one per four words | 1 | 41 + 32 diodes | none | 4 DIP-8, six 1x3 jumpers (PC7..2); `list` takes 6 cards, `sort` 20 |
| Panel | 3 | 3 | 28 + 20 + 32 | none | A: A/B and SUB..AB switches, their LEDs, data, CF, ZF, CLK, RST LEDs. B: OI..INP switches and LEDs, CLK and RST buttons. C: PC and M LEDs, DATA switches and input port |
| Clock | 1 | 1 | 14 + the Schmitt pair | none | the clock board's circuit on a card; HLT delayed 0.22 ms into the halt gate (D050) |
| Hub: USB, polyfuse, bus pull-ups, M pull-downs (220k, D048), test loops | 1 | 1 | 0 | none | two bus headers, top and bottom edge, one per face's ribbon; ground wired as a ring and bars, no pour |
| Coupon | 1 | 1 | 26 | | powered from the bus header; inputs on a 1x4 header, test loops |
| **Sequencer** | 1 | 1 | 592 + 87 diodes | link ribbon out to the counter cards | **the one big board, 245 x 255 mm, four layers (D051)** |

Why the bit cards are separate designs rather than one design with jumpers:
a bit is three lines (BUSi#, Ai, Bi), so selecting it is three 1 x 4 jumper
headers on a full card, and two cards jumpered alike fight over a bus line.
Four designs cost $6 more. Jumpers stay where the builder configures anyway:
memory slot pairs and program pages.

## The ribbon (D043)

One 64-way ribbon per column face, IDC sockets crimped along it every 110 mm,
one per card, all facing the same way, folded twice at each row end to run
back along the next row. Four cards per 460 mm row, seven rows per face. The
hub card joins the faces. About 6 m of ribbon and 45 sockets for the machine,
crimped in a bench vice. Pin 1 is the ribbon's red edge on every socket.

The links between neighbours (ALU carry, counter carry, memory address, the
sequencer's operand lines) are 6 cm pieces of 6-way or 12-way ribbon with
their own small IDC sockets, the same idiom as today's sequencer-counter link.

The machine deck carries 300 pF per bus line; rerun at 500 pF for margin
before the order (done, step 9: 8 of 8).

## The sequencer (D040, D041, D044, D045)

Stays one board because 45 rows and 23 columns would otherwise cross card
boundaries. Diodes standing up on a 2.54 x 5.08 mm grid make the matrix
114 x 117 mm with a pad pair at every crossing; the 600 transistors of steps,
registers, decoders, rows and column buffers around it at the card pitch on four layers (D051: on two layers the router
plateaued near 100 open nets at the card pitch and near 70 at a 10.16 mm pitch; layer 2 is a ground plane, layer 3 a
third routing layer). Two new gated rows for JNZ and JNC. 245 x 255 mm, about $65 for five.

## Order of work

Each step is a commit or a few; each card passes the three gates of
`plan.md` (ERC and exhaustive or scripted sim of the export at TYP/LO/HI/MIX;
routed with DRC zero; machine gate with the emulator) before the next.

1. **Card frame and dense tile.** Done: `frame.card_frame` (100 x 100 outline, header at the top, holes mid-side, decoupling), `ksch.DenseWriter` (the tile above), `build_reg_card.py`. Proved on `cards/reg0`: 99 transistors, routed DRC-clean in one freerouting pass, ERC clean. The rule stands for every later card: if one does not close, it is the tile pitch that moves, not the card size (a 100 x 150 card is $11.20 instead of $2).
2. **Register bit cards** (4). Done: `cards/reg0..3`, routed DRC-clean; `tb_registers.py cards` 113/113 at TYP, LO, HI, MIX 1..3 on the exports; machine gate with the four cards, all twelve programs at TYP.
3. **ISA: JNZ, JNC.** Done: `isa.md`, `emu.py` (the assembler follows it), `sequencer.py` (two more flag-gated rows, 45 rows and 87 diodes), `programs/loops.asm`; `test_emu.py` passes all twelve programs.
4. **Sequencer at the new pitch**: vertical diodes in `ksch.matrix`, dense tiles, JNZ/JNC rows (done: `boards/03-sequencer`, 245 x 255 on four layers at the card pitch, D051, ERC clean, the matrix hidden from the router), routed 2026-09-14 with freerouting 2.4.1 on the ninth attempt (0 unconnected, 0 DRC errors; the route rules are in D051's amendment and the board README), machine gate on its export: 24 of 24 corner runs and the TYP programs pass. Open item to close first: `sim/out/d041_list_MIX3.log`, list.asm at MIX seed 3 on the buffered sequencer, must show 0 mismatches. Closed 2026-09-11: 210 ticks, 0 mismatches (two earlier runs stalled in ngspice at tick 82 with "timestep too small"; the third retry option, gmin and more transient iterations, got through).
5. **ALU bit cards** (4) with the carry and zero chain. Done: `cards/alu0..3` routed DRC-clean; `tb_alu.py cards` exhaustive 2304/2304 at TYP, LO, HI on the exports (MIX running); machine gate with step 9.
6. **Counter bit cards** (8) with the count carry and the chained link ribbon. Built: `cards/ctr0..7` routed DRC-clean; call.asm on the gate lists 0 mismatches; the exports are proven by the step 9 gate.
7. **Memory control and slot cards** (1 + 8). Built: `cards/memctl`, `cards/memslot` routed DRC-clean; `tb_memory.py cards@dev` 217/217 (the slot jumpers make MAR1..3 ports of the slot subcircuit; left inside they floated and every read came from pair 7); the exports at four corners run in step 9's queue.
8. **Program cards** (one per four words), **panel cards** (3), **clock**, **hub**, **coupon** as cards. Built 2026-09-11: `cards/prog` (six jumpers PC7..2; fib on the gate lists 0 mismatches), `cards/clock`, `cards/hub` (two headers, the 64 lines pre-routed), `cards/panela..c` (a tile column is a panel column, so the LEDs read row by row), `cards/coupon`; all ERC clean and placement DRC clean, routes in progress.
9. **Machine deck** instantiating cards with their links; the machine gate over all twelve programs at TYP, then LO/HI/MIX on fib, alu, gcd, list, logic, call; clock-board runs; 500 pF rerun. Closed 2026-09-14, every run on the whole card deck (`aluc,hubc,regc,seq,ctrc,memc,progc,pnl`): all twelve programs at TYP, 0 mismatches (fib 127 ticks, calc 616, lfsr 1497, sort 974, logic 986; `sim/out/gate_cards_TYP.log`, lfsr in `sim/out/cards_lfsr_TYP.log` after machine.py's virtual reset stopped re-asserting at 1 s); fib, alu, gcd, list, logic, call at LO, HI, MIX1 and MIX2: 24 of 24, 0 mismatches (`sim/out/gate_cards_corners.log`); 500 pF per bus line on fib, list, logic, calc at TYP and LO: 8 of 8 (`sim/out/gate_cards_500pF.log`; logic at LO aborted three times in ngspice with "timestep too small" inside an ALU transistor and passed on a fourth solver rung, more shunt capacitance, gmin and iterations, `sim/out/cards_500pF_logic_LO_rung4.log`: a solver artefact, the circuit is the same one that passes at 300 pF); with the clock card in the deck (`clkc`, its oscillator driving CLK instead of the testbench pulse) fib and call pass at TYP, 127 and 84 ticks, 0 mismatches (`sim/out/cards_clk_*_TYP_rescore.log`; the card's edge takes 35 us from 0.5 V to 3.5 V and the cards step at 2.4 V, so `machine.py` samples each tick before CLK leaves 1.5 V). On the way this gate found D048 and D050 (calc ended one count short) and the lfsr reset bug in the testbench. The testbench's reset still drives RST with the clock card in the deck; the card's own power-on reset is proven by `tb_clock`.
10. **Mounting**: `mounting.md` and the column preview redrawn for a 4 x 7 card grid per face, the sequencer as a 2 x 2 block, the ribbon zigzag; rails per card row. Done 2026-09-14 (`mounting.md`, `docs/mounting/column.html`: 28 slots per face, 39 fixed, the sequencer over three rows of the front).
11. **Docs and order**: `bring-up.md` per card, `order-1.md` with the quotes from the calculator, `bom.py` over the cards, renders; then the order. Status 2026-09-14: `bring-up.md`, `order-1.md` and the parts table from `bom.py` over the routed cards are written, every card's `fab/` holds its gerbers and renders, and the gate of step 9 is closed. Left: the board quotes read from JLCPCB's calculator with the actual gerbers (a cart, not a commit), then the order.
