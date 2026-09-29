# The order: how it got here

What `docs/order-1.md` said before it was rewritten on 2026-09-29, kept for
the record. Nothing here is current: the boards, the counts and the parts
to buy are in `docs/order-1.md`, generated from the routed boards.

## Why cards (2026-09-10, D042)

The machine was first drawn as nine large boards. JLCPCB's quotes for
those, 2-layer, five pieces each:

| Board as it was | Size (mm) | Quote |
|---|---|---|
| Sequencer | 449 x 470 | $258 + $93 shipping |
| Sequencer, matrix turned | 290 x 520 | $153 + $74 shipping |
| Memory | 368 x 377 | $135 + $74 shipping |
| Registers | 266 x 285 | $49 + $30 shipping |

About $1,300 for the machine at five of each. As 100 x 100 mm cards the
same machine is on the fab's cheapest tier, $2 to $4 for five, plus the
sequencer. These tier prices are not quotes: a quote is what the fab's
calculator says for the uploaded files.

## What went wrong with the first version of the order document

- It said "7129 parts on 26 boards". 7129 parts are right; 26 is the
  number of designs. 52 boards are built (eight memory slot cards and
  twenty program cards are one design each).
- It said "buy the buy column" and had no such column, and no spares.
- It said "45 to 50 sockets" for 53 headers, "about 6 m" of ribbon where
  `mounting.md` said 7 m per ribbon, and "four jumper caps per page" where
  a program card has six jumpers and a memory slot card three.
- It named a banana socket (Hirschmann BIL 20) whose drawing had not been
  read, and before that a Cliff S16, which is a different kind of part.
- Its checklist had grown into a wall of text with the history of each
  check in it. The history is here and in `docs/audit.md`.

## The checks, in the order they were learned (2026-09-28)

1. The coupon's project file had lost its design rules to a schematic
   rebuild; kicad-cli then judged the board by KiCad's defaults. Found only
   because the DRC was re-run on the committed board. Since then the order
   gate (`sim/order_check.py`) is run on the commit, not remembered.
2. The hub's first route put CLK 0.17 mm from the +5V socket's copper
   ring, under the socket's nut, with the DRC content at 0.15 mm. The gate's
   `clamp` check came of that: no copper of another net where hardware is
   clamped on the board.
3. The checks had run on the three pilot cards only. Since `5b2a0bd` every
   check runs on all 26 boards; `docs/audit.md` is the record.
4. The ribbon's route could not be built as drawn (an IDC socket lies
   across its ribbon). The headers went to the back of the boards (D059,
   D062) without a track moving; `sim/board_diff.py` is the proof.
