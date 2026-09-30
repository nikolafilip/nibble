# The order: boards, parts, cables, frame

Rewritten 2026-09-29. The three tables between the `bom.py` markers are
written by `python3 sim/bom.py --write` from the routed boards and are not
edited by hand; `python3 sim/bom.py --check` fails when they are stale or
when the schematics and the boards disagree about a part. How this
document got here is in `docs/order-log.md`.

Two words, used strictly: a **design** is a set of files, a **board** is a
piece of fibreglass that is built. The machine is 26 designs and 52 boards.

## 1. What can be ordered today

| | State |
|---|---|
| Coupon, register bit 0, hub (the pilot) | Ready. `ORDER GATE: all pass` on all 26 boards at commit `9519ed3` (2026-09-29): the headers on the back, the hub with its new sockets and its crowbar (D061, D063). Every command of section 6 ended as written |
| Everything else | After the pilot is built and measured (D055) |
| Cables, frame | After `docs/mounting.md` is redrawn for the ribbon behind the cards (D059); `docs/audit.md` section 5 has the open points |

The pilot (D055) is the coupon, register bit 0 and the hub, five of each:
the fab, the parts and the hands are tried on three designs before thirty
are paid for. The coupon has every kind of cell with a test loop on it;
the register card is one full logic card; the hub is the power entry and
the first ribbon.

## 2. Boards

<!-- bom.py: boards -->
| Design | Files | Boards built of each | Five-packs to order | Boards over |
|---|---|---|---|---|
| ALU bit | `cards/alu0` to `alu3`, 4 designs | 1 | 1 each | 4 each |
| clock | `cards/clock` | 1 | 1 | 4 |
| gate coupon (a test card, not in the machine) | `cards/coupon` | 1 | 1 | 4 |
| counter bit | `cards/ctr0` to `ctr7`, 8 designs | 1 | 1 each | 4 each |
| bus hub | `cards/hub` | 1 | 1 | 4 |
| memory control | `cards/memctl` | 1 | 1 | 4 |
| memory slots (one pair of slots a card) | `cards/memslot` | 8 | 2 | 2 |
| panel A | `cards/panela` | 1 | 1 | 4 |
| panel B | `cards/panelb` | 1 | 1 | 4 |
| panel C | `cards/panelc` | 1 | 1 | 4 |
| program (four words a card) | `cards/prog` | 20 | 5 | 5 |
| register bit | `cards/reg0` to `reg3`, 4 designs | 1 | 1 each | 4 each |
| sequencer (245 x 255 mm, four layers) | `boards/03-sequencer` | 1 | 1 | 4 |
| **26 designs** | | **52 boards** | **31 five-packs** | |
<!-- bom.py: end boards -->

The fab sells five of a design. "Boards over" are spares. Twenty program
cards are four five-packs to the last board, so a fifth is ordered (decided
2026-09-29): five over.

To order a design: upload `fab/<name>-gerbers.zip` from its folder at
JLCPCB's quote page, wait for the preview, leave the options as they come
(1.6 mm, HASL, any colour, quantity 5). The cards are two layers, 100 x
100 mm. The sequencer is four layers, 245 x 255 mm, and its zip has eleven
files (two inner layers). The price is what the calculator says for the
uploaded file; write it down here when it has been read. No price in this
document is a quote yet.

## 3. Parts for the pilot

One board of each of the three designs:

<!-- bom.py: pilot -->
| Part | coupon | reg0 | hub | Together |
|---|---|---|---|---|
| 2N7000 transistor, TO-92 | 57 | 99 |  | 156 |
| 1N4148 diode, DO-35 | 2 |  |  | 2 |
| Resistor 100 ohm, 1/4 W axial | 1 |  | 1 | 2 |
| Resistor 1 kohm, 1/4 W axial | 3 | 3 | 1 | 7 |
| Resistor 3.3 kohm, 1/4 W axial | 1 |  |  | 1 |
| Resistor 4.7 kohm, 1/4 W axial | 2 |  |  | 2 |
| Resistor 10 kohm, 1/4 W axial | 3 | 2 | 4 | 9 |
| Resistor 22 kohm, 1/4 W axial |  | 2 |  | 2 |
| Resistor 47 kohm, 1/4 W axial | 36 | 47 |  | 83 |
| Resistor 100 kohm, 1/4 W axial | 1 |  |  | 1 |
| Resistor 220 kohm, 1/4 W axial | 1 |  | 8 | 9 |
| Resistor 1 Mohm, 1/4 W axial | 5 |  |  | 5 |
| LED, 3 mm | 1 | 3 | 1 | 5 |
| Electrolytic capacitor 100 uF, 5 mm can, 2 mm pitch, 16 V or more |  |  | 1 | 1 |
| Electrolytic capacitor 10 uF, 5 mm can, 2 mm pitch, 16 V or more | 1 | 1 |  | 2 |
| Ceramic capacitor 100 nF, 2.5 mm pitch | 1 | 1 | 2 | 4 |
| Ceramic capacitor 47 nF, 2.5 mm pitch | 1 |  |  | 1 |
| Box header 2x32, 2.54 mm (the bus) | 1 | 1 | 2 | 4 |
| Pin header 1x2, 2.54 mm | 1 |  |  | 1 |
| Pin header 1x6, 2.54 mm | 1 |  |  | 1 |
| Test loop, 1.0 mm hole | 15 |  | 6 | 21 |
| SCR BT151-500R, TO-220 (the crowbar) |  |  | 1 | 1 |
| Zener diode 1N4735A, 6.2 V 1.3 W (the crowbar) |  |  | 1 | 1 |
| Rectifier diode 1N5408, 3 A (crossed leads) |  |  | 1 | 1 |
| Polyfuse 1.5 A (Bel 0ZRE0150FF) |  |  | 1 | 1 |
| Banana socket, 4 mm, for the board, upright: Cal Test CT3151V1-2 (red) and CT3151V1-0 (black), one of each |  |  | 2 | 2 |
| **325 parts on one board of each** | 134 | 159 | 32 | |
<!-- bom.py: end pilot -->

All of these come out of the machine's quantities in section 4, the
polyfuse and the hub's 100 uF excepted, which the hub alone uses. The
bench also wants: a 3.3 nF capacitor with clip leads and a x10 scope
probe for the coupon (`sim/results/coupon_expected.md`), a pair of
banana-to-banana leads, and a short 64-way ribbon with three sockets.

## 4. Parts for the machine

<!-- bom.py: parts -->
| Part | Need | Buy | Spares rule |
|---|---|---|---|
| 2N7000 transistor, TO-92 | 3516 | 3900 | a tenth over, to the next 100 |
| 1N4148 diode, DO-35 | 733 | 900 | a tenth over, to the next 100 |
| Resistor 100 ohm, 1/4 W axial | 6 | 100 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 1 kohm, 1/4 W axial | 288 | 400 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 3.3 kohm, 1/4 W axial | 81 | 100 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 4.7 kohm, 1/4 W axial | 4 | 100 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 10 kohm, 1/4 W axial | 133 | 200 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 22 kohm, 1/4 W axial | 87 | 100 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 47 kohm, 1/4 W axial | 1443 | 1600 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 100 kohm, 1/4 W axial | 8 | 100 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 220 kohm, 1/4 W axial | 11 | 100 | a tenth over, to the next 100 (they come in hundreds) |
| Resistor 1 Mohm, 1/4 W axial | 78 | 100 | a tenth over, to the next 100 (they come in hundreds) |
| LED, 3 mm | 281 | 350 | a tenth over, to the next 50 |
| Electrolytic capacitor 100 uF, 5 mm can, 2 mm pitch, 16 V or more | 1 | 10 | a tenth over, to the next 10 |
| Electrolytic capacitor 10 uF, 5 mm can, 2 mm pitch, 16 V or more | 51 | 60 | a tenth over, to the next 10 |
| Electrolytic capacitor 2.2 uF, 5 mm can, 2 mm pitch, 16 V or more | 2 | 10 | a tenth over, to the next 10 |
| Electrolytic capacitor 1 uF, 5 mm can, 2 mm pitch, 16 V or more | 2 | 10 | a tenth over, to the next 10 |
| Ceramic capacitor 100 nF, 2.5 mm pitch | 53 | 60 | a tenth over, to the next 10 |
| Ceramic capacitor 47 nF, 2.5 mm pitch | 2 | 10 | a tenth over, to the next 10 |
| Ceramic capacitor 2.2 nF, 2.5 mm pitch | 2 | 10 | a tenth over, to the next 10 |
| Box header 2x32, 2.54 mm (the bus) | 53 | 56 | a twentieth over, two at the least |
| Box header 2x6, 2.54 mm (link) | 18 | 20 | a twentieth over, two at the least |
| Box header 2x3, 2.54 mm (link) | 20 | 22 | a twentieth over, two at the least |
| Pin header 1x3, 2.54 mm (address jumper) | 144 | 152 | a twentieth over, two at the least |
| Pin header 1x2, 2.54 mm | 2 | 4 | a twentieth over, two at the least |
| Pin header 1x6, 2.54 mm | 1 | 3 | a twentieth over, two at the least |
| DIP switch, 8-way | 84 | 89 | a twentieth over, two at the least |
| Test loop, 1.0 mm hole | 21 | 23 | a twentieth over, two at the least |
| SCR BT151-500R, TO-220 (the crowbar) | 1 | 2 | one over |
| Zener diode 1N4735A, 6.2 V 1.3 W (the crowbar) | 1 | 2 | one over |
| Rectifier diode 1N5408, 3 A (crossed leads) | 1 | 2 | one over |
| DIP switch, 4-way | 1 | 2 | one over |
| DIP switch, 1-way | 1 | 2 | one over |
| Push button, 6 mm tactile | 2 | 3 | one over |
| Potentiometer 1 M linear, 9 mm upright (Alpha RD901F-40) | 1 | 2 | one over |
| Polyfuse 1.5 A (Bel 0ZRE0150FF) | 1 | 2 | one over |
| Banana socket, 4 mm, for the board, upright: Cal Test CT3151V1-2 (red) and CT3151V1-0 (black), one of each | 2 | 2 | none over: two are fitted |
| Jumper cap, 2.54 mm (one on every 1x3 and 1x2 pin header) | 146 | 154 | a twentieth over, two at the least |
| **7136 parts soldered on 52 boards** | | | |
<!-- bom.py: end parts -->

Need is what the 52 boards carry. Buy is Need with spares by the rule in
the last column; the rules are `RULES` in `sim/bom.py`, to be changed
there.

What to look for when buying:

| Part | Look for | Why |
|---|---|---|
| 2N7000 | TO-92, from Onsemi or Diodes Inc. | The boards' holes are 2.54 mm apart; a straight TO-92 has its leads 1.27 mm apart and is spread by hand or on a jig. Anti-static bag until soldered |
| Resistors | 1/4 W, body no longer than 6.3 mm | They stand upright on 5.08 mm |
| Electrolytics | 5 mm can, 2 mm between the leads, 16 V or more | A 25 V 100 uF is a 6.3 mm can and does not fit; the crowbar lets the rail reach 8 V before it fires |
| Ceramic capacitors | 2.5 mm between the leads | Not the 5 mm kind |
| Box headers | Shrouded, straight, 2.54 mm (2x32: XFCN BH254V-64P, LCSC C48603668, or any) | They are soldered on the **back** of the boards (D059) |
| DIP switches | Slide type, 7.62 mm between the rows | |
| Potentiometer | Alpha RD901F-40, 1 M linear | The footprint is this family's: two lugs 9.6 mm apart, 7.5 mm from the pins |
| Polyfuse | Bel 0ZRE0150FF | The footprint is this part's kinked leads: 10.2 mm with a 1.9 mm offset |
| LEDs | 3 mm, any colour; 2 mA types are bright behind 1 k | |
| Banana sockets | Cal Test CT3151V1-2 (red) and CT3151V1-0 (black), the V1 (upright, 19 mm) | The footprint is this part's four pins. The plain CT3151 lies on its side and does not fit |
| SCR, zener, large diode | BT151-500R (TO-220), 1N4735A (6.2 V, 1.3 W), 1N5408 | The crowbar's values are the bench's (`sim/results/crowbar.md`). A clip-on TO-220 heatsink if the supply's limit is ever above 1.5 A |

## 5. Cables and frame

Counted on the boards:

| Part | Need | Buy | Note |
|---|---|---|---|
| IDC socket 2x32 (ZHOURI FC-2.54-64P, LCSC C49261185, or any) | 53 | 60 | one for every bus header: 52 boards, the hub has two. A socket is crimped once |
| IDC socket 2x3 | 20 | 24 | the ALU's and the counter's chains |
| IDC socket 2x6 | 18 | 22 | the sequencer's operand link, the memory's address link |
| Ribbon, 64-way, 1.27 mm | | | the length follows from the route behind the cards, which is not drawn yet |
| Ribbon, 6-way and 12-way | | | offcuts of the 64-way, split along a groove |

The frame's parts are in `docs/mounting.md`. They are bought after the
ribbon's route is drawn: the space between card and rail is where the
ribbon now runs, and the length of the standoffs depends on it.

## 6. Before pressing order

Run from `sim/`, on the commit that is ordered. Each must end as written.

| Command | Ends with |
|---|---|
| `python3 order_check.py <every design in the order>` | `ORDER GATE: all pass` |
| `python3 order_check.py --machine` | `all pass` (every bus header and every link, pin by pin) |
| `python3 order_check.py --selftest` | every planted fault caught |
| `python3 bom.py --check` | the tables are current and the two counts agree |
| `python3 rebuild_check.py` | `every builder writes what is committed` |
| `python3 silk_proof.py <every design in the order>` | the prints in `sim/out/proof/`, looked at: every name readable, none across a pad |

And by eye, in each design's `fab/` folder: the two renders and the
assembly drawing.

What the machine gate (`sim/gate.py`, `sim/results/`) proved is the
circuit; what the order gate proves is that the files are the circuit's.
What neither can show is in `docs/audit.md` section 6: a part that does
not match its usual drawing, the supply's drop along the ribbon, hands.
That is what the pilot is for.
