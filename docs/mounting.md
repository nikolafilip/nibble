# Mounting: the column of cards

Decided 2026-09-10 (D038, D042, D043), redrawn 2026-09-11 for the cards;
the ribbons' section rewritten 2026-09-29 (D059), the rest still to follow.
The machine is 100 x 100 mm cards on one crimped ribbon per pair of faces,
plus the sequencer board (245 x 255), and it lives in a New York apartment.
A wall panel is too big to own, a flat stack hides the LEDs, a card cage
hides them too. So: a freestanding square column with the cards standing
on its faces in a grid, LEDs out, the ribbons behind them.

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

**Being redrawn.** The bus headers are on the back of the boards (D059,
D062) and the ribbon runs behind the cards. What is settled and what is
not:

Settled, because it follows from the parts:

- An IDC socket lies across its ribbon, and every card's header lies along
  its top edge. So the ribbon runs down a column of cards, a socket every
  110 mm, never along a row.
- It is 81 mm wide (64 conductors at 1.27 mm) and passes between a card's
  two standoffs, which are 92 mm apart.
- Every header sits the same way round (notch toward the top edge, pin 1
  top left as the front sees the holes). A ribbon that comes down one
  column and goes up the next must therefore arrive un-mirrored. Two 45
  degree folds that make a U-turn mirror it: conductor 1 changes sides,
  and pins 1 and 64 are +5V and GND. The turn that works is a sideways
  step of two 45 degree folds (down, across, down again) followed by one
  straight fold back on itself: three folds. `docs/bring-up.md` has the
  continuity test that every ribbon gets before it sees power.
- The links between neighbours (2x3 and 2x6 headers on the front, along
  the bottom edge) have the same geometry: their ribbon leaves downward.
  Between two cards side by side the cable is a U with a half twist in it,
  or pin 1 meets pin 6 and the carry line meets ground.

Not settled, and not to be bought for until it is:

- Which card stands in which slot, so that the chains (ALU, counter,
  memory) have their members next to each other and the ribbon's length
  is known. The old slot list below was made for a ribbon along the rows.
- The length of the standoffs. A header on the back with its socket and
  the ribbon on it is deeper than the 12 mm the card stands off the rail;
  under a card's own rail that does no harm (the rail is 30 mm below the
  header), but on the sequencer the upper rail runs right under the
  header. The depth is measured on the pilot's hub with a socket on it,
  then the standoffs are chosen.
- The sequencer's place: its header's middle is 72.5 mm left of the
  board's middle, so the board stands off-centre to bring the header over
  a column of cards.
- The ribbon's length against what the machine was simulated with (300 pF
  on every bus line, 500 pF in the margin run).

`docs/mounting/column.html` still draws the old route (and an older power
entry); it is redrawn with the slot list.

## Parts

| Part | Qty | Note |
|---|---|---|
| 2020 extrusion, 900 mm | 4 | uprights |
| 2020 extrusion, 460 mm | 35 | 25 card rails (7 per face, less the sequencer's three rows), 2 sequencer rails, 8 frame rails; 16 m |
| 2020 corner brackets with screws | 140 | two per rail end |
| M3 T-nuts for the 6 mm slot | 130 | two per card, four for the sequencer, spares |
| M3 male-female standoffs, 12 mm or longer | 130 | brass or nylon; the length is open (see the ribbons) |
| M3 x 6 mm screws | 260 | card to standoff, standoff to T-nut; no washers: the cards' mounting pads are 6.4 mm and tracks pass 0.2 mm outside them (the order gate holds copper of other nets 3.3 mm from the hole's centre, the reach of a hex standoff's corners) |
| Rubber feet or a 500 mm plywood square | 1 | the base |

About $150, all stock items. A face that is not populated needs no rails.

## What it does not do

On the floor the panel's switches
are at 20 to 40 cm, so it wants a low table or the panel cards moved up a
row. It has a back: with all four faces used, half the program is behind
whatever you stand in front of, so it wants a spot you can walk around.
