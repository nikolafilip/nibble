# Mounting: the column of cards

Decided 2026-09-10 (D038, D042, D043), redrawn 2026-09-11 for the cards.
The machine is 100 x 100 mm cards on one crimped ribbon per pair of faces,
plus the sequencer board (245 x 255), and it lives in a New York apartment.
A wall panel is too big to own, a flat stack hides the LEDs, a card cage
hides them too. So: a freestanding square column with the cards standing
on its faces in a grid, LEDs out, the ribbons zigzagging over them.

`docs/mounting/column.html` is the model: open it in a browser (it loads
three.js from a CDN), drag to walk around it, slide the program-card count
to see how it grows. The elevations, rail heights, ribbon lengths and the
parts list on that page are generated from the same card outlines as the
schematics.

## The frame

2020 aluminium extrusion, the 3D-printer profile. Four 900 mm uprights on
a 500 mm square, joined top and bottom by 460 mm rails with corner
brackets. Nothing is drilled: an M3 T-nut slides into a rail slot, a 12 mm
standoff screws into the T-nut, the card screws onto the standoff.
Footprint with cards 54 x 54 cm, height 95 cm, on the floor or a low table.

## The grid

Every face is 460 mm between the uprights: four columns of cards at a
110 mm pitch (100 mm card, 10 mm gap) with 10 mm to spare each side, and
seven rows at the same pitch from 60 mm above the base to 820 mm. A card's
two M3 holes are mid-height on its left and right edges (docs/cards.md), so
one horizontal rail per row carries every card of that row: seven rails
per face at 110, 220, ... 770 mm above the base bottom, two T-nuts and two
standoffs per card. 28 slots per face, 112 on the column.

The sequencer (245 x 255, four corner holes) takes the top three rows of
the front face, centred, on two rails of its own 231 mm apart (525 and
756 mm); those three rows have no other rails and no other cards.

| Face | Cards |
|---|---|
| Front, rows 1 to 4 (16 slots) | hub (bottom right, where the two ribbons meet), clock, panel A, B, C, counter bits 0 to 7, then program cards |
| Front, rows 5 to 7 | the sequencer (245 x 255) |
| Right (28) | register bits 0 to 3, ALU bits 0 to 3, memory control, memory slots 0 to 7, then program cards |
| Left, then back (56) | program cards |

Fixed cards: 39 slots. Program cards fill the rest, four words each: a
program of n words takes ceil(n / 4) cards (`list` 6, `sort` 20); the
8-bit counter caps it at 64 cards, 256 words. Two faces hold 17 program
cards (68 words); a third face is needed for `sort`.

## The ribbons

Two 64-way ribbons (D043). Ribbon A starts at the hub's top header, runs
along the front face's bottom row of headers (every card's header is on
its top edge, at the same place on every card, so the sockets sit at a
110 mm pitch along the ribbon), folds down 110 mm at the row's end, runs
back along the next row, and so on up the front, then around the upright
onto the right face and up it the same way. Ribbon B starts at the hub's
bottom header and does the left face and then the back. A socket is
crimped on wherever a card is; an empty slot is just ribbon. The ribbon
lies flat on the face over the cards' top edges: the visible wiring.

A ribbon over two full faces is about 7 m long and adds about 500 pF to
every bus line; with the hub's 10k pull-ups that is 5 us of rise on a
1 ms tick. The machine deck runs at 300 pF and is rerun at 500 pF
(`CABLE_PF=500`); both must pass before the order. With only the front
and right faces populated the ribbons are 3 to 4 m.

The neighbour links (ALU carry and zero chain, counter carry, memory
address ribbon, the sequencer's operand lines) are short pieces of 6-way
and 12-way ribbon with their own IDC sockets between adjacent cards of a
row; the counter's eight cards and the memory's nine sit side by side in
their rows for that reason (a 4-wide row breaks a chain of eight into two
rows, so the chained ribbon folds down once, like the bus ribbon).

## Parts

| Part | Qty | Note |
|---|---|---|
| 2020 extrusion, 900 mm | 4 | uprights |
| 2020 extrusion, 460 mm | 35 | 25 card rails (7 per face, less the sequencer's three rows), 2 sequencer rails, 8 frame rails; 16 m |
| 2020 corner brackets with screws | 140 | two per rail end |
| M3 T-nuts for the 6 mm slot | 130 | two per card, four for the sequencer, spares |
| M3 x 12 mm male-female standoffs | 130 | brass or nylon |
| M3 x 6 mm screws | 260 | card to standoff, standoff to T-nut |
| Rubber feet or a 500 mm plywood square | 1 | the base |

About $150, all stock items. A face that is not populated needs no rails.

## What it does not do

The ribbons show, and that is the look. On the floor the panel's switches
are at 20 to 40 cm, so it wants a low table or the panel cards moved up a
row. It has a back: with all four faces used, half the program is behind
whatever you stand in front of, so it wants a spot you can walk around.
