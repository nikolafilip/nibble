# Audit of every board (2026-09-28)

Until this date the order gate had run on the three pilot cards only. This
is the record of running every check on all 26 designs (25 cards and the
sequencer), what each check can and cannot see, what was found, and what is
still open. Nothing here has been built: every line is a check on files.

Commit checked: `5b2a0bd`. Since then the bus headers went to the back of
every board and the silkscreen was refitted (no track moved: `sim/board_diff.py`);
the findings' states below are as of that change.

## 1. What was run, on what

| Check | How | Boards | Result |
|---|---|---|---|
| The order gate, eleven checks per board (clean, rules, erc, drc, jlc, fab, zip, outline, pins, asm, clamp) | `python3 sim/order_check.py <26 names>`, log `sim/out/gate_all.log` | all 26 | 286 of 286 pass |
| What joins the boards: bus pins and link pins | `python3 sim/order_check.py --machine` | all 26 | 27 bus headers, 19 links: all pass |
| The checks themselves, against faults planted on purpose | `python3 sim/order_check.py --selftest` | | 17 of 17 part cases, 5 of 5 planted bus and link faults caught |
| Every DRC warning read | kicad-cli, by hand | the 5 boards that have any | section 3 |
| Every assembly drawing looked at | rendered with Chrome, one by one | all 26 | section 2, F2 |
| Other parts' leads under the bus header's body | script over the pads inside each header's courtyard | all 26 (27 headers) | none |
| Every footprint has a courtyard, and courtyard overlap is an error | project files and boards | all 26 | yes; 0 overlaps |
| Hole against lead, per footprint | section 4 | all 22 footprint types | fits on paper; three parts must be the exact family |
| Silkscreen text sizes | script | all 26 | 364 labels under 1.0 mm (F4); 2 after the refit |

## 1a. The header move and the machine gate (2026-09-29)

The machine gate simulated the boards as they were before the headers went
to the back. Two comparisons say its results stand for the boards as they
are now:

- every board's SPICE export is the same, element for element
  (`sim/board_diff.py 992a90f <26 boards>`: "no copper moved", and the
  netlist column);
- the whole-machine deck (fib, all cards, the clock card) written from the
  old tree and from the new one has the same 4957 elements on the same
  nets. The 54 cable capacitors are numbered in another order, one on each
  bus line as before.

One stage does not carry over: the crosstalk stage (`CROSS_PF=100`,
`sim/results/gate25_cross.md`) coupled the lines that were neighbours on
the ribbon then. The neighbours are other lines now (RST and BUS1#, BUS1#
and BUS0#, BUS0# and BUS3#, ...), so that stage is owed again on the new
order: six programs at TYP and HI. Paid 2026-09-30: `sim/results/gate26_cross.md`,
12 of 12 pass (with the clock card's hold-off, D064, in the deck; the card
with it on carries the same deck).

## 2. Findings

| # | Finding | Where | State |
|---|---|---|---|
| F1 | The gate's `pins` rule called four correct timing capacitors reversed and a potentiometer's mounting lugs unconnected | clock, panel B | Fixed in the rule (`5b2a0bd`); the rule now has a self-test |
| F2 | The assembly drawings hid what they were for on the cards with arrays: 32 diode labels covered the 32 diodes of a program card, the panels' switch names ran across the resistors beside them | prog, panel A, B, C, clock | Fixed (`5b2a0bd`), all 26 redrawn and looked at |
| F3 | The sequencer had never been through the gate, had no assembly drawing and no zip; its README gave the part counts of an older board | sequencer | Gate extended: passes. Drawing shows which 87 of the 1035 matrix crossings take a diode. README corrected |
| F4 | 364 silkscreen labels are 0.8 or 0.9 mm high; JLCPCB states 1.0 mm. 8 labels are clipped by a pad's mask opening | every board; the 8: panel B `INP`, panel C `PC0`, sequencer `OPR0 OPR1 OPR3 OPR5 OPR6 ZFQ` | Closed with the headers' move: `pcb.fit_silk` grows every label to 1.0 mm where it has room and moves it off pads, vias, outlines and out from under parts; none is clipped. Two labels stayed 0.8 mm at first (`WRH` on panel B, `RUN` on the clock): the fitter tried a label's own small size lying down before it tried 1.0 mm standing upright. It now tries every place at 1.0 mm first, and both stand upright beside their LEDs at 1.0 mm: no label on any board is under 1.0 mm. The sequencer's row names stand upright over their rows. The gate's `silk` check holds it; `sim/silk_proof.py` plots the print for the eyes |
| F5 | Nothing checked that the bus header of every board has every signal on the same pin. The simulation joins the cards by net name, so a header wired to the wrong pin passes every deck | all | Closed: `--machine` compares every pad of all 27 headers with `sim/bus.py`. They agree |
| F6 | The link ribbons between neighbours have the fault the bus ribbon had: the headers lie along the bottom edge, so a ribbon leaves them up or down, never sideways to the neighbour | ALU, counter, memory cards, sequencer (30 link headers) | Open, section 5. No board changes; it is a matter of where the cards stand and how each ribbon is folded |
| F7 | A ribbon that goes down one column and up the next arrives mirrored (pin 1 where pin 64 should be) unless it is folded an odd number of times on the way. Pins 1 and 64 are +5V and GND | the bus ribbon behind the cards (D059) | Open, section 5: goes into the mounting document with a continuity test before first power |
| F8 | The schematic calls the level switches "switch up = 1". The switches lie on their side: the sliders move left and right. The boards print nothing about it | panel A, B, C, prog, clock | Closed: the boards print `ON >` at every switch, the assembly drawings and `bring-up.md` say closed (ON, to the right) is 1 |
| F9 | The sequencer's bus header is 12.5 mm left of the header line of the card column below it (the board is centred on the face) | mounting | Open, section 5: the rails are slotted, the board can stand 12.5 mm to the right |

## 3. The DRC warnings, all of them

| Board | Warnings | What they are |
|---|---|---|
| prog | 28 | The printed circles of upright diodes 2.54 mm apart touch each other. Print only |
| panel B, panel C | 1 each | A name clipped by a pad (F4) |
| coupon | 1 | The known 0.5 mm stub at the end of the +5V trunk |
| sequencer | 132 | 59 fixed stubs the router did not need, by design; 67 printed circles and outlines touching; 6 names clipped (F4) |
| the other 21 | 0 | |

## 4. Does the part fit the hole

From the boards' drill sizes and the parts' usual drawings. "Usual" is not
"measured": the coupon is the card that finds out, which is why it is
ordered first. The counts are the whole machine's: 52 boards, 7129 parts.

| Part | Footprint: hole, pitch | The part must be | Risk |
|---|---|---|---|
| 2N7000 (3516) | 0.8 mm, three holes 2.54 mm apart | TO-92; leads 0.4 to 0.55 mm | A straight TO-92 has its leads 1.27 mm apart: every one is spread by hand, or bought with formed leads. Which order code is formed to 2.54 mm has not been read from a datasheet yet |
| Resistor, upright (2138) | 0.8 mm, 5.08 mm | 1/4 W axial, body to 6.3 x 2.5 mm, lead 0.6 mm | none |
| 1N4148, upright (727) | 0.8 mm, 2.54 mm | DO-35 glass, body under 2 mm across | At 2.54 mm between neighbours two 1.85 mm bodies leave 0.7 mm |
| LED (281) | 0.9 mm, 2.54 mm | 3 mm round | none |
| Electrolytic (56) | 0.8 mm, 2.0 mm | 5 mm can. 10 uF, 2.2 uF, 1 uF, and 100 uF 16 V on the hub | A 100 uF 25 V can is 6.3 mm: buy 16 V |
| Ceramic capacitor (56) | 0.8 mm, 2.5 mm | 2.5 mm lead pitch, not 5 mm | none |
| Box header 2x32 (53), 2x6 (18), 2x3 (20) | 1.0 mm | 0.64 mm square pins | none |
| Pin header 1x3 (144), 1x2 (2), 1x6 (1) | 1.0 mm | 0.64 mm square pins, a jumper cap on each 1x3 and on the clock's 1x2 | none |
| DIP switch 8-way (84), 4-way (1), 1-way (1) | 0.8 mm, 7.62 mm rows | the common slide type, 9.8 mm wide | none |
| Push button (2) | 1.1 mm, 6.5 x 4.5 mm | 6 mm tactile switch; fits two ways round, both right | none |
| Potentiometer (1) | 1.0 mm pins 2.5 mm apart, two 2.2 mm leg holes 8.8 mm apart, 7.0 mm from the pins | Bourns PTV09A-4, 9 mm, 1 M linear (`lib/nibble.pretty`, from the maker's layout) | Another maker's 9 mm pot only after its drawing has been laid on these numbers; the Alpha RD901F-40 the card was first drawn for has slotted lugs 9.6 mm apart and does not fit |
| Polyfuse (1) | 1.0 mm, 10.2 mm with a 1.9 mm offset | Bel 0ZRE0150FF | The offset is this family's kinked leads |
| Test loop (21) | 1.0 mm | the miniature size | The larger sizes want 1.6 mm |
| Banana socket (2) | four 1.6 mm holes on a 4.76 mm diamond | Cal Test CT3151V1 (D063); footprint drawn from the maker's drawing, `lib/nibble.pretty` | It stands on four solder joints without the panel its drawing has in front of it |
| Crowbar: SCR, zener, 3 A diode (1 each) | TO-220 1.1 mm holes; DO-41 1.1 mm, 10.16 mm; DO-201AD 1.6 mm, 15.24 mm | BT151-500R (pin 1 cathode, 2 anode, 3 gate: read in its datasheet), 1N4735A, 1N5408 | none |

## 5. Open: how the ribbons run

(2026-10-01: settled in `docs/mounting.md` and drawn in `docs/mounting/panel.html`,
D065: the two-sided panel, the slot plan, the routes and lengths of every
ribbon. Open: the standoff length, measured on the pilot, and the 800 pF run.
The points below are kept as the reasoning.)

An IDC socket lies across its ribbon. Every header on every board lies
along a top or bottom edge, so every ribbon leaves its header upward or
downward. D059 settled the bus ribbon (headers on the back, the ribbon down
each column behind the cards). What follows from that and is not yet
written into `mounting.md` or drawn in the model:

1. **Turning the bus ribbon.** The ribbon goes down one column and must come
   up the next. Two 45 degree folds turn it round and leave it mirrored:
   pin 1 of the sockets would meet pin 64 of the headers. A third fold (the
   ribbon doubled back on itself once) puts it right. The same rule holds
   for every turn: a ribbon that reverses direction needs an odd number of
   folds. Before first power every socket is tested for continuity from its
   pin 1 to the hub's pin 1.
2. **Link ribbons, 6-way (ALU and counter chains).** `OUT` is at x = 80 and
   `IN` at x = 14 on the bottom edge; between two cards side by side they
   are 44 mm apart. The ribbon leaves `OUT` downward into the 10 mm gap
   under the row, folds toward the neighbour, folds down, and doubles back
   up into `IN`: three folds, 6-way ribbon, about 80 mm.
3. **Link ribbons, 12-way, chained (sequencer to eight counter cards, memory
   control to eight slots).** Every card has the header at the same place
   (x = 40, bottom edge), so the ribbon that needs no folds runs straight
   down a column of cards, over their fronts, 15 mm wide, across the
   transistors between x = 32 and 48 (no LED stands there). Along a row it
   needs four folds per card. This decides where the counter and memory
   cards stand: in columns, not in rows as `mounting.md` has them.
4. **The sequencer** stands 12.5 mm to the right of centre so that its bus
   header is in line with the column under it. Its link header is on its
   top edge, the counter cards are below it: that ribbon goes over the top
   of the board and down behind it, or the counter cards' chain starts at
   the far end.
5. **Behind the card.** A box header is 9 mm high and the socket on it
   reaches about 15 mm; the rail is 12 mm behind the card, 40 mm below the
   header. The ribbon leaves the socket 13 mm behind the card and has to
   come forward to pass between card and rail. On the sequencer the top
   rail's edge is 0.6 mm from the socket's. Both want drawing to scale
   before the frame is bought.

## 6. What no file can show

| Risk | Why it is open | What settles it |
|---|---|---|
| A part that does not match its usual drawing | section 4 is from drawings | the coupon and register card of the pilot, built |
| Supply drop and ground offset along 7 m of ribbon (about 0.2 to 0.4 V at the far card with every LED lit) | the decks pass at 4.5 and 4.25 V on every card alike; they have never run with the ribbon's resistance between the cards | a deck with the ribbon's resistance in its supply lines; queued behind the reset sweep |
| Pushing a 64-way socket onto a card held by two screws on its mid-line (60 to 100 N) | mechanical | a hand behind the card; goes into `bring-up.md` |
| Static on the bus lines, which go straight to gates | no protection on any card | handling; goes into `bring-up.md` |
| Over-voltage and reversed leads at the bench supply | the crowbar is decided (D061), not built | the hub, with a test bench that chooses its values |
