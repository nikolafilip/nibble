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
right edges). LEDs on the front. About 85 cm2 for logic, laid out at about 70
mm2 per transistor (D045), so up to about 120 transistors per card.

| Card | Count | Designs | Transistors | Neighbour link | Notes |
|---|---|---|---|---|---|
| Register bit i: A, B, OUT flip-flops and muxes for one bit | 4 | 4 (bit baked in) | ~92 | none | LEDs A, B, OUT |
| ALU bit i | 4 | 4 | ~60 | carry and zero-so-far to bit i+1 (2 x 3) | bit 3 carries CF and ZF to the bus |
| Counter bit i: PC bit and RA bit | 8 | 8 | ~52 | count carry to bit i+1 (2 x 3); OPR i from the sequencer's link ribbon (2 x 6, chained) | |
| Memory control: MAR, write gate, PH1 | 1 | 1 | ~35 | MAR0..3 and WR/RD to the slot cards (2 x 6, chained) | |
| Memory slots: two 4-bit slots with their decode | 8 | 1, slot pair by jumper | ~90 | from memory control | 8 cell LEDs |
| Program: four words, page and word-group jumpers | 4 per page | 1 | ~28 + 32 diodes | none | 4 DIP-8; two pages for `list`, five for `sort` |
| Panel | 3 | 3 | ~80 total | none | levels and LEDs on two, data switches and CLK/RST on one |
| Clock | 1 | 1 | 16 | none | |
| Hub: USB, polyfuse, bus pull-ups, M pull-downs, test loops | 1 | 1 | 0 | none | two or three headers where the faces' ribbons meet |
| Coupon | 1 | 1 | 26 | | shrinks from 112 mm to fit the tier |
| **Sequencer** | 1 | 1 | ~600 + 83 diodes | link ribbon out to the counter cards | **the one big board, about 230 x 250 mm** |

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
before the order.

## The sequencer (D040, D041, D044, D045)

Stays one board because 45 rows and 23 columns would otherwise cross card
boundaries. Diodes standing up on a 2.54 x 5.08 mm grid make the matrix
114 x 117 mm with a pad pair at every crossing; the 600 transistors of steps,
registers, decoders, rows and column buffers at the card pitch around it. Two
new gated rows for JNZ and JNC. About 230 x 250 mm, about $40 for five.

## Order of work

Each step is a commit or a few; each card passes the three gates of
`plan.md` (ERC and exhaustive or scripted sim of the export at TYP/LO/HI/MIX;
routed with DRC zero; machine gate with the emulator) before the next.

1. **Card frame and dense tile.** `frame.card_frame` (100 x 100 outline, header at the top, holes mid-side, decoupling), a tile generator at the D045 pitch, and `pcb.py` routing it. Prove it on the register bit card: 92 transistors must route DRC-clean in 85 cm2. If it does not close, it is the tile pitch that moves, not the card size (a 100 x 150 card is $11.20 instead of $2).
2. **Register bit cards** (4): generator from `registers.py` sliced by bit; `tb_registers.py` on one slice; machine gate with four slices in the deck.
3. **ISA: JNZ, JNC** in `isa.md`, `emu.py`, `asm.py`, `sequencer.py` (two gated rows); `test_emu.py`; a program that uses them.
4. **Sequencer at the new pitch**: vertical diodes in `ksch.matrix`, dense tiles, JNZ/JNC rows, route, machine gate. Open item to close first: `sim/out/d041_list_MIX3.log`, list.asm at MIX seed 3 on the buffered sequencer, was started at the end of the 2026-09-10 session; it must show 0 mismatches.
5. **ALU bit cards** (4) with the carry and zero chain; `tb_alu.py` per slice; machine gate.
6. **Counter bit cards** (8) with the count carry and the chained link ribbon.
7. **Memory control and slot cards** (1 + 8); `tb_memory.py` reworked per card.
8. **Program cards** (4 per page), **panel cards** (3), **clock**, **hub**, **coupon** as cards.
9. **Machine deck** instantiating cards with their links; the machine gate over all eleven programs at TYP, then LO/HI/MIX on fib, alu, gcd, list, logic, call; clock-board runs; 500 pF rerun.
10. **Mounting**: `mounting.md` and the column preview redrawn for a 4 x 7 card grid per face, the sequencer as a 2 x 2 block, the ribbon zigzag; rails per card row.
11. **Docs and order**: `bring-up.md` per card, `order-1.md` with the quotes from the calculator, `bom.py` over the cards, renders; then the order.
