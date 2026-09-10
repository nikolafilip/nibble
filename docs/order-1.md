# The order: boards, parts, cables, frame

One order for the whole machine (D032): every board has passed its three
gates (docs/plan.md), so nothing here is a guess that a second order fixes.
Four carts: the fab, the electronic parts, the cables, the frame.

## 1. Boards

**Rewritten for cards on 2026-09-10 (D042); sizes and the parts table below
are regenerated once the cards are routed.** The quotes that drove the
decision, JLCPCB, 2-layer, five pieces:

| Board as it was | Size (mm) | Quote |
|---|---|---|
| Sequencer | 449 × 470 | $258 + $93 shipping |
| Sequencer, matrix turned | 290 × 520 | $153 + $74 shipping |
| Memory | 368 × 377 | $135 + $74 shipping |
| Registers | 266 × 285 | $49 + $30 shipping |

About $1,300 for the machine at five of each. As cards (`cards.md`): twelve
designs of 100 × 100 mm on the $2 to $4 tier plus one sequencer board of
about 230 × 250 mm, $60 to $80 of boards, one package. The order goes in
once every card has passed its three gates; the table of designs, pieces
and the calculator's numbers is filled in then.

## 2. Parts

Totals for one machine with two program pages, from `sim/bom.py` over the
routed cards (to be regenerated; the notes below still hold). Buy the "buy" column: 2N7000 and resistors by the hundred
are cheaper than by the exact count and you will drop some.

<!-- bom -->

Notes:

- **2N7000**: Onsemi or Diodes Inc, TO-92. The footprint is the wide inline one (2.54 mm pitch), so the leads are bent apart with a jig. Keep them in the anti-static bag until they are soldered.
- **Resistors**: 1/4 W axial, mounted vertical (DIN0207, 5.08 mm pitch). Every value on the bus boards is 47k (pull-ups), 1k (LED series) or 10k (bus pull-ups and the memory write gate); the panel adds 1 Meg pull-downs and the debounce values.
- **LEDs**: 3 mm, any colour, one colour for the whole machine or one per board; 2 mA bright types look best behind 1k.
- **Diodes**: 1N4148 everywhere (program words, control matrix, clock, panel).
- **Capacitors**: 100 nF disc 2.5 mm pitch; electrolytics are 5 mm diameter, 2 mm pitch.
- **Switches**: DIP-8 slide (the program words and the panel's levels), one DIP-4 (the panel's data), one DIP-1 (RUN); 6 mm tactile buttons for CLK and RST.
- **Headers**: shrouded 2x32 box headers, 2.54 mm (XFCN BH254V-64P, LCSC C48603668, or any); 2x6 box headers for the sequencer-counter link; 1x3 pin headers for the page jumpers with four jumper caps per page.
- **Hub**: USB-B horizontal receptacle, 750 mA radial polyfuse (Bel 0ZRE0075FF or similar), 100 µF bulk.
- **Clock**: 1 Meg 9 mm vertical pot (Alpha RD901F), 47 nF and 2.2 µF timing caps.
- **Test loops**: 2.5 mm wire loops on the hub and the coupon, or bare wire.

## 3. Cables

One 64-way ribbon per column face with 2 × 32 IDC sockets crimped along it,
one per card (D043): about 6 m of 64-way ribbon (28 AWG, 1.27 mm pitch) and
45 to 50 sockets (ZHOURI FC-2.54-64P, LCSC C49261185, or any), crimped in a
bench vice or a $10 IDC jig. The neighbour links are 6-way and 12-way
ribbon offcuts with 2 × 3 and 2 × 6 sockets, about 20 of each. No
assembled cables.

## 4. Frame

From docs/mounting.md: 2020 aluminium extrusion, the 3D-printer profile.
Rail count changes with the card grid (two rails per row of cards, seven
rows per face); the list below is the nine-board version until
`mounting.md` is redrawn.

| Part | Qty | Note |
|---|---|---|
| 2020 extrusion, 900 mm | 4 | uprights; sold cut to length |
| 2020 extrusion, 460 mm | 30 | 18 board rails, 8 frame rails, 4 for the hub; 14 m in all |
| 2020 corner brackets with screws | 68 | two per rail end |
| M3 T-nuts for the 6 mm slot | 50 | four per board plus spares |
| M3 × 12 mm male-female standoffs | 50 | brass or nylon |
| M3 × 6 mm screws | 100 | board to standoff, standoff to T-nut |
| Rubber feet or a 500 mm plywood square | 1 | the base |

About 100 USD, all stock items.

## Before pressing order

1. `sim/pcb.py` reports zero DRC errors and zero unconnected for every board, and the commit that says so is the one the gerbers came from (`git status` clean under `boards/`).
2. `sim/gate.py` is green for all eleven programs at TYP and for the six corner programs at LO, HI and MIX (docs/plan.md).
3. Look at the renders in each `fab/` folder for 30 seconds each: header on the top edge, pin 1 marked, LEDs on the front, the board name on the silk.
4. `docs/bring-up.md` read once, so the test plan is known before the boards exist.
