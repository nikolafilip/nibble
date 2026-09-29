# The order: boards, parts, cables, frame

Two orders (D055): a pilot of three designs, built and bench-checked, then
everything else. Every card has passed the machine gate (docs/cards.md step
9 and the added corners, `sim/results/`), so nothing in the second order is
a guess that the pilot fixes; the pilot checks the fab, the parts and the
hands. Four carts in the end: the fab, the electronic parts, the cables, the
frame.

## 0. The pilot

| Design | Pieces | Why this one |
|---|---|---|
| coupon | 5 | every cell with a test loop on it: the ring, fan-out, the stacks, the bus driver, the clock card's oscillator, a flip-flop with its reset, the D053 line driver, a threshold fixture, a program row (D056) |
| reg0 | 5 | one full logic card (99 transistors), run by hand on the panel's switches; the same design four times in the machine |
| hub | 5 | the power entry, the bus pull-ups, both 64-way headers; the first ribbon is crimped against it. **On hold (2026-09-28)**: see below |

Three five-packs on the 100 x 100 mm tier, about $10 of boards plus
shipping. Upload `cards/<name>/fab/<name>-gerbers.zip` for each (the nine
files the fab takes: copper, mask, silk, outline, drill, job; JLCPCB, 2
layers, 1.6 mm, HASL, any colour); read the quote from the calculator and
keep the cart out of git. The zip is written by `pcb.py` with the other
fab outputs and checked against them by the order gate (section 5, item
1). Parts for the pilot, one of each card built, from `bom.py` (`--per`):

| Part | Footprint | coupon | reg0 | hub | Total |
|---|---|---|---|---|---|
| banana socket | Banana_Jack_1Pin |  |  | 2 | 2 |
| 100u | CP_Radial_D5.0mm_P2.00mm |  |  | 1 | 1 |
| 10u | CP_Radial_D5.0mm_P2.00mm | 1 | 1 |  | 2 |
| 100n | C_Disc_D5.0mm_W2.5mm_P2.50mm | 1 | 1 | 1 | 3 |
| 47n | C_Disc_D5.0mm_W2.5mm_P2.50mm | 1 |  |  | 1 |
| 1N4148 | D_DO-35_SOD27_P7.62mm_Horizontal | 2 |  |  | 2 |
| polyfuse | Fuse_BelFuse_0ZRE0150FF_L23.4mm_W5.3mm |  |  | 1 | 1 |
| IDC header | IDC-Header_2x32_P2.54mm_Vertical | 1 | 1 | 2 | 4 |
| LED | LED_D3.0mm | 1 | 3 | 1 | 5 |
| pin header | PinHeader_1x02_P2.54mm_Vertical | 1 |  |  | 1 |
| pin header | PinHeader_1x06_P2.54mm_Vertical | 1 |  |  | 1 |
| 100 | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 1 |  |  | 1 |
| 100k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 1 |  |  | 1 |
| 10k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 3 | 2 | 4 | 9 |
| 1Meg | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 5 |  |  | 5 |
| 1k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 3 | 3 | 1 | 7 |
| 220k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 1 |  | 8 | 9 |
| 22k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical |  | 2 |  | 2 |
| 3.3k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 1 |  |  | 1 |
| 4.7k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 2 |  |  | 2 |
| 47k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 36 | 47 |  | 83 |
| 2N7000 | TO-92_Inline_Wide | 57 | 99 |  | 156 |
| test loop | TestPoint_Loop_D2.50mm_Drill1.0mm | 15 |  | 6 | 21 |

320 parts. The machine's totals in section 2 cover these, so buy the
2N7000, the 47k and the 100 nF by the hundred once and the pilot uses the
first of them; the polyfuse, the two banana sockets and the 100 µF
are the hub's alone. A short 64-way ribbon with three sockets (section 3)
is the pilot's bus.

Open before the hub is ordered (2026-09-28, found by asking what the
hardware does rather than what the DRC says):

- The banana sockets are not chosen from a part. The footprint is a 6.1 mm
  hole; a socket named here earlier (Hirschmann BIL 20) is M6 by one listing
  and "8 mm mounting diameter" by another, and no drawing was read. The
  sockets are bought and measured first: the bushing through 6.1 mm, the nut
  and tag inside 15 mm, the length behind the board.
- In the frame the black socket (y 45) stands over the rail, which runs
  behind the card's mid-line from y 40 to 60 at the 12 mm of the standoffs;
  a panel socket is longer than that behind the board. The sockets move
  clear of the rail or the hub gets its own standoffs.
- The 64-way headers go on the back of every board (D059, decided
  2026-09-28). The copper does not change; the silk does (the header's
  outline and pin 1 move to the back, the 0.8 mm labels go to 1.0 mm), so
  **the coupon's and reg0's zips will be replaced too: nothing is uploaded
  until that is done and the gate is green on the new files.**

This document is due a rewrite (its counts say "26 boards" for 26 designs,
52 boards built; it promises a buy column it does not have). Each card's
`fab/<name>-assembly.svg` says which value goes where (the cards print no
references and no values; `sim/assembly.py`).

## 1. Boards

**Rewritten for cards on 2026-09-10 (D042); the parts table below is from
`bom.py` over the routed cards, regenerated 2026-09-28 after D053 and D054
(the clock card's extra stage, the panel's 10k pull-downs and 1k button
drivers with their 100 ohm, the memory control card's mid-tick pulse). The
board quotes still have to be read from the calculator with the actual
gerbers.** The quotes that drove the decision, JLCPCB, 2-layer, five pieces:

| Board as it was | Size (mm) | Quote |
|---|---|---|
| Sequencer | 449 × 470 | $258 + $93 shipping |
| Sequencer, matrix turned | 290 × 520 | $153 + $74 shipping |
| Memory | 368 × 377 | $135 + $74 shipping |
| Registers | 266 × 285 | $49 + $30 shipping |

About $1,300 for the machine at five of each. As cards (`cards.md`) it is
25 designs of 100 x 100 mm on the $2 to $4 tier plus the sequencer, one
package:

| Design | Pieces needed | Five-pack |
|---|---|---|
| reg0, reg1, reg2, reg3 | 1 each | 4 |
| alu0, alu1, alu2, alu3 | 1 each | 4 |
| ctr0 .. ctr7 | 1 each | 8 |
| memctl | 1 | 1 |
| memslot | 8 | 2 |
| prog | 6 for `list`, 20 for `sort` | 2 to 4 |
| clock, hub, panel A, B, C, coupon | 1 each | 6 |
| sequencer, 245 x 255, 4-layer (D051) | 1 | 1, about $65 |

27 to 29 five-packs at $2 to $4 plus the sequencer: $120 to $180 of boards,
one shipment of about $40. Every card has passed its three gates
(docs/plan.md, `cards/README.md`); the numbers above are the tier prices,
to be replaced by the calculator's when the carts are built.

## 2. Parts

Totals for one machine with twenty program cards (`sort`) and eight slot
cards, from `sim/bom.py` over the routed cards and the sequencer. Buy the "buy" column: 2N7000 and resistors by the hundred
are cheaper than by the exact count and you will drop some.

| Part | Footprint | Total |
|---|---|---|
| banana socket | Banana_Jack_1Pin | 2 |
| 100u | CP_Radial_D5.0mm_P2.00mm | 1 |
| 10u | CP_Radial_D5.0mm_P2.00mm | 51 |
| 1u | CP_Radial_D5.0mm_P2.00mm | 2 |
| 2.2u | CP_Radial_D5.0mm_P2.00mm | 2 |
| 100n | C_Disc_D5.0mm_W2.5mm_P2.50mm | 52 |
| 2.2n | C_Disc_D5.0mm_W2.5mm_P2.50mm | 2 |
| 47n | C_Disc_D5.0mm_W2.5mm_P2.50mm | 2 |
| 1N4148 | D_DO-35_SOD27_P2.54mm_Vertical_AnodeUp | 727 |
| 1N4148 | D_DO-35_SOD27_P7.62mm_Horizontal | 6 |
| polyfuse | Fuse_BelFuse_0ZRE0150FF_L23.4mm_W5.3mm | 1 |
| IDC header | IDC-Header_2x03_P2.54mm_Vertical | 20 |
| IDC header | IDC-Header_2x06_P2.54mm_Vertical | 18 |
| IDC header | IDC-Header_2x32_P2.54mm_Vertical | 53 |
| LED | LED_D3.0mm | 281 |
| pin header | PinHeader_1x02_P2.54mm_Vertical | 2 |
| pin header | PinHeader_1x03_P2.54mm_Vertical | 144 |
| pin header | PinHeader_1x06_P2.54mm_Vertical | 1 |
| pot | Potentiometer_Alpha_RD901F-40-00D_Single_Vertical | 1 |
| 100 | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 4 |
| 100k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 8 |
| 10k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 133 |
| 1Meg | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 78 |
| 1k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 288 |
| 220k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 11 |
| 22k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 87 |
| 3.3k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 81 |
| 4.7k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 4 |
| 47k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 1443 |
| switch | SW_DIP_SPSTx01_Slide_9.78x4.72mm_W7.62mm_P2.54mm | 1 |
| switch | SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm | 1 |
| switch | SW_DIP_SPSTx08_Slide_9.78x22.5mm_W7.62mm_P2.54mm | 84 |
| switch | SW_PUSH_6mm | 2 |
| 2N7000 | TO-92_Inline_Wide | 3515 |
| test loop | TestPoint_Loop_D2.50mm_Drill1.0mm | 21 |

7129 parts on 26 boards: alu0, alu1, alu2, alu3, clock, coupon, ctr0, ctr1, ctr2, ctr3, ctr4, ctr5, ctr6, ctr7, hub, memctl, memslot, panela, panelb, panelc, prog, reg0, reg1, reg2, reg3, 03-sequencer

Notes:

- **2N7000**: Onsemi or Diodes Inc, TO-92. The footprint is the wide inline one (2.54 mm pitch), so the leads are bent apart with a jig. Keep them in the anti-static bag until they are soldered.
- **Resistors**: 1/4 W axial, mounted vertical (DIN0207, 5.08 mm pitch). Every value on the bus boards is 47k (pull-ups), 1k (LED series and, since D053, the CLK and RST drivers) or 10k (bus pull-ups, the memory write gate, the panel's CLK and RST pull-downs); the panel adds 1 Meg pull-downs, the debounce values and the three 100 ohm in series with the CLK and RST drivers.
- **LEDs**: 3 mm, any colour, one colour for the whole machine or one per board; 2 mA bright types look best behind 1k.
- **Diodes**: 1N4148 everywhere (program words, control matrix, clock, panel).
- **Capacitors**: 100 nF disc 2.5 mm pitch; electrolytics are 5 mm diameter, 2 mm pitch.
- **Switches**: DIP-8 slide (the program words and the panel's levels), one DIP-4 (the panel's data), one DIP-1 (RUN); 6 mm tactile buttons for CLK and RST.
- **Headers**: shrouded 2x32 box headers, 2.54 mm (XFCN BH254V-64P, LCSC C48603668, or any); 2x6 box headers for the sequencer-counter link; 1x3 pin headers for the page jumpers with four jumper caps per page.
- **Hub**: two 4 mm banana sockets, one red and one black, panel type with a threaded bushing that passes a 6.1 mm hole (the board is the panel: a 6.1 mm hole in a 10.16 mm copper ring; the nut and solder tag clamped on the ring at the back are the connection, and the tag can be soldered to the ring as well), nut and tag within 15 mm across; not the shrouded safety type, which wants a 10.8 mm cutout (Cliff S16C and the like), and no part is named until one has been measured (section 0; D058; no USB, D057), and a pair of banana-to-banana leads for the bench supply; 1.5 A radial polyfuse (Bel 0ZRE0150FF, D052), 100 µF bulk. The machine draws up to about 1.2 A with every LED lit: run it from the bench supply at 5.0 V with the limit at 1.5 A; there is no other power entry.
- **Clock**: 1 Meg 9 mm vertical pot (Alpha RD901F), 47 nF and 2.2 µF timing caps.
- **Test loops**: 2.5 mm wire loops on the hub and the coupon, or bare wire. The coupon also wants a 3.3 nF capacitor with clip leads (the ribbon's load for its DRV loop) and a x10 scope probe; the expected readings assume both (`sim/results/coupon_expected.md`).

## 3. Cables

One 64-way ribbon per column face with 2 × 32 IDC sockets crimped along it,
one per card (D043): about 6 m of 64-way ribbon (28 AWG, 1.27 mm pitch) and
45 to 50 sockets (ZHOURI FC-2.54-64P, LCSC C49261185, or any), crimped in a
bench vice or a $10 IDC jig. The neighbour links are 6-way and 12-way
ribbon offcuts with 2 × 3 and 2 × 6 sockets, about 20 of each. No
assembled cables.

## 4. Frame

From docs/mounting.md: 2020 aluminium extrusion, the 3D-printer profile,
one rail per row of cards (the cards' holes are mid-height on their
sides), seven rows per face, the sequencer on two rails of its own.

| Part | Qty | Note |
|---|---|---|
| 2020 extrusion, 900 mm | 4 | uprights; sold cut to length |
| 2020 extrusion, 460 mm | 35 | 25 card rails, 2 sequencer rails, 8 frame rails; 16 m in all |
| 2020 corner brackets with screws | 140 | two per rail end |
| M3 T-nuts for the 6 mm slot | 130 | two per card, four for the sequencer, spares |
| M3 x 12 mm male-female standoffs | 130 | brass or nylon |
| M3 x 6 mm screws | 260 | card to standoff, standoff to T-nut |
| Rubber feet or a 500 mm plywood square | 1 | the base |

About $150, all stock items; a face left empty needs no rails.

## 5. Before pressing order

1. `python3 sim/order_check.py <card> ...` prints `ORDER GATE: all pass` for every card in the order, on the committed files (it checks that the tree is clean under the card, that the project file carries the routed rules, ERC, DRC with schematic parity, JLCPCB's minimum rules, that the gerbers and drill in `fab/` are the committed board's, that the zip is those files, the 100 x 100 outline and its two mounting holes, every part's pads and polarity against the nets, that the assembly drawing is the board's, and that no copper of another net lies where the hardware clamps on the board: within 7.5 mm of a banana socket's centre or 3.3 mm of a mounting hole's, either face). Added 2026-09-28 after a re-audit of the pilot found the coupon's project file wiped by a schematic rebuild, which no one would have seen without re-running DRC on the committed board; the clamp check the same evening, after the hub's first route had put CLK 0.17 mm from the +5V socket's ring, under its nut, with DRC content at 0.15 mm. The sequencer is not a card; it gets `pcb.py`'s own DRC and the same look at its fab folder.
   The gate covers what a tool can measure. What it cannot, and what the eyes are for (item 3), is listed here so the list can be argued with rather than remembered:
   - the part fits its footprint: lead pitch and hole (the gate's `pins` rule ties pads to nets, not to a part's leads; the pairings are in `sim/README.md`), a bushing through its hole (M6 in 6.1 mm), a body clear of its neighbours (the socket heads and the fuse, the IDC shroud and the card edge);
   - hardware in contact with copper it should not touch: the `clamp` check for the sockets and the mounting holes, and no washers wider than the mounting pad (docs/mounting.md);
   - connectors keyed and numbered the way the ribbon is crimped: pin 1 left on both hub headers, the notch toward the card's edge (bring-up.md section 2 tests it before any card is on the ribbon);
   - silk that says what the bench needs: the board name, pin 1, the socket colours, the fuse rating, the test loops' names; 53 labels on the pilot's three boards are 0.8 mm tall, under JLCPCB's stated 1.0 mm, and may print soft;
   - what the builder is told: the cards print no values, so the assembly drawing is the only map (the gate's `asm` check keeps it the board's);
   - what stands behind the board: a part's length through the board against the 12 mm to the rail (the hub's sockets), the ribbon's path against the cards' faces (docs/mounting.md, "Open");
   - what the supply can do: nothing on the hub stops a bench supply turned past 20 V or leads plugged in reversed.
2. `sim/gate.py` is green with every card in the deck and the clock card running the machine from its own power-on reset: all thirteen programs at TYP, the six corner programs at LO, HI and MIX seeds 1 to 4, at 500 pF per bus line, at 4.5 and 4.25 V, with 100 pF between neighbouring bus lines (`sim/results/`, docs/cards.md steps 9 and 11).
3. Look at the renders in each `fab/` folder for 30 seconds each: header on the top edge, pin 1 marked, LEDs on the front, the board name on the silk.
4. `docs/bring-up.md` read once, so the test plan is known before the boards exist.
5. For the pilot: only the three zips of section 0; the second order waits for the pilot's bench checks (bring-up.md sections 1, 2 and 4).
