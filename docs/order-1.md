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
| 100u | CP_Radial_D5.0mm_P2.00mm | 1 |
| 10u | CP_Radial_D5.0mm_P2.00mm | 51 |
| 1u | CP_Radial_D5.0mm_P2.00mm | 2 |
| 2.2u | CP_Radial_D5.0mm_P2.00mm | 2 |
| 100n | C_Disc_D5.0mm_W2.5mm_P2.50mm | 52 |
| 47n | C_Disc_D5.0mm_W2.5mm_P2.50mm | 1 |
| 1N4148 | D_DO-35_SOD27_P2.54mm_Vertical_AnodeUp | 727 |
| 1N4148 | D_DO-35_SOD27_P7.62mm_Horizontal | 4 |
| polyfuse | Fuse_BelFuse_0ZRE0075FF_L11.5mm_W4.8mm | 1 |
| IDC header | IDC-Header_2x03_P2.54mm_Vertical | 20 |
| IDC header | IDC-Header_2x06_P2.54mm_Vertical | 18 |
| IDC header | IDC-Header_2x32_P2.54mm_Vertical | 53 |
| LED | LED_D3.0mm | 281 |
| pin header | PinHeader_1x02_P2.54mm_Vertical | 1 |
| pin header | PinHeader_1x03_P2.54mm_Vertical | 144 |
| pin header | PinHeader_1x04_P2.54mm_Vertical | 1 |
| pot | Potentiometer_Alpha_RD901F-40-00D_Single_Vertical | 1 |
| 100k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 5 |
| 10k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 214 |
| 1Meg | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 87 |
| 1k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 282 |
| 220k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 2 |
| 22k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 87 |
| 4.7k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 2 |
| 47k | R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical | 1429 |
| switch | SW_DIP_SPSTx01_Slide_9.78x4.72mm_W7.62mm_P2.54mm | 1 |
| switch | SW_DIP_SPSTx04_Slide_9.78x12.34mm_W7.62mm_P2.54mm | 1 |
| switch | SW_DIP_SPSTx08_Slide_9.78x22.5mm_W7.62mm_P2.54mm | 84 |
| switch | SW_PUSH_6mm | 2 |
| 2N7000 | TO-92_Inline_Wide | 3485 |
| test loop | TestPoint_Loop_D2.50mm_Drill1.0mm | 12 |
| USB-B socket | USB_B_OST_USB-B1HSxx_Horizontal | 1 |

7054 parts on 26 boards: alu0, alu1, alu2, alu3, clock, coupon, ctr0, ctr1, ctr2, ctr3, ctr4, ctr5, ctr6, ctr7, hub, memctl, memslot, panela, panelb, panelc, prog, reg0, reg1, reg2, reg3, 03-sequencer

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

## Before pressing order

1. `sim/pcb.py` reports zero DRC errors and zero unconnected for every card and the sequencer, and the commit that says so is the one the gerbers came from (`git status` clean under `cards/` and `boards/03-sequencer/`).
2. `sim/gate.py` is green for all twelve programs at TYP and for the six corner programs at LO, HI and MIX with every card in the deck (docs/plan.md), and again at 500 pF per bus line.
3. Look at the renders in each `fab/` folder for 30 seconds each: header on the top edge, pin 1 marked, LEDs on the front, the board name on the silk.
4. `docs/bring-up.md` read once, so the test plan is known before the boards exist.
