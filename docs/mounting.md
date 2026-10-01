# Mounting: the two-sided panel

Redrawn 2026-10-01 (D065), replacing the four-faced column of D038. The
column's size came from the nine boards of nine sizes; the cards (D042)
are all 100 x 100 mm and the sequencer is the one exception, so the
machine fits on the two faces of one flat panel of aluminium extrusion
standing on a table. It lives in a New York apartment: 58 cm wide, 82 cm
tall, 30 cm of feet front to back, and you walk round it.

`docs/mounting/panel.html` is the model: open it in a browser (it loads
three.js from a CDN), drag to walk round it, slide the program-card count
to see the back fill. `docs/mounting/panel.js` holds the slot plan, the
rails and the ribbons' routes; the page draws from it and `node panel.js`
prints the numbers quoted here, so the document and the model agree.

## The frame

2020 aluminium extrusion, the 3D-printer profile. Two 800 mm uprights
580 mm apart outside to outside, each standing on a 300 mm foot of the
same extrusion laid flat across the panel. Fourteen 580 mm rails lie
across the uprights' faces, seven on the front face and seven on the
back, one corner bracket at each end. Nothing is drilled: an M3 T-nut
slides into a rail's slot, a standoff screws into the T-nut, the card
screws onto the standoff. About 13 cm deep with both faces' cards on.

## The grid

Both faces are five columns of cards at a 110 mm pitch (100 mm card,
10 mm gap), 20 mm inside the uprights' outer edges: columns at 20, 130,
240, 350 and 460 mm from the panel's left edge, as the face is seen. A
card's two M3 holes are mid-height on its left and right edges
(`cards.md`), so one rail per row carries every card of that row.

The front has four rows at the pitch and then a band of three rows for
the sequencer: the sequencer (245 x 255, four corner holes, the upper
pair 20 mm below its top edge, the pairs 231 mm apart) stands on two
rails of its own, 231 mm apart, with its left edge on column 1 so that
its bus header is in line with column 1's ribbon; a third rail between
them carries a row of cards beside it. The back has seven rows at the
pitch. Rail heights, table top to rail centre:

| Row | Front | Back |
|---|---|---|
| 1 | 760 | 760 |
| 2 | 650 | 650 |
| 3 | 540 | 540 |
| 4 | 430 | 430 |
| 5 | 320 (the sequencer's upper rail) | 320 |
| 6 | 210 | 210 |
| 7 | 89 (the sequencer's lower rail) | 100 |

The lowest cards' bottom edges are 4 cm above the table.

## The slots

Front, as the front sees it, left to right; the chains of neighbours run
down the columns (see the links below):

| Row | Column 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 1 | ALU bit 0 | counter bit 0 | counter bit 7 | register bit 0 | register bit 1 |
| 2 | ALU bit 1 | counter bit 1 | counter bit 6 | register bit 2 | register bit 3 |
| 3 | ALU bit 2 | counter bit 2 | counter bit 5 | – | – |
| 4 | ALU bit 3 | counter bit 3 | counter bit 4 | – | – |
| 5 | sequencer | (sequencer) | (sequencer) | clock | – |
| 6 | (sequencer) | (sequencer) | (sequencer) | panel A | panel B |
| 7 | (sequencer) | (sequencer) | (sequencer) | panel C | hub |

Back, as the back sees it (its column 1 stands behind the front's
column 5, so the hub is right behind it):

| Row | Column 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 1 | memory control | program 1 | program 12 | program 13 | – |
| 2 | memory slots 0 | program 2 | program 11 | program 14 | – |
| 3 | memory slots 1 | program 3 | program 10 | program 15 | – |
| 4 | memory slots 2 | program 4 | program 9 | program 16 | – |
| 5 | memory slots 3 | program 5 | program 8 | program 17 | – |
| 6 | memory slots 4 | memory slots 7 | program 7 | program 18 | – |
| 7 | memory slots 5 | memory slots 6 | program 6 | program 19 | program 20 |

The program cards are numbered along ribbon B, so a longer program is
more cards at the ribbon's end, up the back's column 5: 26 program cards
fit (104 words; `sort` takes 20). Which program card holds which page is its
jumpers, not its slot. 61 card slots in all (26 on the front beside the
sequencer, 35 on the back), 50 cards in them, 11 free.

The panel's switches and buttons are 4 to 26 cm above the table, the
hub's banana sockets about 9 cm, bottom right of the front. The memory's 64
cell LEDs and the program are on the back.

## The ribbons

An IDC socket lies across its ribbon and every bus header lies along its
card's top edge, on the back of the card (D059), so the bus ribbon runs
down a column of cards behind them, a socket every 110 mm, never along a
row. It is 81 mm wide (64 conductors at 1.27 mm) and passes between a
card's two standoffs, which are 92 mm apart, through the gap between card
and rail.

Every header sits the same way round (notch toward the card's top edge,
pin 1 at the top left as the front of the card sees the holes), so every
socket must arrive with conductor 1 (the red edge) on the left as that
face is seen. A 45 degree fold turns the ribbon by 90 degrees and moves
conductor 1 from one edge to the other; two of them making a U-turn leave
it mirrored (pin 1 would meet pin 64). **A turn is three folds**: a 45
degree fold sideways, a 45 degree fold back to the column's direction
(the sideways step), and one straight fold back on itself. The same three
folds serve at the top of a column, at the bottom, and where ribbon B
comes up the back after passing under the panel: there it arrives
mirrored because the back's viewer has turned round, and the three folds
put conductor 1 back on the left. The sideways band of a turn starts
just past the last socket and lies back over the column, behind the
cards. `bring-up.md` has the continuity test every ribbon gets before it
sees power.

Ribbon A, from the hub's top header: up column 5, down 4, up 3, down 2,
a sideways step over the sequencer's top edge, down column 1 through the
sequencer's socket, a straight fold, and back up column 1. 22 sockets,
four turns, 3.74 m with 300 mm of slack.

Ribbon B, from the hub's bottom header (along the hub's bottom edge, on
its back): down behind the hub, under the panel between the feet, up the
back's column 1, down 2, up 3, down 4, up 5 as far as the program goes.
30 sockets, five turns, 3.65 m with 300 mm of slack.

7.4 m of 64-way ribbon end to end; buy 10 m, the 6-way and 12-way pieces
are torn off the rest along a groove. The bus sees it all: a line's
capacitance is the whole 7.4 m. Flat ribbon is about 50 pF per metre
between neighbouring conductors and the bus pinout puts signal beside
signal, so a line sees 400 to 800 pF depending on what its neighbours
are doing. The machine deck is proven at 300 and 500 pF per line
(`cards.md` step 9); **a run at 800 pF is on the list before the ribbon
is cut.**

### The links between neighbours

The link headers are on the front of the cards along the bottom edge:
`IN` at x = 14, `OUT` at x = 80, the chained 12-way `LINK` at x = 40.
Their ribbon leaves downward.

- **12-way chains, over the fronts.** Every counter card and every memory
  card has its `LINK` header at the same place, so a 12-way ribbon with a
  socket crimped on every 110 mm runs straight down a column of them,
  15 mm wide, over the transistors between x = 32 and 48 where no LED
  stands. That is why the counter stands in two columns and the memory in
  one: the sequencer's link header (on its top edge, x = 115 of the
  board, in column 2's width) sends its ribbon up column 2 over counter
  bits 3, 2, 1, 0, a U-turn in the top margin, and down column 3 over
  bits 7, 6, 5, 4: 9 sockets, about 1.0 m. Memory control at the top of
  the back's column 1 sends its ribbon down over slots 0 to 5, a U-turn
  under row 7, and up column 2 over slots 6 and 7: 9 sockets, about
  1.0 m. Visible wiring, by design.
- **6-way carry links.** `OUT` of one card to `IN` of the next. Side by
  side (counter bit 3 to bit 4, the only pair in a row) the ribbon leaves
  `OUT` downward into the gap under the row, a U with a half twist back
  up into `IN`: about 80 mm. One above the other (the three ALU pairs and
  the six other counter pairs) the ribbon leaves `OUT` into the gap under
  the card, runs to the column gap on the card's right, along it to the
  gap under the next card and back in to `IN`: about 230 mm, never over
  a card's face. Ten cables, 2.2 m of 6-way.

## Open until the pilot

- **The standoffs.** A box header is 9 mm high and the socket on it
  reaches about 15 mm behind the card; the rail is 40 mm below the
  header, so on a card the socket sits above its rail and 12 mm standoffs
  may do. On the sequencer the upper rail runs 12 mm below its header and
  the socket sits in front of the rail: its four standoffs must be longer
  than the socket is thick. Measure the pilot's hub with a socket crimped
  on, then buy.
- **The 800 pF run** (above).

## Parts

From `node panel.js`:

| Part | Qty | Note |
|---|---|---|
| 2020 extrusion, 800 mm | 2 | the uprights |
| 2020 extrusion, 580 mm | 14 | 7 rails on the front face, 7 on the back; 8.1 m |
| 2020 extrusion, 300 mm | 2 | the feet, flat under the uprights, across the panel |
| 2020 corner brackets with their screws and T-nuts | 32 | one at each rail end, two per foot |
| M3 T-nuts for the 6 mm slot | 114 | two per card, four for the sequencer, ten over |
| M3 male-female standoffs, 12 mm or what the pilot says | 114 | brass; the sequencer's may be longer |
| M3 x 6 mm screws | 228 | card to standoff, standoff to T-nut; no washers: the cards' mounting pads are 6.4 mm and tracks pass 0.2 mm outside them (the order gate holds copper of other nets 3.3 mm from the hole's centre, the reach of a hex standoff's corners) |
| Rubber feet, self-adhesive | 4 | under the feet |

About 10 m of extrusion, all stock lengths. Bought after the pilot's
standoff measurement, with the ribbon.

## What it does not do

It has a back: the memory and the program are behind what you stand in
front of, so it wants a table you can walk round, or it turns on its
feet. The 12-way chains lie over the fronts of the counter and memory
cards. A program longer than 104 words is more than the back holds; the
counter allows 256.
